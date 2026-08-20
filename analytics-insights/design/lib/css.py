"""The report stylesheet, generated from tokens.py.

The CSS is generated rather than hand-written so that a token can only be
changed in one place. Nothing in here invents a value; every literal comes from
``tokens`` or from a resolved ``Brand``.

The register, in one paragraph: cool near-white ground, near-black ink, Inter
with tight negative tracking on anything large, hairline rules doing the work
that boxes and shadows normally do, and no rounded corner anywhere. Density is
deliberately low — a client reads this once, carefully, and the whitespace is
what makes an eleven-row KPI table survivable.
"""

import os
import sys

try:
    from . import tokens as _t
except ImportError:
    sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
    import tokens as _t


def _type(name):
    size, lh, ls, weight = _t.TYPE[name]
    return ("font-size:%gpx;line-height:%g;letter-spacing:%gem;font-weight:%d;"
            % (size, lh, ls, weight))


def font_face(embedded_woff2_b64=None):
    """``@font-face`` for Inter.

    With a base64 payload the report carries its own type and renders the same
    on a machine that has never heard of Inter and has no network. Without one,
    the stack in ``FONT_STACK`` falls back to the platform UI face, which is
    metrically close enough that the layout does not move.
    """
    if not embedded_woff2_b64:
        return "/* Inter not embedded; falling back to the system stack. */"
    return (
        "@font-face{"
        "font-family:'Inter';"
        "font-style:normal;"
        "font-weight:100 900;"
        "font-display:swap;"
        "src:url(data:font/woff2;charset=utf-8;base64,%s) format('woff2');"
        "}" % embedded_woff2_b64
    )


def variables(brand=None):
    accent = brand.accent if brand else _t.ACCENT
    accent_strong = brand.accent_strong if brand else _t.ACCENT_STRONG
    accent_subtle = brand.accent_subtle if brand else _t.ACCENT_SUBTLE
    rows = [
        ("surface", _t.SURFACE), ("surface-subtle", _t.SURFACE_SUBTLE),
        ("surface-inset", _t.SURFACE_INSET),
        ("ink", _t.INK), ("ink-2", _t.INK_SECONDARY),
        ("ink-muted", _t.INK_MUTED), ("ink-faint", _t.INK_FAINT),
        ("border", _t.BORDER), ("border-strong", _t.BORDER_STRONG),
        ("grid", _t.GRID),
        ("accent", accent), ("accent-strong", accent_strong),
        ("accent-subtle", accent_subtle),
        ("improved", _t.VERDICT["improved"]), ("declined", _t.VERDICT["declined"]),
        ("ambiguous", _t.VERDICT["ambiguous"]), ("flat", _t.VERDICT["flat"]),
        ("measure-prose", "%dpx" % _t.MEASURE_PROSE),
        ("measure-wide", "%dpx" % _t.MEASURE_WIDE),
        ("pad", "%dpx" % _t.PAGE_PAD),
        ("section-gap", "%dpx" % _t.SECTION_GAP),
        ("font", _t.FONT_STACK), ("font-mono", _t.FONT_STACK_MONO),
    ]
    for i, hexv in enumerate(_t.CATEGORICAL):
        rows.append(("cat-%d" % (i + 1), hexv))
    body = "".join("--%s:%s;" % (k, v) for k, v in rows)
    return ":root{%s}" % body


