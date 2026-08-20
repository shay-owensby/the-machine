#!/usr/bin/env python3
"""
Turn a raw Search Console retrieval into the output contract: what changed, what
it means, what is worth doing about it, and what cannot be concluded from this
data at all.

    python3 analyze_search_performance.py --raw <..._raw.json> [--out <dir>]

Writes `*_analysis.json` (the contract) and `*_tables.md` (the same figures
already formatted as Markdown tables).

Nothing here touches the network. Given the same raw file it produces the same
analysis, which is what makes a threshold change re-runnable and the fixtures in
assets/fixtures/ able to test the whole analytical half without credentials.

Four rules shape every calculation in this file:

  1. Unavailable is not zero. A metric Search Console did not return stays None
     all the way into the contract, and the presentation layer prints it as
     "not available" rather than as 0.

  2. Lower average position is better. Every direction/verdict pair is computed
     from `better_when`, never from the sign of the change. Position 12 -> 8 is
     an improvement whose arithmetic change is negative, and a report that reads
     the minus sign as bad news is wrong twice.

  3. Thresholds scale with the property. "1,000 impressions" is a rounding error
     on a publisher and the whole month on a local plumber. Opportunity floors
     are derived from this property's own volume, and the CTR benchmark a page
     is judged against is this property's own CTR at that position band -- not
     an industry table this data cannot see.

  4. A dimensional export is not the property total. Search Console withholds
     rows -- anonymised queries especially -- so summed query clicks are lower
     than property clicks, always, by an amount that varies. Property-level
     KPIs come from the dimensionless query and nothing else.
"""

import argparse
import json
import math
import sys
import urllib.parse
from datetime import date, datetime
from pathlib import Path

import gsc_common as gsc


# ---------------------------------------------------------------------------
# Thresholds -- all scaled from the property's own volume where it matters.
# Every one of these lands in analysis["thresholds"] so a reader can see the
# bar a finding had to clear.
# ---------------------------------------------------------------------------

MATERIAL_PCT = 5.0              # a KPI move below this is noise unless huge
MATERIAL_CLICKS_FLOOR = 10      # ...and must also move at least this many clicks
MATERIAL_IMPRESSIONS_FLOOR = 100
MATERIAL_CTR_POINTS = 0.2       # percentage points
MATERIAL_POSITION = 0.3         # average-position places

SMALL_SAMPLE_CLICKS = 30        # below this, click-derived conclusions are soft
SMALL_SAMPLE_IMPRESSIONS = 1000

OPPORTUNITY_IMPRESSION_SHARE = 0.0005   # 0.05% of property impressions...
OPPORTUNITY_IMPRESSION_FLOOR = 100      # ...but never below this

TOP_N = 15                      # rows in a "top" list
DETAIL_N = 10                   # rows in a movers/opportunities list

# Position bands used for ranking opportunities and for the property's own CTR
# benchmark. The bands are conventional: page-one-but-not-top, and page two.
BANDS = (
    ("1-3", 0.0, 3.5),
    ("4-10", 3.5, 10.5),
    ("11-20", 10.5, 20.5),
    ("21+", 20.5, 1e9),
)

CTR_BENCHMARK_MIN_ROWS = 8      # below this a band benchmark is not trustworthy
CANNIBALISATION_MIN_IMPRESSIONS = 200
CANNIBALISATION_MIN_SHARE = 0.2  # the second page must hold 20%+ of the query


# ---------------------------------------------------------------------------
# Small helpers
# ---------------------------------------------------------------------------

def pct(fraction):
    """A Search Console CTR fraction -> percent. None stays None."""
    return None if fraction is None else fraction * 100.0


def rnd(v, places=2):
    if v is None:
        return None
    if isinstance(v, float) and (math.isnan(v) or math.isinf(v)):
        return None
    return round(v, places)


def band_of(position):
    if position is None:
        return None
    for name, lo, hi in BANDS:
        if lo <= position < hi:
            return name
    return None


def fmt_int(v):
    return "n/a" if v is None else "{:,}".format(int(round(v)))


def fmt_rate(v, places=2):
    return "n/a" if v is None else ("%.*f%%" % (places, v))


def fmt_pos(v):
    return "n/a" if v is None else ("%.1f" % v)


def fmt_delta(v, unit):
    if v is None:
        return "n/a"
    sign = "+" if v > 0 else ""
    if unit == "int":
        return "%s%s" % (sign, "{:,}".format(int(round(v))))
    if unit == "rate":
        return "%s%.2f pp" % (sign, v)
    if unit == "position":
        return "%s%.1f" % (sign, v)
    return "%s%.2f" % (sign, v)


def fmt_pct_change(v):
    if v is None:
        return "n/a"
    return "%s%.1f%%" % ("+" if v > 0 else "", v)


def truncate(text, width=60):
    text = str(text or "")
    return text if len(text) <= width else text[: width - 1] + "…"


def short_url(url):
    """A page URL as a path, which is what a reader can actually scan."""
    if not url:
        return ""
    try:
        parts = urllib.parse.urlsplit(url)
        path = parts.path or "/"
        if parts.query:
            path += "?" + parts.query
        return path
    except Exception:
        return url


# ---------------------------------------------------------------------------
# Change records
# ---------------------------------------------------------------------------

def change_record(key, label, unit, better_when, current, previous, material_floor=None,
                  notes=None):
    """One metric, both periods, with direction and verdict kept apart.

    `direction` is arithmetic: did the number go up or down.
    `verdict` is interpretation: was that better or worse for the property.
    They differ for average position, and confusing them is the single most
    common error in a Search Console report.
    """
    notes = list(notes or [])
    absolute = gsc.absolute_change(current, previous)
    percent = gsc.percent_change(current, previous)

    if current is None and previous is None:
        availability = "unavailable"
    elif current is None or previous is None:
        availability = "partial"
    else:
        availability = "available"

    if absolute is None:
        direction = "n/a"
    elif abs(absolute) < 1e-12:
        direction = "flat"
    else:
        direction = "up" if absolute > 0 else "down"

    material = False
    if absolute is not None:
        big_enough = material_floor is None or abs(absolute) >= material_floor
        pct_enough = percent is None or abs(percent) >= MATERIAL_PCT
        material = bool(big_enough and pct_enough and direction != "flat")

    if availability == "unavailable":
        verdict = "unknown"
    elif previous in (None, 0) and current not in (None, 0):
        verdict = "new"
        notes.append(
            "The comparison period was zero or absent, so there is no percentage change to "
            "report -- only the absolute figure."
        )
    elif availability == "partial":
        verdict = "unknown"
    elif not material:
        verdict = "flat"
    elif better_when == "lower":
        verdict = "improved" if absolute < 0 else "declined"
    elif better_when == "higher":
        verdict = "improved" if absolute > 0 else "declined"
    else:
        verdict = "ambiguous"

    if material_floor is not None and absolute is not None and abs(absolute) < material_floor:
        notes.append(
            "Movement is below the materiality floor for this property (%s); treated as flat."
            % fmt_delta(material_floor, unit)
        )

    return {
        "key": key,
        "label": label,
        "unit": unit,
        "better_when": better_when,
        "current": rnd(current, 4),
        "previous": rnd(previous, 4),
        "absolute_change": rnd(absolute, 4),
        "percent_change": rnd(percent, 2),
        "availability": availability,
        "direction": direction,
        "verdict": verdict,
        "material": material,
        "notes": notes,
    }


# ---------------------------------------------------------------------------
# Dataset access
# ---------------------------------------------------------------------------

def rows_of(raw, dataset, period):
    node = ((raw.get("datasets") or {}).get(dataset) or {}).get(period)
    if not node:
        return None
    return node.get("rows")


def meta_of(raw, dataset, period):
    node = ((raw.get("datasets") or {}).get(dataset) or {}).get(period)
    return (node or {}).get("meta") or {}


def totals_from(rows):
    """Property-level totals out of a dimensionless Search Analytics response.

    That response is exactly one row. No rows at all means the property had no
    data in the window -- which is a finding, not a zero.
    """
    if not rows:
        return {"clicks": None, "impressions": None, "ctr": None, "position": None}
    r = rows[0]
    return {
        "clicks": r.get("clicks"),
        "impressions": r.get("impressions"),
        "ctr": pct(r.get("ctr")),
        "position": r.get("position"),
    }


def dimension_totals(rows):
    """Sum a dimensional export. Deliberately separate from totals_from() --
    these two numbers are not the same and the difference is reported."""
    if rows is None:
        return None
    clicks, _, _ = gsc.total(rows, "clicks")
    impressions, _, _ = gsc.total(rows, "impressions")
    position, weight = gsc.weighted_position(rows)
    return {
        "clicks": clicks,
        "impressions": impressions,
        "ctr": pct(gsc.safe_div(clicks, impressions)),
        "position": position,
        "position_weight": weight,
        "rows": len(rows),
    }


# ---------------------------------------------------------------------------
# Joining a dimension across the two periods
# ---------------------------------------------------------------------------

def join_dimension(current_rows, previous_rows, key_field):
    """Merge one dimension's rows across both periods into comparable records.

    A key present in only one period is kept, with the other side None rather
    than zero: Search Console withholding a row and a query genuinely getting no
    impressions look identical in an export, and pretending otherwise invents
    losses that did not happen. `present_in` says which it is.
    """
    cur = {r.get(key_field): r for r in (current_rows or []) if r.get(key_field) is not None}
    prev = {r.get(key_field): r for r in (previous_rows or []) if r.get(key_field) is not None}
    out = []
    for key in set(cur) | set(prev):
        c, p = cur.get(key), prev.get(key)
        rec = {
            "key": key,
            "present_in": "both" if c and p else ("current only" if c else "previous only"),
            "current": _side(c),
            "previous": _side(p),
        }
        rec["changes"] = {
            "clicks": gsc.absolute_change(rec["current"]["clicks"], rec["previous"]["clicks"]),
            "impressions": gsc.absolute_change(
                rec["current"]["impressions"], rec["previous"]["impressions"]),
            "ctr": gsc.absolute_change(rec["current"]["ctr"], rec["previous"]["ctr"]),
            "position": gsc.absolute_change(
                rec["current"]["position"], rec["previous"]["position"]),
        }
        rec["percent_changes"] = {
            "clicks": gsc.percent_change(rec["current"]["clicks"], rec["previous"]["clicks"]),
            "impressions": gsc.percent_change(
                rec["current"]["impressions"], rec["previous"]["impressions"]),
        }
        # Position improves as it falls; expose that once here so no consumer
        # has to remember to invert the sign.
        pos_delta = rec["changes"]["position"]
        rec["position_moved"] = (
            None if pos_delta is None
            else ("improved" if pos_delta < 0 else ("worsened" if pos_delta > 0 else "flat"))
        )
        out.append(rec)
    return out


def _side(row):
    if not row:
        return {"clicks": None, "impressions": None, "ctr": None, "position": None}
    return {
        "clicks": row.get("clicks"),
        "impressions": row.get("impressions"),
        "ctr": pct(row.get("ctr")),
        "position": row.get("position"),
    }


def clean(rec, key_label="query", shorten=False):
    """A joined record trimmed to what a report needs, rounded once."""
    out = {
        key_label: rec["key"],
        "present_in": rec["present_in"],
        "clicks": rnd(rec["current"]["clicks"], 0),
        "impressions": rnd(rec["current"]["impressions"], 0),
        "ctr": rnd(rec["current"]["ctr"], 2),
        "position": rnd(rec["current"]["position"], 1),
        "previous_clicks": rnd(rec["previous"]["clicks"], 0),
        "previous_impressions": rnd(rec["previous"]["impressions"], 0),
        "previous_ctr": rnd(rec["previous"]["ctr"], 2),
        "previous_position": rnd(rec["previous"]["position"], 1),
        "clicks_change": rnd(rec["changes"]["clicks"], 0),
        "clicks_change_pct": rnd(rec["percent_changes"]["clicks"], 1),
        "impressions_change": rnd(rec["changes"]["impressions"], 0),
        "impressions_change_pct": rnd(rec["percent_changes"]["impressions"], 1),
        "ctr_change_points": rnd(rec["changes"]["ctr"], 2),
        "position_change": rnd(rec["changes"]["position"], 1),
        "position_moved": rec["position_moved"],
        "band": band_of(rec["current"]["position"]),
    }
    if shorten:
        out["path"] = short_url(rec["key"])
    return out


