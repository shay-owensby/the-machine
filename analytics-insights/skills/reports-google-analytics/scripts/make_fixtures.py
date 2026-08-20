#!/usr/bin/env python3
"""
Generate the offline test fixtures in assets/fixtures/.

    python3 make_fixtures.py                 # rewrite every fixture
    python3 make_fixtures.py --list          # names and what each one is for

The fixtures are retrieval files in exactly the shape fetch_ga4.py writes, so
everything downstream -- analysis, charts, the report itself -- can be
exercised end to end without credentials, without quota, and without a GA4
property that happens to be in the right state today.

They are DELIBERATELY not realistic in one respect: the numbers are round and
fixed, so a test can assert on them. They are realistic in the respects that
matter -- GA4 rates as ratios in 0..1, durations in seconds, dates as YYYYMMDD,
`(not set)` and `(other)` rows, response metadata carrying dataLossFromOtherRow
and emptyReason, absent rows where a property reports nothing, and the pre-2024
`conversions` metric naming on a property that still answers to it.

Every fixture is synthetic. No client data appears in this directory.
"""

import argparse
import datetime as dt
import json
from pathlib import Path

FIXTURE_DIR = Path(__file__).resolve().parent.parent / "assets" / "fixtures"

CUR = ("2026-07-21", "2026-08-19")
PREV = ("2026-06-21", "2026-07-20")

METRIC_TYPES = {
    "engagementRate": "TYPE_FLOAT", "bounceRate": "TYPE_FLOAT",
    "sessionKeyEventRate": "TYPE_FLOAT", "userKeyEventRate": "TYPE_FLOAT",
    "sessionConversionRate": "TYPE_FLOAT", "userConversionRate": "TYPE_FLOAT",
    "purchaserRate": "TYPE_FLOAT", "cartToViewRate": "TYPE_FLOAT",
    "purchaseToViewRate": "TYPE_FLOAT",
    "averageSessionDuration": "TYPE_SECONDS", "userEngagementDuration": "TYPE_SECONDS",
    "screenPageViewsPerSession": "TYPE_FLOAT", "sessionsPerUser": "TYPE_FLOAT",
    "keyEvents": "TYPE_FLOAT", "conversions": "TYPE_FLOAT",
    "totalRevenue": "TYPE_CURRENCY", "purchaseRevenue": "TYPE_CURRENCY",
    "averagePurchaseRevenue": "TYPE_CURRENCY", "averageRevenuePerUser": "TYPE_CURRENCY",
    "itemRevenue": "TYPE_CURRENCY", "eventValue": "TYPE_CURRENCY",
}


def mtype(name):
    return METRIC_TYPES.get(name, "TYPE_INTEGER")


def report(dimensions, rows, totals=None, meta=None, row_count=None):
    """One parsed report in the shape ga4_common.parse_report() produces."""
    metrics = []
    seen = set()
    for _keys, values in rows:
        for m in values:
            if m not in seen:
                seen.add(m)
                metrics.append({"name": m, "type": mtype(m)})
    if totals:
        for m in totals:
            if m not in seen:
                seen.add(m)
                metrics.append({"name": m, "type": mtype(m)})
    return {
        "dimensions": list(dimensions),
        "metrics": metrics,
        "rows": [{"keys": list(k), "values": dict(v)} for k, v in rows],
        "totals": dict(totals) if totals else None,
        "row_count": row_count if row_count is not None else len(rows),
        "meta": meta or {"currencyCode": "USD", "timeZone": "America/New_York"},
    }


def kpis(sessions, users, new_users, engaged, views, events, key_events,
         avg_duration=95.0, key_event_sessions=None, ecommerce=None, legacy=False):
    """A coherent KPI block: every rate is derived from its own components."""
    ke_sessions = key_event_sessions if key_event_sessions is not None else min(key_events, sessions)
    ke_name = "conversions" if legacy else "keyEvents"
    rate_name = "sessionConversionRate" if legacy else "sessionKeyEventRate"
    user_rate_name = "userConversionRate" if legacy else "userKeyEventRate"
    out = {
        "activeUsers": float(users),
        "totalUsers": float(round(users * 1.04)),
        "newUsers": float(new_users),
        "sessions": float(sessions),
        "engagedSessions": float(engaged),
        "engagementRate": (engaged / sessions) if sessions else 0.0,
        "bounceRate": (1 - engaged / sessions) if sessions else 0.0,
        "averageSessionDuration": float(avg_duration),
        "userEngagementDuration": float(round(avg_duration * engaged)),
        "screenPageViews": float(views),
        "screenPageViewsPerSession": (views / sessions) if sessions else 0.0,
        "sessionsPerUser": (sessions / users) if users else 0.0,
        "eventCount": float(events),
        ke_name: float(key_events),
        rate_name: (ke_sessions / sessions) if sessions else 0.0,
        user_rate_name: (min(ke_sessions, users) / users) if users else 0.0,
    }
    if ecommerce:
        out.update(ecommerce)
    return out


def ecom_block(revenue, transactions, purchasers, users, items_viewed, added, checked, purchased):
    return {
        "totalRevenue": float(revenue),
        "purchaseRevenue": float(revenue),
        "transactions": float(transactions),
        "ecommercePurchases": float(transactions),
        "totalPurchasers": float(purchasers),
        "firstTimePurchasers": float(round(purchasers * 0.62)),
        "purchaserRate": (purchasers / users) if users else 0.0,
        "averagePurchaseRevenue": (revenue / transactions) if transactions else 0.0,
        "averageRevenuePerUser": (revenue / users) if users else 0.0,
        "itemsViewed": float(items_viewed),
        "itemsAddedToCart": float(added),
        "itemsCheckedOut": float(checked),
        "itemsPurchased": float(purchased),
        "addToCarts": float(added),
        "checkouts": float(checked),
        "cartToViewRate": (added / items_viewed) if items_viewed else 0.0,
        "purchaseToViewRate": (purchased / items_viewed) if items_viewed else 0.0,
    }


