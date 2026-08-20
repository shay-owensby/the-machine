#!/usr/bin/env python3
"""
Preflight: can this run reach this client's GA4 property at all?

    python3 check_config.py                            # from the client project root
    python3 check_config.py --project-root ~/clients/acme
    python3 check_config.py --no-network               # config only, no API call
    python3 check_config.py --list-properties          # what can this identity see?

Prints a redacted configuration summary and, unless --no-network, makes three
cheap calls that prove -- separately -- the four things that go wrong:

    1. the credentials mint a token                    (OAuth / service account)
    2. that token carries an Analytics scope           (Data API answers at all)
    3. the identity can read THIS property             (property access)
    4. the property has recent data                    (tracking is alive)

Run this FIRST, every time. Thirty seconds here turns "the report failed after
eleven queries" into "nobody granted the agency account access to the property",
which is a different conversation with a different person.

No secret is printed. Credentials show as present/missing and nothing else.

Exit codes
  0  ready -- configuration resolved and (unless --no-network) the property answered
  2  configuration problem -- something required is missing or malformed
  3  authentication or property-access failure
  4  transient/API failure -- worth retrying
"""

import argparse
import datetime as dt
import json
import sys

import ga4_common as ga


def probe_body(days=7):
    end = dt.date.today() - dt.timedelta(days=1)
    start = end - dt.timedelta(days=days - 1)
    return {
        "dateRanges": [{"startDate": start.isoformat(), "endDate": end.isoformat()}],
        "metrics": [{"name": "sessions"}],
        "limit": 1,
    }


def main():
    ap = argparse.ArgumentParser(description="Check Google credentials and GA4 property configuration.")
    ap.add_argument("--project-root", default=".", help="Client project root holding .env (default: cwd)")
    ap.add_argument("--agency-env", help="Override the shared agency credential file path")
    ap.add_argument("--property-id", help="GA4 property ID (overrides .env)")
    ap.add_argument("--no-network", action="store_true", help="Resolve configuration only; make no API call")
    ap.add_argument("--list-properties", action="store_true",
                    help="List every GA4 property this identity can see, then exit")
    ap.add_argument("--json", action="store_true", help="Machine-readable output only")
    args = ap.parse_args()

    cfg = ga.resolve_config(
        project_root=args.project_root,
        agency_env=args.agency_env,
        property_id=args.property_id,
        require_property_id=not args.list_properties,
    )

    report = ga.describe_config(cfg)
    report["checked"] = "configuration only" if args.no_network else "configuration and live API calls"

    if cfg.problems:
        report["status"] = "blocked"
        emit(report, args.json)
        return 2

    if args.no_network:
        report["status"] = "configuration ok (no API call attempted)"
        emit(report, args.json)
        return 0

    if args.list_properties:
        return list_properties(cfg, report, args.json)

    # --- 1 + 2 + 3: one Data API report proves token, scope, and access ------
    try:
        parsed = ga.run_report(cfg, probe_body())
    except ga.ApiError as exc:
        report["status"] = "api_error"
        report["api_error"] = exc.as_dict()
        emit(report, args.json)
        return 4 if exc.retryable else 3
    except ga.ConfigError as exc:
        report["status"] = "blocked"
        report["problems"] = [str(exc)]
        emit(report, args.json)
        return 2

    rep = ga.parse_report(parsed)
    meta = rep["meta"] or {}
    sessions = (rep["totals"] or {}).get("sessions")
    if sessions is None and rep["rows"]:
        sessions = rep["rows"][0]["values"].get("sessions")

    report["property"].update({
        "time_zone": meta.get("timeZone"),
        "currency": meta.get("currencyCode"),
        "reachable": True,
        "sessions_last_7_days": sessions,
    })
    report["quota"] = cfg.quota

    # --- 4: is anything actually being collected? ---------------------------
    if sessions is None:
        report["warnings"].append(
            "The property answered but reported no sessions figure at all for the last 7 "
            "days. That is not the same as zero -- check the property is the right one.")
    elif sessions == 0:
        report["warnings"].append(
            "The property is reachable but recorded ZERO sessions in the last 7 days. Either "
            "this is a new or dormant property, or tracking has stopped. A report built on "
            "this will be empty, and must say why rather than showing zeros as performance.")

    # --- Admin API: nice to have, never required ----------------------------
    admin = {"available": False}
    try:
        prop = ga.admin_get(cfg, "properties/%s" % cfg.property_id)
        admin.update({
            "available": True,
            "display_name": prop.get("displayName"),
            "time_zone": prop.get("timeZone"),
            "currency": prop.get("currencyCode"),
            "industry": prop.get("industryCategory"),
            "created": prop.get("createTime"),
            "parent_account": prop.get("parent"),
            "property_type": prop.get("propertyType"),
        })
        report["property"]["name"] = prop.get("displayName")
    except ga.ApiError as exc:
        admin["error"] = exc.message
        admin["hint"] = exc.detail
        report["warnings"].append(
            "The Admin API did not answer (%s). Reporting still works -- the property name "
            "will be missing and key-event definitions cannot be read. See "
            "references/authentication.md." % (exc.error_code or exc.status))

    if admin["available"]:
        try:
            ke = ga.admin_get(cfg, "properties/%s/keyEvents" % cfg.property_id)
            names = [k.get("eventName") for k in (ke.get("keyEvents") or [])]
            admin["key_events"] = names
            if not names:
                report["warnings"].append(
                    "This property has NO key events configured. Every conversion-shaped "
                    "number in the report will be absent, and the report must say the "
                    "property does not define conversions rather than reporting zero.")
        except ga.ApiError as exc:
            admin["key_events_error"] = exc.message

    report["admin_api"] = admin
    report["status"] = "ready"
    emit(report, args.json)
    return 0


