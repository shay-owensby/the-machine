#!/usr/bin/env python3
"""Validate the strict Search Console Markdown report structure and path."""

from __future__ import annotations

import argparse
import re
from pathlib import Path

from validate_report_bundle import validate_report_bundle


PLACEHOLDER_RE = re.compile(r"\{\{[A-Z0-9_]+\}\}")
PATH_RE = re.compile(
    r"(?:^|/)analytics-insights/google-search-console/(?P<year>\d{4})/"
    r"(?P<date>\d{8})-google-search-console-report\.md$"
)
HEADING_RE = re.compile(r"^#{1,6} .+$", re.MULTILINE)
REQUIRED_KPIS = (
    "| Clicks |",
    "| Impressions |",
    "| CTR |",
    "| Average position |",
)
REQUIRED_SEARCH_TYPES = (
    "| Web |",
    "| Image |",
    "| Video |",
    "| News |",
    "| Discover |",
    "| Google News |",
)
REQUIRED_LIMITATIONS = (
    "Finalization and freshness",
    "Query anonymization and row truncation",
    "Daily query/page extraction coverage",
    "Dimension-to-total reconciliation",
    "Business-outcome limitation",
)


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser()
    parser.add_argument("report", help="Generated report Markdown file")
    parser.add_argument(
        "--template",
        default=str(
            Path(__file__).resolve().parent.parent / "references" / "report-template.md"
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
            "report path does not match analytics-insights/"
            "google-search-console/YYYY/YYYYmmdd-google-search-console-report.md"
        )
    elif path_match.group("year") != path_match.group("date")[:4]:
        errors.append("year directory does not match the filename year")

    expected_headings = HEADING_RE.findall(template_text)
    actual_headings = HEADING_RE.findall(report_text)
    if actual_headings != expected_headings:
        errors.append("headings differ from the strict template or are out of order")

    unresolved = sorted(set(PLACEHOLDER_RE.findall(report_text)))
    if unresolved:
        errors.append("unresolved placeholders: " + ", ".join(unresolved[:10]))

    for marker in (*REQUIRED_KPIS, *REQUIRED_SEARCH_TYPES):
        if marker not in report_text:
            errors.append(f"required row missing: {marker.strip('| ')}")
    for marker in REQUIRED_LIMITATIONS:
        if marker not in report_text:
            errors.append(f"required limitation missing: {marker}")

    if "N/A —" not in report_text and "N/A" in report_text:
        errors.append("use 'N/A — <reason>' rather than an unexplained N/A")

    if errors:
        print("Report validation failed:")
        for issue in errors:
            print(f"- {issue}")
        return 1

    print(f"Report validation passed: {report_path}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
