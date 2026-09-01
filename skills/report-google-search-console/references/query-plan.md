# Search Console API query plan

Use exact ISO dates for both periods. Run the same request shapes for current and previous windows. The extraction helper implements this minimum plan; when querying another way, preserve the same contract.

## 1. Property discovery

When a property is not configured, call:

```http
GET https://www.googleapis.com/webmasters/v3/sites
Authorization: Bearer <token>
```

Use only a property returned by this endpoint. Preserve its exact `siteUrl` and permission level in extraction metadata.

## 2. Finalization probe

Probe the most recent 10 days of Web data with `dataState=all` and `dimensions=["date"]`. Read `metadata.first_incomplete_date`; do not include that date or any later date in the finalized window. When that field is absent, repeat the probe with `dataState=final` and use the latest date row returned. Record when the extractor must fall back to yesterday because the finalized probe has no rows.

## 3. Search Analytics request families

Endpoint:

```text
POST https://www.googleapis.com/webmasters/v3/sites/{url-encoded-siteUrl}/searchAnalytics/query
```

Common body fields:

```json
{
  "startDate": "YYYY-MM-DD",
  "endDate": "YYYY-MM-DD",
  "type": "web",
  "dataState": "final",
  "aggregationType": "byProperty",
  "rowLimit": 25000,
  "startRow": 0
}
```

Run these families for `web`, `image`, `video`, `news`, `discover`, and `googleNews`:

| Family | Dimensions | Aggregation | Purpose |
|---|---|---|---|
| Property totals | none | `byProperty` when supported; otherwise `auto` | Authoritative clicks, impressions, CTR, and average position |
| Daily | `date` | Same as property totals | Trend, volatility, missing-date, and anomaly analysis |
| Queries | `query` | `byProperty` when supported; otherwise `auto` | Query one day at a time, then aggregate locally for demand, winners/losers, CTR, and ranking opportunities |
| Pages | `page` | `auto` | Query one day at a time, then aggregate locally for landing-page winners/losers and opportunity analysis |
| Countries | `country` | Same as property totals | Geographic mix and outliers |
| Devices | `device` | Same as property totals | Mobile/desktop/tablet performance |
| Search appearances | `searchAppearance` | `auto` | Rich-result and feature visibility |

Use separate requests for current and previous windows. For query and page detail, issue one request series per calendar day and aggregate rows with identical keys across the 30 days: sum clicks and impressions, recompute CTR, and impression-weight average position. Paginate dimensioned families with `rowLimit=25000` and `startRow` increments. Stop only when a response returns zero rows. Apply a bounded per-day page cap and record each affected date.

For `discover` and `googleNews`, use `auto` because `byProperty` is unsupported. A no-row result means no reportable data for that type and period, not an API error.

### Search appearance drilldown

The required summary request uses `searchAppearance` as its only dimension. When a returned appearance is material to a conclusion or recommendation, run a second query with a `dimensionFilterGroups` filter for that exact value and add the relevant page, query, country, or device dimension. Do not combine `searchAppearance` with another grouping dimension in the discovery request.

## 4. Read-only sitemap snapshot

Call once:

```http
GET https://www.googleapis.com/webmasters/v3/sites/{url-encoded-siteUrl}/sitemaps
Authorization: Bearer <token>
```

Retain:

- `path`
- `type`
- `isPending`
- `isSitemapsIndex`
- `lastSubmitted`
- `lastDownloaded`
- `warnings`
- `errors`
- `contents[].type`
- `contents[].submitted`

Do not use deprecated `contents[].indexed`.

## 5. Optional targeted analyses

Only add these when the user supplies the necessary context or the baseline data shows a material opportunity:

- Brand vs. non-brand using an explicit brand-term regex. Never infer the regex from the domain alone.
- Query-by-page diagnostics for cannibalization or intent mismatch. These are high-load and truncated; limit them to material queries or pages.
- Country/device filters for a specific market investigation.
- URL Inspection for a small, justified set of exact URLs. Reporting does not authorize a broad inspection crawl, and URL Inspection is a current snapshot rather than a period comparison.

## 6. Error handling

- Invalid/expired credentials: identify only the auth category and stop.
- Permission denied: state that the authenticated principal lacks access to the exact property; do not change permissions.
- Invalid aggregation/type combination: retry once with `auto` only where the contract allows it and record the substitution.
- Quota or transient server error: bounded backoff; if a family remains unavailable, continue independent families and report the limitation.
- Pagination cap: keep the rows obtained, label the family truncated, and lower confidence for conclusions based on its tail.
- Wrong or ambiguous property: stop before producing a report.
