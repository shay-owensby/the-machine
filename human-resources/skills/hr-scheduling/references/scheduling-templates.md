# Scheduling Templates

Reusable templates for workforce scheduling: a **weekly shift-schedule grid**, a **coverage/staffing plan**, a **PTO/leave calendar**, and an **interview-scheduling grid** — plus a **compliance-check note**. Fill every `<placeholder>`; delete guidance in _italics_. Ground every schedule in the company's **real** hours, roles, and demand (`company.about_file` + what the user states); use `company.timezone` for all times. Keep these in `scheduling/`. Never invent employee names, availability, or absences.

> **Scheduling law is jurisdiction-specific — flag, don't assert.** Predictive-scheduling / fair-workweek rules (advance notice, predictability pay, rest between shifts), overtime, mandatory rest/meal breaks, and minor/young-worker hours all vary by jurisdiction. Scope each to `legal.jurisdictions` and mark it **"verify with counsel"**. The wage-&-hour *obligation* view lives in `legal-compliance/`. See the compliance-check note below.
>
> **Confidentiality:** record **that** someone is off and their coverage — not the private reason. Any medical/health reason for an absence belongs in the confidential records zone (`reports/employee-reports/`), not a shared calendar.

---

## 1. Coverage / staffing plan (build this first — demand drives the schedule)

_Start from what each time block actually requires, by role. Then staff to it. Times in `company.timezone`._

| Role | Open–Mid `<hrs>` | Mid–Close `<hrs>` | Peak block `<hrs>` | Notes / skills required |
|---|---|---|---|---|
| `<role A>` | `<# needed>` | `<# needed>` | `<# needed>` | |
| `<role B>` | | | | |
| **Total headcount required** | | | | |

_Compare total required against available headcount (`company.size`, `employment_types`). Gaps → hiring, cross-training, or coverage from part-time/contractor pool._

## 2. Weekly shift-schedule grid

_Assign named people into shifts against the coverage plan. Distribute hours fairly; rotate undesirable shifts; respect stated availability and skills. Run the compliance check before publishing._

**Week of `<YYYY-MM-DD>`  ·  Location `<site>`  ·  Timezone `<company.timezone>`**

| Employee | Role | Mon | Tue | Wed | Thu | Fri | Sat | Sun | Scheduled hrs |
|---|---|---|---|---|---|---|---|---|---|
| `<name>` | `<role>` | `9–5` | `9–5` | off | `9–5` | `9–5` | off | off | `<total>` |
| `<name>` | | | | | | | | | |
| **Coverage by shift** _(vs. plan)_ | | | | | | | | | |

_Legend: time range = on shift · "off" = not scheduled · "PTO"/"leave" = approved absence (see calendar). Flag any cell that crosses an overtime line, misses a required break, or gives too little rest before the next shift — verify (see note)._

## 3. PTO / leave calendar

_Track who is off when and how the gap is covered. Record coverage, **not** the private reason. Watch for collisions — too many people off in one role at once._

| Employee | Type (PTO / sick / leave — no medical detail) | Start | End | Status (requested / approved) | Coverage arranged (who) | Role gap? |
|---|---|---|---|---|---|---|
| `<name>` | PTO | `<date>` | `<date>` | approved | `<covering employee>` | ☐ |
| `<name>` | leave | | | | | |

_Extended/medical leave: coordinate the leave process with `health-safety-wellness/`; keep medical documentation in the confidential records zone. Leave entitlements are jurisdiction-specific — verify._

## 4. Interview-scheduling grid (cross-ref `recruitment/`)

_Logistics only — the interview kits/content live in `recruitment/`. Coordinate candidate + panel availability in `company.timezone`; mind candidates in other zones. Keep candidate data in-project._

**Requisition / role: `<role>`  ·  Candidate: `<candidate>`  ·  Timezone note: `<candidate tz if different>`**

| Stage | Interviewer(s) | Date | Time (`<company.timezone>`) | Format (onsite / video / phone) | Room / link | Confirmed? |
|---|---|---|---|---|---|---|
| Screen | `<name>` | `<date>` | `<time>` | video | `<link>` | ☐ |
| `<panel / technical>` | | | | | | ☐ |
| `<final>` | | | | | | ☐ |

_Confirm availability with both candidate and each interviewer before locking; hold buffer between stages; send confirmations with clear join details._

## Compliance-check note (run before publishing any schedule)

Check the schedule against these — each is **jurisdiction-specific; verify with counsel, never assert the rule or number**:

| Check | What to look for | Flag |
|---|---|---|
| **Fair-workweek / predictive scheduling** | Is advance-notice of the schedule required? Would a late change owe **predictability pay**? Minimum **rest between shifts** ("clopening")? Good-faith-estimate / access-to-hours duties? | verify per `<jurisdiction>` |
| **Overtime** | Does any employee cross an overtime threshold? Eligibility and multiplier vary — cross-ref `legal-compliance/` | verify per `<jurisdiction>` |
| **Rest / meal breaks** | Are mandated breaks scheduled for shift lengths that require them? | verify per `<jurisdiction>` |
| **Minor / young-worker hours** | If minors are scheduled: hour caps, permitted times, required breaks | verify per `<jurisdiction>` |

_If `legal.jurisdictions` is empty, treat all of the above as unlocalized and label the schedule as needing localization + counsel review before use._
