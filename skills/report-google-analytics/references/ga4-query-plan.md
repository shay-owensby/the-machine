# GA4 minimum query plan

Start with the response-metadata probe below. Then use the exact ISO windows produced by `report_dates.py`. Send the current range first and previous range second, naming them `current` and `previous`. Include `returnPropertyQuota: true` on the probe and on the first, high-cost, or final reporting request.

This is a query design contract, not a frozen schema. Retrieve `properties/{property_id}/metadata`, use `checkCompatibility` for uncertain combinations or candidate additions, and record substitutions or failures. One incompatible metric must not cause an entire diagnostic family to be abandoned.

## 1. Access and response-metadata probe

Before calculating the report windows, make this minimal `runReport` request:

```json
{
  "dateRanges": [
    {"startDate": "yesterday", "endDate": "yesterday", "name": "probe"}
  ],
  "metrics": [{"name": "activeUsers"}],
  "limit": "1",
  "returnPropertyQuota": true
}
```

Relative dates are interpreted in the property's time zone. Read `metadata.timeZone` and `metadata.currencyCode` from the response, plus `emptyReason` and property quota when present. Do not set a request `currencyCode` for this probe. An empty result can still be valid, but an authorization or property-access error must stop the report.

Use the Admin API only when optional descriptive metadata such as display name, property type, industry category, or service level is useful. It is not required to discover report timezone or currency.

## 2. Property schema discovery

1. Fetch Data API Metadata for the property. Record current `apiName` values, custom metrics, registered key-event rate metrics, custom channel groups, deprecations, and blocked reasons.
2. Treat a metric with `blockedReasons` as `N/A — access restricted: <reason>`. Do not treat a returned zero for a blocked metric as observed zero performance.
3. When a combination is uncertain, call `checkCompatibility` with the intended base dimensions, metrics, and filters. Use a compatible-only filter when discovering additions. Do not preflight every known-good family.

## 3. Request efficiency and pagination

- Reuse authenticated API clients and the property Metadata response throughout the run.
- Keep each report within 9 dimensions and 10 metrics.
- Prefer one `runReport` for a normal table. Use `batchRunReports` for up to 5 independent requests against the same property when it reduces network round trips; each contained request still consumes quota.
- Put the named `current` and `previous` date ranges in the same request when the fields are compatible. The response adds a `dateRange` dimension.
- Use dimensionless requests for authoritative KPI totals and never sum distinct-user metrics or ratios from segmented tables.
- Use explicit `limit` and `offset`; the default limit is 10,000 and the maximum is 250,000 rows per request. Repeat the identical request with a stable `orderBys` and increasing offset until collected rows reach `rowCount` or a page is empty.
- Minimize columns, filter complexity, date span, and high-cardinality dimensions. Monitor returned quota and run threshold-prone demographic or audience queries only when material.

## 4. Unsegmented KPI totals — required

Run one or more dimensionless paired-range requests covering every compatible canonical metric:

```text
activeUsers, totalUsers, newUsers,
sessions, engagedSessions, engagementRate, bounceRate,
averageSessionDuration, sessionsPerUser,
screenPageViews, screenPageViewsPerSession, screenPageViewsPerUser,
eventCount, eventCountPerUser, eventsPerSession, userEngagementDuration,
scrolledUsers, keyEvents, sessionKeyEventRate, userKeyEventRate,
active1DayUsers, active7DayUsers, active28DayUsers,
dauPerWau, dauPerMau, wauPerMau,
totalRevenue, purchaseRevenue, grossPurchaseRevenue, totalAdRevenue,
ecommercePurchases, transactions, totalPurchasers, firstTimePurchasers,
firstTimePurchaserRate, transactionsPerPurchaser,
averagePurchaseRevenue, averagePurchaseRevenuePerUser,
averagePurchaseRevenuePerPayingUser, averageRevenuePerUser,
refundAmount, itemsViewed, itemsAddedToCart, itemsCheckedOut, itemsPurchased,
cartToViewRate, purchaseToViewRate,
advertiserAdImpressions, advertiserAdClicks, advertiserAdCost,
advertiserAdCostPerClick, advertiserAdCostPerKeyEvent, returnOnAdSpend,
organicGoogleSearchImpressions, organicGoogleSearchClicks,
organicGoogleSearchClickThroughRate, organicGoogleSearchAveragePosition,
crashAffectedUsers, crashFreeUsersRate
```

Split incompatible metrics into additional dimensionless requests and keep every request at 10 metrics or fewer. These totals are authoritative for the scorecard. `active1DayUsers`, `active7DayUsers`, `active28DayUsers`, `dauPerWau`, `dauPerMau`, and `wauPerMau` are rolling values ending on each period's final date, not 30-day totals.

## 5. Daily trend — required

Dimension: `date`.

Metrics: `activeUsers`, `newUsers`, `sessions`, `engagedSessions`, `screenPageViews`, `keyEvents`, `totalRevenue`, and `advertiserAdCost` where compatible. Use daily data for anomalies, not for summing distinct users into period totals.

## 6. Acquisition — required

### Session acquisition

