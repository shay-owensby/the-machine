#!/usr/bin/env python3
"""
Turn one raw GA4 retrieval file into the structured analysis the reporting
agent consumes. Reads a file, writes files, talks to no network.

    python3 analyze_ga4.py --raw <data/raw.json>

Produces, alongside the raw file unless --out says otherwise:

    analysis.json        the output contract -- everything the agent needs
    kpis.json            the KPI block on its own, for quick reads
    tables.md            pre-rendered Markdown tables
    acquisition.csv, landing-pages.csv, events.csv, devices.csv,
    daily.csv, geography.csv, ecommerce.csv   (only the ones with data)

Four things this file is strict about, because they are where GA4 reports go
wrong:

  1. **Unavailable is not zero.** Every metric carries an availability state. A
     metric this property does not support stays None all the way through and
     prints as "not available", never as 0, 0.0% or a dash that reads like
     zero. A metric GA4 returned AS zero is a real zero and says so.

  2. **A number is not a verdict.** Direction (up/down) is arithmetic; verdict
     (better/worse) needs to know what the metric means. Sessions falling while
     key events and revenue rise is not a decline, and is labelled ambiguous
     rather than guessed at.

  3. **Correlation is not cause.** Every finding states what was observed. None
     of them says one thing caused another; where a cause is plausible the
     wording is "coincides with", "is associated with", "may indicate",
     "warrants investigation".

  4. **A performance drop and a tracking drop look identical in the data.**
     Anything that could be either is reported as both possibilities, with the
     check that would tell them apart.

Percentage change against a zero or missing baseline is undefined -- not
infinite, not 100%. It is reported as undefined with the reason attached.
"""

import argparse
import csv
import datetime as dt
import json
import statistics
import sys
from pathlib import Path

SCHEMA = "reports-google-analytics/analysis@1"
RAW_SCHEMA = "reports-google-analytics/raw@1"

# ---------------------------------------------------------------------------
# What "material" means. Defaults, overridable per run.
#
# A change is worth a client's attention when it is BOTH proportionally big and
# absolutely big. Ten percent of nothing is nothing, and a 2% move on a large
# property is noise -- reporting either as a finding trains people to ignore
# the report.
# ---------------------------------------------------------------------------

MATERIAL_PCT = 10.0
MIN_ABS = {
    "int": 50.0,          # sessions, users, views, events
    "decimal": 5.0,       # key events, per-session ratios
    "rate": 1.0,          # percentage POINTS
    "currency": 100.0,
    "duration": 5.0,      # seconds
}

# Below these, a segment cannot be judged on rate metrics without saying so.
MIN_SESSIONS_TO_JUDGE = 100
MIN_KEY_EVENTS_TO_JUDGE = 15
SPIKE_Z = 3.5             # robust z-score at which a day is called abnormal

# GA4 returns these as ratios in 0..1. Everything downstream works in
# percentage points, so they are converted once, here, at extraction.
RATE_METRICS = {
    "engagementRate", "bounceRate", "sessionKeyEventRate", "userKeyEventRate",
    "sessionConversionRate", "userConversionRate", "purchaserRate",
    "cartToViewRate", "purchaseToViewRate",
}

# Pre-2024 names -> the names used everywhere downstream. The property's own
# wording is preserved separately so the report can match its interface.
CANONICAL = {
    "conversions": "keyEvents",
    "sessionConversionRate": "sessionKeyEventRate",
    "userConversionRate": "userKeyEventRate",
}

# key, label, unit, better_when, note
KPI_SPECS = [
    ("activeUsers", "Active Users", "int", "higher",
     "People who engaged with the site in the period."),
    ("totalUsers", "Total Users", "int", "higher",
     "Everyone GA4 saw, engaged or not."),
    ("newUsers", "New Users", "int", "context",
     "First-time users. Growth when acquisition is the goal; a churn signal when returning users fall at the same time."),
    ("sessions", "Sessions", "int", "higher",
     "Visits. Volume, not value -- fewer better sessions can be the better period."),
    ("engagedSessions", "Engaged Sessions", "int", "higher",
     "Sessions over 10 seconds, with a key event, or with 2+ page views."),
    ("engagementRate", "Engagement Rate", "rate", "higher",
     "Engaged sessions as a share of sessions."),
    ("bounceRate", "Bounce Rate", "rate", "lower",
     "The exact complement of engagement rate in GA4 -- the two always move together."),
    ("averageSessionDuration", "Avg. Session Duration", "duration", "higher",
     "Mean session length in seconds."),
    ("screenPageViews", "Views", "int", "higher",
     "Page and screen views."),
    ("screenPageViewsPerSession", "Views per Session", "decimal", "higher",
     "Depth of visit."),
    ("sessionsPerUser", "Sessions per User", "decimal", "context",
     "Return frequency. Higher is loyalty; it also rises when new-user acquisition stalls."),
    ("eventCount", "Event Count", "int", "context",
     "Every event fired. Moves with traffic AND with tagging changes -- a big jump with flat traffic is a tagging change until proven otherwise."),
    ("eventsPerSession", "Events per Session", "decimal", "context",
     "Derived: event count / sessions."),
    ("keyEvents", "Key Events", "decimal", "higher",
     "The events this property marks as key. What they MEAN is a property configuration question, not a GA4 one."),
    ("sessionKeyEventRate", "Session Key Event Rate", "rate", "higher",
     "Share of sessions with at least one key event."),
    ("userKeyEventRate", "User Key Event Rate", "rate", "higher",
     "Share of active users with at least one key event."),
]

ECOMMERCE_KPI_SPECS = [
    ("totalRevenue", "Total Revenue", "currency", "higher",
     "Purchase, subscription and ad revenue combined."),
    ("purchaseRevenue", "Purchase Revenue", "currency", "higher",
     "Revenue from purchases only."),
    ("transactions", "Transactions", "int", "higher", "Completed transactions."),
    ("ecommercePurchases", "Ecommerce Purchases", "int", "higher",
     "Purchase events counted by GA4's ecommerce model."),
    ("totalPurchasers", "Purchasers", "int", "higher", "Users who bought."),
    ("firstTimePurchasers", "First-time Purchasers", "int", "higher",
     "Users buying for the first time."),
    ("purchaserRate", "Purchaser Rate", "rate", "higher",
     "Purchasers as a share of active users."),
    ("averagePurchaseRevenue", "Avg. Purchase Revenue", "currency", "higher",
     "Mean revenue per purchase."),
    ("averageRevenuePerUser", "Revenue per User", "currency", "higher",
     "Total revenue divided by active users."),
    ("itemsViewed", "Items Viewed", "int", "context", "Product detail views."),
    ("addToCarts", "Add to Carts", "int", "higher", "Add-to-cart events."),
    ("itemsAddedToCart", "Items Added to Cart", "int", "higher", "Items added, not events."),
    ("checkouts", "Checkouts", "int", "higher", "Checkout starts."),
    ("itemsCheckedOut", "Items Checked Out", "int", "higher", "Items entering checkout."),
    ("itemsPurchased", "Items Purchased", "int", "higher", "Items bought."),
    ("cartToViewRate", "Cart-to-View Rate", "rate", "higher",
     "Items added to cart per item viewed."),
    ("purchaseToViewRate", "Purchase-to-View Rate", "rate", "higher",
     "Items bought per item viewed."),
]

ALL_SPECS = {k: (lbl, unit, better, note) for k, lbl, unit, better, note in
             KPI_SPECS + ECOMMERCE_KPI_SPECS}

PRIORITY_FROM_SEVERITY = {"high": "High", "medium": "Medium", "low": "Low"}


# ---------------------------------------------------------------------------
# Extraction
# ---------------------------------------------------------------------------

def canon(name):
    return CANONICAL.get(name, name)


def normalize(values):
    """Canonical metric names, and rates as percentage points.

    One conversion, in one place. Everything downstream can assume a rate is a
    number out of 100 and a key-event metric is called keyEvents.
    """
    out = {}
    for name, value in (values or {}).items():
        key = canon(name)
        if value is not None and name in RATE_METRICS:
            value = value * 100.0
        out[key] = value
    return out


def report_totals(report):
    """Totals for a no-dimension or aggregated report, normalized."""
    if not report:
        return {}
    if report.get("totals"):
        return normalize(report["totals"])
    if report.get("rows"):
        return normalize(report["rows"][0]["values"])
    return {}


DERIVED_NOTE = {
    "eventsPerSession": "Derived: event count divided by sessions. GA4 does not return this "
                        "metric directly.",
    "screenPageViewsPerSession": "Derived from views and sessions because the property did "
                                 "not return the metric itself.",
    "sessionsPerUser": "Derived from sessions and total users because the property did not "
                       "return the metric itself.",
}


def derive_totals(t, track=None):
    """The handful of KPIs GA4 does not return directly.

    Every value here is arithmetic on figures the API DID return -- no gap is
    filled with an assumption. When `track` is given, the keys that had to be
    derived are recorded so the report can say so.
    """
    t = dict(t)
    ec, sess = t.get("eventCount"), t.get("sessions")
    if ec is not None and sess:
        t["eventsPerSession"] = ec / sess
        if track is not None:
            track.add("eventsPerSession")
    if t.get("screenPageViewsPerSession") is None:
        views = t.get("screenPageViews")
        if views is not None and sess:
            t["screenPageViewsPerSession"] = views / sess
            if track is not None:
                track.add("screenPageViewsPerSession")
    if t.get("sessionsPerUser") is None:
        users = t.get("totalUsers")
        if sess is not None and users:
            t["sessionsPerUser"] = sess / users
            if track is not None:
                track.add("sessionsPerUser")
    return t


def dataset(raw, key):
    return (raw.get("datasets") or {}).get(key) or {}


def segment_rows(raw, key, sort_metric="sessions"):
    """Both periods of a dimension breakdown, joined on the dimension key.

    A key present in one period and not the other is kept with the missing side
    as None -- that is a genuinely new or vanished segment, and it is the most
    interesting row in the table. It is never filled with zeros.
    """
    entry = dataset(raw, key)
    cur, prev = entry.get("current"), entry.get("previous")
    if cur is None and prev is None:
        return None

    index = {}
    order = []

    def ingest(report, period):
        for r in (report or {}).get("rows", []) or []:
            k = " / ".join(r["keys"])
            if k not in index:
                index[k] = {"key": k, "keys": r["keys"], "current": None, "previous": None}
                order.append(k)
            index[k][period] = derive_totals(normalize(r["values"]))

    ingest(cur, "current")
    ingest(prev, "previous")

    rows = [index[k] for k in order]
    rows.sort(key=lambda r: ((r.get("current") or {}).get(sort_metric) or -1), reverse=True)
    return rows


# ---------------------------------------------------------------------------
# Comparison
# ---------------------------------------------------------------------------

