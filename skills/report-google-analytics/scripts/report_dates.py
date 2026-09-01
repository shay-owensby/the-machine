#!/usr/bin/env python3
"""Calculate fixed GA4 reporting windows and required output paths."""

from __future__ import annotations

import argparse
import json
from datetime import date, datetime, timedelta
from pathlib import Path
from zoneinfo import ZoneInfo, ZoneInfoNotFoundError


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser()
    parser.add_argument("--timezone", required=True, help="IANA GA4 property time zone")
    parser.add_argument("--as-of", help="Report date in YYYY-MM-DD; defaults to today in the property time zone")
    parser.add_argument("--root", default=".", help="Client project root for the report export")
    parser.add_argument("--create-dir", action="store_true", help="Create the year directory")
    return parser.parse_args()


def main() -> int:
    args = parse_args()
    try:
        property_tz = ZoneInfo(args.timezone)
    except ZoneInfoNotFoundError as exc:
        raise SystemExit(f"Unknown IANA time zone: {args.timezone}") from exc

    try:
        report_date = date.fromisoformat(args.as_of) if args.as_of else datetime.now(property_tz).date()
    except ValueError as exc:
        raise SystemExit("--as-of must be a valid YYYY-MM-DD date") from exc

    current_end = report_date - timedelta(days=1)
    current_start = current_end - timedelta(days=29)
    previous_end = current_start - timedelta(days=1)
    previous_start = previous_end - timedelta(days=29)

    output_dir = Path(args.root) / "analytics-insights" / "google-analytics" / str(report_date.year)
    if args.create_dir:
        output_dir.mkdir(parents=True, exist_ok=True)
    markdown_output_path = output_dir / f"{report_date:%Y%m%d}-google-analytics-report.md"
    html_output_path = markdown_output_path.with_suffix(".html")

    result = {
        "property_timezone": args.timezone,
        "report_date": report_date.isoformat(),
        "current_start": current_start.isoformat(),
        "current_end": current_end.isoformat(),
        "previous_start": previous_start.isoformat(),
        "previous_end": previous_end.isoformat(),
        "current_days": (current_end - current_start).days + 1,
        "previous_days": (previous_end - previous_start).days + 1,
        "output_path": str(markdown_output_path),
        "markdown_output_path": str(markdown_output_path),
        "html_output_path": str(html_output_path),
    }
    print(json.dumps(result, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