def daily_rows(start, end, total_sessions, total_users, total_views, total_events,
               total_key_events, revenue=None, skip_dates=(), spike_date=None,
               spike_multiplier=6.0):
    """Spread period totals across the days with a mild weekly wobble.

    `skip_dates` produces days with NO ROW AT ALL, which is what GA4 returns for
    a day it recorded nothing -- the shape a tracking outage makes.
    """
    s = dt.date.fromisoformat(start)
    e = dt.date.fromisoformat(end)
    days = [s + dt.timedelta(days=i) for i in range((e - s).days + 1)]
    live = [d for d in days if d.isoformat() not in skip_dates]
    weights = []
    for d in live:
        w = 1.0
        if d.weekday() >= 5:
            w = 0.72
        elif d.weekday() == 0:
            w = 1.12
        if spike_date and d.isoformat() == spike_date:
            w *= spike_multiplier
        weights.append(w)
    total_w = sum(weights) or 1.0

    rows = []
    for d, w in zip(live, weights):
        share = w / total_w
        values = {
            "sessions": float(round(total_sessions * share)),
            "activeUsers": float(round(total_users * share)),
            "totalUsers": float(round(total_users * share * 1.04)),
            "newUsers": float(round(total_users * share * 0.61)),
            "engagedSessions": float(round(total_sessions * share * 0.58)),
            "screenPageViews": float(round(total_views * share)),
            "eventCount": float(round(total_events * share)),
            "keyEvents": float(round(total_key_events * share)),
        }
        if revenue is not None:
            values["totalRevenue"] = round(revenue * share, 2)
            values["transactions"] = float(round(revenue * share / 84.0))
        rows.append(([d.strftime("%Y%m%d")], values))
    return rows


def segment(dimension, spec, legacy=False):
    """spec: [(key, sessions, users, engaged_share, key_events, revenue|None), ...]"""
    ke_name = "conversions" if legacy else "keyEvents"
    rate_name = "sessionConversionRate" if legacy else "sessionKeyEventRate"
    rows = []
    for key, sessions, users, eng_share, key_events, revenue in spec:
        values = {
            "sessions": float(sessions),
            "totalUsers": float(users),
            "newUsers": float(round(users * 0.6)),
            "engagedSessions": float(round(sessions * eng_share)),
            "engagementRate": eng_share,
            "averageSessionDuration": float(round(60 + 120 * eng_share, 1)),
            "screenPageViews": float(round(sessions * (1.4 + eng_share))),
        }
        if key_events is not None:
            values[ke_name] = float(key_events)
            values[rate_name] = (min(key_events, sessions) / sessions) if sessions else 0.0
        if revenue is not None:
            values["totalRevenue"] = float(revenue)
            values["transactions"] = float(round(revenue / 84.0))
        rows.append(([key], values))
    return report([dimension], rows)


def envelope(property_overrides=None, periods=None, datasets=None, key_events=None,
             ecommerce=None, errors=None, warnings=None, schema_support=None):
    prop = {
        "property_id": "123456789",
        "name": "Example Property",
        "admin_api_available": True,
        "time_zone": "America/New_York",
        "currency": "USD",
        "industry": "OTHER",
        "created": "2023-04-11T09:12:00Z",
        "account": "accounts/98765",
        "property_type": "PROPERTY_TYPE_ORDINARY",
        "data_streams": [{"name": "Web", "type": "WEB_DATA_STREAM",
                          "uri": "https://www.example.com", "measurement_id": "G-EXAMPLE01"}],
    }
    prop.update(property_overrides or {})
    per = periods or {
        "current": {"start": CUR[0], "end": CUR[1], "days": 30},
        "previous": {"start": PREV[0], "end": PREV[1], "days": 30},
        "basis": "most recent 30 completed days ending yesterday in America/New_York",
        "time_zone": "America/New_York",
        "time_zone_used": "America/New_York",
    }
    return {
        "schema": "reports-google-analytics/raw@1",
        "generated_at": "2026-08-20T06:15:00-04:00",
        "api": {"data_api": "https://analyticsdata.googleapis.com/v1beta",
                "admin_api": "https://analyticsadmin.googleapis.com/v1beta"},
        "property": prop,
        "periods": per,
        "schema_support": schema_support or {
            "metadata_loaded": True, "dimension_count": 218, "metric_count": 121,
            "custom_dimensions": [], "custom_metrics": [],
            "unsupported_metrics": [], "kpi_metrics_requested": [],
        },
        "key_events": key_events or {
            "metric_naming": "keyEvents",
            "metrics_used": ["keyEvents", "sessionKeyEventRate", "userKeyEventRate"],
            "definitions": [
                {"event_name": "generate_lead", "counting_method": "ONCE_PER_SESSION",
                 "custom": True, "created": "2024-02-01T10:00:00Z", "default_value": None},
                {"event_name": "contact_form_submit", "counting_method": "ONCE_PER_EVENT",
                 "custom": True, "created": "2024-02-01T10:00:00Z", "default_value": None},
            ],
            "declared_in_env": [],
        },
        "ecommerce": ecommerce or {"state": "no_data", "signals": {},
                                   "reason": "Ecommerce metrics were returned and every one "
                                             "is zero."},
        "datasets": datasets or {},
        "errors": errors or [],
        "warnings": warnings or [],
        "config": {
            "agency_env": "~/clients/agency.env",
            "client_env": "/path/to/client/.env",
            "property_id": prop["property_id"],
            "auth_mode": "oauth",
            "declared_key_events": [],
            "client_name": None,
            "site_url": "https://www.example.com",
        },
    }


def ds(current, previous, dimensions=(), sort_metric="sessions", limit=50):
    return {"dimensions": list(dimensions), "metrics": [], "limit": limit,
            "sort_metric": sort_metric, "current": current, "previous": previous}


# ---------------------------------------------------------------------------
# Fixtures
# ---------------------------------------------------------------------------

