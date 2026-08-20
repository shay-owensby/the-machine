---
name: reports-google-ads
description: Pull a Google Ads account's performance for the most recent completed 30 days against the 30 days before it, analyse it, chart it, and hand back a structured analysis file another agent can write an executive report from. Reads shared Google credentials from ~/clients/agency.env (the universal agency credential file every reports-* skill uses) and the client's own GOOGLE_ADS_CUSTOMER_ID from the client project's .env. Retrieves account and campaign performance -- impressions, clicks, CTR, spend, CPC, conversions, conversion rate, CPA, conversion value, ROAS, impression share and where it was lost -- plus device, network, ad group, keyword, search term and conversion-action detail where the account reports them. Use this skill whenever someone asks for Google Ads performance, a PPC report, a paid search report, "how are the ads doing", "pull the Google Ads numbers", "what happened in Google Ads last month", "run the ads report", "why is CPA up", "which campaigns are wasting money", an account health check, or a monthly or quarterly client report on paid search. Use it too as the data layer behind the google-ads reporting agent, and for scheduled monthly reporting runs. Brand-agnostic: no client, industry or account assumption is baked in.
---

# Google Ads Performance Reporting

Get the numbers, prove they are the numbers, work out what changed and what it
means, and hand over something another agent can write a report from without
ever touching the API.

**The core discipline: unavailable is not zero.** A metric Google did not return
is missing, and missing is a fact worth reporting. The moment a blank becomes a
`0`, the report says the account converted nothing when the truth was that
conversion tracking was not queried — and nobody downstream can tell the
difference. Every script here carries missing values through as missing, all the
way into the output contract. Never patch one up on the way to a table.

The second discipline: **a number is not a verdict.** Spend went up is
arithmetic. Spend going up is *good* only against an objective this skill does
not have. Direction and verdict are separate fields in the contract for exactly
that reason — report the direction always, the verdict only where the metric
carries one.

---

## The four-stage pipeline

Retrieval, analysis, drawing and rendering are separate processes writing
separate files, and they are separate on purpose:

```
fetch_google_ads.py    API  ->  *_raw.json         what the account said
analyze_performance.py file ->  *_analysis.json    what it means, plus tables
make_charts.py         file ->  charts/*.svg|png   what it looks like
render_report.py       file ->  *.html             what the client receives
```

The last stage lives in the plugin's design system rather than in this skill,
because every `reports-*` skill renders through the same one. See
`design/DESIGN.md`.

Once `*_raw.json` exists, everything after it is reproducible offline: the same
input gives the same analysis, the analysis can be re-run after a threshold
change without re-querying, and the fixtures in `assets/fixtures/` exercise the
whole downstream half without credentials. A pipeline that re-queried for every
re-render would return slightly different numbers each time — conversions are
restated for days afterwards — and a report whose numbers move while you are
writing it cannot be checked.

---

## Outputs

Everything is written into the **client project root** — the current working
directory — under `analytics-insights/google-ads/`:

```
.env                                          THIS CLIENT'S config (customer ID)
analytics-insights/
  google-ads/
    2026-08-19-google-ads.md                  the report (written by the agent)
    2026-08-19-google-ads.html                the client-facing deliverable
    brand.json                                this client's accent (optional)
    _data/
      1234567890_2026-07-20_2026-08-18_raw.json        what the API returned
      1234567890_2026-07-20_2026-08-18_analysis.json   the output contract
      1234567890_2026-07-20_2026-08-18_tables.md       pre-rendered tables
    charts/
      1234567890_2026-07-20_2026-08-18_kpi-change.png  and .svg
      ..._daily-trend  ..._campaign-spend-conversions
      ..._campaign-efficiency  ..._impression-share  ..._device-mix
      1234567890_..._charts.json                       the chart manifest
```

Reports are dated by the day they were written; data files are named for the
account and the period they cover, so two runs on the same period overwrite each
other and two runs on different periods do not.

Every chart is written twice from one drawing: a `.png` the Markdown embeds and
a `.svg` the HTML inlines. The `.html` is the file that goes to the client --
one self-contained document with the stylesheet, the typeface and every chart
inside it. The `.md` stays as the source of record.

Two path roots are in play and mixing them up is the one mechanical error that
will bite: `scripts/`, `references/` and `assets/` are relative to **this
skill's directory**, while `analytics-insights/` and `.env` are relative to the
**client project root**. Use absolute paths for the scripts if there is any
doubt.

---

## Before anything else — configuration

