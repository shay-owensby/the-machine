#!/usr/bin/env python3
"""
Shared plumbing for every reports-google-analytics script: configuration,
Google authentication, and the two Google Analytics APIs this skill talks to.

Nothing in here is client-specific and nothing in here is a secret. Secrets are
read at run time out of the shared agency credential file and the client's own
.env, held in memory for the length of one process, and never written to
stdout, to a log, to a report, or into any file this skill produces.
`describe_config()` is the only function that renders configuration for human
eyes, and it renders a secret as `present` or `missing` -- never as a value,
never as a prefix, never as a length.

Two APIs, two jobs:

    Google Analytics Data API   analyticsdata.googleapis.com/v1beta
        Every reporting number. runReport, getMetadata, checkCompatibility.

    Google Analytics Admin API  analyticsadmin.googleapis.com/v1beta
        Metadata only: property name, time zone, currency, the key-event
        definitions, data streams, account discovery. Never a metric.

The Admin API is OPTIONAL. It is a separate API that a Google Cloud project can
have switched off while the Data API works perfectly, so nothing required for a
report is sourced from it. Time zone and currency are taken from the Data API's
own response metadata when Admin is unavailable, and the report says the
property name is unknown rather than inventing one.

Configuration comes from four places, later ones winning:

    1. ~/clients/agency.env        shared agency credentials (all reports-* skills)
    2. <project root>/.env         this client's own configuration
    3. the process environment     what the caller exported
    4. explicit CLI flags          --property-id, --agency-env

Secrets are only ever accepted from 1-3. There is no CLI flag for a token, so a
credential cannot end up in a shell history file or a transcript.

Stdlib only for the default OAuth path -- urllib, not the google-api-python-
client. That keeps the skill runnable on any machine with python3 and nothing
installed. Service-account authentication is supported as an alternative and is
the one path that needs a third-party library, because signing a JWT needs RSA.
"""

import base64
import json
import os
import random
import re
import time
import urllib.error
import urllib.parse
import urllib.request
from pathlib import Path

# ---------------------------------------------------------------------------
# Constants
# ---------------------------------------------------------------------------

DEFAULT_AGENCY_ENV = "~/clients/agency.env"
TOKEN_URL = "https://oauth2.googleapis.com/token"
DATA_API = "https://analyticsdata.googleapis.com/v1beta"
ADMIN_API = "https://analyticsadmin.googleapis.com/v1beta"

# The only scope this skill needs. Read-only by design: nothing here can change
# a property, and a token minted for this scope alone cannot be used to.
ANALYTICS_SCOPE = "https://www.googleapis.com/auth/analytics.readonly"

# Data API request shape limits. Exceeding either is a 400, so requests are
# chunked to stay inside them rather than discovering the ceiling in production.
MAX_METRICS_PER_REQUEST = 9
MAX_DIMENSIONS_PER_REQUEST = 9

SECRET_KEYS = (
    "GOOGLE_CLIENT_ID",
    "GOOGLE_CLIENT_SECRET",
    "GOOGLE_REFRESH_TOKEN",
)

# A path to a key file, not a key. Still never echoed with its contents.
CREDENTIAL_PATH_KEYS = (
    "GOOGLE_SERVICE_ACCOUNT_FILE",
    "GOOGLE_APPLICATION_CREDENTIALS",
)

NON_SECRET_KEYS = (
    "GA4_PROPERTY_ID",
    "GA4_PROPERTY_NAME",
    "GA4_ACCOUNT_ID",
    "GA4_REPORT_DAYS",
    "GA4_LAG_DAYS",
    "GA4_CURRENCY_SYMBOL",
    "GA4_KEY_EVENTS",
    "GA4_SITE_URL",
    "GA4_CLIENT_NAME",
)

ALL_KEYS = SECRET_KEYS + CREDENTIAL_PATH_KEYS + NON_SECRET_KEYS

ENV_LINE = re.compile(r"^\s*(?:export\s+)?([A-Za-z_][A-Za-z0-9_]*)\s*=\s*(.*?)\s*$")


class ConfigError(Exception):
    """Configuration or credentials are missing or unusable."""


