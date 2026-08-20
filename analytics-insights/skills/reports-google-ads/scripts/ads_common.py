#!/usr/bin/env python3
"""
Shared plumbing for every reports-google-ads script: configuration, OAuth, and
the Google Ads REST call itself.

Nothing in here is client-specific and nothing in here is a secret. Secrets are
read at run time out of the agency credential file and the client's own .env,
held in memory for the length of one process, and never written to stdout, to a
log, to a report, or into any file this skill produces. `describe_config()` is
the only function that renders configuration for human eyes, and it renders a
secret as `present` or `missing` -- never as a value, never as a prefix, never
as a length.

One key deserves a note, because it is named for something other than what it
usually holds. `GOOGLE_ADS_LOGIN_CUSTOMER_ID` is, in Google's own vocabulary,
the manager (MCC) account a call authenticates *through*. In practice it is
also the key people label their Google Ads account with, and this agency's
`.env` files use it that way. So it is read as BOTH: it supplies the target
account when nothing else does, and it supplies the manager header only when a
*different* account is being queried through it. Nothing has to be relabelled
for a report to run, and nothing silently queries a manager account.

Configuration comes from four places, later ones winning:

    1. ~/clients/agency.env        shared agency credentials (all reports-* skills)
    2. <project root>/.env         this client's own configuration
    3. the process environment     what the caller exported
    4. explicit CLI flags          --customer-id, --login-customer-id, --api-version

Secrets are only ever accepted from 1-3. There is no CLI flag for a token, so a
developer token cannot end up in a shell history file or a transcript.

Stdlib only -- urllib, not the google-ads client library. That keeps the skill
runnable on any machine with python3 and nothing installed, which is the
difference between a report that runs tonight and a pip install that needs a
human.
"""

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
API_HOST = "https://googleads.googleapis.com"

# Tried in order when no version is configured, and used as the fallback ladder
# when a configured version has been sunset. Google retires versions roughly
# yearly; a hard-coded single version is the thing most likely to break this
# skill twelve months from now, so it degrades to the next one down and says so.
CANDIDATE_VERSIONS = ("v24", "v23", "v22", "v21", "v20", "v19", "v18")

# Read from the shared agency file. GOOGLE_ADS_LOGIN_CUSTOMER_ID lives there too
# as the agency's default manager account, but it is not a secret and a client
# may override it.
SECRET_KEYS = (
    "GOOGLE_CLIENT_ID",
    "GOOGLE_CLIENT_SECRET",
    "GOOGLE_REFRESH_TOKEN",
    "GOOGLE_ADS_DEVELOPER_TOKEN",
)

NON_SECRET_KEYS = (
    "GOOGLE_ADS_LOGIN_CUSTOMER_ID",
    "GOOGLE_ADS_CUSTOMER_ID",
    "GOOGLE_ADS_API_VERSION",
    "GOOGLE_ADS_REPORT_DAYS",
    "GOOGLE_ADS_LAG_DAYS",
    "GOOGLE_ADS_PRIMARY_CONVERSION_ACTIONS",
    "GOOGLE_ADS_CURRENCY_SYMBOL",
)

ALL_KEYS = SECRET_KEYS + NON_SECRET_KEYS

ENV_LINE = re.compile(r"^\s*(?:export\s+)?([A-Za-z_][A-Za-z0-9_]*)\s*=\s*(.*?)\s*$")


class ConfigError(Exception):
    """Configuration or credentials are missing or unusable."""


