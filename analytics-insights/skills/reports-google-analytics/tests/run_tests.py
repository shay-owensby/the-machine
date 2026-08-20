#!/usr/bin/env python3
"""
The whole pipeline, offline, in one command.

    python3 tests/run_tests.py              # everything
    python3 tests/run_tests.py --list       # what it checks
    python3 tests/run_tests.py -k baseline  # only tests whose name matches

Nothing here touches the network, needs credentials, or reads a real GA4
property. Configuration cases are built from throwaway .env files in a temp
directory; analytical cases run against the fixtures in assets/fixtures/.

What it is actually protecting:

  * that a missing credential, a missing property ID and a mistyped property ID
    each produce their own actionable message and the right exit code;
  * that no secret ever reaches stdout or an output file;
  * that "not available" never becomes 0, in JSON, in a table, or in a CSV;
  * that a zero baseline produces an undefined percentage, not an infinite one;
  * that a collection gap is not reported as a performance decline;
  * that an absent dataset produces an absent section, not an empty one;
  * that every chart either exists on disk or carries a reason it does not.

Exit code 0 when every check passes, 1 otherwise.
"""

import argparse
import json
import shutil
import subprocess
import sys
import tempfile
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
SCRIPTS = ROOT / "scripts"
FIXTURES = ROOT / "assets" / "fixtures"
sys.path.insert(0, str(SCRIPTS))

import ga4_common as ga            # noqa: E402
import analyze_ga4 as an           # noqa: E402
import fetch_ga4 as fe             # noqa: E402

FAKE_SECRET = "FAKE-SECRET-DO-NOT-LEAK-8f3a91c07b"

RESULTS = []
TESTS = []


def test(name):
    def deco(fn):
        TESTS.append((name, fn))
        return fn
    return deco


class Failure(Exception):
    pass


def ok(condition, message):
    if not condition:
        raise Failure(message)


# ---------------------------------------------------------------------------
# Configuration
# ---------------------------------------------------------------------------

def write_env(path, values):
    path.write_text("\n".join("%s=%s" % kv for kv in values.items()) + "\n", encoding="utf-8")


FULL_AGENCY = {
    "GOOGLE_CLIENT_ID": "1234.apps.googleusercontent.com",
    "GOOGLE_CLIENT_SECRET": FAKE_SECRET,
    "GOOGLE_REFRESH_TOKEN": FAKE_SECRET + "-refresh",
}


def make_project(tmp, agency=None, client=None):
    root = Path(tmp) / "project"
    root.mkdir(parents=True, exist_ok=True)
    agency_path = Path(tmp) / "agency.env"
    if agency is not None:
        write_env(agency_path, agency)
    elif agency_path.exists():
        agency_path.unlink()
    if client is not None:
        write_env(root / ".env", client)
    elif (root / ".env").exists():
        (root / ".env").unlink()
    return root, agency_path


@test("config: a missing agency.env names the file and the fix")
def t_missing_agency(tmp):
    root, agency = make_project(tmp, agency=None, client={"GA4_PROPERTY_ID": "123456789"})
    cfg = ga.resolve_config(project_root=str(root), agency_env=str(agency))
    ok(cfg.problems, "expected a problem when agency.env is absent")
    joined = "\n".join(cfg.problems)
    ok(str(agency) in joined, "the problem must name the path it looked in")
    ok("agency.env.example" in joined, "the problem must say how to create it")


@test("config: a missing credential is named individually")
def t_missing_credential(tmp):
    partial = dict(FULL_AGENCY)
    del partial["GOOGLE_REFRESH_TOKEN"]
    root, agency = make_project(tmp, agency=partial, client={"GA4_PROPERTY_ID": "123456789"})
    cfg = ga.resolve_config(project_root=str(root), agency_env=str(agency))
    joined = "\n".join(cfg.problems)
    ok("GOOGLE_REFRESH_TOKEN" in joined, "the missing key must be named")
    ok("GOOGLE_CLIENT_ID" not in joined.split("Missing shared credential(s):")[1].split("\n")[0],
       "keys that ARE present must not be listed as missing")


