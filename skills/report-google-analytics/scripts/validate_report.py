#!/usr/bin/env python3
"""Validate the strict GA4 Markdown report structure and destination."""

from __future__ import annotations

import argparse
import re
from datetime import datetime
from pathlib import Path

from validate_report_bundle import validate_report_bundle


PLACEHOLDER_RE = re.compile(r"\{\{[^{}\n]+\}\}")
PATH_RE = re.compile(
    r"(?:^|/)analytics-insights/google-analytics/"
    r"(?P<year>\d{4})/(?P<date>\d{8})-google-analytics-report\.md$"
)
HEADING_RE = re.compile(r"^#{1,6} .+$", re.MULTILINE)
REQUIRED_KPIS = (
    "Total users",
    "Active users",
    "New users",
    "1-day active users",
    "7-day active users",
    "28-day active users",
    "DAU / WAU",
    "DAU / MAU",
    "WAU / MAU",
    "Sessions",
    "Engaged sessions",
    "Engagement rate",
    "Bounce rate",
    "Average session duration",
    "Sessions per user",
    "Views",
    "Views per session",
    "Views per user",
    "Event count",
    "Events per session",
    "Event count per user",
    "User engagement duration",
    "Scrolled users",
    "Key events",
    "Session key event rate",
    "User key event rate",
    "Total revenue",
    "Purchase revenue",
    "Gross purchase revenue",
    "Total ad revenue",
    "Transactions",
    "Ecommerce purchases",
    "Total purchasers",
    "First-time purchasers",
    "First-time purchaser rate",
    "Transactions per purchaser",
    "Average purchase revenue",
    "Average purchase revenue per user",
    "Average purchase revenue per paying user",
    "Average revenue per user",
    "Refund amount",
    "Items viewed",
    "Items added to cart",
    "Items checked out",
    "Items purchased",
    "Cart-to-view rate",
    "Purchase-to-view rate",
    "Advertiser ad impressions",
    "Advertiser ad clicks",
    "Advertiser ad cost",
    "Advertiser ad cost per click",
    "Advertiser ad cost per key event",
    "Return on ad spend",
    "Organic Google Search impressions",
    "Organic Google Search clicks",
    "Organic Google Search click-through rate",
    "Organic Google Search average position",
    "Crash-affected users",
    "Crash-free users rate",
)
REQUIRED_QUALITY_LABELS = (
    "API response metadata",
    "Unique-count approximation",
    "High-cardinality `(other)` data loss",
    "Metric access restrictions",
)


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser()
    parser.add_argument("report", help="Generated report Markdown file")
    parser.add_argument(
        "--template",
        default=str(
            Path(__file__).resolve().parent.parent
            / "references"
            / "report-template.md"
        ),
        help="Strict report template",
    )
    return parser.parse_args()


def main() -> int:
    args = parse_args()
    report_path = Path(args.report).resolve()
    template_path = Path(args.template).resolve()
    errors: list[str] = []

    if not report_path.is_file():
        raise SystemExit(f"Report not found: {report_path}")
    if not template_path.is_file():
        raise SystemExit(f"Template not found: {template_path}")

    report_text = report_path.read_text(encoding="utf-8")
    template_text = template_path.read_text(encoding="utf-8")
    errors.extend(validate_report_bundle(report_path, report_text))
    path_match = PATH_RE.search(report_path.as_posix())
    if not path_match:
        errors.append(
            "report path must match analytics-insights/"
            "google-analytics/YYYY/YYYYmmdd-google-analytics-report.md"
        )
    else:
        filename_date = path_match.group("date")
        if path_match.group("year") != filename_date[:4]:
            errors.append("year directory does not match the filename year")
        try:
            datetime.strptime(filename_date, "%Y%m%d")
        except ValueError:
            errors.append("filename date is not a valid calendar date")

    if HEADING_RE.findall(report_text) != HEADING_RE.findall(template_text):
        errors.append("headings differ from the strict template or are out of order")

    unresolved = sorted(set(PLACEHOLDER_RE.findall(report_text)))
    if unresolved:
        errors.append("unresolved placeholders: " + ", ".join(unresolved[:12]))

    scorecard_start = report_text.find("## 3. Complete KPI Scorecard")
    scorecard_end = report_text.find("## 4. Acquisition Performance")
    scorecard_text = (
        report_text[scorecard_start:scorecard_end]
        if 0 <= scorecard_start < scorecard_end
        else ""
    )
    for kpi in REQUIRED_KPIS:
        if f"| {kpi} |" not in scorecard_text:
            errors.append(f"required KPI row missing: {kpi}")

    for label in REQUIRED_QUALITY_LABELS:
        if f"**{label}:**" not in report_text:
            errors.append(f"required data-quality disclosure missing: {label}")

    if errors:
        print("Report validation failed:")
        for error in errors:
            print(f"- {error}")
        return 1

    print(f"Report validation passed: {report_path}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
