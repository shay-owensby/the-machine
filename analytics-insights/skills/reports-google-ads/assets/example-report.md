<!--
  A worked example, generated end to end from assets/fixtures/healthy_raw.json.
  Every figure below comes from that fixture's analysis file; nothing is typed
  by hand. The account is synthetic — no client data appears here.

  Use it as the quality bar: this is what the google-ads agent produces.
-->

# Example Client Account — Google Ads Performance Report

**Reporting period:** 2026-07-20 – 2026-08-18 (30 days)
**Comparison period:** 2026-06-20 – 2026-07-19 (30 days)
**Account:** Example Client Account (1234567890) · **Currency:** USD
**Prepared:** 2026-08-19

---

## Executive summary

The account grew this period, and it grew efficiently. Spend rose 15.3% to
$12,880 and returned 490 conversions against 417 — a 17.5% increase — worth
$44,580 in recorded conversion value against $38,065 last period. Because
conversions grew slightly faster than spend, cost per conversion held at $26.29
against $26.79, and ROAS was effectively flat at 3.46 against 3.41. That
combination is what scale is supposed to look like: more money in, proportionally
more out, and unit economics unchanged. Neither the CPA nor the ROAS move clears
the materiality threshold, so the honest reading is that efficiency held steady
while volume grew, not that efficiency improved.

The growth is concentrated. Search — Non-Brand Core took $6,160, 47.8% of
account spend, and accounts for $1,260 of the account's $1,710 spend increase.
It returned that with 176 conversions, up 39.7%, at a CPA of $35.00. That CPA is
a third above the account average, which is normal for non-brand prospecting and
is not by itself a problem — but it does mean the account's blended CPA is being
held down by brand traffic rather than by non-brand efficiency. Search — Brand
converted 210 times at $12.67 with a ROAS of 7.89 on 82% impression share. It is
the most efficient thing in the account and it is close to saturated: at 82%
share there is little headroom left to buy, so future growth has to come from
non-brand, Performance Max, or a larger addressable audience.

The clearest constraint this period is budget. Search impressions lost to budget
rose from 11.5% to 16.9%, a 5.3-point increase, while impressions lost to ad
rank were essentially unchanged at 28.9%. Read together, those two say the
account is now turning away demand it could afford: the auctions are being
entered and won at a similar rate, but the money runs out sooner in the day.
Search — Non-Brand Core is the specific campaign involved, losing 23.0% of its
available impressions to budget on a $120 daily budget. Whether to fund that is a
commercial decision rather than a technical one — the campaign converts at
$35.00, above the blended average — but it should be a decision rather than a
default.

Ad rank is the larger of the two visibility constraints and the harder one.
Search — Non-Brand Core loses 36.0% of its available impressions to rank, which
no amount of extra budget will buy back. Ad rank combines bid and quality, and
these figures do not separate them; the campaign's 5.00% CTR is healthy, which
argues the shortfall is more likely bid or landing-page experience than ad
relevance, but that is a hypothesis to test rather than a finding.

Two things are underperforming. Display — Remarketing converts at $70.00, nearly
three times the account average, with a ROAS of 0.93 — it is returning slightly
less value than it costs. At $420, or 3.3% of spend, it is small enough not to
distort the account and large enough to be worth fixing or stopping. And one
enabled conversion action, "Newsletter Signup (legacy)", has recorded nothing in
either period; a silent action muddies the goal picture and dilutes the signal
automated bidding learns from.

One caveat governs the impression-share figures throughout this report. Only
Search campaigns report impression share, and they account for 13.5% of the
account's impressions — Performance Max and Display, which carry the rest, do
not report it at all. The 54.25% account figure is a genuine measure of the
search side of the account and says nothing about the other 86% of impressions.

Priorities for the next period, in order: decide explicitly whether to fund the
16.9% of search impressions being lost to budget, and if so put the money behind
Search — Brand and the non-brand ad groups already converting near the account
average; work ad rank on Search — Non-Brand Core, starting with ad strength and
keyword-to-ad-group relevance before touching bids; and resolve Display —
Remarketing one way or the other. Nothing here needs urgent intervention — this
is an account growing at stable efficiency, with a visibility ceiling it is now
pressing against.

---

