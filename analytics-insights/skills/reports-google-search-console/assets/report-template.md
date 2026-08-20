# Report template

The structure the `google-search-console` agent produces, written to
`analytics-insights/google-search-console/YYYY-MM-DD/google-search-console-report-YYYY-MM-DD.md`
in the client project.

Guidance is in `<!-- comments -->`; strip them from the finished report.
Everything else is the shape of the document. Sections whose data is unavailable
are **removed and named in Data notes**, never filled with zeros.

---

```markdown
# {Client name} — Organic Search Performance Report

**Property:** `{site_url}` ({domain | URL-prefix} property)
**Reporting period:** {current start} – {current end} ({n} days)
**Comparison period:** {previous start} – {previous end} ({n} days)
**Latest finalised Search Console data:** {freshness.latest_final}
**Search type:** {Web Search}
**Prepared:** {report date}

<!-- All five lines, always. Search Console lags real time; stating the latest
     finalised date pre-empts "why does this stop three days ago?" before it is
     asked. The property type matters too: a domain property includes subdomains
     a URL-prefix property never sees. -->

---

## Executive summary

<!-- 500-1,000 words of prose. No bullets, no headings inside it. Written for
     someone who will read this section and skim the rest.

     Cover, in the order this property's own story dictates:
       - how organic performance changed: clicks, impressions, CTR, position
       - WHERE the click change sits — visibility or click-through rate
         (analysis.click_attribution says which, and says it is arithmetic)
       - which queries and which pages contributed most, named and quantified
       - where visibility grew and where it went
       - the ranking opportunities and the CTR opportunities that are worth
         acting on, and which is which
       - device and geographic movement, only where it changes the picture
       - anomalies worth knowing about, and indexing concerns if any surfaced
       - what is working, what is underperforming, what needs attention now
       - the highest-priority actions for the next period

     Rules:
       - Every claim traceable to a figure in this report.
       - Correlation stays correlation. "Clicks fell 31% while average position
         held at 9.8" — not "the algorithm update cost us traffic".
       - Distinguish clicks from impressions from CTR from position. They are
         four different stories and conflating them is the standard failure.
       - A falling average position is an IMPROVEMENT. Say so in words.
       - Name the hedges the analysis attached: small samples, capped extracts,
         withheld query rows, unavailable datasets.
       - Do not narrate every KPI in order. Lead with what materially changed.
       - No generic SEO commentary. If a sentence would be true of any site in
         any month, cut it. -->

---

## KPI overview

| KPI | Current {n} days | Previous {n} days | Absolute change | % change |
|---|---:|---:|---:|---:|
| Clicks | | | | |
| Impressions | | | | |
| CTR | | | | |
| Average position *(lower is better)* | | | | |

<!-- Paste analysis.tables.kpi rather than retyping. CTR is already formatted as
     a percentage, with the absolute change in percentage POINTS and the % change
     relative — both true, not interchangeable.
     A percentage change against a zero baseline reads "n/a (previous period was
     zero)". Never add a row back with a zero in it. -->

{One or two sentences reading the table: the two moves that matter, and the one
that looks alarming but is not.}

![{alt text from the chart manifest}](charts/{stem}_kpi-summary.png)

---

## Organic search trend

![{alt}](charts/{stem}_organic-click-trend.png)

![{alt}](charts/{stem}_organic-impression-trend.png)

<!-- Include the CTR and position trends only where they carry a point the click
     and impression charts do not. -->

{What the shape shows: steady change, a step, or one event. Use
 analysis.trend.shape for the within-period trend — a flat 30-day total can hide
 a falling second half. Name accepted anomalies with their dates and say plainly
 whether they are worth acting on. Do not narrate ordinary weekday/weekend
 variation.}

---

## Query performance

{Top queries by clicks — 5-10, not an export.}

{Largest gains, largest losses, each with the numbers and what moved:
 impressions, position, or CTR.}

<!-- analysis.tables.top_queries / query_winners / query_losers.
     State once, here or in Data notes, that Search Console withholds query rows
     (anonymised queries especially), so these totals sit below the property
     totals in the KPI table. analysis.queries.reconciliation.coverage_pct has
     the figure for this property. -->

---

## Page performance

{Top pages, pages gaining visibility, pages losing it — quantified.}

<!-- analysis.tables.top_pages / page_winners / page_losers.
     Distinguish the kinds of loss (analysis.pages.visibility_losses[].loss_kind):
     traffic loss, visibility loss, CTR loss, ranking loss. They need different
     fixes and treating them alike produces the wrong recommendation. -->

![{alt}](charts/{stem}_page-performance.png)

---

## Search opportunity analysis

<!-- The most compelling opportunities, each with: query and/or page, current
     position, impressions, clicks, CTR, the relevant period-over-period
     movement, and why it is an opportunity.

     Keep the four kinds apart:
       CTR opportunities       — presentation. Title, description, snippet
                                 eligibility. Does NOT move rankings.
       Ranking opportunities   — positions 4-10 and 11-20 with real impressions.
                                 Slower, less certain, bigger.
       Content opportunities   — queries with visibility and no page that
                                 properly answers them.
       Technical / indexing    — pages that cannot perform until they are indexed
                                 as intended. A prerequisite, not an optimisation. -->

### CTR opportunities

{analysis.tables.page_ctr_opportunities and query_ctr_opportunities.}

<!-- Each row is judged against THIS PROPERTY'S OWN median CTR at the same
     position band — not an industry benchmark, which this data does not contain.
     Say so. The "clicks at band median" figure is a ceiling at today's
     impressions, not a forecast. -->

### Ranking opportunities

{analysis.tables.query_ranking_opportunities.}

<!-- Search Console shows visibility, not commercial value. Where relevance
     cannot be established from this data, say so rather than assuming a query
     with impressions is a query worth winning. -->

![{alt}](charts/{stem}_search-opportunities.png)

---

## Device and geographic insights

<!-- Include ONLY where there is an actionable or strategically relevant finding.
     A device split that mirrors last period is not a section. Devices under 3%
     of clicks are flagged `negligible` and should not carry a paragraph.
     A country growing at the property's own rate is the property seen through
     one market — the analysis only flags markets that diverge from the trend. -->

---

## Strengths

<!-- From findings.strengths. Strongest first. Omit the section entirely if there
     is nothing real — an invented strength costs the whole report its
     credibility. -->

**{Observation, stated as a fact.}**
{Metric evidence: current vs previous, absolute and percentage.}
{Why it matters — what it is worth, or what it protects.}

---

## Weaknesses and risks

<!-- From findings.weaknesses, risks and anomalies. Order by severity, then by
     the click volume involved.

     For each: the issue, the supporting figures, the potential impact, and
     honestly whether it is a real problem or noise.
       - Ranking loss is not CTR loss.
       - Visibility loss is not traffic loss.
       - A reporting artefact is not a performance problem.
       - confidence: low is a thing to watch, not a thing to assert — say which.

     Carry the finding's `caveat` with it. If the caveat is inconvenient, the
     claim was too strong. -->

**{The issue.}**
{Supporting data.}
{Potential impact, quantified where the arithmetic supports it.}
{What would confirm or dismiss it.}

---

## Recommended actionable next steps

<!-- From recommended_actions, highest priority first. Each must be specific
     enough for an SEO strategist, a content team, a developer or a CRO team to
     start on Monday.

     Not: "improve SEO", "optimise rankings", "write more content", "improve
     CTR", "fix technical SEO".

     Yes: "Rewrite the title and meta description for /example-page/, which
     generated 42,000 impressions at average position 4.8 but only 1.2% CTR
     against a 4.9% median for this site's own pages in positions 4-10." -->

### 1. {Action, stated as an instruction}

- **Reason:** {why, in one sentence}
- **Supporting evidence:** {the Search Console figures that triggered it}
- **Expected impact:** {the arithmetic with its assumption visible — a ceiling,
  not a forecast; and whether it is a CTR lever or a ranking lever}
- **Priority:** High | Medium | Low
- **Confidence:** High | Medium | Low

### 2. {…}

---

## Data notes

<!-- Every warning from data_quality, in plain language, plus the standing
     limitations that apply. Non-negotiable: this is what separates a report that
     can be trusted from one that cannot. -->

- **Periods:** {both ranges, their lengths, and the latest finalised date}
- **Data state:** {finalised data only; N provisional days excluded}
- **Query and page coverage:** {e.g. "Query-level rows account for 71% of the
  property's clicks. Search Console withholds rows, anonymised queries above all,
  so query tables describe the visible subset rather than all organic traffic."}
- **Average position:** {an impression-weighted average across every query the
  property appeared for — not a fixed keyword rank; it moves when the query mix
  moves}
- **Search Console vs analytics:** {clicks are not sessions and impressions are
  not visits; these figures will not reconcile with GA4 and are not meant to}
- **Datasets unavailable this period:** {what failed and what is therefore
  unavailable — not empty}
- **Sample size:** {where volumes are too low for confident conclusions}
- **Search type:** {Web Search only; other surfaces reported separately if at all}

---

*Data retrieved from the Google Search Console API on {date} for `{site_url}`.
Current period {range}; comparison period {range}. Latest finalised Search
Console date {date}.*
```