@test("config: a missing property ID points at the client .env, not the agency file")
def t_missing_property(tmp):
    root, agency = make_project(tmp, agency=FULL_AGENCY, client={})
    cfg = ga.resolve_config(project_root=str(root), agency_env=str(agency))
    joined = "\n".join(cfg.problems)
    ok("GA4_PROPERTY_ID" in joined, "the missing key must be named")
    ok(str(root / ".env") in joined, "it must point at the CLIENT env file")
    ok("Property details" in joined, "it must say where to find the value in GA4")


@test("config: a measurement ID, a UA ID and junk each get their own message")
def t_bad_property_ids(tmp):
    cases = {
        "G-ABC1234567": "MEASUREMENT ID",
        "UA-12345-1": "Universal Analytics",
        "GTM-ABC123": "Tag Manager",
        "not-a-number": "no digits",
        "12": "digits",
    }
    for value, expected in cases.items():
        try:
            ga.normalize_property_id(value)
            raise Failure("%r should not have validated" % value)
        except ga.ConfigError as exc:
            ok(expected in str(exc),
               "%r should be diagnosed with %r, got: %s" % (value, expected, exc))


@test("config: property IDs are accepted in every shape people paste them")
def t_good_property_ids(tmp):
    for value in ("123456789", " 123456789 ", "properties/123456789", "123,456,789"):
        ok(ga.normalize_property_id(value) == "123456789",
           "%r should normalise to 123456789" % value)


@test("config: a full configuration resolves with no problems")
def t_full_config(tmp):
    root, agency = make_project(tmp, agency=FULL_AGENCY,
                                client={"GA4_PROPERTY_ID": "123456789",
                                        "GA4_REPORT_DAYS": "30"})
    cfg = ga.resolve_config(project_root=str(root), agency_env=str(agency))
    ok(not cfg.problems, "expected no problems, got: %s" % cfg.problems)
    ok(cfg.auth_mode == "oauth", "OAuth credentials should select the oauth path")
    ok(cfg.property_id == "123456789", "property ID should resolve")
    ok(cfg.report_days == 30, "report days should resolve")


@test("secrets: describe_config never renders a credential value")
def t_no_secret_in_describe(tmp):
    root, agency = make_project(tmp, agency=FULL_AGENCY,
                                client={"GA4_PROPERTY_ID": "123456789"})
    cfg = ga.resolve_config(project_root=str(root), agency_env=str(agency))
    blob = json.dumps(ga.describe_config(cfg))
    ok(FAKE_SECRET not in blob, "a secret value reached describe_config output")
    ok('"present"' in blob, "credentials should render as present/missing")


@test("secrets: check_config prints no credential value in any mode")
def t_no_secret_in_check_config(tmp):
    root, agency = make_project(tmp, agency=FULL_AGENCY,
                                client={"GA4_PROPERTY_ID": "123456789"})
    proc = subprocess.run(
        [sys.executable, str(SCRIPTS / "check_config.py"),
         "--project-root", str(root), "--agency-env", str(agency), "--no-network"],
        capture_output=True, text=True)
    ok(proc.returncode == 0, "a valid config should exit 0, got %d: %s"
       % (proc.returncode, proc.stderr[-400:]))
    ok(FAKE_SECRET not in proc.stdout + proc.stderr, "a secret reached check_config output")


@test("check_config: a blocked configuration exits 2 and explains itself")
def t_check_config_blocked(tmp):
    root, agency = make_project(tmp, agency=FULL_AGENCY, client={})
    proc = subprocess.run(
        [sys.executable, str(SCRIPTS / "check_config.py"),
         "--project-root", str(root), "--agency-env", str(agency), "--no-network"],
        capture_output=True, text=True)
    ok(proc.returncode == 2, "missing property ID should exit 2, got %d" % proc.returncode)
    ok("GA4_PROPERTY_ID" in proc.stdout, "the blocked output should name what is missing")


# ---------------------------------------------------------------------------
# Retrieval logic
#
# The API call itself cannot be exercised offline. Everything around it can,
# and this is where the subtle bugs live: a chunked request that comes back
# describing different rows, a window that quietly includes today, a property
# whose schema is missing a field.
# ---------------------------------------------------------------------------

