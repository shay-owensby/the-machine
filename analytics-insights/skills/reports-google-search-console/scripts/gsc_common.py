#!/usr/bin/env python3
"""
Shared plumbing for every reports-google-search-console script: configuration,
authentication, and the Search Console API calls themselves.

Nothing in here is client-specific and nothing in here is a secret. Secrets are
read at run time out of the shared agency credential file and the client's own
.env, held in memory for the length of one process, and never written to stdout,
to a log, to a report, or into any file this skill produces. `describe_config()`
is the only function that renders configuration for human eyes, and it renders a
credential as `present` or `missing` -- never as a value, never as a prefix,
never as a length.

Configuration comes from four places, later ones winning:

    1. ~/clients/agency.env        shared agency credentials (all reports-* skills)
    2. <project root>/.env         this client's own configuration
    3. the process environment     what the caller exported
    4. explicit CLI flags          --site-url, --search-type, ...

Secrets are only ever accepted from 1-3. There is no CLI flag for a token or a
key, so a credential cannot end up in a shell history file or a transcript.

Stdlib only for the OAuth path -- urllib, not the google-api-python-client. That
keeps the skill runnable on any machine with python3 and nothing installed. The
optional service-account path needs an RS256 signature, which stdlib cannot
produce; it uses `cryptography` if it is importable and otherwise shells out to
`openssl`, which is present on every macOS and Linux box this will run on.

Two APIs are in play and the distinction matters when reading errors:

    Search Console API  searchconsole.googleapis.com   the data
    Google Cloud        console.cloud.google.com       where access is configured

Google Cloud is not a data source. It is where the OAuth client lives and where
the Search Console API is switched on for the project.
"""

import base64
import json
import os
import random
import re
import shutil
import subprocess
import tempfile
import time
import urllib.error
import urllib.parse
import urllib.request
from datetime import date, datetime, timedelta
from pathlib import Path

# ---------------------------------------------------------------------------
# Constants
# ---------------------------------------------------------------------------

DEFAULT_AGENCY_ENV = "~/clients/agency.env"
TOKEN_URL = "https://oauth2.googleapis.com/token"
API_HOST = "https://searchconsole.googleapis.com"

# Search Analytics, Sites and Sitemaps live under the v3 "webmasters" path;
# URL Inspection is a v1 service on the same host. Both are current -- the v3
# path is the shipped surface of the Search Console API, not a legacy one.
WEBMASTERS = "/webmasters/v3"
URL_INSPECTION = "/v1/urlInspection/index:inspect"

# Read-only is all this skill ever needs. It never submits a sitemap, never
# requests indexing, never writes anything.
SCOPE_READONLY = "https://www.googleapis.com/auth/webmasters.readonly"

# The API caps a single Search Analytics response at 25,000 rows and pages with
# startRow. Nothing here assumes one response is the whole dataset.
MAX_ROW_LIMIT = 25000

# Search Console publishes data on a delay -- usually two days, sometimes three
# or more. This is only the size of the window the freshness probe looks back
# over; the actual latest finalised date is discovered, never assumed.
FRESHNESS_LOOKBACK_DAYS = 14

SEARCH_TYPES = ("web", "image", "video", "news", "discover", "googleNews")

# Discover and Google News are separate surfaces with their own dimension rules:
# neither reports queries, and Discover reports no position worth the name.
NO_QUERY_DIMENSION = ("discover", "googleNews")

SECRET_KEYS = (
    "GOOGLE_CLIENT_ID",
    "GOOGLE_CLIENT_SECRET",
    "GOOGLE_REFRESH_TOKEN",
    "GSC_REFRESH_TOKEN",
    "GOOGLE_SERVICE_ACCOUNT_FILE",
    "GOOGLE_APPLICATION_CREDENTIALS",
)

NON_SECRET_KEYS = (
    "GSC_SITE_URL",
    "GSC_SEARCH_TYPE",
    "GSC_EXTRA_SEARCH_TYPES",
    "GSC_REPORT_DAYS",
    "GSC_LAG_DAYS",
    "GSC_BRAND_TERMS",
    "GSC_PRIMARY_COUNTRY",
    "GSC_ROW_LIMIT",
    "GSC_INSPECT_URLS",
    "GSC_MAX_URL_INSPECTIONS",
    "GOOGLE_IMPERSONATE_SUBJECT",
    "CLIENT_NAME",
)

ENV_LINE = re.compile(r"^\s*(?:export\s+)?([A-Za-z_][A-Za-z0-9_]*)\s*=\s*(.*?)\s*$")


class ConfigError(Exception):
    """Configuration or credentials are missing or unusable."""


class ApiError(Exception):
    """A Search Console API call failed. Carries a human-readable diagnosis."""

    def __init__(self, message, status=None, reason=None, detail=None, retryable=False):
        super().__init__(message)
        self.message = message
        self.status = status
        self.reason = reason
        self.detail = detail
        self.retryable = retryable

    def as_dict(self):
        return {
            "message": self.message,
            "http_status": self.status,
            "reason": self.reason,
            "detail": self.detail,
            "retryable": self.retryable,
        }


