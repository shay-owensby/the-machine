# Google Ads reporting data contract

Use this contract for every report produced by the skill.

## 1. Access and authentication

Google Cloud Console is the configuration layer, not the reporting endpoint. The data source is the Google Ads API.

### Authoritative client configuration

The client project's root `./.env` always contains the Google Cloud Console and Google Ads API configuration for this workflow. Resolve it relative to the current client project, not relative to the skill folder. Inspect it before asking the user for any account or credential information.

Use `scripts/check_env_config.py --env-file ./.env` to verify presence without exposing values. Load the selected values programmatically with a dotenv parser. Do not run `source ./.env`, because dotenv files are data and must not be executed as shell code. Do not print the file, display matching lines, include values in command arguments, or copy values into generated artifacts.

The checker recognizes the canonical variables and common aliases for:

- Google Ads developer token.
- OAuth client ID and client secret.
- OAuth refresh token.
- Google Ads customer ID.
- Optional manager/login customer ID.
- Optional Google Cloud project ID.

If a project uses a supported combined JSON configuration variable, load and validate it in memory without printing it. Prefer explicit variables when both forms exist. Missing or empty required values are a configuration blocker; report only the missing logical category, never neighboring keys or values.

Required inputs:

- Target Google Ads customer ID, digits only.
- `login-customer-id`, digits only, when authenticating through a manager account.
- Google Ads developer token with access appropriate to the target account.
- OAuth 2.0 client ID, client secret, and refresh token, or an already configured supported Google Ads client-library credential source.
- An OAuth user that can access the target Google Ads account.

Use the newest stable Google Ads API version supported by the installed official client library. Prefer the official client library and `GoogleAdsService.SearchStream`; use REST only when the environment already has a secure OAuth flow. Validate fields with the current Google Ads Fields service or official Query Builder rather than guessing when the API rejects a field combination.

Never print or persist secrets. Do not put secrets in command arguments if they can appear in process listings. Read them from the client project's `./.env` into process memory and pass them directly to the supported Google Ads client configuration. A service account is not the default: it requires Google Workspace domain-wide delegation and impersonation.

Useful official references:

- Authentication: <https://developers.google.com/google-ads/api/docs/oauth/overview>
- Call structure and headers: <https://developers.google.com/google-ads/api/docs/concepts/call-structure>
- GAQL overview: <https://developers.google.com/google-ads/api/docs/query/overview>
- Field compatibility: <https://developers.google.com/google-ads/api/fields/latest/overview>
- Credential security: <https://developers.google.com/google-ads/api/docs/productionize/secure-credentials>

## 2. Fixed date convention

Dates use the Google Ads customer account time zone.

- Report date: calendar date when the report is generated.
- Current period: the 30 complete calendar days ending yesterday, inclusive.
- Previous period: the immediately preceding 30 complete calendar days, inclusive.
- The windows never overlap and always contain exactly 30 dates.

Use explicit `segments.date BETWEEN 'YYYY-MM-DD' AND 'YYYY-MM-DD'` filters so both ranges are reproducible. A single 60-day daily query may be split locally, but aggregates must be calculated from the correct 30 rows. Only include today if the user explicitly requests partial-day reporting; then label the comparison as non-equivalent.

## 3. Query families

Run separate GAQL queries when resources or metrics cannot coexist. Add identifiers and names needed to make every row understandable. Retain zero-spend active entities where the API returns them; note that Google Ads may omit rows with zero metrics.

Use [gaql-query-plan.md](gaql-query-plan.md) as the minimum extraction plan. It is a query design contract, not a frozen API schema: validate selectable fields against the current API version and record any substitutions or failures.

### Account metadata

From `customer`, retrieve the descriptive name, customer ID, currency code, time zone, auto-tagging state, and test-account state when selectable.

### Campaign daily performance — required

From `campaign`, retrieve `segments.date` plus:

- Campaign ID, name, status, channel type/subtype, bidding strategy type, and optimization score when available.
- Budget amount and budget delivery metadata from the compatible campaign budget resource.
- Impressions, clicks, cost, CTR, average CPC, average CPM, interactions, interaction rate, engagements, and engagement rate.
- Conversions, conversion rate, cost per conversion, conversion value, value per cost, all conversions, all-conversion value, view-through conversions, and cross-device conversions.
- Video views, video view rate, average CPV, and quartile completion rates when applicable.
- Search impression share, search exact-match impression share, search top and absolute-top impression share, and lost impression share due to budget and rank when applicable.
- Invalid clicks and invalid click rate when available.

Use campaign daily data as the authoritative source for account totals after summing campaigns. Do not sum percentages or averages; recompute them from their base numerators and denominators whenever possible.

### Required diagnostic cuts

Pull the current and previous periods for every supported, material cut:

- Device and ad network type via campaign metrics segmented by device/network.
- Conversion action name/category/source with conversions and conversion value.
- Ad group performance.
- Ad/creative performance and status; include ad strength or policy state where exposed and useful.
- Keyword performance, match type, quality score components, and status for Search campaigns.
- Search-term performance and targeting status; include Performance Max campaign search-term views when supported.
- Landing-page performance from the landing-page or expanded-landing-page view.
- User location and geographic performance.
- Age and gender performance when privacy thresholds permit.
- Asset group, asset, listing group, product, or Shopping performance for Performance Max and Shopping campaigns when applicable.
- Call metrics when call reporting is configured.
- Change events from the available past-30-day window when they help explain a material shift. Do not imply that a recorded change caused the shift.

If a query family is not applicable, unsupported, privacy-suppressed, or denied, record that in Data Quality & Limitations and use `N/A — <reason>` in the corresponding template fields.

## 4. KPI catalog and calculations

The strict template contains the canonical KPI catalog. Keep every row.

Normalize API values first:

- Monetary micros: divide by 1,000,000 and express in the account currency.
- API share/rate fields returned as fractions: multiply by 100 for display as percentages.
- Preserve enough precision for calculation; round only for display.
- Counts: whole numbers unless the API returns modeled fractional conversions.

Recompute where base values exist:

| KPI | Formula |
|---|---|
| CTR | clicks / impressions |
| Average CPC | cost / clicks |
| Average CPM | cost / impressions × 1,000 |
| Interaction rate | interactions / impressions |
| Conversion rate | conversions / interactions; use the API conversion-rate definition when interaction types differ |
| Cost per conversion / CPA | cost / conversions |
| ROAS | conversion value / cost |
| Average conversion value | conversion value / conversions |
| Video view rate | video views / video impressions when comparable |
| Average CPV | video cost / video views |
| Call-through rate | phone calls / phone impressions |
| Cost per phone call | cost attributable to the same reporting cut / phone calls; label as approximate if attribution is not isolated |
| Average order value | revenue / orders; do not substitute conversions for orders without labeling the proxy |
| Gross profit margin | gross profit / revenue |

Period comparison:

- Absolute change = current − previous.
- Relative change = (current − previous) / previous.
- If previous is zero and current is nonzero, relative change is `N/M — no prior-period base`.
- If both are zero, relative change is `0.0%`.
- If either value is unavailable, change is `N/A`.
- Show percentage-point change for rate/share metrics in the absolute-change column and relative percentage change in the `% change` column.

Direction is contextual. Lower cost, CPA, wasted spend, invalid-click rate, and lost impression share are generally favorable. Higher volume, rate, value, ROAS, and impression share are generally favorable only when quality and economics remain acceptable. Never label spend growth as good or bad without outcome context.

## 5. Reconciliation and quality checks

Before analysis:

1. Confirm both ranges contain exactly 30 complete dates in the account time zone.
2. Confirm currency and customer ID match the requested account.
3. Sum raw campaign totals without segment duplication and compare them with any customer-level aggregate. Investigate material discrepancies.
4. Verify cost-micros conversion and percentage scaling.
5. Recompute ratio KPIs from summed bases instead of averaging row-level ratios.
6. Check that current and previous filters are identical except for dates.
7. Distinguish primary conversions from all conversions and conversion value from all-conversion value.
8. Flag missing conversion values, implausible zero values, tracking changes, disapproved ads, limited budgets, privacy suppression, and tiny samples.
9. Inspect material campaign additions, removals, status changes, budget changes, or tracking changes that make the periods less comparable.
10. Note that recent conversions may mature after the click because of conversion lag and later adjustments.

Treat a discrepancy as material when it could change a conclusion. As a default review trigger, investigate differences above both 1% and a meaningful business amount; do not present that heuristic as an industry benchmark.

## 6. Analysis standards

Executive conclusions must be traceable to reported evidence. A strength or weakness should cite at least one KPI and one campaign, segment, or diagnostic cut where possible.

Prioritize findings using:

- Business impact: spend, conversion volume/value, and strategic importance.
- Confidence: sample size, consistency across days, data quality, and tracking stability.
- Controllability: whether bidding, budget, targeting, creative, landing page, feed, or measurement changes could address it.
- Urgency: wasted spend, broken tracking, policy problems, or capped high-performing campaigns.

Avoid overreacting to small samples. Report at least one concrete strength and one concrete weakness when supported. If the account has no spend, conversions, or sufficient data, say so explicitly and make measurement or activation the first action.

Recommendations must include the evidence, proposed action, intended KPI direction, owner role, time horizon, and validation method. Do not promise an exact uplift unless a user-supplied experiment or forecast supports it. Prefer tests with a defined success metric and review window.

## 7. Output rules

- Follow `report-template.md` exactly: same headings, order, and KPI rows.
- Replace every `{{PLACEHOLDER}}`; use `N/A — <reason>` rather than deleting content.
- Use the account currency consistently and state it once in metadata and table labels.
- Include enough top and bottom entities to explain performance. Default to 5 each; use fewer only when fewer exist.
- Save to `./analytics-insights/google-ads/YYYY/YYYYmmdd-google-ads-report.md`.
- The filename and year folder use the report date in the account time zone.
- Validate with `scripts/validate_report.py` before delivery.
