#!/usr/bin/env python3
"""
Retrieve one reporting run's worth of GA4 data and write it to a single raw
JSON file. Retrieval only -- no analysis, no interpretation, no rounding.

    python3 fetch_ga4.py --project-root . --out reports/google-analytics/<end>/data

Default periods: the most recent 30 completed days in the PROPERTY's time zone,
against the 30 days immediately before them. Yesterday is the last day
included; today is never included, because a partial day would compare against
a whole one.

Three things this script does that a naive GA4 client does not:

  1. **It asks the property what it can report before asking for numbers.**
     properties/{id}/metadata lists every dimension and metric this property
     actually supports, custom definitions included. Requests are filtered
     against that list, so a property without a given field produces an honest
     "not supported by this property" note instead of a 400 that kills the run.

  2. **It handles key events under both names.** `keyEvents` /
     `sessionKeyEventRate` / `userKeyEventRate` replaced `conversions` /
     `sessionConversionRate` / `userConversionRate`. Which pair a property
     answers to is discovered, not assumed, and recorded in the output.

  3. **It chunks requests to stay inside the API's shape limits** (9 metrics
     per request here), sorting every chunk by the same metric so the chunks
     describe the same rows, then merges them by dimension key.

What it does NOT do: fill gaps. A metric the API did not return is absent here
and stays absent downstream. A day with no rows is a day with no rows, not a
zero. A query that fails is recorded in `errors` with the reason and the
dataset it fed is marked unavailable. Nothing is defaulted to zero, ever.

Exit codes
  0  complete -- every requested dataset came back
  1  partial   -- core data retrieved, some optional datasets failed (see errors[])
  2  configuration problem
  3  authentication/property-access failure, or core data unavailable
  4  transient API failure -- retry
"""

import argparse
import datetime as dt
import json
import sys
from pathlib import Path

import ga4_common as ga

SCHEMA = "reports-google-analytics/raw@1"

# ---------------------------------------------------------------------------
# Field catalogues
#
# These are CANDIDATES. Every name is checked against the property's own
# metadata before it is requested, so a name that a given property (or a future
# API revision) does not carry is dropped with a reason rather than failing the
# run. Keep them here, in one place: the analysis, the charts and the reference
# docs all describe what is in this file, and a metric added in two places
# drifts in one.
# ---------------------------------------------------------------------------

# Audience, engagement and content KPIs every property should be able to report.
CORE_METRICS = [
    "activeUsers",
    "totalUsers",
    "newUsers",
    "sessions",
    "engagedSessions",
    "engagementRate",
    "bounceRate",
    "averageSessionDuration",
    "userEngagementDuration",
    "screenPageViews",
    "screenPageViewsPerSession",
    "sessionsPerUser",
    "eventCount",
]

# Key-event metrics under the current names, with the pre-2024 names as the
# fallback pair. Exactly one pair is used per run; which one is recorded.
KEY_EVENT_METRICS = ["keyEvents", "sessionKeyEventRate", "userKeyEventRate"]
LEGACY_KEY_EVENT_METRICS = ["conversions", "sessionConversionRate", "userConversionRate"]

# Ecommerce. Present in every property's metadata whether or not the site sells
# anything, so availability here proves nothing -- only returned VALUES do.
ECOMMERCE_METRICS = [
    "totalRevenue",
    "purchaseRevenue",
    "transactions",
    "ecommercePurchases",
    "totalPurchasers",
    "firstTimePurchasers",
    "purchaserRate",
    "averagePurchaseRevenue",
    "averageRevenuePerUser",
    "itemsViewed",
    "itemsAddedToCart",
    "itemsCheckedOut",
    "itemsPurchased",
    "addToCarts",
    "checkouts",
    "cartToViewRate",
    "purchaseToViewRate",
]

# The metrics that decide whether this property does ecommerce at all.
ECOMMERCE_SIGNALS = ["transactions", "ecommercePurchases", "purchaseRevenue", "totalRevenue"]

# Per-row metric set for a dimension breakdown. Deliberately smaller than the
# KPI set: a breakdown is read across rows, and twenty columns is not read.
SEGMENT_METRICS = [
    "sessions",
    "totalUsers",
    "newUsers",
    "engagedSessions",
    "engagementRate",
    "averageSessionDuration",
    "screenPageViews",
]
SEGMENT_ECOMMERCE_METRICS = ["totalRevenue", "transactions"]

DAILY_METRICS = [
    "sessions",
    "activeUsers",
    "totalUsers",
    "newUsers",
    "engagedSessions",
    "screenPageViews",
    "eventCount",
]
DAILY_ECOMMERCE_METRICS = ["totalRevenue", "transactions"]

EVENT_METRICS = ["eventCount", "totalUsers", "eventValue"]