@test("fetch: chunked requests stay in shape and share one sort metric")
def t_chunking(tmp):
    metrics = ["sessions", "totalUsers", "newUsers", "engagedSessions", "engagementRate",
               "averageSessionDuration", "screenPageViews", "keyEvents",
               "sessionKeyEventRate", "totalRevenue", "transactions"]
    chunks = fe.chunk_metrics(metrics, "sessions")
    ok(all(len(c) <= ga.MAX_METRICS_PER_REQUEST for c in chunks),
       "a chunk exceeded the request limit: %s" % [len(c) for c in chunks])
    ok(all(c[0] == "sessions" for c in chunks),
       "the sort metric must ride in every chunk, or the chunks describe different rows")
    ok({m for c in chunks for m in c} == set(metrics), "chunking lost a metric")
    ok(fe.chunk_metrics(["sessions"], "sessions") == [["sessions"]],
       "a single metric should produce one chunk")


@test("fetch: merging chunks never invents a zero for a row that lacked a metric")
def t_merge(tmp):
    def rep(rows, metrics):
        return {"dimensions": ["x"],
                "metrics": [{"name": m, "type": "TYPE_INTEGER"} for m in metrics],
                "rows": [{"keys": [k], "values": v} for k, v in rows],
                "totals": None, "row_count": len(rows), "meta": {}}
    warnings = []
    merged = fe.merge_reports([
        rep([("a", {"sessions": 10.0}), ("b", {"sessions": 5.0})], ["sessions"]),
        rep([("a", {"sessions": 10.0, "keyEvents": 2.0}),
             ("c", {"sessions": 1.0, "keyEvents": 9.0})], ["sessions", "keyEvents"]),
    ], warnings, "test")
    by = {r["keys"][0]: r["values"] for r in merged["rows"]}
    ok(by["a"] == {"sessions": 10.0, "keyEvents": 2.0}, "matching rows should merge")
    ok("keyEvents" not in by["b"],
       "a row the second chunk did not return must not gain a fabricated zero")
    ok(by["c"]["keyEvents"] == 9.0, "a row only the second chunk saw must be kept")
    ok(warnings, "a stray row must be flagged, not absorbed silently")
    ok(fe.merge_reports([None, None], [], "test") is None,
       "merging nothing must give None, not an empty report")


@test("fetch: the default window is 30 completed days and never includes today")
def t_periods(tmp):
    import datetime as dt
    import types
    args = types.SimpleNamespace(current=None, previous=None, end_date=None)
    warnings = []
    p = fe.build_periods(args, "America/New_York", 30, 0, warnings)
    cur, prev = p["current"], p["previous"]
    ok(cur["days"] == prev["days"] == 30, "both periods should be 30 days")
    ok(dt.date.fromisoformat(cur["end"]) < dt.date.today(),
       "the current period must never include today")
    ok(dt.date.fromisoformat(prev["end"])
       == dt.date.fromisoformat(cur["start"]) - dt.timedelta(days=1),
       "the periods must be adjacent and must not overlap")
    ok("America/New_York" in p["basis"], "the basis must name the time zone used")

    warnings = []
    lagged = fe.build_periods(args, "America/New_York", 30, 2, warnings)
    ok(dt.date.fromisoformat(lagged["current"]["end"])
       == dt.date.fromisoformat(cur["end"]) - dt.timedelta(days=2),
       "GA4_LAG_DAYS must move the window back")
    ok("settling" in lagged["basis"], "the basis must disclose the lag")


@test("fetch: unequal or overlapping periods are allowed but always warned about")
def t_period_warnings(tmp):
    import types
    args = types.SimpleNamespace(current="2026-07-01:2026-07-31",
                                 previous="2026-06-01:2026-06-15", end_date=None)
    warnings = []
    fe.build_periods(args, "UTC", 30, 0, warnings)
    ok(any("different lengths" in w for w in warnings),
       "unequal periods must warn that percentages will mislead")

    args = types.SimpleNamespace(current="2026-07-01:2026-07-31",
                                 previous="2026-06-15:2026-07-10", end_date=None)
    warnings = []
    fe.build_periods(args, "UTC", 30, 0, warnings)
    ok(any("overlaps" in w for w in warnings), "overlapping periods must warn")


