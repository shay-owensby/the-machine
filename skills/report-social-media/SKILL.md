---
name: report-social-media
description: Pull read-only Zernio social analytics and account insights, compare the last 30 complete days with the immediately preceding 30 days, and deliver matching Markdown and self-contained HTML reports with tables, accessible charts, every available KPI, and prioritized next steps. Use for one-off or recurring Zernio social-media performance reporting; do not use to publish content, reply to messages, change campaigns, or alter account configuration.
---

# Social Media Report

Produce an evidence-backed, read-only report across the Zernio profiles and connected social accounts in the client project.

## Required resources

Before reading credentials, calling Zernio, analyzing data, or writing a report, read:

- [references/data-contract.md](references/data-contract.md) for date logic, KPI calculations, comparison rules, security, and analytical standards.
- [references/zernio-query-plan.md](references/zernio-query-plan.md) for the required and conditional API query families.
- [references/report-template.md](references/report-template.md) for the mandatory output structure. Copy its headings and canonical KPI rows exactly.
- [references/html-output.md](references/html-output.md) for the shared CSS, visualization requirements, chart-directive schema, and Markdown-to-HTML build procedure.

## Workflow

1. Work from the client project root. Read the Zernio key or token and any configured reporting-scope identifiers from `./.env` without printing, logging, committing, or copying credentials. Prefer `ZERNIO_API_KEY`; recognize the documented credential and scope variables in the data contract. `scripts/zernio_get.py` is the safe read-only request helper when no installed Zernio SDK is already available.
2. Use only authenticated `GET` requests against the Zernio API. Inventory accessible profiles and accounts to validate access and health. Choose scope using the data-contract precedence: an explicit user filter first, then configured `ZERNIO_PROFILE_ID` / `ZERNIO_ACCOUNT_IDS`, then live discovery. When configured IDs exist, use them as the client scope after validation; do not rediscover ownership or silently widen to other accessible profiles. If a configured ID is inaccessible, stale, or inconsistent, report the configuration problem rather than substituting another account.
3. Determine the reporting time zone using the precedence in the data contract. Run `scripts/report_dates.py --timezone <iana-time-zone> --create-dir` to calculate two adjacent, non-overlapping 30-day windows and the required destination.
4. Follow the query plan. Pull every page and every applicable account-level endpoint for the connected platforms. Include all numeric KPI fields returned by Zernio, not only the canonical scorecard. Record unsupported, permission-gated, delayed, pending, or unavailable fields as `N/A — <reason>`; never convert them to zero.
5. Reconcile totals before analysis. Keep account-level, post-level, inbox, and paid-media scopes distinct. Recalculate additive totals from raw rows when appropriate; never sum reach, followers, unique people, rates, averages, or time-based metrics across accounts or posts unless the API defines that aggregation.
6. Compare current with previous using both absolute and relative change. Analyze platform, account, content, format, timing, audience/follower, community/inbox, and paid performance wherever data exists. Separate observations from hypotheses. Quantify every strength, weakness, and action.
7. Fill every section of the strict template. Do not delete, rename, or reorder headings or canonical KPI rows. Add every additional numeric metric returned by Zernio to the applicable platform/account table and to `All Additional KPI Fields Returned by Zernio` so the report is exhaustive.
8. Add the chart directives required by `references/html-output.md` under the most relevant existing headings. Prefer an executive KPI-change chart, a daily reach or engagement trend, and a platform, account, format, or content-type comparison. Every plotted value must reconcile to a nearby table.
9. Save the Markdown report to `./analytics-insights/social-media/YYYY/YYYYmmdd-social-media-report.md`, using the report-generation date in the chosen reporting time zone for `YYYY` and the filename date. Run `scripts/build_report_outputs.py <markdown-report-path>` to generate its SVG chart assets and same-basename HTML companion. Do not leave raw API responses or secret-bearing files in the report tree.
10. Run `scripts/validate_report.py <markdown-report-path>` and correct every failure. Return clickable links to both the Markdown and HTML files and state the current and previous comparison periods.

## Boundaries

- Reporting is read-only. It does not authorize posting, syncing external posts with a mutation, replying, editing ads, reconnecting accounts, changing scopes, or changing Zernio configuration.
- Do not expose `.env` contents or credentials in commands, logs, intermediate files, or reports. Never place a token directly in a command argument.
- Do not call a missing, invalid, or permission-gated metric zero. Preserve `N/A` with a reason and identify the concrete remediation when known.
- Do not claim causation, invent benchmarks, fabricate goals, or project uplift. Label hypotheses and say how to test them.
- Do not rank small samples as decisive. Flag fewer than five posts in either period for an account, format, or platform as low confidence.