class ApiError(Exception):
    """A Google Analytics API call failed. Carries a human-readable diagnosis."""

    def __init__(self, message, status=None, error_code=None, detail=None,
                 retryable=False, api=None):
        super().__init__(message)
        self.message = message
        self.status = status
        self.error_code = error_code
        self.detail = detail
        self.retryable = retryable
        self.api = api

    def as_dict(self):
        return {
            "message": self.message,
            "http_status": self.status,
            "error_code": self.error_code,
            "detail": self.detail,
            "retryable": self.retryable,
            "api": self.api,
        }


# ---------------------------------------------------------------------------
# .env parsing
# ---------------------------------------------------------------------------

def read_env_file(path):
    """Parse a KEY=value file. Returns {} for a file that is not there.

    Tolerates `export ` prefixes, single or double quotes, blank lines and
    `#` comments -- the shapes these files actually turn up in.
    """
    p = Path(path).expanduser()
    values = {}
    if not p.is_file():
        return values
    try:
        text = p.read_text(encoding="utf-8", errors="replace")
    except OSError as exc:
        raise ConfigError("Cannot read %s: %s" % (p, exc.strerror or exc))
    for raw in text.splitlines():
        if not raw.strip() or raw.lstrip().startswith("#"):
            continue
        m = ENV_LINE.match(raw)
        if not m:
            continue
        key, value = m.group(1), m.group(2)
        if value and value[0] == value[-1:] and value[0] in ("'", '"'):
            value = value[1:-1]
        else:
            value = value.split(" #", 1)[0].strip()
        values[key] = value
    return values


def normalize_property_id(value):
    """A GA4 property ID is the numeric ID, not the Measurement ID.

    People paste four different things into this field. Each wrong one gets its
    own message, because "invalid property ID" sends someone back to the same
    screen they just copied from.
    """
    if value in (None, ""):
        return None
    raw = str(value).strip()

    if raw.lower().startswith("properties/"):
        raw = raw.split("/", 1)[1].strip()

    if re.match(r"^G-[A-Z0-9]+$", raw, re.I):
        raise ConfigError(
            "GA4_PROPERTY_ID is %r, which is a MEASUREMENT ID (the G- tag that goes on the "
            "website), not a property ID.\n"
            "  The property ID is the number shown under Admin > Property > Property details, "
            "and in the URL as ?p=123456789. It is digits only." % value)
    if re.match(r"^UA-\d+-\d+$", raw, re.I):
        raise ConfigError(
            "GA4_PROPERTY_ID is %r, which is a Universal Analytics property. UA properties "
            "stopped collecting data in 2023 and are not reachable through the Data API.\n"
            "  Use the numeric GA4 property ID instead." % value)
    if re.match(r"^GTM-[A-Z0-9]+$", raw, re.I):
        raise ConfigError(
            "GA4_PROPERTY_ID is %r, which is a Google Tag Manager container ID, not a GA4 "
            "property ID." % value)

    digits = re.sub(r"[^0-9]", "", raw)
    if not digits:
        raise ConfigError(
            "GA4_PROPERTY_ID is %r, which contains no digits. A GA4 property ID is a number "
            "such as 123456789 (Admin > Property > Property details)." % value)
    if len(digits) < 6 or len(digits) > 15:
        raise ConfigError(
            "GA4_PROPERTY_ID is %r, which is %d digits. GA4 property IDs are typically 9-12 "
            "digits. Check Admin > Property > Property details." % (value, len(digits)))
    return digits


# ---------------------------------------------------------------------------
# Configuration
# ---------------------------------------------------------------------------

class Config(object):
    def __init__(self):
        self.client_id = None
        self.client_secret = None
        self.refresh_token = None
        self.service_account_file = None
        self.auth_mode = None          # "oauth" | "service_account"
        self.property_id = None
        self.property_name_hint = None
        self.account_id = None
        self.report_days = 30
        self.lag_days = 0
        self.currency_symbol = None
        self.declared_key_events = []
        self.site_url = None
        self.client_name = None
        self.agency_env_path = None
        self.agency_env_found = False
        self.client_env_path = None
        self.client_env_found = False
        self.sources = {}              # key -> where the value came from
        self.problems = []             # blocking, human-readable
        self.warnings = []             # non-blocking
        self._token = None
        self._token_expires = 0.0
        self.quota = None              # last reported propertyQuota, if any

    @property
    def ok(self):
        return not self.problems

    def require_ok(self):
        if self.problems:
            raise ConfigError("\n".join(self.problems))


