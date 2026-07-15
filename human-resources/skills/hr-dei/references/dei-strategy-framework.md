# DEI Strategy Framework

A reusable method for building a lawful, effective diversity-equity-inclusion program: assess, act across the lifecycle, run initiatives, set accountable goals, and measure. This is a **framework, not a data set** — every number below is a clearly-marked *example*. Real figures come only from supplied data or a named source. Fill every `<placeholder>`; delete guidance in _italics_.

> ⚠️ **DEI has real legal constraints, and they vary by jurisdiction and change over time.** Quotas, protected-characteristic preferences/set-asides, and protected-group-restricted programs can be **unlawful** and create reverse-discrimination liability — what's permitted differs by jurisdiction and employer type. This framework builds **lawful, opportunity-widening** DEI (remove barriers, broaden pipelines, standardize criteria, open programs to all); it does **not** design quotas or preferences. Flag every protected-characteristic design choice for **employment-counsel review**, scope legality to `legal.jurisdictions`, and stamp "⚠️ Draft — requires review by qualified HR/legal counsel before use" when `legal.counsel_review: true`. **Never fabricate benchmark/market/representation numbers.** Report aggregates only; **suppress small groups (commonly n < 5) that could re-identify individuals.**

## Step 1 — Maturity / assessment model

Locate where the organization is, so the plan is proportionate. Assess each dimension honestly from evidence, not aspiration.

| Dimension | Ad hoc (1) | Emerging (2) | Structured (3) | Embedded (4) |
|---|---|---|---|---|
| **Leadership & accountability** | No owner | Stated intent | Named owner + goals | Tied to leader objectives |
| **Data & measurement** | None | One-off snapshot | Tracked over time | Drives decisions |
| **Equitable processes** | Informal | Some standardized | Structured hiring/pay/promo | Audited, corrected |
| **Inclusion & culture** | Unmeasured | Survey run | Acted on by team | Belonging is the norm |
| **Programs (ERG/mentoring)** | None | Grassroots | Resourced, open to all | Integrated, evaluated |

_Score each 1–4 from real evidence; the lowest dimensions usually set the priorities._

## Step 2 — Assessment (aggregate, privacy-safe)

Baseline from **supplied** data only. Three lenses:

**A. Representation across the lifecycle** — find where representation drops.

| Stage | Group A | Group B | … | Notes |
|---|---|---|---|---|
| `Applicants` | `%` | `%` | | _suppress cells < min n_ |
| `Hires` | `%` | `%` | | |
| `Current (by level)` | `%` | `%` | | |
| `Promotions` | `%` | `%` | | |
| `Exits` | `%` | `%` | | |

_Percentages are placeholders. Populate only from supplied HRIS/ATS data. **Suppress or roll up any group below the minimum cell size** — a cell of 2 names people._

**B. Pay equity** — do **not** re-derive here; consume the internal pay-equity method owned by `compensation-benefits/` (`references/pay-band-framework.md`, Step 7): comparable-work pay gaps remaining after legitimate controls, jurisdiction-scoped and counsel-flagged. Pay-equity output may also route to `reports/analytics/`.

**C. Inclusion** — measure *experience*, which representation misses: inclusion-survey items (belonging, fair treatment, voice), eNPS cut by group **only where cells are large enough**. Aggregate.

## Step 3 — Focus areas across the employee lifecycle (the lawful core)

Fix the *processes* that produce inequitable outcomes; apply them to everyone.

| Lifecycle stage | Barrier to remove / process to standardize | Owns the tooling | DEI role |
|---|---|---|---|
| **Attraction & hiring** | Narrow sourcing; biased JDs; inconsistent interviews | `recruitment/` | Widen pipeline; inclusive JDs; structured interviews & scorecards |
| **Pay** | Unexplained pay gaps; opaque ranges | `compensation-benefits/` | Consume pay-equity findings; push transparency |
| **Development & advancement** | Unequal access to stretch work, mentoring, promotion | `training-development/`, `strategy/` | Check access/promo rates; equalize opportunity |
| **Retention & exit** | Inclusion breakdowns driving regretted exits | — | Analyze exit patterns by group (aggregated) |

> Frame each as *removing a barrier / standardizing a process / widening a pipeline*, **open to all** — not a protected-characteristic preference. Anything that would give a protected group a hiring/promotion edge, set-aside, or restricted benefit → flag for counsel before design.

## Step 4 — Initiative planning

Design programs to build belonging — structured to be **open to all** (a frequent legality pitfall is restricting participation by protected characteristic).

| Initiative | Purpose | Lawful design note | Delivery |
|---|---|---|---|
| **ERGs / affinity groups** | Community, voice, feedback channel | Voluntary, employee-led, **membership open to all** | Company-supported |
| **Mentoring / sponsorship** | Widen access to advancement | **Transparent, open access criteria** | HR-run |
| **Bias-awareness / inclusive-leadership training** | Reduce biased decisions | Applies to all managers | Hand to `training-development/` |

## Step 5 — Goals with accountability (lawfully)

Prefer **process** and **aspirational** goals over outcome quotas (which risk unlawful preference). Assign owner, cadence, and review.

| Goal type | Example _(illustrative)_ | Lawful? |
|---|---|---|
| **Process** | `Structured interviews for all roles` | ✅ preferred |
| **Process** | `Diverse candidate slates via broader sourcing` | ✅ preferred |
| **Equity** | `Close unexplained pay gaps after controls` | ✅ preferred |
| **Aspirational** | `Improve inclusion-survey belonging score` | ✅ preferred |
| **Outcome quota** | `Hire X% of group Y` | ⚠️ **flag for counsel — quota/preference risk** |

Assign each goal an owner and a review cadence; tie DEI progress into leadership reviews (accountability, Step 1 dimension). **Flag any outcome-percentage target for counsel before adoption.**

## Step 6 — Metrics (aggregated, small-n suppressed)

Track over time; definitions live in the hr-metrics catalog (DEI representation, pay-equity ratio, eNPS/engagement).

| Metric | What it shows | Guardrail |
|---|---|---|
| Representation by level/stage | Where representation drops | Suppress cells < min n |
| Pay-equity ratio (by group) | Comparable-work pay parity | From `compensation-benefits/`; counsel-flagged |
| Inclusion / belonging score | Felt inclusion | Cut by group only if cell large enough |
| Promotion & access rates | Advancement equity | Aggregate |
| Regretted-exit rate by group | Where inclusion breaks | Aggregate |

**All example figures are placeholders — populate only from supplied data or a named source.**

## Step 7 — Governance & accountability structure

- **Executive sponsor** — a named leader accountable for the program (not "everyone").
- **DEI owner / council** — runs the plan, coordinates with `recruitment/`, `compensation-benefits/`, `training-development/`, `strategy/`.
- **Cadence** — regular review of metrics and goals; report progress (aggregated) via the **hr-reports** skill.
- **Counsel checkpoint** — every design choice that touches a protected characteristic passes employment counsel before rollout.

## Reminders

- Build lawful, opportunity-widening DEI — never quotas, preferences, set-asides, or restricted programs; legality is jurisdiction-specific and changing, flag for counsel.
- Never fabricate representation/benchmark/market numbers — supplied data or a named source only.
- Report aggregates; suppress small groups that could re-identify people. Everything is a draft for HR/legal review.
