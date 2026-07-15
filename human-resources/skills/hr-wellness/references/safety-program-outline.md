# Health, Safety & Wellness Frameworks

Three reusable frameworks: a **workplace safety program**, an **EAP/wellness-program outline**, and a **return-to-work / reasonable-accommodation interactive-process checklist**. Fill every `<placeholder>`; delete guidance in _italics_. Ground everything in the company's **actual** operations, worksites, and hazards (`company.about_file` + what the user states) — never invent a hazard, standard, entitlement, or benefit.

> ⚠️ **Draft — requires review by qualified HR/legal counsel and a qualified safety professional before use.** _(Include when `legal.counsel_review: true`; recommended regardless in this domain.)_
>
> **Jurisdiction & threshold flags travel with every item below.** Occupational-safety (OSHA-type), leave, and reasonable-accommodation (ADA-type) rules are jurisdiction- and size-specific. Never state a safety standard, exposure limit, incident-reporting form or deadline, leave duration, eligibility threshold, or accommodation obligation as fact. Scope each to `legal.jurisdictions`, name the jurisdiction, and mark it **"verify against current `<jurisdiction>` rule / qualified safety professional"**. The *compliance* obligations are tracked separately in `legal-compliance/`.
>
> **Medical information is confidential and separate.** Any injury, medical, leave, or accommodation documentation is the most sensitive PII. Keep it in the confidential records zone (`confidentiality.records_dir`, i.e. `reports/employee-reports/`), separate from the general personnel file — never in the shareable `health-safety-wellness/` folder. In the accommodation process, work from **functional limitations**, not diagnoses.

---

## Part A — Workplace safety program

### A1. Purpose & scope
_One paragraph: the company's commitment to a safe workplace, and which sites, operations, and workers this program covers (include remote/hybrid where relevant)._

### A2. Roles & responsibilities
| Role | Safety responsibility |
|---|---|
| Senior management | Visible commitment, resources, accountability — the foundation of the program |
| Safety coordinator / committee | `<owns the program: assessment, training, investigation, review>` |
| Managers / supervisors | Enforce safe-work procedures evenly; ensure training; act on hazards |
| Employees | Follow procedures, use PPE, report hazards / injuries / near-misses without fear |
| First-aid / emergency responders | `<designated responders and their training>` |

### A3. Hazard assessment
Walk the **real** worksites and tasks. For each identified hazard, rank and assign a control using the **hierarchy of controls** (apply in this order — PPE is the last resort, not the first).

| # | Location / task | Hazard | Likelihood (L/M/H) | Severity (L/M/H) | Risk rank | Control (elim → substitute → engineering → administrative → PPE) | Owner | Status |
|---|---|---|---|---|---|---|---|---|
| 1 | `<area/task>` | `<hazard>` | | | | | | ☐ |
| 2 | | | | | | | | ☐ |

_Reassess on the review cadence and whenever operations, equipment, or the workspace change._

### A4. Safe-work procedures
_Written step-by-step procedures for each hazardous task (e.g. equipment operation, chemical handling, lifting, lone/remote work). Name the task, the steps, the required controls/PPE, and what to do if something goes wrong. Keep them where workers can actually find them._

### A5. Safety training plan
| Training | Audience | When | Frequency / refresher | Delivery (coordinate `training-development/`) | Roster kept? |
|---|---|---|---|---|---|
| New-hire safety orientation | All new hires | Day 1 / week 1 | Once + as needed | | ☐ |
| Task-specific / equipment | `<roles>` | Before task | `<cadence>` | | ☐ |
| Emergency / first-aid | `<designated>` | | `<cadence>` | | ☐ |
| Refresher / annual | `<audience>` | | `<cadence>` | | ☐ |

_Some safety training is mandated on a set cadence in certain jurisdictions/industries — **verify** which apply; don't assert a mandate._

### A6. PPE
| Task / area | Required PPE | Provided by | Fit / inspection | Training given |
|---|---|---|---|---|
| `<task>` | `<PPE>` | Company | `<how>` | ☐ |

_Scope PPE to the real hazards from A3. Don't assume PPE the operations don't require._

### A7. Incident reporting & investigation
Make reporting **easy and blame-reducing** — you want near-misses reported, not hidden.

1. **Report** — any employee reports an injury, illness, or near-miss immediately via `<channel>`; supervisor notified.
2. **Immediate response** — first aid / medical attention; make the area safe; preserve the scene where needed.
3. **Investigate** — for anything beyond trivial, investigate promptly to **root cause** (not just "who"); interview involved parties factually.
4. **Corrective action** — assign fixes to the hazard/root cause, with an owner and due date; track to closure.
5. **Record** — log it (structure below). **Which injuries/illnesses must be formally recorded or reported to an agency, on what form, and by when, is jurisdiction-specific — verify; do not assert a form or deadline.**
6. **Confidentiality** — any medical detail about the injured worker goes to the confidential records zone, not the shareable log.

