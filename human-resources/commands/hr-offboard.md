---
description: Offboard a departing employee — voluntary (resignation/retirement) or involuntary (termination/layoff). Runs a risk/eligibility check first, routing involuntary cases to counsel review and employee-relations coordination, then generates the exit checklist, final-pay/property/benefits checklist, and (voluntary) exit-interview guide. Never executes a termination — drafts and confirms only.
---

# Offboard a Departing Employee

You are coordinating an employee separation for this client. This is the highest-legal-risk HR work — proceed carefully. You produce **drafts for HR/counsel review** and you **never execute a termination, final-pay run, or access revocation in any system**. Follow the method in `${CLAUDE_PLUGIN_ROOT}/skills/hr-offboarding/SKILL.md`.

## 1. Setup gate

Look for `human-resources/config.yaml` at the project root; require `version: 1` and `setup.completed: true` (protocol: `${CLAUDE_PLUGIN_ROOT}/skills/hr-config/SKILL.md`). Missing/invalid → stop: "Human resources isn't configured for this project yet. Run `/setup-human-resources` first."

## 2. Load context

- `human-resources/config.yaml` (all of it)
- Brand files: `company.soul_file` (voice for departure comms), `company.about_file`, `company.design_file` — null → note degraded mode, warn once
- `company.name`, `company.size` (drives mass-layoff notice questions), `company.locations`, `legal.jurisdictions`, `legal.counsel_review`, `confidentiality.records_dir`
- If the case is involuntary, the relevant `employee-relations/` history and `legal-compliance/` context

## 3. Intake

Gather (use AskUserQuestion where options are enumerable):
- **Employee** (name or placeholder)
- **Separation type** — voluntary (resignation/retirement) · involuntary (termination) · layoff/RIF
- **Last working day**
- **Reason** (keep detail confidential; enough to route correctly)
- **Work location** — resolve to a jurisdiction in `legal.jurisdictions`; if outside that list, flag and produce general best-practice only

## 4. Risk / eligibility check FIRST (before mechanics)

Branch on type before generating any checklist:
- **Voluntary** → confirm the resignation is documented; an exit interview applies. Lower risk; proceed to mechanics.
- **Involuntary (termination)** → route to **counsel review** and **coordinate with `employee-relations/`** (performance/conduct/PIP history, documentation) and **`legal-compliance/`**. Flag for counsel: at-will vs. notice/cause, documentation sufficiency, protected-class/retaliation risk, final-pay timing, and any severance & release. Stamp the packet when `legal.counsel_review: true`.
- **Layoff / RIF** → all of the above, plus flag that **mass-layoff advance-notice obligations key off headcount/`company.size` and location** — route to counsel and **do not assert a specific employee-count threshold or notice period as fact**; document selection criteria and note adverse-impact review.

State the risk routing back to the user and confirm before proceeding. Make explicit that everything produced is a draft to review before any action is taken.

## 5. Generate the offboarding package

Using `references/offboarding-checklist.md` (and `references/exit-interview-guide.md` for voluntary):

1. **Exit checklist** — phase-by-phase (type/risk gate → pre-departure → last day → post-departure) with owners, tailored to the separation type.
2. **Final-pay / property / benefits checklist** — final pay, accrued-leave payout, deductions, property return, and benefits continuation (COBRA-type). Flag every jurisdiction-specific item (final-pay timing, accrued-leave payout, continuation eligibility/notice/window) as *verify with counsel* — **never state a specific deadline, threshold, or coverage duration as fact**, and never fabricate one.
3. **Access-revocation / deprovisioning plan** — the request/plan for IT/security to execute (never auto-revoke).
4. **Exit-interview guide** (voluntary only) — from the guide reference; do not run a voluntary-style exit interview for a termination/layoff.

When `legal.counsel_review: true`, stamp every separation/termination/layoff packet with "⚠️ Draft — requires review by qualified HR/legal counsel before use".

## 6. Write outputs (confidential-aware)

- Write shareable deliverables (exit checklist, final-pay/property/benefits checklist, exit-interview guide) to `offboarding/<employee-slug>/`.
- Keep the reason, case detail, and any identifiable records in the confidential zone (`confidentiality.records_dir`) / `employee-relations/` — **never** in shareable templates.
- Exit-interview theme summaries go to `reports/analytics/`, aggregated and anonymized (no individual PII).
- If you detect PII or sensitive reasons in a tracked (non-gitignored) file, warn and offer to move or redact. Never paste separation PII/reasons into an external service, web search, or MCP call.

## 7. Closeout

Summarize what was produced and where it lives, the risk routing (and for involuntary/layoff, that it awaits counsel/employee-relations review), which items need jurisdiction verification, and the reminder: **nothing is executed in any system by this command — a human, after HR/counsel review, runs final pay, revokes access, and updates the HRIS. These are drafts and confirmations only.**