Shared Google credentials live in **`~/clients/agency.env`** and are shared by
every skill whose name starts with `reports-`. They are never copied into a
client project, never passed on a command line, and never printed.

The client project's `.env` holds **which account to report on**:

```bash
GOOGLE_ADS_CUSTOMER_ID=123-456-7890        # the account being reported on
GOOGLE_ADS_LOGIN_CUSTOMER_ID=098-765-4321  # a manager account, if one is needed
```

| | What it is | Where it lives |
|---|---|---|
| **Shared credentials** | OAuth client, refresh token, developer token | `~/clients/agency.env` — agency-wide |
| **The account to report on** | The operating account whose data you want | client `.env` |
| **Manager (MCC) account** | The account a call authenticates *through*, when the target is managed | `agency.env` by default; client `.env` overrides |

**Both keys can name the account.** `GOOGLE_ADS_LOGIN_CUSTOMER_ID` is Google's
name for the manager account, but it is also the key these `.env` files label
the Google Ads account with — so it is read as both:

```
account to report on   =  --customer-id
                       -> GOOGLE_ADS_CUSTOMER_ID
                       -> GOOGLE_ADS_LOGIN_CUSTOMER_ID      (this agency's convention)

manager header         =  GOOGLE_ADS_LOGIN_CUSTOMER_ID, and only when it names a
                          DIFFERENT account from the one being queried
```

Nothing has to be relabelled for a report to run, and no run silently queries a
manager account through itself. `check_config.py` prints which key supplied the
account and whether a manager header was sent, and it stops the run if the
account turns out to be a manager — a manager holds no campaigns, so it reports
zero everything, which is the wrong account rather than a quiet one.

Falling back to `GOOGLE_ADS_LOGIN_CUSTOMER_ID` from the **shared** `agency.env`
works, but warns loudly: that is the agency-wide default and is very likely not
this client's account.

Full detail, including what each environment variable is for and how to mint a
refresh token: `references/authentication.md`.

---

## The pipeline

### Step 0 — Preflight, every run

```bash
python3 scripts/check_config.py --project-root .
```

Resolves configuration, then makes one cheap call to prove the credentials, the
login customer ID and the target customer ID work **together**. It prints the
account name, currency and time zone, and it prints credentials as
`present`/`missing` and never as values.

Exit `0` ready · `2` configuration problem · `3` auth or permission failure ·
`4` transient failure, retry.

Anything but `0` stops the run. Report the problem and what would fix it —
`references/troubleshooting.md` maps every common error to its cause. Do not
proceed to retrieval hoping it resolves itself, and never write a report from a
run that could not authenticate.

Read back the account name and currency before going further. **If the account
name is not the client you are reporting on, stop.** A wrong customer ID
produces a complete, plausible, entirely wrong report.

### Step 1 — Retrieve

```bash
python3 scripts/fetch_google_ads.py --project-root . --out analytics-insights/google-ads/_data
```

Defaults to the most recent 30 completed days **in the account's own time zone**
against the 30 days immediately before. Yesterday is the last day included;
today never is, because a partial day compared against a whole one is a decline
that did not happen.

To override:

```bash
--days 30                                  # period length (both periods)
--end-date 2026-08-18                      # last day of the current period
--current 2026-07-20:2026-08-18 --previous 2026-06-20:2026-07-19
--skip search_terms,keywords               # trim optional datasets
```

Exit `0` complete · `1` partial, some optional datasets failed · `2` config ·
`3` core data unavailable · `4` transient.

Exit `1` is a normal outcome and not a reason to stop: the raw file records
which queries failed and why, and every downstream stage treats those sections
as unavailable rather than empty. Exit `3` is a stop — without account and
campaign data there is no report.

What gets retrieved, which metrics exist for which campaign types, and the GAQL
behind each dataset: `references/data-retrieval.md`.

### Step 2 — Analyse

```bash
python3 scripts/analyze_performance.py --raw analytics-insights/google-ads/_data/<file>_raw.json
```

Writes `*_analysis.json` — the output contract — and `*_tables.md`, which holds
the KPI and campaign tables already formatted in the account's currency.

It computes every KPI for both periods, the absolute and percentage change, a
direction, a verdict, and whether the move is material; runs the diagnostic
rules; validates the data against itself; and derives recommendations from the
findings. Derived metrics are computed from base counts (CTR from clicks and
impressions, CPA from cost and conversions) rather than taken from the API's own
averages, so every figure in the report can be recomputed from two other figures
in the same table.