def resolve_config(project_root=".", agency_env=None, property_id=None,
                   require_property_id=True):
    """Build a Config from the agency file, the client .env, the process
    environment and explicit overrides -- in that order of increasing priority.

    Never raises for a missing value: it collects them into `problems` so one
    run reports everything that is wrong instead of one thing per run.
    """
    cfg = Config()

    agency_path = Path(
        agency_env or os.environ.get("AGENCY_ENV") or DEFAULT_AGENCY_ENV
    ).expanduser()
    cfg.agency_env_path = str(agency_path)
    agency_values = read_env_file(agency_path)
    cfg.agency_env_found = agency_path.is_file()

    client_path = Path(project_root).expanduser().resolve() / ".env"
    cfg.client_env_path = str(client_path)
    client_values = read_env_file(client_path)
    cfg.client_env_found = client_path.is_file()

    def pick(key, cli=None, cli_label="--flag"):
        for value, source in (
            (cli, cli_label),
            (os.environ.get(key), "process environment"),
            (client_values.get(key), cfg.client_env_path),
            (agency_values.get(key), cfg.agency_env_path),
        ):
            if value not in (None, ""):
                cfg.sources[key] = source
                return value
        cfg.sources[key] = None
        return None

    cfg.client_id = pick("GOOGLE_CLIENT_ID")
    cfg.client_secret = pick("GOOGLE_CLIENT_SECRET")
    cfg.refresh_token = pick("GOOGLE_REFRESH_TOKEN")
    sa_file = pick("GOOGLE_SERVICE_ACCOUNT_FILE") or pick("GOOGLE_APPLICATION_CREDENTIALS")
    cfg.service_account_file = str(Path(sa_file).expanduser()) if sa_file else None

    if not cfg.agency_env_found:
        cfg.problems.append(
            "The shared agency credential file is not there: %s\n"
            "  Every reports-* skill reads its Google credentials from that one file.\n"
            "  Create it from assets/agency.env.example, or point at another copy with\n"
            "  --agency-env /path/to/agency.env (or AGENCY_ENV=...)." % cfg.agency_env_path)

    # Which authentication path this run will take. OAuth is the default because
    # it is what the agency file already carries; a service-account key file
    # wins only when the OAuth trio is incomplete, so adding a key file cannot
    # silently change how every existing client authenticates.
    have_oauth = all((cfg.client_id, cfg.client_secret, cfg.refresh_token))
    if have_oauth:
        cfg.auth_mode = "oauth"
    elif cfg.service_account_file:
        cfg.auth_mode = "service_account"
        if not Path(cfg.service_account_file).is_file():
            cfg.problems.append(
                "GOOGLE_SERVICE_ACCOUNT_FILE points at %s, which is not a file."
                % cfg.service_account_file)
    else:
        missing = [k for k, v in (("GOOGLE_CLIENT_ID", cfg.client_id),
                                  ("GOOGLE_CLIENT_SECRET", cfg.client_secret),
                                  ("GOOGLE_REFRESH_TOKEN", cfg.refresh_token)) if not v]
        cfg.problems.append(
            "Missing shared credential(s): %s\n"
            "  Expected in %s (or the process environment).\n"
            "  These are agency-wide -- do not copy them into the client project.\n"
            "  A service-account key file at GOOGLE_SERVICE_ACCOUNT_FILE is the "
            "alternative; neither is configured." % (", ".join(missing), cfg.agency_env_path))

    try:
        cfg.property_id = normalize_property_id(pick("GA4_PROPERTY_ID", property_id, "--property-id"))
    except ConfigError as exc:
        cfg.problems.append(str(exc))

    if require_property_id and not cfg.property_id:
        cfg.problems.append(
            "No GA4 property ID.\n"
            "  This is the property being reported on, and it is CLIENT configuration --\n"
            "  it belongs in %s as GA4_PROPERTY_ID, not in the agency file.\n"
            "  Find it under Admin > Property > Property details, or pass\n"
            "  --property-id 123456789 for a one-off run." % cfg.client_env_path)

    cfg.property_name_hint = pick("GA4_PROPERTY_NAME")
    cfg.account_id = pick("GA4_ACCOUNT_ID")
    cfg.site_url = pick("GA4_SITE_URL")
    cfg.client_name = pick("GA4_CLIENT_NAME")
    cfg.currency_symbol = pick("GA4_CURRENCY_SYMBOL")

    days = pick("GA4_REPORT_DAYS")
    if days:
        try:
            cfg.report_days = max(1, int(str(days).strip()))
        except ValueError:
            cfg.warnings.append("GA4_REPORT_DAYS=%r is not a number. Using 30." % days)

    lag = pick("GA4_LAG_DAYS")
    if lag:
        try:
            cfg.lag_days = max(0, int(str(lag).strip()))
        except ValueError:
            cfg.warnings.append("GA4_LAG_DAYS=%r is not a number. Using 0." % lag)

    declared = pick("GA4_KEY_EVENTS")
    if declared:
        cfg.declared_key_events = [s.strip() for s in declared.split(",") if s.strip()]

    return cfg


