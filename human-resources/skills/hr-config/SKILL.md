---
name: hr-config
description: Load and validate the human-resources configuration for the current client project, resolve export paths, and enforce the setup-completion gate. Use when any human-resources command, skill, or agent needs project configuration, company/brand file paths, jurisdiction/legal context, the export folder map, or must verify that /setup-human-resources has been completed.
---

# HR Config

Every human-resources component reads its client-specific context through this skill. The plugin itself is brand-agnostic: **all** client specifics (company facts, voice, jurisdictions, headcount, HRIS, export locations) live in the consuming client project. Nothing about a real company is ever baked into the plugin.

## Canonical setup-check protocol

Run this before doing ANY human-resources work. Never proceed with guessed or partial config.

1. Resolve the project root: the current working directory, or `git rev-parse --show-toplevel` if inside a git repo.
2. Look for `<root>/human-resources/config.yaml`.
3. Parse it. Require `version: 1` and `setup.completed: true`.
4. If the file is missing, unparseable, or incomplete → **stop immediately** and tell the user:
   > Human resources isn't configured for this project yet. Run `/setup-human-resources` first.
   Subagents return that exact sentence as their result so the orchestrator surfaces it.

## Config resolution

- Config file: `human-resources/config.yaml` (schema: [references/config-schema.md](references/config-schema.md))
- Company identity/facts: path in `company.about_file` (setup resolves `./ABOUT.md`, falling back to `_configuration/references/ABOUT.md`) — what the company IS and does
- Employee-facing voice/tone: path in `company.soul_file` (same resolution for `SOUL.md`) — how employee comms, offer letters, handbooks SOUND
- Document/brand visuals: path in `company.design_file` (same resolution for `DESIGN.md`) — how printed/branded HR docs LOOK
- Export folder map (where every deliverable is written): [references/folder-map.md](references/folder-map.md), rooted at `exports.root` (default `human-resources/`)
- Employee records / PII: `human-resources/reports/employee-reports/` — treat as strictly confidential (see below)

## The export root vs. the plugin

`human-resources/` in the **client project** holds config + all exports (see the folder map). `human-resources/` in **this plugin repo** holds the skills/agents/commands. They share a name but are different trees — never write client deliverables into the plugin, and never read plugin files as if they were client data. Resolve plugin files via `${CLAUDE_PLUGIN_ROOT}`.

## Two rules that are non-negotiable across every component

### 1. Not legal advice — draft, then human review
HR work touches employment law, which is jurisdiction-specific and changes constantly. Every component:
- produces **drafts and analyses for review by the client's qualified HR professional and/or employment counsel** — never definitive legal advice or a guarantee of compliance;
- grounds any jurisdiction-specific claim in `legal.jurisdictions` from config, and says so explicitly ("Under California law…"), flagging when a rule may vary by locality or may be outdated;
- when `legal.counsel_review: true`, stamps generated policies, contracts, terminations, and compliance findings with a visible "⚠️ Draft — requires review by qualified HR/legal counsel before use" banner;
- never fabricates a statute, case, filing deadline, or dollar threshold. If unsure, it says the number must be verified against the current jurisdiction rule and points the user to the authoritative source.

### 2. Confidential by default — PII stays in the project
Employee data is sensitive personal information. Every component:
- keeps all employee records, case files, reviews, and reports **inside the client project** (under the folder map) — never pastes PII into an external service, MCP call, web search, or draft that leaves the project without the user explicitly directing it;
- never invents real employee data; placeholder or supplied data only;
- warns if it detects credentials, SSNs/national IDs, bank details, or health information sitting in a tracked (non-gitignored) file, and offers to help move or redact them;
- honors `confidentiality.records_dir` and does not co-mingle identifiable records with shareable templates.

## HRIS / systems connection (optional)

- `hris.connection: none` (default) → the plugin drafts documents and reports; a human enters data into the HRIS. This is the safe default and covers most work.
- `hris.connection: api_key` → `hris.auth_env_var` names the env var (value lives in the client's gitignored `.env`; source it inline per Bash call: `set -a; source .env; set +a`). **Read-only** endpoints (fetch roster, list positions) may be called freely. Any write/create/terminate call happens only in the main conversation where the user can see it, and only when the user explicitly asks — never from a subagent, never speculatively.
- `hris.connection: mcp` → `hris.mcp_server_name` must exist in the client's `.mcp.json`. Same read-free / write-gated rule.
- Writes that change an employee's status, pay, or employment (hire, terminate, change comp) are **never** performed automatically — always draft, confirm with the user, then act.

## Degraded modes (warn, don't block)

- `company.about_file: null` → rely on `company.industry` / `company.size` / `company.locations` from config; never invent business specifics, benefits, or policies the company hasn't stated; warn once.
- `company.soul_file: null` → write employee-facing copy in a neutral, professional, plain-language voice; note that brand voice guidelines were unavailable.
- `company.design_file: null` → use clean, accessible default document formatting; skip brand styling cues; warn.
- `legal.jurisdictions` empty → do not make jurisdiction-specific legal claims at all; produce general best-practice drafts, clearly labeled as needing localization and counsel review.
- HRIS unreachable / not configured → produce file-based drafts and a manual-entry guide; never block on system access.

## Validation rules

| Condition | Requirement |
|---|---|
| always | `version: 1` and `setup.completed: true` |
| always | No credential values anywhere in `config.yaml`. If you find one, warn the user and help move it to `.env`. |
| always | `legal.jurisdictions` present (may be a single entry) before producing any compliance, termination, or statutory-policy document |
| `hris.connection: api_key` | `hris.auth_env_var` present (env var NAME only) |
| `hris.connection: mcp` | `hris.mcp_server_name` present and that server exists in the client's `.mcp.json` |
| `company.union: true` | labor-relations features (CBA-aware grievances, bargaining prep) become available; otherwise skipped |

## Credentials handling

- Secrets live only in the client project's `.env` (verify it is gitignored; if not, warn before touching it).
- Shell state does not persist between Bash calls — source inline every time: `set -a; source .env; set +a; curl ...`
- Never write a credential value into `config.yaml`, a draft, a report, or a commit. Env var **names** only.
