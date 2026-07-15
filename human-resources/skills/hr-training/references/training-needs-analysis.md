# Training-Needs Analysis (TNA) Framework

A TNA answers one question before any course is designed: **is training the right fix, and if so, for what gap, for whom, and how much?** Skipping it produces training that is well-made but aimed at nothing. Work it top-down through three levels, quantify the gap, prioritize, then decide how to source the solution.

> Ground every level in real inputs from the client project — do not invent capability data, performance scores, or headcounts. Where a level needs data the client hasn't supplied, mark it as an input to collect, don't fill it with an assumption. Any individual performance data used here is confidential (`reports/employee-reports/performance-management/`); keep aggregate findings in `training-development/` and named findings in the confidential zone.

## The core equation

> **Gap = Required capability − Current capability**

Training only addresses gaps caused by a **lack of knowledge or skill**. If the gap is caused by something else — unclear expectations, missing tools, broken process, weak incentives, wrong hire, capacity — training will not fix it, and naming that early saves the budget. Always ask: *"Could they do it if their life depended on it?"* If yes, it's not a training gap.

## The three levels

### 1. Organizational level — should we train, and toward what?
Start from the business, not the course.
- What capabilities does the strategy require? Pull from workforce plans, org design, and goals in the `strategy/` folder.
- What's the trigger? (new strategy, new system, new regulation, growth, quality/safety problem, turnover, restructure.)
- Is the environment ready — will managers reinforce it, is there time and budget, does the culture support applying it? Training dropped into an unsupportive system doesn't stick.
- Output: the business case for training in this area, and the results it should move.

### 2. Task / role level — what must the role be able to do?
Define the target bar for the role, independent of who currently holds it.
- Break the role into its key tasks and the competencies each requires (knowledge, skills, behaviors). Use job descriptions and role requirements from `recruitment/` and the actual work from `company.about_file`.
- For each competency, state the **required proficiency standard** — the observable "can do X to Y standard under Z conditions" bar.
- Distinguish frequent/critical tasks (worth training) from rare/low-stakes ones (job aid may suffice).
- Output: the competency-and-standard profile the training must produce.

### 3. Individual level — who is below the bar, and by how much?
Compare real people to the role standard.
- Sources: performance reviews and goals (`reports/employee-reports/performance-management/`, supplied data only), manager input, self-assessment, skills inventory, assessment/test results, observation, error/quality/safety data, customer feedback.
- For each competency, place current proficiency against the required standard; the distance is the individual gap.
- Aggregate across people to see whether a gap is widespread (cohort training) or isolated (coaching, not a course).
- Output: who needs what, and the size of each gap.

## Prioritize the gaps

Not every gap earns a course. Rank by:

| Factor | Ask |
|---|---|
| Business impact | How much does closing this move a strategic result, revenue, quality, safety, or risk? |
| Gap size | How far below standard, and how many people? |
| Urgency | Is there a deadline, regulation, launch, or active risk driving it? |
| Feasibility | Can training realistically close it, and is the environment ready to reinforce it? |
| Cost of inaction | What happens if we don't — compliance exposure, turnover, errors, missed strategy? |

Mandatory/compliance gaps are typically non-negotiable and jump the queue — but confirm what is actually required in `legal.jurisdictions` via `legal-compliance/`, and flag cadence/records for counsel. Don't assert a legal training requirement as settled.

## Build vs. buy (sourcing)

For each prioritized gap, decide how to source the solution:

| Choose **build** (internal design) when… | Choose **buy** (external course/vendor) when… |
|---|---|
| Content is company-specific, proprietary, or house methodology | Content is generic/standardized (common software, general management, commodity compliance) |
| You have internal SMEs and design capacity | No internal expertise or bandwidth; speed matters |
| It's ongoing/repeatable — worth the build cost | It's one-off or infrequent |
| Deep alignment to your process is essential | A proven off-the-shelf program already exists |
| Confidentiality requires keeping it in-house | Certification/accreditation must come from an authorized provider |

Blended is common: buy the standard foundation, build the company-specific layer on top. When buying, define selection criteria (objectives fit, quality, format, accessibility, cost, vendor track record) — but the plugin doesn't endorse or invent specific vendors; it frames the decision.

## TNA output

A short TNA summary that feeds design:
- **Gap statement** — required vs. current, for whom, evidenced by what.
- **Root cause** — confirmed as a knowledge/skill gap (not a process/tooling/motivation issue).
- **Priority** — with the ranking rationale.
- **Track** — technical / leadership / compliance / onboarding.
- **Build vs. buy** — with reasoning and, if build, the objectives to hand to the curriculum template.
- **Success measure** — the result this training should move (feeds the evaluation plan).
