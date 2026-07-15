---
description: Configure the grants plugin for this client project — capture the organization's identity, mission, and current funding goals into the context files the grant-researcher scores against. Run once per client project (re-run to update).
---

# Setup: Grants

You are configuring the grants plugin for THIS client project. The plugin is brand-agnostic — every skill and agent reads the organization's specifics from three context files plus a small marker config, all written here. Your job is a short onboarding interview that produces those files, so the grant-researcher (and future grants skills) have real context to work from.

Work through the steps below **one at a time**, conversationally — this is an interview, not a form dump. Use the AskUserQuestion tool where options are enumerable; plain questions where free text is needed. The richer these files are, the sharper every fit score will be, so draw the user out — but never invent facts to fill a gap.

## Step 0 — Re-run detection

Resolve the project root (current directory, or `git rev-parse --show-toplevel`). If `grants/config.yaml` exists with `setup.completed: true`, tell the user setup was already done (show the date), read the current context files, and ask whether to **update** them (load existing content as the starting point for each step) or **exit**.

## Step 1 — Organization identity → `grants/references/ORGANIZATION.md`

This is what drives the **eligibility gate**, so completeness here matters most. Collect:

- **Legal name** (and any DBA)
- **Location** — city, state/province, country. Funders are almost always geographically scoped, so be precise.
- **Legal / tax status** — e.g. 501(c)(3) public charity, fiscal-sponsored, government entity, school, tribal org, for-profit, individual. Capture the EIN (or local registration number) if the user has it.
- **Founded / age**, approximate **annual budget** and **staff size** (grants often have budget floors/ceilings)
- **Populations / communities served** and geographic reach of the work
- **What the org does** — programs and activities, in plain terms
- **Assets on hand for applications** — does the org have audited financials, recent 990s/annual reports, a board list, a logic model? (These affect Readiness scoring later.)

Write it as clear markdown under headed sections. If the user already drafted `ORGANIZATION.md`, read it, confirm what's there, and fill gaps rather than overwriting good content.

## Step 2 — Mission → `grants/references/MISSION-STATEMENT.md`

Capture the organization's mission statement (and vision/values if offered). If the org has a formal statement, use it verbatim; if not, help the user articulate a concise one. This anchors the **Mission & Program Alignment** dimension, the heaviest part of the score.

## Step 3 — Current goals & funding needs → `grants/references/GOALS.md`

This is what the researcher matches award amounts and eligible-use against. Ask about:

- **Current priorities / projects** for the next 6–18 months
- **What funding is needed for** — operating support, a specific project, capital/equipment, seed funding, a program expansion
- **Rough amounts** needed, and any **matching-funds** capacity (some grants require cost-share)
- **Grant-type preferences or exclusions** — anything the org can't or won't take (e.g. can't meet large matches, won't take restricted faith-based funding, only wants general operating support)

Write these as a prioritized list with amounts where known.

## Step 4 — Search scope (optional, light)

Briefly confirm the search boundaries so the researcher doesn't waste effort:

- Which **funder types** are in scope — government (federal/state/local), private/family foundations, community foundations, corporate giving? (Default: all.)
- Any **geographic limits** beyond the org's location (e.g. "national grants are fine" vs. "local only").

Keep this light — it's guidance, not a hard config. Note the answers in `GOALS.md` under a short "Grant search scope" heading rather than a separate file.

## Step 5 — Write everything

1. Write/update the three context files: `grants/references/ORGANIZATION.md`, `grants/references/MISSION-STATEMENT.md`, `grants/references/GOALS.md`. Preserve any good existing content; never blank a file the user already filled.
2. Write `grants/config.yaml`:
   ```yaml
   version: 1
   setup:
     completed: true
     date: "YYYY-MM-DD"          # today's date — run `date +%Y-%m-%d`
     plugin_version: "X.Y.Z"      # from ${CLAUDE_PLUGIN_ROOT}/.claude-plugin/plugin.json
   context:
     organization: grants/references/ORGANIZATION.md
     mission: grants/references/MISSION-STATEMENT.md
     goals: grants/references/GOALS.md
   ```
3. Create the `grants/reports/research/` directory (add a `.gitkeep` so the empty dir is tracked). Do **not** create `grants/references/research-log.md` — the researcher creates it on first run and owns its history.
4. Print a short summary of what was captured and finish with: **"Setup complete. Run the grant-researcher to find and score live grants for this organization."**

## Guardrails

- **Never write a credential or secret** into `config.yaml` or the context files.
- **Never invent org facts** (tax status, budget, EIN, geography). If the user doesn't know something, leave it clearly marked as unknown — a blank is safer than a wrong eligibility signal.
- The context files are the user's source of truth; treat existing content as authoritative and additive-only unless they ask you to rewrite it.
