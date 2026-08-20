---
name: reports-google-search-console
description: Pull a Google Search Console property's organic performance for the most recent 30 finalised days against the 30 days before it, analyse it, chart it, and hand back a structured analysis file another agent can write an executive report from. Reads shared Google credentials from ~/clients/agency.env (the universal agency credential file every reports-* skill uses) and the client's own GSC_SITE_URL from the client project's .env. Retrieves Search Analytics performance -- clicks, impressions, CTR and average position -- by day, query, page, query+page, device, country and search appearance, plus optional sitemap and URL Inspection diagnostics, and separates CTR opportunities from ranking opportunities using the property's own CTR by position band rather than an industry benchmark. Use this skill whenever someone asks for Search Console performance, an SEO or organic search report, "how is organic traffic doing", "pull the Search Console numbers", "why did our rankings drop", "which pages lost traffic", "what keywords are we close to ranking for", a visibility or indexing check, or a monthly or quarterly client report on organic search. Use it too as the data layer behind the google-search-console reporting agent, and for scheduled monthly reporting runs. Brand-agnostic: no client, industry, property or brand-term assumption is baked in.
---

# Google Search Console Performance Reporting

Get the numbers, prove they are the numbers, work out what changed and what it
means, and hand over something another agent can write a report from without
ever touching the API.

**The core discipline: unavailable is not zero.** A row Search Console did not
return is missing, and missing is a fact worth reporting. Search Console
withholds rows constantly — anonymised queries above all — so the moment a blank
becomes a `0`, the report says a query lost all its traffic when the truth is
that Google declined to show it. Every script here carries missing values through
as missing, all the way into the output contract.

**The second discipline: lower average position is better.** Position 12 → 8 is
an improvement whose arithmetic change is negative. Direction (up/down) and
verdict (better/worse) are separate fields in the contract for exactly that
reason, and every chart that plots position inverts its axis and says so.

**The third: a click loss is not automatically a ranking loss.** Clicks =
impressions × CTR. The analysis decomposes the change arithmetically before
anyone reaches for an explanation, because the fix for lost visibility, lost
rankings and lost click-through are three different pieces of work.

---

## The three-stage pipeline

Retrieval, analysis and presentation are separate processes writing separate
files, and they are separate on purpose:

```
fetch_search_console.py         API  ->  *_raw.json        what the property said
analyze_search_performance.py   file ->  *_analysis.json   what it means, plus tables
make_charts.py                  file ->  charts/*.png      what it looks like
```

Once `*_raw.json` exists, everything after it is reproducible offline: the same
input gives the same analysis, thresholds can change without re-querying, and the
fixtures in `assets/fixtures/` exercise the whole downstream half without
credentials. A pipeline that re-queried for every re-render would return slightly
different numbers each time — Search Console restates recent days — and a report
whose numbers move while you are writing it cannot be checked.

---

## Outputs

Everything is written into the **client project root** — the current working
directory — under `analytics-insights/google-search-console/`:

```
.env                                       THIS CLIENT'S config (GSC_SITE_URL)
analytics-insights/
  google-search-console/
    2026-08-16/                            named for the last day of data
      google-search-console-report-2026-08-19.md    the report (written by the agent)
      data/
        www-example-com_2026-07-18_2026-08-16_raw.json       what the API returned
        www-example-com_2026-07-18_2026-08-16_analysis.json  the output contract
        www-example-com_2026-07-18_2026-08-16_tables.md      pre-rendered tables
      charts/
        ..._kpi-summary.png          ..._organic-click-trend.png
        ..._organic-impression-trend.png  ..._ctr-trend.png
        ..._position-trend.png       ..._query-performance.png
        ..._page-performance.png     ..._search-opportunities.png
        ..._device-performance.png   ..._country-performance.png
        ..._charts.json                                      the chart manifest
```

The dated folder is the **last day of data**, so two runs of the same period land
in the same place and two runs of different periods do not. The report file is
dated by the day it was written, because that is the date a client will ask about.
`--flat` writes straight into `--out` when a different layout is wanted.

Two path roots are in play and mixing them up is the one mechanical error that
will bite: `scripts/`, `references/` and `assets/` are relative to **this skill's
directory**, while `analytics-insights/` and `.env` are relative to the **client
project root**. Use absolute paths for the scripts if there is any doubt.

---

## Before anything else — configuration

Shared Google credentials live in **`~/clients/agency.env`** and are shared by
every skill whose name starts with `reports-`. They are never copied into a
client project, never passed on a command line, and never printed.

The client project's `.env` holds **which property to report on**:

```bash
GSC_SITE_URL=https://www.example.com/     # required: URL-prefix property
GSC_SITE_URL=sc-domain:example.com        # ...or a domain property
GSC_BRAND_TERMS=example co,examplco       # optional: enables the branded split
```

Three things get confused, and only the first is a credential:

| | What it is | Where it lives |
|---|---|---|
| **Shared credentials** | OAuth client, refresh token (or a service-account key) | `~/clients/agency.env` — agency-wide |
| **API access** | The Search Console API enabled on the Cloud project | Google Cloud Console — one-off |
| **Property access** | The identity added as a user on the client's property | Search Console → Settings → Users and permissions — **per client** |

Property access is a **prerequisite, not a credential**. Working credentials plus
no property access is the most common failure on a new client, and it is fixed by
the client, not by the agency. For a service account, the address to add is its
`client_email`.

⚠️ **Scope.** The shared `GOOGLE_REFRESH_TOKEN` may have been minted for Google
Ads only, in which case the token exchange succeeds and the first Search Console
call fails. Re-mint it with `https://www.googleapis.com/auth/webmasters.readonly`
as well, or add a `GSC_REFRESH_TOKEN` to `agency.env` — the skill prefers it when
present.

Full detail: `references/authentication.md`. Property identifiers and what
validation actually checks: `references/property-validation.md`.

---

## The pipeline

### Step 0 — Preflight, every run

```bash
python3 scripts/check_config.py --project-root .
python3 scripts/check_config.py --list-sites      # what CAN this identity read?
```

Resolves configuration, then proves three things: the credentials work, the
configured property is readable by this identity, and the property has finalised
Search Analytics data. It prints credentials as `present`/`missing` and never as
values.

Exit `0` ready · `2` configuration problem · `3` auth, permission or no data ·
`4` transient failure, retry.

Anything but `0` stops the run. Report the problem and what would fix it —
`references/troubleshooting.md` maps every common error to its cause. Never write
a report from a run that could not authenticate.

**Read back the property identifier before going further.** `https://example.com/`,
`https://www.example.com/` and `sc-domain:example.com` are three different
properties with different data, and the wrong one produces a complete, plausible,
entirely wrong report. The skill never falls back to a similar property; if the
configured one is unreachable it says which ones are, and stops.

### Step 1 — Retrieve

```bash
python3 scripts/fetch_search_console.py --project-root . \
  --out analytics-insights/google-search-console
```

It discovers the **latest finalised date** for the property rather than assuming
yesterday — Search Console lags two to three days, sometimes more — then builds
the most recent 30 finalised days against the 30 immediately before, and pulls
every dataset with proper pagination.

To override:

```bash
--days 30                                  # period length (both windows)
--end-date 2026-08-10                      # last day of the current period
--current 2026-07-18:2026-08-16 --previous 2025-07-18:2025-08-16   # year on year
--skip query_page,countries                # trim optional datasets
--chunk-days 7                             # large property: retrieve in slices
--sitemaps --inspect-urls                  # optional diagnostics
--data-state all                           # include provisional days (say so in the report)
```

Exit `0` complete · `1` partial, some optional datasets failed · `2` config ·
`3` core data or property access unavailable · `4` transient.

Exit `1` is a normal outcome and not a reason to stop: the raw file records which
queries failed and why, and every downstream stage treats those sections as
unavailable rather than empty. Exit `3` is a stop.

What gets retrieved, how pagination and chunking work, and why search appearance
needs its own query: `references/data-retrieval.md`.

### Step 2 — Analyse

```bash
python3 scripts/analyze_search_performance.py \
  --raw analytics-insights/google-search-console/2026-08-16/data/<file>_raw.json
```

Writes `*_analysis.json` — the output contract — and `*_tables.md`, which holds
every table already formatted.

It computes the four KPIs for both periods with absolute and percentage change,
direction, verdict and materiality; decomposes the click change into its
impression and CTR components; joins queries, pages, devices, countries and
search appearance across both periods; finds CTR and ranking opportunities;
classifies losses by kind; runs the diagnostic rules; validates the data against
itself; and derives recommendations from the findings.

Two design choices worth knowing before reading the output:

- **Opportunity thresholds scale with the property.** The impression floor is
  0.05% of the property's own impressions, never below 100. A fixed threshold
  buries a small site's whole opportunity set or floods a publisher's report.
- **The CTR benchmark is the property's own.** A row is judged against this
  site's median CTR in the same position band (1-3, 4-10, 11-20, 21+), not an
  industry curve this data does not contain.

The change maths, materiality and the position rules:
`references/period-comparison.md`. Every diagnostic rule and what it does and
does not claim: `references/diagnostics.md`.

