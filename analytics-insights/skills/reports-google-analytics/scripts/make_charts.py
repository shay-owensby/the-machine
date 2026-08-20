#!/usr/bin/env python3
"""
Draw the report's charts from an analysis file. Reads a file, writes PNGs, and
records what it drew -- and what it could not -- in a manifest.

    python3 make_charts.py --analysis <data/analysis.json>

Design rules this file follows, so the charts read as one system:

  * One measure per axis. Never two y-scales on one plot -- sessions and
    revenue get two stacked panels sharing an x-axis, not a twin axis. A
    dual-axis chart lets the author imply a relationship by choosing the
    scales, which is exactly what an executive report must not do.
  * Colour carries the JOB, not the mark. Change charts are diverging
    (better / worse / ambiguous); comparison charts use one hue for the current
    period and a muted one for the previous.
  * Better and worse are decided by the ANALYSIS, not by the sign. Event count
    rising is grey (ambiguous), because event count has no direction without
    context.
  * Colour is never the only channel: bars carry direct labels, legends are
    present wherever two series are, and the report's tables are the accessible
    fallback.
  * A chart whose data is unavailable is not drawn and is not faked. It is
    listed in the manifest with the reason, so the report can say so instead of
    describing a picture that does not exist.

Colour, type, spacing and the chart theme are NOT defined in this file. They
come from the plugin design system -- see design/DESIGN.md, with the values in
design/lib/tokens.py -- and are imported below from design/lib/charts.py.
Contrast and all-pairs colour-vision separation are measured there rather than
asserted here: run `python3 design/lib/tokens.py` to re-derive every figure.

Exit codes: 0 charts drawn, 2 bad input, 3 nothing could be drawn, 4 matplotlib missing.
"""

import argparse
import json
import sys
import textwrap
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

HEADLINE_KPIS = ["sessions", "activeUsers", "engagedSessions", "engagementRate",
                 "screenPageViews", "keyEvents", "sessionKeyEventRate",
                 "totalRevenue", "transactions"]




def shorten(name, limit=34):
    name = str(name or "")
    if len(name) <= limit:
        return name
    return name[:limit - 1] + "…"