@test("fetch: the property schema decides what is requested")
def t_schema(tmp):
    schema = fe.Schema({
        "dimensions": [{"apiName": "date"}, {"apiName": "landingPage"},
                       {"apiName": "customEvent:plan", "customDefinition": True,
                        "uiName": "Plan", "category": "Custom"}],
        "metrics": [{"apiName": "sessions"}, {"apiName": "conversions"}],
    })
    keep, dropped = schema.filter_metrics(["sessions", "keyEvents", "conversions"])
    ok(keep == ["sessions", "conversions"], "unsupported metrics must be dropped")
    ok(dropped and dropped[0][0] == "keyEvents", "a dropped metric must carry a reason")
    ok(schema.first_dimension(["landingPagePlusQueryString", "landingPage"]) == "landingPage",
       "a renamed dimension must fall back to the name this property carries")
    ok(schema.first_dimension(["nothingLikeThis"]) is None,
       "an unsupported dimension must resolve to None, not to a guess")
    ok(len(schema.custom_dimensions) == 1, "custom dimensions must be discovered")

    blind = fe.Schema({})
    ok(blind.has_metric("anything") and blind.first_dimension(["date"]) == "date",
       "an unreadable schema must degrade open, not drop every field")


# ---------------------------------------------------------------------------
# Analysis
# ---------------------------------------------------------------------------

def load_fixture(name):
    path = FIXTURES / ("%s_raw.json" % name)
    if not path.is_file():
        raise Failure("fixture %s is missing -- run scripts/make_fixtures.py" % name)
    raw = json.loads(path.read_text(encoding="utf-8"))
    raw["_source_path"] = str(path)
    return raw


def analyse(name):
    return an.build(load_fixture(name))


@test("analysis: every fixture analyses without raising")
def t_all_fixtures_build(tmp):
    names = sorted(p.name.replace("_raw.json", "") for p in FIXTURES.glob("*_raw.json"))
    ok(len(names) >= 10, "expected at least ten fixtures, found %d" % len(names))
    for name in names:
        a = analyse(name)
        ok(a["schema"] == an.SCHEMA, "%s produced the wrong schema" % name)
        ok(a["kpis"], "%s produced no KPIs" % name)


@test("honesty: an unavailable metric is never a zero")
def t_unavailable_never_zero(tmp):
    a = analyse("unsupported-metrics")
    unavailable = [k for k in a["kpis"] if k["availability"] == "unavailable"]
    ok(unavailable, "the unsupported-metrics fixture should have unavailable KPIs")
    for rec in unavailable:
        ok(rec["current"] is None and rec["previous"] is None,
           "%s is unavailable but carries a value" % rec["key"])
        ok(rec["absolute_change"] is None and rec["percent_change"] is None,
           "%s is unavailable but carries a change" % rec["key"])
        ok(any("NOT zero" in n or "not returned" in n.lower() for n in rec["notes"]),
           "%s must say it is not zero" % rec["key"])
    for line in (a["tables"]["kpi"] or "").splitlines():
        ok("| 0 |" not in line or "not available" not in line,
           "an unavailable metric rendered as 0 in the KPI table")


@test("honesty: a zero baseline gives an undefined percentage, never infinity")
def t_zero_baseline(tmp):
    a = analyse("zero-previous")
    for rec in a["kpis"]:
        if rec["availability"] == "available" and rec["previous"] == 0 and rec["current"]:
            ok(rec["percent_change"] is None,
               "%s divided by a zero baseline" % rec["key"])
            ok(rec["verdict"] == "new", "%s should be flagged new, not improved" % rec["key"])
            ok(any("undefined" in n for n in rec["notes"]),
               "%s must explain the undefined percentage" % rec["key"])
    blob = json.dumps(a)
    ok("Infinity" not in blob and "NaN" not in blob, "a non-finite number reached the output")
    ids = [f["id"] for f in a["findings_flat"]]
    ok("no_baseline" in ids, "an empty baseline must produce the no-baseline finding")
    ok(not a["findings"]["weaknesses"],
       "nothing should be called a weakness when there is nothing to compare against")


