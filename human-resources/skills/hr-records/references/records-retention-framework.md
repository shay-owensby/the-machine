# Employee Records: File-Structure & Retention Framework

A reusable framework for organizing employee records into properly separated files and setting a retention schedule. Fill every `<placeholder>`; delete guidance in _italics_. All identifiable records live in the confidential zone (`confidentiality.records_dir`, i.e. `reports/employee-reports/`) — never in a shareable folder, and gitignored when the repo is shared. Never invent employee data or a retention period.

> ⚠️ **Draft — requires review by qualified HR/legal counsel before use.** _(Include when `legal.counsel_review: true`.)_
>
> **Retention periods and required records are jurisdiction- and record-type-specific.** Every retention cell below is a **placeholder marked "verify per jurisdiction"** — do **not** fill in a number of years from memory. Scope each to `legal.jurisdictions`, and verify against the jurisdiction's labor/employment and tax agencies and counsel. The retention *obligation* tracking lives in `legal-compliance/`.

---

## The separate-files rule (read first)

Employee records are **not one file**. In many jurisdictions, keeping certain records separate — with different access — is a legal requirement, not a preference. Never co-mingle:

1. **Personnel file** — the general employment record.
2. **Confidential medical file — SEPARATE** — anything medical/health. **This is the most sensitive file and must be kept apart from the personnel file with tighter access.**
3. **Payroll / tax file** — compensation and financial PII.
4. **Work-authorization / eligibility file — commonly SEPARATE** — employment-eligibility/work-authorization verification records, often required to be stored apart with their own retention.

_Which separations are legally mandated, and the exact retention for each, is jurisdiction-specific — **verify with counsel**. Never assert the rule as settled._

## Record-category table

| Record category | File / location | Who may access (least-privilege) | Retention period | Disposal method |
|---|---|---|---|---|
| **Personnel** — offer/employment agreement, job description, position & pay history, performance reviews, acknowledgments, discipline, training records | Personnel file (confidential zone) | HR; the employee's manager on a need-to-know basis; the employee (own record — access right is jurisdiction-specific, verify) | `<verify per jurisdiction>` | Secure destruction (shred/secure-delete) |
| **Medical / health — CONFIDENTIAL & SEPARATE** — injury/workers'-comp records, leave medical documentation, accommodation medical info, medical exam / fitness-for-duty results, health-related benefits data | **Separate confidential medical file** (confidential zone) | Strictly limited authorized roles only; **not** the general manager; need-to-know | `<verify per jurisdiction — often different from personnel>` | Secure destruction |
| **Payroll / tax** — compensation, tax-withholding, direct-deposit/banking, timekeeping & wage records | Payroll/tax file (confidential zone) | Payroll/finance + authorized HR only | `<verify per jurisdiction — tax and wage rules differ>` | Secure destruction |
| **Benefits** — enrollment and administration (route any health-related detail to the medical file) | Benefits file (confidential zone) | Authorized HR/benefits admin | `<verify per jurisdiction>` | Secure destruction |
| **Work-authorization / eligibility — SEPARATE** — employment-eligibility/work-authorization verification records | **Separate** eligibility file (confidential zone) | Authorized HR only | `<verify per jurisdiction — often a distinct required period>` | Secure destruction |
| **Recruitment** — applications, resumes, interview notes, scorecards, background-check records (for both hired and non-hired candidates) | Recruitment records (confidential zone) | Hiring team + HR, need-to-know | `<verify per jurisdiction — non-hire retention often mandated>` | Secure destruction |
| **Performance** — reviews, goals/OKRs, calibration, PIPs, 1:1/feedback records | `reports/employee-reports/performance-management/` | HR + the employee's manager, need-to-know | `<verify per jurisdiction>` | Secure destruction |
| **Employee-relations / investigation** — case files, investigation notes, disciplinary/grievance records | `employee-relations/` (confidential) | Strictly limited investigation/HR roles | `<verify per jurisdiction>` | Secure destruction |

_Add or split categories to match the client's actual records. Keep the four core separations intact._

## Access-control model

- **Least-privilege by default** — access is granted by role and need-to-know, not by seniority.
- **Managers** see role-relevant personnel data only; **never** the medical, payroll, or work-authorization files.
- **Medical, payroll, and work-authorization files** are restricted to specifically authorized roles.
- **Employees** generally have a right to access their own records — **the scope and process are jurisdiction-specific; verify**.
- Document who holds each access right so the model is applied evenly and can be audited.

## Change-tracking (accuracy)

Records must stay accurate. When any record changes, log it:

| Date | Record / employee (ref) | Field changed | From → To | Authorized by | Source (e.g. HRIS sync, form) |
|---|---|---|---|---|---|
| | | | | | |

_Never alter a record without an authorization trail. A stale record (wrong pay, wrong emergency contact) causes real harm._

## Data-subject-access note (privacy-law-flagged)

Many jurisdictions grant employees rights over their personal data — to **access**, and sometimes to **correct** or restrict processing. Handling of such a request (scope, timeline, what must be provided or withheld, how medical/third-party data is treated) is **jurisdiction- and privacy-law-specific — verify with counsel before responding**. Do not assert a right, a timeline, or an exemption as fact. Record any request and its handling in the confidential zone. Never transmit the responsive records outside the project.

## Disposal

- Dispose only **after** the verified retention period, and only via **secure destruction** (shredding for paper; secure deletion for digital).
- Suspend disposal for any record under a **legal hold** (litigation, audit, or investigation) — **verify with counsel**.
- Log disposals (what category, when, by whom) so the retention schedule is demonstrably followed.
