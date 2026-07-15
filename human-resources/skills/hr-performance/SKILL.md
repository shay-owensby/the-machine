---
name: hr-performance
description: Run a fair, defensible performance-management system — goal-setting (OKRs/KPIs/SMART), ongoing feedback and 1:1s, review cycles (annual/quarterly with self, manager, and optional 360 inputs), cross-manager calibration to reduce bias, distinguishing high performers from those needing support, and coaching managers to write behavior-based, non-discriminatory evaluations and legally sound PIPs. Use when the client wants to set goals, run a review cycle, calibrate ratings, draft a performance review, or put an employee on a performance improvement plan.
---

# HR Performance Management

Turns performance management from an annual scramble into a fair, consistent, documented system: set clear goals, give feedback continuously, review on a predictable cadence, calibrate across managers to strip out bias, and route the results — grow the high performers, support the strugglers, and document everything to a standard that holds up under scrutiny. This skill owns HR function #4 and exports to `reports/employee-reports/performance-management/` — the **confidential** zone (identifiable per-employee PII).

## Setup gate (run first)

Enforce the config gate before any work, per `${CLAUDE_PLUGIN_ROOT}/skills/hr-config/SKILL.md`: look for `human-resources/config.yaml` at project root, require `version: 1` and `setup.completed: true`. If missing or invalid, STOP and tell the user exactly:
> Human resources isn't configured for this project yet. Run `/setup-human-resources` first.

Then load context: `company.about_file` (what the company does — grounds what "good performance" means for a role), `company.soul_file` (voice for employee-facing review and feedback language), `company.design_file` (branded document look), `company.size`, `company.locations`, and `legal.jurisdictions`. Honor degraded modes (null brand file → neutral, plain-language voice + warn once; empty `legal.jurisdictions` → no jurisdiction-specific claims, general best-practice only).

## Two standing safety rules (apply to everything below)

1. **Drafts, not legal advice — and some of this is legally sensitive.** Reviews, goals, calibration notes, and PIPs are drafts for review by the client's qualified HR professional and/or employment counsel. **PIPs and any disciplinary or termination-track documentation carry real legal risk** — a poorly written, inconsistently applied, or pretextual performance record is evidence in a discrimination, retaliation, or wrongful-termination claim. So: keep every performance record **factual, specific, and behavior-based**; apply the same standard to comparable employees; never editorialize about personality, protected characteristics, or their proxies. Flag any termination-track item for counsel and coordinate it with `employee-relations/` and `offboarding/`. When `legal.counsel_review: true` (and always for PIPs regardless), stamp PIPs and disciplinary documentation with "⚠️ Draft — requires review by qualified HR/legal counsel before use". Never fabricate a statute, threshold, deadline, or a fact about an employee's performance.
2. **Confidential by default.** Performance records are identifiable PII. Keep them in-project under `reports/employee-reports/performance-management/`; never paste employee names, ratings, review text, or PIP content into an external service, web search, or MCP call. Warn if you spot performance PII in a tracked (non-gitignored) file. Never invent performance data, ratings, or verdicts about a real employee — placeholder or supplied inputs only.

## Operating method

1. **Goal-setting.** Establish the performance contract up front: what the employee is trying to achieve this period, and how it ties to team and company priorities. Use `references/goal-okr-framework.md` — pick OKRs, KPIs, or SMART goals to fit the role, cascade company → team → individual so everyone pulls the same direction, and make each goal measurable so the review isn't a matter of opinion. Set goals **at the start** of the cycle, not retrofitted at review time. Few, clear, owned.
2. **Ongoing feedback & 1:1s.** Performance management is continuous, not a once-a-year event. Coach managers to hold regular 1:1s, give timely specific feedback (both recognition and course-correction), and keep a lightweight running record of notable examples throughout the period — so the formal review summarizes a documented year rather than inventing one from the last two weeks (recency bias). No surprises at review time.
3. **Review cycle.** Run reviews on the configured cadence (annual and/or quarterly). Gather inputs in parallel: **employee self-review**, **manager review**, and — when the client uses it — **360/peer feedback**. Draft each on `references/review-template.md` (same template, self and manager versions), scoring competencies against **behavioral anchors** and assessing goals-vs-results with evidence. The `/hr-review-cycle` command orchestrates the whole cycle end to end.
4. **Calibration.** Before ratings are finalized, calibrate across managers to reduce bias and rating inflation/deflation. Compare how different managers apply the scale, surface outliers, and check that similar performance earns similar ratings regardless of who the manager is or who the employee is. Watch for the classic distortions — halo/horns, recency, leniency/severity, central tendency, and similar-to-me bias — and for any pattern where ratings correlate with a protected characteristic rather than with results. Calibration produces **calibration-ready summaries**, not published ratings.
5. **Route the outcomes.**
   - **High performers** → development and stretch (hand off to `training-development/` for growth plans, and to `strategy/` for succession/high-potential planning). Recognize and retain them.
   - **Solid performers** → reinforce, set the next cycle's goals, target growth areas.
   - **Underperformers** → first ask whether goals, feedback, and support were actually in place (if not, fix that before escalating). Where a genuine, documented performance gap remains, move to a **PIP** using `references/pip-template.md`: factual gap statements, measurable expectations, real support/resources, a check-in cadence, a defined timeline, and clearly stated consequences. A PIP is a support tool first; it is also a legally sensitive document — see safety rule 1.
6. **Support managers in delivering evaluations.** Managers, not this plugin, own and deliver the evaluation. Coach them to: cite specific behaviors and results (not traits or hearsay), tie every rating to evidence, balance strengths with growth, keep language consistent and non-discriminatory, separate performance from personality, and be ready to have a two-way conversation. The employee's self-review and comments are part of the record.

## When to use each reference

- **`references/review-template.md`** — drafting or structuring any performance review (self or manager version): goals-vs-results, competency ratings with behavioral anchors, strengths, growth areas, manager summary, employee comments, and the overall rating scale.
- **`references/goal-okr-framework.md`** — setting or scoring goals: choosing OKRs vs. KPIs vs. SMART, writing them well, cascading company → team → individual, and tracking/scoring them.
- **`references/pip-template.md`** — putting an employee on a performance improvement plan: gap statements, measurable expectations, support, cadence, timeline, consequences, and the counsel-review requirements. **Read its legal-sensitivity note before drafting.**

## Agents this skill drives

- **hr-performance-reviewer** — from **supplied** inputs, drafts a review packet, consolidates self + manager + peer inputs, produces calibration-ready summaries, or drafts a PIP. Factual and behavior-based; never invents performance data or verdicts; flags termination-track PIPs for counsel. Writes into `reports/employee-reports/performance-management/`.

## Commands this skill drives

- **/hr-review-cycle** — orchestrates a full review cycle: scope → gather self/manager/(peer) inputs → calibration guidance → dispatch hr-performance-reviewer to generate packets → store confidentially. Produces drafts for manager/HR finalization; never publishes ratings.

## Boundaries

- Export **only** to `reports/employee-reports/performance-management/` — the confidential zone. Never write performance PII elsewhere and never invent new top-level folders.
- Development/succession outcomes are handed off to `training-development/` and `strategy/`; termination-track matters coordinate with `employee-relations/` and `offboarding/` — this skill does not own discipline or separation.
- Everything is a **draft for HR/manager review**; the plugin never finalizes or publishes a rating, and never decides an employment outcome. PIPs and disciplinary documentation are legally sensitive and flagged for counsel. Never fabricate performance data about a real employee.
