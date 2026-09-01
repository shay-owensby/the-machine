---
name: report-mailchimp
description: Pull read-only Mailchimp Marketing API data, compare the latest 30 complete days with the immediately preceding 30 days, and deliver a comprehensive Markdown email-performance report with all available KPIs, an executive summary, strengths, weaknesses, and prioritized next steps. Use for one-off or recurring Mailchimp campaign reporting; do not use to send or modify campaigns, contacts, audiences, automations, stores, or account settings.
---

# Mailchimp Report

Produce an evidence-backed, read-only report for the Mailchimp account and audience scope configured in the active client project.

## Required resources

Before reading credentials, calling Mailchimp, analyzing results, or writing the report, read:

- [references/data-contract.md](references/data-contract.md) for authentication, scope, date rules, KPI definitions, reconciliation, analysis, and security requirements.
- [references/mailchimp-query-plan.md](references/mailchimp-query-plan.md) while retrieving the required and conditional Marketing API endpoint families.
- [references/report-template.md](references/report-template.md) for the mandatory output structure. Copy its headings and canonical KPI rows exactly.

## Workflow

1. Work from the client project root. Read Mailchimp configuration from `./.env` without printing, logging, committing, or copying secrets. Prefer `MAILCHIMP_API_KEY`; support `MAILCHIMP_ACCESS_TOKEN` with an explicit server prefix. Use `scripts/mailchimp_get.py` for safe authenticated GET requests when no installed official Mailchimp client is already available.
2. Call the API root to validate authentication and resolve account ID, account name, account time zone, role, industry, and available account-level benchmarks. Validate an optional configured account ID. Select audience and store scope using the data-contract precedence; never silently widen beyond explicit or configured IDs.
3. Run `scripts/report_dates.py --timezone <account-time-zone> --create-dir` to calculate two adjacent, non-overlapping 30-day windows and the required report destination. Filter campaigns by `send_time`, not creation or update time.
4. Follow the query plan. Retrieve every page of sent campaign reports for both windows, all applicable aggregate diagnostics, scoped audience activity, and connected-store context. Include regular, plain-text, RSS, A/B, multivariate, and automation email reports when Mailchimp returns them.
5. Reconcile parent and child reports before aggregation. Do not count both a parent campaign and its variants as separate sends in the same total. Recompute portfolio rates from valid numerators and denominators; never average campaign-level rates. Keep different currencies and audience scopes separate.
6. Compare current and previous periods using absolute and relative change. Include every numeric performance KPI returned by applicable Mailchimp report endpoints, even when it is not a canonical scorecard row. Use `N/A — <specific reason>` for unsupported, unavailable, inapplicable, permission-gated, or non-comparable values.
7. Separate observations from hypotheses. Quantify each strength and weakness. Each recommended action must name an owner role, timing, success measure, guardrail, and next review point. Account for campaign maturity, Apple Mail Privacy Protection, tracking settings, sample size, automation cadence, and e-commerce attribution.
8. Fill every section of the strict template without deleting, renaming, or reordering headings or canonical KPI rows. Remove every placeholder.
9. Save only the finished report to `./analytics-insights/mailchimp/YYYY/YYYYmmdd-mailchimp-report.md`, using the report-generation date in the Mailchimp account time zone for `YYYY` and the filename date. Do not leave raw API responses, recipient data, or secret-bearing files in the report tree.
10. Run `scripts/validate_report.py <report-path>` and correct every failure. Return a clickable link to the report and state both comparison periods.

## Boundaries

- Use only Mailchimp Marketing API `GET` endpoints. A reporting request does not authorize sending, scheduling, editing, deleting, archiving, tagging, syncing, triggering automations, changing contacts, or modifying configuration.
- Mailchimp API keys can confer broad account access. Treat them like passwords and never expose a credential, credential prefix, `.env` line, authorization header, or secret-bearing command.
- Aggregate KPI reporting does not require recipient-level endpoints. Do not retrieve or report email addresses, member records, IP addresses, individual activity, abuse reporters, or subscriber hashes unless the user separately requests and authorizes a contact-level analysis.
- Do not claim causation, fabricate targets, benchmarks, attribution, or projected uplift. Label hypotheses and state how to validate them.
- Do not hide weak, zero, or unavailable results. Explain material gaps and the concrete remediation when known.
- This skill covers the Marketing API. Mailchimp Transactional/Mandrill reporting is outside scope unless the user explicitly requests a separate transactional analysis.
