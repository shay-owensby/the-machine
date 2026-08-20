#!/usr/bin/env python3
"""
Generate the offline test fixtures in assets/fixtures/.

    python3 make_fixtures.py                 # rewrite every fixture
    python3 make_fixtures.py --list          # names and what each one is for

The fixtures are retrieval files in exactly the shape fetch_google_ads.py
writes, so everything downstream -- analysis, charts, the report itself -- can
be exercised end to end without credentials, without quota, and without an
account that happens to be in the right state today.

They are DELIBERATELY not realistic in one respect: the numbers are round and
fixed, so a test can assert on them. They are realistic in the respect that
matters -- REST shapes, string-encoded int64s, micros for cost, doubles for
conversion value, and *absent* keys where an account does not report a metric.

Every fixture is synthetic. No client data appears in this directory.
"""

import argparse
import datetime as dt
import json
from pathlib import Path

FIXTURE_DIR = Path(__file__).resolve().parent.parent / "assets" / "fixtures"

CUR = ("2026-07-20", "2026-08-18")
PREV = ("2026-06-20", "2026-07-19")


def metrics(impressions=None, clicks=None, cost=None, conversions=None,
            value=None, all_conv=None, all_value=None, ctr=None, cpc=None,
            search_is=None, lost_budget=None, lost_rank=None, abs_top=None):
    """Build a REST metrics block, omitting anything not supplied.

    Omission is the point: that is how the API reports a metric an account or
    campaign type cannot produce, and the pipeline must carry it through as
    "not available" rather than zero.
    """
    m = {}
    if impressions is not None:
        m["impressions"] = str(int(impressions))
    if clicks is not None:
        m["clicks"] = str(int(clicks))
    if cost is not None:
        m["costMicros"] = str(int(round(cost * 1000000)))
    if conversions is not None:
        m["conversions"] = float(conversions)
    if value is not None:
        m["conversionsValue"] = float(value)
    if all_conv is not None:
        m["allConversions"] = float(all_conv)
    if all_value is not None:
        m["allConversionsValue"] = float(all_value)
    if ctr is not None:
        m["ctr"] = float(ctr)
    if cpc is not None:
        m["averageCpc"] = str(int(round(cpc * 1000000)))
    if search_is is not None:
        m["searchImpressionShare"] = float(search_is)
    if lost_budget is not None:
        m["searchBudgetLostImpressionShare"] = float(lost_budget)
    if lost_rank is not None:
        m["searchRankLostImpressionShare"] = float(lost_rank)
    if abs_top is not None:
        m["searchAbsoluteTopImpressionShare"] = float(abs_top)
    return m


def campaign(cid, name, status="ENABLED", channel="SEARCH", bidding="MAXIMIZE_CONVERSIONS",
             budget=None, **kw):
    row = {
        "campaign": {
            "resourceName": "customers/1234567890/campaigns/%s" % cid,
            "id": str(cid),
            "name": name,
            "status": status,
            "advertisingChannelType": channel,
            "biddingStrategyType": bidding,
        },
        "metrics": metrics(**kw),
    }
    if budget is not None:
        row["campaignBudget"] = {"amountMicros": str(int(budget * 1000000)),
                                 "explicitlyShared": False}
    return row


def daily_rows(start, end, cost, clicks, impressions, conversions, value=None):
    """Spread period totals evenly across the days, with a mild weekly wobble
    so trend charts have something to draw that is not a straight line."""
    s = dt.date.fromisoformat(start)
    e = dt.date.fromisoformat(end)
    n = (e - s).days + 1
    rows = []
    for i in range(n):
        d = s + dt.timedelta(days=i)
        # A weekday rhythm plus a slow drift and a small deterministic wobble.
        # Deterministic matters: a fixture that changes between runs cannot be
        # asserted on, and a perfectly flat one makes the trend charts a lie
        # about what real accounts look like.
        import math
        weekday = 0.72 if d.weekday() >= 5 else 1.12
        drift = 1.0 + 0.22 * (i / max(1, n - 1) - 0.5)
        wobble = 1.0 + 0.10 * math.sin(i * 1.7) + 0.05 * math.cos(i * 0.9)
        factor = weekday * drift * wobble
        rows.append({
            "segments": {"date": d.isoformat()},
            "metrics": metrics(
                impressions=round(impressions / n * factor),
                clicks=round(clicks / n * factor),
                cost=round(cost / n * factor, 2),
                conversions=round(conversions / n * factor, 2),
                value=None if value is None else round(value / n * factor, 2),
            ),
        })
    return rows


