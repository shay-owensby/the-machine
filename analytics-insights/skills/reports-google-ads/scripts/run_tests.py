#!/usr/bin/env python3
"""
The skill's own test suite. No network, no credentials, no quota.

    python3 run_tests.py            # everything
    python3 run_tests.py --verbose  # name every passing case too

Covers the cases that break reports rather than the cases that break code:
missing credentials, an account with no conversions, an account with no
conversion value, a comparison period of zeros, sparse campaigns, paused
campaigns, partial metric availability, failed queries, rate limits and a
sunset API version. Each one asserts on what the OUTPUT says, because the
failure mode that matters is a report that reads as confident when the data
underneath it is missing.

The live API is exercised separately by check_config.py, which is the only
part of this skill that needs credentials to prove itself.

Exit code 0 all passed, 1 one or more failed.
"""

import argparse
import io
import json
import os
import sys
import tempfile
from pathlib import Path

import ads_common as ads
import analyze_performance as ap

HERE = Path(__file__).resolve().parent
FIXTURES = HERE.parent / "assets" / "fixtures"

RESULTS = []


def check(name, condition, detail=""):
    RESULTS.append((name, bool(condition), detail))
    return bool(condition)


def section(title):
    RESULTS.append((("== %s" % title), None, ""))


def load(fixture):
    raw = json.loads((FIXTURES / ("%s_raw.json" % fixture)).read_text())
    raw["_source_path"] = str(FIXTURES / ("%s_raw.json" % fixture))
    return ap.build(raw)


def kpi(analysis, key):
    return analysis["kpis_by_key"][key]


# ---------------------------------------------------------------------------
# Configuration and credentials
# ---------------------------------------------------------------------------

