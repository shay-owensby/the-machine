# email-marketing

A brand-agnostic Claude Code plugin that acts as a per-client **email marketing agent team**. It produces a recurring (typically weekly) newsletter end-to-end: kickoff input from you, trend research with a deduplicated topic log, brand-voiced copywriting, AI-generated imagery, adversarial QA, and delivery of a **draft** to the client's email platform.

> **Safety rule baked into every component: this plugin never sends or schedules an email.** It creates drafts (via API or as files). A human reviews and sends from the platform UI.

## Supported platforms

| Platform | Draft via API | Notes |
|---|---|---|
| Mailchimp | ✅ | Marketing API v3 |
| Klaviyo | ✅ | Template → campaign flow |
| Constant Contact | ✅ | V3 API, OAuth2 (rotating refresh tokens) |
| Omnisend | ✅ | Template import → draft campaign flow |
| Moosend | ✅* | Drafts via API, but HTML imports only from a public URL (WebLocation) — see reference |
| MoeGo | file-only | No campaign API; manual rebuild in MoeGo's builder |

## Quick start (in a client project)

1. Install/enable this plugin, then run **`/setup-email-marketing`** in the client project. The wizard configures: platform + connection (env var names only — secrets live in the client's gitignored `.env`), delivery mode (`api_draft` or `file_only`), recurring sections, brand file locations, industry/topic hints, and image preferences.
2. Run **`/email-newsletter`** each week. It always starts by asking: *"Anything specific to include in this week's email?"*

## What lands in the client project

```
<client>/
├── DESIGN.md                       # brand visual guidelines (read, never written)
├── SOUL.md                         # brand voice guidelines (read, never written)
└── email-marketing/
    ├── config.yaml                 # per-client config (no secrets — env var names only)
    ├── references/
    │   └── topic-researcher.md     # topic suggestion log — newest entries at the TOP; dedup source of truth
    ├── reports/
    │   └── analytics/              # campaign-analyst markdown reports (YYYY-mm-dd-campaign-analysis.md)
    └── drafts/
        └── YYYY-mm-dd/             # one folder per issue
            ├── YYYY-mm-dd.html         # email body only (header/footer live on the platform)
            ├── YYYY-mm-dd.meta.yaml    # subject + A/B variants, preview text, topic, campaign_id, status
            └── images/
```

Brand files are looked up at the client project root (`./DESIGN.md`, `./SOUL.md`) with a fallback to `_configuration/references/`.

## Architecture

**Commands** (orchestration):
- `commands/setup-email-marketing.md` — per-client configuration wizard; everything else refuses to run until it has completed.
- `commands/email-newsletter.md` — the weekly pipeline: kickoff question → parallel research + analytics subagents → user picks topic → images (Higgsfield MCP) → copywriting subagent → QA subagent → user review → draft delivery → bookkeeping.

**Agents** (isolated subagent system prompts):
- `agents/topic-researcher.md` — 1–3 trending topic candidates with rationale + sources; **always** prepends every suggestion to `email-marketing/references/topic-researcher.md` and never repeats a logged topic.
- `agents/email-copywriter.md` — subject line A/B/C, preview text, and email-client-safe HTML body in the voice of `SOUL.md`.
- `agents/email-qa.md` — adversarial pre-flight: links, spam triggers, rendering pitfalls, size, accessibility, brand compliance.
- `agents/campaign-analyst.md` — read-only past-campaign stats via the platform API; **always** exports a markdown report to `email-marketing/reports/analytics/`.

**Skills** (shared expertise):
- `skills/email-marketing-config/` — config loading/validation + the canonical setup-check protocol. References: `config-schema.md`, `topic-log-format.md`.
- `skills/email-platforms/` — platform API dispatch and draft-only safety rules. References: one verified API doc per platform.
- `skills/email-html/` — email-client-safe HTML authoring. References: `html-boilerplate.md`, `qa-checklist.md`.
- `skills/email-topic-research/` — research method, tool ladder (Semrush MCP → WebSearch → WebFetch), semantic dedup rules.
- `skills/email-images/` — Higgsfield MCP workflow, DESIGN.md-driven prompting, image hosting strategy.

## MCP

`mcp.json` ships empty on purpose. Higgsfield (image generation) and Semrush (trend research) are user-level connectors; email-platform MCP servers carry per-client auth and belong in the **client project's** `.mcp.json`, configured during setup.

## Credentials policy

- API keys/tokens are stored **only** in the client project's `.env` (which must be gitignored). `config.yaml` records env var **names**, never values.
- All runtime calls source `.env` inline per invocation: `set -a; source .env; set +a; curl ...`
- Only read-only endpoints are called automatically; campaign creation endpoints run visibly in the main conversation; send/schedule endpoints are on an explicit deny-list in every platform reference.