def envelope(name, account=None, periods=None, datasets=None, errors=None, warnings=None):
    return {
        "schema": "reports-google-ads/raw@1",
        "generated_at": "2026-08-19T09:00:00+01:00",
        "api_version": "v21",
        "fixture": name,
        "account": account or {
            "customer_id": "1234567890",
            "name": "Example Client Account",
            "currency": "USD",
            "time_zone": "America/New_York",
            "is_manager": False,
            "is_test_account": False,
            "status": "ENABLED",
            "auto_tagging_enabled": True,
            "optimization_score": 0.78,
            "login_customer_id": "9876543210",
        },
        "periods": periods or {
            "current": {"start": CUR[0], "end": CUR[1], "days": 30},
            "previous": {"start": PREV[0], "end": PREV[1], "days": 30},
            "basis": "most recent 30 completed days ending yesterday in America/New_York",
            "time_zone": "America/New_York",
        },
        "datasets": datasets or {},
        "errors": errors or [],
        "warnings": warnings or [],
        "config": {
            "agency_env": "~/clients/agency.env",
            "client_env": "/example/client/.env",
            "login_customer_id": "9876543210",
            "customer_id": "1234567890",
            "primary_conversion_actions": [],
        },
    }


# ---------------------------------------------------------------------------
# The fixtures
# ---------------------------------------------------------------------------

