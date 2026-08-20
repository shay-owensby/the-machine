#!/usr/bin/env python3
"""
The skill's own test suite. No network, no credentials, no quota.

    python3 run_tests.py            # everything
    python3 run_tests.py --verbose  # name every passing case too

Covers the cases that break Search Console reports rather than the cases that
break code: missing credentials, a property the identity cannot read, a
comparison period that does not exist, a query extract that hit the row cap, a
property whose CTR fell while its rankings held, and the standing trap of
average position, where the arithmetic sign and the verdict point in opposite
directions.

The HTTP layer is exercised by substituting `gsc_common._http`, so pagination,
retries, token refresh and error classification are all tested without a
network.

Exit code 0 all passed, 1 one or more failed.
"""

import argparse
import json
import os
import sys
import tempfile
from datetime import date
from pathlib import Path

import gsc_common as gsc
import analyze_search_performance as asp

HERE = Path(__file__).resolve().parent
FIXTURES = HERE.parent / "assets" / "fixtures"

RESULTS = []


def check(name, condition, detail=""):
    RESULTS.append((name, bool(condition), detail))
    return bool(condition)


def section(title):
    RESULTS.append((("== %s" % title), None, ""))


def load(fixture):
    path = FIXTURES / ("%s_raw.json" % fixture)
    raw = json.loads(path.read_text())
    raw["_source_path"] = str(path)
    return asp.build(raw)


def kpi(analysis, key):
    return analysis["kpis_by_key"][key]


def clean_env():
    for key in gsc.SECRET_KEYS + gsc.NON_SECRET_KEYS + ("AGENCY_ENV",):
        os.environ.pop(key, None)


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

        clean_env()
        cfg = gsc.resolve_config(project_root=str(project), agency_env=str(agency))
        check("missing agency.env is a blocking problem", cfg.problems)
        check("missing agency.env names the file it wanted",
              any(str(agency) in p for p in cfg.problems))

        agency.write_text(
            "GOOGLE_CLIENT_ID=abc.apps.googleusercontent.com\n"
            "# a comment\n"
            "export GOOGLE_CLIENT_SECRET='shh'\n"
        )
        cfg = gsc.resolve_config(project_root=str(project), agency_env=str(agency))
        check("quoted and export-prefixed values parse",
              cfg.client_secret == "shh" and cfg.client_id.startswith("abc"))
        check("missing refresh token blocks the run",
              any("No usable Google credentials" in p for p in cfg.problems))

        agency.write_text(
            "GOOGLE_CLIENT_ID=abc.apps.googleusercontent.com\n"
            "GOOGLE_CLIENT_SECRET=shh\n"
            "GOOGLE_REFRESH_TOKEN=1//token\n"
        )
        cfg = gsc.resolve_config(project_root=str(project), agency_env=str(agency))
        check("no GSC_SITE_URL is a blocking problem",
              any("No Search Console property" in p for p in cfg.problems))
        check("the missing-property message names the client .env, not the agency file",
              any(str(project / ".env") in p for p in cfg.problems))
        check("credentials alone resolve the oauth method", cfg.auth_method == "oauth_user")

        (project / ".env").write_text("GSC_SITE_URL=https://www.example.com\n")
        cfg = gsc.resolve_config(project_root=str(project), agency_env=str(agency))
        check("client .env supplies the property", cfg.ok, str(cfg.problems))
        check("a URL-prefix property gains its trailing slash",
              cfg.site_url == "https://www.example.com/")
        check("property type is url_prefix", cfg.property_type == "url_prefix")

        (project / ".env").write_text(
            "GSC_SITE_URL=SC-Domain:Example.com\n"
            "GSC_BRAND_TERMS=Example Brand, examplebrand ,exmaple brand\n"
            "GSC_PRIMARY_COUNTRY=usa\n"
            "GSC_REPORT_DAYS=28\n"
            "GSC_SEARCH_TYPE=image\n"
            "GSC_EXTRA_SEARCH_TYPES=news,nonsense\n"
        )
        cfg = gsc.resolve_config(project_root=str(project), agency_env=str(agency))
        check("a domain property normalises its prefix and host",
              cfg.site_url == "sc-domain:example.com")
        check("property type is domain", cfg.property_type == "domain")
        check("brand terms split and strip, misspellings included",
              cfg.brand_terms == ["Example Brand", "examplebrand", "exmaple brand"])
        check("primary country accepted", cfg.primary_country == "usa")
        check("report days honoured", cfg.report_days == 28)
        check("search type honoured", cfg.search_type == "image")
        check("valid extra search type kept", "news" in cfg.extra_search_types)
        check("invalid extra search type dropped with a warning",
              "nonsense" not in cfg.extra_search_types
              and any("nonsense" in w for w in cfg.warnings))

        cfg = gsc.resolve_config(project_root=str(project), agency_env=str(agency),
                                 site_url="https://blog.example.com/")
        check("CLI --site-url overrides the client .env",
              cfg.site_url == "https://blog.example.com/")

        (project / ".env").write_text("GSC_SITE_URL=example.com\n")
        cfg = gsc.resolve_config(project_root=str(project), agency_env=str(agency))
        check("a bare hostname is rejected rather than guessed",
              any("not a Search Console property identifier" in p for p in cfg.problems))
        check("the rejection offers both property forms",
              any("sc-domain:example.com" in p and "https://example.com/" in p
                  for p in cfg.problems))

        # A refresh token minted specifically for Search Console wins over the
        # shared one, which may only carry the Ads scope.
        agency.write_text(
            "GOOGLE_CLIENT_ID=abc\nGOOGLE_CLIENT_SECRET=shh\n"
            "GOOGLE_REFRESH_TOKEN=ads-token\nGSC_REFRESH_TOKEN=gsc-token\n"
        )
        (project / ".env").write_text("GSC_SITE_URL=sc-domain:example.com\n")
        cfg = gsc.resolve_config(project_root=str(project), agency_env=str(agency))
        check("a GSC-specific refresh token takes precedence",
              cfg.refresh_token == "gsc-token")

        clean_env()


