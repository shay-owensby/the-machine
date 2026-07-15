---
name: hr-compliance
description: Support employment-law compliance without giving legal advice — scope work to the client's jurisdictions, size, and industry, then work domain by domain (hiring/EEO, wage & hour & classification, leave & accommodation, workplace safety, anti-harassment, required postings, recordkeeping & retention, worker classification, privacy) to produce checklists and trackers with explicit "verify against current rule" flags and pointers to the authoritative labor agency. Use when the client wants a compliance checklist, a required-posting tracker, a recordkeeping/retention plan, a statutory-policy gap review, or an audit of a supplied HR artifact.
---

# HR Legal Compliance

Helps a client build and maintain employment-law compliance across the jurisdictions where they employ people — organized by compliance domain, grounded in their `legal.jurisdictions`, `company.size`, and industry, and always pointed at the authoritative source rather than asserting the law. This skill owns HR function #7 and exports to `legal-compliance/` (see the folder map).

**This is the highest legal-sensitivity area of the plugin.** Everything it produces is a compliance-support draft for the client's qualified employment counsel — never a compliance guarantee, a legal opinion, or a substitute for counsel. Read the two standing safety rules below before any work; they are paramount here.

## Setup gate (run first)

Enforce the config gate before any work, per `${CLAUDE_PLUGIN_ROOT}/skills/hr-config/SKILL.md`: look for `human-resources/config.yaml` at project root, require `version: 1` and `setup.completed: true`. If missing or invalid, STOP and tell the user exactly:
> Human resources isn't configured for this project yet. Run `/setup-human-resources` first.

Then load context: `company.about_file` (what the company does — for industry-specific obligations), `company.industry`, `company.size` (headcount — statutory thresholds key off it), `company.locations` and `legal.jurisdictions` (the authoritative scope for every claim), `company.employment_types`, `company.remote_policy` (remote workers can pull additional jurisdictions and posting duties into scope), `company.union`, and `legal.counsel_review`. Honor degraded modes: empty `legal.jurisdictions` → make **no** jurisdiction-specific legal claim at all; produce general best-practice frameworks clearly labeled "general best practice — must be localized to the company's jurisdictions and verified with counsel", and ask the user to complete `legal.jurisdictions`.

## Two standing safety rules (paramount — apply to everything below)

1. **Drafts, not legal advice.** Every output is a **compliance-support draft for the client's qualified HR professional and/or employment counsel** — never a compliance guarantee, a legal opinion, or a statement that the client "is compliant". Concretely:
   - **Scope every jurisdiction-specific item to `legal.jurisdictions`.** Name the jurisdiction it applies to ("Under `US-CA`…"), and flag it explicitly: **"verify against current `<jurisdiction>` rule"**. Work outside the configured jurisdictions is refused — say the jurisdiction isn't in scope and ask the user to add it to `legal.jurisdictions`.
   - **Never fabricate.** Do not invent a statute name, citation, numeric threshold, deadline, dollar figure, retention period, or filing requirement. If you don't have it from the user or an authoritative source, say it **must be verified** and name the source to check (the government labor agency for that jurisdiction). A plausible-sounding but unverified number is worse than an explicit "verify this".
   - **Stamp findings and trackers** with a visible banner: **"⚠️ Draft — requires review by qualified HR/legal counsel before use"** (always when `legal.counsel_review: true`; recommended regardless in this domain).
   - **Point to authority, don't assert it.** For each item, cite *where to verify* — the relevant government labor/employment agency, the jurisdiction's official posting page, the agency's recordkeeping guidance — rather than presenting the rule as settled.
2. **Confidential by default.** Compliance work touches sensitive material (employee records, investigation outcomes, medical/accommodation and payroll data). Keep audits, trackers, and any identifiable data **in-project** under `legal-compliance/` (and identifiable records under the confidential zone `confidentiality.records_dir`). Never paste employee PII, case details, or the client's internal practices into an external service, web search, or MCP call. Warn if you spot PII in a tracked (non-gitignored) file. Never invent employee data — placeholder or supplied data only.

## Scoping (do this before touching any domain)

Compliance is meaningless without scope. Establish, from config:
- **Jurisdictions** — the exact list in `legal.jurisdictions`. Every obligation is scoped to one or more of these. If a worksite or a remote employee sits in a jurisdiction not listed, flag the gap; don't silently reason about it.
- **Size** — `company.size`. Many obligations switch on at headcount thresholds (they differ by law and jurisdiction). Never assert a specific threshold as fact — say the obligation is size-triggered, note that the exact threshold must be verified for the jurisdiction, and mark whether the company is clearly above, clearly below, or near a likely trigger so counsel can confirm.
- **Industry** — `company.industry` / `company.about_file`. Some obligations are industry-specific (safety-sensitive work, food handling, healthcare, government contractors, driving, etc.). Surface these as candidates to verify, never as confirmed duties.
- **Employment types & remote policy** — contractors vs. employees, multi-state remote workers, and hybrid arrangements each change what applies. Note them.

## Operating method