# ---------------------------------------------------------------------------
# .env parsing
# ---------------------------------------------------------------------------

def read_env_file(path):
    """Parse a KEY=value file. Returns {} for a file that is not there.

    Tolerates `export ` prefixes, single or double quotes, blank lines and `#`
    comments -- the shapes these files actually turn up in.
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


# ---------------------------------------------------------------------------
# Property identifiers
#
# A Search Console property is identified by one of two exact strings, and the
# difference is not cosmetic:
#
#   sc-domain:example.com        a DOMAIN property   -- every subdomain, both
#                                                       protocols, one dataset
#   https://www.example.com/     a URL-PREFIX property -- exactly that origin
#                                                       and path prefix,
#                                                       trailing slash included
#
# `https://example.com/` and `https://www.example.com/` are DIFFERENT
# properties, and neither is `sc-domain:example.com`. The public website URL is
# not automatically the property identifier, and guessing produces a clean
# 403/404 rather than a wrong report -- which is the one mercy here.
# ---------------------------------------------------------------------------

def property_type(site_url):
    if not site_url:
        return None
    return "domain" if str(site_url).strip().lower().startswith("sc-domain:") else "url_prefix"


def normalize_site_url(value):
    """Tidy a property identifier without inventing one.

    Fixes only what is unambiguous: surrounding whitespace, a missing trailing
    slash on a URL-prefix origin, `sc-domain:` casing. It never converts between
    the two property kinds and never adds or removes `www` -- those change which
    property is being asked for.
    """
    if value is None:
        return None
    v = str(value).strip().strip('"').strip("'")
    if not v:
        return None
    if v.lower().startswith("sc-domain:"):
        host = v.split(":", 1)[1].strip().lower().rstrip("/")
        if host.startswith("http://") or host.startswith("https://"):
            host = urllib.parse.urlsplit(host).netloc
        return "sc-domain:" + host
    if "://" not in v:
        # Bare host: genuinely ambiguous -- could be either property kind. Say so
        # rather than choosing one.
        raise ConfigError(
            "GSC_SITE_URL=%r is not a Search Console property identifier.\n"
            "  It must be exactly one of:\n"
            "    sc-domain:%s          for a Domain property\n"
            "    https://%s/           for a URL-prefix property\n"
            "  These are different properties with different data. Copy the value from\n"
            "  the property switcher in Search Console rather than typing the website\n"
            "  address." % (v, v.lstrip("/"), v.lstrip("/"))
        )
    parts = urllib.parse.urlsplit(v)
    path = parts.path or "/"
    if not path.endswith("/"):
        path += "/"
    return urllib.parse.urlunsplit((parts.scheme.lower(), parts.netloc.lower(), path, "", ""))


def encode_site_url(site_url):
    """Path-segment encoding for the API. `:` and `/` must both be escaped."""
    return urllib.parse.quote(site_url, safe="")


def site_display(site_url):
    """A human label for a property: the domain, without the scheme noise."""
    if not site_url:
        return None
    if property_type(site_url) == "domain":
        return site_url.split(":", 1)[1]
    return urllib.parse.urlsplit(site_url).netloc or site_url


# ---------------------------------------------------------------------------
# Configuration
# ---------------------------------------------------------------------------

class Config(object):
    def __init__(self):
        self.client_id = None
        self.client_secret = None
        self.refresh_token = None
        self.service_account_file = None
        self.impersonate_subject = None
        self.auth_method = None          # oauth_user | service_account
        self.site_url = None
        self.site_url_raw = None
        self.property_type = None
        self.search_type = "web"
        self.extra_search_types = []
        self.report_days = 30
        self.lag_days = 0
        self.brand_terms = []
        self.primary_country = None
        self.row_limit = MAX_ROW_LIMIT
        self.inspect_urls = False
        self.max_url_inspections = 10
        self.client_name = None
        self.agency_env_path = None
        self.agency_env_found = False
        self.client_env_path = None
        self.client_env_found = False
        self.sources = {}
        self.problems = []
        self.warnings = []
        self._token = None
        self._token_expires = 0.0

    @property
    def ok(self):
        return not self.problems

    def require_ok(self):
        if self.problems:
            raise ConfigError("\n".join(self.problems))


def _int_or_warn(cfg, key, raw, default, minimum=0, maximum=None):
    if raw in (None, ""):
        return default
    try:
        v = int(str(raw).strip())
    except ValueError:
        cfg.warnings.append("%s=%r is not a number. Using %s." % (key, raw, default))
        return default
    v = max(minimum, v)
    if maximum is not None:
        v = min(maximum, v)
    return v


def resolve_config(
    project_root=".",
    agency_env=None,
    site_url=None,
    search_type=None,
    require_site_url=True,
):
    """Build a Config from the agency file, the client .env, the process
    environment and explicit overrides -- in that order of increasing priority.

    Never raises for a missing value: it collects them into `problems` so the
    caller can report every missing thing at once instead of one per run.
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
    # A GSC-specific refresh token wins when the agency has minted one for the
    # webmasters scope separately from the Ads token. Most agencies have one
    # token carrying every scope; both arrangements work.
    cfg.refresh_token = pick("GSC_REFRESH_TOKEN") or pick("GOOGLE_REFRESH_TOKEN")
    cfg.service_account_file = (
        pick("GOOGLE_SERVICE_ACCOUNT_FILE") or pick("GOOGLE_APPLICATION_CREDENTIALS")
    )
    cfg.impersonate_subject = pick("GOOGLE_IMPERSONATE_SUBJECT")

    if not cfg.agency_env_found:
        cfg.problems.append(
            "The shared agency credential file is not there: %s\n"
            "  Every reports-* skill reads its Google credentials from that one file.\n"
            "  Create it from assets/agency.env.example, or point at another copy with\n"
            "  --agency-env /path/to/agency.env (or AGENCY_ENV=...)." % cfg.agency_env_path
        )

    # -- decide the authentication method -----------------------------------
    have_oauth = bool(cfg.client_id and cfg.client_secret and cfg.refresh_token)
    sa_path = None
    if cfg.service_account_file:
        sa_path = Path(cfg.service_account_file).expanduser()
        if not sa_path.is_file():
            cfg.warnings.append(
                "GOOGLE_SERVICE_ACCOUNT_FILE points at %s, which is not a readable file. "
                "Ignoring it." % sa_path
            )
            sa_path = None

    if have_oauth:
        cfg.auth_method = "oauth_user"
    elif sa_path:
        cfg.auth_method = "service_account"
        cfg.service_account_file = str(sa_path)
    else:
        cfg.auth_method = None
        missing = [
            k for k, v in (
                ("GOOGLE_CLIENT_ID", cfg.client_id),
                ("GOOGLE_CLIENT_SECRET", cfg.client_secret),
                ("GOOGLE_REFRESH_TOKEN", cfg.refresh_token),
            ) if not v
        ]
        cfg.problems.append(
            "No usable Google credentials.\n"
            "  Missing from %s: %s\n"
            "  Either complete the OAuth trio there, or set GOOGLE_SERVICE_ACCOUNT_FILE to\n"
            "  a service-account key file. Do not copy either into the client project."
            % (cfg.agency_env_path, ", ".join(missing) or "(all present but unusable)")
        )

    # -- the one piece of required client configuration ---------------------
    raw_site = pick("GSC_SITE_URL", site_url, "--site-url")
    cfg.site_url_raw = raw_site
    if raw_site:
        try:
            cfg.site_url = normalize_site_url(raw_site)
            cfg.property_type = property_type(cfg.site_url)
        except ConfigError as exc:
            cfg.problems.append(str(exc))
    elif require_site_url:
        cfg.problems.append(
            "No Search Console property.\n"
            "  This is CLIENT configuration and belongs in %s as GSC_SITE_URL --\n"
            "  not in the agency file. Use the exact identifier Search Console shows:\n"
            "    GSC_SITE_URL=sc-domain:example.com        (Domain property)\n"
            "    GSC_SITE_URL=https://www.example.com/     (URL-prefix property)\n"
            "  Or pass --site-url for a one-off run.\n"
            "  Run: python3 scripts/check_config.py --list-sites to see what this identity\n"
            "  can actually reach." % cfg.client_env_path
        )

    st = (pick("GSC_SEARCH_TYPE", search_type, "--search-type") or "web").strip()
    lowered = {t.lower(): t for t in SEARCH_TYPES}
    if st.lower() in lowered:
        cfg.search_type = lowered[st.lower()]
    else:
        cfg.warnings.append(
            "GSC_SEARCH_TYPE=%r is not a Search Console search type (%s). Using web."
            % (st, ", ".join(SEARCH_TYPES))
        )
        cfg.search_type = "web"

    extra = pick("GSC_EXTRA_SEARCH_TYPES")
    if extra:
        for token in [s.strip() for s in extra.split(",") if s.strip()]:
            if token.lower() in lowered:
                t = lowered[token.lower()]
                if t != cfg.search_type and t not in cfg.extra_search_types:
                    cfg.extra_search_types.append(t)
            else:
                cfg.warnings.append(
                    "GSC_EXTRA_SEARCH_TYPES lists %r, which is not a search type. Ignored."
                    % token
                )

    cfg.report_days = _int_or_warn(cfg, "GSC_REPORT_DAYS", pick("GSC_REPORT_DAYS"), 30, minimum=1)
    cfg.lag_days = _int_or_warn(cfg, "GSC_LAG_DAYS", pick("GSC_LAG_DAYS"), 0, minimum=0)
    cfg.row_limit = _int_or_warn(
        cfg, "GSC_ROW_LIMIT", pick("GSC_ROW_LIMIT"), MAX_ROW_LIMIT, minimum=1, maximum=MAX_ROW_LIMIT
    )
    cfg.max_url_inspections = _int_or_warn(
        cfg, "GSC_MAX_URL_INSPECTIONS", pick("GSC_MAX_URL_INSPECTIONS"), 10, minimum=0, maximum=100
    )

    brands = pick("GSC_BRAND_TERMS")
    if brands:
        cfg.brand_terms = [s.strip() for s in brands.split(",") if s.strip()]

    country = pick("GSC_PRIMARY_COUNTRY")
    if country:
        c = country.strip().lower()
        if len(c) != 3:
            cfg.warnings.append(
                "GSC_PRIMARY_COUNTRY=%r is not a three-letter ISO-3166-1 alpha-3 code "
                "(Search Console uses usa, gbr, aus, can...). Ignoring it." % country
            )
        else:
            cfg.primary_country = c

    inspect = pick("GSC_INSPECT_URLS")
    if inspect:
        cfg.inspect_urls = str(inspect).strip().lower() in ("1", "true", "yes", "on")

    cfg.client_name = pick("CLIENT_NAME")

    return cfg


