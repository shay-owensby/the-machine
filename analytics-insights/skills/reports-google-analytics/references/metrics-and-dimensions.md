# Metrics, dimensions, and what GA4 will and will not tell you

Every field name below is a **Google Analytics Data API** API name, not a GA4
interface label. The two differ often enough to matter: the interface says
"Views", the API says `screenPageViews`.

---

## The schema is asked, never assumed

Before any reporting request, the fetch calls:

```
GET properties/{id}/metadata
```

That returns every dimension and metric **this property** supports, custom
definitions included. Requests are filtered against it, so:

- a field this property does not carry is dropped with a reason, instead of
  returning a 400 that kills the whole run;
- custom dimensions and custom metrics are discovered rather than guessed;
- the report can state which metrics were unavailable and why.

A dropped metric is recorded in `schema_support.unsupported_metrics` and
surfaces in the analysis as **not available** — never as zero.

Where a field exists but cannot be paired with a given dimension, the API
returns a 400. The fetch answers that by calling
`properties/{id}:checkCompatibility`, re-requesting only the compatible
metrics, and recording what it had to leave out. The breakdown loses a column;
the run does not lose the dataset.

---

## Key events, under two names

Google renamed conversions to **key events** in 2024. Which name a property
answers to is discovered, not assumed:

| Current | Pre-2024 | Meaning |
|---|---|---|
| `keyEvents` | `conversions` | Count of key events |
| `sessionKeyEventRate` | `sessionConversionRate` | Share of sessions with at least one |
| `userKeyEventRate` | `userConversionRate` | Share of active users with at least one |

Whichever pair the property supports is used. Downstream, the legacy names are
normalised to the current ones so there is one name in the analysis — while
`key_events.metric_naming` preserves the property's own wording, so the report
can match the interface the client actually looks at.

**GA4 records which events are key events. It does not record what they mean.**
A key event may be a purchase, a form submission, a phone tap, a newsletter
signup, or a scroll to 90%. Where the meaning is not established — from
`GA4_KEY_EVENTS`, from the Admin API definitions, or from the client — the
report says the meaning is undetermined. It does not call a key event a lead or
a sale.

---

## Core KPIs

Requested for both periods with no dimension. Every one is checked against the
property schema first.

| API name | Report label | Unit | Better when | Note |
|---|---|---|---|---|
| `activeUsers` | Active Users | count | higher | Users who engaged |
| `totalUsers` | Total Users | count | higher | Everyone GA4 saw |
| `newUsers` | New Users | count | context | Growth signal or churn signal, depending on what returning users did |
| `sessions` | Sessions | count | higher | Volume, not value |
| `engagedSessions` | Engaged Sessions | count | higher | >10s, or a key event, or 2+ views |
| `engagementRate` | Engagement Rate | % | higher | Engaged ÷ sessions |
| `bounceRate` | Bounce Rate | % | lower | **Exactly** 1 − engagement rate |
| `averageSessionDuration` | Avg. Session Duration | seconds | higher | |
| `userEngagementDuration` | — | seconds | context | Retrieved, not tabled |
| `screenPageViews` | Views | count | higher | Pages and screens |
| `screenPageViewsPerSession` | Views per Session | ratio | higher | Derived when absent |
| `sessionsPerUser` | Sessions per User | ratio | context | Loyalty, or stalled acquisition |
| `eventCount` | Event Count | count | context | Moves with traffic *and* with tagging |
| — | Events per Session | ratio | context | Derived: `eventCount ÷ sessions` |
| `keyEvents` | Key Events | count | higher | Meaning is a property question |
| `sessionKeyEventRate` | Session Key Event Rate | % | higher | |
| `userKeyEventRate` | User Key Event Rate | % | higher | |

Three of these are **derived** when the property does not return them directly
(`screenPageViewsPerSession`, `sessionsPerUser`, `eventsPerSession`). Deriving
is arithmetic on figures the API did return — no gap is filled with an
assumption — and each derived KPI carries a note saying so.

### Bounce rate is not an independent finding

In GA4, `bounceRate = 1 − engagementRate`, exactly. They are one number
reported twice. The analysis checks this holds and says so, so the report does
not list "engagement up" and "bounce down" as two separate wins.

---

## Ecommerce

| API name | Label |
|---|---|
| `totalRevenue` | Total Revenue (purchases + subscriptions + ads) |
| `purchaseRevenue` | Purchase Revenue |
| `transactions` / `ecommercePurchases` | Transactions / Ecommerce Purchases |
| `totalPurchasers` / `firstTimePurchasers` | Purchasers / First-time Purchasers |
| `purchaserRate` | Purchaser Rate |
| `averagePurchaseRevenue` | Avg. Purchase Revenue |
| `averageRevenuePerUser` | Revenue per User |
| `itemsViewed`, `itemsAddedToCart`, `itemsCheckedOut`, `itemsPurchased` | Funnel steps |
| `addToCarts`, `checkouts` | Event-level cart and checkout activity |
| `cartToViewRate`, `purchaseToViewRate` | Item progression rates |

