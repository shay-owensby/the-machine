# Diagnostics: the rules, and what each one does and does not claim

Every rule below produces a finding with `evidence[]`, `severity` and
`confidence`. Severity is how much it matters; confidence is how sure the data
allows anyone to be. They are different axes — a high-severity, low-confidence
finding is a thing to investigate, not a thing to assert.

**None of these rules establishes a cause.** Search Console reports what
happened in search results. It does not know about algorithm updates,
competitors, site releases, redirects, robots rules, seasonality or the client's
own marketing calendar. Findings therefore say *"coincides with"*, *"is
associated with"*, *"may indicate"*, *"warrants investigation"* — and the
templates enforce it.

## Property-level rules

| Rule | Fires when | The claim | The limit |
|---|---|---|---|
| `clicks_up` / `clicks_down` | Clicks move materially | Traffic rose or fell by this much | None — this is the headline fact |
| `impressions_up_clicks_flat` | Impressions improved, clicks did not | Visibility grew without a matching click gain | New impressions often arrive at weaker positions, which lowers average CTR with nothing worsening |
| `clicks_falling_faster` | Clicks fell and their % fall exceeds the impression % move by 5+ points | The loss is not visibility alone | Says where the loss is, not why |
| `ctr_down_position_stable` | CTR declined materially while average position did not | Rankings held; the share of impressions converting fell | A stable average position can still hide a changed SERP — more ads, an AI answer, a new feature block. GSC does not report SERP layout |
| `ctr_up` | CTR improved and clicks did not decline | More of the same visibility became visits | — |
| `position_improved` / `position_declined` | Average position moves materially | Rankings improved or worsened | Average position moves with the query mix, not only with rankings |
| `position_up_clicks_down` | Position improved while clicks fell | The improvement landed somewhere that does not carry click volume | — |
| `declining_within_period` | Second half of the current period is 20%+ below the first | The period total hides a downward trend | Two halves of one month is a coarse instrument; it flags, it does not diagnose |
| `rising_within_period` | Second half 20%+ above the first | Momentum inside the period | Same |
| `broadly_flat` | No KPI clears materiality | The period was stable | Stability needs no cause |
| `no_baseline` | The comparison window returned nothing | Every figure is an absolute; nothing is a change | Explicitly forbids calling it growth |
| `click_attribution` | Clicks moved materially | Arithmetic split of the change between impressions and CTR | Arithmetic, not explanation |

## Query and page rules

Applied identically to both dimensions.

| Rule | Fires when | The claim | The limit |
|---|---|---|---|
| `*_gains` / `*_losses` | Rows clear the click floor (0.5% of property clicks, minimum 10) | The change is concentrated here | Dimensional data omits rows; a row that "vanished" may have been withheld |
| `*_loss_concentration` | The top 5 losers hold 60%+ of the loss | A narrow cause, easier to find than a broad one | — |
| `*_visibility_losses` | Impressions down 25%+ from a base above the opportunity floor | Visibility is going before traffic notices | — |
| `*_ctr_opportunities` | Impressions above the floor and CTR below 70% of the property's own median for that position band | The row underperforms its own ranking | Presentation lever only; the figure is a ceiling at today's impressions |
| `*_ranking_opportunities` | Impressions above the floor and position in 4-10 or 11-20 | Small ranking movement produces disproportionate click movement here | GSC cannot say whether the term is commercially relevant |

### Loss classification

Not every click loss is a ranking loss. `classify_loss()` names which:

| Kind | Signature |
|---|---|
| `visibility` | Impressions fell; position roughly held. Fewer queries matched, or the SERP changed shape |
| `ranking` | Position worsened by more than 0.6 places |
| `ctr` | Impressions and position held; CTR fell |
| `mixed` | More than one of the above |
| `unclear` | None crossed its threshold |

The recommendation that follows differs by kind, which is the point of
classifying at all.

### The CTR benchmark is the property's own

A row is judged against **this property's median CTR in the same position
band**, not an industry curve. Bands: 1-3, 4-10, 11-20, 21+; a band needs at
least 8 rows before it is used as a benchmark.

An industry CTR table is not in this data, varies with SERP layout and intent,
and would be an assumption dressed as a benchmark. "Below what this site itself
achieves at this position" is a claim the data supports — and it automatically
adapts to a brand-heavy property, a publisher, or a niche B2B site without
anyone configuring anything.

### Opportunity floors scale with the property

```
floor = max(100 impressions, 0.05% of the property's current-period impressions)
```

2,000,000 impressions → 1,000. 20,000 impressions → 100. A fixed threshold
either buries a small site's entire opportunity set or fills a publisher's report
with noise.

## Device, country and structural rules

| Rule | Fires when | The limit |
|---|---|---|
| `device_ctr_decline:*` | A device with 1,000+ impressions loses 0.4+ CTR points | Devices with under 3% of clicks are flagged `negligible` and should not carry a paragraph |
| `country_move:*` | A market with 5%+ of clicks moves materially **and diverges from the property trend by 15+ points** | A market growing at the property's own rate is the property, seen through one market — not news |
| `cannibalisation:*` | Two or more pages hold impressions for one query, the second holding 20%+ | A signal, never a diagnosis. Two pages for one query is normal when they serve different intents |
| `indexing:*` | URL Inspection returns anything but an indexed PASS for a page that lost visibility | Point-in-time status, not a 30-day history. It cannot explain the trend on its own |

## Anomaly detection

Two guards, because the naive version produces nothing but false positives:

1. **Weekday and weekend days are judged against their own group.** Search
   traffic on most properties falls 20-40% every weekend. A detector that has not
   been told this flags eight Saturdays a month and teaches the client to skip the
   section.
2. **Median absolute deviation, plus a percentage floor.** One enormous spike
   inflates a standard deviation until it hides itself; a robust bar alone still
   fires on ordinary wobble at high volume.

A day must clear 4× MAD **and** 30% of its group's typical day **and** an
absolute floor. Clicks and impressions moving together on the same date raises
confidence from medium to high.

Every anomaly carries the caveat that one unusual day is worth noting and rarely
worth acting on. Consecutive days are the signal.

## What the diagnostics never do

- Attribute a decline to an algorithm update. Search Console does not report
  updates, and coincidence in time is not evidence.
- Attribute a decline to a competitor. Search Console shows no competitor data.
- Attribute a decline to technical SEO or content quality without an indexing
  signal that actually supports it.
- Claim that rewriting metadata will improve rankings. CTR work and ranking work
  are separate levers and every recommendation says which one it is pulling.
- Assert anything at all from a handful of clicks.
