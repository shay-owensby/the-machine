#!/usr/bin/env python3
"""
Retrieve everything the report needs from the Search Console API and write it to
one raw file. This script talks to the API; nothing after it does.

    python3 fetch_search_console.py --project-root . --out <dir>

What it does, in order:

  1. Confirms the configured property exists and this identity can read it.
     It never falls back to a different property -- a report about the wrong
     site is worse than no report.
  2. Discovers the latest FINALISED date for the property. Search Console lags
     real time by two to three days and sometimes more; yesterday is not
     assumed to hold finished data, it is checked.
  3. Builds the two windows: the most recent N finalised days, and the N
     immediately before them. Equal lengths, no gap, no overlap.
  4. Pulls the datasets, paging each one to completion or to an explicit cap
     that is recorded when it bites.
  5. Writes one JSON file. Every dataset carries the request that produced it
     and whether the extract is believed complete.

Datasets, and why each one is a separate query:

  totals            no dimensions -- the property-level KPI truth. Summing a
                    dimensional export does NOT reproduce these numbers, which
                    is a fact about Search Console, not a bug here.
  daily             by date, both periods -- trend, spikes, drops
  queries           by query, both periods -- the search terms themselves
  pages             by page, both periods -- the landing pages
  query_page        by query+page, current only -- which page answers which
                    query, and where two pages compete for one
  devices           by device, both periods
  countries         by country, both periods
  search_appearance by searchAppearance ALONE -- this dimension cannot be
                    combined with any other, so it is its own query or it is
                    an HTTP 400
  sitemaps          optional diagnostic, submitted-sitemap health
  url_inspection    optional diagnostic, a handful of URLs chosen from the
                    page data above -- never the whole site

Exit codes
  0  complete
  1  partial -- optional datasets failed; the raw file records which and why
  2  configuration problem
  3  core data unavailable -- no property access, or no finalised data at all
  4  transient API failure worth retrying
"""

import argparse
import json
import sys
import time
from datetime import date, datetime, timedelta
from pathlib import Path

import gsc_common as gsc


# Optional datasets: a failure here degrades the report, it does not stop it.
OPTIONAL = ("query_page", "devices", "countries", "search_appearance",
            "sitemaps", "url_inspection", "extra_search_types")

# Core datasets: without these there is no report.
CORE = ("totals", "daily", "queries", "pages")


def log(msg):
    print(msg, file=sys.stderr)


def on_retry(attempt, delay, err):
    log("  retry %d in %.1fs (%s)" % (attempt, delay, err.message[:120]))


class Run(object):
    """Collects datasets, errors and warnings for one retrieval."""

    def __init__(self, cfg, skip=()):
        self.cfg = cfg
        self.skip = set(skip)
        self.datasets = {}
        self.errors = []
        self.warnings = []
        self.api_calls = 0

    def skipped(self, name):
        return name in self.skip

    def note_error(self, dataset, exc, fatal=False):
        entry = {"dataset": dataset, "fatal": fatal}
        entry.update(exc.as_dict() if isinstance(exc, gsc.ApiError) else {"message": str(exc)})
        self.errors.append(entry)
        log("  %s: %s" % (dataset, entry.get("message")))

    def query(self, dataset, **kw):
        self.api_calls += 1
        rows, meta = gsc.search_analytics(self.cfg, on_retry=on_retry, **kw)
        if meta["truncated"]:
            self.warnings.append(
                "%s: the extract hit the %d-row cap and was stopped. This dataset is a "
                "partial view of the period; totals derived from it are lower bounds."
                % (dataset, meta["rows_returned"])
            )
        return rows, meta


# ---------------------------------------------------------------------------
# Chunked retrieval for large properties
# ---------------------------------------------------------------------------

