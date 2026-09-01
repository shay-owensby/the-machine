#!/usr/bin/env python3
"""Calculate finalized Search Console periods and required report paths."""

from __future__ import annotations

import argparse
import json
from datetime import date, datetime, timedelta
from pathlib import Path
from zoneinfo import ZoneInfo


PACIFIC = ZoneInfo("America/Los_Angeles")


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser()
    parser.add_argument(
        "--report-date",
        help="Report date in YYYY-MM-DD; defaults to today in Pacific Time",
    )
    parser.add_argument(
        "--latest-finalized-date",
        help="Latest complete finalized Search Console date in YYYY-MM-DD",
    )
    parser.add_argument(
        "--first-incomplete-date",
        help="First incomplete Search Console date; current period ends the day before",
    )
    parser.add_argument("--root", default=".", help="Client project root")
    parser.add_argument("--create-dir", action="store_true", help="Create the year directory")
    return parser.parse_args()


def main() -> int:
    args = parse_args()
    report_date = (
        date.fromisoformat(args.report_date)
        if args.report_date
        else datetime.now(PACIFIC).date()
    )
    if args.latest_finalized_date and args.first_incomplete_date:
        raise SystemExit("Use only one of --latest-finalized-date or --first-incomplete-date")

    yesterday = report_date - timedelta(days=1)
    if args.latest_finalized_date:
        current_end = date.fromisoformat(args.latest_finalized_date)
    elif args.first_incomplete_date:
        current_end = date.fromisoformat(args.first_incomplete_date) - timedelta(days=1)
    else:
        current_end = yesterday

    if current_end > yesterday:
        raise SystemExit("Latest finalized date cannot be later than yesterday in Pacific Time")

    current_start = current_end - timedelta(days=29)
    previous_end = current_start - timedelta(days=1)
    previous_start = previous_end - timedelta(days=29)
    output_dir = Path(args.root) / "analytics-insights" / "google-search-console" / str(report_date.year)
    if args.create_dir:
        output_dir.mkdir(parents=True, exist_ok=True)
    markdown_output_path = output_dir / f"{report_date:%Y%m%d}-google-search-console-report.md"
    html_output_path = markdown_output_path.with_suffix(".html")

    result = {
        "date_timezone": "America/Los_Angeles",
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
