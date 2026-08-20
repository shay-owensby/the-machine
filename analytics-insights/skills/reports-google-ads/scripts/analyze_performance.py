#!/usr/bin/env python3
"""
Turn one raw retrieval file into the structured analysis the reporting agent
consumes. Reads a file, writes a file, talks to no network.

    python3 analyze_performance.py --raw <raw.json> --out <dir>

Produces:
    <out>/<customer>_<start>_<end>_analysis.json   the output contract
    <out>/<customer>_<start>_<end>_tables.md       KPI + campaign tables, pre-rendered

Two things this file is strict about, because they are where reports go wrong:

  1. **Unavailable is not zero.** Every metric carries an availability state.
     A metric the API never returned stays None all the way through and prints
     as "not available", never as 0, 0.00%% or a dash that reads like zero.

  2. **A number is not a verdict.** Direction (up/down) is arithmetic; verdict
     (better/worse) needs to know what the metric means, and some metrics --
     spend, impressions -- have no verdict without business context. Those are
     labelled ambiguous rather than guessed at.

Percentage change against a zero or missing baseline is undefined, not infinite
and not 100%%. It is reported as undefined with the reason attached.
"""

import argparse
import datetime as dt
import json
import math
import sys
from pathlib import Path

import ads_common as ads

SCHEMA = "reports-google-ads/analysis@1"

# ---------------------------------------------------------------------------
# What "material" means. Defaults, overridable per run.
#
# A change is worth a client's attention when it is BOTH proportionally big and
# absolutely big. Ten percent of nothing is nothing, and a 2% move on a large
# account is usually noise -- reporting either as a finding trains people to
# ignore the report.
# ---------------------------------------------------------------------------

MATERIAL_PCT = 10.0          # |% change| at or above this is proportionally material
MIN_ABS = {                  # ...and the absolute change must also clear this
    "currency": 25.0,        # in account currency
    "int": 25.0,
    "rate": 0.5,             # percentage POINTS for CTR / conv-rate / share metrics
    "decimal": 0.1,          # ROAS points
}
SMALL_SAMPLE_CONVERSIONS = 30   # below this, conversion-derived metrics are noisy
SPARSE_CLICKS = 100             # below this a campaign cannot be judged on rate metrics


# key, label, unit, better_when, description
KPI_SPECS = [
    ("cost",              "Spend",                    "currency", "context",
     "Total cost. Neither direction is good or bad on its own -- it is an input."),
    ("impressions",       "Impressions",              "int",      "context",
     "Times an ad was shown. Volume, not value."),
    ("clicks",            "Clicks",                   "int",      "higher",
     "Paid interactions."),
    ("ctr",               "CTR",                      "rate",     "higher",
     "Clicks per impression. Ad and query relevance."),
    ("average_cpc",       "Avg. CPC",                 "currency", "lower",
     "Cost per click. Cheaper is better in isolation, but not when it comes from lower-intent traffic."),
    ("conversions",       "Conversions",              "decimal",  "higher",
     "Conversions attributed to ads, as counted by the account's conversion settings."),
    ("conversion_rate",   "Conversion rate",          "rate",     "higher",
     "Conversions per click."),
    ("cost_per_conversion", "CPA",                    "currency", "lower",
     "Cost per conversion."),
    ("conversions_value", "Conversion value",         "currency", "higher",
     "Value attributed to conversions. Only meaningful if the account records values."),
    ("roas",              "ROAS",                     "decimal",  "higher",
     "Conversion value per unit of spend."),
    ("search_impression_share", "Search impression share", "rate", "higher",
     "Share of available search impressions won. Impression-weighted across campaigns that report it."),
    ("search_lost_is_budget", "Search lost IS (budget)", "rate",  "lower",
     "Share of search impressions lost because budget ran out."),
    ("search_lost_is_rank",   "Search lost IS (rank)",   "rate",  "lower",
     "Share of search impressions lost to ad rank -- bid, quality, or both."),
]

KPI_BY_KEY = {k[0]: k for k in KPI_SPECS}


# ---------------------------------------------------------------------------
# Metric extraction
# ---------------------------------------------------------------------------

def totals_from_rows(rows):
    """Aggregate base metrics from a list of REST rows.

    Only base counts are summed. Every rate is derived afterwards from the
    bases, because summing an average across rows is arithmetic nonsense --
    and because a derived rate is reproducible from two numbers in the table.
    """
    if rows is None:
        return None
    out = {}
    for key, getter in (
        ("impressions", lambda r: ads.num(r, "metrics.impressions")),
        ("clicks", lambda r: ads.num(r, "metrics.clicks")),
        ("cost", lambda r: ads.micros(r, "metrics.cost_micros")),
        ("conversions", lambda r: ads.num(r, "metrics.conversions")),
        # conversions_value and all_conversions_value are plain doubles in
        # account currency -- unlike cost, they are not micros.
        ("conversions_value", lambda r: ads.num(r, "metrics.conversions_value")),
        ("all_conversions", lambda r: ads.num(r, "metrics.all_conversions")),
        ("all_conversions_value", lambda r: ads.num(r, "metrics.all_conversions_value")),
    ):
        total, hits, seen = ads.accumulate(rows, getter)
        out[key] = total
        out["_%s_rows" % key] = hits
    out["_rows"] = len(rows)
    return out


def derive(t):
    """Add the derived metrics. None in, None out -- never a fabricated zero."""
    if t is None:
        return None
    imp, clicks, cost = t.get("impressions"), t.get("clicks"), t.get("cost")
    conv, value = t.get("conversions"), t.get("conversions_value")
    t["ctr"] = pct(ads.safe_div(clicks, imp))
    t["average_cpc"] = ads.safe_div(cost, clicks)
    t["conversion_rate"] = pct(ads.safe_div(conv, clicks))
    t["cost_per_conversion"] = ads.safe_div(cost, conv)
    t["roas"] = ads.safe_div(value, cost)
    t["value_per_conversion"] = ads.safe_div(value, conv)
    return t


def pct(ratio):
    return None if ratio is None else ratio * 100.0


def share_metrics(campaign_rows):
    """Impression-weighted search impression share across campaigns that report it.

    Campaigns that do not report impression share (Performance Max, Display,
    Video, Shopping in some cases) are excluded from the weighting rather than
    counted as zero -- including them would drag the account figure down with
    data that does not exist.
    """
    if campaign_rows is None:
        return {"search_impression_share": None, "search_lost_is_budget": None,
                "search_lost_is_rank": None, "coverage": None}

    def collect(metric):
        pairs = []
        for r in campaign_rows:
            v = ads.num(r, metric)
            imp = ads.num(r, "metrics.impressions") or 0
            if v is not None:
                pairs.append((v, imp))
        return ads.weighted_mean(pairs)

    is_val, is_weight = collect("metrics.search_impression_share")
    budget_val, _ = collect("metrics.search_budget_lost_impression_share")
    rank_val, _ = collect("metrics.search_rank_lost_impression_share")
    total_imp, _, _ = ads.accumulate(campaign_rows, lambda r: ads.num(r, "metrics.impressions"))

    return {
        "search_impression_share": pct(is_val),
        "search_lost_is_budget": pct(budget_val),
        "search_lost_is_rank": pct(rank_val),
        "coverage": {
            "impressions_covered": is_weight,
            "impressions_total": total_imp,
            "share_of_impressions": (
                None if not total_imp else round(100.0 * is_weight / total_imp, 1)),
            "campaigns_reporting": sum(
                1 for r in campaign_rows
                if ads.num(r, "metrics.search_impression_share") is not None),
            "campaigns_total": len(campaign_rows),
        },
    }


# ---------------------------------------------------------------------------
# Change maths
# ---------------------------------------------------------------------------

def change(current, previous, unit, better_when, key=None, label=None,
           material_pct=MATERIAL_PCT, min_abs=None):
    """One KPI's full comparison record."""
    spec_min = (min_abs or MIN_ABS).get(unit, 0.0)
    rec = {
        "key": key,
        "label": label,
        "unit": unit,
        "better_when": better_when,
        "current": current,
        "previous": previous,
        "absolute_change": None,
        "percent_change": None,
        "direction": "unknown",
        "verdict": "unknown",
        "material": False,
        "notes": [],
    }

    if current is None and previous is None:
        rec["availability"] = "unavailable"
        rec["notes"].append("Not returned by the API for either period.")
        rec["direction"] = "n/a"
        rec["verdict"] = "unknown"
        return rec

    if current is None or previous is None:
        rec["availability"] = "partial"
        rec["notes"].append(
            "Only the %s period returned this metric; no comparison is possible."
            % ("current" if current is not None else "previous"))
        rec["direction"] = "n/a"
        return rec

    rec["availability"] = "available"
    rec["absolute_change"] = current - previous

    if previous == 0:
        if current == 0:
            rec["percent_change"] = 0.0
            rec["direction"] = "flat"
            rec["verdict"] = "flat"
            rec["notes"].append("Zero in both periods.")
            return rec
        rec["percent_change"] = None
        rec["direction"] = "up"
        rec["verdict"] = "new"
        rec["material"] = True
        rec["notes"].append(
            "The previous period was zero, so percentage change is undefined. Report the "
            "absolute figure instead.")
        return rec

    rec["percent_change"] = (current - previous) / abs(previous) * 100.0

    if abs(rec["absolute_change"]) < 1e-9:
        rec["direction"] = "flat"
        rec["verdict"] = "flat"
        return rec

    rec["direction"] = "up" if rec["absolute_change"] > 0 else "down"
    rec["material"] = (
        abs(rec["percent_change"]) >= material_pct
        and abs(rec["absolute_change"]) >= spec_min
    )
    if not rec["material"]:
        rec["notes"].append(
            "Below the materiality threshold (%.0f%% and %s absolute); treat as noise."
            % (material_pct, fmt_plain(spec_min, unit)))

    if better_when == "context":
        rec["verdict"] = "ambiguous"
        rec["notes"].append(
            "Direction alone does not say whether this is good -- it depends on the "
            "objective for the period.")
    elif better_when == "higher":
        rec["verdict"] = "improved" if rec["direction"] == "up" else "declined"
    elif better_when == "lower":
        rec["verdict"] = "improved" if rec["direction"] == "down" else "declined"

    if not rec["material"] and rec["verdict"] in ("improved", "declined"):
        rec["verdict"] = "flat"
    return rec


