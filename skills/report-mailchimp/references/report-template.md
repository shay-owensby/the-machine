# Mailchimp Email Marketing Performance Report

| Report detail | Value |
|---|---|
| Client / brand scope | {{CLIENT_AND_BRAND_SCOPE}} |
| Mailchimp account | {{ACCOUNT_NAME_AND_SAFE_ID}} |
| Audiences / lists | {{AUDIENCE_SCOPE}} |
| Connected stores | {{STORE_SCOPE_OR_NONE}} |
| Reporting time zone | {{REPORTING_TIME_ZONE_AND_SOURCE}} |
| Current period | {{CURRENT_START}} to {{CURRENT_END}} — 30 complete days |
| Previous period | {{PREVIOUS_START}} to {{PREVIOUS_END}} — 30 complete days |
| API observation time | {{API_OBSERVATION_TIME}} |
| Report generated | {{REPORT_GENERATED_DATE}} |
| Data source | Mailchimp Marketing API v3.0 |
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
| Campaigns sent | {{VALUE}} | {{VALUE}} | {{VALUE}} | {{VALUE}} | {{INTERPRETATION}} |
| Emails sent | {{VALUE}} | {{VALUE}} | {{VALUE}} | {{VALUE}} | {{INTERPRETATION}} |
| Delivery rate | {{VALUE}} | {{VALUE}} | {{VALUE}} | {{VALUE}} | {{INTERPRETATION}} |
| Proxy-excluded open rate | {{VALUE}} | {{VALUE}} | {{VALUE}} | {{VALUE}} | {{INTERPRETATION}} |
| Click rate | {{VALUE}} | {{VALUE}} | {{VALUE}} | {{VALUE}} | {{INTERPRETATION}} |
| Click-to-open rate (CTOR) | {{VALUE}} | {{VALUE}} | {{VALUE}} | {{VALUE}} | {{INTERPRETATION}} |
| Unsubscribe rate | {{VALUE}} | {{VALUE}} | {{VALUE}} | {{VALUE}} | {{INTERPRETATION}} |
| Complaint rate | {{VALUE}} | {{VALUE}} | {{VALUE}} | {{VALUE}} | {{INTERPRETATION}} |
| Net audience change | {{VALUE}} | {{VALUE}} | {{VALUE}} | {{VALUE}} | {{INTERPRETATION}} |
| Revenue | {{VALUE}} | {{VALUE}} | {{VALUE}} | {{VALUE}} | {{INTERPRETATION}} |

## 2. Scope, Methodology, and Data Confidence

| Item | Detail |
|---|---|
| Account and audience scope | {{ACCOUNT_AND_AUDIENCE_SCOPE}} |
| Date convention | Latest 30 complete account-time-zone days ending yesterday vs. the immediately preceding 30 complete days |
| Campaign inclusion rule | Sent email campaigns assigned by `send_time`; parent/child reports deduplicated |
| Campaign types included | {{CAMPAIGN_TYPES_INCLUDED}} |
| Filters or exclusions | {{FILTERS_EXCLUSIONS_OR_NONE}} |
| Data freshness / campaign maturity | {{FRESHNESS_AND_MATURITY}} |
| Tracking configuration coverage | {{TRACKING_COVERAGE}} |
| Permissions / plan gaps | {{PERMISSION_AND_PLAN_GAPS_OR_NONE}} |
| Comparison quality | {{HIGH_MEDIUM_LOW_WITH_REASON}} |

{{METHODOLOGY_AND_RECONCILIATION_NOTES}}

### Coverage by Audience

| Audience / list | Safe ID | Active status | Current campaigns | Previous campaigns | Current member snapshot | Connected store / currency | Limitation |
|---|---|---|---:|---:|---:|---|---|
{{AUDIENCE_COVERAGE_ROWS}}

## 3. Complete KPI Scorecard

{{SCORECARD_READING_NOTE}}

### Campaign Volume and Delivery

