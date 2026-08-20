# Visualizations

`make_charts.py` draws from `analysis.json` and writes PNGs plus a manifest. It
never reads the API and never recomputes a number.

```bash
python3 scripts/make_charts.py --analysis reports/google-analytics/2026-08-19/data/analysis.json --update-analysis
```

Default output is `<analysis dir>/../charts`, so `data/` and `charts/` sit
side by side under the dated report folder and `./charts/…` resolves from the
report.

---

## The charts

| File | What it shows | Drawn when |
|---|---|---|
| `kpi-change.png` | Percentage change per headline KPI, coloured by verdict | ≥ 3 headline KPIs comparable in both periods |
| `daily-performance.png` | Sessions, key events and revenue as stacked panels by day, with the previous period aligned day-for-day | ≥ 7 days of daily data |
| `channel-performance.png` | Sessions per acquisition channel, both periods | The channel breakdown was retrieved |
| `landing-page-performance.png` | Entrances per landing page, both periods | The landing-page breakdown was retrieved |
| `key-event-performance.png` | Volume per key event, both periods | At least one event is a key event and carried volume |
| `device-performance.png` | Sessions per device beside the current-period key-event rate | The device breakdown was retrieved |
| `ecommerce-performance.png` | Revenue per channel, both periods | `ecommerce_state == "active"` |
| `ecommerce-funnel.png` | Item counts by funnel step with progression rates | ≥ 3 funnel steps returned data |

Nothing else is drawn. A chart that adds no insight is clutter with a caption.

---

## The rules the charts follow

**One measure per axis.** Sessions and revenue get two stacked panels sharing
an x-axis, never a twin axis. A dual-axis chart lets the author imply a
relationship by choosing the scales — exactly what an executive report must not
do.

**Colour carries the job, not the mark.** Change charts are diverging (blue
better, red worse, grey ambiguous). Comparison charts are one hue for the
current period and a muted grey for the previous. Categories never get a
generated hue.

**Better and worse come from the analysis, not the sign.** Event count rising
draws grey, because event count has no direction without context.

**Colour is never the only channel.** Bars carry direct labels, legends are
present wherever two series are, and the report's tables are the accessible
fallback.

**Gaps stay gaps.** A day with no data breaks the line and is shaded, never
plotted at zero.

**A chart with no data is not drawn and not faked.** It goes in the manifest
with a reason, so the report can say the visual is unavailable.

**The palette is not defined here.** It comes from the plugin design system at
`design/DESIGN.md`; the values live in `design/lib/tokens.py` and
`make_charts.py` imports them from `design/lib/charts.py`. Improved is blue
rather than green so the improved/declined pair survives red-green deficiency;
categorical series are assigned in fixed order and never cycled or generated.
Contrast and all-pairs colour-vision separation are measured — run
`python3 design/lib/tokens.py` to re-derive them. Rendering and the per-client
accent: `references/design.md`.

---

## Embedding

Every drawn chart carries a ready-made line:

```markdown
![Daily performance](./charts/daily-performance.png)
```

Use `markdown` from the manifest verbatim — the relative path is correct
wherever the report folder is moved, which an absolute path would not be. It
names the `.png`; the HTML renderer swaps in the `.svg` twin written from the
same drawing, so the Markdown stays readable as Markdown.

Give every embedded chart a sentence of interpretation beneath it. A chart
nobody explains is decoration.

---

## When matplotlib is missing

The script exits 4, writes a manifest with the reason, and draws nothing. The
report is still written — without charts, and saying plainly that the visuals
could not be generated.

```bash
python3 -m pip install matplotlib
```

Never describe a chart that was not drawn.
