---
name: reports-google-analytics
description: Retrieve Google Analytics 4 performance data through the Google Analytics Data API, compare the most recent 30 completed days against the 30 before them, validate the data, analyse acquisition, content, engagement, key events, devices, geography and ecommerce, generate executive charts, and emit a structured analysis file a reporting agent turns into a client-facing report. Brand-agnostic and reusable across any GA4 property — lead generation, ecommerce, content, apps. Credentials are shared agency-wide in ~/clients/agency.env; the only client-specific value is GA4_PROPERTY_ID. Use this skill whenever the user wants a GA4 report, Google Analytics numbers, website or app performance, traffic analysis, "how is the site doing", "pull GA4", "analytics report", "traffic report", "monthly analytics", "what happened to our traffic", "why did conversions drop", "check our key events", "landing page performance", "which channels are working", "ecommerce performance", "session data", "engagement rate", or a period-over-period comparison of website performance. Also use it when another agent needs GA4 data prepared for a report, or when a GA4 property needs its configuration or tracking sanity-checked.
---

# Google Analytics reporting

Turn a GA4 property into two things a client can act on: **a structured
analysis file with every number checked**, and **charts that do not overstate
what the numbers say**.

**The core discipline: never let a measurement failure be reported as a
business result.** A tracking outage and a demand collapse look identical in a
30-day total. So does a broken tag and a conversion problem. Everything in this
skill exists to keep those apart — and where the data genuinely cannot separate
them, to say so and name the check that would.

Three rules sit above the rest:

1. **Unavailable is not zero.** A metric this property does not report stays
   absent from retrieval through to the page, and prints as "not available".
2. **A number is not a verdict.** Sessions falling while key events rise is a
   better period, not a worse one.
3. **Correlation is not cause.** Findings say what was observed. Where a cause
   is plausible but unproven, they say "may indicate" and stop there.

---

## The pipeline

Six pieces, each reading a file and writing a file. Only one touches the
network.

```
ga4_common.py    config · auth · HTTP · error classification
      ↓
fetch_ga4.py     Google Analytics Data + Admin APIs  →  data/raw.json
      ↓
analyze_ga4.py   raw.json  →  analysis.json · kpis.json · tables.md · CSVs
      ↓
make_charts.py   analysis.json  →  charts/*.svg · *.png · charts.json
      ↓
the agent        analysis.json  →  google-analytics-report-<date>.md
      ↓
render_report.py report.md      →  google-analytics-report-<date>.html
```

The last step lives in the plugin design system, not in this skill: every
`reports-*` skill renders through the same one, which is what makes an
Analytics report and an Ads report look like two documents from one practice.
It produces a single self-contained HTML file — stylesheet, typeface and every
chart embedded, nothing fetched from the network — and that is the file the
client receives. The Markdown stays as the source of record.

```bash
D=~/the-machine/analytics-insights/design/lib
python3 $D/render_report.py --report google-analytics-report-<date>.md \
  --analysis analysis.json --source google-analytics --project-root .
```

Put `<!-- tiles -->` in the report where the KPI stat-tile row belongs. Details,
including the per-client accent: `references/design.md` and `design/DESIGN.md`.

The split is what makes everything after retrieval testable offline, against a
property that has no key events, or lost four days of data, or launched last
week — without waiting for a real client property to be in that state, and
without spending quota to reproduce a bug twice.

---

## Run it

From the **client project root** — the directory holding that client's `.env`:

```bash
SKILL=~/the-machine/analytics-insights/skills/reports-google-analytics

python3 $SKILL/scripts/check_config.py                    # 1. preflight, every time
python3 $SKILL/scripts/fetch_ga4.py                       # 2. retrieve
python3 $SKILL/scripts/analyze_ga4.py --raw reports/google-analytics/<END>/data/raw.json
python3 $SKILL/scripts/make_charts.py \
  --analysis reports/google-analytics/<END>/data/analysis.json --update-analysis
```

`<END>` is the last day of the current period. Take it from the `raw_file` path
`fetch_ga4.py` prints — do not compute it, because `GA4_LAG_DAYS` or
`--end-date` may have moved it.

Exit codes are consistent across all four: **0** success · **1** partial, core
data is there · **2** configuration · **3** authentication or property access ·
**4** transient, retry.

Full command reference, including how another agent invokes this:
`references/workflow.md`.

---

## Configuration, in two files

| File | Holds | Shared |
|---|---|---|
| `~/clients/agency.env` | Google OAuth credentials | Every `reports-*` skill, every client |
| `<client project>/.env` | `GA4_PROPERTY_ID` | This client only |

A credential lives in exactly one place on the machine, so a client project can
be copied, shared or archived without carrying one. Secrets are read at run
time, held for one process, and never written to stdout, a log, a report, a
JSON file, a CSV, a chart or an error message.

**GA4 has no login customer ID.** Unlike Google Ads there is no manager
account and no hierarchy: a property ID plus a granted identity is the whole
address.

```bash
# <client project>/.env          -- no secrets here, ever
GA4_PROPERTY_ID=123456789
```

Digits only, from **Admin → Property → Property details**. Not the `G-`
measurement ID, not a `UA-` property, not a `GTM-` container — each of those
gets its own error message naming what it actually is.

**The property-access prerequisite, per client:** someone with Administrator
rights on the property must add the agency's Google identity under **Admin →
Property → Property access management** with the **Viewer** role. This is not a
credential and it belongs in no file. `check_config.py --list-properties` shows
everything the identity can currently reach.

Two APIs, enabled once agency-wide in the Google Cloud project: the **Google
Analytics Data API** (required — every number) and the **Google Analytics Admin
API** (optional — property name, key-event definitions, property discovery).
Google Cloud provisions and authorises them; the data itself comes from the
Analytics APIs.