def test_secrets_never_printed():
    section("secrets")
    with tempfile.TemporaryDirectory() as tmp:
        tmp = Path(tmp)
        agency = tmp / "agency.env"
        project = tmp / "client"
        project.mkdir()
        agency.write_text(
            "GOOGLE_CLIENT_ID=SECRET-CLIENT-ID\n"
            "GOOGLE_CLIENT_SECRET=SECRET-CLIENT-SECRET\n"
            "GOOGLE_REFRESH_TOKEN=SECRET-REFRESH-TOKEN\n"
        )
        (project / ".env").write_text("GSC_SITE_URL=sc-domain:example.com\n")
        clean_env()
        cfg = gsc.resolve_config(project_root=str(project), agency_env=str(agency))
        rendered = json.dumps(gsc.describe_config(cfg))
        for secret in ("SECRET-CLIENT-ID", "SECRET-CLIENT-SECRET", "SECRET-REFRESH-TOKEN"):
            check("describe_config() does not leak %s" % secret.split("-", 1)[1].lower(),
                  secret not in rendered)
        check("credentials render as present", '"GOOGLE_CLIENT_ID": "present"' in rendered)
        check("the property itself is safe to print", "sc-domain:example.com" in rendered)
        clean_env()


# ---------------------------------------------------------------------------
# The HTTP layer, without HTTP
# ---------------------------------------------------------------------------

class FakeHttp(object):
    """Substitutes gsc_common._http. Queue up (status, body) pairs; token
    requests are answered automatically so tests only describe API calls."""

    def __init__(self, responses):
        self.responses = list(responses)
        self.calls = []
        self.token_calls = 0

    def __call__(self, url, data=None, headers=None, method=None, timeout=120):
        if "oauth2.googleapis.com" in url:
            self.token_calls += 1
            return 200, json.dumps({"access_token": "at-%d" % self.token_calls,
                                    "expires_in": 3600})
        body = json.loads(data.decode("utf-8")) if data else None
        self.calls.append({"url": url, "body": body, "headers": headers})
        if not self.responses:
            raise AssertionError("FakeHttp ran out of responses for %s" % url)
        return self.responses.pop(0)


def fake_cfg(site_url="https://www.example.com/"):
    cfg = gsc.Config()
    cfg.client_id = "id"
    cfg.client_secret = "secret"
    cfg.refresh_token = "token"
    cfg.auth_method = "oauth_user"
    cfg.site_url = site_url
    cfg.property_type = gsc.property_type(site_url)
    cfg.agency_env_path = "/nowhere/agency.env"
    return cfg


def sa_rows(n, start=0):
    return json.dumps({"rows": [
        {"keys": ["query %d" % (start + i)], "clicks": 10, "impressions": 100,
         "ctr": 0.1, "position": 5.0}
        for i in range(n)
    ]})


def with_http(fake, fn):
    original = gsc._http
    gsc._http = fake
    try:
        return fn()
    finally:
        gsc._http = original


