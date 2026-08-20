#!/usr/bin/env python3
"""
Generate the offline fixtures the test suite runs against.

    python3 make_fixtures.py            # write them all
    python3 make_fixtures.py --list     # what each one is for

Every fixture is a complete `*_raw.json` in exactly the shape
fetch_search_console.py writes, so the whole analytical half of the skill runs
against them with no credentials, no network and no quota.

They are deterministic -- fixed seeds, round numbers -- so assertions can be
exact rather than approximate.

The cases are chosen for the shapes that break Search Console reports, not the
shapes that break code:

  healthy         growth everywhere, every dataset present
  ctr-decline     rankings held, CTR fell, clicks fell faster than impressions
  visibility-loss impressions collapsed on a handful of pages, one deindexed
  zero-previous   a newly verified property with an empty comparison period
  low-traffic     a small local property where percentages mean very little
  truncated       a large property whose query extract hit the row cap
  partial         search appearance and countries failed to retrieve
  domain-property a domain property with a second search type in play
"""

import argparse
import json
import random
from datetime import date, timedelta
from pathlib import Path

HERE = Path(__file__).resolve().parent
OUT = HERE.parent / "assets" / "fixtures"

CURRENT = ("2026-07-18", "2026-08-16")
PREVIOUS = ("2026-06-18", "2026-07-17")
LATEST_FINAL = "2026-08-16"


# ---------------------------------------------------------------------------
# Builders
# ---------------------------------------------------------------------------

def daily(start, days, clicks_base, impressions_base, position, seed,
          trend=0.0, spike_on=None, spike_factor=3.0, drop_on=None, drop_factor=0.2,
          ctr_drift=0.0):
    """A day-by-day series with weekday shape, a gentle trend, and optional
    single-day events. Weekend dips are deliberate: an anomaly detector that
    calls every Sunday an anomaly is worse than none."""
    rnd = random.Random(seed)
    d0 = date.fromisoformat(start)
    rows = []
    for i in range(days):
        day = d0 + timedelta(days=i)
        weekend = 0.72 if day.weekday() >= 5 else 1.0
        drift = 1.0 + trend * (i / max(1, days - 1))
        noise = 1.0 + rnd.uniform(-0.08, 0.08)
        impressions = impressions_base * weekend * drift * noise
        clicks = clicks_base * weekend * drift * noise * (1.0 + ctr_drift * (i / max(1, days - 1)))
        if spike_on == str(day):
            clicks *= spike_factor
            impressions *= spike_factor
        if drop_on == str(day):
            clicks *= drop_factor
            impressions *= drop_factor
        clicks = int(round(clicks))
        impressions = int(round(impressions))
        rows.append({
            "date": str(day),
            "clicks": clicks,
            "impressions": impressions,
            "ctr": (clicks / impressions) if impressions else 0.0,
            "position": round(position + rnd.uniform(-0.4, 0.4), 2),
        })
    return rows


def row(dim, key, clicks, impressions, position):
    return {
        dim: key,
        "clicks": clicks,
        "impressions": impressions,
        "ctr": (clicks / impressions) if impressions else 0.0,
        "position": position,
    }


def totals_row(clicks, impressions, position):
    return [{
        "clicks": clicks,
        "impressions": impressions,
        "ctr": (clicks / impressions) if impressions else 0.0,
        "position": position,
    }]


def meta(dimensions, start, end, rows, truncated=False, row_limit=25000, pages=1,
         search_type="web"):
    return {
        "dimensions": dimensions,
        "search_type": search_type,
        "start_date": start,
        "end_date": end,
        "data_state": "final",
        "row_limit": row_limit,
        "pages_fetched": pages,
        "rows_returned": rows,
        "truncated": truncated,
        "complete": not truncated,
        "aggregation_type": None,
    }


def dataset(dimensions, current_rows, previous_rows, truncated=False, pages=1):
    node = {
        "current": {
            "rows": current_rows,
            "meta": meta(dimensions, CURRENT[0], CURRENT[1], len(current_rows), truncated,
                         pages=pages),
        }
    }
    if previous_rows is not None:
        node["previous"] = {
            "rows": previous_rows,
            "meta": meta(dimensions, PREVIOUS[0], PREVIOUS[1], len(previous_rows), truncated,
                         pages=pages),
        }
    return node