# ---------------------------------------------------------------------------
# The property's own CTR benchmark
# ---------------------------------------------------------------------------

def ctr_benchmarks(records):
    """Median CTR by position band, computed from this property's own rows.

    This is the only honest yardstick available from Search Console alone. An
    industry CTR curve is not in this data, varies by SERP layout and intent,
    and would be an assumption dressed as a benchmark. "Below what this site
    itself achieves at this position" is a claim the data supports.
    """
    buckets = {}
    for r in records:
        if not r.get("impressions") or r.get("ctr") is None or r.get("position") is None:
            continue
        if r["impressions"] < 10:
            continue
        buckets.setdefault(r.get("band"), []).append(r["ctr"])
    out = {}
    for band, values in buckets.items():
        if band is None or len(values) < CTR_BENCHMARK_MIN_ROWS:
            continue
        values.sort()
        mid = len(values) // 2
        median = values[mid] if len(values) % 2 else (values[mid - 1] + values[mid]) / 2.0
        out[band] = {"median_ctr": rnd(median, 2), "rows": len(values)}
    return out


# ---------------------------------------------------------------------------
# Trend and anomalies
# ---------------------------------------------------------------------------

def build_trend(raw):
    cur_rows = rows_of(raw, "daily", "current") or []
    prev_rows = rows_of(raw, "daily", "previous") or []

    def series(rows):
        out = []
        for r in sorted(rows, key=lambda x: x.get("date") or ""):
            out.append({
                "date": r.get("date"),
                "clicks": rnd(r.get("clicks"), 0),
                "impressions": rnd(r.get("impressions"), 0),
                "ctr": rnd(pct(r.get("ctr")), 3),
                "position": rnd(r.get("position"), 2),
            })
        return out

    current = series(cur_rows)
    previous = series(prev_rows)
    return {
        "current": current,
        "previous": previous,
        "days_current": len(current),
        "days_previous": len(previous),
        "anomalies": detect_anomalies(current),
        "shape": describe_shape(current),
    }


def _median(values):
    if not values:
        return None
    v = sorted(values)
    mid = len(v) // 2
    return v[mid] if len(v) % 2 else (v[mid - 1] + v[mid]) / 2.0


def detect_anomalies(series):
    """Days that stand out far enough to be worth a sentence.

    Two guards, because the naive version produces nothing but false positives:

    * Weekdays and weekend days are judged against their own group. Search
      traffic on most properties falls 20-40% at the weekend, every weekend. A
      detector that has not been told this flags eight Saturdays a month and
      teaches the client to skip the section.

    * Median absolute deviation, not standard deviation, and a percentage floor
      on top. One enormous spike inflates a standard deviation until it hides
      itself, and a robust bar alone still fires on ordinary wobble at high
      volume.

    A day must clear 4x MAD, 30% of its group's typical day, and an absolute
    floor before it is called anything.
    """
    groups = {}
    for day in series:
        try:
            weekday = date.fromisoformat(day["date"]).weekday()
        except (ValueError, TypeError, KeyError):
            weekday = 0
        groups.setdefault("weekend" if weekday >= 5 else "weekday", []).append(day)

    out = []
    for metric in ("clicks", "impressions"):
        for group_name, days in groups.items():
            values = [d[metric] for d in days if d.get(metric) is not None]
            if len(values) < 6:
                continue
            med = _median(values)
            if not med:
                continue
            mad = _median([abs(v - med) for v in values]) or 0
            if mad == 0:
                continue
            floor = max(10 if metric == "clicks" else 100, med * 0.3)
            for day in days:
                v = day.get(metric)
                if v is None:
                    continue
                deviation = v - med
                if abs(deviation) < floor or abs(deviation) < 4 * mad:
                    continue
                out.append({
                    "date": day["date"],
                    "metric": metric,
                    "value": v,
                    "typical": rnd(med, 0),
                    "baseline": "typical %s" % group_name,
                    "deviation": rnd(deviation, 0),
                    "deviation_pct": rnd(deviation / med * 100.0, 1),
                    "kind": "spike" if deviation > 0 else "drop",
                    "confidence": "medium",
                    "statement": (
                        "%s on %s was %s against a typical %s of %s (%s)."
                        % (metric.capitalize(), day["date"], fmt_int(v), group_name,
                           fmt_int(med), fmt_pct_change(deviation / med * 100.0))
                    ),
                })

    # Clicks and impressions moving together on the same day is stronger
    # evidence than either alone.
    by_date = {}
    for a in out:
        by_date.setdefault(a["date"], []).append(a)
    for group in by_date.values():
        if len(group) > 1:
            for a in group:
                a["confidence"] = "high"
                a["notes"] = "Clicks and impressions both moved on this date."
    out.sort(key=lambda a: (a["date"], a["metric"]))
    return out


def describe_shape(series):
    """First half against second half of the current period.

    A 30-day total can be flat while the last ten days fall off a cliff, and the
    KPI table cannot show that. This is the cheapest way to catch it.
    """
    clicks = [d["clicks"] for d in series if d.get("clicks") is not None]
    if len(clicks) < 14:
        return None
    half = len(clicks) // 2
    first = sum(clicks[:half])
    second = sum(clicks[len(clicks) - half:])
    change = gsc.percent_change(second, first)
    if change is None:
        return None
    if abs(change) < 10:
        trend = "stable"
    elif change > 0:
        trend = "rising"
    else:
        trend = "falling"
    return {
        "first_half_clicks": first,
        "second_half_clicks": second,
        "change_pct": rnd(change, 1),
        "trend": trend,
        "statement": (
            "Within the current period, the second half delivered %s clicks against %s in the "
            "first half (%s)." % (fmt_int(second), fmt_int(first), fmt_pct_change(change))
        ),
    }


# ---------------------------------------------------------------------------
# Attribution: where did the click change come from?
# ---------------------------------------------------------------------------

def decompose_clicks(kpis):
    """Split the click change into the part impressions explain and the part CTR
    explains.

    clicks = impressions x CTR, so

        d(clicks) ~= d(impressions) x CTR_prev  +  impressions_now x d(CTR)

    The two terms plus a small interaction remainder add back to the actual
    change. This is arithmetic, not causation: it says which factor the change
    sits in, not why that factor moved.
    """
    clicks = kpis.get("clicks") or {}
    impressions = kpis.get("impressions") or {}
    ctr = kpis.get("ctr") or {}
    if any(k.get("availability") != "available" for k in (clicks, impressions, ctr)):
        return None
    d_imp = impressions["absolute_change"]
    d_ctr_frac = (ctr["absolute_change"] or 0) / 100.0
    ctr_prev_frac = (ctr["previous"] or 0) / 100.0
    imp_now = impressions["current"] or 0

    from_impressions = d_imp * ctr_prev_frac
    from_ctr = imp_now * d_ctr_frac
    actual = clicks["absolute_change"]
    residual = actual - (from_impressions + from_ctr)

    total_effect = abs(from_impressions) + abs(from_ctr)
    if total_effect == 0:
        dominant = "neither"
    elif abs(from_impressions) >= abs(from_ctr) * 1.5:
        dominant = "impressions"
    elif abs(from_ctr) >= abs(from_impressions) * 1.5:
        dominant = "ctr"
    else:
        dominant = "both"

    return {
        "actual_click_change": rnd(actual, 0),
        "explained_by_impressions": rnd(from_impressions, 0),
        "explained_by_ctr": rnd(from_ctr, 0),
        "interaction_residual": rnd(residual, 0),
        "dominant_factor": dominant,
        "statement": {
            "impressions": (
                "The click change sits mostly in visibility: impressions moved by %s, worth "
                "about %s clicks at the previous CTR." % (
                    fmt_delta(d_imp, "int"), fmt_delta(from_impressions, "int"))
            ),
            "ctr": (
                "The click change sits mostly in click-through rate: CTR moved %s, worth about "
                "%s clicks at the current impression volume." % (
                    fmt_delta(ctr["absolute_change"], "rate"), fmt_delta(from_ctr, "int"))
            ),
            "both": (
                "Impressions and CTR both moved materially: about %s clicks from visibility and "
                "%s from click-through rate." % (
                    fmt_delta(from_impressions, "int"), fmt_delta(from_ctr, "int"))
            ),
            "neither": "Neither impressions nor CTR moved enough to explain a click change.",
        }[dominant],
        "caveat": (
            "This is an arithmetic split of where the change sits, not an explanation of why "
            "it happened."
        ),
    }


def concentration(records, key_label, direction="loss", limit=5):
    """How much of the total movement a handful of rows account for.

    "Clicks fell 18%" and "clicks fell 18%, and 80% of that came from three
    pages" call for different responses. This is the second sentence.
    """
    movers_list = [
        r for r in records
        if r.get("clicks_change") is not None
        and ((r["clicks_change"] < 0) if direction == "loss" else (r["clicks_change"] > 0))
    ]
    if not movers_list:
        return None
    movers_list.sort(key=lambda r: r["clicks_change"], reverse=(direction == "gain"))
    total_move = sum(r["clicks_change"] for r in movers_list)
    top = movers_list[:limit]
    top_move = sum(r["clicks_change"] for r in top)
    if not total_move:
        return None
    return {
        "direction": direction,
        "total_change_across_rows": rnd(total_move, 0),
        "top_n": len(top),
        "top_n_change": rnd(top_move, 0),
        "top_n_share_pct": rnd(abs(top_move) / abs(total_move) * 100.0, 1),
        "entities": [r.get(key_label) for r in top],
    }


# ---------------------------------------------------------------------------
# Opportunity detection
# ---------------------------------------------------------------------------

def opportunity_floor(total_impressions):
    """The impression bar a row must clear to be worth a recommendation.

    Scaled from the property: 0.05% of its impressions, never below 100. On a
    property with 2,000,000 impressions that is 1,000; on one with 20,000 it is
    the floor. A fixed threshold either buries a small site's entire opportunity
    set or fills a large site's report with noise.
    """
    if not total_impressions:
        return OPPORTUNITY_IMPRESSION_FLOOR
    return max(OPPORTUNITY_IMPRESSION_FLOOR,
               int(round(total_impressions * OPPORTUNITY_IMPRESSION_SHARE)))


def ctr_opportunities(records, benchmarks, floor, limit=DETAIL_N):
    """Rows with real visibility whose CTR trails what this property achieves at
    the same position band.

    Deliberately NOT "low CTR": a page at position 30 has a low CTR because it is
    at position 30, and rewriting its title will not fix that. The comparison is
    against the same band, so what surfaces is a row underperforming its own
    ranking -- the case where presentation, not position, is the lever.
    """
    out = []
    for r in records:
        imps = r.get("impressions")
        ctr = r.get("ctr")
        band = r.get("band")
        if not imps or ctr is None or band is None or imps < floor:
            continue
        bench = benchmarks.get(band)
        if not bench or bench["median_ctr"] in (None, 0):
            continue
        median = bench["median_ctr"]
        if ctr >= median * 0.7:
            continue
        potential = imps * (median - ctr) / 100.0
        if potential < 5:
            continue
        # How big is the implied gain against what the row earns today? A ceiling
        # of ten times current clicks is arithmetically true and practically
        # misleading: a gap that large usually means the impressions come from
        # queries where the row ranks far below its average position, or from a
        # result type that does not behave like an ordinary blue link. Flagging
        # it keeps an implausible number out of a client's expectations.
        current_clicks = r.get("clicks") or 0
        ratio = (potential / current_clicks) if current_clicks else None
        speculative = ratio is None or ratio > 3

        caveat = (
            "Closing the gap is a presentation change -- title, description, snippet "
            "eligibility -- and does not move rankings. The figure is a ceiling computed at "
            "today's impressions, not a forecast."
        )
        if speculative:
            caveat += (
                " Treat this one as an upper bound only: the implied gain is more than three "
                "times the row's current clicks, which usually means its impressions come from "
                "queries where it ranks well below its average position. Look at it query by "
                "query before promising anything."
            )

        entry = dict(r)
        entry.update({
            "band_median_ctr": median,
            "ctr_gap_points": rnd(median - ctr, 2),
            "clicks_at_band_median": rnd(potential, 0),
            "ceiling_ratio": rnd(ratio, 1),
            "ceiling_is_speculative": speculative,
            "basis": (
                "%s impressions at position %s with %s CTR, against a median of %s for this "
                "property's own rows in positions %s."
                % (fmt_int(imps), fmt_pos(r.get("position")), fmt_rate(ctr),
                   fmt_rate(median), band)
            ),
            "caveat": caveat,
        })
        out.append(entry)
    out.sort(key=lambda r: r["clicks_at_band_median"] or 0, reverse=True)
    return out[:limit]