def test_api_layer():
    section("API layer: pagination, retries, errors")

    # -- pagination ---------------------------------------------------------
    fake = FakeHttp([(200, sa_rows(3)), (200, sa_rows(3, 3)), (200, sa_rows(1, 6))])
    cfg = fake_cfg()
    rows, meta = with_http(fake, lambda: gsc.search_analytics(
        cfg, "2026-07-18", "2026-08-16", dimensions=["query"], row_limit=3))
    check("pagination follows full pages to the end", len(rows) == 7, "%d rows" % len(rows))
    check("pagination advances startRow",
          [c["body"]["startRow"] for c in fake.calls] == [0, 3, 6])
    check("pagination records how many requests it made", meta["pages_fetched"] == 3)
    check("a complete extract is marked complete", meta["complete"] and not meta["truncated"])

    # -- the row cap --------------------------------------------------------
    fake = FakeHttp([(200, sa_rows(3)), (200, sa_rows(3, 3))])
    rows, meta = with_http(fake, lambda: gsc.search_analytics(
        cfg, "2026-07-18", "2026-08-16", dimensions=["query"], row_limit=3, max_rows=5))
    check("max_rows stops paging", len(rows) == 6)
    check("hitting the cap is recorded as truncated, not silently ignored",
          meta["truncated"] and not meta["complete"])

    # -- a dimensionless query pages once and only once ---------------------
    fake = FakeHttp([(200, json.dumps({"rows": [
        {"clicks": 100, "impressions": 5000, "ctr": 0.02, "position": 8.4}]}))])
    rows, meta = with_http(fake, lambda: gsc.search_analytics(
        cfg, "2026-07-18", "2026-08-16", dimensions=[], row_limit=1))
    check("a dimensionless query returns one row and stops",
          len(rows) == 1 and meta["pages_fetched"] == 1)
    check("property totals come back as numbers, not strings",
          rows[0]["clicks"] == 100 and rows[0]["position"] == 8.4)

    # -- zero rows is data, not an error ------------------------------------
    fake = FakeHttp([(200, json.dumps({}))])
    rows, meta = with_http(fake, lambda: gsc.search_analytics(
        cfg, "2026-07-18", "2026-08-16", dimensions=["query"]))
    check("a response with no rows returns empty, not an exception", rows == [])

    # -- retries ------------------------------------------------------------
    fake = FakeHttp([(503, json.dumps({"error": {"message": "backendError",
                                                 "errors": [{"reason": "backendError"}]}})),
                     (200, sa_rows(1))])
    original_sleep = gsc.time.sleep
    gsc.time.sleep = lambda s: None
    try:
        rows, _ = with_http(fake, lambda: gsc.search_analytics(
            cfg, "2026-07-18", "2026-08-16", dimensions=["query"]))
        check("a transient 503 is retried and then succeeds", len(rows) == 1)

        fake = FakeHttp([(401, json.dumps({"error": {"message": "Invalid Credentials"}})),
                         (200, sa_rows(1))])
        cfg2 = fake_cfg()
        rows, _ = with_http(fake, lambda: gsc.search_analytics(
            cfg2, "2026-07-18", "2026-08-16", dimensions=["query"]))
        check("a 401 forces one token refresh and retries",
              len(rows) == 1 and fake.token_calls >= 2)

        fake = FakeHttp([(429, json.dumps({"error": {
            "message": "Quota exceeded", "errors": [{"reason": "rateLimitExceeded"}]}}))] * 5)
        cfg3 = fake_cfg()
        try:
            with_http(fake, lambda: gsc.search_analytics(
                cfg3, "2026-07-18", "2026-08-16", dimensions=["query"]))
            check("a persistent 429 eventually raises", False)
        except gsc.ApiError as exc:
            check("a persistent 429 eventually raises", True)
            check("the quota error is marked retryable", exc.retryable)
            check("the quota error explains itself",
                  "rate limit" in (exc.detail or "").lower())
    finally:
        gsc.time.sleep = original_sleep

    # -- error classification ----------------------------------------------
    cases = [
        (403, {"error": {"message": "Google Search Console API has not been used in project "
                                    "123 before or it is disabled.",
                         "errors": [{"reason": "accessNotConfigured"}]}},
         "search console api", "an API-not-enabled 403 points at the Cloud project"),
        (403, {"error": {"message": "User does not have sufficient permission for site "
                                    "'https://www.example.com/'.",
                         "errors": [{"reason": "forbidden"}]}},
         "users and permissions", "a permission 403 points at Search Console's user settings"),
        (404, {"error": {"message": "Requested entity was not found."}},
         "three different properties", "a 404 explains that property identifiers are exact"),
        (400, {"error": {"message": "Invalid dimension combination"}},
         "searchappearance cannot be combined",
         "a 400 names the dimension rules that usually cause it"),
    ]
    for status, body, needle, label in cases:
        err = gsc._classify(status, json.dumps(body), cfg)
        check(label, needle in (err.detail or "").lower(), err.detail)
        check("%s -- and is not retryable" % label.split(" ")[1], not err.retryable
              or status == 429)


def test_auth_errors():
    section("authentication failures")
    cfg = fake_cfg()

    def token_failure(payload):
        def fake(url, data=None, headers=None, method=None, timeout=120):
            return 400, json.dumps(payload)
        original = gsc._http
        gsc._http = fake
        try:
            gsc.get_access_token(cfg, force=True)
            return None
        except gsc.ApiError as exc:
            return exc
        finally:
            gsc._http = original

    exc = token_failure({"error": "invalid_grant"})
    check("invalid_grant is explained, not just reported", exc and "Testing" in exc.message)
    exc = token_failure({"error": "invalid_client"})
    check("invalid_client names the two variables to check",
          exc and "GOOGLE_CLIENT_ID" in exc.message)
    exc = token_failure({"error": "invalid_scope"})
    check("invalid_scope explains that an Ads-only token cannot read Search Console",
          exc and "adwords scope" in exc.message)
    check("the scope message names the GSC-specific override",
          exc and "GSC_REFRESH_TOKEN" in exc.message)


# ---------------------------------------------------------------------------
# Dates
# ---------------------------------------------------------------------------

def test_dates():
    section("latest finalised date and period construction")

    # Search Console lags. The probe must take the newest date the API actually
    # returned, never today minus one.
    final_rows = json.dumps({"rows": [
        {"keys": ["2026-08-%02d" % d], "clicks": 10, "impressions": 100, "ctr": 0.1,
         "position": 5.0} for d in range(10, 17)]})
    fresh_rows = json.dumps({"rows": [
        {"keys": ["2026-08-%02d" % d], "clicks": 10, "impressions": 100, "ctr": 0.1,
         "position": 5.0} for d in range(10, 19)]})
    fake = FakeHttp([(200, final_rows), (200, fresh_rows)])
    cfg = fake_cfg()
    fresh = with_http(fake, lambda: gsc.latest_final_date(cfg, today=date(2026, 8, 19)))
    check("the latest finalised date is discovered, not assumed",
          fresh["latest_final"] == "2026-08-16")
    check("the reporting lag is measured", fresh["lag_days"] == 3)
    check("fresher provisional days are counted separately",
          fresh["fresh_days_available"] == 2)
    check("the finalised probe asks for dataState=final",
          fake.calls[0]["body"]["dataState"] == "final")
    check("the freshness probe asks for dataState=all separately",
          fake.calls[1]["body"]["dataState"] == "all")

    periods = gsc.build_periods("2026-08-16", days=30)
    check("the current period ends on the latest finalised date",
          periods["current"]["end"] == "2026-08-16")
    check("the current period is 30 days", periods["current"]["start"] == "2026-07-18")
    check("the comparison period ends the day before the current one begins",
          periods["previous"]["end"] == "2026-07-17")
    check("the comparison period is the same length",
          periods["previous"]["start"] == "2026-06-18")
    check("the two windows do not overlap",
          periods["previous"]["end"] < periods["current"]["start"])

    lagged = gsc.build_periods("2026-08-16", days=30, lag_days=3)
    check("lag_days moves both windows back together",
          lagged["current"]["end"] == "2026-08-13" and lagged["previous"]["end"] == "2026-07-14")