ITEM_METRICS = ["itemsViewed", "itemsAddedToCart", "itemsPurchased", "itemRevenue"]

# Dimension candidates, first supported one wins. GA4 has renamed several of
# these; a property answers to whichever its API revision carries.
DIMENSION_CANDIDATES = {
    "landing_page": ["landingPagePlusQueryString", "landingPage"],
    "session_channel": ["sessionDefaultChannelGroup", "sessionDefaultChannelGrouping"],
    "first_user_channel": ["firstUserDefaultChannelGroup", "firstUserDefaultChannelGrouping"],
    "session_source_medium": ["sessionSourceMedium"],
    "session_campaign": ["sessionCampaignName", "sessionCampaignId"],
    "first_user_source_medium": ["firstUserSourceMedium"],
    "page_path": ["pagePath"],
    "page_title": ["pageTitle"],
    "hostname": ["hostName"],
    "device": ["deviceCategory"],
    "browser": ["browser"],
    "os": ["operatingSystem"],
    "platform": ["platform"],
    "country": ["country"],
    "region": ["region"],
    "city": ["city"],
    "event_name": ["eventName"],
    "item_name": ["itemName"],
    "date": ["date"],
}


# ---------------------------------------------------------------------------
# Dates
# ---------------------------------------------------------------------------

def today_in_zone(tz_name, warnings):
    """Today's date in the PROPERTY's time zone.

    GA4 days are property-time-zone days. Computing 'yesterday' in the
    machine's local zone can silently include or drop a day of traffic, which
    is a wrong number in a client report, not a rounding detail.
    """
    if tz_name:
        try:
            from zoneinfo import ZoneInfo
            return dt.datetime.now(ZoneInfo(tz_name)).date(), tz_name
        except Exception as exc:
            warnings.append(
                "Could not use the property time zone %r (%s). Falling back to this "
                "machine's local date, which may shift the window by a day."
                % (tz_name, exc.__class__.__name__))
    else:
        warnings.append(
            "The property did not report a time zone. Using this machine's local date, "
            "which may shift the window by a day.")
    return dt.date.today(), "local"


def parse_range(text, label):
    try:
        start, end = text.split(":", 1)
        s = dt.date.fromisoformat(start.strip())
        e = dt.date.fromisoformat(end.strip())
    except ValueError:
        raise SystemExit("%s must look like YYYY-MM-DD:YYYY-MM-DD (got %r)" % (label, text))
    if e < s:
        raise SystemExit("%s ends before it starts (%s to %s)" % (label, s, e))
    return s, e


def build_periods(args, tz_name, days, lag_days, warnings):
    """Work out the two windows and say plainly how they were chosen."""
    if args.current or args.previous:
        if not (args.current and args.previous):
            raise SystemExit("--current and --previous must be given together.")
        c_start, c_end = parse_range(args.current, "--current")
        p_start, p_end = parse_range(args.previous, "--previous")
        basis = "explicit --current/--previous"
        zone_used = tz_name or "unknown"
    else:
        today, zone_used = today_in_zone(tz_name, warnings)
        if args.end_date:
            c_end = dt.date.fromisoformat(args.end_date)
            basis = "explicit --end-date"
        else:
            c_end = today - dt.timedelta(days=1 + lag_days)
            basis = ("most recent %d completed days ending yesterday in %s" % (days, zone_used))
            if lag_days:
                basis += " minus a %d-day data-settling buffer" % lag_days
        c_start = c_end - dt.timedelta(days=days - 1)
        p_end = c_start - dt.timedelta(days=1)
        p_start = p_end - dt.timedelta(days=days - 1)

    c_days = (c_end - c_start).days + 1
    p_days = (p_end - p_start).days + 1
    if c_days != p_days:
        warnings.append(
            "The two periods are different lengths (%d days vs %d days). Totals are not "
            "comparable and percentage changes will mislead. Every table built on this must "
            "say so." % (c_days, p_days))
    if p_end >= c_start:
        warnings.append(
            "The comparison period overlaps the current period (%s..%s vs %s..%s). The same "
            "days are counted twice." % (p_start, p_end, c_start, c_end))
    if c_end >= dt.date.today():
        warnings.append(
            "The current period ends today or later (%s). Today is a partial day in GA4 and "
            "will under-report against a full day in the comparison period." % c_end)

    return {
        "current": {"start": c_start.isoformat(), "end": c_end.isoformat(), "days": c_days},
        "previous": {"start": p_start.isoformat(), "end": p_end.isoformat(), "days": p_days},
        "basis": basis,
        "time_zone": tz_name,
        "time_zone_used": zone_used,
    }


# ---------------------------------------------------------------------------
# Property schema
# ---------------------------------------------------------------------------