def describe_config(cfg):
    """A dict safe to print, log, or paste into a report.

    Credentials render as present/missing. There is no code path in this module
    that renders a credential any other way.
    """
    return {
        "agency_env": {"path": cfg.agency_env_path, "found": cfg.agency_env_found},
        "client_env": {"path": cfg.client_env_path, "found": cfg.client_env_found},
        "auth": {
            "method": cfg.auth_method,
            "GOOGLE_CLIENT_ID": "present" if cfg.client_id else "missing",
            "GOOGLE_CLIENT_SECRET": "present" if cfg.client_secret else "missing",
            "refresh_token": "present" if cfg.refresh_token else "missing",
            "refresh_token_key": (
                "GSC_REFRESH_TOKEN" if cfg.sources.get("GSC_REFRESH_TOKEN")
                else ("GOOGLE_REFRESH_TOKEN" if cfg.refresh_token else None)
            ),
            "service_account_file": "present" if cfg.service_account_file else "missing",
            "impersonate_subject": bool(cfg.impersonate_subject),
            "scope": SCOPE_READONLY,
        },
        "credential_sources": {k: cfg.sources.get(k) for k in SECRET_KEYS},
        "property": {
            "site_url": cfg.site_url,
            "site_url_as_configured": cfg.site_url_raw,
            "property_type": cfg.property_type,
            "source": cfg.sources.get("GSC_SITE_URL"),
        },
        "settings": {
            "search_type": cfg.search_type,
            "extra_search_types": cfg.extra_search_types,
            "report_days": cfg.report_days,
            "lag_days": cfg.lag_days,
            "row_limit": cfg.row_limit,
            "brand_terms_configured": len(cfg.brand_terms),
            "primary_country": cfg.primary_country,
            "url_inspection_enabled": cfg.inspect_urls,
            "max_url_inspections": cfg.max_url_inspections,
            "client_name": cfg.client_name,
        },
        "problems": cfg.problems,
        "warnings": cfg.warnings,
    }


