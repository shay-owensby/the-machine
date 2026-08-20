#!/usr/bin/env python3
"""
Preflight: can this run reach this client's Google Ads account at all?

    python3 check_config.py                          # from the client project root
    python3 check_config.py --project-root ~/clients/acme
    python3 check_config.py --no-network             # config only, no API call

Prints a redacted configuration summary and, unless --no-network, makes one
cheap API call to prove the credentials, the login customer ID and the target
customer ID actually work together.

Run this FIRST, every time. Thirty seconds here turns "the report failed after
nine queries" into "the developer token is still on test access", which is a
different conversation with a different person.

No secret is printed. Credentials show as present/missing and nothing else.

Exit codes
  0  ready -- configuration resolved and (unless --no-network) the account answered
  2  configuration problem -- something required is missing or malformed
  3  authentication or permission failure -- credentials or account access is wrong
  4  transient/API failure -- worth retrying
"""

import argparse
import json
import sys

import ads_common as ads


PROBE = """
SELECT
  customer.id,
  customer.descriptive_name,
  customer.currency_code,
  customer.time_zone,
  customer.manager,
  customer.test_account,
  customer.auto_tagging_enabled
FROM customer
LIMIT 1
"""


def main():
    ap = argparse.ArgumentParser(description="Check Google Ads credentials and client configuration.")
    ap.add_argument("--project-root", default=".", help="Client project root holding .env (default: cwd)")
    ap.add_argument("--agency-env", help="Override the shared agency credential file path")
    ap.add_argument("--customer-id", help="Target Google Ads customer ID (overrides .env)")
    ap.add_argument("--login-customer-id", help="Manager/MCC customer ID (overrides .env)")
    ap.add_argument("--api-version", help="Pin the Google Ads API version, e.g. v21")
    ap.add_argument("--no-network", action="store_true", help="Resolve configuration only; make no API call")
    ap.add_argument("--json", action="store_true", help="Machine-readable output only")
    args = ap.parse_args()

    cfg = ads.resolve_config(
        project_root=args.project_root,
        agency_env=args.agency_env,
        customer_id=args.customer_id,
        login_customer_id=args.login_customer_id,
        api_version=args.api_version,
    )

    report = ads.describe_config(cfg)
    report["checked"] = "configuration only" if args.no_network else "configuration and live API call"

    if cfg.problems:
        report["status"] = "blocked"
        emit(report, args.json)
        return 2

    if args.no_network:
        report["status"] = "configuration ok (no API call attempted)"
        emit(report, args.json)
        return 0

    try:
        rows = ads.gaql(cfg, PROBE)
    except ads.ApiError as exc:
        report["status"] = "api_error"
        report["api_error"] = exc.as_dict()
        report["settings"]["api_version"] = cfg.api_version
        report["warnings"] = cfg.warnings
        emit(report, args.json)
        return 4 if exc.retryable else 3
    except ads.ConfigError as exc:
        report["status"] = "blocked"
        report["problems"] = [str(exc)]
        emit(report, args.json)
        return 2

    if not rows:
        report["status"] = "empty"
        report["problems"] = [
            "The account answered but returned no customer row. That should not happen "
            "for a valid customer ID; re-check GOOGLE_ADS_CUSTOMER_ID."
        ]
        emit(report, args.json)
        return 3

    row = rows[0]
    account = {
        "customer_id": ads.field(row, "customer.id"),
        "name": ads.field(row, "customer.descriptive_name"),
        "currency": ads.field(row, "customer.currency_code"),
        "time_zone": ads.field(row, "customer.time_zone"),
        "is_manager": bool(ads.field(row, "customer.manager")),
        "is_test_account": bool(ads.field(row, "customer.test_account")),
        "auto_tagging": ads.field(row, "customer.auto_tagging_enabled"),
    }
    report["account"].update(account)
    report["settings"]["api_version"] = cfg.api_version
    report["warnings"] = cfg.warnings
    report["status"] = "ready"

    if account["is_manager"]:
        report["warnings"].append(
            "The account being queried (%s) is a MANAGER account. Manager accounts hold no "
            "campaigns, so every metric will come back zero -- this is the wrong account, "
            "not a quiet one.%s Set GOOGLE_ADS_CUSTOMER_ID in %s to the client's operating "
            "account; the manager ID stays where it is and will then be sent as the login "
            "header."
            % (account["customer_id"],
               (" It was read from GOOGLE_ADS_LOGIN_CUSTOMER_ID, which is Google's name for"
                " the manager account, so that is the likely cause."
                if cfg.customer_id_key == "GOOGLE_ADS_LOGIN_CUSTOMER_ID" else ""),
               cfg.client_env_path)
        )
    if account["is_test_account"]:
        report["warnings"].append(
            "This is a TEST account. Any numbers it returns are fabricated by Google and "
            "must never be reported to a client."
        )

    emit(report, args.json)
    return 0


def emit(report, as_json):
    if as_json:
        print(json.dumps(report, indent=2))
        return
    print(json.dumps(report, indent=2))
    acct = report.get("account", {})
    print("", file=sys.stderr)
    print("status: %s" % report.get("status"), file=sys.stderr)
    if acct.get("name"):
        print("account: %s (%s) %s / %s" % (
            acct.get("name"), acct.get("customer_id"),
            acct.get("currency"), acct.get("time_zone")), file=sys.stderr)
        print("         account ID read from %s; login header %s" % (
            acct.get("customer_id_key") or "unknown",
            ("sent as %s" % acct["login_customer_id"]) if acct.get("login_customer_id")
            else "not sent (querying directly)"), file=sys.stderr)
    for w in report.get("warnings") or []:
        print("warning: %s" % w, file=sys.stderr)
    for p in report.get("problems") or []:
        print("problem: %s" % p, file=sys.stderr)


if __name__ == "__main__":
    sys.exit(main())
