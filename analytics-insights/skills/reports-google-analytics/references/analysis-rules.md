# Analysis rules

The rules that turn numbers into findings. They are written down here because
the difference between a useful report and a misleading one is almost never the
arithmetic.

---

## 1. Unavailable is not zero

Three states, kept distinct all the way to the page:

| State | Means | Renders as |
|---|---|---|
| `available` | The API returned a number | The number |
| `partial` | Returned for one period only | The value, and "no comparable figure last period" |
| `unavailable` | Not returned for either period | **"not available"** |

A metric this property does not support is `None` from retrieval through
analysis to output, and no code path converts it to 0. In CSVs it is an empty
cell. A zero GA4 explicitly returned is a real zero and is reported as such —
"no key events were recorded", not "key events fell to zero".

---

## 2. A number is not a verdict

Direction is arithmetic. Verdict needs to know what the metric means.

| `better_when` | Verdict when up | Applies to |
|---|---|---|
| `higher` | improved | sessions, engaged sessions, engagement rate, key events, revenue |
| `lower` | declined | bounce rate |
| `context` | **ambiguous, always** | new users, sessions per user, event count, events per session, items viewed |

Metrics marked `context` never get a good/bad label from direction alone. Event
count rising 40% is not a win; it is a fact that needs a cause.

### The cross-checks that override the arithmetic

- **Sessions down, key events or revenue up** → sessions are re-labelled
  *ambiguous*, with the note that this is a mix change and not lost
  performance. Fewer, better sessions is a good period.
- **Sessions up, key events down** → sessions carry the note that the extra
  traffic did not bring outcomes with it. Volume is not the story.
- **Engagement rate and bounce rate** are checked to sum to 100% and reported
  as one finding.

---

## 3. Materiality: both proportion and volume

A change is material when it clears **both** thresholds:

- **≥ 10%** proportionally (`--material-pct`), **and**
- an absolute floor by unit: 50 (counts), 5 (key events and ratios),
  1 percentage point (rates), 100 (currency), 5 seconds (duration).

Ten percent of nothing is nothing. Two percent on a large property is noise.
A change that clears one threshold and not the other is recorded with its
numbers and marked immaterial, so the report can leave it out without losing
it.

---

## 4. Percentage change against zero is undefined

Not infinite. Not 100%. Not a dash that reads like zero.

| Previous | Current | Result |
|---|---|---|
| 0 | 0 | 0% change, "zero in both periods" |
| 0 | > 0 | `percent_change: null`, verdict **new**, "report the absolute figure instead" |
| null | any | `availability: partial`, no comparison |

When the **whole comparison period** is empty, no comparison rule runs at all.
The analysis emits one finding — *the comparison period has no data to compare
against* — and the report presents this period as a first baseline. Nothing is
called a strength or a weakness when there is nothing to compare it to.

---

## 5. Small samples do not produce confident conclusions

Two floors, and they are different:

- **Per segment: 100 sessions** (`--min-sessions`). Below it, a channel, page
  or device is not judged on rate metrics. Landing pages below it are not
  judged at all.
- **Per property: 1,000 sessions** (ten times the segment floor). Below it,
  *every* property-level finding drops to low severity and low confidence and
  says why.

Key events have their own floor: below **15** in either period, conversion
findings are downgraded. Six key events becoming nine is a two-percentage-point
swing in the rate and pure noise.

Findings are downgraded rather than deleted. The movement did happen; what
changes is how much weight it can carry.

---

## 6. Correlation is not cause

No finding in this skill says one thing caused another. Where a cause is
plausible but unproven the wording is deliberate:

> is associated with · coincides with · may indicate · warrants investigation ·
> is consistent with · points at

"Sessions rose while key events fell" is a fact. "The new traffic was lower
quality" is a hypothesis, and it is written as one.

---

## 7. A tracking problem and a performance problem look identical

This is the single most consequential rule. Anything that could be either is
reported as both possibilities, with the check that separates them.

The patterns that trigger it:

| Pattern | Why it is ambiguous |
|---|---|
| A day with **no rows at all** | No recorded events. An outage or a genuine gap — GA4 cannot tell you which |
| An event that **stopped firing** | Steady volume to zero is a tag, consent or release change until proven otherwise |
| **Event count** moving 40 points more than sessions | Events per session does not swing that far on behaviour alone |
| **Key events at zero** while key events are defined | A measurement failure reported as a business result would be a lie |
| A large **direct traffic** rise | As often lost attribution — stripped UTMs, a redirect, an app hiding the referrer — as real direct demand |
| A large **`(not set)` / `(other)`** bucket | Cardinality limits or failed attribution, not a real segment |

**When days are missing, every volume decline in the period is caveated
automatically**: confidence drops to low and each statement gains a sentence
saying how much of the period is missing and that the true size of the change
cannot be stated until the gap is explained.

---

## 8. Findings

```json
{
  "id": "key_event_rate_decline",
  "type": "strength | weakness | risk | opportunity | anomaly | observation",
  "title": "one line",
  "statement": "what was observed, and what cannot be concluded from it",
  "evidence": ["each entry a number from the data"],
  "severity": "high | medium | low",
  "confidence": "high | medium | low",
  "scope": "property | acquisition | content | events | device | geo | ecommerce | tracking",
  "entity": "the channel, page or event, when it has one"
}
```

Every evidence line carries actual figures for both periods. A finding with no
number in its evidence is a finding that should not have been written.

---

## 9. Recommendations

One per finding that supports one. **No finding, no recommendation.** Each
carries:

**Action** · **Reason** · **Supporting evidence** · **Expected impact** ·
**Priority** (High/Medium/Low, from severity) · **Confidence**, plus
`from_finding` — the ID of the finding it came from, so nothing in the report
is untraceable.

They are deduplicated by action text, keeping the highest priority instance,
and sorted by priority.

A recommendation must be specific enough for a named team to act on this week.
"Improve engagement" is not a recommendation. "Review /pricing against the
property's better-engaging entry pages: load time, above-the-fold match to the
traffic source's promise, and the first action available" is.

---

## 10. What is checked, in order

1. **KPI cross-checks** — traffic vs key events, engagement, key-event rate,
   event volume vs traffic, new-user mix, revenue vs traffic
2. **Acquisition** — channel winners and losers by absolute session change,
   with share of total
3. **Content** — high-traffic pages engaging below the landing-page median,
   high-traffic pages with zero key events, and material entrance movers
4. **Device** — desktop vs mobile key-event rate gap, only when both clear the
   session floor and the relative gap exceeds 25%
5. **Events** — stopped, new, and 60%+ swings; key events defined but silent
6. **Trends** — days with no data, robust-z-score spikes and drops (median and
   MAD, so one spike cannot hide itself), and first-half vs second-half drift
7. **Ecommerce** — funnel step-rate regressions, order value vs order count
8. **Geography** — only where a market moved materially and cleared the floor
9. **Data quality** — every check in `data-quality.md`
