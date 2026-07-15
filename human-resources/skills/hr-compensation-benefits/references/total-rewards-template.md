# Total Rewards & Benefits Summary Template

Two related templates: a **benefits summary** (the program, plan-agnostic) and an **individual total-rewards statement** (one person's full package). Both are populated **only from figures the company actually supplies** — plan documents, an offer sheet, an HRIS export, or the client's stated benefits. Fill every `<placeholder>`; delete guidance in _italics_.

> ⚠️ **Never invent plan specifics or dollar values.** Do not fabricate carrier names, coverage tiers, deductibles, premiums, match percentages, PTO accrual rates, or the dollar value of any benefit. If a figure isn't supplied, leave the placeholder and note "**source needed**" — then ask the client for the plan doc or number. Employer-cost figures for benefits must come from the client's actual costs, not estimates you make up. Ground employee-facing tone in `company.soul_file`; if it's null, use a neutral, plain-language voice and warn once. This is a draft for review, not a binding statement of benefits or compensation.

---

## Part 1 — Benefits summary (program-level)

_A plain-language overview of what the company offers. Include only categories the company genuinely provides; delete the rest rather than leaving an empty promise._

### Health & insurance
- **Medical:** `<plan name / tier — as supplied>` · employee cost share: `<as supplied>` — _source needed if blank._
- **Dental / Vision:** `<as supplied>`
- **Life / disability / other:** `<as supplied>`

### Retirement
- **Plan type:** `<e.g. defined-contribution plan — as supplied>`
- **Employer contribution / match:** `<exact terms as supplied>` — _do not guess a match formula._

### Time off & leave
- **Vacation / PTO:** `<policy as supplied>`
- **Sick leave:** `<as supplied — note this is often jurisdiction-mandated; verify against legal.jurisdictions>`
- **Parental / family leave:** `<as supplied — entitlements vary by jurisdiction; flag for compliance>`
- **Holidays:** `<count / list as supplied>`

### Other perks
- `<Stipends, wellness, learning budget, equipment/remote allowance, etc. — only those actually offered>`

> Leave entitlements (sick, family, parental) and their minimums are frequently **jurisdiction-mandated**. Where a figure is a legal minimum, scope it to `legal.jurisdictions` and flag for compliance/counsel — do not assert a statutory entitlement you can't confirm.

---

## Part 2 — Individual total-rewards statement

_One employee's (or one offer's) complete package. Every figure is supplied or explicitly a placeholder. This is confidential PII — keep it in-project._

**Prepared for:** `<employee name / "Offer — <role>">` · **Level:** `<level>` · **As of:** `<date>`

| Component | Value _(company-supplied)_ | Notes |
|---|---|---|
| **Base salary** | `<$ base>` | Compa-ratio: `<actual ÷ band midpoint>` |
| **Variable / bonus** | `<$ at target — and target %>` | `<plan basis — as supplied>` |
| **Equity** | `<grant value / units — as supplied>` | `<vesting terms — as supplied; do not fabricate a valuation>` |
| **Retirement (employer)** | `<$ employer contribution>` | `<match terms>` |
| **Health & insurance (employer cost)** | `<$ employer-paid premium>` | **source needed** if blank — use real employer cost, not an estimate |
| **PTO value** | `<$ = days × daily base>` | `<days>` days |
| **Other perks** | `<$ stipends / allowances>` | `<itemize>` |
| **Total rewards** | `<Σ of supplied components>` | Sum only the components you actually have |

_Value figures shown as `<$…>` are placeholders — replace only with company-supplied numbers, and never sum in an invented value to reach a rounder total._

### How to present it
- Lead with base and the headline total, then break down the components so the employee sees the full value beyond salary.
- Distinguish **cash** (base, bonus) from **non-cash value** (employer benefit cost, equity, PTO value) honestly — don't overstate the total by blending them without labels.
- Use `company.soul_file` voice; keep it warm, clear, and accurate.

## Reminders
- Every value traces to a supplied source; any blank is "**source needed**", never a guess.
- Jurisdiction-mandated leave/benefit minimums are flagged for compliance, not asserted.
- Individual statements are confidential PII → keep in-project; identifiable per-employee statements belong in the confidential zone (`reports/employee-reports/`), program-level summaries in `compensation-benefits/`.