class Charts(object):
    def __init__(self, analysis, out_dir, plt, matplotlib, FuncFormatter, report_dir=None):
        self.a = analysis
        self.out = Path(out_dir)
        self.out.mkdir(parents=True, exist_ok=True)
        self.report_dir = Path(report_dir) if report_dir else self.out.parent
        self.plt = plt
        self.mpl = matplotlib
        self.FuncFormatter = FuncFormatter
        self.manifest = []
        self.currency = (analysis.get("property") or {}).get("currency") or ""
        cur = analysis["periods"]["current"]
        prev = analysis["periods"]["previous"]
        self.current_label = "%s to %s" % (cur["start"], cur["end"])
        self.previous_label = "%s to %s" % (prev["start"], prev["end"])
        self.period_label = "%s vs %s" % (self.current_label, self.previous_label)
        self.kpis = {k["key"]: k for k in analysis.get("kpis", [])}
        self.sections = analysis.get("sections") or {}
        self.ke_available = self.kpis.get("keyEvents", {}).get("availability") != "unavailable"
        self.ecommerce = analysis.get("ecommerce_state") == "active"

    # -- helpers -----------------------------------------------------------

    def money_fmt(self):
        sym = {"USD": "$", "GBP": "£", "EUR": "€", "CAD": "C$", "AUD": "A$",
               "NZD": "NZ$", "JPY": "¥"}.get(self.currency, "")

        def f(x, _pos=None):
            if abs(x) >= 1000:
                return "%s%s" % (sym, "{:,.0f}".format(x))
            return "%s%s" % (sym, "{:,.0f}".format(x)) if sym else \
                "{:,.0f} {}".format(x, self.currency).strip()
        return self.FuncFormatter(f)

    def count_fmt(self):
        def f(x, _pos=None):
            if abs(x) >= 1000000:
                return "{:,.1f}M".format(x / 1000000.0)
            if abs(x) >= 1000:
                return "{:,.0f}k".format(x / 1000.0)
            return "{:,.0f}".format(x)
        return self.FuncFormatter(f)

    def save(self, fig, name, title, alt, note=None):
        # Two files, one drawing: the SVG the HTML report inlines and the PNG
        # the Markdown copy embeds. See design/DESIGN.md.
        path = self.out / ("%s.png" % name)
        svg = save_twin(fig, path)
        self.plt.close(fig)
        try:
            rel = path.relative_to(self.report_dir)
            rel_str = "./%s" % rel.as_posix()
        except ValueError:
            rel_str = str(path)
        self.manifest.append({
            "id": name,
            "file": str(path),
            "filename": path.name,
            "svg_file": svg,
            "svg_filename": Path(svg).name,
            "relative_path": rel_str,
            "markdown": "![%s](%s)" % (title, rel_str),
            "title": title,
            "alt": alt,
            "note": note,
            "status": "drawn",
        })
        return path

    def skip(self, name, title, reason):
        self.manifest.append({"id": name, "file": None, "title": title,
                              "status": "not drawn", "reason": reason})

    def suptitle(self, fig, title, subtitle, wrap=104):
        """Title block measured in inches, not figure fractions.

        Figure fractions mean a different physical offset on every chart
        height, which is how a title ends up sitting on its own subtitle.
        """
        lines = textwrap.wrap(subtitle, wrap) if subtitle else []
        h = fig.get_size_inches()[1]
        fig.text(0.012, 1 - 0.20 / h, title, ha="left", va="top",
                 fontsize=13.5, fontweight="semibold", color=INK)
        for i, line in enumerate(lines):
            fig.text(0.012, 1 - (0.46 + 0.155 * i) / h, line, ha="left", va="top",
                     fontsize=9.5, color=INK_2)
        reserve = 0.55 + 0.16 * len(lines)
        fig.subplots_adjust(top=1 - reserve / h)

    def legend_below(self, fig, handles, labels, ncol=2):
        h = fig.get_size_inches()[1]
        fig.subplots_adjust(bottom=fig.subplotpars.bottom + 0.42 / h)
        fig.legend(handles, labels, loc="lower left", bbox_to_anchor=(0.012, 0.005),
                   ncol=ncol, frameon=False, fontsize=9)

    def rows_with(self, rows, metric, limit, require_previous=False):
        """Rows that actually carry the metric. Absent is dropped, not zeroed."""
        out = []
        for r in rows or []:
            cur = (r.get("current") or {}).get(metric)
            prev = (r.get("previous") or {}).get(metric)
            if cur is None and prev is None:
                continue
            if require_previous and prev is None:
                prev = None
            out.append((r["key"], cur, prev))
        return out[:limit]

    # -- 1. KPI change ------------------------------------------------------

    def kpi_change(self):
        recs = [self.kpis[k] for k in HEADLINE_KPIS
                if k in self.kpis
                and self.kpis[k].get("availability") == "available"
                and self.kpis[k].get("percent_change") is not None]
        if len(recs) < 3:
            self.skip("kpi-change", "Period-over-period change by KPI",
                      "Fewer than three headline KPIs have a comparable figure in both "
                      "periods.")
            return
        recs = list(reversed(recs))
        labels, values, colors = [], [], []
        for k in recs:
            suffix = {"improved": " (better)", "declined": " (worse)"}.get(k["verdict"], "")
            labels.append(k["label"] + suffix)
            values.append(k["percent_change"])
            colors.append(VERDICT_COLOR.get(k["verdict"], NEUTRAL))

        fig, ax = self.plt.subplots(figsize=(8.6, 0.44 * len(recs) + 1.9))
        ax.barh(labels, values, color=colors, height=0.54, zorder=3)
        ax.axvline(0, color=AXIS, linewidth=1.0, zorder=4)
        ax.grid(axis="y", visible=False)
        ax.set_xlabel("Change vs previous period (%)")
        lo, hi = min(values + [0]), max(values + [0])
        pad = max(abs(lo), abs(hi)) * 0.30 + 2
        ax.set_xlim(lo - pad, hi + pad)
        for y, v in enumerate(values):
            ax.text(v + (pad * 0.10 if v >= 0 else -pad * 0.10), y,
                    "%s%.1f%%" % ("+" if v > 0 else "", v),
                    va="center", ha="left" if v >= 0 else "right",
                    fontsize=9, color=INK_2)
        finish(ax)
        self.suptitle(fig, "Period-over-period change by KPI",
                      "%s. Blue is a favourable move, red unfavourable, grey a metric whose "
                      "direction is not good or bad on its own." % self.period_label)
        return self.save(
            fig, "kpi-change", "Period-over-period change by KPI",
            "Horizontal bar chart of percentage change for each headline KPI between %s and "
            "%s, coloured by whether the analysis judged the move favourable."
            % (self.current_label, self.previous_label))

    # -- 2. Daily performance ----------------------------------------------

    def daily_performance(self):
        trends = self.sections.get("trends") or {}
        series = trends.get("current") or []
        if len(series) < 7:
            self.skip("daily-performance", "Daily performance",
                      "Fewer than seven days of daily data were returned.")
            return

        panels = [("sessions", "Sessions", BLUE, "count")]
        if self.ke_available and any((d["values"] or {}).get("keyEvents") is not None
                                     for d in series):
            panels.append(("keyEvents", "Key events", AQUA, "count"))
        if self.ecommerce and any((d["values"] or {}).get("totalRevenue") is not None
                                  for d in series):
            panels.append(("totalRevenue", "Revenue", ORANGE, "money"))

        prev_series = trends.get("previous") or []
        dates = [d["date"] for d in series]
        rows = len(panels)
        fig, axes = self.plt.subplots(rows, 1, figsize=(9.6, 2.5 * rows + 1.4), sharex=True)
        if rows == 1:
            axes = [axes]

        drew_previous = False
        for ax, (metric, label, color, kind) in zip(axes, panels):
            ys = [(d["values"] or {}).get(metric) for d in series]
            xs = list(range(len(series)))
            # Gaps stay gaps: a day with no data breaks the line rather than
            # being drawn at zero.
            ax.plot(xs, [y if y is not None else float("nan") for y in ys],
                    color=color, linewidth=2.0, zorder=3, label="%s (current)" % label)
            for x, y in zip(xs, ys):
                if y is None:
                    ax.axvspan(x - 0.5, x + 0.5, color=RED, alpha=0.08, zorder=1)

            if len(prev_series) == len(series):
                prev_ys = [(d["values"] or {}).get(metric) for d in prev_series]
                if any(v is not None for v in prev_ys):
                    ax.plot(xs, [y if y is not None else float("nan") for y in prev_ys],
                            color=PREVIOUS, linewidth=1.4, linestyle="--", zorder=2,
                            label="%s (previous period, aligned by day)" % label)
                    drew_previous = True

            ax.set_ylabel(label)
            ax.set_ylim(bottom=0)
            ax.yaxis.set_major_formatter(self.money_fmt() if kind == "money" else self.count_fmt())
            finish(ax)

        step = max(1, len(dates) // 10)
        axes[-1].set_xticks(list(range(0, len(dates), step)))
        axes[-1].set_xticklabels([dates[i][5:] for i in range(0, len(dates), step)])
        axes[-1].set_xlabel("Date (current period, %s)" % self.current_label)

        note = "One measure per panel, each on its own scale. "
        if drew_previous:
            note += ("Solid coloured line is the current period; dashed grey is the previous "
                     "period aligned day-for-day. ")
        missing = trends.get("missing_days_current") or []
        if missing:
            note += "Shaded columns are days GA4 returned no data for."
        self.suptitle(fig, "Daily performance", note)
        return self.save(
            fig, "daily-performance", "Daily performance",
            "Stacked line panels of %s by day across %s, each panel on its own scale, with "
            "the previous period shown as a dashed line where available."
            % (", ".join(p[1].lower() for p in panels), self.current_label),
            note="Days with no data are shaded rather than plotted as zero."
            if missing else None)

    # -- 3. Channel performance --------------------------------------------

    def channel_performance(self, top_n=8):
        rows = (self.sections.get("acquisition") or {}).get("session_channels")
        data = self.rows_with(rows, "sessions", top_n)
        if len(data) < 2:
            self.skip("channel-performance", "Sessions by acquisition channel",
                      "The session channel breakdown was not available.")
            return
        return self._grouped_bars(
            data, "channel-performance", "Sessions by acquisition channel",
            "Sessions", "count",
            "Session-scoped channel: where each VISIT came from, not where the person was "
            "originally acquired. %s." % self.period_label,
            "Grouped horizontal bars comparing sessions per acquisition channel between the "
            "current and previous periods.")

    # -- 4. Landing pages ---------------------------------------------------

    def landing_pages(self, top_n=10):
        rows = (self.sections.get("content") or {}).get("landing_pages")
        data = self.rows_with(rows, "sessions", top_n)
        if len(data) < 2:
            self.skip("landing-page-performance", "Sessions by landing page",
                      "The landing-page breakdown was not available.")
            return
        return self._grouped_bars(
            data, "landing-page-performance", "Sessions by landing page",
            "Entrances (sessions)", "count",
            "Top entry pages by sessions. %s." % self.period_label,
            "Grouped horizontal bars comparing entrances per landing page between the "
            "current and previous periods.")

    # -- 5. Key events ------------------------------------------------------

    def key_events(self, top_n=8):
        events = ((self.sections.get("events") or {}) or {}).get("events") or []
        key_rows = [e for e in events if e.get("is_key_event")]
        if not key_rows:
            self.skip("key-event-performance", "Key events by event name",
                      "No event in this property is marked as a key event, or the event "
                      "breakdown was not retrieved.")
            return
        data = []
        for e in key_rows[:top_n]:
            cur = (e.get("current") or {}).get("keyEvents")
            if cur is None:
                cur = (e.get("current") or {}).get("eventCount")
            prev = (e.get("previous") or {}).get("keyEvents")
            if prev is None:
                prev = (e.get("previous") or {}).get("eventCount")
            if cur is None and prev is None:
                continue
            data.append((e["event_name"], cur, prev))
        if not data:
            self.skip("key-event-performance", "Key events by event name",
                      "Key events are defined but no volume was returned for them.")
            return
        return self._grouped_bars(
            data, "key-event-performance", "Key events by event name",
            "Key events", "count",
            "What each key event represents for the business is a property configuration "
            "question, not one GA4 answers. %s." % self.period_label,
            "Grouped horizontal bars comparing key-event volume per event name between the "
            "current and previous periods.")

    # -- 6. Devices ---------------------------------------------------------

    def devices(self):
        rows = (self.sections.get("devices") or {}).get("device_categories")
        data = self.rows_with(rows, "sessions", 6)
        if len(data) < 2:
            self.skip("device-performance", "Performance by device category",
                      "The device breakdown was not available.")
            return

        show_rate = self.ke_available and any(
            (r.get("current") or {}).get("sessionKeyEventRate") is not None
            or ((r.get("current") or {}).get("keyEvents") is not None
                and (r.get("current") or {}).get("sessions"))
            for r in rows)

        cols = 2 if show_rate else 1
        fig, axes = self.plt.subplots(1, cols, figsize=(5.4 * cols + 1.4,
                                                       0.62 * len(data) + 2.4))
        axes = [axes] if cols == 1 else list(axes)

        labels = [d[0].title() for d in data][::-1]
        cur = [d[1] for d in data][::-1]
        prev = [d[2] for d in data][::-1]
        ys = range(len(labels))
        ax = axes[0]
        ax.barh([y + 0.19 for y in ys], cur, height=0.36, color=BLUE, zorder=3)
        ax.barh([y - 0.19 for y in ys], [p if p is not None else 0 for p in prev],
                height=0.36, color=PREVIOUS, zorder=3)
        ax.set_yticks(list(ys))
        ax.set_yticklabels(labels)
        ax.set_xlabel("Sessions")
        ax.xaxis.set_major_formatter(self.count_fmt())
        ax.grid(axis="y", visible=False)
        finish(ax)

        if show_rate:
            by_key = {r["key"].lower(): r for r in rows}
            rates = []
            for label in labels:
                r = by_key.get(label.lower(), {})
                c = r.get("current") or {}
                v = c.get("sessionKeyEventRate")
                if v is None and c.get("keyEvents") is not None and c.get("sessions"):
                    v = c["keyEvents"] / c["sessions"] * 100
                rates.append(v)
            ax2 = axes[1]
            drawn = [(y, v) for y, v in zip(ys, rates) if v is not None]
            ax2.barh([y for y, _ in drawn], [v for _, v in drawn], height=0.5,
                     color=AQUA, zorder=3)
            ax2.set_yticks(list(ys))
            ax2.set_yticklabels(["" for _ in labels])
            ax2.set_xlabel("Session key event rate, current period (%)")
            ax2.grid(axis="y", visible=False)
            span = max([v for _, v in drawn] + [1])
            for y, v in drawn:
                ax2.text(v + span * 0.03, y, "%.1f%%" % v, va="center", fontsize=9,
                         color=INK_2)
            ax2.set_xlim(0, span * 1.25)
            finish(ax2)

        self.suptitle(fig, "Performance by device category",
                      "Volume on the left for both periods, current-period conversion rate on "
                      "the right: the device with the most sessions is often not the one that "
                      "converts. %s." % self.period_label)
        handles = [self.plt.Rectangle((0, 0), 1, 1, color=BLUE),
                   self.plt.Rectangle((0, 0), 1, 1, color=PREVIOUS)]
        self.legend_below(fig, handles, ["Current period", "Previous period"], ncol=2)
        return self.save(
            fig, "device-performance", "Performance by device category",
            "Bar chart of sessions per device category for both periods%s."
            % (", beside the session key event rate for each" if show_rate else ""))

    # -- 7. Ecommerce -------------------------------------------------------

    def ecommerce_performance(self, top_n=8):
        if not self.ecommerce:
            self.skip("ecommerce-performance", "Revenue by acquisition channel",
                      "This property returned no purchase activity, so no ecommerce chart is "
                      "drawn.")
            return
        ecom = self.sections.get("ecommerce") or {}
        data = self.rows_with(ecom.get("revenue_by_channel"), "totalRevenue", top_n)
        if len(data) < 2:
            self.skip("ecommerce-performance", "Revenue by acquisition channel",
                      "Revenue by channel was not available.")
            return
        return self._grouped_bars(
            data, "ecommerce-performance", "Revenue by acquisition channel",
            "Revenue (%s)" % (self.currency or "reporting currency"), "money",
            "GA4's own attribution, which will not tie exactly to a payment processor. %s."
            % self.period_label,
            "Grouped horizontal bars comparing revenue per acquisition channel between the "
            "current and previous periods.")

    def ecommerce_funnel(self):
        if not self.ecommerce:
            return
        ecom = self.sections.get("ecommerce") or {}
        funnel = [s for s in (ecom.get("funnel") or []) if s.get("current") is not None]
        if len(funnel) < 3:
            self.skip("ecommerce-funnel", "Item funnel",
                      "Fewer than three funnel steps returned data.")
            return
        labels = [s["label"] for s in funnel]
        cur = [s["current"] for s in funnel]
        prev = [s["previous"] if s["previous"] is not None else 0 for s in funnel]

        fig, ax = self.plt.subplots(figsize=(8.8, 0.66 * len(funnel) + 2.4))
        ys = list(range(len(labels)))[::-1]
        ax.barh([y + 0.19 for y in ys], cur, height=0.36, color=ORANGE, zorder=3)
        ax.barh([y - 0.19 for y in ys], prev, height=0.36, color=PREVIOUS, zorder=3)
        ax.set_yticks(ys)
        ax.set_yticklabels(labels)
        ax.set_xlabel("Items")
        ax.xaxis.set_major_formatter(self.count_fmt())
        ax.grid(axis="y", visible=False)
        span = max(cur + prev + [1])
        for y, step in zip(ys, funnel):
            if step.get("step_rate_current") is not None:
                ax.text(step["current"] + span * 0.02, y + 0.19,
                        "%.1f%% of previous step" % step["step_rate_current"],
                        va="center", fontsize=8.5, color=INK_2)
        ax.set_xlim(0, span * 1.34)
        finish(ax)
        self.suptitle(fig, "Item funnel: view to purchase",
                      "Item counts at each step, with the share carried from the step above. "
                      "%s." % self.period_label)
        handles = [self.plt.Rectangle((0, 0), 1, 1, color=ORANGE),
                   self.plt.Rectangle((0, 0), 1, 1, color=PREVIOUS)]
        self.legend_below(fig, handles, ["Current period", "Previous period"], ncol=2)
        return self.save(
            fig, "ecommerce-funnel", "Item funnel: view to purchase",
            "Horizontal bars of item counts at each ecommerce funnel step for both periods, "
            "annotated with the progression rate from the step above.")

    # -- shared grouped-bar builder ----------------------------------------

    def _grouped_bars(self, data, name, title, axis_label, kind, subtitle, alt):
        labels = [shorten(d[0]) for d in data][::-1]
        cur = [d[1] if d[1] is not None else 0 for d in data][::-1]
        prev_raw = [d[2] for d in data][::-1]
        prev = [p if p is not None else 0 for p in prev_raw]

        fig, ax = self.plt.subplots(figsize=(9.2, 0.56 * len(labels) + 2.4))
        ys = list(range(len(labels)))
        ax.barh([y + 0.19 for y in ys], cur, height=0.36, color=BLUE, zorder=3)
        ax.barh([y - 0.19 for y in ys], prev, height=0.36, color=PREVIOUS, zorder=3)
        ax.set_yticks(ys)
        ax.set_yticklabels(labels)
        ax.set_xlabel(axis_label)
        ax.xaxis.set_major_formatter(self.money_fmt() if kind == "money" else self.count_fmt())
        ax.grid(axis="y", visible=False)

        span = max(cur + prev + [1])
        for y, c, p in zip(ys, cur, prev_raw):
            if p is None:
                ax.text(c + span * 0.02, y + 0.19, "new this period", va="center",
                        fontsize=8.5, color=INK_2)
                continue
            if p:
                delta = (c - p) / p * 100
                ax.text(c + span * 0.02, y + 0.19, "%s%.0f%%" % ("+" if delta > 0 else "", delta),
                        va="center", fontsize=8.5,
                        color=BLUE if delta > 0 else (RED if delta < 0 else INK_2))
        ax.set_xlim(0, span * 1.22)
        finish(ax)
        self.suptitle(fig, title, subtitle)
        handles = [self.plt.Rectangle((0, 0), 1, 1, color=BLUE),
                   self.plt.Rectangle((0, 0), 1, 1, color=PREVIOUS)]
        self.legend_below(fig, handles, ["Current period", "Previous period"], ncol=2)
        return self.save(fig, name, title, alt)


def main():
    ap = argparse.ArgumentParser(description="Draw charts from a GA4 analysis file.")
    ap.add_argument("--analysis", required=True)
    ap.add_argument("--out", help="Directory for PNGs (default: <analysis dir>/../charts)")
    ap.add_argument("--report-dir", help="Directory the Markdown report will live in, so the "
                                         "manifest can carry relative paths (default: the "
                                         "charts directory's parent)")
    ap.add_argument("--update-analysis", action="store_true",
                    help="Write the chart manifest back into the analysis file")
    ap.add_argument("--top-n", type=int, default=8, help="Rows per breakdown chart (default 8)")
    args = ap.parse_args()

    a_path = Path(args.analysis).expanduser()
    if not a_path.is_file():
        print("No such analysis file: %s" % a_path, file=sys.stderr)
        return 2
    try:
        analysis = json.loads(a_path.read_text(encoding="utf-8"))
    except ValueError as exc:
        print("That analysis file is not valid JSON (%s)." % exc, file=sys.stderr)
        return 2

    out_dir = Path(args.out).expanduser() if args.out else a_path.parent.parent / "charts"
    matplotlib, plt, FuncFormatter = load_matplotlib()

    if plt is None:
        manifest = [{
            "id": "all", "file": None, "status": "not drawn",
            "reason": "matplotlib is not installed on this machine, so no charts were "
                      "generated. Install it with `python3 -m pip install matplotlib`, or "
                      "write the report without charts and say in the report that the "
                      "visuals are unavailable -- do not describe charts that do not exist.",
        }]
        out_dir.mkdir(parents=True, exist_ok=True)
        (out_dir / "charts.json").write_text(json.dumps(manifest, indent=2), encoding="utf-8")
        print(json.dumps({"status": "unavailable", "charts": manifest}, indent=2))
        return 4

    style(plt, matplotlib)
    charts = Charts(analysis, out_dir, plt, matplotlib, FuncFormatter,
                    report_dir=args.report_dir)
    charts.kpi_change()
    charts.daily_performance()
    charts.channel_performance(top_n=args.top_n)
    charts.landing_pages(top_n=max(args.top_n, 10))
    charts.key_events(top_n=args.top_n)
    charts.devices()
    charts.ecommerce_performance(top_n=args.top_n)
    charts.ecommerce_funnel()

    manifest_path = out_dir / "charts.json"
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
        "files": [c["relative_path"] for c in drawn],
    }, indent=2))
    return 0 if drawn else 3


if __name__ == "__main__":
    sys.exit(main())