def change(current, previous, unit, better_when, key=None, label=None,
           material_pct=MATERIAL_PCT, min_abs=None, note=None):
    """One metric's full comparison record."""
    spec_min = (min_abs or MIN_ABS).get(unit, 0.0)
    rec = {
        "key": key, "label": label, "unit": unit, "better_when": better_when,
        "current": current, "previous": previous,
        "absolute_change": None, "percent_change": None,
        "direction": "unknown", "verdict": "unknown", "material": False,
        "availability": "available", "notes": ([note] if note else []),
    }

    if current is None and previous is None:
        rec["availability"] = "unavailable"
        rec["direction"] = "n/a"
        rec["verdict"] = "unknown"
        rec["notes"].append(
            "Not returned by the API for either period. This is NOT zero -- the property "
            "either does not support the metric or did not report it.")
        return rec

    if current is None or previous is None:
        rec["availability"] = "partial"
        rec["direction"] = "n/a"
        rec["notes"].append(
            "Only the %s period returned this metric, so no comparison is possible."
            % ("current" if current is not None else "previous"))
        return rec

    rec["absolute_change"] = current - previous

    if previous == 0:
        if current == 0:
            rec["percent_change"] = 0.0
            rec["direction"] = "flat"
            rec["verdict"] = "flat"
            rec["notes"].append("Zero in both periods, as reported by GA4.")
            return rec
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
    rec["material"] = (abs(rec["percent_change"]) >= material_pct
                       and abs(rec["absolute_change"]) >= spec_min)
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
    if unit == "duration":
        return "%.0fs" % value
    if unit == "int":
        return "{:,.0f}".format(value)
    return "{:,.2f}".format(value)


# ---------------------------------------------------------------------------
# Formatting for the pre-rendered tables
# ---------------------------------------------------------------------------

SYMBOLS = {"USD": "$", "GBP": "£", "EUR": "€", "CAD": "C$", "AUD": "A$",
           "NZD": "NZ$", "JPY": "¥", "INR": "₹", "ZAR": "R", "SEK": "kr",
           "CHF": "CHF ", "BRL": "R$", "MXN": "MX$"}


class Fmt(object):
    def __init__(self, currency, symbol_override=None):
        self.currency = currency or ""
        self.symbol = symbol_override or SYMBOLS.get(self.currency)

    def money(self, v, dp=2):
        if v is None:
            return "not available"
        s = "{:,.{dp}f}".format(v, dp=dp)
        if self.symbol:
            return "%s%s" % (self.symbol, s)
        return ("%s %s" % (s, self.currency)).strip()

    def duration(self, v):
        if v is None:
            return "not available"
        m, s = divmod(int(round(v)), 60)
        return "%d:%02d" % (m, s)

    def value(self, v, unit):
        if v is None:
            return "not available"
        if unit == "currency":
            return self.money(v)
        if unit == "rate":
            return "%.1f%%" % v
        if unit == "duration":
            return self.duration(v)
        if unit == "int":
            return "{:,.0f}".format(v)
        if unit == "decimal" and abs(v - round(v)) < 1e-6:
            # Key events and per-session ratios come back as floats. A whole
            # number of key events reads as a count, not a measurement.
            return "{:,.0f}".format(v)
        return "{:,.2f}".format(v)

    def delta(self, rec):
        if rec["absolute_change"] is None:
            return "n/a"
        sign = "+" if rec["absolute_change"] > 0 else ""
        if rec["unit"] == "rate":
            return "%s%.1f pp" % (sign, rec["absolute_change"])
        if rec["unit"] == "duration":
            return "%s%s" % (sign, self.duration(abs(rec["absolute_change"])))
        if rec["unit"] == "currency":
            return "%s%s" % (sign, self.money(rec["absolute_change"]))
        if rec["unit"] == "int":
            return "%s{:,.0f}".format(rec["absolute_change"]) % sign
        if abs(rec["absolute_change"] - round(rec["absolute_change"])) < 1e-6:
            return "%s{:,.0f}".format(rec["absolute_change"]) % sign
        return "%s{:,.2f}".format(rec["absolute_change"]) % sign

    def pct(self, rec):
        if rec["availability"] == "unavailable":
            return "n/a"
        if rec["percent_change"] is None:
            if rec["verdict"] == "new":
                return "new (was zero)"
            return "n/a"
        sign = "+" if rec["percent_change"] > 0 else ""
        return "%s%.1f%%" % (sign, rec["percent_change"])


# ---------------------------------------------------------------------------
# Findings
# ---------------------------------------------------------------------------

def finding(kind, fid, title, statement, evidence, severity="medium",
            confidence="high", scope="property", entity=None):
    return {
        "id": fid,
        "type": kind,          # strength | weakness | risk | opportunity | anomaly | observation
        "title": title,
        "statement": statement,
        "evidence": evidence,  # short factual strings, each a number from the data
        "severity": severity,  # high | medium | low
        "confidence": confidence,
        "scope": scope,        # property | acquisition | content | events | device | geo | ecommerce | tracking
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
        rec["label"], fmt.value(rec["current"], rec["unit"]),
        fmt.value(rec["previous"], rec["unit"]), fmt.delta(rec), fmt.pct(rec))


def kpi_findings(kpis, fmt, ecom_state, baseline_empty=False,
                 min_sessions=MIN_SESSIONS_TO_JUDGE):
    """Property-level diagnostics.

    Each rule states what it saw and what it cannot conclude from it.
    """
    out = []
    K = kpis

    if baseline_empty:
        # Nothing to compare against. Every rule below would be dividing this
        # period by an empty one, so none of them run: the honest finding is
        # that there is no baseline.
        return [finding(
            "observation", "no_baseline",
            "The comparison period has no data to compare against",
            "GA4 recorded no sessions in the previous period, so every period-over-period "
            "figure in this report is undefined rather than infinite. Report this period's "
            "absolute numbers and treat them as the first baseline; the next report will be "
            "the first with a genuine comparison.",
            [ev(fmt, K.get("sessions", {})), ev(fmt, K.get("activeUsers", {})),
             ev(fmt, K.get("keyEvents", {}))],
            severity="medium", confidence="high", scope="property")]

    def has(key):
        return K.get(key, {}).get("availability") == "available"

    sessions, users = K.get("sessions", {}), K.get("activeUsers", {})
    ke, ke_rate = K.get("keyEvents", {}), K.get("sessionKeyEventRate", {})
    eng = K.get("engagementRate", {})
    rev = K.get("totalRevenue", {})

    # -- traffic and conversion pulling apart ------------------------------
    if has("sessions") and has("keyEvents"):
        if sessions["direction"] == "up" and ke["verdict"] == "declined" and (
                sessions["material"] or ke["material"]):
            out.append(finding(
                "weakness", "traffic_up_key_events_down",
                "More traffic, fewer key events",
                "Sessions rose while key events fell. The additional traffic did not convert "
                "at the previous rate; that is consistent with a change in traffic mix, a "
                "change in the site, or a change in key-event tracking, and the data alone "
                "does not separate them.",
                [ev(fmt, sessions), ev(fmt, ke), ev(fmt, ke_rate)],
                severity="high", scope="property"))
        elif sessions["direction"] == "down" and ke["verdict"] == "improved":
            out.append(finding(
                "strength", "traffic_down_key_events_up",
                "Fewer sessions, more key events",
                "Sessions fell while key events rose, so the period converted better on less "
                "traffic. A session decline here is not automatically a performance decline.",
                [ev(fmt, sessions), ev(fmt, ke), ev(fmt, ke_rate)],
                severity="medium", scope="property"))
        elif sessions["verdict"] == "improved" and ke["verdict"] == "improved":
            out.append(finding(
                "strength", "traffic_and_key_events_up",
                "Traffic and key events both up",
                "Volume and outcomes moved together, which is growth rather than a mix shift.",
                [ev(fmt, sessions), ev(fmt, ke), ev(fmt, ke_rate)],
                severity="low", scope="property"))
        elif sessions["verdict"] == "declined" and ke["verdict"] == "declined":
            out.append(finding(
                "weakness", "traffic_and_key_events_down",
                "Traffic and key events both down",
                "Both volume and outcomes fell. Check the acquisition section for which "
                "channels lost traffic before treating this as a site or offer problem.",
                [ev(fmt, sessions), ev(fmt, ke)],
                severity="high", scope="property"))

    # -- engagement --------------------------------------------------------
    if has("engagementRate") and eng["material"] and eng["verdict"] in ("improved", "declined"):
        kind = "strength" if eng["verdict"] == "improved" else "weakness"
        out.append(finding(
            kind, "engagement_rate_move",
            "Engagement rate %s %s" % ("up" if eng["direction"] == "up" else "down",
                                       fmt.delta(eng)),
            "Engagement rate moved materially. In GA4 this is the share of sessions lasting "
            "over 10 seconds, firing a key event, or viewing 2+ pages -- so it moves with "
            "traffic quality and with site speed, not only with content.",
            [ev(fmt, eng), ev(fmt, K.get("averageSessionDuration", {})),
             ev(fmt, K.get("screenPageViewsPerSession", {}))],
            severity="medium" if abs(eng["absolute_change"] or 0) < 5 else "high",
            scope="property"))

    # -- key event rate ----------------------------------------------------
    if has("sessionKeyEventRate") and ke_rate["material"] and ke_rate["verdict"] == "declined":
        out.append(finding(
            "weakness", "key_event_rate_decline",
            "Session key event rate fell %s" % fmt.delta(ke_rate),
            "A smaller share of sessions produced a key event. Because a tracking change and "
            "a conversion problem look the same here, check the event section for key events "
            "that stopped firing before treating this as a performance issue.",
            [ev(fmt, ke_rate), ev(fmt, ke), ev(fmt, sessions)],
            severity="high", scope="property"))

    # -- event count vs traffic: the tagging tell --------------------------
    events, sess = K.get("eventCount", {}), K.get("sessions", {})
    if (events.get("availability") == "available" and sess.get("availability") == "available"
            and events.get("percent_change") is not None
            and sess.get("percent_change") is not None):
        gap = events["percent_change"] - sess["percent_change"]
        if abs(gap) >= 40 and abs(events["percent_change"]) >= 25:
            out.append(finding(
                "anomaly", "event_volume_vs_traffic",
                "Event volume moved far more than traffic",
                "Event count changed %.0f%% while sessions changed %.0f%%. Events per session "
                "moving that far in one period is more often a tagging or configuration "
                "change than a behaviour change, and warrants investigation before any of it "
                "is read as user behaviour."
                % (events["percent_change"], sess["percent_change"]),
                [ev(fmt, events), ev(fmt, sess), ev(fmt, K.get("eventsPerSession", {}))],
                severity="medium", confidence="medium", scope="tracking"))

    # -- new vs returning --------------------------------------------------
    new_u, tot_u = K.get("newUsers", {}), K.get("totalUsers", {})
    if (new_u.get("availability") == "available" and tot_u.get("availability") == "available"
            and tot_u.get("current") and tot_u.get("previous")):
        cur_share = (new_u["current"] / tot_u["current"]) * 100
        prev_share = (new_u["previous"] / tot_u["previous"]) * 100
        if abs(cur_share - prev_share) >= 8:
            out.append(finding(
                "observation", "new_user_mix_shift",
                "New-user share moved %.0f points" % (cur_share - prev_share),
                "New users made up %.0f%% of users this period against %.0f%% last period. A "
                "mix shift of this size changes what every engagement and conversion metric "
                "means, because new and returning users behave differently."
                % (cur_share, prev_share),
                ["New users: %s vs %s" % (fmt.value(new_u["current"], "int"),
                                          fmt.value(new_u["previous"], "int")),
                 "Total users: %s vs %s" % (fmt.value(tot_u["current"], "int"),
                                            fmt.value(tot_u["previous"], "int"))],
                severity="low", scope="property"))

    # -- revenue vs traffic ------------------------------------------------
    if ecom_state == "active" and has("totalRevenue") and has("sessions"):
        if rev["verdict"] == "declined" and sessions["verdict"] in ("flat", "improved"):
            out.append(finding(
                "weakness", "revenue_down_traffic_stable",
                "Revenue fell without a traffic fall",
                "Revenue declined while sessions held or grew, so the loss is in conversion "
                "or order value rather than in audience size.",
                [ev(fmt, rev), ev(fmt, sessions),
                 ev(fmt, K.get("averagePurchaseRevenue", {})),
                 ev(fmt, K.get("transactions", {}))],
                severity="high", scope="ecommerce"))
        elif rev["verdict"] == "improved" and rev["material"]:
            out.append(finding(
                "strength", "revenue_up",
                "Revenue up %s" % fmt.pct(rev),
                "Revenue grew materially over the comparison period.",
                [ev(fmt, rev), ev(fmt, K.get("transactions", {})),
                 ev(fmt, K.get("averagePurchaseRevenue", {}))],
                severity="medium", scope="ecommerce"))

    # -- the small-sample guard -------------------------------------------
    #
    # Every rule above is arithmetic on two numbers, and arithmetic does not
    # know when a number is too small to mean anything. A key-event rate that
    # moves from 6 events to 9 is a two-percentage-point swing and also pure
    # noise. Rather than suppress those findings -- the movement did happen --
    # they drop to low severity and low confidence and say why, so nothing
    # built on them can be presented as a confident conclusion.
    property_floor = min_sessions * 10
    thin_traffic = (sessions.get("availability") == "available"
                    and (sessions.get("current") or 0) < property_floor)
    thin_key_events = (ke.get("availability") == "available"
                       and min(ke.get("current") or 0, ke.get("previous") or 0)
                       < MIN_KEY_EVENTS_TO_JUDGE)
    if thin_traffic or thin_key_events:
        reason = []
        if thin_traffic:
            reason.append("the property recorded %s sessions, below the %s-session floor for "
                          "a stable comparison"
                          % (fmt.value(sessions.get("current"), "int"),
                             "{:,}".format(property_floor)))
        if thin_key_events:
            reason.append("key-event volume is in single or low double figures, where a "
                          "difference of a handful of events moves the rate by whole "
                          "percentage points")
        caveat = (" Treat this as an observation rather than a conclusion: %s."
                  % " and ".join(reason))
        for f in out:
            f["severity"] = "low"
            f["confidence"] = "low"
            f["statement"] += caveat
    return out