# ---------------------------------------------------------------------------
# Arithmetic
# ---------------------------------------------------------------------------

def test_arithmetic():
    section("arithmetic that keeps unavailable meaning unavailable")

    check("percentage change from zero is undefined, not infinite",
          gsc.percent_change(50, 0) is None)
    check("percentage change from None is undefined", gsc.percent_change(50, None) is None)
    check("percentage change is signed correctly", gsc.percent_change(120, 100) == 20.0)
    check("safe_div never returns zero for 0/0", gsc.safe_div(0, 0) is None)
    check("summing None with None stays None", gsc.add(None, None) is None)
    check("summing a number with None keeps the number", gsc.add(5, None) == 5)

    rows = [{"position": 3.0, "impressions": 40000}, {"position": 90.0, "impressions": 4}]
    value, weight = gsc.weighted_position(rows)
    check("average position is impression-weighted, not a flat mean",
          value is not None and value < 3.1, str(value))
    check("the weight behind a weighted position is reported", weight == 40004)
    check("a row with no position is skipped rather than counted as zero",
          gsc.weighted_position([{"position": None, "impressions": 100},
                                 {"position": 4.0, "impressions": 100}])[0] == 4.0)

    # Average position: the sign of the change and the verdict must disagree.
    improved = asp.change_record("average_position", "Average position", "position", "lower",
                                 8.0, 12.0, asp.MATERIAL_POSITION)
    check("position 12 -> 8 has a negative arithmetic change",
          improved["absolute_change"] == -4.0)
    check("position 12 -> 8 reads as down", improved["direction"] == "down")
    check("position 12 -> 8 is an IMPROVEMENT", improved["verdict"] == "improved")
    worsened = asp.change_record("average_position", "Average position", "position", "lower",
                                 9.0, 5.0, asp.MATERIAL_POSITION)
    check("position 5 -> 9 is a DECLINE", worsened["verdict"] == "declined")
    check("position 5 -> 9 reads as up", worsened["direction"] == "up")

    tiny = asp.change_record("clicks", "Clicks", "int", "higher", 13, 9,
                             asp.MATERIAL_CLICKS_FLOOR)
    check("a 44% swing on nine clicks is not material", not tiny["material"])
    check("an immaterial move is flat rather than improved", tiny["verdict"] == "flat")
    check("the immaterial move still reports its absolute change",
          tiny["absolute_change"] == 4)

    new = asp.change_record("clicks", "Clicks", "int", "higher", 310, None)
    check("a missing baseline gives verdict new", new["verdict"] == "new")
    check("a missing baseline gives no percentage", new["percent_change"] is None)
    check("a missing baseline says so in its notes",
          any("no percentage change" in n for n in new["notes"]))


# ---------------------------------------------------------------------------
# The fixtures
# ---------------------------------------------------------------------------

def test_healthy():
    section("healthy: growth across the board")
    a = load("healthy")
    check("clicks improved", kpi(a, "clicks")["verdict"] == "improved")
    check("position improving is reported as an improvement",
          kpi(a, "average_position")["verdict"] == "improved"
          and kpi(a, "average_position")["absolute_change"] < 0)
    check("the KPI table marks position as lower-is-better",
          "lower is better" in a["tables"]["kpi"])
    check("both period lengths appear in the KPI table header",
          "Current 30 days" in a["tables"]["kpi"] and "Previous 30 days" in a["tables"]["kpi"])
    check("CTR opportunities were found", a["pages"]["ctr_opportunities"])
    check("a CTR opportunity is judged against this property's own band median",
          all(r.get("band_median_ctr") is not None for r in a["pages"]["ctr_opportunities"]))
    check("a CTR recommendation names a specific page and its numbers",
          any("/blog/widget-buying-guide/" in r["action"] for r in a["recommended_actions"]))
    speculative = [r for r in a["pages"]["ctr_opportunities"] if r["ceiling_is_speculative"]]
    check("an implausible CTR ceiling is flagged rather than quoted flat", speculative)
    check("the flagged ceiling warns it is an upper bound",
          all("upper bound only" in r["caveat"] for r in speculative))
    check("a recommendation built on a speculative ceiling drops to low confidence",
          all(r["confidence"] == "low" for r in a["recommended_actions"]
              if r["from_finding"] == "page_ctr_opportunities"
              and "sceptically" in r["expected_impact"]))
    check("a CTR recommendation separates presentation from ranking",
          any("does not change rankings" in r["expected_impact"]
              or "not move position" in r["expected_impact"]
              for r in a["recommended_actions"]))
    check("ranking opportunities are confined to positions 4-20",
          all(r["band"] in ("4-10", "11-20") for r in a["queries"]["ranking_opportunities"]))
    check("brand split ran because terms are configured", a["brand"] is not None)
    check("the brand split names the configured terms",
          a["brand"]["configured_terms"] == ["examplebrand", "example brand"])
    check("the brand split flags that anonymised queries are missing",
          "anonymised" in a["brand"]["basis"])
    check("cannibalisation is a signal with a caveat, not a diagnosis",
          all("intent" in s["caveat"] for s in a["query_page"]["cannibalisation"]))
    check("search appearance is reported as its own dataset",
          a["search_appearance"] and "cannot be combined" in a["search_appearance"]["note"])
    check("device data carries a negligible flag for tablet",
          any(r["device"] == "TABLET" and r["negligible"] for r in a["devices"]["rows"]))


