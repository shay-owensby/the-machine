# Mailchimp Report Data Contract

Use this contract for every report produced by the skill.

## Authentication and configuration

- API base URL: `https://<server-prefix>.api.mailchimp.com/3.0/`.
- Work from the active client project root. Resolve `./.env` relative to that root, never relative to the skill directory.
- Supported credential variables:
  - `MAILCHIMP_API_KEY` — preferred for a single account; authenticate with HTTP Basic Auth. Derive the server prefix from the final `-<dc>` suffix when present.
  - `MAILCHIMP_ACCESS_TOKEN` — OAuth bearer token; requires `MAILCHIMP_SERVER_PREFIX` or `MAILCHIMP_DC`.
  - `MAILCHIMP_SERVER_PREFIX` or `MAILCHIMP_DC` — optional with a suffixed API key and required with OAuth.
- Optional validation and scope variables:
  - `MAILCHIMP_ACCOUNT_ID` — expected account ID; stop if the API root returns a different account.
  - `MAILCHIMP_LIST_IDS` — comma-separated audience/list allowlist.
  - `MAILCHIMP_STORE_IDS` — comma-separated connected-store allowlist.
  - `MAILCHIMP_REPORT_TIMEZONE` or `REPORT_TIMEZONE` — explicit IANA override when the account time zone is missing or intentionally superseded.
- Environment variables may supply the same keys and take precedence over `.env` for the current process.
- Never shell-source `.env`. Load it with a dotenv parser or `scripts/mailchimp_get.py`. Do not print values, pass credentials in command arguments, copy the file, or include secrets in errors or outputs.
- Validate access with `GET /`. Record account name, account ID, role, industry, plan, account time zone, and API observation time, but do not include the account email, username, personal name, avatar, postal contact, or login history in the report.
- If credentials, server prefix, or access are missing or invalid, state only the missing configuration category and stop. Never invent data.

## Scope selection

Choose scope in this order:

1. Audience, campaign-type, or store filters explicitly supplied by the user for the current run.
2. Valid configured `MAILCHIMP_LIST_IDS` and `MAILCHIMP_STORE_IDS`.
3. All active audiences and associated stores accessible in the authenticated Mailchimp account.

Validate every configured ID against the live account. If a configured ID is missing, inactive, inaccessible, or belongs to a different account, report the configuration issue rather than substituting another ID. A user-supplied filter may intentionally override project defaults for that run; disclose the override.

Campaign reports do not accept a list filter. Retrieve the date-bounded report set and filter locally by each report's `list_id`. Do not analyze or retain out-of-scope rows beyond what is required to apply that filter.

## Reporting periods

Use two adjacent periods of complete calendar days:

- Report date `R`: today in the selected reporting time zone.
- Current: `R - 30 days` through `R - 1 day`, inclusive.
- Previous: `R - 60 days` through `R - 31 days`, inclusive.

Choose the reporting time zone in this order:

1. A time zone explicitly supplied by the user.
2. `MAILCHIMP_REPORT_TIMEZONE` or `REPORT_TIMEZONE`.
3. `account_timezone` returned by `GET /`.
4. The client project's local IANA time zone when the API value is absent or invalid.

Record the zone and source. Use `scripts/report_dates.py` to generate the local dates and ISO 8601 boundaries. The reporting windows are half-open timestamp intervals: `start <= send_time < next_midnight`. Because the API describes `since_send_time` and `before_send_time` as strict comparisons, widen the server query slightly if needed and always apply the exact boundaries locally after parsing `send_time`.

The main period assignment is the campaign's send date. Engagement and revenue fields are lifetime-to-observation totals attributed to campaigns sent in the selected window, not events that necessarily occurred during the window. Record the API observation time and flag current campaigns sent within the last 72 hours as still maturing.

## Completeness and API behavior

