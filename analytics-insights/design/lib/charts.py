"""The shared matplotlib theme.

Every chart in every Analytics & Insights report is drawn through this module,
so a bar in the Google Ads report and a bar in the Search Console report are
the same bar. Before this existed the same forty lines of rcParams were
copied into three scripts, and they had already begun to drift.

A skill imports the names it needs and draws its own forms; it does not define
a colour, a font size or a line width of its own. If a chart needs a value that
is not here, the value belongs in ``tokens.py`` and the design guide, not in
the skill.

The rules the theme enforces, and why
-------------------------------------

**One measure per axis.** There is no helper here for a twin y-axis, because a
dual-axis chart lets whoever draws it choose two scales that make two series
appear to move together or apart. The implication is manufactured, and it is
the commonest way a chart with no false number in it tells a false story. Two
measures get two stacked panels sharing an x-axis.

**Colour carries the job, not the mark.** Change charts are coloured by the
analysis's *verdict* — a CPA that fell is blue because falling is better;
spend that rose is grey because spend has no direction without an objective.
Colouring by sign would mark a falling CPA as a decline.

**Colour is never the only channel.** Direct labels on every bar, a legend
wherever there are two or more series, "(better)" and "(worse)" written into
KPI labels. All of it has to survive a greyscale printer and a reader with
deuteranopia, and the report's own tables are the accessible fallback.

**Recessive chrome.** Hairline solid gridlines one shade off the surface. No
dashes, no tick marks, no box around the marks, no gridline on the categorical
axis. Stacked segments are separated by a gap of surface, not by a border.

Charts are written as SVG *and* PNG. The HTML report inlines the SVG, so the
chart is vector, scales with the column, and is set in the same embedded Inter
as the paragraph beneath it. The PNG is for the Markdown copy.
"""

import os
import sys

_HERE = os.path.dirname(os.path.abspath(__file__))
try:
    from . import tokens as _t
except ImportError:
    sys.path.insert(0, _HERE)
    import tokens as _t

FONT_DIR = os.path.join(os.path.dirname(_HERE), "fonts")


# --------------------------------------------------------------------------
# The names a skill's chart code uses. Mapped from tokens so there is still
# exactly one definition of each colour.
# --------------------------------------------------------------------------

SURFACE = _t.SURFACE_CHART
INK = _t.INK
INK_2 = _t.INK_SECONDARY
MUTED = _t.INK_MUTED
GRID = _t.GRID
AXIS = _t.BORDER_STRONG

BLUE = _t.CATEGORICAL[0]
ORANGE = _t.CATEGORICAL[1]
AQUA = _t.CATEGORICAL[2]          # teal; the historic name is kept so the
MAGENTA = _t.CATEGORICAL[3]       # skills' chart code did not have to change
PURPLE = _t.CATEGORICAL[4]
BLUE_LIGHT = _t.SEQUENTIAL[1]
BLUE_DARK = _t.SEQUENTIAL[4]
RED = _t.VERDICT["declined"]
NEUTRAL = _t.CATEGORICAL_OTHER
PREVIOUS = _t.PREVIOUS
CURRENT = _t.CURRENT

CATEGORICAL = list(_t.CATEGORICAL)
SEQUENTIAL = list(_t.SEQUENTIAL)
VERDICT_COLOR = dict(_t.VERDICT)

LINEWIDTH = _t.CHART_LINEWIDTH
MARKER = _t.CHART_MARKER
SEGMENT_GAP = _t.CHART_BAR_GAP
WIDTH_IN = _t.CHART_WIDTH_IN
FONT = _t.TYPE_CHART


# --------------------------------------------------------------------------
# Loading
# --------------------------------------------------------------------------

def load_matplotlib():
    """Import matplotlib headlessly. Returns ``(None, None, None)`` if absent.

    matplotlib is the plugin's one optional dependency. A skill that cannot
    import it writes a manifest saying so and draws nothing; the report then
    says the visuals are unavailable. It never describes a chart that does not
    exist.
    """
    try:
        import matplotlib
        matplotlib.use("Agg")
        import matplotlib.pyplot as plt
        from matplotlib.ticker import FuncFormatter
        return matplotlib, plt, FuncFormatter
    except ImportError:
        return None, None, None


def register_fonts(matplotlib):
    """Make the vendored Inter available to matplotlib.

    Registering the real font file matters beyond appearance: matplotlib lays
    text out from the font's own metrics, so a chart laid out against Helvetica
    and then displayed in Inter would have labels that no longer sit where they
    were placed. Returns the family name actually available.
    """
    if not os.path.isdir(FONT_DIR):
        return _t.FONT_FALLBACKS_MPL[1]
    try:
        from matplotlib import font_manager
    except ImportError:
        return _t.FONT_FALLBACKS_MPL[1]

    registered = False
    for name in sorted(os.listdir(FONT_DIR)):
        if name.lower().endswith((".ttf", ".otf")):
            try:
                font_manager.fontManager.addfont(os.path.join(FONT_DIR, name))
                registered = True
            except (RuntimeError, OSError):
                pass
    if not registered:
        return _t.FONT_FALLBACKS_MPL[1]
    available = {f.name for f in font_manager.fontManager.ttflist}
    return _t.FONT_FAMILY if _t.FONT_FAMILY in available else _t.FONT_FALLBACKS_MPL[1]