def test_ctr_decline():
    section("ctr-decline: rankings held, CTR fell")
    a = load("ctr-decline")
    ids = {f["id"] for group in a["findings"].values() for f in group}
    check("the CTR-with-stable-position finding fires", "ctr_down_position_stable" in ids)
    check("clicks falling faster than impressions is called out",
          "clicks_falling_faster" in ids)
    check("the attribution puts the change in CTR, not visibility",
          a["click_attribution"]["dominant_factor"] == "ctr")
    check("the attribution states it is arithmetic, not cause",
          "not an explanation" in a["click_attribution"]["caveat"])
    check("position is NOT blamed", kpi(a, "average_position")["verdict"] == "flat")
    check("a recommendation targets presentation rather than rankings",
          any("presentation" in r["reason"].lower() or "title" in r["action"].lower()
              for r in a["recommended_actions"]))
    finding = next(f for group in a["findings"].values() for f in group
                   if f["id"] == "ctr_down_position_stable")
    check("the CTR finding hedges on SERP layout, which GSC cannot see",
          "SERP" in (finding["caveat"] or ""))


def test_visibility_loss():
    section("visibility-loss: impressions gone, one page deindexed")
    a = load("visibility-loss")
    ids = {f["id"] for group in a["findings"].values() for f in group}
    check("page visibility losses are reported separately from click losses",
          "page_visibility_losses" in ids)
    check("losses are classified by kind rather than all called ranking",
          {r["loss_kind"] for r in a["pages"]["visibility_losses"]} - {"unclear"})
    check("an indexing risk is raised from URL Inspection",
          any(i.startswith("indexing:") for i in ids))
    indexing = next(f for f in a["findings"]["risks"] if f["id"].startswith("indexing:"))
    check("the indexing finding separates point-in-time status from the trend",
          "moment of the call" in (indexing["caveat"] or ""))
    check("the indexing recommendation is prioritised High",
          any(r["from_finding"].startswith("indexing:") and r["priority"] == "High"
              for r in a["recommended_actions"]))
    check("a single-day drop is detected", any(x["kind"] == "drop"
                                               for x in a["trend"]["anomalies"]))
    check("the anomaly is judged against a like-for-like weekday baseline",
          all("typical" in x["baseline"] for x in a["trend"]["anomalies"]))


def test_zero_previous():
    section("zero-previous: a property with no comparison period")
    a = load("zero-previous")
    for key in ("clicks", "impressions", "ctr", "average_position"):
        k = kpi(a, key)
        check("%s reports no percentage change against an absent baseline" % key,
              k["percent_change"] is None)
        check("%s still reports its current-period value" % key, k["current"] is not None)
        check("%s is marked new rather than improved" % key, k["verdict"] == "new")
    ids = {f["id"] for group in a["findings"].values() for f in group}
    check("the missing baseline is stated as a finding", "no_baseline" in ids)
    finding = next(f for f in a["findings"]["observations"] if f["id"] == "no_baseline")
    check("the finding forbids calling it growth", "not describe this as growth"
          in (finding["caveat"] or ""))
    check("the KPI table says n/a rather than printing a zero baseline",
          "n/a (previous period was zero)" in a["tables"]["kpi"])
    check("no KPI row shows a previous value of 0",
          "| 0 |" not in a["tables"]["kpi"])


def test_low_traffic():
    section("low-traffic: a property too small for percentages")
    a = load("low-traffic")
    check("a 46% click swing on six clicks is not called material",
          not kpi(a, "clicks")["material"])
    check("the small sample is recorded in data quality",
          a["data_quality"]["insufficient_data"])
    check("the sample-size check warns rather than passing",
          any(c["check"] == "sample size" and c["status"] == "warn"
              for c in a["data_quality"]["checks"]))
    check("no high-severity finding is asserted on this volume",
          not any(f["severity"] == "high"
                  for group in a["findings"].values() for f in group))


def test_truncated():
    section("truncated: the query extract hit the row cap")
    a = load("truncated")
    check("the row cap surfaces as a warning",
          any("cap" in w.lower() for w in a["data_quality"]["warnings"]))
    check("the completeness check warns rather than passing",
          any(c["check"] == "queries complete" and c["status"] == "warn"
              for c in a["data_quality"]["checks"]))
    check("a recommendation exists to re-run the extract in slices",
          any("chunk-days" in r["action"] for r in a["recommended_actions"]))
    check("the truncation recommendation says the KPIs are unaffected",
          any("chunk-days" in r["action"] and "KPI" in r["expected_impact"]
              for r in a["recommended_actions"]))
    check("a flat property is described as flat rather than left silent",
          any(f["id"] == "broadly_flat" for f in a["findings"]["observations"]))


def test_partial():
    section("partial: two datasets failed to retrieve")
    a = load("partial")
    check("search appearance is unavailable, not empty", a["search_appearance"] is None)
    check("countries are unavailable, not empty", a["countries"] is None)
    check("the failures are named in the warnings",
          any("search_appearance" in w for w in a["data_quality"]["warnings"]))
    check("the warning says unavailable rather than empty",
          any("unavailable, not empty" in w for w in a["data_quality"]["warnings"]))
    check("the failures are carried through as errors",
          len(a["data_quality"]["errors"]) == 2)
    check("core KPIs still report", kpi(a, "clicks")["availability"] == "available")
    check("no country or appearance table was rendered",
          not a["tables"].get("countries") and not a["tables"].get("search_appearance"))
    check("no brand split without configured terms", a["brand"] is None)
    check("the missing brand split explains what would enable it",
          "GSC_BRAND_TERMS" in a["brand_note"])