def fmt_plain(value, unit):
    if value is None:
        return "not available"
    if unit == "rate":
        return "%.1f pp" % value
    if unit == "int":
        return "{:,.0f}".format(value)
    return "{:,.2f}".format(value)


# ---------------------------------------------------------------------------
# Formatting for the pre-rendered tables
# ---------------------------------------------------------------------------

SYMBOLS = {"USD": "$", "GBP": "£", "EUR": "€", "CAD": "C$", "AUD": "A$",
           "NZD": "NZ$", "JPY": "¥", "INR": "₹", "ZAR": "R"}


class Fmt(object):
    def __init__(self, currency):
        self.currency = currency or ""
        self.symbol = SYMBOLS.get(self.currency)

    def money(self, v, dp=2):
        if v is None:
            return "not available"
        s = "{:,.{dp}f}".format(v, dp=dp)
        return (self.symbol + s) if self.symbol else ("%s %s" % (s, self.currency)).strip()

    def value(self, v, unit, dp=None):
        if v is None:
            return "not available"
        if unit == "currency":
            return self.money(v)
        if unit == "rate":
            return "{:,.2f}%".format(v)
        if unit == "int":
            return "{:,.0f}".format(v)
        if unit == "decimal":
            # Precision follows magnitude, matching design/lib/fmt.py so the
            # figure in this table and the figure in the report's stat tile are
            # the same string. 490 conversions is 490, not 490.00; a ROAS of
            # 3.46 keeps both places, where the second one means something.
            if float(v).is_integer():
                return "{:,.0f}".format(v)
            if abs(v) >= 100:
                return "{:,.0f}".format(v)
            if abs(v) >= 10:
                return "{:,.1f}".format(v)
            return "{:,.2f}".format(v)
        return str(v)

    def delta(self, rec):
        """Absolute change, in the metric's own unit."""
        v = rec.get("absolute_change")
        if v is None:
            return "n/a"
        unit = rec["unit"]
        sign = "+" if v > 0 else ""
        if unit == "rate":
            return "%s%.2f pp" % (sign, v)
        if unit == "currency":
            return ("+" if v > 0 else "-") + self.money(abs(v))
        if unit == "int":
            return "%s%s" % (sign, "{:,.0f}".format(v))
        return "%s%s" % (sign, "{:,.2f}".format(v))

    def pct(self, rec):
        v = rec.get("percent_change")
        if v is None:
            if rec.get("verdict") == "new":
                return "n/a (from zero)"
            if rec.get("availability") in ("unavailable", "partial"):
                return "n/a"
            return "n/a"
        return "%s%.1f%%" % ("+" if v > 0 else "", v)


# ---------------------------------------------------------------------------
# Findings
# ---------------------------------------------------------------------------

def finding(kind, fid, title, statement, evidence, severity="medium",
            confidence="high", scope="account", entity=None):
    return {
        "id": fid,
        "type": kind,                 # strength | weakness | anomaly | opportunity | observation
        "title": title,
        "statement": statement,
        "evidence": evidence,         # list of short factual strings, each a number from the data
        "severity": severity,         # high | medium | low
        "confidence": confidence,     # high | medium | low
        "scope": scope,               # account | campaign | segment | tracking
        "entity": entity,
    }


def ev(fmt, rec):
    """One evidence line for a KPI record."""
    if rec["availability"] == "unavailable":
        return "%s: not available" % rec["label"]
    if rec["availability"] == "partial":
        return "%s: %s this period, no comparable figure last period" % (
            rec["label"], fmt.value(rec["current"], rec["unit"]))
    return "%s: %s vs %s (%s, %s)" % (
        rec["label"],
        fmt.value(rec["current"], rec["unit"]),
        fmt.value(rec["previous"], rec["unit"]),
        fmt.delta(rec), fmt.pct(rec))


def account_findings(kpis, fmt, ctx):
    """Account-level diagnostics.

    Each rule states what it saw and what it cannot conclude. Correlation is
    described as correlation: "spend rose while conversions fell" is a fact;
    "the budget increase caused the decline" is not, and is not written here.
    """
    out = []
    k = kpis

    def r(key):
        return k.get(key, {})

    def val(key, which="current"):
        return r(key).get(which)

    def material(key):
        return r(key).get("material") and r(key).get("availability") == "available"

    low_sample = (val("conversions") or 0) < SMALL_SAMPLE_CONVERSIONS
    sample_note = (
        " Fewer than %d conversions in the period, so conversion-derived figures move a "
        "long way on small changes -- treat this as a signal to watch, not a settled "
        "result." % SMALL_SAMPLE_CONVERSIONS)

    # -- efficiency divergence: spend and conversions moving apart -----------
    cost_rec, conv_rec = r("cost"), r("conversions")
    if (cost_rec.get("availability") == "available"
            and conv_rec.get("availability") == "available"
            and cost_rec.get("percent_change") is not None
            and conv_rec.get("percent_change") is not None):
        gap = cost_rec["percent_change"] - conv_rec["percent_change"]
        if cost_rec["percent_change"] > 5 and gap > 15:
            out.append(finding(
                "weakness", "spend_outpacing_conversions",
                "Spend grew faster than conversions",
                "Spend rose %.1f%% while conversions moved %.1f%% -- a %.0f-point gap. The "
                "account bought more traffic than it converted; whether that is a bidding, "
                "landing-page or demand problem is not decidable from these figures alone."
                % (cost_rec["percent_change"], conv_rec["percent_change"], gap),
                [ev(fmt, cost_rec), ev(fmt, conv_rec), ev(fmt, r("cost_per_conversion"))],
                severity="high", confidence="medium" if low_sample else "high"))
        elif conv_rec["percent_change"] > 5 and gap < -15:
            out.append(finding(
                "strength", "conversions_outpacing_spend",
                "Conversions grew faster than spend",
                "Conversions rose %.1f%% on %.1f%% %s spend -- the account converted more "
                "from roughly the same investment."
                % (conv_rec["percent_change"], abs(cost_rec["percent_change"]),
                   "more" if cost_rec["percent_change"] > 0 else "less"),
                [ev(fmt, conv_rec), ev(fmt, cost_rec), ev(fmt, r("cost_per_conversion"))],
                severity="medium", confidence="medium" if low_sample else "high"))

    # -- CPA ----------------------------------------------------------------
    cpa = r("cost_per_conversion")
    if material("cost_per_conversion"):
        kind = "weakness" if cpa["verdict"] == "declined" else "strength"
        out.append(finding(
            kind, "cpa_shift",
            "Cost per conversion %s" % ("rose" if cpa["direction"] == "up" else "fell"),
            "CPA moved from %s to %s (%s). At this period's conversion volume that is a "
            "%s of roughly %s across the period.%s"
            % (fmt.money(cpa["previous"]), fmt.money(cpa["current"]), fmt.pct(cpa),
               "cost" if cpa["direction"] == "up" else "saving",
               fmt.money(abs(cpa["absolute_change"]) * (val("conversions") or 0)),
               sample_note if low_sample else ""),
            [ev(fmt, cpa), ev(fmt, conv_rec), ev(fmt, cost_rec)],
            severity="high" if kind == "weakness" else "medium",
            confidence="low" if low_sample else "high"))

    # -- ROAS ---------------------------------------------------------------
    roas = r("roas")
    if material("roas"):
        kind = "strength" if roas["verdict"] == "improved" else "weakness"
        out.append(finding(
            kind, "roas_shift",
            "ROAS %s" % ("improved" if kind == "strength" else "deteriorated"),
            "ROAS moved from %.2f to %.2f (%s) on conversion value of %s."
            % (roas["previous"], roas["current"], fmt.pct(roas),
               fmt.money(val("conversions_value"))),
            [ev(fmt, roas), ev(fmt, r("conversions_value")), ev(fmt, cost_rec)],
            severity="high", confidence="low" if low_sample else "high"))

    # -- conversion volume and value ---------------------------------------
    for key in ("conversions", "conversions_value", "clicks"):
        rec = r(key)
        if not material(key):
            continue
        kind = "strength" if rec["verdict"] == "improved" else "weakness"
        out.append(finding(
            kind, "%s_shift" % key,
            "%s %s %s" % (rec["label"], "rose" if rec["direction"] == "up" else "fell",
                          ("%.1f%%" % abs(rec["percent_change"]))
                          if rec.get("percent_change") is not None else "from zero"),
            "%s moved from %s to %s (%s, %s)%s" % (
                rec["label"], fmt.value(rec["previous"], rec["unit"]),
                fmt.value(rec["current"], rec["unit"]), fmt.delta(rec), fmt.pct(rec),
                ", against a %s change in spend." % fmt.pct(cost_rec)
                if cost_rec.get("percent_change") is not None else "."),
            [ev(fmt, rec), ev(fmt, cost_rec),
             ev(fmt, r("cost_per_conversion") if key != "clicks" else r("average_cpc"))],
            severity="high" if key == "conversions" else "medium",
            confidence="low" if (key != "clicks" and low_sample) else "high"))

    # -- CTR / CPC / conversion rate ----------------------------------------
    for key, up_word, down_word in (
        ("ctr", "improved", "fell"),
        ("average_cpc", "rose", "fell"),
        ("conversion_rate", "improved", "fell"),
    ):
        rec = r(key)
        if not material(key):
            continue
        kind = "strength" if rec["verdict"] == "improved" else "weakness"
        word = up_word if rec["direction"] == "up" else down_word
        out.append(finding(
            kind, "%s_shift" % key,
            "%s %s" % (rec["label"], word),
            "%s moved from %s to %s (%s)." % (
                rec["label"], fmt.value(rec["previous"], rec["unit"]),
                fmt.value(rec["current"], rec["unit"]), fmt.pct(rec)),
            [ev(fmt, rec)],
            severity="medium",
            confidence="low" if (key == "conversion_rate" and low_sample) else "high"))

    # -- cheaper clicks that are not converting -----------------------------
    cpc, cvr = r("average_cpc"), r("conversion_rate")
    if (cpc.get("direction") == "down" and cvr.get("direction") == "down"
            and cpc.get("material") and cvr.get("material")):
        out.append(finding(
            "anomaly", "cheap_traffic_low_quality",
            "Clicks got cheaper and converted less",
            "CPC fell %s while conversion rate fell %s. Cheaper clicks are usually good "
            "news; falling conversion rate at the same time is consistent with a shift "
            "toward lower-intent traffic, though it is also consistent with a landing-page "
            "or seasonality effect. The data here does not separate them."
            % (fmt.pct(cpc), fmt.pct(cvr)),
            [ev(fmt, cpc), ev(fmt, cvr), ev(fmt, r("clicks"))],
            severity="medium", confidence="medium"))

    # -- impression share ---------------------------------------------------
    is_rec, lost_budget, lost_rank = r("search_impression_share"), r("search_lost_is_budget"), r("search_lost_is_rank")
    if is_rec.get("availability") == "available" and is_rec.get("material"):
        kind = "strength" if is_rec["verdict"] == "improved" else "weakness"
        out.append(finding(
            kind, "impression_share_shift",
            "Search impression share %s" % ("rose" if is_rec["direction"] == "up" else "fell"),
            "Impression-weighted search impression share moved from %.1f%% to %.1f%% (%s), "
            "across the %d of %d campaigns that report it."
            % (is_rec["previous"], is_rec["current"], fmt.delta(is_rec),
               ctx.get("is_campaigns_reporting", 0), ctx.get("is_campaigns_total", 0)),
            [ev(fmt, is_rec), ev(fmt, lost_budget), ev(fmt, lost_rank)],
            severity="medium"))
    if lost_budget.get("current") is not None and lost_budget["current"] >= 10:
        out.append(finding(
            "opportunity", "budget_capped_account",
            "Budget is capping search impressions",
            "%.1f%% of available search impressions were lost to budget. That is demand the "
            "account could have served and did not." % lost_budget["current"],
            [ev(fmt, lost_budget), ev(fmt, r("cost_per_conversion")), ev(fmt, cost_rec)],
            severity="high" if lost_budget["current"] >= 20 else "medium"))
    if lost_rank.get("current") is not None and lost_rank["current"] >= 30:
        out.append(finding(
            "weakness", "rank_limited_account",
            "Ad rank is the main brake on visibility",
            "%.1f%% of available search impressions were lost to ad rank rather than "
            "budget. Ad rank combines bid and quality; this figure alone does not say "
            "which of the two is short." % lost_rank["current"],
            [ev(fmt, lost_rank), ev(fmt, lost_budget), ev(fmt, r("ctr"))],
            severity="medium"))

    # Nothing conversion-derived deserves a "high" on a handful of conversions.
    if low_sample:
        for f in out:
            if (f["id"] in ("spend_outpacing_conversions", "conversions_outpacing_spend",
                            "cpa_shift", "roas_shift", "conversion_rate_shift")
                    and f["severity"] == "high"):
                f["severity"] = "medium"

    return out


