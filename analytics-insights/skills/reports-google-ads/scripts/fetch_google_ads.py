#!/usr/bin/env python3
"""
Retrieve one reporting run's worth of Google Ads data and write it to a single
raw JSON file. Retrieval only -- no analysis, no interpretation, no rounding.

    python3 fetch_google_ads.py --project-root . --out analytics-insights/google-ads/_data

Default periods: the most recent 30 completed days in the ACCOUNT's time zone,
against the 30 days immediately before them. Yesterday is the last day included;
today is never included, because a partial day would compare against a whole one.

Why a file, and why raw: analysis and charting read this file instead of the
API, so the analytical logic can be tested, re-run and argued with offline
without burning quota or -- worse -- quietly returning different numbers the
second time. The file is also the audit trail for what the account actually
said on the day the report was written.

What it does NOT do: fill gaps. A metric the API did not return is absent here
and stays absent downstream. A query that fails is recorded in `errors` with the
reason, and the dataset it fed is marked unavailable. Nothing is defaulted to
zero, ever.

Exit codes
  0  complete -- every requested dataset came back
  1  partial   -- core data retrieved, some optional datasets failed (see errors[])
  2  configuration problem
  3  authentication/permission failure, or core data unavailable
  4  transient API failure -- retry
"""

import argparse
import datetime as dt
import json
import sys
from pathlib import Path

import ads_common as ads

SCHEMA = "reports-google-ads/raw@1"

# ---------------------------------------------------------------------------
# Field lists
#
# Keep these in one place: the analysis, the charts and the reference docs all
# describe what is here, and a metric added in two places drifts in one.
# ---------------------------------------------------------------------------

CORE_METRICS = """
  metrics.impressions,
  metrics.clicks,
  metrics.ctr,
  metrics.cost_micros,
  metrics.average_cpc,
  metrics.conversions,
  metrics.conversions_value,
  metrics.cost_per_conversion,
  metrics.value_per_conversion,
  metrics.conversions_from_interactions_rate,
  metrics.all_conversions,
  metrics.all_conversions_value
"""

SHARE_METRICS = """
  metrics.search_impression_share,
  metrics.search_budget_lost_impression_share,
  metrics.search_rank_lost_impression_share,
  metrics.search_absolute_top_impression_share,
  metrics.search_top_impression_share
"""


def q_customer():
    return """
SELECT
  customer.id,
  customer.descriptive_name,
  customer.currency_code,
  customer.time_zone,
  customer.manager,
  customer.test_account,
  customer.status,
  customer.auto_tagging_enabled,
  customer.optimization_score
FROM customer
LIMIT 1
"""


def q_account_totals(start, end):
    return "SELECT %s FROM customer WHERE segments.date BETWEEN '%s' AND '%s'" % (
        CORE_METRICS, start, end)


def q_daily(start, end):
    return ("SELECT segments.date, %s FROM customer "
            "WHERE segments.date BETWEEN '%s' AND '%s' ORDER BY segments.date"
            % (CORE_METRICS, start, end))


def q_campaigns(start, end):
    return """
SELECT
  campaign.id,
  campaign.name,
  campaign.status,
  campaign.advertising_channel_type,
  campaign.advertising_channel_sub_type,
  campaign.bidding_strategy_type,
  campaign.start_date,
  campaign.end_date,
  campaign_budget.amount_micros,
  campaign_budget.explicitly_shared,
  %s,
  %s
FROM campaign
WHERE segments.date BETWEEN '%s' AND '%s'
ORDER BY metrics.cost_micros DESC
""" % (CORE_METRICS, SHARE_METRICS, start, end)


def q_device(start, end):
    return ("SELECT segments.device, %s FROM campaign "
            "WHERE segments.date BETWEEN '%s' AND '%s'" % (CORE_METRICS, start, end))


def q_network(start, end):
    return ("SELECT segments.ad_network_type, %s FROM campaign "
            "WHERE segments.date BETWEEN '%s' AND '%s'" % (CORE_METRICS, start, end))


def q_ad_groups(start, end, limit):
    return """
SELECT
  campaign.id, campaign.name,
  ad_group.id, ad_group.name, ad_group.status,
  %s
FROM ad_group
WHERE segments.date BETWEEN '%s' AND '%s'
ORDER BY metrics.cost_micros DESC
LIMIT %d
""" % (CORE_METRICS, start, end, limit)


def q_keywords(start, end, limit):
    return """
SELECT
  campaign.name,
  ad_group.name,
  ad_group_criterion.keyword.text,
  ad_group_criterion.keyword.match_type,
  ad_group_criterion.status,
  %s
FROM keyword_view
WHERE segments.date BETWEEN '%s' AND '%s'
ORDER BY metrics.cost_micros DESC
LIMIT %d
""" % (CORE_METRICS, start, end, limit)


