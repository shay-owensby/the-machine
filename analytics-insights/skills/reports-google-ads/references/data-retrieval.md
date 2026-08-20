# Data retrieval

`fetch_google_ads.py` runs one GAQL query per dataset per period against the
Google Ads REST endpoint (`googleAds:search`), pages through every result, and
writes them all into one raw JSON file.

## What is retrieved

| Dataset | Resource | Periods | Required | What it is for |
|---|---|---|---|---|
| `customer` | `customer` | — | yes | Account name, currency, **time zone**, manager/test flags, status |
| `account_totals` | `customer` | both | yes | Headline KPIs, independent of the campaign list |
| `daily` | `customer` + `segments.date` | both | yes | Trend charts, and checking days actually have data |
| `campaigns` | `campaign` (+ `campaign_budget`) | both | yes | Campaign comparison, impression share, budgets |
| `device` | `campaign` + `segments.device` | both | no | Traffic and conversion mix |
| `network` | `campaign` + `segments.ad_network_type` | both | no | Search vs Partners vs Display vs YouTube mix |
| `ad_groups` | `ad_group` | both | no | Where inside a campaign the money goes (top 100 by cost) |
| `keywords` | `keyword_view` | both | no | Keyword-level spend and conversions (top 100 by cost) |
| `search_terms` | `search_term_view` | current only | no | What people actually typed; waste hunting (top 200 by cost) |
| `conversion_actions_meta` | `conversion_action` | — | no | Names, categories, counting type, whether an action is in `conversions` |
| `conversion_performance` | `customer` + conversion-action segments | both | no | Volume per conversion action |

Each optional dataset fails independently. A failure is recorded in `errors[]`
with its message, error code and a hint, and the section is `null` — meaning
**unavailable**, which is not the same as an empty list meaning "queried, none
found". Downstream code distinguishes the two and so must any report.

`--skip device,network,ad_groups,keywords,search_terms,conversion_actions`
trims a run. Skipping keywords and search terms roughly halves the query count
on a large account.

## Metrics retrieved

Base counts (everything else is derived from these):

```
metrics.impressions, metrics.clicks, metrics.cost_micros,
metrics.conversions, metrics.conversions_value,
metrics.all_conversions, metrics.all_conversions_value
```

Also selected, and used as a cross-check rather than as the source of truth:

```
metrics.ctr, metrics.average_cpc, metrics.cost_per_conversion,
metrics.value_per_conversion, metrics.conversions_from_interactions_rate
```

Impression share, campaign level only:

```
metrics.search_impression_share
metrics.search_budget_lost_impression_share
metrics.search_rank_lost_impression_share
metrics.search_absolute_top_impression_share
metrics.search_top_impression_share
```

**Why derive rather than take.** CTR, CPC, CPA and ROAS are all recomputed from
the base counts. Two reasons: an average cannot be summed across rows (an
account CTR is not the mean of its campaigns' CTRs), and a derived figure can be
checked against the two numbers next to it in the same table. The analysis
compares its derived CTR against the API's own and notes any difference beyond
rounding.

## Units and shapes the REST surface returns

- **int64 arrives as a JSON string**: `"impressions": "42000"`. Everything is
  coerced through `ads.num()`.
- **Money arrives in micros**: `cost_micros: "12345678"` is 12.345678 in account
  currency. `ads.micros()` divides by 1,000,000.
- **`conversions_value` and `all_conversions_value` are plain doubles**, already
  in account currency — *not* micros. Dividing them by a million is a common and
  spectacular error.
- **Impression share metrics are fractions**: `0.4123` is 41.23%.
- **Impression share is capped at 0.9** — Google reports `> 90%` as exactly 0.9.
  Treat 90% as "90% or more".
- **An absent key means the API did not return the field.** Carried through as
  `None`. Never defaulted.

## Availability by campaign type

Not every metric exists for every campaign. The API returns nothing rather than
zero, and the analysis excludes those campaigns from weighted account figures
instead of dragging them down with data that does not exist.

| Campaign type | Impression share | Search terms | Keywords |
|---|---|---|---|
| Search | yes | yes | yes |
| Shopping | partial (`search_impression_share` only in some accounts) | yes | no (product groups) |
| Performance Max | **no** | limited (search themes, separate report) | no |
| Display | no | no | no |
| Video / Demand Gen | no | no | no |
| App | no | no | no |

Consequences worth stating in a report: an account that is mostly Performance
Max has **no meaningful account-level impression share**, and the analysis says
what percentage of impressions its impression-share figure actually covers.

## Conversions vs all conversions

- `metrics.conversions` counts only conversion actions with *Include in
  "Conversions"* set. This is what bidding optimises toward and what the report
  headlines.
- `metrics.all_conversions` counts everything, including actions deliberately
  excluded from bidding.

Per-action figures come from `conversion_performance`, which segments by
conversion action. **Segmenting by conversion action is only compatible with the
`all_conversions` family**, so per-action numbers are all-conversions numbers and
are labelled as such. They will not sum to the headline `conversions` figure, and
presenting them as if they should is a bug in the report, not the data.

## Row caps

`ad_groups` and `keywords` are capped at 100 rows by cost (`--top-n`), search
terms at 200 (`--search-terms-limit`). When a query hits its cap the run adds a
warning: the list is the top rows by cost, **not** the account, and totals must
never be summed from it. Account and campaign datasets are uncapped.

## Pagination, retries, and versions

- Every query follows `nextPageToken` to the end. No dataset is silently
  truncated by paging.
- Transient failures (429, 500, 502, 503, 504, network errors) retry up to five
  times with exponential backoff and jitter. A 401 forces one token refresh and
  retries once.
- If the configured API version has been sunset, the client walks down
  `CANDIDATE_VERSIONS` until one answers, and records the switch as a warning.
  Pin `GOOGLE_ADS_API_VERSION` to stop the ladder being needed.

## The raw file

```jsonc
{
  "schema": "reports-google-ads/raw@1",
  "generated_at": "2026-08-19T09:12:04+01:00",
  "api_version": "v21",
  "account": { "customer_id", "name", "currency", "time_zone",
               "is_manager", "is_test_account", "status", "login_customer_id" },
  "periods": { "current": {"start","end","days"},
               "previous": {"start","end","days"},
               "basis": "how the window was chosen",
               "time_zone": "America/New_York" },
  "datasets": { "<name>": { "current": [rows] | null, "previous": [rows] | null } },
  "errors":   [ { "dataset", "required", "message", "error_code",
                  "http_status", "hint", "retryable" } ],
  "warnings": [ "..." ],
  "config":   { "agency_env", "client_env", "login_customer_id", "customer_id" }
}
```

Rows are the API's own JSON, unmodified — camelCase keys, string int64s, micros
intact. Nothing is rounded, renamed or filled in on the way to disk, so the file
is a faithful record of what the account said on the day it was asked.

No secret is written into it. `config` holds file paths and customer IDs only.
