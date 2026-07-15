# Employment Compliance Checklist — Framework

A domain-organized checklist/tracker **framework** for supporting a client's employment-law compliance. It is deliberately **jurisdiction-agnostic**: the items describe *categories of obligation* that commonly exist, with placeholders to fill from `legal.jurisdictions`, `company.size`, and `company.industry` — and from the **authoritative labor agency** for each jurisdiction. Nothing here states a threshold, deadline, dollar figure, or citation as fact; those are filled in at run time and always flagged for verification.

## How to use

1. Confirm scope from config: `legal.jurisdictions`, `company.size`, `company.industry`, `company.employment_types`, `company.remote_policy`, `company.union`. If `legal.jurisdictions` is empty, use these as general best-practice prompts only, labeled "must be localized and verified with counsel".
2. For each domain below, instantiate the rows that apply given scope. Fill the placeholders. For every jurisdiction- or threshold-dependent item, keep the **verify-source** populated and mark it "verify against current `<jurisdiction>` rule".
3. Track status over time; record a **last-verified date** on each item. A living, dated tracker is what demonstrates good-faith diligence.
4. Never assert an obligation exists at a specific number — say it is triggered by size/jurisdiction/industry and must be confirmed with the named authority.

## Column definitions

| Column | What goes in it |
|---|---|
| **Item** | The obligation, framed generically (no fabricated statute name or number). |
| **Applies-when (trigger)** | The condition that brings it into scope: jurisdiction(s) from `legal.jurisdictions`, a size threshold (stated as size-triggered, *threshold to verify*), an industry factor, or an employment-type factor. |
| **Status** | `Compliant (evidenced)` / `Gap` / `In progress` / `N/A` / `Unknown — verify`. Never mark `Compliant` without the evidence in the next column. |
| **Evidence / document** | The artifact that would prove it: signed policy, posted notice, retained record, training roster, filed form. Where it lives in-project. |
| **Verify-source** | The **authoritative source** to confirm the rule and its current specifics — the government labor/employment agency for that jurisdiction, its official posting page, its recordkeeping guidance. Populate this for every jurisdiction-specific row. |
| **Risk-if-missing** | Consequence of the gap, at a high level (e.g. penalty exposure, individual liability, invalidated action) — and a severity note. Flag counsel-escalation items. |

> ⚠️ **Draft — requires review by qualified HR/legal counsel before use.** Stamp this on any instantiated tracker (always when `legal.counsel_review: true`).

## Domain 1 — Hiring & EEO

| Item | Applies-when (trigger) | Status | Evidence / document | Verify-source | Risk-if-missing |
|---|---|---|---|---|---|
| Equal-opportunity / non-discrimination obligations in hiring | Jurisdiction(s) `<from legal.jurisdictions>`; some duties size-triggered *(threshold to verify)* | | EEO policy; job-posting EEO statement | `<jurisdiction labor / fair-employment agency>` | |
| Background-check / criminal-history inquiry limits (e.g. ban-the-box, timing, individualized assessment) | Jurisdiction-specific *(verify)* | | Documented screening procedure & consent | `<jurisdiction agency>` | |
| Salary-history inquiry limits | Jurisdiction-specific *(verify)* | | Interview guidelines | `<jurisdiction agency>` | |
| Pay-range-in-posting (pay transparency) | Jurisdiction-specific *(verify)* | | Postings showing range | `<jurisdiction agency>` | |
| Work-authorization / employment-eligibility verification | Jurisdiction-specific *(verify form & timing)* | | Completed verification records (confidential zone) | `<national/jurisdiction authority>` | Invalid hire / penalty |
| Required applicant/new-hire notices | Jurisdiction-specific *(verify)* | | Notice acknowledgments | `<jurisdiction agency>` | |

## Domain 2 — Wage & Hour / Classification (exempt vs. non-exempt)

| Item | Applies-when (trigger) | Status | Evidence / document | Verify-source | Risk-if-missing |
|---|---|---|---|---|---|
| Minimum-wage compliance | Jurisdiction-specific rate *(never state the rate — verify)* | | Payroll records | `<jurisdiction wage authority>` | Back-pay + penalties |
| Overtime eligibility & rate | Jurisdiction-specific *(verify multiplier & thresholds)* | | Time & payroll records | `<jurisdiction wage authority>` | Back-pay + penalties |
| Exempt vs. non-exempt classification (duties + salary tests) | Per role; jurisdiction-specific tests *(verify)* | | Classification worksheet per role | `<jurisdiction wage authority>` | Misclassification liability — **escalate to counsel** |
| Meal / rest break rules | Jurisdiction-specific *(verify)* | | Break policy & records | `<jurisdiction wage authority>` | |
| Pay frequency & pay-statement content | Jurisdiction-specific *(verify)* | | Sample pay statements | `<jurisdiction wage authority>` | |
| Final-pay timing on separation | Jurisdiction-specific *(verify)* | | Offboarding pay checklist (coord. `offboarding/`) | `<jurisdiction wage authority>` | Penalty exposure |

## Domain 3 — Leave & Accommodation