def list_properties(cfg, report, as_json):
    """Account/property discovery -- the fastest way to find a property ID, and
    the fastest proof that access was granted to the wrong account."""
    try:
        summaries = ga.admin_get(cfg, "accountSummaries?pageSize=200")
    except ga.ApiError as exc:
        report["status"] = "api_error"
        report["api_error"] = exc.as_dict()
        report["problems"] = [
            "Property discovery needs the Google Analytics ADMIN API, which is a separate "
            "API from the Data API used for reporting. If it is disabled, find the property "
            "ID by hand in the GA4 interface: Admin > Property > Property details."]
        emit(report, as_json)
        return 4 if exc.retryable else 3

    found = []
    for acct in summaries.get("accountSummaries", []) or []:
        for prop in acct.get("propertySummaries", []) or []:
            found.append({
                "property_id": (prop.get("property") or "").split("/")[-1],
                "property_name": prop.get("displayName"),
                "account": acct.get("displayName"),
                "account_id": (acct.get("account") or "").split("/")[-1],
            })
    report["status"] = "ready"
    report["visible_properties"] = found
    if not found:
        report["warnings"].append(
            "This identity can see no GA4 properties at all. Nobody has granted it access "
            "yet -- see references/authentication.md, 'Property access'.")
    emit(report, as_json)
    return 0


def emit(report, as_json):
    print(json.dumps(report, indent=2))
    if as_json:
        return
    prop = report.get("property", {})
    print("", file=sys.stderr)
    print("status: %s" % report.get("status"), file=sys.stderr)
    if prop.get("property_id"):
        print("property: %s (%s) %s / %s" % (
            prop.get("name") or prop.get("name_hint") or "name unknown",
            prop.get("property_id"), prop.get("currency") or "currency unknown",
            prop.get("time_zone") or "time zone unknown"), file=sys.stderr)
    for row in report.get("visible_properties") or []:
        print("  %s  %-40s  %s" % (row["property_id"], row["property_name"], row["account"]),
              file=sys.stderr)
    for w in report.get("warnings") or []:
        print("warning: %s" % w, file=sys.stderr)
    for p in report.get("problems") or []:
        print("problem: %s" % p, file=sys.stderr)
    err = report.get("api_error")
    if err:
        print("error: %s" % err.get("message"), file=sys.stderr)
        if err.get("detail"):
            print("hint: %s" % err["detail"], file=sys.stderr)


if __name__ == "__main__":
    sys.exit(main())