def chunked_query(run, dataset, start, end, chunk_days, **kw):
    """Retrieve a dimensional dataset in smaller date ranges and aggregate.

    Search Console returns at most 25,000 rows for one request and, on a large
    property, a 30-day window genuinely has more distinct queries than that. Ten
    three-day slices surface far more of the long tail than one thirty-day pull.

    The aggregation is honest about what it is: clicks and impressions sum,
    position is re-weighted by impressions, CTR is recomputed from the summed
    counts. The result is NOT identical to what a single un-capped 30-day query
    would return -- it can contain queries the single query never showed -- and
    the meta records that so the report can say it.
    """
    s = gsc.parse_date(start)
    e = gsc.parse_date(end)
    acc = {}
    metas = []
    cursor = s
    while cursor <= e:
        stop = min(cursor + timedelta(days=chunk_days - 1), e)
        rows, meta = run.query(
            "%s[%s..%s]" % (dataset, cursor, stop),
            start_date=cursor, end_date=stop, **kw
        )
        metas.append(meta)
        dims = meta["dimensions"]
        for r in rows:
            key = tuple(r.get(d) for d in dims)
            node = acc.setdefault(key, {d: r.get(d) for d in dims})
            node["clicks"] = gsc.add(node.get("clicks"), r.get("clicks"))
            node["impressions"] = gsc.add(node.get("impressions"), r.get("impressions"))
            if r.get("position") is not None and r.get("impressions"):
                node["_pos_num"] = (node.get("_pos_num") or 0.0) + r["position"] * r["impressions"]
                node["_pos_den"] = (node.get("_pos_den") or 0.0) + r["impressions"]
        cursor = stop + timedelta(days=1)

    out = []
    for node in acc.values():
        den = node.pop("_pos_den", None)
        num = node.pop("_pos_num", None)
        node["position"] = (num / den) if den else None
        node["ctr"] = gsc.safe_div(node.get("clicks"), node.get("impressions"))
        out.append(node)
    out.sort(key=lambda r: (r.get("clicks") or 0, r.get("impressions") or 0), reverse=True)

    meta = dict(metas[0]) if metas else {}
    meta.update({
        "start_date": str(s),
        "end_date": str(e),
        "rows_returned": len(out),
        "pages_fetched": sum(m.get("pages_fetched", 0) for m in metas),
        "chunked": True,
        "chunk_days": chunk_days,
        "chunks": len(metas),
        "truncated": any(m.get("truncated") for m in metas),
        "complete": not any(m.get("truncated") for m in metas),
        "note": (
            "Retrieved in %d date slices and aggregated. Clicks and impressions are sums; "
            "position is impression-weighted; CTR is recomputed from the sums. This surfaces "
            "more of the long tail than a single window and will not tie exactly to a "
            "single-request extract." % len(metas)
        ),
    })
    return out, meta


# ---------------------------------------------------------------------------
# Property validation
# ---------------------------------------------------------------------------

def validate_property(cfg):
    """Prove the property exists and is readable, before spending any quota.

    Returns (property_info, sites_list_or_None). Raises ApiError on failure --
    with, where the API allowed it, the list of properties this identity CAN
    reach, because "which one did you mean" is the actual next question.
    """
    try:
        info = gsc.get_site(cfg, on_retry=on_retry)
    except gsc.ApiError as exc:
        sites = None
        try:
            sites = gsc.list_sites(cfg, on_retry=on_retry)
        except gsc.ApiError:
            pass
        if sites is not None:
            reachable = ", ".join(s["site_url"] for s in sites[:25]) or "(none)"
            near = [s["site_url"] for s in sites
                    if gsc.site_display(s["site_url"]) and cfg.site_url
                    and gsc.site_display(s["site_url"]).replace("www.", "")
                    == (gsc.site_display(cfg.site_url) or "").replace("www.", "")]
            extra = ""
            if near:
                extra = ("\n  The same domain IS reachable as: %s -- that is a different "
                         "property with different data. Use the exact string."
                         % ", ".join(near))
            exc.detail = (exc.detail or "") + (
                "\n  Properties this identity can read: %s%s" % (reachable, extra)
            )
        raise exc
    return info


# ---------------------------------------------------------------------------
# Retrieval
# ---------------------------------------------------------------------------