def fx_leadgen_healthy():
    """A normal lead-generation property: traffic up, key events up faster, no
    ecommerce. The case every other fixture is a deviation from."""
    cur = kpis(48200, 36100, 22400, 28900, 96400, 289000, 1244, avg_duration=104)
    prev = kpis(42800, 32700, 20900, 24800, 83100, 251000, 998, avg_duration=97)
    datasets = {
        "totals": ds(report([], [([], cur)], totals=cur), report([], [([], prev)], totals=prev),
                     limit=1),
        "daily": ds(report(["date"], daily_rows(CUR[0], CUR[1], 48200, 36100, 96400, 289000, 1244)),
                    report(["date"], daily_rows(PREV[0], PREV[1], 42800, 32700, 83100, 251000, 998)),
                    dimensions=["date"], sort_metric=None, limit=400),
        "channels": ds(
            segment("sessionDefaultChannelGroup", [
                ("Organic Search", 19400, 15100, 0.63, 512, None),
                ("Direct", 11200, 8900, 0.55, 246, None),
                ("Paid Search", 7800, 6200, 0.71, 338, None),
                ("Organic Social", 5100, 4300, 0.41, 62, None),
                ("Referral", 3200, 2400, 0.66, 74, None),
                ("Email", 1500, 1100, 0.78, 12, None),
            ]),
            segment("sessionDefaultChannelGroup", [
                ("Organic Search", 18100, 14200, 0.61, 466, None),
                ("Direct", 10600, 8500, 0.54, 231, None),
                ("Paid Search", 5900, 4700, 0.69, 214, None),
                ("Organic Social", 5400, 4600, 0.43, 58, None),
                ("Referral", 1600, 1300, 0.60, 21, None),
                ("Email", 1200, 900, 0.75, 8, None),
            ]),
            dimensions=["sessionDefaultChannelGroup"]),
        "first_user_channels": ds(
            segment("firstUserDefaultChannelGroup", [
                ("Organic Search", 17800, 14000, 0.62, 470, None),
                ("Direct", 9900, 8100, 0.54, 210, None),
                ("Paid Search", 6100, 5000, 0.70, 260, None),
            ]),
            segment("firstUserDefaultChannelGroup", [
                ("Organic Search", 17100, 13600, 0.60, 441, None),
                ("Direct", 9700, 8000, 0.53, 205, None),
                ("Paid Search", 4700, 3900, 0.68, 180, None),
            ]),
            dimensions=["firstUserDefaultChannelGroup"], sort_metric="totalUsers"),
        "source_medium": ds(
            segment("sessionSourceMedium", [
                ("google / organic", 18900, 14800, 0.63, 498, None),
                ("(direct) / (none)", 11200, 8900, 0.55, 246, None),
                ("google / cpc", 7800, 6200, 0.71, 338, None),
                ("facebook / social", 3900, 3300, 0.39, 41, None),
            ]),
            segment("sessionSourceMedium", [
                ("google / organic", 17700, 13900, 0.61, 452, None),
                ("(direct) / (none)", 10600, 8500, 0.54, 231, None),
                ("google / cpc", 5900, 4700, 0.69, 214, None),
                ("facebook / social", 4100, 3500, 0.41, 39, None),
            ]),
            dimensions=["sessionSourceMedium"]),
        "landing_pages": ds(
            segment("landingPagePlusQueryString", [
                ("/", 14200, 11800, 0.61, 288, None),
                ("/services/plumbing", 8900, 7400, 0.72, 402, None),
                ("/blog/how-to-choose-a-plumber", 7100, 6600, 0.34, 18, None),
                ("/contact", 4800, 3900, 0.81, 396, None),
                ("/services/heating", 4100, 3400, 0.69, 118, None),
                ("/pricing", 3600, 3000, 0.58, 22, None),
                ("/blog/winter-checklist", 2900, 2700, 0.29, 0, None),
            ]),
            segment("landingPagePlusQueryString", [
                ("/", 13800, 11500, 0.60, 262, None),
                ("/services/plumbing", 6900, 5800, 0.70, 301, None),
                ("/blog/how-to-choose-a-plumber", 7400, 6900, 0.36, 21, None),
                ("/contact", 4300, 3500, 0.80, 331, None),
                ("/services/heating", 4000, 3300, 0.68, 110, None),
                ("/pricing", 3400, 2900, 0.57, 19, None),
                ("/blog/winter-checklist", 4100, 3800, 0.31, 2, None),
            ]),
            dimensions=["landingPagePlusQueryString"], limit=100),
        "devices": ds(
            segment("deviceCategory", [
                ("mobile", 29300, 22600, 0.55, 522, None),
                ("desktop", 16400, 12100, 0.68, 682, None),
                ("tablet", 2500, 1400, 0.58, 40, None),
            ]),
            segment("deviceCategory", [
                ("mobile", 25100, 19400, 0.54, 428, None),
                ("desktop", 15600, 11800, 0.67, 546, None),
                ("tablet", 2100, 1500, 0.57, 24, None),
            ]),
            dimensions=["deviceCategory"], limit=10),
        "geo_country": ds(
            segment("country", [
                ("United States", 41200, 31000, 0.60, 1180, None),
                ("Canada", 3800, 2900, 0.58, 44, None),
                ("United Kingdom", 1600, 1300, 0.51, 12, None),
            ]),
            segment("country", [
                ("United States", 37100, 28200, 0.58, 950, None),
                ("Canada", 3300, 2600, 0.57, 36, None),
                ("United Kingdom", 1400, 1150, 0.50, 8, None),
            ]),
            dimensions=["country"], limit=30),
        "events": ds(
            report(["eventName"], [
                (["page_view"], {"eventCount": 96400.0, "totalUsers": 36100.0, "keyEvents": 0.0}),
                (["session_start"], {"eventCount": 48200.0, "totalUsers": 36100.0, "keyEvents": 0.0}),
                (["user_engagement"], {"eventCount": 44100.0, "totalUsers": 28900.0, "keyEvents": 0.0}),
                (["scroll"], {"eventCount": 39800.0, "totalUsers": 24100.0, "keyEvents": 0.0}),
                (["click"], {"eventCount": 21400.0, "totalUsers": 14200.0, "keyEvents": 0.0}),
                (["form_start"], {"eventCount": 3120.0, "totalUsers": 2810.0, "keyEvents": 0.0}),
                (["generate_lead"], {"eventCount": 848.0, "totalUsers": 812.0, "keyEvents": 848.0}),
                (["contact_form_submit"], {"eventCount": 396.0, "totalUsers": 381.0, "keyEvents": 396.0}),
                (["phone_click"], {"eventCount": 1240.0, "totalUsers": 1090.0, "keyEvents": 0.0}),
            ]),
            report(["eventName"], [
                (["page_view"], {"eventCount": 83100.0, "totalUsers": 32700.0, "keyEvents": 0.0}),
                (["session_start"], {"eventCount": 42800.0, "totalUsers": 32700.0, "keyEvents": 0.0}),
                (["user_engagement"], {"eventCount": 38200.0, "totalUsers": 24800.0, "keyEvents": 0.0}),
                (["scroll"], {"eventCount": 35100.0, "totalUsers": 21600.0, "keyEvents": 0.0}),
                (["click"], {"eventCount": 19100.0, "totalUsers": 12900.0, "keyEvents": 0.0}),
                (["form_start"], {"eventCount": 2640.0, "totalUsers": 2380.0, "keyEvents": 0.0}),
                (["generate_lead"], {"eventCount": 667.0, "totalUsers": 641.0, "keyEvents": 667.0}),
                (["contact_form_submit"], {"eventCount": 331.0, "totalUsers": 318.0, "keyEvents": 331.0}),
                (["phone_click"], {"eventCount": 1180.0, "totalUsers": 1040.0, "keyEvents": 0.0}),
            ]),
            dimensions=["eventName"], sort_metric="eventCount", limit=100),
    }
    return envelope(datasets=datasets)