## KPI overview

| KPI | Current 30 days (2026-07-20 – 2026-08-18) | Previous 30 days (2026-06-20 – 2026-07-19) | Absolute change | % change |
|---|---:|---:|---:|---:|
| Spend | $12,880.00 | $11,170.00 | +$1,710.00 | +15.3% |
| Impressions | 960,000 | 886,000 | +74,000 | +8.4% |
| Clicks | 14,800 | 13,200 | +1,600 | +12.1% |
| CTR | 1.54% | 1.49% | +0.05 pp | +3.5% |
| Avg. CPC | $0.87 | $0.85 | +$0.02 | +2.8% |
| Conversions | 490.00 | 417.00 | +73.00 | +17.5% |
| Conversion rate | 3.31% | 3.16% | +0.15 pp | +4.8% |
| CPA | $26.29 | $26.79 | -$0.50 | -1.9% |
| Conversion value | $44,580.00 | $38,065.00 | +$6,515.00 | +17.1% |
| ROAS | 3.46 | 3.41 | +0.05 | +1.6% |
| Search impression share | 54.25% | 59.10% | -4.86 pp | -8.2% |
| Search lost IS (budget) | 16.86% | 11.52% | +5.34 pp | +46.4% |
| Search lost IS (rank) | 28.89% | 29.38% | -0.49 pp | -1.7% |

Conversions and conversion value both outgrew spend, which is why CPA and ROAS
barely moved. The one materially adverse figure is impressions lost to budget,
up 5.3 points.

![Horizontal bar chart of percentage change for each KPI, coloured blue where the change is an improvement, red where it is a decline, and grey where direction alone does not say.](charts/1234567890_2026-07-20_2026-08-18_kpi-change.png)

---

## Performance detail

### Campaigns

| Campaign | Type | Status | Spend | Spend Δ% | Conversions | Conv. Δ% | CPA | ROAS | Search IS |
|---|---|---|---:|---:|---:|---:|---:|---:|---:|
| Search — Non-Brand Core | Search | Enabled | $6,160.00 | +25.7% | 176.0 | +39.7% | $35.00 | 2.57 | 41.0% |
| Performance Max — Retail | Performance Max | Enabled | $3,640.00 | +8.3% | 98.0 | +11.4% | $37.14 | 2.02 | n/a |
| Search — Brand | Search | Enabled | $2,660.00 | +5.6% | 210.0 | +6.1% | $12.67 | 7.89 | 82.0% |
| Display — Remarketing | Display | Enabled | $420.00 | +7.7% | 6.0 | +20.0% | $70.00 | 0.93 | n/a |

![Two horizontal bar charts side by side sharing campaign labels: spend on the left, conversions on the right, campaigns ordered by spend.](charts/1234567890_2026-07-20_2026-08-18_campaign-spend-conversions.png)

Search — Non-Brand Core drove the account's growth on both sides: 74% of the
spend increase and the largest conversion increase. Search — Brand delivers the
most conversions from the least spend, and its 82% impression share means that
is close to its ceiling.

### Where search impressions went

![Stacked horizontal bars, one per search campaign, splitting available impressions into won, lost to budget, lost to ad rank, and unaccounted.](charts/1234567890_2026-07-20_2026-08-18_impression-share.png)

Non-brand wins 41% of its available impressions, loses 23% to budget and 36% to
rank. Brand wins 82%. The two constraints need different responses: budget is a
funding decision, rank is an optimisation problem.

---

## Strengths

**Conversion growth outpaced spend growth.**
Conversions +17.5% (490 vs 417) on spend +15.3% ($12,880 vs $11,170); CPA
$26.29 vs $26.79. The account absorbed a 15% budget increase without unit
economics deteriorating — which is the test of whether more money should follow.

**Brand search is highly efficient and nearly saturated.**
Search — Brand: 210 conversions at $12.67 CPA, ROAS 7.89, 82% impression share.
It is less than half the blended CPA and is protecting demand that already
exists. At 82% share there is little left to buy, so it is a floor to defend
rather than a growth lever.

**Recorded conversion value grew in line with volume.**
$44,580 vs $38,065 (+17.1%), against conversions +17.5%. Value per conversion
was essentially unchanged, so the growth is more conversions rather than a shift
in what is being counted.

