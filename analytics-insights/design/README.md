# design/

The visual system every report in this plugin is built from.

**Read [`DESIGN.md`](DESIGN.md) first.** It is the guide — what the values are,
what each one is for, and why. This file is the two-minute version for someone
wiring a skill up.

## The rule

Import the values. Never restate them. Everything lives in
[`lib/tokens.py`](lib/tokens.py); the stylesheet, the chart theme, the tiles and
the HTML shell are all generated from it.

```python
sys.path.insert(0, str(Path(__file__).resolve().parents[3] / "design" / "lib"))
from charts import BLUE, VERDICT_COLOR, load_matplotlib, style, finish, save_twin
```

## Rendering a report

```bash
D=~/the-machine/analytics-insights/design/lib

python3 $D/render_report.py \
  --report analytics-insights/google-ads/2026-08-19-google-ads.md \
  --analysis <..._analysis.json> --source google-ads --project-root .
```

Writes one self-contained `.html` beside the Markdown — stylesheet, Inter and
every chart embedded, nothing fetched from the network. Mail it as a single
attachment or print it.

Put `<!-- tiles -->` in the Markdown where the KPI stat-tile row belongs.

Exit `3` means a referenced chart was not on disk. The HTML still renders, with
the gap stated where the chart would have been.

## Per-client accent

```bash
python3 $D/brand.py --project-root . --suggest                    # read the client's DESIGN.md
python3 $D/brand.py --project-root . --accent '#006ac6' --client 'Name' --write
```

`--suggest` scores prose and **does not choose**; confirm before writing. The
accent reaches the masthead rule, links and section markers. It never reaches a
chart — the data palette is fixed for every client.

## Checking it

```bash
python3 lib/tokens.py   # every contrast and CVD-separation claim, recomputed
```

`lib/tokens.py` re-derives every number `DESIGN.md` asserts. Change a colour and
it either passes with new figures or fails and names the pair that broke.

## Adding a skill to the system

1. Import the theme in `scripts/make_charts.py` (snippet above). Define no
   colour, font size or line width locally.
2. Save with `save_twin(fig, png_path)` so the PNG and its SVG twin come from
   one drawing.
3. Add the skill's headline KPIs to `HEADLINE_KPIS` in `lib/render_report.py`
   so its stat-tile row leads with the right figures.
4. If its analysis file stores the daily series in a new shape, teach
   `_daily_rows()` about it — one adapter there, rather than a schema change in
   the skill.
5. Add a `references/design.md` pointing here, and a render step to `SKILL.md`.

## Fonts

Inter, vendored under [`fonts/`](fonts/) — SIL Open Font License, see
`LICENSE-Inter.txt`. The variable `woff2` (latin, 48KB) is embedded in each HTML
report; the static TTFs are what matplotlib loads, so a chart is laid out from
the same metrics it is displayed in. `Inter-latin-ext-var.woff2` is available for
accented Latin and is not embedded by default.
