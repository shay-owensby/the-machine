---
name: report-google-ads
description: Pull read-only Google Ads API performance data, compare the last 30 complete days with the immediately preceding 30 days, and deliver matching Markdown and self-contained HTML reports with tables, accessible charts, KPI scorecards, and prioritized next steps. Use for recurring or one-off Google Ads performance reporting; do not use to change campaigns.
---

# Google Ads Report

Produce an evidence-backed, read-only Google Ads performance report. Google Cloud provides the OAuth project and API enablement; use the Google Ads API and GAQL for the advertising data.

## Required resources

Before querying or writing the report, read:

- [references/data-contract.md](references/data-contract.md) for authentication, date rules, queries, KPI calculations, validation, and analysis standards.
- [references/gaql-query-plan.md](references/gaql-query-plan.md) while pulling data for the minimum query set and campaign-type diagnostics.
- [references/report-template.md](references/report-template.md) for the mandatory report structure. Copy its structure exactly into the deliverable.
- [references/html-output.md](references/html-output.md) for the shared CSS, visualization requirements, chart-directive schema, and Markdown-to-HTML build procedure.

## Workflow

1. Treat the client project root `./.env` as the authoritative source for Google Cloud OAuth, Google Ads API, customer, and manager-account configuration. Run `scripts/check_env_config.py --env-file ./.env` before attempting authentication. Load values privately with a dotenv parser; never shell-source, reveal, echo, log, or write them into the report. Do not ask the user for credentials that are present in this file.
2. Use the `.env` configuration to authenticate with read access, then identify or verify the Google Ads customer ID, manager/login customer ID when applicable, account time zone, and currency. If the file is absent or a required value is empty, state only the missing configuration category and stop rather than inventing data.
3. Use `scripts/report_dates.py --timezone <account-time-zone> --create-dir` to calculate the reporting windows and destination. Unless the user explicitly requests another convention, use the latest 30 complete calendar days ending yesterday in the account time zone and compare them with the immediately preceding 30 complete days.
4. Pull account, campaign, conversion, budget, bidding, device, network, geographic, demographic, keyword/search-term, ad/asset, and landing-page data as applicable. Query resource families separately when GAQL field compatibility requires it. Preserve unavailable metrics as `N/A` with a reason.
5. Normalize micros, ratios, currency, missing values, and campaign-type-specific metrics according to the data contract. Reconcile totals and guard against duplicated aggregates caused by segmentation.
6. Compare current and previous periods with absolute and percentage changes. Separate observed facts from interpretations. Base strengths, weaknesses, and recommendations on quantified evidence, materiality, business goals, and campaign type.
7. Fill every section and table in the strict template. Do not delete, rename, or reorder headings or KPI rows. Use `N/A — <reason>` where data is unsupported or unavailable. Do not leave placeholders.
8. Add the chart directives required by `references/html-output.md` under the most relevant existing headings. Prefer an executive KPI-change chart, a daily performance trend, and a campaign or segment comparison. Every plotted value must reconcile to a nearby table.
9. Save the Markdown report to `./analytics-insights/google-ads/YYYY/YYYYmmdd-google-ads-report.md`, where `YYYY` and the filename date use the report-generation date in the account time zone. Run `scripts/build_report_outputs.py <markdown-report-path>` to generate its SVG chart assets and same-basename HTML companion.
10. Run `scripts/validate_report.py <markdown-report-path>` and correct every failure before delivery. Return clickable links to both the Markdown and HTML files and a concise statement of the period covered.

## Boundaries

- Treat all Google Ads access as read-only. A reporting request does not authorize campaign, budget, bid, targeting, creative, conversion, or account changes.
- Treat `./.env` as sensitive client data. Read only the keys required for Google Ads reporting and never copy the file into the skill, report folder, logs, or temporary extraction artifacts.
- Do not claim causation from period-over-period correlations. Label hypotheses and state what would validate them.
- Do not fabricate benchmarks, targets, attribution results, or projected uplift. If no goal or external benchmark was supplied, evaluate relative performance and account economics only.
- Call out conversion lag, attribution settings, tracking gaps, material changes, partial data, and very small samples when they affect confidence.
- Never omit a weak or unavailable KPI to make performance appear stronger.
