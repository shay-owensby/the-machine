# Google Analytics (GA4) Performance Report

| Report detail | Value |
|---|---|
| Property | {{PROPERTY_NAME}} |
| Property ID | {{PROPERTY_ID}} |
| Property type / streams | {{PROPERTY_TYPE_AND_STREAMS}} |
| Reporting time zone | {{PROPERTY_TIME_ZONE}} |
| Currency | {{CURRENCY}} |
| Current period | {{CURRENT_START}} to {{CURRENT_END}} — 30 complete days |
| Previous period | {{PREVIOUS_START}} to {{PREVIOUS_END}} — 30 complete days |
| Report generated | {{REPORT_GENERATED_DATE}} |
| Data source | Google Analytics Data API v1; optional Analytics Admin API for descriptive property metadata |
| Overall confidence | {{CONFIDENCE_LEVEL_AND_REASON}} |

## 1. Executive Summary

{{EXECUTIVE_SUMMARY}}

1. **Primary outcome:** {{PRIMARY_OUTCOME}}
2. **Largest strength:** {{LARGEST_STRENGTH}}
3. **Largest weakness:** {{LARGEST_WEAKNESS}}
4. **Highest-value opportunity:** {{HIGHEST_VALUE_OPPORTUNITY}}
5. **Measurement caveat:** {{PRIMARY_MEASUREMENT_CAVEAT_OR_NONE}}
6. **Recommended focus for the next 30 days:** {{NEXT_30_DAY_FOCUS}}

| Headline KPI | Current | Previous | Change | Executive interpretation |
|---|---:|---:|---:|---|
| Active users | {{VALUE}} | {{VALUE}} | {{VALUE}} | {{INTERPRETATION}} |
| Sessions | {{VALUE}} | {{VALUE}} | {{VALUE}} | {{INTERPRETATION}} |
| Engagement rate | {{VALUE}} | {{VALUE}} | {{VALUE}} | {{INTERPRETATION}} |
| Key events | {{VALUE}} | {{VALUE}} | {{VALUE}} | {{INTERPRETATION}} |
| Session key event rate | {{VALUE}} | {{VALUE}} | {{VALUE}} | {{INTERPRETATION}} |
| Total revenue | {{VALUE}} | {{VALUE}} | {{VALUE}} | {{INTERPRETATION}} |

## 2. Scope, Methodology, and Confidence

| Item | Detail |
|---|---|
| Account/property scope | {{ACCOUNT_AND_PROPERTY_SCOPE}} |
| Date convention | Last 30 complete property-time-zone days ending yesterday vs. the immediately preceding 30 complete days |
| Reporting identity / attribution context | {{IDENTITY_AND_ATTRIBUTION_CONTEXT}} |
| Included platforms and streams | {{INCLUDED_PLATFORMS_AND_STREAMS}} |
| Filters or exclusions | {{FILTERS_EXCLUSIONS_OR_NONE}} |
| Custom definitions reviewed | {{CUSTOM_DEFINITIONS_REVIEWED}} |
| Data thresholding / sampling | {{THRESHOLDING_SAMPLING_STATUS}} |
| Response metadata / access restrictions | {{RESPONSE_METADATA_AND_RESTRICTIONS}} |
| Comparison quality | {{HIGH_MEDIUM_LOW_WITH_REASON}} |

{{METHODOLOGY_NOTES}}

## 3. Complete KPI Scorecard

{{SCORECARD_READING_NOTE}}

### Audience and Retention

