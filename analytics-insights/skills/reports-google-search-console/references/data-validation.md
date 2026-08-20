# Data quality: the checks, and which ones block a report

`analysis["data_quality"]` holds five things:

| Field | What it is |
|---|---|
| `checks[]` | Every check run, with `pass` / `warn` / `fail` / `skipped` and a detail line |
| `warnings[]` | **Everything here belongs in the report**, in the report's own words |
| `errors[]` | Retrieval failures carried through from the raw file |
| `unavailable[]` | Datasets and metrics that could not be retrieved |
| `insufficient_data[]` | Scopes too small to support a conclusion |
| `limitations[]` | The standing Search Console caveats that apply to every report |

A warning that only exists in a JSON file is a warning nobody received.

## The checks

| Check | Fails / warns when |
|---|---|
| reporting periods stated | never fails — it records both ranges into the contract |
| equal-length periods | the two windows differ in length |
| finalised data only | the run used `dataState=all`, or the latest finalised date was not established |
| fresh data excluded | records how many provisional days were deliberately left out |
| property access | records the identifier, type and permission level actually used |
| `<dataset>` retrieved | a core dataset is missing entirely |
| `<dataset>` complete | the extract hit a row cap |
| query/page coverage of property clicks | dimensional clicks are below 80% (warn) or 50% (fail) of property clicks |
| sample size | fewer than 30 clicks in the current period |
| branded/non-branded split | skipped, with the reason, when no brand terms are configured |
| search appearance | skipped when the property returns none |

## Unavailable is not zero, and empty is not zero either

Three different states, three different sentences:

| State | Means | The report says |
|---|---|---|
| **Unavailable** | The query failed or was skipped | "Country data could not be retrieved this period" |
| **Empty** | The query succeeded and returned no rows | "No search appearance data is reported for this property" |
| **Zero** | The API returned a real 0 | "Zero clicks" |

Nothing in the pipeline converts one into another. A missing metric stays `None`
from the API response to the contract, and the presentation layer prints "not
available".

## Dimensional totals never equal property totals

This is the check people query most, so the analysis computes it explicitly:

```jsonc
"reconciliation": {
  "dimension_clicks": 5840, "property_clicks": 12480,
  "coverage_pct": 46.8,
  "note": "Search Console withholds rows from dimensional exports, so this total is a floor..."
}
```

Search Console withholds rows — anonymised queries above all, to protect rare
searches that could identify a person. The gap is **not missing traffic and not a
bug**. Property-level KPIs come from the dimensionless query and are the figures
to quote; query and page tables describe the visible subset.

Coverage varies hugely by property. Below 80% the analysis warns so the report
can say what its query tables do and do not represent.

## What blocks a report

**Blocking** — do not write a report:

- Property access failed, or the property is not the client's
- No finalised data exists for the property
- Core retrieval (`totals`, `daily`) failed
- Both periods returned nothing

**Not blocking** — report, and say so plainly:

- An optional dataset failed (countries, search appearance, devices)
- The query or page extract hit a row cap
- The comparison period is empty because the property is new
- The property is too small for confident percentages
- No brand terms are configured
- Charts could not be drawn because matplotlib is missing

## Reading it before writing anything

```bash
python3 -c "import json,sys; d=json.load(open(sys.argv[1])); print(json.dumps(d['data_quality'], indent=2))" \
  analytics-insights/google-search-console/<date>/data/<file>_analysis.json
```

Every entry in `warnings` must appear somewhere in the finished report — most
naturally in the Data notes section. The `limitations` list is the standing set
that applies even to a perfect run, and at least the relevant ones belong in the
report too.