- Use the official [Mailchimp Marketing API reference](https://mailchimp.com/developer/marketing/api/) and live response schema as the authority.
- Use only `GET` endpoints. Prefer aggregate report resources; recipient-level rows are prohibited for ordinary KPI reporting.
- Paginate until the collected row count matches `total_items` or the API returns no more rows. Use `count=1000` where supported and advance `offset` by the actual number returned.
- Mailchimp limits the Marketing API to 10 simultaneous connections. Keep reporting concurrency below that limit; four or fewer concurrent requests is a safe ceiling. Retry `429` and transient `5xx` responses only with bounded backoff and honor `Retry-After` when present.
- Treat `401` as invalid/revoked credentials, `403` as role or plan restriction, and `404` as an inaccessible or inapplicable resource after verifying the ID. Never translate missing/null/permission-gated values to zero.
- Query the current and previous windows with identical scope and rules. Record every endpoint family attempted and its status.
- Include all numeric performance fields returned from `/reports`, applicable child reports, click details, domain performance, locations, EepURL, e-commerce product activity, audience activity, and other aggregate endpoints required by the query plan. Canonical metrics belong in their named scorecard rows; all remaining performance fields belong in `All Additional Numeric KPI Fields Returned by Mailchimp`. Technical IDs, pagination counters, coordinates, time-zone offsets, and configuration enums are not KPIs; retain them only where needed for scope or reconciliation.
- Do not persist raw API responses unless the user explicitly requests them. If temporary processing is necessary, use a private temporary directory outside the report tree and remove it after the final report is validated.

## Canonical KPI definitions

Calculate at full precision and round only for presentation.

### Campaign volume and delivery

- **Campaigns sent:** count unique top-level sent campaign reports in the window after scope filtering. Child variants are diagnostics, not extra portfolio campaigns, unless the parent aggregate is unavailable and the report clearly uses deduplicated child totals instead.
- **Emails sent:** sum `emails_sent` across the deduplicated campaign set.
- **Hard bounces / soft bounces / syntax errors:** sums of the corresponding `bounces` fields.
- **Total bounces:** hard bounces + soft bounces. Keep syntax errors separate unless Mailchimp explicitly includes them in a returned bounce total.
- **Successful deliveries:** emails sent - hard bounces - soft bounces. If a returned Mailchimp delivery total differs, preserve both, use the documented API total, and explain the reconciliation.
- **Delivery rate:** successful deliveries / emails sent × 100.
- **Bounce rate:** total bounces / emails sent × 100.
- **Average recipients per campaign:** emails sent / campaigns sent.
- **Campaign frequency:** campaigns sent / (30 / 7), shown as campaigns per week.

### Opens, clicks, and sharing

- **Total opens:** sum `opens.opens_total`.
- **Proxy-excluded total opens:** sum `opens.proxy_excluded_opens` when returned for every included campaign; otherwise report partial coverage or `N/A`.
- **Unique opens:** sum `opens.unique_opens` across campaigns. This is unique within each campaign, not deduplicated people across the portfolio.
- **Proxy-excluded unique opens:** sum `opens.proxy_excluded_unique_opens` under the same coverage rule.
- **Open rate:** unique opens / successful deliveries × 100. Compare against returned campaign `open_rate` only for reconciliation; never average rates.
- **Proxy-excluded open rate:** proxy-excluded unique opens / successful deliveries × 100. Prefer this metric for interpretation when coverage is complete because proxy opens can distort conventional opens.
- **Total clicks:** sum `clicks.clicks_total`.
- **Unique clicks:** sum `clicks.unique_clicks`; preserve Mailchimp's field label and do not treat it as unique people.
- **Unique subscriber clicks:** sum `clicks.unique_subscriber_clicks`, representing campaign recipients who clicked.
- **Click rate:** unique subscriber clicks / successful deliveries × 100, reconciled with Mailchimp's returned `clicks.click_rate`.
- **Click-to-open rate (CTOR):** unique subscriber clicks / unique opens × 100. Also provide proxy-excluded CTOR when proxy-excluded unique opens are complete. Label the denominator.
- **Forwards / forward opens:** sums of `forwards.forwards_count` and `forwards.forwards_opens`.
- **Social-sharing metrics:** sum Facebook-like and EepURL values only when supported. Treat EepURL referrer and social data as partial platform-specific tracking, not total social impact.

### List health and negative signals

- **Unsubscribes:** sum campaign `unsubscribed` for campaign-attributed performance. Keep audience-activity `unsubs` separate because its attribution and timing differ.
- **Unsubscribe rate:** campaign unsubscribes / successful deliveries × 100.
- **Abuse complaints:** sum `abuse_reports`.
- **Complaint rate:** abuse complaints / successful deliveries × 100.
- **Audience subscribes / audience unsubscribes / other adds / other removes / hard-bounce removals:** sum the daily `/lists/{list_id}/activity` fields inside each exact calendar window.
- **Net audience change:** subscribes + other adds - audience unsubscribes - other removes - hard-bounce removals. State that this is reconstructed from Mailchimp activity categories.
- **Audience growth rate:** net audience change / reconstructed starting active members × 100 only when an exact start boundary can be supported. Otherwise report `N/A — exact period-start audience size unavailable` and retain net change.
- **Active audience size:** use `lists[].stats.member_count` as an observation-time snapshot. Do not present it as an exact period-end historical value unless a boundary snapshot exists.

### Revenue and commerce

- **Orders:** sum `ecommerce.total_orders`.
- **Gross sales / total spent:** sum `ecommerce.total_spent`; Mailchimp describes this as order totals without deductions.
- **Revenue:** sum `ecommerce.total_revenue`; Mailchimp describes this as order totals less shipping and tax.
- **Average order value:** revenue / orders.
- **Revenue per delivered email:** revenue / successful deliveries.
- **Revenue per 1,000 delivered:** revenue / successful deliveries × 1,000.
- **Click-to-order rate:** orders / unique subscriber clicks × 100. Label it as a campaign-attributed ratio, not a user-level conversion funnel.
- Never sum currencies. Produce separate scorecards by currency and mark a portfolio revenue total `N/A` when more than one currency is present.

### Changes and formatting

- **Absolute change:** current - previous.
- **Percent change:** `(current - previous) / abs(previous) × 100`.
- When previous is zero and current is nonzero, show the absolute change and `N/M — prior period was zero`. When both are zero, show `0.0%`. For non-comparable metrics, show `N/A — <reason>`.
- Round counts to whole numbers, currency to two decimals with its ISO currency code, rates and percentage-point changes to one decimal, and ratios to two decimals. Use `pp` for absolute rate change and `%` for relative change.

## Reconciliation rules

Before interpreting results:

1. Match `/campaigns` and `/reports` by campaign ID and exact `send_time`. Explain missing reports, unsent campaigns, deleted/inactive lists, or permission restrictions.
2. For A/B, multivariate, RSS, Timewarp, and other parent-child structures, use the parent report as the portfolio total when it is complete. Use sub-reports for variant diagnostics only. If the parent is incomplete, construct one child-based total and document it; never add parent and children together.
3. Recalculate additive totals from the deduplicated campaign set. Recalculate rates from aggregate numerators and denominators. Do not sum percentages, average rates, or deduplicate recipients across campaigns without person-level data.
4. Reconcile `emails_sent`, `delivery_status`, bounces, opens, clicks, unsubs, complaints, and e-commerce totals. Preserve API discrepancies and identify the chosen source.
5. Keep campaign-attributed unsubscribes separate from audience activity. Keep current audience snapshots separate from exact-window flows.
6. Keep link, domain, location, product, and time-series breakdowns tied to their parent campaign. State when an endpoint returns only top rows rather than complete coverage.
7. Keep list benchmarks and industry benchmarks separate from period results. Mailchimp list-stat percentages may use a 0–100 scale while campaign rates commonly use 0–1; normalize before comparing.
8. Keep each store currency separate. Do not apply an exchange rate unless the user supplies and authorizes a rate source.

## Analytical standard

- Every executive claim includes a quantified comparison and scope.
- A strength or weakness identifies the KPI, direction, magnitude, affected campaign/audience/content set, business significance, and confidence caveat when relevant.
- An action connects to evidence, names an owner role, specifies timing, defines a measurable success criterion and guardrail, and states the next evaluation window.
- Distinguish `Observation`, `Hypothesis`, and `Validation`. Period-over-period association is not causal proof.
- Segment by campaign, campaign type, audience, subject/content theme, send day/time, domain, link, automation/manual send, experiment variant, and store/product when sample size supports it.
- Flag comparisons with fewer than five campaigns in either period as low confidence. Do not rank one-off campaigns as a durable pattern without saying so.
- Flag campaigns younger than 72 hours at observation time as maturing. Previous-period campaigns have had longer to accrue late opens, clicks, and revenue; call out this asymmetry.
- Treat conventional open metrics cautiously because Apple Mail Privacy Protection and other proxies can inflate opens. Prefer proxy-excluded metrics when complete, and use clicks, conversions, complaints, and unsubscribes as stronger action signals.
- Do not infer creative quality from subject lines alone. Campaign content retrieval is optional and should occur only when content-level diagnosis is needed; summarize content without copying entire emails into the report.
- Use Mailchimp-provided industry stats only when returned for the account and label them as contextual benchmarks, not user-supplied goals.

## Output contract

- Destination: `./analytics-insights/mailchimp/YYYY/YYYYmmdd-mailchimp-report.md`.
- The filename date and year directory use the report-generation date in the selected reporting time zone.
- Copy the report template headings and canonical KPI rows exactly. Replace every placeholder. Variable-row placeholders may expand to any number of Markdown rows.
- Use `N/A — <specific reason>` instead of removing a row or leaving a blank cell.
- The only permanent output is the final Markdown report unless the user explicitly requests raw exports.