def retrieve(cfg, periods, run, args):
    cur = periods["current"]
    prev = periods["previous"]
    st = cfg.search_type

    def both(dataset, dimensions, max_rows=None, chunk=False, aggregation_type=None):
        """Run one dimensional query over both periods."""
        out = {}
        for label, window in (("current", cur), ("previous", prev)):
            if chunk and args.chunk_days:
                rows, meta = chunked_query(
                    run, "%s.%s" % (dataset, label), window["start"], window["end"],
                    args.chunk_days, dimensions=dimensions, search_type=st,
                    data_state=args.data_state, max_rows=max_rows,
                    aggregation_type=aggregation_type,
                )
            else:
                rows, meta = run.query(
                    "%s.%s" % (dataset, label),
                    start_date=window["start"], end_date=window["end"],
                    dimensions=dimensions, search_type=st, data_state=args.data_state,
                    max_rows=max_rows, aggregation_type=aggregation_type,
                )
            out[label] = {"rows": rows, "meta": meta}
        return out

    # -- core ---------------------------------------------------------------

    log("totals (property level, no dimensions)")
    run.datasets["totals"] = both("totals", [])

    log("daily")
    run.datasets["daily"] = both("daily", ["date"])

    log("queries")
    run.datasets["queries"] = both(
        "queries", ["query"], max_rows=args.max_rows, chunk=True
    )

    log("pages")
    run.datasets["pages"] = both(
        "pages", ["page"], max_rows=args.max_rows, chunk=True
    )

    # -- optional -----------------------------------------------------------

    if not run.skipped("query_page"):
        log("query+page (current period only)")
        try:
            rows, meta = run.query(
                "query_page.current",
                start_date=cur["start"], end_date=cur["end"],
                dimensions=["query", "page"], search_type=st,
                data_state=args.data_state, max_rows=args.max_query_page_rows,
            )
            run.datasets["query_page"] = {"current": {"rows": rows, "meta": meta}}
        except gsc.ApiError as exc:
            run.note_error("query_page", exc)

    if not run.skipped("devices"):
        log("devices")
        try:
            run.datasets["devices"] = both("devices", ["device"])
        except gsc.ApiError as exc:
            run.note_error("devices", exc)

    if not run.skipped("countries"):
        log("countries")
        try:
            run.datasets["countries"] = both("countries", ["country"])
        except gsc.ApiError as exc:
            run.note_error("countries", exc)

    if not run.skipped("search_appearance"):
        log("search appearance (own query -- this dimension cannot be combined)")
        try:
            run.datasets["search_appearance"] = both("search_appearance", ["searchAppearance"])
        except gsc.ApiError as exc:
            run.note_error("search_appearance", exc)
            run.warnings.append(
                "Search appearance data is unavailable for this property. Many properties "
                "return none; this is not an error in the site."
            )


def retrieve_extra_search_types(cfg, periods, run, args):
    """Other Search Console surfaces, kept in their own box.

    Image, Video, News, Discover and Google News are separate datasets with
    separate behaviour -- Discover and Google News have no query dimension and
    no meaningful position at all. They are NEVER added into the web-search KPI
    totals; a combined number describes nothing that exists.
    """
    out = {}
    cur, prev = periods["current"], periods["previous"]
    for st in cfg.extra_search_types:
        log("extra search type: %s" % st)
        entry = {"search_type": st, "supports_query_dimension": st not in gsc.NO_QUERY_DIMENSION}
        try:
            for label, window in (("current", cur), ("previous", prev)):
                rows, meta = run.query(
                    "extra.%s.totals.%s" % (st, label),
                    start_date=window["start"], end_date=window["end"],
                    dimensions=[], search_type=st, data_state=args.data_state,
                )
                entry.setdefault("totals", {})[label] = {"rows": rows, "meta": meta}
            rows, meta = run.query(
                "extra.%s.daily.current" % st,
                start_date=cur["start"], end_date=cur["end"],
                dimensions=["date"], search_type=st, data_state=args.data_state,
            )
            entry["daily"] = {"current": {"rows": rows, "meta": meta}}
            out[st] = entry
        except gsc.ApiError as exc:
            run.note_error("extra_search_types.%s" % st, exc)
    return out


def pick_inspection_targets(run, limit):
    """Choose the few URLs worth a URL Inspection call.

    URL Inspection is a point-in-time index check with a real daily quota, not a
    crawler. It earns its call on pages where the performance data has already
    raised a question: a page that lost most of its impressions, or one holding
    impressions with no clicks at all. Everything else is answered better and
    more cheaply by the Search Analytics data already in hand.
    """
    pages = run.datasets.get("pages") or {}
    cur = {r["page"]: r for r in (pages.get("current", {}).get("rows") or []) if r.get("page")}
    prev = {r["page"]: r for r in (pages.get("previous", {}).get("rows") or []) if r.get("page")}

    scored = []
    for url, before in prev.items():
        prev_imp = before.get("impressions") or 0
        if prev_imp < 100:
            continue
        now = cur.get(url)
        now_imp = (now or {}).get("impressions") or 0
        lost = prev_imp - now_imp
        if now_imp == 0 and prev_imp >= 100:
            scored.append((lost * 2, url, "no impressions at all this period, %d previously"
                           % prev_imp))
        elif prev_imp and lost / prev_imp >= 0.6 and lost >= 200:
            scored.append((lost, url, "impressions down %.0f%% (%d -> %d)"
                           % (lost / prev_imp * 100, prev_imp, now_imp)))
    scored.sort(reverse=True, key=lambda t: t[0])
    return [(url, why) for _, url, why in scored[:limit]]