def fx_healthy():
    """A normal account: spend up, conversions up faster, one budget-capped
    winner, one expensive laggard, full impression-share reporting."""
    cur_campaigns = [
        campaign(11, "Search — Brand", budget=40,
                 impressions=42000, clicks=3800, cost=2660.00, conversions=210, value=21000,
                 search_is=0.82, lost_budget=0.04, lost_rank=0.14, abs_top=0.55),
        campaign(12, "Search — Non-Brand Core", budget=120,
                 impressions=88000, clicks=4400, cost=6160.00, conversions=176, value=15840,
                 search_is=0.41, lost_budget=0.23, lost_rank=0.36, abs_top=0.18),
        campaign(13, "Performance Max — Retail", channel="PERFORMANCE_MAX", budget=90,
                 impressions=310000, clicks=5200, cost=3640.00, conversions=98, value=7350),
        campaign(14, "Display — Remarketing", channel="DISPLAY", budget=15,
                 impressions=520000, clicks=1400, cost=420.00, conversions=6, value=390),
    ]
    prev_campaigns = [
        campaign(11, "Search — Brand", budget=40,
                 impressions=40000, clicks=3600, cost=2520.00, conversions=198, value=19800,
                 search_is=0.84, lost_budget=0.03, lost_rank=0.13, abs_top=0.57),
        campaign(12, "Search — Non-Brand Core", budget=100,
                 impressions=76000, clicks=3500, cost=4900.00, conversions=126, value=11340,
                 search_is=0.46, lost_budget=0.16, lost_rank=0.38, abs_top=0.21),
        campaign(13, "Performance Max — Retail", channel="PERFORMANCE_MAX", budget=90,
                 impressions=290000, clicks=4800, cost=3360.00, conversions=88, value=6600),
        campaign(14, "Display — Remarketing", channel="DISPLAY", budget=15,
                 impressions=480000, clicks=1300, cost=390.00, conversions=5, value=325),
    ]
    cur_tot = dict(impressions=960000, clicks=14800, cost=12880.00, conversions=490, value=44580)
    prev_tot = dict(impressions=886000, clicks=13200, cost=11170.00, conversions=417, value=38065)

    return envelope("healthy", datasets={
        "account_totals": {
            "current": [{"metrics": metrics(all_conv=520, all_value=46000, **cur_tot)}],
            "previous": [{"metrics": metrics(all_conv=440, all_value=39500, **prev_tot)}],
        },
        "daily": {
            "current": daily_rows(CUR[0], CUR[1], cur_tot["cost"], cur_tot["clicks"],
                                  cur_tot["impressions"], cur_tot["conversions"], cur_tot["value"]),
            "previous": daily_rows(PREV[0], PREV[1], prev_tot["cost"], prev_tot["clicks"],
                                   prev_tot["impressions"], prev_tot["conversions"], prev_tot["value"]),
        },
        "campaigns": {"current": cur_campaigns, "previous": prev_campaigns},
        "device": {
            "current": [
                {"segments": {"device": "MOBILE"}, "metrics": metrics(impressions=610000, clicks=9800, cost=8200.00, conversions=310, value=27000)},
                {"segments": {"device": "DESKTOP"}, "metrics": metrics(impressions=290000, clicks=4300, cost=4000.00, conversions=165, value=16000)},
                {"segments": {"device": "TABLET"}, "metrics": metrics(impressions=60000, clicks=700, cost=680.00, conversions=15, value=1580)},
            ],
            "previous": [
                {"segments": {"device": "MOBILE"}, "metrics": metrics(impressions=520000, clicks=8000, cost=6600.00, conversions=250, value=22000)},
                {"segments": {"device": "DESKTOP"}, "metrics": metrics(impressions=310000, clicks=4500, cost=4000.00, conversions=155, value=15000)},
                {"segments": {"device": "TABLET"}, "metrics": metrics(impressions=56000, clicks=700, cost=570.00, conversions=12, value=1065)},
            ],
        },
        "network": {
            "current": [
                {"segments": {"adNetworkType": "SEARCH"}, "metrics": metrics(impressions=130000, clicks=8200, cost=8820.00, conversions=386, value=36840)},
                {"segments": {"adNetworkType": "CONTENT"}, "metrics": metrics(impressions=830000, clicks=6600, cost=4060.00, conversions=104, value=7740)},
            ],
            "previous": [
                {"segments": {"adNetworkType": "SEARCH"}, "metrics": metrics(impressions=116000, clicks=7100, cost=7420.00, conversions=324, value=31140)},
                {"segments": {"adNetworkType": "CONTENT"}, "metrics": metrics(impressions=770000, clicks=6100, cost=3750.00, conversions=93, value=6925)},
            ],
        },
        "ad_groups": {
            "current": [
                {"campaign": {"name": "Search — Non-Brand Core"}, "adGroup": {"id": "201", "name": "Core Terms — Exact", "status": "ENABLED"},
                 "metrics": metrics(impressions=41000, clicks=2300, cost=3450.00, conversions=104, value=9360)},
                {"campaign": {"name": "Search — Brand"}, "adGroup": {"id": "202", "name": "Brand — Exact", "status": "ENABLED"},
                 "metrics": metrics(impressions=30000, clicks=2900, cost=1740.00, conversions=160, value=16000)},
            ],
            "previous": [],
        },
        "keywords": {
            "current": [
                {"campaign": {"name": "Search — Non-Brand Core"}, "adGroup": {"name": "Core Terms — Exact"},
                 "adGroupCriterion": {"keyword": {"text": "example service near me", "matchType": "EXACT"}, "status": "ENABLED"},
                 "metrics": metrics(impressions=18000, clicks=1100, cost=1815.00, conversions=44, value=3960)},
                {"campaign": {"name": "Search — Non-Brand Core"}, "adGroup": {"name": "Core Terms — Phrase"},
                 "adGroupCriterion": {"keyword": {"text": "example service cost", "matchType": "PHRASE"}, "status": "ENABLED"},
                 "metrics": metrics(impressions=12000, clicks=640, cost=1216.00, conversions=9, value=810)},
            ],
            "previous": [],
        },
        "search_terms": {
            "current": [
                {"campaign": {"name": "Search — Non-Brand Core"}, "adGroup": {"name": "Core Terms — Phrase"},
                 "searchTermView": {"searchTerm": "free example service", "status": "NONE"},
                 "metrics": metrics(impressions=3400, clicks=220, cost=418.00, conversions=0, value=0)},
                {"campaign": {"name": "Search — Non-Brand Core"}, "adGroup": {"name": "Core Terms — Exact"},
                 "searchTermView": {"searchTerm": "example service near me", "status": "ADDED"},
                 "metrics": metrics(impressions=6100, clicks=410, cost=676.50, conversions=21, value=1890)},
            ],
            "previous": None,
            "previous_note": "Not retrieved.",
        },
        "conversion_actions_meta": {
            "current": [
                {"conversionAction": {"id": "301", "name": "Purchase", "category": "PURCHASE",
                                      "type": "WEBPAGE", "status": "ENABLED", "primaryForGoal": True,
                                      "countingType": "ONE_PER_CLICK", "includeInConversionsMetric": True}},
                {"conversionAction": {"id": "302", "name": "Phone Call", "category": "PHONE_CALL_LEAD",
                                      "type": "CLICK_TO_CALL", "status": "ENABLED", "primaryForGoal": True,
                                      "countingType": "ONE_PER_CLICK", "includeInConversionsMetric": True}},
                {"conversionAction": {"id": "303", "name": "Newsletter Signup (legacy)", "category": "SIGNUP",
                                      "type": "WEBPAGE", "status": "ENABLED", "primaryForGoal": False,
                                      "countingType": "ONE_PER_CLICK", "includeInConversionsMetric": False}},
            ],
            "previous": None,
        },
        "conversion_performance": {
            "current": [
                {"segments": {"conversionActionName": "Purchase", "conversionActionCategory": "PURCHASE"},
                 "metrics": metrics(all_conv=360, all_value=42000)},
                {"segments": {"conversionActionName": "Phone Call", "conversionActionCategory": "PHONE_CALL_LEAD"},
                 "metrics": metrics(all_conv=160, all_value=4000)},
            ],
            "previous": [
                {"segments": {"conversionActionName": "Purchase", "conversionActionCategory": "PURCHASE"},
                 "metrics": metrics(all_conv=305, all_value=36500)},
                {"segments": {"conversionActionName": "Phone Call", "conversionActionCategory": "PHONE_CALL_LEAD"},
                 "metrics": metrics(all_conv=135, all_value=3000)},
            ],
        },
    })