def campaign_analysis(raw, fmt, account_kpis):
    """Per-campaign comparison plus the flags that drive campaign-level findings."""
    ds = raw.get("datasets", {}).get("campaigns") or {}
    cur_rows, prev_rows = ds.get("current"), ds.get("previous")
    if cur_rows is None and prev_rows is None:
        return [], []

    def index(rows):
        out = {}
        for r in rows or []:
            cid = str(ads.field(r, "campaign.id"))
            out[cid] = r
        return out

    cur_i, prev_i = index(cur_rows), index(prev_rows)
    account_cost = account_kpis.get("cost", {}).get("current") or 0
    account_cpa = account_kpis.get("cost_per_conversion", {}).get("current")
    account_roas = account_kpis.get("roas", {}).get("current")
    account_cost_delta = account_kpis.get("cost", {}).get("absolute_change")

    campaigns = []
    for cid in sorted(set(cur_i) | set(prev_i),
                      key=lambda c: -(ads.micros(cur_i.get(c, {}), "metrics.cost_micros") or 0)):
        crow, prow = cur_i.get(cid), prev_i.get(cid)
        src = crow or prow
        cur_t = derive(totals_from_rows([crow])) if crow else None
        prev_t = derive(totals_from_rows([prow])) if prow else None

        entry = {
            "id": cid,
            "name": ads.field(src, "campaign.name"),
            "status": ads.field(src, "campaign.status"),
            "channel_type": ads.field(src, "campaign.advertising_channel_type"),
            "channel_sub_type": ads.field(src, "campaign.advertising_channel_sub_type"),
            "bidding_strategy": ads.field(src, "campaign.bidding_strategy_type"),
            "daily_budget": ads.micros(src, "campaign_budget.amount_micros"),
            "shared_budget": ads.field(src, "campaign_budget.explicitly_shared"),
            "present_in": ("both" if crow and prow else ("current only" if crow else "previous only")),
            "current": public_totals(cur_t),
            "previous": public_totals(prev_t),
            "impression_share": {
                "search_impression_share": pct(ads.num(crow, "metrics.search_impression_share")) if crow else None,
                "search_lost_is_budget": pct(ads.num(crow, "metrics.search_budget_lost_impression_share")) if crow else None,
                "search_lost_is_rank": pct(ads.num(crow, "metrics.search_rank_lost_impression_share")) if crow else None,
                "search_absolute_top_is": pct(ads.num(crow, "metrics.search_absolute_top_impression_share")) if crow else None,
            },
            "changes": {},
            "flags": [],
        }

        for key in ("cost", "clicks", "impressions", "conversions", "conversions_value",
                    "ctr", "average_cpc", "conversion_rate", "cost_per_conversion", "roas"):
            spec = KPI_BY_KEY.get(key)
            entry["changes"][key] = change(
                (cur_t or {}).get(key), (prev_t or {}).get(key),
                spec[2] if spec else "decimal", spec[3] if spec else "context",
                key=key, label=spec[1] if spec else key)

        cost = (cur_t or {}).get("cost")
        conv = (cur_t or {}).get("conversions")
        clicks = (cur_t or {}).get("clicks")
        cpa = (cur_t or {}).get("cost_per_conversion")
        roas_c = (cur_t or {}).get("roas")
        entry["share_of_spend"] = (
            None if not account_cost or cost is None else round(100.0 * cost / account_cost, 1))

        if clicks is not None and clicks < SPARSE_CLICKS:
            entry["flags"].append("sparse_data")
        if cost and conv == 0:
            entry["flags"].append("spend_no_conversions")
        if cost and conv and account_cpa and cpa and cpa > account_cpa * 1.5:
            entry["flags"].append("cpa_well_above_account")
        if cost and conv and account_cpa and cpa and cpa < account_cpa * 0.6:
            entry["flags"].append("cpa_well_below_account")
        lb = entry["impression_share"]["search_lost_is_budget"]
        lr = entry["impression_share"]["search_lost_is_rank"]
        if lb is not None and lb >= 10:
            entry["flags"].append("budget_constrained")
        if lr is not None and lr >= 30:
            entry["flags"].append("rank_constrained")
        if entry["status"] == "PAUSED" and cost:
            entry["flags"].append("paused_but_spent")
        cost_change = entry["changes"]["cost"].get("absolute_change")
        if (account_cost_delta and cost_change is not None
                and abs(account_cost_delta) > 0
                and abs(cost_change) >= abs(account_cost_delta) * 0.4):
            entry["flags"].append("drove_account_spend_change")
        if roas_c is not None and account_roas and roas_c > account_roas * 1.3:
            entry["flags"].append("roas_well_above_account")

        campaigns.append(entry)

    findings = campaign_level_findings(campaigns, fmt, account_kpis)

    # A campaign with almost no traffic cannot support a confident finding, no
    # matter which rule fired. Rather than suppress it -- a starved campaign is
    # still worth seeing -- every finding about it is marked down, so it sorts
    # below the things the data can actually carry.
    sparse_names = {c["name"] for c in campaigns if "sparse_data" in c["flags"]}
    for f in findings:
        if f.get("entity") in sparse_names and f["severity"] != "low":
            f["severity"] = "low"
            f["confidence"] = "low"
            f["statement"] += (
                " Volumes for this campaign are below the %d-click floor, so read this as a "
                "flag to check rather than a conclusion." % SPARSE_CLICKS)
    return campaigns, findings


