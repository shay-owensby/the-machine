---
description: Onboard a new hire — from an accepted offer to a productive employee. Generates the onboarding checklist, 30/60/90 plan, welcome packet, and access/equipment request list, pulling the handbook acknowledgment from policies. Optional argument pre-seeds the hire's name/role.
---

# Onboard a New Hire

You are coordinating the onboarding of a new employee for this client. Produce a complete, confidential-aware onboarding package as **drafts** — you never provision real accounts, credentials, or system access, and you never enter data into an HRIS automatically. Follow the method in `${CLAUDE_PLUGIN_ROOT}/skills/hr-onboarding/SKILL.md`.

## 1. Setup gate

Look for `human-resources/config.yaml` at the project root; require `version: 1` and `setup.completed: true` (protocol: `${CLAUDE_PLUGIN_ROOT}/skills/hr-config/SKILL.md`). Missing/invalid → stop: "Human resources isn't configured for this project yet. Run `/setup-human-resources` first."

## 2. Load context

- `human-resources/config.yaml` (all of it)
- Brand files: `company.about_file` (company/culture intro), `company.soul_file` (welcome/orientation voice), `company.design_file` (document look) — null → note degraded mode, warn once
- `company.name`, `company.size`, `company.locations`, `company.remote_policy`, `company.employment_types`, `legal.jurisdictions`, `legal.counsel_review`, `confidentiality.records_dir`, `defaults.approver`
- The employee handbook and acknowledgment form in `policies/` (for the day-1 handbook acknowledgment) — if none exists yet, note it and suggest `/hr-handbook`

## 3. Intake

Gather (use AskUserQuestion where options are enumerable; `$ARGUMENTS` pre-seeds name/role and you confirm the rest):
- **Name** (or placeholder if not yet disclosed)
- **Role / title** and **level**
- **Start date**
- **Manager** and **team**
- **Work location** — resolve it to a jurisdiction in `legal.jurisdictions`; if it resolves outside that list, flag it and produce general best-practice only
- **Employment type** (from `company.employment_types`) and on-site / hybrid / remote arrangement

State the resolved jurisdiction and employment type back to the user — they determine which new-hire paperwork applies.

## 4. Generate the onboarding package

Using `references/onboarding-checklist.md` and `references/30-60-90-template.md`, produce:

1. **Onboarding checklist** — the phase-by-phase checklist (pre-start / day 1 / week 1 / first 90 days) with owners, tailored to the role, employment type, and work arrangement. Mark every required-form row as *jurisdiction-specific, verify against `legal.jurisdictions`* — never assert a specific form name/ID/deadline as fact for an unconfirmed jurisdiction, and never fabricate one.
2. **30/60/90 plan** — from the template, adapted to role and level, with learning goals, milestones, and scheduled check-ins.
3. **Welcome packet** — a warm pre-start welcome note + day-1 logistics in `company.soul_file` voice, plus the company/culture intro grounded in `company.about_file`.
4. **Access / equipment request list** — hardware, accounts, and least-privilege system access the role needs, formatted as a request for IT/access owners to action. Do **not** create accounts or credentials.
5. **Handbook acknowledgment** — pull the acknowledgment form from `policies/` so day-1 orientation matches the current handbook version. When `legal.counsel_review: true`, stamp any formal acknowledgment/onboarding agreement with "⚠️ Draft — requires review by qualified HR/legal counsel before use".

## 5. Write outputs (confidential-aware)

- Write shareable deliverables (checklist, 30/60/90 plan, welcome packet, access request list) to `onboarding/<employee-slug>/`.
- Any completed form or artifact carrying PII (national ID/SSN, work-authorization docs, bank details, DOB, home address) goes to the confidential records zone (`confidentiality.records_dir` → `reports/employee-reports/`), **never** into the shareable `onboarding/` templates.
- If you detect PII sitting in a tracked (non-gitignored) file, warn and offer to move or redact it. Never paste new-hire PII into an external service, web search, or MCP call.

## 6. Closeout

Summarize what was produced and where it lives, the resolved jurisdiction and which paperwork rows need counsel/HR verification, any coordination handoffs (handbook acknowledgment ↔ `policies/`, role training ↔ `training-development/`, orientation scheduling ↔ `scheduling/`), and the reminder: **these are drafts for review — HR/counsel verify jurisdiction-specific forms, a human provisions access, and PII stays in-project.**