def segment_findings(rows, label, scope, fmt, min_sessions, total_sessions,
                     material_pct=MATERIAL_PCT, top=5, baseline_empty=False):
    """Winners and losers in a breakdown, with the small-sample guard applied."""
    out = []
    if not rows or baseline_empty:
        return out

    movers = []
    for r in rows:
        cur = (r.get("current") or {}).get("sessions")
        prev = (r.get("previous") or {}).get("sessions")
        rec = change(cur, prev, "int", "higher", key=r["key"], label=r["key"],
                     material_pct=material_pct)
        if rec["material"] or rec["verdict"] == "new":
            movers.append((r, rec))

    movers.sort(key=lambda pair: abs(pair[1]["absolute_change"] or 0), reverse=True)

    for r, rec in movers[:top]:
        cur = r.get("current") or {}
        prev = r.get("previous") or {}
        share = None
        if total_sessions and cur.get("sessions") is not None:
            share = cur["sessions"] / total_sessions * 100
        ke_rec = change(cur.get("keyEvents"), prev.get("keyEvents"), "decimal", "higher",
                        material_pct=material_pct)
        evidence = ["%s sessions: %s vs %s (%s, %s)" % (
            r["key"], fmt.value(cur.get("sessions"), "int"),
            fmt.value(prev.get("sessions"), "int"), fmt.delta(rec), fmt.pct(rec))]
        if share is not None:
            evidence.append("%.1f%% of sessions this period" % share)
        if ke_rec["availability"] == "available":
            evidence.append("key events: %s vs %s (%s)" % (
                fmt.value(ke_rec["current"], "decimal"),
                fmt.value(ke_rec["previous"], "decimal"), fmt.pct(ke_rec)))

        gaining = rec["direction"] == "up" or rec["verdict"] == "new"
        kind = "strength" if gaining else "weakness"
        small = (cur.get("sessions") or 0) < min_sessions and (prev.get("sessions") or 0) < min_sessions
        out.append(finding(
            kind, "%s_move:%s" % (scope, r["key"]),
            "%s %s: sessions %s" % (label, r["key"], "up" if gaining else "down"),
            "%s %s %s sessions %s period over period%s."
            % (label, r["key"], "gained" if gaining else "lost",
               fmt.delta(rec),
               " from a very small base, so the percentage overstates it" if small else ""),
            evidence,
            severity=("low" if small else ("high" if (share or 0) > 15 else "medium")),
            confidence="low" if small else "high",
            scope=scope, entity=r["key"]))
    return out


def landing_page_findings(rows, fmt, min_sessions, ke_available, material_pct=MATERIAL_PCT,
                          baseline_empty=False):
    """High-traffic pages that convert or engage badly, and big movers.

    Pages below the traffic floor are not judged at all: a page with nine
    sessions and no key events has told you nothing.
    """
    out = []
    if not rows:
        return out

    judged = [r for r in rows if ((r.get("current") or {}).get("sessions") or 0) >= min_sessions]
    if not judged:
        out.append(finding(
            "observation", "landing_pages_below_floor",
            "No landing page has enough traffic to judge",
            "Every landing page is below the %d-session floor this period, so page-level "
            "engagement and conversion figures are not stable enough to act on."
            % min_sessions,
            ["Top landing page: %s with %s sessions" % (
                rows[0]["key"], fmt.value((rows[0].get("current") or {}).get("sessions"), "int"))]
            if rows else [],
            severity="low", confidence="high", scope="content"))
        return out

    eng_values = [(r.get("current") or {}).get("engagementRate") for r in judged]
    eng_values = [v for v in eng_values if v is not None]
    median_eng = statistics.median(eng_values) if eng_values else None

    for r in judged[:15]:
        cur, prev = r.get("current") or {}, r.get("previous") or {}
        sess = cur.get("sessions")
        eng = cur.get("engagementRate")
        ke = cur.get("keyEvents")

        if median_eng is not None and eng is not None and eng < median_eng - 15 and sess >= min_sessions * 2:
            out.append(finding(
                "weakness", "landing_weak_engagement:%s" % r["key"],
                "High-traffic landing page with weak engagement: %s" % r["key"],
                "This page takes a large share of entrances but engages a much smaller share "
                "of them than the typical landing page on the property. That is where the "
                "cheapest engagement gains usually are.",
                ["%s: %s sessions, %.1f%% engagement rate against a %.1f%% median across "
                 "landing pages" % (r["key"], fmt.value(sess, "int"), eng, median_eng)]
                + (["key events from this page: %s" % fmt.value(ke, "decimal")]
                   if ke is not None else []),
                severity="medium", scope="content", entity=r["key"]))

        if ke_available and ke is not None and ke == 0 and sess >= min_sessions * 2:
            out.append(finding(
                "weakness", "landing_no_key_events:%s" % r["key"],
                "No key events from a high-traffic landing page: %s" % r["key"],
                "GA4 recorded zero key events from this entry page despite substantial "
                "traffic. Either the page genuinely does not lead to a key event, or the key "
                "event is not attributed to it -- both are worth one check.",
                ["%s: %s sessions, 0 key events" % (r["key"], fmt.value(sess, "int"))],
                severity="medium", confidence="medium", scope="content", entity=r["key"]))

    movers = []
    for r in ([] if baseline_empty else rows):
        cur = (r.get("current") or {}).get("sessions")
        prev = (r.get("previous") or {}).get("sessions")
        if (cur or 0) < min_sessions and (prev or 0) < min_sessions:
            continue
        rec = change(cur, prev, "int", "higher", material_pct=material_pct)
        if rec["material"] or rec["verdict"] == "new":
            movers.append((r, rec))
    movers.sort(key=lambda pair: abs(pair[1]["absolute_change"] or 0), reverse=True)

    for r, rec in movers[:6]:
        gaining = rec["direction"] == "up" or rec["verdict"] == "new"
        out.append(finding(
            "strength" if gaining else "weakness",
            "landing_move:%s" % r["key"],
            "Landing page %s: entrances %s" % (r["key"], "up" if gaining else "down"),
            "Entrances to this page moved materially. A single-page swing of this size "
            "usually traces to one channel, a ranking change, or a campaign starting or "
            "stopping -- the acquisition section is where to confirm which.",
            ["%s: %s vs %s sessions (%s, %s)" % (
                r["key"], fmt.value(rec["current"], "int"), fmt.value(rec["previous"], "int"),
                fmt.delta(rec), fmt.pct(rec))],
            severity="medium", scope="content", entity=r["key"]))
    return out


def device_findings(rows, fmt, min_sessions, ke_available):
    """Device gaps only when there is enough of both to compare."""
    out = []
    if not rows or not ke_available:
        return out
    by_key = {r["key"].lower(): r for r in rows}
    desktop, mobile = by_key.get("desktop"), by_key.get("mobile")
    if not (desktop and mobile):
        return out

    def rate(r):
        cur = r.get("current") or {}
        v = cur.get("sessionKeyEventRate")
        if v is None:
            ke, sess = cur.get("keyEvents"), cur.get("sessions")
            if ke is not None and sess:
                v = ke / sess * 100
        return v, (cur.get("sessions") or 0)

    d_rate, d_sess = rate(desktop)
    m_rate, m_sess = rate(mobile)
    if d_rate is None or m_rate is None:
        return out
    if d_sess < min_sessions or m_sess < min_sessions:
        return out

    gap = d_rate - m_rate
    if abs(gap) < 1.0 or (d_rate == 0 and m_rate == 0):
        return out
    relative = abs(gap) / max(d_rate, m_rate) * 100 if max(d_rate, m_rate) else 0
    if relative < 25:
        return out

    weaker, stronger = ("Mobile", "desktop") if gap > 0 else ("Desktop", "mobile")
    weak_sess = m_sess if gap > 0 else d_sess
    out.append(finding(
        "weakness", "device_key_event_gap",
        "%s converts far below %s" % (weaker, stronger),
        "%s sessions produce key events at %.1f%% against %.1f%% on %s -- a %.0f%% relative "
        "gap. On a property where %s carries %s sessions, closing part of that gap is worth "
        "more than the same effort spent on %s."
        % (weaker, min(d_rate, m_rate), max(d_rate, m_rate), stronger, relative,
           weaker.lower(), fmt.value(weak_sess, "int"), stronger),
        ["Desktop: %s sessions, %.1f%% session key event rate" % (fmt.value(d_sess, "int"), d_rate),
         "Mobile: %s sessions, %.1f%% session key event rate" % (fmt.value(m_sess, "int"), m_rate)],
        severity="high" if relative >= 50 else "medium", scope="device"))
    return out