def describe_config(cfg):
    """A dict safe to print, log, or paste into a report.

    Secrets render as present/missing. There is no code path in this module
    that renders a secret any other way.
    """
    return {
        "agency_env": {"path": cfg.agency_env_path, "found": cfg.agency_env_found},
        "client_env": {"path": cfg.client_env_path, "found": cfg.client_env_found},
        "auth": {
            "mode": cfg.auth_mode,
            "scope": ANALYTICS_SCOPE,
            "GOOGLE_CLIENT_ID": "present" if cfg.client_id else "missing",
            "GOOGLE_CLIENT_SECRET": "present" if cfg.client_secret else "missing",
            "GOOGLE_REFRESH_TOKEN": "present" if cfg.refresh_token else "missing",
            "service_account_file": cfg.service_account_file or None,
        },
        "credential_sources": {k: cfg.sources.get(k) for k in SECRET_KEYS},
        "property": {
            "property_id": cfg.property_id,
            "property_id_source": cfg.sources.get("GA4_PROPERTY_ID"),
            "name_hint": cfg.property_name_hint,
            "account_id": cfg.account_id,
            "site_url": cfg.site_url,
            "client_name": cfg.client_name,
        },
        "settings": {
            "report_days": cfg.report_days,
            "lag_days": cfg.lag_days,
            "declared_key_events": cfg.declared_key_events,
            "currency_symbol": cfg.currency_symbol,
        },
        "problems": cfg.problems,
        "warnings": cfg.warnings,
    }


# ---------------------------------------------------------------------------
# HTTP
# ---------------------------------------------------------------------------

RETRYABLE_STATUS = (429, 500, 502, 503, 504)


def _request(method, url, data=None, headers=None, timeout=180):
    """Return (status, body_text). Never raises for an HTTP error status --
    the caller needs the body to classify what went wrong."""
    req = urllib.request.Request(url, data=data, headers=headers or {}, method=method)
    try:
        with urllib.request.urlopen(req, timeout=timeout) as resp:
            return resp.getcode(), resp.read().decode("utf-8", errors="replace")
    except urllib.error.HTTPError as exc:
        body = ""
        try:
            body = exc.read().decode("utf-8", errors="replace")
        except Exception:
            pass
        return exc.code, body
    except urllib.error.URLError as exc:
        raise ApiError(
            "Network error talking to %s: %s" % (url.split("/")[2], exc.reason),
            retryable=True)


# ---------------------------------------------------------------------------
# Authentication
# ---------------------------------------------------------------------------