def fx_ecommerce_growth():
    """A store with revenue, a working funnel, and a weakening checkout step."""
    cur_ec = ecom_block(184600, 2198, 1904, 61200, 92400, 18900, 9100, 3120)
    prev_ec = ecom_block(163200, 1942, 1712, 57400, 84100, 17400, 9600, 2780)
    cur = kpis(96200, 61200, 38900, 58100, 288600, 812000, 2198, avg_duration=142,
               ecommerce=cur_ec)
    prev = kpis(89400, 57400, 36600, 53200, 264800, 742000, 1942, avg_duration=138,
                ecommerce=prev_ec)
    datasets = {
        "totals": ds(report([], [([], cur)], totals=cur), report([], [([], prev)], totals=prev),
                     limit=1),
        "daily": ds(
            report(["date"], daily_rows(CUR[0], CUR[1], 96200, 61200, 288600, 812000, 2198,
                                        revenue=184600)),
            report(["date"], daily_rows(PREV[0], PREV[1], 89400, 57400, 264800, 742000, 1942,
                                        revenue=163200)),
            dimensions=["date"], sort_metric=None, limit=400),
        "channels": ds(
            segment("sessionDefaultChannelGroup", [
                ("Organic Search", 31200, 21400, 0.64, 742, 61800),
                ("Paid Search", 21800, 15600, 0.66, 604, 52400),
                ("Direct", 18400, 12900, 0.58, 401, 33900),
                ("Email", 9600, 5100, 0.79, 288, 24800),
                ("Organic Social", 9800, 7600, 0.42, 84, 6900),
                ("Referral", 5400, 3900, 0.61, 79, 4800),
            ]),
            segment("sessionDefaultChannelGroup", [
                ("Organic Search", 30100, 20800, 0.63, 698, 58200),
                ("Paid Search", 16900, 12400, 0.65, 471, 40100),
                ("Direct", 18900, 13300, 0.57, 396, 33100),
                ("Email", 9100, 4900, 0.78, 271, 23400),
                ("Organic Social", 9200, 7100, 0.41, 71, 5900),
                ("Referral", 5200, 3800, 0.60, 35, 2500),
            ]),
            dimensions=["sessionDefaultChannelGroup"]),
        "landing_pages": ds(
            segment("landingPagePlusQueryString", [
                ("/", 28400, 19800, 0.62, 604, 48200),
                ("/collections/new-arrivals", 16200, 11400, 0.71, 512, 44900),
                ("/products/signature-jacket", 11800, 8900, 0.68, 388, 36100),
                ("/collections/sale", 9600, 7200, 0.59, 214, 17400),
                ("/blog/style-guide", 8100, 7400, 0.31, 12, 900),
                ("/pages/shipping", 4200, 3800, 0.44, 18, 1200),
            ]),
            segment("landingPagePlusQueryString", [
                ("/", 27900, 19400, 0.61, 566, 45800),
                ("/collections/new-arrivals", 12100, 8800, 0.70, 402, 34600),
                ("/products/signature-jacket", 11400, 8600, 0.67, 356, 33200),
                ("/collections/sale", 9900, 7400, 0.58, 208, 16900),
                ("/blog/style-guide", 9800, 8900, 0.33, 15, 1100),
                ("/pages/shipping", 4100, 3700, 0.43, 14, 800),
            ]),
            dimensions=["landingPagePlusQueryString"], limit=100),
        "devices": ds(
            segment("deviceCategory", [
                ("mobile", 62400, 40100, 0.58, 1102, 82400),
                ("desktop", 30100, 18900, 0.66, 1042, 96800),
                ("tablet", 3700, 2200, 0.60, 54, 5400),
            ]),
            segment("deviceCategory", [
                ("mobile", 57800, 37600, 0.57, 942, 71200),
                ("desktop", 28200, 17800, 0.65, 962, 87400),
                ("tablet", 3400, 2000, 0.59, 38, 4600),
            ]),
            dimensions=["deviceCategory"], limit=10),
        "revenue_by_channel": ds(
            report(["sessionDefaultChannelGroup"], [
                (["Organic Search"], {"totalRevenue": 61800.0, "purchaseRevenue": 61800.0,
                                      "transactions": 742.0, "sessions": 31200.0,
                                      "totalPurchasers": 664.0}),
                (["Paid Search"], {"totalRevenue": 52400.0, "purchaseRevenue": 52400.0,
                                   "transactions": 604.0, "sessions": 21800.0,
                                   "totalPurchasers": 541.0}),
                (["Direct"], {"totalRevenue": 33900.0, "purchaseRevenue": 33900.0,
                              "transactions": 401.0, "sessions": 18400.0,
                              "totalPurchasers": 362.0}),
                (["Email"], {"totalRevenue": 24800.0, "purchaseRevenue": 24800.0,
                             "transactions": 288.0, "sessions": 9600.0,
                             "totalPurchasers": 244.0}),
            ]),
            report(["sessionDefaultChannelGroup"], [
                (["Organic Search"], {"totalRevenue": 58200.0, "transactions": 698.0,
                                      "sessions": 30100.0, "totalPurchasers": 631.0}),
                (["Paid Search"], {"totalRevenue": 40100.0, "transactions": 471.0,
                                   "sessions": 16900.0, "totalPurchasers": 428.0}),
                (["Direct"], {"totalRevenue": 33100.0, "transactions": 396.0,
                              "sessions": 18900.0, "totalPurchasers": 357.0}),
                (["Email"], {"totalRevenue": 23400.0, "transactions": 271.0,
                             "sessions": 9100.0, "totalPurchasers": 231.0}),
            ]),
            dimensions=["sessionDefaultChannelGroup"], sort_metric="totalRevenue"),
        "revenue_by_device": ds(
            report(["deviceCategory"], [
                (["desktop"], {"totalRevenue": 96800.0, "transactions": 1042.0,
                               "sessions": 30100.0, "purchaserRate": 0.049}),
                (["mobile"], {"totalRevenue": 82400.0, "transactions": 1102.0,
                              "sessions": 62400.0, "purchaserRate": 0.024}),
                (["tablet"], {"totalRevenue": 5400.0, "transactions": 54.0,
                              "sessions": 3700.0, "purchaserRate": 0.021}),
            ]),
            report(["deviceCategory"], [
                (["desktop"], {"totalRevenue": 87400.0, "transactions": 962.0,
                               "sessions": 28200.0, "purchaserRate": 0.048}),
                (["mobile"], {"totalRevenue": 71200.0, "transactions": 942.0,
                              "sessions": 57800.0, "purchaserRate": 0.022}),
                (["tablet"], {"totalRevenue": 4600.0, "transactions": 38.0,
                              "sessions": 3400.0, "purchaserRate": 0.019}),
            ]),
            dimensions=["deviceCategory"], sort_metric="totalRevenue"),
        "items": ds(
            report(["itemName"], [
                (["Signature Jacket"], {"itemsViewed": 14200.0, "itemsAddedToCart": 3100.0,
                                        "itemsPurchased": 604.0, "itemRevenue": 42800.0}),
                (["Merino Scarf"], {"itemsViewed": 9800.0, "itemsAddedToCart": 2400.0,
                                    "itemsPurchased": 512.0, "itemRevenue": 18400.0}),
                (["Rain Shell"], {"itemsViewed": 8100.0, "itemsAddedToCart": 1600.0,
                                  "itemsPurchased": 388.0, "itemRevenue": 31200.0}),
            ]),
            report(["itemName"], [
                (["Signature Jacket"], {"itemsViewed": 13100.0, "itemsAddedToCart": 2900.0,
                                        "itemsPurchased": 561.0, "itemRevenue": 39800.0}),
                (["Merino Scarf"], {"itemsViewed": 9100.0, "itemsAddedToCart": 2300.0,
                                    "itemsPurchased": 486.0, "itemRevenue": 17400.0}),
                (["Rain Shell"], {"itemsViewed": 7600.0, "itemsAddedToCart": 1500.0,
                                  "itemsPurchased": 341.0, "itemRevenue": 27400.0}),
            ]),
            dimensions=["itemName"], sort_metric="itemsPurchased", limit=25),
        "events": ds(
            report(["eventName"], [
                (["page_view"], {"eventCount": 288600.0, "totalUsers": 61200.0, "keyEvents": 0.0}),
                (["view_item"], {"eventCount": 92400.0, "totalUsers": 38900.0, "keyEvents": 0.0}),
                (["add_to_cart"], {"eventCount": 18900.0, "totalUsers": 12400.0, "keyEvents": 0.0}),
                (["begin_checkout"], {"eventCount": 9100.0, "totalUsers": 6800.0, "keyEvents": 0.0}),
                (["purchase"], {"eventCount": 2198.0, "totalUsers": 1904.0, "keyEvents": 2198.0}),
            ]),
            report(["eventName"], [
                (["page_view"], {"eventCount": 264800.0, "totalUsers": 57400.0, "keyEvents": 0.0}),
                (["view_item"], {"eventCount": 84100.0, "totalUsers": 36600.0, "keyEvents": 0.0}),
                (["add_to_cart"], {"eventCount": 17400.0, "totalUsers": 11600.0, "keyEvents": 0.0}),
                (["begin_checkout"], {"eventCount": 9600.0, "totalUsers": 7100.0, "keyEvents": 0.0}),
                (["purchase"], {"eventCount": 1942.0, "totalUsers": 1712.0, "keyEvents": 1942.0}),
            ]),
            dimensions=["eventName"], sort_metric="eventCount", limit=100),
    }
    return envelope(
        property_overrides={"name": "Example Store", "currency": "USD",
                            "industry": "SHOPPING"},
        datasets=datasets,
        key_events={"metric_naming": "keyEvents",
                    "metrics_used": ["keyEvents", "sessionKeyEventRate", "userKeyEventRate"],
                    "definitions": [{"event_name": "purchase",
                                     "counting_method": "ONCE_PER_EVENT", "custom": False,
                                     "created": "2023-04-11T09:12:00Z", "default_value": None}],
                    "declared_in_env": ["purchase"]},
        ecommerce={"state": "active",
                   "signals": {"transactions": {"current": 2198.0, "previous": 1942.0},
                               "purchaseRevenue": {"current": 184600.0, "previous": 163200.0}},
                   "reason": "The property returned non-zero purchase activity."})


