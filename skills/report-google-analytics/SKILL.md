---
name: report-google-analytics
description: Pull read-only GA4 data through the Google Analytics Data API using credentials from the client project's .env, compare the last 30 complete days with the preceding 30 days, and deliver matching Markdown and self-contained HTML reports with tables, accessible charts, KPI scorecards, and prioritized next steps. Use for one-off or recurring Google Analytics 4 performance reporting; do not use for Universal Analytics or to change Analytics configuration.
---

# Google Analytics Report

Produce an evidence-backed, read-only GA4 performance report. Google Cloud Console provides the OAuth project and API enablement; use the Google Analytics Data API for report data and response metadata. Use the Analytics Admin API only as an optional source of descriptive property metadata.

## Required resources

Before accessing credentials, querying data, or writing the report, read:

- [references/data-contract.md](references/data-contract.md) for authentication, dates, KPI definitions, reconciliation, analysis, and security rules.
- [references/ga4-query-plan.md](references/ga4-query-plan.md) while pulling the required query families.
- [references/report-template.md](references/report-template.md) for the mandatory output structure. Copy its structure exactly.
- [references/html-output.md](references/html-output.md) for the shared CSS, visualization requirements, chart-directive schema, and Markdown-to-HTML build procedure.

## Workflow

1. Work from the client project root. Read credential and property settings from `./.env` without printing, logging, committing, or copying secrets. Never assume an API key alone grants access to private Analytics data.
2. Resolve the numeric GA4 property ID and an identity with Viewer-or-higher access. Confirm the Google Analytics Data API is enabled. Use the `analytics.readonly` OAuth scope and the official client library or REST API. If credentials, property ID, API enablement, or access are missing, identify only the missing requirement and stop; never invent data.
3. Make the minimal access probe defined in the query plan. Read the property time zone and currency from the returned `ResponseMetaData`; use the Admin API only when already available and descriptive property details add value. Then run `scripts/report_dates.py --timezone <property-time-zone> --create-dir` to calculate two non-overlapping 30-day windows and the required destination.
4. Retrieve property-specific Metadata, use current `apiName` values, and identify custom or access-blocked metrics. Build efficient query families within Data API limits; use `checkCompatibility` to discover compatible additions or resolve uncertain combinations rather than preflighting every known-good request. Reuse one client, batch up to five same-property reports when useful, and paginate with `limit` plus `offset` until `rowCount` is satisfied.
5. Pull every required family in the query plan with paired named date ranges (`current`, `previous`) wherever compatible. Reconcile unsegmented totals before analysis. Do not sum distinct-user metrics across rows, average ratios, or combine scopes as though they were interchangeable. Preserve thresholded, sampled, access-blocked, incompatible, inapplicable, or unavailable data as `N/A — <reason>`.
6. Compare current and previous periods using absolute and relative change. Separate observations from hypotheses. Support every strength, weakness, and action with quantified evidence; account for tracking changes, consent/modeling, attribution, seasonality, thresholding, and small samples.
7. Fill every section and canonical KPI row in the strict template. Do not delete, rename, or reorder headings or KPI rows. Include applicable property-specific custom metrics in the designated table. Replace every placeholder.
8. Add the chart directives required by `references/html-output.md` under the most relevant existing headings. Prefer an executive KPI-change chart, a daily users or sessions trend, and a channel, source, landing-page, or device comparison. Every plotted value must reconcile to a nearby table.
9. Save the Markdown report to `./analytics-insights/google-analytics/YYYY/YYYYmmdd-google-analytics-report.md`, using the report-generation date in the property time zone for `YYYY` and the filename date. Run `scripts/build_report_outputs.py <markdown-report-path>` to generate its SVG chart assets and same-basename HTML companion.
10. Run `scripts/validate_report.py <markdown-report-path>` and correct every failure. Return clickable links to both the Markdown and HTML files and state both comparison periods.

## Boundaries

- Treat Analytics and Google Cloud access as read-only. A reporting request does not authorize tag, event, key-event, audience, attribution, data-retention, property, IAM, billing, or API-configuration changes.
- Do not expose `.env` contents in commands, logs, intermediate files, or reports. Do not place secret values in command arguments.
- Never interpret a zero returned for a Metadata-blocked cost or revenue metric as observed zero performance.
- Do not claim causation from period-over-period movement. Label hypotheses and say how to validate them.
- Do not fabricate targets, benchmarks, attribution results, or projected uplift. If the user supplied no target, judge relative performance, measurement health, and observed business outcomes only.
- Never hide a weak, zero, or unavailable KPI. Explain why `N/A` appears and how to make the metric reportable when practical.