def test_config():
    section("configuration and credentials")

    with tempfile.TemporaryDirectory() as tmp:
        tmp = Path(tmp)
        agency = tmp / "agency.env"
        project = tmp / "client"
        project.mkdir()

        # -- missing agency.env entirely
        clean_env()
        cfg = ads.resolve_config(project_root=str(project), agency_env=str(agency))
        check("missing agency.env is a blocking problem", cfg.problems)
        check("missing agency.env names the file it wanted",
              any(str(agency) in p for p in cfg.problems))
        check("missing agency.env does not raise", True)

        # -- agency.env present but incomplete
        agency.write_text("GOOGLE_CLIENT_ID=abc\n# a comment\nexport GOOGLE_CLIENT_SECRET='shh'\n")
        cfg = ads.resolve_config(project_root=str(project), agency_env=str(agency))
        joined = "\n".join(cfg.problems)
        check("missing refresh token is reported",
              "GOOGLE_REFRESH_TOKEN" in joined)
        check("missing developer token is reported",
              "GOOGLE_ADS_DEVELOPER_TOKEN" in joined)
        check("quoted and exported values parse",
              cfg.client_secret == "shh" and cfg.client_id == "abc")

        # -- credentials complete, no account named anywhere
        agency.write_text(
            "GOOGLE_CLIENT_ID=abc\nGOOGLE_CLIENT_SECRET=shh\n"
            "GOOGLE_REFRESH_TOKEN=1//tok\nGOOGLE_ADS_DEVELOPER_TOKEN=devtok\n")
        cfg = ads.resolve_config(project_root=str(project), agency_env=str(agency))
        check("no account named anywhere is a blocking problem",
              any("No Google Ads account to report on" in x for x in cfg.problems))
        check("the block names both accepted keys",
              any("GOOGLE_ADS_LOGIN_CUSTOMER_ID" in x and "GOOGLE_ADS_CUSTOMER_ID" in x
                  for x in cfg.problems))

        # -- the real convention: a client .env labels its ACCOUNT with the login
        #    key. It has to resolve, and it has to say that it did.
        agency.write_text(
            "GOOGLE_CLIENT_ID=abc\nGOOGLE_CLIENT_SECRET=shh\n"
            "GOOGLE_REFRESH_TOKEN=1//tok\nGOOGLE_ADS_DEVELOPER_TOKEN=devtok\n"
            "GOOGLE_ADS_LOGIN_CUSTOMER_ID=111-222-3333\n")
        (project / ".env").write_text("GOOGLE_ADS_LOGIN_CUSTOMER_ID=444-555-6666\n")
        cfg = ads.resolve_config(project_root=str(project), agency_env=str(agency))
        check("GOOGLE_ADS_LOGIN_CUSTOMER_ID in a client .env supplies the account",
              cfg.customer_id == "4445556666", cfg.customer_id)
        check("the key that supplied the account is recorded",
              cfg.customer_id_key == "GOOGLE_ADS_LOGIN_CUSTOMER_ID")
        check("reading the account out of the manager key is warned about",
              any("GOOGLE_ADS_LOGIN_CUSTOMER_ID" in w and "MANAGER" in w for w in cfg.warnings))
        check("a client-specific value beats the agency default",
              cfg.customer_id != "1112223333")
        check("the agency default is not then also sent as a manager header",
              cfg.login_customer_id is None, cfg.login_customer_id)
        check("a resolvable account is not a blocking problem", not cfg.problems, cfg.problems)

        # -- falling back to the SHARED value works but must be loud: it is the
        #    agency-wide default and almost certainly the wrong account
        (project / ".env").write_text("")
        cfg = ads.resolve_config(project_root=str(project), agency_env=str(agency))
        check("with no client config, the shared login value becomes the account",
              cfg.customer_id == "1112223333")
        check("using the shared value as the account warns that it is agency-wide",
              any("SHARED" in w and "wrong account" in w for w in cfg.warnings))

        # -- explicit GOOGLE_ADS_CUSTOMER_ID wins, and the manager header returns
        (project / ".env").write_text(
            "GOOGLE_ADS_CUSTOMER_ID=444-555-6666\nGOOGLE_ADS_API_VERSION=v21\n")
        cfg = ads.resolve_config(project_root=str(project), agency_env=str(agency))
        check("explicit GOOGLE_ADS_CUSTOMER_ID supplies the account",
              cfg.customer_id == "4445556666" and cfg.customer_id_key == "GOOGLE_ADS_CUSTOMER_ID")
        check("a distinct manager account is sent as the login header",
              cfg.login_customer_id == "1112223333")
        check("configuration with everything present has no problems", not cfg.problems, cfg.problems)
        check("pinned API version is honoured", cfg.api_version == "v21")

        # -- a client with its own manager overrides the agency's
        (project / ".env").write_text(
            "GOOGLE_ADS_CUSTOMER_ID=444-555-6666\nGOOGLE_ADS_LOGIN_CUSTOMER_ID=999-888-7777\n")
        cfg = ads.resolve_config(project_root=str(project), agency_env=str(agency))
        check("client overrides the agency manager account",
              cfg.login_customer_id == "9998887777")
        check("the account itself is unaffected by the manager override",
              cfg.customer_id == "4445556666")

        # -- a malformed customer ID is caught before any API call
        (project / ".env").write_text("GOOGLE_ADS_CUSTOMER_ID=12345\n")
        cfg = ads.resolve_config(project_root=str(project), agency_env=str(agency))
        check("a short customer ID is rejected with a readable message",
              any("10 digits" in x for x in cfg.problems))

        # -- the same ID in both slots: query it directly, send no manager header
        (project / ".env").write_text(
            "GOOGLE_ADS_CUSTOMER_ID=1112223333\nGOOGLE_ADS_LOGIN_CUSTOMER_ID=1112223333\n")
        cfg = ads.resolve_config(project_root=str(project), agency_env=str(agency))
        check("an account equal to the login ID is queried directly, with no header",
              cfg.customer_id == "1112223333" and cfg.login_customer_id is None)
        check("querying an ID that is also the login value is warned about",
              any("same ID" in w for w in cfg.warnings))

        # -- CLI overrides beat every file
        cfg = ads.resolve_config(project_root=str(project), agency_env=str(agency),
                                 customer_id="777-777-7777")
        check("--customer-id wins over the client .env", cfg.customer_id == "7777777777")

        # -- secrets never appear in the describable configuration
        cfg = ads.resolve_config(project_root=str(project), agency_env=str(agency),
                                 customer_id="7777777777")
        blob = json.dumps(ads.describe_config(cfg))
        for secret in ("shh", "1//tok", "devtok"):
            check("secret %r is absent from describe_config output" % secret,
                  secret not in blob)
        check("describe_config reports credentials as present",
              '"GOOGLE_ADS_DEVELOPER_TOKEN": "present"' in blob)


