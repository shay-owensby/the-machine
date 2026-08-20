# reports-google-ads

Retrieves a Google Ads account's performance for the most recent completed 30
days against the 30 days before it, analyses it, charts it, and produces a
structured analysis file that the `google-ads` agent turns into a client-facing
report.

Brand-agnostic: nothing about a client, an industry or an account is baked in.
The only per-client configuration is which account to query.

---

## File structure

```
skills/reports-google-ads/
├── SKILL.md                        The workflow. Start here
├── README.md                       This file: structure, setup, operations
├── references/
│   ├── authentication.md           Credentials, MCC behaviour, OAuth setup, auth failures
│   ├── data-retrieval.md           Datasets, GAQL, metric availability, units, row caps
│   ├── period-comparison.md        Date windows, time zones, lag, change maths, materiality
│   ├── diagnostics.md              Every diagnostic rule and what it does not claim
│   ├── visualization.md            Chart catalogue, design rules, palette
│   ├── data-validation.md          The checks, unavailable vs zero, what blocks a report
│   ├── output-contract.md          The analysis file, field by field
│   ├── troubleshooting.md          API errors mapped to causes and fixes
│   └── testing.md                  Test suite, fixtures, pre-flight checklist
├── scripts/
│   ├── ads_common.py               Config, OAuth, REST, retries, error classification
│   ├── check_config.py             Preflight: configuration + one live call
│   ├── fetch_google_ads.py         Retrieval  →  *_raw.json
│   ├── analyze_performance.py      Analysis   →  *_analysis.json, *_tables.md
│   ├── make_charts.py              Charts     →  charts/*.png + manifest
│   ├── make_fixtures.py            Regenerates the offline fixtures
│   └── run_tests.py                The whole suite, offline
└── assets/
    ├── agency.env.example          Shared credential file (placeholders only)
    ├── client.env.example          Client project .env (placeholders only)
    ├── report-template.md          The final report's structure
    ├── example-report.md           A complete worked report, built from a fixture
    └── fixtures/*_raw.json         Synthetic accounts for the awkward cases
```

### What each file is for

| File | Purpose |
|---|---|
| `SKILL.md` | The operating instructions: pipeline, output locations, the rules that are not negotiable, when to stop and ask |
| `references/authentication.md` | The credential architecture and the three identifiers people confuse — developer token, login customer ID, target customer ID |
| `references/data-retrieval.md` | What is queried and why; which metrics exist for which campaign types; how REST encodes money and int64 |
| `references/period-comparison.md` | How the two windows are chosen, and the arithmetic of change including the zero-baseline and materiality rules |
| `references/diagnostics.md` | The rule catalogue, thresholds, and the line between correlation and causation |
| `references/visualization.md` | Which chart answers which question, and the design rules that keep them honest |
| `references/data-validation.md` | Reconciliation and coverage checks, and the unavailable-is-not-zero rule in full |
| `references/output-contract.md` | The schema another agent codes against |
| `references/troubleshooting.md` | Exit codes and every common Google Ads API error |
| `references/testing.md` | What the suite covers, the fixtures, and the pre-publication checklist |
| `scripts/ads_common.py` | Shared plumbing. Also the only place a secret is ever held, and it never prints one |
| `scripts/check_config.py` | Thirty seconds that turns "the report failed after nine queries" into "the developer token is still on test access" |
| `scripts/fetch_google_ads.py` | One run's retrieval, in one file, unmodified |
| `scripts/analyze_performance.py` | Every number a report quotes, computed once |
| `scripts/make_charts.py` | PNGs from the analysis file, never from the API |
| `scripts/make_fixtures.py` | Synthetic accounts, deterministic, REST-shaped |
| `scripts/run_tests.py` | 130+ assertions with no network and no credentials |
| `assets/report-template.md` | The report skeleton the agent fills |
| `assets/example-report.md` | The same skeleton filled from the `healthy` fixture — what "good" looks like |

---

## Setup

### 1. Shared credentials, once per machine

```bash
cp assets/agency.env.example ~/clients/agency.env
chmod 600 ~/clients/agency.env
$EDITOR ~/clients/agency.env
```

Five values, all from Google: OAuth client ID and secret, a refresh token, a
developer token with Basic access, and the agency's manager (MCC) account ID.
How to obtain each: `references/authentication.md`.

Keep this file out of every git repository. It is shared by every `reports-*`
skill; no client project ever holds a copy.

### 2. Per client, once

```bash
cp assets/client.env.example ~/clients/<client>/.env
```

Set `GOOGLE_ADS_CUSTOMER_ID` to the account being reported on — the **operating**
account, not the manager. Everything else is optional.