# ---------------------------------------------------------------------------
# Authentication
# ---------------------------------------------------------------------------

def _http(url, data=None, headers=None, method=None, timeout=120):
    """Return (status, body_text). Never raises for an HTTP error status -- the
    caller needs the body to classify what went wrong."""
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
            retryable=True,
        )


def _b64url(raw):
    return base64.urlsafe_b64encode(raw).rstrip(b"=")


def _sign_rs256(private_key_pem, message):
    """RS256 over `message`. Uses `cryptography` when available, otherwise
    openssl. Raises ConfigError when neither can sign -- never returns a
    signature it did not actually compute."""
    try:
        from cryptography.hazmat.primitives import hashes, serialization
        from cryptography.hazmat.primitives.asymmetric import padding
        key = serialization.load_pem_private_key(private_key_pem.encode("utf-8"), password=None)
        return key.sign(message, padding.PKCS1v15(), hashes.SHA256())
    except ImportError:
        pass
    except Exception as exc:
        raise ConfigError("Service-account private key could not be loaded: %s" % exc)

    if shutil.which("openssl") is None:
        raise ConfigError(
            "Service-account authentication needs an RSA signature and this machine has "
            "neither the `cryptography` package nor `openssl`.\n"
            "  Fix either way:  python3 -m pip install cryptography\n"
            "  Or use the OAuth user credentials in agency.env instead, which need nothing "
            "installed."
        )

    # openssl cannot take the key and the data on one stdin, so the key goes to a
    # private temporary file that exists for the length of one signature.
    with tempfile.TemporaryDirectory() as tmp:
        keyfile = Path(tmp) / "k.pem"
        keyfile.write_text(private_key_pem)
        os.chmod(str(keyfile), 0o600)
        proc = subprocess.run(
            ["openssl", "dgst", "-sha256", "-sign", str(keyfile), "-binary"],
            input=message, capture_output=True,
        )
    if proc.returncode != 0:
        raise ConfigError(
            "openssl could not sign the service-account assertion: %s"
            % (proc.stderr.decode("utf-8", errors="replace")[:200] or "unknown error")
        )
    return proc.stdout