def _oauth_token(cfg):
    payload = urllib.parse.urlencode({
        "client_id": cfg.client_id,
        "client_secret": cfg.client_secret,
        "refresh_token": cfg.refresh_token,
        "grant_type": "refresh_token",
    }).encode("utf-8")
    status, body = _request(
        "POST", TOKEN_URL, payload,
        {"Content-Type": "application/x-www-form-urlencoded"})

    if status != 200:
        err, desc = "", ""
        try:
            parsed = json.loads(body)
            err = parsed.get("error", "")
            desc = parsed.get("error_description", "")
        except ValueError:
            pass
        if err == "invalid_grant":
            raise ApiError(
                "OAuth refused the refresh token (invalid_grant).\n"
                "  The usual causes, in order of likelihood:\n"
                "   1. The OAuth consent screen is still in Testing -- those refresh tokens\n"
                "      expire after 7 days. Publish the app to Production (or use an\n"
                "      Internal app) and mint a new token.\n"
                "   2. The token was revoked, or the Google account's password changed.\n"
                "   3. The refresh token does not belong to this client ID/secret pair.\n"
                "  Fix: regenerate GOOGLE_REFRESH_TOKEN with the analytics.readonly scope\n"
                "  included, and update %s." % cfg.agency_env_path,
                status=status, error_code="invalid_grant", api="oauth")
        if err == "invalid_client":
            raise ApiError(
                "OAuth refused the client credentials (invalid_client). GOOGLE_CLIENT_ID and "
                "GOOGLE_CLIENT_SECRET in %s do not match a live OAuth client in the Google "
                "Cloud project." % cfg.agency_env_path,
                status=status, error_code="invalid_client", api="oauth")
        if err == "invalid_scope":
            raise ApiError(
                "OAuth rejected the requested scope. The refresh token must have been minted "
                "with %s among its scopes." % ANALYTICS_SCOPE,
                status=status, error_code="invalid_scope", api="oauth")
        raise ApiError(
            "OAuth token exchange failed (HTTP %s%s)." % (status, ": " + err if err else ""),
            status=status, error_code=err or None, detail=desc or None,
            retryable=status in RETRYABLE_STATUS, api="oauth")

    parsed = json.loads(body)
    # Google returns the granted scopes. If analytics.readonly is not among
    # them, every Data API call will fail with a scope error twenty seconds
    # from now -- say it here instead, where the fix is obvious.
    granted = (parsed.get("scope") or "").split()
    if granted and not any(s in granted for s in (
            ANALYTICS_SCOPE,
            "https://www.googleapis.com/auth/analytics",
            "https://www.googleapis.com/auth/analytics.edit")):
        raise ApiError(
            "The refresh token in %s is valid, but it was NOT granted a Google Analytics "
            "scope.\n"
            "  Granted: %s\n"
            "  Needed:  %s\n"
            "  The token is probably the Google Ads one. Re-run the OAuth consent flow and "
            "tick Analytics as well as Ads, then replace GOOGLE_REFRESH_TOKEN. One token can "
            "carry both scopes -- see references/authentication.md."
            % (cfg.agency_env_path, ", ".join(granted), ANALYTICS_SCOPE),
            status=200, error_code="missing_analytics_scope", api="oauth")
    return parsed["access_token"], float(parsed.get("expires_in", 3600))


def _sign_rs256(message, private_key_pem):
    """RS256 signature, using whichever crypto library is present.

    The stdlib cannot do RSA, so this is the one place the skill has an optional
    third-party dependency. The OAuth path has none, which is why it is the
    default.
    """
    try:
        from cryptography.hazmat.primitives import hashes, serialization
        from cryptography.hazmat.primitives.asymmetric import padding
        key = serialization.load_pem_private_key(private_key_pem.encode("utf-8"), password=None)
        return key.sign(message, padding.PKCS1v15(), hashes.SHA256())
    except ImportError:
        pass
    try:
        import rsa  # type: ignore
        key = rsa.PrivateKey.load_pkcs1(private_key_pem.encode("utf-8"))
        return rsa.sign(message, key, "SHA-256")
    except Exception:
        pass
    raise ConfigError(
        "Service-account authentication needs an RSA signing library, and neither\n"
        "  `cryptography` nor `rsa` is importable on this machine.\n"
        "  Either install one (python3 -m pip install cryptography) or use the OAuth\n"
        "  credentials in the agency file, which need no third-party library at all.")