def fx_no_conversions():
    """Spend, clicks, and nothing recorded. The tracking-versus-reality case."""
    cur = [campaign(21, "Search — Generic", budget=50,
                    impressions=52000, clicks=1900, cost=2470.00, conversions=0, value=0,
                    search_is=0.33, lost_budget=0.28, lost_rank=0.39)]
    prev = [campaign(21, "Search — Generic", budget=50,
                     impressions=48000, clicks=1750, cost=2275.00, conversions=0, value=0,
                     search_is=0.35, lost_budget=0.25, lost_rank=0.40)]
    return envelope("no-conversions", datasets={
        "account_totals": {
            "current": [{"metrics": metrics(impressions=52000, clicks=1900, cost=2470.00, conversions=0, value=0)}],
            "previous": [{"metrics": metrics(impressions=48000, clicks=1750, cost=2275.00, conversions=0, value=0)}],
        },
        "daily": {
            "current": daily_rows(CUR[0], CUR[1], 2470.00, 1900, 52000, 0, 0),
            "previous": daily_rows(PREV[0], PREV[1], 2275.00, 1750, 48000, 0, 0),
        },
        "campaigns": {"current": cur, "previous": prev},
        "conversion_actions_meta": {"current": [
            {"conversionAction": {"id": "401", "name": "Contact Form", "category": "SUBMIT_LEAD_FORM",
                                  "type": "WEBPAGE", "status": "ENABLED", "primaryForGoal": True,
                                  "countingType": "ONE_PER_CLICK", "includeInConversionsMetric": True}},
        ], "previous": None},
        "conversion_performance": {"current": [], "previous": []},
    })