The change maths, the materiality thresholds and the direction-versus-verdict
rules: `references/period-comparison.md`. The diagnostic rules and what each one
does and does not claim: `references/diagnostics.md`.

### Step 3 — Chart

```bash
python3 scripts/make_charts.py \
  --analysis analytics-insights/google-ads/_data/<file>_analysis.json \
  --out analytics-insights/google-ads/charts --update-analysis
```

Draws only the charts the data supports and records every one it skipped, with
the reason, in the manifest. `--update-analysis` writes the manifest back into
the analysis file so the report can reference charts from one place. Each chart
is written as both `.png` and `.svg`; reference the `.png` in the Markdown and
the renderer will inline the vector twin.

Exit `4` means matplotlib is not installed: the run continues, the manifest says
why there are no charts, and **the report says the visuals are unavailable**. It
never describes a chart that was not drawn.

The chart catalogue: `references/visualization.md`. The design rules the charts
obey, and the palette they draw from: `design/DESIGN.md` at the plugin root.

### Step 4 — Read the data-quality section before writing anything

```bash
python3 -c "import json,sys; d=json.load(open(sys.argv[1])); print(json.dumps(d['data_quality'], indent=2))" \
  analytics-insights/google-ads/_data/<file>_analysis.json
```

`data_quality` holds the reconciliation checks, the failed queries, the metrics
that are unavailable, and the campaigns and accounts with too little data to
support a conclusion. **Everything in `warnings` belongs in the report**, in the
report's own words. A warning that only exists in a JSON file is a warning
nobody received.

What each check means and which ones block a report: `references/data-validation.md`.

### Step 5 — Render the client-facing HTML

Once the agent has written the Markdown report, render it:

```bash
D=~/the-machine/analytics-insights/design/lib
python3 $D/render_report.py \
  --report analytics-insights/google-ads/2026-08-19-google-ads.md \
  --analysis analytics-insights/google-ads/_data/<file>_analysis.json \
  --source google-ads --project-root .
```

Produces **one self-contained `.html`** beside the Markdown: stylesheet, Inter
and every chart embedded, nothing fetched from the network. That file is what
goes to the client, by mail or as a printed PDF.

It also builds the KPI stat-tile row at the top from the analysis file. Put
`<!-- tiles -->` in the report where the row belongs; without a marker it goes
directly under the masthead.

If the client has a brand accent recorded, it is picked up from
`analytics-insights/brand.json` automatically. To set one:

```bash
python3 $D/brand.py --project-root . --suggest      # read the client's DESIGN.md
python3 $D/brand.py --project-root . --accent '#006ac6' --client 'Name' --write
```

Exit `3` means a chart the report references was not on disk. The HTML is still
written, with the gap stated where the chart would have been -- never a broken
image and never a silent omission.

### Step 6 — Hand over

The consumer is normally the `google-ads` agent, which writes the client-facing
Markdown report. Give it the paths, not the numbers:

- `*_analysis.json` — the contract, and the only source of figures
- `*_tables.md` — tables to paste rather than retype
- `charts/*_charts.json` — chart files, titles and alt text
- `*_raw.json` — only if something needs checking back to source

Field by field, with types: `references/output-contract.md`.

---

## Reading the analysis without re-deriving it

Everything an agent needs is already computed. The parts that get misread:

**`kpis[]` / `kpis_by_key{}`** — the same records twice, as a list in report
order and keyed for lookup. Each has `availability` (`available`, `partial`,
`unavailable`), `direction` (arithmetic), `verdict` (interpretation:
`improved`, `declined`, `ambiguous`, `flat`, `new`, `unknown`), `material`, and
`notes[]` that qualify it. Read `availability` first: on anything but
`available`, the figure does not go in a table as a number.

**`percent_change: null`** means undefined, not zero. Against a zero baseline
there is no percentage — report the absolute change and say the previous period
was zero.

**`findings`** — grouped into `strengths`, `weaknesses`, `anomalies`,
`opportunities` and `observations`, each with `evidence[]` (the actual numbers),
`severity` and `confidence`. `confidence: low` almost always means small
samples; a low-confidence finding is a thing to watch, not a thing to assert.

**`recommended_actions[]`** — each carries `action`, `reason`, `evidence[]`,
`expected_impact`, `priority` and the `from_finding` it came from. There is no
default list: an account with nothing wrong produces none, and that is a
legitimate report.

**`data_quality`** — checks, warnings, errors, `unavailable_metrics[]` and
`insufficient_data[]`. Not optional garnish.

---

## Rules that are not negotiable