Details, including how to mint one refresh token carrying both the Analytics
and Ads scopes: `references/authentication.md` and `references/configuration.md`.

---

## Reporting periods

- **Current:** the most recent 30 *fully completed* days, ending yesterday.
- **Comparison:** the 30 days immediately before that.
- **Today is never included** — a partial day compared against a whole one
  invents a decline.
- "Yesterday" is computed in the **property's** time zone, not the machine's.
- Both ranges are stated in full in every report.

Override with `--days`, `--end-date`, or `--current`/`--previous` together.

---

## What it analyses

**KPIs** — active/total/new users, sessions, engaged sessions, engagement rate,
bounce rate, average session duration, views, views per session, sessions per
user, event count, events per session, key events, session and user key-event
rates. Plus the full ecommerce set **when the property returned actual purchase
activity**.

**Acquisition** — session-scoped channel, source/medium and campaign, kept
strictly apart from first-user attribution. They answer different questions,
their totals do not reconcile, and they never share a row.

**Content** — landing pages and pages, with the weak high-traffic performers,
the material movers, and the pages carrying a disproportionate share of key
events or revenue. Pages below the traffic floor are not judged.

**Devices, geography, events, ecommerce, daily trends** — each with the
small-sample guard applied, and geography reported only where a difference is
real.

**Key events under both names.** Google renamed conversions to key events in
2024; which name a property answers to is discovered, not assumed, and
normalised downstream while preserving the property's own wording. GA4 records
*which* events are key events — it does not record what they *mean*. Where the
meaning is not established, the report says so rather than calling a key event a
lead or a sale.

**The schema is asked, never assumed.** `properties/{id}/metadata` is read
first, so a metric this property does not carry is dropped with a reason instead
of returning a 400 that kills the run — and custom dimensions and metrics are
discovered rather than guessed.

---

## What it produces

```
reports/google-analytics/2026-08-19/
├── google-analytics-report-2026-08-19.md      written by the agent
├── data/
│   ├── raw.json         everything the API returned — the audit trail
│   ├── analysis.json    the output contract
│   ├── kpis.json        the KPI block alone
│   ├── tables.md        pre-rendered Markdown tables
│   └── *.csv            daily, acquisition, landing pages, pages, devices,
│                        geography, events, ecommerce
└── charts/
    ├── charts.json      the manifest — including what was NOT drawn, and why
    └── *.png            kpi-change, daily-performance, channel-performance,
                         landing-page-performance, key-event-performance,
                         device-performance, ecommerce-performance, ecommerce-funnel
```

**Only files with data are written.** A property with no ecommerce gets no
`ecommerce.csv` and no ecommerce charts — not empty ones.

The folder is named for the **last day of data**, not the day it was generated,
so re-running a period overwrites instead of accumulating.

---

## Reference files

Read the one you need; none of them is required reading before a normal run.

| File | Read it when |
|---|---|
| `references/workflow.md` | Running the pipeline, or invoking it from another agent |
| `references/authentication.md` | Anything auth: scopes, tokens, property access, required APIs |
| `references/configuration.md` | Which value goes in which file, periods, output layout |
| `references/metrics-and-dimensions.md` | What GA4 will and will not tell you, and under what field name |
| `references/analysis-rules.md` | How a number becomes a finding — materiality, verdicts, guards |
| `references/data-quality.md` | The checks, and what each one changes about the report |
| `references/output-contract.md` | The shape of `analysis.json`, field by field |
| `references/visualizations.md` | What is drawn and how to embed it |
| `references/design.md` | Rendering the client-facing HTML, the per-client accent, what the design system governs |
| `../../design/DESIGN.md` | **The plugin design system** — colour, type, spacing, components, chart rules. Binding on this skill. |
| `references/troubleshooting.md` | Any error message, exit code, or number that looks wrong |
| `references/testing.md` | The fixtures, validating a change offline, adding a case |

`assets/agency.env.example` and `assets/client.env.example` are copy-ready
placeholders. `assets/report-template.md` is the report's structure.

---

## Validating a change

There is no automated suite. Eleven fixtures in `assets/fixtures/` run the
pipeline below retrieval offline — no credentials, no quota — and
`references/testing.md` lists what to check a change against: that no output
file contains a credential, that "not available" never becomes zero, that a
zero baseline gives an undefined percentage rather than infinity, that a
collection gap caveats every decline it could explain, and that every
recommendation traces back to a finding.

The fixtures cover the property states that are hard to find on demand: no key
events, a tracking outage, an empty comparison period, too little traffic to
judge, quota failures mid-run, the pre-2024 metric naming, heavy `(not set)`, a
disabled Admin API, and a schema missing several KPIs.

---

## The rules, in one place

1. Never invent data.
2. Never silently replace missing data with zero.
3. State when a metric could not be retrieved.
4. Separate facts from interpretations.
5. Separate tracking concerns from performance concerns.
6. Do not infer causation without evidence.
7. Prioritise material changes over minor fluctuations.
8. Weigh percentage change **and** absolute volume.
9. Avoid strong conclusions from small samples.
10. Use GA4 terminology correctly.
11. Keep session acquisition apart from first-user acquisition.
12. Do not assume a key event is a sale or a lead.
13. Do not assume a property has ecommerce.
14. Do not assume two properties share a configuration.
15. Keep the architecture brand-agnostic.
16. Keep credentials centralised in `~/clients/agency.env`.
17. Never expose a credential.
18. Recommend only what the data supports.
19. Prefer actionable insight to descriptive commentary.
20. Flag every material data-quality concern.
