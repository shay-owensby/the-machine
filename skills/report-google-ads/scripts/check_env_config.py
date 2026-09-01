#!/usr/bin/env python3
"""Check Google Ads dotenv configuration without revealing secret values."""

from __future__ import annotations

import argparse
import json
import re
from pathlib import Path


KEY_RE = re.compile(r"^[A-Za-z_][A-Za-z0-9_]*$")
REQUIRED_ALIASES = {
    "developer_token": (
        "GOOGLE_ADS_DEVELOPER_TOKEN",
        "GOOGLE_ADS_API_DEVELOPER_TOKEN",
        "GOOGLE_DEVELOPER_TOKEN",
    ),
    "oauth_client_id": (
        "GOOGLE_ADS_CLIENT_ID",
        "GOOGLE_OAUTH_CLIENT_ID",
        "GOOGLE_CLOUD_CLIENT_ID",
    ),
    "oauth_client_secret": (
        "GOOGLE_ADS_CLIENT_SECRET",
        "GOOGLE_OAUTH_CLIENT_SECRET",
        "GOOGLE_CLOUD_CLIENT_SECRET",
    ),
    "oauth_refresh_token": (
        "GOOGLE_ADS_REFRESH_TOKEN",
        "GOOGLE_OAUTH_REFRESH_TOKEN",
        "GOOGLE_REFRESH_TOKEN",
    ),
    "customer_id": (
        "GOOGLE_ADS_CUSTOMER_ID",
        "GOOGLE_ADS_CLIENT_CUSTOMER_ID",
        "GOOGLE_CUSTOMER_ID",
    ),
}
OPTIONAL_ALIASES = {
    "login_customer_id": (
        "GOOGLE_ADS_LOGIN_CUSTOMER_ID",
        "GOOGLE_ADS_MANAGER_CUSTOMER_ID",
        "GOOGLE_MANAGER_CUSTOMER_ID",
    ),
    "google_cloud_project_id": (
        "GOOGLE_CLOUD_PROJECT_ID",
        "GOOGLE_PROJECT_ID",
        "GCP_PROJECT_ID",
    ),
}
BUNDLE_ALIASES = (
    "GOOGLE_ADS_CONFIGURATION_JSON",
    "GOOGLE_ADS_CREDENTIALS_JSON",
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
    bundle_name = find_alias(values, BUNDLE_ALIASES)
    required = {
        category: find_alias(values, aliases)
        for category, aliases in REQUIRED_ALIASES.items()
    }
    optional = {
        category: find_alias(values, aliases)
        for category, aliases in OPTIONAL_ALIASES.items()
    }
    missing = [] if bundle_name else [category for category, name in required.items() if not name]

    result = {
        "status": "ready" if not missing else "blocked",
        "configuration_bundle_key": bundle_name,
        "required_key_names": {key: value for key, value in required.items() if value},
        "optional_key_names": {key: value for key, value in optional.items() if value},
        "missing": missing,
    }
    print(json.dumps(result, indent=2))
    return 0 if not missing else 1


if __name__ == "__main__":
    raise SystemExit(main())