def fx_no_key_events():
    """Key events are defined and none of them fired. Conversion reporting must
    be withheld, not reported as zero."""
    cur = kpis(12400, 9800, 6600, 6900, 24800, 71200, 0, avg_duration=88)
    prev = kpis(11900, 9400, 6300, 6600, 23100, 68400, 0, avg_duration=86)
    datasets = {
        "totals": ds(report([], [([], cur)], totals=cur), report([], [([], prev)], totals=prev),
                     limit=1),
        "daily": ds(report(["date"], daily_rows(CUR[0], CUR[1], 12400, 9800, 24800, 71200, 0)),
                    report(["date"], daily_rows(PREV[0], PREV[1], 11900, 9400, 23100, 68400, 0)),
                    dimensions=["date"], sort_metric=None, limit=400),
        "channels": ds(
            segment("sessionDefaultChannelGroup", [
                ("Organic Search", 6100, 4900, 0.58, 0, None),
                ("Direct", 3900, 3100, 0.52, 0, None),
                ("Referral", 2400, 1800, 0.61, 0, None),
            ]),
            segment("sessionDefaultChannelGroup", [
                ("Organic Search", 5900, 4700, 0.57, 0, None),
                ("Direct", 3800, 3000, 0.51, 0, None),
                ("Referral", 2200, 1700, 0.60, 0, None),
            ]),
            dimensions=["sessionDefaultChannelGroup"]),
        "devices": ds(
            segment("deviceCategory", [("mobile", 7400, 5900, 0.54, 0, None),
                                       ("desktop", 4600, 3600, 0.62, 0, None)]),
            segment("deviceCategory", [("mobile", 7100, 5700, 0.53, 0, None),
                                       ("desktop", 4500, 3500, 0.61, 0, None)]),
            dimensions=["deviceCategory"], limit=10),
        "events": ds(
            report(["eventName"], [
                (["page_view"], {"eventCount": 24800.0, "totalUsers": 9800.0, "keyEvents": 0.0}),
                (["session_start"], {"eventCount": 12400.0, "totalUsers": 9800.0, "keyEvents": 0.0}),
                (["scroll"], {"eventCount": 9100.0, "totalUsers": 5400.0, "keyEvents": 0.0}),
            ]),
            report(["eventName"], [
                (["page_view"], {"eventCount": 23100.0, "totalUsers": 9400.0, "keyEvents": 0.0}),
                (["session_start"], {"eventCount": 11900.0, "totalUsers": 9400.0, "keyEvents": 0.0}),
                (["scroll"], {"eventCount": 8700.0, "totalUsers": 5200.0, "keyEvents": 0.0}),
            ]),
            dimensions=["eventName"], sort_metric="eventCount", limit=100),
    }
    return envelope(datasets=datasets)


