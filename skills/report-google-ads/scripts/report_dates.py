#!/usr/bin/env python3
"""Calculate fixed Google Ads reporting windows and required output paths."""

from __future__ import annotations

import argparse
import json
from datetime import date, datetime, timedelta
from pathlib import Path
from zoneinfo import ZoneInfo, ZoneInfoNotFoundError


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser()
    parser.add_argument("--timezone", required=True, help="IANA Google Ads account time zone")
    parser.add_argument(
        "--as-of",
        help="Report date in YYYY-MM-DD; defaults to today in the account time zone",
    )
    parser.add_argument("--root", default=".", help="Project root for the report export")
    parser.add_argument("--create-dir", action="store_true", help="Create the year directory")
    return parser.parse_args()


def main() -> int:
    args = parse_args()
    try:
        account_tz = ZoneInfo(args.timezone)
    except ZoneInfoNotFoundError as exc:
        raise SystemExit(f"Unknown IANA time zone: {args.timezone}") from exc

    report_date = date.fromisoformat(args.as_of) if args.as_of else datetime.now(account_tz).date()
    current_end = report_date - timedelta(days=1)
    current_start = current_end - timedelta(days=29)
    previous_end = current_start - timedelta(days=1)
    previous_start = previous_end - timedelta(days=29)

    output_dir = Path(args.root) / "analytics-insights" / "google-ads" / str(report_date.year)
    if args.create_dir:
        output_dir.mkdir(parents=True, exist_ok=True)
    markdown_output_path = output_dir / f"{report_date:%Y%m%d}-google-ads-report.md"
    html_output_path = markdown_output_path.with_suffix(".html")

    result = {
        "account_timezone": args.timezone,
        "report_date": report_date.isoformat(),
        "current_start": current_start.isoformat(),
        "current_end": current_end.isoformat(),
        "previous_start": previous_start.isoformat(),
        "previous_end": previous_end.isoformat(),
        "output_path": str(markdown_output_path),
        "markdown_output_path": str(markdown_output_path),
        "html_output_path": str(html_output_path),
    }
    print(json.dumps(result, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
