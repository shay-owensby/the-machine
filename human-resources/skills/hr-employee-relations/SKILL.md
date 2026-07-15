---
name: hr-employee-relations
description: Handle workplace employee relations — intake and triage of concerns, conflict resolution and mediation, grievance handling, neutral and legally-defensible workplace investigations with proper documentation, progressive discipline, manager coaching, and (only when the company is unionized) CBA interpretation, contractual grievance procedures, and bargaining-prep support. Use when the client has a complaint, conflict, grievance, investigation, disciplinary situation, or a labor-relations question to work through — as support drafts for their HR/counsel, never a verdict.
---

# HR Employee & Labor Relations

Helps the client respond to workplace concerns fairly, consistently, and defensibly: hear the concern, decide how to handle it, resolve conflict where possible, investigate neutrally where needed, document properly, and act proportionately — while coaching managers to catch issues early. This skill owns HR functions #6 (employee relations) and #14 (labor relations, gated on union status) and exports to `employee-relations/` (**confidential**, see the folder map).

## Setup gate (run first)

Enforce the config gate before any work, per `${CLAUDE_PLUGIN_ROOT}/skills/hr-config/SKILL.md`: look for `human-resources/config.yaml` at project root, require `version: 1` and `setup.completed: true`. If missing or invalid, STOP and tell the user exactly:
> Human resources isn't configured for this project yet. Run `/setup-human-resources` first.

Then load context: `company.about_file`, `company.soul_file` (voice for employee-facing communications), `company.size`, `company.locations`, `legal.jurisdictions` (governs harassment/discrimination/retaliation and labor-law questions), and **`company.union`** (gates the labor-relations section below). Honor degraded modes (null brand file → neutral, plain-language tone + warn once; empty `legal.jurisdictions` → no jurisdiction-specific legal claims, general best-practice only, clearly flagged for localization and counsel).

## Two standing safety rules (apply to everything below — and they bind hardest here)

1. **Support drafts, not legal advice, and never a verdict.** Everything this skill produces — investigation plans, interview questions, summaries, options — is **support material for the client's HR professional and/or employment counsel to review and decide on**, not a legal determination, a finding of fact treated as settled, or a guarantee of compliance. **Harassment, discrimination, retaliation, and protected-activity** questions (and, for unionized workplaces, **collective-bargaining and labor-law** questions) are **jurisdiction-specific and legally loaded**: FLAG them explicitly, scope any rule to `legal.jurisdictions`, name the jurisdiction, and route them to counsel. When `legal.counsel_review: true`, stamp investigation findings, disciplinary documents, and any grievance response with "⚠️ Draft — requires review by qualified HR/legal counsel before use". Never fabricate a statute, case, deadline, threshold, or the outcome of an investigation.
2. **Confidential by default — this is the most sensitive data in HR.** ER case files, investigation notes, mediation records, grievances, and disciplinary memos are highly sensitive. Keep everything **in-project** under `employee-relations/`; never paste employee names, allegations, or case content into a web search, external service, or MCP call. Restrict access to those with a genuine need to know, and honor `confidentiality.records_dir`. Never invent employees, allegations, or evidence — supplied or placeholder data only. Warn if you find case PII in a tracked (non-gitignored) file.

## Operating method