`GOOGLE_ADS_LOGIN_CUSTOMER_ID` is also accepted as the account, because that is
the key these `.env` files label it with. When both are present,
`GOOGLE_ADS_CUSTOMER_ID` is the account and `GOOGLE_ADS_LOGIN_CUSTOMER_ID`
becomes the manager header — which is what an MCC-managed account needs. When
only the login key is present, it is the account and no manager header is sent.
Either way `check_config.py` prints which key supplied the account, and stops
the run if that account turns out to be a manager. Details:
`references/authentication.md`.

### 3. Optional: charts

```bash
python3 -m pip install matplotlib
```

The one optional dependency. Everything else is the Python standard library.
Without it the pipeline runs and the report says the visuals are unavailable.

---

## Running it

From the **client project root**:

```bash
S=~/the-machine/analytics-insights/skills/reports-google-ads

# 0. preflight -- always
python3 $S/scripts/check_config.py --project-root .

# 1. retrieve
python3 $S/scripts/fetch_google_ads.py --project-root . \
        --out analytics-insights/google-ads/_data

# 2. analyse
RAW=$(ls -t analytics-insights/google-ads/_data/*_raw.json | head -1)
python3 $S/scripts/analyze_performance.py --raw "$RAW"

# 3. chart
ANALYSIS="${RAW%_raw.json}_analysis.json"
python3 $S/scripts/make_charts.py --analysis "$ANALYSIS" \
        --out analytics-insights/google-ads/charts --update-analysis

# 4. read the warnings before writing anything
python3 -c "import json,sys;print(json.dumps(json.load(open(sys.argv[1]))['data_quality'],indent=2))" "$ANALYSIS"
```

Common variations:

```bash
--days 7                                     # a smaller, cheaper window
--end-date 2026-07-31                        # report a closed month
--current 2026-07-01:2026-07-31 --previous 2026-06-01:2026-06-30
--skip search_terms,keywords                 # fewer queries on a large account
--material-pct 5                             # a lower materiality bar (analysis)
```

### Where output goes

```
<client project>/analytics-insights/google-ads/
├── YYYY-MM-DD-google-ads.md          the report (written by the agent)
├── _data/
│   ├── <customer>_<start>_<end>_raw.json
│   ├── <customer>_<start>_<end>_analysis.json
│   └── <customer>_<start>_<end>_tables.md
└── charts/
    ├── <customer>_<start>_<end>_kpi-change.png
    └── <customer>_<start>_<end>_charts.json
```

Reports are dated by the day they were written; data files by the account and
period they cover, so re-running the same period overwrites rather than
accumulates.

---

## How another agent invokes this skill

The `google-ads` agent is the intended consumer, but any agent can use it. The
contract is: **run the pipeline, then read `*_analysis.json` — never the API,
and never re-derive a number.**

```bash
# after steps 0-3 above
python3 - "$ANALYSIS" <<'PY'
import json, sys
d = json.load(open(sys.argv[1]))
print(d["account"]["name"], d["account"]["currency"])
print(d["periods"]["current"], "vs", d["periods"]["previous"])
print(d["tables"]["kpi"])                       # paste, do not retype
for f in d["findings"]["weaknesses"]:
    print(f["severity"], f["title"], f["evidence"])
for r in d["recommended_actions"]:
    print(r["priority"], r["action"])
for w in d["data_quality"]["warnings"]:
    print("WARN", w)
PY
```

Rules for the consumer:

1. Quote figures from the analysis file; do not recompute them.
2. Check `availability` before printing any metric. `unavailable` never becomes
   a zero or a dash that reads like one.
3. `percent_change: null` means undefined — report the absolute change and say
   the baseline was zero.
4. Keep the hedges: `confidence: low` in, "worth watching" out — not a finding
   asserted as fact.
5. Put every `data_quality.warnings` entry in the report.
6. Reference charts by the manifest's `filename` and use its `alt` text. Never
   describe a chart with `status: "not drawn"`.

Field-by-field: `references/output-contract.md`.

---

## Testing

```bash
python3 scripts/run_tests.py            # offline, no credentials, ~1 second
python3 scripts/run_tests.py --verbose
python3 scripts/make_fixtures.py --list
```

Covers missing credentials, invalid customer IDs, inaccessible accounts, an
account with no conversions, an account with no conversion value, a zero
comparison period, paused campaigns, sparse campaigns, partial metric
availability, failed queries, rate limits and a sunset API version. Full
inventory and the pre-publication checklist: `references/testing.md`.

Live credentials are exercised by `check_config.py` alone, which is the only
part of the skill that needs them to prove itself.

---

## Security

- Secrets live in `~/clients/agency.env`, are read at run time, held for the
  life of one process, and never written anywhere.
- No CLI flag accepts a secret, so none can land in a shell history or a
  transcript.
- `describe_config()` renders credentials as `present` / `missing` — never a
  value, a prefix or a length. Nothing else prints configuration.
- Raw, analysis and chart files contain account IDs and metrics only.
- If you add debugging output, do not print the config object.