def ranking_opportunities(records, floor, limit=DETAIL_N):
    """Rows with meaningful visibility sitting just below where clicks live.

    Positions 4-10 and 11-20 only. A row at position 60 has no realistic upside
    this dataset can evidence, and one already at 1-3 has nowhere to go.
    Priority weights impressions first, then how close the row already is, then
    whether it is moving the right way -- a query improving from 14 to 11 is a
    better bet than one falling from 8 to 12.
    """
    out = []
    for r in records:
        imps = r.get("impressions")
        pos = r.get("position")
        band = r.get("band")
        if not imps or pos is None or imps < floor:
            continue
        if band not in ("4-10", "11-20"):
            continue
        closeness = max(0.0, (20.5 - pos) / 20.5)
        momentum = 0.0
        if r.get("position_change") is not None:
            momentum = max(-1.0, min(1.0, -r["position_change"] / 5.0))
        score = imps * (0.6 + 0.4 * closeness) * (1.0 + 0.25 * momentum)
        if r.get("position_change") is None:
            movement = ""
        elif r["position_change"] < -0.3:
            movement = ", position improving"
        elif r["position_change"] > 0.3:
            movement = ", position worsening"
        else:
            movement = ", position broadly stable"
        entry = dict(r)
        entry.update({
            "opportunity_score": rnd(score, 0),
            "basis": "%s impressions at average position %s (%s band)%s."
                     % (fmt_int(imps), fmt_pos(pos), band, movement),
            "caveat": (
                "Search Console cannot say whether this term is commercially relevant. "
                "Confirm the intent matches the business before committing work."
            ),
        })
        out.append(entry)
    out.sort(key=lambda r: r["opportunity_score"] or 0, reverse=True)
    return out[:limit]


def movers(records, direction, floor_clicks, limit=DETAIL_N):
    """Biggest absolute click gains or losses, filtered for materiality."""
    out = []
    for r in records:
        change = r.get("clicks_change")
        if change is None:
            continue
        if direction == "gain" and change <= 0:
            continue
        if direction == "loss" and change >= 0:
            continue
        if abs(change) < floor_clicks:
            continue
        out.append(r)
    out.sort(key=lambda r: r["clicks_change"], reverse=(direction == "gain"))
    return out[:limit]


def visibility_losses(records, floor, limit=DETAIL_N):
    """Rows losing impressions, which is a different problem from losing clicks.

    A page can hold its clicks while its impressions halve -- the visibility is
    going, the traffic has not noticed yet. Reporting only click losses misses
    it until the quarter it becomes a click loss.
    """
    out = []
    for r in records:
        change = r.get("impressions_change")
        prev = r.get("previous_impressions")
        if change is None or change >= 0 or not prev or prev < floor:
            continue
        if abs(change) < max(OPPORTUNITY_IMPRESSION_FLOOR, prev * 0.25):
            continue
        entry = dict(r)
        entry["loss_kind"] = classify_loss(r)
        out.append(entry)
    out.sort(key=lambda r: r["impressions_change"])
    return out[:limit]


def classify_loss(r):
    """Name what kind of loss this row is, rather than calling everything a
    ranking problem.

    visibility  fewer impressions, position roughly held -- fewer queries
                matched, or the SERP changed shape
    ranking     position worsened materially
    ctr         impressions and position held, CTR fell
    mixed       more than one of the above moved
    """
    kinds = []
    imp_change = r.get("impressions_change") or 0
    prev_imp = r.get("previous_impressions") or 0
    if imp_change < 0 and abs(imp_change) >= max(OPPORTUNITY_IMPRESSION_FLOOR, prev_imp * 0.2):
        kinds.append("visibility")
    if (r.get("position_change") or 0) > MATERIAL_POSITION * 2:
        kinds.append("ranking")
    if (r.get("ctr_change_points") or 0) < -MATERIAL_CTR_POINTS:
        kinds.append("ctr")
    if not kinds:
        return "unclear"
    return kinds[0] if len(kinds) == 1 else "mixed"


# ---------------------------------------------------------------------------
# Branded vs non-branded -- only ever with configured terms
# ---------------------------------------------------------------------------

def brand_split(records, brand_terms):
    """Split queries into branded and non-branded, using CONFIGURED terms only.

    With no configured terms this returns None and the report says the analysis
    requires configuration. It does not guess. Guessing means deciding that
    "smith plumbing" is branded and "smith street plumber" is not, from a data
    source that knows neither the brand nor the street -- and every downstream
    number inherits the guess.
    """
    if not brand_terms:
        return None
    terms = [t.lower() for t in brand_terms if t.strip()]
    branded, non_branded = [], []
    for r in records:
        q = str(r.get("query") or "").lower()
        (branded if any(t in q for t in terms) else non_branded).append(r)

    def side(rows, label):
        clicks = sum(r["clicks"] or 0 for r in rows)
        imps = sum(r["impressions"] or 0 for r in rows)
        prev_clicks = sum(r.get("previous_clicks") or 0 for r in rows)
        prev_imps = sum(r.get("previous_impressions") or 0 for r in rows)
        return {
            "label": label,
            "queries": len(rows),
            "clicks": clicks,
            "impressions": imps,
            "ctr": rnd(pct(gsc.safe_div(clicks, imps)), 2),
            "previous_clicks": prev_clicks,
            "previous_impressions": prev_imps,
            "clicks_change": clicks - prev_clicks,
            "clicks_change_pct": rnd(gsc.percent_change(clicks, prev_clicks), 1),
        }

    b, n = side(branded, "branded"), side(non_branded, "non-branded")
    total_clicks = (b["clicks"] or 0) + (n["clicks"] or 0)
    return {
        "configured_terms": brand_terms,
        "branded": b,
        "non_branded": n,
        "branded_share_of_clicks_pct": rnd(
            (b["clicks"] / total_clicks * 100.0) if total_clicks else None, 1),
        "basis": (
            "Classified by substring match against %d configured brand term(s). Query-level "
            "data excludes anonymised queries, so these shares describe the visible query set, "
            "not all organic traffic." % len(brand_terms)
        ),
    }


# ---------------------------------------------------------------------------
# Cannibalisation signal
# ---------------------------------------------------------------------------

def cannibalisation(query_page_rows, floor):
    """Queries where two or more pages both hold real impressions.

    This is a signal, not a diagnosis. Two pages ranking for one query is normal
    when they serve different intents and a problem when they are the same
    article twice. Search Console cannot tell those apart; a human reading the
    two URLs can, in about ten seconds.
    """
    if not query_page_rows:
        return []
    by_query = {}
    for r in query_page_rows:
        q, p = r.get("query"), r.get("page")
        if not q or not p:
            continue
        by_query.setdefault(q, []).append(r)

    out = []
    for q, rows in by_query.items():
        if len(rows) < 2:
            continue
        rows.sort(key=lambda r: r.get("impressions") or 0, reverse=True)
        total_imp = sum(r.get("impressions") or 0 for r in rows)
        if total_imp < max(CANNIBALISATION_MIN_IMPRESSIONS, floor):
            continue
        second = rows[1]
        share = gsc.safe_div(second.get("impressions"), total_imp) or 0
        if share < CANNIBALISATION_MIN_SHARE:
            continue
        out.append({
            "query": q,
            "pages": [
                {
                    "page": r.get("page"),
                    "path": short_url(r.get("page")),
                    "clicks": rnd(r.get("clicks"), 0),
                    "impressions": rnd(r.get("impressions"), 0),
                    "ctr": rnd(pct(r.get("ctr")), 2),
                    "position": rnd(r.get("position"), 1),
                }
                for r in rows[:4]
            ],
            "total_impressions": rnd(total_imp, 0),
            "second_page_share_pct": rnd(share * 100.0, 1),
            "signal": (
                "%d pages hold impressions for this query; the second holds %.0f%% of them."
                % (len(rows), share * 100.0)
            ),
            "caveat": (
                "Two pages ranking for one query is only a problem when they serve the same "
                "intent. Read both URLs before consolidating anything."
            ),
        })
    out.sort(key=lambda r: r["total_impressions"], reverse=True)
    return out[:DETAIL_N]


# ---------------------------------------------------------------------------
# Findings
#
# Every finding carries the numbers that produced it. A finding without evidence
# is an opinion, and an opinion in a client report is indistinguishable from a
# mistake. Severity is how much it matters; confidence is how sure the data
# allows anyone to be -- they are not the same axis, and a high-severity,
# low-confidence finding is exactly the thing to investigate rather than assert.
# ---------------------------------------------------------------------------

def finding(fid, ftype, title, statement, evidence, severity="medium", confidence="medium",
            scope="property", entity=None, caveat=None):
    return {
        "id": fid,
        "type": ftype,
        "title": title,
        "statement": statement,
        "evidence": [e for e in evidence if e],
        "severity": severity,
        "confidence": confidence,
        "scope": scope,
        "entity": entity,
        "caveat": caveat,
    }