class Schema(object):
    """What this property can actually report, straight from its metadata."""

    def __init__(self, metadata):
        self.dimensions = {}
        self.metrics = {}
        self.custom_dimensions = []
        self.custom_metrics = []
        for d in (metadata or {}).get("dimensions", []) or []:
            name = d.get("apiName")
            if not name:
                continue
            self.dimensions[name] = d
            if d.get("customDefinition"):
                self.custom_dimensions.append({"api_name": name, "ui_name": d.get("uiName"),
                                               "scope": d.get("category")})
        for m in (metadata or {}).get("metrics", []) or []:
            name = m.get("apiName")
            if not name:
                continue
            self.metrics[name] = m
            if m.get("customDefinition"):
                self.custom_metrics.append({"api_name": name, "ui_name": m.get("uiName"),
                                            "type": m.get("type")})
        self.loaded = bool(self.dimensions or self.metrics)

    def has_metric(self, name):
        return (not self.loaded) or (name in self.metrics)

    def has_dimension(self, name):
        return (not self.loaded) or (name in self.dimensions)

    def filter_metrics(self, names):
        """-> (supported, [(name, reason), ...])"""
        keep, dropped = [], []
        for n in names:
            if self.has_metric(n):
                keep.append(n)
            else:
                dropped.append((n, "not in this property's metric schema"))
        return keep, dropped

    def first_dimension(self, candidates):
        for c in candidates:
            if self.has_dimension(c):
                return c
        return None


# ---------------------------------------------------------------------------
# Retrieval
# ---------------------------------------------------------------------------

def chunk_metrics(metrics, sort_metric):
    """Split a metric list into request-sized chunks.

    The sort metric rides in EVERY chunk. Without it the chunks come back
    ordered differently, and a top-50 from chunk 1 is then a different fifty
    rows from the top-50 in chunk 2 -- which merges into a table of numbers
    that never coexisted.
    """
    size = ga.MAX_METRICS_PER_REQUEST
    if sort_metric and sort_metric in metrics:
        rest = [m for m in metrics if m != sort_metric]
        if not rest:
            return [[sort_metric]]
        per = size - 1
        return [[sort_metric] + rest[i:i + per] for i in range(0, len(rest), per)]
    return [metrics[i:i + size] for i in range(0, len(metrics), size)] or [[]]


def merge_reports(parts, warnings, label):
    """Merge chunked reports of the same dimensions into one row set."""
    parts = [p for p in parts if p]
    if not parts:
        return None
    base = parts[0]
    index = {}
    order = []
    for r in base["rows"]:
        key = tuple(r["keys"])
        index[key] = dict(r["values"])
        order.append(key)
    metrics = list(base["metrics"])
    seen = {m["name"] for m in metrics}

    for part in parts[1:]:
        for m in part["metrics"]:
            if m["name"] not in seen:
                metrics.append(m)
                seen.add(m["name"])
        strays = 0
        for r in part["rows"]:
            key = tuple(r["keys"])
            if key not in index:
                index[key] = {}
                order.append(key)
                strays += 1
            index[key].update(r["values"])
        if strays:
            warnings.append(
                "%s: a follow-up metric request returned %d row(s) the first request did "
                "not. They are kept, with the first request's metrics absent rather than "
                "zero." % (label, strays))

    totals = {}
    for part in parts:
        if part.get("totals"):
            totals.update(part["totals"])

    meta = dict(base.get("meta") or {})
    for part in parts[1:]:
        if (part.get("meta") or {}).get("dataLossFromOtherRow"):
            meta["dataLossFromOtherRow"] = True
        if (part.get("meta") or {}).get("subjectToThresholding"):
            meta["subjectToThresholding"] = True

    return {
        "dimensions": base["dimensions"],
        "metrics": metrics,
        "rows": [{"keys": list(k), "values": index[k]} for k in order],
        "totals": totals or None,
        "row_count": base.get("row_count"),
        "meta": meta,
    }


