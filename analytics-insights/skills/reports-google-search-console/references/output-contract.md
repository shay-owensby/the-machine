# The output contract

`*_analysis.json`, schema `reports-google-search-console/analysis@1`. This is
what the `google-search-console` agent consumes; it should never need the raw
file or the API to write a report.

## Top level

| Field | Type | What it is |
|---|---|---|
| `schema` | string | `reports-google-search-console/analysis@1` |
| `generated_at` | ISO 8601 | When the analysis ran (not when the data was retrieved) |
| `source_raw_file` | path | The retrieval file it was built from |
| `property` | object | Identifier, type, permission level |
| `client` | object | `{name}` from `CLIENT_NAME`, or null |
| `search_type` | string | The surface these figures describe — `web` by default |
| `data_state` | string | `final` or `all` |
| `freshness` | object\|null | Latest finalised date and the lag behind it |
| `periods` | object | Both windows, and the basis they were built on |
| `kpis` | array | KPI change records, in report order |
| `kpis_by_key` | object | The same records keyed by metric |
| `trend` | object | Daily series for both periods, anomalies, within-period shape |
| `click_attribution` | object\|null | Where the click change sits: impressions or CTR |
| `queries` | object\|null | The full query analysis |
| `pages` | object\|null | The full page analysis |
| `query_page` | object\|null | Query/page owners and cannibalisation signals |
| `devices` | object\|null | Per-device comparison |
| `countries` | object\|null | Per-country comparison, plus whether geography is material |
| `search_appearance` | object\|null | Result-feature comparison |
| `extra_search_types` | object | Other surfaces, each with its own KPIs — never merged |
| `sitemaps` | object\|null | Sitemap status and any problems found |
| `url_inspection` | object\|null | Index diagnostics for selected URLs |
| `brand` | object\|null | Branded/non-branded split — **null unless brand terms are configured** |
| `brand_note` | string | Present when `brand` is null: why, and how to enable it |
| `thresholds` | object | Every bar this run used, including how the floors were derived |
| `findings` | object | `strengths`, `weaknesses`, `risks`, `opportunities`, `anomalies`, `observations` |
| `data_quality` | object | Checks, warnings, errors, unavailable, insufficient data, limitations |
| `recommended_actions` | array | Derived from findings |
| `tables` | object | Pre-rendered Markdown tables |
| `charts` | array | Chart manifest (populated by `make_charts.py --update-analysis`) |

## `property`

```jsonc
{ "site_url": "https://www.example.com/", "property_type": "url_prefix",
  "display": "www.example.com", "permission_level": "siteFullUser", "access": "ok" }
```

`property_type` is `domain` or `url_prefix`, and it belongs in the report header:
a domain property includes subdomains a URL-prefix property never sees.

## `periods`

```jsonc
{ "current":  { "start": "2026-07-18", "end": "2026-08-16", "days": 30 },
  "previous": { "start": "2026-06-18", "end": "2026-07-17", "days": 30 },
  "lag_days": 0, "comparable": true,
  "basis": "the most recent 30 finalised days for this property (latest finalised date
            2026-08-16), against the 30 days immediately before them" }
```

`comparable: false` means the windows differ in length and totals are not
like-for-like. Both ranges appear verbatim in every report and every chart.

## `freshness`

```jsonc
{ "latest_final": "2026-08-16", "latest_including_fresh": "2026-08-18",
  "lag_days": 3, "fresh_days_available": 2, "queried_through": "2026-08-19" }
```

`latest_final` belongs in the report header. `fresh_days_available` is what was
deliberately excluded, and saying so pre-empts "why does this stop three days
ago?".

## `kpis[]` / `kpis_by_key{}`

Keys, in report order: `clicks`, `impressions`, `ctr`, `average_position`.

```jsonc
{ "key": "average_position", "label": "Average position", "unit": "position",
  "better_when": "lower",
  "current": 11.4, "previous": 12.1,
  "absolute_change": -0.7,
  "percent_change": -5.79,
  "availability": "available",      // available | partial | unavailable
  "direction": "down",              // arithmetic: up | down | flat | n/a
  "verdict": "improved",            // interpretation: improved | declined | flat | new | unknown
  "material": true,
  "notes": ["Lower is better: a fall in this number is an improvement. ..."] }
```

Units: `int` (clicks, impressions), `rate` (CTR, already ×100 — `2.40` means
2.40%), `position` (lower is better).

**Read `availability` first.** On anything but `available` the value does not go
into a table as a number. **`percent_change: null` means undefined, not zero.**

## `trend`

```jsonc
{ "current": [{"date": "2026-07-18", "clicks": 402, "impressions": 11203,
               "ctr": 3.589, "position": 11.32}, ...],
  "previous": [...],
  "anomalies": [{"date": "2026-08-02", "metric": "clicks", "kind": "spike",
                 "value": 784, "typical": 236, "baseline": "typical weekend",
                 "deviation_pct": 232.9, "confidence": "high", "statement": "..."}],
  "shape": {"trend": "rising", "change_pct": 18.4, "statement": "..."} }
```

`shape` compares the two halves of the current period — a 30-day total can be
flat while the last ten days fall off a cliff.

## `queries` / `pages`

Identical structure. Page records carry an extra `path` field, which is what
belongs in a table.

```jsonc
{ "rows_analysed": 26,
  "reconciliation": { "dimension_clicks": 5840, "property_clicks": 12480,
                      "coverage_pct": 46.8, "note": "..." },
  "ctr_benchmarks": { "4-10": {"median_ctr": 5.93, "rows": 11}, ... },
  "impression_floor": 171, "click_floor": 62,
  "top_by_clicks": [...], "top_by_impressions": [...],
  "winners": [...], "losers": [...],
  "ctr_opportunities": [...], "ranking_opportunities": [...],
  "visibility_losses": [...],
  "loss_concentration": {...}, "gain_concentration": {...} }
```