def test_domain_property():
    section("domain-property: a domain property with a second search type")
    a = load("domain-property")
    check("the property type is recognised as domain",
          a["property"]["property_type"] == "domain")
    check("image search is kept as its own dataset", "image" in a["extra_search_types"])
    check("the second search type warns against adding it to the totals",
          "never be added" in a["extra_search_types"]["image"]["note"])
    web_clicks = kpi(a, "clicks")["current"]
    image_clicks = next(k["current"] for k in a["extra_search_types"]["image"]["kpis"]
                        if k["key"] == "clicks")
    check("web totals exclude image clicks", web_clicks == 9400 and image_clicks == 1800)
    check("sitemap problems are surfaced", a["sitemaps"]["problems"])
    check("a sitemap that has never been downloaded is flagged",
          any("never been downloaded" in p for p in a["sitemaps"]["problems"]))
    check("sitemap findings stay supplementary",
          "not as a technical SEO audit" in a["sitemaps"]["note"])
    check("a genuine one-day spike is still detected",
          any(x["kind"] == "spike" and x["date"] == "2026-08-02"
              for x in a["trend"]["anomalies"]))
    check("ordinary weekend dips are NOT called anomalies",
          all(x["date"] == "2026-08-02" for x in a["trend"]["anomalies"]))


# ---------------------------------------------------------------------------
# Invariants -- these must hold for every fixture
# ---------------------------------------------------------------------------

def test_invariants():
    section("invariants across every fixture")
    for name in ("healthy", "ctr-decline", "visibility-loss", "zero-previous",
                 "low-traffic", "truncated", "partial", "domain-property"):
        a = load(name)
        blob = json.dumps(a)

        check("%s: no NaN or Infinity reaches the contract" % name,
              "NaN" not in blob and "Infinity" not in blob)

        check("%s: both periods are stated" % name,
              a["periods"]["current"]["start"] and a["periods"]["previous"]["end"])

        check("%s: no percentage change survives a zero baseline" % name,
              all(k["percent_change"] is None
                  for k in a["kpis"] if k["previous"] in (None, 0)))

        check("%s: unavailable KPIs are never printed as numbers" % name,
              all("not available" in a["tables"]["kpi"]
                  for k in a["kpis"] if k["availability"] == "unavailable") or
              not any(k["availability"] == "unavailable" for k in a["kpis"]))

        for group, items in a["findings"].items():
            for f in items:
                check("%s: finding %s carries evidence" % (name, f["id"]), f["evidence"])
                check("%s: finding %s carries severity and confidence" % (name, f["id"]),
                      f["severity"] in ("low", "medium", "high")
                      and f["confidence"] in ("low", "medium", "high"))

        for r in a["recommended_actions"]:
            check("%s: recommendation has every required field" % name,
                  all(r.get(k) for k in ("action", "reason", "evidence", "expected_impact",
                                         "priority")))
            check("%s: recommendation cites a finding" % name, r["from_finding"])
            check("%s: recommendation avoids empty advice" % name,
                  r["action"].strip().lower() not in (
                      "improve seo", "optimise rankings", "write more content",
                      "improve ctr", "fix technical seo"))

        check("%s: the standing Search Console limitations are stated" % name,
              len(a["data_quality"]["limitations"]) >= 4)
        check("%s: clicks are never equated with sessions" % name,
              any("not sessions" in l for l in a["data_quality"]["limitations"]))
        check("%s: the thresholds used are published" % name,
              a["thresholds"]["opportunity_impression_floor"] >= 100)
        check("%s: the CTR benchmark disclaims industry data" % name,
              "No industry benchmark" in a["thresholds"]["ctr_benchmark"])


def test_reconciliation():
    section("dimensional totals versus property totals")
    a = load("healthy")
    recon = a["queries"]["reconciliation"]
    check("query-level clicks are reconciled against the property total",
          recon["dimension_clicks"] < recon["property_clicks"])
    check("the coverage gap is expressed as a percentage",
          0 < recon["coverage_pct"] < 100)
    check("the gap is explained as withheld rows, not missing traffic",
          "withholds rows" in recon["note"])
    check("a coverage gap below 80% raises a warning",
          any("covers" in w and "%" in w for w in a["data_quality"]["warnings"]))


# ---------------------------------------------------------------------------
# End-to-end retrieval, with the network replaced
# ---------------------------------------------------------------------------

class ScriptedApi(object):
    """Answers every Search Console endpoint from a script, so the retrieval
    script can be driven end to end without credentials or a network.

    This is the only test that exercises fetch_search_console.py itself: the
    property check, the freshness probe, the period arithmetic, every dataset
    query, and the raw file it writes.
    """

    def __init__(self, site_url="https://www.example.com/", latest_final="2026-08-16",
                 fail=()):
        self.site_url = site_url
        self.latest_final = latest_final
        self.fail = set(fail)
        self.queries = []

    def __call__(self, url, data=None, headers=None, method=None, timeout=120):
        if "oauth2.googleapis.com" in url:
            return 200, json.dumps({"access_token": "at", "expires_in": 3600})
        if url.endswith("/sites"):
            return 200, json.dumps({"siteEntry": [
                {"siteUrl": self.site_url, "permissionLevel": "siteFullUser"}]})
        if "/searchAnalytics/query" not in url:
            # sites.get for the configured property
            return 200, json.dumps({"siteUrl": self.site_url,
                                    "permissionLevel": "siteFullUser"})
        body = json.loads(data.decode("utf-8"))
        dims = body.get("dimensions") or []
        self.queries.append(body)

        if dims == ["searchAppearance"] and "search_appearance" in self.fail:
            return 400, json.dumps({"error": {
                "message": "Invalid dimension", "errors": [{"reason": "badRequest"}]}})

        if dims == ["date"]:
            last = self.latest_final if body["dataState"] == "final" else "2026-08-18"
            start, end = body["startDate"], body["endDate"]
            days = []
            cursor = date.fromisoformat(start)
            stop = min(date.fromisoformat(end), date.fromisoformat(last))
            while cursor <= stop:
                days.append({"keys": [str(cursor)], "clicks": 400, "impressions": 10000,
                             "ctr": 0.04, "position": 9.5})
                cursor = date.fromisoformat(str(cursor)).toordinal() + 1
                cursor = date.fromordinal(cursor)
            return 200, json.dumps({"rows": days})

        if not dims:
            return 200, json.dumps({"rows": [
                {"clicks": 12000, "impressions": 300000, "ctr": 0.04, "position": 9.5}]})

        key_count = len(dims)
        rows = [{"keys": ["%s-%d" % (dims[0], i)] + ["extra"] * (key_count - 1),
                 "clicks": 100 - i, "impressions": 4000 - i * 10,
                 "ctr": 0.025, "position": 6.0 + i}
                for i in range(5)]
        return 200, json.dumps({"rows": rows})


