#!/usr/bin/env python3
"""Fetch a read-only 60-day Google Search Console reporting dataset."""

from __future__ import annotations

import argparse
import json
import os
import re
import sys
import tempfile
import time
from datetime import date, datetime, timedelta
from pathlib import Path
from typing import Any
from urllib import error, parse, request
from zoneinfo import ZoneInfo


PACIFIC = ZoneInfo("America/Los_Angeles")
API_ROOT = "https://www.googleapis.com/webmasters/v3"
TOKEN_URL = "https://oauth2.googleapis.com/token"
READONLY_SCOPE = "https://www.googleapis.com/auth/webmasters.readonly"
KEY_RE = re.compile(r"^[A-Za-z_][A-Za-z0-9_]*$")

ALIASES = {
    "access_token": (
        "GOOGLE_SEARCH_CONSOLE_ACCESS_TOKEN",
        "GSC_ACCESS_TOKEN",
        "GOOGLE_OAUTH_ACCESS_TOKEN",
    ),
    "client_id": (
        "GOOGLE_SEARCH_CONSOLE_CLIENT_ID",
        "GSC_CLIENT_ID",
        "GOOGLE_OAUTH_CLIENT_ID",
        "GOOGLE_CLOUD_CLIENT_ID",
    ),
    "client_secret": (
        "GOOGLE_SEARCH_CONSOLE_CLIENT_SECRET",
        "GSC_CLIENT_SECRET",
        "GOOGLE_OAUTH_CLIENT_SECRET",
        "GOOGLE_CLOUD_CLIENT_SECRET",
    ),
    "refresh_token": (
        "GOOGLE_SEARCH_CONSOLE_REFRESH_TOKEN",
        "GSC_REFRESH_TOKEN",
        "GOOGLE_OAUTH_REFRESH_TOKEN",
        "GOOGLE_REFRESH_TOKEN",
    ),
    "application_credentials": (
        "GOOGLE_APPLICATION_CREDENTIALS",
        "GOOGLE_SERVICE_ACCOUNT_FILE",
        "GOOGLE_SEARCH_CONSOLE_CREDENTIALS_FILE",
    ),
    "service_account_json": (
        "GOOGLE_SERVICE_ACCOUNT_JSON",
        "GOOGLE_SEARCH_CONSOLE_SERVICE_ACCOUNT_JSON",
    ),
    "site_url": (
        "GOOGLE_SEARCH_CONSOLE_SITE_URL",
        "GOOGLE_SEARCH_CONSOLE_PROPERTY",
        "SEARCH_CONSOLE_SITE_URL",
        "GSC_SITE_URL",
        "GSC_PROPERTY",
    ),
}

SEARCH_TYPES = ("web", "image", "video", "news", "discover", "googleNews")
FAMILIES: dict[str, list[str]] = {
    "totals": [],
    "daily": ["date"],
    "queries": ["query"],
    "pages": ["page"],
    "countries": ["country"],
    "devices": ["device"],
    "search_appearances": ["searchAppearance"],
}
DAILY_DETAIL_FAMILIES = {"queries", "pages"}


class SafeError(RuntimeError):
    """Error whose message is safe to show without credential values."""


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser()
    parser.add_argument("--env-file", default="./.env", help="Client project dotenv file")
    parser.add_argument("--site-url", help="Exact Search Console property URL")
    parser.add_argument("--output", required=True, help="Temporary JSON output path")
    parser.add_argument("--report-date", help="YYYY-MM-DD; defaults to today Pacific Time")
    parser.add_argument("--end-date", help="Explicit latest finalized date in YYYY-MM-DD")
    parser.add_argument(
        "--types",
        default=",".join(SEARCH_TYPES),
        help="Comma-separated Search Console types",
    )
    parser.add_argument("--row-limit", type=int, default=25000)
    parser.add_argument("--max-pages", type=int, default=4)
    parser.add_argument(
        "--detail-mode",
        choices=("daily", "period"),
        default="daily",
        help="Query/page extraction strategy; daily follows Google's comprehensive-data guidance",
    )
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


