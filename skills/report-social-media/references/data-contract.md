# Social Media Report Data Contract

## Authentication and scope

- API base URL: `https://zernio.com/api/v1`.
- Authentication: `Authorization: Bearer <token>`.
- Read `./.env` from the client project root. Resolve the first non-empty value in this order: `ZERNIO_API_KEY`, `ZERNIO_ACCESS_TOKEN`, `ZERNIO_API_TOKEN`, `ZERNIO_TOKEN`. Prefer the first, which is Zernio's documented variable.
- Also recognize optional client-scope configuration in `./.env`:
  - `ZERNIO_PROFILE_ID` — authoritative profile ID for this client project.
  - `ZERNIO_PROFILE_NAME` — human-readable label used to validate and display the configured profile; it is not a substitute for an ID when names are ambiguous.
  - `ZERNIO_ACCOUNT_IDS` — comma-separated authoritative allowlist of account IDs to report.
  - `ZERNIO_<PLATFORM>_ACCOUNT_ID` — optional per-platform aliases such as `ZERNIO_FACEBOOK_ACCOUNT_ID` or `ZERNIO_INSTAGRAM_ACCOUNT_ID`. When `ZERNIO_ACCOUNT_IDS` is present, every per-platform ID must be included in that allowlist.
- Choose reporting scope in this order: (1) a profile/account filter explicitly supplied by the user for the current request, (2) valid configured IDs from `./.env`, (3) live discovery rules. An explicit user filter may intentionally override project defaults for that run.
- Always inventory accessible profiles and accounts, even when scope is configured, but use the inventory only to validate IDs, profile membership, connection state, and analytics access. Do not use it to re-determine client ownership or add unconfigured accounts.
- Validate that `ZERNIO_PROFILE_ID` exists and is accessible; validate that every configured account ID exists, is accessible, and belongs to the configured profile when one is set. If `ZERNIO_PROFILE_NAME` is present, confirm it matches the live profile label. If aliases and the account allowlist conflict, or an ID is stale/inaccessible, stop scope selection and report the specific configuration issue without falling back to other profiles.
- When no explicit or configured scope exists, report the single accessible profile if there is exactly one. If several profiles are accessible, report all of them unless the user identifies one; never silently infer ownership from names or usernames.
- Never display a credential, the matching `.env` line, a request header, or a command containing the credential. Never put credentials in the report.
- Use only `GET` endpoints. A reporting request does not authorize write operations, including on-demand external-post sync.
- If authentication fails, state only that the Zernio credential is missing, invalid, expired, or lacks access. Do not echo its value or prefix.

## Reporting periods

Use two adjacent 30-day periods of complete calendar days:

- Report date `R`: today in the reporting time zone.
- Current: `R - 30 days` through `R - 1 day`, inclusive.
- Previous: `R - 60 days` through `R - 31 days`, inclusive.

Choose the IANA reporting time zone in this order:

1. A time zone explicitly supplied by the user.
2. `SOCIAL_REPORT_TIMEZONE` or `REPORT_TIMEZONE` in `./.env`.
3. A relevant Zernio/ad-account time zone returned by the API when the scope is a single brand and it is unambiguous.
4. The client project's local system time zone.

Record the selected time zone and its source. Send inclusive date bounds explicitly to every endpoint. For timestamp parameters, use the start of the first day and end of the last day in the selected zone, expressed in ISO 8601. Follow endpoint-specific exclusive end-date rules where the live schema says so, and document the conversion.

## Completeness and availability

- Inventory profiles and connected accounts before querying analytics.
- Include `source=all` so Zernio-published and externally published content are represented. If a platform cannot list external content, disclose the coverage limitation.
- Paginate until the API indicates no more rows or the collected count equals the reported total. Prefer the maximum allowed page size.
- Query the current and previous windows separately with identical filters.
- Treat HTTP `202`, `backfillPending`, `syncStatus` other than synced, and platform freshness timestamps as data-quality signals. Do not repeatedly poll indefinitely; make one bounded retry when the response recommends it, then report pending data.
- Treat `401` as an authentication failure, `402` as an analytics/add-on restriction, `403` as permission/access restriction, and `412` as a missing platform scope or reconnection requirement. Preserve the endpoint and account affected without exposing secrets.
- A missing/null field is unavailable unless the schema explicitly defines its absence as zero. Platform metric names differ; do not infer equivalence merely from similar labels.
- Use the current live Zernio OpenAPI specification or endpoint page to discover valid metric names. Include every numeric KPI field returned for the selected scope in the report's additional-KPI inventory.