def public_totals(t):
    """Strip the private row-count keys before the totals go into the contract."""
    if t is None:
        return None
    return {k: v for k, v in t.items() if not k.startswith("_")}


def campaign_level_findings(campaigns, fmt, account_kpis):
    out = []
    account_cpa = account_kpis.get("cost_per_conversion", {}).get("current")

    for c in campaigns:
        cur = c.get("current") or {}
        cost, conv = cur.get("cost"), cur.get("conversions")
        share = c.get("share_of_spend")
        sparse = "sparse_data" in c["flags"]

        if "spend_no_conversions" in c["flags"] and share and share >= 5:
            out.append(finding(
                "weakness", "campaign_no_conversions:%s" % c["id"],
                "%s spent with no recorded conversions" % c["name"],
                "%s took %s (%.0f%% of account spend) and recorded zero conversions. %s"
                % (c["name"], fmt.money(cost), share,
                   "With only %s clicks the campaign has not had a fair test yet."
                   % "{:,.0f}".format(cur.get("clicks") or 0) if sparse else
                   "At %s clicks that is enough traffic to expect at least one."
                   % "{:,.0f}".format(cur.get("clicks") or 0)),
                ["Spend: %s (%.0f%% of account)" % (fmt.money(cost), share),
                 "Clicks: %s" % "{:,.0f}".format(cur.get("clicks") or 0),
                 "Conversions: 0",
                 "Campaign type: %s, bidding: %s" % (c["channel_type"], c["bidding_strategy"])],
                severity="high" if not sparse else "low",
                confidence="low" if sparse else "high",
                scope="campaign", entity=c["name"]))

        if "cpa_well_above_account" in c["flags"] and not sparse:
            out.append(finding(
                "weakness", "campaign_high_cpa:%s" % c["id"],
                "%s converts well above account CPA" % c["name"],
                "%s is converting at %s against an account average of %s, on %s of spend."
                % (c["name"], fmt.money(cur.get("cost_per_conversion")),
                   fmt.money(account_cpa), fmt.money(cost)),
                ["CPA: %s vs account %s" % (fmt.money(cur.get("cost_per_conversion")),
                                            fmt.money(account_cpa)),
                 "Spend: %s (%s%% of account)" % (fmt.money(cost), share),
                 "Conversions: %s" % "{:,.1f}".format(conv or 0)],
                severity="high" if (share or 0) >= 15 else "medium",
                scope="campaign", entity=c["name"]))

        if "cpa_well_below_account" in c["flags"] and not sparse:
            out.append(finding(
                "strength", "campaign_low_cpa:%s" % c["id"],
                "%s converts well below account CPA" % c["name"],
                "%s converts at %s against an account average of %s."
                % (c["name"], fmt.money(cur.get("cost_per_conversion")), fmt.money(account_cpa)),
                ["CPA: %s vs account %s" % (fmt.money(cur.get("cost_per_conversion")),
                                            fmt.money(account_cpa)),
                 "Conversions: %s on %s" % ("{:,.1f}".format(conv or 0), fmt.money(cost))],
                severity="medium", scope="campaign", entity=c["name"]))

        if "budget_constrained" in c["flags"]:
            efficient = (account_cpa and cur.get("cost_per_conversion")
                         and cur["cost_per_conversion"] <= account_cpa)
            out.append(finding(
                "opportunity" if efficient else "observation",
                "campaign_budget_constrained:%s" % c["id"],
                "%s is losing impressions to budget" % c["name"],
                "%s lost %.1f%% of available search impressions to budget%s."
                % (c["name"], c["impression_share"]["search_lost_is_budget"],
                   ", and converts at or below account CPA -- unserved demand at a price "
                   "the account already accepts" if efficient else ""),
                ["Search lost IS (budget): %.1f%%" % c["impression_share"]["search_lost_is_budget"],
                 "Daily budget: %s" % fmt.money(c.get("daily_budget")),
                 "CPA: %s vs account %s" % (fmt.money(cur.get("cost_per_conversion")),
                                            fmt.money(account_cpa))],
                severity="high" if efficient else "low",
                confidence="medium" if sparse else "high",
                scope="campaign", entity=c["name"]))

        if "rank_constrained" in c["flags"]:
            out.append(finding(
                "weakness", "campaign_rank_constrained:%s" % c["id"],
                "%s is losing impressions to ad rank" % c["name"],
                "%s lost %.1f%% of available search impressions to ad rank. Bid, quality or "
                "both are short; this metric does not separate them."
                % (c["name"], c["impression_share"]["search_lost_is_rank"]),
                ["Search lost IS (rank): %.1f%%" % c["impression_share"]["search_lost_is_rank"],
                 "Search IS: %s" % ("%.1f%%" % c["impression_share"]["search_impression_share"]
                                    if c["impression_share"]["search_impression_share"] is not None
                                    else "not available"),
                 "CTR: %s" % (("%.2f%%" % cur.get("ctr")) if cur.get("ctr") is not None else "not available")],
                severity="medium", scope="campaign", entity=c["name"]))

        if "paused_but_spent" in c["flags"]:
            out.append(finding(
                "observation", "campaign_paused_but_spent:%s" % c["id"],
                "%s is paused but spent during the period" % c["name"],
                "%s is currently PAUSED yet recorded %s of spend in the period, so it was "
                "running for part of it. Period-over-period comparisons for this campaign "
                "are not like-for-like." % (c["name"], fmt.money(cost)),
                ["Status now: PAUSED", "Spend in period: %s" % fmt.money(cost)],
                severity="low", scope="campaign", entity=c["name"]))

        if "drove_account_spend_change" in c["flags"]:
            ch = c["changes"]["cost"]
            out.append(finding(
                "observation", "campaign_spend_swing:%s" % c["id"],
                "%s accounts for much of the account's spend change" % c["name"],
                "%s spend moved %s (%s), a large share of the account's total movement."
                % (c["name"], fmt.delta(ch), fmt.pct(ch)),
                [ev(fmt, ch), "Share of account spend: %s%%" % share],
                severity="low", scope="campaign", entity=c["name"]))

        if c["present_in"] == "current only" and cost:
            out.append(finding(
                "observation", "campaign_new:%s" % c["id"],
                "%s has no comparison baseline" % c["name"],
                "%s ran in the current period only, taking %s. It has no comparison "
                "baseline, and its spend is part of any account-level increase."
                % (c["name"], fmt.money(cost)),
                ["Spend: %s" % fmt.money(cost),
                 "Conversions: %s" % ("{:,.1f}".format(conv) if conv is not None else "not available")],
                severity="low", scope="campaign", entity=c["name"]))
        if c["present_in"] == "previous only":
            prev = c.get("previous") or {}
            out.append(finding(
                "observation", "campaign_stopped:%s" % c["id"],
                "%s ran last period but not this one" % c["name"],
                "%s spent %s last period and nothing this period. Any account-level decline "
                "includes its absence." % (c["name"], fmt.money(prev.get("cost"))),
                ["Previous spend: %s" % fmt.money(prev.get("cost")),
                 "Previous conversions: %s" % ("{:,.1f}".format(prev.get("conversions"))
                                               if prev.get("conversions") is not None else "not available")],
                severity="low", scope="campaign", entity=c["name"]))

    return out


# ---------------------------------------------------------------------------
# Segments, conversion tracking, trend
# ---------------------------------------------------------------------------

def segment_analysis(raw, key, dimension, fmt):
    """Aggregate a segmented dataset and compare mix between periods.

    A mix shift is reported in percentage POINTS of spend and conversions,
    because a segment can grow its share while shrinking in absolute terms and
    the two readings lead to different decisions.
    """
    ds = raw.get("datasets", {}).get(key) or {}
    if ds.get("current") is None and ds.get("previous") is None:
        return None

    def bucket(rows):
        if rows is None:
            return None
        groups = {}
        for r in rows:
            label = ads.field(r, dimension) or "UNSPECIFIED"
            groups.setdefault(label, []).append(r)
        return {label: derive(totals_from_rows(rs)) for label, rs in groups.items()}

    cur, prev = bucket(ds.get("current")), bucket(ds.get("previous"))
    cur_total = sum((v.get("cost") or 0) for v in (cur or {}).values()) or 0
    prev_total = sum((v.get("cost") or 0) for v in (prev or {}).values()) or 0

    rows_out = []
    for label in sorted(set(cur or {}) | set(prev or {}),
                        key=lambda l: -((cur or {}).get(l, {}).get("cost") or 0)):
        c = (cur or {}).get(label)
        p = (prev or {}).get(label)
        c_share = None if not cur_total or not c else round(100.0 * (c.get("cost") or 0) / cur_total, 1)
        p_share = None if not prev_total or not p else round(100.0 * (p.get("cost") or 0) / prev_total, 1)
        rows_out.append({
            "label": label,
            "current": public_totals(c),
            "previous": public_totals(p),
            "spend_share_current": c_share,
            "spend_share_previous": p_share,
            "spend_share_change_pp": (None if c_share is None or p_share is None
                                      else round(c_share - p_share, 1)),
        })
    return rows_out