def envelope(site_url, datasets, property_type="url_prefix", warnings=None, errors=None,
             settings=None, extra=None, freshness=None, permission="siteFullUser"):
    return {
        "schema": "reports-google-search-console/raw@1",
        "generated_at": "2026-08-19T09:00:00+01:00",
        "retrieval_seconds": 12.3,
        "api_calls": 18,
        "partial": bool(errors),
        "property": {
            "site_url": site_url,
            "property_type": property_type,
            "permission_level": permission,
            "display": site_url.replace("sc-domain:", "").replace("https://", "").rstrip("/"),
            "access": "ok",
        },
        "client": {"name": None},
        "freshness": freshness or {
            "latest_final": LATEST_FINAL,
            "latest_including_fresh": "2026-08-18",
            "queried_through": "2026-08-19",
            "lag_days": 3,
            "fresh_days_available": 2,
            "days_with_final_data_in_window": 12,
            "lookback_days": 14,
        },
        "periods": {
            "current": {"start": CURRENT[0], "end": CURRENT[1], "days": 30},
            "previous": {"start": PREVIOUS[0], "end": PREVIOUS[1], "days": 30},
            "lag_days": 0,
            "comparable": True,
            "basis": "the most recent 30 finalised days for this property (latest finalised "
                     "date %s), against the 30 days immediately before them" % LATEST_FINAL,
        },
        "search_type": "web",
        "data_state": "final",
        "settings": {
            "report_days": 30,
            "lag_days": 0,
            "row_limit": 25000,
            "max_rows": 50000,
            "chunk_days": 0,
            "brand_terms": (settings or {}).get("brand_terms", []),
            "brand_terms_configured": bool((settings or {}).get("brand_terms")),
            "primary_country": None,
            "extra_search_types": (settings or {}).get("extra_search_types", []),
            "skipped": [],
        },
        "datasets": datasets,
        "extra_search_types": extra or {},
        "errors": errors or [],
        "warnings": warnings or [],
    }


def scale(rows, factor, position_shift=0.0, dim=None):
    """The same dimensional rows at a different volume, for a comparison period."""
    out = []
    for r in rows:
        clicks = int(round((r["clicks"] or 0) * factor))
        impressions = int(round((r["impressions"] or 0) * factor))
        copy = dict(r)
        copy["clicks"] = clicks
        copy["impressions"] = impressions
        copy["ctr"] = (clicks / impressions) if impressions else 0.0
        copy["position"] = round((r["position"] or 0) + position_shift, 1)
        out.append(copy)
    return out


# ---------------------------------------------------------------------------
# Query and page sets
# ---------------------------------------------------------------------------

def query_set(rnd, count, top_clicks, brandish=True):
    """A realistic-shaped query set: a few heavy heads, a long tail, and a
    handful of high-impression low-CTR rows for the opportunity logic to find."""
    rows = []
    for i in range(count):
        decay = 1.0 / (1.0 + i * 0.55)
        clicks = max(0, int(round(top_clicks * decay * rnd.uniform(0.85, 1.15))))
        position = round(1.2 + i * 0.45 + rnd.uniform(-0.3, 0.6), 1)
        ctr = max(0.004, 0.32 * (1.0 / (1.0 + position * 0.55)))
        impressions = max(clicks + 1, int(round(clicks / ctr))) if clicks else int(
            round(400 * decay))
        rows.append(row("query", "example query %d" % (i + 1), clicks, impressions, position))
    if brandish:
        rows.append(row("query", "examplebrand", int(top_clicks * 0.8), int(top_clicks * 1.2), 1.1))
        rows.append(row("query", "example brand reviews", int(top_clicks * 0.15),
                        int(top_clicks * 0.4), 1.8))
    return rows


def page_set(rnd, count, top_clicks, base="https://www.example.com"):
    rows = []
    paths = ["/", "/services/", "/pricing/", "/blog/guide-to-widgets/", "/contact/",
             "/blog/how-to-choose/", "/products/widget-a/", "/products/widget-b/",
             "/about/", "/blog/comparison/", "/resources/", "/case-studies/",
             "/blog/checklist/", "/support/", "/locations/"]
    for i in range(min(count, len(paths))):
        decay = 1.0 / (1.0 + i * 0.5)
        clicks = max(0, int(round(top_clicks * decay * rnd.uniform(0.9, 1.1))))
        position = round(2.0 + i * 0.9 + rnd.uniform(-0.4, 0.5), 1)
        ctr = max(0.005, 0.28 * (1.0 / (1.0 + position * 0.5)))
        impressions = max(clicks + 1, int(round(clicks / ctr))) if clicks else 500
        rows.append(row("page", base + paths[i], clicks, impressions, position))
    return rows