def _service_account_token(cfg):
    try:
        info = json.loads(Path(cfg.service_account_file).expanduser().read_text())
    except (OSError, ValueError) as exc:
        raise ConfigError(
            "Service-account key file %s could not be read as JSON: %s"
            % (cfg.service_account_file, exc)
        )
    for required in ("client_email", "private_key", "token_uri"):
        if not info.get(required):
            raise ConfigError(
                "Service-account key file is missing %r. It should be the JSON key "
                "downloaded from Google Cloud, unedited." % required
            )

    now = int(time.time())
    claims = {
        "iss": info["client_email"],
        "scope": SCOPE_READONLY,
        "aud": info["token_uri"],
        "iat": now,
        "exp": now + 3600,
    }
    if cfg.impersonate_subject:
        claims["sub"] = cfg.impersonate_subject

    header = _b64url(json.dumps({"alg": "RS256", "typ": "JWT"}).encode("utf-8"))
    body = _b64url(json.dumps(claims).encode("utf-8"))
    signing_input = header + b"." + body
    signature = _b64url(_sign_rs256(info["private_key"], signing_input))
    assertion = (signing_input + b"." + signature).decode("ascii")

    payload = urllib.parse.urlencode({
        "grant_type": "urn:ietf:params:oauth:grant-type:jwt-bearer",
        "assertion": assertion,
    }).encode("utf-8")
    status, text = _http(
        info["token_uri"], data=payload,
        headers={"Content-Type": "application/x-www-form-urlencoded"}, method="POST",
    )
    if status != 200:
        err, desc = "", ""
        try:
            parsed = json.loads(text)
            err = parsed.get("error", "")
            desc = parsed.get("error_description", "")
        except ValueError:
            pass
        if err == "unauthorized_client" and cfg.impersonate_subject:
            raise ApiError(
                "The service account is not authorised to impersonate %s "
                "(unauthorized_client). Domain-wide delegation must be granted in the "
                "Workspace admin console for this client ID and the scope %s."
                % (cfg.impersonate_subject, SCOPE_READONLY),
                status=status, reason=err,
            )
        raise ApiError(
            "Service-account token exchange failed (HTTP %s%s)."
            % (status, ": " + err if err else ""),
            status=status, reason=err or None, detail=desc or None,
            retryable=status in RETRYABLE_STATUS,
        )
    parsed = json.loads(text)
    return parsed["access_token"], float(parsed.get("expires_in", 3600))


def _oauth_user_token(cfg):
    payload = urllib.parse.urlencode({
        "client_id": cfg.client_id,
        "client_secret": cfg.client_secret,
        "refresh_token": cfg.refresh_token,
        "grant_type": "refresh_token",
    }).encode("utf-8")
    status, text = _http(
        TOKEN_URL, data=payload,
        headers={"Content-Type": "application/x-www-form-urlencoded"}, method="POST",
    )
    if status != 200:
        err, desc = "", ""
        try:
            parsed = json.loads(text)
            err = parsed.get("error", "")
            desc = parsed.get("error_description", "")
        except ValueError:
            pass
        if err == "invalid_grant":
            raise ApiError(
                "OAuth refused the refresh token (invalid_grant).\n"
                "  The usual causes, in order of likelihood:\n"
                "   1. The OAuth consent screen is still in Testing -- those refresh tokens\n"
                "      expire after 7 days. Publish the app to Production (or make it\n"
                "      Internal) and mint a new token.\n"
                "   2. The token was revoked, or the Google account's password changed.\n"
                "   3. The refresh token does not belong to this client ID/secret pair.\n"
                "  Fix: regenerate the refresh token WITH the scope %s and update %s."
                % (SCOPE_READONLY, cfg.agency_env_path),
                status=status, reason="invalid_grant",
            )
        if err == "invalid_client":
            raise ApiError(
                "OAuth refused the client credentials (invalid_client). GOOGLE_CLIENT_ID "
                "and GOOGLE_CLIENT_SECRET in %s do not match a live OAuth client in the "
                "Google Cloud project." % cfg.agency_env_path,
                status=status, reason="invalid_client",
            )
        if err == "invalid_scope":
            raise ApiError(
                "The refresh token was not granted the Search Console scope (%s).\n"
                "  A token minted for Google Ads only carries the adwords scope and cannot\n"
                "  read Search Console. Re-mint it with both scopes, or add a separate\n"
                "  GSC_REFRESH_TOKEN to %s." % (SCOPE_READONLY, cfg.agency_env_path),
                status=status, reason="invalid_scope",
            )
        raise ApiError(
            "OAuth token exchange failed (HTTP %s%s)." % (status, ": " + err if err else ""),
            status=status, reason=err or None, detail=desc or None,
            retryable=status in RETRYABLE_STATUS,
        )
    parsed = json.loads(text)
    return parsed["access_token"], float(parsed.get("expires_in", 3600))


def get_access_token(cfg, force=False):
    """A short-lived access token, cached for the life of the process.

    Never returned to any caller outside this module except inside an
    Authorization header.
    """
    if cfg._token and not force and time.time() < cfg._token_expires - 60:
        return cfg._token
    if cfg.auth_method == "service_account":
        token, ttl = _service_account_token(cfg)
    elif cfg.auth_method == "oauth_user":
        token, ttl = _oauth_user_token(cfg)
    else:
        raise ConfigError(
            "No authentication method resolved. Check %s." % cfg.agency_env_path
        )
    cfg._token = token
    cfg._token_expires = time.time() + ttl
    return token


