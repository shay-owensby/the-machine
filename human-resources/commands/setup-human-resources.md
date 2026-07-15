---
description: Configure the human-resources plugin for this client project — company facts, jurisdictions, headcount, HRIS connection, brand/voice files, export folders, and confidentiality settings. Run once per client project (re-run to reconfigure).
---

# Setup: Human Resources

You are configuring the human-resources plugin for THIS client project. Work through the wizard below **one step at a time**, using the AskUserQuestion tool where options are enumerable and plain questions where free text is needed. Keep it conversational — this is an onboarding interview, not a form dump.

Read `${CLAUDE_PLUGIN_ROOT}/skills/hr-config/references/config-schema.md` and `${CLAUDE_PLUGIN_ROOT}/skills/hr-config/references/folder-map.md` first so you know the exact target schema and the folder tree you will create.

## Step 0 — Re-run detection

If `human-resources/config.yaml` exists at the project root and has `setup.completed: true`: tell the user setup was already completed (show date + company name + jurisdictions), and ask whether to **reconfigure** (load every current value as the default for each step below) or **exit**.

## Step 1 — Company basics

Collect and confirm: `company.name`, `company.industry` (one line), `company.size` (current headcount, integer), `company.employment_types` (which of full_time / part_time / contractor / seasonal / intern the company uses), `company.remote_policy` (onsite / hybrid / remote), and `company.timezone`. Explain that headcount matters because some legal thresholds key off it.

## Step 2 — Locations & jurisdictions (drives all compliance work)

Collect `company.locations` (one or more: country, region/state, city). From those, derive and confirm `legal.jurisdictions` (stable codes like `US-Federal`, `US-CA`, `CA-ON`, `UK`, `EU`). Emphasize: **this list is the ground truth** — every compliance, termination, and statutory-policy output is scoped to it, and the plugin will refuse to make jurisdiction-specific legal claims outside it. Ask whether operations are unionized (`company.union`); if yes, note that labor-relations features will be enabled.

Set `legal.disclaimer_required: true` always. Ask whether generated policies/contracts/terminations/audits should carry the counsel-review banner (`legal.counsel_review`, default true, recommended).

## Step 3 — Brand & voice files

Look for these at the project root, then `_configuration/references/`, and record resolved paths. ABOUT.md = what the company IS, SOUL.md = how employee-facing comms SOUND, DESIGN.md = how documents LOOK.
1. `./ABOUT.md`, `./SOUL.md`, `./DESIGN.md`
2. `_configuration/references/ABOUT.md` (etc.)

For each found, read briefly and confirm it's the right document. For each missing/empty, warn about degraded output (per the hr-config degraded-modes table) and offer to (a) proceed degraded with `null`, or (b) interview the user now and draft the file to the project root with their approval. Never invent company facts when ABOUT.md is absent.

## Step 4 — HRIS / systems connection

Ask whether HR data lives in a system the plugin should read from: **BambooHR, Gusto, Rippling, Workday, ADP, other, or none/manual**.
- **none / manual** (default, recommended): the plugin drafts documents and reports; a human enters data into whatever system they use. Choose this if unsure.
- **API key**: ask only for the env var NAME (e.g. `BAMBOOHR_API_KEY`); value goes in `<project>/.env`. Check `.gitignore` covers `.env` — if not, warn and offer to add it. Collect required extras (e.g. subdomain). Remind the user the plugin only ever **reads** automatically; writes (hire/terminate/comp changes) are always drafted and confirmed in the main conversation first.
- **MCP**: ask for the server name as it appears in the client's `.mcp.json`. Never write MCP entries containing secrets yourself.

**Never write a credential value into config.yaml. Ever.**

## Step 5 — Confidentiality

Confirm `confidentiality.pii_handling: strict` (recommended default) and explain what it enforces: employee records/PII stay in-project, never sent externally, segregated under `confidentiality.records_dir` (`human-resources/reports/employee-reports`). If the project git repo is shared, recommend gitignoring the confidential zones and offer to add them to `.gitignore`.

## Step 6 — Defaults

Collect `defaults.approver` (the role that signs off HR drafts, e.g. "HR Manager") and an optional `defaults.document_footer`.

## Step 7 — Write everything

1. Write `human-resources/config.yaml` exactly per the schema, with `setup.completed: true`, today's date in `completed_at`, and `plugin_version` read from `${CLAUDE_PLUGIN_ROOT}/.claude-plugin/plugin.json`.
2. Create the full export folder tree from `${CLAUDE_PLUGIN_ROOT}/skills/hr-config/references/folder-map.md` under `exports.root`, with a `.gitkeep` in each empty directory. Never overwrite existing content in these folders.
3. If the user agreed, add the confidential zones (and `.env`) to `.gitignore`.
4. Print a summary table of the configuration (company, size, jurisdictions, union, HRIS mode, brand files found, folders created) and the two standing rules — **drafts for review, not legal advice** and **PII stays in-project** — then finish with the list of what they can run next:
   - `/hr-hire` — recruitment pipeline
   - `/hr-onboard` — onboarding a new hire
   - `/hr-offboard` — offboarding / separation
   - `/hr-review-cycle` — performance review cycle
   - `/hr-handbook` — build or update the employee handbook
   - or invoke any `hr-*` skill directly (e.g. "draft a remote-work policy", "audit our postings for compliance").