def test_end_to_end_retrieval():
    section("end-to-end retrieval into a raw file")
    import fetch_search_console as fetch

    with tempfile.TemporaryDirectory() as tmp:
        tmp = Path(tmp)
        agency = tmp / "agency.env"
        agency.write_text("GOOGLE_CLIENT_ID=CRED-CLIENT-ID\n"
                          "GOOGLE_CLIENT_SECRET=CRED-CLIENT-SECRET\n"
                          "GOOGLE_REFRESH_TOKEN=CRED-REFRESH-TOKEN\n")
        project = tmp / "client"
        project.mkdir()
        (project / ".env").write_text("GSC_SITE_URL=https://www.example.com/\n")

        api = ScriptedApi(fail=("search_appearance",))
        clean_env()
        argv = sys.argv
        sys.argv = ["fetch_search_console.py", "--project-root", str(project),
                    "--agency-env", str(agency), "--out", str(tmp / "out")]
        original = gsc._http
        gsc._http = api
        try:
            code = fetch.main()
        finally:
            gsc._http = original
            sys.argv = argv

        check("a run with one failed optional dataset exits 1, not 0 or 3", code == 1,
              "exit %s" % code)

        raw_files = list((tmp / "out").rglob("*_raw.json"))
        check("exactly one raw file is written", len(raw_files) == 1)
        raw = json.loads(raw_files[0].read_text())

        check("the raw file lands in a dated folder named for the last day of data",
              raw_files[0].parent.parent.name == "2026-08-16")
        check("the raw file is named for the property and the period",
              "www-example-com_2026-07-18_2026-08-16" in raw_files[0].name)
        check("the schema is stamped",
              raw["schema"] == "reports-google-search-console/raw@1")

        check("the latest finalised date is discovered from the API",
              raw["freshness"]["latest_final"] == "2026-08-16")
        check("provisional days are found and excluded",
              raw["freshness"]["fresh_days_available"] == 2)
        check("the current period ends on the latest finalised date",
              raw["periods"]["current"]["end"] == "2026-08-16")
        check("the comparison period is adjacent and equal length",
              raw["periods"]["previous"]["end"] == "2026-07-17"
              and raw["periods"]["previous"]["start"] == "2026-06-18")
        check("the basis of the periods is recorded in words",
              "finalised" in raw["periods"]["basis"])

        for dataset in ("totals", "daily", "queries", "pages"):
            check("core dataset %s was retrieved" % dataset, dataset in raw["datasets"])
        check("query+page is retrieved for the current period only",
              list(raw["datasets"]["query_page"].keys()) == ["current"])
        check("the failed dataset is absent rather than empty",
              "search_appearance" not in raw["datasets"])
        check("the failure is recorded with its reason",
              any(e["dataset"] == "search_appearance" for e in raw["errors"]))
        check("the failure is explained as an expected property difference",
              any("not an error in the site" in w for w in raw["warnings"]))

        report_queries = [q for q in api.queries
                          if q["startDate"] >= raw["periods"]["previous"]["start"]
                          and q["endDate"] <= raw["periods"]["current"]["end"]]
        check("every reporting query asked for finalised data only",
              report_queries and all(q["dataState"] == "final" for q in report_queries))
        check("only the freshness probe ever asks for provisional data",
              all(q["dataState"] == "final" or q["dimensions"] == ["date"]
                  for q in api.queries))
        check("every query names the configured search type",
              all(q["type"] == "web" for q in api.queries))
        check("every query stays inside the API row limit",
              all(q["rowLimit"] <= gsc.MAX_ROW_LIMIT for q in api.queries))
        appearance_queries = [q for q in api.queries
                              if q.get("dimensions") == ["searchAppearance"]]
        check("search appearance is queried alone, never combined",
              all(len(q["dimensions"]) == 1 for q in appearance_queries))
        check("the property totals query carries no dimensions",
              any(q["dimensions"] == [] for q in api.queries))

        blob = json.dumps(raw)
        for secret in ("CRED-CLIENT-ID", "CRED-CLIENT-SECRET", "CRED-REFRESH-TOKEN"):
            check("no credential value reaches the raw file (%s)" % secret.lower(),
                  secret not in blob)

        raw["_source_path"] = str(raw_files[0])
        analysis = asp.build(raw)
        check("the analysis builds from a live-shaped raw file",
              analysis["kpis_by_key"]["clicks"]["current"] == 12000)
        check("search appearance is unavailable rather than empty in the analysis",
              analysis["search_appearance"] is None)
        check("the retrieval failure surfaces in data quality",
              any("search_appearance" in w for w in analysis["data_quality"]["warnings"]))


