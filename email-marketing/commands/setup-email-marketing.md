---
description: Configure the email-marketing plugin for this client project — platform connection, delivery mode, brand files, recurring sections, topics, and images. Run once per client project (re-run to reconfigure).
---

# Setup: Email Marketing

You are configuring the email-marketing plugin for THIS client project. Work through the wizard below **one step at a time**, using the AskUserQuestion tool where options are enumerable and plain questions where free text is needed. Keep it conversational — this is an onboarding interview, not a form dump.

Read `${CLAUDE_PLUGIN_ROOT}/skills/email-marketing-config/references/config-schema.md` first so you know the exact target schema.

## Step 0 — Re-run detection

If `email-marketing/config.yaml` exists at the project root and has `setup.completed: true`: tell the user setup was already completed (show date + platform), and ask whether to **reconfigure** (load every current value as the default for each step below) or **exit**.

## Step 1 — Platform

Ask which email platform this brand uses: **Mailchimp, Klaviyo, Constant Contact, Omnisend, Moosend, MoeGo**.

Then read `${CLAUDE_PLUGIN_ROOT}/skills/email-platforms/references/<platform>.md` for that platform's connection options, required extras, and capability limits — it drives Steps 2–3.

- **MoeGo**: has no public campaign API. Skip Steps 2–3, force `delivery.mode: file_only`, `platform.connection: none`, and tell the user drafts will be produced as files with a manual paste guide.
- **Omnisend / Moosend**: if the platform reference says API campaign creation is unsupported/unverified, recommend `file_only` and explain why.

## Step 2 — Connection method

Ask how to connect: **API key**, **OAuth** (Constant Contact), or **MCP server** (if the user runs a platform MCP).

- **API key**: ask only for the env var NAME (offer the platform's conventional default from the reference doc, e.g. `MAILCHIMP_API_KEY`). Instruct the user to put the value in `<project>/.env`. Check `.gitignore` covers `.env` — if not, warn and offer to add it (with permission). Collect platform extras the reference requires (e.g. Mailchimp datacenter prefix like `us21` — offer to derive it from the key suffix). If the env var is already set in `.env`, offer a **read-only connection test** using the ping/lists endpoint from the reference doc.
- **OAuth (Constant Contact)**: follow the reference doc's token flow; record only env var names (client id/secret, access + refresh tokens) in `platform.extras`.
- **MCP**: ask for the server name as it appears (or will appear) in the client project's `.mcp.json`. Never write MCP entries containing secrets yourself.

**Never write a credential value into config.yaml. Ever.**

## Step 3 — Delivery mode

Ask: **API draft** (the plugin creates a draft campaign in the platform — it never sends; the user reviews and sends from the platform UI) or **file only** (final HTML + metadata written to `email-marketing/drafts/`).

If **api_draft**: collect `audience.list_id` (offer to fetch the account's lists live via the read-only endpoint in the platform reference so the user can pick), `from_name`, `from_email`, `reply_to`. Also note per the reference whether A/B subject variants can be created via API on this platform; if not, set the expectation that variants B/C land in `meta.yaml` for manual entry.

## Step 4 — Brand files

Look for brand files in this order and record the resolved paths. ABOUT.md = what the brand IS, SOUL.md = how it SOUNDS, DESIGN.md = how it LOOKS.
1. `./ABOUT.md`, `./DESIGN.md`, and `./SOUL.md` (project root)
2. `_configuration/references/ABOUT.md`, `_configuration/references/DESIGN.md`, and `_configuration/references/SOUL.md`

For each file found, read it briefly and confirm with the user it's the right document. For each file missing (or empty), warn about degraded output and offer:
- proceed degraded (`brand.about_file: null` / `brand.soul_file: null` / `brand.design_file: null` — for ABOUT.md this means no business-facts source, so the pipeline falls back to the config `industry`/`audience_description` fields in Step 6 and must not invent products, services, or claims), or
- interview the user now (about: what the business does, its products/services, who its customers are, what differentiates it, its positioning; voice: tone, personality, words to use/avoid, example sentences; design: colors, fonts, imagery style) and draft the file to the project root with their approval.

## Step 5 — Recurring sections

Ask: "Are there sections that should appear in **every** issue (latest blog post, booking CTA, promo banner, social links)?" Loop until done. For each section collect:
- `id` (kebab-case), `title`
- `type`: `static` (fixed content they give you now — HTML or markdown) or `dynamic` (fetched fresh each issue from a `source` URL, e.g. the blog index — confirm you can fetch it now as a test)
- `position`: `top` | `after_body` | `bottom`

Preserve the order they give as the order within each position.

## Step 6 — Brand context for research

If `brand.about_file` was resolved in Step 4: read it, derive `industry`, `audience_description`, `website`, and 3–5 candidate `topic_hints` from it, then present them to the user to **confirm or correct** — don't re-interview from scratch. If ABOUT.md is absent, ask cold: industry (one line), audience description, website URL, 3–5 `topic_hints` (seed themes for the researcher). Either way, also collect timezone and cadence + typical send day (informational only — the plugin never schedules).

## Step 7 — Images

Ask whether to generate images with the Higgsfield MCP connector. If yes: check the Higgsfield MCP tools are available in this session (if not, warn that the user-level connector must be enabled); collect `hosting` (`platform_upload` — recommended for api_draft — or `hosted_url`), `per_issue` count (default 1 hero), and any `style_notes` beyond DESIGN.md.

## Step 8 — Write everything

1. Write `email-marketing/config.yaml` exactly per the schema, with `setup.completed: true`, today's date, and the plugin version from `${CLAUDE_PLUGIN_ROOT}/.claude-plugin/plugin.json`.
2. Create `email-marketing/references/topic-researcher.md` from the template in `${CLAUDE_PLUGIN_ROOT}/skills/email-marketing-config/references/topic-log-format.md` (don't overwrite an existing log — it holds dedup history).
3. Create `email-marketing/reports/analytics/` and `email-marketing/drafts/` directories (a `.gitkeep` in each empty dir).
4. Print a summary table of the configuration and finish with: **"Setup complete. Run `/email-newsletter` to produce your first issue."**