| KPI | API metric / basis | Current | Previous | Absolute change | % change | Interpretation |
|---|---|---:|---:|---:|---:|---|
| Total users | `totalUsers` | {{VALUE}} | {{VALUE}} | {{VALUE}} | {{VALUE}} | {{INTERPRETATION}} |
| Active users | `activeUsers` | {{VALUE}} | {{VALUE}} | {{VALUE}} | {{VALUE}} | {{INTERPRETATION}} |
| New users | `newUsers` | {{VALUE}} | {{VALUE}} | {{VALUE}} | {{VALUE}} | {{INTERPRETATION}} |
| 1-day active users | `active1DayUsers` — rolling value ending on period end | {{VALUE}} | {{VALUE}} | {{VALUE}} | {{VALUE}} | {{INTERPRETATION}} |
| 7-day active users | `active7DayUsers` — rolling value ending on period end | {{VALUE}} | {{VALUE}} | {{VALUE}} | {{VALUE}} | {{INTERPRETATION}} |
| 28-day active users | `active28DayUsers` — rolling value ending on period end | {{VALUE}} | {{VALUE}} | {{VALUE}} | {{VALUE}} | {{INTERPRETATION}} |
| DAU / WAU | `dauPerWau` — rolling ratio ending on period end | {{VALUE}} | {{VALUE}} | {{VALUE}} | {{VALUE}} | {{INTERPRETATION}} |
| DAU / MAU | `dauPerMau` — rolling ratio ending on period end | {{VALUE}} | {{VALUE}} | {{VALUE}} | {{VALUE}} | {{INTERPRETATION}} |
| WAU / MAU | `wauPerMau` — rolling ratio ending on period end | {{VALUE}} | {{VALUE}} | {{VALUE}} | {{VALUE}} | {{INTERPRETATION}} |

### Acquisition and Sessions

| KPI | API metric / basis | Current | Previous | Absolute change | % change | Interpretation |
|---|---|---:|---:|---:|---:|---|
| Sessions | `sessions` | {{VALUE}} | {{VALUE}} | {{VALUE}} | {{VALUE}} | {{INTERPRETATION}} |
| Engaged sessions | `engagedSessions` | {{VALUE}} | {{VALUE}} | {{VALUE}} | {{VALUE}} | {{INTERPRETATION}} |
| Engagement rate | `engagementRate` | {{VALUE}} | {{VALUE}} | {{VALUE}} | {{VALUE}} | {{INTERPRETATION}} |
| Bounce rate | `bounceRate` | {{VALUE}} | {{VALUE}} | {{VALUE}} | {{VALUE}} | {{INTERPRETATION}} |
| Average session duration | `averageSessionDuration` | {{VALUE}} | {{VALUE}} | {{VALUE}} | {{VALUE}} | {{INTERPRETATION}} |
| Sessions per user | `sessionsPerUser` | {{VALUE}} | {{VALUE}} | {{VALUE}} | {{VALUE}} | {{INTERPRETATION}} |

### Engagement, Content, and Events

| KPI | API metric / basis | Current | Previous | Absolute change | % change | Interpretation |
|---|---|---:|---:|---:|---:|---|
| Views | `screenPageViews` | {{VALUE}} | {{VALUE}} | {{VALUE}} | {{VALUE}} | {{INTERPRETATION}} |
| Views per session | `screenPageViewsPerSession` | {{VALUE}} | {{VALUE}} | {{VALUE}} | {{VALUE}} | {{INTERPRETATION}} |
| Views per user | `screenPageViewsPerUser` | {{VALUE}} | {{VALUE}} | {{VALUE}} | {{VALUE}} | {{INTERPRETATION}} |
| Event count | `eventCount` | {{VALUE}} | {{VALUE}} | {{VALUE}} | {{VALUE}} | {{INTERPRETATION}} |
| Events per session | `eventsPerSession` | {{VALUE}} | {{VALUE}} | {{VALUE}} | {{VALUE}} | {{INTERPRETATION}} |
| Event count per user | `eventCountPerUser` | {{VALUE}} | {{VALUE}} | {{VALUE}} | {{VALUE}} | {{INTERPRETATION}} |
| User engagement duration | `userEngagementDuration` | {{VALUE}} | {{VALUE}} | {{VALUE}} | {{VALUE}} | {{INTERPRETATION}} |
| Scrolled users | `scrolledUsers` | {{VALUE}} | {{VALUE}} | {{VALUE}} | {{VALUE}} | {{INTERPRETATION}} |

### Key Events and Outcomes