def event_analysis(raw, fmt, min_sessions, material_pct=MATERIAL_PCT, baseline_empty=False):
    """Which events matter, which changed, and which stopped."""
    rows = segment_rows(raw, "events", sort_metric="eventCount")
    findings = []
    if rows is None:
        return None, findings

    ke_defs = ((raw.get("key_events") or {}).get("definitions")) or []
    declared = set((raw.get("key_events") or {}).get("declared_in_env") or [])
    key_event_names = {d.get("event_name") for d in ke_defs if d.get("event_name")}

    out = []
    for r in rows:
        cur, prev = r.get("current") or {}, r.get("previous") or {}
        rec = change(cur.get("eventCount"), prev.get("eventCount"), "int", "context",
                     key=r["key"], label=r["key"], material_pct=material_pct)
        is_key = r["key"] in key_event_names or (cur.get("keyEvents") or 0) > 0
        out.append({
            "event_name": r["key"],
            "is_key_event": bool(is_key),
            "declared_primary": r["key"] in declared,
            "current": cur, "previous": prev,
            "count_change": rec,
        })

    # Automatic GA4 events carry no business meaning on their own; naming them
    # keeps the report from presenting page_view growth as a conversion story.
    AUTOMATIC = {"page_view", "session_start", "first_visit", "user_engagement",
                 "scroll", "click", "view_search_results", "file_download",
                 "video_start", "video_progress", "video_complete", "form_start",
                 "form_submit"}

    for e in ([] if baseline_empty else out):
        name = e["event_name"]
        cur_count = (e["current"] or {}).get("eventCount")
        prev_count = (e["previous"] or {}).get("eventCount")

        # Stopped firing: present before, absent or zero now.
        if prev_count and prev_count >= 25 and (cur_count in (None, 0)):
            findings.append(finding(
                "anomaly", "event_stopped:%s" % name,
                "Event stopped firing: %s" % name,
                "`%s` fired %s times last period and %s this period. An event going to zero "
                "is far more often a tag, consent or release change than a behaviour change, "
                "and it should be confirmed in the tag setup before any of it is read as "
                "performance."
                % (name, fmt.value(prev_count, "int"),
                   "not at all" if cur_count is None else "zero times"),
                ["%s: %s -> %s events" % (name, fmt.value(prev_count, "int"),
                                          fmt.value(cur_count, "int") if cur_count is not None
                                          else "no rows returned")],
                severity="high" if e["is_key_event"] else "medium",
                confidence="medium", scope="tracking", entity=name))

        # Newly appearing.
        elif (prev_count in (None, 0)) and cur_count and cur_count >= 50:
            findings.append(finding(
                "observation", "event_new:%s" % name,
                "New event: %s" % name,
                "`%s` did not appear last period and fired %s times this period. That is "
                "normally a new tag or a new feature; confirm which before reading the "
                "volume as a change in behaviour."
                % (name, fmt.value(cur_count, "int")),
                ["%s: no rows last period, %s events this period"
                 % (name, fmt.value(cur_count, "int"))],
                severity="low", confidence="medium", scope="tracking", entity=name))

        # Big swings on established events.
        elif (e["count_change"]["availability"] == "available"
              and e["count_change"]["percent_change"] is not None
              and abs(e["count_change"]["percent_change"]) >= 60
              and (prev_count or 0) >= 100):
            sev = "high" if e["is_key_event"] else "low"
            findings.append(finding(
                "anomaly" if abs(e["count_change"]["percent_change"]) >= 150 else "observation",
                "event_swing:%s" % name,
                "Event volume swung %s: %s" % (fmt.pct(e["count_change"]), name),
                "`%s` moved %s period over period. %s"
                % (name, fmt.pct(e["count_change"]),
                   "It is a key event, so this moves the conversion figures directly."
                   if e["is_key_event"] else
                   "It is an automatically collected event, so it tracks traffic and tagging "
                   "rather than intent." if name in AUTOMATIC else
                   "Confirm whether the underlying tag or page changed."),
                ["%s: %s vs %s events (%s)" % (
                    name, fmt.value(cur_count, "int"), fmt.value(prev_count, "int"),
                    fmt.pct(e["count_change"]))],
                severity=sev, confidence="medium",
                scope="events" if e["is_key_event"] else "tracking", entity=name))

    key_events = [e for e in out if e["is_key_event"]]
    if ke_defs and not key_events:
        findings.append(finding(
            "risk", "key_events_defined_but_silent",
            "Key events are configured but none fired",
            "This property defines %d key event(s) and none of them recorded activity in the "
            "reporting period. Either the events are not being sent, or the actions did not "
            "happen. This must be resolved before any conversion figure in the report is "
            "trusted." % len(ke_defs),
            ["Defined key events: %s" % ", ".join(sorted(n for n in key_event_names if n))],
            severity="high", confidence="high", scope="tracking"))

    return {
        "events": out[:60],
        "key_event_definitions": ke_defs,
        "key_event_names": sorted(n for n in key_event_names if n),
        "declared_primary_events": sorted(declared),
        "meaning_note": (
            "GA4 records that these events are marked as key events. It does not record what "
            "they MEAN to the business. Where a key event's business meaning is not "
            "documented in the client's configuration, the report must say the meaning is "
            "undetermined rather than calling it a lead or a sale."),
    }, findings


# ---------------------------------------------------------------------------
# Trend and anomalies
# ---------------------------------------------------------------------------

def trend_analysis(raw, fmt, ke_available):
    """Daily series, gaps, and days that are genuinely abnormal.

    A robust z-score (median and median absolute deviation) is used rather than
    mean and standard deviation, because one spike inflates a standard
    deviation enough to hide itself.
    """
    entry = dataset(raw, "daily")
    cur, prev = entry.get("current"), entry.get("previous")
    findings = []
    if cur is None and prev is None:
        return None, findings

    def series(report, window):
        if not report:
            return []
        by_date = {}
        for r in report.get("rows", []) or []:
            if not r["keys"]:
                continue
            raw_date = r["keys"][0]
            try:
                d = dt.date(int(raw_date[0:4]), int(raw_date[4:6]), int(raw_date[6:8])).isoformat()
            except (ValueError, IndexError):
                d = raw_date
            by_date[d] = derive_totals(normalize(r["values"]))
        out = []
        start = dt.date.fromisoformat(window["start"])
        end = dt.date.fromisoformat(window["end"])
        day = start
        while day <= end:
            iso = day.isoformat()
            out.append({"date": iso, "values": by_date.get(iso), "returned": iso in by_date})
            day += dt.timedelta(days=1)
        return out

    periods = raw["periods"]
    current_series = series(cur, periods["current"])
    previous_series = series(prev, periods["previous"])

    missing = [d["date"] for d in current_series if not d["returned"]]
    if missing:
        findings.append(finding(
            "anomaly", "daily_missing_days",
            "%d day(s) returned no data" % len(missing),
            "GA4 returned no row at all for %s. A day with no rows is a day with no recorded "
            "events -- which is either a genuine traffic gap or a collection outage. It is "
            "not zero traffic that can be reported as performance."
            % (", ".join(missing[:6]) + (" and others" if len(missing) > 6 else "")),
            ["Days with no data: %s" % ", ".join(missing[:10])],
            severity="high" if len(missing) > 1 else "medium",
            confidence="medium", scope="tracking"))

    def anomalies(series_rows, metric, label):
        values = [(d["date"], (d["values"] or {}).get(metric)) for d in series_rows]
        present = [(d, v) for d, v in values if v is not None]
        if len(present) < 10:
            return []
        nums = [v for _, v in present]
        med = statistics.median(nums)
        deviations = [abs(v - med) for v in nums]
        mad = statistics.median(deviations)
        if mad == 0:
            return []
        found = []
        for d, v in present:
            z = 0.6745 * (v - med) / mad
            if abs(z) >= SPIKE_Z:
                found.append({"date": d, "metric": metric, "label": label, "value": v,
                              "median": med, "z": round(z, 2),
                              "direction": "spike" if z > 0 else "drop"})
        return found

    spikes = []
    for metric, label in (("sessions", "Sessions"), ("keyEvents", "Key Events"),
                          ("totalRevenue", "Revenue")):
        spikes.extend(anomalies(current_series, metric, label))

    for a in spikes[:6]:
        findings.append(finding(
            "anomaly", "daily_%s_%s" % (a["direction"], a["date"]),
            "%s %s on %s" % (a["label"], a["direction"], a["date"]),
            "%s on %s was %s against a period median of %s. One abnormal day does not move a "
            "30-day total much, but it does distort a daily chart and it is worth knowing "
            "what happened -- a campaign send, a press mention, a bot, or an outage."
            % (a["label"], a["date"], fmt.value(a["value"], "int"),
               fmt.value(a["median"], "int")),
            ["%s on %s: %s (period median %s, robust z %.1f)"
             % (a["label"], a["date"], fmt.value(a["value"], "int"),
                fmt.value(a["median"], "int"), a["z"])],
            severity="low", confidence="medium", scope="property"))

    # Sustained direction: compare the two halves of the current period.
    def halves(metric):
        vals = [(d["values"] or {}).get(metric) for d in current_series]
        vals = [v for v in vals if v is not None]
        if len(vals) < 14:
            return None
        mid = len(vals) // 2
        first, second = vals[:mid], vals[mid:]
        if not sum(first):
            return None
        return (sum(second) / len(second)) / (sum(first) / len(first)) - 1

    drift = halves("sessions")
    if drift is not None and abs(drift) >= 0.25:
        findings.append(finding(
            "observation", "trend_within_period",
            "Traffic %s through the period" % ("built" if drift > 0 else "faded"),
            "Daily sessions in the second half of the period ran %.0f%% %s the first half. "
            "The period total hides that; where the period ends matters for what happens "
            "next." % (abs(drift) * 100, "above" if drift > 0 else "below"),
            ["Second-half daily average vs first half: %s%.0f%%"
             % ("+" if drift > 0 else "-", abs(drift) * 100)],
            severity="medium", scope="property"))

    return {
        "current": current_series,
        "previous": previous_series,
        "missing_days_current": missing,
        "anomalies": spikes,
        "within_period_drift": drift,
        "metrics": sorted({m for d in current_series if d["values"] for m in d["values"]}),
    }, findings


# ---------------------------------------------------------------------------
# Ecommerce
# ---------------------------------------------------------------------------