class Runner(object):
    def __init__(self, cfg, verbose=True):
        self.cfg = cfg
        self.verbose = verbose
        self.errors = []
        self.warnings = []

    def note(self, msg):
        if self.verbose:
            print(msg, file=sys.stderr)

    def _on_retry(self, label):
        def cb(attempt, delay, err):
            self.note("  %s: transient failure (%s), retry %d in %.1fs"
                      % (label, err.error_code or err.status, attempt, delay))
        return cb

    def report(self, key, dimensions, metrics, start, end, sort_metric=None,
               limit=100, order_by_dimension=None, required=False, label=None):
        """One dataset for one period, chunked and merged. None on failure."""
        label = label or key
        if not metrics:
            self.errors.append({
                "dataset": key, "required": required,
                "message": "No supported metric remained after filtering against the "
                           "property schema.",
                "error_code": "schema.NO_METRICS", "http_status": None,
                "hint": None, "retryable": False})
            return None

        parts = []
        for chunk in chunk_metrics(metrics, sort_metric):
            body = {
                "dateRanges": [{"startDate": start, "endDate": end}],
                "dimensions": [{"name": d} for d in dimensions],
                "metrics": [{"name": m} for m in chunk],
                "limit": limit,
                "metricAggregations": ["TOTAL"],
            }
            if order_by_dimension:
                body["orderBys"] = [{"dimension": {"dimensionName": order_by_dimension},
                                     "desc": False}]
            elif sort_metric and sort_metric in chunk:
                body["orderBys"] = [{"metric": {"metricName": sort_metric}, "desc": True}]

            try:
                parsed = ga.run_report(self.cfg, body, on_retry=self._on_retry(label))
            except ga.ApiError as exc:
                recovered = self._retry_without_incompatible(
                    label, body, chunk, dimensions, exc)
                if recovered is None:
                    self.errors.append(dict(
                        {"dataset": key, "required": required}, **exc.as_dict()))
                    self.note("  %s: FAILED -- %s" % (label, exc.message))
                    return None
                parsed = recovered
            parts.append(ga.parse_report(parsed))

        merged = merge_reports(parts, self.warnings, label)
        self.note("  %s: %d row(s)" % (label, len(merged["rows"]) if merged else 0))
        return merged

    def _retry_without_incompatible(self, label, body, chunk, dimensions, exc):
        """A 400 on a dimension/metric pairing is answerable, not fatal.

        checkCompatibility says which metrics this dimension will accept; the
        request goes again with only those, and the dropped ones are recorded as
        unavailable for this breakdown -- which is true, and is not zero.
        """
        if exc.status != 400 or not dimensions:
            return None
        try:
            compat = ga.check_compatibility(self.cfg, dimensions, chunk)
        except ga.ApiError:
            return None
        allowed = {c.get("metricMetadata", {}).get("apiName")
                   for c in compat.get("metricCompatibilities", []) or []
                   if c.get("compatibility") == "COMPATIBLE"}
        keep = [m for m in chunk if m in allowed]
        dropped = [m for m in chunk if m not in allowed]
        if not keep or not dropped:
            return None
        self.warnings.append(
            "%s: GA4 will not report %s alongside %s, so %s left out of that breakdown. "
            "%s still in the KPI totals where the property supports %s."
            % (label, ", ".join(dropped), " + ".join(dimensions),
               "they were" if len(dropped) > 1 else "it was",
               "They are" if len(dropped) > 1 else "It is",
               "them" if len(dropped) > 1 else "it"))
        body = dict(body, metrics=[{"name": m} for m in keep])
        if body.get("orderBys"):
            ob = body["orderBys"][0]
            if ob.get("metric", {}).get("metricName") not in keep:
                body.pop("orderBys")
        try:
            return ga.run_report(self.cfg, body, on_retry=self._on_retry(label))
        except ga.ApiError:
            return None


# ---------------------------------------------------------------------------
# Main
# ---------------------------------------------------------------------------