def clean_env():
    for k in list(os.environ):
        if k.startswith("GOOGLE_"):
            del os.environ[k]


# ---------------------------------------------------------------------------
# API error handling, retries, version fallback
# ---------------------------------------------------------------------------

def fake_cfg():
    cfg = ads.Config()
    cfg.client_id, cfg.client_secret = "id", "secret"
    cfg.refresh_token, cfg.developer_token = "refresh", "dev"
    cfg.customer_id, cfg.login_customer_id = "1234567890", "1112223333"
    cfg.api_version = "v99"
    cfg.agency_env_path = "/nowhere/agency.env"
    cfg._token, cfg._token_expires = "cached", float("inf")
    return cfg


def test_api_errors(monkey):
    section("API errors, retries and version negotiation")

    err_permission = json.dumps({"error": {"code": 403, "message": "The caller does not have permission",
        "details": [{"errors": [{"errorCode": {"authorizationError": "USER_PERMISSION_DENIED"},
                                 "message": "User doesn't have permission to access customer."}]}]}})
    err_devtoken = json.dumps({"error": {"code": 403, "message": "denied",
        "details": [{"errors": [{"errorCode": {"authorizationError": "DEVELOPER_TOKEN_NOT_APPROVED"},
                                 "message": "Developer token is not approved."}]}]}})
    err_quota = json.dumps({"error": {"code": 429, "message": "Resource exhausted",
        "details": [{"errors": [{"errorCode": {"quotaError": "RESOURCE_EXHAUSTED"},
                                 "message": "Too many requests."}]}]}})

    cfg = fake_cfg()
    e = ads._classify(403, err_permission, cfg)
    check("permission error is not retryable", not e.retryable)
    check("permission error explains login-customer-id", "MANAGER" in (e.detail or ""))
    check("permission error names the customer being queried", "1234567890" in (e.detail or ""))

    e = ads._classify(403, err_devtoken, cfg)
    check("test-access developer token is explained", "Basic access" in (e.detail or ""))

    e = ads._classify(429, err_quota, cfg)
    check("quota error is retryable", e.retryable)

    e = ads._classify(500, "<html>500</html>", cfg)
    check("a non-JSON 500 is still retryable", e.retryable)

    # -- transient failures are retried, then succeed
    calls = {"n": 0}

    def flaky(url, data, headers, timeout=120):
        calls["n"] += 1
        if calls["n"] < 3:
            return 503, json.dumps({"error": {"code": 503, "message": "backend error"}})
        return 200, json.dumps({"results": [{"metrics": {"clicks": "7"}}]})

    monkey(ads, "_post", flaky)
    monkey(ads.time, "sleep", lambda s: None)
    cfg = fake_cfg()
    rows = ads.gaql(cfg, "SELECT metrics.clicks FROM customer")
    check("a transient 503 is retried until it succeeds", calls["n"] == 3 and len(rows) == 1)

    # -- persistent rate limiting eventually raises, and says it is retryable
    def always_429(url, data, headers, timeout=120):
        return 429, err_quota
    monkey(ads, "_post", always_429)
    cfg = fake_cfg()
    try:
        ads.gaql(cfg, "SELECT metrics.clicks FROM customer", max_attempts=2)
        check("persistent rate limiting raises", False)
    except ads.ApiError as exc:
        check("persistent rate limiting raises ApiError", True)
        check("the rate-limit error is marked retryable", exc.retryable)

    # -- a sunset API version walks down the ladder rather than dying
    seen = []

    def version_gone(url, data, headers, timeout=120):
        version = url.split("/")[3]
        seen.append(version)
        if version != "v21":
            return 404, json.dumps({"error": {"code": 404, "message":
                "Method not found. Requested version was not found."}})
        return 200, json.dumps({"results": []})

    monkey(ads, "_post", version_gone)
    cfg = fake_cfg()
    cfg.api_version = ads.CANDIDATE_VERSIONS[0]
    ads.gaql(cfg, "SELECT metrics.clicks FROM customer")
    check("a sunset API version falls back to a live one", cfg.api_version == "v21", seen)
    check("the version switch is recorded as a warning",
          any("not available" in w for w in cfg.warnings))

    # -- pagination
    pages = {"n": 0}

    def paged(url, data, headers, timeout=120):
        pages["n"] += 1
        if pages["n"] == 1:
            return 200, json.dumps({"results": [{"a": 1}], "nextPageToken": "tok"})
        return 200, json.dumps({"results": [{"a": 2}]})

    monkey(ads, "_post", paged)
    cfg = fake_cfg()
    rows = ads.gaql(cfg, "SELECT metrics.clicks FROM customer")
    check("paged responses are followed to the end", len(rows) == 2)

    # -- an expired access token is refreshed once, not looped on
    refreshed = {"n": 0}
    states = {"n": 0}

    def unauthorized_once(url, data, headers, timeout=120):
        states["n"] += 1
        if states["n"] == 1:
            return 401, json.dumps({"error": {"code": 401, "message": "invalid auth"}})
        return 200, json.dumps({"results": []})

    monkey(ads, "_post", unauthorized_once)
    monkey(ads, "get_access_token", lambda cfg, force=False: (
        refreshed.__setitem__("n", refreshed["n"] + (1 if force else 0)) or "token"))
    cfg = fake_cfg()
    ads.gaql(cfg, "SELECT metrics.clicks FROM customer")
    check("a 401 triggers exactly one forced token refresh", refreshed["n"] == 1)


