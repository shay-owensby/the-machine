---
name: hr-reports
description: Produce cross-function HR reports and dashboards from SUPPLIED data — pick the metrics that answer the question, validate and aggregate the data (privacy-safe, small-n suppressed), compute the metrics, and present a clear markdown report or dashboard with trends and caveats. Use when the client wants a headcount, turnover, hiring-funnel, DEI, comp, or mixed people-analytics report or dashboard. Never fabricates figures; always states the data source and its gaps.
---

# HR Reporting & Analytics

Turns supplied people data into a clear, honest, decision-ready report or dashboard — the cross-function reporting layer that headcount, turnover, hiring, comp, and DEI work all surface through. This skill owns cross-function HR reporting and exports to `reports/analytics/` (see the folder map). It computes and presents; it never invents numbers.

## Setup gate (run first)

Enforce the config gate before any work, per `${CLAUDE_PLUGIN_ROOT}/skills/hr-config/SKILL.md`: look for `human-resources/config.yaml` at project root, require `version: 1` and `setup.completed: true`. If missing or invalid, STOP and tell the user exactly:
> Human resources isn't configured for this project yet. Run `/setup-human-resources` first.

Then load context: `company.name`, `company.size` (sanity-check totals against it; small headcount makes fine cuts re-identifying — see rule 2), `company.locations`, `company.employment_types`, `company.soul_file` (voice for the narrative), `company.design_file` (branded look if the report is presented), and `legal.jurisdictions` (context for any statutory metric). Honor degraded modes (null brand file → neutral voice + warn once).

## Two standing safety rules (apply to everything below)

1. **Never fabricate a figure — reports are only as good as their data.** Every number in a report is **computed from data the user supplied** (an HRIS/ATS export, a roster, a survey file, prior reports in `reports/analytics/`) — never recalled, estimated, or filled in from memory. If a metric's inputs are missing, **report the gap explicitly** ("time-to-fill unavailable — no requisition open/close dates supplied") rather than guessing. State the **data source and its date** at the top of every report, and label every derived figure so a reader can trace it. Benchmarks/market comparisons appear only when the user supplies a named source — never an invented "industry average". Reports are drafts for HR review, not audited statements; where a metric touches statutory obligation, note it's jurisdiction-specific and for HR/counsel to verify.
2. **Confidential by default — aggregate, and suppress small groups.** Cross-function reports are **aggregate** — they must not expose individual PII. **Small cuts re-identify people**: a turnover cell of 1, "engineers in the London office" when there are 3, or any demographic slice below the minimum cell size effectively names someone. **Suppress or roll up any group below a minimum cell size** (commonly n < 5) before it appears in a report, and never include names, IDs, or per-person rows in an analytics report — those belong in the confidential `reports/employee-reports/` zone. Never paste raw PII into an external service, web search, or MCP call.

## Operating method

1. **Frame the question.** Establish what decision the report serves ("is attrition rising?", "how healthy is the hiring funnel?", "what's our headcount trend by function?"). The question decides the metrics — don't dump every metric you can compute.
2. **Pick the metrics.** Choose the minimum set that answers the question from `references/hr-metrics-catalog.md` (each entry gives the precise formula, inputs, and interpretation). Note which inputs each needs so you can check them against the supplied data.
3. **Validate the data.** Before computing: confirm the source and its date; check the period covered; sanity-check totals (e.g. headcount vs. `company.size`); note missing fields, duplicates, or ambiguous categories. Decide the denominator/period conventions and state them (e.g. average headcount for turnover). If the data can't support a chosen metric, drop it and record the gap — don't approximate.
4. **Aggregate for privacy.** Apply the minimum-cell-size rule (rule 2) to every cut. Where a small group would be exposed, roll it up to a coarser cut or suppress it and say so. Never let a per-person row survive into the report.
5. **Compute.** Apply the catalog formulas exactly, on the validated data, over the stated period. Show the inputs behind each headline number so it's traceable. Keep units and periods consistent across the report.
6. **Trend it.** Where prior reports exist in `reports/analytics/`, compare run-over-run and show direction (↑/↓/→) — a metric with no comparison point is a snapshot; say so. For small samples, describe the change plainly rather than overclaiming ("up 3 exits on a base of 40", not a dramatic percentage).
7. **Present clearly.** Write a clean markdown report or dashboard: a header with source/date/period, the headline metrics (tables for numbers), trends, cuts (privacy-safe), and a short "what this suggests" read in `company.soul_file` voice — framed as observations for HR, not directives. Close with **caveats**: data gaps, suppressed cells, small-sample cautions, and anything needing verification. For strategic interpretation of the numbers, hand to the **hr-strategy** skill (people data → leadership insight).

## When to use each reference

- **`references/hr-metrics-catalog.md`** — whenever you select or compute a metric: precise definitions, formulas, required inputs, and interpretation notes for headcount/FTE, turnover/attrition, retention, time-to-fill/time-to-hire, cost-per-hire, offer-acceptance, absenteeism, internal-mobility/promotion, span of control, DEI representation, compa-ratio/pay-equity ratio, training completion, and eNPS/engagement.

## Agents this skill drives

- **hr-report-writer** — assembles a cross-function HR report or dashboard from **supplied** data using the metrics catalog: computes the metrics, shows trends against prior reports, flags data gaps, aggregates to protect privacy (small-n suppression), and writes a dated markdown report to `reports/analytics/YYYY-mm-dd-<topic>.md`. Refuses to invent numbers.

## Boundaries

- Export only to `reports/analytics/`. Per-person/identifiable records belong in the confidential `reports/employee-reports/` zone, never in an analytics report. Never invent new top-level folders.
- Never fabricate a figure or a benchmark — compute only from supplied data; report gaps rather than guessing; state the source and date.
- Aggregate only; suppress groups below the minimum cell size. Reports are drafts for HR review; statutory-metric caveats are jurisdiction-specific and flagged, never asserted.
