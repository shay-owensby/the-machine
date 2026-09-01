---
name: report-google-search-console
description: Pull read-only Google Search Console API data, compare the latest 30 complete finalized days with the preceding 30 days, and deliver matching Markdown and self-contained HTML reports with tables, accessible charts, native performance KPIs, opportunities, and prioritized next steps. Use for one-off or recurring Google Search Console performance reporting; do not use to change a property or submit URLs or sitemaps.
---

# Google Search Console Report

Produce an evidence-backed, read-only organic-search performance report. Google Cloud Console provides the OAuth project and API enablement; the reporting data comes from the Google Search Console API.

## Required resources

Before accessing credentials, querying data, or writing the report, read:

- [references/data-contract.md](references/data-contract.md) for authentication, date conventions, KPI calculations, completeness checks, and analysis standards.
- [references/query-plan.md](references/query-plan.md) while extracting the required Search Analytics and sitemap datasets.
- [references/report-template.md](references/report-template.md) before drafting. Copy its headings, order, KPI rows, and tables exactly.
- [references/html-output.md](references/html-output.md) for the shared CSS, visualization requirements, chart-directive schema, and Markdown-to-HTML build procedure.

## Workflow

1. Resolve the active client project root and treat `./.env` there as the authoritative credential source. Run `scripts/check_env_config.py --env-file ./.env`. Parse the file as data; never shell-source, display, echo, log, or copy it. Do not ask for credentials already present there.
2. Authenticate with OAuth 2.0 read-only access. An API key alone cannot authorize private Search Console data. Resolve the property from `--site-url`, a recognized `.env` variable, or `sites.list`. If several properties are available and none is configured, stop and ask the user which exact property to report on.
3. Determine the latest finalized Search Console date and use Pacific Time date semantics. Generate two adjacent, non-overlapping 30-day windows. Prefer `scripts/fetch_search_console.py --env-file ./.env --output <temporary-json-path>`; use `--site-url` only when selection is required. Keep raw extraction files temporary and outside the reports directory.
4. Pull property totals and daily, query, page, country, device, and search-appearance data for every supported search type. Extract high-cardinality query and page detail one day at a time, then aggregate locally across each 30-day period. Also retrieve a read-only sitemap snapshot. Follow the query plan, paginate until an empty response or a recorded safety cap, and preserve unavailable or truncated data as an explicit limitation.
5. Reconcile totals before analysis. Use no-dimension property totals as authoritative for clicks, impressions, CTR, and average position. Never sum rows from different dimensions, average row-level CTR, or treat the returned query/page rows as complete property totals.
6. Compare current and previous periods using absolute and percentage changes. Separate facts from hypotheses. Base strengths, weaknesses, and recommendations on quantified material evidence; do not use generic SEO advice as a finding.
7. Fill every section of the strict template. Do not delete, rename, or reorder headings or KPI rows. Use `N/A — <reason>` when a metric, segment, or comparison is unavailable. Remove every placeholder.
8. Add the chart directives required by `references/html-output.md` under the most relevant existing headings. Prefer an executive KPI-change chart, a daily clicks or impressions trend, and a query, page, device, country, or search-appearance comparison. Every plotted value must reconcile to a nearby table.
9. Save the Markdown report to `./analytics-insights/google-search-console/YYYY/YYYYmmdd-google-search-console-report.md`. `YYYY` and the filename date use the report-generation date in Pacific Time. Run `scripts/build_report_outputs.py <markdown-report-path>` to generate its SVG chart assets and same-basename HTML companion.
10. Run `scripts/validate_report.py <markdown-report-path>` and correct every failure. Deliver clickable links to both the Markdown and HTML files and state both comparison windows and the property analyzed.

## Boundaries

- Search Console access is read-only. Reporting never authorizes property changes, sitemap submissions/deletions, URL indexing requests, or external SEO changes.
- Read only the credential and property variables needed from `./.env`. Never put secrets in process arguments, reports, temporary filenames, console output, or skill files.
- Do not claim that ranking, CTR, or traffic changes caused business outcomes. Search Console measures Google Search visibility and clicks, not sessions, leads, revenue, or conversions.
- Do not invent goals, benchmarks, brand terms, causation, or projected uplift. Mark brand/non-brand analysis `N/A` unless brand terms are supplied or configured.
- Call out incomplete/fresh data, anonymized queries, top-row truncation, data anomalies, search-type incompatibilities, small samples, migrations, seasonality, and tracking/property changes when they affect confidence.
- Never omit a weak or unavailable KPI to make performance appear stronger.