def ecommerce_analysis(raw, kpis, fmt, material_pct=MATERIAL_PCT):
    state = (raw.get("ecommerce") or {}).get("state")
    findings = []
    if state != "active":
        return {"state": state, "reason": (raw.get("ecommerce") or {}).get("reason"),
                "included": False}, findings

    funnel_keys = [("itemsViewed", "Items viewed"), ("itemsAddedToCart", "Items added to cart"),
                   ("itemsCheckedOut", "Items checked out"), ("itemsPurchased", "Items purchased")]
    funnel = []
    prev_step = None
    for key, label in funnel_keys:
        rec = kpis.get(key)
        if not rec or rec["availability"] != "available":
            continue
        step = {"key": key, "label": label, "current": rec["current"],
                "previous": rec["previous"], "step_rate_current": None,
                "step_rate_previous": None}
        if prev_step and prev_step["current"]:
            step["step_rate_current"] = rec["current"] / prev_step["current"] * 100
        if prev_step and prev_step["previous"]:
            step["step_rate_previous"] = rec["previous"] / prev_step["previous"] * 100
        funnel.append(step)
        prev_step = step

    for step in funnel:
        cur_r, prev_r = step["step_rate_current"], step["step_rate_previous"]
        if cur_r is None or prev_r is None:
            continue
        drop = prev_r - cur_r
        if drop >= 5 and prev_r > 0:
            findings.append(finding(
                "weakness", "ecom_step_drop:%s" % step["key"],
                "Progression to %s weakened" % step["label"].lower(),
                "The share of items moving to this step fell from %.1f%% to %.1f%%. A step "
                "rate falling while the step above holds points at that step, not at traffic."
                % (prev_r, cur_r),
                ["%s: %s vs %s (step rate %.1f%% vs %.1f%%)"
                 % (step["label"], fmt.value(step["current"], "int"),
                    fmt.value(step["previous"], "int"), cur_r, prev_r)],
                severity="high" if drop >= 10 else "medium", scope="ecommerce"))

    aov = kpis.get("averagePurchaseRevenue", {})
    tx = kpis.get("transactions", {})
    if (aov.get("availability") == "available" and tx.get("availability") == "available"
            and aov.get("material") and tx.get("material")
            and aov["direction"] != tx["direction"]):
        findings.append(finding(
            "observation", "ecom_aov_vs_volume",
            "Order value and order count moved in opposite directions",
            "Average purchase revenue went %s while transactions went %s. Revenue is being "
            "held up (or held back) by basket size rather than by demand."
            % (aov["direction"], tx["direction"]),
            [ev(fmt, aov), ev(fmt, tx), ev(fmt, kpis.get("purchaseRevenue", {}))],
            severity="medium", scope="ecommerce"))

    return {
        "state": state,
        "included": True,
        "funnel": funnel,
        "revenue_by_channel": segment_rows(raw, "revenue_by_channel", sort_metric="totalRevenue"),
        "revenue_by_device": segment_rows(raw, "revenue_by_device", sort_metric="totalRevenue"),
        "items": segment_rows(raw, "items", sort_metric="itemsPurchased"),
        "note": "Revenue figures are in the property's reporting currency (%s) and reflect "
                "GA4's own attribution model, which will not tie exactly to a payment "
                "processor." % (raw.get("property", {}).get("currency") or "unknown"),
    }, findings


# ---------------------------------------------------------------------------
# Data quality
# ---------------------------------------------------------------------------

def data_quality(raw, kpis, sections, fmt, min_sessions):
    checks = []
    warnings = list(raw.get("warnings") or [])
    unavailable = []

    def check(name, status, detail):
        checks.append({"check": name, "status": status, "detail": detail})

    for key, rec in kpis.items():
        if rec["availability"] == "unavailable":
            unavailable.append({"metric": rec["label"] or key, "api_name": key,
                                "reason": "not returned by this property for either period"})

    seen_unavailable = {u["api_name"] for u in unavailable}
    for u in (raw.get("schema_support") or {}).get("unsupported_metrics") or []:
        if u["metric"] in seen_unavailable:
            continue
        seen_unavailable.add(u["metric"])
        unavailable.append({"metric": u["metric"], "api_name": u["metric"],
                            "reason": u.get("reason")})

    # -- periods -----------------------------------------------------------
    periods = raw["periods"]
    comparable = periods["current"]["days"] == periods["previous"]["days"]
    check("Comparable periods",
          "pass" if comparable else "fail",
          "Current %s..%s (%d days) vs previous %s..%s (%d days)."
          % (periods["current"]["start"], periods["current"]["end"], periods["current"]["days"],
             periods["previous"]["start"], periods["previous"]["end"], periods["previous"]["days"]))

    # -- comparison baseline ----------------------------------------------
    prev_sessions = kpis.get("sessions", {}).get("previous")
    if prev_sessions in (None, 0):
        check("Comparison period has data", "warn",
              "The previous period recorded %s. Percentage change is undefined against an "
              "empty baseline, and this report is a first baseline rather than a comparison."
              % ("no sessions" if prev_sessions == 0 else "no session figure at all"))
        warnings.append(
            "The comparison period has no traffic, so every percentage change is undefined. "
            "Report absolute figures and say plainly that there is no comparable prior "
            "period -- never print a change of 100% or infinity.")
    else:
        check("Comparison period has data", "pass",
              "%s sessions in the comparison period." % fmt.value(prev_sessions, "int"))

    # -- volume floor ------------------------------------------------------
    # The property-level floor is an order of magnitude above the per-segment
    # one: a property can clear 100 sessions and still be far too small for a
    # 30-day comparison to mean anything.
    property_floor = min_sessions * 10
    sessions = kpis.get("sessions", {})
    if sessions.get("availability") == "available":
        low = (sessions["current"] or 0) < property_floor
        check("Enough traffic to draw conclusions",
              "warn" if low else "pass",
              "%s sessions in the current period against a %d-session floor for a stable "
              "property-level comparison (%d per segment)."
              % (fmt.value(sessions["current"], "int"), property_floor, min_sessions))
        if low:
            warnings.append(
                "The property recorded %s sessions in %d days. Rate metrics, segment splits "
                "and page-level figures are volatile at that volume; percentage changes will "
                "look dramatic and mean little. Prefer absolute numbers and avoid strong "
                "conclusions."
                % (fmt.value(sessions["current"], "int"), periods["current"]["days"]))
        if sessions["current"] == 0:
            warnings.append(
                "ZERO sessions were recorded in the current period. Do not report this as a "
                "performance result -- establish first whether tracking is live.")
    else:
        check("Enough traffic to draw conclusions", "fail",
              "Sessions were not returned at all, so nothing below can be volume-weighted.")

    # -- key events --------------------------------------------------------
    ke = kpis.get("keyEvents", {})
    ke_defs = (raw.get("key_events") or {}).get("definitions")
    naming = (raw.get("key_events") or {}).get("metric_naming")
    if ke.get("availability") == "unavailable":
        check("Key events retrievable", "fail",
              "No key-event metric exists in this property's schema, so conversion "
              "performance cannot be reported at all.")
    elif ke.get("current") in (0, None) and ke.get("previous") in (0, None):
        check("Key events recorded", "warn",
              "GA4 returned zero key events in both periods. Either this property records no "
              "conversions, or key events are not configured or not firing.")
        warnings.append(
            "Zero key events in both periods. The conversion sections of the report must say "
            "the property recorded no key events -- not that conversions fell.")
    else:
        check("Key events recorded", "pass",
              "%s key events this period, under the property's `%s` metric naming."
              % (fmt.value(ke.get("current"), "decimal"), naming or "unknown"))

    if ke_defs is None:
        check("Key event definitions readable", "warn",
              "The Admin API did not return key-event definitions, so which events count as "
              "key events is unknown. Their business meaning cannot be stated.")
    elif not ke_defs:
        check("Key event definitions readable", "warn",
              "This property has no key events configured.")
    else:
        check("Key event definitions readable", "pass",
              "%d key event(s) defined: %s" % (
                  len(ke_defs), ", ".join(d.get("event_name") or "?" for d in ke_defs[:8])))

    # -- (not set) and (other) ---------------------------------------------
    for section_key, rows in (("acquisition channels", (sections.get("acquisition") or {}).get("session_channels")),
                              ("landing pages", (sections.get("content") or {}).get("landing_pages")),
                              ("source / medium", (sections.get("acquisition") or {}).get("source_medium"))):
        if not rows:
            continue
        total = sum((r.get("current") or {}).get("sessions") or 0 for r in rows)
        if not total:
            continue
        for r in rows:
            label = (r["key"] or "").strip().lower()
            if label in ("(not set)", "(other)", "(not provided)", ""):
                share = ((r.get("current") or {}).get("sessions") or 0) / total * 100
                if share >= 5:
                    status = "fail" if share >= 20 else "warn"
                    check("Unattributed rows in %s" % section_key, status,
                          "%.1f%% of %s sessions sit in `%s`. Rows in that bucket cannot be "
                          "acted on, and at this share they distort every split below."
                          % (share, section_key, r["key"] or "(blank)"))
                    warnings.append(
                        "%.1f%% of sessions in the %s breakdown are `%s`. GA4 puts traffic "
                        "there when it exceeds a cardinality limit or cannot be attributed; "
                        "shares of total in that table do not add up to the property total."
                        % (share, section_key, r["key"] or "(blank)"))

    # -- direct traffic surge ----------------------------------------------
    channels = (sections.get("acquisition") or {}).get("session_channels") or []
    direct = next((r for r in channels if (r["key"] or "").lower() == "direct"), None)
    if direct:
        cur = (direct.get("current") or {}).get("sessions")
        prev = (direct.get("previous") or {}).get("sessions")
        if cur and prev and prev > 0 and (cur - prev) / prev >= 0.30 and (cur - prev) >= 100:
            check("Direct traffic stability", "warn",
                  "Direct sessions rose %.0f%%. A large direct increase is as often lost "
                  "attribution -- missing UTMs, a redirect stripping parameters, an app or "
                  "email client hiding the referrer -- as it is genuine direct demand."
                  % ((cur - prev) / prev * 100))
            warnings.append(
                "Direct traffic rose %.0f%% (%s to %s sessions). Treat part of that as "
                "possible attribution loss from other channels until UTM tagging and "
                "redirects have been checked."
                % ((cur - prev) / prev * 100, fmt.value(prev, "int"), fmt.value(cur, "int")))

    # -- engagement / bounce complement ------------------------------------
    eng, bounce = kpis.get("engagementRate", {}), kpis.get("bounceRate", {})
    if (eng.get("availability") == "available" and bounce.get("availability") == "available"
            and eng.get("current") is not None and bounce.get("current") is not None):
        total = eng["current"] + bounce["current"]
        if abs(total - 100) < 0.5:
            check("Engagement and bounce rate", "pass",
                  "They sum to 100%% as GA4 defines them, so they are one finding, not two. "
                  "Report whichever the client's team uses.")

    # -- tracking outage shape ---------------------------------------------
    trend = sections.get("trends") or {}
    if trend.get("missing_days_current"):
        check("Continuous daily collection", "fail",
              "%d day(s) in the current period returned no rows: %s. Any period total below "
              "is missing those days."
              % (len(trend["missing_days_current"]), ", ".join(trend["missing_days_current"][:8])))
        warnings.append(
            "%d day(s) in the current period returned no data (%s). Period totals are missing "
            "those days, so the period-over-period comparison understates this period by an "
            "unknown amount. Establish whether this was an outage before attributing any "
            "decline to performance."
            % (len(trend["missing_days_current"]), ", ".join(trend["missing_days_current"][:8])))
    elif trend.get("current"):
        check("Continuous daily collection", "pass",
              "Every day in the current period returned data.")

    # -- ecommerce ---------------------------------------------------------
    ecom = raw.get("ecommerce") or {}
    check("Ecommerce data",
          {"active": "pass", "no_data": "info"}.get(ecom.get("state"), "warn"),
          (ecom.get("reason") or "Ecommerce state undetermined.")
          + (" The ecommerce section is omitted from the report."
             if ecom.get("state") != "active" else ""))

    # -- API failures ------------------------------------------------------
    errors = raw.get("errors") or []
    if errors:
        check("All requested datasets retrieved", "fail",
              "%d request(s) failed: %s" % (
                  len(errors), "; ".join("%s (%s)" % (e.get("dataset"), e.get("message"))
                                         for e in errors[:4])))
    else:
        check("All requested datasets retrieved", "pass", "No API request failed.")

    if not (raw.get("schema_support") or {}).get("metadata_loaded"):
        check("Property schema loaded", "warn",
              "The property metadata could not be read, so requests were not filtered against "
              "this property's real schema.")
    else:
        check("Property schema loaded", "pass",
              "%d dimensions and %d metrics available; %d custom dimensions, %d custom metrics."
              % ((raw["schema_support"].get("dimension_count") or 0),
                 (raw["schema_support"].get("metric_count") or 0),
                 len(raw["schema_support"].get("custom_dimensions") or []),
                 len(raw["schema_support"].get("custom_metrics") or [])))

    return {
        "checks": checks,
        "warnings": warnings,
        "unavailable_metrics": unavailable,
        "api_errors": errors,
        "periods_comparable": comparable,
        "material_thresholds": {"percent": MATERIAL_PCT, "absolute": MIN_ABS,
                                "min_sessions_to_judge": min_sessions},
    }


