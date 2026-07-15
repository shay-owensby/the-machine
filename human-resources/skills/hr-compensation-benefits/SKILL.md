---
name: hr-compensation-benefits
description: Build and maintain a company's pay program and benefits communications — comp philosophy, job leveling/architecture, salary bands from real market data, bonus/incentive and equity structures, offer modeling, internal pay-equity review, and total-rewards/benefits summaries. Use when the client wants to design or audit pay bands, model an offer, run a pay-equity scan, structure incentives, or summarize the benefits the company actually offers.
---

# HR Compensation & Benefits

Turns a company's pay philosophy into a defensible, transparent, and equitable pay program — and communicates the full value of an offer or an employee's total rewards. This skill owns HR function #3 and exports to `compensation-benefits/`; benchmarking and pay-equity reports may **also** land in `reports/analytics/` (see the folder map). It splits into two halves — **(A) Compensation** and **(B) Benefits** — that share the same safety rules.

## Setup gate (run first)

Enforce the config gate before any work, per `${CLAUDE_PLUGIN_ROOT}/skills/hr-config/SKILL.md`: look for `human-resources/config.yaml` at project root, require `version: 1` and `setup.completed: true`. If missing or invalid, STOP and tell the user exactly:
> Human resources isn't configured for this project yet. Run `/setup-human-resources` first.

Then load context: `company.about_file` (what the company does — grounds which roles and benefits are plausible), `company.soul_file` (voice for employee-facing rewards comms), `company.design_file` (branded document look), `company.name`, `company.size`, `company.locations` (drive geographic pay differentials and which minimum-wage/overtime rules apply), `company.employment_types`, `company.remote_policy`, and `legal.jurisdictions`. Honor degraded modes (null brand file → neutral, plain-language voice + warn once; empty `legal.jurisdictions` → no jurisdiction-specific pay-law claims, general best-practice only + flag for localization).

## Two standing safety rules (apply to everything below)

1. **Drafts, not legal advice — and never fabricated numbers.** Comp structures, offer models, and pay-equity analyses are drafts for review by the client's qualified HR professional and/or employment counsel. Pay-equity, pay-transparency (range-in-posting), minimum-wage, and overtime/exempt-classification rules are **jurisdiction-specific** — scope every such claim to `legal.jurisdictions`, name the jurisdiction ("Under California law…"), and flag "verify with counsel". **Never fabricate market salary data, benefit plan details, or a legal threshold.** If the user hasn't supplied market data, say so and require a real source (a named salary survey, an offer sheet, HRIS export) — do not invent numbers, ranges, or percentiles. When `legal.counsel_review: true`, stamp comp structures and pay-equity analyses with "⚠️ Draft — requires review by qualified HR/legal counsel before use".
2. **Confidential by default.** Individual pay data (salaries, bonuses, equity grants, offer amounts, and anything that maps a number to a named person) is highly sensitive PII. Keep it **in-project** under `compensation-benefits/` and, for identifiable per-employee equity/pay-equity records, the confidential zone (`confidentiality.records_dir` → `reports/employee-reports/`). Never paste individual pay data into an external service, web search, or MCP call. Warn if you spot pay PII in a tracked (non-gitignored) file. Never invent employee comp data — placeholder or supplied data only.

## A. Compensation — operating method

