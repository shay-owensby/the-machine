---
name: gbp-no-website
description: Audit Google Business Profiles in Google Maps for a user-supplied business category and city/state, then report profiles whose GBP has no Website field. Use for local website-opportunity discovery, not for general web-presence research or arbitrary lead lists.
---

# GBP No-Website Opportunities

Find active, relevant Google Business Profiles whose profile does not have a website attached. Treat this as a browser-based, read-only audit of Google Maps.

## Inputs

Require:

- one business category;
- one city and state.

Ask only for a missing or materially ambiguous required input. Default to the named city limits or explicit GBP service area; do not silently expand to surrounding cities or a metro area.

Before auditing, read [references/audit-method.md](references/audit-method.md). It defines the coverage, verification, deduplication, stopping, and reporting rules for this skill.

## Operating rules

- Use an available browser-control capability to inspect Google Maps. Prefer the in-app browser unless the user requests Chrome or an existing Chrome session is genuinely needed.
- Work from the public information shown on Google Maps. Do not claim, edit, message, call, or otherwise interact with a business.
- Do not click through to external websites merely to test them. The qualifying condition is whether the GBP itself displays a primary Website action or field.
- If the Website field contains any destination—including a social profile, marketplace page, corporate location page, or Google-hosted site—the profile does not qualify. Broken or low-quality destinations still count as attached websites.
- Appointment, order, menu, reservation, and social links do not count as a Website field unless Google presents that link as the profile's primary Website action.
- A website found outside the GBP does not disqualify a listing. This skill audits the profile configuration, not the business's total web presence.
- Never infer “no website” from a search-results card alone. Open the distinct GBP detail view and verify that the Website action/field is absent after inspecting the available details.
- Do not evade CAPTCHAs, login gates, consent gates, rate limits, or other access controls. On interruption, save a partial report with the checkpoint and explain what remains.

## Output

Save the finished audit relative to the current working project at:

`./website-opportunities/YYYYmmdd/YYYYmmdd-website-opportunities.md`

Use the local calendar date at execution time. Create missing directories and the file. If that day's file already exists, preserve unrelated audits and append a new category/location section. If the same category/location audit already exists, update that section rather than creating a misleading duplicate.

Always write the report, including when zero opportunities qualify or the audit is partial. Keep factual observations separate from coverage limitations, and do not call a browser audit exhaustive unless the audit method's completion conditions were met without unresolved access or result-cap limitations.
