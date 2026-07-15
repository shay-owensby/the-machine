---
name: hr-dei
description: Build a diverse workforce and an inclusive culture LAWFULLY — assessment (representation, pay-equity, inclusion surveys, all aggregate and privacy-safe), equitable practices across the employee lifecycle (inclusive hiring, equitable pay, development, promotion), inclusion initiatives (ERGs, mentoring, bias-awareness training), goal-setting with accountability, and measurement. Use when the client wants a DEI strategy, a representation or inclusion assessment, an ERG or mentoring program, inclusive-hiring or bias-awareness plans, or DEI goals and metrics — always scoped for legality and counsel review.
---

# HR Diversity, Equity & Inclusion

Helps a company build a genuinely diverse workforce and an inclusive culture **within the law** — by fixing the practices that produce inequitable outcomes rather than by imposing unlawful preferences. This skill owns HR function #10 and exports to `diversity-equity-inclusion/`; representation and pay-equity reports may **also** land in `reports/analytics/` (see the folder map).

## Setup gate (run first)

Enforce the config gate before any work, per `${CLAUDE_PLUGIN_ROOT}/skills/hr-config/SKILL.md`: look for `human-resources/config.yaml` at project root, require `version: 1` and `setup.completed: true`. If missing or invalid, STOP and tell the user exactly:
> Human resources isn't configured for this project yet. Run `/setup-human-resources` first.

Then load context: `company.about_file` (what the company is and values — grounds initiatives in real work), `company.soul_file` (voice for culture/employee comms), `company.design_file` (branded look), `company.name`, `company.size` (small headcount makes demographic cuts re-identifying — see rule 2), `company.locations`, `company.remote_policy`, and `legal.jurisdictions` (**the** determinant of what is lawful — see rule 1). Honor degraded modes (null brand file → neutral voice + warn once; empty `legal.jurisdictions` → make no jurisdiction-specific legality claim, produce general best-practice framing only, and flag the whole program for localization + counsel).

## Two standing safety rules (apply to everything below)

1. **Drafts, not legal advice — DEI has real legal constraints.** DEI programs operate inside employment law, and the legal landscape **varies sharply by jurisdiction and changes over time**. Some practices that sound pro-diversity are **unlawful**: hiring/promotion **quotas**, race/sex/protected-characteristic **preferences** or set-asides, protected-group-restricted programs or benefits, and "balancing" decisions on protected characteristics can create **reverse-discrimination / disparate-treatment liability** — and what's permitted differs by jurisdiction (and by whether the employer is public/private or a government contractor). This skill therefore builds **lawful, opportunity-widening** DEI: remove barriers, broaden pipelines, standardize criteria, and open programs to all — it does **not** design quotas or preferences. **Flag every design choice that touches a protected characteristic for employment-counsel review**, scope legality to `legal.jurisdictions`, name the jurisdiction, and — when `legal.counsel_review: true` — stamp DEI strategies, goals, and reports with "⚠️ Draft — requires review by qualified HR/legal counsel before use". **Never fabricate benchmark, market, or representation numbers** — no invented "industry average is X%", no made-up parity figures; every number comes from supplied data or a named source, or it's a placeholder and a question.
2. **Confidential by default — small groups re-identify people.** Representation, pay-equity, and inclusion-survey data are sensitive. **Report only aggregates**, and beware that **small-group demographic cuts can re-identify individuals** — a "women in Engineering" cell of 2, or the single employee of a given background at a site, is effectively named. **Suppress or aggregate any small group** (apply a minimum cell size — commonly n < 5 — or roll up to a coarser cut) before anything leaves the confidential zone. Keep identifiable DEI data in-project under `confidentiality.records_dir` → `reports/employee-reports/`; never paste demographic PII into an external service, web search, or MCP call. Never invent employee demographic data — supplied or placeholder only.

## Operating method