## Canonical KPI definitions

Use Zernio's returned value when it provides an unambiguous aggregate. Otherwise apply these rules:

- **Posts published:** count of unique platform posts published in the window. A multi-platform Zernio post counts once per destination account in account/platform tables; report a separate unique Zernio-post count if useful.
- **Impressions, reach, views, likes/reactions, comments, shares/reshares, saves, clicks, follows, and reposts:** period totals from like-for-like API scope. Do not sum a Zernio parent post and its `platformAnalytics` children.
- **Total engagements:** sum of likes/reactions + comments + shares/reshares + saves + clicks. Add platform-native engagement types only when identified, and disclose the formula. Exclude impressions, reach, views, follows, and passive watch time.
- **Engagement rate:** use the API's aggregate rate when its basis is documented. Otherwise calculate `total engagements / impressions * 100`; if impressions are unavailable or zero, use reach only when clearly labeled `engagement rate by reach`. Never average post-level rates to produce an overall rate.
- **Click-through rate:** `clicks / impressions * 100` when both are comparable.
- **View rate:** `views / impressions * 100` only when both metrics describe the same content and platform scope.
- **Current followers:** the final valid follower observation on or before the period end, reported per account. Do not sum follower counts across accounts into a unique audience claim; an optional arithmetic portfolio total must be labeled non-deduplicated.
- **Net follower growth:** ending followers minus the final observation immediately before the period start, or Zernio's returned growth value for the exact window.
- **Follower growth rate:** `net follower growth / starting followers * 100`. If starting followers are zero, report `N/A — zero denominator`.
- **Average watch time, retention, skip rate, response time, cost metrics, CTR, CPM, CPC, conversion rate, and ROAS:** do not sum or arithmetically average row-level values. Use API aggregates or recompute from valid numerators and denominators.
- **Percent change:** `(current - previous) / abs(previous) * 100`. When previous is zero and current is nonzero, show the absolute change and `N/M — prior period was zero`; when both are zero show `0.0%`.

Round counts to whole numbers, currency to two decimals, rates to one decimal percentage point, and durations in a human-readable form. Retain enough precision during calculations to avoid compounding rounding error.

## Reconciliation

Before interpreting results:

1. Reconcile the post list with daily metrics by window, filter, and source. Explain differences caused by attribution (`publish` versus `received`), lifetime post totals, platform delays, or missing external posts.
2. Reconcile account/platform totals from child rows, not both child and parent aggregates.
3. Keep account-level insights separate from post-level totals. For example, Instagram account reach covers all content surfaces and is not interchangeable with summed post reach.
4. Keep organic, inbox/community, and paid-media metrics in separate tables. Do not merge paid impressions or clicks into organic totals.
5. Note any cross-platform semantic mismatch in the metric definition appendix.

## Analytical standard

- Executive claims must include a number and comparison.
- A strength or weakness must cite the KPI, affected platform/account/content set, direction, magnitude, and confidence caveat when relevant.
- An action must connect to evidence, name an owner role, specify timing, define an observable success measure, and state the next evaluation window.
- Distinguish facts from hypotheses. Use language such as `Observation`, `Hypothesis`, and `Validation` where causal evidence is absent.
- Prioritize actions by expected relevance and evidence strength, not invented uplift.
- Flag sample sizes under five posts per compared segment as low confidence.

## Output contract

- Destination: `./analytics-insights/social-media/YYYY/YYYYmmdd-social-media-report.md`.
- The filename date and year directory use the report-generation date in the reporting time zone.
- Copy the report template's headings and canonical KPI rows exactly. Replace every placeholder. Variable-row placeholders may expand into as many Markdown rows as needed.
- Use `N/A — <specific reason>` instead of removing a row or leaving a blank cell.
- The only permanent output is the final Markdown report unless the user explicitly requests raw exports.
