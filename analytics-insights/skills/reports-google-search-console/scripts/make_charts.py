#!/usr/bin/env python3
"""
Draw the report's charts from an analysis file. Reads a file, writes PNGs, and
records what it drew -- and what it could not -- in a manifest.

    python3 make_charts.py --analysis <..._analysis.json> --out <dir> --update-analysis

Design rules this file follows, so the charts read as one system:

  * One measure per axis. Never two y-scales on one plot. A dual-axis chart lets
    the author imply a relationship by choosing the scales, which is exactly what
    an executive report must not do.
  * Average position is drawn on an INVERTED axis, so an improvement moves up,
    and every position chart says so in its subtitle. A position chart with a
    conventional axis reads as a collapse when the rankings improved.
  * Colour carries the job, not the mark. Change charts are diverging (better /
    worse / ambiguous, decided by the analysis rather than by the sign);
    magnitude charts are one hue; composition charts use a fixed order.
  * Colour is never the only channel: bars carry direct labels, the legend is
    present with two or more series, and the report's tables are the accessible
    fallback.
  * A chart whose data is unavailable is not drawn and is not faked. It is listed
    in the manifest with the reason, so the report can say so in words.

Palette: the validated default categorical/diverging set -- blue #2a78d6, orange
#eb6834, aqua #1baf7a, diverging blue<->red #e34948 with a grey neutral.

Exit codes: 0 charts drawn · 3 nothing could be drawn · 4 matplotlib missing.
"""

import argparse
import json
import sys
from pathlib import Path

# -- design system ---------------------------------------------------------
# Colour, type, spacing and the whole chart theme come from the plugin's design
# system rather than from this file. See design/DESIGN.md for what the values
# mean and why they are what they are. A colour changed here instead of there
# puts this report out of step with every other report the plugin produces --
# which is exactly the drift this import exists to stop.
sys.path.insert(0, str(Path(__file__).resolve().parents[3] / "design" / "lib"))
from charts import (                                                # noqa: E402
    SURFACE, INK, INK_2, MUTED, GRID, AXIS,
    BLUE, BLUE_LIGHT, BLUE_DARK, ORANGE, AQUA, MAGENTA, PURPLE,
    RED, NEUTRAL, PREVIOUS, CURRENT,
    CATEGORICAL, SEQUENTIAL, VERDICT_COLOR,
    load_matplotlib, style, finish, no_grid, series_color,
    save_figure, save_twin,
    suptitle as design_suptitle, legend_below as design_legend_below,
)



def thousands(FuncFormatter):
    return FuncFormatter(lambda v, _: "{:,.0f}".format(v))


def truncate(text, width=34):
    text = str(text or "")
    return text if len(text) <= width else text[: width - 1] + "…"


class Manifest(object):
    """Every chart the report might reference: drawn, or skipped with a reason
    the report can print as a sentence."""

    def __init__(self):
        self.entries = []

    def drawn(self, key, path, title, alt, explains):
        self.entries.append({
            "key": key, "status": "drawn", "file": str(path), "filename": Path(path).name,
            "title": title, "alt": alt, "explains": explains,
        })

    def skipped(self, key, title, reason):
        self.entries.append({
            "key": key, "status": "not drawn", "file": None, "filename": None,
            "title": title, "alt": None, "reason": reason,
        })

    def as_list(self):
        return self.entries

    @property
    def drawn_count(self):
        return len([e for e in self.entries if e["status"] == "drawn"])


# ---------------------------------------------------------------------------
# Charts
# ---------------------------------------------------------------------------