def segment_findings(rows, dimension_label, fmt):
    out = []
    for r in rows or []:
        shift = r.get("spend_share_change_pp")
        if shift is None or abs(shift) < 10:
            continue
        out.append(finding(
            "anomaly", "mix_shift:%s:%s" % (dimension_label, r["label"]),
            "%s mix shifted toward %s" % (dimension_label, r["label"])
            if shift > 0 else "%s mix shifted away from %s" % (dimension_label, r["label"]),
            "%s moved from %.1f%% to %.1f%% of spend (%+.1f points). Spend %s from %s to %s."
            % (r["label"], r["spend_share_previous"], r["spend_share_current"], shift,
               "rose" if (r["current"] or {}).get("cost", 0) > (r["previous"] or {}).get("cost", 0) else "fell",
               fmt.money((r["previous"] or {}).get("cost")),
               fmt.money((r["current"] or {}).get("cost"))),
            ["%s spend share: %.1f%% vs %.1f%% (%+.1f pp)"
             % (r["label"], r["spend_share_current"], r["spend_share_previous"], shift),
             "%s conversions: %s vs %s" % (
                 r["label"],
                 "{:,.1f}".format((r["current"] or {}).get("conversions") or 0),
                 "{:,.1f}".format((r["previous"] or {}).get("conversions") or 0))],
            severity="medium", scope="segment", entity=r["label"]))
    return out


def conversion_tracking(raw, kpis, fmt):
    """What the account's conversion setup looks like, and where it looks wrong.

    Every check here is detectable from the retrieved data alone. None of them
    proves a tracking fault -- they describe patterns that are usually one, and
    they say so.
    """
    meta_ds = (raw.get("datasets", {}).get("conversion_actions_meta") or {}).get("current")
    perf_ds = raw.get("datasets", {}).get("conversion_performance") or {}
    findings_out = []
    actions = []

    def by_action(rows):
        if rows is None:
            return None
        out = {}
        for r in rows:
            name = ads.field(r, "segments.conversion_action_name") or "(unnamed)"
            entry = out.setdefault(name, {
                "name": name,
                "category": ads.field(r, "segments.conversion_action_category"),
                "all_conversions": None,
                "all_conversions_value": None,
            })
            entry["all_conversions"] = ads.add(entry["all_conversions"],
                                               ads.num(r, "metrics.all_conversions"))
            entry["all_conversions_value"] = ads.add(entry["all_conversions_value"],
                                                     ads.num(r, "metrics.all_conversions_value"))
        return out

    cur_actions = by_action(perf_ds.get("current"))
    prev_actions = by_action(perf_ds.get("previous"))
    meta_by_name = {}
    for r in meta_ds or []:
        meta_by_name[ads.field(r, "conversion_action.name")] = {
            "status": ads.field(r, "conversion_action.status"),
            "type": ads.field(r, "conversion_action.type"),
            "category": ads.field(r, "conversion_action.category"),
            "primary_for_goal": ads.field(r, "conversion_action.primary_for_goal"),
            "counting_type": ads.field(r, "conversion_action.counting_type"),
            "in_conversions_metric": ads.field(r, "conversion_action.include_in_conversions_metric"),
        }

    names = set(cur_actions or {}) | set(prev_actions or {}) | set(meta_by_name)
    for name in sorted(names):
        c = (cur_actions or {}).get(name, {})
        p = (prev_actions or {}).get(name, {})
        meta = meta_by_name.get(name, {})
        rec = {
            "name": name,
            "category": c.get("category") or meta.get("category"),
            "status": meta.get("status"),
            "counting_type": meta.get("counting_type"),
            "included_in_conversions_metric": meta.get("in_conversions_metric"),
            "primary_for_goal": meta.get("primary_for_goal"),
            "all_conversions_current": c.get("all_conversions"),
            "all_conversions_previous": p.get("all_conversions"),
            "all_conversions_value_current": c.get("all_conversions_value"),
        }
        rec["change"] = change(rec["all_conversions_current"], rec["all_conversions_previous"],
                               "decimal", "higher", key="all_conversions", label=name)
        actions.append(rec)

    # -- zero-conversion account -------------------------------------------
    conv = kpis.get("conversions", {})
    cost = kpis.get("cost", {})
    if conv.get("current") == 0 and (cost.get("current") or 0) > 0:
        findings_out.append(finding(
            "anomaly", "no_conversions_recorded",
            "The account recorded no conversions while spending",
            "%s of spend produced zero recorded conversions in the current period. Either "
            "the account genuinely converted nothing, or conversions are not being tracked. "
            "Nothing in the API response distinguishes the two -- check the conversion "
            "actions and the tag before treating this as a performance result."
            % fmt.money(cost.get("current")),
            ["Spend: %s" % fmt.money(cost.get("current")),
             "Conversions: 0",
             "Conversion actions returning data: %d" % sum(
                 1 for a in actions if (a["all_conversions_current"] or 0) > 0)],
            severity="high", confidence="high", scope="tracking"))

    # -- no conversion value -----------------------------------------------
    value = kpis.get("conversions_value", {})
    if (conv.get("current") or 0) > 0 and (value.get("current") in (None, 0)):
        findings_out.append(finding(
            "observation", "no_conversion_value",
            "No conversion value is recorded, so ROAS cannot be calculated",
            "The account records conversions but no conversion value, so ROAS and value per "
            "conversion are unavailable rather than zero. Efficiency in this report is "
            "measured by CPA only.",
            ["Conversions: %s" % "{:,.1f}".format(conv.get("current") or 0),
             "Conversion value: %s" % ("0" if value.get("current") == 0 else "not returned")],
            severity="low", confidence="high", scope="tracking"))

    # -- placeholder values -------------------------------------------------
    vpc = ads.safe_div(value.get("current"), conv.get("current"))
    if vpc is not None and conv.get("current", 0) >= 10 and abs(vpc - round(vpc)) < 0.01 and round(vpc) in (1, 0):
        findings_out.append(finding(
            "anomaly", "placeholder_conversion_value",
            "Conversion value looks like a placeholder",
            "Value per conversion is exactly %.2f across %s conversions. A flat per-unit "
            "value usually means a default was set on the conversion action rather than "
            "real revenue being passed back, which makes ROAS a restatement of conversion "
            "volume rather than a return figure."
            % (vpc, "{:,.1f}".format(conv.get("current"))),
            ["Value per conversion: %.2f" % vpc,
             "Conversion value: %s" % fmt.money(value.get("current")),
             "Conversions: %s" % "{:,.1f}".format(conv.get("current"))],
            severity="medium", confidence="medium", scope="tracking"))

    # -- very high conversion rate -----------------------------------------
    cvr = kpis.get("conversion_rate", {}).get("current")
    if cvr is not None and cvr > 50:
        findings_out.append(finding(
            "observation", "very_high_conversion_rate",
            "Conversion rate above 50%% suggests low-friction actions are counted",
            "A %.1f%% conversion rate normally means the account counts lightweight actions "
            "(page views, clicks-to-call, every-conversion counting) rather than completed "
            "sales or qualified leads. It is not wrong, but conversion counts should be read "
            "as interactions unless the conversion actions say otherwise." % cvr,
            ["Conversion rate: %.1f%%" % cvr,
             "Conversion actions in use: %d" % len([a for a in actions if (a["all_conversions_current"] or 0) > 0])],
            severity="low", confidence="medium", scope="tracking"))

    # -- dead conversion actions -------------------------------------------
    dead = [a["name"] for a in actions
            if a.get("status") == "ENABLED"
            and (a["all_conversions_current"] or 0) == 0
            and (a["all_conversions_previous"] or 0) == 0]
    if dead and cur_actions is not None:
        findings_out.append(finding(
            "observation", "inactive_conversion_actions",
            "%d enabled conversion action(s) recorded nothing in either period" % len(dead),
            "These conversion actions are enabled but have not fired in 60 days: %s. Either "
            "the action is broken, or it is measuring something that no longer happens. "
            "Enabled-but-silent actions make the account's goal picture harder to read."
            % ", ".join(dead[:8]),
            ["Silent actions: %s" % ", ".join(dead[:8]),
             "Actions with data this period: %d" % len([a for a in actions if (a["all_conversions_current"] or 0) > 0])],
            severity="low", confidence="medium", scope="tracking"))

    return actions, findings_out


def trend_series(raw):
    """Daily rows for both periods, flattened for charting and gap checking."""
    ds = raw.get("datasets", {}).get("daily") or {}
    out = []
    for period in ("previous", "current"):
        for r in ds.get(period) or []:
            out.append({
                "date": ads.field(r, "segments.date"),
                "period": period,
                "impressions": ads.num(r, "metrics.impressions"),
                "clicks": ads.num(r, "metrics.clicks"),
                "cost": ads.micros(r, "metrics.cost_micros"),
                "conversions": ads.num(r, "metrics.conversions"),
                "conversions_value": ads.num(r, "metrics.conversions_value"),
            })
    out.sort(key=lambda x: (x["date"] or ""))
    return out


# ---------------------------------------------------------------------------
# Validation
# ---------------------------------------------------------------------------