# ---------------------------------------------------------------------------
# Fixtures
# ---------------------------------------------------------------------------

def fx_healthy():
    rnd = random.Random(11)
    queries_cur = query_set(rnd, 24, 900)
    # One deliberately underperforming high-impression row for the CTR
    # opportunity logic, and one page-two row with real volume for the ranking
    # opportunity logic.
    queries_cur.append(row("query", "widget buying guide", 120, 42000, 4.8))
    queries_cur.append(row("query", "best widgets 2026", 40, 18000, 12.4))
    queries_prev = scale(queries_cur, 0.86, 0.4)
    queries_prev = [r for r in queries_prev if r["query"] != "example query 7"]

    pages_cur = page_set(rnd, 14, 1400)
    pages_cur.append(row("page", "https://www.example.com/blog/widget-buying-guide/",
                         420, 96000, 4.6))
    pages_prev = scale(pages_cur, 0.84, 0.5)

    cur_clicks = 12480
    prev_clicks = 10640
    cur_impressions = 341000
    prev_impressions = 302500

    datasets = {
        "totals": dataset([], totals_row(cur_clicks, cur_impressions, 11.4),
                          totals_row(prev_clicks, prev_impressions, 12.1)),
        "daily": dataset(["date"],
                         daily(CURRENT[0], 30, 416, 11367, 11.4, seed=1, trend=0.18),
                         daily(PREVIOUS[0], 30, 355, 10083, 12.1, seed=2, trend=0.05)),
        "queries": dataset(["query"], queries_cur, queries_prev),
        "pages": dataset(["page"], pages_cur, pages_prev),
        "query_page": {"current": {
            "rows": [
                row("query", "widget buying guide", 90, 30000, 4.5) | {
                    "page": "https://www.example.com/blog/widget-buying-guide/"},
                row("query", "widget buying guide", 30, 12000, 8.9) | {
                    "page": "https://www.example.com/blog/guide-to-widgets/"},
                row("query", "example query 1", 800, 9000, 1.4) | {
                    "page": "https://www.example.com/"},
            ],
            "meta": meta(["query", "page"], CURRENT[0], CURRENT[1], 3),
        }},
        "devices": dataset(["device"], [
            row("device", "MOBILE", 7200, 219000, 12.6),
            row("device", "DESKTOP", 5000, 118000, 9.4),
            row("device", "TABLET", 280, 4000, 11.9),
        ], [
            row("device", "MOBILE", 6100, 194000, 13.1),
            row("device", "DESKTOP", 4300, 104500, 9.9),
            row("device", "TABLET", 240, 4000, 12.2),
        ]),
        "countries": dataset(["country"], [
            row("country", "usa", 9800, 268000, 11.0),
            row("country", "can", 1400, 39000, 12.2),
            row("country", "gbr", 780, 22000, 13.4),
            row("country", "aus", 300, 9000, 14.1),
        ], [
            row("country", "usa", 8500, 240000, 11.6),
            row("country", "can", 1150, 34000, 12.8),
            row("country", "gbr", 690, 19500, 13.9),
            row("country", "aus", 240, 8000, 14.6),
        ]),
        "search_appearance": dataset(["searchAppearance"], [
            row("searchAppearance", "AMP_BLUE_LINK", 0, 0, 0.0),
            row("searchAppearance", "PRODUCT_SNIPPETS", 1900, 41000, 8.2),
            row("searchAppearance", "REVIEW_SNIPPET", 640, 19000, 9.1),
        ], [
            row("searchAppearance", "PRODUCT_SNIPPETS", 1500, 33000, 8.9),
            row("searchAppearance", "REVIEW_SNIPPET", 610, 18500, 9.3),
        ]),
    }
    return envelope("https://www.example.com/", datasets,
                    settings={"brand_terms": ["examplebrand", "example brand"]})


