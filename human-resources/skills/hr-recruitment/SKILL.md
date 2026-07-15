---
name: hr-recruitment
description: Run the full recruiting lifecycle for a role — intake and criteria definition, an inclusive bias-free job description, a posting/sourcing plan, structured resume screening against a weighted rubric, interview coordination, reference checks, and offer hand-off. Use when the client wants to open a search, write a JD, screen a candidate batch, or stand up a hiring process for a specific role.
---

# HR Recruitment & Staffing

Turns a hiring need into a defensible, inclusive, candidate-friendly search: define the role, attract a diverse pool, screen against consistent evidence-based criteria, interview structurally, and hand a clean offer to compensation. This skill owns HR function #1 and exports to `recruitment/` (see the folder map).

## Setup gate (run first)

Enforce the config gate before any work, per `${CLAUDE_PLUGIN_ROOT}/skills/hr-config/SKILL.md`: look for `human-resources/config.yaml` at project root, require `version: 1` and `setup.completed: true`. If missing or invalid, STOP and tell the user exactly:
> Human resources isn't configured for this project yet. Run `/setup-human-resources` first.

Then load context: `company.about_file` (what the company does), `company.soul_file` (voice for candidate-facing copy), `company.design_file` (branded document look), `company.size`, `company.locations`, `company.remote_policy`, and `legal.jurisdictions`. Honor degraded modes (null brand file → neutral voice + warn once; empty `legal.jurisdictions` → no jurisdiction-specific claims, general best-practice only).

## Two standing safety rules (apply to everything below)

1. **Drafts, not legal advice.** JDs, screening notes, interview kits, and offers are drafts for review by the client's qualified HR professional and/or employment counsel. Any job-posting or screening rule that depends on employment law (pay-transparency, salary-history bans, ban-the-box, adverse-impact/disparate-impact standards, work-authorization checks) is **jurisdiction-specific** — scope it to `legal.jurisdictions`, say which jurisdiction it applies to, and flag it "verify with counsel". When `legal.counsel_review: true`, stamp the offer letter and any formal legal doc with "⚠️ Draft — requires review by qualified HR/legal counsel before use". Never fabricate a statute, threshold, deadline, or dollar figure.
2. **Confidential by default.** Resumes and candidate PII are sensitive. Keep them in-project under `recruitment/`; never paste candidate names, contact details, or resume content into an external service, web search, or MCP call. Warn if you spot PII in a tracked (non-gitignored) file. Never invent candidates or resume content — placeholder or supplied data only.

## Operating method

1. **Intake.** Capture the role brief: title, level/seniority, team and reporting line, employment type (from `company.employment_types`), location and on-site/hybrid/remote expectation, target start date, headcount, and the reason for the req (backfill vs. new). Split criteria into **must-have** (true disqualifiers) and **nice-to-have** — keep must-haves few and genuinely essential; every must-have becomes a screen and an interview signal, so an inflated list narrows the pool and imports bias. Get the **comp band** from the hr-compensation-benefits skill / the `compensation-benefits/` folder (never invent numbers); the band drives both the JD range and later the offer. Note that the role's location resolves to a jurisdiction in `legal.jurisdictions` — flag that jurisdiction now, because it governs pay-range-in-posting and salary-history rules downstream.
2. **Job description.** Draft an inclusive, bias-free JD from `references/job-description-template.md`, grounded in `company.about_file` for the company summary and `company.soul_file` for voice. Run the inclusive-language checklist. Insert the comp range if the resolved jurisdiction requires (or the client chooses) pay transparency — flag it as jurisdiction-specific to verify. Include the EEO statement placeholder. Get hiring-manager sign-off before posting.
3. **Posting & channel plan.** Recommend where to post: general boards, niche/industry boards, the careers page, employee referrals, and diversity-focused channels to widen the pool. Set a realistic timeline against the target start date. Note application mechanics (ATS, required fields) and keep the application short.
4. **Sourcing plan.** Beyond passive posting: outline proactive sourcing (referrals, communities, targeted outreach), an outreach message template in brand voice, and a plan to reach underrepresented candidates. Do not scrape or store PII externally.
5. **Structured resume screening.** Screen the supplied batch against `references/screening-rubric.md`: apply the must-have gate first, then score weighted dimensions with evidence quoted from each resume, apply the bias-avoidance rules, and produce a ranked shortlist with rationale. Flag any screening criterion that is legally risky (proxies for protected class, salary-history dependence, unexplained gaps used against a candidate) for review.
6. **Interview coordination.** Hand off to the **hr-interview-designer** agent to build the structured interview kit (competencies, question bank, anchored scorecards, panel/stage plan, off-limits question areas). Schedule the stages via the `scheduling/` folder (interview scheduling lives there per the folder map), coordinating panelists and candidate availability. Give every interviewer the scorecard and the off-limits list before they interview.
7. **Reference checks.** Provide a consistent, job-related reference-check question set run the same way for finalists, with candidate consent; keep notes in-project. Flag that permissible reference/background inquiries vary by jurisdiction — verify with counsel.
8. **Offer.** Pull the offer number from the hr-compensation-benefits skill / `compensation-benefits/` folder (never invent it). Draft the offer letter in `company.soul_file` voice; when `legal.counsel_review: true`, stamp the counsel-review banner. Note that offer-letter contents, at-will language, and contingencies are jurisdiction-specific — flag for counsel.

**Candidate experience** runs through all of it: clear expectations, prompt communication, respectful rejections, and a short, accessible process. **EEO / inclusion**: consistent criteria applied to every candidate, structured evaluation over gut feel, inclusive language, and a widened pool — these both reduce legal risk and improve hiring.

## When to use each reference

- **`references/job-description-template.md`** — writing or revising any job description or posting; also holds the inclusive-language do/don't checklist and the pay-range-in-posting note.
- **`references/screening-rubric.md`** — screening a resume batch, or setting up the scoring framework and bias-avoidance rules before candidates arrive.

## Agents this skill drives

- **hr-recruiter** — drafts the JD + sourcing/posting plan, and/or screens a resume batch into a ranked shortlist. Writes drafts into `recruitment/` (or the per-search subfolder).
- **hr-interview-designer** — builds the structured interview kit for the role. Writes into `recruitment/`.

## Boundaries

- Export only to `recruitment/` (per-search subfolder `recruitment/<role-slug>/` optional). Interview scheduling coordinates with `scheduling/`. Never invent new top-level folders.
- Comp numbers come from compensation, not from here. Legal claims are jurisdiction-scoped and flagged for verification. Candidate PII stays in-project.
