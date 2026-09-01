#!/usr/bin/env python3
"""Validate the strict Mailchimp Markdown report structure and destination."""

from __future__ import annotations

import argparse
import re
from pathlib import Path


PLACEHOLDER_RE = re.compile(r"\{\{[A-Z0-9_]+\}\}")
PATH_RE = re.compile(
    r"(?:^|/)analytics-insights/mailchimp/(?P<year>\d{4})/"
    r"(?P<date>\d{8})-mailchimp-report\.md$"
)
HEADING_RE = re.compile(r"^#{1,6} .+$", re.MULTILINE)
REQUIRED_KPIS = (
    "Campaigns sent",
    "Campaign frequency",
    "Emails sent",
    "Average recipients per campaign",
    "Successful deliveries",
    "Delivery rate",
    "Total bounces",
    "Bounce rate",
    "Hard bounces",
    "Soft bounces",
    "Syntax errors",
    "Total opens",
    "Proxy-excluded total opens",
    "Unique opens",
    "Proxy-excluded unique opens",
    "Open rate",
    "Proxy-excluded open rate",
    "Total clicks",
    "Unique clicks",
    "Unique subscriber clicks",
    "Click rate",
    "Click-to-open rate (CTOR)",
    "Proxy-excluded CTOR",
    "Forwards",
    "Forward opens",
    "Campaign-attributed unsubscribes",
    "Unsubscribe rate",
    "Abuse complaints",
    "Complaint rate",
    "Audience subscribes",
    "Audience unsubscribes",
    "Other audience adds",
    "Other audience removes",
    "Hard-bounce removals",
    "Net audience change",
    "Audience growth rate",
    "Active audience size",
    "Orders",
    "Gross sales / total spent",
    "Revenue",
    "Average order value",
    "Revenue per delivered email",
    "Revenue per 1,000 delivered",
    "Click-to-order rate",
)


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser()
    parser.add_argument("report", help="Generated Mailchimp report Markdown file")
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

    path_match = PATH_RE.search(report_path.as_posix())
    if not path_match:
        errors.append(
            "report path must match analytics-insights/"
            "mailchimp/YYYY/YYYYmmdd-mailchimp-report.md"
        )
    elif path_match.group("year") != path_match.group("date")[:4]:
        errors.append("year directory does not match the filename year")

    if HEADING_RE.findall(report_text) != HEADING_RE.findall(template_text):
        errors.append("headings differ from the strict template or are out of order")

    unresolved = sorted(set(PLACEHOLDER_RE.findall(report_text)))
    if unresolved:
        errors.append("unresolved placeholders: " + ", ".join(unresolved[:12]))

    for kpi in REQUIRED_KPIS:
        if f"| {kpi} |" not in report_text:
            errors.append(f"required KPI row missing: {kpi}")

    if "All Additional Numeric KPI Fields Returned by Mailchimp" not in report_text:
        errors.append("additional Mailchimp KPI inventory is missing")

    if errors:
        print("Report validation failed:")
        for error in errors:
            print(f"- {error}")
        return 1

    print(f"Report validation passed: {report_path}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