def fx_ctr_decline():
    """Rankings held, impressions held, CTR fell. The case a report most often
    gets wrong by blaming rankings."""
    rnd = random.Random(21)
    queries_cur = query_set(rnd, 20, 300, brandish=False)
    queries_prev = []
    for r in queries_cur:
        copy = dict(r)
        copy["clicks"] = int(round(r["clicks"] * 1.42))
        copy["impressions"] = int(round(r["impressions"] * 1.02))
        copy["ctr"] = copy["clicks"] / copy["impressions"]
        copy["position"] = r["position"] + 0.05
        queries_prev.append(copy)

    pages_cur = page_set(rnd, 12, 500)
    pages_prev = []
    for r in pages_cur:
        copy = dict(r)
        copy["clicks"] = int(round(r["clicks"] * 1.4))
        copy["impressions"] = int(round(r["impressions"] * 1.01))
        copy["ctr"] = copy["clicks"] / copy["impressions"]
        copy["position"] = r["position"]
        pages_prev.append(copy)

    datasets = {
        "totals": dataset([], totals_row(4100, 210000, 9.8),
                          totals_row(5900, 206000, 9.9)),
        "daily": dataset(["date"],
                         daily(CURRENT[0], 30, 137, 7000, 9.8, seed=3, trend=-0.15),
                         daily(PREVIOUS[0], 30, 197, 6867, 9.9, seed=4)),
        "queries": dataset(["query"], queries_cur, queries_prev),
        "pages": dataset(["page"], pages_cur, pages_prev),
        "devices": dataset(["device"], [
            row("device", "MOBILE", 2400, 140000, 10.4),
            row("device", "DESKTOP", 1700, 70000, 8.6),
        ], [
            row("device", "MOBILE", 3800, 138000, 10.3),
            row("device", "DESKTOP", 2100, 68000, 8.7),
        ]),
    }
    return envelope("https://www.example.com/", datasets)


def fx_visibility_loss():
    """Impressions gone on a handful of pages, one of them no longer indexed."""
    rnd = random.Random(31)
    pages_cur = page_set(rnd, 10, 300)
    pages_prev = scale(pages_cur, 1.05)
    # Three pages that had real visibility and now have almost none.
    gone = [
        ("https://www.example.com/resources/big-guide/", 12, 900, 28.0, 640, 41000, 6.2),
        ("https://www.example.com/blog/legacy-post/", 0, 0, None, 310, 22000, 7.8),
        ("https://www.example.com/products/discontinued/", 4, 400, 33.0, 180, 12500, 9.1),
    ]
    for url, c, i, p, pc, pi, pp in gone:
        if i:
            pages_cur.append(row("page", url, c, i, p))
        pages_prev.append(row("page", url, pc, pi, pp))

    queries_cur = query_set(rnd, 15, 200, brandish=False)
    queries_prev = scale(queries_cur, 1.6, -0.6)

    datasets = {
        "totals": dataset([], totals_row(2400, 88000, 14.8),
                          totals_row(3600, 152000, 11.2)),
        "daily": dataset(["date"],
                         daily(CURRENT[0], 30, 80, 2933, 14.8, seed=5, trend=-0.35,
                               drop_on="2026-08-04", drop_factor=0.15),
                         daily(PREVIOUS[0], 30, 120, 5067, 11.2, seed=6)),
        "queries": dataset(["query"], queries_cur, queries_prev),
        "pages": dataset(["page"], pages_cur, pages_prev),
        "url_inspection": {
            "results": [{
                "url": "https://www.example.com/blog/legacy-post/",
                "verdict": "NEUTRAL",
                "coverage_state": "Crawled - currently not indexed",
                "robots_txt_state": "ALLOWED",
                "indexing_state": "INDEXING_ALLOWED",
                "page_fetch_state": "SUCCESSFUL",
                "last_crawl_time": "2026-07-29T04:12:00Z",
                "crawled_as": "MOBILE",
                "google_canonical": "https://www.example.com/blog/legacy-post/",
                "user_canonical": "https://www.example.com/blog/legacy-post/",
                "selected_because": "no impressions at all this period, 22000 previously",
                "mobile_usability_verdict": "PASS",
                "rich_results_verdict": None,
                "inspection_link": None,
            }],
            "note": "URL Inspection reports index status at the moment of the call.",
        },
    }
    return envelope("https://www.example.com/", datasets)


def fx_zero_previous():
    """A newly verified property. The comparison period has no data at all --
    not zeros, no rows."""
    rnd = random.Random(41)
    queries_cur = query_set(rnd, 8, 40, brandish=False)
    pages_cur = page_set(rnd, 5, 60)
    datasets = {
        "totals": dataset([], totals_row(310, 14200, 18.6), []),
        "daily": dataset(["date"], daily(CURRENT[0], 30, 10, 473, 18.6, seed=7, trend=1.4), []),
        "queries": dataset(["query"], queries_cur, []),
        "pages": dataset(["page"], pages_cur, []),
    }
    return envelope(
        "https://www.newsite.example/", datasets,
        warnings=["The property was verified inside the comparison window; the previous period "
                  "has no data because the property did not exist to Search Console yet."],
    )