def build_findings(a):
    """Everything worth a sentence, grouped by what kind of sentence it is."""
    out = {"strengths": [], "weaknesses": [], "risks": [], "opportunities": [],
           "anomalies": [], "observations": []}

    k = a["kpis_by_key"]
    clicks, imps, ctr, pos = k["clicks"], k["impressions"], k["ctr"], k["average_position"]
    small_sample = (clicks.get("current") or 0) < SMALL_SAMPLE_CLICKS
    base_conf = "low" if small_sample else "high"

    def ev(kpi):
        return "%s: %s vs %s (%s, %s)" % (
            kpi["label"],
            fmt_metric(kpi, kpi["current"]), fmt_metric(kpi, kpi["previous"]),
            fmt_delta(kpi["absolute_change"], kpi["unit"]),
            fmt_pct_change(kpi["percent_change"]),
        )

    # -- headline direction -------------------------------------------------
    if clicks["verdict"] == "improved":
        out["strengths"].append(finding(
            "clicks_up", "traffic", "Organic clicks grew",
            "Organic clicks rose %s (%s) against the comparison period."
            % (fmt_delta(clicks["absolute_change"], "int"),
               fmt_pct_change(clicks["percent_change"])),
            [ev(clicks), ev(imps)], severity="high", confidence=base_conf,
        ))
    elif clicks["verdict"] == "declined":
        out["weaknesses"].append(finding(
            "clicks_down", "traffic", "Organic clicks fell",
            "Organic clicks fell %s (%s) against the comparison period."
            % (fmt_delta(clicks["absolute_change"], "int"),
               fmt_pct_change(clicks["percent_change"])),
            [ev(clicks), ev(imps), ev(ctr)], severity="high", confidence=base_conf,
        ))

    if imps["verdict"] == "improved" and clicks["verdict"] != "improved":
        out["observations"].append(finding(
            "impressions_up_clicks_flat", "visibility",
            "Visibility grew without a matching click gain",
            "Impressions rose %s while clicks %s. More of the site is being shown; more of it "
            "is not being clicked." % (
                fmt_pct_change(imps["percent_change"]),
                "fell %s" % fmt_pct_change(clicks["percent_change"])
                if clicks["verdict"] == "declined" else "held broadly flat"),
            [ev(imps), ev(clicks), ev(ctr), ev(pos)], severity="medium", confidence=base_conf,
            caveat="New impressions often arrive at weaker positions, which lowers average CTR "
                   "without anything getting worse. Check the position trend before treating "
                   "this as a CTR problem.",
        ))

    # Clicks falling faster than impressions is the case that matters, whether
    # impressions fell slightly, held, or rose. Gating this on impressions also
    # having declined misses the worst version of it: visibility up, traffic
    # down.
    if (clicks["verdict"] == "declined"
            and clicks["percent_change"] is not None
            and imps["percent_change"] is not None
            and clicks["percent_change"] < imps["percent_change"] - 5):
        out["weaknesses"].append(finding(
            "clicks_falling_faster", "ctr",
            "Clicks are falling faster than impressions",
            "Clicks fell %s while impressions moved %s, so the loss is not visibility alone -- "
            "the site is converting a smaller share of what it is shown for." % (
                fmt_pct_change(clicks["percent_change"]),
                fmt_pct_change(imps["percent_change"])),
            [ev(clicks), ev(imps), ev(ctr), ev(pos)], severity="high", confidence=base_conf,
        ))

    # -- CTR and position ---------------------------------------------------
    position_stable = pos["availability"] == "available" and not pos["material"]
    if ctr["verdict"] == "declined" and position_stable:
        out["weaknesses"].append(finding(
            "ctr_down_position_stable", "ctr",
            "CTR fell while average position held",
            "Click-through rate fell %s while average position stayed within %s. Rankings did "
            "not move; the share of impressions turning into clicks did." % (
                fmt_delta(ctr["absolute_change"], "rate"), fmt_pos(MATERIAL_POSITION)),
            [ev(ctr), ev(pos), ev(imps)], severity="high", confidence=base_conf,
            caveat="A stable average position can still hide a changed SERP -- more ads, an AI "
                   "answer, a new feature block. Search Console does not report SERP layout, so "
                   "this is a symptom to investigate, not a diagnosis.",
        ))
    elif ctr["verdict"] == "improved" and clicks["verdict"] != "declined":
        out["strengths"].append(finding(
            "ctr_up", "ctr", "Click-through rate improved",
            "CTR rose %s, so a larger share of the same visibility turned into visits."
            % fmt_delta(ctr["absolute_change"], "rate"),
            [ev(ctr), ev(imps), ev(clicks)], severity="medium", confidence=base_conf,
        ))

    if pos["verdict"] == "improved":
        out["strengths"].append(finding(
            "position_improved", "ranking", "Average position improved",
            "Average position improved from %s to %s (lower is better)."
            % (fmt_pos(pos["previous"]), fmt_pos(pos["current"])),
            [ev(pos), ev(imps)], severity="medium", confidence="medium",
            caveat="Search Console average position is an impression-weighted average across "
                   "every query the property appeared for. It moves when the query mix changes, "
                   "not only when rankings do.",
        ))
        if clicks["verdict"] == "declined":
            out["observations"].append(finding(
                "position_up_clicks_down", "ranking",
                "Rankings improved while clicks fell",
                "Average position improved but clicks fell, which usually means the improvement "
                "landed on lower-volume queries, or the query mix shifted.",
                [ev(pos), ev(clicks), ev(imps)], severity="medium", confidence="medium",
            ))
    elif pos["verdict"] == "declined":
        out["weaknesses"].append(finding(
            "position_declined", "ranking", "Average position worsened",
            "Average position moved from %s to %s (higher is worse)."
            % (fmt_pos(pos["previous"]), fmt_pos(pos["current"])),
            [ev(pos), ev(imps), ev(clicks)], severity="medium", confidence="medium",
            caveat="Average position falls when a property starts appearing for many new "
                   "low-ranking queries, even with nothing lost. Read it alongside impressions.",
        ))

    # -- no baseline, or no material movement at all ------------------------
    if all(kpi["verdict"] == "new" for kpi in a["kpis"] if kpi["current"] is not None):
        out["observations"].append(finding(
            "no_baseline", "coverage", "No comparison period exists",
            "The comparison window returned no data, so every figure in this report is an "
            "absolute for the current period and nothing is a change. A property verified "
            "part-way through the baseline window produces exactly this shape.",
            ["Current period: %s clicks, %s impressions"
             % (fmt_int(clicks["current"]), fmt_int(imps["current"])),
             "Comparison period %s to %s returned no rows"
             % (a["periods"]["previous"]["start"], a["periods"]["previous"]["end"])],
            severity="medium", confidence="high",
            caveat="Do not describe this as growth. There is no baseline to have grown from.",
        ))
    elif not any(kpi["material"] for kpi in a["kpis"]):
        out["observations"].append(finding(
            "broadly_flat", "trend", "Performance was broadly flat",
            "No headline metric moved beyond this property's materiality thresholds: clicks %s, "
            "impressions %s, CTR %s, average position %s. A stable period is a finding in its "
            "own right and does not need a cause." % (
                fmt_pct_change(clicks["percent_change"]),
                fmt_pct_change(imps["percent_change"]),
                fmt_delta(ctr["absolute_change"], "rate"),
                fmt_delta(pos["absolute_change"], "position")),
            [ev(clicks), ev(imps), ev(ctr), ev(pos)],
            severity="low", confidence=base_conf,
        ))

    # -- attribution --------------------------------------------------------
    dec = a.get("click_attribution")
    if dec and clicks.get("material"):
        out["observations"].append(finding(
            "click_attribution", "attribution", "Where the click change sits",
            dec["statement"],
            ["Impressions component: %s clicks" % fmt_delta(dec["explained_by_impressions"], "int"),
             "CTR component: %s clicks" % fmt_delta(dec["explained_by_ctr"], "int"),
             "Actual change: %s clicks" % fmt_delta(dec["actual_click_change"], "int")],
            severity="low", confidence="high", caveat=dec["caveat"],
        ))

    # -- shape within the period -------------------------------------------
    shape = (a.get("trend") or {}).get("shape")
    if shape and shape["trend"] == "falling" and abs(shape["change_pct"] or 0) >= 20:
        out["risks"].append(finding(
            "declining_within_period", "trend", "Performance is falling within the period",
            shape["statement"] + " A period total can look acceptable while the trend inside it "
            "is not.",
            [shape["statement"]], severity="high", confidence="medium",
        ))
    elif shape and shape["trend"] == "rising" and (shape["change_pct"] or 0) >= 20:
        out["strengths"].append(finding(
            "rising_within_period", "trend", "Performance is rising within the period",
            shape["statement"], [shape["statement"]], severity="medium", confidence="medium",
        ))

    # -- anomalies ----------------------------------------------------------
    for anomaly in (a.get("trend") or {}).get("anomalies", [])[:6]:
        out["anomalies"].append(finding(
            "anomaly:%s:%s" % (anomaly["date"], anomaly["metric"]), "anomaly",
            "%s %s on %s" % (anomaly["metric"].capitalize(), anomaly["kind"], anomaly["date"]),
            anomaly["statement"], [anomaly["statement"]],
            severity="low" if anomaly["kind"] == "spike" else "medium",
            confidence=anomaly["confidence"], scope="day", entity=anomaly["date"],
            caveat="A single unusual day is worth noting and rarely worth acting on. Repeated "
                   "or consecutive days are the signal.",
        ))

    # -- query and page level ----------------------------------------------
    queries = a.get("queries") or {}
    pages = a.get("pages") or {}

    for label, node, key_label in (("query", queries, "query"), ("page", pages, "page")):
        losers = node.get("losers") or []
        if losers:
            top = losers[0]
            name = top.get("path") or top.get(key_label)
            out["weaknesses"].append(finding(
                "%s_losses" % label, "traffic",
                "Click losses concentrated in specific %ss" % label,
                "The largest %s loss is %s: %s clicks (%s), %s." % (
                    label, truncate(name, 70), fmt_delta(top["clicks_change"], "int"),
                    fmt_pct_change(top["clicks_change_pct"]),
                    describe_row_change(top)),
                ["%s: %s clicks (%s), impressions %s, position %s -> %s" % (
                    truncate(r.get("path") or r.get(key_label), 60),
                    fmt_delta(r["clicks_change"], "int"), fmt_pct_change(r["clicks_change_pct"]),
                    fmt_delta(r["impressions_change"], "int"),
                    fmt_pos(r["previous_position"]), fmt_pos(r["position"]))
                 for r in losers[:5]],
                severity="high" if len(losers) >= 3 else "medium",
                confidence="high", scope=label,
            ))
        winners = node.get("winners") or []
        if winners:
            top = winners[0]
            name = top.get("path") or top.get(key_label)
            out["strengths"].append(finding(
                "%s_gains" % label, "traffic", "Click growth concentrated in specific %ss" % label,
                "The largest %s gain is %s: %s clicks (%s), %s." % (
                    label, truncate(name, 70), fmt_delta(top["clicks_change"], "int"),
                    fmt_pct_change(top["clicks_change_pct"]),
                    describe_row_change(top)),
                ["%s: %s clicks (%s), position %s -> %s" % (
                    truncate(r.get("path") or r.get(key_label), 60),
                    fmt_delta(r["clicks_change"], "int"), fmt_pct_change(r["clicks_change_pct"]),
                    fmt_pos(r["previous_position"]), fmt_pos(r["position"]))
                 for r in winners[:5]],
                severity="medium", confidence="high", scope=label,
            ))

        conc = node.get("loss_concentration")
        if conc and conc["top_n_share_pct"] and conc["top_n_share_pct"] >= 60:
            out["risks"].append(finding(
                "%s_loss_concentration" % label, "concentration",
                "Most of the %s-level loss comes from a handful of %ss" % (label, label),
                "%d %ss account for %.0f%% of the total %s-level click loss (%s of %s clicks). "
                "A narrow cause is easier to find and easier to fix than a broad one." % (
                    conc["top_n"], label, conc["top_n_share_pct"], label,
                    fmt_delta(conc["top_n_change"], "int"),
                    fmt_delta(conc["total_change_across_rows"], "int")),
                [truncate(e, 70) for e in conc["entities"]],
                severity="medium", confidence="high", scope=label,
            ))

        vis = node.get("visibility_losses") or []
        if vis:
            out["risks"].append(finding(
                "%s_visibility_losses" % label, "visibility",
                "%ss losing impressions" % label.capitalize(),
                "%d %s(s) lost a quarter or more of their impressions. Visibility loss precedes "
                "click loss; these are the ones to look at before they become a traffic "
                "problem." % (len(vis), label),
                ["%s: impressions %s -> %s (%s), position %s -> %s [%s]" % (
                    truncate(r.get("path") or r.get(key_label), 55),
                    fmt_int(r["previous_impressions"]), fmt_int(r["impressions"]),
                    fmt_pct_change(r["impressions_change_pct"]),
                    fmt_pos(r["previous_position"]), fmt_pos(r["position"]), r["loss_kind"])
                 for r in vis[:5]],
                severity="medium", confidence="medium", scope=label,
            ))

        ctr_ops = node.get("ctr_opportunities") or []
        if ctr_ops:
            total = sum(r["clicks_at_band_median"] or 0 for r in ctr_ops)
            out["opportunities"].append(finding(
                "%s_ctr_opportunities" % label, "ctr",
                "%ss underperforming their own position band on CTR" % label.capitalize(),
                "%d %s(s) hold substantial impressions at a CTR well below what this property "
                "achieves at the same positions. Closing those gaps at today's impression "
                "volume is worth roughly %s clicks a period." % (
                    len(ctr_ops), label, fmt_int(total)),
                ["%s: %s impressions at position %s, CTR %s vs band median %s (%s clicks)" % (
                    truncate(r.get("path") or r.get(key_label), 55), fmt_int(r["impressions"]),
                    fmt_pos(r["position"]), fmt_rate(r["ctr"]), fmt_rate(r["band_median_ctr"]),
                    fmt_int(r["clicks_at_band_median"]))
                 for r in ctr_ops[:5]],
                severity="medium", confidence="medium", scope=label,
                caveat="A ceiling at current impressions, not a forecast, and a presentation "
                       "lever rather than a ranking one.",
            ))

        rank_ops = node.get("ranking_opportunities") or []
        if rank_ops:
            out["opportunities"].append(finding(
                "%s_ranking_opportunities" % label, "ranking",
                "%ss with visibility just below the click zone" % label.capitalize(),
                "%d %s(s) carry meaningful impressions in positions 4-20, where small ranking "
                "movements produce disproportionate click changes." % (len(rank_ops), label),
                ["%s: %s impressions at position %s%s" % (
                    truncate(r.get("path") or r.get(key_label), 55), fmt_int(r["impressions"]),
                    fmt_pos(r["position"]),
                    "" if r["position_change"] is None
                    else " (%s from %s)" % (
                        fmt_delta(r["position_change"], "position"), fmt_pos(r["previous_position"])))
                 for r in rank_ops[:5]],
                severity="medium", confidence="medium", scope=label,
                caveat="Search Console shows visibility, not commercial value. Confirm relevance "
                       "before committing effort.",
            ))

    # -- devices ------------------------------------------------------------
    devices = a.get("devices") or {}
    for row in devices.get("rows") or []:
        if (row.get("impressions") or 0) < SMALL_SAMPLE_IMPRESSIONS:
            continue
        if (row.get("ctr_change_points") or 0) <= -MATERIAL_CTR_POINTS * 2 and row["device"]:
            out["weaknesses"].append(finding(
                "device_ctr_decline:%s" % row["device"], "ctr",
                "%s CTR declined" % str(row["device"]).capitalize(),
                "%s CTR fell from %s to %s across %s impressions." % (
                    str(row["device"]).capitalize(), fmt_rate(row["previous_ctr"]),
                    fmt_rate(row["ctr"]), fmt_int(row["impressions"])),
                ["%s: clicks %s, impressions %s, position %s -> %s" % (
                    row["device"], fmt_delta(row["clicks_change"], "int"),
                    fmt_delta(row["impressions_change"], "int"),
                    fmt_pos(row["previous_position"]), fmt_pos(row["position"]))],
                severity="medium", confidence="medium", scope="device", entity=row["device"],
            ))

    # -- countries ----------------------------------------------------------
    #
    # A country growing at the same rate as the property is not news -- it is the
    # property, seen through one market. What is worth a sentence is DIVERGENCE:
    # a market moving against the trend, or far harder than it.
    countries = a.get("countries") or {}
    if countries.get("material"):
        property_pct = clicks.get("percent_change")
        flagged = 0
        for row in (countries.get("rows") or []):
            if flagged >= 3:
                break
            change = row.get("clicks_change")
            country_pct = row.get("clicks_change_pct")
            share = row.get("share_of_clicks_pct") or 0
            if change is None or abs(change) < max(MATERIAL_CLICKS_FLOOR, 50) or share < 5:
                continue
            if property_pct is not None and country_pct is not None:
                divergence = country_pct - property_pct
                if abs(divergence) < 15:
                    continue
            else:
                divergence = None
            flagged += 1
            out["observations"].append(finding(
                "country_move:%s" % row["country"], "geography",
                "%s moved against the property trend" % str(row["country"]).upper(),
                "%s holds %.0f%% of clicks and changed %s (%s)%s." % (
                    str(row["country"]).upper(), share, fmt_delta(change, "int"),
                    fmt_pct_change(country_pct),
                    ", against %s for the property overall" % fmt_pct_change(property_pct)
                    if divergence is not None else ""),
                ["%s: %s clicks vs %s, %s impressions vs %s, position %s -> %s" % (
                    str(row["country"]).upper(), fmt_int(row["clicks"]),
                    fmt_int(row["previous_clicks"]), fmt_int(row["impressions"]),
                    fmt_int(row["previous_impressions"]),
                    fmt_pos(row["previous_position"]), fmt_pos(row["position"]))],
                severity="low", confidence="medium", scope="country", entity=row["country"],
            ))

    # -- cannibalisation ----------------------------------------------------
    for signal in (a.get("query_page") or {}).get("cannibalisation", [])[:3]:
        out["observations"].append(finding(
            "cannibalisation:%s" % signal["query"], "cannibalisation",
            "Multiple pages competing for one query",
            "%s -- %s" % (truncate(signal["query"], 60), signal["signal"]),
            ["%s: %s impressions at position %s" % (
                p["path"], fmt_int(p["impressions"]), fmt_pos(p["position"]))
             for p in signal["pages"][:3]],
            severity="low", confidence="low", scope="query", entity=signal["query"],
            caveat=signal["caveat"],
        ))

    # -- indexing diagnostics ----------------------------------------------
    for result in ((a.get("url_inspection") or {}).get("results") or []):
        verdict = (result.get("verdict") or "").upper()
        coverage = result.get("coverage_state") or "unknown"
        if verdict == "PASS" and "indexed" in coverage.lower():
            continue
        out["risks"].append(finding(
            "indexing:%s" % result["url"], "indexing",
            "Indexing state worth checking on %s" % short_url(result["url"]),
            "URL Inspection reports %s (%s) for this page, which lost visibility this period "
            "(%s)." % (verdict or "no verdict", coverage, result.get("selected_because", "")),
            ["Coverage: %s" % coverage,
             "Google-selected canonical: %s" % (result.get("google_canonical") or "not reported"),
             "User-declared canonical: %s" % (result.get("user_canonical") or "not reported"),
             "Last crawl: %s" % (result.get("last_crawl_time") or "not reported"),
             "Robots: %s" % (result.get("robots_txt_state") or "not reported")],
            severity="high", confidence="medium", scope="page", entity=result["url"],
            caveat="URL Inspection reports index status at the moment of the call. It does not "
                   "describe the 30-day period and cannot, on its own, explain the trend.",
        ))

    return out