def fx_zero_previous():
    """A brand new property: the comparison period is genuinely all zeros, so
    every percentage change is undefined rather than infinite."""
    cur = kpis(3100, 2400, 2280, 1700, 6200, 18400, 46, avg_duration=76)
    prev = kpis(0, 0, 0, 0, 0, 0, 0, avg_duration=0)
    datasets = {
        "totals": ds(report([], [([], cur)], totals=cur), report([], [([], prev)], totals=prev),
                     limit=1),
        "daily": ds(report(["date"], daily_rows(CUR[0], CUR[1], 3100, 2400, 6200, 18400, 46)),
                    report(["date"], [], row_count=0,
                           meta={"currencyCode": "GBP", "timeZone": "Europe/London",
                                 "emptyReason": "NO_DATA_IN_DATE_RANGE"}),
                    dimensions=["date"], sort_metric=None, limit=400),
        "channels": ds(
            segment("sessionDefaultChannelGroup", [
                ("Direct", 1400, 1100, 0.51, 18, None),
                ("Organic Social", 1100, 900, 0.44, 12, None),
                ("Referral", 600, 400, 0.62, 16, None),
            ]),
            report(["sessionDefaultChannelGroup"], [], row_count=0,
                   meta={"emptyReason": "NO_DATA_IN_DATE_RANGE"}),
            dimensions=["sessionDefaultChannelGroup"]),
        "devices": ds(
            segment("deviceCategory", [("mobile", 1900, 1500, 0.48, 24, None),
                                       ("desktop", 1200, 900, 0.59, 22, None)]),
            report(["deviceCategory"], [], row_count=0),
            dimensions=["deviceCategory"], limit=10),
        "events": ds(
            report(["eventName"], [
                (["page_view"], {"eventCount": 6200.0, "totalUsers": 2400.0, "keyEvents": 0.0}),
                (["generate_lead"], {"eventCount": 46.0, "totalUsers": 44.0, "keyEvents": 46.0}),
            ]),
            report(["eventName"], [], row_count=0),
            dimensions=["eventName"], sort_metric="eventCount", limit=100),
    }
    return envelope(
        property_overrides={"name": "Example Launch Site", "currency": "GBP",
                            "time_zone": "Europe/London", "created": "2026-07-18T11:00:00Z"},
        datasets=datasets)


def fx_low_traffic():
    """Volumes too small for any rate metric to be stable. Nothing here should
    produce a confident finding."""
    cur = kpis(212, 168, 121, 104, 486, 1240, 6, avg_duration=71)
    prev = kpis(188, 149, 110, 96, 421, 1090, 9, avg_duration=68)
    datasets = {
        "totals": ds(report([], [([], cur)], totals=cur), report([], [([], prev)], totals=prev),
                     limit=1),
        "daily": ds(report(["date"], daily_rows(CUR[0], CUR[1], 212, 168, 486, 1240, 6)),
                    report(["date"], daily_rows(PREV[0], PREV[1], 188, 149, 421, 1090, 9)),
                    dimensions=["date"], sort_metric=None, limit=400),
        "channels": ds(
            segment("sessionDefaultChannelGroup", [
                ("Direct", 96, 74, 0.49, 3, None),
                ("Organic Search", 71, 58, 0.54, 2, None),
                ("Referral", 45, 36, 0.44, 1, None),
            ]),
            segment("sessionDefaultChannelGroup", [
                ("Direct", 84, 66, 0.48, 5, None),
                ("Organic Search", 66, 54, 0.52, 3, None),
                ("Referral", 38, 29, 0.42, 1, None),
            ]),
            dimensions=["sessionDefaultChannelGroup"]),
        "landing_pages": ds(
            segment("landingPagePlusQueryString", [
                ("/", 118, 92, 0.51, 4, None),
                ("/about", 44, 38, 0.39, 0, None),
                ("/contact", 50, 41, 0.62, 2, None),
            ]),
            segment("landingPagePlusQueryString", [
                ("/", 104, 84, 0.50, 6, None),
                ("/about", 41, 35, 0.38, 1, None),
                ("/contact", 43, 36, 0.60, 2, None),
            ]),
            dimensions=["landingPagePlusQueryString"], limit=100),
        "devices": ds(
            segment("deviceCategory", [("mobile", 128, 101, 0.47, 2, None),
                                       ("desktop", 84, 67, 0.55, 4, None)]),
            segment("deviceCategory", [("mobile", 112, 89, 0.46, 4, None),
                                       ("desktop", 76, 60, 0.54, 5, None)]),
            dimensions=["deviceCategory"], limit=10),
    }
    return envelope(property_overrides={"name": "Example Small Site"}, datasets=datasets)


