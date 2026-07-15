---
name: hr-training
description: Run learning & development for the company — a training-needs analysis that surfaces skill gaps, learning design across technical/leadership/compliance/onboarding tracks, curricula and course outlines with measurable objectives, delivery-mode selection, and career-path/leadership-development and training-evaluation frameworks. Use when the client wants to diagnose skill gaps, design a course or curriculum, build a compliance-training plan, stand up a leadership program, or measure whether training worked.
---

# HR Training & Development

Turns a capability gap into a defensible learning plan: diagnose what people can't yet do, design learning that closes the gap, build curricula with measurable objectives, pick the right delivery, and evaluate whether it worked. This skill owns HR function #5 and exports to `training-development/` (see the folder map).

## Setup gate (run first)

Enforce the config gate before any work, per `${CLAUDE_PLUGIN_ROOT}/skills/hr-config/SKILL.md`: look for `human-resources/config.yaml` at project root, require `version: 1` and `setup.completed: true`. If missing or invalid, STOP and tell the user exactly:
> Human resources isn't configured for this project yet. Run `/setup-human-resources` first.

Then load context: `company.about_file` (what the company does, so training is grounded in real work), `company.soul_file` (voice for learner-facing material), `company.design_file` (branded document/deck look), `company.size`, `company.locations`, `company.remote_policy` (drives delivery mode), and `legal.jurisdictions` (governs which compliance training is mandatory). Honor degraded modes (null brand file → neutral voice + warn once; empty `legal.jurisdictions` → no jurisdiction-specific mandatory-training claims, general best-practice only).

## Two standing safety rules (apply to everything below)

1. **Drafts, not legal advice.** Curricula, outlines, and plans are drafts for review by the client's qualified HR professional and, for anything statutory, employment counsel. **Which training is legally mandatory** (harassment-prevention, safety/OSHA-type, wage-and-hour, industry licensure, data-privacy) — and its required cadence, minimum duration, audience, and recordkeeping — is **jurisdiction-specific**: scope every such claim to `legal.jurisdictions`, name the jurisdiction, and flag it "verify with counsel". When `legal.counsel_review: true`, stamp any compliance-training plan or completion attestation with "⚠️ Draft — requires review by qualified HR/legal counsel before use". Never fabricate a statute, required hour-count, renewal interval, or deadline.
2. **Confidential by default.** Individual training records, assessment scores, and named skill-gap findings are employee data — keep them in-project, and route any identifiable per-employee record to the confidential zone (`reports/employee-reports/`), not to the shareable `training-development/` folder. Never invent employee names, scores, or completion data — placeholder or supplied data only.

## Operating method

1. **Training-needs analysis (TNA).** Before designing anything, diagnose the gap using `references/training-needs-analysis.md`. Work three levels: **organizational** (what capabilities the business strategy needs — pull from the `strategy/` folder's workforce plans / org design), **task/role** (what a specific role must be able to do — from role requirements and job descriptions in `recruitment/`), and **individual** (who is below the required bar — from performance data in `reports/employee-reports/performance-management/`, using supplied data only). A gap is **required capability − current capability**; no gap, no training. Prioritize gaps by business impact, size, and urgency, and decide **build vs. buy** (design internally vs. source an external course/vendor) per the reference.
2. **Frame the learning.** For each prioritized gap, classify the track, because each is designed and evaluated differently:
   - **Technical / role skills** — job-specific competencies; heavy on practice and on-the-job application.
   - **Leadership / management development** — people-leadership, decision-making, coaching; ties into career paths and succession (coordinate with `strategy/`).
   - **Compliance / mandatory** — required by law or policy. Cross-reference `legal-compliance/` for what is required in `legal.jurisdictions`, and treat cadence/records as jurisdiction-specific to verify. Do not present a compliance course as satisfying a legal requirement — it is a draft to confirm with counsel.
   - **Onboarding / role-readiness** — new-hire ramp. Coordinate with `onboarding/` (the onboarding checklist assigns training via this folder) rather than duplicating it.
3. **Write measurable objectives.** State what the learner will be able to *do* after the training, observably and measurably (action verb + condition + standard), not "understand" or "be aware of". Objectives are the spine — every module and every assessment maps back to one.
4. **Build the curriculum / course outline.** Use `references/curriculum-template.md`: audience and prerequisites, the measurable objectives, a module breakdown, learner activities, assessment method, duration, delivery mode, materials, and the evaluation plan. Map objectives → modules → assessment so nothing is taught that isn't assessed and nothing is assessed that wasn't taught. For proprietary content only the company holds (internal systems, product specifics, house methods), leave a clearly-marked placeholder for the client to supply — never fabricate it.
5. **Choose delivery mode.** Match mode to the objective, audience, and constraints: instructor-led (in-person or virtual), e-learning/self-paced, blended, on-the-job / coaching, cohort program, or microlearning. Weigh `company.remote_policy` and `company.locations` (distributed teams favor async/virtual), scale, urgency, and whether the skill needs live practice or feedback. Note accessibility (captioning, materials, accommodations).
6. **Career paths & leadership development.** Where relevant, design progression: role-to-role paths, the competencies each step requires, and the development actions (training, stretch assignments, mentoring) that move someone along. Coordinate with succession planning in `strategy/`. Keep any individual's development plan in the confidential zone.
7. **Evaluation.** Build in measurement from the start using a levels model (e.g. Kirkpatrick: **reaction** → **learning** → **behavior** → **results**): learner reaction, learning gained (pre/post assessment), on-the-job behavior change, and business results tied back to the TNA gap. Define the metric and how it's collected for each level the training warrants; not every course needs level 4, but every course should at least measure learning against its objectives.

## When to use each reference

- **`references/training-needs-analysis.md`** — diagnosing skill gaps and deciding what (if anything) to train and whether to build or buy, before any design work.
- **`references/curriculum-template.md`** — building any course or multi-course curriculum outline: the audience-to-evaluation structure with measurable objectives and the objectives→modules→assessment map.

## Agents this skill drives

- **hr-training-designer** — builds a curriculum or single-course outline for a supplied skill gap, role, or compliance requirement, using the curriculum template and mapping objectives → modules → assessment. Writes into `training-development/`.

## Boundaries

- Export only to `training-development/`. Individual training records / named gap findings go to the confidential `reports/employee-reports/` zone, not here. Never invent new top-level folders.
- Onboarding training coordinates with `onboarding/`; mandatory-training requirements come from `legal-compliance/` and are jurisdiction-scoped and flagged, never asserted as settled law. Leadership/career paths coordinate with `strategy/`.
- Do not fabricate proprietary or company-specific course content, statutory training requirements, or employee completion data. Everything is a draft for HR review.