**Incident log structure** (keep identifying medical detail OUT of this shareable log — reference a confidential case file instead):

| Incident ID | Date | Location / task | Type (injury / illness / near-miss / property) | Brief description (no medical detail) | Root cause | Corrective action | Owner | Status | Reportable? (verify per jurisdiction) | Confidential case file ref |
|---|---|---|---|---|---|---|---|---|---|---|
| | | | | | | | | ☐ | verify | `reports/employee-reports/...` |

### A8. Review cadence
_Review the whole program on a set cadence (`<e.g. annually>`) and after any significant incident, new hazard, or change in operations. Record what changed and when. A program that is never reviewed is a program that has already drifted._

---

## Part B — EAP / wellness-program outline

_Design supports people will actually use. Ground every offering in what the company can genuinely provide — do not promise a benefit it hasn't decided to fund. Voice employee-facing text per `company.soul_file`._

### B1. Employee Assistance Program (EAP)
- **What it offers:** `<confidential counseling, referrals, work-life resources, crisis support — as applicable>`
- **Confidentiality:** State plainly that EAP use is **confidential** and separate from HR/performance records — trust is what makes an EAP used. HR never receives clinical details.
- **Access:** how to reach it, cost to the employee (`<typically no cost>`), availability.
- **Manager role:** managers may *refer* and *support*, never diagnose or pry; keep any awareness confidential.

### B2. Wellness initiatives
| Dimension | Example initiatives | Offered? | Notes |
|---|---|---|---|
| Physical | `<fitness, ergonomics, health screenings>` | ☐ | ground in real budget/benefit decisions |
| Mental / emotional | `<EAP, mental-health days, mindfulness>` | ☐ | |
| Financial | `<planning resources, education>` | ☐ | |
| Social / community | `<connection, ERG tie-ins, volunteering>` | ☐ | |

### B3. Stress, workload & burnout
_Practical supports: workload/capacity conversations in 1:1s, realistic expectations, manager awareness of burnout signs, flexible-work options where the policy allows, and a clear path to the EAP. Address causes (workload, unclear expectations), not just symptoms._

### B4. Communication & uptake
_How the programs are announced, kept visible, and measured (uptake, anonymous feedback). A benefit nobody knows about isn't a benefit._

---

## Part C — Return-to-work / reasonable-accommodation interactive-process checklist

> **This is an ADA-type interactive process — jurisdiction-specific and legally sensitive.** Run it as a documented, good-faith, back-and-forth process, **not** a yes/no decision. Scope obligations to `legal.jurisdictions`, flag every entitlement/threshold to **verify with counsel**, and coordinate the leave/accommodation compliance layer with `legal-compliance/`. **All medical documentation stays in the confidential records zone, separate from the personnel file.**

| Done | Step | Notes |
|---|---|---|
| ☐ | **Recognize the request** — an accommodation request need not use specific words; a manager who learns of a limitation should route it to HR | |
| ☐ | **Engage promptly** — open a timely, good-faith dialogue with the employee | document date opened |
| ☐ | **Identify essential job functions** — from the job description; separate essential from marginal | |
| ☐ | **Focus on functional limitations, not diagnosis** — request only the minimum medical information needed to understand limitations and duration | keep in confidential zone |
| ☐ | **Explore accommodations together** — brainstorm options; consider the employee's preference; look at reassignment/modified duty/schedule/equipment as applicable | |
| ☐ | **Assess reasonableness** — effectiveness vs. hardship; **whether a given option is required is jurisdiction-specific — verify with counsel** | |
| ☐ | **Decide & implement** — grant, offer an alternative, or (only with counsel) document why no reasonable option exists | |
| ☐ | **Document each step** — request, dialogue, information considered, decision, and rationale — kept confidential | process record vs. medical detail |
| ☐ | **Return-to-work plan (if leave involved)** — coordinate with any leave; define modified/light duty where offered; set a medically-appropriate ramp; confirm fitness per policy | |
| ☐ | **Follow up** — check the accommodation is working; revisit as circumstances change | |
| ☐ | **Confidentiality maintained throughout** — medical info shared strictly on need-to-know; stored separate from personnel file | see hr-records skill |

_Retention periods for accommodation/medical records are jurisdiction-specific — see the records-retention framework and verify._
