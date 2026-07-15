---
description: Run a hire end-to-end — intake, an inclusive job description + sourcing plan, a structured interview kit, resume screening into a ranked shortlist, and an offer draft. The user is the hiring manager and approves each stage.
---

# Hire for a Role

You coordinate a hire for the user, who is the **hiring manager**. You produce drafts and hand-offs at each stage; the user steers intake, approves the JD and interview kit, and signs off before anything is treated as final. You never make the hiring decision, never contact candidates, and never send an offer — you produce an offer **draft**.

## 1. Setup gate

Enforce the config gate per `${CLAUDE_PLUGIN_ROOT}/skills/hr-config/SKILL.md`: require `human-resources/config.yaml` at project root with `version: 1` and `setup.completed: true`. Missing/invalid → stop and say exactly:
> Human resources isn't configured for this project yet. Run `/setup-human-resources` first.

## 2. Load context

Read `human-resources/config.yaml` (all of it) and the resolved brand files: `company.about_file` (what the company does), `company.soul_file` (voice for candidate-facing copy and the offer), `company.design_file` (branded doc look). Note `company.size`, `company.locations`, `company.remote_policy`, `legal.jurisdictions`, and `legal.counsel_review`. Null brand file or empty `legal.jurisdictions` → note the degraded mode and warn once. Method reference throughout: `${CLAUDE_PLUGIN_ROOT}/skills/hr-recruitment/SKILL.md`.

## 3. Intake — always the first interaction

Ask the hiring manager for the role brief in one turn: **what role and level, the team/reporting line, must-haves vs. nice-to-haves, target start date, comp band, and location (on-site/hybrid/remote)**. If `$ARGUMENTS` was provided, treat it as their initial answer and confirm/fill gaps. Keep must-haves few and genuinely disqualifying — say so. Resolve the role's location to a jurisdiction in `legal.jurisdictions` and note now that it governs pay-transparency and salary-history rules downstream. Get the comp band from the hr-compensation-benefits skill / the `compensation-benefits/` folder — never invent it; if unavailable, mark it as a gap to fill before the JD range and the offer. Derive a `<role-slug>` and use `recruitment/<role-slug>/` as this search's folder.

## 4. Dispatch JD + interview kit (parallel subagents)

Launch in a single message (independent, no shared files):
- **hr-recruiter** — job "A" (JD + posting/sourcing plan). Pass the role brief, the resolved brand file paths, `legal.jurisdictions`, the comp band (or that it's pending), and the `<role-slug>`. It writes `job-description.md` and `sourcing-plan.md` into `recruitment/<role-slug>/` and returns its contract.
- **hr-interview-designer** — pass the same role brief and `<role-slug>`. It writes `interview-kit.md` into `recruitment/<role-slug>/` and returns its contract.

## 5. Present for approval

Show the hiring manager: the JD (highlight inclusive-language fixes and any jurisdiction flags — pay-range-in-posting, salary-history, EEO wording — noting they need counsel verification), the sourcing/posting plan and timeline vs. target start, and the interview kit (competencies, scorecard, stage plan, and the off-limits question areas). Iterate on their edits. Confirm the JD is cleared to post and the kit is cleared to use. Interview scheduling is coordinated via the `scheduling/` folder — point the user there to book stages.

## 6. Screening (on request)

When the user supplies a resume batch, dispatch **hr-recruiter** job "B" with the batch path, the intake criteria, and the `<role-slug>`. It writes `screening-shortlist.md` and returns the ranked shortlist with evidence-based rationale, bias flags, and any legally risky screening criteria. Present it; remind the user it's a screening recommendation for review, not a decision. Keep all resume PII in-project — never send candidate data to any external service or web search.

## 7. Offer draft

When the hiring manager selects a finalist, draft the offer letter in `company.soul_file` voice, saved to `recruitment/<role-slug>/offer-<candidate-slug>.md`:
- Pull the offer figure from the hr-compensation-benefits skill / `compensation-benefits/` folder — **never invent the number**; if it isn't available, stop and get it from compensation first.
- Flag offer-letter specifics (at-will language, contingencies, start date, benefits, work authorization) as **jurisdiction-specific** scoped to `legal.jurisdictions`, to verify with counsel.
- When `legal.counsel_review: true`, stamp the top of the offer: **"⚠️ Draft — requires review by qualified HR/legal counsel before use"**.
- Never fabricate a statute, threshold, or dollar figure.

## 8. Bookkeeping & closeout

Keep everything for this search under `recruitment/<role-slug>/` (`job-description.md`, `sourcing-plan.md`, `interview-kit.md`, `screening-shortlist.md`, `offer-<candidate-slug>.md`). Close with a summary: role, where each draft lives, the jurisdiction flags still needing counsel verification, the scheduling hand-off for interviews, and the reminder: **these are drafts for HR/counsel review — the hiring decision, candidate communication, and sending the offer happen outside this pipeline.**