# ---------------------------------------------------------------------------
# The Search Console API
# ---------------------------------------------------------------------------

RETRYABLE_STATUS = (429, 500, 502, 503, 504)


def _classify(status, body, cfg, context=""):
    """Turn a Search Console error response into something a human can act on."""
    message = None
    reason = None
    detail = None
    try:
        parsed = json.loads(body)
        node = parsed.get("error", parsed)
        message = node.get("message")
        errors = node.get("errors") or []
        if errors:
            reason = errors[0].get("reason")
        reason = reason or node.get("status")
    except (ValueError, AttributeError):
        message = (body or "")[:400]

    flat = ("%s %s" % (reason or "", message or "")).lower()
    prop = cfg.site_url or "(no property configured)"
    hint = None

    if status == 403 and ("accessnotconfigured" in flat or "has not been used in project" in flat
                          or "is disabled" in flat):
        hint = (
            "The Search Console API is not enabled on the Google Cloud project behind these "
            "credentials. Enable 'Google Search Console API' in that project "
            "(APIs & Services -> Library), wait a minute, and re-run. This is a Cloud "
            "project setting, not a Search Console permission."
        )
    elif status == 403 and ("insufficient permission" in flat or "forbidden" in flat
                            or "does not have sufficient permission" in flat):
        who = (
            "the service account in %s" % cfg.service_account_file
            if cfg.auth_method == "service_account"
            else "the Google account behind the refresh token"
        )
        hint = (
            "The authenticated identity cannot read %s. Property access is granted inside "
            "Search Console itself: Settings -> Users and permissions -> Add user, with %s "
            "added at Full or Restricted. Cloud project access does not grant it. Run "
            "check_config.py --list-sites to see which properties this identity CAN reach."
            % (prop, who)
        )
    elif status == 401:
        hint = (
            "The access token was rejected. It is refreshed automatically, so if this "
            "persists the credential itself is bad -- or it was minted without the %s "
            "scope." % SCOPE_READONLY
        )
    elif status == 404:
        hint = (
            "Search Console has no property %s for this identity. The identifier must match "
            "exactly, including the trailing slash and the sc-domain: prefix: "
            "'https://example.com/', 'https://www.example.com/' and 'sc-domain:example.com' "
            "are three different properties. check_config.py --list-sites prints the exact "
            "strings this identity can use." % prop
        )
    elif status == 429 or "quota" in flat or "ratelimit" in flat:
        hint = (
            "Search Console rate limits per property and per Cloud project. The script backs "
            "off and retries; if it keeps failing, wait and re-run -- do not report a partial "
            "extract as final."
        )
    elif status == 400:
        hint = (
            "Search Console rejected the request%s. The usual causes are an unsupported "
            "dimension combination (searchAppearance cannot be combined with other "
            "dimensions; discover and googleNews have no query dimension), a date outside "
            "the 16-month window, or a rowLimit above %d."
            % (" (%s)" % context if context else "", MAX_ROW_LIMIT)
        )

    return ApiError(
        message or ("Search Console API returned HTTP %s" % status),
        status=status,
        reason=reason,
        detail=hint or detail,
        retryable=(status in RETRYABLE_STATUS) or ("ratelimit" in flat) or ("backenderror" in flat),
    )


def _call(cfg, url, body=None, method="GET", max_attempts=5, on_retry=None, context=""):
    attempt = 0
    payload = json.dumps(body).encode("utf-8") if body is not None else None
    while True:
        attempt += 1
        headers = {"Authorization": "Bearer " + get_access_token(cfg)}
        if payload is not None:
            headers["Content-Type"] = "application/json"
        status, text = _http(url, data=payload, headers=headers, method=method)

        if status == 200:
            if not text.strip():
                return {}
            try:
                return json.loads(text)
            except ValueError:
                raise ApiError(
                    "Search Console returned a body that is not JSON%s."
                    % (" (%s)" % context if context else ""),
                    status=200,
                )

        err = _classify(status, text, cfg, context)
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


# -- Sites API --------------------------------------------------------------

def list_sites(cfg, **kw):
    """Every property this identity can reach, with its permission level."""
    data = _call(cfg, API_HOST + WEBMASTERS + "/sites", context="sites.list", **kw)
    out = []
    for entry in data.get("siteEntry", []) or []:
        url = entry.get("siteUrl")
        out.append({
            "site_url": url,
            "permission_level": entry.get("permissionLevel"),
            "property_type": property_type(url),
        })
    return out


def get_site(cfg, site_url=None, **kw):
    """One property, or an ApiError saying why not."""
    target = site_url or cfg.site_url
    data = _call(
        cfg, "%s%s/sites/%s" % (API_HOST, WEBMASTERS, encode_site_url(target)),
        context="sites.get", **kw
    )
    return {
        "site_url": data.get("siteUrl", target),
        "permission_level": data.get("permissionLevel"),
        "property_type": property_type(data.get("siteUrl", target)),
    }


# -- Sitemaps API -----------------------------------------------------------

