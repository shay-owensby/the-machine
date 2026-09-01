#!/usr/bin/env python3
"""Calculate fixed social reporting windows and required output paths."""

from __future__ import annotations

import argparse
import json
from datetime import date, datetime, timedelta
from pathlib import Path
from zoneinfo import ZoneInfo, ZoneInfoNotFoundError


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser()
    parser.add_argument("--timezone", required=True, help="IANA reporting time zone")
    parser.add_argument("--as-of", help="Report date in YYYY-MM-DD; defaults to today in the reporting time zone")
    parser.add_argument("--root", default=".", help="Client project root for the report export")
    parser.add_argument("--create-dir", action="store_true", help="Create the required year directory")
    return parser.parse_args()


def main() -> int:
    args = parse_args()
    try:
        report_tz = ZoneInfo(args.timezone)
    except ZoneInfoNotFoundError as exc:
        raise SystemExit(f"Unknown IANA time zone: {args.timezone}") from exc

    try:
        report_date = date.fromisoformat(args.as_of) if args.as_of else datetime.now(report_tz).date()
    except ValueError as exc:
        raise SystemExit("--as-of must be a valid YYYY-MM-DD date") from exc

    current_end = report_date - timedelta(days=1)
    current_start = current_end - timedelta(days=29)
    previous_end = current_start - timedelta(days=1)
    previous_start = previous_end - timedelta(days=29)

    output_dir = Path(args.root) / "analytics-insights" / "social-media" / str(report_date.year)
    if args.create_dir:
        output_dir.mkdir(parents=True, exist_ok=True)
    markdown_output_path = output_dir / f"{report_date:%Y%m%d}-social-media-report.md"
    html_output_path = markdown_output_path.with_suffix(".html")

    result = {
        "report_timezone": args.timezone,
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