def main():
    ap = argparse.ArgumentParser(description="Retrieve GA4 data for a period-over-period report.")
    ap.add_argument("--project-root", default=".", help="Client project root holding .env (default: cwd)")
    ap.add_argument("--out", help="Directory for the raw JSON file "
                                  "(default: reports/google-analytics/<period end>/data)")
    ap.add_argument("--agency-env", help="Override the shared agency credential file path")
    ap.add_argument("--property-id", help="GA4 property ID (overrides .env)")
    ap.add_argument("--days", type=int, help="Days per period (default 30, or GA4_REPORT_DAYS)")
    ap.add_argument("--end-date", help="Last day of the current period, YYYY-MM-DD")
    ap.add_argument("--current", help="Explicit current period YYYY-MM-DD:YYYY-MM-DD")
    ap.add_argument("--previous", help="Explicit comparison period YYYY-MM-DD:YYYY-MM-DD")
    ap.add_argument("--skip", default="", help="Comma-separated optional datasets to skip "
                                               "(source_medium,campaigns,first_user_channels,pages,"
                                               "hostname,browsers,os,geo,events,items)")
    ap.add_argument("--top-n", type=int, default=50, help="Row cap for channel-style breakdowns (default 50)")
    ap.add_argument("--page-limit", type=int, default=100, help="Row cap for page breakdowns (default 100)")
    ap.add_argument("--quiet", action="store_true")
    args = ap.parse_args()

    cfg = ga.resolve_config(project_root=args.project_root, agency_env=args.agency_env,
                            property_id=args.property_id)
    if cfg.problems:
        print(json.dumps({"status": "blocked", "problems": cfg.problems,
                          "config": ga.describe_config(cfg)}, indent=2))
        for p in cfg.problems:
            print("problem: %s" % p, file=sys.stderr)
        return 2

    runner = Runner(cfg, verbose=not args.quiet)
    runner.warnings.extend(cfg.warnings)
    skip = {s.strip() for s in args.skip.split(",") if s.strip()}
    days = args.days or cfg.report_days

    runner.note("GA4 retrieval -- property %s (%s auth)" % (cfg.property_id, cfg.auth_mode))

    # -- 1. What can this property report? ----------------------------------
    try:
        metadata = ga.get_metadata(cfg, on_retry=runner._on_retry("metadata"))
    except ga.ApiError as exc:
        payload = base_payload(cfg, None, None, None, runner)
        payload["errors"].append(dict({"dataset": "metadata", "required": True}, **exc.as_dict()))
        write_out(args, cfg, payload, None)
        print(json.dumps({"status": "blocked", "error": exc.as_dict()}, indent=2))
        print("problem: %s" % exc.message, file=sys.stderr)
        if exc.detail:
            print("hint: %s" % exc.detail, file=sys.stderr)
        return 4 if exc.retryable else 3

    schema = Schema(metadata)
    runner.note("  schema: %d dimensions, %d metrics (%d custom dimensions, %d custom metrics)"
                % (len(schema.dimensions), len(schema.metrics),
                   len(schema.custom_dimensions), len(schema.custom_metrics)))

    # Key events under whichever name this property answers to.
    if all(schema.has_metric(m) for m in KEY_EVENT_METRICS):
        key_event_metrics = list(KEY_EVENT_METRICS)
        key_event_naming = "keyEvents"
    elif all(schema.has_metric(m) for m in LEGACY_KEY_EVENT_METRICS):
        key_event_metrics = list(LEGACY_KEY_EVENT_METRICS)
        key_event_naming = "conversions (pre-2024 naming)"
        runner.warnings.append(
            "This property reports the older `conversions` metric rather than `keyEvents`. "
            "The numbers mean the same thing; the report should use the property's own "
            "wording.")
    else:
        key_event_metrics = []
        key_event_naming = None
        runner.warnings.append(
            "Neither `keyEvents` nor `conversions` is in this property's metric schema, so "
            "no conversion-shaped metric can be retrieved. Conversion sections must be "
            "omitted, not reported as zero.")

    # -- 2. Property metadata: Admin API where possible, Data API otherwise --
    prop = {"property_id": cfg.property_id, "name": cfg.property_name_hint,
            "admin_api_available": False}
    try:
        p = ga.admin_get(cfg, "properties/%s" % cfg.property_id, on_retry=runner._on_retry("admin.property"))
        prop.update({
            "admin_api_available": True,
            "name": p.get("displayName") or cfg.property_name_hint,
            "time_zone": p.get("timeZone"),
            "currency": p.get("currencyCode"),
            "industry": p.get("industryCategory"),
            "created": p.get("createTime"),
            "account": p.get("parent"),
            "property_type": p.get("propertyType"),
        })
    except ga.ApiError as exc:
        prop["admin_api_error"] = exc.message
        runner.warnings.append(
            "The Google Analytics Admin API did not answer (%s), so the property's name and "
            "key-event definitions could not be read. Reporting numbers are unaffected -- "
            "they come from the Data API. Do not invent a property name."
            % (exc.error_code or exc.status))

    key_event_definitions = None
    if prop["admin_api_available"]:
        try:
            ke = ga.admin_get(cfg, "properties/%s/keyEvents" % cfg.property_id,
                              on_retry=runner._on_retry("admin.keyEvents"))
            key_event_definitions = [{
                "event_name": k.get("eventName"),
                "counting_method": k.get("countingMethod"),
                "custom": k.get("custom"),
                "created": k.get("createTime"),
                "default_value": k.get("defaultValue"),
            } for k in (ke.get("keyEvents") or [])]
        except ga.ApiError as exc:
            prop["key_events_error"] = exc.message
        try:
            streams = ga.admin_get(cfg, "properties/%s/dataStreams" % cfg.property_id,
                                   on_retry=runner._on_retry("admin.dataStreams"))
            prop["data_streams"] = [{
                "name": s.get("displayName"),
                "type": s.get("type"),
                "uri": (s.get("webStreamData") or {}).get("defaultUri"),
                "measurement_id": (s.get("webStreamData") or {}).get("measurementId"),
            } for s in (streams.get("dataStreams") or [])]
        except ga.ApiError:
            pass

    # -- 3. Periods, in the property's time zone ----------------------------
    periods = build_periods(args, prop.get("time_zone"), days, cfg.lag_days, runner.warnings)
    cur, prev = periods["current"], periods["previous"]
    runner.note("  current  %s .. %s (%d days)" % (cur["start"], cur["end"], cur["days"]))
    runner.note("  previous %s .. %s (%d days)" % (prev["start"], prev["end"], prev["days"]))

    # -- 4. KPI totals, both periods ----------------------------------------
    kpi_candidates = CORE_METRICS + key_event_metrics + ECOMMERCE_METRICS
    kpi_metrics, dropped = schema.filter_metrics(kpi_candidates)
    unsupported = [{"metric": n, "reason": r} for n, r in dropped]
    if dropped:
        runner.note("  unsupported by this property: %s" % ", ".join(n for n, _ in dropped))

    datasets = {}

    def both(key, dimensions, metrics, sort_metric=None, limit=100,
             order_by_dimension=None, required=False):
        entry = {"dimensions": dimensions, "metrics": metrics, "limit": limit,
                 "sort_metric": sort_metric}
        for period, window in (("current", cur), ("previous", prev)):
            entry[period] = runner.report(
                key, dimensions, metrics, window["start"], window["end"],
                sort_metric=sort_metric, limit=limit,
                order_by_dimension=order_by_dimension, required=required,
                label="%s.%s" % (key, period))
        datasets[key] = entry
        return entry

    totals = both("totals", [], kpi_metrics, limit=1, required=True)
    if totals["current"] is None and totals["previous"] is None:
        payload = base_payload(cfg, prop, periods, schema, runner)
        payload["datasets"] = datasets
        path = write_out(args, cfg, payload, cur)
        print(json.dumps({"status": "blocked", "raw_file": str(path),
                          "errors": runner.errors}, indent=2))
        return 4 if all(e.get("retryable") for e in runner.errors) else 3

    # Currency and time zone as the Data API itself reports them -- the
    # authority when the Admin API is unavailable.
    for period in ("current", "previous"):
        meta = ((totals.get(period) or {}).get("meta") or {})
        if meta.get("currencyCode") and not prop.get("currency"):
            prop["currency"] = meta["currencyCode"]
            prop["currency_source"] = "Data API response metadata"
        if meta.get("timeZone") and not prop.get("time_zone"):
            prop["time_zone"] = meta["timeZone"]
            prop["time_zone_source"] = "Data API response metadata"

    # -- 5. Does this property do ecommerce? --------------------------------
    ecom = ecommerce_state(totals, schema, runner)
    seg_metrics = list(SEGMENT_METRICS) + (key_event_metrics[:1] or [])
    if key_event_metrics[1:2]:
        seg_metrics.append(key_event_metrics[1])       # session key-event rate
    if ecom["state"] == "active":
        seg_metrics += SEGMENT_ECOMMERCE_METRICS
    seg_metrics, _ = schema.filter_metrics(seg_metrics)

    daily_metrics = list(DAILY_METRICS) + (key_event_metrics[:1] or [])
    if ecom["state"] == "active":
        daily_metrics += DAILY_ECOMMERCE_METRICS
    daily_metrics, _ = schema.filter_metrics(daily_metrics)

    def dim(role):
        return schema.first_dimension(DIMENSION_CANDIDATES[role])

    # -- 6. Daily trend ------------------------------------------------------
    d_date = dim("date")
    if d_date:
        both("daily", [d_date], daily_metrics, limit=max(400, days * 2),
             order_by_dimension=d_date, required=True)

    # -- 7. Acquisition ------------------------------------------------------
    d_channel = dim("session_channel")
    if d_channel:
        both("channels", [d_channel], seg_metrics, sort_metric="sessions", limit=args.top_n)
    else:
        runner.warnings.append(
            "This property does not expose a session channel-group dimension, so acquisition "
            "cannot be broken down by channel.")

    if "source_medium" not in skip and dim("session_source_medium"):
        both("source_medium", [dim("session_source_medium")], seg_metrics,
             sort_metric="sessions", limit=args.top_n)
    if "campaigns" not in skip and dim("session_campaign"):
        both("campaigns", [dim("session_campaign")], seg_metrics,
             sort_metric="sessions", limit=args.top_n)
    if "first_user_channels" not in skip and dim("first_user_channel"):
        fu_metrics, _ = schema.filter_metrics(
            ["totalUsers", "newUsers", "activeUsers", "engagedSessions", "engagementRate"]
            + (key_event_metrics[:1] or []))
        both("first_user_channels", [dim("first_user_channel")], fu_metrics,
             sort_metric="totalUsers", limit=args.top_n)

    # -- 8. Content ----------------------------------------------------------
    d_landing = dim("landing_page")
    if d_landing:
        both("landing_pages", [d_landing], seg_metrics, sort_metric="sessions",
             limit=args.page_limit)
    if "pages" not in skip and dim("page_path"):
        page_metrics, _ = schema.filter_metrics(
            ["screenPageViews", "sessions", "totalUsers", "userEngagementDuration",
             "engagementRate"] + (key_event_metrics[:1] or []))
        dims = [dim("page_path")]
        if dim("page_title"):
            dims.append(dim("page_title"))
        both("pages", dims, page_metrics, sort_metric="screenPageViews", limit=args.page_limit)
    if "hostname" not in skip and dim("hostname"):
        both("hostname", [dim("hostname")], seg_metrics, sort_metric="sessions", limit=20)

    # -- 9. Technology -------------------------------------------------------
    if dim("device"):
        both("devices", [dim("device")], seg_metrics, sort_metric="sessions", limit=10)
    if "browsers" not in skip and dim("browser"):
        both("browsers", [dim("browser")], seg_metrics, sort_metric="sessions", limit=15)
    if "os" not in skip and dim("os"):
        both("operating_systems", [dim("os")], seg_metrics, sort_metric="sessions", limit=15)
    if "browsers" not in skip and dim("platform"):
        both("platforms", [dim("platform")], seg_metrics, sort_metric="sessions", limit=10)

    # -- 10. Geography -------------------------------------------------------
    if "geo" not in skip:
        for role, key, limit in (("country", "geo_country", 30),
                                 ("region", "geo_region", 30),
                                 ("city", "geo_city", 30)):
            if dim(role):
                both(key, [dim(role)], seg_metrics, sort_metric="sessions", limit=limit)

    # -- 11. Events ----------------------------------------------------------
    if "events" not in skip and dim("event_name"):
        ev_metrics, _ = schema.filter_metrics(
            EVENT_METRICS + (key_event_metrics[:1] or []))
        both("events", [dim("event_name")], ev_metrics, sort_metric="eventCount", limit=100)

    # -- 12. Ecommerce detail ------------------------------------------------
    if ecom["state"] == "active":
        if "items" not in skip and dim("item_name"):
            it_metrics, _ = schema.filter_metrics(ITEM_METRICS)
            both("items", [dim("item_name")], it_metrics, sort_metric="itemsPurchased", limit=25)
        if d_channel:
            rev_metrics, _ = schema.filter_metrics(
                ["totalRevenue", "purchaseRevenue", "transactions", "sessions", "totalPurchasers"])
            both("revenue_by_channel", [d_channel], rev_metrics,
                 sort_metric="totalRevenue", limit=args.top_n)
        if dim("device"):
            rev_metrics, _ = schema.filter_metrics(
                ["totalRevenue", "transactions", "sessions", "purchaserRate"])
            both("revenue_by_device", [dim("device")], rev_metrics,
                 sort_metric="totalRevenue", limit=10)

    # -- 13. Row caps and thresholding are missing data. Say so. ------------
    for key, entry in datasets.items():
        limit = entry.get("limit") or 0
        for period in ("current", "previous"):
            rep = entry.get(period)
            if not rep:
                continue
            if limit and len(rep["rows"]) >= limit and limit > 1:
                runner.warnings.append(
                    "%s (%s) hit the %d-row cap -- the list is the top rows by %s, not the "
                    "whole property. Totals must not be summed from it."
                    % (key, period, limit, entry.get("sort_metric") or "the sort metric"))
            meta = rep.get("meta") or {}
            if meta.get("dataLossFromOtherRow"):
                runner.warnings.append(
                    "%s (%s): GA4 reports that this breakdown exceeded its cardinality limit "
                    "and some rows were folded into an aggregated (other) row. Row-level "
                    "figures are incomplete and shares of total will not add up."
                    % (key, period))
            if meta.get("subjectToThresholding"):
                runner.warnings.append(
                    "%s (%s): GA4 applied data thresholding, so some rows are withheld for "
                    "privacy. Small segments may be missing entirely." % (key, period))
            if meta.get("emptyReason"):
                runner.warnings.append(
                    "%s (%s): GA4 returned no rows and gave the reason %r."
                    % (key, period, meta["emptyReason"]))
            if meta.get("samplingMetadatas"):
                runner.warnings.append(
                    "%s (%s): the response is SAMPLED. Figures are estimates, not counts."
                    % (key, period))

    payload = base_payload(cfg, prop, periods, schema, runner)
    payload["datasets"] = datasets
    payload["key_events"] = {
        "metric_naming": key_event_naming,
        "metrics_used": key_event_metrics,
        "definitions": key_event_definitions,
        "declared_in_env": cfg.declared_key_events,
    }
    payload["ecommerce"] = ecom
    payload["schema_support"]["unsupported_metrics"] = unsupported
    payload["schema_support"]["kpi_metrics_requested"] = kpi_metrics

    path = write_out(args, cfg, payload, cur)
    runner.note("wrote %s" % path)

    core_failed = [e for e in runner.errors if e.get("required")]
    summary = {
        "status": "complete" if not runner.errors else ("blocked" if core_failed else "partial"),
        "raw_file": str(path),
        "property": {k: prop.get(k) for k in ("property_id", "name", "currency", "time_zone")},
        "periods": {"current": cur, "previous": prev, "basis": periods["basis"]},
        "key_event_naming": key_event_naming,
        "ecommerce": ecom["state"],
        "datasets": {k: {p: (len(v[p]["rows"]) if v.get(p) else None)
                         for p in ("current", "previous")} for k, v in datasets.items()},
        "unsupported_metrics": [u["metric"] for u in unsupported],
        "errors": runner.errors,
        "warnings": runner.warnings,
        "quota": cfg.quota,
    }
    print(json.dumps(summary, indent=2))

    if core_failed:
        return 4 if all(e.get("retryable") for e in core_failed) else 3
    return 1 if runner.errors else 0