def describe_row_change(r):
    """One clause naming what actually moved for a row."""
    kind = classify_loss(r) if (r.get("clicks_change") or 0) < 0 else None
    if kind == "ranking":
        return "driven by position moving from %s to %s" % (
            fmt_pos(r["previous_position"]), fmt_pos(r["position"]))
    if kind == "visibility":
        return "driven by impressions falling %s" % fmt_pct_change(r["impressions_change_pct"])
    if kind == "ctr":
        return "driven by CTR falling %s with impressions broadly held" % fmt_delta(
            r["ctr_change_points"], "rate")
    if (r.get("clicks_change") or 0) > 0 and (r.get("position_change") or 0) < -MATERIAL_POSITION:
        return "alongside position improving from %s to %s" % (
            fmt_pos(r["previous_position"]), fmt_pos(r["position"]))
    if (r.get("clicks_change") or 0) > 0 and (r.get("impressions_change") or 0) > 0:
        return "alongside impressions rising %s" % fmt_pct_change(r["impressions_change_pct"])
    return "with impressions %s and position %s" % (
        fmt_delta(r["impressions_change"], "int"), fmt_delta(r["position_change"], "position"))


def fmt_metric(kpi, value):
    if value is None:
        return "not available"
    if kpi["unit"] == "int":
        return fmt_int(value)
    if kpi["unit"] == "rate":
        return fmt_rate(value)
    if kpi["unit"] == "position":
        return fmt_pos(value)
    return "%.2f" % value


# ---------------------------------------------------------------------------
# Recommendations
#
# Derived from findings, never from a template. An analysis with nothing wrong
# produces no recommendations, and that is a legitimate report -- inventing
# three so the section is not empty is the failure this design exists to
# prevent.
# ---------------------------------------------------------------------------

def build_recommendations(a):
    out = []
    f = a["findings"]
    by_id = {x["id"]: x for group in f.values() for x in group}
    queries = a.get("queries") or {}
    pages = a.get("pages") or {}

    def add(action, reason, evidence, impact, priority, confidence, from_finding):
        out.append({
            "action": action, "reason": reason, "evidence": evidence,
            "expected_impact": impact, "priority": priority, "confidence": confidence,
            "from_finding": from_finding,
        })

    # -- page CTR opportunities: the most specific action available ---------
    for r in (pages.get("ctr_opportunities") or [])[:3]:
        if r.get("ceiling_is_speculative"):
            impact = (
                "The property's own band median implies up to %s more clicks per 30 days at "
                "today's impressions -- an upper bound worth treating sceptically, since it is "
                "%s times the page's current clicks. Confirm query by query which searches "
                "those impressions come from before committing to a number. Either way this is "
                "a presentation change and does not move rankings."
                % (fmt_int(r["clicks_at_band_median"]), r.get("ceiling_ratio"))
            )
            priority, confidence = "Medium", "low"
        else:
            impact = (
                "Reaching the property's own band median at today's impression volume is worth "
                "about %s additional clicks per 30 days. That is a ceiling computed from "
                "current impressions, not a forecast, and it does not change rankings."
                % fmt_int(r["clicks_at_band_median"])
            )
            priority = "High" if (r["clicks_at_band_median"] or 0) >= 50 else "Medium"
            confidence = "medium"
        add(
            "Rewrite the title tag and meta description for %s, then re-check CTR after two to "
            "four weeks of finalised data." % (r.get("path") or r.get("page")),
            "The page holds %s impressions at average position %s but converts them at %s, "
            "against a median of %s for this property's own pages in the same position band."
            % (fmt_int(r["impressions"]), fmt_pos(r["position"]), fmt_rate(r["ctr"]),
               fmt_rate(r["band_median_ctr"])),
            [r["basis"]],
            impact, priority, confidence, "page_ctr_opportunities",
        )

    for r in (queries.get("ctr_opportunities") or [])[:2]:
        page_hint = ""
        owner = (a.get("query_page") or {}).get("owners", {}).get(r["query"])
        if owner:
            page_hint = " The page currently ranking for it is %s." % short_url(owner)
        add(
            "Review how %s is presented in search results -- the ranking page's title, "
            "description and snippet eligibility for that query.%s"
            % ('"%s"' % r["query"], page_hint),
            "The query returns %s impressions at average position %s with a CTR of %s, against "
            "%s for this property's own rows at the same positions."
            % (fmt_int(r["impressions"]), fmt_pos(r["position"]), fmt_rate(r["ctr"]),
               fmt_rate(r["band_median_ctr"])),
            [r["basis"]],
            "Worth roughly %s clicks a period at the property's own band median. Presentation "
            "only -- this does not move position." % fmt_int(r["clicks_at_band_median"]),
            "Medium", "medium", "query_ctr_opportunities",
        )

    # -- ranking opportunities ---------------------------------------------
    for r in (queries.get("ranking_opportunities") or [])[:3]:
        owner = (a.get("query_page") or {}).get("owners", {}).get(r["query"])
        where = " Currently answered by %s." % short_url(owner) if owner else ""
        add(
            "Strengthen the page targeting %s -- depth, internal links from related pages, and "
            "direct coverage of the query's intent.%s" % ('"%s"' % r["query"], where),
            "It draws %s impressions at average position %s, close enough that a small ranking "
            "gain produces a disproportionate click gain."
            % (fmt_int(r["impressions"]), fmt_pos(r["position"])),
            [r["basis"]],
            "Moving from the %s band toward the top of page one is where most of the click "
            "volume for this query sits. Ranking work is slower and less certain than "
            "presentation work; treat this as a quarter, not a fortnight." % r["band"],
            "Medium", "low" if r["band"] == "11-20" else "medium",
            "query_ranking_opportunities",
        )

    # -- losses -------------------------------------------------------------
    losers = pages.get("losers") or []
    if losers:
        worst = losers[0]
        kinds = {}
        for r in losers[:5]:
            kinds[classify_loss(r)] = kinds.get(classify_loss(r), 0) + 1
        dominant_kind = max(kinds, key=kinds.get) if kinds else "unclear"
        action_by_kind = {
            "ranking": "Audit the SERP for the queries these pages used to rank for, compare "
                       "the pages now ranking above them, and identify what changed on the page "
                       "or in the competitive set",
            "visibility": "Check indexing and crawl status for these pages, then review whether "
                          "the queries they matched are still being triggered at all",
            "ctr": "Review how these pages appear in search results -- title, description, and "
                   "whether a SERP feature is now taking the click",
            "mixed": "Break the loss down query by query for these pages before choosing a fix",
            "unclear": "Review these pages query by query to establish what actually moved",
        }
        add(
            "%s, starting with %s." % (
                action_by_kind[dominant_kind], worst.get("path") or worst.get("page")),
            "The largest page-level losses are dominated by %s change, not by a single uniform "
            "cause." % dominant_kind,
            ["%s: %s clicks (%s), impressions %s, position %s -> %s [%s]" % (
                r.get("path") or r.get("page"), fmt_delta(r["clicks_change"], "int"),
                fmt_pct_change(r["clicks_change_pct"]), fmt_delta(r["impressions_change"], "int"),
                fmt_pos(r["previous_position"]), fmt_pos(r["position"]), classify_loss(r))
             for r in losers[:5]],
            "Recovering the top five declining pages to their previous click volume would "
            "return about %s clicks a period." % fmt_int(
                abs(sum(r["clicks_change"] or 0 for r in losers[:5]))),
            "High", "medium", "page_losses",
        )

    # -- indexing -----------------------------------------------------------
    for finding_item in f.get("risks", []):
        if finding_item["type"] != "indexing":
            continue
        add(
            "Investigate the indexing state of %s in Search Console's URL Inspection, and "
            "confirm whether the Google-selected canonical is the intended URL."
            % finding_item["entity"],
            finding_item["statement"],
            finding_item["evidence"],
            "If the page is not indexed as intended, no amount of content or ranking work on it "
            "will produce impressions. This is a prerequisite, not an optimisation.",
            "High", "medium", finding_item["id"],
        )

    # -- CTR at property level ---------------------------------------------
    if "ctr_down_position_stable" in by_id:
        add(
            "Audit the search-result presentation of the top ten pages by impressions -- titles, "
            "descriptions, and whether a SERP feature now sits above them.",
            "Property CTR fell while average position held, so the loss is in what happens on "
            "the results page rather than in where the site ranks.",
            [e for e in by_id["ctr_down_position_stable"]["evidence"]],
            "Restoring the previous CTR at today's impression volume would return about %s "
            "clicks a period." % fmt_int(
                abs((a["kpis_by_key"]["impressions"]["current"] or 0)
                    * (a["kpis_by_key"]["ctr"]["absolute_change"] or 0) / 100.0)),
            "High", "medium", "ctr_down_position_stable",
        )

    # -- data quality that blocks conclusions -------------------------------
    for w in a["data_quality"]["warnings"]:
        if "cap" in w.lower() or "truncat" in w.lower():
            add(
                "Re-run the extract with --chunk-days 7 before drawing query-level conclusions "
                "for this property.",
                "A dataset hit the API row cap, so the query and page lists are a partial view.",
                [w],
                "A complete extract changes which rows appear in the movers and opportunity "
                "lists. The property-level KPIs are unaffected.",
                "Medium", "high", "data_quality",
            )
            break

    order = {"High": 0, "Medium": 1, "Low": 2}
    out.sort(key=lambda r: order.get(r["priority"], 3))
    return out