def list_sitemaps(cfg, site_url=None, **kw):
    target = site_url or cfg.site_url
    data = _call(
        cfg, "%s%s/sites/%s/sitemaps" % (API_HOST, WEBMASTERS, encode_site_url(target)),
        context="sitemaps.list", **kw
    )
    out = []
    for s in data.get("sitemap", []) or []:
        contents = s.get("contents") or []
        out.append({
            "path": s.get("path"),
            "last_submitted": s.get("lastSubmitted"),
            "last_downloaded": s.get("lastDownloaded"),
            "is_pending": s.get("isPending"),
            "is_sitemaps_index": s.get("isSitemapsIndex"),
            "type": s.get("type"),
            "warnings": _as_int(s.get("warnings")),
            "errors": _as_int(s.get("errors")),
            "submitted": sum(_as_int(c.get("submitted")) or 0 for c in contents) or None,
            "indexed": sum(_as_int(c.get("indexed")) or 0 for c in contents) or None,
        })
    return out


def _as_int(v):
    if v in (None, ""):
        return None
    try:
        return int(v)
    except (TypeError, ValueError):
        return None


# -- URL Inspection API -----------------------------------------------------

def inspect_url(cfg, page_url, site_url=None, **kw):
    """Point-in-time index status for one URL. Quota is 2,000/day and 600/minute
    per property -- this is called deliberately, never in a loop over a report."""
    target = site_url or cfg.site_url
    body = {"inspectionUrl": page_url, "siteUrl": target}
    if cfg.primary_country:
        body["languageCode"] = "en-US"
    data = _call(cfg, API_HOST + URL_INSPECTION, body=body, method="POST",
                 context="urlInspection.index.inspect", **kw)
    result = (data.get("inspectionResult") or {})
    index = result.get("indexStatusResult") or {}
    mobile = result.get("mobileUsabilityResult") or {}
    rich = result.get("richResultsResult") or {}
    return {
        "url": page_url,
        "verdict": index.get("verdict"),
        "coverage_state": index.get("coverageState"),
        "robots_txt_state": index.get("robotsTxtState"),
        "indexing_state": index.get("indexingState"),
        "page_fetch_state": index.get("pageFetchState"),
        "last_crawl_time": index.get("lastCrawlTime"),
        "crawled_as": index.get("crawledAs"),
        "google_canonical": index.get("googleCanonical"),
        "user_canonical": index.get("userCanonical"),
        "sitemaps": index.get("sitemap"),
        "referring_urls": index.get("referringUrls"),
        "mobile_usability_verdict": mobile.get("verdict"),
        "rich_results_verdict": rich.get("verdict"),
        "inspection_link": result.get("inspectionResultLink"),
    }


# -- Search Analytics -------------------------------------------------------

def search_analytics(
    cfg,
    start_date,
    end_date,
    dimensions=None,
    search_type=None,
    row_limit=None,
    max_rows=None,
    data_state="final",
    dimension_filter_groups=None,
    aggregation_type=None,
    site_url=None,
    on_retry=None,
    on_page=None,
):
    """One Search Analytics query, paged to completion.

    Returns (rows, meta). `rows` are normalised dicts; `meta` records what was
    asked for and whether the extract is believed complete.

    Paging is the point. A single response is capped at 25,000 rows, and a
    property with more queries than that will hand back a first page that looks
    like a complete dataset. `meta['complete']` is False when the cap was hit
    and paging was stopped by `max_rows` -- a report that quotes such an extract
    must say so.
    """
    dims = list(dimensions or [])
    st = search_type or cfg.search_type
    limit = min(row_limit or cfg.row_limit or MAX_ROW_LIMIT, MAX_ROW_LIMIT)
    target = site_url or cfg.site_url
    url = "%s%s/sites/%s/searchAnalytics/query" % (API_HOST, WEBMASTERS, encode_site_url(target))

    rows = []
    start_row = 0
    pages = 0
    truncated = False

    while True:
        body = {
            "startDate": str(start_date),
            "endDate": str(end_date),
            "dimensions": dims,
            "type": st,
            "rowLimit": limit,
            "startRow": start_row,
            "dataState": data_state,
        }
        if dimension_filter_groups:
            body["dimensionFilterGroups"] = dimension_filter_groups
        if aggregation_type:
            body["aggregationType"] = aggregation_type

        data = _call(
            cfg, url, body=body, method="POST", on_retry=on_retry,
            context="searchAnalytics dims=%s type=%s" % (dims or ["(none)"], st),
        )
        page = data.get("rows", []) or []
        pages += 1
        for r in page:
            rows.append(_normalise_row(r, dims))
        if on_page:
            on_page(pages, len(page), len(rows))

        if len(page) < limit:
            break
        start_row += limit
        if max_rows is not None and len(rows) >= max_rows:
            truncated = True
            break
        # A dimensionless query returns exactly one row; nothing to page.
        if not dims:
            break

    meta = {
        "dimensions": dims,
        "search_type": st,
        "start_date": str(start_date),
        "end_date": str(end_date),
        "data_state": data_state,
        "row_limit": limit,
        "pages_fetched": pages,
        "rows_returned": len(rows),
        "truncated": truncated,
        "complete": not truncated,
        "aggregation_type": aggregation_type,
    }
    return rows, meta