def q_search_terms(start, end, limit):
    return """
SELECT
  campaign.name,
  ad_group.name,
  search_term_view.search_term,
  search_term_view.status,
  metrics.impressions,
  metrics.clicks,
  metrics.ctr,
  metrics.cost_micros,
  metrics.conversions,
  metrics.conversions_value
FROM search_term_view
WHERE segments.date BETWEEN '%s' AND '%s'
ORDER BY metrics.cost_micros DESC
LIMIT %d
""" % (start, end, limit)


def q_conversion_actions_meta():
    return """
SELECT
  conversion_action.id,
  conversion_action.name,
  conversion_action.category,
  conversion_action.type,
  conversion_action.status,
  conversion_action.primary_for_goal,
  conversion_action.counting_type,
  conversion_action.include_in_conversions_metric
FROM conversion_action
"""


def q_conversion_performance(start, end):
    # Segmenting by conversion action is only compatible with the all_conversions
    # family, which is why per-action figures downstream are all-conversions
    # figures and are labelled as such rather than mixed with metrics.conversions.
    return """
SELECT
  segments.conversion_action_name,
  segments.conversion_action_category,
  metrics.all_conversions,
  metrics.all_conversions_value
FROM customer
WHERE segments.date BETWEEN '%s' AND '%s'
""" % (start, end)


# ---------------------------------------------------------------------------
# Dates
# ---------------------------------------------------------------------------

def today_in_zone(tz_name, warnings):
    """Today's date in the account's own time zone.

    Google Ads days are account-time-zone days. Computing 'yesterday' in the
    machine's local zone can silently include or drop a day of spend, which is
    a wrong number in a client report, not a rounding detail.
    """
    if tz_name:
        try:
            from zoneinfo import ZoneInfo
            return dt.datetime.now(ZoneInfo(tz_name)).date(), tz_name
        except Exception as exc:
            warnings.append(
                "Could not use the account time zone %r (%s). Falling back to this "
                "machine's local date, which may shift the window by a day."
                % (tz_name, exc.__class__.__name__)
            )
    else:
        warnings.append(
            "The account did not report a time zone. Using this machine's local date."
        )
    return dt.date.today(), "local"


def iso(d):
    return d.isoformat()


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
    else:
        today, zone_used = today_in_zone(tz_name, warnings)
        if args.end_date:
            c_end = dt.date.fromisoformat(args.end_date)
            basis = "explicit --end-date"
        else:
            c_end = today - dt.timedelta(days=1 + lag_days)
            basis = ("most recent %d completed days ending yesterday in %s"
                     % (days, zone_used))
            if lag_days:
                basis += " minus a %d-day conversion-lag buffer" % lag_days
        c_start = c_end - dt.timedelta(days=days - 1)
        p_end = c_start - dt.timedelta(days=1)
        p_start = p_end - dt.timedelta(days=days - 1)

    c_days = (c_end - c_start).days + 1
    p_days = (p_end - p_start).days + 1
    if c_days != p_days:
        warnings.append(
            "The two periods are different lengths (%d days vs %d days). Totals are not "
            "comparable and percentage changes will mislead. Every table built on this "
            "must say so." % (c_days, p_days)
        )
    if p_end >= c_start:
        warnings.append(
            "The comparison period overlaps the current period (%s..%s vs %s..%s). The "
            "same days are counted twice." % (p_start, p_end, c_start, c_end))

    return {
        "current": {"start": iso(c_start), "end": iso(c_end), "days": c_days},
        "previous": {"start": iso(p_start), "end": iso(p_end), "days": p_days},
        "basis": basis,
        "time_zone": tz_name,
    }


# ---------------------------------------------------------------------------
# Retrieval
# ---------------------------------------------------------------------------

class Runner(object):
    def __init__(self, cfg, verbose=True):
        self.cfg = cfg
        self.verbose = verbose
        self.errors = []
        self.warnings = []

    def note(self, msg):
        if self.verbose:
            print(msg, file=sys.stderr)

    def run(self, key, query, required=False, label=None):
        """Run one query. On failure record it and return None -- never a []."""
        label = label or key
        try:
            def on_retry(attempt, delay, err):
                self.note("  %s: transient failure (%s), retry %d in %.1fs"
                          % (label, err.error_code or err.status, attempt, delay))
            rows = ads.gaql(self.cfg, query, on_retry=on_retry)
            self.note("  %s: %d row(s)" % (label, len(rows)))
            return rows
        except ads.ApiError as exc:
            self.errors.append({
                "dataset": key,
                "required": required,
                "message": exc.message,
                "error_code": exc.error_code,
                "http_status": exc.status,
                "hint": exc.detail,
                "retryable": exc.retryable,
            })
            self.note("  %s: FAILED -- %s" % (label, exc.message))
            return None


