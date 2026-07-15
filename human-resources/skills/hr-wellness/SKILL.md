---
name: hr-wellness
description: Build workplace health, safety, and wellness programs — physical safety (hazard assessment, safety programs and training, incident reporting and recordkeeping), emergency preparedness, occupational-safety compliance, leave and reasonable-accommodation and return-to-work processes, and mental-health/wellness (EAP, wellness initiatives, stress management) — as frameworks and drafts scoped to the client's jurisdictions, with safety/leave/medical rules flagged for verification and medical information kept confidential and separate. Use when the client wants a safety program, hazard assessment, incident-reporting process, emergency plan, an accommodation/return-to-work process, or an EAP/wellness-program design.
---

# HR Health, Safety & Wellness

Helps a client protect the physical and mental health of its people: a working safety program, a way to prepare for emergencies, a fair and confidential process for leave and accommodation, and wellness supports that people actually use. This skill owns HR function #9 and exports to `health-safety-wellness/` (see the folder map). It builds **frameworks and drafts**, not fabricated law — occupational-safety, leave, and accommodation rules are all jurisdiction-specific and go to the client's counsel and safety professional before use.

## Setup gate (run first)

Enforce the config gate before any work, per `${CLAUDE_PLUGIN_ROOT}/skills/hr-config/SKILL.md`: look for `human-resources/config.yaml` at project root, require `version: 1` and `setup.completed: true`. If missing or invalid, STOP and tell the user exactly:
> Human resources isn't configured for this project yet. Run `/setup-human-resources` first.

Then load context: `company.about_file` (what the company does — its real hazards, worksites, and physical operations drive the whole program), `company.industry` (safety obligations are heavily industry-specific — manufacturing, food handling, healthcare, driving, construction each carry their own), `company.size` (some safety/leave duties switch on at headcount thresholds), `company.locations` and `legal.jurisdictions` (the authoritative scope for every safety/leave claim), `company.remote_policy` (remote/hybrid workers change ergonomic and worksite-safety scope), `company.soul_file` (voice for employee-facing wellness and safety communications), `company.design_file` (branded document look), and `legal.counsel_review`. Honor degraded modes: null `about_file` → don't invent hazards, equipment, or operations the company hasn't stated; empty `legal.jurisdictions` → make **no** jurisdiction-specific safety/leave claim; produce general best-practice frameworks labeled "must be localized and verified with counsel / a qualified safety professional".

## Two standing safety rules (paramount — apply to everything below)