@test("honesty: zero key events is reported as zero recorded, not as a decline")
def t_no_key_events(tmp):
    a = analyse("no-key-events")
    ids = [f["id"] for f in a["findings_flat"]]
    ok("key_events_defined_but_silent" in ids,
       "defined-but-silent key events must be raised as a risk")
    checks = {c["check"]: c for c in a["data_quality"]["checks"]}
    ok(checks["Key events recorded"]["status"] == "warn",
       "zero key events should be a data-quality warning")
    ok(any("not that conversions fell" in w for w in a["data_quality"]["warnings"]),
       "the warning must forbid reporting zero as a decline")


@test("honesty: a collection gap caveats every decline it could explain")
def t_tracking_gap(tmp):
    a = analyse("tracking-outage")
    ids = [f["id"] for f in a["findings_flat"]]
    ok("daily_missing_days" in ids, "missing days must be raised")
    declines = [f for f in a["findings_flat"]
                if f["type"] == "weakness" and "down" in f["title"].lower()]
    ok(declines, "the outage fixture should produce decline findings")
    for f in declines:
        ok(f["confidence"] == "low",
           "%s should drop to low confidence when days are missing" % f["id"])
        ok("missing measurement" in f["statement"],
           "%s must carry the missing-measurement caveat" % f["id"])
    ok(any(f["id"].startswith("event_stopped:") for f in a["findings_flat"]),
       "an event that stopped firing must be raised")


@test("structure: an absent dataset produces an absent section, not an empty one")
def t_partial_failure(tmp):
    a = analyse("partial-failure")
    ok(a["sections"]["content"]["landing_pages"] is None,
       "a dataset that was never retrieved must be None, not []")
    ok(a["tables"]["landing_pages"] is None, "no table should be rendered for it")
    ok(not [f for f in a["findings_flat"] if f["id"].startswith("landing_")],
       "no landing-page finding may be drawn from a dataset that failed")
    ok(a["data_quality"]["api_errors"], "the API errors must be carried through")
    checks = {c["check"]: c for c in a["data_quality"]["checks"]}
    ok(checks["All requested datasets retrieved"]["status"] == "fail",
       "a failed dataset must fail its check")


@test("compatibility: a property using `conversions` is normalised to key events")
def t_legacy_naming(tmp):
    a = analyse("legacy-conversions")
    ke = {k["key"]: k for k in a["kpis"]}["keyEvents"]
    ok(ke["availability"] == "available",
       "legacy `conversions` must surface as keyEvents")
    ok(ke["current"] == 486, "the legacy value should carry through unchanged")
    ok("conversions" in (a["key_events"].get("metric_naming") or ""),
       "the property's own naming must be preserved for the report to use")


@test("ecommerce: included when there is revenue, omitted when there is not")
def t_ecommerce_gating(tmp):
    store = analyse("ecommerce-growth")
    ok(store["ecommerce_state"] == "active", "the store fixture should be active")
    ok(store["sections"]["ecommerce"]["included"], "the ecommerce section should be included")
    ok(store["sections"]["ecommerce"]["funnel"], "the funnel should be populated")
    ok(store["tables"]["ecommerce"], "an ecommerce KPI table should be rendered")

    leadgen = analyse("leadgen-healthy")
    ok(leadgen["ecommerce_state"] != "active", "the lead-gen fixture is not ecommerce")
    ok(not leadgen["sections"]["ecommerce"]["included"],
       "the ecommerce section must be excluded")
    ok(leadgen["tables"]["ecommerce"] is None, "no ecommerce table for a non-store")
    ok(not any(k["key"] == "totalRevenue" for k in leadgen["kpis"]),
       "revenue must not appear as a KPI row for a property with no revenue")


