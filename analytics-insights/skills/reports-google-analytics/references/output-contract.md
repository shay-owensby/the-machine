# The output contract

`analysis.json` is what the reporting agent reads. It is designed so the agent
never has to open a raw API response, recompute a percentage, or decide whether
a missing value means zero.

Schema: `reports-google-analytics/analysis@1`

---

## Top level

```jsonc
{
  "schema": "reports-google-analytics/analysis@1",
  "generated_at": "2026-08-20T06:15:00-04:00",
  "source_raw": "/…/data/raw.json",

  "property":   { … },   // who this is about
  "periods":    { … },   // exactly which days
  "key_events": { … },   // naming, definitions, what was declared
  "ecommerce_state": "active | no_data | unavailable",

  "kpis":        [ … ],  // ordered, ready to table
  "kpis_by_key": { … },  // the same records, keyed
  "sections":    { … },  // acquisition, content, engagement, events, devices,
                         // geography, ecommerce, trends
  "findings":      { … },// grouped by type
  "findings_flat": [ … ],// the same findings in one list
  "recommended_actions": [ … ],
  "data_quality":  { … },
  "tables":        { … },// pre-rendered Markdown
  "charts":        [ … ] // manifest, once make_charts has run
}
```

---

## `property`

```jsonc
{
  "property_id": "123456789",
  "name": "Acme Home Services",     // null when the Admin API is unavailable — never invented
  "time_zone": "America/New_York",
  "currency": "USD",
  "industry": "OTHER",
  "created": "2023-04-11T09:12:00Z",
  "property_type": "PROPERTY_TYPE_ORDINARY",
  "data_streams": [ { "name": "Web", "type": "WEB_DATA_STREAM", "uri": "…", "measurement_id": "G-…" } ],
  "site_url": "https://www.acme.com",
  "client_name": "Acme Ltd",
  "admin_api_available": true
}
```

A `null` name means the name is unknown. The report writes "GA4 property
123456789", not a guess.

## `periods`

```jsonc
{
  "current":  { "start": "2026-07-21", "end": "2026-08-19", "days": 30 },
  "previous": { "start": "2026-06-21", "end": "2026-07-20", "days": 30 },
  "basis": "most recent 30 completed days ending yesterday in America/New_York",
  "time_zone": "America/New_York"
}
```

`basis` is a sentence the report can quote directly. Every report states both
date ranges in full.

## `kpis[]` — one record per metric

```jsonc
{
  "key": "sessionKeyEventRate",
  "label": "Session Key Event Rate",
  "unit": "int | decimal | rate | currency | duration",
  "better_when": "higher | lower | context",
  "current": 4.18,
  "previous": 3.92,
  "absolute_change": 0.26,          // null when it cannot be computed
  "percent_change": 6.63,           // null against a zero or missing baseline
  "direction": "up | down | flat | n/a | unknown",
  "verdict": "improved | declined | flat | ambiguous | new | unknown",
  "material": true,
  "availability": "available | partial | unavailable",
  "derived": true,                  // present only when computed, not returned
  "notes": ["…"]                    // always read these; they carry the caveats
}
```

`rate` values are percentage points (4.18 means 4.18%), converted once at
extraction. `duration` is seconds.

**Read `verdict`, not the sign of `percent_change`.** The verdict already
accounts for what the metric means and for the cross-checks. **Read `notes`**
— that is where "sessions fell while outcomes rose, so this is a mix change"
lives.

## `sections`

| Section | Contains |
|---|---|
| `acquisition` | `session_channels`, `session_source_medium`, `session_campaigns`, `first_user_channels`, `attribution_note` |
| `content` | `landing_pages`, `pages`, `hostnames`, `note` |
| `engagement` | `summary` — the engagement KPI records |
| `events` | `events[]`, `key_event_definitions`, `key_event_names`, `declared_primary_events`, `meaning_note` |
| `devices` | `device_categories`, `browsers`, `operating_systems`, `platforms` |
| `geography` | `countries`, `regions`, `cities`, `note` |
| `ecommerce` | `state`, `included`, `funnel`, `revenue_by_channel`, `revenue_by_device`, `items`, `note` |
| `trends` | `current[]`, `previous[]`, `missing_days_current`, `anomalies`, `within_period_drift` |

Every breakdown row:

```jsonc
{ "key": "Organic Search", "keys": ["Organic Search"],
  "current":  { "sessions": 19400, "engagementRate": 63.0, "keyEvents": 512, … },
  "previous": { … } }        // null when the segment did not exist last period
```

**`null` for a whole section means the dataset was never retrieved.** Omit that
section from the report and say why. It does not mean the property has nothing.

A `previous` of `null` on a row is a genuinely new segment — usually the most
interesting row in the table.

`trends.current[]` has one entry per calendar day, each with
`"returned": true|false`. A `false` day is a day GA4 returned no rows for. It is
not zero traffic.

## `findings` and `findings_flat`

Grouped into `strengths`, `weaknesses`, `risks`, `opportunities`, `anomalies`,
`observations`. Record shape is in `analysis-rules.md` §8.

Rank by `severity`, then by `confidence`. A `low` confidence finding belongs in
the report only with its caveat attached.

## `recommended_actions[]`

```jsonc
{
  "action": "…", "reason": "…", "evidence": ["…"],
  "expected_impact": "…", "priority": "High | Medium | Low",
  "confidence": "high | medium | low",
  "from_finding": "device_key_event_gap"
}
```

Already deduplicated and sorted by priority.

## `data_quality`

```jsonc
{
  "checks": [ { "check": "…", "status": "pass|info|warn|fail", "detail": "…" } ],
  "warnings": ["…"],
  "unavailable_metrics": [ { "metric": "…", "api_name": "…", "reason": "…" } ],
  "api_errors": [ { "dataset": "…", "message": "…", "hint": "…", "retryable": true } ],
  "periods_comparable": true,
  "material_thresholds": { "percent": 10.0, "absolute": { … }, "min_sessions_to_judge": 100 }
}
```

Every `fail`, and every `warn` that affects a number in the report, must appear
in the report's own data-quality note. They are not internal diagnostics.

## `tables`

Pre-rendered Markdown, ready to paste: `kpi`, `channels`, `first_user_channels`,
`landing_pages`, `devices`, `events`, `ecommerce`. A `null` table means there
was nothing to render — omit the section rather than printing an empty table.

## `charts[]`

Written by `make_charts.py --update-analysis`, also at `charts/charts.json`:

```jsonc
{
  "id": "daily-performance",
  "file": "/absolute/path/…png",
  "relative_path": "./charts/daily-performance.png",
  "markdown": "![Daily performance](./charts/daily-performance.png)",
  "title": "…", "alt": "…",
  "status": "drawn | not drawn",
  "reason": "…"                   // present when not drawn
}
```

Embed `markdown` verbatim. **Never describe a chart whose status is
`not drawn`** — say the visual is unavailable and why, or leave it out.

---

## The five rules a consumer of this file must follow

1. `null` is never zero. It is "not available", and it must print as that.
2. `percent_change: null` with `verdict: "new"` means the baseline was zero.
   Report the absolute figure; never write ∞ or 100%.
3. `verdict` outranks the sign of the change. It already knows what the metric
   means.
4. `notes` are not decoration. They carry the caveat that makes the number
   honest.
5. A `null` section or table means the data was not retrieved. Say so; do not
   render it as empty.