# ---------------------------------------------------------------------------
# Analysis behaviour, fixture by fixture
# ---------------------------------------------------------------------------

def test_healthy():
    section("fixture: healthy account")
    a = load("healthy")
    check("periods are declared and equal length", a["periods"]["comparable"])
    check("every KPI spec appears in the contract", len(a["kpis"]) == len(ap.KPI_SPECS))
    check("ROAS is available when conversion value is recorded",
          kpi(a, "roas")["availability"] == "available")
    check("spend is never given a good/bad verdict",
          kpi(a, "cost")["verdict"] == "ambiguous")
    check("conversion growth is recorded as a strength",
          any(f["id"] == "conversions_shift" for f in a["findings"]["strengths"]))
    check("all four campaigns are compared", len(a["campaigns"]) == 4)
    check("the KPI table renders", a["tables"]["kpi"].count("\n") >= 5)
    check("the campaign table renders", "Search — Brand" in a["tables"]["campaigns"])
    check("impression share is weighted, not averaged",
          abs(kpi(a, "search_impression_share")["current"] - 54.25) < 0.5,
          kpi(a, "search_impression_share")["current"])
    check("impression-share coverage is disclosed",
          a["impression_share_coverage"]["campaigns_reporting"] == 2)
    check("a partial impression-share picture raises a warning",
          any("impression share covers" in w for w in a["data_quality"]["warnings"]))
    check("every recommendation carries evidence",
          all(r["evidence"] for r in a["recommended_actions"]))
    check("every recommendation carries a priority",
          all(r["priority"] in ("High", "Medium", "Low") for r in a["recommended_actions"]))
    check("a Display campaign is not told to audit search terms",
          not any("search-term" in r["action"] and "Display" in r["action"]
                  for r in a["recommended_actions"]))


def test_no_conversions():
    section("fixture: account with no conversions")
    a = load("no-conversions")
    check("CPA is unavailable rather than zero",
          kpi(a, "cost_per_conversion")["availability"] == "unavailable")
    check("CPA is not rendered as a number in the KPI table",
          "| CPA |" not in a["tables"]["kpi"])
    check("zero conversions with spend is raised as an anomaly",
          any(f["id"] == "no_conversions_recorded" for f in a["findings"]["anomalies"]))
    check("the anomaly refuses to say whether tracking is broken",
          any("distinguishes the two" in f["statement"]
              for f in a["findings"]["anomalies"] if f["id"] == "no_conversions_recorded"))
    check("verifying tracking is the top recommendation",
          a["recommended_actions"] and a["recommended_actions"][0]["priority"] == "High")
    check("conversions are reported as an explicit zero, not as missing",
          kpi(a, "conversions")["current"] == 0
          and kpi(a, "conversions")["availability"] == "available")


