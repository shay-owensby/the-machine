"""The Analytics & Insights design tokens.

This module is the single source of truth. The stylesheet, the matplotlib
chart theme, the stat tiles and the HTML shell are all generated from these
values, so a colour or a spacing step exists in exactly one place.

Nothing here is decorative. Every colour has a measured contrast ratio against
the surface it is used on, and the categorical set has a measured worst-pair
separation under normal, protan, deutan and tritan vision. Run
``python3 tokens.py`` to re-check all of it.

The design is deliberately **single-mode light**. A report is printed, mailed
and read on a client's screen; a PNG or a PDF cannot answer a reader's theme,
and a chart that tries to work in both modes works well in neither.
"""

import sys

try:
    from . import color as _c
except ImportError:  # executed directly, or imported by path
    import os
    sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
    import color as _c


# ==========================================================================
# Surfaces and ink
# --------------------------------------------------------------------------
# A cool near-white, not the warm off-white of the previous system. Warmth
# reads as "document"; the Linear register is neutral and slightly cool, and
# it keeps the client's own accent from being tinted by the paper it sits on.
# ==========================================================================

SURFACE = "#ffffff"          # the page
SURFACE_SUBTLE = "#fafafa"   # table header bands, tile grounds
SURFACE_INSET = "#f4f4f5"    # callouts, code, "no data" panels
SURFACE_CHART = "#ffffff"    # charts sit on the page, not on a card

INK = "#08090a"              # 19.9:1 — headings, figures, table values
INK_SECONDARY = "#3c3f44"    # 10.6:1 — body copy
INK_MUTED = "#6f737b"        #  4.8:1 — captions, axis labels, meta
INK_FAINT = "#9a9ea6"        #  2.7:1 — decorative only, never load-bearing

BORDER = "#e6e6e9"           # hairlines, table rules, tile edges
BORDER_STRONG = "#d0d0d5"    # axis lines, emphasised rules
GRID = "#eeeef0"             # chart gridlines, one shade off the surface


# ==========================================================================
# Accent
# --------------------------------------------------------------------------
# The default is Linear's indigo. It is replaced per client by brand.py, which
# is why nothing structural depends on this hue — the accent marks links, the
# active rule and the report's one emphasis, and never encodes data.
# ==========================================================================

ACCENT = "#5b60d9"           # 5.1:1 on white — passes as link text
ACCENT_STRONG = "#4348c0"    # hover / pressed
ACCENT_SUBTLE = "#eeeefc"    # tint ground behind an accented block


# ==========================================================================
# Data colour
# --------------------------------------------------------------------------
# Fixed. A client's brand colour never enters a chart: if the accent changed
# per client, the same chart would encode a different meaning in two reports,
# and two clients' reports could not be read with the same eye.
#
# Measured (see validate()): every hue >= 3.10:1 on white; worst pair across
# all four vision types dE2000 6.9 (tritan, blue vs teal).
# ==========================================================================

CATEGORICAL = [
    "#3060e0",   # blue
    "#e0761f",   # amber
    "#0f8f74",   # teal
    "#c2409e",   # magenta
    "#6b21a8",   # purple
]

CATEGORICAL_NAMES = ["blue", "amber", "teal", "magenta", "purple"]

# Anything past the fifth class is grouped into this, never given a sixth hue.
CATEGORICAL_OTHER = "#c4c6cc"

# Verdict colouring: by whether the move was *good*, never by its sign.
# A CPA that fell is blue. Spend that rose is grey. Colouring by sign would
# mark a falling CPA as a decline, which is the single most common way a
# correct chart tells a false story.
VERDICT = {
    "improved": "#3060e0",   # blue, not green: survives red-green deficiency
    "declined": "#e5484d",   # red
    "ambiguous": "#8b8d98",  # directionally neutral (spend, impressions)
    "flat": "#c4c6cc",       # below the materiality threshold
    "new": "#0f8f74",        # present this period only
    "unknown": "#c4c6cc",
}

# Period comparison in dumbbells and paired bars.
PREVIOUS = "#b9bbc2"
CURRENT = "#3060e0"

