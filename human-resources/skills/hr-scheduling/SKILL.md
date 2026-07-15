---
name: hr-scheduling
description: Build and manage workforce schedules — shift schedules and coverage/staffing plans against demand and headcount, PTO/leave calendars and coverage during absences, and interview scheduling coordination — as reusable templates and drafts, with jurisdiction-specific predictive-scheduling / fair-workweek laws (advance notice, predictability pay) and overtime/rest-break/minor-hours rules flagged for verification rather than asserted. Use when the client wants to build a shift schedule, a coverage/staffing plan, a PTO/leave calendar, arrange coverage for an absence, or coordinate interview scheduling.
---

# HR Scheduling

Helps a client staff the right people at the right times: build shift schedules against real demand and available headcount, keep a clear PTO/leave calendar and arrange coverage when people are out, and coordinate interview scheduling for active searches. This skill owns HR function-area scheduling and exports to `scheduling/` (see the folder map). It produces **reusable templates and drafts** — scheduling law (fair-workweek, overtime, breaks, minor-hours) is jurisdiction-specific and goes to the client's counsel before anything is treated as a rule.

## Setup gate (run first)

Enforce the config gate before any work, per `${CLAUDE_PLUGIN_ROOT}/skills/hr-config/SKILL.md`: look for `human-resources/config.yaml` at project root, require `version: 1` and `setup.completed: true`. If missing or invalid, STOP and tell the user exactly:
> Human resources isn't configured for this project yet. Run `/setup-human-resources` first.

Then load context: `company.about_file` (what the operation is — its hours, roles, and demand pattern drive the schedule), `company.size` (headcount available to schedule), `company.employment_types` (full-time / part-time / contractor shape coverage), `company.locations` and `legal.jurisdictions` (the authoritative scope for any scheduling-law claim), `company.remote_policy`, and `company.timezone` (schedules and interviews are time-sensitive). Honor degraded modes: null `about_file` → don't invent hours, roles, or demand the company hasn't stated; empty `legal.jurisdictions` → make **no** jurisdiction-specific scheduling-law claim; produce general templates labeled "must be localized and verified with counsel".

## Standing safety rules (apply to everything below)

1. **Drafts, not legal advice — scheduling is legally regulated.** Several areas are **jurisdiction-specific** and must be flagged, scoped to `legal.jurisdictions`, and verified — never asserted as fact:
   - **Predictive-scheduling / fair-workweek laws** — some jurisdictions require **advance notice** of schedules, **predictability pay** for late changes, rest between shifts ("clopening" limits), good-faith estimates, and access-to-hours rules. Whether these apply, and their exact thresholds, is jurisdiction-specific — **flag and verify; never state a notice period or penalty as fact.**
   - **Overtime and rest/meal breaks** — overtime eligibility and multipliers, and mandatory rest/meal breaks, vary by jurisdiction. **Cross-ref `legal-compliance/`** (the hr-compliance skill tracks the wage-&-hour obligation); this skill just flags where a schedule could trigger them. Never assert an overtime threshold, multiplier, or break rule.
   - **Minor / young-worker hours** — where minors are employed, hours, timing, and break rules are tightly regulated and jurisdiction-specific — **flag and verify**.
   - When `legal.counsel_review: true`, note on any schedule that touches these areas that the scheduling-law items require counsel verification.
2. **Confidential by default.** Schedules and PTO/leave calendars contain employee data, and **the reason for a leave/absence can be sensitive (medical, personal)**. Keep schedules and calendars **in-project** under `scheduling/`. Record **that** someone is out and their coverage — not **why**, unless operationally necessary; any medical/health reason belongs in the confidential records zone (`confidentiality.records_dir`), not the shared calendar (see the hr-records and hr-wellness skills). Never paste employee data into an external service, web search, or MCP call. Never invent employee names, availability, or absences — placeholder or supplied data only.

## Operating method

1. **Build the shift schedule & coverage/staffing plan.** Start from **demand**, not from who's available: what does each day/shift actually require? Using `references/scheduling-templates.md`:
   - Map **demand → required headcount by role, by time block** (the coverage/staffing plan). Ground it in the real operation (`about_file`, hours, historical patterns the user provides).
   - Assign available people (respecting `employment_types`, stated availability, skills, and fairness — rotate undesirable shifts, distribute hours equitably) into the **weekly shift-schedule grid**.
   - Check the schedule against the **compliance flags** before publishing: does anyone cross an overtime line, miss a required break, get too little rest between shifts, or would a late change trigger predictability pay? Flag these for verification — don't silently assume the rule or silently ignore it.
   - Leave slack for the coverage you'll inevitably need.
2. **Manage the PTO/leave calendar & absence coverage.** Keep a clear calendar of who is off when (record the coverage, not the private reason). When someone is out — planned PTO or an unplanned absence — arrange coverage: identify who can fill in (skills + availability + hours/overtime impact), and update the schedule. For extended leave, coordinate the leave process itself with `health-safety-wellness/` (and keep any medical detail confidential). Watch for coverage collisions (too many people off at once for a role) and surface them early.
3. **Coordinate interview scheduling (cross-ref `recruitment/`).** For active searches, coordinate interview logistics using the interview-scheduling grid: candidate availability, interviewer panels and their availability, room/link, and stage sequence — in `company.timezone`, and mind candidates in other zones. This is the logistics layer; the interview *content and kits* live in `recruitment/`. Keep candidate data in-project.

## When to use the reference

- **`references/scheduling-templates.md`** — building any of: a **weekly shift-schedule grid**, a **coverage/staffing plan** (roles × time × required headcount), a **PTO/leave calendar**, or an **interview-scheduling grid**; plus a **compliance-check note** (fair-workweek / overtime / breaks / minor-hours — jurisdiction-verify).

## Boundaries

- Export **only** to `scheduling/`. Never invent new top-level folders. Any medical/health reason for an absence goes to the confidential records zone — never the shared calendar.
- Every scheduling-law item (fair-workweek/predictive-scheduling, overtime, rest/meal breaks, minor hours) is scoped to `legal.jurisdictions`, named, and flagged to verify with counsel. The wage-&-hour *obligation* view lives in `legal-compliance/`. Never assert a notice period, predictability-pay penalty, overtime threshold/multiplier, break rule, or minor-hours limit as fact.
- Everything is a **draft/template for review** — the plugin builds schedules and coverage plans; a human approves and publishes them. Never invent employee availability, absences, or names.