def fx_no_conversion_value():
    """Lead-gen: conversions yes, value never recorded. ROAS must be absent."""
    cur = [campaign(31, "Search — Services", budget=60,
                    impressions=61000, clicks=2400, cost=3120.00, conversions=96,
                    search_is=0.52, lost_budget=0.11, lost_rank=0.37)]
    prev = [campaign(31, "Search — Services", budget=60,
                     impressions=58000, clicks=2500, cost=2875.00, conversions=115,
                     search_is=0.55, lost_budget=0.08, lost_rank=0.37)]
    return envelope("no-conversion-value", datasets={
        "account_totals": {
            "current": [{"metrics": metrics(impressions=61000, clicks=2400, cost=3120.00, conversions=96)}],
            "previous": [{"metrics": metrics(impressions=58000, clicks=2500, cost=2875.00, conversions=115)}],
        },
        "daily": {
            "current": daily_rows(CUR[0], CUR[1], 3120.00, 2400, 61000, 96),
            "previous": daily_rows(PREV[0], PREV[1], 2875.00, 2500, 58000, 115),
        },
        "campaigns": {"current": cur, "previous": prev},
    })


def fx_zero_previous():
    """A brand new account: the comparison period is genuinely all zeros, and
    every percentage change against it is undefined rather than +100%."""
    cur = [campaign(41, "Search — Launch", budget=35,
                    impressions=18000, clicks=760, cost=988.00, conversions=22, value=1980,
                    search_is=0.29, lost_budget=0.31, lost_rank=0.40)]
    prev = [campaign(41, "Search — Launch", budget=35,
                     impressions=0, clicks=0, cost=0, conversions=0, value=0)]
    return envelope("zero-previous", datasets={
        "account_totals": {
            "current": [{"metrics": metrics(impressions=18000, clicks=760, cost=988.00, conversions=22, value=1980)}],
            "previous": [{"metrics": metrics(impressions=0, clicks=0, cost=0, conversions=0, value=0)}],
        },
        "daily": {
            "current": daily_rows(CUR[0], CUR[1], 988.00, 760, 18000, 22, 1980),
            "previous": [],
        },
        "campaigns": {"current": cur, "previous": prev},
    })


def fx_sparse():
    """A very small account plus a paused campaign that still spent. Nothing
    here supports a confident conclusion, and the analysis has to say so."""
    cur = [
        campaign(51, "Search — Local", budget=10,
                 impressions=2100, clicks=64, cost=118.40, conversions=3, value=270,
                 search_is=0.22, lost_budget=0.36, lost_rank=0.42),
        campaign(52, "Search — Old Promo", status="PAUSED", budget=10,
                 impressions=300, clicks=9, cost=17.10, conversions=0, value=0,
                 search_is=0.05, lost_budget=0.10, lost_rank=0.85),
    ]
    prev = [
        campaign(51, "Search — Local", budget=10,
                 impressions=2400, clicks=71, cost=127.80, conversions=5, value=450,
                 search_is=0.25, lost_budget=0.33, lost_rank=0.42),
    ]
    return envelope("sparse", datasets={
        "account_totals": {
            "current": [{"metrics": metrics(impressions=2400, clicks=73, cost=135.50, conversions=3, value=270)}],
            "previous": [{"metrics": metrics(impressions=2400, clicks=71, cost=127.80, conversions=5, value=450)}],
        },
        "daily": {
            "current": daily_rows(CUR[0], CUR[1], 135.50, 73, 2400, 3, 270),
            "previous": daily_rows(PREV[0], PREV[1], 127.80, 71, 2400, 5, 450),
        },
        "campaigns": {"current": cur, "previous": prev},
    })