| KPI | API field / formula | Current | Previous | Absolute change | % change | Interpretation |
|---|---|---:|---:|---:|---:|---|
| Campaigns sent | Deduplicated report count | {{VALUE}} | {{VALUE}} | {{VALUE}} | {{VALUE}} | {{INTERPRETATION}} |
| Campaign frequency | Campaigns / (30 / 7) | {{VALUE}} | {{VALUE}} | {{VALUE}} | {{VALUE}} | {{INTERPRETATION}} |
| Emails sent | `emails_sent` | {{VALUE}} | {{VALUE}} | {{VALUE}} | {{VALUE}} | {{INTERPRETATION}} |
| Average recipients per campaign | Emails sent / campaigns sent | {{VALUE}} | {{VALUE}} | {{VALUE}} | {{VALUE}} | {{INTERPRETATION}} |
| Successful deliveries | Emails sent - hard bounces - soft bounces | {{VALUE}} | {{VALUE}} | {{VALUE}} | {{VALUE}} | {{INTERPRETATION}} |
| Delivery rate | Successful deliveries / emails sent | {{VALUE}} | {{VALUE}} | {{VALUE}} | {{VALUE}} | {{INTERPRETATION}} |
| Total bounces | Hard + soft bounces | {{VALUE}} | {{VALUE}} | {{VALUE}} | {{VALUE}} | {{INTERPRETATION}} |
| Bounce rate | Total bounces / emails sent | {{VALUE}} | {{VALUE}} | {{VALUE}} | {{VALUE}} | {{INTERPRETATION}} |
| Hard bounces | `bounces.hard_bounces` | {{VALUE}} | {{VALUE}} | {{VALUE}} | {{VALUE}} | {{INTERPRETATION}} |
| Soft bounces | `bounces.soft_bounces` | {{VALUE}} | {{VALUE}} | {{VALUE}} | {{VALUE}} | {{INTERPRETATION}} |
| Syntax errors | `bounces.syntax_errors` | {{VALUE}} | {{VALUE}} | {{VALUE}} | {{VALUE}} | {{INTERPRETATION}} |

### Opens, Clicks, and Sharing

| KPI | API field / formula | Current | Previous | Absolute change | % change | Interpretation |
|---|---|---:|---:|---:|---:|---|
| Total opens | `opens.opens_total` | {{VALUE}} | {{VALUE}} | {{VALUE}} | {{VALUE}} | {{INTERPRETATION}} |
| Proxy-excluded total opens | `opens.proxy_excluded_opens` | {{VALUE}} | {{VALUE}} | {{VALUE}} | {{VALUE}} | {{INTERPRETATION}} |
| Unique opens | `opens.unique_opens` | {{VALUE}} | {{VALUE}} | {{VALUE}} | {{VALUE}} | {{INTERPRETATION}} |
| Proxy-excluded unique opens | `opens.proxy_excluded_unique_opens` | {{VALUE}} | {{VALUE}} | {{VALUE}} | {{VALUE}} | {{INTERPRETATION}} |
| Open rate | Unique opens / successful deliveries | {{VALUE}} | {{VALUE}} | {{VALUE}} | {{VALUE}} | {{INTERPRETATION}} |
| Proxy-excluded open rate | Proxy-excluded unique opens / successful deliveries | {{VALUE}} | {{VALUE}} | {{VALUE}} | {{VALUE}} | {{INTERPRETATION}} |
| Total clicks | `clicks.clicks_total` | {{VALUE}} | {{VALUE}} | {{VALUE}} | {{VALUE}} | {{INTERPRETATION}} |
| Unique clicks | `clicks.unique_clicks` | {{VALUE}} | {{VALUE}} | {{VALUE}} | {{VALUE}} | {{INTERPRETATION}} |
| Unique subscriber clicks | `clicks.unique_subscriber_clicks` | {{VALUE}} | {{VALUE}} | {{VALUE}} | {{VALUE}} | {{INTERPRETATION}} |
| Click rate | Unique subscriber clicks / successful deliveries | {{VALUE}} | {{VALUE}} | {{VALUE}} | {{VALUE}} | {{INTERPRETATION}} |
| Click-to-open rate (CTOR) | Unique subscriber clicks / unique opens | {{VALUE}} | {{VALUE}} | {{VALUE}} | {{VALUE}} | {{INTERPRETATION}} |
| Proxy-excluded CTOR | Unique subscriber clicks / proxy-excluded unique opens | {{VALUE}} | {{VALUE}} | {{VALUE}} | {{VALUE}} | {{INTERPRETATION}} |
| Forwards | `forwards.forwards_count` | {{VALUE}} | {{VALUE}} | {{VALUE}} | {{VALUE}} | {{INTERPRETATION}} |
| Forward opens | `forwards.forwards_opens` | {{VALUE}} | {{VALUE}} | {{VALUE}} | {{VALUE}} | {{INTERPRETATION}} |

### List Health and Negative Signals