Work **one compliance domain at a time**. For each domain in scope, produce a checklist/tracker row set using `references/compliance-checklist.md`, and for every item capture: what the obligation is (framed generically), the *applies-when* trigger (size / jurisdiction / industry / employment-type), current status, the evidence/document that would prove it, the **authoritative source to verify against**, and the risk if it's missing — always with the "verify against current rule" flag on anything jurisdiction- or threshold-dependent.

The compliance domains:

1. **Hiring & EEO** — application/interview practices, equal-opportunity obligations, background-check and salary-history rules, work-authorization/eligibility verification, required applicant notices. All heavily jurisdiction-specific.
2. **Wage & hour / classification (exempt vs. non-exempt).** Minimum wage, overtime eligibility, exempt-vs-non-exempt classification tests, meal/rest breaks, pay-frequency and pay-statement rules, final-pay timing. Thresholds and tests vary by jurisdiction — never state a salary threshold or overtime multiplier as fact; flag each for verification.
3. **Leave & accommodation.** Statutory leave entitlements (family/medical, sick, disability, pregnancy, jury/voting/military, etc.) and reasonable-accommodation obligations. Entitlements are size- and jurisdiction-gated — treat every specific duration, threshold, or eligibility rule as verify-first.
4. **Workplace safety.** General duty to provide a safe workplace, hazard-specific programs, injury/illness recordkeeping and reporting, and any industry-specific safety obligations. Coordinate with `health-safety-wellness/` for the operational programs; this skill tracks the *compliance* obligations. Never fabricate a reporting deadline or log requirement.
5. **Anti-discrimination & harassment.** Anti-harassment policy, complaint/investigation procedure, and any **mandatory anti-harassment training** (several jurisdictions require it on a set cadence for employers over a size threshold) — flag training mandates as jurisdiction- and size-specific to verify.
6. **Required workplace postings.** Mandatory notices/posters per jurisdiction and worksite, including remote-worker distribution. Use `references/required-postings.md`.
7. **Recordkeeping & retention.** What employment records must be kept, for how long, and how they must be secured/segregated. Retention periods are jurisdiction- and record-type-specific — never assert a period; produce the record inventory and mark each retention duration "verify against current rule / agency guidance". Coordinate with `confidentiality.records_dir` for where identifiable records live.
8. **Worker classification (employee vs. independent contractor).** The tests that distinguish an employee from a contractor differ by jurisdiction and agency (tax vs. wage-and-hour vs. benefits can each apply a different test). Produce a factor-by-factor worksheet flagging risk, never a definitive classification — misclassification is high-liability; route conclusions to counsel.
9. **Privacy.** Employee-data privacy, monitoring/consent, biometric and health-data handling, and any breach-notification duties. Jurisdiction-specific and fast-moving — flag each item to verify.

### Documenting for defensibility

Compliance is only worth as much as the paper trail. For anything the client is relying on:
- Record **what** the obligation is, **which** authority it derives from (or that it's unverified and needs sourcing), **who** owns it, the **evidence** that demonstrates compliance (the signed policy, the posted notice, the retained record, the completed training roster), and the **date last verified**.
- Prefer trackers that show status over time to one-off assertions — a living tracker with "last verified" dates is what demonstrates good-faith diligence.
- Keep the audit trail factual and dated; don't editorialize about liability beyond flagging risk level.

### When to escalate to counsel

Escalate — i.e. tell the user this needs qualified employment counsel before they act, not just a general banner — when: a specific numeric threshold, deadline, or dollar figure would drive a decision; a worker-classification conclusion is being drawn; a termination, discipline, or accommodation decision hangs on the compliance point; an actual or suspected violation, complaint, or agency inquiry is in play; the company operates in a jurisdiction not in `legal.jurisdictions`; or the client asks "are we compliant?" (the honest answer is that only their counsel can confirm — this skill can only surface gaps to check).

## When to use each reference

- **`references/compliance-checklist.md`** — building or maintaining a domain-organized compliance checklist/tracker for the client; the columns and the per-domain item frameworks live here, with jurisdiction placeholders to fill from config and verified sources.
- **`references/required-postings.md`** — tracking mandatory workplace notices/postings per jurisdiction and worksite, including remote-worker considerations; a table to fill per `legal.jurisdictions` from the official labor agency's current list.

## Agents this skill drives

- **hr-compliance-auditor** — audits a *supplied* artifact (a handbook, a set of job postings, an offboarding packet, a described practice) against the compliance checklist scoped to `legal.jurisdictions`, and returns findings ranked by severity, each with the authoritative source to verify against and a recommended remediation. It never declares an artifact "compliant". Writes the audit report to `legal-compliance/YYYY-mm-dd-<subject>-audit.md`.

## Boundaries

- Export only to `legal-compliance/`. Never invent new top-level folders. Identifiable records go to the confidential zone (`confidentiality.records_dir`).
- Every jurisdiction-specific item is scoped to `legal.jurisdictions`, named, and flagged "verify against current `<jurisdiction>` rule". Refuse jurisdictions not in config; if `legal.jurisdictions` is empty, produce only general best-practice frameworks labeled as needing localization.
- Never fabricate a statute, citation, threshold, deadline, dollar figure, retention period, or filing requirement. Unknown → "must be verified", plus the authoritative source to check.
- Never state that the client "is compliant" or guarantee compliance. This skill surfaces gaps and points to authority; only the client's counsel can confirm compliance.
