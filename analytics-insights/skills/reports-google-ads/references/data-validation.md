# Data validation

Validation runs **before** any conclusion is drawn, and its output is part of
the contract. A report that quietly drops these warnings claims more certainty
than the data supports.

Everything lands in `analysis.data_quality`:

```jsonc
{ "checks":              [ { "check", "result", "ok", ... } ],
  "warnings":            [ "..." ],
  "errors":              [ { "dataset", "message", "error_code", "hint", "retryable" } ],
  "unavailable_metrics": [ { "metric", "reason" } ],
  "insufficient_data":   [ { "scope", "entity", "reason" } ] }
```

## The checks

**1. Reporting periods.** Both windows, their lengths, how they were chosen, and
the time zone they were computed in. `ok: false` when the periods are different
lengths — allowed, but then totals are not comparable and every table must say
so.

**2. Campaign spend reconciles to account spend.** Campaign rows are summed and
compared against the independently queried account total, per period, with a
0.5% tolerance. A mismatch means the campaign list is not the whole account
(something failed, something paged short, something is attributed above campaign
level) and **campaign figures must not be presented as a complete breakdown**.
This is the check that catches a silently truncated retrieval.

**3. Daily coverage.** Days that returned rows versus days requested. A gap is
not automatically wrong — a day with no activity returns no row — but a large
gap can mean the account was paused for part of the period, which changes what
the totals mean.

**4. Metric availability.** Every KPI is classified `available`, `partial` or
`unavailable`, and the unavailable ones are listed with the reason.

**5. Sample size.** Accounts under 30 conversions and campaigns under 100 clicks
are named in `insufficient_data`, with the numbers that put them there.

**6. Account flags.** Manager accounts and test accounts produce warnings loud
enough to stop a report: a manager account has no campaigns and a test account's
figures are synthetic.

**7. Query failures.** Every entry in the raw file's `errors[]` becomes a
warning phrased for a report: *"Query failed: … The 'search_terms.current'
section of this report is unavailable, not empty."*

**8. Impression-share coverage.** What share of account impressions the
impression-share figure actually covers, and how many campaigns report it at
all. Below 90%, a warning — on a Performance Max-heavy account, an
"account impression share" of 54% may describe 14% of the impressions.

## Unavailable is not zero

The single rule this whole layer exists to enforce.

| Situation | Correct handling | Wrong handling |
|---|---|---|
| API omitted the field | `null`, "not available" | `0` |
| API returned `0` | `0`, reported as zero | "no data" |
| Query failed | section `null`, warned, named | empty list treated as "nothing found" |
| Derived rate with a zero denominator | `null`, availability `partial` | `0.00%` |
| Campaign type cannot report the metric | excluded from weighted account figures | counted as `0`, dragging the account figure down |

`ads.accumulate()` returns `None` when *no* row carried a metric, and
`ads.weighted_mean()` skips missing values rather than treating them as zero and
reports how much weight it actually used. `safe_div()` returns `None` rather
than `0` for `0/0`.

## Detecting suspect conversion tracking

From the retrieved data alone, four patterns are detectable. None proves a
fault; each is worth checking before the period's performance is interpreted.

1. **Spend with zero conversions.** Genuinely converted nothing, or not tracked.
   Indistinguishable from the API. Verify before drawing any efficiency
   conclusion — and if it cannot be verified, report the ambiguity rather than
   the CPA.
2. **Conversions with no value.** Normal for lead generation. ROAS is
   unavailable, not zero, and the report measures efficiency by CPA.
3. **Flat per-conversion value** (exactly 1.00 or 0.00 across ten or more
   conversions). A default set on the conversion action, so "ROAS" is conversion
   volume wearing a currency symbol. A change in it is a change in volume.
4. **Conversion rate above 50%.** The account is counting lightweight actions.
   Read "conversions" as interactions unless the conversion-action list says
   otherwise.

Plus, from `conversion_actions_meta`: actions that are **enabled and silent in
both periods**, and actions excluded from the `conversions` metric — the second
explains why per-action figures do not sum to the headline number.

## What blocks a report

| Condition | Action |
|---|---|
| Authentication or permission failure | **Stop.** No report. Report the credential problem |
| Account and campaign data both unavailable | **Stop.** There is nothing to report |
| Target is a manager account | **Stop.** Wrong account |
| Target is a test account | **Stop.** Synthetic figures must never reach a client |
| Account name does not match the client | **Stop.** Wrong customer ID |
| Optional datasets failed | Continue; name each unavailable section |
| Campaign spend does not reconcile | Continue; do not present campaign figures as complete |
| Small samples | Continue; keep every hedge the analysis attached |
| No conversions recorded | Continue; lead the report with it |

## Verifying by hand

Two checks worth doing before a report goes out, both cheap:

```bash
# Does the KPI table's spend match the raw file's account total?
python3 -c "
import json,sys
raw=json.load(open(sys.argv[1]))
rows=raw['datasets']['account_totals']['current']
print(sum(int(r['metrics']['costMicros']) for r in rows)/1e6)
" <file>_raw.json
```

and open the Google Ads UI on the same date range. Small differences are normal
— attribution restates, and the UI's default date range is not this one — but a
difference of more than a few percent means the window, the account, or the
attribution setting is not what the report assumes. Chase it before publishing,
not after.
