# Charts: the catalogue and the rules behind it

```bash
python3 scripts/make_charts.py \
  --analysis <..._analysis.json> \
  --out analytics-insights/google-search-console/<date>/charts \
  --update-analysis
```

`--update-analysis` writes the manifest back into the analysis file so the
report references charts from one place. The manifest is also written beside the
PNGs as `<stem>_charts.json`.

## The catalogue

| Key | Title | Drawn when | What it argues |
|---|---|---|---|
| `kpi-summary` | Search performance change | Any KPI has both periods | Which headline metrics moved and whether the move was good |
| `organic-click-trend` | Daily organic clicks | 3+ days of click data | Whether the change was steady, a step, or one event |
| `organic-impression-trend` | Daily impressions | 3+ days | Whether visibility moved with clicks or independently |
| `ctr-trend` | Daily click-through rate | 3+ days | Whether conversion of impressions is holding or eroding |
| `position-trend` | Daily average position | 3+ days | Whether ranking movement explains the click trend |
| `query-performance` | Query gains and losses | 2+ comparable queries | Which search terms the change came from |
| `page-performance` | Page gains and losses | 2+ comparable pages | Which pages the change came from |
| `search-opportunities` | Visibility against ranking, by page | 4+ pages with impressions and position | Where big visibility sits at weak positions or weak CTR |
| `device-performance` | Performance by device | 2+ devices | Whether mobile and desktop moved together |
| `country-performance` | Clicks by country | Geography is material | Which markets carry the traffic and which moved |

Ten charts is the ceiling, not the target. **A chart with no sentence beside it
is decoration**, and eight charts with no argument is a data dump. Most reports
carry four to six.

## Rules the charts follow

**One measure per axis.** Never two y-scales on one plot. A dual-axis chart lets
the author imply a relationship by choosing the scales, which is exactly what an
executive report must not do. Device performance is two panels side by side, not
one plot with two axes.

**Average position is drawn upside down.** The y-axis is inverted so an
improvement moves up, and the subtitle says so: *"axis inverted: higher on the
chart is a better position"*. A position chart with a conventional axis reads as
a collapse when the rankings improved — the single most common Search Console
chart error. The axis is also formatted to one decimal place, because rounding
9.4, 9.8 and 10.2 to whole numbers prints "10" three times down the side.

**Colour carries the job, not the mark.** Change charts are diverging — blue
better, red worse, grey no verdict — and *the verdict comes from the analysis,
not from the sign*. A falling average position is blue. Magnitude charts are one
hue. Composition charts use a fixed order.

**Colour is never the only channel.** Every bar carries a direct label, the
legend is present with two or more series, and the report's own tables are the
accessible fallback.

**Both date ranges appear in every chart subtitle.** A chart that outlives its
report still says what it covers.

**Only accepted anomalies are annotated.** The click and impression trends ring
the days the analysis actually accepted as anomalies — not every local minimum.

## Palette

**It is not defined here.** Colour, type, spacing and the chart theme come from
the plugin design system at `design/DESIGN.md`, and the values live in
`design/lib/tokens.py`. `make_charts.py` imports the theme from
`design/lib/charts.py` and defines no colour of its own.

What the roles mean, so a chart can be read without opening the token file:

| Role | Where it comes from |
|---|---|
| Improved | `VERDICT["improved"]` — blue, not green, so it survives red-green deficiency |
| Declined | `VERDICT["declined"]` — red |
| Ambiguous | `VERDICT["ambiguous"]` — grey, for a metric with no direction of its own |
| Below materiality | `VERDICT["flat"]` — pale grey |
| Series 1..5 | `CATEGORICAL[0..4]`, assigned in order, never cycled, never generated |
| Comparison period | `PREVIOUS` |
| Surface / ink / grid | `SURFACE` / `INK` / `GRID` |

Contrast and all-pairs colour-vision separation are **measured, not asserted**:
run `python3 design/lib/tokens.py` to re-derive every figure. Past five classes
the answer is an "Other" group or a table, never a sixth hue.

Rendering, per-client accent and the full rules: `references/design.md`.

## When a chart is not drawn

It is **not drawn, not faked, and not filled with zeros**. The manifest records
it with a reason written as a sentence a report can print:

```jsonc
{ "key": "country-performance", "status": "not drawn",
  "reason": "Geography is immaterial for this property: 94% of clicks come from a
             single market and no other market moved materially." }
```

The report either omits the section or states the reason. It never describes a
chart that does not exist.

## No matplotlib

`make_charts.py` exits **4**, writes a manifest in which every chart is skipped
with the same reason, and the run continues. **The report then says the visuals
are unavailable** and leans on the pre-rendered tables, which carry every figure
the charts would have shown.

```bash
python3 -m pip install matplotlib     # if charts are wanted
```

## Embedding in the report

Relative paths, so the folder can be moved or zipped:

```markdown
![Daily organic clicks, 2026-07-18 to 2026-08-16](charts/example-com_2026-07-18_2026-08-16_organic-click-trend.png)
```

Use the manifest's `alt` text as the alt text — it is written to describe the
chart to someone who cannot see it, and `explains` gives the sentence that
should sit beside it.
