# Social Media Performance Report

| Report detail | Value |
|---|---|
| Client / brand scope | {{CLIENT_AND_BRAND_SCOPE}} |
| Zernio profiles | {{PROFILE_NAMES_AND_IDS}} |
| Connected accounts | {{CONNECTED_ACCOUNTS_SUMMARY}} |
| Reporting time zone | {{REPORTING_TIME_ZONE_AND_SOURCE}} |
| Current period | {{CURRENT_START}} to {{CURRENT_END}} — 30 complete days |
| Previous period | {{PREVIOUS_START}} to {{PREVIOUS_END}} — 30 complete days |
| Report generated | {{REPORT_GENERATED_DATE}} |
| Data source | Zernio API v1 |
| Overall confidence | {{CONFIDENCE_LEVEL_AND_REASON}} |

## 1. Executive Summary

{{EXECUTIVE_SUMMARY}}

1. **Primary outcome:** {{PRIMARY_OUTCOME}}
2. **Largest strength:** {{LARGEST_STRENGTH}}
3. **Largest weakness:** {{LARGEST_WEAKNESS}}
4. **Highest-value opportunity:** {{HIGHEST_VALUE_OPPORTUNITY}}
5. **Primary measurement caveat:** {{PRIMARY_MEASUREMENT_CAVEAT_OR_NONE}}
6. **Recommended focus for the next 30 days:** {{NEXT_30_DAY_FOCUS}}

| Headline KPI | Current | Previous | Absolute change | % change | Executive interpretation |
|---|---:|---:|---:|---:|---|
| Posts published | {{VALUE}} | {{VALUE}} | {{VALUE}} | {{VALUE}} | {{INTERPRETATION}} |
| Impressions | {{VALUE}} | {{VALUE}} | {{VALUE}} | {{VALUE}} | {{INTERPRETATION}} |
| Reach | {{VALUE}} | {{VALUE}} | {{VALUE}} | {{VALUE}} | {{INTERPRETATION}} |
| Total engagements | {{VALUE}} | {{VALUE}} | {{VALUE}} | {{VALUE}} | {{INTERPRETATION}} |
| Engagement rate | {{VALUE}} | {{VALUE}} | {{VALUE}} | {{VALUE}} | {{INTERPRETATION}} |
| Clicks | {{VALUE}} | {{VALUE}} | {{VALUE}} | {{VALUE}} | {{INTERPRETATION}} |
| Net follower growth | {{VALUE}} | {{VALUE}} | {{VALUE}} | {{VALUE}} | {{INTERPRETATION}} |

## 2. Scope, Methodology, and Data Confidence

| Item | Detail |
|---|---|
| Account/profile scope | {{ACCOUNT_AND_PROFILE_SCOPE}} |
| Date convention | Last 30 complete reporting-time-zone days ending yesterday vs. the immediately preceding 30 complete days |
| Included publishing sources | {{PUBLISHING_SOURCES}} |
| Included data families | {{INCLUDED_DATA_FAMILIES}} |
| Filters or exclusions | {{FILTERS_EXCLUSIONS_OR_NONE}} |
| Data freshness | {{DATA_FRESHNESS_SUMMARY}} |
| Pending sync/backfill | {{PENDING_SYNC_OR_NONE}} |
| Permissions/add-on gaps | {{PERMISSION_AND_ADDON_GAPS_OR_NONE}} |
| Comparison quality | {{HIGH_MEDIUM_LOW_WITH_REASON}} |

{{METHODOLOGY_AND_RECONCILIATION_NOTES}}

### Coverage by Profile and Account

| Profile | Platform | Account | Connection / analytics status | Current coverage | Previous coverage | Freshness / limitation |
|---|---|---|---|---|---|---|
{{COVERAGE_ROWS}}

## 3. Complete KPI Scorecard

{{SCORECARD_READING_NOTE}}

### Publishing and Visibility

| KPI | API field / formula | Current | Previous | Absolute change | % change | Interpretation |
|---|---|---:|---:|---:|---:|---|
| Posts published | Unique destination posts | {{VALUE}} | {{VALUE}} | {{VALUE}} | {{VALUE}} | {{INTERPRETATION}} |
| Impressions | `impressions` | {{VALUE}} | {{VALUE}} | {{VALUE}} | {{VALUE}} | {{INTERPRETATION}} |
| Reach | `reach` | {{VALUE}} | {{VALUE}} | {{VALUE}} | {{VALUE}} | {{INTERPRETATION}} |
| Views | `views` | {{VALUE}} | {{VALUE}} | {{VALUE}} | {{VALUE}} | {{INTERPRETATION}} |
| Publishing frequency | Posts / 7 days | {{VALUE}} | {{VALUE}} | {{VALUE}} | {{VALUE}} | {{INTERPRETATION}} |

### Engagement and Actions

