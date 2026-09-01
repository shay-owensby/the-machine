# Google Search Console reporting data contract

Use this contract for every report produced by the skill.

## 1. Access and authentication

Google Cloud Console is the OAuth configuration and API-enablement layer. The private reporting source is the Google Search Console API.

### Authoritative client configuration

The active client project's root `./.env` contains the configuration for this workflow. Resolve it relative to the current project, never relative to the skill folder. Run `scripts/check_env_config.py --env-file ./.env` before attempting authentication.

Load dotenv values with a parser. Never execute the file with `source`, print its contents, expose values in command arguments, copy it into the skill or report tree, or include secrets in errors. Missing configuration errors name only the logical category.

Supported authentication, in priority order:

1. An OAuth access token, recognizing that it may expire during the run.
2. OAuth client ID, client secret, and refresh token, refreshed in memory through Google's token endpoint.
3. An Application Default Credentials or service-account credential source only when it is already configured and the principal has explicit Search Console property access. Do not create or grant access as part of reporting.

Required authorization scope: `https://www.googleapis.com/auth/webmasters.readonly`. An API key by itself is not valid authorization for private Search Console data.

The property must match Search Console exactly:

- URL-prefix property: `https://www.example.com/` including the protocol and trailing slash.
- Domain property: `sc-domain:example.com`.

Use a configured property variable when present. Otherwise call `GET https://www.googleapis.com/webmasters/v3/sites`. If exactly one usable property exists, use it. If multiple exist, ask the user to select the exact property; do not guess from the repository name or website files.

Official references:

- OAuth: <https://developers.google.com/webmaster-tools/v1/how-tos/authorizing>
- Sites list: <https://developers.google.com/webmaster-tools/v1/sites/list>
- Search Analytics query: <https://developers.google.com/webmaster-tools/v1/searchanalytics/query>
- Usage limits: <https://developers.google.com/webmaster-tools/limits>

## 2. Fixed date convention

Search Console API dates use Pacific Time (`America/Los_Angeles`), including daylight-saving changes.

- Report date: calendar date when the report is generated in Pacific Time.
- Current period: the latest 30 complete finalized Search Console dates, inclusive.
- Previous period: the immediately preceding 30 dates, inclusive.
- The windows never overlap and each contains exactly 30 calendar dates.

Probe the most recent 10 days grouped by `date`, as Google recommends. First use `dataState=all`; when response metadata includes `first_incomplete_date`, end the current window on the preceding date. If that metadata is absent, repeat the date probe with `dataState=final` and use its latest returned date. If the finalized probe has no rows, fall back to yesterday in Pacific Time and explicitly lower confidence because a no-row day can mean zero activity, delayed processing, or omitted data.

Only include incomplete data when the user explicitly requests it. If used, label it prominently and make the comparison limitation explicit.

## 3. Native KPIs and calculations

The Search Analytics API exposes four native performance KPIs. The strict template always includes all four:

| KPI | Definition and handling |
|---|---|
| Clicks | Google Search result clicks attributed to the property for the selected type and filters. |
| Impressions | Times a property result was shown under Search Console's counting rules. |
| CTR | Clicks / impressions. Display as a percentage. Recompute from summed clicks and impressions only when a native total is unavailable. |
| Average position | The API's average topmost-result position. Lower is generally better, but interpret with query mix, device, feature, and impression changes. Use the no-dimension API total; when a derived roll-up is unavoidable, use impression weighting and label it derived. |

Period comparison:

- Absolute change = current − previous.
- Relative change = `(current − previous) / previous`.
- For CTR, show percentage-point change as the absolute change and relative percentage change separately.
- For average position, show position-point change; a negative value generally indicates improvement. Do not describe a percentage change in position as a proportional ranking gain.
- If previous is zero and current is nonzero, relative change is `N/M — no prior-period base`.
- If both values are zero, relative change is `0.0%`.
- If either value is unavailable, both changes are `N/A`.

Derived diagnostic KPIs may include clicks/impressions per day, reported query/page counts, position-bucket counts and impressions, device/country share, and winner/loser counts. Label them as derived and state the row universe. They do not replace the four native KPI rows.

## 4. Required search types and dimensions

Evaluate each supported type separately: `web`, `image`, `video`, `news`, `discover`, and `googleNews`. Web is the primary executive view unless the user's business context makes another surface primary. Do not sum types into an undocumented “all search” total because surfaces differ and can overlap in interpretation.

For both periods, obtain:

- No-dimension property totals.
- Daily performance (`date`).
- Queries (`query`).
- Pages (`page`).
- Countries (`country`).
- Devices (`device`).
- Search appearances (`searchAppearance`).

Use separate requests for dimensions. Never sum totals from query, page, country, device, or search-appearance datasets together. Query/page detail can be truncated and rare queries are anonymized; dimension row sums can therefore be lower than property totals.

