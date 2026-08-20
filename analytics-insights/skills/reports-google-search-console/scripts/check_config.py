#!/usr/bin/env python3
"""
Preflight: can this run reach this client's Search Console property at all?

    python3 check_config.py                              # from the client project root
    python3 check_config.py --project-root ~/clients/acme
    python3 check_config.py --list-sites                 # every property this identity can read
    python3 check_config.py --no-network                 # configuration only, no API call

Prints a redacted configuration summary and, unless --no-network, proves three
things with two cheap calls: the credentials work, the configured property
exists and is readable, and the property actually has finalised Search Analytics
data to report on.

Run this FIRST, every time. Thirty seconds here turns "the report failed after
nine queries" into "the service account was never added to the property", which
is a different conversation with a different person.

No credential is printed. They show as present/missing and nothing else.

Exit codes
  0  ready
  2  configuration problem -- something required is missing or malformed
  3  authentication, permission or property failure
  4  transient/API failure -- worth retrying
"""

import argparse
import json
import sys

import gsc_common as gsc


def main():
    ap = argparse.ArgumentParser(
        description="Check Search Console credentials and client configuration.")
    ap.add_argument("--project-root", default=".", help="Client project root holding .env")
    ap.add_argument("--agency-env", help="Override the shared agency credential file path")
    ap.add_argument("--site-url", help="Property to check (overrides GSC_SITE_URL)")
    ap.add_argument("--search-type", help="Search type to probe (default web)")
    ap.add_argument("--list-sites", action="store_true",
                    help="List every property this identity can read, then exit")
    ap.add_argument("--no-network", action="store_true",
                    help="Resolve configuration only; make no API call")
    ap.add_argument("--json", action="store_true", help="Machine-readable output only")
    args = ap.parse_args()

    cfg = gsc.resolve_config(
        project_root=args.project_root, agency_env=args.agency_env,
        site_url=args.site_url, search_type=args.search_type,
        require_site_url=not args.list_sites,
    )

    report = gsc.describe_config(cfg)
    report["checked"] = ("configuration only" if args.no_network
                         else "configuration and live API calls")

    if cfg.problems:
        report["status"] = "blocked"
        emit(report, args.json)
        return 2

    if args.no_network:
        report["status"] = "configuration ok (no API call attempted)"
        emit(report, args.json)
        return 0

    # -- 1. can we authenticate, and what can this identity see? -------------
    try:
        sites = gsc.list_sites(cfg)
    except gsc.ApiError as exc:
        report["status"] = "api_error"
        report["api_error"] = exc.as_dict()
        emit(report, args.json)
        return 4 if exc.retryable else 3
    except gsc.ConfigError as exc:
        report["status"] = "blocked"
        report["problems"] = [str(exc)]
        emit(report, args.json)
        return 2

    report["accessible_properties"] = sites
    report["accessible_property_count"] = len(sites)

    if args.list_sites:
        report["status"] = "listed"
        emit(report, args.json)
        return 0

    # -- 2. is the configured property one of them? --------------------------
    match = next((s for s in sites if s["site_url"] == cfg.site_url), None)
    if not match:
        near = [s["site_url"] for s in sites
                if gsc.site_display(s["site_url"])
                and (gsc.site_display(s["site_url"]) or "").replace("www.", "")
                == (gsc.site_display(cfg.site_url) or "").replace("www.", "")]
        report["status"] = "property_not_accessible"
        problem = (
            "GSC_SITE_URL is %r, which is not among the %d propert(ies) this identity can read.\n"
            "  Search Console property identifiers are exact: 'https://example.com/', "
            "'https://www.example.com/' and 'sc-domain:example.com' are three different\n"
            "  properties holding different data."
            % (cfg.site_url, len(sites))
        )
        if near:
            problem += ("\n  The same domain IS readable as: %s\n"
                        "  If that is the right property, set GSC_SITE_URL to that exact string."
                        % ", ".join(near))
        else:
            problem += (
                "\n  Grant access in Search Console: Settings -> Users and permissions -> Add "
                "user, with %s at Full or Restricted. This is not a Google Cloud permission."
                % ("the service account's client_email"
                   if cfg.auth_method == "service_account"
                   else "the Google account behind the refresh token")
            )
        report["problems"] = [problem]
        emit(report, args.json)
        return 3

    report["property"].update({
        "permission_level": match["permission_level"],
        "resolved_property_type": match["property_type"],
    })
    if match["permission_level"] == "siteUnverifiedUser":
        report["warnings"].append(
            "This identity is listed on the property as an unverified user, which grants no "
            "data access. An Owner must add it as a Full or Restricted user."
        )

    # -- 3. does the property have finalised data to report on? --------------
    try:
        freshness = gsc.latest_final_date(cfg)
    except gsc.ApiError as exc:
        report["status"] = "api_error"
        report["api_error"] = exc.as_dict()
        emit(report, args.json)
        return 4 if exc.retryable else 3

    report["freshness"] = freshness
    if not freshness["latest_final"]:
        report["status"] = "no_data"
        report["problems"] = [
            "The property is readable but returned no finalised data in the last %d days.\n"
            "  Either it is newly verified, it has no search traffic, or the identifier points "
            "at a property that is not the live site." % freshness["lookback_days"]
        ]
        emit(report, args.json)
        return 3

    if (freshness.get("lag_days") or 0) > 5:
        report["warnings"].append(
            "The latest finalised date is %s, %d days behind today. Search Console normally "
            "lags two to three days; a larger gap can mean a reporting delay on Google's side."
            % (freshness["latest_final"], freshness["lag_days"])
        )

    report["status"] = "ready"
    emit(report, args.json)
    return 0


def emit(report, as_json):
    print(json.dumps(report, indent=2))
    if as_json:
        return
    print("", file=sys.stderr)
    print("status: %s" % report.get("status"), file=sys.stderr)
    prop = report.get("property") or {}
    if prop.get("site_url"):
        print("property: %s (%s, permission: %s)" % (
            prop.get("site_url"), prop.get("property_type"),
            prop.get("permission_level") or "unknown"), file=sys.stderr)
    fresh = report.get("freshness")
    if fresh and fresh.get("latest_final"):
        print("latest finalised data: %s (%s days behind today); %d provisional day(s) exist"
              % (fresh["latest_final"], fresh.get("lag_days"),
                 fresh.get("fresh_days_available", 0)), file=sys.stderr)
    if report.get("accessible_property_count") is not None and report.get("status") == "listed":
        for s in report.get("accessible_properties") or []:
            print("  %-50s %s" % (s["site_url"], s["permission_level"]), file=sys.stderr)
    for w in report.get("warnings") or []:
        print("warning: %s" % w, file=sys.stderr)
    for p in report.get("problems") or []:
        print("problem: %s" % p, file=sys.stderr)


if __name__ == "__main__":
    try:
        sys.exit(main())
    except gsc.ConfigError as exc:
        print("problem: %s" % exc, file=sys.stderr)
        sys.exit(2)