def _service_account_token(cfg):
    try:
        info = json.loads(Path(cfg.service_account_file).read_text(encoding="utf-8"))
    except (OSError, ValueError) as exc:
        raise ConfigError("Cannot read the service-account key file: %s" % exc)
    for required in ("client_email", "private_key", "token_uri"):
        if not info.get(required):
            raise ConfigError(
                "The service-account key file is missing %r. It should be the JSON key "
                "downloaded from Google Cloud, unmodified." % required)

    now = int(time.time())
    header = {"alg": "RS256", "typ": "JWT"}
    claims = {
        "iss": info["client_email"],
        "scope": ANALYTICS_SCOPE,
        "aud": info["token_uri"],
        "iat": now,
        "exp": now + 3600,
    }

    def b64(obj):
        return base64.urlsafe_b64encode(json.dumps(obj, separators=(",", ":")).encode()).rstrip(b"=")

    signing_input = b64(header) + b"." + b64(claims)
    signature = _sign_rs256(signing_input, info["private_key"])
    assertion = (signing_input + b"." + base64.urlsafe_b64encode(signature).rstrip(b"=")).decode()

    payload = urllib.parse.urlencode({
        "grant_type": "urn:ietf:params:oauth:grant-type:jwt-bearer",
        "assertion": assertion,
    }).encode("utf-8")
    status, body = _request("POST", info["token_uri"], payload,
                            {"Content-Type": "application/x-www-form-urlencoded"})
    if status != 200:
        err = ""
        try:
            err = json.loads(body).get("error", "")
        except ValueError:
            pass
        raise ApiError(
            "The service account could not get a token (HTTP %s%s). Check that the key has "
            "not been disabled and that the Analytics APIs are enabled in its Google Cloud "
            "project." % (status, ": " + err if err else ""),
            status=status, error_code=err or None,
            retryable=status in RETRYABLE_STATUS, api="oauth")
    parsed = json.loads(body)
    return parsed["access_token"], float(parsed.get("expires_in", 3600))


def get_access_token(cfg, force=False):
    """Short-lived access token, cached for the life of the process.

    Never returned to any caller outside this module except inside an
    Authorization header.
    """
    if cfg._token and not force and time.time() < cfg._token_expires - 60:
        return cfg._token
    if cfg.auth_mode == "service_account":
        token, ttl = _service_account_token(cfg)
    else:
        token, ttl = _oauth_token(cfg)
    cfg._token = token
    cfg._token_expires = time.time() + ttl
    return cfg._token


# ---------------------------------------------------------------------------
# Error classification
# ---------------------------------------------------------------------------

def _identity_hint(cfg):
    if cfg.auth_mode == "service_account":
        try:
            email = json.loads(Path(cfg.service_account_file).read_text()).get("client_email")
        except Exception:
            email = "the service account"
        return ("the service account %s" % email)
    return "the Google account behind GOOGLE_REFRESH_TOKEN"