def style(plt, matplotlib):
    """Apply the theme. Call once, before drawing anything."""
    family = register_fonts(matplotlib)
    stack = [family] + [f for f in _t.FONT_FALLBACKS_MPL if f != family]

    matplotlib.rcParams.update({
        "figure.facecolor": SURFACE,
        "axes.facecolor": SURFACE,
        "savefig.facecolor": SURFACE,
        "savefig.edgecolor": SURFACE,

        "font.family": "sans-serif",
        "font.sans-serif": stack,
        "font.size": FONT["tick"],

        "text.color": INK,
        "axes.edgecolor": AXIS,
        "axes.linewidth": 0.8,
        "axes.labelcolor": INK_2,
        "axes.labelsize": FONT["axis"],
        "axes.titlecolor": INK,
        "axes.titlesize": FONT["title"],
        "axes.titleweight": "semibold",

        "axes.grid": True,
        "axes.axisbelow": True,
        "grid.color": GRID,
        "grid.linewidth": _t.CHART_GRID_WIDTH,
        "grid.linestyle": "-",          # solid hairlines; a dashed grid is noise

        "xtick.color": MUTED,
        "ytick.color": MUTED,
        "xtick.labelcolor": INK_2,
        "ytick.labelcolor": INK_2,
        "xtick.labelsize": FONT["tick"],
        "ytick.labelsize": FONT["tick"],

        "legend.frameon": False,
        "legend.fontsize": FONT["legend"],

        "lines.linewidth": LINEWIDTH,
        "lines.solid_capstyle": "round",
        "patch.linewidth": 0,

        "figure.dpi": _t.CHART_DPI,
        "savefig.dpi": _t.CHART_DPI,

        # Keep text as text in the SVG. The HTML report embeds Inter, so inline
        # SVG inherits it: the chart's labels stay selectable, searchable and
        # crisp at any zoom, and the file stays small. Converting text to paths
        # would guarantee the shape but lose all three.
        "svg.fonttype": "none",
    })
    return family


def finish(ax, spines=("top", "right")):
    """Strip the chart down to its marks.

    Removes the named spines, thins what is left, and removes tick marks
    entirely — the gridline already says where the value is, and a tick beside
    it is the same information drawn twice.
    """
    for s in spines:
        ax.spines[s].set_visible(False)
    for s in ax.spines.values():
        s.set_linewidth(0.8)
        s.set_color(AXIS)
    ax.tick_params(axis="both", length=0, pad=6)


def no_grid(ax, axis="y"):
    """Turn off the gridline on a categorical axis, which measures nothing."""
    ax.grid(False, axis=axis)


# --------------------------------------------------------------------------
# Output
# --------------------------------------------------------------------------

def save_figure(fig, plt, out_dir, stem, name, formats=None, pad=0.28):
    """Write one figure in every configured format.

    Returns ``{extension: path}``, with the SVG first — it is what the HTML
    report inlines, and the PNG is the Markdown copy of the same drawing.
    """
    formats = formats or _t.CHART_FORMATS
    paths = {}
    for ext in formats:
        path = os.path.join(out_dir, "%s_%s.%s" % (stem, name, ext))
        fig.savefig(path, format=ext, bbox_inches="tight", pad_inches=pad,
                    facecolor=SURFACE)
        paths[ext] = path
    plt.close(fig)
    return paths


def save_twin(fig, png_path, pad=0.28):
    """Write a figure as PNG and as its SVG twin, without closing it.

    For chart code that already manages its own figure lifecycle. Give it the
    PNG path it was going to write; it writes ``<stem>.svg`` beside it, which
    is the file the HTML report inlines. Returns the SVG path.
    """
    png_path = str(png_path)
    svg_path = os.path.splitext(png_path)[0] + ".svg"
    fig.savefig(png_path, format="png", bbox_inches="tight", pad_inches=pad,
                facecolor=SURFACE)
    fig.savefig(svg_path, format="svg", bbox_inches="tight", pad_inches=pad,
                facecolor=SURFACE)
    return svg_path


# --------------------------------------------------------------------------
# Shared furniture
# --------------------------------------------------------------------------

def suptitle(fig, title, subtitle, wrap=104):
    """The title block, measured in inches rather than figure fractions.

    A figure fraction is a different physical offset at every chart height,
    which is how a title ends up sitting on top of its own subtitle on one
    chart and floating above it on the next.

    Every chart carries its subtitle, and every subtitle carries the exact
    date ranges. A chart that travels out of the report without its dates
    cannot be checked by the person it was sent to.
    """
    import textwrap
    lines = textwrap.wrap(subtitle, wrap) if subtitle else []
    h = fig.get_size_inches()[1]
    fig.text(0.012, 1 - 0.20 / h, title, ha="left", va="top",
             fontsize=FONT["title"], fontweight="semibold", color=INK)
    for i, line in enumerate(lines):
        fig.text(0.012, 1 - (0.46 + 0.155 * i) / h, line, ha="left", va="top",
                 fontsize=FONT["subtitle"], color=INK_2)
    reserve = 0.55 + 0.16 * len(lines)
    fig.subplots_adjust(top=1 - reserve / h)


def legend_below(fig, handles, labels, ncol):
    """Legends sit under the plot in reserved space, never over the marks."""
    h = fig.get_size_inches()[1]
    fig.subplots_adjust(bottom=fig.subplotpars.bottom + 0.42 / h)
    fig.legend(handles, labels, loc="lower left", bbox_to_anchor=(0.012, 0.005),
               ncol=ncol, frameon=False, fontsize=FONT["legend"])


def verdict_color(verdict):
    return VERDICT_COLOR.get(verdict, NEUTRAL)


def series_color(index):
    """The categorical colour for series ``index``, in fixed order.

    Never cycles and never generates. Past the fifth class the answer is a
    table or an "Other" group, not a sixth hue that no reader can tell from
    the second.
    """
    if index < len(CATEGORICAL):
        return CATEGORICAL[index]
    return _t.CATEGORICAL_OTHER