def main():
    ap = argparse.ArgumentParser(description="Retrieve Google Search Console data for a report.")
    ap.add_argument("--project-root", default=".", help="Client project root holding .env")
    ap.add_argument("--agency-env", help="Override the shared agency credential file path")
    ap.add_argument("--site-url", help="Search Console property (overrides GSC_SITE_URL)")
    ap.add_argument("--out", default="analytics-insights/google-search-console",
                    help="Output directory (a dated subdirectory is created inside it)")
    ap.add_argument("--days", type=int, help="Period length in days for both windows (default 30)")
    ap.add_argument("--end-date", help="Last day of the current period (default: latest finalised)")
    ap.add_argument("--current", help="Explicit current window START:END")
    ap.add_argument("--previous", help="Explicit comparison window START:END")
    ap.add_argument("--search-type", help="web|image|video|news|discover|googleNews (default web)")
    ap.add_argument("--data-state", default="final", choices=("final", "all"),
                    help="final = finalised data only (default). all = includes fresh, "
                         "provisional days -- never the default for a client report.")
    ap.add_argument("--skip", default="", help="Comma-separated optional datasets to skip")
    ap.add_argument("--max-rows", type=int, default=50000,
                    help="Cap for query/page extracts across pages (default 50000)")
    ap.add_argument("--max-query-page-rows", type=int, default=25000,
                    help="Cap for the query+page extract (default 25000)")
    ap.add_argument("--chunk-days", type=int, default=0,
                    help="Retrieve query/page datasets in N-day slices and aggregate. "
                         "Use on large properties where a single window hits the row cap.")
    ap.add_argument("--sitemaps", action="store_true", help="Also retrieve sitemap status")
    ap.add_argument("--inspect-urls", action="store_true",
                    help="Run URL Inspection on the worst-declining pages (quota-aware)")
    ap.add_argument("--no-freshness-probe", action="store_true",
                    help="Skip latest-finalised-date discovery (requires --end-date)")
    ap.add_argument("--flat", action="store_true",
                    help="Write straight into --out instead of <out>/<YYYY-MM-DD>/data/")
    args = ap.parse_args()

    started = time.time()

    cfg = gsc.resolve_config(
        project_root=args.project_root, agency_env=args.agency_env,
        site_url=args.site_url, search_type=args.search_type,
    )
    if cfg.problems:
        for p in cfg.problems:
            log("problem: %s" % p)
        return 2
    for w in cfg.warnings:
        log("warning: %s" % w)

    if args.days:
        cfg.report_days = args.days

    run = Run(cfg, skip=[s.strip() for s in args.skip.split(",") if s.strip()])
    if not args.sitemaps:
        run.skip.add("sitemaps")
    if not (args.inspect_urls or cfg.inspect_urls):
        run.skip.add("url_inspection")

    # -- 1. property validation ---------------------------------------------
    log("validating property %s" % cfg.site_url)
    try:
        prop = validate_property(cfg)
    except gsc.ApiError as exc:
        log("property check failed: %s" % exc.message)
        if exc.detail:
            log(exc.detail)
        return 4 if exc.retryable else 3
    except gsc.ConfigError as exc:
        log("problem: %s" % exc)
        return 2

    log("  %s (%s property, permission: %s)"
        % (prop["site_url"], prop["property_type"], prop["permission_level"]))
    if prop.get("permission_level") == "siteUnverifiedUser":
        run.warnings.append(
            "This identity is listed on the property as an UNVERIFIED user, which grants no "
            "data access. Someone with Owner rights must add it as a Full or Restricted user."
        )

    # -- 2. freshness --------------------------------------------------------
    freshness = None
    if args.no_freshness_probe:
        if not (args.end_date or args.current):
            log("problem: --no-freshness-probe needs --end-date or --current.")
            return 2
    else:
        log("discovering the latest finalised date")
        try:
            freshness = gsc.latest_final_date(cfg, on_retry=on_retry)
        except gsc.ApiError as exc:
            log("freshness probe failed: %s" % exc.message)
            return 4 if exc.retryable else 3
        if not freshness["latest_final"]:
            log("problem: the property returned no finalised data in the last %d days."
                % freshness["lookback_days"])
            log("  Either the property is brand new, has no search traffic, or the identity "
                "has access to a property that is not the live site.")
            return 3
        log("  latest finalised: %s (%d days behind today); %d fresher provisional day(s) exist"
            % (freshness["latest_final"], freshness["lag_days"] or 0,
               freshness["fresh_days_available"]))

    # -- 3. periods ----------------------------------------------------------
    if args.current:
        cs, ce = args.current.split(":")
        if args.previous:
            ps, pe = args.previous.split(":")
        else:
            span = (gsc.parse_date(ce) - gsc.parse_date(cs)).days + 1
            pe = gsc.parse_date(cs) - timedelta(days=1)
            ps = pe - timedelta(days=span - 1)
            ps, pe = str(ps), str(pe)
        cur_days = (gsc.parse_date(ce) - gsc.parse_date(cs)).days + 1
        prev_days = (gsc.parse_date(pe) - gsc.parse_date(ps)).days + 1
        periods = {
            "current": {"start": cs, "end": ce, "days": cur_days},
            "previous": {"start": ps, "end": pe, "days": prev_days},
            "lag_days": 0,
            "comparable": cur_days == prev_days,
        }
        periods["basis"] = "explicit date ranges supplied on the command line"
        if not periods["comparable"]:
            run.warnings.append(
                "The two windows are different lengths (%d vs %d days). Totals are not "
                "comparable and percentage changes between them are misleading."
                % (cur_days, prev_days)
            )
    else:
        end = args.end_date or freshness["latest_final"]
        periods = gsc.build_periods(end, days=cfg.report_days, lag_days=cfg.lag_days)
        periods["basis"] = (
            "the most recent %d finalised days for this property (latest finalised date %s%s), "
            "against the %d days immediately before them"
            % (cfg.report_days, end,
               ", held back %d days" % cfg.lag_days if cfg.lag_days else "",
               cfg.report_days)
        )

    if freshness and periods["current"]["end"] > (freshness["latest_final"] or ""):
        run.warnings.append(
            "The current period ends %s but the latest finalised date is %s. The final days "
            "of the window are provisional and will be revised upward by Google."
            % (periods["current"]["end"], freshness["latest_final"])
        )
    if args.data_state == "all":
        run.warnings.append(
            "Retrieved with dataState=all, which includes fresh, unfinalised days. Those days "
            "are incomplete and will rise. This is not the default and must be stated in the "
            "report."
        )

    log("current  %s .. %s" % (periods["current"]["start"], periods["current"]["end"]))
    log("previous %s .. %s" % (periods["previous"]["start"], periods["previous"]["end"]))

    # 16-month window: Search Console keeps roughly 16 months of Search Analytics
    # data, so a comparison period older than that comes back empty rather than
    # wrong -- but empty for that reason is worth saying out loud.
    horizon = date.today() - timedelta(days=480)
    if gsc.parse_date(periods["previous"]["start"]) < horizon:
        run.warnings.append(
            "The comparison period starts %s, close to or beyond Search Console's ~16-month "
            "retention. Missing rows there are a retention limit, not a traffic collapse."
            % periods["previous"]["start"]
        )

    # -- 4. datasets ---------------------------------------------------------
    try:
        retrieve(cfg, periods, run, args)
    except gsc.ApiError as exc:
        run.note_error("core", exc, fatal=True)
        write_raw(cfg, prop, freshness, periods, run, args, started, partial=True)
        return 4 if exc.retryable else 3

    extra = {}
    if cfg.extra_search_types and not run.skipped("extra_search_types"):
        extra = retrieve_extra_search_types(cfg, periods, run, args)

    if not run.skipped("sitemaps"):
        log("sitemaps")
        try:
            run.api_calls += 1
            run.datasets["sitemaps"] = {"entries": gsc.list_sitemaps(cfg, on_retry=on_retry)}
        except gsc.ApiError as exc:
            run.note_error("sitemaps", exc)

    if not run.skipped("url_inspection"):
        targets = pick_inspection_targets(run, cfg.max_url_inspections)
        if not targets:
            log("url inspection: no page met the decline threshold; nothing inspected")
            run.datasets["url_inspection"] = {
                "results": [],
                "note": "No page declined sharply enough to justify an inspection call.",
            }
        else:
            log("url inspection: %d page(s)" % len(targets))
            results = []
            for url, why in targets:
                try:
                    run.api_calls += 1
                    result = gsc.inspect_url(cfg, url, on_retry=on_retry)
                    result["selected_because"] = why
                    results.append(result)
                except gsc.ApiError as exc:
                    run.note_error("url_inspection", exc)
                    if exc.status == 429 or (exc.reason or "").lower().startswith("quota"):
                        run.warnings.append(
                            "URL Inspection quota was exhausted after %d of %d URLs. The "
                            "inspected set is partial." % (len(results), len(targets))
                        )
                        break
            run.datasets["url_inspection"] = {
                "results": results,
                "note": (
                    "URL Inspection reports index status at the moment of the call. It is not "
                    "a history and does not explain the 30-day performance trend on its own."
                ),
            }

    path = write_raw(cfg, prop, freshness, periods, run, args, started, extra=extra)
    log("")
    log("wrote %s" % path)
    log("%d API call(s), %.1fs" % (run.api_calls, time.time() - started))

    missing_core = [d for d in CORE if d not in run.datasets]
    if missing_core:
        log("core datasets missing: %s" % ", ".join(missing_core))
        return 3
    if run.errors:
        log("%d optional dataset(s) failed -- recorded in the raw file as unavailable, "
            "not as empty." % len(run.errors))
        return 1
    return 0