def _normalise_row(row, dims):
    """One Search Analytics row -> a flat dict.

    Clicks and impressions are counts; ctr arrives as a fraction and is kept as
    a fraction here (the presentation layer multiplies by 100 exactly once);
    position is a 1-based average where LOWER IS BETTER. A metric the API did
    not return stays None -- it is never filled in with a zero.
    """
    out = {}
    keys = row.get("keys") or []
    for i, dim in enumerate(dims):
        out[dim] = keys[i] if i < len(keys) else None
    out["clicks"] = _as_num(row.get("clicks"))
    out["impressions"] = _as_num(row.get("impressions"))
    out["ctr"] = _as_num(row.get("ctr"))
    out["position"] = _as_num(row.get("position"))
    return out


def _as_num(v):
    if v is None or v == "":
        return None
    try:
        return float(v)
    except (TypeError, ValueError):
        return None


# ---------------------------------------------------------------------------
# Dates
# ---------------------------------------------------------------------------

def parse_date(value):
    if isinstance(value, date):
        return value
    return datetime.strptime(str(value).strip(), "%Y-%m-%d").date()


def latest_final_date(cfg, search_type=None, lookback_days=FRESHNESS_LOOKBACK_DAYS,
                      today=None, on_retry=None):
    """Discover the most recent date Search Console has FINALISED for this
    property, and how much fresher-but-provisional data sits on top of it.

    One cheap query over the last fortnight by date. The newest date it returns
    is the newest finalised date -- which is typically two to three days back,
    sometimes more, and is never assumed to be yesterday. Returns a dict; the
    caller decides what to do when `latest_final` is None (a property with no
    data at all in the window).
    """
    end = today or date.today()
    start = end - timedelta(days=lookback_days)
    final_rows, _ = search_analytics(
        cfg, start, end, dimensions=["date"], search_type=search_type,
        data_state="final", on_retry=on_retry,
    )
    fresh_rows, _ = search_analytics(
        cfg, start, end, dimensions=["date"], search_type=search_type,
        data_state="all", on_retry=on_retry,
    )

    def newest(rows):
        dates = [r.get("date") for r in rows if r.get("date")]
        return max(dates) if dates else None

    latest_final = newest(final_rows)
    latest_any = newest(fresh_rows)
    lag = None
    if latest_final:
        lag = (end - parse_date(latest_final)).days

    return {
        "latest_final": latest_final,
        "latest_including_fresh": latest_any,
        "queried_through": str(end),
        "lag_days": lag,
        "fresh_days_available": (
            (parse_date(latest_any) - parse_date(latest_final)).days
            if latest_final and latest_any and latest_any > latest_final else 0
        ),
        "days_with_final_data_in_window": len([r for r in final_rows if r.get("date")]),
        "lookback_days": lookback_days,
    }


def build_periods(end_date, days=30, lag_days=0):
    """The two comparison windows, ending on the last finalised day.

    current  = the `days` most recent finalised days
    previous = the `days` immediately before that, with no gap and no overlap

    `lag_days` walks the whole pair further back, for properties where the
    freshest finalised days are still visibly settling.
    """
    end = parse_date(end_date) - timedelta(days=lag_days)
    cur_start = end - timedelta(days=days - 1)
    prev_end = cur_start - timedelta(days=1)
    prev_start = prev_end - timedelta(days=days - 1)
    return {
        "current": {"start": str(cur_start), "end": str(end), "days": days},
        "previous": {"start": str(prev_start), "end": str(prev_end), "days": days},
        "lag_days": lag_days,
        "comparable": True,
    }


# ---------------------------------------------------------------------------
# Arithmetic that keeps "unavailable" meaning unavailable
# ---------------------------------------------------------------------------

def add(a, b):
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


def total(rows, key):
    """Sum one metric across rows -> (total, contributing_rows, total_rows).

    `total` is None when NO row carried the metric, which is the honest answer
    for a dataset that does not report it at all.
    """
    out = None
    hits = 0
    for r in rows:
        v = r.get(key)
        if v is not None:
            hits += 1
            out = add(out, v)
    return out, hits, len(rows)


def weighted_position(rows):
    """Impression-weighted average position across rows -> (value, weight).

    Average position cannot be averaged flat: a query with 40,000 impressions
    at position 3 and one with 4 impressions at position 90 do not average to
    46.5 in any sense a reader would recognise. Rows with no position or no
    impressions are skipped rather than counted as zero, and the weight actually
    used comes back so the caller can say how much of the dataset it covers.
    """
    num = 0.0
    den = 0.0
    for r in rows:
        pos = r.get("position")
        imp = r.get("impressions")
        if pos is None or not imp:
            continue
        num += pos * imp
        den += imp
    if den == 0:
        return None, 0
    return num / den, den


def percent_change(current, previous):
    """Percentage change, or None when it is undefined.

    Undefined against a zero or missing baseline. There is no percentage
    increase from zero, and reporting one as "+100%" or "+∞" is a fabrication.
    """
    if current is None or previous in (None, 0):
        return None
    return (current - previous) / abs(previous) * 100.0


def absolute_change(current, previous):
    if current is None or previous is None:
        return None
    return current - previous