| KPI | API field / formula | Current | Previous | Absolute change | % change | Interpretation |
|---|---|---:|---:|---:|---:|---|
| Likes / reactions | `likes` / reactions | {{VALUE}} | {{VALUE}} | {{VALUE}} | {{VALUE}} | {{INTERPRETATION}} |
| Comments | `comments` | {{VALUE}} | {{VALUE}} | {{VALUE}} | {{VALUE}} | {{INTERPRETATION}} |
| Shares / reshares | `shares` / reshares | {{VALUE}} | {{VALUE}} | {{VALUE}} | {{VALUE}} | {{INTERPRETATION}} |
| Saves | `saves` | {{VALUE}} | {{VALUE}} | {{VALUE}} | {{VALUE}} | {{INTERPRETATION}} |
| Reposts | `reposts` | {{VALUE}} | {{VALUE}} | {{VALUE}} | {{VALUE}} | {{INTERPRETATION}} |
| Clicks | `clicks` | {{VALUE}} | {{VALUE}} | {{VALUE}} | {{VALUE}} | {{INTERPRETATION}} |
| Follows attributed to content | `follows` | {{VALUE}} | {{VALUE}} | {{VALUE}} | {{VALUE}} | {{INTERPRETATION}} |
| Total engagements | Likes + comments + shares + saves + clicks, adjusted as disclosed | {{VALUE}} | {{VALUE}} | {{VALUE}} | {{VALUE}} | {{INTERPRETATION}} |
| Engagement rate | API aggregate or disclosed weighted formula | {{VALUE}} | {{VALUE}} | {{VALUE}} | {{VALUE}} | {{INTERPRETATION}} |
| Click-through rate | Clicks / impressions | {{VALUE}} | {{VALUE}} | {{VALUE}} | {{VALUE}} | {{INTERPRETATION}} |
| View rate | Views / impressions, where comparable | {{VALUE}} | {{VALUE}} | {{VALUE}} | {{VALUE}} | {{INTERPRETATION}} |

### Followers and Video Quality

| KPI | API field / formula | Current | Previous | Absolute change | % change | Interpretation |
|---|---|---:|---:|---:|---:|---|
| Current followers | End-of-period follower observations | {{VALUE}} | {{VALUE}} | {{VALUE}} | {{VALUE}} | {{INTERPRETATION}} |
| Net follower growth | Ending minus starting followers | {{VALUE}} | {{VALUE}} | {{VALUE}} | {{VALUE}} | {{INTERPRETATION}} |
| Follower growth rate | Net growth / starting followers | {{VALUE}} | {{VALUE}} | {{VALUE}} | {{VALUE}} | {{INTERPRETATION}} |
| Average watch time | Platform/API aggregate | {{VALUE}} | {{VALUE}} | {{VALUE}} | {{VALUE}} | {{INTERPRETATION}} |
| Total watch time | Platform/API aggregate | {{VALUE}} | {{VALUE}} | {{VALUE}} | {{VALUE}} | {{INTERPRETATION}} |
| Reels skip rate | `reelsSkipRate` | {{VALUE}} | {{VALUE}} | {{VALUE}} | {{VALUE}} | {{INTERPRETATION}} |

### All Additional KPI Fields Returned by Zernio

| KPI | Scope | API endpoint / field | Current | Previous | Absolute change | % change | Definition / interpretation |
|---|---|---|---:|---:|---:|---:|---|
{{ADDITIONAL_KPI_ROWS_OR_NONE}}

## 4. Platform and Account Performance

| Profile | Platform / account | Posts | Impressions | Reach | Engagements | Engagement rate | Clicks | Net follower growth | Assessment |
|---|---|---:|---:|---:|---:|---:|---:|---:|---|
{{PLATFORM_ACCOUNT_ROWS}}

{{PLATFORM_ACCOUNT_FINDINGS}}

### Platform-Native Account Insights

| Platform / account | KPI | Current | Previous | Change | Data scope / caveat | Interpretation |
|---|---|---:|---:|---:|---|---|
{{PLATFORM_NATIVE_INSIGHT_ROWS_OR_NONE}}

## 5. Content Performance

### Top-Performing Content

| Rank | Platform / account | Published | Content / link | Format | Primary KPI | Result | Supporting KPIs | Why it worked / hypothesis |
|---:|---|---|---|---|---|---:|---|---|
{{TOP_CONTENT_ROWS}}

### Underperforming Content

| Rank | Platform / account | Published | Content / link | Format | Primary KPI | Result | Supporting KPIs | Diagnosis / hypothesis |
|---:|---|---|---|---|---|---:|---|---|
{{UNDERPERFORMING_CONTENT_ROWS}}

### Format and Content-Type Performance

| Platform | Format / content type | Posts | Reach or impressions per post | Engagement rate | Clicks / actions | Change vs. previous | Confidence | Assessment |
|---|---|---:|---:|---:|---:|---:|---|---|
{{FORMAT_PERFORMANCE_ROWS}}

{{CONTENT_FINDINGS}}

## 6. Audience and Follower Insights

| Platform / account | Starting followers | Ending followers | Net growth | Growth rate | Previous net growth | Change | Assessment |
|---|---:|---:|---:|---:|---:|---:|---|
{{FOLLOWER_ROWS}}