# ---------------------------------------------------------------------------
# Recommendations
# ---------------------------------------------------------------------------

def recommend(findings, sections, kpis, fmt, ecom_state):
    """One action per finding that supports one, with the evidence attached.

    No finding, no recommendation. A recommendation that is not traceable to a
    number in this file does not get written.
    """
    out = []

    def add(fid, action, reason, evidence, impact, priority, confidence="high"):
        out.append({
            "action": action, "reason": reason, "evidence": evidence,
            "expected_impact": impact, "priority": priority, "confidence": confidence,
            "from_finding": fid,
        })

    by_id = {f["id"]: f for f in findings}
    ke_rate = kpis.get("sessionKeyEventRate", {})
    sessions = kpis.get("sessions", {})

    for f in findings:
        fid, sev = f["id"], f["severity"]
        prio = PRIORITY_FROM_SEVERITY.get(sev, "Medium")

        if fid == "traffic_up_key_events_down":
            add(fid,
                "Before changing anything on the site, verify the key-event tags fired "
                "continuously across both periods, then split the session key event rate by "
                "channel and landing page to find where the new traffic landed.",
                "Traffic grew and key events did not follow it. That is either a mix problem "
                "(new traffic of lower intent) or a measurement problem, and the two need "
                "different owners.",
                f["evidence"],
                "Either a corrected conversion baseline, or a named channel and page to fix.",
                "High")

        elif fid == "key_event_rate_decline":
            add(fid,
                "Compare the session key event rate by landing page and by device for both "
                "periods, and check whether any key event stopped firing mid-period.",
                "The share of sessions producing a key event fell materially. Isolating "
                "where it fell separates a tracking break from a genuine conversion decline.",
                f["evidence"],
                "Recovering the previous rate on current traffic would return roughly %s key "
                "events per 30 days." % (
                    fmt.value(abs((ke_rate.get("absolute_change") or 0) / 100.0
                                  * (sessions.get("current") or 0)), "decimal")
                    if ke_rate.get("absolute_change") and sessions.get("current") else "the lost volume"),
                "High")

        elif fid.startswith("event_stopped:"):
            name = f["entity"]
            add(fid,
                "Check the tag, trigger and consent conditions for `%s` in Google Tag Manager "
                "(or the site code) and confirm the date it stopped." % name,
                "An event that goes from steady volume to nothing is a collection failure "
                "until proven otherwise, and every conversion figure that depends on it is "
                "wrong until it is fixed.",
                f["evidence"],
                "Restored measurement, and a corrected view of whether performance actually "
                "changed.",
                "High", confidence="medium")

        elif fid == "device_key_event_gap":
            add(fid,
                "Run the weaker device's top three landing pages through a mobile usability "
                "and page-speed check, and compare the key-event funnel step by step against "
                "the stronger device.",
                "A relative conversion gap of this size on a device carrying meaningful "
                "traffic is usually a small number of concrete friction points, not a broad "
                "design problem.",
                f["evidence"],
                "Closing even a quarter of the gap on the weaker device's current sessions "
                "would add key events without any additional traffic.",
                "High" if sev == "high" else "Medium")

        elif fid.startswith("landing_weak_engagement:"):
            add(fid,
                "Review %s against the property's better-engaging entry pages: load time, "
                "above-the-fold match to the traffic source's promise, and the first action "
                "available." % f["entity"],
                "It receives enough entrances to matter and engages a materially smaller "
                "share of them than the typical landing page here.",
                f["evidence"],
                "Bringing this page to the property's median engagement rate would convert a "
                "measurable share of its existing entrances into engaged sessions.",
                prio)

        elif fid.startswith("landing_no_key_events:"):
            add(fid,
                "Confirm whether a key event is reachable from %s at all, and whether the "
                "key event fires on the page it completes on." % f["entity"],
                "Substantial entrances with zero recorded key events is either a page with no "
                "conversion path or a page whose conversions are not attributed to it.",
                f["evidence"],
                "Either a corrected attribution picture or a clear case for adding a "
                "conversion path to a page that already has traffic.",
                prio, confidence="medium")

        elif fid.startswith("landing_move:") and f["type"] == "weakness":
            add(fid,
                "Trace the entrance loss on %s to a channel: compare its source/medium split "
                "across the two periods, and check for a ranking, redirect or campaign change "
                "on that URL." % f["entity"],
                "A single page losing this many entrances is usually one identifiable cause, "
                "and it is recoverable if found early.",
                f["evidence"],
                "Recovering the lost entrances on a page that already converts.",
                prio)

        elif fid.startswith("channel_move:") or fid.startswith("acquisition_move:"):
            entity = f["entity"]
            if f["type"] == "weakness":
                add(fid,
                    "Diagnose the %s decline before reallocating budget or effort: check "
                    "whether sessions fell across all landing pages or on specific ones, and "
                    "whether the channel's key event rate held." % entity,
                    "A channel losing volume while holding its conversion rate is a supply "
                    "problem; one losing conversion rate is a relevance or landing-page "
                    "problem. The fix differs.",
                    f["evidence"],
                    "A specific cause for the largest single source of lost sessions this "
                    "period.",
                    prio)
            else:
                add(fid,
                    "Confirm the %s gain is durable (not a single spike day) and, if it is, "
                    "resource it: it is the channel currently returning the most incremental "
                    "sessions." % entity,
                    "Growth concentrated in one channel is the cheapest thing to extend, and "
                    "the easiest to lose by not noticing it.",
                    f["evidence"],
                    "Compounding an already-working channel rather than starting a new one.",
                    "Medium")

        elif fid.startswith("ecom_step_drop:"):
            add(fid,
                "Instrument and review the checkout step that lost progression: confirm the "
                "step's events still fire, then test the step itself on mobile.",
                "A step rate falling while the step above it holds points at that step "
                "specifically.",
                f["evidence"],
                "Recovering step progression converts existing demand, with no traffic cost.",
                "High" if sev == "high" else "Medium")

        elif fid == "revenue_down_traffic_stable":
            add(fid,
                "Split revenue by channel and by device across both periods, and check "
                "average purchase revenue against transaction count to see whether the loss "
                "is in basket size or in order count.",
                "Revenue fell without a traffic fall, so the cause is in conversion or order "
                "value -- both of which are addressable without buying more traffic.",
                f["evidence"],
                "A named cause for the revenue gap rather than a traffic response to it.",
                "High")

        elif fid == "key_events_defined_but_silent":
            add(fid,
                "Treat the conversion reporting as unavailable until the key events are "
                "confirmed firing: test each defined key event in GA4 DebugView or Realtime.",
                "The property defines key events and none recorded activity. Reporting zero "
                "conversions from this state would be reporting a measurement failure as a "
                "business result.",
                f["evidence"],
                "Working conversion measurement, and an honest baseline for the next period.",
                "High")

        elif fid == "event_volume_vs_traffic":
            add(fid,
                "Diff the tag configuration between the two periods before reading any "
                "event-based metric: list events by volume in both periods and identify which "
                "ones account for the gap.",
                "Events per session moving this far in one period is usually a tagging "
                "change, and it silently changes engagement and conversion metrics.",
                f["evidence"],
                "Confidence that the period-over-period comparison is measuring the same "
                "thing twice.",
                "Medium", confidence="medium")

        elif fid == "daily_missing_days":
            add(fid,
                "Establish what happened on the days with no data before publishing any "
                "period total: check the site was up, the tag was present, and consent "
                "settings did not change.",
                "Missing days pull down every total in the report, and attributing that to "
                "performance would be wrong.",
                f["evidence"],
                "Either a corrected total or a documented reason the period is short.",
                "High", confidence="medium")

    # Deduplicate by action text, keeping the highest priority instance.
    rank = {"High": 0, "Medium": 1, "Low": 2}
    seen = {}
    for r in out:
        prev = seen.get(r["action"])
        if prev is None or rank.get(r["priority"], 3) < rank.get(prev["priority"], 3):
            seen[r["action"]] = r
    ordered = sorted(seen.values(), key=lambda r: rank.get(r["priority"], 3))
    return ordered


# ---------------------------------------------------------------------------
# Tables
# ---------------------------------------------------------------------------

def kpi_table(kpis, order, fmt, periods):
    head = ("| KPI | Current %s days | Previous %s days | Absolute change | %% change |\n"
            "|---|---:|---:|---:|---:|"
            % (periods["current"]["days"], periods["previous"]["days"]))
    lines = [head]
    for key in order:
        rec = kpis.get(key)
        if not rec or rec["availability"] == "unavailable":
            continue
        lines.append("| %s | %s | %s | %s | %s |" % (
            rec["label"], fmt.value(rec["current"], rec["unit"]),
            fmt.value(rec["previous"], rec["unit"]), fmt.delta(rec), fmt.pct(rec)))
    return "\n".join(lines)


