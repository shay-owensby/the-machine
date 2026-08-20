# Diagnostics — every rule, and what it does not claim

A finding is a pattern the data supports, not a diagnosis. The rules below fire
on arithmetic; the causes they suggest are candidates for someone who can open
the account, look at the ads, and know what the business was doing that month.

Every finding carries:

```jsonc
{ "id", "type",        // strength | weakness | anomaly | opportunity | observation
  "title", "statement",
  "evidence": ["Spend: $12,880.00 vs $11,170.00 (+$1,710.00, +15.3%)", ...],
  "severity",          // high | medium | low
  "confidence",        // high | medium | low
  "scope",             // account | campaign | segment | tracking
  "entity" }           // campaign or segment name, when scoped to one
```

`evidence` is always real figures from the retrieval. A finding whose evidence
you cannot check against the tables is a bug.

## Account-level rules

| id | Fires when | Type | Says | Does **not** say |
|---|---|---|---|---|
| `spend_outpacing_conversions` | Spend up >5% and the spend/conversion growth gap >15 points | weakness | The account bought more traffic than it converted | Which of bidding, landing pages, competition or demand caused it |
| `conversions_outpacing_spend` | Conversions up >5% and the gap runs the other way | strength | More output from roughly the same input | That the change is repeatable |
| `conversions_shift`, `conversions_value_shift`, `clicks_shift` | Material move in volume | strength/weakness | The headline volume move, against the spend move | Anything about cause |
| `cpa_shift` | Material CPA move | strength/weakness | The move, plus what it is worth at this period's volume | That CPA will stay there |
| `roas_shift` | Material ROAS move (only when conversion value exists) | strength/weakness | The move and the value behind it | That recorded value is real revenue — see `placeholder_conversion_value` |
| `ctr_shift`, `average_cpc_shift`, `conversion_rate_shift` | Material move | strength/weakness | The move | Cause |
| `cheap_traffic_low_quality` | CPC **and** conversion rate both fall materially | anomaly | Cheaper clicks converting less, consistent with lower-intent traffic | Which of traffic mix, landing page or seasonality it is — it names all three |
| `impression_share_shift` | Material impression-share move | strength/weakness | The move, and how much of the account reports IS at all | That total demand was stable |
| `budget_capped_account` | Lost IS (budget) ≥ 10% | opportunity | Demand the account did not serve | That more budget converts at the same CPA — it says diminishing returns apply |
| `rank_limited_account` | Lost IS (rank) ≥ 30% | weakness | Ad rank is the brake, so budget alone will not fix it | Whether it is bid or quality — the metric does not separate them |

## Campaign-level rules

| id | Fires when | Type | Note |
|---|---|---|---|
| `campaign_no_conversions:<id>` | Spend recorded, conversions exactly 0, ≥5% of account spend | weakness | Splits on click volume: under the sparse floor it becomes a *low*-severity "not enough traffic to call yet" with a test-window recommendation instead of a pause |
| `campaign_high_cpa:<id>` | CPA > 1.5× account CPA, not sparse | weakness | Severity rises to high at ≥15% of account spend |
| `campaign_low_cpa:<id>` | CPA < 0.6× account CPA, not sparse | strength | Titled "converts well below account CPA" — never "best campaign", which the data was not asked to establish |
| `campaign_budget_constrained:<id>` | Lost IS (budget) ≥ 10% | opportunity if its CPA is at or below account CPA, otherwise observation | Losing impressions to budget on an *inefficient* campaign is not an opportunity |
| `campaign_rank_constrained:<id>` | Lost IS (rank) ≥ 30% | weakness | |
| `campaign_paused_but_spent:<id>` | Status PAUSED but spend in the period | observation | Its period comparison is not like-for-like |
| `campaign_spend_swing:<id>` | Its spend change ≥ 40% of the account's total spend change | observation | Names what drove the account number |
| `campaign_new:<id>` | Present in the current period only | observation | "Has no comparison baseline" |
| `campaign_stopped:<id>` | Present in the previous period only | observation | Its absence is part of any decline |

Every finding about a campaign flagged `sparse_data` (under 100 clicks) is
forced to `severity: low`, `confidence: low`, with a sentence appended saying it
is a flag to check rather than a conclusion.

## Segment rules

`mix_shift:<dimension>:<label>` fires when a device or network moves **≥ 10
percentage points** of spend share between periods. The statement gives both the
share move and the absolute spend move, because a segment can gain share while
spending less — and the two readings lead to opposite decisions.

## Conversion-tracking rules

These describe patterns that are *usually* a tracking fault. None of them proves
one, and each says so.

| id | Fires when | Reading |
|---|---|---|
| `no_conversions_recorded` | Spend > 0 and conversions = 0 in the current period | Either the account genuinely converted nothing or tracking is broken. **Nothing in the API response distinguishes them.** Verify before drawing any performance conclusion |
| `no_conversion_value` | Conversions > 0, conversion value 0 or absent | ROAS is unavailable, not zero. Efficiency is CPA-only for this account |
| `placeholder_conversion_value` | Value per conversion is a flat 1.00 or 0.00 across ≥10 conversions | A default value on the conversion action, not real revenue. ROAS is then a restatement of conversion volume |
| `very_high_conversion_rate` | Conversion rate > 50% | The account is counting lightweight actions (page views, click-to-call, every-conversion counting). Not wrong, but "conversions" means interactions here |
| `inactive_conversion_actions` | Enabled actions with zero in both periods | Broken, or measuring something that stopped happening. Silent actions muddy the goal picture and dilute automated bidding signals |

## From findings to recommendations

`recommended_actions[]` is generated *from* findings — no finding, no
recommendation, and an account with nothing wrong produces none. Each carries
`action`, `reason`, `evidence[]`, `expected_impact`, `priority`, `confidence`
and `from_finding`.

Two things the generator is careful about:

**Specificity.** Actions name the campaign, the number that triggered them and
the first place to look. "Improve targeting" is not a recommendation; "audit
Search — Non-Brand Core's top spending search terms, which are converting at
$35.00 against an account average of $26.29" is.

**Fit.** The audit recommendation branches on campaign type — search terms and
negatives for Search and Shopping, asset groups and search themes for
Performance Max, placements and audiences for Display and Video. Telling someone
to audit the search terms of a Display campaign identifies the report as
automated and wrong in the same sentence.

Expected impact is stated as arithmetic with its assumption visible — "returning
to the previous CPA at this period's conversion volume is worth about $245" —
never as a forecast. Impression share does not scale linearly with budget, and
the budget recommendations say so.

## Correlation, causation, and how to write it

The data supports statements of the form *X and Y both moved*. It does not
support *X caused Y*. Two moves in the same period is the weakest possible
evidence of a mechanism: a competitor entering the auction, a landing page
change, a seasonal shift and a bidding change all look identical in this data.

Write: "CPA rose 21% while impression share fell 5 points and CPC rose 16%."
Not: "increased competition drove CPA up."

Where a cause genuinely is knowable from the data — a campaign that stopped
running, a campaign that started, a budget that was raised — name it, and say
which figure shows it.

## Tuning

Thresholds are constants at the top of `analyze_performance.py`
(`MATERIAL_PCT`, `MIN_ABS`, `SMALL_SAMPLE_CONVERSIONS`, `SPARSE_CLICKS`) and are
echoed into `analysis.thresholds` so a report can state the bar it used.
`--material-pct` overrides the percentage per run. A very small account may
justify a lower absolute floor; change it deliberately, and say in the report
that you did.