| KPI | API metric / basis | Current | Previous | Absolute change | % change | Interpretation |
|---|---|---:|---:|---:|---:|---|
| Key events | `keyEvents` | {{VALUE}} | {{VALUE}} | {{VALUE}} | {{VALUE}} | {{INTERPRETATION}} |
| Session key event rate | `sessionKeyEventRate` | {{VALUE}} | {{VALUE}} | {{VALUE}} | {{VALUE}} | {{INTERPRETATION}} |
| User key event rate | `userKeyEventRate` | {{VALUE}} | {{VALUE}} | {{VALUE}} | {{VALUE}} | {{INTERPRETATION}} |

### Revenue and Ecommerce

| KPI | API metric / basis | Current | Previous | Absolute change | % change | Interpretation |
|---|---|---:|---:|---:|---:|---|
| Total revenue | `totalRevenue` | {{VALUE}} | {{VALUE}} | {{VALUE}} | {{VALUE}} | {{INTERPRETATION}} |
| Purchase revenue | `purchaseRevenue` | {{VALUE}} | {{VALUE}} | {{VALUE}} | {{VALUE}} | {{INTERPRETATION}} |
| Gross purchase revenue | `grossPurchaseRevenue` | {{VALUE}} | {{VALUE}} | {{VALUE}} | {{VALUE}} | {{INTERPRETATION}} |
| Total ad revenue | `totalAdRevenue` | {{VALUE}} | {{VALUE}} | {{VALUE}} | {{VALUE}} | {{INTERPRETATION}} |
| Transactions | `transactions` | {{VALUE}} | {{VALUE}} | {{VALUE}} | {{VALUE}} | {{INTERPRETATION}} |
| Ecommerce purchases | `ecommercePurchases` | {{VALUE}} | {{VALUE}} | {{VALUE}} | {{VALUE}} | {{INTERPRETATION}} |
| Total purchasers | `totalPurchasers` | {{VALUE}} | {{VALUE}} | {{VALUE}} | {{VALUE}} | {{INTERPRETATION}} |
| First-time purchasers | `firstTimePurchasers` | {{VALUE}} | {{VALUE}} | {{VALUE}} | {{VALUE}} | {{INTERPRETATION}} |
| First-time purchaser rate | `firstTimePurchaserRate` | {{VALUE}} | {{VALUE}} | {{VALUE}} | {{VALUE}} | {{INTERPRETATION}} |
| Transactions per purchaser | `transactionsPerPurchaser` | {{VALUE}} | {{VALUE}} | {{VALUE}} | {{VALUE}} | {{INTERPRETATION}} |
| Average purchase revenue | `averagePurchaseRevenue` | {{VALUE}} | {{VALUE}} | {{VALUE}} | {{VALUE}} | {{INTERPRETATION}} |
| Average purchase revenue per user | `averagePurchaseRevenuePerUser` | {{VALUE}} | {{VALUE}} | {{VALUE}} | {{VALUE}} | {{INTERPRETATION}} |
| Average purchase revenue per paying user | `averagePurchaseRevenuePerPayingUser` | {{VALUE}} | {{VALUE}} | {{VALUE}} | {{VALUE}} | {{INTERPRETATION}} |
| Average revenue per user | `averageRevenuePerUser` | {{VALUE}} | {{VALUE}} | {{VALUE}} | {{VALUE}} | {{INTERPRETATION}} |
| Refund amount | `refundAmount` | {{VALUE}} | {{VALUE}} | {{VALUE}} | {{VALUE}} | {{INTERPRETATION}} |
| Items viewed | `itemsViewed` | {{VALUE}} | {{VALUE}} | {{VALUE}} | {{VALUE}} | {{INTERPRETATION}} |
| Items added to cart | `itemsAddedToCart` | {{VALUE}} | {{VALUE}} | {{VALUE}} | {{VALUE}} | {{INTERPRETATION}} |
| Items checked out | `itemsCheckedOut` | {{VALUE}} | {{VALUE}} | {{VALUE}} | {{VALUE}} | {{INTERPRETATION}} |
| Items purchased | `itemsPurchased` | {{VALUE}} | {{VALUE}} | {{VALUE}} | {{VALUE}} | {{INTERPRETATION}} |
| Cart-to-view rate | `cartToViewRate` | {{VALUE}} | {{VALUE}} | {{VALUE}} | {{VALUE}} | {{INTERPRETATION}} |
| Purchase-to-view rate | `purchaseToViewRate` | {{VALUE}} | {{VALUE}} | {{VALUE}} | {{VALUE}} | {{INTERPRETATION}} |

