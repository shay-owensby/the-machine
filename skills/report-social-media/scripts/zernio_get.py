#!/usr/bin/env python3
"""Make one authenticated, read-only Zernio GET request without exposing secrets."""

from __future__ import annotations

import argparse
import json
import os
import sys
from pathlib import Path
from urllib.error import HTTPError, URLError
from urllib.parse import urlencode
from urllib.request import Request, urlopen


TOKEN_NAMES = ("ZERNIO_API_KEY", "ZERNIO_ACCESS_TOKEN", "ZERNIO_API_TOKEN", "ZERNIO_TOKEN")


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser()
    parser.add_argument("endpoint", help="Read-only API endpoint, such as /v1/accounts")
    parser.add_argument("--param", action="append", default=[], metavar="KEY=VALUE", help="Query parameter; repeat as needed")
    parser.add_argument("--env-file", default=".env", help="Client project .env path")
    parser.add_argument("--base-url", default=None, help="Override API base ending before /v1")
    parser.add_argument("--timeout", type=float, default=45.0)
    return parser.parse_args()


def read_env(path: Path) -> dict[str, str]:
    values: dict[str, str] = {}
    if not path.is_file():
        return values
    for raw_line in path.read_text(encoding="utf-8").splitlines():
        line = raw_line.strip()
        if not line or line.startswith("#"):
            continue
        if line.startswith("export "):
            line = line[7:].lstrip()
        if "=" not in line:
            continue
        key, value = line.split("=", 1)
        key = key.strip()
        value = value.strip()
        if len(value) >= 2 and value[0] == value[-1] and value[0] in {"'", '"'}:
            value = value[1:-1]
        values[key] = value
    return values


def main() -> int:
    args = parse_args()
    endpoint = "/" + args.endpoint.lstrip("/")
    if not endpoint.startswith("/v1/"):
        raise SystemExit("endpoint must begin with /v1/")

    env_values = read_env(Path(args.env_file))
    token = next(
        (
            os.environ.get(name) or env_values.get(name)
            for name in TOKEN_NAMES
            if os.environ.get(name) or env_values.get(name)
        ),
        None,
    )
    if not token:
        raise SystemExit("No Zernio credential found in the environment or client .env")

    params: list[tuple[str, str]] = []
    for item in args.param:
        if "=" not in item:
            raise SystemExit("each --param must use KEY=VALUE")
        key, value = item.split("=", 1)
        if not key:
            raise SystemExit("query parameter names cannot be empty")
        params.append((key, value))

    base_url = (args.base_url or env_values.get("ZERNIO_API_BASE_URL") or "https://zernio.com/api").rstrip("/")
    url = base_url + endpoint
    if params:
        url += "?" + urlencode(params)

    request = Request(
        url,
        method="GET",
        headers={"Authorization": f"Bearer {token}", "Accept": "application/json"},
    )
    try:
        with urlopen(request, timeout=args.timeout) as response:
            body = response.read().decode("utf-8")
    except HTTPError as exc:
        safe_body = exc.read().decode("utf-8", errors="replace").replace(token, "[REDACTED]")
        try:
            detail = json.dumps(json.loads(safe_body), ensure_ascii=False)
        except (json.JSONDecodeError, TypeError):
            detail = "request failed"
        print(f"Zernio API HTTP {exc.code}: {detail}", file=sys.stderr)
        return 1
    except URLError as exc:
        print(f"Zernio API connection failed: {exc.reason}", file=sys.stderr)
        return 1

    try:
        parsed = json.loads(body)
    except json.JSONDecodeError:
        print("Zernio API returned a non-JSON response", file=sys.stderr)
        return 1
    print(json.dumps(parsed, indent=2, ensure_ascii=False))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