@test("ecommerce: a weakening funnel step is found")
def t_ecommerce_funnel(tmp):
    a = analyse("ecommerce-growth")
    ok(any(f["id"].startswith("ecom_step_drop:") for f in a["findings_flat"]),
       "the checkout step regression should be detected")


@test("attribution: unattributed buckets are surfaced, not silently included")
def t_not_set(tmp):
    a = analyse("not-set-heavy")
    checks = [c for c in a["data_quality"]["checks"] if "Unattributed" in c["check"]]
    ok(checks, "large (not set)/(other) buckets must raise a check")
    ok(any(c["status"] == "fail" for c in checks),
       "a bucket over 20%% of sessions should fail, not warn")
    ok(any("Direct traffic" in w for w in a["data_quality"]["warnings"]),
       "a direct-traffic surge should be flagged as possible attribution loss")


@test("sampling: a tiny property gets a volume warning and few conclusions")
def t_low_traffic(tmp):
    a = analyse("low-traffic")
    checks = {c["check"]: c for c in a["data_quality"]["checks"]}
    ok(checks["Enough traffic to draw conclusions"]["status"] == "warn",
       "a property this small must be flagged")
    high = [f for f in a["findings_flat"] if f["severity"] == "high"]
    ok(not high, "no high-severity finding should come out of 212 sessions: %s"
       % [f["id"] for f in high])


@test("metadata: a missing property name is left missing, never invented")
def t_no_admin_api(tmp):
    a = analyse("no-admin-api")
    ok(a["property"]["name"] is None, "the property name must stay unknown")
    ok(a["property"]["admin_api_available"] is False, "the Admin API state must be recorded")
    ok(a["property"]["time_zone"], "the time zone should still come from the Data API")
    checks = {c["check"]: c for c in a["data_quality"]["checks"]}
    ok(checks["Key event definitions readable"]["status"] == "warn",
       "unreadable key-event definitions must be flagged")


@test("interpretation: falling sessions with rising outcomes is not called a decline")
def t_mix_shift(tmp):
    raw = load_fixture("leadgen-healthy")
    # Invert the session counts so the current period has fewer sessions and
    # more key events than the previous one.
    cur = raw["datasets"]["totals"]["current"]["totals"]
    prev = raw["datasets"]["totals"]["previous"]["totals"]
    cur["sessions"], prev["sessions"] = 38000.0, 48000.0
    a = an.build(raw)
    sessions = {k["key"]: k for k in a["kpis"]}["sessions"]
    ok(sessions["verdict"] == "ambiguous",
       "a session fall alongside rising key events must not be called a decline")
    ok(any("mix change" in n for n in sessions["notes"]), "it must say why")
    ok(any(f["id"] == "traffic_down_key_events_up" for f in a["findings_flat"]),
       "the mix shift should be a strength finding")


@test("recommendations: every one traces back to a finding")
def t_recommendations_traceable(tmp):
    for name in ("leadgen-healthy", "ecommerce-growth", "tracking-outage"):
        a = analyse(name)
        ids = {f["id"] for f in a["findings_flat"]}
        ok(a["recommended_actions"], "%s produced no recommendations" % name)
        for rec in a["recommended_actions"]:
            ok(rec["from_finding"] in ids,
               "%s: recommendation %r has no supporting finding"
               % (name, rec["action"][:50]))
            for field in ("action", "reason", "evidence", "expected_impact",
                          "priority", "confidence"):
                ok(rec.get(field), "%s: recommendation is missing %s" % (name, field))
            ok(rec["priority"] in ("High", "Medium", "Low"), "bad priority")


# ---------------------------------------------------------------------------
# Output files
# ---------------------------------------------------------------------------

@test("outputs: CSV leaves an unavailable value blank, never zero")
def t_csv_blank(tmp):
    out = Path(tmp) / "csv"
    raw = load_fixture("leadgen-healthy")
    a = an.build(raw)
    an.write_outputs(a, out, raw)
    path = out / "acquisition.csv"
    ok(path.is_file(), "acquisition.csv should be written")
    header, *rows = path.read_text(encoding="utf-8").strip().splitlines()
    ok("current_totalRevenue" in header, "the header should carry every metric column")
    idx = header.split(",").index("current_totalRevenue")
    for row in rows:
        ok(row.split(",")[idx] == "",
           "a metric this property does not report must be an empty cell, not 0")


