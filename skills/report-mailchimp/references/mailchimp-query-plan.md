# Mailchimp Marketing API Query Plan

Use the official [Marketing API reference](https://mailchimp.com/developer/marketing/api/) as the live authority. API version and availability can change; record the observed API version when available. All calls in this plan are `GET` requests.

## 1. Account, scope, and dates

1. `GET /`
   - Validate authentication and capture `account_id`, `account_name`, `role`, `account_timezone`, `account_industry`, `pricing_plan_type`, `total_subscribers`, and `industry_stats`.
   - Do not retain or report personal account fields.
2. `GET /lists?count=1000&offset=<n>`
   - Inventory all audiences/lists and validate configured list IDs.
   - Capture list name, active state, date created, permission reminder, campaign defaults, list rating, current `stats`, and the linked store relationship where returned.
   - Treat `stats.member_count` as an observation-time snapshot.
3. `GET /ecommerce/stores?count=1000&offset=<n>`
   - Run when commerce is connected or campaign reports return e-commerce values.
   - Validate configured store IDs and capture list association, platform, currency, and connection/update metadata. Never retrieve customers, carts, or orders for an aggregate campaign report.
4. Resolve the reporting zone and run `scripts/report_dates.py`. Record the exact half-open current and previous timestamp intervals and the API observation time.

## 2. Campaign and report inventory

Query a combined widened 60-day range, then apply exact local boundaries and scope filters client-side:

- `GET /campaigns?status=sent&since_send_time=<widened-start>&before_send_time=<widened-end>&count=1000&offset=<n>`
- `GET /reports?since_send_time=<widened-start>&before_send_time=<widened-end>&count=1000&offset=<n>`

Retrieve all fields initially so numeric fields newly added by Mailchimp are not silently omitted. Match campaign metadata to report rows by ID. Include campaign title, subject line, preview text, type, status, list ID/name, send time, archive URL, tracking configuration, recipients/segment metadata, and report metrics. Do not include reply-to addresses or recipient data in the report.

Split rows into `current` and `previous` using `start <= send_time < end_exclusive` in the selected zone. Record campaigns returned by only one inventory endpoint as a data-quality finding.

The main report payload provides the canonical campaign KPIs, including:

- emails sent, delivery status, bounces, syntax errors, complaints, unsubscribes, forwards;
- total/unique/proxy-excluded opens and open rates;
- total/unique/subscriber clicks and click rate;
- Facebook sharing, industry stats, list stats;
- A/B fields, Timewarp, timeseries, e-commerce totals, and any new numeric fields returned by the live API.

## 3. Per-campaign aggregate diagnostics

For every in-scope campaign in both periods, retrieve each applicable endpoint. Paginate collection endpoints to `total_items`.

| Family | Endpoint | Use |
|---|---|---|
| Full report | `/reports/{campaign_id}` | Reconcile the collection row and capture fields omitted from list responses. |
| Advice | `/reports/{campaign_id}/advice` | Mailchimp-generated feedback based on opens, clicks, bounces, unsubs, and complaints; treat as supporting context, not authoritative strategy. |
| Click details | `/reports/{campaign_id}/click-details` | Link URL, total clicks, unique clicks, percentages, and variant splits. Sanitize displayed URLs and never expose tokens or personal query parameters. |
| Domain performance | `/reports/{campaign_id}/domain-performance` | Sent, delivered, bounce, open, click, unsubscribe, and percentage metrics by mailbox domain. |
| Locations | `/reports/{campaign_id}/locations` | Top open locations and proxy-excluded opens. Label this as open-derived and potentially incomplete. |
| EepURL | `/reports/{campaign_id}/eepurl` | Tracked campaign-URL clicks, referrers, tweets, and retweets when supported. |
| Product activity | `/reports/{campaign_id}/ecommerce-product-activity` | Product-level revenue, purchases, and recommendation-attributed activity when commerce is supported. |
| Sub-reports | `/reports/{campaign_id}/sub-reports` | A/B, multivariate, RSS, Timewarp, and other child-campaign diagnostics. Do not add child metrics to an already complete parent total. |

Do not call these recipient-level endpoints for ordinary reporting: `open-details`, `email-activity`, `sent-to`, `unsubscribed`, clicked-link `members`, individual abuse reports, or list `members`. Their aggregate counts already exist in the report resources, and the detailed rows can expose personal data.

## 4. Audience health and growth

For each scoped audience:

- `GET /lists/{list_id}/activity?count=1000&offset=<n>`
  - Retrieve enough daily rows to cover both exact 30-day windows.
  - Aggregate emails sent, unique opens, recipient clicks, hard bounces, subscribes, unsubscribes, other adds, and other removes by exact day.
  - Use campaign reports—not list activity—as the canonical campaign engagement source. Use list activity for audience-flow and cross-checking only.
- `GET /lists/{list_id}/growth-history?count=1000&offset=<n>`
  - Use only as monthly context and reconciliation. Do not present monthly rows as exact 30-day results.
- `GET /lists/{list_id}/clients`
  - Optional snapshot diagnostic for email-client mix. It has no exact period filter; label it observation-time context, not a period comparison.
- `GET /lists/{list_id}/locations`
  - Optional snapshot diagnostic for audience geography. Do not confuse it with campaign open locations.

Do not call `/audiences` beta endpoints unless the stable list endpoints cannot provide a required aggregate and the user accepts beta coverage. Never use contact endpoints for KPI totals.

## 5. Automation and experiment context

When any report type is `automation` or `auto`, or the user specifically asks about automations:

- `GET /automations?count=1000&offset=<n>`
- `GET /automations/{workflow_id}/emails?count=1000&offset=<n>` for applicable classic workflows.

Treat workflow `emails_sent` as lifetime/current-state context unless it can be matched to date-bounded campaign reports. Customer Journey/Automation Flow coverage may differ from Classic Automations; disclose what the Marketing API returned rather than assuming full workflow coverage.

For A/B or multivariate campaigns, compare child variants on delivered volume, proxy-excluded open rate, click rate, CTOR, unsub rate, complaint rate, revenue, and the declared test variable. Avoid declaring a winner when sample size, allocation, statistical confidence, or post-test selection data is unavailable.

## 6. Reconciliation and completeness ledger

Before writing:

1. Confirm current and previous campaign ID sets, campaign counts, list scope, and exact date assignment.
2. Confirm every paginated collection reached `total_items` or document the shortfall.
3. Confirm parent/child deduplication and every numerator/denominator used in rate calculations.
4. Confirm all numeric performance fields from applicable responses appear either in a canonical KPI row, a detailed table, or `All Additional Numeric KPI Fields Returned by Mailchimp`. Exclude IDs, pagination metadata, coordinates, time-zone offsets, and configuration enums from the KPI inventory.
5. Confirm every missing endpoint or field is represented as `N/A — <reason>` rather than zero.
6. Confirm no recipient email, IP address, subscriber hash, personal URL token, authorization data, or raw response remains in the report or output directory.

Record the result in the report's API coverage ledger with one row per query family, including filters, pagination status, current/previous availability, and reconciliation notes.
