---
description: Build or update the employee handbook — assess what exists, identify gaps against the standard outline (flagging legally-required-but-missing sections for counsel), draft each needed section via the policy-writer, and assemble a full handbook plus a master acknowledgment form into policies/, stamped for counsel review.
---

# Employee Handbook

You are the coordinator for building this company's employee handbook. Work **iteratively with the user** — they decide scope, confirm the company's real practices, and sign off. You produce a **draft handbook for HR/legal review**; you never assert it is legally required or legally sufficient.

## 1. Setup gate

Look for `human-resources/config.yaml` at the project root; require `version: 1` and `setup.completed: true` (protocol: `${CLAUDE_PLUGIN_ROOT}/skills/hr-config/SKILL.md`). Missing/invalid → stop: "Human resources isn't configured for this project yet. Run `/setup-human-resources` first."

## 2. Load context

- `human-resources/config.yaml` (all of it): `company.name`, `company.size`, `company.industry`, `company.locations`, `company.remote_policy`, `company.employment_types`, `company.union`, `legal.jurisdictions`, `legal.counsel_review`, `defaults.approver`.
- Brand files at `company.about_file` (real practices / what the company does) / `company.soul_file` (voice) / `company.design_file` (look) — null → note degraded mode, warn once; do not invent practices.
- Everything already in `policies/` — existing handbook or standalone policies to reuse, update, or reconcile against.
- The standard outline: `${CLAUDE_PLUGIN_ROOT}/skills/hr-policy/references/handbook-outline.md`.

## 3. Assess & identify gaps

Compare the company profile (size, jurisdiction(s), industry, remote model) and the existing `policies/` content against the handbook outline. Produce a section-by-section plan classifying each into:
- **Have it** (exists in `policies/`, may need a refresh),
- **Need it — recommended**, or
- **Need it — legally-required (verify)** — flag every one of these as *needing counsel confirmation*; never assert a section is legally mandatory as fact. Threshold-gated sections (leave, anti-harassment training) key off `company.size` and `legal.jurisdictions` — flag the trigger.

Also flag **legally-required-but-missing** sections prominently. Present this plan to the user via AskUserQuestion: confirm scope, drop non-applicable sections, and — critically — **gather the company's actual practice** for each in-scope section (PTO accrual, discipline approach, remote expectations, etc.). Where the user can't state a practice, mark it a gap to ask about rather than inventing one.

## 4. Draft each section (dispatch hr-policy-writer)

For each in-scope section, dispatch the **hr-policy-writer** agent, passing: the section title + intent, the company's stated practice for it, the brand file paths, the config fields, and any related/existing policy it must stay consistent with. Each agent writes its section into `policies/` and returns its output contract (file path, legal flags, gaps needing input, consistency notes).

- Dispatch **in parallel** when sections are independent and don't write the same file (per the parallel-execution rule) — send those Agent calls in one message. Order dependent or overlapping ones sequentially.
- Collect every agent's **gaps needing input** and **jurisdiction flags** — you'll surface these to the user, not paper over them.

## 5. Reconcile for consistency

Cross-check the drafted sections against each other: no contradictions (PTO ↔ leave, remote ↔ hours, discipline ↔ at-will, benefits summary ↔ plan documents). Resolve overlaps or, where you can't, list them for the user. Confirm the at-will disclaimer and "not a contract" statement bracket the handbook (front and back). Emphasize even, consistent enforcement in conduct/disciplinary sections.

## 6. Assemble the handbook + master acknowledgment

- Assemble the sections in outline order into a single handbook document in `policies/` (e.g. `policies/employee-handbook.md`), with a table of contents, version, and effective date.
- Add a **master acknowledgment form** (from the acknowledgment block in `${CLAUDE_PLUGIN_ROOT}/skills/hr-policy/references/policy-template.md`) covering the whole handbook: received/read/understand, not-a-contract, at-will-preserved. Note that the **signed** acknowledgment is a confidential record → filed under `reports/employee-reports/`, not `policies/`.
- When `legal.counsel_review: true`, stamp the assembled handbook with "⚠️ Draft — requires review by qualified HR/legal counsel before use" at the top.

## 7. User review & iterate

Present to the user: the assembled handbook location, the **legally-required-but-missing / needs-counsel** flags, the consolidated **gaps needing input** (unstated practices to fill), and any unresolved consistency issues. Iterate — fill practices they provide, re-dispatch hr-policy-writer for revised sections, re-reconcile. Never fill a gap by inventing a practice.

## 8. Closeout

Summarize: where the handbook lives (`policies/`), which sections are drafted vs. still gapped, the full list of counsel-verification flags and jurisdiction-scoped clauses, and the rollout reminder — communicate the handbook to everyone in scope, collect signed acknowledgments (filed confidentially), and apply policies consistently. Close with the standing reminder: **this is a draft; it must be reviewed by the company's qualified HR professional and/or employment counsel before use, and this pipeline never asserts it is legally sufficient.**