1. **Drafts, not legal advice — and this domain is legally sensitive.** Safety programs, incident-recordkeeping requirements, emergency plans, leave entitlements, and accommodation obligations are **jurisdiction-specific** (occupational-safety / OSHA-type regimes, ADA-type accommodation law, family/medical/disability leave law). So:
   - **Scope every jurisdiction- or threshold-dependent item to `legal.jurisdictions`**, name the jurisdiction ("Under `US-Federal` OSHA-type rules…"), and flag it: **"verify against current `<jurisdiction>` rule / a qualified safety professional"**.
   - **Never fabricate** a safety standard, a permissible-exposure limit, an incident-reporting deadline or log form, a leave duration or eligibility threshold, or an accommodation obligation. Unknown → say it **must be verified** and name the authority (the jurisdiction's occupational-safety agency, labor/employment agency, or counsel). A plausible-sounding but invented number is worse than an explicit "verify this".
   - **Coordinate compliance with `legal-compliance/`** — the hr-compliance skill tracks the *compliance obligations* (which safety standards, postings, recordkeeping duties, and leave/accommodation duties apply); this skill builds the *operational programs*. Don't duplicate or contradict it.
   - **Stamp formal safety, leave, and accommodation policies** with the visible banner **"⚠️ Draft — requires review by qualified HR/legal counsel and a qualified safety professional before use"** (always when `legal.counsel_review: true`; recommended regardless in this domain).
2. **Confidential by default — medical information is the most sensitive PII.** Any leave, accommodation, injury, or health information is protected and must be kept **confidential and physically/logically separate from the general personnel file** (see the hr-records skill — this is a legal requirement in many jurisdictions, not a nicety). Concretely:
   - Keep accommodation case notes, medical documentation, injury details, and return-to-work medical information in the **confidential records zone** (`confidentiality.records_dir`, i.e. `reports/employee-reports/`), **never** in the shareable `health-safety-wellness/` program folder.
   - In the interactive accommodation process, focus on **functional limitations and job functions**, not diagnoses; collect the minimum medical information necessary and share it only on a strict need-to-know basis.
   - Never paste an employee's health/medical/injury details into an external service, web search, or MCP call. Never invent employee health data — placeholder or supplied data only. Warn if you spot medical PII sitting in a tracked (non-gitignored) or shareable file.

## Operating method

Work the domain the client needs; each points to a section of the reference.

1. **Physical workplace safety.** Build the safety program with `references/safety-program-outline.md`:
   - **Roles & responsibilities** — who owns safety (management commitment is the foundation), the safety committee/coordinator, and every employee's part.
   - **Hazard assessment** — walk the actual worksites and tasks (grounded in `about_file` and what the user states), identify hazards, rank by likelihood × severity, and assign controls using the hierarchy of controls (eliminate → substitute → engineering → administrative → PPE, in that order — PPE is the last line, not the first).
   - **Safe-work procedures & training** — written procedures for hazardous tasks, and a training plan (new-hire safety orientation, task-specific training, refreshers) with a completion roster. Coordinate training delivery with `training-development/`.
   - **PPE** — what's required for which task, provision, fit, and use — scoped to the real hazards, never assumed.
   - **Incident reporting & investigation** — a clear, blame-reducing path for employees to report injuries, illnesses, and near-misses; prompt investigation to root cause; corrective action tracked to closure. Injury/illness **recordkeeping and reporting requirements (forms, thresholds, deadlines) are jurisdiction-specific — flag and verify**; never assert a specific log form or reporting deadline.
   - **Review cadence** — the program is living: review on a set cadence and after any significant incident or change in operations.
2. **Emergency preparedness.** Plan for the emergencies the site could realistically face (fire, medical, severe weather, hazardous release, security, utility loss — scope to the real operations and locations). Cover evacuation routes and assembly points, roles and a chain of communication, first-aid/medical response, drills and their cadence, and post-incident recovery. Keep it specific to the actual worksites.
3. **Occupational-safety compliance (cross-ref `legal-compliance/`).** This skill builds the program; the *obligations* — which safety standards apply, required postings, mandatory recordkeeping and reporting, industry-specific duties — are tracked in `legal-compliance/` by the hr-compliance skill and its checklist. Point the user there for the compliance layer; never assert a safety standard or reporting duty as fact here.
4. **Leave & reasonable accommodation & return-to-work (ADA-type interactive process — flagged; medical info confidential).** Run these as a **documented, good-faith interactive process**, not a yes/no decision, using the checklist in the reference:
   - Recognize a request (it need not use magic words), engage in a timely back-and-forth, focus on **functional limitations vs. essential job functions**, explore reasonable accommodations, and document each step and decision.
   - Leave entitlements and accommodation obligations are **size- and jurisdiction-gated** — treat every specific duration, eligibility threshold, or obligation as verify-first, scoped to `legal.jurisdictions`, and route decisions to counsel. Coordinate the leave-compliance layer with `legal-compliance/`.
   - **Return-to-work** — a structured, medically-appropriate return (including modified/light duty where offered), coordinated with any leave, again documenting the process.
   - **Keep all medical documentation in the confidential records zone, separate from the personnel file** (safety rule 2). The accommodation *process record* can note that an accommodation was granted and its operational terms; the underlying medical detail stays confidential.
5. **Mental-health & wellness programs.** Design supports people will actually use — an **EAP** (confidential counseling/referral; make clear its confidentiality so people trust it), wellness initiatives (physical, financial, social, and mental-health), stress-management and workload/burnout supports, and manager awareness of how to respond and refer without prying into diagnoses. Use the EAP/wellness section of the reference. Ground offerings in what the company can actually provide; don't promise benefits it hasn't decided to fund. Voice employee-facing wellness comms per `company.soul_file`.

## When to use the reference

- **`references/safety-program-outline.md`** — building any of: a **workplace safety program** (roles, hazard assessment, safe-work procedures, training, PPE, incident reporting & investigation, an incident-log structure, review cadence); an **EAP/wellness-program outline**; or a **return-to-work / reasonable-accommodation interactive-process checklist**. Every jurisdiction-dependent item carries a verify flag, and the medical-confidentiality notes travel with it.

## Boundaries

- Export **only** to `health-safety-wellness/`. Never invent new top-level folders. Any medical/health/injury/accommodation PII goes to the confidential records zone (`confidentiality.records_dir`, i.e. `reports/employee-reports/`) — never into the shareable program folder.
- Every jurisdiction- or threshold-dependent safety/leave/accommodation item is scoped to `legal.jurisdictions`, named, and flagged to verify with counsel / a qualified safety professional. If `legal.jurisdictions` is empty, produce only general best-practice frameworks labeled as needing localization.
- Never fabricate a safety standard, exposure limit, incident-reporting deadline or form, leave duration/threshold, or accommodation obligation. Unknown → "must be verified", plus the authority to check. The *compliance* layer lives in `legal-compliance/`.
- Everything is a **draft for review** by the client's qualified HR professional, employment counsel, and (for safety) a qualified safety professional — never definitive legal or safety advice or a guarantee of compliance. Never invent employee health data.