def test_no_conversion_value():
    section("fixture: conversions without value")
    a = load("no-conversion-value")
    check("conversion value is unavailable",
          kpi(a, "conversions_value")["availability"] == "unavailable")
    check("ROAS is unavailable, not 0.00", kpi(a, "roas")["availability"] == "unavailable")
    check("neither appears in the KPI table",
          "ROAS" not in a["tables"]["kpi"] and "Conversion value" not in a["tables"]["kpi"])
    check("both are listed as unavailable metrics",
          {"ROAS", "Conversion value"} <=
          {u["metric"] for u in a["data_quality"]["unavailable_metrics"]})
    check("the conversion decline is still reported",
          any(f["id"] == "conversions_shift" for f in a["findings"]["weaknesses"]))


def test_zero_previous():
    section("fixture: comparison period of zeros")
    a = load("zero-previous")
    conv = kpi(a, "conversions")
    check("percent change against zero is undefined, not infinite",
          conv["percent_change"] is None)
    check("the verdict for a zero baseline is 'new'", conv["verdict"] == "new")
    check("the reason is spelled out",
          any("undefined" in n for n in conv["notes"]))
    check("the absolute change is still reported", conv["absolute_change"] == 22)
    check("the KPI table prints n/a rather than a percentage",
          "n/a (from zero)" in a["tables"]["kpi"])
    check("derived rates with a zero denominator are marked partial",
          kpi(a, "cost_per_conversion")["availability"] == "partial")
    check("no analysis step divided by zero", True)


def test_sparse():
    section("fixture: sparse data and a paused campaign")
    a = load("sparse")
    check("the account is flagged as too small to conclude from",
          any(i["scope"] == "account" for i in a["data_quality"]["insufficient_data"]))
    check("sparse campaigns are named individually",
          any(i["scope"] == "campaign" for i in a["data_quality"]["insufficient_data"]))
    check("no campaign finding on a sparse campaign claims high severity",
          all(f["severity"] != "high"
              for group in a["findings"].values() for f in group
              if f.get("scope") == "campaign"))
    check("a paused campaign that spent is called out",
          any(f["id"].startswith("campaign_paused_but_spent")
              for f in a["findings"]["observations"]))
    check("small samples reduce confidence on conversion-derived findings",
          all(f["confidence"] in ("low", "medium")
              for group in a["findings"].values() for f in group
              if f["id"] in ("cpa_shift", "roas_shift", "conversion_rate_shift")))


def test_partial_failure():
    section("fixture: failed queries and missing metrics")
    a = load("partial-failure")
    check("query failures survive into data quality",
          len(a["data_quality"]["errors"]) == 2)
    check("a failed query is described as unavailable, not empty",
          any("unavailable, not empty" in w for w in a["data_quality"]["warnings"]))
    check("impression share is unavailable for a Performance Max account",
          kpi(a, "search_impression_share")["availability"] == "unavailable")
    check("impression-share rows are absent from the KPI table",
          "Search impression share" not in a["tables"]["kpi"])
    check("core KPIs still report", kpi(a, "cost")["availability"] == "available")
    check("no conversion-action findings are invented when the query failed",
          not any(f["scope"] == "tracking" and f["id"] == "inactive_conversion_actions"
                  for group in a["findings"].values() for f in group))


def test_placeholder_value():
    section("fixture: placeholder conversion value")
    a = load("placeholder-value")
    check("a flat per-conversion value is flagged",
          any(f["id"] == "placeholder_conversion_value" for f in a["findings"]["anomalies"]))
    check("the flag explains what it does to ROAS",
          any("restatement of conversion volume" in f["statement"]
              for f in a["findings"]["anomalies"]))