def fx_low_traffic():
    """A small local property. Percentages here are almost meaningless and the
    analysis must say so rather than report a 60% swing on nine clicks."""
    rnd = random.Random(51)
    queries_cur = [
        row("query", "plumber near me", 6, 340, 8.2),
        row("query", "emergency plumber", 4, 210, 11.4),
        row("query", "boiler repair cost", 3, 190, 14.8),
        row("query", "local plumbing company", 2, 90, 9.1),
    ]
    queries_prev = [
        row("query", "plumber near me", 4, 300, 9.0),
        row("query", "emergency plumber", 3, 180, 12.1),
        row("query", "boiler repair cost", 2, 150, 15.9),
    ]
    pages_cur = [
        row("page", "https://www.example.com/", 9, 520, 9.4),
        row("page", "https://www.example.com/contact/", 4, 190, 11.2),
    ]
    pages_prev = [
        row("page", "https://www.example.com/", 6, 460, 10.1),
        row("page", "https://www.example.com/contact/", 3, 160, 11.9),
    ]
    datasets = {
        "totals": dataset([], totals_row(19, 980, 10.2), totals_row(13, 840, 11.1)),
        "daily": dataset(["date"], daily(CURRENT[0], 30, 0.6, 33, 10.2, seed=8),
                         daily(PREVIOUS[0], 30, 0.4, 28, 11.1, seed=9)),
        "queries": dataset(["query"], queries_cur, queries_prev),
        "pages": dataset(["page"], pages_cur, pages_prev),
    }
    return envelope("https://www.example.com/", datasets)


def fx_truncated():
    """A large property whose query extract hit the API row cap. The report must
    not present it as the complete query set."""
    rnd = random.Random(61)
    queries_cur = query_set(rnd, 40, 4000)
    queries_prev = scale(queries_cur, 0.95, 0.2)
    pages_cur = page_set(rnd, 15, 8000)
    pages_prev = scale(pages_cur, 0.97)
    datasets = {
        "totals": dataset([], totals_row(184000, 6120000, 14.2),
                          totals_row(178000, 5940000, 14.5)),
        "daily": dataset(["date"],
                         daily(CURRENT[0], 30, 6133, 204000, 14.2, seed=10),
                         daily(PREVIOUS[0], 30, 5933, 198000, 14.5, seed=12)),
        "queries": dataset(["query"], queries_cur, queries_prev, truncated=True, pages=2),
        "pages": dataset(["page"], pages_cur, pages_prev),
    }
    env = envelope("sc-domain:example.com", datasets, property_type="domain")
    env["warnings"].append(
        "queries.current: the extract hit the 50000-row cap and was stopped. This dataset is a "
        "partial view of the period; totals derived from it are lower bounds."
    )
    return env


def fx_partial():
    """Two optional datasets failed. They are unavailable, which is not empty."""
    rnd = random.Random(71)
    queries_cur = query_set(rnd, 14, 400, brandish=False)
    pages_cur = page_set(rnd, 10, 600)
    datasets = {
        "totals": dataset([], totals_row(5200, 190000, 10.9),
                          totals_row(5050, 187000, 11.0)),
        "daily": dataset(["date"], daily(CURRENT[0], 30, 173, 6333, 10.9, seed=13),
                         daily(PREVIOUS[0], 30, 168, 6233, 11.0, seed=14)),
        "queries": dataset(["query"], queries_cur, scale(queries_cur, 0.98)),
        "pages": dataset(["page"], pages_cur, scale(pages_cur, 0.99)),
        "devices": dataset(["device"], [
            row("device", "MOBILE", 3100, 120000, 11.4),
            row("device", "DESKTOP", 2100, 70000, 10.1),
        ], [
            row("device", "MOBILE", 3000, 118000, 11.5),
            row("device", "DESKTOP", 2050, 69000, 10.2),
        ]),
    }
    return envelope(
        "https://shop.example.com/", datasets,
        errors=[
            {"dataset": "search_appearance", "fatal": False,
             "message": "Search Console returned HTTP 400 for the searchAppearance dimension.",
             "http_status": 400, "reason": "badRequest", "retryable": False,
             "detail": "This property returns no search appearance data."},
            {"dataset": "countries", "fatal": False,
             "message": "Rate limit exceeded.", "http_status": 429, "reason": "rateLimitExceeded",
             "retryable": True, "detail": "Retry later."},
        ],
        warnings=["Search appearance data is unavailable for this property."],
    )