def fx_tracking_outage():
    """Four days returned no rows and a key event stopped firing. The period
    total looks like a performance collapse and is not one."""
    skip = ["2026-08-08", "2026-08-09", "2026-08-10", "2026-08-11"]
    cur = kpis(31200, 24100, 15600, 17800, 62400, 168000, 402, avg_duration=91)
    prev = kpis(43800, 33900, 21400, 26100, 87600, 262000, 1104, avg_duration=99)
    datasets = {
        "totals": ds(report([], [([], cur)], totals=cur), report([], [([], prev)], totals=prev),
                     limit=1),
        "daily": ds(
            report(["date"], daily_rows(CUR[0], CUR[1], 31200, 24100, 62400, 168000, 402,
                                        skip_dates=skip)),
            report(["date"], daily_rows(PREV[0], PREV[1], 43800, 33900, 87600, 262000, 1104)),
            dimensions=["date"], sort_metric=None, limit=400),
        "channels": ds(
            segment("sessionDefaultChannelGroup", [
                ("Organic Search", 13100, 10200, 0.57, 168, None),
                ("Direct", 9400, 7300, 0.55, 121, None),
                ("Paid Search", 5600, 4400, 0.62, 88, None),
                ("Organic Social", 3100, 2600, 0.40, 25, None),
            ]),
            segment("sessionDefaultChannelGroup", [
                ("Organic Search", 18400, 14300, 0.58, 462, None),
                ("Direct", 13200, 10300, 0.56, 331, None),
                ("Paid Search", 7900, 6200, 0.63, 241, None),
                ("Organic Social", 4300, 3600, 0.41, 70, None),
            ]),
            dimensions=["sessionDefaultChannelGroup"]),
        "devices": ds(
            segment("deviceCategory", [("mobile", 19100, 14800, 0.53, 188, None),
                                       ("desktop", 11200, 8700, 0.63, 202, None),
                                       ("tablet", 900, 600, 0.55, 12, None)]),
            segment("deviceCategory", [("mobile", 26800, 20700, 0.54, 512, None),
                                       ("desktop", 15800, 12300, 0.64, 561, None),
                                       ("tablet", 1200, 900, 0.56, 31, None)]),
            dimensions=["deviceCategory"], limit=10),
        "events": ds(
            report(["eventName"], [
                (["page_view"], {"eventCount": 62400.0, "totalUsers": 24100.0, "keyEvents": 0.0}),
                (["session_start"], {"eventCount": 31200.0, "totalUsers": 24100.0, "keyEvents": 0.0}),
                (["generate_lead"], {"eventCount": 402.0, "totalUsers": 388.0, "keyEvents": 402.0}),
            ]),
            report(["eventName"], [
                (["page_view"], {"eventCount": 87600.0, "totalUsers": 33900.0, "keyEvents": 0.0}),
                (["session_start"], {"eventCount": 43800.0, "totalUsers": 33900.0, "keyEvents": 0.0}),
                (["generate_lead"], {"eventCount": 738.0, "totalUsers": 712.0, "keyEvents": 738.0}),
                (["contact_form_submit"], {"eventCount": 366.0, "totalUsers": 352.0,
                                           "keyEvents": 366.0}),
            ]),
            dimensions=["eventName"], sort_metric="eventCount", limit=100),
    }
    return envelope(property_overrides={"name": "Example Outage Property"}, datasets=datasets)


def fx_partial_failure():
    """Core data came back; the landing-page and event queries did not. Those
    sections must be absent from the report, not empty."""
    base = fx_leadgen_healthy()
    base["datasets"].pop("landing_pages", None)
    base["datasets"]["events"] = ds(None, None, dimensions=["eventName"],
                                    sort_metric="eventCount", limit=100)
    base["errors"] = [
        {"dataset": "landing_pages.current", "required": False,
         "message": "Exhausted property tokens for a project per property per hour.",
         "error_code": "RESOURCE_EXHAUSTED", "http_status": 429,
         "hint": "Analytics Data API quota exhausted for this property.", "retryable": True,
         "api": "data"},
        {"dataset": "events.current", "required": False,
         "message": "Exhausted property tokens for a project per property per hour.",
         "error_code": "RESOURCE_EXHAUSTED", "http_status": 429,
         "hint": "Analytics Data API quota exhausted for this property.", "retryable": True,
         "api": "data"},
    ]
    base["warnings"].append(
        "landing_pages and events could not be retrieved this run. Those sections are "
        "unavailable, which is not the same as empty.")
    return base


def fx_legacy_conversions():
    """A property that still answers to `conversions` rather than `keyEvents`."""
    cur = kpis(22600, 17400, 11200, 13100, 44800, 128000, 486, avg_duration=93, legacy=True)
    prev = kpis(21100, 16300, 10600, 12100, 41900, 119000, 441, avg_duration=91, legacy=True)
    datasets = {
        "totals": ds(report([], [([], cur)], totals=cur), report([], [([], prev)], totals=prev),
                     limit=1),
        "daily": ds(report(["date"], daily_rows(CUR[0], CUR[1], 22600, 17400, 44800, 128000, 486)),
                    report(["date"], daily_rows(PREV[0], PREV[1], 21100, 16300, 41900, 119000, 441)),
                    dimensions=["date"], sort_metric=None, limit=400),
        "channels": ds(
            segment("sessionDefaultChannelGroup", [
                ("Organic Search", 9800, 7600, 0.60, 212, None),
                ("Direct", 6400, 5100, 0.54, 128, None),
                ("Email", 3200, 2100, 0.74, 96, None),
                ("Referral", 3200, 2600, 0.58, 50, None),
            ], legacy=True),
            segment("sessionDefaultChannelGroup", [
                ("Organic Search", 9400, 7300, 0.59, 198, None),
                ("Direct", 6200, 4900, 0.53, 121, None),
                ("Email", 2800, 1900, 0.73, 84, None),
                ("Referral", 2700, 2200, 0.57, 38, None),
            ], legacy=True),
            dimensions=["sessionDefaultChannelGroup"]),
        "devices": ds(
            segment("deviceCategory", [("mobile", 13400, 10200, 0.56, 214, None),
                                       ("desktop", 8400, 6600, 0.65, 258, None),
                                       ("tablet", 800, 600, 0.58, 14, None)], legacy=True),
            segment("deviceCategory", [("mobile", 12600, 9600, 0.55, 196, None),
                                       ("desktop", 7900, 6200, 0.64, 232, None),
                                       ("tablet", 600, 500, 0.57, 13, None)], legacy=True),
            dimensions=["deviceCategory"], limit=10),
    }
    return envelope(
        property_overrides={"name": "Example Legacy Property"},
        datasets=datasets,
        key_events={"metric_naming": "conversions (pre-2024 naming)",
                    "metrics_used": ["conversions", "sessionConversionRate",
                                     "userConversionRate"],
                    "definitions": None, "declared_in_env": []},
        warnings=["This property reports the older `conversions` metric rather than "
                  "`keyEvents`."])