def segment_table(rows, label, fmt, ke_available, limit=10, revenue=False):
    if not rows:
        return None
    cols = ["| %s | Sessions | Prev sessions | Change | Engagement rate |" % label,
            "|---|---:|---:|---:|---:|"]
    if ke_available:
        cols[0] = cols[0][:-1] + " Key events | Key event rate |"
        cols[1] = cols[1][:-1] + "---:|---:|"
    if revenue:
        cols[0] = cols[0][:-1] + " Revenue |"
        cols[1] = cols[1][:-1] + "---:|"
    lines = cols
    for r in rows[:limit]:
        cur, prev = r.get("current") or {}, r.get("previous") or {}
        rec = change(cur.get("sessions"), prev.get("sessions"), "int", "higher")
        row = "| %s | %s | %s | %s | %s |" % (
            r["key"], fmt.value(cur.get("sessions"), "int"),
            fmt.value(prev.get("sessions"), "int"), fmt.pct(rec),
            fmt.value(cur.get("engagementRate"), "rate"))
        if ke_available:
            rate = cur.get("sessionKeyEventRate")
            if rate is None and cur.get("keyEvents") is not None and cur.get("sessions"):
                rate = cur["keyEvents"] / cur["sessions"] * 100
            row = row[:-1] + " %s | %s |" % (fmt.value(cur.get("keyEvents"), "decimal"),
                                             fmt.value(rate, "rate"))
        if revenue:
            row = row[:-1] + " %s |" % fmt.value(cur.get("totalRevenue"), "currency")
        lines.append(row)
    return "\n".join(lines)


def event_table(events, fmt, limit=15):
    if not events:
        return None
    lines = ["| Event | Key event | Count | Previous | % change |",
             "|---|:--:|---:|---:|---:|"]
    for e in events[:limit]:
        rec = e["count_change"]
        lines.append("| `%s` | %s | %s | %s | %s |" % (
            e["event_name"], "yes" if e["is_key_event"] else "",
            fmt.value((e["current"] or {}).get("eventCount"), "int"),
            fmt.value((e["previous"] or {}).get("eventCount"), "int"),
            fmt.pct(rec)))
    return "\n".join(lines)


# ---------------------------------------------------------------------------
# CSV
# ---------------------------------------------------------------------------

def write_csv(path, header, rows):
    if not rows:
        return None
    with open(path, "w", newline="", encoding="utf-8") as fh:
        w = csv.writer(fh)
        w.writerow(header)
        w.writerows(rows)
    return str(path)


def segment_csv_rows(rows, metrics):
    out = []
    for r in rows or []:
        cur, prev = r.get("current") or {}, r.get("previous") or {}
        line = [r["key"]]
        for m in metrics:
            line.append(fmt_csv(cur.get(m)))
        for m in metrics:
            line.append(fmt_csv(prev.get(m)))
        out.append(line)
    return out


def fmt_csv(v):
    """Empty cell means 'not available'. Never a zero standing in for silence."""
    if v is None:
        return ""
    if abs(v - round(v)) < 1e-9:
        return "%d" % round(v)
    return "%.4f" % v


def segment_csv_header(dim_label, metrics):
    return ([dim_label] + ["current_%s" % m for m in metrics]
            + ["previous_%s" % m for m in metrics])


# ---------------------------------------------------------------------------
# Build
# ---------------------------------------------------------------------------

SEGMENT_CSV_METRICS = ["sessions", "totalUsers", "newUsers", "engagedSessions",
                       "engagementRate", "averageSessionDuration", "screenPageViews",
                       "keyEvents", "sessionKeyEventRate", "totalRevenue", "transactions"]


def build(raw, material_pct=MATERIAL_PCT, min_sessions=MIN_SESSIONS_TO_JUDGE,
          symbol_override=None):
    prop = raw.get("property") or {}
    fmt = Fmt(prop.get("currency"), symbol_override)
    periods = raw["periods"]

    derived_keys = set()
    totals = {p: derive_totals(report_totals(dataset(raw, "totals").get(p)), derived_keys)
              for p in ("current", "previous")}

    ecom_state = (raw.get("ecommerce") or {}).get("state")
    # Ecommerce metrics exist in every property's schema, so listing them for a
    # property that sells nothing would fill the "not available" list with
    # seventeen metrics nobody asked for. They enter the KPI set only when the
    # property returned actual purchase activity.
    specs = list(KPI_SPECS) + (list(ECOMMERCE_KPI_SPECS) if ecom_state == "active" else [])

    kpis = {}
    for key, label, unit, better, note in specs:
        kpis[key] = change(totals["current"].get(key), totals["previous"].get(key),
                           unit, better, key=key, label=label,
                           material_pct=material_pct, note=note)
        if key in derived_keys and key in DERIVED_NOTE:
            kpis[key]["derived"] = True
            kpis[key]["notes"].append(DERIVED_NOTE[key])

    # Cross-checks that turn an arithmetic verdict into an honest one.
    sessions, ke, rev = kpis.get("sessions", {}), kpis.get("keyEvents", {}), kpis.get("totalRevenue", {})
    if (sessions.get("direction") == "down"
            and (ke.get("verdict") == "improved" or rev.get("verdict") == "improved")):
        sessions["verdict"] = "ambiguous"
        sessions["notes"].append(
            "Sessions fell while outcomes rose, so this is a mix change rather than a "
            "decline. Do not report it as lost performance.")
    if (sessions.get("direction") == "up" and ke.get("verdict") == "declined"):
        sessions["notes"].append(
            "The extra sessions did not carry key events with them; volume alone is not the "
            "story here.")

    ke_available = kpis.get("keyEvents", {}).get("availability") != "unavailable"
    prev_sessions = totals["previous"].get("sessions")
    baseline_empty = prev_sessions in (None, 0)

    # -- sections ----------------------------------------------------------
    total_sessions = totals["current"].get("sessions")
    channels = segment_rows(raw, "channels")
    sections = {
        "acquisition": {
            "session_channels": channels,
            "session_source_medium": segment_rows(raw, "source_medium"),
            "session_campaigns": segment_rows(raw, "campaigns"),
            "first_user_channels": segment_rows(raw, "first_user_channels", sort_metric="totalUsers"),
            "attribution_note": (
                "Session-scoped dimensions (`session*`) describe where a VISIT came from. "
                "First-user dimensions (`firstUser*`) describe where a PERSON was originally "
                "acquired, however long ago. The two answer different questions and their "
                "totals do not reconcile -- never mix a first-user metric with a "
                "session-scoped one in the same row."),
        },
        "content": {
            "landing_pages": segment_rows(raw, "landing_pages"),
            "pages": segment_rows(raw, "pages", sort_metric="screenPageViews"),
            "hostnames": segment_rows(raw, "hostname"),
            "note": "Landing pages are session entry points; pages are all views. A page can "
                    "be heavily viewed and rarely entered on, and vice versa.",
        },
        "engagement": {
            "summary": {k: kpis[k] for k in
                        ("engagementRate", "bounceRate", "averageSessionDuration",
                         "screenPageViewsPerSession", "engagedSessions", "eventsPerSession")
                        if k in kpis},
        },
        "devices": {
            "device_categories": segment_rows(raw, "devices"),
            "browsers": segment_rows(raw, "browsers"),
            "operating_systems": segment_rows(raw, "operating_systems"),
            "platforms": segment_rows(raw, "platforms"),
        },
        "geography": {
            "countries": segment_rows(raw, "geo_country"),
            "regions": segment_rows(raw, "geo_region"),
            "cities": segment_rows(raw, "geo_city"),
            "note": "Geographic splits are only worth reporting where the differences are "
                    "large and the samples are not tiny. City-level rows in particular are "
                    "often below the level GA4 will report reliably.",
        },
    }

    events_section, event_finds = event_analysis(raw, fmt, min_sessions, material_pct,
                                                baseline_empty=baseline_empty)
    sections["events"] = events_section
    trend_section, trend_finds = trend_analysis(raw, fmt, ke_available)
    sections["trends"] = trend_section
    ecom_section, ecom_finds = ecommerce_analysis(raw, kpis, fmt, material_pct)
    sections["ecommerce"] = ecom_section

    # -- findings ----------------------------------------------------------
    findings = []
    findings += kpi_findings(kpis, fmt, ecom_state, baseline_empty=baseline_empty,
                             min_sessions=min_sessions)
    findings += segment_findings(channels, "Channel", "acquisition", fmt, min_sessions,
                                 total_sessions, material_pct, baseline_empty=baseline_empty)
    findings += landing_page_findings(sections["content"]["landing_pages"], fmt, min_sessions,
                                      ke_available, material_pct,
                                      baseline_empty=baseline_empty)
    findings += device_findings(sections["devices"]["device_categories"], fmt, min_sessions,
                                ke_available)
    findings += event_finds
    findings += trend_finds
    findings += ecom_finds

    # Geography only when a real difference exists and the sample supports it.
    countries = sections["geography"]["countries"]
    if countries and total_sessions and not baseline_empty:
        top = countries[0]
        share = ((top.get("current") or {}).get("sessions") or 0) / total_sessions * 100
        movers = [r for r in countries[:8]
                  if ((r.get("current") or {}).get("sessions") or 0) >= min_sessions]
        for r in movers[1:4]:
            rec = change((r.get("current") or {}).get("sessions"),
                         (r.get("previous") or {}).get("sessions"), "int", "higher",
                         material_pct=material_pct)
            if rec["material"] and abs(rec["absolute_change"] or 0) >= min_sessions:
                findings.append(finding(
                    "observation", "geo_move:%s" % r["key"],
                    "%s sessions %s %s" % (r["key"], "up" if rec["direction"] == "up" else "down",
                                           fmt.pct(rec)),
                    "Traffic from %s moved materially while the property's largest market "
                    "(%s, %.0f%% of sessions) did not move with it."
                    % (r["key"], top["key"], share),
                    ["%s: %s vs %s sessions (%s)" % (
                        r["key"], fmt.value(rec["current"], "int"),
                        fmt.value(rec["previous"], "int"), fmt.pct(rec))],
                    severity="low", scope="geo", entity=r["key"]))

    # A gap in collection makes every volume decline partly an artefact of the
    # gap. Rather than deleting those findings -- the decline is real in the
    # data -- each one carries the caveat and drops to low confidence, so the
    # report cannot present a measurement gap as a performance story.
    gap_days = len((sections.get("trends") or {}).get("missing_days_current") or [])
    if gap_days:
        share = gap_days / max(1, periods["current"]["days"]) * 100
        for f in findings:
            if f["type"] in ("weakness", "risk") and f["id"] not in (
                    "daily_missing_days",) and "down" in (f["title"] + f["statement"]).lower():
                f["confidence"] = "low"
                f["statement"] += (
                    " Note: %d of the %d days in this period returned no data at all (%.0f%% "
                    "of the period), so part of this decline is missing measurement rather "
                    "than lost performance. The size of the real change cannot be stated "
                    "until the gap is explained."
                    % (gap_days, periods["current"]["days"], share))

    dq = data_quality(raw, kpis, sections, fmt, min_sessions)
    for i, w in enumerate(dq["warnings"], 1):
        findings.append(finding(
            "risk", "data_quality:%02d" % i,
            "Data quality: %s" % (w.split(".")[0][:70] + ("..." if len(w) > 70 else "")),
            w, [w], severity="medium", confidence="high", scope="tracking"))

    recommendations = recommend(findings, sections, kpis, fmt, ecom_state)

    grouped = {}
    for f in findings:
        grouped.setdefault({"strength": "strengths", "weakness": "weaknesses",
                            "risk": "risks", "opportunity": "opportunities",
                            "anomaly": "anomalies"}.get(f["type"], "observations"), []).append(f)
    for bucket in ("strengths", "weaknesses", "risks", "opportunities", "anomalies",
                   "observations"):
        grouped.setdefault(bucket, [])

    # -- tables ------------------------------------------------------------
    kpi_order = [k for k, _l, _u, _b, _n in KPI_SPECS]
    ecom_order = [k for k, _l, _u, _b, _n in ECOMMERCE_KPI_SPECS]
    tables = {
        "kpi": kpi_table(kpis, kpi_order, fmt, periods),
        "channels": segment_table(channels, "Channel", fmt, ke_available,
                                  revenue=(ecom_state == "active")),
        "landing_pages": segment_table(sections["content"]["landing_pages"], "Landing page",
                                       fmt, ke_available, limit=12,
                                       revenue=(ecom_state == "active")),
        "devices": segment_table(sections["devices"]["device_categories"], "Device", fmt,
                                 ke_available, revenue=(ecom_state == "active")),
        "events": event_table((events_section or {}).get("events"), fmt),
        "ecommerce": kpi_table(kpis, ecom_order, fmt, periods) if ecom_state == "active" else None,
        "first_user_channels": segment_table(sections["acquisition"]["first_user_channels"],
                                             "First user channel", fmt, False),
    }

    return {
        "schema": SCHEMA,
        "generated_at": dt.datetime.now().astimezone().isoformat(timespec="seconds"),
        "source_raw": raw.get("_source_path"),
        "property": {
            "property_id": prop.get("property_id"),
            "name": prop.get("name"),
            "time_zone": prop.get("time_zone"),
            "currency": prop.get("currency"),
            "industry": prop.get("industry"),
            "created": prop.get("created"),
            "property_type": prop.get("property_type"),
            "data_streams": prop.get("data_streams"),
            "site_url": (raw.get("config") or {}).get("site_url"),
            "client_name": (raw.get("config") or {}).get("client_name"),
            "admin_api_available": prop.get("admin_api_available"),
        },
        "periods": periods,
        "key_events": raw.get("key_events") or {},
        "ecommerce_state": ecom_state,
        "kpis": [kpis[k] for k in kpi_order if k in kpis]
                + [kpis[k] for k in ecom_order if k in kpis],
        "kpis_by_key": kpis,
        "sections": sections,
        "findings": grouped,
        "findings_flat": findings,
        "recommended_actions": recommendations,
        "data_quality": dq,
        "tables": tables,
        "charts": [],
    }