# Sequential ramp for magnitude — one hue, light to dark. Generated from the
# categorical blue so a magnitude chart and a categorical chart are visibly
# the same family.
SEQUENTIAL = ["#dce6fb", "#a8c0f4", "#6f93ec", "#3060e0", "#1e3f96"]


# ==========================================================================
# Typography
# --------------------------------------------------------------------------
# Inter, vendored with the plugin under design/fonts (SIL OFL). The page
# embeds it; matplotlib loads the same family from the same directory, so a
# chart's axis labels and the paragraph beneath them are set in one typeface.
#
# Tight negative tracking on large sizes is the most recognisable single
# element of this register. It must scale with size: -0.022em on a 30px title
# and 0 on 12px body, never a flat value applied everywhere.
# ==========================================================================

FONT_STACK = ('Inter, ui-sans-serif, -apple-system, BlinkMacSystemFont, '
              '"Segoe UI", Helvetica, Arial, sans-serif')
FONT_STACK_MONO = ('ui-monospace, SFMono-Regular, "SF Mono", Menlo, Consolas, '
                   '"Liberation Mono", monospace')
FONT_FAMILY = "Inter"
FONT_FALLBACKS_MPL = ["Inter", "Helvetica Neue", "Helvetica", "Arial", "DejaVu Sans"]

WEIGHT_REGULAR = 400
WEIGHT_MEDIUM = 500
WEIGHT_SEMIBOLD = 600

# (size px, line-height, letter-spacing em, weight)
TYPE = {
    "title":    (30, 1.18, -0.022, 600),
    "section":  (21, 1.25, -0.017, 600),
    "sub":      (16, 1.35, -0.011, 600),
    "body":     (15, 1.65, -0.004, 400),
    "small":    (13.5, 1.55, -0.002, 400),
    "table":    (13.5, 1.45, -0.002, 400),
    "caption":  (12.5, 1.5, 0.0, 400),
    "label":    (11.5, 1.3, 0.062, 600),   # uppercase eyebrow
    "figure":   (30, 1.1, -0.024, 600),    # the number on a stat tile
    "delta":    (13, 1.2, -0.004, 500),
}

# Chart type sizes, in points, so a chart's label matches the page's caption
# at the size the chart is actually placed.
TYPE_CHART = {
    "title": 13.5,
    "subtitle": 10.0,
    "axis": 9.5,
    "tick": 9.0,
    "value": 9.0,
    "legend": 9.5,
    "annotation": 8.5,
}


# ==========================================================================
# Space, measure, chrome
# ==========================================================================

SPACE = [0, 2, 4, 8, 12, 16, 24, 32, 40, 56, 72, 96, 128]

RADIUS = 0                   # every corner, everywhere. No exceptions.
HAIRLINE = 1                 # px

MEASURE_PROSE = 720          # px — the executive summary reads at this width
MEASURE_WIDE = 1080          # px — tables, charts and the tile grid
PAGE_PAD = 56                # px — desktop gutter
PAGE_PAD_SMALL = 20          # px — narrow viewport gutter
SECTION_GAP = 72             # px — between top-level sections
RULE_GAP = 40                # px — around a horizontal rule


# ==========================================================================
# Charts
# ==========================================================================

CHART_DPI = 160              # for the PNG copy; SVG is resolution independent
CHART_WIDTH_IN = 9.0         # standard full-width figure
CHART_WIDTH_HALF_IN = 4.4
CHART_LINEWIDTH = 1.8
CHART_GRID_WIDTH = 1.0
CHART_BAR_GAP = 2.0          # px of surface between stacked segments, not a border
CHART_MARKER = 6.5

# The catalogue is shared. A skill adds an entry rather than inventing a
# private chart type, so "the campaign chart" means one thing across reports.
CHART_FORMATS = ("svg", "png")


# ==========================================================================
# Validation
# ==========================================================================

CONTRAST_FLOOR_TEXT = 4.5    # WCAG AA, body text
CONTRAST_FLOOR_LARGE = 3.0   # WCAG AA, >=18.66px semibold
CONTRAST_FLOOR_MARK = 3.0    # WCAG AA non-text, a chart mark on its surface
SEPARATION_FLOOR = 5.0       # dE2000 between any two categorical hues, any vision