def chart_kpi_summary(a, plt, out, stem, manifest, period_label):
    kpis = [k for k in a["kpis"] if k["availability"] == "available"
            and k["percent_change"] is not None]
    if not kpis:
        manifest.skipped(
            "kpi-summary", "KPI change",
            "No KPI had a comparable value in both periods, so there is no change to plot.")
        return

    labels, values, colors = [], [], []
    for k in kpis:
        label = k["label"]
        if k["key"] == "average_position":
            label += "\n(lower is better)"
        labels.append(label)
        values.append(k["percent_change"])
        colors.append(VERDICT_COLOR.get(k["verdict"], NEUTRAL))

    fig, ax = plt.subplots(figsize=(8.2, 4.0))
    bars = ax.bar(labels, values, color=colors, width=0.55)
    ax.axhline(0, color=AXIS, linewidth=1.0)
    span = max(abs(min(values)), abs(max(values)), 1.0)
    ax.set_ylim(min(0, min(values)) - span * 0.25, max(0, max(values)) + span * 0.25)
    for bar, k in zip(bars, kpis):
        v = k["percent_change"]
        offset = span * 0.05
        ax.text(bar.get_x() + bar.get_width() / 2, v + (offset if v >= 0 else -offset),
                "%+.1f%%" % v, ha="center", va="bottom" if v >= 0 else "top",
                fontsize=9.5, color=INK, fontweight="medium")
    ax.set_ylabel("Change vs comparison period (%)")
    ax.set_title("Search performance change\n%s" % period_label, loc="left")
    ax.text(0.0, -0.22, "Blue = better for the property · red = worse · grey = no verdict. "
                        "A fall in average position is an improvement.",
            transform=ax.transAxes, fontsize=8.5, color=MUTED)
    fig.tight_layout()
    path = out / ("%s_kpi-summary.png" % stem)
    save_twin(fig, path)
    plt.close(fig)
    manifest.drawn(
        "kpi-summary", path, "Search performance change",
        "Bar chart of percentage change for clicks, impressions, CTR and average position "
        "between the two periods, coloured by whether the move is better or worse for the "
        "property.",
        "Which headline metrics moved, in which direction, and by how much.")