def validate(raw, kpis, campaigns, trend, fmt):
    """Everything that should make a reader trust the numbers less.

    Validation runs before any conclusion is drawn, and its output is part of
    the contract: a report that quietly drops these warnings is a report that
    claims more certainty than the data supports.
    """
    warnings = list(raw.get("warnings") or [])
    errors = list(raw.get("errors") or [])
    checks = []
    unavailable = []
    insufficient = []

    periods = raw.get("periods") or {}
    cur_p, prev_p = periods.get("current", {}), periods.get("previous", {})
    checks.append({
        "check": "reporting periods",
        "result": "%s..%s (%s days) vs %s..%s (%s days)" % (
            cur_p.get("start"), cur_p.get("end"), cur_p.get("days"),
            prev_p.get("start"), prev_p.get("end"), prev_p.get("days")),
        "ok": cur_p.get("days") == prev_p.get("days"),
        "basis": periods.get("basis"),
        "time_zone": periods.get("time_zone"),
    })

    # Campaign sums vs the account totals the API reported independently.
    for period in ("current", "previous"):
        camp_rows = (raw.get("datasets", {}).get("campaigns") or {}).get(period)
        acct_rows = (raw.get("datasets", {}).get("account_totals") or {}).get(period)
        if camp_rows is None or acct_rows is None:
            continue
        camp_cost, _, _ = ads.accumulate(camp_rows, lambda r: ads.micros(r, "metrics.cost_micros"))
        acct_cost, _, _ = ads.accumulate(acct_rows, lambda r: ads.micros(r, "metrics.cost_micros"))
        if camp_cost is None or acct_cost is None:
            continue
        diff = abs(camp_cost - acct_cost)
        tolerance = max(0.01, acct_cost * 0.005)
        ok = diff <= tolerance
        checks.append({
            "check": "campaign spend reconciles to account spend (%s)" % period,
            "result": "campaigns %s vs account %s (difference %s)" % (
                fmt.money(camp_cost), fmt.money(acct_cost), fmt.money(diff)),
            "ok": ok,
        })
        if not ok:
            warnings.append(
                "Campaign-level spend for the %s period does not reconcile with the "
                "account total (%s vs %s). Something is missing from the campaign list -- "
                "do not present campaign figures as a complete breakdown."
                % (period, fmt.money(camp_cost), fmt.money(acct_cost)))

    # Days actually returned vs days requested.
    for period, spec in (("current", cur_p), ("previous", prev_p)):
        days_returned = len({t["date"] for t in trend if t["period"] == period and t["date"]})
        expected = spec.get("days")
        if expected and days_returned and days_returned < expected:
            checks.append({
                "check": "daily coverage (%s)" % period,
                "result": "%d of %d days returned rows" % (days_returned, expected),
                "ok": False,
            })
            warnings.append(
                "The %s period returned data for %d of %d days. Days with no rows are days "
                "with no activity, not days worth zero -- but a large gap can also mean the "
                "account was paused, which changes what the totals mean."
                % (period, days_returned, expected))

    # Which KPIs simply are not there.
    for key, rec in kpis.items():
        if rec.get("availability") == "unavailable":
            unavailable.append({"metric": rec["label"],
                                "reason": "not returned by the API for either period"})
        elif rec.get("availability") == "partial":
            which = "current" if rec.get("current") is not None else "previous"
            unavailable.append({
                "metric": rec["label"],
                "reason": "available for the %s period only -- either the API did not return "
                          "it, or it is a derived metric whose denominator was zero in the "
                          "other period. No comparison is possible either way." % which})

    # Campaigns too small to judge.
    for c in campaigns:
        if "sparse_data" in c.get("flags", []):
            cur = c.get("current") or {}
            insufficient.append({
                "scope": "campaign",
                "entity": c["name"],
                "reason": "%s clicks and %s conversions in the current period -- below the "
                          "%d-click floor for reading rate metrics"
                          % ("{:,.0f}".format(cur.get("clicks") or 0),
                             "{:,.1f}".format(cur.get("conversions") or 0),
                             SPARSE_CLICKS),
            })

    conv = kpis.get("conversions", {}).get("current")
    if conv is not None and conv < SMALL_SAMPLE_CONVERSIONS:
        insufficient.append({
            "scope": "account",
            "entity": raw.get("account", {}).get("name"),
            "reason": "%s conversions in the current period. CPA, conversion rate and ROAS "
                      "swing hard on small counts; percentage changes on them are indicative "
                      "at best." % "{:,.1f}".format(conv),
        })

    if raw.get("account", {}).get("is_test_account"):
        warnings.append("This is a Google Ads TEST account. The figures are synthetic.")

    for e in errors:
        warnings.append(
            "Query failed: %s (%s). The '%s' section of this report is unavailable, not empty."
            % (e.get("message"), e.get("error_code") or e.get("http_status"), e.get("dataset")))

    return {
        "checks": checks,
        "warnings": warnings,
        "errors": errors,
        "unavailable_metrics": unavailable,
        "insufficient_data": insufficient,
    }


# ---------------------------------------------------------------------------
# Recommendations
#
# Each is derived from a finding, names the entity and the number that produced
# it, and dies with that finding. There is no default list -- an account with
# nothing wrong gets no recommendations, which is a legitimate result.
# ---------------------------------------------------------------------------

PRIORITY_FROM_SEVERITY = {"high": "High", "medium": "Medium", "low": "Low"}


def recommend(findings, campaigns, kpis, fmt):
    out = []

    def add(fid, action, reason, evidence, impact, priority, confidence="high"):
        out.append({
            "action": action,
            "reason": reason,
            "evidence": evidence,
            "expected_impact": impact,
            "priority": priority,
            "confidence": confidence,
            "from_finding": fid,
        })

    by_id = {f["id"]: f for f in findings}
    account_cpa = kpis.get("cost_per_conversion", {}).get("current")

    for f in findings:
        fid, sev = f["id"], f["severity"]
        prio = PRIORITY_FROM_SEVERITY.get(sev, "Medium")

        if fid.startswith("campaign_no_conversions:"):
            name = f["entity"]
            c = next((c for c in campaigns if c["name"] == name), {})
            cur = c.get("current") or {}
            if f["confidence"] == "low":
                add(fid,
                    "Give %s a defined test window and a decision date rather than pausing "
                    "it now: it has only %s clicks, which is not enough traffic to call."
                    % (name, "{:,.0f}".format(cur.get("clicks") or 0)),
                    "Zero conversions on a small click base is as consistent with too little "
                    "traffic as with a broken campaign.",
                    ["%s: %s spend, %s clicks, 0 conversions"
                     % (name, fmt.money(cur.get("cost")), "{:,.0f}".format(cur.get("clicks") or 0))],
                    "Either a real read on the campaign or a clean case for stopping it, "
                    "within one more period.",
                    "Low", confidence="medium")
            else:
                add(fid,
                    "Pause or restructure %s, and check its conversion tracking before "
                    "re-enabling it." % name,
                    "It consumed %s (%s%% of account spend) across %s clicks without "
                    "recording a single conversion."
                    % (fmt.money(cur.get("cost")), c.get("share_of_spend"),
                       "{:,.0f}".format(cur.get("clicks") or 0)),
                    ["%s: %s spend, %s clicks, 0 conversions"
                     % (name, fmt.money(cur.get("cost")), "{:,.0f}".format(cur.get("clicks") or 0)),
                     "Campaign type: %s; bidding: %s" % (c.get("channel_type"), c.get("bidding_strategy"))],
                    "Frees %s per period to redeploy into campaigns that are converting."
                    % fmt.money(cur.get("cost")),
                    "High")

        elif fid.startswith("campaign_budget_constrained:") and f["severity"] == "high":
            name = f["entity"]
            c = next((c for c in campaigns if c["name"] == name), {})
            cur = c.get("current") or {}
            lost = (c.get("impression_share") or {}).get("search_lost_is_budget")
            add(fid,
                "Raise the daily budget on %s (currently %s/day) and re-check impression "
                "share after 7-14 days." % (name, fmt.money(c.get("daily_budget"))),
                "It lost %.1f%% of available search impressions to budget while converting "
                "at %s, at or below the account average of %s -- the account is turning away "
                "demand it can already afford."
                % (lost, fmt.money(cur.get("cost_per_conversion")), fmt.money(account_cpa)),
                ["%s: search lost IS (budget) %.1f%%" % (name, lost),
                 "%s CPA %s vs account %s" % (name, fmt.money(cur.get("cost_per_conversion")),
                                              fmt.money(account_cpa)),
                 "Current daily budget: %s" % fmt.money(c.get("daily_budget"))],
                "Recovering the lost impression share at today's conversion rate would add "
                "conversions at roughly today's CPA. Impression share does not scale linearly "
                "with budget, so treat the figure as a ceiling, not a forecast.",
                "High")

        elif fid.startswith("campaign_high_cpa:"):
            name = f["entity"]
            c = next((c for c in campaigns if c["name"] == name), {})
            cur = c.get("current") or {}
            channel = (c.get("channel_type") or "").upper()
            if channel in ("SEARCH", "SHOPPING"):
                how = ("Audit %s at search-term and ad-group level: check its top spending "
                       "terms for intent mismatch, add negatives where the intent is wrong, "
                       "and compare its landing page against the account's efficient "
                       "campaigns." % name)
            elif channel == "PERFORMANCE_MAX":
                how = ("Audit %s by asset group and listing group: check the search-themes "
                       "and placement reports for low-intent traffic, exclude what does not "
                       "fit, and verify the campaign is not absorbing brand queries the "
                       "search campaigns already win." % name)
            elif channel in ("DISPLAY", "VIDEO", "DEMAND_GEN"):
                how = ("Audit %s by placement and audience: pull the placement report, "
                       "exclude the sites and apps taking spend without converting, and "
                       "check the audience definition still matches the offer." % name)
            else:
                how = ("Audit %s by its own targeting dimensions: find where the spend is "
                       "going and exclude what is not converting." % name)
            add(fid, how,
                "It converts at %s against an account average of %s while taking %s%% of "
                "spend." % (fmt.money(cur.get("cost_per_conversion")), fmt.money(account_cpa),
                            c.get("share_of_spend")),
                ["%s CPA %s vs account %s" % (name, fmt.money(cur.get("cost_per_conversion")),
                                              fmt.money(account_cpa)),
                 "%s spend %s (%s%% of account)" % (name, fmt.money(cur.get("cost")),
                                                    c.get("share_of_spend"))],
                "Bringing this campaign to the account average CPA would free roughly %s per "
                "period at current conversion volume."
                % fmt.money(max(0.0, (cur.get("cost") or 0) - (account_cpa or 0) * (cur.get("conversions") or 0))),
                "High" if (c.get("share_of_spend") or 0) >= 15 else "Medium")

        elif fid.startswith("campaign_rank_constrained:"):
            name = f["entity"]
            c = next((c for c in campaigns if c["name"] == name), {})
            lost = (c.get("impression_share") or {}).get("search_lost_is_rank")
            add(fid,
                "Work ad rank on %s: review ad strength and ad-group-to-keyword relevance "
                "first, then test a bid or target-CPA adjustment on its top-converting ad "
                "groups." % name,
                "%.1f%% of its available impressions are lost to rank rather than budget, so "
                "more budget alone will not buy them back." % lost,
                ["%s: search lost IS (rank) %.1f%%" % (name, lost),
                 "%s CTR: %s" % (name, ("%.2f%%" % (c.get("current") or {}).get("ctr")
                                        if (c.get("current") or {}).get("ctr") is not None
                                        else "not available"))],
                "Rank-driven impression share responds to quality and bid together; expect "
                "movement over weeks, not days.",
                "Medium")

        elif fid == "spend_outpacing_conversions":
            add(fid,
                "Re-check bidding targets and budget pacing across the campaigns that grew "
                "spend this period, starting with the largest spend movers listed below.",
                f["statement"],
                f["evidence"],
                "Holding CPA at the previous period's level on this period's spend would "
                "have produced materially more conversions; the gap is the size of the prize.",
                "High")

        elif fid == "cpa_shift" and f["type"] == "weakness":
            add(fid,
                "Identify which campaigns drove the CPA increase (see the campaign table) "
                "and treat the two or three largest contributors as the work for the period.",
                f["statement"],
                f["evidence"],
                "Returning to the previous CPA at this period's conversion volume is worth "
                "roughly %s." % fmt.money(abs(kpis.get("cost_per_conversion", {}).get("absolute_change") or 0)
                                          * (kpis.get("conversions", {}).get("current") or 0)),
                "High", confidence=f["confidence"])

        elif fid == "budget_capped_account":
            lb = kpis.get("search_lost_is_budget", {}).get("current")
            add(fid,
                "Decide, explicitly, whether to fund the %.1f%% of search impressions the "
                "account is losing to budget -- and if so, put the money behind the "
                "campaigns already converting at or below account CPA." % lb,
                "Lost-to-budget impression share is demand the account chose not to serve.",
                f["evidence"],
                "Additional volume at approximately current CPA, subject to the usual "
                "diminishing returns as impression share rises.",
                "High" if lb >= 20 else "Medium")

        elif fid == "no_conversions_recorded":
            add(fid,
                "Verify conversion tracking end to end (tag firing, conversion actions "
                "enabled, primary-for-goal set) before drawing any performance conclusion "
                "from this period.",
                "The account spent %s and recorded no conversions. Reporting on efficiency "
                "is impossible until it is known whether that is real."
                % fmt.money(kpis.get("cost", {}).get("current")),
                f["evidence"],
                "Restores the account's ability to be measured at all. Nothing else on this "
                "list can be prioritised properly until it is resolved.",
                "High")

        elif fid == "placeholder_conversion_value":
            add(fid,
                "Replace the flat per-conversion value with real transaction or lead values, "
                "or stop reporting ROAS for this account.",
                f["statement"],
                f["evidence"],
                "Makes ROAS a genuine return measure instead of a restatement of conversion "
                "volume.",
                "Medium", confidence="medium")

        elif fid == "inactive_conversion_actions":
            add(fid,
                "Review the enabled conversion actions that recorded nothing in 60 days and "
                "either fix or archive them.",
                f["statement"],
                f["evidence"],
                "A shorter, live list of conversion actions makes the account's goals legible "
                "and stops dead actions diluting automated bidding signals.",
                "Low", confidence="medium")

    # Stable ordering: priority first, then account-level before campaign-level.
    order = {"High": 0, "Medium": 1, "Low": 2}
    out.sort(key=lambda r: (order.get(r["priority"], 3), r["from_finding"]))
    return out


