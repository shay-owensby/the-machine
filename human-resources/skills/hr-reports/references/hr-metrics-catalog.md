# HR Metrics Catalog

Precise definitions and formulas for the core HR metrics, so every report computes them the same way and states them honestly. This is a **definitions reference, not data** — no figure here is real. Compute every metric **only from supplied data**, over a stated period, and label the source. Where a metric is cut by group, apply the **minimum-cell-size suppression** (commonly n < 5) from the hr-reports skill — small cuts re-identify people.

> ⚠️ Never fabricate or estimate a metric value; if the inputs aren't supplied, report the gap. Benchmarks appear only from a named source the user supplies — never an invented "industry average". Metrics that touch statutory obligation (e.g. leave, classification) are jurisdiction-specific and for HR/counsel to verify. Reports are drafts for HR review.

## Conventions used below

- **Average headcount** over a period = (headcount at start + headcount at end) ÷ 2 (or the mean of monthly headcounts for more accuracy) — the standard denominator for rate metrics; state which you used.
- **Period** — always state it (month, quarter, rolling 12 months). Annualize a partial-period rate only with an explicit, stated method.
- **Traceability** — show the inputs behind each headline number so a reader can reproduce it.

---

## 1. Headcount & FTE

- **Headcount** = count of employees at a point in time (a *count of people*, regardless of hours). State the "as of" date and whether contractors are included.
- **FTE (full-time equivalent)** = Σ (each employee's scheduled hours ÷ full-time hours). A 20-hour employee at a 40-hour standard = 0.5 FTE.
- **Inputs:** roster with employment type and scheduled hours; the full-time-hours standard.
- **Interpretation:** headcount tracks *people* (for culture, coverage); FTE tracks *capacity/cost*. Report both when part-time is material. Reconcile the total against `company.size`.

## 2. Turnover / attrition (voluntary & involuntary)

- **Turnover rate** = (separations in period ÷ average headcount) × 100.
- **Voluntary turnover** = resignations initiated by the employee ÷ average headcount.
- **Involuntary turnover** = employer-initiated exits (termination, layoff) ÷ average headcount.
- Optionally split **regretted vs. non-regretted** voluntary (was the exit a loss?).
- **Inputs:** separations by reason and date; average headcount for the period.
- **Interpretation:** always separate voluntary from involuntary — they mean opposite things. High *voluntary regretted* turnover is a retention/inclusion signal; involuntary spikes may reflect restructuring (route to `strategy/`). Small bases move percentages wildly — report the raw count too.

## 3. Retention rate

- **Retention rate** = (employees present at both start and end of period ÷ employees at start) × 100. Counts only those who *stayed the whole period* (new hires within the period are excluded from the numerator base).
- **Inputs:** start-of-period roster; who from it remained at end.
- **Interpretation:** retention and turnover are related but not simple complements (retention fixes a starting cohort; turnover uses average headcount and counts all leavers). Report cohort/first-year retention separately when onboarding quality is the question.

## 4. Time-to-fill & time-to-hire

- **Time-to-fill** = days from **requisition opened** to **offer accepted** (the business's view: how long a vacancy is open).
- **Time-to-hire** = days from **candidate entered the pipeline** (applied/sourced) to **offer accepted** (the candidate's view: process speed).
- Report as **median** (robust to outliers) alongside the mean.
- **Inputs:** req open dates; application/source dates; offer-accept dates.
- **Interpretation:** the two answer different questions — distinguish them. Long time-to-fill feeds the workforce plan's lead-time assumptions (`strategy/`).

## 5. Cost-per-hire

- **Cost-per-hire** = (total internal recruiting costs + total external recruiting costs) ÷ number of hires in the period.
- Typical components: advertising/job boards, agency fees, referral bonuses, recruiter time, tooling, relocation.
- **Inputs:** itemized recruiting spend for the period; hire count. Compute only from supplied costs — never estimate.
- **Interpretation:** state exactly which cost components are included (definitions vary widely, so cross-company comparison is unreliable without matching scope).

## 6. Offer-acceptance rate

- **Offer-acceptance rate** = (offers accepted ÷ offers extended) × 100.
- **Inputs:** offers extended and accepted in the period.
- **Interpretation:** low acceptance points at compensation, candidate experience, or speed. Pair with time-to-hire and (via `compensation-benefits/`) offer competitiveness.

## 7. Absenteeism rate

- **Absenteeism rate** = (unscheduled absence days ÷ available workdays in period) × 100.
- **Inputs:** unscheduled absence days (exclude approved planned leave/PTO unless defining a total-absence metric — state which); scheduled workdays × headcount.
- **Interpretation:** define whether planned leave is included; note statutory/protected leave is **jurisdiction-specific** and must not be conflated with discretionary absence — flag for HR/counsel.

## 8. Internal mobility & promotion rate

- **Internal mobility rate** = (internal moves — promotions + lateral transfers — in period ÷ average headcount) × 100.
- **Promotion rate** = (promotions in period ÷ average headcount) × 100.
- **Internal fill rate** = (roles filled internally ÷ total roles filled) × 100.
- **Inputs:** internal move records tagged promotion vs. lateral; hires by source (internal/external).
- **Interpretation:** healthy internal mobility supports the "build" play in workforce planning (`strategy/`) and is a development-program signal (`training-development/`). Check promotion rates across groups for equity (aggregated) — feeds `diversity-equity-inclusion/`.

## 9. Span of control

- **Span of control** = direct reports ÷ manager, reported as an **average** across managers and by layer.
- **Inputs:** reporting relationships (manager → reports).
- **Interpretation:** a diagnostic for `strategy/` org design — very low spans (esp. "manager of one") suggest excess layers; very high spans suggest overloaded managers. It's a computed diagnostic, not a target.

## 10. DEI representation

- **Representation %** = (headcount in group ÷ total headcount) × 100, reported by level, function, and lifecycle stage (applicant → hire → promote → exit).
- **Inputs:** aggregated demographic counts from HRIS/ATS (supplied), by cut.
- **Interpretation:** **aggregate only; suppress any cell below the minimum size** — a small group is re-identifying. Use stage-by-stage representation to locate where representation drops. Feeds `diversity-equity-inclusion/`. Never present a target percentage as a quota — that's a legality matter for counsel.

## 11. Compa-ratio & pay-equity ratio

- **Compa-ratio** = actual base pay ÷ band midpoint (1.00 = paid at midpoint). Report as an average per band/group.
- **Pay-equity ratio** = median (or mean) pay of one group ÷ that of the reference group, for **comparable work**, ideally after controlling for legitimate factors (level, location, tenure, performance).
- **Inputs:** supplied pay data with band/level/group; the pay-equity method is owned by `compensation-benefits/` (`references/pay-band-framework.md`).
- **Interpretation:** a **raw** ratio is a prompt to investigate, not proof of discrimination. Pay-equity law is **jurisdiction-specific** — scope to `legal.jurisdictions`, flag for counsel, keep individual pay confidential.

## 12. Training completion

- **Training completion rate** = (learners who completed ÷ learners assigned) × 100, per course/curriculum.
- **Inputs:** assigned vs. completed counts (from LMS or supplied records).
- **Interpretation:** completion measures *coverage*, not *learning* — pair with assessment/behavior outcomes from `training-development/` (Kirkpatrick levels). For mandatory/compliance training, cadence and recordkeeping are jurisdiction-specific (`legal-compliance/`).

## 13. eNPS / engagement

- **eNPS (employee Net Promoter Score)** = % promoters (9–10) − % detractors (0–6), from the "how likely to recommend as a place to work" item. Ranges −100 to +100.
- **Engagement / inclusion score** = mean or favorable-% of the survey's engagement/inclusion items.
- **Inputs:** survey responses; response count (report the response rate).
- **Interpretation:** report the **response rate** — a low rate biases the score. **Cut by group only where the group is large enough** to protect anonymity (a small team's scores can expose individuals). Trend over time matters more than a single reading.

## Reminders

- Every value is computed from supplied data over a stated period, with its inputs shown; missing inputs → report the gap, never a guess.
- Aggregate; suppress groups below the minimum cell size. No names, IDs, or per-person rows in an analytics report.
- Metrics touching statute (leave, classification, pay-equity) are jurisdiction-specific and for HR/counsel to verify. Reports are drafts for HR review.