1. **Never invent a number.** Every figure in a report traces to the analysis
   file, which traces to the raw file, which is what the API returned.
2. **Never turn unavailable into zero.** Not in a table, not in a chart, not in
   a sentence. Say "not available" and say why.
3. **Never report a percentage change against a zero or missing baseline.** It
   is undefined. Give the absolute figure and name the baseline problem.
4. **Never present a partial retrieval as complete.** If a query failed, the
   section it fed is unavailable and the report says so.
5. **Separate fact from interpretation.** "Spend rose 15% while conversions rose
   17%" is a fact. "The budget increase drove conversions" is a claim about
   causation this data cannot support — write the correlation and stop.
6. **Never draw a strong conclusion from a small sample.** Below ~30 conversions
   in a period, conversion-derived metrics swing on noise; the analysis marks
   them `confidence: low` and the report keeps that hedge.
7. **Material before dramatic.** A 40% move on 5 conversions is smaller news
   than a 6% move on 5,000. Report both the percentage and the absolute.
8. **Never print a secret.** Not a token, not a refresh token, not a developer
   token, not the contents of `agency.env` — not in a log, a report, an error
   message, or a debugging aside.
9. **Never copy shared credentials into a client project.** One file,
   `~/clients/agency.env`, for every client.
10. **Always state the exact date ranges**, both of them, in every report and
    every chart. A period-over-period figure without its periods is unverifiable.
11. **Recommend only what the data supports.** No finding, no recommendation.
12. **Report on the account you were asked about.** Check the account name from
    `check_config.py` against the client before writing a word.

---

## When to stop and ask

Keep going without asking for ordinary judgement calls — an ambiguous verdict
and a low-confidence finding are what those fields exist for. Stop and ask when:

- **The account name does not match the client.** Never guess a customer ID.
- **The account has no `GOOGLE_ADS_CUSTOMER_ID` and there is more than one
  plausible account** in the manager hierarchy.
- **Core retrieval fails on authentication or permissions.** That is a
  credentials or account-access problem for a human, not something to work
  around.
- **The account is a manager or a test account.** Both produce numbers that must
  never reach a client.
- **Conversion tracking looks broken** (zero conversions on real spend) and the
  client has not already been told. Report it as a finding; do not quietly
  report a CPA of "not available" and move on.

On an unattended run there is nobody to ask: write the report with the problem
as its headline finding, state plainly what could not be established, and make
no recommendation that depends on the missing piece.

---

## Reference files

| File | What it covers |
|---|---|
| `references/authentication.md` | Credential architecture, every environment variable, MCC behaviour, OAuth setup, auth failures |
| `references/data-retrieval.md` | Datasets, GAQL, metric availability by campaign type, row caps, segmentation limits |
| `references/period-comparison.md` | Date windows, time zones, conversion lag, change maths, materiality, direction vs verdict |
| `references/diagnostics.md` | Every diagnostic rule, its threshold, and what it does and does not claim |
| `references/visualization.md` | The chart catalogue and when a chart is skipped |
| `../../design/DESIGN.md` | **The plugin design system** — colour, type, spacing, components, the chart rules, and per-client branding. Binding on this skill. |
| `references/data-validation.md` | The checks, unavailable vs zero, tracking suspicion, what blocks a report |
| `references/output-contract.md` | The analysis file field by field |
| `references/troubleshooting.md` | Google Ads API errors mapped to causes and fixes |
| `references/testing.md` | The test suite, the fixtures, and how to add a case |

| Script | What it does |
|---|---|
| `scripts/ads_common.py` | Config resolution, OAuth, the REST call, retries, error classification, row helpers |
| `scripts/check_config.py` | Preflight: configuration plus one live call |
| `scripts/fetch_google_ads.py` | Retrieval to `*_raw.json` |
| `scripts/analyze_performance.py` | Analysis to `*_analysis.json` and `*_tables.md` |
| `scripts/make_charts.py` | Charts and the chart manifest |
| `scripts/make_fixtures.py` | Regenerates the offline fixtures |
| `scripts/run_tests.py` | The whole suite, offline |

| Asset | What it is |
|---|---|
| `assets/agency.env.example` | The shared credential file, placeholders only |
| `assets/client.env.example` | A client project's `.env`, placeholders only |
| `assets/report-template.md` | The structure of the final Markdown report |
| `assets/example-report.md` | A complete worked report, generated from a fixture — the quality bar |
| `assets/fixtures/*.json` | Synthetic accounts covering the awkward cases |