### Step 3 — Chart

```bash
python3 scripts/make_charts.py \
  --analysis .../data/<file>_analysis.json \
  --out .../charts --update-analysis
```

Draws only the charts the data supports and records every one it skipped, with a
printable reason, in the manifest. `--update-analysis` writes the manifest back
into the analysis file so the report references charts from one place.

Exit `4` means matplotlib is not installed: the run continues, the manifest says
why there are no charts, and **the report says the visuals are unavailable**. It
never describes a chart that was not drawn.

Run this *after* the analysis, every time. Re-running Step 2 rewrites the
analysis file with an empty `charts` array, so an analysis re-run without a chart
re-run leaves the report with no manifest to reference.

The catalogue and the design rules: `references/visualization.md`.

### Step 4 — Read the data-quality section before writing anything

```bash
python3 -c "import json,sys; d=json.load(open(sys.argv[1])); print(json.dumps(d['data_quality'], indent=2))" \
  .../data/<file>_analysis.json
```

`data_quality` holds the checks, the failed queries, the capped extracts, the
coverage gap between dimensional and property totals, and the scopes with too
little data to support a conclusion. **Everything in `warnings` belongs in the
report**, in the report's own words. A warning that only exists in a JSON file is
a warning nobody received.

What each check means and which ones block a report:
`references/data-validation.md`.

### Step 5 — Hand over

The consumer is normally the `google-search-console` agent, which writes the
client-facing Markdown report. Give it the paths, not the numbers:

- `*_analysis.json` — the contract, and the only source of figures
- `*_tables.md` — tables to paste rather than retype
- `charts/*_charts.json` — chart files, titles and alt text
- `*_raw.json` — only if something needs checking back to source

Field by field, with types: `references/output-contract.md`.

---

## Reading the analysis without re-deriving it

Everything an agent needs is already computed. The parts that get misread:

**`kpis[]` / `kpis_by_key{}`** — the same records twice, as a list in report order
and keyed for lookup. Each has `availability` (`available`, `partial`,
`unavailable`), `direction` (arithmetic), `verdict` (interpretation), `material`
and `notes[]`. Read `availability` first: on anything else the figure does not go
in a table as a number. For `average_position`, read `verdict`, never the sign.

**`percent_change: null`** means undefined, not zero. Against a zero or absent
baseline there is no percentage — report the absolute change and say the previous
period had no data.

**CTR carries two changes.** `absolute_change` is in percentage points (2.00% →
2.40% is +0.40 pp); `percent_change` is relative (+20%). Both are true and they
are not interchangeable.

**`click_attribution`** — whether the click change sits in impressions or in CTR.
It is arithmetic, and it says so in its own `caveat`. It is not an explanation.

**`queries` / `pages`** — same structure. `top_by_clicks`, `winners`, `losers`,
`ctr_opportunities`, `ranking_opportunities`, `visibility_losses`,
`loss_concentration`, and a `reconciliation` block quantifying how much of the
property's clicks the dimensional rows actually cover.

**`findings`** — six groups, each finding with `evidence[]`, `severity`,
`confidence` and often a `caveat`. **The caveat travels with the finding**: if
the finding is used, the caveat is used. `confidence: low` almost always means a
small sample.

**`recommended_actions[]`** — `action`, `reason`, `evidence[]`,
`expected_impact`, `priority`, `confidence`, `from_finding`. There is no default
list: a property with nothing wrong produces none, and that is a legitimate
report.

**`brand`** — `null` unless `GSC_BRAND_TERMS` is configured, with `brand_note`
explaining why. Never estimate the split.

**`extra_search_types`** — other surfaces with their own KPIs. Never added into
the web totals.

---

## Rules that are not negotiable

1. **Never invent a number.** Every figure traces to the analysis file, which
   traces to the raw file, which is what the API returned.
2. **Never turn unavailable into zero.** Not in a table, not in a chart, not in a
   sentence. Say "not available" and say why.
3. **Never report a percentage change against a zero or absent baseline.** It is
   undefined. Give the absolute figure and name the baseline problem.
4. **Never present a partial or capped extract as complete.** If a query failed
   or hit the row cap, say so where the figures appear.
5. **Use the latest finalised data by default**, and state the latest finalised
   date in every report. Provisional days rise afterwards.
6. **Always state both exact date ranges**, in the report and on every chart.
7. **Interpret average position correctly.** Lower is better. And it is an
   impression-weighted average across every query the property appeared for — not
   a fixed keyword rank.
8. **Separate clicks, impressions, CTR and position.** Four metrics, four
   stories. A click decline is not automatically a ranking decline.