---

## Weaknesses and risks

**The account is now losing meaningful volume to budget.**
Search impressions lost to budget rose from 11.5% to 16.9% (+5.3 points, +46.4%
relative) while rank-driven losses were flat. At current conversion rates the
unserved share represents real volume, though impression share does not scale
linearly with budget, so the recoverable portion is smaller than the headline.
*Confidence: high — this is a direct measure, not an inference.*

**Non-brand search is rank-constrained.**
Search — Non-Brand Core loses 36.0% of available impressions to ad rank on 41%
impression share. Rank combines bid and quality and this figure does not
separate them. Its 5.00% CTR argues against an ad-relevance problem, which
points at bid or landing-page experience — a hypothesis to test, not a
conclusion.

**Display — Remarketing is not paying for itself.**
$420 spend, 6 conversions, CPA $70.00 against an account average of $26.29,
ROAS 0.93. At 3.3% of spend it is not distorting the account, but it is
returning slightly less value than it costs.

**One conversion action is enabled and silent.**
"Newsletter Signup (legacy)" recorded nothing in either period. Either it is
broken or it measures something that no longer happens; enabled-but-silent
actions dilute the signal automated bidding learns from.

---

## Recommended next steps

### 1. Decide whether to fund the search impressions being lost to budget

- **Reason:** 16.9% of available search impressions went unserved because budget
  ran out, up from 11.5%.
- **Supporting evidence:** Search lost IS (budget) 16.86% vs 11.52% (+5.34 pp);
  account CPA $26.29, stable; Search — Non-Brand Core losing 23.0% to budget on
  a $120/day budget.
- **Expected impact:** Additional volume at approximately current CPA. Impression
  share does not scale linearly with budget — treat the lost share as a ceiling,
  not a forecast.
- **Priority:** High

### 2. Work ad rank on Search — Non-Brand Core

- **Reason:** 36.0% of its available impressions are lost to rank, which more
  budget cannot buy back.
- **Supporting evidence:** Search lost IS (rank) 36.0%; search IS 41.0%; CTR
  5.00% (healthy, which argues against ad relevance as the cause).
- **Expected impact:** Rank responds to bid and quality together; expect movement
  over weeks, not days. Start with ad strength and keyword-to-ad-group
  relevance, then test a bid or target-CPA change on the top-converting ad
  groups.
- **Priority:** Medium

### 3. Fix or stop Display — Remarketing

- **Reason:** CPA $70.00 against an account average of $26.29, ROAS 0.93.
- **Supporting evidence:** $420 spend (3.3% of account), 6 conversions.
- **Expected impact:** Bringing it to account-average CPA would free roughly $262
  per period at current conversion volume. Pull the placement report first,
  exclude the sites and apps taking spend without converting, and check the
  audience still matches the offer.
- **Priority:** Medium

### 4. Review the silent conversion action

- **Reason:** "Newsletter Signup (legacy)" has recorded nothing in 60 days.
- **Supporting evidence:** 2 of 3 enabled actions recorded data this period.
- **Expected impact:** A shorter, live list of conversion actions makes the
  account's goals legible and stops dead actions diluting bidding signals.
- **Priority:** Low

---

## Data notes

- **Periods:** 2026-07-20 – 2026-08-18 against 2026-06-20 – 2026-07-19, both 30
  days, computed in the account's time zone (America/New_York).
- **Impression-share coverage:** Search impression share covers 13.5% of account
  impressions — 2 of 4 campaigns report it. Performance Max and Display do not
  report impression share and are excluded from the account figure rather than
  counted as zero. The 54.25% figure describes the search side of the account
  only.
- **Sample size:** All campaigns cleared the thresholds for confident reading;
  no small-sample caveats apply this period.
- **Conversion lag:** No lag buffer was applied. Conversions in the last few days
  of the current period may still be attributed and will nudge the figures up
  slightly on a later re-run.
- **Queries:** All datasets retrieved successfully.

---

*Data retrieved from the Google Ads API on 2026-08-19 for Example Client Account
(1234567890). Figures are in USD. Current period 2026-07-20 – 2026-08-18;
comparison period 2026-06-20 – 2026-07-19.*