# ---------------------------------------------------------------------------
# Data quality
# ---------------------------------------------------------------------------

def build_data_quality(raw, a):
    checks = []
    warnings = list(raw.get("warnings") or [])
    errors = list(raw.get("errors") or [])
    unavailable = []
    insufficient = []

    def check(name, status, detail):
        checks.append({"check": name, "status": status, "detail": detail})

    # -- periods ------------------------------------------------------------
    p = a["periods"]
    check("reporting periods stated", "pass",
          "Current %s to %s; comparison %s to %s." % (
              p["current"]["start"], p["current"]["end"],
              p["previous"]["start"], p["previous"]["end"]))
    if not p.get("comparable", True):
        check("equal-length periods", "fail",
              "The windows are %d and %d days. Totals are not comparable."
              % (p["current"]["days"], p["previous"]["days"]))
        warnings.append(
            "The two periods are different lengths (%d vs %d days), so absolute totals and "
            "percentage changes between them are not like-for-like."
            % (p["current"]["days"], p["previous"]["days"]))
    else:
        check("equal-length periods", "pass",
              "Both windows are %d days." % p["current"]["days"])

    fresh = a.get("freshness")
    if fresh and fresh.get("latest_final"):
        check("finalised data only", "pass" if a["data_state"] == "final" else "warn",
              "Latest finalised date %s, %s days behind the run date. dataState=%s."
              % (fresh["latest_final"], fresh.get("lag_days"), a["data_state"]))
        if fresh.get("fresh_days_available"):
            check("fresh data excluded", "pass",
                  "%d more recent day(s) exist but are provisional and were excluded."
                  % fresh["fresh_days_available"])
    else:
        check("finalised data only", "warn",
              "The latest finalised date was not established for this run.")

    # -- property -----------------------------------------------------------
    check("property access", "pass",
          "%s (%s property, permission %s)." % (
              a["property"]["site_url"], a["property"]["property_type"],
              a["property"].get("permission_level")))

    # -- retrieval completeness --------------------------------------------
    for dataset in ("totals", "daily", "queries", "pages"):
        meta = meta_of(raw, dataset, "current")
        if not meta:
            check("%s retrieved" % dataset, "fail", "Dataset missing from the retrieval.")
            unavailable.append(dataset)
            continue
        if meta.get("truncated"):
            check("%s complete" % dataset, "warn",
                  "Hit the row cap at %s rows; this is a partial view."
                  % fmt_int(meta.get("rows_returned")))
        else:
            check("%s complete" % dataset, "pass",
                  "%s rows over %s request(s)." % (
                      fmt_int(meta.get("rows_returned")), meta.get("pages_fetched")))

    for err in errors:
        unavailable.append(err.get("dataset"))
        warnings.append(
            "%s could not be retrieved (%s). That section is unavailable, not empty."
            % (err.get("dataset"), (err.get("message") or "")[:160]))

    # -- dimensional vs property totals -------------------------------------
    for label, node in (("query", a.get("queries")), ("page", a.get("pages"))):
        recon = (node or {}).get("reconciliation")
        if not recon or recon.get("coverage_pct") is None:
            continue
        cov = recon["coverage_pct"]
        status = "pass" if cov >= 80 else ("warn" if cov >= 50 else "fail")
        check("%s coverage of property clicks" % label, status,
              "%s-level rows account for %.0f%% of property clicks (%s of %s)." % (
                  label, cov, fmt_int(recon["dimension_clicks"]),
                  fmt_int(recon["property_clicks"])))
        if cov < 80:
            warnings.append(
                "%s-level data covers %.0f%% of the property's clicks. Search Console withholds "
                "rows -- anonymised queries in particular -- so %s totals are always lower than "
                "property totals and the gap is not missing traffic."
                % (label.capitalize(), cov, label))

    # -- sample size --------------------------------------------------------
    clicks = a["kpis_by_key"]["clicks"]
    if (clicks.get("current") or 0) < SMALL_SAMPLE_CLICKS:
        insufficient.append({
            "scope": "property",
            "detail": "Only %s clicks in the current period. Percentage changes on this volume "
                      "swing on a handful of visits; conclusions are marked low confidence."
                      % fmt_int(clicks.get("current")),
        })
        check("sample size", "warn",
              "%s clicks in the current period, below the %d-click bar for confident "
              "period-over-period conclusions." % (fmt_int(clicks.get("current")),
                                                   SMALL_SAMPLE_CLICKS))
    else:
        check("sample size", "pass",
              "%s clicks in the current period." % fmt_int(clicks.get("current")))

    # -- zero baseline ------------------------------------------------------
    for kpi in a["kpis"]:
        if kpi["verdict"] == "new":
            warnings.append(
                "%s had no comparison-period value, so no percentage change exists for it. The "
                "absolute figure is reported instead." % kpi["label"])
        if kpi["availability"] != "available" and kpi["verdict"] != "new":
            unavailable.append(kpi["key"])
            warnings.append(
                "%s is %s for this period and must not be reported as zero."
                % (kpi["label"], kpi["availability"]))
        if kpi["availability"] == "partial" and kpi["current"] is None:
            unavailable.append(kpi["key"])
            warnings.append(
                "%s has no current-period value. Report it as not available, never as zero."
                % kpi["label"])

    # -- brand classification ----------------------------------------------
    if a.get("brand") is None:
        check("branded/non-branded split", "skipped",
              "No brand terms configured (GSC_BRAND_TERMS), so no branded/non-branded "
              "classification was attempted. Guessing which queries are branded would put an "
              "assumption into every figure derived from it.")

    # -- search appearance --------------------------------------------------
    if not (a.get("search_appearance") or {}).get("rows"):
        check("search appearance", "skipped",
              "No search appearance data returned. Many properties return none; this is not a "
              "fault in the site.")

    # -- standing limitations ----------------------------------------------
    limitations = [
        "Search Console reports organic search visibility and clicks. Clicks are not sessions, "
        "impressions are not visits, and neither reconciles to GA4 by design.",
        "Query-level and page-level exports omit rows, so their totals are lower than the "
        "property totals in the KPI table. The property figures are the ones to quote.",
        "Average position is an impression-weighted average across every query the property "
        "appeared for. It is not a fixed keyword rank and moves when the query mix changes.",
        "Search Console retains roughly 16 months of Search Analytics data.",
        "%s data only. Other search surfaces are separate datasets and are never added into "
        "these totals." % a["search_type"].capitalize(),
    ]
    if (a.get("url_inspection") or {}).get("results"):
        limitations.append(
            "URL Inspection results describe index status at the moment of the call, not the "
            "reporting period.")

    return {
        "checks": checks,
        "warnings": sorted(set(warnings), key=warnings.index) if warnings else [],
        "errors": errors,
        "unavailable": sorted(set(x for x in unavailable if x)),
        "insufficient_data": insufficient,
        "limitations": limitations,
        "blocking": [c for c in checks if c["status"] == "fail"],
    }


# ---------------------------------------------------------------------------
# Dimension analysis blocks
# ---------------------------------------------------------------------------

def analyse_dimension(raw, dataset, key_field, key_label, property_totals, floor,
                      shorten=False):
    """The full treatment for one dimension: join, rank, find opportunities, and
    reconcile against the property totals."""
    cur = rows_of(raw, dataset, "current")
    prev = rows_of(raw, dataset, "previous")
    if cur is None:
        return None

    joined = join_dimension(cur, prev, key_field)
    records = [clean(r, key_label, shorten=shorten) for r in joined]

    benchmarks = ctr_benchmarks(records)
    click_floor = max(MATERIAL_CLICKS_FLOOR, int((property_totals.get("clicks") or 0) * 0.005))

    by_clicks = sorted(records, key=lambda r: r.get("clicks") or 0, reverse=True)
    by_impressions = sorted(records, key=lambda r: r.get("impressions") or 0, reverse=True)

    dim_totals = dimension_totals(cur)
    recon = None
    if dim_totals and property_totals.get("clicks") is not None:
        recon = {
            "dimension_clicks": rnd(dim_totals["clicks"], 0),
            "property_clicks": rnd(property_totals["clicks"], 0),
            "dimension_impressions": rnd(dim_totals["impressions"], 0),
            "property_impressions": rnd(property_totals["impressions"], 0),
            "coverage_pct": rnd(
                gsc.safe_div(dim_totals["clicks"], property_totals["clicks"]) * 100.0
                if property_totals["clicks"] else None, 1),
            "rows": dim_totals["rows"],
            "note": (
                "Search Console withholds rows from dimensional exports, so this total is a "
                "floor rather than the property's traffic. The KPI table figures come from the "
                "dimensionless query and are the ones to quote."
            ),
        }

    return {
        "rows_analysed": len(records),
        "meta": {
            "current": meta_of(raw, dataset, "current"),
            "previous": meta_of(raw, dataset, "previous"),
        },
        "reconciliation": recon,
        "ctr_benchmarks": benchmarks,
        "impression_floor": floor,
        "click_floor": click_floor,
        "top_by_clicks": by_clicks[:TOP_N],
        "top_by_impressions": by_impressions[:TOP_N],
        "winners": movers(records, "gain", click_floor),
        "losers": movers(records, "loss", click_floor),
        "ctr_opportunities": ctr_opportunities(records, benchmarks, floor),
        "ranking_opportunities": ranking_opportunities(records, floor),
        "visibility_losses": visibility_losses(records, floor),
        "loss_concentration": concentration(records, key_label, "loss"),
        "gain_concentration": concentration(records, key_label, "gain"),
        "all_records_count": len(records),
    }


