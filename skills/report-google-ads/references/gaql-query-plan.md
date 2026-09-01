# GAQL query plan

Use exact ISO dates in every performance query. Replace `CURRENT_START`, `CURRENT_END`, `PREVIOUS_START`, and `PREVIOUS_END` with the windows from `report_dates.py`. Run the same query shape for both periods, or query the full 60-day span with `segments.date` and split locally.

Field availability changes across Google Ads API versions. Validate each SELECT list with the current Google Ads Fields service. When one optional metric makes a query invalid, move it into a compatible query rather than dropping the whole diagnostic family.

## Minimum extraction set

### Customer metadata

```sql
SELECT
  customer.id,
  customer.descriptive_name,
  customer.currency_code,
  customer.time_zone,
  customer.auto_tagging_enabled,
  customer.test_account
FROM customer
LIMIT 1
```

### Campaign-by-day core facts

```sql
SELECT
  segments.date,
  campaign.id,
  campaign.name,
  campaign.status,
  campaign.advertising_channel_type,
  campaign.advertising_channel_sub_type,
  campaign.bidding_strategy_type,
  metrics.impressions,
  metrics.clicks,
  metrics.cost_micros,
  metrics.interactions,
  metrics.engagements,
  metrics.conversions,
  metrics.conversions_value,
  metrics.all_conversions,
  metrics.all_conversions_value,
  metrics.view_through_conversions,
  metrics.cross_device_conversions,
  metrics.video_views
FROM campaign
WHERE segments.date BETWEEN 'CURRENT_START' AND 'CURRENT_END'
```

Derive additive totals and ratios locally. Pull average/rate fields separately only when their Google Ads definition cannot be reproduced reliably from the selected bases.

### Budget, bidding, and visibility

Use a campaign query compatible with the current version to retrieve campaign budget amount, campaign optimization score, eligible/status fields, and these Search metrics when applicable:

```text
metrics.search_impression_share
metrics.search_exact_match_impression_share
metrics.search_top_impression_share
metrics.search_absolute_top_impression_share
metrics.search_budget_lost_impression_share
metrics.search_rank_lost_impression_share
```

Do not aggregate share metrics by averaging campaign rows. Report campaign-level shares, and use an API-provided account aggregate only if the resource supports it.

### Device and network cuts

Reuse the core additive metrics in separate campaign queries with one segment at a time:

```text
segments.device
segments.ad_network_type
```

Never sum totals from different segmented queries together.

### Conversion actions

Use campaign or customer performance metrics segmented by the compatible conversion fields:

```text
segments.conversion_action
segments.conversion_action_name
segments.conversion_action_category
metrics.conversions
metrics.conversions_value
metrics.all_conversions
metrics.all_conversions_value
metrics.cost_micros
```

Query `conversion_action` separately for primary/secondary status, origin, counting type, and attribution model when selectable. Avoid allocating total cost to a conversion action unless the API resource makes that allocation valid.

## Diagnostic resources

Query the following only when the account contains the applicable campaign type and the data can change a conclusion:

| Diagnostic | Preferred resource/view | Minimum facts |
|---|---|---|
| Ad groups | `ad_group` | Campaign/ad-group identity, status, impressions, clicks, cost, conversions, value |
| Ads and creative | `ad_group_ad` and compatible asset views | Ad identity/type/status, strength/policy where exposed, impressions, cost, conversions, value |
| Keywords | `keyword_view` | Keyword text, match type, status, quality score components, impressions, clicks, cost, conversions, value |
| Search terms | `search_term_view` | Query text, campaign/ad group, targeting status, impressions, clicks, cost, conversions, value |
| Performance Max queries | `campaign_search_term_view` when supported | Query/category, campaign, impressions/clicks/conversions where exposed |
| Landing pages | `landing_page_view` or `expanded_landing_page_view` | URL, clicks, cost, conversions, conversion value |
| Geography | `user_location_view` and geo target constants | Country/region/city or most useful supported level, clicks, cost, conversions, value |
| Demographics | `age_range_view`, `gender_view` | Segment, impressions, clicks, cost, conversions, value |
| Performance Max | `asset_group`, asset-group asset and product-group views | Asset group/asset/product identity, status/performance label, impressions/clicks/cost/conversions/value where supported |
| Shopping | `shopping_performance_view` or product views | Product identifiers and dimensions, impressions/clicks/cost/conversions/value/orders/revenue where supported |
| Calls | campaign/customer call-compatible metrics | Phone impressions, phone calls, phone-through rate |
| Change history | `change_event` | Change time, resource, operation, user/client type, changed fields; obey the API's 30-day window and row limit |

## Pagination and row handling

- Prefer `SearchStream` for large result sets. If using paged search, follow page tokens until exhaustion.
- Preserve raw identifiers so duplicate names do not collapse distinct entities.
- Store enough decimal precision for modeled conversions and values.
- Treat missing rows and explicit zeros differently when possible.
- Keep extraction artifacts temporary and outside the final reports folder; the final folder is for the Markdown report only.
- Record API version, query families completed, failed/unsupported fields, and reconciliation results in the report appendix.

## Error handling

- Authentication/authorization failure: identify the missing credential or account permission without exposing a secret, then stop.
- Invalid field combination: inspect field compatibility, split the query, and retry only the affected family.
- Rate limit or transient server error: use bounded exponential backoff and honor retry metadata. Do not retry indefinitely.
- Partial family failure: continue safe independent queries, mark the unavailable section precisely, and lower report confidence.
- Wrong customer, currency, or time zone: stop and resolve before producing the report.