def pick(values: dict[str, str], category: str) -> str | None:
    return next((values[name] for name in ALIASES[category] if values.get(name)), None)


def http_json(
    url: str,
    *,
    token: str | None = None,
    method: str = "GET",
    body: dict[str, Any] | None = None,
    form: dict[str, str] | None = None,
    attempts: int = 5,
) -> dict[str, Any]:
    headers = {"Accept": "application/json", "User-Agent": "codex-gsc-report/1.0"}
    data: bytes | None = None
    if token:
        headers["Authorization"] = f"Bearer {token}"
    if body is not None:
        headers["Content-Type"] = "application/json"
        data = json.dumps(body, separators=(",", ":")).encode("utf-8")
    elif form is not None:
        headers["Content-Type"] = "application/x-www-form-urlencoded"
        data = parse.urlencode(form).encode("utf-8")

    for attempt in range(attempts):
        try:
            req = request.Request(url, data=data, headers=headers, method=method)
            with request.urlopen(req, timeout=60) as response:
                payload = response.read()
                return json.loads(payload.decode("utf-8")) if payload else {}
        except error.HTTPError as exc:
            transient = exc.code == 429 or 500 <= exc.code < 600
            if transient and attempt + 1 < attempts:
                retry_after = exc.headers.get("Retry-After")
                delay = (
                    min(float(retry_after), 30.0)
                    if retry_after and retry_after.isdigit()
                    else min(2**attempt, 16)
                )
                time.sleep(delay)
                continue
            category = {
                400: "invalid request or credential grant",
                401: "expired or invalid OAuth credentials",
                403: "property permission or API access denied",
                404: "Search Console property not found",
                429: "Search Console API quota exceeded",
            }.get(exc.code, f"Search Console API HTTP {exc.code}")
            raise SafeError(category) from None
        except (error.URLError, TimeoutError) as exc:
            if attempt + 1 < attempts:
                time.sleep(min(2**attempt, 16))
                continue
            raise SafeError("network failure while calling the Search Console API") from exc
    raise SafeError("Search Console API request failed")


def token_from_google_auth(values: dict[str, str]) -> str:
    try:
        import google.auth  # type: ignore[import-not-found]
        from google.auth.transport.requests import Request as GoogleAuthRequest  # type: ignore[import-not-found]
        from google.oauth2 import service_account  # type: ignore[import-not-found]
    except ImportError as exc:
        raise SafeError(
            "application credentials are configured but google-auth is not installed"
        ) from exc

    inline_json = pick(values, "service_account_json")
    credential_path = pick(values, "application_credentials")
    if inline_json:
        try:
            info = json.loads(inline_json)
        except json.JSONDecodeError as exc:
            raise SafeError("configured service-account JSON is invalid") from exc
        credentials = service_account.Credentials.from_service_account_info(
            info, scopes=[READONLY_SCOPE]
        )
    elif credential_path:
        credentials, _ = google.auth.load_credentials_from_file(
            credential_path, scopes=[READONLY_SCOPE]
        )
    else:
        credentials, _ = google.auth.default(scopes=[READONLY_SCOPE])
    credentials.refresh(GoogleAuthRequest())
    if not credentials.token:
        raise SafeError("application credentials did not produce an OAuth token")
    return str(credentials.token)


def get_access_token(values: dict[str, str]) -> tuple[str, str]:
    direct = pick(values, "access_token")
    if direct:
        return direct, "access_token"

    client_id = pick(values, "client_id")
    client_secret = pick(values, "client_secret")
    refresh_token = pick(values, "refresh_token")
    if client_id and client_secret and refresh_token:
        response = http_json(
            TOKEN_URL,
            method="POST",
            form={
                "client_id": client_id,
                "client_secret": client_secret,
                "refresh_token": refresh_token,
                "grant_type": "refresh_token",
            },
        )
        token = response.get("access_token")
        if not token:
            raise SafeError("OAuth refresh did not return an access token")
        return str(token), "oauth_refresh_token"

    if pick(values, "application_credentials") or pick(values, "service_account_json"):
        return token_from_google_auth(values), "application_credentials"

    raise SafeError("no usable OAuth or application credentials found in the client .env")