def fx_domain_property():
    """A domain property, with Image search retrieved as a separate dataset that
    must never be folded into the web totals."""
    rnd = random.Random(81)
    queries_cur = query_set(rnd, 18, 700)
    pages_cur = page_set(rnd, 12, 900, base="https://blog.example.com")
    datasets = {
        "totals": dataset([], totals_row(9400, 288000, 12.8),
                          totals_row(8900, 275000, 13.0)),
        "daily": dataset(["date"], daily(CURRENT[0], 30, 313, 9600, 12.8, seed=15,
                                         spike_on="2026-08-02", spike_factor=3.4),
                         daily(PREVIOUS[0], 30, 297, 9167, 13.0, seed=16)),
        "queries": dataset(["query"], queries_cur, scale(queries_cur, 0.94, 0.3)),
        "pages": dataset(["page"], pages_cur, scale(pages_cur, 0.95, 0.2)),
        "sitemaps": {"entries": [
            {"path": "https://example.com/sitemap.xml", "last_submitted": "2026-02-01T10:00:00Z",
             "last_downloaded": "2026-08-15T02:10:00Z", "is_pending": False,
             "is_sitemaps_index": True, "type": "sitemapIndex", "warnings": 3, "errors": 0,
             "submitted": 1240, "indexed": 1180},
            {"path": "https://example.com/sitemap-old.xml", "last_submitted": "2024-05-01T10:00:00Z",
             "last_downloaded": None, "is_pending": False, "is_sitemaps_index": False,
             "type": "sitemap", "warnings": 0, "errors": 4, "submitted": 300, "indexed": 12},
        ]},
    }
    extra = {
        "image": {
            "search_type": "image",
            "supports_query_dimension": True,
            "totals": {
                "current": {"rows": totals_row(1800, 96000, 22.4),
                            "meta": meta([], CURRENT[0], CURRENT[1], 1, search_type="image")},
                "previous": {"rows": totals_row(1500, 88000, 23.1),
                             "meta": meta([], PREVIOUS[0], PREVIOUS[1], 1, search_type="image")},
            },
            "daily": {"current": {
                "rows": daily(CURRENT[0], 30, 60, 3200, 22.4, seed=17),
                "meta": meta(["date"], CURRENT[0], CURRENT[1], 30, search_type="image"),
            }},
        }
    }
    return envelope("sc-domain:example.com", datasets, property_type="domain",
                    settings={"extra_search_types": ["image"]}, extra=extra)


FIXTURES = {
    "healthy": (fx_healthy, "Growth across the board, every dataset present"),
    "ctr-decline": (fx_ctr_decline, "Rankings and impressions held; CTR and clicks fell"),
    "visibility-loss": (fx_visibility_loss, "Pages lost impressions; one is no longer indexed"),
    "zero-previous": (fx_zero_previous, "Newly verified property, empty comparison period"),
    "low-traffic": (fx_low_traffic, "Small local property where percentages mislead"),
    "truncated": (fx_truncated, "Large property whose query extract hit the row cap"),
    "partial": (fx_partial, "Search appearance and countries failed to retrieve"),
    "domain-property": (fx_domain_property, "Domain property with Image search as a separate set"),
}


def main():
    ap = argparse.ArgumentParser(description="Generate offline Search Console fixtures.")
    ap.add_argument("--list", action="store_true", help="List the fixtures and exit")
    ap.add_argument("--only", help="Generate one fixture by name")
    args = ap.parse_args()

    if args.list:
        for name, (_, description) in sorted(FIXTURES.items()):
            print("%-18s %s" % (name, description))
        return 0

    OUT.mkdir(parents=True, exist_ok=True)
    names = [args.only] if args.only else sorted(FIXTURES)
    for name in names:
        if name not in FIXTURES:
            print("No such fixture: %s" % name)
            return 2
        builder, _ = FIXTURES[name]
        path = OUT / ("%s_raw.json" % name)
        path.write_text(json.dumps(builder(), indent=2))
        print("wrote %s" % path)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