@test("outputs: the ecommerce CSV is not written for a property with no revenue")
def t_no_empty_ecommerce_csv(tmp):
    out = Path(tmp) / "noecom"
    raw = load_fixture("leadgen-healthy")
    an.write_outputs(an.build(raw), out, raw)
    ok(not (out / "ecommerce.csv").exists(),
       "an empty ecommerce.csv must not be created just to fill the folder")
    ok((out / "kpis.json").is_file(), "kpis.json should always be written")
    ok((out / "tables.md").is_file(), "tables.md should always be written")


@test("outputs: daily.csv marks a day with no data rather than writing zeros")
def t_daily_gap_csv(tmp):
    out = Path(tmp) / "daily"
    raw = load_fixture("tracking-outage")
    an.write_outputs(an.build(raw), out, raw)
    lines = (out / "daily.csv").read_text(encoding="utf-8").strip().splitlines()
    header = lines[0].split(",")
    ok(header[1] == "data_returned", "daily.csv must record whether a day returned data")
    sess = header.index("sessions")
    gaps = [l for l in lines[1:] if l.split(",")[1] == "no"]
    ok(len(gaps) == 4, "expected four gap days, found %d" % len(gaps))
    for line in gaps:
        ok(line.split(",")[sess] == "",
           "a day with no data must be blank in the CSV, never 0")


@test("charts: every chart is either on disk or carries a reason it is not")
def t_charts(tmp):
    try:
        import matplotlib  # noqa: F401
    except ImportError:
        RESULTS.append(("charts", "skipped", "matplotlib is not installed"))
        return "skipped: matplotlib is not installed"
    for name in ("leadgen-healthy", "ecommerce-growth", "no-key-events", "zero-previous"):
        out = Path(tmp) / "charts" / name
        raw = load_fixture(name)
        an.write_outputs(an.build(raw), out / "data", raw)
        proc = subprocess.run(
            [sys.executable, str(SCRIPTS / "make_charts.py"),
             "--analysis", str(out / "data" / "analysis.json"),
             "--out", str(out / "charts"), "--update-analysis"],
            capture_output=True, text=True)
        ok(proc.returncode == 0, "%s: charts exited %d: %s"
           % (name, proc.returncode, proc.stderr[-300:]))
        manifest = json.loads((out / "charts" / "charts.json").read_text())
        ok(manifest, "%s produced an empty manifest" % name)
        for entry in manifest:
            if entry["status"] == "drawn":
                ok(Path(entry["file"]).is_file(),
                   "%s: %s claims to be drawn and is not on disk" % (name, entry["id"]))
                ok(entry["relative_path"].startswith("./charts/"),
                   "%s: %s needs a relative path the report can embed" % (name, entry["id"]))
                ok(entry.get("alt"), "%s: %s has no alt text" % (name, entry["id"]))
            else:
                ok(entry.get("reason"),
                   "%s: %s was skipped without a reason" % (name, entry["id"]))
        if name == "no-key-events":
            skipped = {e["id"] for e in manifest if e["status"] != "drawn"}
            ok("key-event-performance" in skipped,
               "a property with no key events must not get a key-event chart")


@test("outputs: no output file contains a credential")
def t_no_secret_in_outputs(tmp):
    out = Path(tmp) / "leak"
    raw = load_fixture("leadgen-healthy")
    raw["config"]["agency_env"] = "~/clients/agency.env"
    an.write_outputs(an.build(raw), out, raw)
    for path in out.rglob("*"):
        if path.is_file():
            body = path.read_text(encoding="utf-8", errors="replace")
            for needle in ("GOOGLE_REFRESH_TOKEN=", "GOOGLE_CLIENT_SECRET=", FAKE_SECRET,
                           "refresh_token", "access_token", "Bearer "):
                ok(needle not in body,
                   "%s contains %r" % (path.name, needle))