class ApiError(Exception):
    """A Google Ads API call failed. Carries a human-readable diagnosis."""

    def __init__(self, message, status=None, error_code=None, detail=None, retryable=False):
        super().__init__(message)
        self.message = message
        self.status = status
        self.error_code = error_code
        self.detail = detail
        self.retryable = retryable

    def as_dict(self):
        return {
            "message": self.message,
            "http_status": self.status,
            "error_code": self.error_code,
            "detail": self.detail,
            "retryable": self.retryable,
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


def normalize_customer_id(value, label):
    """Google Ads customer IDs are ten digits. People paste them dashed."""
    if value is None:
        return None
    digits = re.sub(r"[^0-9]", "", str(value))
    if not digits:
        return None
    if len(digits) != 10:
        raise ConfigError(
            "%s is %r, which is %d digits after stripping punctuation. A Google Ads "
            "customer ID is exactly 10 digits (123-456-7890 or 1234567890)."
            % (label, value, len(digits))
        )
    return digits


# ---------------------------------------------------------------------------
# Configuration
# ---------------------------------------------------------------------------

class Config(object):
    def __init__(self):
        self.client_id = None
        self.client_secret = None
        self.refresh_token = None
        self.developer_token = None
        self.login_customer_id = None
        self.customer_id = None
        self.customer_id_key = None      # which env key actually supplied it
        self.api_version = None
        self.api_version_source = "default"
        self.report_days = 30
        self.lag_days = 0
        self.primary_conversion_actions = []
        self.currency_symbol = None
        self.agency_env_path = None
        self.agency_env_found = False
        self.client_env_path = None
        self.client_env_found = False
        self.sources = {}          # key -> where the value came from
        self.problems = []         # blocking, human-readable
        self.warnings = []         # non-blocking
        self._token = None
        self._token_expires = 0.0

    # -- introspection ------------------------------------------------------

    @property
    def ok(self):
        return not self.problems

    def require_ok(self):
        if self.problems:
            raise ConfigError("\n".join(self.problems))


def resolve_config(
    project_root=".",
    agency_env=None,
    customer_id=None,
    login_customer_id=None,
    api_version=None,
    require_customer_id=True,
):
    """Build a Config from the agency file, the client .env, the process
    environment and explicit overrides -- in that order of increasing priority.

    Never raises for missing values: it collects them into `problems` so the
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
    cfg.refresh_token = pick("GOOGLE_REFRESH_TOKEN")
    cfg.developer_token = pick("GOOGLE_ADS_DEVELOPER_TOKEN")

    if not cfg.agency_env_found:
        cfg.problems.append(
            "The shared agency credential file is not there: %s\n"
            "  Every reports-* skill reads its Google credentials from that one file.\n"
            "  Create it from assets/agency.env.example, or point at another copy with\n"
            "  --agency-env /path/to/agency.env (or AGENCY_ENV=...)." % cfg.agency_env_path
        )

    missing_secrets = []
    for key, attr in (
        ("GOOGLE_CLIENT_ID", "client_id"),
        ("GOOGLE_CLIENT_SECRET", "client_secret"),
        ("GOOGLE_REFRESH_TOKEN", "refresh_token"),
        ("GOOGLE_ADS_DEVELOPER_TOKEN", "developer_token"),
    ):
        if not getattr(cfg, attr):
            missing_secrets.append(key)
    if missing_secrets:
        cfg.problems.append(
            "Missing shared credential(s): %s\n"
            "  Expected in %s (or the process environment).\n"
            "  Do not copy these into the client project -- they are agency-wide."
            % (", ".join(missing_secrets), cfg.agency_env_path)
        )

    # -- the manager/login value, whatever it turns out to be used for
    login_raw = pick("GOOGLE_ADS_LOGIN_CUSTOMER_ID", login_customer_id, "--login-customer-id")
    login_source = cfg.sources.get("GOOGLE_ADS_LOGIN_CUSTOMER_ID")
    login_value = None
    try:
        login_value = normalize_customer_id(
            login_raw, "login customer ID (GOOGLE_ADS_LOGIN_CUSTOMER_ID)")
    except ConfigError as exc:
        cfg.problems.append(str(exc))

    # -- the account being reported on.
    #
    # GOOGLE_ADS_CUSTOMER_ID is the explicit name for it and wins whenever it is
    # set. When it is absent, GOOGLE_ADS_LOGIN_CUSTOMER_ID supplies it instead:
    # that key is what these .env files label the account with, and refusing to
    # read it would mean every client had to be relabelled before a report could
    # run. Which key was used is recorded, and check_config.py reports it, so a
    # value read out of the manager slot is never mistaken for a deliberate one.
    target_value = None
    try:
        target_value = normalize_customer_id(
            pick("GOOGLE_ADS_CUSTOMER_ID", customer_id, "--customer-id"),
            "target customer ID (GOOGLE_ADS_CUSTOMER_ID)",
        )
    except ConfigError as exc:
        cfg.problems.append(str(exc))

    if target_value:
        cfg.customer_id = target_value
        cfg.customer_id_key = ("--customer-id"
                               if cfg.sources.get("GOOGLE_ADS_CUSTOMER_ID") == "--customer-id"
                               else "GOOGLE_ADS_CUSTOMER_ID")
    elif login_value:
        cfg.customer_id = login_value
        cfg.customer_id_key = "GOOGLE_ADS_LOGIN_CUSTOMER_ID"
        cfg.sources["GOOGLE_ADS_CUSTOMER_ID"] = login_source
        if login_source == cfg.agency_env_path:
            cfg.warnings.append(
                "The account to report on was taken from GOOGLE_ADS_LOGIN_CUSTOMER_ID in "
                "the SHARED file %s, because neither GOOGLE_ADS_CUSTOMER_ID nor a "
                "client-specific value was set. That is the agency-wide default, so it is "
                "very likely the wrong account for this client. Confirm the account name "
                "in the preflight output before reporting on it, and set "
                "GOOGLE_ADS_CUSTOMER_ID in %s."
                % (cfg.agency_env_path, cfg.client_env_path))
        else:
            cfg.warnings.append(
                "The account to report on (%s) was read from GOOGLE_ADS_LOGIN_CUSTOMER_ID "
                "in %s, since GOOGLE_ADS_CUSTOMER_ID was not set. That key is Google's name "
                "for the MANAGER account, so confirm the preflight reports a real operating "
                "account and not a manager." % (login_value, login_source))

    # -- the manager header.
    #
    # Only sent when it names a DIFFERENT account from the one being queried.
    # Sending login-customer-id equal to the target is at best redundant, and
    # when that ID is a manager it is the setup that returns an account with no
    # campaigns and every metric zero.
    if login_value and login_value != cfg.customer_id:
        cfg.login_customer_id = login_value
    else:
        cfg.login_customer_id = None
        if login_value and cfg.customer_id == login_value \
                and cfg.customer_id_key != "GOOGLE_ADS_LOGIN_CUSTOMER_ID":
            cfg.warnings.append(
                "GOOGLE_ADS_LOGIN_CUSTOMER_ID and the target account are the same ID (%s), "
                "so no manager header is sent and the account is queried directly. If this "
                "account is actually managed by an MCC, set that MCC's ID as the login "
                "customer ID instead." % login_value)

    if require_customer_id and not cfg.customer_id:
        cfg.problems.append(
            "No Google Ads account to report on.\n"
            "  Set GOOGLE_ADS_CUSTOMER_ID in %s to the account being reported on.\n"
            "  (GOOGLE_ADS_LOGIN_CUSTOMER_ID is also accepted, since these .env files\n"
            "   label the account with that key, but neither was found.)\n"
            "  Or pass --customer-id 123-456-7890 for a one-off run." % cfg.client_env_path
        )

    version = pick("GOOGLE_ADS_API_VERSION", api_version, "--api-version")
    if version:
        version = version.strip()
        if not re.match(r"^v\d+$", version):
            cfg.warnings.append(
                "GOOGLE_ADS_API_VERSION=%r does not look like a version (expected e.g. v21). "
                "Ignoring it and auto-negotiating instead." % version
            )
            version = None
        else:
            cfg.api_version_source = cfg.sources.get("GOOGLE_ADS_API_VERSION") or "configured"
    cfg.api_version = version or CANDIDATE_VERSIONS[0]
    if not version:
        cfg.api_version_source = "auto (no GOOGLE_ADS_API_VERSION set)"

    days = pick("GOOGLE_ADS_REPORT_DAYS")
    if days:
        try:
            cfg.report_days = max(1, int(str(days).strip()))
        except ValueError:
            cfg.warnings.append("GOOGLE_ADS_REPORT_DAYS=%r is not a number. Using 30." % days)

    lag = pick("GOOGLE_ADS_LAG_DAYS")
    if lag:
        try:
            cfg.lag_days = max(0, int(str(lag).strip()))
        except ValueError:
            cfg.warnings.append("GOOGLE_ADS_LAG_DAYS=%r is not a number. Using 0." % lag)

    primary = pick("GOOGLE_ADS_PRIMARY_CONVERSION_ACTIONS")
    if primary:
        cfg.primary_conversion_actions = [
            s.strip() for s in primary.split(",") if s.strip()
        ]

    cfg.currency_symbol = pick("GOOGLE_ADS_CURRENCY_SYMBOL")

    return cfg


def describe_config(cfg):
    """A dict safe to print, log, or paste into a report.

    Secrets render as present/missing. There is no code path in this module
    that renders a secret any other way.
    """
    return {
        "agency_env": {
            "path": cfg.agency_env_path,
            "found": cfg.agency_env_found,
        },
        "client_env": {
            "path": cfg.client_env_path,
            "found": cfg.client_env_found,
        },
        "credentials": {
            "GOOGLE_CLIENT_ID": "present" if cfg.client_id else "missing",
            "GOOGLE_CLIENT_SECRET": "present" if cfg.client_secret else "missing",
            "GOOGLE_REFRESH_TOKEN": "present" if cfg.refresh_token else "missing",
            "GOOGLE_ADS_DEVELOPER_TOKEN": "present" if cfg.developer_token else "missing",
        },
        "credential_sources": {
            k: cfg.sources.get(k) for k in SECRET_KEYS
        },
        "account": {
            "customer_id": cfg.customer_id,
            "customer_id_key": cfg.customer_id_key,
            "customer_id_source": cfg.sources.get("GOOGLE_ADS_CUSTOMER_ID"),
            "login_customer_id": cfg.login_customer_id,
            "login_customer_id_source": (
                cfg.sources.get("GOOGLE_ADS_LOGIN_CUSTOMER_ID")
                if cfg.login_customer_id else
                "not sent (no separate manager account configured)"),
        },
        "settings": {
            "api_version": cfg.api_version,
            "api_version_source": cfg.api_version_source,
            "report_days": cfg.report_days,
            "lag_days": cfg.lag_days,
            "primary_conversion_actions": cfg.primary_conversion_actions,
        },
        "problems": cfg.problems,
        "warnings": cfg.warnings,
    }


# ---------------------------------------------------------------------------
# OAuth
# ---------------------------------------------------------------------------

def _post(url, data, headers, timeout=120):
    """POST bytes, return (status, body_text). Never raises for an HTTP error
    status -- the caller needs the body to classify what went wrong."""
    req = urllib.request.Request(url, data=data, headers=headers, method="POST")
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


def get_access_token(cfg, force=False):
    """Exchange the long-lived refresh token for a short-lived access token.

    Cached for the life of the process. The token is never returned to any
    caller outside this module except inside an Authorization header.
    """
    if cfg._token and not force and time.time() < cfg._token_expires - 60:
        return cfg._token

    payload = urllib.parse.urlencode({
        "client_id": cfg.client_id,
        "client_secret": cfg.client_secret,
        "refresh_token": cfg.refresh_token,
        "grant_type": "refresh_token",
    }).encode("utf-8")

    status, body = _post(
        TOKEN_URL, payload,
        {"Content-Type": "application/x-www-form-urlencoded"},
    )

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
                "  Fix: regenerate GOOGLE_REFRESH_TOKEN and update %s."
                % cfg.agency_env_path,
                status=status, error_code="invalid_grant",
            )
        if err == "invalid_client":
            raise ApiError(
                "OAuth refused the client credentials (invalid_client). GOOGLE_CLIENT_ID "
                "and GOOGLE_CLIENT_SECRET in %s do not match a live OAuth client in the "
                "Google Cloud project." % cfg.agency_env_path,
                status=status, error_code="invalid_client",
            )
        raise ApiError(
            "OAuth token exchange failed (HTTP %s%s)." % (status, ": " + err if err else ""),
            status=status, error_code=err or None, detail=desc or None,
            retryable=status in (429, 500, 502, 503, 504),
        )

    parsed = json.loads(body)
    cfg._token = parsed["access_token"]
    cfg._token_expires = time.time() + float(parsed.get("expires_in", 3600))
    return cfg._token


# ---------------------------------------------------------------------------
# Google Ads API
# ---------------------------------------------------------------------------

RETRYABLE_STATUS = (429, 500, 502, 503, 504)


def _classify(status, body, cfg):
    """Turn a Google Ads error response into something a human can act on."""
    code = None
    message = None
    detail = None
    try:
        parsed = json.loads(body)
        node = parsed.get("error", parsed)
        if isinstance(node, list):
            node = node[0].get("error", node[0])
        message = node.get("message")
        for det in node.get("details", []) or []:
            for err in det.get("errors", []) or []:
                ec = err.get("errorCode") or {}
                if ec:
                    code = "%s.%s" % (list(ec.keys())[0], list(ec.values())[0])
                message = err.get("message") or message
                if err.get("trigger"):
                    detail = str(err["trigger"])
                break
            if code:
                break
    except (ValueError, KeyError, IndexError, AttributeError):
        message = (body or "")[:400]

    hint = None
    flat = ((code or "") + " " + (message or "")).upper()

    if "DEVELOPER_TOKEN_NOT_APPROVED" in flat:
        hint = ("The developer token only has Test Account access. It works against test "
                "accounts and returns this against every production account. Apply for "
                "Basic access in the manager account's API Center (~5 business days).")
    elif "DEVELOPER_TOKEN_PROHIBITED" in flat or "INVALID_DEVELOPER_TOKEN" in flat:
        hint = ("GOOGLE_ADS_DEVELOPER_TOKEN is not valid for this Google Cloud project, or "
                "is mistyped. Copy it again from the manager account's API Center.")
    elif "USER_PERMISSION_DENIED" in flat:
        hint = ("The authenticated Google account cannot see customer %s through login "
                "customer %s. Either the account is not linked to that manager, or the "
                "user behind GOOGLE_REFRESH_TOKEN has no access to it. Check the account "
                "hierarchy, and check GOOGLE_ADS_LOGIN_CUSTOMER_ID is the MANAGER account, "
                "not the account being queried."
                % (cfg.customer_id, cfg.login_customer_id or "(not set)"))
    elif "CUSTOMER_NOT_FOUND" in flat or "NOT_ADS_USER" in flat:
        hint = ("Customer ID %s does not resolve to a Google Ads account this login can "
                "reach. Verify the ten digits." % cfg.customer_id)
    elif "CUSTOMER_NOT_ENABLED" in flat:
        hint = ("The account is cancelled or suspended. Historical data may still be "
                "queryable; live campaign data will not be.")
    elif "LOGIN_CUSTOMER_ID" in flat or ("MANAGER" in flat and "REQUIRED" in flat):
        hint = ("This account must be queried through its manager account. Set "
                "GOOGLE_ADS_LOGIN_CUSTOMER_ID to the MCC ID.")
    elif "RESOURCE_EXHAUSTED" in flat or status == 429:
        hint = ("Rate limited or out of daily operations. The script backs off and retries; "
                "if it keeps failing, wait and re-run -- do not report partial data as "
                "final.")
    elif "UNRECOGNIZED_FIELD" in flat or "UNKNOWN_FIELD" in flat:
        hint = ("A field in the query does not exist in API version %s. Pin a known-good "
                "version with GOOGLE_ADS_API_VERSION." % cfg.api_version)
    elif status == 401:
        hint = ("The access token was rejected. It is refreshed automatically, so if this "
                "persists the refresh token itself is bad.")

    return ApiError(
        message or ("Google Ads API returned HTTP %s" % status),
        status=status,
        error_code=code,
        detail=hint or detail,
        retryable=(status in RETRYABLE_STATUS) or ("RESOURCE_EXHAUSTED" in flat),
    )


def _version_missing(status, body):
    """True when the failure looks like 'that API version is gone'."""
    if status != 404:
        return False
    return "not found" in (body or "").lower()


def gaql(cfg, query, customer_id=None, max_attempts=5, on_retry=None):
    """Run one GAQL query and return a list of raw REST result rows.

    Pages through nextPageToken, retries transient failures with exponential
    backoff, and walks down the API version ladder if the configured version has
    been sunset (recording the switch in cfg.warnings).

    Raises ApiError, carrying a diagnosis, on anything it cannot recover from.
    """
    cid = customer_id or cfg.customer_id
    if not cid:
        raise ConfigError("gaql() called with no customer ID.")

    rows = []
    page_token = None
    tried_versions = []

    while True:
        body = {"query": query}
        if page_token:
            body["pageToken"] = page_token
        payload = json.dumps(body).encode("utf-8")

        attempt = 0
        while True:
            attempt += 1
            token = get_access_token(cfg)
            headers = {
                "Authorization": "Bearer " + token,
                "developer-token": cfg.developer_token,
                "Content-Type": "application/json",
            }
            if cfg.login_customer_id:
                headers["login-customer-id"] = cfg.login_customer_id

            url = "%s/%s/customers/%s/googleAds:search" % (API_HOST, cfg.api_version, cid)
            status, text = _post(url, payload, headers)

            if status == 200:
                break

            if _version_missing(status, text):
                tried_versions.append(cfg.api_version)
                remaining = [v for v in CANDIDATE_VERSIONS if v not in tried_versions]
                if remaining:
                    cfg.warnings.append(
                        "Google Ads API %s is not available; retrying with %s. Pin a "
                        "version with GOOGLE_ADS_API_VERSION to stop this happening."
                        % (cfg.api_version, remaining[0])
                    )
                    cfg.api_version = remaining[0]
                    cfg.api_version_source = "auto-negotiated (previous version sunset)"
                    attempt = 0
                    continue
                raise ApiError(
                    "No supported Google Ads API version found. Tried: %s. Set "
                    "GOOGLE_ADS_API_VERSION to a current version."
                    % ", ".join(tried_versions),
                    status=status, error_code="version.NOT_FOUND",
                )

            err = _classify(status, text, cfg)
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

        try:
            parsed = json.loads(text) if text.strip() else {}
        except ValueError:
            raise ApiError("Google Ads API returned a body that is not JSON.", status=200)

        rows.extend(parsed.get("results", []) or [])
        page_token = parsed.get("nextPageToken")
        if not page_token:
            return rows


# ---------------------------------------------------------------------------
# Row helpers
#
# The REST surface returns int64 as a JSON *string*, doubles as numbers, and
# omits fields an account cannot report. That last point is load-bearing: a
# missing key means "not returned", which is not the same as zero, and nothing
# in this module converts one into the other.
# ---------------------------------------------------------------------------

def _camel(snake):
    head, *rest = snake.split("_")
    return head + "".join(w[:1].upper() + w[1:] for w in rest)


def field(row, path, default=None):
    """Dotted lookup on a REST row: field(row, 'metrics.cost_micros')."""
    node = row
    for part in path.split("."):
        key = _camel(part)
        if not isinstance(node, dict) or key not in node:
            return default
        node = node[key]
    return node


def num(row, path):
    """A numeric metric, or None when the API did not return it."""
    raw = field(row, path)
    if raw is None or raw == "":
        return None
    try:
        return float(raw)
    except (TypeError, ValueError):
        return None


def micros(row, path):
    """Micros -> currency units, or None when not returned."""
    v = num(row, path)
    return None if v is None else v / 1000000.0


def add(a, b):
    """Sum that keeps None meaning 'unavailable': None+None is None."""
    if a is None:
        return b
    if b is None:
        return a
    return a + b


def accumulate(rows, getter):
    """Sum a metric across rows -> (total, contributing_rows, total_rows).

    `total` is None when NO row carried the metric: the honest answer for an
    account that does not report it at all.
    """
    total = None
    hits = 0
    for r in rows:
        v = getter(r)
        if v is not None:
            hits += 1
            total = add(total, v)
    return total, hits, len(rows)


def safe_div(numerator, denominator):
    """Ratio, or None when it cannot be computed. Never returns 0 for 0/0."""
    if numerator is None or denominator in (None, 0):
        return None
    return numerator / denominator


def weighted_mean(pairs):
    """Impression-weighted average for share metrics -> (value, weight_used).

    pairs is [(value, weight), ...]; entries with a None value are skipped
    entirely rather than counted as zero, and the weight actually used is
    returned so the caller can say how much of the account it covers.
    """
    num_ = 0.0
    den = 0.0
    for value, weight in pairs:
        if value is None or not weight:
            continue
        num_ += value * weight
        den += weight
    if den == 0:
        return None, 0
    return num_ / den, den