9. **Never assume query-level exports are complete.** Search Console withholds
   rows; dimensional totals sit below property totals, always, by a varying
   amount. Quote the property-level KPIs.
10. **Never classify branded queries without configured brand terms.** No
    guessing which queries contain the brand.
11. **Never equate Search Console clicks with GA4 sessions**, or impressions with
    visits. They measure different things and will not reconcile.
12. **Never combine search types into one total.** Web, Image, Video, News,
    Discover and Google News are separate datasets.
13. **Separate CTR optimisation from ranking optimisation.** Rewriting a title
    does not move rankings, and the recommendation must say which lever it pulls.
14. **Keep indexing diagnostics separate from performance history.** URL
    Inspection is point-in-time; Search Analytics is a 30-day window.
15. **Separate fact from interpretation, and never claim causation without
    evidence.** Not algorithm updates, not competitors, not site changes. Use
    "coincides with", "is associated with", "may indicate", "warrants
    investigation".
16. **Material before dramatic.** A 40% move on 50 clicks is smaller news than a
    6% move on 50,000. Report both the percentage and the absolute.
17. **Never draw a strong conclusion from a small sample.** Below ~30 clicks in a
    period, keep the hedge the analysis attached.
18. **Recommend only what the data supports.** No finding, no recommendation.
19. **Never print a credential.** Not a token, not a key path's contents, not the
    contents of `agency.env` — not in a log, a report, an error message, or a
    debugging aside.
20. **Never copy shared credentials into a client project.** One file,
    `~/clients/agency.env`, for every client.
21. **Report on the property you were asked about.** Check the identifier from
    `check_config.py` against the client before writing a word.

---

## When to stop and ask

Keep going without asking for ordinary judgement calls — an ambiguous verdict and
a low-confidence finding are what those fields exist for. Stop and ask when:

- **The property identifier does not match the client's site**, or more than one
  property for that domain is readable and it is not obvious which is intended.
  Never guess between `www` and non-`www`, or between a domain and a URL-prefix
  property.
- **The identity cannot read the property.** That is an access request for the
  client, not something to work around.
- **The property has no finalised data at all.** There is no report to write.
- **The property is not the live site** — an `http://` prefix property for an
  `https://` site, or a staging subdomain.
- **A branded/non-branded split is requested but no brand terms are configured.**
  Ask for the terms, including abbreviations and misspellings; do not infer them.

On an unattended run there is nobody to ask: write the report with the problem as
its headline finding, state plainly what could not be established, and make no
recommendation that depends on the missing piece.

---

## Reference files

| File | What it covers |
|---|---|
| `references/authentication.md` | Credential architecture, OAuth and service-account paths, scopes, required APIs, property-access prerequisite, auth failures |
| `references/property-validation.md` | Domain vs URL-prefix properties, exact identifiers, what validation checks, no-fallback behaviour |
| `references/data-retrieval.md` | Endpoints, datasets, request body, pagination, chunked retrieval, search types, API efficiency |
| `references/period-comparison.md` | Latest finalised date, the two windows, change maths, CTR points vs percent, average position, materiality, attribution |
| `references/diagnostics.md` | Every diagnostic rule, its threshold, and what it does and does not claim |
| `references/data-validation.md` | The checks, unavailable vs empty vs zero, dimensional vs property totals, what blocks a report |
| `references/visualization.md` | The chart catalogue, design rules, palette, when a chart is skipped |
| `references/output-contract.md` | The analysis file field by field |
| `references/troubleshooting.md` | Search Console API errors mapped to causes and fixes |
| `references/testing.md` | The test suite, the fixtures, and how to add a case |

| Script | What it does |
|---|---|
| `scripts/gsc_common.py` | Config resolution, OAuth and service-account auth, the API calls, pagination, retries, error classification, date and change maths |
| `scripts/check_config.py` | Preflight: configuration, property access, data availability |
| `scripts/fetch_search_console.py` | Retrieval to `*_raw.json` |
| `scripts/analyze_search_performance.py` | Analysis to `*_analysis.json` and `*_tables.md` |
| `scripts/make_charts.py` | Charts and the chart manifest |
| `scripts/make_fixtures.py` | Regenerates the offline fixtures |
| `scripts/run_tests.py` | The whole suite, offline |

| Asset | What it is |
|---|---|
| `assets/agency.env.example` | The shared credential file, placeholders only |
| `assets/client.env.example` | A client project's `.env`, placeholders only |
| `assets/report-template.md` | The structure of the final Markdown report |
| `assets/fixtures/*.json` | Synthetic properties covering the awkward cases |
