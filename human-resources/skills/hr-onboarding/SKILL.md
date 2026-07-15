---
name: hr-onboarding
description: Take a signed offer to a productive, welcomed new hire — pre-boarding paperwork and access, day-1 orientation with handbook acknowledgment, team introductions, role ramp, and a 30/60/90-day plan. Use when the client has an accepted offer and needs to onboard a new employee, build a reusable onboarding checklist, or draft a 30/60/90 ramp plan for a role.
---

# HR Onboarding & Orientation

Turns an accepted offer into a new hire who feels welcomed and reaches productivity on a clear timeline: gather paperwork before day 1, provision access, orient them to the company/policies/culture, introduce the team, and ramp them against explicit 30/60/90 goals. This skill owns HR function #2 and exports to `onboarding/` (see the folder map).

## Setup gate (run first)

Enforce the config gate before any work, per `${CLAUDE_PLUGIN_ROOT}/skills/hr-config/SKILL.md`: look for `human-resources/config.yaml` at project root, require `version: 1` and `setup.completed: true`. If missing or invalid, STOP and tell the user exactly:
> Human resources isn't configured for this project yet. Run `/setup-human-resources` first.

Then load context: `company.about_file` (what the company does — for the company/culture intro), `company.soul_file` (voice for welcome/orientation copy), `company.design_file` (branded document look), `company.name`, `company.size`, `company.locations`, `company.remote_policy`, `company.employment_types`, and `legal.jurisdictions` (governs which new-hire forms are required). Honor degraded modes (null brand file → neutral, warm-but-professional voice + warn once; empty `legal.jurisdictions` → no jurisdiction-specific form claims, general best-practice only + flag for localization).

## Two standing safety rules (apply to everything below)

1. **Drafts, not legal advice.** Onboarding checklists, welcome packets, and 30/60/90 plans are drafts for review by the client's qualified HR professional and/or employment counsel. Any **required new-hire form depends on jurisdiction** (work-authorization / employment-eligibility verification, tax-withholding forms, state new-hire reporting, mandatory notices) — scope those to `legal.jurisdictions`, name the jurisdiction, and flag "verify with counsel". Never fabricate a form name, filing deadline, retention period, or dollar threshold; if unsure, say the item must be verified against the current jurisdiction rule. When `legal.counsel_review: true`, stamp any formal onboarding agreement or acknowledgment form with "⚠️ Draft — requires review by qualified HR/legal counsel before use".
2. **Confidential by default.** A new hire's paperwork carries sensitive PII (national ID/SSN, work-authorization documents, bank/direct-deposit details, home address, date of birth). Keep completed forms and any identifiable data in-project under the confidential zone (`confidentiality.records_dir` → `reports/employee-reports/`), never in the shareable `onboarding/` templates. Never paste new-hire PII into an external service, web search, or MCP call. Warn if you spot PII in a tracked (non-gitignored) file. Never invent employee data — placeholder or supplied data only.

## Operating method

1. **Intake.** Capture the new-hire brief: name (or placeholder), role/title, level, start date, manager, team, work location (resolve it to a jurisdiction in `legal.jurisdictions`), employment type (from `company.employment_types`), and on-site/hybrid/remote arrangement. The resolved jurisdiction and employment type together determine which paperwork applies — flag the jurisdiction now.
2. **Pre-boarding (before day 1).** Draft the pre-start packet from `references/onboarding-checklist.md`:
   - **Paperwork** — the offer/acceptance on file, and the required new-hire forms for the resolved jurisdiction: employment-eligibility / work-authorization verification, tax-withholding, direct-deposit, emergency contact, and benefits enrollment. List these as *jurisdiction-specific, verify against `legal.jurisdictions`* — do not assert a specific form name or ID as fact for a jurisdiction you can't confirm.
   - **Equipment & access requests** — build the list of hardware, accounts, and system access the role needs, and route the request to IT/access owners. Do not create real accounts or credentials; produce the request list for a human to action.
   - **Welcome touch** — a warm pre-start welcome note in `company.soul_file` voice (first-day logistics: where/when, what to bring, dress, parking/remote link, who greets them).
3. **Day-1 orientation.** Draft the orientation plan: company and culture intro grounded in `company.about_file`; a walk-through of core policies by pulling the **employee handbook from `policies/`** (do not restate policy from memory — reference the handbook that lives there); and the **handbook acknowledgment** form for the hire to sign. Coordinate with the hr-policies work so the acknowledgment matches the current handbook version. Confirm workstation/access is live, and cover safety/emergency basics (coordinate with `health-safety-wellness/` if the role warrants it).
4. **Team introductions.** Plan introductions: manager 1:1, an onboarding buddy/mentor, key cross-functional partners, and a first-week meet-the-team. For remote/hybrid hires (`company.remote_policy`), make the social integration deliberate rather than incidental.
5. **Role ramp & training.** Identify the role's required and recommended training and hand off to `training-development/` for the curriculum (do not invent course content) — compliance/mandatory training, tools, and role skills. Sequence early wins so the hire contributes quickly.
6. **30/60/90 plan.** Build the ramp plan from `references/30-60-90-template.md`, adapted to the role and level: learning goals and milestones for each window, scheduled check-ins (manager + HR), and a clear definition of "fully ramped". Give the hire and the manager a shared copy.
7. **Assemble & route outputs.** Write the onboarding checklist, welcome packet, access/equipment request list, and 30/60/90 plan into `onboarding/` (per hire, use an `onboarding/<employee-slug>/` subfolder). Keep any completed forms carrying PII out of the shareable templates and in the confidential records zone.

**Experience matters:** a new hire decides early whether they made the right choice. Warm, organized, and paced onboarding — not a paperwork dump — drives retention and time-to-productivity.

## When to use each reference

- **`references/onboarding-checklist.md`** — building or running the phase-by-phase onboarding checklist (pre-start / day 1 / week 1 / first 90 days) with task owners; also holds the note that required new-hire forms vary by jurisdiction.
- **`references/30-60-90-template.md`** — drafting a new hire's 30/60/90-day ramp plan (goals, learning, milestones, check-ins), adaptable by role and level.

## Boundaries

- Export only to `onboarding/` (per-hire subfolder `onboarding/<employee-slug>/` optional). Handbook acknowledgment coordinates with `policies/`; role training with `training-development/`; scheduling of orientation/intro sessions with `scheduling/`; safety orientation with `health-safety-wellness/`. Completed PII-bearing forms live in the confidential records zone, never in shareable templates. Never invent new top-level folders.
- Never provision real accounts, credentials, or system access — produce request lists a human actions. Required-form claims are jurisdiction-scoped and flagged for verification. New-hire PII stays in-project.