---

## Length and shape

| Section | Target |
|---|---|
| Executive summary | 500–1,000 words |
| KPI overview | The table, plus 1–3 sentences |
| Organic search trend | 1–2 charts and a paragraph that reads them |
| Query performance | 1–2 tables, 5–10 rows each, with commentary |
| Page performance | 1–2 tables with commentary |
| Search opportunity analysis | 3–8 opportunities, CTR and ranking kept apart |
| Device / geographic | 0–2 short paragraphs, or omitted |
| Strengths | 2–4 items |
| Weaknesses and risks | 2–5 items |
| Recommended next steps | 3–6, prioritised |
| Data notes | Every warning, however short |

Whole report: roughly 1,500–2,500 words plus tables and charts. Longer and the
executive summary stops being read; shorter and the recommendations arrive
without their evidence.

## Adapting it

The skeleton is fixed; the middle flexes with the property:

- **No comparison period** (new property) → drop every change column, report
  absolutes, and state plainly that no baseline exists. Do not call it growth.
- **Very low traffic** → lead with direction and opportunity, not significance.
  Say once that percentage changes on this volume are not meaningful.
- **Publisher / high volume** → the long tail matters; note whether the extract
  was chunked, and lead with page-level movement over individual queries.
- **Ecommerce** → product pages and search appearance features carry the story;
  category-level page grouping usually beats a flat page list.
- **Local / multi-location** → location pages as a group, and the country and
  device sections earn their place more often than elsewhere.
- **No brand terms configured** → no branded/non-branded section, and one line in
  Data notes saying it requires configuration. Never estimate the split.
- **CTR fell, rankings held** → this is the report. Lead with it, keep it
  separate from ranking work, and do not promise ranking gains from metadata.
- **Indexing problems found** → treat as a prerequisite section before the
  optimisation recommendations, and keep point-in-time index status visibly
  separate from the 30-day trend.
