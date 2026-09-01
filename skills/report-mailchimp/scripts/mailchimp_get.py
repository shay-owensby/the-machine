#!/usr/bin/env python3
"""Make one authenticated Mailchimp Marketing API GET request without exposing secrets."""

from __future__ import annotations

import argparse
import base64
import json
import os
import re
import sys
import time
from pathlib import Path
from urllib.error import HTTPError, URLError
from urllib.parse import urlencode
from urllib.request import Request, urlopen


DC_RE = re.compile(r"^[a-z]{2}\d+$", re.IGNORECASE)


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser()
    parser.add_argument("endpoint", help="Read-only Marketing API endpoint, such as /reports")
    parser.add_argument("--param", action="append", default=[], metavar="KEY=VALUE", help="Query parameter; repeat as needed")
    parser.add_argument("--env-file", default=".env", help="Client project .env path")
    parser.add_argument("--timeout", type=float, default=60.0)
    parser.add_argument("--max-retries", type=int, default=3, help="Bounded retries for 429 and transient 5xx errors")
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


def setting(name: str, env_values: dict[str, str]) -> str | None:
    value = os.environ.get(name)
    if value is not None and value.strip():
        return value.strip()
    value = env_values.get(name)
    return value.strip() if value and value.strip() else None


def redact(text: str, secrets: list[str]) -> str:
    safe = text
    for secret in secrets:
        if secret:
            safe = safe.replace(secret, "[REDACTED]")
    return safe


def main() -> int:
    args = parse_args()
    if args.max_retries < 0 or args.max_retries > 5:
        raise SystemExit("--max-retries must be between 0 and 5")

    endpoint = "/" + args.endpoint.lstrip("/")
    if "://" in endpoint or "#" in endpoint:
        raise SystemExit("endpoint must be a relative Mailchimp Marketing API path")

    env_values = read_env(Path(args.env_file))
    api_key = setting("MAILCHIMP_API_KEY", env_values)
    access_token = setting("MAILCHIMP_ACCESS_TOKEN", env_values)
    server_prefix = setting("MAILCHIMP_SERVER_PREFIX", env_values) or setting("MAILCHIMP_DC", env_values)

    if not api_key and not access_token:
        raise SystemExit("No Mailchimp credential found in the environment or client .env")
    if not server_prefix and api_key and "-" in api_key:
        candidate = api_key.rsplit("-", 1)[-1]
        if DC_RE.fullmatch(candidate):
            server_prefix = candidate.lower()
    if not server_prefix or not DC_RE.fullmatch(server_prefix):
        raise SystemExit("A valid Mailchimp server prefix is required")

    params: list[tuple[str, str]] = []
    for item in args.param:
        if "=" not in item:
            raise SystemExit("each --param must use KEY=VALUE")
        key, value = item.split("=", 1)
        if not key:
            raise SystemExit("query parameter names cannot be empty")
        params.append((key, value))

    url = f"https://{server_prefix}.api.mailchimp.com/3.0{endpoint}"
    if params:
        url += "?" + urlencode(params)

    headers = {"Accept": "application/json", "User-Agent": "Codex-Mailchimp-Report/1.0"}
    if access_token:
        headers["Authorization"] = f"Bearer {access_token}"
    else:
        basic = base64.b64encode(f"codex:{api_key}".encode("utf-8")).decode("ascii")
        headers["Authorization"] = f"Basic {basic}"

    secrets = [api_key or "", access_token or "", headers["Authorization"]]
    for attempt in range(args.max_retries + 1):
        request = Request(url, method="GET", headers=headers)
        try:
            with urlopen(request, timeout=args.timeout) as response:
                body = response.read().decode("utf-8")
            break
        except HTTPError as exc:
            safe_body = redact(exc.read().decode("utf-8", errors="replace"), secrets)
            retryable = exc.code == 429 or 500 <= exc.code <= 599
            if retryable and attempt < args.max_retries:
                retry_after = exc.headers.get("Retry-After")
                try:
                    delay = min(float(retry_after), 30.0) if retry_after else min(2**attempt, 8)
                except ValueError:
                    delay = min(2**attempt, 8)
                time.sleep(delay)
                continue
            try:
                parsed_error = json.loads(safe_body)
                detail = parsed_error.get("detail") or parsed_error.get("title") or "request failed"
            except (json.JSONDecodeError, AttributeError):
                detail = "request failed"
            print(f"Mailchimp API HTTP {exc.code}: {detail}", file=sys.stderr)
            return 1
        except URLError as exc:
            if attempt < args.max_retries:
                time.sleep(min(2**attempt, 8))
                continue
            reason = redact(str(exc.reason), secrets)
            print(f"Mailchimp API connection failed: {reason}", file=sys.stderr)
            return 1
    else:
        print("Mailchimp API request failed after bounded retries", file=sys.stderr)
        return 1

    try:
        parsed = json.loads(body)
    except json.JSONDecodeError:
        print("Mailchimp API returned a non-JSON response", file=sys.stderr)
        return 1
    print(json.dumps(parsed, indent=2, ensure_ascii=False))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
