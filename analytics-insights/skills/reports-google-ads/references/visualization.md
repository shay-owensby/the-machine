# Visualisation

`make_charts.py` draws from the analysis file — never from the API — so a chart
always shows exactly the figures in the tables beside it. Each chart is written
as a PNG for the Markdown report and an SVG for the HTML one, from a single
drawing.

## The catalogue

| id | Form | Drawn when | The question it answers |
|---|---|---|---|
| `kpi-change` | Diverging horizontal bars, one per KPI | ≥3 KPIs comparable in both periods | What moved, and was the move good? |
| `daily-trend` | Two stacked line panels sharing a date axis | ≥14 daily rows | How did spend and conversions run day to day, and where does the period boundary fall? |
| `campaign-spend-conversions` | Two horizontal bar panels, shared campaign order | ≥2 campaigns with spend | Where does the money go, and does output follow it? |
| `campaign-efficiency` | Dumbbell, previous → current | ≥2 campaigns with CPA (or ROAS) in both periods | Which campaigns got cheaper or dearer per conversion? |
| `impression-share` | Stacked horizontal bars to 100% | ≥1 campaign reporting search IS | Of the impressions available, what was won, and what was lost to budget versus rank? |
| `device-mix` | Two stacked share bars, previous vs current | ≥2 devices with spend | Did the traffic mix shift? |

A chart with no data is **not drawn and not faked**. It is recorded in the
manifest with `status: "not drawn"` and a reason ("No campaign reported search
impression share — Performance Max, Display and Video do not report it"), which
is a sentence the report can use directly.

## The manifest

```jsonc
[ { "id": "kpi-change",
    "file": "/abs/path/..._kpi-change.png",
    "filename": "..._kpi-change.png",
    "svg_file": "/abs/path/..._kpi-change.svg",
    "svg_filename": "..._kpi-change.svg",
    "title": "Period-over-period change by KPI",
    "alt": "Horizontal bar chart of percentage change for each KPI ...",
    "note": null,
    "status": "drawn" },
  { "id": "impression-share", "file": null, "status": "not drawn",
    "reason": "No campaign reported search impression share ..." } ]
```

`--update-analysis` copies it into `analysis.charts`. Embed by `filename` --
the PNG -- relative to the report. The HTML renderer swaps in the SVG twin
automatically, so the Markdown stays readable as Markdown:

```markdown
![Horizontal bar chart of percentage change for each KPI, blue where the change
is an improvement and red where it is a decline.](charts/1234567890_2026-07-20_2026-08-18_kpi-change.png)
```

Use the manifest's `alt` text. It describes the chart's construction rather than
repeating its title, which is what a screen-reader user needs and what a reader
of a printed copy gets from the figure itself.

## Design rules

**They are not in this file.** Colour, type, spacing, chrome and the honesty
rules every chart obeys live in the plugin's design system, at
`design/DESIGN.md`, and the values themselves live in `design/lib/tokens.py`.
`make_charts.py` imports the theme from `design/lib/charts.py` and defines no
colour, font size or line width of its own.

That is the point of the arrangement: this skill, `reports-google-analytics`
and `reports-google-search-console` previously each carried their own copy of
the same forty lines of styling, and the copies had begun to drift.

The four rules worth restating here, because they constrain what you may *draw*
rather than how it looks:

- **One measure per axis, never a dual axis.** Spend and conversions get two
  stacked panels sharing a date axis. A twin axis lets the author pick scales
  that make two series appear to move together or apart; the implication is
  manufactured, and it is the commonest way a chart with no false number in it
  tells a false story.
- **Colour follows the verdict, not the sign.** A CPA that fell is blue. Spend
  that rose is grey. The verdict comes from the analysis file; chart code never
  decides it.
- **Colour is never the only channel.** Every bar directly labelled, a legend
  wherever there are two or more series, "(better)" and "(worse)" appended to
  KPI labels so the verdict survives greyscale.
- **Every chart states its period** in its subtitle, with exact dates and any
  qualification the data needs. A chart that travels out of the report without
  its dates cannot be checked by whoever receives it.

## Rendering environment

Charts need **matplotlib**. It is the one optional dependency in the skill;
everything else is standard library.

```bash
python3 -m pip install matplotlib
```

Without it, `make_charts.py` exits `4`, writes a manifest saying why, and draws
nothing. The report then says the visuals are unavailable. It never describes a
chart that does not exist.

Each chart is written **twice from one drawing**: a PNG at 160 dpi that the
Markdown report embeds, and an SVG that the HTML report inlines. They come from
the same figure, so they cannot disagree. The SVG keeps its text as text, and
the HTML report embeds Inter, so a chart's labels are set in the same typeface
as the paragraph beneath them and stay selectable and crisp at any zoom.

Both are deliberately single-mode light. A raster chart cannot respond to a
reader's theme, and a mid-grey "theme-neutral" chart is worse in both modes than
a good light one.

## Choosing what to include

Not every chart belongs in every report. Lead with `kpi-change` — it is the
executive summary in one image — then include only the charts that carry a point
you are making in the text:

- Volume or pacing is the story → `daily-trend`
- Money is concentrated in the wrong place → `campaign-spend-conversions`
- Efficiency moved → `campaign-efficiency`
- Growth is capped → `impression-share`
- The audience shifted → `device-mix`

A chart with no accompanying sentence is decoration. Six charts and no argument
is a data dump.
