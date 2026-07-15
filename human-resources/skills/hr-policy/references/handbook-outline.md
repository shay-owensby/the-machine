# Employee Handbook — Standard Outline

A standard table of contents for an employee handbook, annotated with whether each section is **commonly legally-required (verify)** or **recommended**, and cross-referenced to the HR function folder that owns the underlying detail. Use it as the needs-assessment checklist: for the company in hand, keep what applies, drop what doesn't, and add industry-specific sections.

**How to read the annotations**
- **Legally-required (verify)** = commonly mandated *for some employers* — the requirement, and its trigger, depend on `company.size`, `legal.jurisdictions`, and industry. Treat every one as *needs counsel confirmation*, never as settled fact. Requirements and thresholds vary widely by location.
- **Recommended** = strong best practice that reduces risk and confusion even where not mandated.
- Nothing here asserts a specific law. Do not copy statutory wording from memory; source approved, counsel-verified text from the client.

---

## Front matter

### 1. Welcome & introduction — *recommended*
Brief welcome in `company.soul_file` voice; what the handbook is and isn't. State that the handbook is a set of guidelines, **not an employment contract**, and that it may be updated.

### 2. At-will employment statement — *legally-sensitive (verify); jurisdiction-specific*
Where at-will applies, a clear at-will disclaimer (employment may end by either party, with/without cause) and a statement that no manager can alter at-will status except in writing by an authorized officer. At-will doctrine and its exceptions vary by jurisdiction and may not apply everywhere — **verify with counsel**; do not assert at-will as universal.

### 3. Purpose, scope & revision note — *recommended*
Who the handbook covers (employment types from `company.employment_types`), how updates are communicated, and the current version/effective date (version control).

---

## Conduct & equal opportunity

### 4. Equal Employment Opportunity (EEO) — *legally-required (verify) for many employers*
Commitment to equal opportunity and non-discrimination. The protected categories and exact required wording are jurisdiction-specific — source approved text; verify with counsel. → cross-refs `diversity-equity-inclusion/` and `legal-compliance/`.

### 5. Anti-harassment & anti-retaliation — *legally-required (verify) for many employers*
Prohibited conduct, examples, multiple reporting channels, investigation commitment, and a no-retaliation guarantee. Some jurisdictions also mandate training at certain headcounts — flag against `company.size`. → cross-refs `employee-relations/` (investigations) and `legal-compliance/`.

### 6. Code of conduct — *recommended*
Expected professional behavior, conflicts of interest, confidentiality of company/customer information, attendance, and general standards. Ground in the company's actual expectations, not a generic list.

---

## Wage, hour & time

### 7. Employment classifications — *legally-sensitive (verify)*
Definitions of the classes the company uses (full-time, part-time, exempt/non-exempt, contractor) and what each means for benefits and overtime eligibility. Exempt/non-exempt tests are jurisdiction-specific — verify. → cross-refs `compensation-benefits/`.

### 8. Wage & hour / pay practices — *legally-required (verify)*
Pay periods and paydays, timekeeping, overtime rules, meal/rest breaks, and deductions. Overtime thresholds, break entitlements, and pay-frequency rules are **jurisdiction-specific and size-sensitive** — never state a threshold without scoping it to `legal.jurisdictions` and flagging for counsel. → cross-refs `compensation-benefits/` and `legal-compliance/`.

### 9. Paid time off (PTO / vacation / sick) — *partly legally-required (verify)*
The company's actual PTO/vacation practice (accrual, carryover, payout) plus any mandated paid-sick-leave. Paid-sick-leave mandates and vacation-payout-on-termination rules are jurisdiction-specific — verify; do not invent accrual rates, use the company's stated practice or ask. → cross-refs `scheduling/` (PTO calendar) and `legal-compliance/`.

### 10. Leaves of absence — *legally-required (verify), size- and jurisdiction-gated*
Job-protected and other leaves (family/medical, parental, disability/accommodation, jury, military, bereavement, voting). Eligibility and entitlement key hard off `company.size` and `legal.jurisdictions` — flag every threshold for counsel; never state a leave entitlement as fact without verification. → cross-refs `legal-compliance/` (statutory leave tracking) and `health-safety-wellness/` (accommodation/return-to-work).

---

## Benefits, work model & resources

### 11. Benefits summary (pointer) — *recommended*
A high-level summary only, with a pointer to the authoritative plan documents — the handbook must not restate benefit terms that the plan governs. Do not invent benefits. → owned by `compensation-benefits/`; direct readers to the summary plan descriptions there.

### 12. Remote / hybrid work — *recommended*
Eligibility, expectations, hours/availability, equipment, expense handling, and data security for remote/hybrid work. Align to `company.remote_policy`; keep consistent with the hours and acceptable-use policies. → cross-refs `health-safety-wellness/` (remote ergonomics/safety).

### 13. Technology & acceptable use — *recommended*
Acceptable use of company systems, devices, email, internet, and social media; monitoring expectations; data security and confidentiality; BYOD if applicable. Monitoring-disclosure rules vary by jurisdiction — flag. → cross-refs `legal-compliance/`.

### 14. Health, safety & workplace security — *legally-required (verify) for many employers*
Safety commitment, incident/injury reporting, emergency procedures, and any industry-specific safety obligations. Specific safety obligations and posting/reporting rules are jurisdiction- and industry-specific — verify. → owned by `health-safety-wellness/`; cross-refs `legal-compliance/`.

---

## Enforcement & acknowledgment

### 15. Disciplinary & corrective action — *recommended*
The company's actual approach to performance and conduct problems (e.g. a progressive-discipline framework) written to be applied **consistently to everyone**. Preserve at-will where applicable (do not imply discipline steps are guaranteed). Uneven enforcement is a legal-risk theme — emphasize even application. → cross-refs `employee-relations/`.

### 16. Grievance / complaint & open-door — *recommended*
How employees raise concerns, the escalation path, multiple channels, and the anti-retaliation guarantee restated. → cross-refs `employee-relations/`.

### 17. Handbook acknowledgment — *strongly recommended (enforcement record)*
A signed acknowledgment that the employee received, read, and understands the handbook, and understands it is not a contract and does not alter at-will status. Use the acknowledgment block from `policy-template.md`. The **signed** acknowledgment is a confidential record → filed under `reports/employee-reports/`, not in `policies/`.

---

## Assembly notes

- **Order matters for enforceability:** the at-will disclaimer, the "not a contract" statement, and the acknowledgment should bracket the handbook (front and back) so nothing in between reads as a promise.
- **Only include what the company actually does.** A handbook that describes benefits, leaves, or discipline steps the company hasn't adopted creates obligations and contradictions. Where a needed section has no stated practice, ask the user — don't invent it.
- **Keep it internally consistent.** PTO ↔ leave, remote ↔ hours, discipline ↔ at-will, benefits summary ↔ plan documents: reconcile before assembly.
- **Stamp for review.** When `legal.counsel_review: true`, the assembled handbook carries "⚠️ Draft — requires review by qualified HR/legal counsel before use". The handbook is never asserted to be legally sufficient.