def list_sites(token: str) -> list[dict[str, Any]]:
    response = http_json(f"{API_ROOT}/sites", token=token)
    return list(response.get("siteEntry", []))


def choose_site(
    token: str, values: dict[str, str], explicit_site: str | None
) -> tuple[str, str | None]:
    sites = list_sites(token)
    requested = explicit_site or pick(values, "site_url")
    if requested:
        match = next((site for site in sites if site.get("siteUrl") == requested), None)
        if not match:
            raise SafeError(
                "configured Search Console property is not accessible to this OAuth principal"
            )
        return requested, match.get("permissionLevel")

    usable = [
        site
        for site in sites
        if site.get("siteUrl")
        and site.get("permissionLevel") not in {None, "siteUnverifiedUser"}
    ]
    if len(usable) == 1:
        return str(usable[0]["siteUrl"]), usable[0].get("permissionLevel")
    if not usable:
        raise SafeError("OAuth principal has no usable Search Console properties")
    choices = ", ".join(str(site["siteUrl"]) for site in usable)
    raise SafeError(
        f"multiple Search Console properties are available; choose one with --site-url: {choices}"
    )


def analytics_endpoint(site_url: str) -> str:
    encoded = parse.quote(site_url, safe="")
    return f"{API_ROOT}/sites/{encoded}/searchAnalytics/query"


def query_once(token: str, site_url: str, body: dict[str, Any]) -> dict[str, Any]:
    return http_json(
        analytics_endpoint(site_url), token=token, method="POST", body=body
    )


def discover_latest_finalized(
    token: str, site_url: str, report_date: date
) -> tuple[date, dict[str, Any]]:
    yesterday = report_date - timedelta(days=1)
    probe_start = yesterday - timedelta(days=9)
    common_body = {
        "startDate": probe_start.isoformat(),
        "endDate": yesterday.isoformat(),
        "dimensions": ["date"],
        "type": "web",
        "aggregationType": "byProperty",
        "rowLimit": 25000,
        "startRow": 0,
    }
    fresh_response = query_once(
        token,
        site_url,
        {
            **common_body,
            "dataState": "all",
        },
    )
    metadata = dict(fresh_response.get("metadata", {}))
    first_incomplete = metadata.get("first_incomplete_date")
    selection: str
    if first_incomplete:
        latest = date.fromisoformat(first_incomplete) - timedelta(days=1)
        selection = "first_incomplete_date_metadata"
    else:
        finalized_response = query_once(
            token,
            site_url,
            {**common_body, "dataState": "final"},
        )
        finalized_dates: list[date] = []
        for row in finalized_response.get("rows", []):
            keys = row.get("keys", [])
            if not keys:
                continue
            try:
                candidate = date.fromisoformat(str(keys[0]))
            except ValueError:
                continue
            if candidate <= yesterday:
                finalized_dates.append(candidate)
        if finalized_dates:
            latest = max(finalized_dates)
            selection = "latest_finalized_date_row"
        else:
            latest = yesterday
            selection = "fallback_yesterday_no_finalized_rows"
    return latest, {
        "probe_start": probe_start.isoformat(),
        "probe_end": yesterday.isoformat(),
        "first_incomplete_date": first_incomplete,
        "latest_finalized_date": latest.isoformat(),
        "selection": selection,
    }


def aggregation_for(search_type: str, dimensions: list[str]) -> str:
    if search_type in {"discover", "googleNews"}:
        return "auto"
    if "page" in dimensions or "searchAppearance" in dimensions:
        return "auto"
    return "byProperty"