def write_raw(cfg, prop, freshness, periods, run, args, started, extra=None, partial=False):
    out_dir = Path(args.out).expanduser()
    stem = "%s_%s_%s" % (
        slug(cfg.site_url), periods["current"]["start"], periods["current"]["end"]
    )
    data_dir = out_dir if args.flat else out_dir / periods["current"]["end"] / "data"
    data_dir.mkdir(parents=True, exist_ok=True)
    path = data_dir / ("%s_raw.json" % stem)

    envelope = {
        "schema": "reports-google-search-console/raw@1",
        "generated_at": datetime.now().astimezone().isoformat(timespec="seconds"),
        "retrieval_seconds": round(time.time() - started, 1),
        "api_calls": run.api_calls,
        "partial": partial,
        "property": {
            "site_url": prop["site_url"],
            "property_type": prop["property_type"],
            "permission_level": prop.get("permission_level"),
            "display": gsc.site_display(prop["site_url"]),
            "access": "ok",
        },
        "client": {"name": cfg.client_name},
        "freshness": freshness,
        "periods": periods,
        "search_type": cfg.search_type,
        "data_state": args.data_state,
        "settings": {
            "report_days": cfg.report_days,
            "lag_days": cfg.lag_days,
            "row_limit": cfg.row_limit,
            "max_rows": args.max_rows,
            "chunk_days": args.chunk_days,
            "brand_terms": cfg.brand_terms,
            "brand_terms_configured": bool(cfg.brand_terms),
            "primary_country": cfg.primary_country,
            "extra_search_types": cfg.extra_search_types,
            "skipped": sorted(run.skip),
        },
        "datasets": run.datasets,
        "extra_search_types": extra or {},
        "errors": run.errors,
        "warnings": run.warnings,
    }
    path.write_text(json.dumps(envelope, indent=2))
    return path


def slug(site_url):
    """A filename-safe stem for a property identifier.

    Dots become dashes so the stem cannot be mistaken for a file extension by a
    tool that splits on the last one, and so `www.example.com` and
    `sc-domain:example.com` produce visibly different names.
    """
    s = (site_url or "unknown").replace("sc-domain:", "domain-")
    s = s.replace("https://", "").replace("http://", "").rstrip("/")
    return "".join(c if c.isalnum() or c == "-" else "-" for c in s)


if __name__ == "__main__":
    try:
        sys.exit(main())
    except gsc.ConfigError as exc:
        log("problem: %s" % exc)
        sys.exit(2)
    except KeyboardInterrupt:
        log("interrupted")
        sys.exit(4)