# ---------------------------------------------------------------------------
# Pre-rendered tables
#
# The agent writing the report pastes these rather than re-formatting numbers
# by hand. Every re-typed figure is a chance to mistype one.
# ---------------------------------------------------------------------------

def kpi_table(kpis, fmt, periods):
    cur, prev = periods["current"], periods["previous"]
    lines = [
        "| KPI | Current 30 days (%s – %s) | Previous 30 days (%s – %s) | Absolute change | %% change |"
        % (cur["start"], cur["end"], prev["start"], prev["end"]),
        "|---|---:|---:|---:|---:|",
    ]
    for key, label, unit, better, _desc in KPI_SPECS:
        rec = kpis.get(key)
        if not rec or rec["availability"] == "unavailable":
            continue
        lines.append("| %s | %s | %s | %s | %s |" % (
            label,
            fmt.value(rec["current"], unit),
            fmt.value(rec["previous"], unit),
            fmt.delta(rec),
            fmt.pct(rec),
        ))
    return "\n".join(lines)


def campaign_table(campaigns, fmt, limit=15):
    lines = [
        "| Campaign | Type | Status | Spend | Spend Δ% | Conversions | Conv. Δ% | CPA | ROAS | Search IS |",
        "|---|---|---|---:|---:|---:|---:|---:|---:|---:|",
    ]
    for c in campaigns[:limit]:
        cur = c.get("current") or {}
        ch = c.get("changes") or {}
        share = (c.get("impression_share") or {}).get("search_impression_share")
        lines.append("| %s | %s | %s | %s | %s | %s | %s | %s | %s | %s |" % (
            c["name"],
            (c.get("channel_type") or "").replace("_", " ").title(),
            (c.get("status") or "").title(),
            fmt.money(cur.get("cost")),
            fmt.pct(ch.get("cost", {})),
            "{:,.1f}".format(cur["conversions"]) if cur.get("conversions") is not None else "n/a",
            fmt.pct(ch.get("conversions", {})),
            fmt.money(cur.get("cost_per_conversion")),
            "{:,.2f}".format(cur["roas"]) if cur.get("roas") is not None else "n/a",
            "%.1f%%" % share if share is not None else "n/a",
        ))
    return "\n".join(lines)


def segment_table(rows, dimension_label, fmt, limit=8):
    if not rows:
        return None
    lines = [
        "| %s | Spend | Share of spend | Clicks | Conversions | CPA |" % dimension_label,
        "|---|---:|---:|---:|---:|---:|",
    ]
    for r in rows[:limit]:
        cur = r.get("current") or {}
        lines.append("| %s | %s | %s | %s | %s | %s |" % (
            (r["label"] or "").replace("_", " ").title(),
            fmt.money(cur.get("cost")),
            "%.1f%%" % r["spend_share_current"] if r.get("spend_share_current") is not None else "n/a",
            "{:,.0f}".format(cur["clicks"]) if cur.get("clicks") is not None else "n/a",
            "{:,.1f}".format(cur["conversions"]) if cur.get("conversions") is not None else "n/a",
            fmt.money(cur.get("cost_per_conversion")),
        ))
    return "\n".join(lines)


# ---------------------------------------------------------------------------
# Main
# ---------------------------------------------------------------------------

