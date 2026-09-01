# Zernio Query Plan

Zernio changes its analytics surface over time. Check the [live API documentation](https://docs.zernio.com/) or [OpenAPI specification](https://docs.zernio.com/api/openapi) before querying. Use the current schema as authoritative for parameter names, metric enums, response shapes, range limits, and availability.

## 1. Scope inventory — always

Query:

- `GET /v1/profiles` — accessible brand/profile containers.
- `GET /v1/accounts` — connected accounts, platform, username/display name, profile membership, and analytics-access signal. Paginate if the live response supports it.
- Read-only account health endpoints when available — analytics permission, expired connection, and missing-scope context.

Apply scope in this order: a user-supplied profile/account filter, validated `ZERNIO_PROFILE_ID` / `ZERNIO_ACCOUNT_IDS` project configuration, then live discovery. When project scope is configured, query only the account allowlist after validating every ID and profile membership; do not add other accounts merely because they share the profile. If no explicit or configured scope exists, include the only accessible profile or all accessible profiles when there are several. Identify disconnected, over-limit, analytics-ineligible, stale-configured, or mismatched configured accounts in coverage notes.

## 2. Core organic performance — always

For current and previous windows with identical filters:

- `GET /v1/analytics` with `source=all`, explicit `fromDate` and `toDate`, `limit=100`, and every page. Preserve post ID, platform/account, published time, content excerpt, URL, media/content type, source, sync status, every numeric analytics field, and `lastUpdated`.
- `GET /v1/analytics/daily-metrics` with explicit timestamps, `source=all`, and `attribution=publish` for a publish-cohort comparison. When supported and useful, also call `attribution=received` for the trend section; never mix the two bases.
- `GET /v1/accounts/follower-stats` with explicit dates and daily granularity. To measure starting and ending follower levels correctly, include the last observation immediately before each window when available.

Canonical post fields currently include impressions, reach, likes/reactions, comments, shares/reshares, saves, clicks, views, follows, reposts, engagement rate, Instagram Reels watch-time fields, video duration, and Reels skip rate. Treat the live response as authoritative and capture additional numeric fields automatically.

## 3. Platform account insights — conditional per account

Call every applicable read-only endpoint exposed by the live schema for each connected account. Request all valid metrics, either by omitting `metrics` when that means all or by passing the complete current enum.

- Instagram: `/v1/analytics/instagram/account-insights`, `/v1/analytics/instagram/follower-history`, and demographics when returned and sufficiently populated.
- Facebook Pages: `/v1/analytics/facebook/page-insights`; include post earnings when the account and permissions support it.
- LinkedIn organizations: `/v1/analytics/linkedin/org-aggregate-analytics`.
- LinkedIn personal accounts: `/v1/accounts/{accountId}/linkedin-aggregate-analytics`; respect any exclusive `endDate` semantics and the limitation to eligible posts.
- YouTube: `/v1/analytics/youtube/channel-insights`, daily views, demographics, and applicable video-retention data for leading videos.
- TikTok: `/v1/analytics/tiktok/account-insights`.
- Google Business Profile: `/v1/analytics/googlebusiness/performance` and search keywords.
- Any newer platform-specific analytics endpoint present in the live OpenAPI specification.

Pull both `total_value` and `time_series` only where each metric supports them. Do not force time-series mode for total-only metrics. Respect documented delays and privacy thresholds.

## 4. Publishing optimization — always when available

Query the widest supported historical lookback separately from the two-period KPI comparison, and label that analysis window clearly:

- `GET /v1/analytics/best-time`
- `GET /v1/analytics/content-decay`
- `GET /v1/analytics/posting-frequency`

Use these results for recommendations, not as period totals. Record that best-time hours are UTC when the endpoint returns UTC, and convert them to the reporting time zone in the report.

## 5. Community and inbox — conditional

If accessible and relevant social inbox data exists, query the current and previous windows from the `/v1/analytics/inbox/*` family, including volume, heatmap, source breakdown, response time, top accounts, and conversations. Include every returned numeric KPI. Keep this section `N/A` when the account lacks the Inbox add-on or no supported inbox accounts are in scope.

## 6. Paid social — conditional

If connected ad accounts or campaigns are accessible, query read-only paid analytics for both periods:

- Daily account timeline such as `GET /v1/ads/timeline`.
- Campaign inventory and `GET /v1/ads/campaigns/{campaignId}/analytics` for in-scope campaigns.
- Ad-level analytics only when needed to identify material drivers; paginate inventories and avoid unnecessary fan-out.
- Request relevant breakdowns only where supported and statistically safe.

Include spend, impressions, reach, clicks, engagement, CTR, CPC, CPM, conversions/actions, cost per conversion, purchase value, and ROAS when returned. Keep currency and ad-account time zone explicit. Never combine paid totals with organic KPI totals.

## 7. Coverage ledger

Maintain a ledger while querying:

| Query family | Account/profile | Current | Previous | Freshness | Limitation/action |
|---|---|---|---|---|---|

Record success, no data, unsupported platform, missing add-on, missing scope, pending backfill, or API error. The report's coverage section must summarize this ledger.

## 8. Analysis cuts

At minimum, compare:

- Portfolio/profile total and each platform/account.
- Each available KPI, with scope and definition intact.
- Publishing volume and cadence.
- Top and bottom posts by a fair mix of reach/visibility, engagement rate, clicks/actions, follower impact, and video quality where available.
- Content format/media type and useful platform-native classifications.
- Follower growth and audience/account insights.
- Day-of-week and time-of-day only with adequate sample size.
- Community/inbox and paid performance when available.

Do not publish rankings that compare non-equivalent denominators without an explicit caveat.
