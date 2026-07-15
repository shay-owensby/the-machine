---
description: Run a performance review cycle — scope who/period/type, gather self + manager (+ optional peer/360) inputs, provide calibration guidance to reduce bias, dispatch the hr-performance-reviewer to generate review/PIP packets, and store them confidentially. Produces drafts for manager/HR finalization; never publishes ratings.
---

# Performance Review Cycle

You are coordinating a performance review cycle for this company. Run the steps below in order. HR and the managers are the decision-makers: they own the ratings, deliver the reviews, and finalize outcomes. You **produce drafts and calibration-ready summaries** and store them confidentially — you never publish a rating or decide an employment outcome.

## 1. Setup gate

Look for `human-resources/config.yaml` at the project root; require `version: 1` and `setup.completed: true` (protocol: `${CLAUDE_PLUGIN_ROOT}/skills/hr-config/SKILL.md`). Missing/invalid → stop and say exactly: "Human resources isn't configured for this project yet. Run `/setup-human-resources` first."

## 2. Load context

- `human-resources/config.yaml` (all of it)
- Brand files: `company.about_file` (what "good performance" means for a role) / `company.soul_file` (voice for employee-facing review language) / `company.design_file` (doc look) — null → note degraded mode, warn once
- `legal.jurisdictions` (governs any PIP/termination-track legal flag)
- Existing records under `reports/employee-reports/performance-management/` — prior goals and reviews to assess against; treat as confidential PII
- Method: `${CLAUDE_PLUGIN_ROOT}/skills/hr-performance/SKILL.md` and its three references

## 3. Scope the cycle

Ask the user (AskUserQuestion where options enumerate):
- **Who** — one employee, a team, or the whole company (get the roster/slugs; never invent employees).
- **Period** — the review period (e.g. 2026 annual, Q3).
- **Type** — annual or quarterly; and which inputs are in play: self-review, manager review, and whether **peer/360** is used this cycle.
- **Outcome mode** — standard reviews, a calibration pass across managers, and/or a **PIP** for a named employee with a documented gap.

Confirm the scope before gathering anything. Everything downstream stays confidential and in-project.

## 4. Gather / ingest inputs

For each employee in scope, collect the **supplied** inputs — self-review, manager review, optional peer/360, goal records from the prior cycle. If the client keeps these in files, point them into `reports/employee-reports/performance-management/<employee-slug>/`; if they're pasted in, save them there. **Never fabricate an input** — if a self-review or manager input is missing, note it and proceed with what exists, scoring absences as absent. If goals were never set for the period, surface that (it changes what a fair review can even conclude) and recommend fixing goal-setting for next cycle per `references/goal-okr-framework.md`.

## 5. Calibration guidance (reduce bias)

Before ratings firm up, give the managers/HR calibration guidance per the skill: apply the **same scale and behavioral anchors** across managers; watch for halo/horns, recency, leniency/severity, central-tendency, and similar-to-me bias; check that comparable performance earns comparable ratings regardless of manager or employee; and flag any rating pattern that tracks a protected characteristic rather than results. If the scope includes a calibration pass, this is where you brief it. Calibration produces **calibration-ready summaries**, not published ratings.

## 6. Generate packets (dispatch subagents)

Dispatch the **hr-performance-reviewer** agent per employee/job, passing config paths, the employee slug, and the **supplied inputs** (self/manager/peer/goals), plus which job to do: review packet, consolidation of self+manager+peer, calibration-ready summary, or PIP. When there are **3+ independent employees with no shared files**, dispatch in parallel (one message, multiple Agent calls); go sequential for dependent steps (e.g. consolidate, then calibrate the group). Each agent writes its draft into `reports/employee-reports/performance-management/<employee-slug>/` and returns its output contract.

For any **PIP**: confirm it targets a genuine, documented gap where goals/feedback/support were actually in place; ensure the counsel-review banner is stamped; and flag any termination-track PIP for counsel, coordinating with `employee-relations/` and `offboarding/` — never execute a separation from here.

## 7. Route outcomes

From the drafts, summarize routing for HR/managers (do not act unilaterally):
- **High performers** → recommend development/stretch via `training-development/` and succession/high-potential planning via `strategy/`.
- **Solid performers** → seed next-cycle goals (per the goal/OKR framework).
- **Underperformers** → the PIP drafted in step 6, flagged for counsel where termination-track.

## 8. Closeout

Store everything confidentially under `reports/employee-reports/performance-management/`. Give the user a closing summary: who was reviewed, where each draft lives (file paths), the calibration flags to resolve, any PIP/counsel flags, and the reminder: **these are drafts for manager/HR calibration and finalization — this pipeline never publishes a rating or decides an outcome.** Warn if any performance PII sits in a tracked (non-gitignored) file and offer to help move or gitignore it.