### Advertising and Organic Search

| KPI | API metric / basis | Current | Previous | Absolute change | % change | Interpretation |
|---|---|---:|---:|---:|---:|---|
| Advertiser ad impressions | `advertiserAdImpressions` | {{VALUE}} | {{VALUE}} | {{VALUE}} | {{VALUE}} | {{INTERPRETATION}} |
| Advertiser ad clicks | `advertiserAdClicks` | {{VALUE}} | {{VALUE}} | {{VALUE}} | {{VALUE}} | {{INTERPRETATION}} |
| Advertiser ad cost | `advertiserAdCost` | {{VALUE}} | {{VALUE}} | {{VALUE}} | {{VALUE}} | {{INTERPRETATION}} |
| Advertiser ad cost per click | `advertiserAdCostPerClick` | {{VALUE}} | {{VALUE}} | {{VALUE}} | {{VALUE}} | {{INTERPRETATION}} |
| Advertiser ad cost per key event | `advertiserAdCostPerKeyEvent` | {{VALUE}} | {{VALUE}} | {{VALUE}} | {{VALUE}} | {{INTERPRETATION}} |
| Return on ad spend | `returnOnAdSpend` | {{VALUE}} | {{VALUE}} | {{VALUE}} | {{VALUE}} | {{INTERPRETATION}} |
| Organic Google Search impressions | `organicGoogleSearchImpressions` | {{VALUE}} | {{VALUE}} | {{VALUE}} | {{VALUE}} | {{INTERPRETATION}} |
| Organic Google Search clicks | `organicGoogleSearchClicks` | {{VALUE}} | {{VALUE}} | {{VALUE}} | {{VALUE}} | {{INTERPRETATION}} |
| Organic Google Search click-through rate | `organicGoogleSearchClickThroughRate` | {{VALUE}} | {{VALUE}} | {{VALUE}} | {{VALUE}} | {{INTERPRETATION}} |
| Organic Google Search average position | `organicGoogleSearchAveragePosition` | {{VALUE}} | {{VALUE}} | {{VALUE}} | {{VALUE}} | {{INTERPRETATION}} |

### App Quality

| KPI | API metric / basis | Current | Previous | Absolute change | % change | Interpretation |
|---|---|---:|---:|---:|---:|---|
| Crash-affected users | `crashAffectedUsers` | {{VALUE}} | {{VALUE}} | {{VALUE}} | {{VALUE}} | {{INTERPRETATION}} |
| Crash-free users rate | `crashFreeUsersRate` | {{VALUE}} | {{VALUE}} | {{VALUE}} | {{VALUE}} | {{INTERPRETATION}} |

### Property-Specific and Custom KPIs

| KPI | API name / formula | Scope and definition | Current | Previous | Absolute change | % change | Interpretation |
|---|---|---|---:|---:|---:|---:|---|
| {{CUSTOM_KPI_OR_NONE}} | {{API_NAME_OR_FORMULA}} | {{SCOPE_AND_DEFINITION}} | {{VALUE}} | {{VALUE}} | {{VALUE}} | {{VALUE}} | {{INTERPRETATION}} |

## 4. Acquisition Performance

### Session Acquisition

| Channel / source-medium | Sessions | Change | Engagement rate | Key events | Session key event rate | Revenue | Assessment |
|---|---:|---:|---:|---:|---:|---:|---|
| {{CHANNEL_OR_SOURCE}} | {{VALUE}} | {{VALUE}} | {{VALUE}} | {{VALUE}} | {{VALUE}} | {{VALUE}} | {{ASSESSMENT}} |

{{SESSION_ACQUISITION_FINDINGS}}

### First-User Acquisition

