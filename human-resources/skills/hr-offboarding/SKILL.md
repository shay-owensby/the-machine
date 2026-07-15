---
name: hr-offboarding
description: Manage voluntary and involuntary separations — resignation/retirement, termination, and layoff. Branches on type and legal risk first, coordinates high-risk separations with employee-relations and legal-compliance, then runs the mechanics — exit checklist, final pay and benefits, property return, access revocation, and (voluntary) exit interview. Use when an employee is leaving and the client needs a separation plan, exit checklist, or exit-interview guide.
---

# HR Offboarding & Termination

Handles an employee's departure with dignity, legal care, and operational completeness — whether they resigned, retired, were terminated, or were part of a layoff. This skill owns HR function #13 and exports to `offboarding/` (see the folder map). It never executes a termination in any system; it drafts and confirms.

## Setup gate (run first)

Enforce the config gate before any work, per `${CLAUDE_PLUGIN_ROOT}/skills/hr-config/SKILL.md`: look for `human-resources/config.yaml` at project root, require `version: 1` and `setup.completed: true`. If missing or invalid, STOP and tell the user exactly:
> Human resources isn't configured for this project yet. Run `/setup-human-resources` first.

Then load context: `company.about_file`, `company.soul_file` (voice for departure comms), `company.design_file`, `company.name`, `company.size` (drives mass-layoff notice questions), `company.locations`, `legal.jurisdictions` (governs final-pay timing, benefits continuation, notice rules), `legal.counsel_review`, and `confidentiality.records_dir`. Honor degraded modes (null brand file → neutral, respectful voice + warn once; empty `legal.jurisdictions` → no jurisdiction-specific legal claims, general best-practice only, flagged for localization and counsel).

## Two standing safety rules (apply to everything below)

1. **Drafts, not legal advice.** Separation is the highest-legal-risk work in HR. Exit checklists, final-pay/property/benefits checklists, and separation/termination packets are drafts for review by the client's qualified HR professional and/or employment counsel. **Final-pay timing, benefits-continuation rules, required separation notices, mass-layoff notice obligations, and severance/release enforceability are all jurisdiction-specific** — scope every such claim to `legal.jurisdictions`, name the jurisdiction, and flag "verify with counsel". **Never assert a specific final-pay deadline, a mass-layoff headcount threshold, a notice period, a severance formula, or a benefits-continuation window as fact** — flag it as something counsel must verify against the current rule for the jurisdiction. Never fabricate a statute, threshold, deadline, or dollar figure. When `legal.counsel_review: true`, stamp every separation/termination/layoff packet with "⚠️ Draft — requires review by qualified HR/legal counsel before use".
2. **Confidential by default.** Separations involve sensitive PII and often sensitive circumstances (performance, conduct, health, disputes). Keep case detail, reasons, and identifiable records in-project under the confidential zone (`confidentiality.records_dir`) and coordinate with `employee-relations/` for any investigation/conduct file — never in the shareable `offboarding/` templates. Never paste separation PII or reasons into an external service, web search, or MCP call. Warn if you spot PII in a tracked (non-gitignored) file. Never invent employee data — placeholder or supplied data only.

## Operating method

### Step 1 — Branch on type and risk FIRST (before any mechanics)

Determine the separation type and route accordingly — this decides everything downstream:

- **Voluntary — resignation / retirement.** Lower legal risk. Confirm the resignation is documented (in writing where possible), acknowledge it professionally, set the last day, and proceed to the mechanics. An **exit interview** applies here.
- **Involuntary — termination (individual).** High legal sensitivity. Before mechanics: confirm the decision and its documentation, and **coordinate with `employee-relations/`** (performance/conduct history, prior warnings/PIP, investigation record) and **`legal-compliance/`**. Flag for counsel: at-will vs. notice/cause obligations (jurisdiction- and contract-specific — verify), documentation sufficiency, protected-class/retaliation risk, final-pay timing (jurisdiction-specific — verify), and any **severance & release** offer (counsel drafts/reviews; release enforceability is jurisdiction-specific). When `legal.counsel_review: true`, stamp the packet.
- **Involuntary — layoff / reduction in force.** Highest sensitivity. Everything above, plus: **mass-layoff advance-notice obligations key off headcount and `company.size`** and location — **flag this and route to counsel; do not assert a specific employee-count threshold or notice period as fact.** Selection criteria must be documented and defensible (coordinate `employee-relations/` and `legal-compliance/`), adverse-impact should be reviewed, and severance/release terms are counsel's call. No exit interview in the voluntary sense; handle communications with extra care.

For any involuntary path, make clear the plan is a **draft for counsel and HR to review before any action is taken**, and that nothing is executed in any system by this skill.

### Step 2 — Run the mechanics (from `references/offboarding-checklist.md`)

Once the type/risk branch is set, work the exit checklist across its phases:

3. **Final pay & benefits.** Draft the final-pay items (last paycheck, accrued-but-unused leave payout if owed, expense reimbursements, deductions) and benefits handling. **Final-pay timing and whether accrued leave must be paid out are jurisdiction-specific — flag and verify.** Note benefits-continuation (a COBRA-type continuation-of-coverage option) as **jurisdiction-specific — verify the eligibility, notice, and window**; do not state a specific duration as fact.
4. **Company-property return.** Build the return list (laptop, phone, badge/keys, credit card, documents, other assets) with owners and a return method (in-person or shipping kit for remote).
5. **Access revocation / deprovisioning.** Draft the access-removal list (SSO, email, systems, physical access, third-party accounts) timed to the last-day plan and coordinated with IT/security — least-privilege, and for sensitive involuntary cases, timed appropriately. This skill produces the **request/plan**; a human executes the revocation. Never auto-revoke.
6. **Knowledge transfer.** Plan handover of responsibilities, documentation, key contacts, and in-flight work before the last day.
7. **Exit interview (voluntary only).** For resignations/retirements, run the structured exit interview from `references/exit-interview-guide.md`, and summarize themes into `reports/analytics/` **without exposing individual PII inappropriately** (aggregate/anonymize per the guide). Do not run a voluntary-style exit interview for a termination.

### Step 3 — Assemble & route outputs

Write the exit checklist, final-pay/property/benefits checklist, and (voluntary) exit-interview guide/summary into `offboarding/` (per departure, use `offboarding/<employee-slug>/`). Keep reasons and identifiable case detail in the confidential zone / `employee-relations/`, not in shareable templates. Stamp separation/termination/layoff packets with the counsel-review banner when `legal.counsel_review: true`.

**Dignity throughout:** even involuntary separations should be handled respectfully, privately, and consistently — it protects the departing person, the remaining team, and the company.

## When to use each reference

- **`references/offboarding-checklist.md`** — running the exit mechanics (pre-departure / last day / post-departure): final pay, benefits continuation, property return, access deprovisioning, knowledge transfer, with jurisdiction-flagged items.
- **`references/exit-interview-guide.md`** — conducting a voluntary-departure exit interview and rolling themes up into `reports/analytics/` without exposing individual PII.

## Boundaries

- Export only to `offboarding/` (per-departure subfolder `offboarding/<employee-slug>/` optional). High-risk separations coordinate with `employee-relations/` and `legal-compliance/`; exit-interview theme summaries go to `reports/analytics/`; confidential reasons/records stay in the confidential zone. Never invent new top-level folders.
- **Never auto-executes a termination, final-pay run, or access revocation in any system — drafts and confirms only.** Legal claims (final-pay timing, notice thresholds, benefits-continuation, severance/release) are jurisdiction-scoped and flagged for counsel verification, never asserted as fact. Separation PII and reasons stay in-project.
