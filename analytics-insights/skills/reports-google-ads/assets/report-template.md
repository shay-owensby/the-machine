# Report template

The structure the `google-ads` agent produces, written to
`analytics-insights/google-ads/YYYY-MM-DD-google-ads.md` in the client project.

Guidance is in `<!-- comments -->`; strip them from the finished report.
Everything else is the shape of the document. Sections whose data is
unavailable are **removed and named in Data notes**, never filled with zeros.

---

```markdown
# {Client name} — Google Ads Performance Report

**Reporting period:** {current start} – {current end} ({n} days)
**Comparison period:** {previous start} – {previous end} ({n} days)
**Account:** {account name} ({customer ID}) · **Currency:** {code}
**Prepared:** {report date}

<!-- Both ranges, always, at the top. A period-over-period figure without its
     periods cannot be checked, and this is the first thing a client verifies. -->

---

## Executive summary

<!-- 500-1000 words of prose. No bullets, no headings inside it. Written for
     someone who will read this section and skim the rest.

     Cover, in an order the account's own story dictates:
       - what changed, with the two or three numbers that carry it
       - how big the change is in money and in volume, not only in percent
       - which campaigns or factors contributed most
       - what is working and worth protecting
       - what is underperforming and what it is costing
       - what needs attention now, and why now
       - the priorities for the coming period

     Rules:
       - Every claim traceable to a figure in this report.
       - Correlation stays correlation. "Spend rose 15% while conversions rose
         17%" — not "the budget increase drove conversions".
       - Name the hedges the analysis attached: small samples, unavailable
         metrics, provisional recent conversions.
       - No generic marketing commentary. If a sentence would be true of any
         account in any month, cut it. -->

---

## KPI overview

| KPI | Current {n} days | Previous {n} days | Absolute change | % change |
|---|---:|---:|---:|---:|
| Spend | | | | |
| Impressions | | | | |
| Clicks | | | | |
| CTR | | | | |
| Avg. CPC | | | | |
| Conversions | | | | |
| Conversion rate | | | | |
| CPA | | | | |
| Conversion value | | | | |
| ROAS | | | | |
| Search impression share | | | | |
| Search lost IS (budget) | | | | |
| Search lost IS (rank) | | | | |

<!-- Paste analysis.tables.kpi rather than retyping. It is already in the
     account's currency, and rows for unavailable metrics are already absent.
     Never add a row back with a zero in it.
     A percentage change against a zero baseline reads "n/a (from zero)". -->

{One or two sentences reading the table: the two moves that matter and the one
that looks alarming but is not.}

![{alt text from the chart manifest}](charts/{stem}_kpi-change.png)

---

## Performance detail

### Campaigns

| Campaign | Type | Status | Spend | Spend Δ% | Conversions | Conv. Δ% | CPA | ROAS | Search IS |
|---|---|---|---:|---:|---:|---:|---:|---:|---:|

<!-- analysis.tables.campaigns. Top 10-15 by spend; say so if truncated. -->

![{alt}](charts/{stem}_campaign-spend-conversions.png)

{Which campaigns moved the account number, and in which direction.}

### {Trend / device / network / impression share — include only what carries a point}

<!-- A chart with no sentence beside it is decoration. Six charts and no
     argument is a data dump. -->

---

## Strengths

<!-- From findings.strengths, plus opportunities already being captured.
     Strongest first. Omit the section entirely if there is nothing real --
     an invented strength costs the whole report its credibility. -->

**{Observation, stated as a fact.}**
{Metric evidence: current vs previous, absolute and percentage.}
{Why it matters commercially — what it is worth, or what it protects.}

---

## Weaknesses and risks

<!-- From findings.weaknesses and anomalies. Order by severity, then by money.

     For each: the issue, the supporting figures, the likely impact, and
     honestly whether it is a real problem or noise. A finding carrying
     confidence: low is a thing to watch, not a thing to assert -- say which. -->

**{The issue.}**
{Supporting data.}
{Potential impact, quantified where the arithmetic supports it.}
{Confidence: what would confirm or dismiss it.}

---

## Recommended next steps

<!-- From recommended_actions, highest priority first. Each must be specific
     enough for a practitioner to start on Monday.

     Not: "improve targeting", "optimise campaigns", "increase conversions".
     Yes: "raise Search — Services' daily budget from $60 to $85 and re-check
     impression share after 14 days". -->

### 1. {Action, stated as an instruction}

- **Reason:** {why, in one sentence}
- **Supporting evidence:** {the figures that triggered it}
- **Expected impact:** {arithmetic with its assumption visible — a ceiling, not
  a forecast}
- **Priority:** High | Medium | Low

### 2. {…}

---

## Data notes

<!-- Every warning from data_quality, in plain language. Non-negotiable: this
     is what separates a report that can be trusted from one that cannot. -->

- **Periods:** {ranges, lengths, and the account time zone they were computed in}
- **Metrics unavailable this period:** {metric — why. e.g. "ROAS — the account
  records no conversion value, so return cannot be calculated. Efficiency is
  measured by CPA."}
- **Coverage:** {e.g. "Search impression share covers 14% of account
  impressions; Performance Max and Display do not report it."}
- **Sample size:** {campaigns or the account below the thresholds}
- **Queries that failed:** {dataset — what is therefore unavailable, not empty}
- **Conversion lag:** {whether recent conversions are still settling}

---

*Data retrieved from the Google Ads API on {date} for {account} ({customer ID}).
Figures are in {currency}. Current period {range}; comparison period {range}.*
```

---

## Length and shape

| Section | Target |
|---|---|
| Executive summary | 500–1,000 words |
| KPI overview | The table, plus 1–3 sentences |
| Performance detail | 2–4 short subsections, each with a chart or a table and a sentence that reads it |
| Strengths | 2–4 items |
| Weaknesses and risks | 2–5 items |
| Recommended next steps | 3–6, prioritised |
| Data notes | Every warning, however short |

Whole report: roughly 1,200–2,000 words plus tables and charts. Longer than that
and the executive summary stops being read; shorter and the recommendations
arrive without their evidence.

## Adapting it

The skeleton is fixed; the middle flexes with the account:

- **No conversion value** → no ROAS row, no ROAS chart, efficiency framed
  entirely as CPA, and a line in Data notes explaining why.
- **No conversions at all** → the tracking question *is* the report. Lead with
  it, and make no efficiency claims.
- **Performance Max-heavy** → little or no impression share. Drop the section
  and say why rather than presenting a figure that covers a sliver of the
  account.
- **Single campaign** → drop the campaign comparison and go deeper on ad groups,
  keywords and search terms.
- **New account** → no comparison period. Report absolutes, drop the change
  column, and say plainly that no baseline exists.
