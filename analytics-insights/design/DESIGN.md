# Analytics & Insights — design system

The visual language every report, chart and dashboard this plugin produces is
built from. It belongs to the **Analytics & Insights plugin only**. Other
plugins in `the-machine` have their own guides, and client projects have their
own `_context/DESIGN.md` describing *the client's* brand — this document does
not override either, and neither overrides this one. The one place they meet is
the accent colour, and that meeting is described in [Per-client brand](#per-client-brand).

---

## The one rule

**Import the values. Never restate them.**

Every colour, size, weight and spacing step lives in [`lib/tokens.py`](lib/tokens.py).
The stylesheet, the chart theme, the stat tiles and the HTML shell are all
generated from it. A skill that needs a value imports it; a skill that needs a
value that does not exist yet adds it here, with a reason, and then imports it.

This rule is not tidiness. Before it existed, the same forty lines of chart
styling were pasted into three skills' `make_charts.py` and had already started
to drift — the Search Console charts were rendering at a different DPI to the
Google Ads charts, and nobody had noticed, because nobody ever sees two of these
reports side by side. The system is only a system if there is one copy of it.

```python
# In any script under skills/*/scripts/
sys.path.insert(0, str(Path(__file__).resolve().parents[3] / "design" / "lib"))
from charts import BLUE, VERDICT_COLOR, load_matplotlib, style, finish, save_twin
```

---

## The register

Cool near-white ground. Near-black ink. Inter, with tight negative tracking on
anything large and a wide-tracked uppercase micro-label for anything small.
Hairline rules doing the work that cards, shadows and coloured banding normally
do. A great deal of air. Square corners, everywhere, with no exception.

The reference point is Linear's product surface, adapted for a document that
gets printed and mailed rather than scrolled in an app. Two departures from
Linear proper, both deliberate:

- **Light only.** Linear is dark-first. A client report is read on a screen you
  do not control, printed, and forwarded as a PDF; a raster chart cannot respond
  to a reader's theme, and a chart tuned to work in both modes works well in
  neither. There is one surface, and it is white.
- **Airier than the app.** Linear's in-app density is right for a tool you live
  in. This is a document someone reads once, carefully, and where a thirteen-row
  KPI table has to stay survivable. Sections are separated by 72px, not 24.

### What is deliberately absent

Rounded corners. Drop shadows. Gradients. Coloured section banners. Zebra
striping. Icon sets. Emoji. Progress rings and gauges. Dual-axis charts. Pie
charts beyond two slices. Any hue generated at runtime.

Each of these was left out for a reason, and the reasons are given where they
come up below. Absence is as much a part of this system as anything in it — a
single rounded corner or one drop shadow reads as a mistake against the rest.

---

## Foundations

### Surface and ink

| Token | Value | Contrast on surface | Used for |
|---|---|---:|---|
| `SURFACE` | `#ffffff` | — | the page, and the ground behind every chart |
| `SURFACE_SUBTLE` | `#fafafa` | — | table header bands, tile grounds where one is needed |
| `SURFACE_INSET` | `#f4f4f5` | — | notes, code, the panel that stands where a chart could not be drawn |
| `INK` | `#08090a` | 19.9:1 | headings, figures, the value cells of a table |
| `INK_SECONDARY` | `#3c3f44` | 10.6:1 | body copy |
| `INK_MUTED` | `#6f737b` | 4.8:1 | captions, axis labels, metadata |
| `INK_FAINT` | `#9a9ea6` | 2.7:1 | decorative only — **never** load-bearing text |
| `BORDER` | `#e6e6e9` | — | hairlines, table rules, tile edges |
| `BORDER_STRONG` | `#d0d0d5` | — | axis lines, the rule under a table header |
| `GRID` | `#eeeef0` | — | chart gridlines, one shade off the surface |

The near-white is *cool*, not the warm off-white this plugin used previously.
Warmth reads as "document" and tints whatever accent sits on it, which matters
when the accent is a client's own colour and they know exactly what it should
look like.

`INK_FAINT` sits below 4.5:1 by design. It is for a sparkline stroke and a list
marker. Text set in it is a bug.

### Accent

One accent, and it is the only place a client's own colour enters the report.

| Token | Default | Used for |
|---|---|---|
| `ACCENT` | `#5b60d9` | the masthead rule, links, the marker on a note |
| `ACCENT_STRONG` | `#4348c0` | hover and pressed states |
| `ACCENT_SUBTLE` | `#eeeefc` | a tint ground behind an accented block |

The default is Linear's indigo. It is replaced per client — see
[Per-client brand](#per-client-brand). Nothing structural may depend on the
accent's hue, because it is not stable across reports.

**The accent never encodes data.** Not a bar, not a line, not a segment, not a
delta. See below for why.

### Data colour

Fixed for every client, for every report, forever.

**Categorical** — assigned in order, never cycled, never generated:

| | Hex | Contrast on white |
|---|---|---:|
| 1 blue | `#3060e0` | 5.42:1 |
| 2 amber | `#e0761f` | 3.10:1 |
| 3 teal | `#0f8f74` | 4.04:1 |
| 4 magenta | `#c2409e` | 4.65:1 |
| 5 purple | `#6b21a8` | 8.72:1 |

Worst-pair CIEDE2000 separation across all five, measured under normal, protan,
deutan and tritan vision: **6.9** (tritan, blue vs teal). Every hue clears the
3:1 WCAG floor for a non-text mark on its surface. These numbers are produced by
`python3 lib/tokens.py`, not asserted here — if you change a hue, the check tells
you what you did.

Past five classes the answer is a table or an "Other" group (`#c4c6cc`), never a
sixth hue. A reader cannot reliably tell a sixth categorical colour from the
second, and a legend with nine entries is a legend nobody reads.

**Verdict** — the colouring for any chart or figure showing change:

| Verdict | Hex | Meaning |
|---|---|---|
| `improved` | `#3060e0` blue | the move was good for the account |
| `declined` | `#e5484d` red | the move was bad for the account |
| `ambiguous` | `#8b8d98` grey | the metric has no direction without an objective |
| `flat` | `#c4c6cc` pale grey | below the materiality threshold |

Two things about this table are load-bearing.

**Improved is blue, not green.** Red-green is the deficiency roughly one man in
twelve has. Blue against red survives it: measured worst-pair separation across
all four vision types is 21.1, against the roughly 3-6 a red/green pair would
give under deuteranopia.

**The colour follows the verdict, not the sign.** A CPA that fell is blue,
because falling is better. Spend that rose is grey, because spend has no
direction until you say what it was for. Colouring by sign would paint a falling
CPA as a decline — a chart containing no false number that nevertheless tells a
false story. The verdict comes from the analysis file's `verdict` field. Chart
code never decides it.

**Sequential** — one hue, light to dark, for magnitude:
`#dce6fb → #a8c0f4 → #6f93ec → #3060e0 → #1e3f96`. Generated from the categorical
blue so a magnitude chart and a categorical chart look like the same family.

**Why the client's brand colour is not allowed in here.** If the data palette
followed the accent, the same chart would encode a different meaning in two
clients' reports, and nobody could carry a reading habit from one to the next.
Worse, a brand colour is chosen to look right on a logo — it has no obligation
to be separable from four other colours under deuteranopia, and most are not.

### Typography

**Inter**, vendored in [`fonts/`](fonts/) under the SIL Open Font License. The
variable `woff2` (latin, 48KB) is embedded in every HTML report as base64; the
static TTFs are what matplotlib loads. The page and the chart beside it are set
in one typeface, and the report renders identically on a machine that has never
heard of Inter and has no network.

Registering the real font file matters beyond appearance: matplotlib lays text
out from the font's own metrics, so a chart laid out against Helvetica and then
displayed in Inter would have labels no longer sitting where they were placed.

| Role | Size | Line height | Tracking | Weight |
|---|---:|---:|---:|---:|
| `title` | 30 | 1.18 | −0.022em | 600 |
| `section` | 21 | 1.25 | −0.017em | 600 |
| `sub` | 16 | 1.35 | −0.011em | 600 |
| `body` | 15 | 1.65 | −0.004em | 400 |
| `small` / `table` | 13.5 | 1.55 / 1.45 | −0.002em | 400 |
| `caption` | 12.5 | 1.5 | 0 | 400 |
| `label` | 11.5 | 1.3 | **+0.062em** | 600, uppercase |
| `figure` | 30 | 1.1 | −0.024em | 600, tabular |
| `delta` | 13 | 1.2 | −0.004em | 500, tabular |

**Tracking scales with size, and reverses direction at the bottom.** Negative on
anything large, zero at caption size, strongly positive on the uppercase label.
This is the single most recognisable element of the register, and a flat
letter-spacing applied everywhere is what makes an imitation of it look wrong.

**Numbers are tabular everywhere they are compared** — tiles, table cells,
deltas. `font-variant-numeric: tabular-nums`, which Inter supports properly. A
column of figures then lines up on its digits and can be read as a shape rather
than a list. Set `.num` on a cell and it happens.

Monospace (`ui-monospace` / SF Mono / Menlo) is for identifiers, file paths and
code only. It is not vendored; it is a system stack.

### Space and measure

Scale, in px: `2 4 8 12 16 24 32 40 56 72 96 128`. Nothing between steps.

| Token | Value | |
|---|---:|---|
| `MEASURE_PROSE` | 720px | paragraphs, lists, notes, captions |
| `MEASURE_WIDE` | 1080px | tables, charts, the tile grid |
| `PAGE_PAD` | 56px | desktop gutter (20px under 720px) |
| `SECTION_GAP` | 72px | between top-level sections |

Constraining the *paragraph* rather than the *container* is what lets a
thirteen-column KPI table and a readable executive summary share one page. A
720px measure is about 90 characters of Inter at 15px, which is where a long
prose section stays comfortable.

### Chrome

`RADIUS = 0`. Every corner, everywhere. The stylesheet enforces it with a
`border-radius: 0 !important` on `*`, and `lib/tokens.py` fails its own
validation if the token is ever set to anything else.

Hairlines at 1px do the separating. There are no shadows and no elevation model:
a rule and 72px of space say "new section" more clearly than a floating card,
and they survive being printed.

---

## Components

### Masthead

A 2px accent rule across the top, the title, then a metadata rail: reporting
period, comparison period, account, currency. Both date ranges appear here,
always. A period-over-period figure without its periods cannot be checked, and
the date range is the first thing a client verifies.

The renderer builds this automatically from the `# Title` and the `**Label:**`
lines beneath it. Authors write ordinary Markdown.

### Stat tiles

The KPI row: four to six figures a decision-maker checks first, each with its
change and the shape of the period behind it. One hairline grid, tiles sharing
their borders, no fill and no shadow.

Built in HTML and inline SVG rather than as an image, because it stays
selectable so a client can copy a figure out, it is set in the same type as the
paragraph beneath it, and it re-flows on a phone — none of which a PNG of six
tiles can do.

- **Column count leaves no orphan.** Six tiles go three-across in two even rows,
  not five-across with one box sitting alone under an empty row.
- **No arrows.** The signed percentage already states the direction. An arrow
  beside it is the same fact drawn twice, and it actively misleads on the two
  cases that matter most: an up-arrow next to the word "better" on a falling
  CPA, and an up-arrow next to a change too small to be material.
- **The verdict is written in words** — "better", "worse", "not material" — so
  it survives greyscale printing and is announced by a screen reader.
- **Unavailable says "not available"**, never a zero and never a dash that could
  be read as one, and carries the reason.
- **A change against a zero baseline is undefined.** The tile shows the absolute
  change and says the baseline was zero. It never prints a percentage.
- **Figures match the table exactly.** Compact form (`1.2M`) only above a
  million. A tile reading `$12.9k` beside a table reading `$12,880.00` makes a
  reader stop and check whether they are the same number.

Sparklines are a bare line: no axis, no fill, no gridline, last point marked.
They answer one question — drift, spike or cliff — and deliberately cannot be
read for values. A flat series is drawn flat rather than scaled up into noise,
which is the usual way a sparkline manufactures a story. Ratio KPIs that are not
stored per day (CPA, ROAS, CTR) are derived from the two counts that are, so the
row does not end up half-populated.

### Tables

Horizontal rules only, no vertical rules, no striping. Uppercase micro-label
header over a `BORDER_STRONG` rule; hairline between rows; first column in `INK`
at weight 500; everything else in `INK_SECONDARY`.

Numeric cells are detected by the renderer and set right-aligned and tabular
without the author marking them up — the report Markdown is written by an agent
reading an analysis file, and requiring it to also get alignment right is one
more thing that can go wrong in a way the reader sees. Cells reading "not
available" or "n/a" are styled as absences.

Paste `analysis.tables.*` rather than retyping figures. Every re-typed number is
a chance to mistype one.

On screen a wide table scrolls inside its own container. **On paper it cannot** —
print ignores the scroller, the table expands the page box, and everything else
on the page gets pushed off the right edge with it. The print rules drop the
table's `nowrap` and some of its size instead, so it fits.

### Figures

Charts are inlined as SVG: vector, selectable, scaling with the column, set in
the report's own embedded Inter. A caption appears only when the chart manifest
carries a `note` — the chart draws its own title and subtitle, and repeating
them underneath is the same text twice.

**A chart that was not drawn is stated, in the space it would have occupied**,
using the manifest's `reason` as a sentence. It is never replaced by a chart of
zeros, and never silently dropped.

### Notes, priority markers, colophon

Notes and data caveats are deliberately plain: inset ground, 2px accent rule at
the left. A caveat styled like a warning banner gets skipped, and these have to
be read.

Recommendations carry a bordered `High` / `Medium` / `Low` marker so priority can
be scanned down the margin instead of disappearing into the sentence.

Every report ends with a colophon naming the account, the analysis file, its
schema and when it was generated, and stating that unavailable metrics are never
shown as zero. The report says where its numbers came from.

---

## Charts

Full catalogue rules live with each skill; what follows binds all of them.

**One measure per axis. Never a dual-axis chart.** There is no helper for a twin
y-axis in `lib/charts.py`, and adding one would be a change to this document. A
dual-axis chart lets whoever draws it pick two scales that make two series
appear to move together or apart; the implication is manufactured, and it is the
commonest way a chart with no false number in it tells a false story. Two
measures get two stacked panels sharing an x-axis.

**Colour is never the only channel.** Every bar is directly labelled. Any chart
with two or more series carries a legend. KPI labels append "(better)" and
"(worse)" so the verdict survives a greyscale printer. The report's own tables
are the accessible fallback, and they always contain the same numbers.

**Recessive chrome.** Solid hairline gridlines one shade off the surface — no
dashes, which are noise. No tick marks: the gridline already says where the
value is, and a tick beside it is the same information drawn twice. No box
around the marks; only the left and bottom spines survive. Stacked segments are
separated by a 2px gap of surface, not by a border.

**Every chart states its period** in its subtitle, with exact dates and any
qualification the data needs ("Search campaigns only — campaign types that do
not report impression share are absent from this chart, not zero"). A chart that
travels out of the report without its dates cannot be checked by whoever it
reaches.

**Layout is measured in inches, not figure fractions**, so a title never lands on
top of its own subtitle at one chart height and floats at another. Legends sit
in reserved space below the plot, never over the marks.

**Two files, one drawing.** `save_twin()` writes the PNG the Markdown copy
embeds and the SVG the HTML report inlines, from the same figure. They cannot
disagree.

matplotlib is the plugin's one optional dependency. Without it a skill writes a
manifest saying so and draws nothing; the report then says the visuals are
unavailable. **It never describes a chart that does not exist.**

---

## Per-client brand

A report is for a client, so it carries the client's colour — in the masthead
rule, the section markers, the links and the note markers. Nothing else.

**Resolution order**

1. `--accent '#rrggbb'` on the command line.
2. `analytics-insights/brand.json` in the client project.
3. Candidates extracted from the client's `_context/DESIGN.md` — **offered, never
   applied silently.**
4. The plugin default.

Client `DESIGN.md` files are prose written by a different skill to no fixed
schema, so `lib/brand.py` scores rather than parses, and returns a ranked list
for a human or an agent to confirm. It does not pick one. An unconfirmed accent
is how a report goes out in another company's colour.

```bash
D=~/the-machine/analytics-insights/design/lib
python3 $D/brand.py --project-root . --suggest        # what the DESIGN.md offers
python3 $D/brand.py --project-root . --accent '#006ac6' --client 'Mr. Electric' --write
```

**Contrast is enforced, hue is preserved.** Any accent failing 4.5:1 as text on
white is darkened along CIELAB L* until it passes, keeping hue and chroma. The
client's blue stays their blue; it stops being illegible. A brand yellow like
`#f5d90a` (1.4:1) resolves to `#867700` — recognisably the same colour, and
readable.

---

## Producing a report

```bash
S=~/the-machine/analytics-insights/skills/reports-google-ads
D=~/the-machine/analytics-insights/design/lib

python3 $S/scripts/fetch_google_ads.py   --project-root .
python3 $S/scripts/analyze_performance.py --raw <..._raw.json>
python3 $S/scripts/make_charts.py --analysis <..._analysis.json> \
        --out charts --update-analysis          # writes .png and .svg

# ... the agent writes the Markdown report ...

python3 $D/render_report.py --report 2026-08-19-google-ads.md \
        --analysis <..._analysis.json> --source google-ads --project-root .
```

The result is **one self-contained `.html`**: stylesheet, Inter and every chart
embedded. Nothing beside it to lose, so it can be mailed as a single attachment
or printed, and it looks the same either way. The Markdown stays on disk as the
source of record — it is what an agent reads to revise the report, and what
survives if the renderer changes.

Put `<!-- tiles -->` in the Markdown where the KPI row belongs. Without a marker
the renderer places it under the masthead.

`render_report.py` exits `3` when a chart the report references is missing. It
still renders, with the gap stated where the chart would have been.

---

## Extending it

**A new value** goes in `lib/tokens.py` with a comment saying what it is for,
and it goes in this document. It does not go in a skill.

**A new chart type** goes in the skill that needs it, drawn with the shared
theme, and its row goes in that skill's catalogue table. If two skills need it,
it moves into `lib/charts.py`.

**A new component** goes in `lib/css.py` (structure) and, if it generates markup,
its own module beside `lib/tiles.py`.

**Changing a data colour** requires re-running `python3 lib/tokens.py` and
recording the new measured separation in the table above. The floors are 3:1
contrast for a mark and CIEDE2000 5.0 between any two categorical hues under
every vision type. The validator fails the build rather than warning.

---

## Verifying

```bash
cd ~/the-machine/analytics-insights/design
python3 lib/tokens.py     # every contrast and separation claim, recomputed
```

`lib/tokens.py` re-derives every number this document asserts. Nothing here is
taken on trust: if a token changes, the check either passes with new figures or
fails and names the pair that broke.

---

## File map

| Path | |
|---|---|
| [`lib/tokens.py`](lib/tokens.py) | **the single source of truth**, and its own validator |
| [`lib/color.py`](lib/color.py) | WCAG contrast, CIEDE2000, dichromat simulation, L* adjustment |
| [`lib/brand.py`](lib/brand.py) | per-client accent resolution and `DESIGN.md` extraction |
| [`lib/css.py`](lib/css.py) | the stylesheet, generated from tokens |
| [`lib/charts.py`](lib/charts.py) | the shared matplotlib theme |
| [`lib/tiles.py`](lib/tiles.py) | stat tiles and sparklines |
| [`lib/fmt.py`](lib/fmt.py) | number and date formatting |
| [`lib/markdown.py`](lib/markdown.py) | the report Markdown subset renderer |
| [`lib/render_report.py`](lib/render_report.py) | assembles the self-contained HTML |
| [`fonts/`](fonts/) | Inter, SIL OFL — see `LICENSE-Inter.txt` |
