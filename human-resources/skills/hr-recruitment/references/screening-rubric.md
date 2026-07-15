# Structured Resume Screening Rubric

A consistent, evidence-based framework for screening a resume batch into a ranked shortlist. Apply it **identically to every candidate** in the batch — consistency is what makes screening fair, defensible, and useful. Screen against the criteria defined at intake, never against improvised preferences.

## Confidentiality & PII

Resumes are candidate PII. Keep them and all screening notes **in-project** under `recruitment/` (or `recruitment/<role-slug>/`). Never paste candidate names, contact details, or resume text into a web search, external service, or MCP call. Never invent candidates or resume content — score only what a supplied resume actually says. If asked to store or share these outside the project, warn first.

## Step 1 — Must-have gate (pass/fail)

List the intake **must-haves** (the genuinely disqualifying criteria only). For each candidate, mark each must-have `met` / `not met` / `unclear`, with the resume evidence quoted. Any `not met` on a true must-have → **screened out** at this gate; record why. If a must-have is `unclear`, don't reject on assumption — flag it as a question for a screen call rather than guessing.

Keep the gate honest: if most of the pool fails a "must-have", the criterion was probably a nice-to-have inflated at intake — surface that back to the hiring manager rather than shrinking the pool.

## Step 2 — Weighted scoring dimensions

Score only candidates who passed the gate. Define 4–6 dimensions from the intake criteria, assign a weight to each (weights sum to 100%), and score each dimension **0–5** with quoted evidence. Adapt the dimensions and weights to the role; a typical starting frame:

| Dimension | What it measures | Suggested weight |
|---|---|---|
| Core skills / technical fit | Demonstrated ability in the role's essential competencies | 30% |
| Relevant experience | Depth/relevance of work to this role's outcomes (relevance over raw tenure) | 25% |
| Scope & impact | Evidence of results, ownership, and outcomes achieved | 20% |
| Domain / industry knowledge | Familiarity with the field, tools, or context (if required) | 15% |
| Growth signal | Trajectory, learning, adaptability | 10% |

**Weighted score** = Σ(dimension score ÷ 5 × weight). Rank the passing candidates by weighted score.

Anchor the 0–5 scale so scoring is repeatable:
- **5** — strong, clearly evidenced fit; exceeds the bar.
- **3** — solid, meets the bar with evidence.
- **1** — weak or thin evidence.
- **0** — no evidence in the resume (score the absence, don't infer).

## Step 3 — Evidence-based notes

For every score, quote or cite the specific resume line that justifies it. No score without evidence. Where the resume is silent, score conservatively and note it as a screen-call question — do not fill gaps with assumptions. This evidence trail is what makes the shortlist defensible and useful to the hiring manager.

## Step 4 — Bias-avoidance rules (mandatory)

- **Judge job-related criteria only.** Ignore name, gender, age, ethnicity, photo, marital/family status, address, national origin, disability, and other protected characteristics — and their proxies (e.g. graduation year → age, some names/schools → ethnicity or class).
- **Don't penalize on proxies.** Employment gaps, non-linear paths, non-elite schools, or "culture fit" are not scoring criteria unless they map to a genuine, job-related requirement — and even then, verify in a screen rather than assume.
- **Same rubric, same weights, every candidate.** No mid-batch criteria changes. If you refine criteria, re-score the whole batch.
- **Skills over pedigree.** Prefer demonstrated competency to school/employer brand or raw years.
- **Flag legally risky screens.** Salary-history dependence, ban-the-box/criminal-record screens, unexplained-gap penalties, and adverse-impact-prone filters are **jurisdiction-specific** — flag them, scope to `legal.jurisdictions`, and route for counsel verification. Never present these as settled rules.

## Step 5 — Ranked shortlist output

Produce:
1. **Shortlist (advance):** ranked, each with weighted score, a 2–3 sentence evidence-based rationale, and specific things to probe in interview/screen.
2. **Maybe / hold:** borderline candidates and what would move them.
3. **Screened out:** with the specific must-have that failed (brief, factual).
4. **Bias & legal flags:** any criterion that risked bias or is legally sensitive, called out for review.

Everything here is a **draft screening recommendation for HR/hiring-manager review**, not a hiring decision or legal advice. Save to `recruitment/` (or the per-search subfolder).