STRUCTURE = """
/* ---------------------------------------------------------------------- *
 * Reset. Only what the document actually uses.
 * ---------------------------------------------------------------------- */
*,*::before,*::after{box-sizing:border-box}
html{-webkit-text-size-adjust:100%%}
body,h1,h2,h3,h4,p,ul,ol,li,figure,figcaption,table,blockquote{margin:0;padding:0}
ul,ol{list-style:none}
img,svg{max-width:100%%;height:auto;display:block}
table{border-collapse:collapse;border-spacing:0}

/* Every corner in this document is square. This is the one rule with no
   exception; a single rounded element reads as a mistake against the rest. */
*{border-radius:0 !important}

/* ---------------------------------------------------------------------- *
 * Page
 * ---------------------------------------------------------------------- */
body{
  background:var(--surface);
  color:var(--ink-2);
  font-family:var(--font);
  %(body_type)s
  font-feature-settings:"cv05" 1,"cv08" 1,"ss03" 1;
  -webkit-font-smoothing:antialiased;
  text-rendering:optimizeLegibility;
}
.report{
  max-width:calc(var(--measure-wide) + var(--pad) * 2);
  margin:0 auto;
  padding:%(pad_top)dpx var(--pad) %(pad_bottom)dpx;
}

/* Prose holds a comfortable measure; tables, charts and tiles take the full
   column. Constraining the paragraph rather than the container is what lets a
   wide KPI table and a readable summary share one page. */
.report > p,
.report > ul,
.report > ol,
.report > blockquote,
.report > h3,
.report > .note{max-width:var(--measure-prose)}

/* ---------------------------------------------------------------------- *
 * Type
 * ---------------------------------------------------------------------- */
h1{%(title)s color:var(--ink);}
h2{%(section)s color:var(--ink);}
h3{%(sub)s color:var(--ink);}
p{margin:0 0 %(p_gap)dpx}
strong{font-weight:600;color:var(--ink)}
em{font-style:italic}
a{color:var(--accent);text-decoration:none;border-bottom:1px solid var(--accent-subtle)}
a:hover{color:var(--accent-strong);border-bottom-color:var(--accent-strong)}
code{font-family:var(--font-mono);font-size:0.88em;background:var(--surface-inset);
     padding:2px 5px;color:var(--ink)}
pre{font-family:var(--font-mono);font-size:13px;line-height:1.55;
    background:var(--surface-inset);padding:%(sp16)dpx %(sp16)dpx;overflow-x:auto;
    margin:0 0 %(sp24)dpx;border-left:2px solid var(--border-strong)}
pre code{background:none;padding:0}

/* The uppercase micro-label. Used for eyebrows, table headers and tile
   labels — the same treatment every time it appears, so the reader learns it
   once. */
.label{%(label)s text-transform:uppercase;color:var(--ink-muted)}

ul,ol{margin:0 0 %(sp24)dpx;padding:0}
li{position:relative;padding-left:%(sp24)dpx;margin-bottom:%(sp12)dpx}
ul > li::before{content:"";position:absolute;left:2px;top:0.62em;
  width:5px;height:1px;background:var(--ink-faint)}
ol{counter-reset:ol}
ol > li{counter-increment:ol}
ol > li::before{content:counter(ol);position:absolute;left:0;top:0;
  %(caption)s color:var(--ink-faint);font-variant-numeric:tabular-nums}

blockquote{border-left:2px solid var(--border-strong);padding-left:%(sp16)dpx;
  margin:0 0 %(sp24)dpx;color:var(--ink-muted)}

hr{border:0;border-top:1px solid var(--border);margin:%(rule_gap)dpx 0}

/* ---------------------------------------------------------------------- *
 * Masthead
 * ---------------------------------------------------------------------- */
.masthead{border-top:2px solid var(--accent);padding-top:%(sp24)dpx;
  margin-bottom:%(sp56)dpx}
.masthead h1{margin-bottom:%(sp16)dpx}
.masthead .meta{display:flex;flex-wrap:wrap;gap:0 %(sp24)dpx;
  %(caption)s color:var(--ink-muted);max-width:none}
.masthead .meta > span{white-space:nowrap}
.masthead .meta b{font-weight:500;color:var(--ink-2)}

/* ---------------------------------------------------------------------- *
 * Sections. A hairline above each one, and a lot of air. The rule is what
 * replaces the card, the shadow and the coloured band.
 * ---------------------------------------------------------------------- */
section{margin-top:var(--section-gap)}
section > h2{border-top:1px solid var(--border);padding-top:%(sp24)dpx;
  margin-bottom:%(sp24)dpx}
section > h3{margin:%(sp40)dpx 0 %(sp12)dpx}
section > *:last-child{margin-bottom:0}

/* ---------------------------------------------------------------------- *
 * Stat tiles. One hairline grid, tiles sharing their borders, no fill and no
 * shadow. The figure is the only large thing on the tile.
 * ---------------------------------------------------------------------- */
.tiles{display:grid;--cols:3;
  grid-template-columns:repeat(var(--cols),minmax(0,1fr));
  border-top:1px solid var(--border);border-left:1px solid var(--border);
  margin:0 0 %(sp32)dpx}
.tile{border-right:1px solid var(--border);border-bottom:1px solid var(--border);
  padding:%(sp16)dpx %(sp16)dpx %(sp12)dpx;min-height:132px;
  display:flex;flex-direction:column}
.tile .label{margin-bottom:%(sp12)dpx}
.tile .figure{%(figure)s color:var(--ink);font-variant-numeric:tabular-nums;
  margin-bottom:%(sp4)dpx}
.tile .delta{%(delta)s font-variant-numeric:tabular-nums;
  display:flex;align-items:baseline;gap:5px}
.tile .delta .verdict{%(caption)s color:var(--ink-muted);letter-spacing:0}
.tile .spark{margin-top:auto;padding-top:%(sp12)dpx}
.tile.unavailable .figure{color:var(--ink-faint);font-size:17px;letter-spacing:-0.01em}

.d-improved{color:var(--improved)}
.d-declined{color:var(--declined)}
.d-ambiguous{color:var(--ambiguous)}
.d-flat{color:var(--ink-muted)}

/* ---------------------------------------------------------------------- *
 * Tables. Horizontal rules only. Numbers right-aligned and tabular, so a
 * column of figures lines up on its digits and can be scanned as a shape.
 * ---------------------------------------------------------------------- */
.table-wrap{overflow-x:auto;margin:0 0 %(sp32)dpx;
  border-bottom:1px solid var(--border)}
table{width:100%%;%(table)s}
thead th{%(label)s text-transform:uppercase;color:var(--ink-muted);
  text-align:left;padding:0 %(sp16)dpx %(sp12)dpx 0;
  border-bottom:1px solid var(--border-strong);white-space:nowrap;vertical-align:bottom}
tbody td{padding:%(sp12)dpx %(sp16)dpx %(sp12)dpx 0;
  border-bottom:1px solid var(--border);vertical-align:top;color:var(--ink-2)}
tbody tr:last-child td{border-bottom:0}
tbody td:first-child{color:var(--ink);font-weight:500;padding-left:0}
thead th:last-child,tbody td:last-child{padding-right:0}
th.num,td.num{text-align:right;font-variant-numeric:tabular-nums;
  white-space:nowrap;font-feature-settings:"tnum" 1}
td.num{color:var(--ink)}
td.na{color:var(--ink-faint)}
.t-improved{color:var(--improved)}
.t-declined{color:var(--declined)}

/* ---------------------------------------------------------------------- *
 * Figures
 * ---------------------------------------------------------------------- */
figure{margin:0 0 %(sp32)dpx}
figure svg,figure img{width:100%%;height:auto}
figcaption{%(caption)s color:var(--ink-muted);margin-top:%(sp12)dpx;
  padding-top:%(sp12)dpx;border-top:1px solid var(--border);
  max-width:var(--measure-prose)}
figcaption b{color:var(--ink-2);font-weight:500}

/* A chart that could not be drawn says so, in the space it would have taken.
   It is never replaced by a chart of zeros. */
.no-chart{background:var(--surface-inset);border-left:2px solid var(--border-strong);
  padding:%(sp16)dpx;margin:0 0 %(sp32)dpx;%(small)s color:var(--ink-muted);
  max-width:var(--measure-prose)}

/* ---------------------------------------------------------------------- *
 * Notes and caveats. Deliberately plain: a data caveat that looks like a
 * warning banner gets skipped, and these have to be read.
 * ---------------------------------------------------------------------- */
.note{background:var(--surface-inset);border-left:2px solid var(--accent);
  padding:%(sp16)dpx %(sp16)dpx;margin:0 0 %(sp24)dpx;%(small)s}
.note .label{margin-bottom:%(sp8)dpx}
.note p:last-child{margin-bottom:0}

/* ---------------------------------------------------------------------- *
 * Priority markers on recommendations
 * ---------------------------------------------------------------------- */
.pri{%(label)s text-transform:uppercase;display:inline-block;
  padding:3px 7px;border:1px solid var(--border-strong);color:var(--ink-muted);
  margin-right:%(sp8)dpx;vertical-align:2px}
.pri-high{border-color:var(--declined);color:var(--declined)}
.pri-medium{border-color:var(--border-strong);color:var(--ink-2)}

/* ---------------------------------------------------------------------- *
 * Footer
 * ---------------------------------------------------------------------- */
.colophon{margin-top:var(--section-gap);padding-top:%(sp24)dpx;
  border-top:1px solid var(--border);%(caption)s color:var(--ink-faint)}
.colophon p{margin-bottom:%(sp8)dpx;max-width:var(--measure-prose)}

/* ---------------------------------------------------------------------- *
 * Narrow viewports
 * ---------------------------------------------------------------------- */
@media (max-width:960px){
  .tiles{grid-template-columns:repeat(3,minmax(0,1fr))}
}
@media (max-width:720px){
  .report{padding:%(sp32)dpx %(pad_small)dpx %(sp56)dpx}
  h1{font-size:25px}
  h2{font-size:19px}
  .tile .figure{font-size:25px}
  .tiles{grid-template-columns:repeat(2,minmax(0,1fr))}
  :root{--section-gap:%(sp56)dpx}
}

/* ---------------------------------------------------------------------- *
 * Print. The report is mailed as often as it is opened, so this is not an
 * afterthought: the page keeps its rules, drops its interactive colour, and
 * refuses to break a table row or a chart across a page.
 * ---------------------------------------------------------------------- */
@media print{
  @page{margin:16mm 14mm}
  body{font-size:10.5pt;line-height:1.55}
  .report{max-width:none;padding:0}
  a{color:var(--ink);border-bottom:0}

  /* A printed page cannot scroll. On screen a wide table lives inside its own
     horizontal scroller; on paper that scroller is ignored, the table expands
     the page box, and everything else on the page -- the tile row included --
     gets pushed off the right edge with it. So on paper the table gives up
     its nowrap and some of its size instead, and fits. */
  .table-wrap{overflow:visible;width:100%%}
  table{font-size:8.5pt;table-layout:auto}
  thead th{font-size:7.5pt;white-space:normal;padding-right:8px;padding-bottom:8px}
  tbody td{padding:8px 8px 8px 0;white-space:normal}
  th.num,td.num{white-space:nowrap}
  .tiles{--cols:3}
  .tile{min-height:0;padding:10px 12px 10px}
  .tile .figure{font-size:19pt}
  .tile .spark{padding-top:8px}
  figure svg,figure img{max-width:100%%}
  h1,h2,h3{break-after:avoid;page-break-after:avoid}
  section{break-inside:auto;margin-top:%(sp40)dpx}
  figure,.tile,.note,.no-chart{break-inside:avoid;page-break-inside:avoid}
  tr,thead{break-inside:avoid;page-break-inside:avoid}
  thead{display:table-header-group}
  .tiles{break-inside:avoid;page-break-inside:avoid}
  .colophon{break-inside:avoid}
}
"""


def stylesheet(brand=None, embedded_woff2_b64=None):
    """The complete stylesheet for one report."""
    sp = {"sp%d" % v: v for v in _t.SPACE}
    body = STRUCTURE % dict(
        sp,
        body_type=_type("body"),
        title=_type("title"), section=_type("section"), sub=_type("sub"),
        label=_type("label"), caption=_type("caption"), small=_type("small"),
        table=_type("table"), figure=_type("figure"), delta=_type("delta"),
        p_gap=_t.SPACE[5],            # 16
        pad_top=_t.SPACE[9],          # 56
        pad_bottom=_t.SPACE[11],      # 96
        rule_gap=_t.RULE_GAP,
        pad_small=_t.PAGE_PAD_SMALL,
    )
    return "\n".join([font_face(embedded_woff2_b64), variables(brand), body])


if __name__ == "__main__":
    sys.stdout.write(stylesheet())
