---
name: email-marketing-config
description: Load and validate the email-marketing configuration for the current client project, and enforce the setup-completion gate. Use when any email-marketing command, skill, or agent needs project configuration, brand file paths, the topic log, or must verify that /setup-email-marketing has been completed.
---

# Email Marketing Config

Every email-marketing component reads its client-specific context through this skill. The plugin itself is brand-agnostic: **all** client specifics (platform, credentials, identity/facts, voice, sections, topics) live in the consuming client project.

## Canonical setup-check protocol

Run this before doing ANY email-marketing work. Never proceed with guessed or partial config.

1. Resolve the project root: the current working directory, or `git rev-parse --show-toplevel` if inside a git repo.
2. Look for `<root>/email-marketing/config.yaml`.
3. Parse it. Require `version: 1` and `setup.completed: true`.
4. If the file is missing, unparseable, or incomplete → **stop immediately** and tell the user:
   > Email marketing isn't configured for this project yet. Run `/setup-email-marketing` first.
   Subagents return that sentence as their result so the orchestrator surfaces it.

## Config resolution

- Config file: `email-marketing/config.yaml` (schema: [references/config-schema.md](references/config-schema.md))
- Brand identity/facts: path in `brand.about_file` (setup resolves `./ABOUT.md`, falling back to `_configuration/references/ABOUT.md`)
- Brand voice: path in `brand.soul_file` (setup resolves `./SOUL.md`, falling back to `_configuration/references/SOUL.md`)
- Brand visuals: path in `brand.design_file` (same resolution for `DESIGN.md`)
- Topic suggestion log: `email-marketing/references/topic-researcher.md` (format: [references/topic-log-format.md](references/topic-log-format.md))
- Analytics reports: `email-marketing/reports/analytics/`
- Drafts: `email-marketing/drafts/YYYY-mm-dd/` — one folder per issue, date-named; inside it `YYYY-mm-dd.html` (body) and `YYYY-mm-dd.meta.yaml`

## Validation rules

| Condition | Requirement |
|---|---|
| `delivery.mode: api_draft` | `audience.list_id` present; `platform.connection` set |
| `platform.connection: api_key` | `platform.auth_env_var` present (env var NAME only — never a value) |
| `platform.connection: mcp` | `platform.mcp_server_name` present and that server exists in the client's `.mcp.json` |
| `platform.name: moego` | `delivery.mode` must be `file_only` (no public campaign API) |
| always | No credential values anywhere in config.yaml. If you find one, warn the user and help move it to `.env`. |

## Degraded modes (warn, don't block)

- `brand.about_file: null` → rely on `brand.industry` / `brand.audience_description` / `brand.website` from config; never invent business specifics (services, offers, credentials); warn once.
- `brand.soul_file: null` → write in a neutral, professional voice and prefix every produced draft with a visible warning that brand voice guidelines were unavailable.
- `brand.design_file: null` → skip image generation styling cues; use safe defaults; warn.
- Higgsfield MCP tools unavailable → produce a no-image layout; never block the pipeline on images.
- Platform API unreachable in `api_draft` mode → fall back to file-only output for this issue and tell the user why.

## Credentials handling

- Secrets live only in the client project's `.env` (verify it is gitignored; if not, warn before touching it).
- Shell state does not persist between Bash calls — source inline every time:
  `set -a; source .env; set +a; curl ...`
- Read-only endpoints (ping, list fetch, reports) may be called freely. Campaign-creation calls happen in the main conversation where the user can see them. Send/schedule endpoints are forbidden everywhere — see the deny-list in each platform reference under `skills/email-platforms/references/`.