| First-user channel / source-medium | New users | Change | Engaged sessions | Key events | User key event rate | Revenue | Assessment |
|---|---:|---:|---:|---:|---:|---:|---|
| {{FIRST_USER_CHANNEL_OR_SOURCE}} | {{VALUE}} | {{VALUE}} | {{VALUE}} | {{VALUE}} | {{VALUE}} | {{VALUE}} | {{ASSESSMENT}} |

{{FIRST_USER_ACQUISITION_FINDINGS}}

### Campaign Performance

| Campaign | Scope / source | Sessions | Ad cost | Key events | Cost per key event | Revenue | ROAS | Change vs. previous | Assessment |
|---|---|---:|---:|---:|---:|---:|---:|---:|---|
| {{CAMPAIGN}} | {{SCOPE_AND_SOURCE}} | {{VALUE}} | {{VALUE}} | {{VALUE}} | {{VALUE}} | {{VALUE}} | {{VALUE}} | {{VALUE}} | {{ASSESSMENT}} |

{{CAMPAIGN_FINDINGS_AND_LIMITATIONS}}

## 5. Audience and Technology

### Geographic Performance

| Geography | Active users | Sessions | Engagement rate | Key events | Session key event rate | Revenue | Assessment |
|---|---:|---:|---:|---:|---:|---:|---|
| {{GEOGRAPHY}} | {{VALUE}} | {{VALUE}} | {{VALUE}} | {{VALUE}} | {{VALUE}} | {{VALUE}} | {{ASSESSMENT}} |

### Device, Platform, and Browser Performance

| Device / platform / browser | Active users | Sessions | Engagement rate | Key events | Session key event rate | Revenue | Assessment |
|---|---:|---:|---:|---:|---:|---:|---|
| {{TECHNOLOGY_SEGMENT}} | {{VALUE}} | {{VALUE}} | {{VALUE}} | {{VALUE}} | {{VALUE}} | {{VALUE}} | {{ASSESSMENT}} |

### New vs. Returning Users

| User state | Active users | Sessions | Engagement rate | Key events | User key event rate | Revenue | Assessment |
|---|---:|---:|---:|---:|---:|---:|---|
| {{USER_STATE}} | {{VALUE}} | {{VALUE}} | {{VALUE}} | {{VALUE}} | {{VALUE}} | {{VALUE}} | {{ASSESSMENT}} |

{{AUDIENCE_TECHNOLOGY_FINDINGS}}

## 6. Content and Landing Pages

### Landing Page Performance

| Landing page | Sessions | Change | Engagement rate | Bounce rate | Key events | Session key event rate | Revenue | Assessment |
|---|---:|---:|---:|---:|---:|---:|---:|---|
| {{LANDING_PAGE}} | {{VALUE}} | {{VALUE}} | {{VALUE}} | {{VALUE}} | {{VALUE}} | {{VALUE}} | {{VALUE}} | {{ASSESSMENT}} |

### Page and Screen Performance

| Page / screen | Views | Active users | Engagement duration | Scrolled users | Key events | Revenue | Assessment |
|---|---:|---:|---:|---:|---:|---:|---|
| {{PAGE_OR_SCREEN}} | {{VALUE}} | {{VALUE}} | {{VALUE}} | {{VALUE}} | {{VALUE}} | {{VALUE}} | {{ASSESSMENT}} |

{{CONTENT_AND_LANDING_PAGE_FINDINGS}}

## 7. Events and Key Events

### Event Performance

| Event | Event count | Change | Active users | Events per user | Key events | Event value / revenue | Assessment |
|---|---:|---:|---:|---:|---:|---:|---|
| {{EVENT_NAME}} | {{VALUE}} | {{VALUE}} | {{VALUE}} | {{VALUE}} | {{VALUE}} | {{VALUE}} | {{ASSESSMENT}} |

### Key Event Performance

| Key event | Count | Change | Session rate | User rate | Revenue / value | Measurement note | Assessment |
|---|---:|---:|---:|---:|---:|---|---|
| {{KEY_EVENT_NAME}} | {{VALUE}} | {{VALUE}} | {{VALUE}} | {{VALUE}} | {{VALUE}} | {{MEASUREMENT_NOTE}} | {{ASSESSMENT}} |