For the `query` and `page` families, query each calendar day separately and aggregate identical keys locally across the period. Sum clicks and impressions, recompute CTR, and calculate an impression-weighted average position. Preserve the number of source rows, days successfully queried, failed days, and days that hit a pagination cap. This follows Google's comprehensive-data guidance and respects the 50,000-row-per-day-per-search-type limit.

Search appearance is a two-step workflow when detail beyond the summary is material:

1. Query `searchAppearance` as the only dimension to discover values actually present for the property and period.
2. For each material returned value, optionally run a second request filtered to that exact appearance and add the needed page, query, country, or device dimension. Record that these filtered totals use the API's applicable aggregation behavior.

## 5. Aggregation, pagination, and completeness

- Use `type`, not deprecated `searchType`.
- Set `dataState=final` for the report extraction.
- Use `byProperty` for no-page Search Analytics requests where supported. Use `auto` when grouping/filtering by page or search appearance, and for types that do not support property aggregation.
- `rowLimit` is at most 25,000 per request. Follow `startRow` offsets until the API returns an empty row set, as Google's pagination guidance specifies, or until a bounded safety cap is reached and recorded.
- Search Analytics is bounded by internal storage limits and does not guarantee every row. The API exposes at most 50,000 rows per day per property per search type, sorted by clicks. Expensive page/query queries also consume higher load quota.
- Prefer the fewest query families that satisfy the report; do not repeatedly pull the same 60-day data.
- On 429 or transient 5xx errors, use bounded exponential backoff and honor `Retry-After`. Never retry indefinitely.

Official detail:

- Data extraction limits: <https://developers.google.com/webmaster-tools/v1/how-tos/all-your-data>
- Search Console data caveats: <https://support.google.com/webmasters/answer/96568>

## 6. Sitemap context

Call the read-only sitemap list endpoint once. Report sitemap path, type, pending state, last download, warnings, errors, and submitted URL counts when available. The `contents[].indexed` field is deprecated and must not be presented as an indexing KPI.

Sitemap state is a current snapshot, not a 30-day comparison. Do not infer that sitemap submission caused organic performance changes.

Official reference: <https://developers.google.com/webmaster-tools/v1/sitemaps/list>

## 7. Reconciliation and quality checks

Before analysis:

1. Confirm the property and permission level.
2. Confirm both windows contain exactly 30 Pacific calendar dates and are adjacent.
3. Confirm all report requests used the same filters, aggregation convention, and search type except where API compatibility requires otherwise.
4. Use no-dimension rows as the authoritative totals. Recompute CTR from authoritative clicks and impressions as a check.
5. Ensure CTR is scaled from 0–1 to a displayed percentage.
6. Do not average average-position rows without impression weighting.
7. Compare dimension-row sums to totals and quantify material coverage gaps as truncation/anonymization, not “missing traffic.”
8. For daily query/page extraction, verify every date was attempted and flag failed or pagination-capped days.
9. Flag types or query families that returned no data, were unsupported, hit pagination caps, or failed.
10. Inspect known Search Console data anomalies for dates in either window when a suspicious discontinuity could change a conclusion: <https://support.google.com/webmasters/answer/6211453>.
11. Distinguish a true zero, an absent row, an unavailable field, and a failed request.

## 8. Analysis standards

Every executive finding must be traceable to evidence in the report. A strength or weakness should cite at least one native KPI and one query, page, device, country, search appearance, or search-type cut when possible.

Prioritize findings by:

- Impact: clicks/impressions affected and strategic page/query importance.
- Confidence: sample size, consistency across days, completeness, and data quality.
- Controllability: content, snippet, internal linking, technical indexing, template, or SERP-feature changes within the user's control.
- Urgency: material losses, sitemap errors, deindexing signals, migrations, or sharp cross-segment declines.

Useful opportunity patterns include:

- High-impression queries or pages with below-context CTR.
- Queries in positions 4–10 or 11–20 with meaningful impressions.
- Pages losing both impressions and position.
- Pages gaining position but not CTR.
- Device-specific or country-specific underperformance.
- Search appearances with growing visibility but weak clicks.

Do not apply universal CTR-by-position benchmarks without a user-supplied or sourced benchmark. Compare against the property's own prior period and relevant peer segments. Do not infer conversions or revenue from clicks.

Recommendations must include evidence, a concrete action, target KPI and direction, owner role, time horizon, and validation method. Prefer reversible tests with a defined review date. Never promise exact uplift.

## 9. Output contract

- Preserve the exact headings, order, and KPI rows in `report-template.md`.
- Replace every `{{PLACEHOLDER}}`; use `N/A — <reason>` instead of deleting required content.
- Default top/bottom lists to 10 rows when at least 10 meaningful rows exist; show fewer when the universe is smaller.
- Escape Markdown table pipes in query text and URLs.
- Save to `./analytics-insights/google-search-console/YYYY/YYYYmmdd-google-search-console-report.md` using the Pacific report date.
- Store only the final Markdown report in the report year directory. Keep raw API data temporary and remove it after the report is validated.
- Run `scripts/validate_report.py` before delivery.