def fx_partial_failure():
    """Core data came back; the search-term query and the whole conversion
    section did not. Those sections must read as unavailable, not empty -- and
    a Performance Max-only account reports no impression share at all."""
    cur = [campaign(61, "Performance Max — All Products", channel="PERFORMANCE_MAX", budget=200,
                    impressions=410000, clicks=6800, cost=8160.00, conversions=142, value=17040)]
    prev = [campaign(61, "Performance Max — All Products", channel="PERFORMANCE_MAX", budget=200,
                     impressions=380000, clicks=6100, cost=7320.00, conversions=151, value=19630)]
    return envelope(
        "partial-failure",
        datasets={
            "account_totals": {
                "current": [{"metrics": metrics(impressions=410000, clicks=6800, cost=8160.00, conversions=142, value=17040)}],
                "previous": [{"metrics": metrics(impressions=380000, clicks=6100, cost=7320.00, conversions=151, value=19630)}],
            },
            "daily": {
                "current": daily_rows(CUR[0], CUR[1], 8160.00, 6800, 410000, 142, 17040),
                "previous": daily_rows(PREV[0], PREV[1], 7320.00, 6100, 380000, 151, 19630),
            },
            "campaigns": {"current": cur, "previous": prev},
            "search_terms": {"current": None, "previous": None},
            "conversion_performance": {"current": None, "previous": None},
        },
        errors=[
            {"dataset": "search_terms.current", "required": False,
             "message": "The developer token does not have access to this report.",
             "error_code": "authorizationError.USER_PERMISSION_DENIED",
             "http_status": 403, "hint": "Check account access.", "retryable": False},
            {"dataset": "conversion_performance.current", "required": False,
             "message": "Rate limit exceeded.", "error_code": "quotaError.RESOURCE_EXHAUSTED",
             "http_status": 429, "hint": "Retry later.", "retryable": True},
        ],
        warnings=["Search-term and conversion-action data are unavailable for this run."],
    )


def fx_placeholder_value():
    """Conversion value is a flat 1.00 per conversion: ROAS looks like a
    return figure but is only a restatement of conversion volume."""
    cur = [campaign(71, "Search — Bookings", budget=30,
                    impressions=7000, clicks=610, cost=812.00, conversions=221, value=221.00,
                    search_is=0.42, lost_budget=0.24, lost_rank=0.33)]
    prev = [campaign(71, "Search — Bookings", budget=30,
                     impressions=8500, clicks=712, cost=816.00, conversions=270, value=270.00,
                     search_is=0.46, lost_budget=0.21, lost_rank=0.32)]
    return envelope("placeholder-value", datasets={
        "account_totals": {
            "current": [{"metrics": metrics(impressions=7000, clicks=610, cost=812.00, conversions=221, value=221.00)}],
            "previous": [{"metrics": metrics(impressions=8500, clicks=712, cost=816.00, conversions=270, value=270.00)}],
        },
        "daily": {
            "current": daily_rows(CUR[0], CUR[1], 812.00, 610, 7000, 221, 221.00),
            "previous": daily_rows(PREV[0], PREV[1], 816.00, 712, 8500, 270, 270.00),
        },
        "campaigns": {"current": cur, "previous": prev},
    })


FIXTURES = {
    "healthy": (fx_healthy, "Normal account, growth, full metric availability"),
    "no-conversions": (fx_no_conversions, "Spend with zero recorded conversions"),
    "no-conversion-value": (fx_no_conversion_value, "Lead gen: no conversion value, so no ROAS"),
    "zero-previous": (fx_zero_previous, "Comparison period is all zeros"),
    "sparse": (fx_sparse, "Tiny volumes plus a paused campaign that spent"),
    "partial-failure": (fx_partial_failure, "Some queries failed; PMax reports no impression share"),
    "placeholder-value": (fx_placeholder_value, "Flat 1.00 conversion value masquerading as revenue"),
}


def main():
    ap = argparse.ArgumentParser(description="Write the offline test fixtures.")
    ap.add_argument("--list", action="store_true")
    ap.add_argument("--out", default=str(FIXTURE_DIR))
    args = ap.parse_args()

    if args.list:
        for name, (_fn, desc) in sorted(FIXTURES.items()):
            print("%-22s %s" % (name, desc))
        return 0

    out = Path(args.out)
    out.mkdir(parents=True, exist_ok=True)
    for name, (fn, _desc) in sorted(FIXTURES.items()):
        path = out / ("%s_raw.json" % name)
        path.write_text(json.dumps(fn(), indent=2), encoding="utf-8")
        print("wrote %s" % path)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