def query_family(
    token: str,
    site_url: str,
    *,
    start: date,
    end: date,
    search_type: str,
    dimensions: list[str],
    row_limit: int,
    max_pages: int,
) -> dict[str, Any]:
    rows: list[dict[str, Any]] = []
    metadata: dict[str, Any] = {}
    response_aggregation_type: str | None = None
    truncated_by_cap = False
    page_count = 0

    while True:
        body: dict[str, Any] = {
            "startDate": start.isoformat(),
            "endDate": end.isoformat(),
            "type": search_type,
            "dataState": "final",
            "aggregationType": aggregation_for(search_type, dimensions),
            "rowLimit": row_limit,
            "startRow": len(rows),
        }
        if dimensions:
            body["dimensions"] = dimensions
        response = query_once(token, site_url, body)
        batch = list(response.get("rows", []))
        rows.extend(batch)
        page_count += 1
        metadata.update(response.get("metadata", {}))
        response_aggregation_type = response.get("responseAggregationType")
        if not dimensions or not batch:
            break
        if page_count >= max_pages:
            truncated_by_cap = True
            break

    return {
        "status": "partial" if truncated_by_cap else "complete",
        "dimensions": dimensions,
        "aggregation_type": response_aggregation_type,
        "rows": rows,
        "row_count": len(rows),
        "pages_fetched": page_count,
        "truncated_by_page_cap": truncated_by_cap,
        "metadata": metadata,
    }


def days_inclusive(start: date, end: date) -> list[date]:
    return [start + timedelta(days=offset) for offset in range((end - start).days + 1)]


def aggregate_dimension_rows(rows: list[dict[str, Any]]) -> list[dict[str, Any]]:
    aggregates: dict[tuple[str, ...], dict[str, Any]] = {}
    for row in rows:
        key = tuple(str(value) for value in row.get("keys", []))
        clicks = float(row.get("clicks", 0.0) or 0.0)
        impressions = float(row.get("impressions", 0.0) or 0.0)
        position = row.get("position")
        aggregate = aggregates.setdefault(
            key,
            {
                "keys": list(key),
                "clicks": 0.0,
                "impressions": 0.0,
                "position_weight": 0.0,
                "position_impressions": 0.0,
                "days_present": set(),
            },
        )
        aggregate["clicks"] += clicks
        aggregate["impressions"] += impressions
        if position is not None and impressions > 0:
            aggregate["position_weight"] += float(position) * impressions
            aggregate["position_impressions"] += impressions
        source_date = row.get("_source_date")
        if source_date:
            aggregate["days_present"].add(str(source_date))

    output: list[dict[str, Any]] = []
    for aggregate in aggregates.values():
        impressions = aggregate["impressions"]
        item: dict[str, Any] = {
            "keys": aggregate["keys"],
            "clicks": aggregate["clicks"],
            "impressions": impressions,
            "ctr": aggregate["clicks"] / impressions if impressions else 0.0,
            "days_present": len(aggregate["days_present"]),
        }
        if aggregate["position_impressions"]:
            item["position"] = (
                aggregate["position_weight"] / aggregate["position_impressions"]
            )
        output.append(item)
    output.sort(key=lambda item: item["clicks"], reverse=True)
    return output


def query_family_daily(
    token: str,
    site_url: str,
    *,
    start: date,
    end: date,
    search_type: str,
    dimensions: list[str],
    row_limit: int,
    max_pages: int,
) -> dict[str, Any]:
    source_rows: list[dict[str, Any]] = []
    aggregation_types: set[str] = set()
    failed_days: list[dict[str, str]] = []
    truncated_days: list[str] = []
    total_pages = 0
    successful_days = 0

    for index, query_date in enumerate(days_inclusive(start, end)):
        try:
            result = query_family(
                token,
                site_url,
                start=query_date,
                end=query_date,
                search_type=search_type,
                dimensions=dimensions,
                row_limit=row_limit,
                max_pages=max_pages,
            )
        except SafeError as exc:
            if index == 0:
                raise
            failed_days.append({"date": query_date.isoformat(), "reason": str(exc)})
            continue

        successful_days += 1
        total_pages += int(result["pages_fetched"])
        if result.get("aggregation_type"):
            aggregation_types.add(str(result["aggregation_type"]))
        if result.get("truncated_by_page_cap"):
            truncated_days.append(query_date.isoformat())
        for row in result["rows"]:
            source_rows.append({**row, "_source_date": query_date.isoformat()})

    aggregated_rows = aggregate_dimension_rows(source_rows)
    status = "partial" if failed_days or truncated_days else "complete"
    return {
        "status": status,
        "dimensions": dimensions,
        "aggregation_types": sorted(aggregation_types),
        "source_granularity": "daily",
        "rows": aggregated_rows,
        "row_count": len(aggregated_rows),
        "source_row_count": len(source_rows),
        "days_expected": (end - start).days + 1,
        "days_succeeded": successful_days,
        "failed_days": failed_days,
        "truncated_days": truncated_days,
        "pages_fetched": total_pages,
    }


