# Google Analytics 4 Performance Report — {{PROPERTY NAME or "GA4 property {{ID}}"}}

**Reporting period:** {{current start}} to {{current end}} ({{n}} days)
**Comparison period:** {{previous start}} to {{previous end}} ({{n}} days)
**Property:** {{name}} ({{property_id}}) · {{time zone}} · {{currency}}
**Report generated:** {{YYYY-MM-DD}}

> Structure only. Every `{{…}}` comes from `analysis.json`. Sections marked
> *conditional* are omitted entirely when they do not apply — never left in as
> an empty heading or a table of zeros.

---

## Executive summary

500–1,000 words of prose. No bullet lists, no KPI recital.

It answers, in this order of priority rather than this order of headings:

- what happened this period, and whether the property is better or worse off;
- the two or three KPI movements that actually matter, with figures;
- what changed in acquisition, and which channels drove it;
- what changed in engagement and in key events;
- revenue and transactions, where the property sells;
- which landing pages materially moved the numbers;
- device trends where the gap is large enough to act on;
- anomalies, and — separately — anything that looks like a tracking problem
  rather than a performance problem;
- what is working, what is underperforming;
- what deserves attention first, and the highest-priority actions for next
  period.

Every conclusion carries a number from the data. Where a cause is plausible but
unproven, it is written as one: "coincides with", "may indicate", "warrants
investigation".

---

## KPI overview

{{tables.kpi — already rendered}}

Only metrics this property actually returned. Unavailable metrics are absent
from the table or read "not available" — never 0. Where the baseline was zero,
the change column says "new (was zero)" rather than a percentage.

{{![Period-over-period change by KPI](./charts/kpi-change.png)}}

---

## Performance trend

{{![Daily performance](./charts/daily-performance.png)}}

Two or three sentences on shape: where traffic built or faded within the
period, any day that stands out, and — where days returned no data — that the
totals are missing them.

---

## Acquisition performance

{{tables.channels}}

{{![Sessions by acquisition channel](./charts/channel-performance.png)}}

Winners and losers by absolute session change, not by percentage. State whether
each mover kept its key-event rate: a channel losing volume while holding its
conversion rate is a supply problem; one losing conversion rate is a relevance
problem, and they have different owners.

*Conditional:* where first-user channels are reported, they go in their own
sub-section with the distinction stated — session-scoped is where the **visit**
came from, first-user is where the **person** was originally acquired. Their
totals do not reconcile and must never share a row.

---

## Content and landing page performance

{{tables.landing_pages}}

{{![Sessions by landing page](./charts/landing-page-performance.png)}}

Insight, not a URL dump: the pages that gained or lost materially, the
high-traffic pages engaging below the property's median, and the pages carrying
a disproportionate share of key events or revenue. Pages below the traffic
floor are not judged.

---

## Key events and conversion performance

{{tables.events}}

{{![Key events by event name](./charts/key-event-performance.png)}}

Overall key events, the key-event rate, and which individual events moved.

State plainly where the business meaning of a key event is not established —
GA4 records that an event is a key event, not what it represents. Anything that
looks like a tracking concern rather than a conversion change belongs in
§ Weaknesses and risks, labelled as such.

---

## Ecommerce performance *(conditional — only when the property returned revenue)*

{{tables.ecommerce}}

{{![Revenue by acquisition channel](./charts/ecommerce-performance.png)}}
{{![Item funnel: view to purchase](./charts/ecommerce-funnel.png)}}

Transactions, revenue, purchaser rate, average purchase value, and where the
funnel gained or lost progression. Note that GA4's attribution will not tie
exactly to a payment processor.

Omit this whole section — heading included — for a property with no purchase
activity. Never present missing ecommerce tracking as zero revenue.

---

## Device performance

{{tables.devices}}

{{![Performance by device category](./charts/device-performance.png)}}

Only where the difference is large enough to act on. Quantify the gap in both
relative and absolute terms: a conversion-rate gap matters in proportion to the
sessions sitting on the weaker side of it.

---

## Strengths

Three to five, each with: the finding, the metric, the quantified change, and
why it matters. No trivial fluctuations — if it did not clear the materiality
threshold, it does not belong here.

---

## Weaknesses and risks

Each with: the issue, the supporting data, the quantified change, the potential
impact, and — explicitly — whether this is a performance problem or a possible
tracking problem. Where the data cannot separate them, say so and name the
check that would.

---

## Data quality notes

Every `fail` and every material `warn` from `data_quality.checks`, in plain
language: metrics that could not be retrieved, days with no data, unattributed
buckets, sampling or thresholding, datasets that failed to retrieve, and what
each one means for the numbers above.

This section is not optional and it is not an appendix. A reader who acts on
the report without it may be acting on a measurement artefact.

---

## Recommended next steps

Prioritised, High first. For each:

**Action** — what to do, specific enough for a marketing, SEO, paid-media, CRO
or web team to start this week.
**Reason** — why.
**Supporting evidence** — the GA4 figures behind it.
**Expected impact** — what improvement it is intended to create.
**Priority** — High / Medium / Low.
**Confidence** — High / Medium / Low, with the reason when it is not high.

Every recommendation traces to a finding above. None of them is "improve
engagement", "optimise traffic" or "focus on SEO".

---

## Appendix — method

- Data source: Google Analytics Data API, property {{property_id}}.
- Current period {{…}} vs previous period {{…}}, both {{n}} completed days in
  the property's time zone ({{tz}}). Today is excluded.
- Comparisons are period-over-period. A change is called material at ≥10% and
  above an absolute floor by metric type.
- Metrics the property does not report are shown as not available, never as
  zero.