def test_invariants():
    section("invariants across every fixture")
    for name in sorted(p.name.replace("_raw.json", "") for p in FIXTURES.glob("*_raw.json")):
        a = load(name)
        table = a["tables"]["kpi"] + (a["tables"]["campaigns"] or "")

        unavailable_rendered_as_zero = False
        for k in a["kpis"]:
            if k["availability"] != "available" and k["current"] is None:
                row = "| %s |" % k["label"]
                if row in a["tables"]["kpi"]:
                    unavailable_rendered_as_zero = True
        check("[%s] no unavailable KPI is printed in the table" % name,
              not unavailable_rendered_as_zero)

        check("[%s] percentage change is never computed from a zero baseline" % name,
              all(not (k["previous"] == 0 and k["percent_change"] not in (None, 0.0))
                  for k in a["kpis"]))
        check("[%s] every finding carries evidence" % name,
              all(f["evidence"] for group in a["findings"].values() for f in group))
        check("[%s] every finding declares severity and confidence" % name,
              all(f["severity"] and f["confidence"]
                  for group in a["findings"].values() for f in group))
        check("[%s] recommendations only reference findings that exist" % name,
              {r["from_finding"] for r in a["recommended_actions"]} <=
              {f["id"] for group in a["findings"].values() for f in group})
        check("[%s] the reporting periods are stated" % name,
              a["periods"]["current"]["start"] and a["periods"]["previous"]["end"])
        check("[%s] no NaN or Infinity leaked into the contract" % name,
              "NaN" not in json.dumps(a) and "Infinity" not in json.dumps(a))


def test_charts():
    section("charts")
    import make_charts
    matplotlib, plt, _ = make_charts.load_matplotlib()
    if plt is None:
        check("matplotlib is absent -- charts degrade instead of crashing", True,
              "install matplotlib to test chart rendering")
        return
    with tempfile.TemporaryDirectory() as tmp:
        a = load("healthy")
        a_path = Path(tmp) / "healthy_analysis.json"
        a_path.write_text(json.dumps(a))
        rc = run_module(make_charts, ["--analysis", str(a_path), "--out", str(Path(tmp) / "charts"),
                                      "--update-analysis"])
        check("chart generation succeeds", rc == 0)
        manifest = json.loads((Path(tmp) / "charts" / "healthy_charts.json").read_text())
        drawn = [c for c in manifest if c["status"] == "drawn"]
        check("charts are drawn for a complete account", len(drawn) >= 5, len(drawn))
        check("every drawn chart exists on disk",
              all(Path(c["file"]).is_file() for c in drawn))
        check("every chart has a title and alt text",
              all(c["title"] and c["alt"] for c in drawn))
        check("the manifest is written back into the analysis",
              json.loads(a_path.read_text())["charts"])

        # a Performance Max account has no impression share to draw
        a2 = load("partial-failure")
        a2_path = Path(tmp) / "pmax_analysis.json"
        a2_path.write_text(json.dumps(a2))
        run_module(make_charts, ["--analysis", str(a2_path), "--out", str(Path(tmp) / "charts2")])
        m2 = json.loads((Path(tmp) / "charts2" / "pmax_charts.json").read_text())
        skipped = [c for c in m2 if c["status"] != "drawn"]
        check("an undrawable chart is skipped with a stated reason",
              any(c["id"] == "impression-share" and c.get("reason") for c in skipped))