**Every GA4 property carries these in its schema whether or not the site sells
anything.** Their presence proves nothing; only returned values do. So:

| State | What it means | What the report does |
|---|---|---|
| `active` | Non-zero purchase activity returned | Full ecommerce section |
| `no_data` | Metrics returned, all zero | **Omit the section.** GA4 cannot distinguish "sells nothing" from "purchase events not sent", and neither should the report |
| `unavailable` | No value returned at all | Omit, and record as unavailable |

A zero GA4 explicitly returned is a real zero and is described as "no purchases
recorded". Never as revenue of zero implying lost sales.

---

## Acquisition: two different questions

This is the distinction most GA4 reports get wrong.

| Scope | Dimensions | Answers |
|---|---|---|
| **Session** | `sessionDefaultChannelGroup`, `sessionSource`, `sessionMedium`, `sessionSourceMedium`, `sessionCampaignName` | Where did this **visit** come from? |
| **First user** | `firstUserDefaultChannelGroup`, `firstUserSource`, `firstUserMedium`, `firstUserSourceMedium`, `firstUserCampaignName` | Where was this **person** originally acquired, however long ago? |

They answer different questions, their totals do not reconcile, and a
first-user metric must never sit in the same row as a session-scoped one. A
user first acquired through Organic Search in March and returning via Email in
August is one first-user Organic row and one session-scoped Email row.

Session-scoped is the default throughout this skill. First-user channels are
retrieved separately, tabled separately, and labelled.

---

## Content

| Dimension | Meaning |
|---|---|
| `landingPagePlusQueryString` (or `landingPage`) | Session **entry** page |
| `pagePath` | Any page viewed |
| `pageTitle` | Its title |
| `hostName` | Which host served it — the tell for a subdomain or a staging site in the same property |

Landing pages and pages are different populations. A page can be heavily viewed
and rarely entered on, and the reverse. Sessions belong to landing pages; views
belong to pages.

Pages below the traffic floor (default 100 sessions) are not judged at all. A
page with nine sessions and no key events has told you nothing.

---

## Technology and geography

`deviceCategory` (desktop / mobile / tablet), `browser`, `operatingSystem`,
`platform`; `country`, `region`, `city`.

Device is analysed by default. Geography is retrieved but only reported where
the differences are large and the samples are not tiny — a 300% rise from four
sessions to sixteen is not a market opening up. City-level rows are frequently
below the level GA4 will report at all.

---

## Events

`eventName` with `eventCount`, `keyEvents`, `totalUsers`, `eventValue`.

The analysis separates:

- **key events** — what the property marks as significant;
- **automatically collected events** — `page_view`, `session_start`,
  `first_visit`, `user_engagement`, `scroll`, `click`, and the enhanced
  measurement set. These track traffic and tagging, not intent, and are labelled
  as such;
- **everything else** — custom events, whose meaning depends on the
  implementation.

Three patterns are watched for, because each is more often a tagging change
than a behaviour change: an event that **stopped firing**, an event that
**newly appeared**, and an established event whose volume **swung by 60% or
more**.

---

## Request shape limits

The Data API caps a request at ~10 metrics and ~9 dimensions. Requests are
chunked at 9 metrics, and **the sort metric rides in every chunk** — without it,
chunk 2 comes back ordered differently, and a top-50 from chunk 1 merges with a
different fifty rows into a table of numbers that never coexisted.

Row caps are applied per breakdown (50 for channels, 100 for pages). A
breakdown that hits its cap is flagged: the list is the top rows by the sort
metric, not the whole property, and totals must not be summed from it.

---

## What the API tells you about its own answer

Every response carries `ResponseMetaData`, and all of it is captured:

| Field | Meaning | Why it matters |
|---|---|---|
| `dataLossFromOtherRow` | Cardinality limit hit; rows folded into `(other)` | Row figures are incomplete; shares will not add up |
| `subjectToThresholding` | Rows withheld for privacy | Small segments may be missing entirely |
| `emptyReason` | Why nothing came back | Distinguishes "no data" from "no such thing" |
| `samplingMetadatas` | The response is sampled | Figures are estimates, not counts |
| `currencyCode`, `timeZone` | The property's own settings | The authority when the Admin API is unavailable |

Each of these becomes a data-quality warning in the analysis rather than a
silent footnote in a log.