1. **Assess — aggregate and privacy-safe.** Establish the baseline from **supplied** data, never invented, using `references/dei-strategy-framework.md`:
   - **Representation** — demographic makeup by level, function, and stage (applicant → hire → promote → exit), to locate where representation drops. Aggregate; suppress small cells.
   - **Pay equity** — cross-reference `compensation-benefits/` (which owns the internal pay-equity method): pay for comparable work across groups, gaps remaining after legitimate controls. Pay-equity outputs may also go to `reports/analytics/`. Jurisdiction-scope and flag for counsel.
   - **Inclusion** — how included/belonging people feel (inclusion-survey items, eNPS cut by group **only where cells are large enough**). Measures experience, which representation alone misses.
2. **Fix the practices across the employee lifecycle (this is the lawful core).** Target the *processes* that produce inequitable outcomes, applied to everyone:
   - **Attraction & hiring** — widen sourcing channels, write inclusive/unbiased job descriptions, use structured interviews and consistent scorecards, diverse-but-not-quota interview practices. Cross-reference `recruitment/` (which owns JD/screening/interview tooling); DEI supplies the equity lens, not a quota.
   - **Pay** — equitable, transparent pay via `compensation-benefits/`; DEI consumes the pay-equity findings, it doesn't set bands.
   - **Development & advancement** — equal access to stretch work, mentoring, and training; check promotion and access rates for unexplained gaps. Cross-reference `training-development/` and `strategy/` (succession/talent pools).
   - **Retention & exit** — analyze exit patterns by group (aggregated) to find where inclusion breaks down.
   Frame every fix as *removing a barrier / standardizing a process / widening a pipeline* — open to all — not as a protected-characteristic preference.
3. **Inclusion initiatives.** Design programs that build belonging, structured to be **open to all** (participation not restricted by protected characteristic — a common legality pitfall): **ERGs / affinity groups** (voluntary, employee-led, membership open), **mentoring/sponsorship** (transparent access criteria), and **bias-awareness / inclusive-leadership training** (hand delivery to `training-development/`). Flag any design that would restrict a program or benefit by protected characteristic for counsel.
4. **Set goals with accountability — lawfully.** Prefer **process and aspirational** goals (e.g. "diverse candidate slates via broader sourcing", "structured interviews for all roles", "close unexplained pay gaps", "improve inclusion-survey scores") over **outcome quotas** ("hire X% of group Y"), which risk unlawful preference. Assign owners, cadence, and review. Explicitly flag any outcome-percentage target for counsel before it's adopted.
5. **Measure.** Track representation, inclusion, and equity metrics over time (definitions in the hr-metrics catalog: DEI representation, pay-equity ratio, eNPS/engagement) — always aggregated, small-n suppressed. Report progress against the process/aspirational goals. Cross-reference the **hr-reports** skill for the report/dashboard itself.

## When to use the reference

- **`references/dei-strategy-framework.md`** — building a DEI strategy end-to-end: the maturity/assessment model, focus areas across the lifecycle, initiative planning, representation & inclusion metrics (with the small-n re-identification warning and aggregation guidance), and the governance/accountability structure — carrying the legal-caution/counsel flag throughout.

## Cross-references

- `recruitment/` — owns inclusive JD/screening/interview tooling; DEI adds the equity lens.
- `compensation-benefits/` — owns the pay-equity method; DEI consumes its findings (which may also feed `reports/analytics/`).
- `training-development/` — delivers bias-awareness / inclusive-leadership training.
- `strategy/` — succession/talent pools where advancement equity is checked.
- `legal-compliance/` and counsel — own what is lawful in `legal.jurisdictions`; DEI flags and routes, never rules.

## Boundaries

- Export only to `diversity-equity-inclusion/`; representation and pay-equity reports may **also** go to `reports/analytics/`. Identifiable demographic records live in the confidential `reports/employee-reports/` zone. Never invent new top-level folders.
- **Never design quotas, protected-characteristic preferences, set-asides, or protected-group-restricted programs.** Build lawful, opportunity-widening DEI and flag every protected-characteristic design choice for counsel — legality is jurisdiction-specific and changing, never asserted as settled.
- Never fabricate representation, benchmark, or market numbers — supplied data or a named source only, else a placeholder and a question.
- Report aggregates only; suppress small groups that could re-identify individuals. Everything is a draft for HR/legal review.