{{EVENT_AND_KEY_EVENT_FINDINGS}}

## 8. Ecommerce and Monetization

### Ecommerce Funnel

| Funnel stage | Current | Previous | Change | Step rate / loss | Assessment |
|---|---:|---:|---:|---:|---|
| Item views | {{VALUE}} | {{VALUE}} | {{VALUE}} | {{VALUE}} | {{ASSESSMENT}} |
| Adds to cart | {{VALUE}} | {{VALUE}} | {{VALUE}} | {{VALUE}} | {{ASSESSMENT}} |
| Checkouts | {{VALUE}} | {{VALUE}} | {{VALUE}} | {{VALUE}} | {{ASSESSMENT}} |
| Purchases | {{VALUE}} | {{VALUE}} | {{VALUE}} | {{VALUE}} | {{ASSESSMENT}} |

### Product Performance

| Product / item | Views | Adds to cart | Checkouts | Items purchased | Item revenue | Refunds | Assessment |
|---|---:|---:|---:|---:|---:|---:|---|
| {{PRODUCT_OR_ITEM}} | {{VALUE}} | {{VALUE}} | {{VALUE}} | {{VALUE}} | {{VALUE}} | {{VALUE}} | {{ASSESSMENT}} |

### Revenue Analysis

{{REVENUE_AND_MONETIZATION_ANALYSIS}}

## 9. Trends and Anomalies

### Daily Trend

| Date / interval | Active users | Sessions | Engagement rate | Key events | Revenue | Ad cost | Notable observation |
|---|---:|---:|---:|---:|---:|---:|---|
| {{DATE_OR_INTERVAL}} | {{VALUE}} | {{VALUE}} | {{VALUE}} | {{VALUE}} | {{VALUE}} | {{VALUE}} | {{OBSERVATION}} |

### Material Anomalies and Explanatory Signals

1. {{ANOMALY_OR_NONE_WITH_DATE_MAGNITUDE_AND_HYPOTHESIS}}
2. {{ANOMALY_OR_NONE_WITH_DATE_MAGNITUDE_AND_HYPOTHESIS}}
3. {{ANOMALY_OR_NONE_WITH_DATE_MAGNITUDE_AND_HYPOTHESIS}}

{{TREND_CONTEXT_AND_SEASONALITY_NOTES}}

## 10. Strengths

| Strength | Quantified evidence | Why it matters | Confidence |
|---|---|---|---|
| {{STRENGTH}} | {{EVIDENCE}} | {{BUSINESS_IMPACT}} | {{CONFIDENCE}} |

{{STRENGTHS_SYNTHESIS}}

## 11. Weaknesses and Risks

| Weakness / risk | Quantified evidence | Business impact | Likely driver or hypothesis | Confidence |
|---|---|---|---|---|
| {{WEAKNESS_OR_RISK}} | {{EVIDENCE}} | {{BUSINESS_IMPACT}} | {{DRIVER_OR_HYPOTHESIS}} | {{CONFIDENCE}} |

{{WEAKNESSES_AND_RISKS_SYNTHESIS}}

## 12. Prioritized Action Plan

| Priority | Evidence / problem | Action | Intended KPI movement | Owner role | Time horizon | Validation method |
|---:|---|---|---|---|---|---|
| 1 | {{EVIDENCE}} | {{ACTION}} | {{TARGET_DIRECTION_NOT_UNSUPPORTED_FORECAST}} | {{OWNER_ROLE}} | {{TIME_HORIZON}} | {{VALIDATION_METHOD}} |
| 2 | {{EVIDENCE}} | {{ACTION}} | {{TARGET_DIRECTION_NOT_UNSUPPORTED_FORECAST}} | {{OWNER_ROLE}} | {{TIME_HORIZON}} | {{VALIDATION_METHOD}} |
| 3 | {{EVIDENCE}} | {{ACTION}} | {{TARGET_DIRECTION_NOT_UNSUPPORTED_FORECAST}} | {{OWNER_ROLE}} | {{TIME_HORIZON}} | {{VALIDATION_METHOD}} |
| 4 | {{EVIDENCE}} | {{ACTION}} | {{TARGET_DIRECTION_NOT_UNSUPPORTED_FORECAST}} | {{OWNER_ROLE}} | {{TIME_HORIZON}} | {{VALIDATION_METHOD}} |
| 5 | {{EVIDENCE}} | {{ACTION}} | {{TARGET_DIRECTION_NOT_UNSUPPORTED_FORECAST}} | {{OWNER_ROLE}} | {{TIME_HORIZON}} | {{VALIDATION_METHOD}} |