| KPI | API field / formula | Current | Previous | Absolute change | % change | Interpretation |
|---|---|---:|---:|---:|---:|---|
| Campaign-attributed unsubscribes | `unsubscribed` | {{VALUE}} | {{VALUE}} | {{VALUE}} | {{VALUE}} | {{INTERPRETATION}} |
| Unsubscribe rate | Campaign unsubscribes / successful deliveries | {{VALUE}} | {{VALUE}} | {{VALUE}} | {{VALUE}} | {{INTERPRETATION}} |
| Abuse complaints | `abuse_reports` | {{VALUE}} | {{VALUE}} | {{VALUE}} | {{VALUE}} | {{INTERPRETATION}} |
| Complaint rate | Abuse complaints / successful deliveries | {{VALUE}} | {{VALUE}} | {{VALUE}} | {{VALUE}} | {{INTERPRETATION}} |
| Audience subscribes | List activity `subs` | {{VALUE}} | {{VALUE}} | {{VALUE}} | {{VALUE}} | {{INTERPRETATION}} |
| Audience unsubscribes | List activity `unsubs` | {{VALUE}} | {{VALUE}} | {{VALUE}} | {{VALUE}} | {{INTERPRETATION}} |
| Other audience adds | List activity `other_adds` | {{VALUE}} | {{VALUE}} | {{VALUE}} | {{VALUE}} | {{INTERPRETATION}} |
| Other audience removes | List activity `other_removes` | {{VALUE}} | {{VALUE}} | {{VALUE}} | {{VALUE}} | {{INTERPRETATION}} |
| Hard-bounce removals | List activity `hard_bounce` | {{VALUE}} | {{VALUE}} | {{VALUE}} | {{VALUE}} | {{INTERPRETATION}} |
| Net audience change | Subs + other adds - unsubs - other removes - hard-bounce removals | {{VALUE}} | {{VALUE}} | {{VALUE}} | {{VALUE}} | {{INTERPRETATION}} |
| Audience growth rate | Net change / exact starting active members | {{VALUE}} | {{VALUE}} | {{VALUE}} | {{VALUE}} | {{INTERPRETATION}} |
| Active audience size | Observation-time `stats.member_count` | {{VALUE}} | {{VALUE}} | {{VALUE}} | {{VALUE}} | {{INTERPRETATION}} |

### Revenue and Commerce

| KPI | API field / formula | Current | Previous | Absolute change | % change | Interpretation |
|---|---|---:|---:|---:|---:|---|
| Orders | `ecommerce.total_orders` | {{VALUE}} | {{VALUE}} | {{VALUE}} | {{VALUE}} | {{INTERPRETATION}} |
| Gross sales / total spent | `ecommerce.total_spent` | {{VALUE}} | {{VALUE}} | {{VALUE}} | {{VALUE}} | {{INTERPRETATION}} |
| Revenue | `ecommerce.total_revenue` | {{VALUE}} | {{VALUE}} | {{VALUE}} | {{VALUE}} | {{INTERPRETATION}} |
| Average order value | Revenue / orders | {{VALUE}} | {{VALUE}} | {{VALUE}} | {{VALUE}} | {{INTERPRETATION}} |
| Revenue per delivered email | Revenue / successful deliveries | {{VALUE}} | {{VALUE}} | {{VALUE}} | {{VALUE}} | {{INTERPRETATION}} |
| Revenue per 1,000 delivered | Revenue / successful deliveries × 1,000 | {{VALUE}} | {{VALUE}} | {{VALUE}} | {{VALUE}} | {{INTERPRETATION}} |
| Click-to-order rate | Orders / unique subscriber clicks | {{VALUE}} | {{VALUE}} | {{VALUE}} | {{VALUE}} | {{INTERPRETATION}} |

### All Additional Numeric KPI Fields Returned by Mailchimp

| KPI | Scope | API endpoint / field | Current | Previous | Absolute change | % change | Definition / interpretation |
|---|---|---|---:|---:|---:|---:|---|
{{ADDITIONAL_KPI_ROWS_OR_NONE}}

## 4. Campaign Performance

### Current-Period Campaigns

| Campaign | Type | Audience | Sent | Delivered | Proxy-excluded open rate | Click rate | CTOR | Unsub rate | Complaint rate | Revenue | Assessment |
|---|---|---|---|---:|---:|---:|---:|---:|---:|---:|---|
{{CURRENT_CAMPAIGN_ROWS}}

### Previous-Period Campaigns

| Campaign | Type | Audience | Sent | Delivered | Proxy-excluded open rate | Click rate | CTOR | Unsub rate | Complaint rate | Revenue | Assessment |
|---|---|---|---|---:|---:|---:|---:|---:|---:|---:|---|
{{PREVIOUS_CAMPAIGN_ROWS}}

### Campaign-Type and Segment Performance

| Type / audience / segment | Period | Campaigns | Delivered | Proxy-excluded open rate | Click rate | CTOR | Unsub rate | Revenue | Confidence | Assessment |
|---|---|---:|---:|---:|---:|---:|---:|---:|---|---|
{{CAMPAIGN_SEGMENT_ROWS}}

{{CAMPAIGN_FINDINGS}}

## 5. Link and Content Performance

### Top Links

| Period | Campaign | Sanitized link / destination | Total clicks | Unique clicks | Share of campaign clicks | Interpretation |
|---|---|---|---:|---:|---:|---|
{{TOP_LINK_ROWS_OR_NONE}}