def _classify(status, body, cfg, api):
    """Turn a Google Analytics error response into something a human can act on."""
    code = None
    message = None
    reason = None
    try:
        parsed = json.loads(body)
        node = parsed.get("error", parsed)
        message = node.get("message")
        code = node.get("status") or node.get("code")
        for det in node.get("details", []) or []:
            if det.get("reason"):
                reason = det["reason"]
            for viol in det.get("violations", []) or []:
                if viol.get("description"):
                    message = "%s (%s)" % (message, viol["description"])
                    break
    except (ValueError, AttributeError):
        message = (body or "")[:400]

    flat = ("%s %s %s" % (code or "", reason or "", message or "")).upper()
    hint = None

    if "SERVICE_DISABLED" in flat or "HAS NOT BEEN USED IN PROJECT" in flat or "IS DISABLED" in flat:
        api_name = ("Google Analytics Data API" if api == "data"
                    else "Google Analytics Admin API")
        hint = ("The %s is not enabled in the Google Cloud project that owns these "
                "credentials. Enable it in that project (APIs & Services > Library > "
                "%s > Enable) and retry in a minute or two. This is a one-time, "
                "agency-wide fix -- it is not per client." % (api_name, api_name))
    elif "ACCESS_TOKEN_SCOPE_INSUFFICIENT" in flat or "INSUFFICIENT AUTHENTICATION SCOPES" in flat:
        hint = ("The token is valid but was not granted %s. Re-run the OAuth consent flow "
                "with the Analytics scope ticked and replace GOOGLE_REFRESH_TOKEN in %s."
                % (ANALYTICS_SCOPE, cfg.agency_env_path))
    elif "PERMISSION_DENIED" in flat or status == 403:
        hint = ("%s cannot read GA4 property %s. This is a property-access problem, not a "
                "credential problem: someone with Administrator rights on the property must "
                "add that identity under Admin > Property access management with the Viewer "
                "role (Analyst or above also works). Access can take a few minutes to "
                "propagate." % (_identity_hint(cfg).capitalize(), cfg.property_id))
    elif status == 404 or "NOT_FOUND" in flat:
        hint = ("GA4 property %s does not exist, or is not visible to this identity. Check "
                "the number under Admin > Property > Property details -- it is the numeric "
                "property ID, not the G- measurement ID." % cfg.property_id)
    elif status == 401 or "UNAUTHENTICATED" in flat:
        hint = ("The access token was rejected. It is refreshed automatically, so if this "
                "persists the refresh token or key file itself is bad.")
    elif "RESOURCE_EXHAUSTED" in flat or status == 429:
        hint = ("Analytics Data API quota exhausted for this property (tokens are per "
                "property per hour, and are shared with anything else querying it). The "
                "script backs off and retries; if it keeps failing, wait for the hour to "
                "roll over and re-run. Do not report partial data as final.")
    elif "DID NOT MATCH THE EXPECTED PATTERN" in flat or "INVALID_ARGUMENT" in flat:
        if "COMPATIB" in flat or "CANNOT BE USED" in flat or "NOT COMPATIBLE" in flat:
            hint = ("That dimension and metric combination is not queryable together in GA4. "
                    "The fetch checks compatibility before asking, so seeing this means a "
                    "hand-built request -- run :checkCompatibility on it.")
        elif "FIELD" in flat and ("NOT" in flat or "UNKNOWN" in flat):
            hint = ("A field name in the request does not exist in this property's schema. "
                    "The fetch filters requests against the property metadata for exactly "
                    "this reason; a hand-built request bypasses that filter.")
        else:
            hint = "The request was malformed. The message above names the offending field."

    return ApiError(
        message or ("Google Analytics API returned HTTP %s" % status),
        status=status,
        error_code=str(code) if code is not None else (reason or None),
        detail=hint,
        retryable=(status in RETRYABLE_STATUS) or ("RESOURCE_EXHAUSTED" in flat),
        api=api)


# ---------------------------------------------------------------------------
# API calls
# ---------------------------------------------------------------------------

def _call(cfg, method, url, body=None, api="data", max_attempts=5, on_retry=None):
    payload = json.dumps(body).encode("utf-8") if body is not None else None
    attempt = 0
    while True:
        attempt += 1
        token = get_access_token(cfg)
        headers = {"Authorization": "Bearer " + token}
        if payload is not None:
            headers["Content-Type"] = "application/json"
        status, text = _request(method, url, payload, headers)

        if status == 200:
            try:
                return json.loads(text) if text.strip() else {}
            except ValueError:
                raise ApiError(
                    "The %s API returned a body that is not JSON. This is usually a proxy or "
                    "captive-portal page rather than Google."
                    % ("Data" if api == "data" else "Admin"),
                    status=200, api=api)

        err = _classify(status, text, cfg, api)
        if status == 401 and attempt == 1:
            get_access_token(cfg, force=True)
            continue
        if err.retryable and attempt < max_attempts:
            delay = min(32.0, float(2 ** (attempt - 1))) + random.uniform(0, 0.75)
            if on_retry:
                on_retry(attempt, delay, err)
            time.sleep(delay)
            continue
        raise err


