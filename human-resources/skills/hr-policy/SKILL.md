---
name: hr-policy
description: Build and maintain the employee handbook and standalone workplace policies — decide which policies the company actually needs (by size, jurisdiction, and industry), draft them in the company's plain-language voice grounded in its real practices, keep them internally consistent and version-controlled, attach an acknowledgment/sign-off form to each, and plan the rollout. Use when the client wants to create or update a handbook, write or revise a single policy (PTO, remote work, code of conduct, acceptable use, etc.), or audit their policies for gaps and contradictions.
---

# HR Policy Development & Enforcement

Turns how the company actually operates into a clear, consistent, enforceable set of written policies — an employee handbook plus standalone policies — that employees can understand, managers can apply evenly, and counsel can stand behind. This skill owns HR function #8 and exports to `policies/` (see the folder map).

## Setup gate (run first)

Enforce the config gate before any work, per `${CLAUDE_PLUGIN_ROOT}/skills/hr-config/SKILL.md`: look for `human-resources/config.yaml` at project root, require `version: 1` and `setup.completed: true`. If missing or invalid, STOP and tell the user exactly:
> Human resources isn't configured for this project yet. Run `/setup-human-resources` first.

Then load context: `company.about_file` (what the company does and how it operates), `company.soul_file` (voice for employee-facing writing), `company.design_file` (branded document look), `company.name`, `company.size`, `company.industry`, `company.locations`, `company.remote_policy`, `company.union`, and `legal.jurisdictions`. Honor degraded modes (null `soul_file` → neutral, plain, professional voice + warn once; null `about_file` → do not invent practices, ask the user; empty `legal.jurisdictions` → no jurisdiction-specific claims, general best-practice drafts labeled for localization).

## Two standing safety rules (apply to everything below)

1. **Drafts, not legal advice.** Every policy and handbook section is a draft for review by the client's qualified HR professional and/or employment counsel — never a definitive statement of law or a guarantee of compliance. Whether a policy is legally *required*, what it must *say*, and any threshold, notice period, or entitlement in it are **jurisdiction- and size-specific** — scope every such claim to `legal.jurisdictions` and `company.size`, name the jurisdiction it applies to ("Under California law…"), and flag it "verify with counsel". When `legal.counsel_review: true`, stamp every generated policy and the assembled handbook with "⚠️ Draft — requires review by qualified HR/legal counsel before use". Never fabricate a statute, case, filing deadline, dollar threshold, or leave entitlement — if a number is needed and unknown, say it must be verified against the current jurisdiction rule and point to the authoritative source.
2. **Confidential by default.** Policies themselves are shareable within the org, but ground them only in the company's stated facts — never paste employee PII into a policy, and never send company practice details to an external service, web search, or MCP call beyond what the user directs. Never invent company practices; supplied or stated facts only.

## Operating method

1. **Inventory & needs assessment.** Read what already exists in `policies/`. Then determine which policies this company needs, driven by three inputs: **size** (`company.size` — some policies unlock at headcount thresholds, e.g. leave and anti-harassment training requirements often key off employee count — flag every threshold for counsel), **jurisdiction** (`legal.jurisdictions` — some policies are legally *required* in a location and merely recommended elsewhere), and **industry** (`company.industry` — e.g. safety, driving, food handling, client-data policies). Produce a policy list split into **legally-required (verify)** and **recommended**, using `references/handbook-outline.md` as the checklist. **Flag every "required" item as needing counsel confirmation** — never assert a policy is legally mandatory as settled fact.
2. **Ground in actual practice — ask, don't invent.** A policy must describe what the company *actually does*, not a generic ideal. Pull practices from `company.about_file` and what the user tells you (PTO accrual, remote expectations, hours, dress, discipline steps). Where a needed policy has no stated practice behind it, **ask the user rather than inventing one** — an invented PTO accrual or discipline ladder is worse than an explicit gap. List unanswered gaps plainly.
3. **Draft in plain language.** Write each policy from `references/policy-template.md`, in `company.soul_file` voice but always clear, direct, and readable — short sentences, defined terms, no legalese the employee can't parse. A policy people don't understand can't be followed or enforced. Be specific and enforceable (who, what, when, consequences) without being so rigid it can't flex.
4. **Consistency — no contradictions, even enforcement.** Two things must be consistent. (a) **Internal consistency:** no policy may contradict another (e.g. a PTO policy and a leave policy that disagree on carryover; a remote policy and a hours policy that conflict). Cross-check every new/changed policy against the rest of the set and reconcile. (b) **Consistency of enforcement is a legal-risk theme:** policies must be written to be applied *evenly to everyone* — inconsistent or selective enforcement is a common source of discrimination and wrongful-termination exposure. Emphasize even application in the policy text and the rollout note; avoid discretion language that invites uneven treatment, and pair disciplinary/conduct policies with the process that keeps enforcement uniform.
5. **Acknowledgment / sign-off.** Every policy and the handbook as a whole gets an acknowledgment form (the block in `references/policy-template.md`): employee name, policy title + version, "I have received, read, and understand…", signature, date. This is the record that the employee was on notice — it matters for enforcement. Note that acknowledgments are often kept in the employee's file (a confidential record under `reports/employee-reports/`), not in the shareable `policies/` folder.
6. **Version control.** Policies change; you must be able to say which version was in force when. Carry a version and effective/review date in each policy's front matter (or a `-v2` filename suffix when iterating, per the folder map). When revising, preserve the prior version, note what changed and why, and re-issue for acknowledgment if the change is material.
7. **Communication / rollout note.** A policy nobody knew about can't be enforced. For each new or materially changed policy, produce a short rollout note: who it applies to, effective date, how it's being communicated (all-hands, email, handbook update), where to find it, who to ask, and the acknowledgment deadline. Roll out consistently to everyone in scope.

For a full handbook, drive the **hr-policy-writer** agent per needed section and assemble; the **hr-handbook** command orchestrates that end to end. For a single policy, hand the section to **hr-policy-writer** directly.

## When to use each reference

- **`references/handbook-outline.md`** — deciding which sections a handbook needs, and which are commonly legally-required (verify) vs. recommended; also holds the cross-references to the owning function folders (leave ↔ compliance, benefits ↔ compensation-benefits, safety ↔ health-safety-wellness).
- **`references/policy-template.md`** — drafting or revising any standalone policy; holds the section structure, the acknowledgment block, and the drafting style guide (clear, enforceable, non-discriminatory, consistent).

## Agents this skill drives

- **hr-policy-writer** — drafts ONE policy or ONE handbook section on request, grounded in the company's stated practices and jurisdiction, using the policy template. Flags legally-required-but-unstated practices (asks rather than invents), flags jurisdiction-specific clauses for counsel, and stamps the counsel-review banner. Writes into `policies/`.

## Boundaries

- Export only to `policies/` (handbook, standalone policies, codes of conduct, acknowledgment forms). Acknowledgment *records* signed by a real employee are confidential and belong under `reports/employee-reports/`. Never invent new top-level folders.
- Never assert a policy is legally required or legally sufficient — that is counsel's call. Legal claims are jurisdiction- and size-scoped and flagged for verification. Policies describe the company's real practices; where a practice is unknown, ask.