### Subject Line, Preview Text, and Content Signals

| Period | Campaign / theme | Subject / preview summary | Delivered | Proxy-excluded open rate | Click rate | CTOR | Confidence | Observation / hypothesis |
|---|---|---|---:|---:|---:|---:|---|---|
{{CONTENT_SIGNAL_ROWS}}

{{LINK_AND_CONTENT_FINDINGS}}

## 6. Deliverability and Domain Performance

| Domain | Period | Sent | Delivered | Delivery rate | Bounces | Bounce rate | Opens | Clicks | Unsubs | Risk / opportunity |
|---|---|---:|---:|---:|---:|---:|---:|---:|---:|---|
{{DOMAIN_ROWS}}

### Deliverability Signals

| Signal | Current | Previous | Change | Affected scope | Severity | Interpretation / remediation |
|---|---:|---:|---:|---|---|---|
{{DELIVERABILITY_SIGNAL_ROWS}}

{{DELIVERABILITY_FINDINGS}}

## 7. Audience Growth and Engagement

| Audience | Period | Subscribes | Other adds | Unsubscribes | Other removes | Hard-bounce removals | Net change | Emails sent | Unique opens | Recipient clicks | Assessment |
|---|---|---:|---:|---:|---:|---:|---:|---:|---:|---:|---|
{{AUDIENCE_ACTIVITY_ROWS}}

### Audience Snapshot Context

| Audience | Active members now | List rating | Average list open rate | Average list click rate | Monthly growth context | Limitation |
|---|---:|---:|---:|---:|---|---|
{{AUDIENCE_SNAPSHOT_ROWS}}

{{AUDIENCE_FINDINGS}}

## 8. Send Timing, Geography, and Client Context

| Dimension | Segment | Period / observation | Campaigns or sample | Delivered / opens | Proxy-excluded open rate | Click rate | Confidence | Implication |
|---|---|---|---:|---:|---:|---:|---|---|
{{TIMING_GEOGRAPHY_CLIENT_ROWS_OR_NONE}}

{{TIMING_GEOGRAPHY_CLIENT_FINDINGS_OR_NA}}

## 9. Automation and Experiment Performance

| Workflow / experiment | Type | Variant / email | Period | Delivered | Proxy-excluded open rate | Click rate | CTOR | Unsub rate | Revenue | Confidence / winner status |
|---|---|---|---|---:|---:|---:|---:|---:|---:|---|
{{AUTOMATION_EXPERIMENT_ROWS_OR_NONE}}

{{AUTOMATION_EXPERIMENT_FINDINGS_OR_NA}}

## 10. E-commerce and Product Performance

| Store / currency | Period | Orders | Gross sales | Revenue | Average order value | Revenue / delivered | Click-to-order rate | Assessment |
|---|---|---:|---:|---:|---:|---:|---:|---|
{{ECOMMERCE_SUMMARY_ROWS_OR_NA}}

### Product Activity

| Period | Campaign | Product | Purchased | Revenue | Recommendation purchases | Recommendation revenue | Assessment |
|---|---|---|---:|---:|---:|---:|---|
{{PRODUCT_ACTIVITY_ROWS_OR_NA}}

{{ECOMMERCE_FINDINGS_OR_NA}}

## 11. Strengths

| Priority | Strength | Quantified evidence | Business significance | Confidence |
|---:|---|---|---|---|
{{STRENGTH_ROWS}}

## 12. Weaknesses and Risks

| Priority | Weakness / risk | Quantified evidence | Likely implication | Confidence / validation needed |
|---:|---|---|---|---|
{{WEAKNESS_ROWS}}

## 13. Actionable Next Steps

| Priority | Action | Evidence / rationale | Owner role | Timing | Success measure | Guardrail | Next review |
|---:|---|---|---|---|---|---|---|
{{ACTION_ROWS}}

### 30-Day Test Plan

| Hypothesis | Change to test | Campaign / audience | Primary KPI | Guardrail | Minimum evidence | Decision rule |
|---|---|---|---|---|---|---|
{{TEST_PLAN_ROWS}}

## 14. Measurement Gaps and Caveats

| Gap / caveat | Affected scope | Impact on interpretation | Recommended remediation |
|---|---|---|---|
{{MEASUREMENT_GAP_ROWS_OR_NONE}}

## 15. Appendix: KPI Definitions, Sources, and Reconciliation

### KPI Definitions

| KPI | Definition used | Source endpoint / field | Scope caveat |
|---|---|---|---|
{{KPI_DEFINITION_ROWS}}

### API Coverage and Reconciliation

| Query family | Endpoint(s) | Filters / pagination | Current status | Previous status | Reconciliation note |
|---|---|---|---|---|---|
{{API_COVERAGE_ROWS}}

### Calculation Notes

{{CALCULATION_NOTES}}
