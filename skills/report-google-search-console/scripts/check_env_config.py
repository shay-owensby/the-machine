#!/usr/bin/env python3
"""Check Search Console dotenv configuration without revealing secret values."""

from __future__ import annotations

import argparse
import json
import re
from pathlib import Path


KEY_RE = re.compile(r"^[A-Za-z_][A-Za-z0-9_]*$")

ACCESS_TOKEN_ALIASES = (
    "GOOGLE_SEARCH_CONSOLE_ACCESS_TOKEN",
    "GSC_ACCESS_TOKEN",
    "GOOGLE_OAUTH_ACCESS_TOKEN",
)
CLIENT_ID_ALIASES = (
    "GOOGLE_SEARCH_CONSOLE_CLIENT_ID",
    "GSC_CLIENT_ID",
    "GOOGLE_OAUTH_CLIENT_ID",
    "GOOGLE_CLOUD_CLIENT_ID",
)
CLIENT_SECRET_ALIASES = (
    "GOOGLE_SEARCH_CONSOLE_CLIENT_SECRET",
    "GSC_CLIENT_SECRET",
    "GOOGLE_OAUTH_CLIENT_SECRET",
    "GOOGLE_CLOUD_CLIENT_SECRET",
)
REFRESH_TOKEN_ALIASES = (
    "GOOGLE_SEARCH_CONSOLE_REFRESH_TOKEN",
    "GSC_REFRESH_TOKEN",
    "GOOGLE_OAUTH_REFRESH_TOKEN",
    "GOOGLE_REFRESH_TOKEN",
)
ADC_ALIASES = (
    "GOOGLE_APPLICATION_CREDENTIALS",
    "GOOGLE_SERVICE_ACCOUNT_FILE",
    "GOOGLE_SEARCH_CONSOLE_CREDENTIALS_FILE",
)
SERVICE_ACCOUNT_JSON_ALIASES = (
    "GOOGLE_SERVICE_ACCOUNT_JSON",
    "GOOGLE_SEARCH_CONSOLE_SERVICE_ACCOUNT_JSON",
)
PROPERTY_ALIASES = (
    "GOOGLE_SEARCH_CONSOLE_SITE_URL",
    "GOOGLE_SEARCH_CONSOLE_PROPERTY",
    "SEARCH_CONSOLE_SITE_URL",
    "GSC_SITE_URL",
    "GSC_PROPERTY",
)


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser()
    parser.add_argument("--env-file", default="./.env", help="Client project dotenv file")
    return parser.parse_args()


def parse_dotenv(path: Path) -> dict[str, str]:
    values: dict[str, str] = {}
    for raw_line in path.read_text(encoding="utf-8-sig").splitlines():
        line = raw_line.strip()
        if not line or line.startswith("#"):
            continue
        if line.startswith("export "):
            line = line[7:].lstrip()
        key, separator, raw_value = line.partition("=")
        key = key.strip()
        if not separator or not KEY_RE.fullmatch(key):
            continue
        value = raw_value.strip()
        if len(value) >= 2 and value[0] == value[-1] and value[0] in {"'", '"'}:
            value = value[1:-1]
        values[key] = value
    return values


def find_alias(values: dict[str, str], aliases: tuple[str, ...]) -> str | None:
    return next((name for name in aliases if values.get(name)), None)


def main() -> int:
    args = parse_args()
    env_path = Path(args.env_file).resolve()
    if not env_path.is_file():
        print(json.dumps({"status": "blocked", "missing": ["client_project_dotenv"]}, indent=2))
        return 1

    values = parse_dotenv(env_path)
    access_token = find_alias(values, ACCESS_TOKEN_ALIASES)
    oauth_parts = {
        "oauth_client_id": find_alias(values, CLIENT_ID_ALIASES),
        "oauth_client_secret": find_alias(values, CLIENT_SECRET_ALIASES),
        "oauth_refresh_token": find_alias(values, REFRESH_TOKEN_ALIASES),
    }
    adc = find_alias(values, ADC_ALIASES)
    service_account_json = find_alias(values, SERVICE_ACCOUNT_JSON_ALIASES)
    property_name = find_alias(values, PROPERTY_ALIASES)

    if access_token:
        auth_method = "access_token"
        missing: list[str] = []
    elif all(oauth_parts.values()):
        auth_method = "oauth_refresh_token"
        missing = []
    elif adc or service_account_json:
        auth_method = "application_credentials"
        missing = []
    else:
        auth_method = None
        missing = ["oauth_access_token_or_refresh_credentials_or_application_credentials"]
        if any(oauth_parts.values()):
            missing.extend(category for category, name in oauth_parts.items() if not name)

    configured = {
        "access_token": access_token,
        **{key: value for key, value in oauth_parts.items() if value},
        "application_credentials": adc,
        "service_account_json": service_account_json,
        "property": property_name,
    }
    result = {
        "status": "ready" if not missing else "blocked",
        "authentication_method": auth_method,
        "configured_key_names": {key: value for key, value in configured.items() if value},
        "property_selection": "configured" if property_name else "discover_with_sites_list",
        "missing": missing,
    }
    print(json.dumps(result, indent=2))
    return 0 if not missing else 1


if __name__ == "__main__":
    raise SystemExit(main())
