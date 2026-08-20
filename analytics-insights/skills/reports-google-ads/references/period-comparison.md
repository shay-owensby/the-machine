# Periods and period-over-period maths

## The default window

- **Current period**: the most recent 30 *completed* days — ending yesterday.
- **Previous period**: the 30 days immediately before that, contiguous, no gap.

For a run on 19 August 2026: current `2026-07-20 .. 2026-08-18`, previous
`2026-06-20 .. 2026-07-19`.

Two decisions inside that:

**Yesterday, not today.** A partial day compared against a whole one produces a
decline that did not happen. Today is never included.

**The account's time zone, not the machine's.** Google Ads days are account-time-zone
days. `fetch_google_ads.py` reads `customer.time_zone` first and computes the
window in it. On a machine in London reporting a New York account, using local
dates shifts the window by a day and quietly moves spend between periods. If the
zone cannot be resolved, the run falls back to local dates **and says so in the
warnings**.

## Overriding the window

```bash
--days 30                                   # both periods, kept equal
--end-date 2026-08-18                       # move the current period's last day
--current 2026-07-01:2026-07-31 --previous 2026-06-01:2026-06-30
```

Explicit periods of different lengths are allowed — calendar months are not the
same length — but the run warns, and **every table built on unequal periods must
say so**, because totals are then not comparable and percentage changes mislead.
Prefer equal 30-day windows unless the client reports on calendar months.

## Conversion lag

Conversions are attributed to the *click* date, so the last few days of any
window keep gaining conversions for days or weeks afterwards. A report written
on day 1 will show a lower recent CPA than the same report re-run a fortnight
later.

- `GOOGLE_ADS_LAG_DAYS=3` (or `--days`-adjacent config) moves the whole window
  back by that many days, so the current period is fully settled.
- Without a lag buffer, say so in the report: recent-period conversions are
  provisional and will rise.
- Long-lag accounts (considered purchases, B2B, anything with a sales cycle of
  weeks) need a lag buffer or their most recent period always looks worse than
  it is. This is the single most common false "performance is declining" finding.

## The change record

Every KPI produces:

```jsonc
{
  "key": "cost_per_conversion", "label": "CPA", "unit": "currency",
  "better_when": "lower",
  "current": 26.29, "previous": 26.79,
  "absolute_change": -0.50, "percent_change": -1.87,
  "availability": "available",     // available | partial | unavailable
  "direction": "down",             // arithmetic: up | down | flat | n/a
  "verdict": "flat",               // interpretation
  "material": false,
  "notes": ["Below the materiality threshold ..."]
}
```

### Availability

| Value | Meaning | In a table |
|---|---|---|
| `available` | Both periods returned it | Print the numbers |
| `partial` | One period only — not returned, or a derived rate whose denominator was zero | Print the one period, no comparison; say why |
| `unavailable` | Neither period | Omit the row, or print "not available" — **never 0** |

### Percentage change

`(current - previous) / |previous| * 100`, with three exceptions:

| Case | Result | Why |
|---|---|---|
| previous = 0, current > 0 | `percent_change: null`, `verdict: "new"` | Division by zero is undefined; "+100%" and "+∞" are both fabrications |
| previous = 0, current = 0 | `0.0`, `verdict: "flat"` | Genuinely unchanged |
| either side missing | `null`, `availability` not `available` | Nothing to compare |

The KPI table prints `n/a (from zero)` in that first case. Report the absolute
change instead, and say the previous period was zero.

### Direction versus verdict

`direction` is arithmetic. `verdict` is what it means for the account:

| Metric | `better_when` | Reasoning |
|---|---|---|
| Clicks, CTR, conversions, conversion rate, conversion value, ROAS, impression share | `higher` | More is better, all else equal |
| Avg. CPC, CPA, lost IS (budget), lost IS (rank) | `lower` | Cheaper or less lost is better, all else equal |
| **Spend, impressions** | `context` | An input, not a result. Spending less is only good if the account was wasting it; spending more is only bad if it bought nothing. Verdict is always `ambiguous`. |

Two cross-checks then qualify the verdict rather than reversing it:

- Spend down **and** conversions down adds: *the saving is not efficiency — the
  account bought less.*
- Spend up with CPA flat or improving adds: *that is scale, not waste.*
- CPC down **and** conversion rate down produces a separate `anomaly`: cheaper
  clicks that convert less are consistent with lower-intent traffic — and also
  with a landing page change or seasonality. The finding says all three.

### Materiality

A change is `material` only when it is **both** proportionally and absolutely
big:

| | Threshold |
|---|---|
| Percentage | `|% change| >= 10` (`--material-pct` to change) |
| Currency metrics | `>= 25` in account currency |
| Count metrics | `>= 25` |
| Rate metrics (CTR, conversion rate, share) | `>= 0.5` percentage **points** |
| Ratio metrics (ROAS) | `>= 0.1` |

Immaterial moves get `verdict: "flat"` and a note. They stay in the KPI table —
readers want the number — but they do not become findings, and they must not
become recommendations. A report where every metric is a story is a report
nobody finishes.

### Small samples

Below **30 conversions** in the current period, every conversion-derived metric
(CPA, conversion rate, ROAS) is noisy: one extra conversion moves CPA several
percent. The analysis:

- adds an `insufficient_data` entry at account scope,
- sets `confidence: "low"` on conversion-derived findings,
- downgrades those findings from `high` severity to `medium`.

Campaigns under **100 clicks** are flagged `sparse_data`, listed in
`insufficient_data`, and every finding about them is forced to low severity and
low confidence. They are still reported — a starved campaign is worth seeing —
but never as a conclusion.

## Percentage points versus percent

Rate metrics move in **points**. CTR going 2.00% → 2.50% is *+0.50 points*, or
*+25%* relative. Both are true and they sound very different. The tables print
the absolute change in points (`+0.50 pp`) and the relative change as a
percentage, side by side, so neither can be quoted alone by accident.