def sitemap_snapshot(token: str, site_url: str) -> dict[str, Any]:
    encoded = parse.quote(site_url, safe="")
    response = http_json(f"{API_ROOT}/sites/{encoded}/sitemaps", token=token)
    sanitized: list[dict[str, Any]] = []
    for item in response.get("sitemap", []):
        sanitized.append(
            {
                "path": item.get("path"),
                "type": item.get("type"),
                "is_pending": item.get("isPending"),
                "is_sitemaps_index": item.get("isSitemapsIndex"),
                "last_submitted": item.get("lastSubmitted"),
                "last_downloaded": item.get("lastDownloaded"),
                "warnings": item.get("warnings"),
                "errors": item.get("errors"),
                "contents": [
                    {"type": content.get("type"), "submitted": content.get("submitted")}
                    for content in item.get("contents", [])
                ],
            }
        )
    return {"sitemaps": sanitized, "count": len(sanitized)}


def validate_output_path(output: Path, env_path: Path) -> None:
    if output.resolve() == env_path.resolve():
        raise SafeError("output path must not overwrite the client .env")
    if output.suffix.lower() != ".json":
        raise SafeError("temporary extraction output must use a .json filename")


def atomic_write_json(path: Path, payload: dict[str, Any]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    fd, temp_name = tempfile.mkstemp(prefix=f".{path.name}.", dir=path.parent)
    try:
        with os.fdopen(fd, "w", encoding="utf-8") as handle:
            json.dump(payload, handle, indent=2, ensure_ascii=False)
            handle.write("\n")
        os.replace(temp_name, path)
    finally:
        if os.path.exists(temp_name):
            os.unlink(temp_name)


def main() -> int:
    args = parse_args()
    env_path = Path(args.env_file).resolve()
    output_path = Path(args.output).resolve()
    try:
        if not env_path.is_file():
            raise SafeError("client project .env not found")
        validate_output_path(output_path, env_path)
        if not 1 <= args.row_limit <= 25000:
            raise SafeError("--row-limit must be between 1 and 25000")
        if not 1 <= args.max_pages <= 20:
            raise SafeError("--max-pages must be between 1 and 20")

        selected_types = [item.strip() for item in args.types.split(",") if item.strip()]
        unknown = sorted(set(selected_types) - set(SEARCH_TYPES))
        if unknown:
            raise SafeError("unsupported Search Console type: " + ", ".join(unknown))

        values = parse_dotenv(env_path)
        token, auth_method = get_access_token(values)
        site_url, permission_level = choose_site(token, values, args.site_url)
        report_date = (
            date.fromisoformat(args.report_date)
            if args.report_date
            else datetime.now(PACIFIC).date()
        )
        if args.end_date:
            current_end = date.fromisoformat(args.end_date)
            finalization = {
                "probe_start": None,
                "probe_end": None,
                "first_incomplete_date": None,
                "latest_finalized_date": current_end.isoformat(),
                "selection": "explicit_end_date",
            }
        else:
            current_end, finalization = discover_latest_finalized(token, site_url, report_date)
        if current_end >= report_date:
            raise SafeError("latest finalized date must be earlier than the Pacific report date")

        current_start = current_end - timedelta(days=29)
        previous_end = current_start - timedelta(days=1)
        previous_start = previous_end - timedelta(days=29)
        periods = {
            "current": {"start": current_start, "end": current_end},
            "previous": {"start": previous_start, "end": previous_end},
        }

        data: dict[str, Any] = {}
        failures: list[dict[str, str]] = []
        for search_type in selected_types:
            type_payload: dict[str, Any] = {}
            for period_name, window in periods.items():
                period_payload: dict[str, Any] = {}
                for family_name, dimensions in FAMILIES.items():
                    try:
                        query_function = (
                            query_family_daily
                            if args.detail_mode == "daily"
                            and family_name in DAILY_DETAIL_FAMILIES
                            else query_family
                        )
                        family_result = query_function(
                            token,
                            site_url,
                            start=window["start"],
                            end=window["end"],
                            search_type=search_type,
                            dimensions=dimensions,
                            row_limit=args.row_limit,
                            max_pages=args.max_pages,
                        )
                        period_payload[family_name] = family_result
                        if family_result.get("status") == "partial":
                            failed_day_count = len(family_result.get("failed_days", []))
                            capped_day_count = len(family_result.get("truncated_days", []))
                            period_cap = bool(family_result.get("truncated_by_page_cap"))
                            failures.append(
                                {
                                    "search_type": search_type,
                                    "period": period_name,
                                    "family": family_name,
                                    "reason": (
                                        f"partial extraction: {failed_day_count} failed days; "
                                        f"{capped_day_count} pagination-capped days; "
                                        f"period cap reached={period_cap}"
                                    ),
                                }
                            )
                    except SafeError as exc:
                        period_payload[family_name] = {
                            "status": "unavailable",
                            "reason": str(exc),
                            "rows": [],
                            "row_count": 0,
                        }
                        failures.append(
                            {
                                "search_type": search_type,
                                "period": period_name,
                                "family": family_name,
                                "reason": str(exc),
                            }
                        )
                type_payload[period_name] = period_payload
            data[search_type] = type_payload

        try:
            sitemaps = sitemap_snapshot(token, site_url)
        except SafeError as exc:
            sitemaps = {"status": "unavailable", "reason": str(exc), "sitemaps": []}
            failures.append(
                {
                    "search_type": "not_applicable",
                    "period": "snapshot",
                    "family": "sitemaps",
                    "reason": str(exc),
                }
            )

        payload = {
            "schema_version": 1,
            "generated_at": datetime.now(PACIFIC).isoformat(),
            "date_timezone": "America/Los_Angeles",
            "report_date": report_date.isoformat(),
            "property": {"site_url": site_url, "permission_level": permission_level},
            "authentication_method": auth_method,
            "finalization": finalization,
            "periods": {
                name: {
                    "start": window["start"].isoformat(),
                    "end": window["end"].isoformat(),
                }
                for name, window in periods.items()
            },
            "search_types": selected_types,
            "detail_mode": args.detail_mode,
            "data": data,
            "sitemaps": sitemaps,
            "failures": failures,
            "limitations": [
                "Search Analytics returns top rows and can omit anonymized or low-volume queries.",
                "Dimension row sums may be lower than no-dimension property totals.",
                "Sitemap indexed counts are excluded because the API field is deprecated.",
            ],
        }
        atomic_write_json(output_path, payload)
        print(
            json.dumps(
                {
                    "status": "complete",
                    "output": str(output_path),
                    "property": site_url,
                    "current_period": payload["periods"]["current"],
                    "previous_period": payload["periods"]["previous"],
                    "failed_query_families": len(failures),
                },
                indent=2,
            )
        )
        return 0
    except (SafeError, ValueError) as exc:
        print(json.dumps({"status": "blocked", "reason": str(exc)}, indent=2), file=sys.stderr)
        return 1


if __name__ == "__main__":
    raise SystemExit(main())