| Item | Applies-when (trigger) | Status | Evidence / document | Verify-source | Risk-if-missing |
|---|---|---|---|---|---|
| Family / medical leave entitlement | Size- and jurisdiction-gated *(verify threshold & duration)* | | Leave policy | `<jurisdiction labor agency>` | |
| Paid sick leave | Jurisdiction-specific *(verify accrual/caps)* | | Sick-leave policy & accrual records | `<jurisdiction agency>` | |
| Disability / pregnancy accommodation & interactive process | Jurisdiction-specific; size-triggered *(verify)* | | Accommodation procedure; case records (confidential) | `<jurisdiction fair-employment agency>` | Discrimination exposure — **escalate** |
| Other statutory leave (jury, voting, military, bereavement, domestic-violence, etc.) | Jurisdiction-specific *(verify which apply)* | | Leave policy | `<jurisdiction agency>` | |

## Domain 4 — Workplace Safety

| Item | Applies-when (trigger) | Status | Evidence / document | Verify-source | Risk-if-missing |
|---|---|---|---|---|---|
| General safe-workplace duty & written safety program | All employers; scope by `company.industry` | | Safety program (coord. `health-safety-wellness/`) | `<jurisdiction safety agency>` | |
| Injury / illness recordkeeping & reporting | Size- and industry-triggered *(verify threshold & deadlines)* | | Incident log; reports | `<jurisdiction safety agency>` | Penalty exposure |
| Industry-specific safety obligations | `company.industry` *(verify which apply)* | | Program docs, training | `<industry regulator / safety agency>` | |
| Required safety training | Jurisdiction / industry *(verify)* | | Training rosters | `<jurisdiction safety agency>` | |

## Domain 5 — Anti-Discrimination & Harassment

| Item | Applies-when (trigger) | Status | Evidence / document | Verify-source | Risk-if-missing |
|---|---|---|---|---|---|
| Anti-harassment / anti-discrimination policy | All employers; content jurisdiction-specific | | Policy in handbook (coord. `policies/`) | `<jurisdiction fair-employment agency>` | |
| Complaint & investigation procedure | All employers | | Documented procedure; case files (confidential, `employee-relations/`) | `<jurisdiction agency>` | |
| Mandatory anti-harassment training | Size- and jurisdiction-triggered *(verify cadence & threshold)* | | Training rosters & dates | `<jurisdiction agency>` | Penalty / defense weakened |

## Domain 6 — Required Workplace Postings

Track in `references/required-postings.md` (per jurisdiction and worksite, incl. remote workers). Summarize status here with a link to that tracker.

| Item | Applies-when (trigger) | Status | Evidence / document | Verify-source | Risk-if-missing |
|---|---|---|---|---|---|
| Mandatory notices/posters displayed at each worksite | Per jurisdiction & worksite *(verify current list)* | | Posting tracker; photos/records | `<jurisdiction labor agency posting page>` | Penalty exposure |
| Remote-worker notice distribution | Where remote employees present *(verify method accepted)* | | Distribution records | `<jurisdiction labor agency>` | |

## Domain 7 — Recordkeeping & Retention

| Item | Applies-when (trigger) | Status | Evidence / document | Verify-source | Risk-if-missing |
|---|---|---|---|---|---|
| Employment record inventory (personnel, payroll, tax, I-9-type, medical, leave, safety) | All employers; specifics jurisdiction-specific | | Record inventory & storage map | `<jurisdiction agency recordkeeping guidance>` | |
| Retention periods per record type | Jurisdiction- & type-specific *(never assert a period — verify)* | | Retention schedule | `<jurisdiction agency>` | Spoliation / penalty |
| Secure storage & segregation (medical/PII separate) | All employers; jurisdiction privacy rules | | Storage controls; `confidentiality.records_dir` layout | `<jurisdiction agency>` | Privacy exposure |

## Domain 8 — Worker Classification (Employee vs. Independent Contractor)

| Item | Applies-when (trigger) | Status | Evidence / document | Verify-source | Risk-if-missing |
|---|---|---|---|---|---|
| Contractor-vs-employee test applied per engagement | Any `contractor` in `company.employment_types`; jurisdiction- & agency-specific tests *(verify which test)* | | Classification worksheet per worker | `<jurisdiction labor & tax authorities>` | Misclassification liability — **escalate to counsel** |
| Contractor agreement & practices consistent with classification | Per engagement | | Signed agreements; actual-practice notes | `<jurisdiction agency>` | |

## Domain 9 — Privacy

| Item | Applies-when (trigger) | Status | Evidence / document | Verify-source | Risk-if-missing |
|---|---|---|---|---|---|
| Employee-data privacy notice & handling | Jurisdiction-specific *(verify)* | | Privacy notice; data map | `<jurisdiction data-protection authority>` | |
| Monitoring / surveillance consent | Jurisdiction-specific *(verify)* | | Consent records; policy | `<jurisdiction authority>` | |
| Biometric / health-data handling | Where collected; jurisdiction-specific *(verify)* | | Consent & storage controls | `<jurisdiction authority>` | High exposure — **escalate** |
| Breach-notification duties | Jurisdiction-specific *(verify triggers & deadlines)* | | Incident-response plan | `<jurisdiction authority>` | Penalty exposure |

## Reminders

- Instantiated trackers are **compliance-support drafts for counsel review**, not legal advice or a compliance guarantee.
- Fill placeholders from config + verified authoritative sources only. Never fabricate a statute, threshold, deadline, dollar figure, retention period, or filing requirement.
- Refuse jurisdictions not in `legal.jurisdictions`; flag any worksite/remote employee sitting outside the configured list.
- Save to `legal-compliance/`; identifiable records to `confidentiality.records_dir`.