def validate():
    """Re-derive every claim this module makes. Returns (ok, lines)."""
    lines = []
    ok = True

    def check(label, actual, floor, unit=":1"):
        nonlocal ok
        passed = actual >= floor
        if not passed:
            ok = False
        lines.append("  %s %-38s %6.2f%s  (floor %.2f)"
                     % ("PASS" if passed else "FAIL", label, actual, unit, floor))

    lines.append("Text and ink on the page surface (%s)" % SURFACE)
    for name, hexv, floor in [
        ("ink", INK, CONTRAST_FLOOR_TEXT),
        ("ink-secondary", INK_SECONDARY, CONTRAST_FLOOR_TEXT),
        ("ink-muted", INK_MUTED, CONTRAST_FLOOR_TEXT),
        ("accent (as link text)", ACCENT, CONTRAST_FLOOR_TEXT),
        ("accent-strong", ACCENT_STRONG, CONTRAST_FLOOR_TEXT),
    ]:
        check(name, _c.contrast_ratio(hexv, SURFACE), floor)

    lines.append("")
    lines.append("Ink on the subtle surface (%s)" % SURFACE_SUBTLE)
    for name, hexv in [("ink", INK), ("ink-muted", INK_MUTED)]:
        check(name, _c.contrast_ratio(hexv, SURFACE_SUBTLE), CONTRAST_FLOOR_TEXT)

    lines.append("")
    lines.append("Chart marks on the chart surface (%s)" % SURFACE_CHART)
    for i, hexv in enumerate(CATEGORICAL):
        check("categorical %d (%s)" % (i + 1, CATEGORICAL_NAMES[i]),
              _c.contrast_ratio(hexv, SURFACE_CHART), CONTRAST_FLOOR_MARK)
    for name in ("improved", "declined", "ambiguous"):
        check("verdict %s" % name,
              _c.contrast_ratio(VERDICT[name], SURFACE_CHART), CONTRAST_FLOOR_MARK)
    check("sequential darkest",
          _c.contrast_ratio(SEQUENTIAL[-1], SURFACE_CHART), CONTRAST_FLOOR_MARK)

    lines.append("")
    lines.append("Categorical separation, all pairs, all vision types")
    sep = _c.worst_pair_separation(CATEGORICAL)
    for kind in _c.CVD_KINDS:
        d, a, b = sep[kind]
        lines.append("  %s %-38s %6.2f    (%s vs %s)"
                     % ("PASS" if d >= SEPARATION_FLOOR else "FAIL",
                        "dE2000 worst pair, %s" % kind, d, a, b))
        if d < SEPARATION_FLOOR:
            ok = False

    lines.append("")
    lines.append("Verdict separation, all pairs, all vision types")
    sep = _c.worst_pair_separation([VERDICT["improved"], VERDICT["declined"],
                                    VERDICT["ambiguous"]])
    for kind in _c.CVD_KINDS:
        d, a, b = sep[kind]
        lines.append("  %s %-38s %6.2f    (%s vs %s)"
                     % ("PASS" if d >= SEPARATION_FLOOR else "FAIL",
                        "dE2000 worst pair, %s" % kind, d, a, b))
        if d < SEPARATION_FLOOR:
            ok = False

    lines.append("")
    lines.append("Structural invariants")
    if RADIUS != 0:
        ok = False
        lines.append("  FAIL radius must be 0 everywhere")
    else:
        lines.append("  PASS radius is 0 everywhere")
    if len(CATEGORICAL) != len(CATEGORICAL_NAMES):
        ok = False
        lines.append("  FAIL categorical names do not match the palette")
    else:
        lines.append("  PASS categorical palette is named")

    return ok, lines


if __name__ == "__main__":
    ok, lines = validate()
    print("Analytics & Insights design tokens")
    print("=" * 66)
    for line in lines:
        print(line)
    print("=" * 66)
    print("OK" if ok else "FAILED")
    sys.exit(0 if ok else 1)