def test_retrieval_stops_on_wrong_property():
    section("retrieval refuses to report on the wrong property")
    import fetch_search_console as fetch

    with tempfile.TemporaryDirectory() as tmp:
        tmp = Path(tmp)
        agency = tmp / "agency.env"
        agency.write_text("GOOGLE_CLIENT_ID=id\nGOOGLE_CLIENT_SECRET=secret\n"
                          "GOOGLE_REFRESH_TOKEN=token\n")
        project = tmp / "client"
        project.mkdir()
        # Configured WITHOUT www; the identity can only read the www property.
        (project / ".env").write_text("GSC_SITE_URL=https://example.com/\n")

        class Denied(ScriptedApi):
            def __call__(self, url, data=None, headers=None, method=None, timeout=120):
                if "oauth2.googleapis.com" in url:
                    return 200, json.dumps({"access_token": "at", "expires_in": 3600})
                if url.endswith("/sites"):
                    return 200, json.dumps({"siteEntry": [
                        {"siteUrl": "https://www.example.com/",
                         "permissionLevel": "siteFullUser"}]})
                if "/searchAnalytics/query" not in url:
                    return 403, json.dumps({"error": {
                        "message": "User does not have sufficient permission for site "
                                   "'https://example.com/'.",
                        "errors": [{"reason": "forbidden"}]}})
                raise AssertionError("no data query should be made for an unreadable property")

        clean_env()
        argv = sys.argv
        sys.argv = ["fetch_search_console.py", "--project-root", str(project),
                    "--agency-env", str(agency), "--out", str(tmp / "out")]
        original = gsc._http
        gsc._http = Denied()
        try:
            code = fetch.main()
        finally:
            gsc._http = original
            sys.argv = argv

        check("an unreadable property stops the run with exit 3", code == 3, "exit %s" % code)
        check("nothing is written when the property check fails",
              not list((tmp / "out").rglob("*_raw.json")) if (tmp / "out").exists() else True)


# ---------------------------------------------------------------------------
# Charts
# ---------------------------------------------------------------------------

def test_charts():
    section("charts")
    try:
        import matplotlib  # noqa: F401
    except ImportError:
        check("matplotlib is available (charts are skipped without it)", True,
              "matplotlib not installed -- chart tests skipped, which is the "
              "documented degraded behaviour")
        return

    import make_charts

    with tempfile.TemporaryDirectory() as tmp:
        tmp = Path(tmp)
        a = load("healthy")
        analysis_path = tmp / "healthy_analysis.json"
        analysis_path.write_text(json.dumps(a))
        argv = sys.argv
        sys.argv = ["make_charts.py", "--analysis", str(analysis_path),
                    "--out", str(tmp / "charts"), "--update-analysis"]
        try:
            code = make_charts.main()
        finally:
            sys.argv = argv
        check("charts draw for a complete property", code == 0)

        updated = json.loads(analysis_path.read_text())
        charts = updated["charts"]
        check("the manifest is written back into the analysis", charts)
        drawn = [c for c in charts if c["status"] == "drawn"]
        check("at least eight charts draw for a complete property", len(drawn) >= 8,
              "%d drawn" % len(drawn))
        check("every drawn chart exists on disk", all(Path(c["file"]).is_file() for c in drawn))
        check("every drawn chart has a title and alt text",
              all(c["title"] and c["alt"] for c in drawn))
        check("every drawn chart says what it is for", all(c["explains"] for c in drawn))
        for c in charts:
            if c["status"] != "drawn":
                check("skipped chart %s explains why" % c["key"], c.get("reason"))

        # A property with no device data must not get an empty device chart.
        b = load("low-traffic")
        analysis_path2 = tmp / "low_analysis.json"
        analysis_path2.write_text(json.dumps(b))
        sys.argv = ["make_charts.py", "--analysis", str(analysis_path2),
                    "--out", str(tmp / "charts2")]
        try:
            make_charts.main()
        finally:
            sys.argv = argv
        manifest = json.loads((tmp / "charts2" / "low_charts.json").read_text())
        device = next(c for c in manifest["charts"] if c["key"] == "device-performance")
        check("a chart with no data is skipped rather than drawn empty",
              device["status"] == "not drawn")
        check("the skipped device chart gives a reason a report can print",
              "not returned" in device["reason"])


# ---------------------------------------------------------------------------

def main():
    ap = argparse.ArgumentParser(description="Run the offline test suite.")
    ap.add_argument("--verbose", action="store_true", help="Name every passing case")
    args = ap.parse_args()

    for test in (test_config, test_secrets_never_printed, test_api_layer, test_auth_errors,
                 test_dates, test_arithmetic, test_healthy, test_ctr_decline,
                 test_visibility_loss, test_zero_previous, test_low_traffic, test_truncated,
                 test_partial, test_domain_property, test_invariants, test_reconciliation,
                 test_end_to_end_retrieval, test_retrieval_stops_on_wrong_property,
                 test_charts):
        try:
            test()
        except Exception as exc:  # a crash is a failure, not a stack trace
            RESULTS.append(("%s CRASHED: %r" % (test.__name__, exc), False, ""))

    passed = [r for r in RESULTS if r[1] is True]
    failed = [r for r in RESULTS if r[1] is False]

    for name, ok, detail in RESULTS:
        if ok is None:
            print("\n%s" % name)
        elif ok and args.verbose:
            print("  pass  %s" % name)
        elif not ok:
            print("  FAIL  %s%s" % (name, ("  -- %s" % detail) if detail else ""))

    print("\n%d passed, %d failed, %d assertions"
          % (len(passed), len(failed), len(passed) + len(failed)))
    return 1 if failed else 0


if __name__ == "__main__":
    sys.exit(main())
