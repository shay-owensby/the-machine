# Design and rendering

This skill does not have a visual language of its own. Colour, typography,
spacing, the chart theme and the report layout come from the plugin design
system at **`design/DESIGN.md`** (plugin root), and the values live in
`design/lib/tokens.py`.

`scripts/make_charts.py` imports its theme from `design/lib/charts.py` and
defines no colour, font size or line width of its own. If a chart here needs a
value that is not in the design system, the value belongs in `tokens.py` and in
`DESIGN.md` — not in this skill.

## Charts

Every chart is written twice from one drawing: a `.png` the Markdown report
embeds and a `.svg` the HTML report inlines. `save_twin()` does both, so the
two can never disagree.

The rules that constrain what may be drawn, in full in `DESIGN.md`:

- One measure per axis. Never a dual axis.
- Colour follows the analysis's `verdict`, not the sign of the change.
- Colour is never the only channel — direct labels, a legend for two or more
  series, and the verdict written in words.
- Every chart states its exact period in its subtitle.
- A chart the data cannot support is **not drawn and not faked**: it is recorded
  in the manifest with a reason the report can print as a sentence.

## Rendering the client-facing report

The Markdown report is the source of record. The file the client receives is one
self-contained HTML document — stylesheet, typeface and every chart embedded,
nothing fetched from the network.

```bash
D=~/the-machine/analytics-insights/design/lib
python3 $D/render_report.py \\
  --report analytics-insights/google-search-console/YYYY-MM-DD-google-search-console.md \\
  --analysis <..._analysis.json> \\
  --source google-search-console --project-root .
```

Put `<!-- tiles -->` in the report where the KPI stat-tile row belongs; the
renderer builds it from the analysis file. The headline KPIs for this report are
listed in `HEADLINE_KPIS` in `render_report.py` under the `google-search-console` key — add or
reorder them there, not here.

Exit `3` means a referenced chart was not on disk. The HTML still renders, with
the gap stated where the chart would have been.

## Per-client accent

A Google Search Console report carries the client's accent colour in its masthead rule, links
and section markers. Nothing else, and never a chart.

```bash
python3 $D/brand.py --project-root . --suggest     # candidates from _context/DESIGN.md
python3 $D/brand.py --project-root . --accent '#rrggbb' --client 'Name' --write
```

The suggestion step scores prose and **does not choose**. Confirm before writing:
an unconfirmed accent is how a Search Console property report goes out in another company's colour.