def main():
    ap = argparse.ArgumentParser(description="Retrieve Google Ads data for a period-over-period report.")
    ap.add_argument("--project-root", default=".", help="Client project root holding .env (default: cwd)")
    ap.add_argument("--out", default="analytics-insights/google-ads/_data",
                    help="Directory for the raw JSON file (relative to the project root)")
    ap.add_argument("--agency-env", help="Override the shared agency credential file path")
    ap.add_argument("--customer-id", help="Target Google Ads customer ID (overrides .env)")
    ap.add_argument("--login-customer-id", help="Manager/MCC customer ID (overrides .env)")
    ap.add_argument("--api-version", help="Pin the Google Ads API version, e.g. v21")
    ap.add_argument("--days", type=int, help="Days per period (default 30, or GOOGLE_ADS_REPORT_DAYS)")
    ap.add_argument("--end-date", help="Last day of the current period, YYYY-MM-DD")
    ap.add_argument("--current", help="Explicit current period YYYY-MM-DD:YYYY-MM-DD")
    ap.add_argument("--previous", help="Explicit comparison period YYYY-MM-DD:YYYY-MM-DD")
    ap.add_argument("--skip", default="", help="Comma-separated optional datasets to skip "
                                               "(device,network,ad_groups,keywords,search_terms,conversion_actions)")
    ap.add_argument("--top-n", type=int, default=100, help="Row cap for ad groups and keywords (default 100)")
    ap.add_argument("--search-terms-limit", type=int, default=200, help="Row cap for search terms (default 200)")
    ap.add_argument("--quiet", action="store_true")
    args = ap.parse_args()

    cfg = ads.resolve_config(
        project_root=args.project_root,
        agency_env=args.agency_env,
        customer_id=args.customer_id,
        login_customer_id=args.login_customer_id,
        api_version=args.api_version,
    )
    if cfg.problems:
        print(json.dumps({"status": "blocked", "problems": cfg.problems,
                          "config": ads.describe_config(cfg)}, indent=2))
        for p in cfg.problems:
            print("problem: %s" % p, file=sys.stderr)
        return 2

    runner = Runner(cfg, verbose=not args.quiet)
    runner.warnings.extend(cfg.warnings)
    skip = {s.strip() for s in args.skip.split(",") if s.strip()}
    days = args.days or cfg.report_days

    runner.note("Google Ads retrieval -- customer %s via login %s, API %s"
                % (cfg.customer_id, cfg.login_customer_id or "(none)", cfg.api_version))

    # 1. The account itself, first: its time zone decides what "yesterday" means
    #    and its currency decides what every money figure downstream means.
    customer_rows = runner.run("customer", q_customer(), required=True)
    if customer_rows is None:
        payload = base_payload(cfg, None, None, runner)
        write_out(args, cfg, payload, None)
        return 3 if not any(e["retryable"] for e in runner.errors) else 4

    crow = customer_rows[0] if customer_rows else {}
    account = {
        "customer_id": ads.field(crow, "customer.id") or cfg.customer_id,
        "name": ads.field(crow, "customer.descriptive_name"),
        "currency": ads.field(crow, "customer.currency_code"),
        "time_zone": ads.field(crow, "customer.time_zone"),
        "is_manager": bool(ads.field(crow, "customer.manager")),
        "is_test_account": bool(ads.field(crow, "customer.test_account")),
        "status": ads.field(crow, "customer.status"),
        "auto_tagging_enabled": ads.field(crow, "customer.auto_tagging_enabled"),
        "optimization_score": ads.field(crow, "customer.optimization_score"),
        "login_customer_id": cfg.login_customer_id,
    }
    if account["is_manager"]:
        runner.warnings.append(
            "Customer %s is a manager (MCC) account. Manager accounts run no campaigns, so "
            "every metric below will be empty or zero. Report on the operating account "
            "instead." % account["customer_id"])
    if account["is_test_account"]:
        runner.warnings.append(
            "Customer %s is a TEST account. Its metrics are synthetic and must never be "
            "presented to a client." % account["customer_id"])
    if account["status"] and account["status"] not in ("ENABLED", "UNSPECIFIED", "UNKNOWN"):
        runner.warnings.append("Account status is %s." % account["status"])

    periods = build_periods(args, account["time_zone"], days, cfg.lag_days, runner.warnings)
    cur, prev = periods["current"], periods["previous"]
    runner.note("  current  %s .. %s (%d days)" % (cur["start"], cur["end"], cur["days"]))
    runner.note("  previous %s .. %s (%d days)" % (prev["start"], prev["end"], prev["days"]))

    datasets = {}

    def both(key, fn, required=False):
        datasets[key] = {
            "current": runner.run("%s.current" % key, fn(cur["start"], cur["end"]), required),
            "previous": runner.run("%s.previous" % key, fn(prev["start"], prev["end"]), required),
        }

    both("account_totals", q_account_totals, required=True)
    both("daily", q_daily, required=True)
    both("campaigns", q_campaigns, required=True)

    if "device" not in skip:
        both("device", q_device)
    if "network" not in skip:
        both("network", q_network)
    if "ad_groups" not in skip:
        both("ad_groups", lambda s, e: q_ad_groups(s, e, args.top_n))
    if "keywords" not in skip:
        both("keywords", lambda s, e: q_keywords(s, e, args.top_n))
    if "search_terms" not in skip:
        datasets["search_terms"] = {
            "current": runner.run("search_terms.current",
                                  q_search_terms(cur["start"], cur["end"], args.search_terms_limit)),
            "previous": None,
        }
        datasets["search_terms"]["previous_note"] = (
            "Not retrieved. Search-term reporting is expensive and its comparison value is "
            "low; the current period is enough to spot waste.")
    if "conversion_actions" not in skip:
        datasets["conversion_actions_meta"] = {
            "current": runner.run("conversion_actions_meta", q_conversion_actions_meta()),
            "previous": None,
        }
        both("conversion_performance", q_conversion_performance)

    # Row caps are a form of missing data. Say so rather than let a truncated
    # list read as the whole account.
    for key, limit in (("ad_groups", args.top_n), ("keywords", args.top_n),
                       ("search_terms", args.search_terms_limit)):
        ds = datasets.get(key)
        if not ds:
            continue
        for period in ("current", "previous"):
            rows = ds.get(period)
            if rows is not None and len(rows) >= limit:
                runner.warnings.append(
                    "%s (%s) hit the %d-row cap -- the list is the top rows by cost, not "
                    "the whole account. Totals must not be summed from it."
                    % (key, period, limit))

    payload = base_payload(cfg, account, periods, runner)
    payload["datasets"] = datasets

    core_failed = [e for e in runner.errors if e["required"]]
    path = write_out(args, cfg, payload, cur)

    runner.note("wrote %s" % path)
    summary = {
        "status": "complete" if not runner.errors else ("blocked" if core_failed else "partial"),
        "raw_file": str(path),
        "account": {k: account[k] for k in ("customer_id", "name", "currency", "time_zone")},
        "periods": {"current": cur, "previous": prev, "basis": periods["basis"]},
        "datasets": {k: {p: (len(v[p]) if isinstance(v.get(p), list) else None)
                         for p in ("current", "previous")}
                     for k, v in datasets.items()},
        "errors": runner.errors,
        "warnings": runner.warnings,
    }
    print(json.dumps(summary, indent=2))

    if core_failed:
        return 4 if all(e["retryable"] for e in core_failed) else 3
    return 1 if runner.errors else 0


def base_payload(cfg, account, periods, runner):
    return {
        "schema": SCHEMA,
        "generated_at": dt.datetime.now().astimezone().isoformat(timespec="seconds"),
        "api_version": cfg.api_version,
        "account": account,
        "periods": periods,
        "datasets": {},
        "errors": runner.errors,
        "warnings": runner.warnings,
        "config": {
            "agency_env": cfg.agency_env_path,
            "client_env": cfg.client_env_path,
            "login_customer_id": cfg.login_customer_id,
            "customer_id": cfg.customer_id,
            "primary_conversion_actions": cfg.primary_conversion_actions,
        },
    }


def write_out(args, cfg, payload, cur):
    root = Path(args.project_root).expanduser().resolve()
    out_dir = Path(args.out)
    if not out_dir.is_absolute():
        out_dir = root / out_dir
    out_dir.mkdir(parents=True, exist_ok=True)
    stamp = ("%s_%s" % (cur["start"], cur["end"])) if cur else dt.date.today().isoformat()
    path = out_dir / ("%s_%s_raw.json" % (cfg.customer_id, stamp))
    path.write_text(json.dumps(payload, indent=2), encoding="utf-8")
    return path


if __name__ == "__main__":
    sys.exit(main())