1. **Comp philosophy.** Establish (or read back) the company's stated pay philosophy: target market position (e.g. "pay at the 50th percentile"), which markets it competes in, how it balances internal equity vs. external competitiveness, and how pay, bonus, and equity mix. This is a policy the client owns — capture their intent; don't invent a posture they haven't chosen.
2. **Job leveling / architecture.** Define a leveling framework: job families, a consistent level ladder (e.g. IC and manager tracks), and level descriptors (scope, complexity, autonomy, impact) so roles map to levels consistently. Consistent leveling is what makes bands and equity checks defensible. See `references/pay-band-framework.md`.
3. **Salary bands from market data.** Build bands per level/family using `references/pay-band-framework.md`: choose a **real** market-data source (a named salary survey or supplied benchmark — never a guess), set range min / midpoint / max and range spread, and compute compa-ratio and band overlap. Apply geographic differentials from `company.locations` / `company.remote_policy`. **If no market data is supplied, stop and ask for a real source — do not populate a band with invented numbers.**
4. **Bonus / incentive & equity structures.** Frame variable-pay plans (annual bonus target %, sales commission/quota logic, spot awards) and equity structures (grant type, vesting schedule, refresh philosophy) as **methodology and structure**, populated only from figures the company supplies. Do not fabricate grant sizes, strike prices, or valuations.
5. **Offer modeling.** Model an offer for a specific role/level against the band: base within range (report the compa-ratio), variable target, equity, and the resulting total. Check internal equity against peers at the same level (using supplied peer data only), and flag whether pay-range-in-posting / salary-history rules apply for the role's jurisdiction. Hand the final number to recruitment (`recruitment/`) for the offer letter — the letter is theirs; the number is yours.
6. **Internal pay-equity review.** On **supplied** compensation data, run an internal equity check per `references/pay-band-framework.md`: compare pay for comparable work across groups, surface unexplained gaps after controlling for legitimate factors (level, location, tenure, performance), and recommend remediation. Pay-equity obligations and protected classes are **jurisdiction-specific** — scope to `legal.jurisdictions`, flag for counsel, and stamp the counsel-review banner when `legal.counsel_review: true`. Pay-equity outputs may also go to `reports/analytics/`. Note the DEI overlap: pay-equity analyses also feed `diversity-equity-inclusion/`.
7. **Pay transparency in postings.** Where a role's jurisdiction requires (or the client chooses) a posted pay range, supply the band range to recruitment and flag it as jurisdiction-specific to verify — this is the hand-off point to `recruitment/` pay-transparency work.

## B. Benefits — operating method

1. **Inventory what the company actually offers.** Summarize benefits **only** from what the company genuinely provides (from `company.about_file` or figures/plan docs the client supplies): health/medical/dental/vision, retirement (plan type, match), PTO/leave (vacation, sick, parental, other), and other perks (stipends, wellness, remote/equipment allowances). **Never invent plan specifics** — carrier names, coverage tiers, deductibles, match percentages, accrual rates. If a detail isn't supplied, mark it a placeholder and request the source document.
2. **Benefits summary / total rewards.** Produce a plain-language benefits summary and, per employee or offer, a total-rewards statement using `references/total-rewards-template.md`: base + variable + equity + employer-paid benefits value + PTO value + perks. Every figure comes from company-supplied data.
3. **Open-enrollment communication.** Draft clear, deadline-anchored open-enrollment comms in `company.soul_file` voice: what's changing, the windows, how to enroll, and where to get help. State only the plan facts the company supplies; do not assert costs, coverage, or dates you can't confirm.
4. **Vendor management notes.** Keep methodology notes for managing benefits vendors/brokers (renewal timelines, what to review, questions to ask) — a framework, not fabricated plan or pricing detail.

## Classification & wage law — cross-reference compliance

Exempt/non-exempt classification and minimum-wage / overtime rules determine legal pay floors and eligibility, and they are jurisdiction-specific. This skill uses classification as an **input** to comp and offer work but does **not** own the legal determination — **cross-reference `legal-compliance/`** for the classification analysis and statutory thresholds. Never assert an exemption status, minimum wage, or overtime threshold as settled fact; scope it to `legal.jurisdictions` and route to compliance/counsel.

## When to use each reference

- **`references/pay-band-framework.md`** — building or maintaining pay bands (job leveling, choosing a real market-data source, min/mid/max and range spread, compa-ratio, band overlap, geographic differentials) and running an internal pay-equity check. Holds the table templates with clearly-marked example numbers.
- **`references/total-rewards-template.md`** — producing a benefits summary or an individual total-rewards statement (base, variable, equity, benefits value, PTO, perks) from company-supplied figures only.

## Agents this skill drives

- **hr-comp-analyst** — given supplied market data + a role/level, designs or reviews pay bands, models an offer against a band, and/or runs an internal pay-equity scan on supplied compensation data. Refuses to fabricate market or benefit numbers; flags jurisdiction-specific pay-equity/transparency obligations for counsel. Writes to `compensation-benefits/`; benchmarking/equity summaries also to `reports/analytics/`.

## Boundaries

- Export only to `compensation-benefits/`; benchmarking and pay-equity reports may **also** go to `reports/analytics/`. Identifiable per-employee pay/equity records live in the confidential zone. Never invent new top-level folders.
- Never fabricate market salary data, benefit plan details, or legal thresholds — require a real source. Offer letters and the classification/wage-law determination belong to recruitment and legal-compliance respectively. All pay claims that touch law are jurisdiction-scoped and flagged, never asserted as settled. Individual pay data stays in-project.