def ecommerce_state(totals, schema, runner):
    """Does this property record purchases?

    Every GA4 property carries the ecommerce metrics in its schema whether or
    not the site sells anything, so their presence proves nothing. Only values
    do -- and a returned 0 is a real zero (no purchases recorded), which is a
    different statement from "not available".
    """
    supported = [m for m in ECOMMERCE_SIGNALS if schema.has_metric(m)]
    if not supported:
        return {"state": "unavailable",
                "reason": "No ecommerce metric exists in this property's schema.",
                "signals": {}}

    signals = {}
    any_value = False
    any_positive = False
    for m in supported:
        vals = {}
        for period in ("current", "previous"):
            rep = totals.get(period)
            v = None
            if rep:
                v = (rep.get("totals") or {}).get(m)
                if v is None and rep.get("rows"):
                    v = rep["rows"][0]["values"].get(m)
            vals[period] = v
            if v is not None:
                any_value = True
                if v > 0:
                    any_positive = True
        signals[m] = vals

    if any_positive:
        return {"state": "active", "signals": signals,
                "reason": "The property returned non-zero purchase activity."}
    if any_value:
        return {"state": "no_data", "signals": signals,
                "reason": "Ecommerce metrics were returned and every one is zero. Either the "
                          "property records no purchases, or purchase events are not being "
                          "sent. GA4 cannot tell these apart, and neither should the report."}
    return {"state": "unavailable", "signals": signals,
            "reason": "Ecommerce metrics were requested but no value came back for either "
                      "period."}