Every row:

```jsonc
{ "query": "widget buying guide", "present_in": "both",
  "clicks": 120, "impressions": 42000, "ctr": 0.29, "position": 4.8,
  "previous_clicks": 103, "previous_impressions": 36120,
  "previous_ctr": 0.29, "previous_position": 5.2,
  "clicks_change": 17, "clicks_change_pct": 16.5,
  "impressions_change": 5880, "impressions_change_pct": 16.3,
  "ctr_change_points": 0.0,
  "position_change": -0.4, "position_moved": "improved",
  "band": "4-10" }
```

`position_moved` is the pre-inverted reading (`improved` / `worsened` / `flat`)
so no consumer has to remember which way position runs.

`present_in` is `both`, `current only` or `previous only`. **A row missing from
one period is not a zero** — Search Console may simply have withheld it.

Opportunity rows carry extra fields: `band_median_ctr`, `ctr_gap_points`,
`clicks_at_band_median` (a ceiling at today's impressions, not a forecast) or
`opportunity_score`, plus `basis` and `caveat` sentences written to be quoted.

CTR opportunities also carry `ceiling_ratio` and `ceiling_is_speculative`. When
the implied gain is more than three times the row's current clicks the ceiling is
flagged: a gap that large usually means the impressions come from queries where
the row ranks well below its average position, so the band median is not a
realistic target. The caveat says so and the derived recommendation drops to
`confidence: low`. **Do not quote a flagged ceiling as an expectation.**

`visibility_losses` rows carry `loss_kind`: `visibility`, `ranking`, `ctr`,
`mixed` or `unclear`.

## `findings`

Six arrays: `strengths`, `weaknesses`, `risks`, `opportunities`, `anomalies`,
`observations`. Each finding:

```jsonc
{ "id": "ctr_down_position_stable", "type": "ctr",
  "title": "CTR fell while average position held",
  "statement": "Click-through rate fell -0.91 pp while average position stayed within 0.3...",
  "evidence": ["CTR: 1.95% vs 2.86% (-0.91 pp, -31.8%)", ...],
  "severity": "high", "confidence": "high",
  "scope": "property", "entity": null,
  "caveat": "A stable average position can still hide a changed SERP..." }
```

Order for a report by `severity`, then by the click volume involved — not by the
order they appear. **`caveat` travels with the finding**: if the finding is used,
its caveat is used.

`confidence: low` almost always means a small sample. A low-confidence finding is
a thing to watch, not a thing to assert.

## `recommended_actions[]`

```jsonc
{ "action": "Rewrite the title tag and meta description for /blog/widget-buying-guide/,
             then re-check CTR after two to four weeks of finalised data.",
  "reason": "The page holds 96,000 impressions at average position 4.6 but converts them
             at 0.44%, against a median of 5.93% for this property's own pages in the same
             position band.",
  "evidence": ["96,000 impressions at position 4.6 with 0.44% CTR, against a median of ..."],
  "expected_impact": "Reaching the property's own band median at today's impression volume
                      is worth about 5,270 additional clicks per 30 days. That is a ceiling
                      computed from current impressions, not a forecast, and it does not
                      change rankings.",
  "priority": "High",              // High | Medium | Low
  "confidence": "medium",
  "from_finding": "page_ctr_opportunities" }
```

Sorted by priority. **May be empty** — a property with nothing wrong gets no
recommendations, and inventing some to fill a section is the failure this field
is designed to prevent.

## `extra_search_types`

```jsonc
{ "image": { "search_type": "image", "supports_query_dimension": true,
             "kpis": [ ...four change records... ],
             "note": "A separate Search Console surface... NOT part of the web totals
                      and must never be added to them." } }
```

## `data_quality`

See `references/data-validation.md`. Everything in `warnings` belongs in the
report; `limitations` are the standing Search Console caveats that apply even to
a clean run.

## `tables`

Pre-rendered Markdown, already formatted: `kpi`, `top_queries`, `query_winners`,
`query_losers`, `query_ctr_opportunities`, `query_ranking_opportunities`,
`top_pages`, `page_winners`, `page_losers`, `page_ctr_opportunities`,
`page_ranking_opportunities`, `devices`, `countries`, `search_appearance`,
`brand`, `extra_search_types`. Any of them may be absent — an absent table means
there was nothing to put in it.

Paste them rather than retyping figures. Every retyped number is a chance to
mistype one. To restructure a table, build it from the structured fields; do not
hand-edit the numbers in these strings.

## `charts[]`

Entries with `status: "drawn"` carry `file`, `filename`, `title`, `alt` and
`explains`. Entries with `status: "not drawn"` carry `reason` — a sentence the
report can use to explain the gap.

## Consuming it from another agent

```bash
A=analytics-insights/google-search-console/2026-08-16/data/www-example-com_2026-07-18_2026-08-16_analysis.json

python3 -c "
import json,sys; d=json.load(open(sys.argv[1]))
print(d['property']['site_url'], d['property']['property_type'])
print(d['periods']['current'], d['periods']['previous'])
print(d['tables']['kpi'])
for f in d['findings']['weaknesses']: print(f['severity'], f['title'])
for r in d['recommended_actions']: print(r['priority'], r['action'])
for w in d['data_quality']['warnings']: print('WARN', w)
" $A
```

Stability: the schema string changes if a field is removed or its meaning
changes. Added fields do not bump it. Code against `availability` and `verdict`
rather than inferring state from `null`.