def write_outputs(analysis, out_dir, raw):
    out_dir = Path(out_dir)
    out_dir.mkdir(parents=True, exist_ok=True)
    written = {}

    a_path = out_dir / "analysis.json"
    a_path.write_text(json.dumps(analysis, indent=2), encoding="utf-8")
    written["analysis"] = str(a_path)

    k_path = out_dir / "kpis.json"
    k_path.write_text(json.dumps({
        "property": analysis["property"],
        "periods": analysis["periods"],
        "ecommerce_state": analysis["ecommerce_state"],
        "kpis": analysis["kpis"],
    }, indent=2), encoding="utf-8")
    written["kpis"] = str(k_path)

    sections = analysis["sections"]
    fmt_metrics = SEGMENT_CSV_METRICS

    exports = [
        ("acquisition.csv", "channel", sections["acquisition"]["session_channels"]),
        ("acquisition-source-medium.csv", "source_medium", sections["acquisition"]["session_source_medium"]),
        ("landing-pages.csv", "landing_page", sections["content"]["landing_pages"]),
        ("pages.csv", "page", sections["content"]["pages"]),
        ("devices.csv", "device_category", sections["devices"]["device_categories"]),
        ("geography.csv", "country", sections["geography"]["countries"]),
    ]
    for name, dim_label, rows in exports:
        path = write_csv(out_dir / name, segment_csv_header(dim_label, fmt_metrics),
                         segment_csv_rows(rows, fmt_metrics))
        if path:
            written[name] = path

    events = (sections.get("events") or {}).get("events")
    if events:
        rows = [[e["event_name"], "yes" if e["is_key_event"] else "no",
                 fmt_csv((e["current"] or {}).get("eventCount")),
                 fmt_csv((e["previous"] or {}).get("eventCount")),
                 fmt_csv((e["current"] or {}).get("keyEvents")),
                 fmt_csv((e["current"] or {}).get("totalUsers"))]
                for e in events]
        path = write_csv(out_dir / "events.csv",
                         ["event_name", "is_key_event", "current_event_count",
                          "previous_event_count", "current_key_events", "current_total_users"],
                         rows)
        written["events.csv"] = path

    trends = sections.get("trends") or {}
    if trends.get("current"):
        metrics = trends.get("metrics") or []
        rows = []
        for d in trends["current"]:
            rows.append([d["date"], "yes" if d["returned"] else "no"]
                        + [fmt_csv((d["values"] or {}).get(m)) for m in metrics])
        path = write_csv(out_dir / "daily.csv", ["date", "data_returned"] + metrics, rows)
        written["daily.csv"] = path

    ecom = sections.get("ecommerce") or {}
    if ecom.get("included"):
        rows = []
        for step in ecom.get("funnel") or []:
            rows.append(["funnel", step["label"], fmt_csv(step["current"]),
                         fmt_csv(step["previous"]), fmt_csv(step["step_rate_current"]),
                         fmt_csv(step["step_rate_previous"])])
        for r in ecom.get("revenue_by_channel") or []:
            cur, prev = r.get("current") or {}, r.get("previous") or {}
            rows.append(["channel", r["key"], fmt_csv(cur.get("totalRevenue")),
                         fmt_csv(prev.get("totalRevenue")), fmt_csv(cur.get("transactions")),
                         fmt_csv(prev.get("transactions"))])
        for r in ecom.get("items") or []:
            cur, prev = r.get("current") or {}, r.get("previous") or {}
            rows.append(["item", r["key"], fmt_csv(cur.get("itemRevenue")),
                         fmt_csv(prev.get("itemRevenue")), fmt_csv(cur.get("itemsPurchased")),
                         fmt_csv(prev.get("itemsPurchased"))])
        path = write_csv(out_dir / "ecommerce.csv",
                         ["kind", "label", "current_value", "previous_value",
                          "current_secondary", "previous_secondary"], rows)
        if path:
            written["ecommerce.csv"] = path

    # Pre-rendered tables
    t = analysis["tables"]
    p = analysis["periods"]
    md = ["# GA4 tables — %s" % (analysis["property"]["name"] or
                                 "property %s" % analysis["property"]["property_id"]),
          "",
          "Current: %s to %s | Previous: %s to %s"
          % (p["current"]["start"], p["current"]["end"],
             p["previous"]["start"], p["previous"]["end"]),
          "", "## KPI overview", "", t["kpi"] or "_No KPI was available._"]
    for title, key in (("Acquisition — session channel", "channels"),
                       ("Acquisition — first user channel", "first_user_channels"),
                       ("Landing pages", "landing_pages"),
                       ("Devices", "devices"),
                       ("Events", "events"),
                       ("Ecommerce", "ecommerce")):
        if t.get(key):
            md += ["", "## %s" % title, "", t[key]]
    t_path = out_dir / "tables.md"
    t_path.write_text("\n".join(md) + "\n", encoding="utf-8")
    written["tables"] = str(t_path)

    return written


def main():
    ap = argparse.ArgumentParser(description="Analyse a GA4 retrieval file.")
    ap.add_argument("--raw", required=True, help="Path to raw.json written by fetch_ga4.py")
    ap.add_argument("--out", help="Output directory (default: alongside the raw file)")
    ap.add_argument("--material-pct", type=float, default=MATERIAL_PCT,
                    help="Percentage move at or above which a change counts as material (default 10)")
    ap.add_argument("--min-sessions", type=int, default=MIN_SESSIONS_TO_JUDGE,
                    help="Sessions a segment needs before its rate metrics are judged (default 100)")
    ap.add_argument("--currency-symbol", help="Override the currency symbol used in tables")
    ap.add_argument("--quiet", action="store_true")
    args = ap.parse_args()

    raw_path = Path(args.raw).expanduser()
    if not raw_path.is_file():
        print("No such retrieval file: %s" % raw_path, file=sys.stderr)
        return 2
    try:
        raw = json.loads(raw_path.read_text(encoding="utf-8"))
    except ValueError as exc:
        print("That retrieval file is not valid JSON (%s). Re-run the fetch." % exc,
              file=sys.stderr)
        return 2
    raw["_source_path"] = str(raw_path)

    if raw.get("schema") != RAW_SCHEMA:
        print("Unexpected schema %r in %s (expected %s)"
              % (raw.get("schema"), raw_path, RAW_SCHEMA), file=sys.stderr)
        return 2
    if not raw.get("periods"):
        print("That retrieval file has no periods -- the run failed before it fetched "
              "anything. Fix the fetch first.", file=sys.stderr)
        return 2
    if not (raw.get("datasets") or {}).get("totals"):
        print("That retrieval file has no KPI totals, so there is nothing to analyse.",
              file=sys.stderr)
        return 2

    analysis = build(raw, material_pct=args.material_pct, min_sessions=args.min_sessions,
                     symbol_override=args.currency_symbol)
    out_dir = Path(args.out).expanduser() if args.out else raw_path.parent
    written = write_outputs(analysis, out_dir, raw)

    summary = {
        "analysis_file": written["analysis"],
        "files": written,
        "property": analysis["property"]["name"] or analysis["property"]["property_id"],
        "periods": analysis["periods"],
        "ecommerce": analysis["ecommerce_state"],
        "findings": {k: len(v) for k, v in analysis["findings"].items()},
        "recommended_actions": len(analysis["recommended_actions"]),
        "unavailable_metrics": [u["metric"] for u in analysis["data_quality"]["unavailable_metrics"]],
        "failed_checks": [c["check"] for c in analysis["data_quality"]["checks"]
                          if c["status"] == "fail"],
        "warnings": analysis["data_quality"]["warnings"],
    }
    print(json.dumps(summary, indent=2))
    if not args.quiet:
        for name, path in written.items():
            print("wrote %s" % path, file=sys.stderr)
    return 0


if __name__ == "__main__":
    sys.exit(main())