def analyse_devices(raw):
    cur = rows_of(raw, "devices", "current")
    if cur is None:
        return None
    joined = join_dimension(cur, rows_of(raw, "devices", "previous"), "device")
    rows = [clean(r, "device") for r in joined]
    total_clicks = sum(r["clicks"] or 0 for r in rows)
    total_imps = sum(r["impressions"] or 0 for r in rows)
    for r in rows:
        r["share_of_clicks_pct"] = rnd(
            (r["clicks"] / total_clicks * 100.0) if total_clicks and r["clicks"] else None, 1)
        r["share_of_impressions_pct"] = rnd(
            (r["impressions"] / total_imps * 100.0) if total_imps and r["impressions"] else None, 1)
        # Tablet is usually a rounding error. Flagging it once here stops a
        # downstream reader building a paragraph on forty clicks.
        r["negligible"] = bool(
            r["share_of_clicks_pct"] is not None and r["share_of_clicks_pct"] < 3)
    rows.sort(key=lambda r: r["clicks"] or 0, reverse=True)
    return {"rows": rows, "total_clicks": total_clicks, "total_impressions": total_imps}


def analyse_countries(raw):
    cur = rows_of(raw, "countries", "current")
    if cur is None:
        return None
    joined = join_dimension(cur, rows_of(raw, "countries", "previous"), "country")
    rows = [clean(r, "country") for r in joined]
    total_clicks = sum(r["clicks"] or 0 for r in rows)
    for r in rows:
        r["share_of_clicks_pct"] = rnd(
            (r["clicks"] / total_clicks * 100.0) if total_clicks and r["clicks"] else None, 1)
    rows.sort(key=lambda r: r["clicks"] or 0, reverse=True)

    # Geography is only worth a section when the property is not effectively
    # single-market. One country holding 90%+ of clicks is a fact for the data
    # notes, not a chapter.
    top_share = rows[0]["share_of_clicks_pct"] if rows else None
    material = bool(rows and (top_share is None or top_share < 85 or len([
        r for r in rows if (r["share_of_clicks_pct"] or 0) >= 5]) > 1))
    movers_here = [r for r in rows[:10]
                   if r.get("clicks_change") is not None
                   and abs(r["clicks_change"]) >= max(MATERIAL_CLICKS_FLOOR, total_clicks * 0.02)]
    return {
        "rows": rows[:TOP_N],
        "countries_with_data": len(rows),
        "top_country_share_pct": top_share,
        "material": material or bool(movers_here),
        "movers": movers_here[:5],
        "note": (
            "Geography is reported only where it changes the picture. A property whose traffic "
            "is one market does not need a country section."
        ),
    }


def analyse_search_appearance(raw):
    cur = rows_of(raw, "search_appearance", "current")
    if cur is None:
        return None
    joined = join_dimension(cur, rows_of(raw, "search_appearance", "previous"),
                            "searchAppearance")
    rows = [clean(r, "search_appearance") for r in joined]
    rows.sort(key=lambda r: r["impressions"] or 0, reverse=True)
    return {
        "rows": rows[:TOP_N],
        "note": (
            "Search appearance is a separate query because the dimension cannot be combined "
            "with any other. Its rows describe result features, and they overlap -- they do not "
            "sum to the property total."
        ),
    }


def analyse_query_page(raw, floor):
    node = ((raw.get("datasets") or {}).get("query_page") or {}).get("current")
    if not node:
        return None
    rows = node.get("rows") or []
    owners = {}
    for r in sorted(rows, key=lambda r: r.get("impressions") or 0, reverse=True):
        q = r.get("query")
        if q and q not in owners:
            owners[q] = r.get("page")
    return {
        "rows_analysed": len(rows),
        "meta": node.get("meta") or {},
        "owners": owners,
        "cannibalisation": cannibalisation(rows, floor),
        "note": (
            "Requesting query and page together makes Search Console withhold more rows than "
            "either dimension alone. Use it to see which page answers which query, not to total "
            "anything."
        ),
    }


def analyse_extra_search_types(raw):
    out = {}
    for st, node in (raw.get("extra_search_types") or {}).items():
        totals = node.get("totals") or {}
        cur = totals_from((totals.get("current") or {}).get("rows"))
        prev = totals_from((totals.get("previous") or {}).get("rows"))
        out[st] = {
            "search_type": st,
            "supports_query_dimension": node.get("supports_query_dimension"),
            "kpis": [
                change_record("clicks", "Clicks", "int", "higher",
                              cur["clicks"], prev["clicks"], MATERIAL_CLICKS_FLOOR),
                change_record("impressions", "Impressions", "int", "higher",
                              cur["impressions"], prev["impressions"],
                              MATERIAL_IMPRESSIONS_FLOOR),
                change_record("ctr", "CTR", "rate", "higher",
                              cur["ctr"], prev["ctr"], MATERIAL_CTR_POINTS),
                change_record("average_position", "Average position", "position", "lower",
                              cur["position"], prev["position"], MATERIAL_POSITION),
            ],
            "note": (
                "A separate Search Console surface, reported on its own. These figures are NOT "
                "part of the %s totals in the KPI table and must never be added to them."
                % raw.get("search_type", "web")
            ),
        }
    return out


def analyse_sitemaps(raw):
    node = (raw.get("datasets") or {}).get("sitemaps")
    if not node:
        return None
    entries = node.get("entries") or []
    problems = []
    for s in entries:
        if s.get("errors"):
            problems.append("%s reports %d error(s)." % (s["path"], s["errors"]))
        if s.get("is_pending"):
            problems.append("%s is still pending processing." % s["path"])
        if s.get("last_downloaded") is None and not s.get("is_pending"):
            problems.append("%s has never been downloaded by Google." % s["path"])
        if s.get("submitted") and s.get("indexed") is not None and s["submitted"] > 0:
            ratio = s["indexed"] / s["submitted"]
            if ratio < 0.5:
                problems.append(
                    "%s: %s of %s submitted URLs are reported indexed."
                    % (s["path"], fmt_int(s["indexed"]), fmt_int(s["submitted"])))
    return {
        "sitemaps": entries,
        "problems": problems,
        "note": (
            "Sitemap status is supplementary. It is included here because a submitted sitemap "
            "erroring is cheap to see and expensive to miss -- not as a technical SEO audit."
        ),
    }


# ---------------------------------------------------------------------------
# build()
# ---------------------------------------------------------------------------

def build(raw):
    """Raw retrieval -> the output contract."""
    property_info = raw.get("property") or {}
    periods = raw.get("periods") or {}

    cur_totals = totals_from(rows_of(raw, "totals", "current"))
    prev_totals = totals_from(rows_of(raw, "totals", "previous"))

    kpis = [
        change_record("clicks", "Clicks", "int", "higher",
                      cur_totals["clicks"], prev_totals["clicks"], MATERIAL_CLICKS_FLOOR),
        change_record("impressions", "Impressions", "int", "higher",
                      cur_totals["impressions"], prev_totals["impressions"],
                      MATERIAL_IMPRESSIONS_FLOOR),
        change_record(
            "ctr", "CTR", "rate", "higher", cur_totals["ctr"], prev_totals["ctr"],
            MATERIAL_CTR_POINTS,
            notes=["Reported in percentage points. The absolute change is the movement in "
                   "points; the percentage change is that movement relative to the previous "
                   "rate -- a CTR going from 2.0% to 2.4% is +0.4 points and +20% relative."],
        ),
        change_record(
            "average_position", "Average position", "position", "lower",
            cur_totals["position"], prev_totals["position"], MATERIAL_POSITION,
            notes=["Lower is better: a fall in this number is an improvement. It is an "
                   "impression-weighted average across every query the property appeared for, "
                   "not a fixed keyword rank."],
        ),
    ]
    kpis_by_key = {k["key"]: k for k in kpis}

    floor = opportunity_floor(cur_totals.get("impressions"))

    a = {
        "schema": "reports-google-search-console/analysis@1",
        "generated_at": datetime.now().astimezone().isoformat(timespec="seconds"),
        "source_raw_file": raw.get("_source_path"),
        "property": {
            "site_url": property_info.get("site_url"),
            "property_type": property_info.get("property_type"),
            "display": property_info.get("display"),
            "permission_level": property_info.get("permission_level"),
            "access": property_info.get("access", "ok"),
        },
        "client": raw.get("client") or {},
        "search_type": raw.get("search_type", "web"),
        "data_state": raw.get("data_state", "final"),
        "freshness": raw.get("freshness"),
        "periods": periods,
        "kpis": kpis,
        "kpis_by_key": kpis_by_key,
        "trend": build_trend(raw),
    }

    a["click_attribution"] = decompose_clicks(kpis_by_key)
    a["queries"] = analyse_dimension(raw, "queries", "query", "query", cur_totals, floor)
    a["pages"] = analyse_dimension(raw, "pages", "page", "page", cur_totals, floor, shorten=True)
    a["query_page"] = analyse_query_page(raw, floor)
    a["devices"] = analyse_devices(raw)
    a["countries"] = analyse_countries(raw)
    a["search_appearance"] = analyse_search_appearance(raw)
    a["extra_search_types"] = analyse_extra_search_types(raw)
    a["sitemaps"] = analyse_sitemaps(raw)

    inspection = (raw.get("datasets") or {}).get("url_inspection")
    a["url_inspection"] = inspection or None

    brand_terms = ((raw.get("settings") or {}).get("brand_terms")) or []
    query_records = (a["queries"] or {}).get("top_by_impressions") or []
    all_query_records = []
    if a["queries"]:
        cur_rows = rows_of(raw, "queries", "current")
        prev_rows = rows_of(raw, "queries", "previous")
        all_query_records = [clean(r, "query")
                             for r in join_dimension(cur_rows, prev_rows, "query")]
    a["brand"] = brand_split(all_query_records, brand_terms)
    if a["brand"] is None:
        a["brand_note"] = (
            "No brand terms are configured for this property, so no branded/non-branded split "
            "was produced. Set GSC_BRAND_TERMS in the client .env -- including abbreviations, "
            "misspellings and domain variants -- to enable it. Inferring which queries are "
            "branded from the query text alone would be a guess that every derived figure "
            "inherits."
        )

    a["thresholds"] = {
        "material_percent": MATERIAL_PCT,
        "material_clicks_floor": MATERIAL_CLICKS_FLOOR,
        "material_impressions_floor": MATERIAL_IMPRESSIONS_FLOOR,
        "material_ctr_points": MATERIAL_CTR_POINTS,
        "material_position": MATERIAL_POSITION,
        "small_sample_clicks": SMALL_SAMPLE_CLICKS,
        "opportunity_impression_floor": floor,
        "opportunity_impression_basis": (
            "max(%d, %.2f%% of the property's %s current-period impressions)"
            % (OPPORTUNITY_IMPRESSION_FLOOR, OPPORTUNITY_IMPRESSION_SHARE * 100,
               fmt_int(cur_totals.get("impressions")))
        ),
        "position_bands": [b[0] for b in BANDS],
        "ctr_benchmark": (
            "This property's own median CTR per position band, requiring at least %d rows in "
            "the band. No industry benchmark is used or implied." % CTR_BENCHMARK_MIN_ROWS
        ),
    }

    a["findings"] = build_findings(a)
    a["data_quality"] = build_data_quality(raw, a)
    a["recommended_actions"] = build_recommendations(a)
    a["tables"] = build_tables(a)
    a["charts"] = []
    return a


# ---------------------------------------------------------------------------
# Pre-rendered Markdown tables
#
# Rendered once, here, so no figure is retyped into a report. A retyped number
# is a chance to mistype one.
# ---------------------------------------------------------------------------