def run_report(cfg, body, on_retry=None):
    """POST properties/{id}:runReport. Returns the parsed response."""
    body = dict(body)
    body.setdefault("returnPropertyQuota", True)
    url = "%s/properties/%s:runReport" % (DATA_API, cfg.property_id)
    parsed = _call(cfg, "POST", url, body, api="data", on_retry=on_retry)
    if parsed.get("propertyQuota"):
        cfg.quota = parsed["propertyQuota"]
    return parsed


def get_metadata(cfg, on_retry=None):
    """GET properties/{id}/metadata -- every dimension and metric THIS property
    can report, including its custom definitions."""
    url = "%s/properties/%s/metadata" % (DATA_API, cfg.property_id)
    return _call(cfg, "GET", url, api="data", on_retry=on_retry)


def check_compatibility(cfg, dimensions, metrics, on_retry=None):
    """POST properties/{id}:checkCompatibility -- ask before asking."""
    url = "%s/properties/%s:checkCompatibility" % (DATA_API, cfg.property_id)
    body = {
        "dimensions": [{"name": d} for d in dimensions],
        "metrics": [{"name": m} for m in metrics],
        "compatibilityFilter": "COMPATIBLE",
    }
    return _call(cfg, "POST", url, body, api="data", on_retry=on_retry)


def admin_get(cfg, path, on_retry=None):
    """GET a path under the Admin API. Callers must treat failure as optional."""
    url = "%s/%s" % (ADMIN_API, path.lstrip("/"))
    return _call(cfg, "GET", url, api="admin", on_retry=on_retry)


# ---------------------------------------------------------------------------
# Response helpers
#
# The Data API returns every metric value as a STRING, and omits a row entirely
# when it has nothing to report. A missing row means "no data for that key",
# which is not the same as a row of zeros, and a metric this property does not
# support is never requested in the first place -- so it is absent here and
# stays absent downstream. Nothing in this module turns absent into 0.
# ---------------------------------------------------------------------------

def parse_report(parsed):
    """Normalise a runReport response into a stable, boring shape.

    Returns:
        {
          "dimensions": [name, ...],
          "metrics":    [{"name":..., "type":...}, ...],
          "rows":       [{"keys": [...], "values": {metric: float|None}}, ...],
          "totals":     {metric: float|None} or None,
          "row_count":  int or None,
          "meta":       ResponseMetaData verbatim,
        }
    """
    dims = [h.get("name") for h in parsed.get("dimensionHeaders", []) or []]
    mets = [{"name": h.get("name"), "type": h.get("type")}
            for h in parsed.get("metricHeaders", []) or []]

    def values_of(row):
        out = {}
        for i, m in enumerate(mets):
            vals = row.get("metricValues") or []
            raw = vals[i].get("value") if i < len(vals) else None
            out[m["name"]] = _to_number(raw)
        return out

    rows = []
    for row in parsed.get("rows", []) or []:
        keys = [dv.get("value") for dv in (row.get("dimensionValues") or [])]
        rows.append({"keys": keys, "values": values_of(row)})

    totals = None
    if parsed.get("totals"):
        totals = values_of(parsed["totals"][0])

    return {
        "dimensions": dims,
        "metrics": mets,
        "rows": rows,
        "totals": totals,
        "row_count": parsed.get("rowCount"),
        "meta": parsed.get("metadata") or {},
    }


def _to_number(raw):
    if raw is None or raw == "":
        return None
    try:
        return float(raw)
    except (TypeError, ValueError):
        return None


def add(a, b):
    """Sum that keeps None meaning 'unavailable': None + None is None."""
    if a is None:
        return b
    if b is None:
        return a
    return a + b


def safe_div(numerator, denominator):
    """Ratio, or None when it cannot be computed. Never returns 0 for 0/0."""
    if numerator is None or denominator in (None, 0):
        return None
    return numerator / denominator


def sum_metric(rows, metric):
    """Total one metric across parsed rows -> (total, contributing_rows).

    `total` is None when NO row carried the metric, which is the honest answer
    for a metric this property does not produce.
    """
    total = None
    hits = 0
    for r in rows:
        v = (r.get("values") or {}).get(metric)
        if v is not None:
            hits += 1
            total = add(total, v)
    return total, hits