@test("end to end: analyze_ga4.py runs as a subprocess on every fixture")
def t_cli_end_to_end(tmp):
    for path in sorted(FIXTURES.glob("*_raw.json")):
        name = path.name.replace("_raw.json", "")
        out = Path(tmp) / "cli" / name
        proc = subprocess.run(
            [sys.executable, str(SCRIPTS / "analyze_ga4.py"),
             "--raw", str(path), "--out", str(out), "--quiet"],
            capture_output=True, text=True)
        ok(proc.returncode == 0, "%s exited %d: %s"
           % (name, proc.returncode, proc.stderr[-400:]))
        summary = json.loads(proc.stdout)
        ok(summary["analysis_file"], "%s printed no analysis path" % name)
        ok((out / "analysis.json").is_file(), "%s wrote no analysis file" % name)


@test("end to end: a malformed retrieval file is refused, not analysed")
def t_malformed_input(tmp):
    bad = Path(tmp) / "bad.json"
    bad.write_text("{not json at all", encoding="utf-8")
    proc = subprocess.run(
        [sys.executable, str(SCRIPTS / "analyze_ga4.py"), "--raw", str(bad)],
        capture_output=True, text=True)
    ok(proc.returncode == 2, "malformed JSON should exit 2, got %d" % proc.returncode)
    ok("not valid JSON" in proc.stderr, "it should say what is wrong")

    wrong = Path(tmp) / "wrong.json"
    wrong.write_text(json.dumps({"schema": "something/else@9"}), encoding="utf-8")
    proc = subprocess.run(
        [sys.executable, str(SCRIPTS / "analyze_ga4.py"), "--raw", str(wrong)],
        capture_output=True, text=True)
    ok(proc.returncode == 2, "an unknown schema should exit 2, got %d" % proc.returncode)

    missing = Path(tmp) / "nope.json"
    proc = subprocess.run(
        [sys.executable, str(SCRIPTS / "analyze_ga4.py"), "--raw", str(missing)],
        capture_output=True, text=True)
    ok(proc.returncode == 2, "a missing file should exit 2, got %d" % proc.returncode)


# ---------------------------------------------------------------------------
# Runner
# ---------------------------------------------------------------------------

def main():
    ap = argparse.ArgumentParser(description="Run the offline test suite.")
    ap.add_argument("--list", action="store_true", help="List the checks and exit")
    ap.add_argument("-k", dest="filter", help="Only run tests whose name contains this")
    ap.add_argument("--keep", action="store_true", help="Keep the temp directory")
    args = ap.parse_args()

    if args.list:
        for name, _fn in TESTS:
            print(name)
        return 0

    if not list(FIXTURES.glob("*_raw.json")):
        print("No fixtures found. Run: python3 scripts/make_fixtures.py", file=sys.stderr)
        return 1

    tmp = tempfile.mkdtemp(prefix="ga4-tests-")
    passed = failed = skipped = 0
    try:
        for name, fn in TESTS:
            if args.filter and args.filter not in name:
                continue
            case_tmp = Path(tmp) / ("case-%02d" % (passed + failed + skipped))
            case_tmp.mkdir(parents=True, exist_ok=True)
            try:
                result = fn(str(case_tmp))
                if isinstance(result, str) and result.startswith("skipped"):
                    skipped += 1
                    print("SKIP  %s (%s)" % (name, result))
                else:
                    passed += 1
                    print("PASS  %s" % name)
            except Failure as exc:
                failed += 1
                print("FAIL  %s\n        %s" % (name, exc))
            except Exception as exc:  # a crash is a failure, with its traceback
                failed += 1
                import traceback
                print("ERROR %s\n%s" % (name, textwrap_indent(traceback.format_exc())))
    finally:
        if not args.keep:
            shutil.rmtree(tmp, ignore_errors=True)
        else:
            print("\ntemp directory kept at %s" % tmp)

    print("\n%d passed, %d failed, %d skipped" % (passed, failed, skipped))
    return 0 if failed == 0 else 1


def textwrap_indent(text):
    return "\n".join("        " + line for line in text.strip().splitlines())


if __name__ == "__main__":
    sys.exit(main())