def test_fetch(monkey):
    """The retrieval script end to end, against a mocked transport.

    fetch_google_ads.py is the one script that cannot be exercised by the
    fixtures -- the fixtures are its output. So the transport is mocked and the
    script is run for real: its date arithmetic, its query construction, its
    dataset assembly and its failure handling all execute."""
    section("retrieval against a mocked API")
    import datetime as dt
    import fetch_google_ads as fetch

    seen_queries = []

    def fake_post(url, data, headers, timeout=120):
        body = json.loads(data.decode("utf-8"))
        q = " ".join(body["query"].split())
        seen_queries.append((url, q, dict(headers)))

        if "FROM customer" in q and "segments.date" not in q:
            return 200, json.dumps({"results": [{"customer": {
                "id": "1234567890", "descriptiveName": "Mocked Account",
                "currencyCode": "GBP", "timeZone": "Europe/London",
                "manager": False, "testAccount": False, "status": "ENABLED",
                "autoTaggingEnabled": True, "optimizationScore": 0.8}}]})
        if "FROM search_term_view" in q:
            # one optional dataset always fails, so the partial path is covered
            return 403, json.dumps({"error": {"code": 403, "message": "denied", "details": [
                {"errors": [{"errorCode": {"authorizationError": "USER_PERMISSION_DENIED"},
                             "message": "No access to this report."}]}]}})
        if "FROM campaign" in q:
            return 200, json.dumps({"results": [{
                "campaign": {"id": "11", "name": "Search — Brand", "status": "ENABLED",
                             "advertisingChannelType": "SEARCH",
                             "biddingStrategyType": "MAXIMIZE_CONVERSIONS"},
                "campaignBudget": {"amountMicros": "40000000"},
                "metrics": {"impressions": "1000", "clicks": "100",
                            "costMicros": "50000000", "conversions": 10.0,
                            "conversionsValue": 500.0,
                            "searchImpressionShare": 0.5,
                            "searchBudgetLostImpressionShare": 0.2,
                            "searchRankLostImpressionShare": 0.3}}]})
        if "segments.date" in q:
            return 200, json.dumps({"results": [{
                "segments": {"date": "2026-08-01"},
                "metrics": {"impressions": "40", "clicks": "4", "costMicros": "2000000",
                            "conversions": 1.0}}]})
        return 200, json.dumps({"results": []})

    monkey(ads, "_post", fake_post)
    monkey(ads, "get_access_token", lambda cfg, force=False: "access-token")
    monkey(ads.time, "sleep", lambda s: None)

    with tempfile.TemporaryDirectory() as tmp:
        tmp = Path(tmp)
        agency = tmp / "agency.env"
        agency.write_text("GOOGLE_CLIENT_ID=a\nGOOGLE_CLIENT_SECRET=b\n"
                          "GOOGLE_REFRESH_TOKEN=c\nGOOGLE_ADS_DEVELOPER_TOKEN=d\n")
        project = tmp / "client"
        project.mkdir()
        clean_env()

        # -- no account named anywhere: blocked before a single call
        rc = run_module(fetch, ["--project-root", str(project), "--agency-env", str(agency),
                                "--out", str(tmp / "out")])
        check("fetch refuses to run without an account to report on", rc == 2)
        check("fetch made no API call while misconfigured", not seen_queries)

        # the agency's manager account, plus this client's own account
        agency.write_text("GOOGLE_CLIENT_ID=a\nGOOGLE_CLIENT_SECRET=b\n"
                          "GOOGLE_REFRESH_TOKEN=c\nGOOGLE_ADS_DEVELOPER_TOKEN=d\n"
                          "GOOGLE_ADS_LOGIN_CUSTOMER_ID=1112223333\n")
        (project / ".env").write_text("GOOGLE_ADS_CUSTOMER_ID=1234567890\n")
        rc = run_module(fetch, ["--project-root", str(project), "--agency-env", str(agency),
                                "--out", str(tmp / "out"), "--quiet"])
        check("a run with one failed optional dataset exits 1 (partial)", rc == 1, rc)

        files = list((tmp / "out").glob("*_raw.json"))
        check("exactly one raw file is written", len(files) == 1, files)
        raw = json.loads(files[0].read_text())

        check("the raw file is named for the account and the period",
              files[0].name.startswith("1234567890_"), files[0].name)
        check("the account is described from the API, not from config",
              raw["account"]["name"] == "Mocked Account")
        check("the account currency is carried through", raw["account"]["currency"] == "GBP")

        cur, prev = raw["periods"]["current"], raw["periods"]["previous"]
        today = dt.datetime.now().date()
        check("the current period is 30 days", cur["days"] == 30)
        check("the comparison period is 30 days", prev["days"] == 30)
        check("the current period ends yesterday, not today",
              dt.date.fromisoformat(cur["end"]) < today, cur["end"])
        check("the periods are contiguous with no gap and no overlap",
              dt.date.fromisoformat(prev["end"]) + dt.timedelta(days=1)
              == dt.date.fromisoformat(cur["start"]))
        check("the window says how it was chosen", "completed days" in raw["periods"]["basis"])
        check("the window is computed in the account time zone",
              "Europe/London" in raw["periods"]["basis"], raw["periods"]["basis"])

        check("the login-customer-id header is sent",
              all(h.get("login-customer-id") == "1112223333" for _u, _q, h in seen_queries))
        check("the request URL targets the customer being reported on",
              all("/customers/1234567890/" in u for u, _q, _h in seen_queries))
        check("both periods were queried for campaigns",
              sum(1 for _u, q, _h in seen_queries if "FROM campaign" in q and "segments.date" in q) >= 2)

        check("the failed optional dataset is recorded as an error",
              any(e["dataset"].startswith("search_terms") for e in raw["errors"]))
        check("the failed dataset is null, not an empty list",
              raw["datasets"]["search_terms"]["current"] is None)
        check("a failed optional dataset does not fail the run",
              raw["datasets"]["campaigns"]["current"])
        check("no secret is written into the raw file",
              not any(s in json.dumps(raw) for s in ("access-token", "GOOGLE_REFRESH_TOKEN=c")))

        # -- the analysis half accepts what retrieval actually produced
        raw["_source_path"] = str(files[0])
        a = ap.build(raw)
        check("the analysis consumes a real retrieval file",
              a["account"]["name"] == "Mocked Account")
        check("a failed retrieval query surfaces in data quality",
              any("unavailable, not empty" in w for w in a["data_quality"]["warnings"]))

        # -- an inaccessible account stops the run
        def denied(url, data, headers, timeout=120):
            return 403, json.dumps({"error": {"code": 403, "message": "denied", "details": [
                {"errors": [{"errorCode": {"authorizationError": "USER_PERMISSION_DENIED"},
                             "message": "User doesn't have permission."}]}]}})
        monkey(ads, "_post", denied)
        rc = run_module(fetch, ["--project-root", str(project), "--agency-env", str(agency),
                                "--out", str(tmp / "out2"), "--quiet"])
        check("an inaccessible account exits 3, not 0 or 1", rc == 3, rc)
        check("no raw file is written for an inaccessible account",
              not list((tmp / "out2").glob("*_raw.json")) or
              not json.loads(list((tmp / "out2").glob("*_raw.json"))[0].read_text())["datasets"])


