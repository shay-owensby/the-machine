---
name: hr-strategy
description: Run HR as a strategic business partner — workforce planning (forecast staffing needs against the business plan, supply/demand/gap analysis, build-buy-borrow), organizational design (structures, spans & layers, role clarity, restructuring support), succession planning (critical roles, talent pools, readiness), and translating people data into leadership insight aligned to business objectives. Use when the client wants a headcount forecast, an org-design or restructuring analysis, a succession plan for critical roles, or people data framed for a leadership decision.
---

# HR Strategy, Workforce Planning & Org Design

Connects the people agenda to the business plan: forecast the workforce the strategy needs, design the organization to deliver it, secure the pipeline behind critical roles, and turn people data into decisions leaders can act on. This skill owns HR functions #12 (workforce planning & org design) and #15 (HR strategy & business partnership) and exports to `strategy/` (see the folder map).

## Setup gate (run first)

Enforce the config gate before any work, per `${CLAUDE_PLUGIN_ROOT}/skills/hr-config/SKILL.md`: look for `human-resources/config.yaml` at project root, require `version: 1` and `setup.completed: true`. If missing or invalid, STOP and tell the user exactly:
> Human resources isn't configured for this project yet. Run `/setup-human-resources` first.

Then load context: `company.about_file` (what the business does and where it's going — grounds every forecast in real work), `company.soul_file` (voice for leadership-facing narrative), `company.design_file` (branded look for org charts / decks), `company.name`, `company.size` (the current headcount baseline), `company.employment_types`, `company.locations`, `company.remote_policy` (shape spans, layers, and where roles can sit), and `legal.jurisdictions` (reductions and restructuring carry jurisdiction-specific obligations). Honor degraded modes (null `about_file` → rely on `company.industry`/`size`/`locations`, never invent business direction or numbers, warn once; empty `legal.jurisdictions` → make no jurisdiction-specific restructuring/notice claims, flag for localization).

## Two standing safety rules (apply to everything below)

1. **Drafts, not legal advice — and never fabricated numbers.** Workforce plans, org designs, and succession maps are drafts for review by the client's leadership and, wherever a reduction or restructuring is in scope, their qualified HR professional and employment counsel. **Restructurings, layoffs, and role eliminations carry jurisdiction-specific obligations** — notice periods, selection-criteria fairness, consultation/collective-redundancy rules, protected-class and disparate-impact exposure, and severance triggers all **vary by jurisdiction and by headcount** (`company.size`). Scope every such claim to `legal.jurisdictions`, name the jurisdiction, and flag "verify with counsel"; when `legal.counsel_review: true`, stamp any reduction/restructuring plan with "⚠️ Draft — requires review by qualified HR/legal counsel before use". **Never fabricate a forecast number, an attrition rate, a market/benchmark figure, or a statutory threshold** — build forecasts only from supplied business plans, real headcount, and real historical rates; if an input is missing, mark it a placeholder and ask.
2. **Confidential by default.** Succession plans, readiness ratings, flight-risk and performance judgments about named individuals are highly sensitive PII — keep them in-project and route identifiable per-person records to the confidential zone (`confidentiality.records_dir` → `reports/employee-reports/`), not the shareable `strategy/` folder. Aggregate workforce data before it goes into any leadership report; **small headcount cuts (by team, level, location, or demographic) can re-identify individuals** — aggregate or suppress small groups (see the reporting skill's small-n guidance). Never invent employee names, ratings, or succession data — placeholder or supplied data only.

## Operating method

### A. Workforce planning

1. **Anchor to the business plan.** Start from what the business intends to do — growth targets, new products/markets, planned locations, efficiency goals — from `company.about_file` and the leadership inputs the client supplies. No business plan, no forecast: if direction isn't supplied, capture what's known, mark the rest a placeholder, and ask. Do not invent strategy.
2. **Forecast demand.** Translate the business plan into the workforce it requires — roles, levels, skills, headcount, and *when* — using `references/workforce-planning-framework.md`. Tie demand drivers to real plan elements (revenue per head, units of work per role, new-site staffing models) rather than round guesses.
3. **Inventory current supply.** Establish the baseline from real data: current headcount (`company.size`), by role/level/location/employment type, plus critical skills held. Layer in expected **losses** — known attrition, retirements, internal moves — using the client's real historical rates, not invented ones.
4. **Gap analysis.** For each role/skill: gap = forecast demand − (current supply − expected losses). Surface both shortfalls (hire/develop) and surpluses (redeploy/reduce). Quantify only from supplied numbers.
5. **Close the gap — build, buy, or borrow.** For each gap choose the play: **build** (develop/promote internally → hand to `training-development/` and succession below), **buy** (hire externally → hand the demand to `recruitment/`), or **borrow** (contractors/contingent, where `company.employment_types` allows). Weigh lead time, cost, criticality, and how core the capability is.
6. **Scenario-plan.** Run at least growth / flat / reduction scenarios so the plan survives a changed business outlook — see the framework's scenario worksheet. For any **reduction** scenario, do not model names or selections; frame the structural change and immediately flag the legal, notice, and fairness obligations for counsel (safety rule 1).
7. **Action plan.** Produce a dated, owned action plan (what, which role, build/buy/borrow, when, hand-off folder) and the assumptions behind it. Route hiring demand to `recruitment/`, development needs to `training-development/`, and cost implications to `compensation-benefits/`.

### B. Organizational design

1. **Design from the work, not the org chart.** Start from the outcomes the business must deliver and group the work that produces them — by function, product, geography, customer, or a matrix — per `references/org-design-succession.md`. Name the trade-off each grouping makes (e.g. functional depth vs. product speed).
2. **Set spans and layers.** Right-size manager spans of control and the number of layers from top to front line. Too many layers slow decisions and inflate cost; too few overload managers. Use the reference's guidance; weigh `company.size` and `company.remote_policy`. Report span/layer figures as diagnostics from real headcount, not targets pulled from the air.
3. **Clarify roles and decision rights.** Define what each role owns, how roles hand off, and who decides what (a decision-rights view — e.g. who is Responsible/Accountable/Consulted/Informed). Ambiguous decision rights are the usual failure of a redesign; make them explicit.
4. **Support restructuring — carefully.** When redesign implies role changes or eliminations, describe the *structure* (new grouping, spans, reporting lines, role changes) and stop at the people layer: eliminations, selections, and severance are drafts that **must** go to HR/counsel, are jurisdiction- and size-specific, and get the counsel-review banner. Never present a restructuring as legally cleared.

### C. Succession planning

1. **Identify critical roles.** Flag roles whose vacancy would most damage the business — high impact, scarce skills, single points of failure — not merely the most senior. Use the succession template in `references/org-design-succession.md`.
2. **Assess incumbent risk.** For each critical role capture vacancy risk (retirement, flight risk, planned move) from **supplied** data only — never inferred or invented about a named person. Keep these judgments confidential.
3. **Build talent pools & rate readiness.** For each critical role, name potential successors and rate readiness (e.g. ready now / 1–2 years / 3+ years / emergency-only cover). A role with no ready successor is itself a workforce-planning gap (loop to A5: build vs. buy).
4. **Development actions.** For each successor, the specific moves to close the readiness gap — stretch assignments, mentoring, targeted training (hand to `training-development/`). Keep individual development plans in the confidential zone.

### D. People data → leadership insight

Translate people data into decisions: pull metrics from `reports/analytics/` (headcount, turnover, internal mobility, span of control — defined in the hr-reports metrics catalog) and frame them against business objectives — "what this means and what to do", not raw numbers. Always aggregate to protect individuals (safety rule 2), cite the data source and its date, and never assert a figure you weren't given. Cross-reference the **hr-reports** skill for the report/dashboard itself; this skill owns the *strategic interpretation*.

## When to use each reference

- **`references/workforce-planning-framework.md`** — building a headcount/skills forecast: demand forecasting, current-supply inventory, gap analysis, growth/flat/reduction scenario planning, and the action plan. Holds worksheet tables with clearly-marked example numbers.
- **`references/org-design-succession.md`** — designing or restructuring an organization (grouping options, spans & layers, decision rights) and building a succession plan (critical-role register, incumbent risk, successors & readiness levels, development actions), with templates.

## Cross-references

- `reports/analytics/` — the metrics that feed workforce planning and the leadership narrative (via the **hr-reports** skill).
- `recruitment/` — receives external-hire ("buy") demand from the workforce plan.
- `training-development/` — receives "build" development needs and succession development actions.
- `compensation-benefits/` — receives the cost implications of headcount and structure changes.
- `legal-compliance/` — owns the statutory analysis for any reduction/restructuring; this skill flags and routes, never rules.

## Boundaries

- Export only to `strategy/`. Identifiable succession/readiness records and named individual plans go to the confidential `reports/employee-reports/` zone, not here. Never invent new top-level folders.
- Never fabricate a forecast, attrition rate, benchmark, or statutory threshold — build only from supplied business plans and real historical/headcount data; mark missing inputs as placeholders and ask.
- Reductions, layoffs, and restructurings are drafts for HR/counsel: jurisdiction- and headcount-specific, flagged, never asserted as cleared. The legal determination belongs to `legal-compliance/` and counsel.
- Aggregate people data before it reaches any leadership output; suppress small groups that could re-identify individuals.