{{ACTION_PLAN_SEQUENCING_AND_DEPENDENCIES}}

## 13. Data Quality and Limitations

- **Credential and access status:** {{ACCESS_STATUS_WITHOUT_SECRETS}}
- **Property and stream coverage:** {{PROPERTY_STREAM_COVERAGE}}
- **Tagging and key-event health:** {{TAGGING_AND_KEY_EVENT_HEALTH}}
- **Attribution and reporting identity:** {{ATTRIBUTION_AND_IDENTITY_LIMITATION_OR_NONE}}
- **Consent mode / modeled data:** {{CONSENT_AND_MODELING_LIMITATION_OR_NONE}}
- **API response metadata:** {{API_RESPONSE_METADATA}}
- **Thresholding and sampling:** {{THRESHOLDING_AND_SAMPLING_LIMITATION_OR_NONE}}
- **Unique-count approximation:** {{UNIQUE_COUNT_APPROXIMATION_LIMITATION_OR_NONE}}
- **High-cardinality `(other)` data loss:** {{HIGH_CARDINALITY_OTHER_LIMITATION_OR_NONE}}
- **Metric access restrictions:** {{METRIC_ACCESS_RESTRICTIONS_OR_NONE}}
- **Missing or incompatible metrics:** {{MISSING_INCOMPATIBLE_METRICS_OR_NONE}}
- **Period comparability:** {{PERIOD_COMPARABILITY_LIMITATION_OR_NONE}}
- **Other limitations:** {{OTHER_LIMITATIONS_OR_NONE}}

{{DATA_QUALITY_CONCLUSION}}

## 14. Appendix

### KPI Definitions and Assumptions

| KPI / term | Definition or assumption used in this report |
|---|---|
| {{KPI_OR_TERM}} | {{DEFINITION_OR_ASSUMPTION}} |

### API Coverage and Query Notes

| Query family | Dimensions | Metrics / purpose | Status and caveat |
|---|---|---|---|
| Response / property metadata | None | Data API timezone and currency; optional Admin API name, type, and service level | {{STATUS_AND_CAVEAT}} |
| KPI totals | None | Authoritative period totals | {{STATUS_AND_CAVEAT}} |
| Daily trend | `date` | Trend and anomaly detection | {{STATUS_AND_CAVEAT}} |
| Session acquisition | Session-scoped channel/source/campaign | Acquisition quality and outcomes | {{STATUS_AND_CAVEAT}} |
| First-user acquisition | First-user channel/source/campaign | New-user acquisition | {{STATUS_AND_CAVEAT}} |
| Content | Landing page and page/screen | Post-click and content performance | {{STATUS_AND_CAVEAT}} |
| Events | `eventName` | Event and key-event performance | {{STATUS_AND_CAVEAT}} |
| Audience / technology | Geography, device, platform, browser | Segment diagnostics | {{STATUS_AND_CAVEAT}} |
| Ecommerce | Product/item and funnel metrics | Commerce performance | {{STATUS_AND_CAVEAT}} |
| Advertising / organic search | Campaign and Search Console dimensions | Cost, ROAS, and organic search visibility | {{STATUS_AND_CAVEAT}} |
| Custom metrics | Property-specific metadata definitions | Business-specific outcomes | {{STATUS_AND_CAVEAT}} |

{{APPENDIX_NOTES}}
