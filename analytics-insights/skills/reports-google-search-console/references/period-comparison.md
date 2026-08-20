# Reporting periods and change arithmetic

## Search Console lags, and the lag is not fixed

Search Console publishes data on a delay — usually two days, often three, more
after outages. **Yesterday is not a finalised day**, and a report that assumes it
is compares a settled 30 days against a window whose last days are still filling
in. That produces a decline that did not happen.

So the run discovers the lag instead of assuming it:

```
gsc_common.latest_final_date()
  -> one query, dimensions=["date"], last 14 days, dataState="final"
  -> the newest date returned IS the latest finalised date
  -> a second query with dataState="all" shows how many fresher, provisional
     days exist, which is reported and then excluded
```

## The two windows

Given a latest finalised date of **2026-08-16** and the default 30 days:

```
current   2026-07-18 .. 2026-08-16     30 days, ending on the latest finalised day
previous  2026-06-18 .. 2026-07-17     the 30 days immediately before
```

No gap, no overlap, equal lengths. Both ranges appear in the report header,
every chart subtitle, and the analysis file. **A period-over-period figure
without its periods cannot be checked**, and the ranges are the first thing a
client verifies.

Overrides:

```bash
--days 28                                   # both windows
--end-date 2026-08-10                       # last day of the current window
--current 2026-07-18:2026-08-16 --previous 2025-07-18:2025-08-16   # e.g. year on year
GSC_LAG_DAYS=3                              # hold both windows back
```

`GSC_LAG_DAYS` is worth setting on properties where the freshest finalised days
still visibly move. It shifts both windows together, so they stay comparable.

Unequal explicit windows are allowed but flagged: `periods.comparable` becomes
false and the analysis warns that totals between them are not like-for-like.

## The 16-month horizon

Search Console retains roughly 16 months of Search Analytics data. A comparison
window near that edge returns thin or empty data because the data has aged out,
not because traffic collapsed. The run warns when the comparison period starts
more than ~480 days ago.

## Change arithmetic

For every KPI:

| Field | Meaning |
|---|---|
| `absolute_change` | `current - previous` |
| `percent_change` | `(current - previous) / abs(previous) * 100`, **or `null`** |
| `direction` | `up` / `down` / `flat` — arithmetic only |
| `verdict` | `improved` / `declined` / `flat` / `new` / `unknown` — interpretation |
| `material` | whether it clears this property's thresholds |

**`percent_change: null` means undefined, not zero.** Against a zero or missing
baseline there is no percentage; the report gives the absolute figure and says
the previous period was zero. The KPI table prints `n/a (previous period was
zero)`.

### CTR: points and percentages are different numbers

CTR is stored as a percentage (`2.40` means 2.40%).

- `absolute_change` is in **percentage points**: 2.00% → 2.40% is **+0.40 pp**
- `percent_change` is **relative**: the same move is **+20%**

Both are true and they are not interchangeable. A report saying "CTR rose 20%"
without the points figure invites the reader to think CTR is now 22%.

### Average position: lower is better

This is the trap, and it is handled in one place. Each KPI carries
`better_when`, and the verdict is derived from it — never from the sign:

| Movement | `absolute_change` | `direction` | `verdict` |
|---|---|---|---|
| 12.0 → 8.0 | −4.0 | down | **improved** |
| 5.0 → 9.0 | +4.0 | up | **declined** |

Every position chart is drawn on an inverted axis and says so. Every position
figure in a table is labelled *lower is better*.

And a standing caveat the report should carry: **Search Console average position
is not a keyword ranking.** It is an impression-weighted average across every
query the property appeared for. It moves when the query mix moves — a property
that starts appearing for thousands of new low-ranking terms sees its average
position worsen with nothing lost. Read it beside impressions or not at all.

## Materiality: what counts as a change

A percentage without a volume misleads in both directions. A move must clear
**both** a relative and an absolute bar:

| Metric | Relative | Absolute |
|---|---|---|
| Clicks | 5% | 10 clicks |
| Impressions | 5% | 100 impressions |
| CTR | 5% | 0.20 pp |
| Average position | 5% | 0.3 places |

Below either bar the verdict is `flat`, whatever the percentage says. Nine
clicks becoming thirteen is +44% and it is noise.

Above the bar, both figures get reported: *"clicks fell 18% (−2,340)"*. A 40%
move on 50 clicks is smaller news than a 6% move on 50,000.

## Sample size

Below **30 clicks** in the current period, click-derived conclusions are marked
`confidence: low`, the data-quality section warns, and no high-severity finding
is asserted. Small properties get reports about direction and opportunity, not
about statistically significant change — because there is none to have.

## Where the click change sits

`click_attribution` splits the change arithmetically, since clicks =
impressions × CTR:

```
Δclicks  ≈  Δimpressions × CTR_previous  +  impressions_now × ΔCTR  +  remainder
```

`dominant_factor` is `impressions`, `ctr`, `both` or `neither`. This says which
factor the change sits in. **It does not say why that factor moved** — and the
field carries that caveat in the contract so it travels with the number.