def base_payload(cfg, prop, periods, schema, runner):
    return {
        "schema": SCHEMA,
        "generated_at": dt.datetime.now().astimezone().isoformat(timespec="seconds"),
        "api": {"data_api": ga.DATA_API, "admin_api": ga.ADMIN_API},
        "property": prop or {"property_id": cfg.property_id},
        "periods": periods,
        "schema_support": {
            "metadata_loaded": bool(schema and schema.loaded),
            "dimension_count": len(schema.dimensions) if schema else 0,
            "metric_count": len(schema.metrics) if schema else 0,
            "custom_dimensions": schema.custom_dimensions if schema else [],
            "custom_metrics": schema.custom_metrics if schema else [],
            "unsupported_metrics": [],
            "kpi_metrics_requested": [],
        },
        "key_events": {},
        "ecommerce": {},
        "datasets": {},
        "errors": runner.errors,
        "warnings": runner.warnings,
        "config": {
            "agency_env": cfg.agency_env_path,
            "client_env": cfg.client_env_path,
            "property_id": cfg.property_id,
            "auth_mode": cfg.auth_mode,
            "declared_key_events": cfg.declared_key_events,
            "client_name": cfg.client_name,
            "site_url": cfg.site_url,
        },
    }


def default_out_dir(root, cur):
    stamp = cur["end"] if cur else dt.date.today().isoformat()
    return root / "reports" / "google-analytics" / stamp / "data"


def write_out(args, cfg, payload, cur):
    root = Path(args.project_root).expanduser().resolve()
    if args.out:
        out_dir = Path(args.out)
        if not out_dir.is_absolute():
            out_dir = root / out_dir
    else:
        out_dir = default_out_dir(root, cur)
    out_dir.mkdir(parents=True, exist_ok=True)
    path = out_dir / "raw.json"
    path.write_text(json.dumps(payload, indent=2), encoding="utf-8")
    return path


if __name__ == "__main__":
    sys.exit(main())
