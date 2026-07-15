# Standalone Policy Template

A reusable structure for any single workplace policy (PTO, remote work, acceptable use, code of conduct, expense, etc.). Fill every `<placeholder>`; delete guidance in _italics_. Ground the policy in the company's **actual** practices (`company.about_file` + what the user states) and its voice (`company.soul_file`). Do not invent a practice, threshold, or entitlement — where one is needed and unknown, ask the user.

---

## Structure

**Policy title:** `<Descriptive name, e.g. "Paid Time Off Policy">`
**Policy owner:** `<role, e.g. HR Manager — from defaults.approver>`  ·  **Applies to:** `<which employees / employment types>`
**Version:** `<vX.Y>`  ·  **Effective date:** `<YYYY-MM-DD>`  ·  **Next review:** `<YYYY-MM-DD>`

> ⚠️ **Draft — requires review by qualified HR/legal counsel before use.** _(Include this banner when `legal.counsel_review: true`.)_

### 1. Purpose
_One short paragraph: why this policy exists and what it's meant to achieve. Plain language._

### 2. Scope
_Who and what it covers — employment types, locations, systems, situations — and any explicit exclusions. Be precise; scope ambiguity causes uneven enforcement._

### 3. Policy statement
_The rule itself, stated clearly and directly. What is expected, permitted, or prohibited. Specific and enforceable (measurable where possible), but not so rigid it can't reasonably apply. This is the heart of the policy — keep it readable._

### 4. Procedure
_The steps: how an employee complies, requests, reports, or is affected — who does what, in what order, by when, through what channel. Number the steps. If forms or systems are involved, name them._

### 5. Roles & responsibilities
- **Employee:** `<what they must do>`
- **Manager / supervisor:** `<their role — apply the policy consistently to everyone>`
- **HR / policy owner:** `<administration, records, exceptions>`
_Assign responsibility so the policy is actually operated and applied evenly._

### 6. Definitions
_Define every term that could be read more than one way (e.g. "immediate family", "business day", "accrual", "misconduct"). Undefined terms are where inconsistent enforcement starts._

### 7. Effective / review date & version history
_Effective date, review cadence, and a short version log: what changed, when, and why. Preserve prior versions; re-issue for acknowledgment when a change is material._

### 8. Related policies
_Cross-reference policies this one touches so they stay consistent (e.g. a PTO policy links the Leave policy and the Attendance policy). Reconcile any overlap before publishing — no contradictions._

### 9. Jurisdiction & legal flags
_List any clause that depends on employment law, name the jurisdiction from `legal.jurisdictions` it's scoped to, and mark it "verify with counsel". If `legal.jurisdictions` is empty, mark the whole policy as needing localization. Never state a statute, threshold, or entitlement as fact here — flag it for verification._

### 10. Acknowledgment
_Use the block below. The blank form ships with the policy; the signed copy is a confidential record filed under `reports/employee-reports/`, not in `policies/`._

---

## Acknowledgment block

```
ACKNOWLEDGMENT — <Policy title> (Version <vX.Y>, Effective <YYYY-MM-DD>)

I acknowledge that I have received, read, and understand the <Policy title>.
I understand it is my responsibility to comply with it, and that I may ask
<policy owner / HR> if I have any questions. I understand this policy does not
create an employment contract or alter the at-will nature of my employment
(where applicable).

Employee name (print): ____________________________________

Employee signature: _______________________________________

Date: ____________________

<Company name>  ·  <optional document footer>
```

---

## Drafting style guide

Every policy must be **clear, enforceable, non-discriminatory, and consistent**.

**Clear**
- Plain language, short sentences, active voice. Write for the employee who has to follow it, not for a lawyer.
- Define terms; expand acronyms on first use. If a sentence needs re-reading, rewrite it.
- Match `company.soul_file` voice, but never at the cost of clarity.

**Enforceable**
- State who, what, when, and the consequence of non-compliance. Vague rules ("act professionally") can't be enforced fairly — anchor them with examples or standards.
- Avoid promises the company can't keep or doesn't mean (guaranteed outcomes, fixed discipline steps that undercut at-will where it applies).
- Prefer specific, observable standards over discretion; where discretion is unavoidable, bound it and say who exercises it.

**Non-discriminatory**
- Neutral criteria applied to everyone; no language that targets or codes for a protected class.
- Ensure the rule and any accommodation path comply with equal-opportunity obligations — flag jurisdiction-specific accommodation clauses for counsel.
- Don't copy statutory or EEO wording from memory; use the client's approved, counsel-verified text.

**Consistent**
- **Internally:** no clause may contradict another policy — reconcile overlaps (Related policies section).
- **In enforcement:** write the policy so it can be, and is, applied evenly to every employee in scope. Inconsistent enforcement is a top source of legal exposure — the text and the rollout should both push toward uniform application.

## Reminders
- Every policy is a draft for HR/legal review, not legal advice. Never assert it is legally required or legally sufficient.
- Ground it in the company's real practice; where the practice is unknown, ask — don't invent.
- Save the drafted policy to `policies/`. Version it in front matter (or a `-v2` filename suffix when iterating).