def _trend(a, plt, FuncFormatter, out, stem, manifest, key, metric, title, ylabel, alt,
           explains, period_label, invert=False, percent=False, decimals=False):
    trend = a.get("trend") or {}
    current = [d for d in trend.get("current", []) if d.get(metric) is not None]
    previous = [d for d in trend.get("previous", []) if d.get(metric) is not None]
    if len(current) < 3:
        manifest.skipped(key, title,
                         "Fewer than three days of %s data were returned for the current "
                         "period." % metric)
        return

    fig, ax = plt.subplots(figsize=(9.0, 3.9))
    xs = list(range(len(current)))
    ys = [d[metric] for d in current]

    if previous:
        prev_ys = [d[metric] for d in previous][: len(current)]
        ax.plot(range(len(prev_ys)), prev_ys, color=NEUTRAL, linewidth=1.4, linestyle="--",
                label="Previous period (%s to %s)" % (a["periods"]["previous"]["start"],
                                                      a["periods"]["previous"]["end"]))
    ax.plot(xs, ys, color=BLUE, linewidth=2.0,
            label="Current period (%s to %s)" % (a["periods"]["current"]["start"],
                                                 a["periods"]["current"]["end"]))
    if not invert:
        # No shading under an inverted axis: "the area below the line" points at
        # the top of the chart and reads as a filled block rather than a volume.
        ax.fill_between(xs, ys, 0, color=BLUE, alpha=0.07)

    ticks = list(range(0, len(current), max(1, len(current) // 6)))
    ax.set_xticks(ticks)
    ax.set_xticklabels([current[i]["date"][5:] for i in ticks])
    ax.set_xlabel("Day of period (current period dates shown)")
    ax.set_ylabel(ylabel)
    if percent:
        ax.yaxis.set_major_formatter(FuncFormatter(lambda v, _: "%.1f%%" % v))
    elif decimals:
        # Average position lives between about 1 and 40, so rounding the axis to
        # whole thousands prints "10" four times down the side of the chart.
        ax.yaxis.set_major_formatter(FuncFormatter(lambda v, _: "%.1f" % v))
    else:
        ax.yaxis.set_major_formatter(thousands(FuncFormatter))
    if invert:
        ax.invert_yaxis()

    subtitle = period_label
    if invert:
        subtitle += " · axis inverted: higher on the chart is a better position"
    ax.set_title("%s\n%s" % (title, subtitle), loc="left")

    # Mark anomalies the analysis actually accepted -- not every wobble.
    for anomaly in (trend.get("anomalies") or []):
        if anomaly.get("metric") != metric:
            continue
        for i, d in enumerate(current):
            if d["date"] == anomaly["date"]:
                ax.scatter([i], [d[metric]], s=46, facecolor="none", edgecolor=ORANGE,
                           linewidth=1.6, zorder=5)
                ax.annotate(anomaly["kind"], (i, d[metric]), textcoords="offset points",
                            xytext=(0, 12 if anomaly["kind"] == "spike" else -16),
                            ha="center", fontsize=8, color=ORANGE)
    ax.legend(loc="best", fontsize=8.5)
    fig.tight_layout()
    path = out / ("%s_%s.png" % (stem, key))
    save_twin(fig, path)
    plt.close(fig)
    manifest.drawn(key, path, title, alt, explains)


def chart_movers(a, plt, FuncFormatter, out, stem, manifest, node_key, key_label, key, title,
                 period_label):
    node = a.get(node_key) or {}
    winners = (node.get("winners") or [])[:5]
    losers = (node.get("losers") or [])[:5]
    rows = winners + list(reversed(losers))
    if len(rows) < 2:
        top = (node.get("top_by_clicks") or [])[:8]
        if len(top) < 2:
            manifest.skipped(key, title,
                             "Too few %s rows with comparable data in both periods." % key_label)
            return
        labels = [truncate(r.get("path") or r.get(key_label)) for r in top]
        values = [r["clicks"] or 0 for r in top]
        fig, ax = plt.subplots(figsize=(8.6, max(3.0, 0.42 * len(top) + 1.4)))
        ax.barh(labels[::-1], values[::-1], color=BLUE, height=0.6)
        ax.set_xlabel("Clicks, current period")
        ax.xaxis.set_major_formatter(thousands(FuncFormatter))
        ax.set_title("%s\n%s" % (title, period_label), loc="left")
        for i, v in enumerate(values[::-1]):
            ax.text(v, i, " {:,.0f}".format(v), va="center", fontsize=8.5, color=INK_2)
        fig.tight_layout()
        path = out / ("%s_%s.png" % (stem, key))
        save_twin(fig, path)
        plt.close(fig)
        manifest.drawn(key, path, title,
                       "Horizontal bar chart of the top %ss by clicks in the current period."
                       % key_label,
                       "Where the organic clicks actually come from.")
        return

    labels = [truncate(r.get("path") or r.get(key_label)) for r in rows]
    values = [r["clicks_change"] for r in rows]
    colors = [BLUE if v > 0 else RED for v in values]

    fig, ax = plt.subplots(figsize=(8.6, max(3.2, 0.44 * len(rows) + 1.4)))
    ax.barh(labels[::-1], values[::-1], color=colors[::-1], height=0.6)
    ax.axvline(0, color=AXIS, linewidth=1.0)
    ax.set_xlabel("Change in clicks vs comparison period")
    ax.xaxis.set_major_formatter(thousands(FuncFormatter))
    ax.set_title("%s\n%s" % (title, period_label), loc="left")
    span = max(abs(v) for v in values) or 1
    for i, v in enumerate(values[::-1]):
        ax.text(v + (span * 0.02 if v >= 0 else -span * 0.02), i,
                "{:+,.0f}".format(v),
                va="center", ha="left" if v >= 0 else "right", fontsize=8.5, color=INK_2)
    ax.set_xlim(min(0, min(values)) - span * 0.22, max(0, max(values)) + span * 0.22)
    fig.tight_layout()
    path = out / ("%s_%s.png" % (stem, key))
    save_twin(fig, path)
    plt.close(fig)
    manifest.drawn(
        key, path, title,
        "Horizontal bar chart of the %ss that gained and lost the most clicks between the two "
        "periods; blue gained, red lost." % key_label,
        "Which %ss the change in organic traffic actually came from." % key_label)


def chart_opportunities(a, plt, FuncFormatter, out, stem, manifest, period_label):
    """Impressions against position, sized by clicks. The bottom-right of this
    chart is the report's shortlist: high visibility, weak ranking."""
    node = a.get("pages") or {}
    rows = [r for r in (node.get("top_by_impressions") or [])
            if r.get("impressions") and r.get("position") is not None]
    if len(rows) < 4:
        manifest.skipped(
            "search-opportunities", "Visibility against ranking",
            "Fewer than four pages had both impressions and an average position.")
        return

    fig, ax = plt.subplots(figsize=(8.4, 5.0))
    xs = [r["position"] for r in rows]
    ys = [r["impressions"] for r in rows]
    sizes = [max(20, min(600, (r["clicks"] or 0) * 1.2)) for r in rows]
    ctrs = [r["ctr"] or 0 for r in rows]
    median_ctr = sorted(ctrs)[len(ctrs) // 2] if ctrs else 0
    colors = [BLUE if c >= median_ctr else ORANGE for c in ctrs]

    ax.scatter(xs, ys, s=sizes, c=colors, alpha=0.72, edgecolor=SURFACE, linewidth=1.0)
    for r in sorted(rows, key=lambda r: r["impressions"], reverse=True)[:6]:
        ax.annotate(truncate(r.get("path") or r.get("page"), 26),
                    (r["position"], r["impressions"]), textcoords="offset points",
                    xytext=(6, 6), fontsize=8, color=INK_2)

    ax.axvspan(3.5, 10.5, color=AQUA, alpha=0.06)
    ax.axvspan(10.5, 20.5, color=ORANGE, alpha=0.05)
    ax.text(7.0, ax.get_ylim()[1] * 0.97, "positions 4-10", fontsize=8, color=MUTED,
            ha="center", va="top")
    ax.text(15.5, ax.get_ylim()[1] * 0.97, "positions 11-20", fontsize=8, color=MUTED,
            ha="center", va="top")

    ax.set_xlabel("Average position (lower is better)")
    ax.set_ylabel("Impressions, current period")
    ax.yaxis.set_major_formatter(thousands(FuncFormatter))
    ax.set_title("Visibility against ranking, by page\n%s" % period_label, loc="left")
    ax.text(0.0, -0.16,
            "Bubble size = clicks. Orange = CTR below this property's median; blue = at or "
            "above. Large orange bubbles to the right are the shortlist.",
            transform=ax.transAxes, fontsize=8.5, color=MUTED)
    fig.tight_layout()
    path = out / ("%s_search-opportunities.png" % stem)
    save_twin(fig, path)
    plt.close(fig)
    manifest.drawn(
        "search-opportunities", path, "Visibility against ranking, by page",
        "Scatter plot of pages: average position on the horizontal axis, impressions on the "
        "vertical, bubble size by clicks, orange where CTR is below the property median.",
        "Where large visibility sits at weak positions or weak CTR -- the pages with the most "
        "room to improve.")


def chart_devices(a, plt, FuncFormatter, out, stem, manifest, period_label):
    node = a.get("devices") or {}
    rows = [r for r in (node.get("rows") or []) if r.get("clicks") is not None]
    if len(rows) < 2:
        manifest.skipped("device-performance", "Performance by device",
                         "Device data was not returned for this property.")
        return

    fig, (ax1, ax2) = plt.subplots(1, 2, figsize=(9.2, 3.8))
    labels = [str(r["device"]).capitalize() for r in rows]
    current = [r["clicks"] or 0 for r in rows]
    previous = [r["previous_clicks"] or 0 for r in rows]
    width = 0.38
    idx = range(len(rows))
    ax1.bar([i - width / 2 for i in idx], previous, width, color=NEUTRAL, label="Previous")
    ax1.bar([i + width / 2 for i in idx], current, width, color=BLUE, label="Current")
    ax1.set_xticks(list(idx))
    ax1.set_xticklabels(labels)
    ax1.set_ylabel("Clicks")
    ax1.yaxis.set_major_formatter(thousands(FuncFormatter))
    ax1.legend(fontsize=8.5)
    ax1.set_title("Clicks by device", loc="left")

    ctr_current = [r["ctr"] or 0 for r in rows]
    ctr_previous = [r["previous_ctr"] or 0 for r in rows]
    ax2.bar([i - width / 2 for i in idx], ctr_previous, width, color=NEUTRAL, label="Previous")
    ax2.bar([i + width / 2 for i in idx], ctr_current, width, color=AQUA, label="Current")
    ax2.set_xticks(list(idx))
    ax2.set_xticklabels(labels)
    ax2.set_ylabel("CTR")
    ax2.yaxis.set_major_formatter(FuncFormatter(lambda v, _: "%.1f%%" % v))
    ax2.legend(fontsize=8.5)
    ax2.set_title("CTR by device", loc="left")

    fig.suptitle("Performance by device · %s" % period_label, x=0.01, ha="left",
                 fontsize=12.5, fontweight="semibold")
    fig.tight_layout(rect=(0, 0, 1, 0.93))
    path = out / ("%s_device-performance.png" % stem)
    save_twin(fig, path)
    plt.close(fig)
    manifest.drawn(
        "device-performance", path, "Performance by device",
        "Two grouped bar charts comparing clicks and CTR by device between the two periods.",
        "Whether mobile, desktop and tablet moved in the same direction, and where CTR differs.")


def chart_countries(a, plt, FuncFormatter, out, stem, manifest, period_label):
    node = a.get("countries") or {}
    if not node:
        manifest.skipped("country-performance", "Performance by country",
                         "Country data was not returned for this property.")
        return
    if not node.get("material"):
        manifest.skipped(
            "country-performance", "Performance by country",
            "Geography is immaterial for this property: %s%% of clicks come from a single "
            "market and no other market moved materially."
            % (node.get("top_country_share_pct") or "almost all"))
        return
    rows = [r for r in (node.get("rows") or [])[:8] if r.get("clicks")]
    if len(rows) < 2:
        manifest.skipped("country-performance", "Performance by country",
                         "Fewer than two countries returned clicks.")
        return

    fig, ax = plt.subplots(figsize=(8.4, max(3.0, 0.44 * len(rows) + 1.3)))
    labels = [str(r["country"]).upper() for r in rows]
    current = [r["clicks"] or 0 for r in rows]
    previous = [r["previous_clicks"] or 0 for r in rows]
    height = 0.38
    idx = list(range(len(rows)))
    ax.barh([i + height / 2 for i in idx][::-1], previous[::-1], height, color=NEUTRAL,
            label="Previous")
    ax.barh([i - height / 2 for i in idx][::-1], current[::-1], height, color=BLUE,
            label="Current")
    ax.set_yticks(idx[::-1])
    ax.set_yticklabels(labels)
    ax.set_xlabel("Clicks")
    ax.xaxis.set_major_formatter(thousands(FuncFormatter))
    ax.legend(fontsize=8.5)
    ax.set_title("Clicks by country\n%s" % period_label, loc="left")
    fig.tight_layout()
    path = out / ("%s_country-performance.png" % stem)
    save_twin(fig, path)
    plt.close(fig)
    manifest.drawn(
        "country-performance", path, "Clicks by country",
        "Grouped horizontal bar chart comparing clicks by country between the two periods.",
        "Which markets carry the traffic and which of them moved.")


# ---------------------------------------------------------------------------
# CLI
# ---------------------------------------------------------------------------

def main():
    ap = argparse.ArgumentParser(description="Draw charts from a Search Console analysis file.")
    ap.add_argument("--analysis", required=True, help="Path to a *_analysis.json")
    ap.add_argument("--out", help="Directory for the PNGs (default: ../charts of the analysis)")
    ap.add_argument("--update-analysis", action="store_true",
                    help="Write the chart manifest back into the analysis file")
    args = ap.parse_args()

    analysis_path = Path(args.analysis).expanduser()
    if not analysis_path.is_file():
        print("No such analysis file: %s" % analysis_path, file=sys.stderr)
        return 2
    a = json.loads(analysis_path.read_text())

    out = Path(args.out).expanduser() if args.out else analysis_path.parent.parent / "charts"
    out.mkdir(parents=True, exist_ok=True)
    stem = analysis_path.name[:-len("_analysis.json")] \
        if analysis_path.name.endswith("_analysis.json") else analysis_path.stem

    matplotlib, plt, FuncFormatter = load_matplotlib()
    manifest = Manifest()
    period_label = "%s to %s vs %s to %s" % (
        a["periods"]["current"]["start"], a["periods"]["current"]["end"],
        a["periods"]["previous"]["start"], a["periods"]["previous"]["end"])

    if plt is None:
        reason = ("matplotlib is not installed, so no charts were drawn. Install it with "
                  "`python3 -m pip install matplotlib` and re-run. The report must say the "
                  "visuals are unavailable rather than describe charts that do not exist.")
        for key, title in (
            ("kpi-summary", "Search performance change"),
            ("organic-click-trend", "Daily organic clicks"),
            ("organic-impression-trend", "Daily impressions"),
            ("ctr-trend", "Daily click-through rate"),
            ("position-trend", "Daily average position"),
            ("query-performance", "Query gains and losses"),
            ("page-performance", "Page gains and losses"),
            ("search-opportunities", "Visibility against ranking, by page"),
            ("device-performance", "Performance by device"),
            ("country-performance", "Clicks by country"),
        ):
            manifest.skipped(key, title, reason)
        write_manifest(a, manifest, out, stem, analysis_path, args.update_analysis)
        print(reason, file=sys.stderr)
        return 4

    style(plt, matplotlib)

    chart_kpi_summary(a, plt, out, stem, manifest, period_label)
    _trend(a, plt, FuncFormatter, out, stem, manifest, "organic-click-trend", "clicks",
           "Daily organic clicks", "Clicks",
           "Line chart of daily organic clicks across the current period, with the comparison "
           "period behind it as a dashed line.",
           "The shape of the period: whether the change was steady, a step, or one event.",
           period_label)
    _trend(a, plt, FuncFormatter, out, stem, manifest, "organic-impression-trend", "impressions",
           "Daily impressions", "Impressions",
           "Line chart of daily impressions across the current period, with the comparison "
           "period behind it as a dashed line.",
           "Whether visibility moved with clicks or independently of them.",
           period_label)
    _trend(a, plt, FuncFormatter, out, stem, manifest, "ctr-trend", "ctr",
           "Daily click-through rate", "CTR",
           "Line chart of daily click-through rate across the current period.",
           "Whether the share of impressions turning into clicks is holding, rising or eroding.",
           period_label, percent=True)
    _trend(a, plt, FuncFormatter, out, stem, manifest, "position-trend", "position",
           "Daily average position", "Average position",
           "Line chart of daily average position with an inverted axis, so an improvement in "
           "ranking moves upward.",
           "Whether ranking movement explains the click trend.",
           period_label, invert=True, decimals=True)
    chart_movers(a, plt, FuncFormatter, out, stem, manifest, "queries", "query",
                 "query-performance", "Query gains and losses", period_label)
    chart_movers(a, plt, FuncFormatter, out, stem, manifest, "pages", "page",
                 "page-performance", "Page gains and losses", period_label)
    chart_opportunities(a, plt, FuncFormatter, out, stem, manifest, period_label)
    chart_devices(a, plt, FuncFormatter, out, stem, manifest, period_label)
    chart_countries(a, plt, FuncFormatter, out, stem, manifest, period_label)

    write_manifest(a, manifest, out, stem, analysis_path, args.update_analysis)

    for entry in manifest.as_list():
        if entry["status"] == "drawn":
            print(entry["file"])
        else:
            print("skipped %-26s %s" % (entry["key"], entry["reason"]), file=sys.stderr)
    print("", file=sys.stderr)
    print("%d chart(s) drawn, %d skipped"
          % (manifest.drawn_count, len(manifest.as_list()) - manifest.drawn_count),
          file=sys.stderr)
    return 0 if manifest.drawn_count else 3


def write_manifest(a, manifest, out, stem, analysis_path, update_analysis):
    manifest_path = out / ("%s_charts.json" % stem)
    manifest_path.write_text(json.dumps({
        "schema": "reports-google-search-console/charts@1",
        "property": a["property"]["site_url"],
        "periods": a["periods"],
        "charts": manifest.as_list(),
    }, indent=2))
    if update_analysis:
        a["charts"] = manifest.as_list()
        analysis_path.write_text(json.dumps(a, indent=2))


if __name__ == "__main__":
    sys.exit(main())
