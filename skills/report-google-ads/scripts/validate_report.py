#!/usr/bin/env python3
"""Validate the strict Google Ads Markdown report structure and destination."""

from __future__ import annotations

import argparse
import re
from pathlib import Path

from validate_report_bundle import validate_report_bundle


PLACEHOLDER_RE = re.compile(r"\{\{[A-Z0-9_]+\}\}")
PATH_RE = re.compile(
    r"(?:^|/)analytics-insights/google-ads/(?P<year>\d{4})/"
    r"(?P<date>\d{8})-google-ads-report\.md$"
)
HEADING_RE = re.compile(r"^#{1,6} .+$", re.MULTILINE)
REQUIRED_KPIS = (
    "| Impressions |",
    "| Clicks |",
    "| Spend |",
    "| CTR |",
    "| Average CPC |",
    "| Conversions |",
    "| Conversion rate |",
    "| Cost per conversion / CPA |",
    "| Conversion value |",
    "| ROAS |",
    "| Search impression share |",
    "| Video views |",
    "| Phone calls |",
    "| Orders |",
)


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser()
    parser.add_argument("report", help="Generated report Markdown file")
    parser.add_argument(
        "--template",
        default=str(Path(__file__).resolve().parent.parent / "references" / "report-template.md"),
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
        errors.append("report path does not match analytics-insights/google-ads/YYYY/YYYYmmdd-google-ads-report.md")
    elif path_match.group("year") != path_match.group("date")[:4]:
        errors.append("year directory does not match the filename year")

    expected_headings = HEADING_RE.findall(template_text)
    actual_headings = HEADING_RE.findall(report_text)
    if actual_headings != expected_headings:
        errors.append("headings differ from the strict template or are out of order")

    unresolved = sorted(set(PLACEHOLDER_RE.findall(report_text)))
    if unresolved:
        errors.append("unresolved placeholders: " + ", ".join(unresolved[:10]))

    for kpi in REQUIRED_KPIS:
        if kpi not in report_text:
            errors.append(f"required KPI row missing: {kpi.strip('| ')}")

    if errors:
        print("Report validation failed:")
        for error in errors:
            print(f"- {error}")
        return 1

    print(f"Report validation passed: {report_path}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