Dimensions, queried in compatible groups: `sessionDefaultChannelGroup`, `sessionSourceMedium`, `sessionCampaignName`, `sessionCampaignId`, and `sessionGoogleAdsCampaignName` when linked.

Metrics: `sessions`, `engagedSessions`, `engagementRate`, `activeUsers`, `newUsers`, `keyEvents`, `sessionKeyEventRate`, `totalRevenue`, `advertiserAdCost`, and `returnOnAdSpend` where compatible.

### First-user acquisition

Dimensions: `firstUserDefaultChannelGroup`, `firstUserSourceMedium`, and `firstUserCampaignName`.

Metrics: `newUsers`, `activeUsers`, `engagedSessions`, `keyEvents`, `userKeyEventRate`, and `totalRevenue` where compatible. Never merge first-user and session acquisition scopes into one ranking.

## 7. Content and landing pages — required for web properties

### Landing pages

Dimension: `landingPagePlusQueryString`. If sensitive query strings are a concern, substitute `landingPage` or redact sensitive parameters.

Metrics: `sessions`, `engagedSessions`, `engagementRate`, `bounceRate`, `averageSessionDuration`, `screenPageViews`, `keyEvents`, `sessionKeyEventRate`, and `totalRevenue`.

### Pages and screens

Dimensions: `pagePathPlusQueryString` with `pageTitle`, or `unifiedPagePathScreen` with `unifiedScreenClass` for mixed web/app properties.

Metrics: `screenPageViews`, `activeUsers`, `userEngagementDuration`, `scrolledUsers`, `eventCount`, `keyEvents`, and `totalRevenue` where compatible.

## 8. Events and key events — required

Dimension: `eventName`.

Metrics: `eventCount`, `totalUsers`, `activeUsers`, `eventCountPerUser`, `eventValue`, `keyEvents`, and `totalRevenue` where compatible.

Use Metadata to identify registered key events and request applicable per-event metrics such as `sessionKeyEventRate:event_name` and `userKeyEventRate:event_name`.

## 9. Audience and technology — required

Query separately as needed:

- Geography: `country`; add `region` or `city` only when useful and privacy-safe.
- Device: `deviceCategory`, `operatingSystem`, `browser`, `platform`, and `streamName`.
- User state: `newVsReturning` when available.
- Language: `language` when relevant.

Metrics: `activeUsers`, `newUsers`, `sessions`, `engagementRate`, `keyEvents`, `sessionKeyEventRate`, `totalRevenue`, and `averageRevenuePerUser` where compatible.

Demographic dimensions are optional and potentially thresholded. Query them only when material, permitted, and statistically useful.

## 10. Ecommerce and monetization — when applicable

### Funnel totals

Query `itemsViewed`, `itemsAddedToCart`, `itemsCheckedOut`, `itemsPurchased`, `ecommercePurchases`, `transactions`, `purchaseRevenue`, `refundAmount`, `cartToViewRate`, and `purchaseToViewRate` in compatible groups.

### Product performance

Dimensions: `itemId`, `itemName`, `itemBrand`, and `itemCategory` in compatible groups.

Metrics: `itemsViewed`, `itemsAddedToCart`, `itemsCheckedOut`, `itemsPurchased`, `itemRevenue`, `itemRefundAmount`, `cartToViewRate`, and `purchaseToViewRate`.

### Promotions and lists

When data exists, query promotion/list dimensions with `promotionViews`, `promotionClicks`, `itemPromotionClickThroughRate`, `itemListViewEvents`, `itemListClickEvents`, and `itemListClickThroughRate`.

If no ecommerce events exist, mark ecommerce sections `N/A — ecommerce tracking not detected`; do not infer zero commercial activity.

## 11. Advertising and Search Console — when linked

Advertising diagnostics can use session campaign/source dimensions with `advertiserAdImpressions`, `advertiserAdClicks`, `advertiserAdCost`, `advertiserAdCostPerClick`, `advertiserAdCostPerKeyEvent`, `keyEvents`, `totalRevenue`, and `returnOnAdSpend` where compatible.

Search Console diagnostics require an active link. Use supported landing-page and query dimensions with `organicGoogleSearchImpressions`, `organicGoogleSearchClicks`, `organicGoogleSearchClickThroughRate`, and `organicGoogleSearchAveragePosition`. If no link exists, use `N/A — Search Console link unavailable`.

## 12. Custom and business-specific KPIs

Include custom metrics and key-event-specific rates tied to business goals, important funnels, or material volume. Record API name, UI name, scope, definition, and caveat. Do not dump obscure custom metrics without interpretation.

## 13. Result handling

- Sort diagnostics by business impact, normally sessions, key events, revenue, or ad cost.
- Preserve `(not set)`, `(other)`, and blank values when material.
- Capture `rowCount`, quota status, and exact response flags: `samplingMetadatas`, `subjectToThresholding`, `dataLossFromOtherRow`, `schemaRestrictionResponse`, and `emptyReason`.
- Treat unique-user and session metrics as potentially approximate, and remember that adding dimensions can change aggregate results by excluding events without those dimensions.
- Default to the top 10 rows plus materially weak rows; disclose truncation.
- Do not retain credentials or raw user-identifying data.