def build_tables(a):
    tables = {}
    p = a["periods"]
    n_cur, n_prev = p["current"]["days"], p["previous"]["days"]

    rows = ["| KPI | Current %d days | Previous %d days | Absolute change | %% change |"
            % (n_cur, n_prev),
            "|---|---:|---:|---:|---:|"]
    for k in a["kpis"]:
        if k["availability"] == "unavailable":
            rows.append("| %s | not available | not available | — | — |" % k["label"])
            continue
        cur = fmt_metric(k, k["current"])
        prev = fmt_metric(k, k["previous"])
        delta = fmt_delta(k["absolute_change"], k["unit"])
        pctc = ("n/a (previous period was zero)" if k["verdict"] == "new"
                else fmt_pct_change(k["percent_change"]))
        label = k["label"]
        if k["key"] == "average_position":
            label += " *(lower is better)*"
        rows.append("| %s | %s | %s | %s | %s |" % (label, cur, prev, delta, pctc))
    tables["kpi"] = "\n".join(rows)

    def movers_table(records, key_label, title_key, limit=DETAIL_N):
        if not records:
            return None
        head = ["| %s | Clicks | Δ Clicks | Impressions | Δ Impressions | CTR | Position | Δ Pos |"
                % title_key,
                "|---|---:|---:|---:|---:|---:|---:|---:|"]
        for r in records[:limit]:
            head.append("| %s | %s | %s | %s | %s | %s | %s | %s |" % (
                truncate(r.get("path") or r.get(key_label), 52),
                fmt_int(r["clicks"]), fmt_delta(r["clicks_change"], "int"),
                fmt_int(r["impressions"]), fmt_delta(r["impressions_change"], "int"),
                fmt_rate(r["ctr"]), fmt_pos(r["position"]),
                fmt_delta(r["position_change"], "position")))
        return "\n".join(head)

    q, pg = a.get("queries") or {}, a.get("pages") or {}
    tables["top_queries"] = movers_table(q.get("top_by_clicks"), "query", "Query", TOP_N)
    tables["query_winners"] = movers_table(q.get("winners"), "query", "Query")
    tables["query_losers"] = movers_table(q.get("losers"), "query", "Query")
    tables["top_pages"] = movers_table(pg.get("top_by_clicks"), "page", "Page", TOP_N)
    tables["page_winners"] = movers_table(pg.get("winners"), "page", "Page")
    tables["page_losers"] = movers_table(pg.get("losers"), "page", "Page")

    def opportunity_table(records, key_label, title_key, kind):
        if not records:
            return None
        if kind == "ctr":
            head = ["| %s | Impressions | Position | CTR | Band median CTR | Clicks at band median |"
                    % title_key,
                    "|---|---:|---:|---:|---:|---:|"]
            for r in records:
                head.append("| %s | %s | %s | %s | %s | %s |" % (
                    truncate(r.get("path") or r.get(key_label), 52), fmt_int(r["impressions"]),
                    fmt_pos(r["position"]), fmt_rate(r["ctr"]), fmt_rate(r["band_median_ctr"]),
                    fmt_int(r["clicks_at_band_median"])))
        else:
            head = ["| %s | Impressions | Position | Δ Position | CTR | Clicks | Band |"
                    % title_key,
                    "|---|---:|---:|---:|---:|---:|---|"]
            for r in records:
                head.append("| %s | %s | %s | %s | %s | %s | %s |" % (
                    truncate(r.get("path") or r.get(key_label), 52), fmt_int(r["impressions"]),
                    fmt_pos(r["position"]), fmt_delta(r["position_change"], "position"),
                    fmt_rate(r["ctr"]), fmt_int(r["clicks"]), r["band"]))
        return "\n".join(head)

    tables["query_ctr_opportunities"] = opportunity_table(
        q.get("ctr_opportunities"), "query", "Query", "ctr")
    tables["page_ctr_opportunities"] = opportunity_table(
        pg.get("ctr_opportunities"), "page", "Page", "ctr")
    tables["query_ranking_opportunities"] = opportunity_table(
        q.get("ranking_opportunities"), "query", "Query", "ranking")
    tables["page_ranking_opportunities"] = opportunity_table(
        pg.get("ranking_opportunities"), "page", "Page", "ranking")

    devices = a.get("devices")
    if devices and devices.get("rows"):
        rows = ["| Device | Clicks | Δ Clicks | Impressions | Δ Impressions | CTR | Δ CTR | Position | Δ Pos |",
                "|---|---:|---:|---:|---:|---:|---:|---:|---:|"]
        for r in devices["rows"]:
            rows.append("| %s | %s | %s | %s | %s | %s | %s | %s | %s |" % (
                str(r["device"]).capitalize(), fmt_int(r["clicks"]),
                fmt_delta(r["clicks_change"], "int"), fmt_int(r["impressions"]),
                fmt_delta(r["impressions_change"], "int"), fmt_rate(r["ctr"]),
                fmt_delta(r["ctr_change_points"], "rate"), fmt_pos(r["position"]),
                fmt_delta(r["position_change"], "position")))
        tables["devices"] = "\n".join(rows)

    countries = a.get("countries")
    if countries and countries.get("rows"):
        rows = ["| Country | Clicks | Δ Clicks | Share of clicks | Impressions | CTR | Position |",
                "|---|---:|---:|---:|---:|---:|---:|"]
        for r in countries["rows"][:DETAIL_N]:
            rows.append("| %s | %s | %s | %s | %s | %s | %s |" % (
                str(r["country"]).upper(), fmt_int(r["clicks"]),
                fmt_delta(r["clicks_change"], "int"),
                fmt_rate(r.get("share_of_clicks_pct"), 1), fmt_int(r["impressions"]),
                fmt_rate(r["ctr"]), fmt_pos(r["position"])))
        tables["countries"] = "\n".join(rows)

    appearance = a.get("search_appearance")
    if appearance and appearance.get("rows"):
        rows = ["| Search appearance | Clicks | Δ Clicks | Impressions | Δ Impressions | CTR | Position |",
                "|---|---:|---:|---:|---:|---:|---:|"]
        for r in appearance["rows"]:
            rows.append("| %s | %s | %s | %s | %s | %s | %s |" % (
                r["search_appearance"], fmt_int(r["clicks"]),
                fmt_delta(r["clicks_change"], "int"), fmt_int(r["impressions"]),
                fmt_delta(r["impressions_change"], "int"), fmt_rate(r["ctr"]),
                fmt_pos(r["position"])))
        tables["search_appearance"] = "\n".join(rows)

    brand = a.get("brand")
    if brand:
        rows = ["| Segment | Queries | Clicks | Δ Clicks | Impressions | CTR |",
                "|---|---:|---:|---:|---:|---:|"]
        for side in (brand["branded"], brand["non_branded"]):
            rows.append("| %s | %s | %s | %s | %s | %s |" % (
                side["label"].capitalize(), fmt_int(side["queries"]), fmt_int(side["clicks"]),
                fmt_delta(side["clicks_change"], "int"), fmt_int(side["impressions"]),
                fmt_rate(side["ctr"])))
        tables["brand"] = "\n".join(rows)

    extra = a.get("extra_search_types") or {}
    if extra:
        rows = ["| Search type | Clicks | Δ Clicks | Impressions | Δ Impressions | CTR |",
                "|---|---:|---:|---:|---:|---:|"]
        for st, node in extra.items():
            k = {x["key"]: x for x in node["kpis"]}
            rows.append("| %s | %s | %s | %s | %s | %s |" % (
                st, fmt_metric(k["clicks"], k["clicks"]["current"]),
                fmt_delta(k["clicks"]["absolute_change"], "int"),
                fmt_metric(k["impressions"], k["impressions"]["current"]),
                fmt_delta(k["impressions"]["absolute_change"], "int"),
                fmt_metric(k["ctr"], k["ctr"]["current"])))
        tables["extra_search_types"] = "\n".join(rows)

    return tables


def render_tables_markdown(a):
    order = [
        ("KPI overview", "kpi"),
        ("Top queries by clicks", "top_queries"),
        ("Largest query gains", "query_winners"),
        ("Largest query losses", "query_losers"),
        ("Query CTR opportunities", "query_ctr_opportunities"),
        ("Query ranking opportunities", "query_ranking_opportunities"),
        ("Top pages by clicks", "top_pages"),
        ("Largest page gains", "page_winners"),
        ("Largest page losses", "page_losers"),
        ("Page CTR opportunities", "page_ctr_opportunities"),
        ("Page ranking opportunities", "page_ranking_opportunities"),
        ("Device performance", "devices"),
        ("Country performance", "countries"),
        ("Search appearance", "search_appearance"),
        ("Branded vs non-branded", "brand"),
        ("Other search types (separate datasets)", "extra_search_types"),
    ]
    p = a["periods"]
    out = [
        "# Pre-rendered tables",
        "",
        "Property: `%s`  " % a["property"]["site_url"],
        "Current period: %s to %s (%d days)  " % (
            p["current"]["start"], p["current"]["end"], p["current"]["days"]),
        "Comparison period: %s to %s (%d days)  " % (
            p["previous"]["start"], p["previous"]["end"], p["previous"]["days"]),
        "Search type: %s · data state: %s" % (a["search_type"], a["data_state"]),
        "",
        "Paste these rather than retyping figures.",
        "",
    ]
    for title, key in order:
        table = (a.get("tables") or {}).get(key)
        if not table:
            continue
        out += ["## %s" % title, "", table, ""]
    return "\n".join(out)


# ---------------------------------------------------------------------------
# CLI
# ---------------------------------------------------------------------------

def main():
    ap = argparse.ArgumentParser(description="Analyse a Search Console retrieval.")
    ap.add_argument("--raw", required=True, help="Path to a *_raw.json from fetch_search_console.py")
    ap.add_argument("--out", help="Output directory (default: alongside the raw file)")
    ap.add_argument("--quiet", action="store_true", help="Write files, print nothing but paths")
    args = ap.parse_args()

    raw_path = Path(args.raw).expanduser()
    if not raw_path.is_file():
        print("No such raw file: %s" % raw_path, file=sys.stderr)
        return 2
    try:
        raw = json.loads(raw_path.read_text())
    except ValueError as exc:
        print("Raw file is not valid JSON: %s" % exc, file=sys.stderr)
        return 2
    if raw.get("schema") != "reports-google-search-console/raw@1":
        print("Unexpected schema %r -- expected reports-google-search-console/raw@1"
              % raw.get("schema"), file=sys.stderr)
        return 2

    raw["_source_path"] = str(raw_path)
    analysis = build(raw)

    out_dir = Path(args.out).expanduser() if args.out else raw_path.parent
    out_dir.mkdir(parents=True, exist_ok=True)
    stem = raw_path.name[:-len("_raw.json")] if raw_path.name.endswith("_raw.json") \
        else raw_path.stem
    analysis_path = out_dir / ("%s_analysis.json" % stem)
    tables_path = out_dir / ("%s_tables.md" % stem)
    analysis_path.write_text(json.dumps(analysis, indent=2))
    tables_path.write_text(render_tables_markdown(analysis))

    print(str(analysis_path))
    print(str(tables_path))

    if not args.quiet:
        k = analysis["kpis_by_key"]
        print("", file=sys.stderr)
        print("property: %s (%s)" % (analysis["property"]["site_url"],
                                     analysis["property"]["property_type"]), file=sys.stderr)
        print("current:  %s .. %s" % (analysis["periods"]["current"]["start"],
                                      analysis["periods"]["current"]["end"]), file=sys.stderr)
        print("previous: %s .. %s" % (analysis["periods"]["previous"]["start"],
                                      analysis["periods"]["previous"]["end"]), file=sys.stderr)
        for key in ("clicks", "impressions", "ctr", "average_position"):
            kpi = k[key]
            print("  %-18s %12s  (%s, %s) %s" % (
                kpi["label"], fmt_metric(kpi, kpi["current"]),
                fmt_delta(kpi["absolute_change"], kpi["unit"]),
                fmt_pct_change(kpi["percent_change"]), kpi["verdict"]), file=sys.stderr)
        counts = {k2: len(v) for k2, v in analysis["findings"].items() if v}
        print("findings: %s" % (counts or "none"), file=sys.stderr)
        print("recommendations: %d" % len(analysis["recommended_actions"]), file=sys.stderr)
        for w in analysis["data_quality"]["warnings"]:
            print("warning: %s" % w, file=sys.stderr)

    return 0


if __name__ == "__main__":
    sys.exit(main())