def fx_not_set_heavy():
    """A third of sessions unattributed, and GA4 folding rows into (other)."""
    cur = kpis(58400, 44100, 29800, 33200, 116800, 342000, 1102, avg_duration=87)
    prev = kpis(56100, 42600, 28400, 32100, 112200, 331000, 1064, avg_duration=88)
    loss_meta = {"currencyCode": "USD", "timeZone": "America/New_York",
                 "dataLossFromOtherRow": True}
    channels_cur = segment("sessionDefaultChannelGroup", [
        ("Direct", 24800, 19100, 0.52, 402, None),
        ("Organic Search", 14200, 11100, 0.61, 344, None),
        ("Unassigned", 9800, 7600, 0.44, 121, None),
        ("(not set)", 6100, 4800, 0.41, 88, None),
        ("Referral", 3500, 2700, 0.58, 147, None),
    ])
    channels_cur["meta"] = loss_meta
    channels_prev = segment("sessionDefaultChannelGroup", [
        ("Direct", 16400, 12800, 0.51, 288, None),
        ("Organic Search", 19800, 15400, 0.62, 466, None),
        ("Unassigned", 8900, 6900, 0.43, 112, None),
        ("(not set)", 6900, 5400, 0.40, 91, None),
        ("Referral", 4100, 3200, 0.57, 107, None),
    ])
    datasets = {
        "totals": ds(report([], [([], cur)], totals=cur), report([], [([], prev)], totals=prev),
                     limit=1),
        "daily": ds(report(["date"], daily_rows(CUR[0], CUR[1], 58400, 44100, 116800, 342000, 1102)),
                    report(["date"], daily_rows(PREV[0], PREV[1], 56100, 42600, 112200, 331000, 1064)),
                    dimensions=["date"], sort_metric=None, limit=400),
        "channels": ds(channels_cur, channels_prev, dimensions=["sessionDefaultChannelGroup"]),
        "landing_pages": ds(
            segment("landingPagePlusQueryString", [
                ("/", 21400, 16800, 0.56, 388, None),
                ("(other)", 14100, 11200, 0.48, 201, None),
                ("/products", 8900, 7100, 0.63, 288, None),
            ]),
            segment("landingPagePlusQueryString", [
                ("/", 20800, 16300, 0.55, 366, None),
                ("(other)", 13400, 10700, 0.47, 188, None),
                ("/products", 8600, 6900, 0.62, 271, None),
            ]),
            dimensions=["landingPagePlusQueryString"], limit=100),
        "devices": ds(
            segment("deviceCategory", [("mobile", 36100, 27400, 0.55, 512, None),
                                       ("desktop", 20800, 15800, 0.62, 566, None)]),
            segment("deviceCategory", [("mobile", 34600, 26300, 0.54, 488, None),
                                       ("desktop", 20100, 15300, 0.61, 549, None)]),
            dimensions=["deviceCategory"], limit=10),
    }
    return envelope(property_overrides={"name": "Example Unattributed Property"},
                    datasets=datasets)


def fx_no_admin_api():
    """The Admin API is switched off: no property name, no key-event
    definitions. Reporting still works; the report must not invent a name."""
    base = fx_leadgen_healthy()
    base["property"].update({
        "name": None, "admin_api_available": False,
        "admin_api_error": "Google Analytics Admin API has not been used in project "
                           "0000000000 before or it is disabled.",
        "time_zone": "America/New_York", "time_zone_source": "Data API response metadata",
        "currency": "USD", "currency_source": "Data API response metadata",
        "industry": None, "created": None, "data_streams": None,
    })
    base["key_events"]["definitions"] = None
    base["warnings"].append(
        "The Google Analytics Admin API did not answer (SERVICE_DISABLED), so the property's "
        "name and key-event definitions could not be read.")
    return base


def fx_unsupported_metrics():
    """A property whose schema is missing several requested metrics. They must
    print as 'not available', never as zero."""
    base = fx_leadgen_healthy()
    drop = ["screenPageViewsPerSession", "sessionsPerUser", "userEngagementDuration",
            "userKeyEventRate"]
    for period in ("current", "previous"):
        rep = base["datasets"]["totals"][period]
        for m in drop:
            rep["totals"].pop(m, None)
            for row in rep["rows"]:
                row["values"].pop(m, None)
        rep["metrics"] = [m for m in rep["metrics"] if m["name"] not in drop]
    base["schema_support"]["unsupported_metrics"] = [
        {"metric": m, "reason": "not in this property's metric schema"} for m in drop]
    return base


FIXTURES = {
    "leadgen-healthy": (fx_leadgen_healthy,
                        "Normal lead-gen property, growth, full metric availability"),
    "ecommerce-growth": (fx_ecommerce_growth,
                         "Store with revenue, item data, and a weakening checkout step"),
    "no-key-events": (fx_no_key_events,
                      "Key events defined, none fired -- conversions unreportable"),
    "zero-previous": (fx_zero_previous, "Comparison period is genuinely all zeros"),
    "low-traffic": (fx_low_traffic, "Volumes too small for stable rate metrics"),
    "tracking-outage": (fx_tracking_outage,
                        "Four days with no rows and a key event that stopped firing"),
    "partial-failure": (fx_partial_failure, "Quota errors killed two optional datasets"),
    "legacy-conversions": (fx_legacy_conversions,
                           "Property answering to `conversions`, not `keyEvents`"),
    "not-set-heavy": (fx_not_set_heavy,
                      "Large (not set)/(other) buckets plus cardinality data loss"),
    "no-admin-api": (fx_no_admin_api,
                     "Admin API disabled: no property name, no key-event definitions"),
    "unsupported-metrics": (fx_unsupported_metrics,
                            "Property schema missing several KPIs -- must read 'not available'"),
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