def build(raw, material_pct=MATERIAL_PCT):
    account = raw.get("account") or {}
    fmt = Fmt(account.get("currency"))
    periods = raw.get("periods") or {}

    ds = raw.get("datasets", {})
    acct_ds = ds.get("account_totals") or {}
    camp_ds = ds.get("campaigns") or {}

    totals = {}
    fallback_note = None
    for period in ("current", "previous"):
        rows = acct_ds.get(period)
        if rows is None:
            # The account-level query failed; sum campaigns instead and say so,
            # because a campaign sum excludes anything not attached to a campaign.
            rows = camp_ds.get(period)
            if rows is not None:
                fallback_note = (
                    "Account totals were summed from campaign rows because the account-level "
                    "query failed. Any spend not attached to a campaign is missing from them.")
        totals[period] = derive(totals_from_rows(rows))

    shares = {p: share_metrics(camp_ds.get(p)) for p in ("current", "previous")}

    kpis = {}
    for key, label, unit, better, _desc in KPI_SPECS:
        if key in ("search_impression_share", "search_lost_is_budget", "search_lost_is_rank"):
            cur_v = shares["current"].get(key)
            prev_v = shares["previous"].get(key)
        else:
            cur_v = (totals["current"] or {}).get(key)
            prev_v = (totals["previous"] or {}).get(key)
        kpis[key] = change(cur_v, prev_v, unit, better, key=key, label=label,
                           material_pct=material_pct)

    # Cross-checks that turn an arithmetic verdict into an honest one.
    cost, conv = kpis["cost"], kpis["conversions"]
    if (cost["direction"] == "down" and conv.get("direction") == "down"
            and cost.get("availability") == "available"):
        cost["notes"].append(
            "Spend fell alongside conversions, so the saving is not efficiency -- the "
            "account bought less.")
    if (cost["direction"] == "up" and conv.get("verdict") == "improved"
            and kpis["cost_per_conversion"].get("verdict") in ("improved", "flat")):
        cost["notes"].append(
            "Spend rose while CPA held or improved, which is scale rather than waste.")

    api_ctr = None
    for rows in (acct_ds.get("current") or []):
        api_ctr = ads.num(rows, "metrics.ctr")
        break
    if api_ctr is not None and kpis["ctr"]["current"] is not None:
        drift = abs(api_ctr * 100.0 - kpis["ctr"]["current"])
        if drift > 0.05:
            kpis["ctr"]["notes"].append(
                "Derived CTR (%.2f%%) differs from the API's own CTR (%.2f%%) by more than "
                "rounding. Derived is used, since it is reproducible from the clicks and "
                "impressions in this table." % (kpis["ctr"]["current"], api_ctr * 100.0))

    ctx = {
        "is_campaigns_reporting": (shares["current"].get("coverage") or {}).get("campaigns_reporting", 0),
        "is_campaigns_total": (shares["current"].get("coverage") or {}).get("campaigns_total", 0),
    }

    campaigns, camp_findings = campaign_analysis(raw, fmt, kpis)
    device_rows = segment_analysis(raw, "device", "segments.device", fmt)
    network_rows = segment_analysis(raw, "network", "segments.ad_network_type", fmt)
    actions, tracking_findings = conversion_tracking(raw, kpis, fmt)
    trend = trend_series(raw)

    findings = []
    findings.extend(account_findings(kpis, fmt, ctx))
    findings.extend(camp_findings)
    findings.extend(segment_findings(device_rows, "Device", fmt))
    findings.extend(segment_findings(network_rows, "Network", fmt))
    findings.extend(tracking_findings)

    quality = validate(raw, kpis, campaigns, trend, fmt)
    if fallback_note:
        quality["warnings"].append(fallback_note)
    if shares["current"].get("coverage", {}).get("share_of_impressions") is not None:
        cov = shares["current"]["coverage"]
        if cov["share_of_impressions"] < 90 and cov["campaigns_reporting"]:
            quality["warnings"].append(
                "Search impression share covers %.0f%% of account impressions (%d of %d "
                "campaigns report it). Campaign types that do not report impression share -- "
                "Performance Max, Display, Video -- are excluded rather than counted as zero."
                % (cov["share_of_impressions"], cov["campaigns_reporting"], cov["campaigns_total"]))

    recommendations = recommend(findings, campaigns, kpis, fmt)

    def of_type(t):
        return [f for f in findings if f["type"] == t]

    top_lists = {}
    for key, dataset in (("keywords", "keywords"), ("search_terms", "search_terms"),
                         ("ad_groups", "ad_groups")):
        rows = (ds.get(dataset) or {}).get("current")
        if rows is None:
            continue
        top_lists[key] = summarize_rows(key, rows)

    analysis = {
        "schema": SCHEMA,
        "generated_at": dt.datetime.now().astimezone().isoformat(timespec="seconds"),
        "source_raw_file": raw.get("_source_path"),
        "api_version": raw.get("api_version"),
        "account": {
            "customer_id": account.get("customer_id"),
            "name": account.get("name"),
            "currency": account.get("currency"),
            "time_zone": account.get("time_zone"),
            "login_customer_id": account.get("login_customer_id"),
            "status": account.get("status"),
            "is_test_account": account.get("is_test_account"),
            "optimization_score": account.get("optimization_score"),
        },
        "periods": {
            "current": periods.get("current"),
            "previous": periods.get("previous"),
            "basis": periods.get("basis"),
            "time_zone": periods.get("time_zone"),
            "comparable": (periods.get("current", {}).get("days")
                           == periods.get("previous", {}).get("days")),
        },
        "kpis": [kpis[k[0]] for k in KPI_SPECS],
        "kpis_by_key": kpis,
        "impression_share_coverage": shares["current"].get("coverage"),
        "campaigns": campaigns,
        "segments": {"device": device_rows, "network": network_rows},
        "conversion_actions": actions,
        "top_lists": top_lists,
        "trend": {"daily": trend},
        "findings": {
            "strengths": of_type("strength"),
            "weaknesses": of_type("weakness"),
            "anomalies": of_type("anomaly"),
            "opportunities": of_type("opportunity"),
            "observations": of_type("observation"),
        },
        "recommended_actions": recommendations,
        "data_quality": quality,
        "charts": [],
        "tables": {
            "kpi": kpi_table(kpis, fmt, periods),
            "campaigns": campaign_table(campaigns, fmt),
            "device": segment_table(device_rows, "Device", fmt),
            "network": segment_table(network_rows, "Network", fmt),
        },
        "thresholds": {
            "material_percent": material_pct,
            "minimum_absolute_change": MIN_ABS,
            "small_sample_conversions": SMALL_SAMPLE_CONVERSIONS,
            "sparse_campaign_clicks": SPARSE_CLICKS,
        },
    }
    return analysis


def summarize_rows(kind, rows):
    """Condense a top-N list into report-ready entries. Row caps stay visible."""
    out = []
    for r in rows[:25]:
        entry = {
            "campaign": ads.field(r, "campaign.name"),
            "ad_group": ads.field(r, "ad_group.name"),
            "cost": ads.micros(r, "metrics.cost_micros"),
            "clicks": ads.num(r, "metrics.clicks"),
            "impressions": ads.num(r, "metrics.impressions"),
            "conversions": ads.num(r, "metrics.conversions"),
            "conversions_value": ads.num(r, "metrics.conversions_value"),
        }
        entry["cost_per_conversion"] = ads.safe_div(entry["cost"], entry["conversions"])
        if kind == "keywords":
            entry["keyword"] = ads.field(r, "ad_group_criterion.keyword.text")
            entry["match_type"] = ads.field(r, "ad_group_criterion.keyword.match_type")
            entry["status"] = ads.field(r, "ad_group_criterion.status")
        elif kind == "search_terms":
            entry["search_term"] = ads.field(r, "search_term_view.search_term")
            entry["status"] = ads.field(r, "search_term_view.status")
        out.append(entry)
    return {"rows": out, "returned": len(rows), "shown": len(out),
            "note": "Ordered by cost, current period only. Not a complete list."}


def main():
    ap = argparse.ArgumentParser(description="Analyse a Google Ads retrieval file.")
    ap.add_argument("--raw", required=True, help="Path to the *_raw.json written by fetch_google_ads.py")
    ap.add_argument("--out", help="Output directory (default: alongside the raw file)")
    ap.add_argument("--material-pct", type=float, default=MATERIAL_PCT,
                    help="Percentage move at or above which a change counts as material (default 10)")
    ap.add_argument("--quiet", action="store_true")
    args = ap.parse_args()

    raw_path = Path(args.raw).expanduser()
    if not raw_path.is_file():
        print("No such retrieval file: %s" % raw_path, file=sys.stderr)
        return 2
    raw = json.loads(raw_path.read_text(encoding="utf-8"))
    raw["_source_path"] = str(raw_path)

    if raw.get("schema") != "reports-google-ads/raw@1":
        print("Unexpected schema %r in %s" % (raw.get("schema"), raw_path), file=sys.stderr)
        return 2
    if not raw.get("periods"):
        print("That retrieval file has no periods -- the run failed before it fetched "
              "anything. Fix the fetch first.", file=sys.stderr)
        return 2

    analysis = build(raw, material_pct=args.material_pct)

    out_dir = Path(args.out).expanduser() if args.out else raw_path.parent
    out_dir.mkdir(parents=True, exist_ok=True)
    stem = raw_path.name.replace("_raw.json", "")
    a_path = out_dir / ("%s_analysis.json" % stem)
    t_path = out_dir / ("%s_tables.md" % stem)
    a_path.write_text(json.dumps(analysis, indent=2), encoding="utf-8")

    tables = analysis["tables"]
    md = ["# KPI and campaign tables",
          "",
          "Account: %s (%s) — currency %s" % (analysis["account"]["name"],
                                              analysis["account"]["customer_id"],
                                              analysis["account"]["currency"]),
          "Current: %s – %s | Previous: %s – %s"
          % (analysis["periods"]["current"]["start"], analysis["periods"]["current"]["end"],
             analysis["periods"]["previous"]["start"], analysis["periods"]["previous"]["end"]),
          "", "## KPI overview", "", tables["kpi"], "", "## Campaigns", "", tables["campaigns"]]
    if tables.get("device"):
        md += ["", "## Device", "", tables["device"]]
    if tables.get("network"):
        md += ["", "## Network", "", tables["network"]]
    t_path.write_text("\n".join(md) + "\n", encoding="utf-8")

    summary = {
        "analysis_file": str(a_path),
        "tables_file": str(t_path),
        "account": analysis["account"]["name"],
        "periods": analysis["periods"],
        "findings": {k: len(v) for k, v in analysis["findings"].items()},
        "recommended_actions": len(analysis["recommended_actions"]),
        "unavailable_metrics": [u["metric"] for u in analysis["data_quality"]["unavailable_metrics"]],
        "warnings": analysis["data_quality"]["warnings"],
    }
    print(json.dumps(summary, indent=2))
    if not args.quiet:
        print("\nwrote %s\nwrote %s" % (a_path, t_path), file=sys.stderr)
    return 0


if __name__ == "__main__":
    sys.exit(main())