### Audience and Demographic Signals

| Platform / account | Signal / segment | Current result | Previous / benchmark | Confidence / limitation | Implication |
|---|---|---:|---:|---|---|
{{AUDIENCE_SIGNAL_ROWS_OR_NONE}}

{{AUDIENCE_AND_FOLLOWER_FINDINGS}}

## 7. Publishing Cadence and Timing

| Platform / account | Current posts/week | Previous posts/week | Best observed day/time | Time zone | Sample size | Recommendation |
|---|---:|---:|---|---|---:|---|
{{CADENCE_AND_TIMING_ROWS}}

### Content Decay and Frequency Signals

| Platform / account | Signal | Evidence | Confidence | Implication |
|---|---|---|---|---|
{{DECAY_FREQUENCY_ROWS_OR_NONE}}

{{TIMING_AND_CADENCE_FINDINGS}}

## 8. Community and Inbox Performance

| KPI | Current | Previous | Absolute change | % change | Interpretation |
|---|---:|---:|---:|---:|---|
{{INBOX_KPI_ROWS_OR_NA}}

| Platform / account / source | Conversation or message volume | Response time | Change | Peak period | Assessment |
|---|---:|---:|---:|---|---|
{{INBOX_BREAKDOWN_ROWS_OR_NA}}

{{COMMUNITY_AND_INBOX_FINDINGS_OR_NA}}

## 9. Paid Social Performance

| KPI | Current | Previous | Absolute change | % change | Interpretation |
|---|---:|---:|---:|---:|---|
| Spend | {{VALUE}} | {{VALUE}} | {{VALUE}} | {{VALUE}} | {{INTERPRETATION}} |
| Paid impressions | {{VALUE}} | {{VALUE}} | {{VALUE}} | {{VALUE}} | {{INTERPRETATION}} |
| Paid reach | {{VALUE}} | {{VALUE}} | {{VALUE}} | {{VALUE}} | {{INTERPRETATION}} |
| Paid clicks | {{VALUE}} | {{VALUE}} | {{VALUE}} | {{VALUE}} | {{INTERPRETATION}} |
| Paid CTR | {{VALUE}} | {{VALUE}} | {{VALUE}} | {{VALUE}} | {{INTERPRETATION}} |
| CPC | {{VALUE}} | {{VALUE}} | {{VALUE}} | {{VALUE}} | {{INTERPRETATION}} |
| CPM | {{VALUE}} | {{VALUE}} | {{VALUE}} | {{VALUE}} | {{INTERPRETATION}} |
| Conversions | {{VALUE}} | {{VALUE}} | {{VALUE}} | {{VALUE}} | {{INTERPRETATION}} |
| Cost per conversion | {{VALUE}} | {{VALUE}} | {{VALUE}} | {{VALUE}} | {{INTERPRETATION}} |
| Purchase value | {{VALUE}} | {{VALUE}} | {{VALUE}} | {{VALUE}} | {{INTERPRETATION}} |
| ROAS | {{VALUE}} | {{VALUE}} | {{VALUE}} | {{VALUE}} | {{INTERPRETATION}} |

### Campaign and Ad Drivers

| Platform | Campaign / ad | Spend | Result | Cost per result | ROAS | Change vs. previous | Assessment |
|---|---|---:|---:|---:|---:|---:|---|
{{PAID_DRIVER_ROWS_OR_NA}}

{{PAID_SOCIAL_FINDINGS_OR_NA}}

## 10. Strengths

| Priority | Strength | Quantified evidence | Business significance | Confidence |
|---:|---|---|---|---|
{{STRENGTH_ROWS}}

## 11. Weaknesses and Risks

| Priority | Weakness / risk | Quantified evidence | Likely implication | Confidence / validation needed |
|---:|---|---|---|---|
{{WEAKNESS_ROWS}}

## 12. Actionable Next Steps

| Priority | Action | Evidence / rationale | Owner role | Timing | Success measure | Next review |
|---:|---|---|---|---|---|---|
{{ACTION_ROWS}}

### 30-Day Test Plan

| Hypothesis | Change to test | Audience / platform | Primary KPI | Guardrail | Decision rule |
|---|---|---|---|---|---|
{{TEST_PLAN_ROWS}}

## 13. Measurement Gaps and Caveats

| Gap / caveat | Affected scope | Impact on interpretation | Recommended remediation |
|---|---|---|---|
{{MEASUREMENT_GAP_ROWS_OR_NONE}}

## 14. Appendix: KPI Definitions, Sources, and Reconciliation

### KPI Definitions and Cross-Platform Differences

| KPI | Definition used | Source endpoint / field | Cross-platform caveat |
|---|---|---|---|
{{KPI_DEFINITION_ROWS}}

### API Coverage and Reconciliation

| Query family | Endpoint(s) | Filters / attribution | Current status | Previous status | Reconciliation note |
|---|---|---|---|---|---|
{{API_COVERAGE_ROWS}}

### Calculation Notes

{{CALCULATION_NOTES}}