def run_module(module, argv):
    """Run a script's main() in-process with its output captured -- including
    stderr, which is where these scripts put their human-readable diagnostics."""
    old = (sys.argv, sys.stdout, sys.stderr)
    sys.argv = [module.__name__] + argv
    sys.stdout, sys.stderr = io.StringIO(), io.StringIO()
    try:
        return module.main()
    finally:
        sys.argv, sys.stdout, sys.stderr = old


# ---------------------------------------------------------------------------

def main():
    ap_ = argparse.ArgumentParser(description="Run the reports-google-ads test suite.")
    ap_.add_argument("--verbose", action="store_true")
    args = ap_.parse_args()

    patches = []

    def monkey(obj, name, value):
        patches.append((obj, name, getattr(obj, name)))
        setattr(obj, name, value)

    if not FIXTURES.exists() or not list(FIXTURES.glob("*_raw.json")):
        print("No fixtures found. Run: python3 make_fixtures.py", file=sys.stderr)
        return 1

    try:
        test_config()
        test_api_errors(monkey)
        test_fetch(monkey)
        test_healthy()
        test_no_conversions()
        test_no_conversion_value()
        test_zero_previous()
        test_sparse()
        test_partial_failure()
        test_placeholder_value()
        test_invariants()
        test_charts()
    finally:
        for obj, name, original in reversed(patches):
            setattr(obj, name, original)

    failed = [r for r in RESULTS if r[1] is False]
    passed = [r for r in RESULTS if r[1] is True]
    for name, ok, detail in RESULTS:
        if ok is None:
            if args.verbose:
                print("\n%s" % name)
        elif ok:
            if args.verbose:
                print("  pass  %s" % name)
        else:
            print("  FAIL  %s%s" % (name, ("  [%s]" % detail) if detail else ""))

    print("\n%d passed, %d failed" % (len(passed), len(failed)))
    return 1 if failed else 0


if __name__ == "__main__":
    sys.exit(main())