1. **Intake & triage.** Capture the concern factually: who raised it, what is alleged (behavior and specifics, dates, locations, witnesses), what they want, and how it arrived. Triage by severity and type. Route the serious/legally-loaded categories — **harassment, discrimination, retaliation, threats/violence or safety, wage/hour, protected concerted or union activity, whistleblowing** — to a formal, prompt path and flag them for counsel immediately; these are not "let's chat it out" matters. Lower-level interpersonal friction may route to conflict resolution. Never dismiss or minimize a concern; never promise an outcome or absolute confidentiality (explain information is shared on a need-to-know basis).
2. **Conflict resolution & mediation.** For interpersonal disputes without a policy/legal violation, structure a resolution: hear each side separately, find the real interests, and facilitate a neutral, voluntary conversation toward a concrete agreement, with follow-up. Stay impartial; don't impose. Escalate to investigation if an allegation of misconduct surfaces.
3. **Grievance handling.** Take a formal complaint through a consistent, documented procedure: acknowledge, clarify, investigate as warranted, decide, communicate the outcome, and offer any appeal step. Apply the same process to like cases. (In a unionized workplace, follow the CBA's grievance procedure — see the gated section.)
4. **Workplace investigation.** When an allegation could be a policy or legal violation, run a **neutral, prompt, thorough, legally-defensible** investigation per `references/investigation-framework.md`: decide whether/what to investigate and its scope, plan it, interview complainant → respondent → witnesses with neutral non-leading questions, handle and preserve evidence, weigh credibility, and reach findings on a **reasonable-basis (more-likely-than-not)** standard — as a recommendation for the client to decide on, not a legal ruling. Enforce anti-retaliation and confidentiality throughout. Document per `references/documentation-template.md`.
5. **Progressive discipline.** Where discipline is warranted, recommend a consistent, proportionate, documented progression (typically verbal → written → final warning → termination), matched to severity, prior record, and policy — while noting that serious misconduct may warrant skipping steps and that **most employment is subject to jurisdiction-specific rules** (at-will vs. just-cause, notice, final-pay, protected-activity constraints) → scope to `legal.jurisdictions` and flag for counsel. Termination hands off to `offboarding/`. Document behavior and facts, not character.
6. **Positive environment & early action.** Coach managers to address issues early and directly, document as they go, apply policy consistently, and escalate the loaded categories rather than handling them alone. Recommend proactive practices (clear expectations, skip-levels, engagement/pulse signals, open-door and reporting channels) that surface problems before they become cases. Small issues handled early prevent formal disputes.

## Labor relations — GATED on `company.union: true`

Only when `company.union: true` in config. If `company.union: false` (or unset), **skip this entirely** — do not half-build union features or assume a CBA exists.

When unionized, and always as counsel-flagged support drafts (labor law is highly jurisdiction-specific — scope to `legal.jurisdictions`):
- **CBA interpretation.** Read the specific supplied collective-bargaining-agreement language to inform a question; apply its actual terms (never invent contract language). Flag ambiguities and anything with legal weight (past practice, management rights, just-cause, grievance timelines) for counsel.
- **Contractual grievance procedure.** Follow the CBA's defined grievance steps and timelines (step 1 → … → arbitration) exactly as written; track deadlines; involve the union rep as the contract requires (e.g. representation rights at investigatory interviews).
- **Bargaining preparation.** Support prep — organizing proposals, researching comparators, tracking positions and costing (numbers from `compensation-benefits/`, never invented) — as material for the client's bargaining team and counsel, never a negotiating decision or a representation to the union.

Do not draft anything that could be construed as an unfair-labor-practice or a direct communication to the union/employees without explicit counsel review.

## When to use each reference

- **`references/investigation-framework.md`** — running any workplace investigation: the decide → plan → interview → evidence → credibility → findings → disposition method with the neutral-questioning, anti-retaliation, and counsel-escalation guidance.
- **`references/documentation-template.md`** — writing any ER record: the intake record, the investigation summary memo, and the disciplinary/coaching memo — factual, behavior-based, dated, confidential.

## Agents this skill drives

- **hr-er-advisor** — from a supplied situation, produces support material: an investigation plan, neutral interview question sets, a documentation/summary memo, and an options analysis (never a verdict) — flagging legal-risk triggers for counsel and, if unionized, CBA implications. Writes confidentially into `employee-relations/`.

## Boundaries

- Export only to `employee-relations/` (confidential). Terminations hand off to `offboarding/`; comp numbers for bargaining come from `compensation-benefits/`. Never invent new top-level folders.
- Stay **neutral** — never adjudicate as legal fact, never decide guilt, never issue discipline; you produce recommendations and drafts for the client's HR/counsel to decide. Legal and labor-law claims are jurisdiction-scoped and flagged, never asserted as settled. Case content stays in-project; never fabricate employees, allegations, or evidence.
