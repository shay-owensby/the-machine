# The output contract

`*_analysis.json`, schema `reports-google-ads/analysis@1`. This is what another
agent consumes; it should never need the raw file or the API to write a report.

## Top level

| Field | Type | What it is |
|---|---|---|
| `schema` | string | `reports-google-ads/analysis@1` |
| `generated_at` | ISO 8601 | When the analysis ran (not when the data was retrieved) |
| `source_raw_file` | path | The retrieval file it was built from |
| `api_version` | string | Google Ads API version used |
| `account` | object | See below |
| `periods` | object | See below |
| `kpis` | array | KPI change records, in report order |
| `kpis_by_key` | object | The same records keyed by metric |
| `impression_share_coverage` | object\|null | How much of the account the IS figure covers |
| `campaigns` | array | Per-campaign comparison |
| `segments` | object | `device` and `network` arrays, or null |
| `conversion_actions` | array | Per-action volumes and metadata |
| `top_lists` | object | `keywords`, `search_terms`, `ad_groups` — capped, current period |
| `trend` | object | `daily[]` for both periods |
| `findings` | object | `strengths`, `weaknesses`, `anomalies`, `opportunities`, `observations` |
| `recommended_actions` | array | Derived from findings |
| `data_quality` | object | Checks, warnings, errors, unavailable metrics, insufficient data |
| `charts` | array | Chart manifest (populated by `make_charts.py --update-analysis`) |
| `tables` | object | Pre-rendered Markdown: `kpi`, `campaigns`, `device`, `network` |
| `thresholds` | object | The materiality and sample-size bars this run used |

## `account`

```jsonc
{ "customer_id": "1234567890", "name": "Example Client Account",
  "currency": "USD", "time_zone": "America/New_York",
  "login_customer_id": "9876543210", "status": "ENABLED",
  "is_test_account": false, "optimization_score": 0.78 }
```

`currency` governs every money figure in the file. Nothing is converted; a
report states the currency once and uses it throughout.

## `periods`

```jsonc
{ "current":  { "start": "2026-07-20", "end": "2026-08-18", "days": 30 },
  "previous": { "start": "2026-06-20", "end": "2026-07-19", "days": 30 },
  "basis": "most recent 30 completed days ending yesterday in America/New_York",
  "time_zone": "America/New_York",
  "comparable": true }
```

`comparable: false` means the two windows are different lengths and totals are
not comparable. Both ranges appear verbatim in every report and every chart.

## `kpis[]` / `kpis_by_key{}`

Keys, in report order: `cost`, `impressions`, `clicks`, `ctr`, `average_cpc`,
`conversions`, `conversion_rate`, `cost_per_conversion`, `conversions_value`,
`roas`, `search_impression_share`, `search_lost_is_budget`,
`search_lost_is_rank`.

```jsonc
{ "key": "cost_per_conversion", "label": "CPA", "unit": "currency",
  "better_when": "lower",           // higher | lower | context
  "current": 26.29, "previous": 26.79,
  "absolute_change": -0.50,
  "percent_change": -1.87,          // null = undefined, never 0
  "availability": "available",      // available | partial | unavailable
  "direction": "down",              // up | down | flat | n/a
  "verdict": "flat",                // improved | declined | ambiguous | flat | new | unknown
  "material": false,
  "notes": ["Below the materiality threshold ..."] }
```

Units: `currency` (account currency), `int`, `rate` (already ×100, so `1.54`
means 1.54%), `decimal` (ROAS, conversion counts).

**Read `availability` before anything else.** On `partial` or `unavailable` the
value is not a number to print.

## `campaigns[]`

```jsonc
{ "id": "12", "name": "Search — Non-Brand Core",
  "status": "ENABLED", "channel_type": "SEARCH", "channel_sub_type": null,
  "bidding_strategy": "MAXIMIZE_CONVERSIONS",
  "daily_budget": 120.0, "shared_budget": false,
  "present_in": "both",             // both | current only | previous only
  "current":  { "impressions", "clicks", "cost", "conversions", "conversions_value",
                "ctr", "average_cpc", "conversion_rate",
                "cost_per_conversion", "roas", "value_per_conversion" },
  "previous": { ...same... },
  "impression_share": { "search_impression_share", "search_lost_is_budget",
                        "search_lost_is_rank", "search_absolute_top_is" },
  "changes": { "<metric>": <change record> },
  "share_of_spend": 47.8,
  "flags": ["budget_constrained", "rank_constrained"] }
```

Ordered by current-period spend, descending. Flags: `sparse_data`,
`spend_no_conversions`, `cpa_well_above_account`, `cpa_well_below_account`,
`budget_constrained`, `rank_constrained`, `paused_but_spent`,
`drove_account_spend_change`, `roas_well_above_account`.

Money is in account currency; rates are ×100; impression share is ×100.

## `findings`

Five arrays. Each finding: `id`, `type`, `title`, `statement`, `evidence[]`,
`severity`, `confidence`, `scope`, `entity`. Campaign findings carry the
campaign id in the finding id (`campaign_high_cpa:14`).

Order them for a report by `severity` then by the absolute money involved, not
by the order they appear.

## `recommended_actions[]`

```jsonc
{ "action": "Raise the daily budget on Search — Services (currently $60.00/day) and re-check impression share after 7-14 days.",
  "reason": "It lost 11.0% of available search impressions to budget while converting at $32.50, at or below the account average ...",
  "evidence": ["Search — Services: search lost IS (budget) 11.0%", "..."],
  "expected_impact": "Recovering the lost impression share at today's conversion rate would add conversions at roughly today's CPA. Impression share does not scale linearly with budget, so treat the figure as a ceiling, not a forecast.",
  "priority": "High",               // High | Medium | Low
  "confidence": "high",
  "from_finding": "campaign_budget_constrained:31" }
```

Sorted by priority. May be empty — an account with nothing wrong gets no
recommendations, and inventing some to fill a section is the failure this field
is designed to prevent.

## `data_quality`

See `references/data-validation.md`. Everything in `warnings` belongs in the
report.

## `tables`

Pre-rendered Markdown, already formatted in the account's currency:
`kpi`, `campaigns`, `device`, `network` (the last two may be null).

Paste them rather than retyping figures — every re-typed number is a chance to
mistype one. If a table needs different columns, build it from the structured
fields; do not hand-edit the numbers in these strings.

## `charts[]`

The manifest from `make_charts.py`. Entries with `status: "drawn"` carry `file`,
`filename`, `title` and `alt`; entries with `status: "not drawn"` carry
`reason`, which is a sentence the report can use to explain the gap.

## Consuming it from another agent

```bash
A=analytics-insights/google-ads/_data/1234567890_2026-07-20_2026-08-18_analysis.json

python3 -c "
import json,sys; d=json.load(open(sys.argv[1]))
print(d['account']['name'], d['account']['currency'])
print(d['periods']['current'], d['periods']['previous'])
print(d['tables']['kpi'])
for f in d['findings']['weaknesses']: print(f['severity'], f['title'])
for r in d['recommended_actions']: print(r['priority'], r['action'])
for w in d['data_quality']['warnings']: print('WARN', w)
" $A
```

Stability: the schema string changes if any field is removed or its meaning
changes. Added fields do not bump it. Code against `availability` and `verdict`
rather than inferring state from `null`.
