#!/usr/bin/env python3
"""
Draw the report's charts from an analysis file. Reads a file, writes PNGs, and
records what it drew (and what it could not) in a manifest.

    python3 make_charts.py --analysis <..._analysis.json> --out <dir>

Design rules this file follows, so the charts read as one system:

  * One measure per axis. Never two y-scales on one plot -- spend and
    conversions get two stacked panels sharing an x-axis, not a twin axis.
    A dual-axis chart lets the author imply a relationship by choosing the
    scales, which is exactly what an executive report must not do.
  * Colour carries the JOB, not the mark. Change charts are diverging
    (better / worse / ambiguous); magnitude charts are one hue; composition
    charts use the fixed categorical order and never a generated hue.
  * Better and worse are decided by the analysis, not by the sign. A CPA that
    fell is blue (better); spend that rose is grey (ambiguous), because spend
    has no direction without an objective.
  * Colour is never the only channel: every bar carries a direct label, the
    legend is always present with two or more series, and the report's own
    tables are the accessible fallback.
  * A chart whose data is unavailable is not drawn and is not faked. It is
    listed in the manifest with the reason, so the report can say so.

Palette: the validated default categorical/diverging set (blue #2a78d6, orange
#eb6834, aqua #1baf7a; diverging blue<->red #e34948 with a grey neutral). The
trio was run through the palette validator for all-pairs CVD separation before
being used here.

Exit codes: 0 charts drawn, 3 nothing could be drawn, 4 matplotlib missing.
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



class Charts(object):
    def __init__(self, analysis, out_dir, stem, plt, matplotlib, FuncFormatter):
        self.a = analysis
        self.out = Path(out_dir)
        self.out.mkdir(parents=True, exist_ok=True)
        self.stem = stem
        self.plt = plt
        self.mpl = matplotlib
        self.FuncFormatter = FuncFormatter
        self.manifest = []
        self.currency = analysis.get("account", {}).get("currency") or ""
        cur = analysis["periods"]["current"]
        prev = analysis["periods"]["previous"]
        self.period_label = "%s to %s vs %s to %s" % (
            cur["start"], cur["end"], prev["start"], prev["end"])
        self.current_label = "%s to %s" % (cur["start"], cur["end"])

    # -- helpers -----------------------------------------------------------

    def money_fmt(self):
        sym = {"USD": "$", "GBP": "£", "EUR": "€", "CAD": "C$", "AUD": "A$"}.get(self.currency, "")
        def f(x, _pos=None):
            if sym:
                return "%s%s" % (sym, "{:,.0f}".format(x))
            return "{:,.0f} {}".format(x, self.currency).strip()
        return self.FuncFormatter(f)

    def save(self, fig, name, title, alt, note=None):
        # Two files, one drawing. The SVG is what the HTML report inlines --
        # vector, selectable, set in the report's own Inter. The PNG is the
        # copy the Markdown version embeds. They are never drawn separately,
        # so they cannot disagree.
        path = self.out / ("%s_%s.png" % (self.stem, name))
        svg = save_twin(fig, path)
        self.plt.close(fig)
        self.manifest.append({
            "id": name,
            "file": str(path),
            "filename": path.name,
            "svg_file": svg,
            "svg_filename": Path(svg).name,
            "title": title,
            "alt": alt,
            "note": note,
            "status": "drawn",
        })
        return path

    def skip(self, name, title, reason):
        self.manifest.append({
            "id": name, "file": None, "title": title,
            "status": "not drawn", "reason": reason,
        })

    def suptitle(self, fig, title, subtitle, wrap=104):
        """Title block, measured in inches rather than figure fractions.

        Figure fractions mean a different physical offset on every chart height,
        which is how a title ends up sitting on top of its own subtitle."""
        import textwrap
        lines = textwrap.wrap(subtitle, wrap) if subtitle else []
        h = fig.get_size_inches()[1]
        fig.text(0.012, 1 - 0.20 / h, title, ha="left", va="top",
                 fontsize=13.5, fontweight="semibold", color=INK)
        for i, line in enumerate(lines):
            fig.text(0.012, 1 - (0.46 + 0.155 * i) / h, line, ha="left", va="top",
                     fontsize=9.5, color=INK_2)
        reserve = 0.55 + 0.16 * len(lines)
        fig.subplots_adjust(top=1 - reserve / h)

    def legend_below(self, fig, handles, labels, ncol):
        """Legends live under the plot, in reserved space -- never floating over
        the marks and never clipped."""
        h = fig.get_size_inches()[1]
        fig.subplots_adjust(bottom=fig.subplotpars.bottom + 0.42 / h)
        fig.legend(handles, labels, loc="lower left", bbox_to_anchor=(0.012, 0.005),
                   ncol=ncol, frameon=False, fontsize=9)

    # -- 1. KPI change ------------------------------------------------------

    def kpi_change(self):
        kpis = [k for k in self.a["kpis"]
                if k.get("availability") == "available"
                and k.get("percent_change") is not None]
        if len(kpis) < 3:
            self.skip("kpi-change", "Period-over-period change by KPI",
                      "Fewer than three KPIs have a comparable figure in both periods.")
            return
        kpis = list(reversed(kpis))
        labels, values, colors = [], [], []
        for k in kpis:
            suffix = {"improved": " (better)", "declined": " (worse)"}.get(k["verdict"], "")
            labels.append(k["label"] + suffix)
            values.append(k["percent_change"])
            colors.append(VERDICT_COLOR.get(k["verdict"], NEUTRAL))

        fig, ax = self.plt.subplots(figsize=(8.6, 0.42 * len(kpis) + 1.9))
        bars = ax.barh(labels, values, color=colors, height=0.52, zorder=3)
        ax.axvline(0, color=AXIS, linewidth=1.0, zorder=4)
        ax.grid(axis="y", visible=False)
        ax.set_xlabel("Change vs previous period (%)")
        lo, hi = min(values + [0]), max(values + [0])
        span = max(abs(lo), abs(hi)) or 1
        pad = span * 0.22
        ax.set_xlim(lo - pad if lo < 0 else -span * 0.06, hi + pad if hi > 0 else span * 0.06)

        for bar, v in zip(bars, values):
            offset = span * 0.025
            ax.text(v + (offset if v >= 0 else -offset), bar.get_y() + bar.get_height() / 2,
                    "%+.1f%%" % v, va="center", ha="left" if v >= 0 else "right",
                    fontsize=9, color=INK_2)

        used = {k["verdict"] for k in kpis}
        legend_spec = [("improved", "Improved"), ("declined", "Declined"),
                       ("ambiguous", "Directionally ambiguous"),
                       ("flat", "Below materiality threshold"), ("new", "No baseline")]
        handles = [self.mpl.patches.Patch(color=VERDICT_COLOR[k], label=lbl)
                   for k, lbl in legend_spec if k in used]
        finish(ax)
        self.suptitle(fig, "Period-over-period change by KPI",
                      "%s. Colour shows whether the move is good for the account, not "
                      "whether the number went up." % self.period_label)
        self.legend_below(fig, handles, [h.get_label() for h in handles], min(len(handles), 4))
        self.save(fig, "kpi-change", "Period-over-period change by KPI",
                  "Horizontal bar chart of percentage change for each KPI, coloured blue "
                  "where the change is an improvement, red where it is a decline, and grey "
                  "where direction alone does not say.")

    # -- 2. daily trend -----------------------------------------------------

    def daily_trend(self):
        daily = [d for d in self.a.get("trend", {}).get("daily", []) if d.get("date")]
        if len(daily) < 14:
            self.skip("daily-trend", "Daily spend and conversions",
                      "Fewer than 14 days of daily rows were returned.")
            return
        import datetime as dt
        dates = [dt.date.fromisoformat(d["date"]) for d in daily]
        spend = [d.get("cost") for d in daily]
        conv = [d.get("conversions") for d in daily]
        boundary = self.a["periods"]["current"]["start"]
        bdate = dt.date.fromisoformat(boundary)

        have_conv = any(c is not None for c in conv)
        rows = 2 if have_conv else 1
        fig, axes = self.plt.subplots(rows, 1, figsize=(9.4, 3.0 * rows + 1.2), sharex=True)
        axes = axes if rows > 1 else [axes]

        panels = [("Spend", spend, self.money_fmt())]
        if have_conv:
            panels.append(("Conversions", conv, None))

        for ax, (label, series, formatter) in zip(axes, panels):
            ax.plot(dates, series, color=BLUE, linewidth=1.8, zorder=3)
            ax.fill_between(dates, series, color=BLUE, alpha=0.07, zorder=2)
            ax.axvline(bdate, color=AXIS, linewidth=1.0, zorder=4)
            ax.set_ylabel(label)
            ax.set_ylim(bottom=0)
            if formatter:
                ax.yaxis.set_major_formatter(formatter)
            ax.grid(axis="x", visible=False)
            finish(ax)

        top = axes[0]
        ymax = top.get_ylim()[1]
        gap = dt.timedelta(days=1)
        top.text(bdate + gap, ymax * 0.98, "current period", fontsize=8.5, color=MUTED,
                 va="top", ha="left")
        top.text(bdate - gap, ymax * 0.98, "previous period", fontsize=8.5, color=MUTED,
                 va="top", ha="right")

        axes[-1].set_xlabel("Date (account time zone: %s)"
                            % (self.a["periods"].get("time_zone") or "unknown"))
        fig.autofmt_xdate(rotation=0, ha="center")
        self.suptitle(fig, "Daily spend and conversions",
                      "%s. Two panels, one measure each -- deliberately not a shared axis, "
                      "which would let the scales imply a relationship." % self.period_label)
        fig.subplots_adjust(hspace=0.18)
        self.save(fig, "daily-trend", "Daily spend and conversions",
                  "Two stacked line charts sharing a date axis: daily spend above, daily "
                  "conversions below, with a vertical rule marking where the previous "
                  "period ends and the current period begins.")

    # -- 3. campaign spend and conversions ----------------------------------

    def campaign_spend_conversions(self, top_n=8):
        camps = [c for c in self.a.get("campaigns", [])
                 if (c.get("current") or {}).get("cost")]
        if len(camps) < 2:
            self.skip("campaign-spend-conversions", "Spend and conversions by campaign",
                      "Fewer than two campaigns recorded spend in the current period.")
            return
        camps = camps[:top_n]
        names = [shorten(c["name"]) for c in camps][::-1]
        spend = [(c["current"] or {}).get("cost") or 0 for c in camps][::-1]
        conv = [(c["current"] or {}).get("conversions") for c in camps][::-1]
        have_conv = any(c is not None for c in conv)

        cols = 2 if have_conv else 1
        fig, axes = self.plt.subplots(1, cols, figsize=(5.2 * cols + 1.6, 0.46 * len(camps) + 2.1),
                                      sharey=True)
        axes = axes if cols > 1 else [axes]

        axes[0].barh(names, spend, color=BLUE, height=0.52, zorder=3)
        axes[0].set_xlabel("Spend")
        axes[0].xaxis.set_major_formatter(self.money_fmt())
        for i, v in enumerate(spend):
            axes[0].text(v, i, "  " + fmt_money(v, self.currency), va="center", fontsize=8.5, color=INK_2)
        axes[0].set_xlim(0, max(spend) * 1.28)

        if have_conv:
            vals = [c or 0 for c in conv]
            axes[1].barh(names, vals, color=BLUE_DARK, height=0.52, zorder=3)
            axes[1].set_xlabel("Conversions")
            for i, (v, raw) in enumerate(zip(vals, conv)):
                axes[1].text(v, i, "  " + ("{:,.0f}".format(v) if raw is not None else "n/a"),
                             va="center", fontsize=8.5, color=INK_2)
            axes[1].set_xlim(0, (max(vals) or 1) * 1.28)

        for ax in axes:
            ax.grid(axis="y", visible=False)
            finish(ax)

        self.suptitle(fig, "Spend and conversions by campaign",
                      "Current period, %s. Same campaign order in both panels; the gap "
                      "between them is the point." % self.current_label)
        fig.subplots_adjust(wspace=0.08)
        self.save(fig, "campaign-spend-conversions", "Spend and conversions by campaign",
                  "Two horizontal bar charts side by side sharing campaign labels: spend on "
                  "the left, conversions on the right, campaigns ordered by spend.")

    # -- 4. CPA / ROAS movement --------------------------------------------

    def efficiency_dumbbell(self, top_n=8):
        camps = [c for c in self.a.get("campaigns", [])
                 if (c.get("current") or {}).get("cost_per_conversion") is not None
                 and (c.get("previous") or {}).get("cost_per_conversion") is not None]
        metric, label, is_money = "cost_per_conversion", "CPA", True
        better_low = True
        if len(camps) < 2:
            camps = [c for c in self.a.get("campaigns", [])
                     if (c.get("current") or {}).get("roas") is not None
                     and (c.get("previous") or {}).get("roas") is not None]
            metric, label, is_money, better_low = "roas", "ROAS", False, False
        if len(camps) < 2:
            self.skip("campaign-efficiency", "Campaign efficiency, previous vs current",
                      "Fewer than two campaigns have a comparable CPA or ROAS in both periods.")
            return
        camps = camps[:top_n][::-1]

        names = [shorten(c["name"]) for c in camps]
        prev = [(c["previous"] or {})[metric] for c in camps]
        cur = [(c["current"] or {})[metric] for c in camps]

        fig, ax = self.plt.subplots(figsize=(8.8, 0.44 * len(camps) + 2.0))
        for i, (p, c) in enumerate(zip(prev, cur)):
            ax.plot([p, c], [i, i], color=AXIS, linewidth=1.6, zorder=2, solid_capstyle="round")
        ax.scatter(prev, range(len(camps)), s=64, color=BLUE_LIGHT, zorder=3,
                   edgecolors=SURFACE, linewidths=2, label="Previous period")
        ax.scatter(cur, range(len(camps)), s=64, color=BLUE_DARK, zorder=4,
                   edgecolors=SURFACE, linewidths=2, label="Current period")
        ax.set_yticks(range(len(camps)))
        ax.set_yticklabels(names)
        ax.grid(axis="y", visible=False)
        if is_money:
            ax.xaxis.set_major_formatter(self.money_fmt())
        ax.set_xlabel("%s (%s is better)" % (label, "lower" if better_low else "higher"))

        span = max(max(prev), max(cur)) or 1
        ax.set_xlim(0, span * 1.32)
        dp = 2 if span < 100 else 0
        for i, (p_val, c_val) in enumerate(zip(prev, cur)):
            # anchor past whichever dot is further right, so the label never lands
            # on the other end of its own dumbbell
            txt = (fmt_money(c_val, self.currency, dp) if is_money
                   else "{:,.2f}".format(c_val))
            ax.text(max(p_val, c_val) + span * 0.035, i, txt,
                    va="center", fontsize=8.5, color=INK_2)
        finish(ax)
        self.suptitle(fig, "Campaign %s, previous vs current period" % label,
                      "%s. Each line is one campaign moving between periods." % self.period_label)
        handles, labels = ax.get_legend_handles_labels()
        self.legend_below(fig, handles, labels, 2)
        self.save(fig, "campaign-efficiency", "Campaign %s, previous vs current period" % label,
                  "Dumbbell chart: for each campaign, a light dot for the previous period's "
                  "%s and a dark dot for the current period's, joined by a line." % label)

    # -- 5. impression share ------------------------------------------------

    def impression_share(self, top_n=8):
        camps = []
        for c in self.a.get("campaigns", []):
            share = c.get("impression_share") or {}
            if share.get("search_impression_share") is None:
                continue
            camps.append(c)
        if not camps:
            self.skip("impression-share", "Where search impressions went",
                      "No campaign reported search impression share. Campaign types such as "
                      "Performance Max, Display and Video do not report it.")
            return
        camps = camps[:top_n][::-1]

        names = [shorten(c["name"]) for c in camps]
        won = [c["impression_share"]["search_impression_share"] or 0 for c in camps]
        budget = [c["impression_share"].get("search_lost_is_budget") or 0 for c in camps]
        rank = [c["impression_share"].get("search_lost_is_rank") or 0 for c in camps]
        other = [max(0.0, 100 - (w + b + r)) for w, b, r in zip(won, budget, rank)]

        fig, ax = self.plt.subplots(figsize=(9.0, 0.5 * len(camps) + 2.3))
        left = [0.0] * len(camps)
        series = [("Impressions won", won, BLUE),
                  ("Lost to budget", budget, ORANGE),
                  ("Lost to ad rank", rank, AQUA),
                  ("Unaccounted", other, GRID)]
        for label, values, color in series:
            ax.barh(names, values, left=left, color=color, height=0.5, zorder=3,
                    edgecolor=SURFACE, linewidth=2)
            for i, (v, l0) in enumerate(zip(values, left)):
                if v >= 12:
                    ax.text(l0 + v / 2, i, "%.0f%%" % v, va="center", ha="center",
                            fontsize=8.5, color=SURFACE if color != GRID else INK_2)
            left = [l + v for l, v in zip(left, values)]

        ax.set_xlim(0, 100)
        ax.set_xlabel("Share of available search impressions (%)")
        ax.grid(axis="y", visible=False)
        finish(ax)
        self.suptitle(fig, "Where search impressions went",
                      "Current period, %s. Search campaigns only -- campaign types that do "
                      "not report impression share are absent from this chart, not zero."
                      % self.current_label)
        handles = [self.mpl.patches.Patch(color=s[2], label=s[0]) for s in series]
        self.legend_below(fig, handles, [s[0] for s in series], 4)
        self.save(fig, "impression-share", "Where search impressions went",
                  "Stacked horizontal bars, one per search campaign, splitting available "
                  "impressions into won, lost to budget, lost to ad rank, and unaccounted.",
                  note="Segments are shares of available impressions and sum to 100% by "
                       "definition; 'unaccounted' is the residual Google does not attribute.")

    # -- 6. mix by device ---------------------------------------------------

    def device_mix(self):
        rows = (self.a.get("segments") or {}).get("device")
        if not rows or len(rows) < 2:
            self.skip("device-mix", "Spend mix by device",
                      "Device segmentation was not retrieved for this run.")
            return
        rows = [r for r in rows if (r.get("current") or {}).get("cost")][:6]
        if len(rows) < 2:
            self.skip("device-mix", "Spend mix by device", "Only one device recorded spend.")
            return

        labels = [(r["label"] or "").replace("_", " ").title() for r in rows]
        cur = [r.get("spend_share_current") or 0 for r in rows]
        prev = [r.get("spend_share_previous") or 0 for r in rows]
        colors = [BLUE, ORANGE, AQUA, "#eda100", "#e87ba4", "#4a3aa7"][:len(rows)]

        fig, ax = self.plt.subplots(figsize=(9.0, 2.9))
        for row_i, (values, name) in enumerate(((prev, "Previous"), (cur, "Current"))):
            left = 0.0
            for value, color, label in zip(values, colors, labels):
                ax.barh([name], [value], left=[left], color=color, height=0.46,
                        zorder=3, edgecolor=SURFACE, linewidth=2)
                if value >= 10:
                    ax.text(left + value / 2, row_i, "%s %.0f%%" % (label, value),
                            va="center", ha="center", fontsize=8.5, color=SURFACE)
                left += value
        ax.set_xlim(0, 100)
        ax.set_xlabel("Share of spend (%)")
        ax.grid(axis="y", visible=False)
        handles = [self.mpl.patches.Patch(color=c, label=l) for c, l in zip(colors, labels)]
        finish(ax)
        self.suptitle(fig, "Spend mix by device",
                      "%s. Shares of spend, not absolute spend -- a segment can gain share "
                      "while spending less." % self.period_label)
        self.legend_below(fig, handles, labels, min(len(labels), 4))
        self.save(fig, "device-mix", "Spend mix by device",
                  "Two stacked horizontal bars comparing each device's share of spend in the "
                  "previous and current periods.")


def shorten(name, limit=32):
    name = name or "(unnamed)"
    return name if len(name) <= limit else name[:limit - 1].rstrip() + "…"


def fmt_money(v, currency, dp=0):
    sym = {"USD": "$", "GBP": "£", "EUR": "€", "CAD": "C$", "AUD": "A$"}.get(currency, "")
    body = "{:,.{dp}f}".format(v, dp=dp)
    if sym:
        return "%s%s" % (sym, body)
    return ("%s %s" % (body, currency)).strip()


def main():
    ap = argparse.ArgumentParser(description="Draw charts from a Google Ads analysis file.")
    ap.add_argument("--analysis", required=True)
    ap.add_argument("--out", help="Directory for PNGs (default: <analysis dir>/charts)")
    ap.add_argument("--update-analysis", action="store_true",
                    help="Write the chart manifest back into the analysis file")
    ap.add_argument("--top-n", type=int, default=8, help="Campaigns per campaign chart (default 8)")
    args = ap.parse_args()

    a_path = Path(args.analysis).expanduser()
    if not a_path.is_file():
        print("No such analysis file: %s" % a_path, file=sys.stderr)
        return 2
    analysis = json.loads(a_path.read_text(encoding="utf-8"))

    matplotlib, plt, FuncFormatter = load_matplotlib()
    out_dir = Path(args.out).expanduser() if args.out else a_path.parent / "charts"
    stem = a_path.name.replace("_analysis.json", "")

    if plt is None:
        manifest = [{
            "id": "all", "file": None, "status": "not drawn",
            "reason": "matplotlib is not installed on this machine, so no charts were "
                      "generated. Install it with `python3 -m pip install matplotlib`, or "
                      "write the report without charts and say in the report that the "
                      "visuals are unavailable -- do not describe charts that do not exist.",
        }]
        out_dir.mkdir(parents=True, exist_ok=True)
        (out_dir / ("%s_charts.json" % stem)).write_text(json.dumps(manifest, indent=2))
        print(json.dumps({"status": "unavailable", "charts": manifest}, indent=2))
        return 4

    style(plt, matplotlib)
    charts = Charts(analysis, out_dir, stem, plt, matplotlib, FuncFormatter)
    charts.kpi_change()
    charts.daily_trend()
    charts.campaign_spend_conversions(top_n=args.top_n)
    charts.efficiency_dumbbell(top_n=args.top_n)
    charts.impression_share(top_n=args.top_n)
    charts.device_mix()

    manifest_path = out_dir / ("%s_charts.json" % stem)
    manifest_path.write_text(json.dumps(charts.manifest, indent=2), encoding="utf-8")

    if args.update_analysis:
        analysis["charts"] = charts.manifest
        a_path.write_text(json.dumps(analysis, indent=2), encoding="utf-8")

    drawn = [c for c in charts.manifest if c["status"] == "drawn"]
    print(json.dumps({
        "status": "ok" if drawn else "nothing drawn",
        "drawn": len(drawn),
        "skipped": [{"id": c["id"], "reason": c.get("reason")}
                    for c in charts.manifest if c["status"] != "drawn"],
        "manifest": str(manifest_path),
        "files": [c["file"] for c in drawn],
    }, indent=2))
    return 0 if drawn else 3


if __name__ == "__main__":
    sys.exit(main())
