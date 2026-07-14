# Omnisend — API Reference (email-marketing plugin)

> Omnisend is an ecommerce email/SMS marketing platform. Current API base URL: `https://api.omnisend.com/api` (date-versioned via `Omnisend-Version` header; current: `2026-03-15`) — doc home: https://api-docs.omnisend.com

Older path-versioned APIs (`https://api.omnisend.com/v3`, v5) still exist, but the flows below use the current versioned API — it is the one that supports campaign creation.

## Capabilities summary

| Capability | Supported | How |
|---|---|---|
| Draft campaigns with custom HTML | **Yes — two-step** | 1) `POST /api/email-templates/import` with raw `html` → `templateID`; 2) `POST /api/campaigns` referencing that `templateID`. Campaign is created in `draft` status. There is NO direct `html` field on the campaign itself. |
| Preview text (preheader) | Yes | `content.email.preheader` (max 250 chars). |
| A/B subject testing | Partial / unclear | Campaign object has an `abTest` field; details thin — record variants in meta.yaml (see below). |
| Media / image upload | **No** | No public media-upload endpoint. Host images at the client's website or upload via the Omnisend UI. |
| Reports API | Yes | `POST /api/analytics/reports` (aggregated metrics, filter by campaign ID). |

Delivery mode: **api_draft** (current API). If the account/key cannot use the versioned API, fall back to **file_only** + manual paste (see "Manual fallback" below). The agent must NEVER call the send endpoint (see ⛔ at the bottom).

## Authentication

Simple API key. **Header (current versioned API):** `Authorization: Omnisend-API-Key <key>` plus the required `Omnisend-Version: 2026-03-15` header on every request. Verified at https://api-docs.omnisend.com/reference/authentication.md
(The legacy v3 API instead used the `X-API-KEY: <key>` header on `https://api.omnisend.com/v3/...` — still documented, but not needed for these flows.)

**Create the key in the UI:** Omnisend app → Store settings → Integrations & API → **API keys** (direct link: https://app.omnisend.com/integrations/api-keys). Give it a descriptive name; copy the key once.

Env var (value lives only in the client project's gitignored `.env`; plugin config stores the env var NAME only):

```
OMNISEND_API_KEY=...
```

**Connection test (read-only)** — list segments (shell state does not persist; source `.env` inline in every Bash call):

```bash
set -a; source .env; set +a; \
curl -s "https://api.omnisend.com/api/segments" \
  -H "Authorization: Omnisend-API-Key $OMNISEND_API_KEY" \
  -H "Omnisend-Version: 2026-03-15"
```

200 with a JSON body = key works. 401 = bad/revoked key — ask the user to re-create it in the UI and update `.env`.

## Fetching audience segments (setup wizard)

Omnisend targets **segments** (not static lists). Same call as the connection test:

```bash
set -a; source .env; set +a; \
curl -s "https://api.omnisend.com/api/segments" \
  -H "Authorization: Omnisend-API-Key $OMNISEND_API_KEY" \
  -H "Omnisend-Version: 2026-03-15"
```

Show the user each segment's `id` and `name`; store the chosen segment ID(s) in the plugin config. Omitting segments on a campaign targets **all subscribers** — confirm with the user which they want. (Rate limit on list endpoints: 100 req/min.)

## Creating a draft campaign (core flow)

**Step 1 — import the HTML as an email template.** `POST /api/email-templates/import` accepts raw HTML (`name` 1–255 chars + `html`, request body max **1 MB**). Omnisend extracts `<style>` from `<head>` into the template's style block and uses the `<body>` content as the template body. Verified at https://api-docs.omnisend.com/reference/email-templates.md

**JSON escaping tip:** never inline HTML into a JSON string by hand — build the payload with `jq --rawfile`:

```bash
set -a; source .env; set +a; \
jq -n --rawfile html email.html --arg name "2026-07 Newsletter body" \
  '{name: $name, html: $html}' > template.json && \
curl -s -X POST "https://api.omnisend.com/api/email-templates/import" \
  -H "Authorization: Omnisend-API-Key $OMNISEND_API_KEY" \
  -H "Omnisend-Version: 2026-03-15" \
  -H "Content-Type: application/json" \
  --data @template.json
```

Response includes the template `id` (24-char hex). Save it to meta.yaml. HTML constraints: unsupported tags (`<script>`, `<iframe>`, ...) are rejected; images must be absolute URLs.

**Step 2 — create the campaign referencing the template.** Campaigns are created in **`draft` status** by default (verified at https://api-docs.omnisend.com/reference/campaigns.md). Required email content fields: `subject` (≤250), `senderName` (≤250), `templateID`. Optional: `preheader` (preview text, ≤250), `senderEmail` (must be on a verified domain), `replyToEmail`.

```bash
set -a; source .env; set +a; \
jq -n \
  --arg name "2026-07 Newsletter" \
  --arg subject "July news from Acme" \
  --arg preheader "The three things worth your time this month" \
  --arg sender "Acme Co" \
  --arg tid "$TEMPLATE_ID" \
  --arg seg "$SEGMENT_ID" \
  '{
    name: $name, type: "regular", channel: "email",
    content: { email: { subject: $subject, preheader: $preheader,
                        senderName: $sender, templateID: $tid } },
    audience: { includedSegmentIDs: [$seg] }
  }' > campaign.json && \
curl -s -X POST "https://api.omnisend.com/api/campaigns" \
  -H "Authorization: Omnisend-API-Key $OMNISEND_API_KEY" \
  -H "Omnisend-Version: 2026-03-15" \
  -H "Content-Type: application/json" \
  --data @campaign.json
```

- **Omit `sendingSettings` entirely.** Scheduling info belongs to the human. ⚠️ unverified — docs state created campaigns default to `draft` but don't explicitly state the effect of an omitted `sendingSettings`; confirm at https://api-docs.omnisend.com/reference/campaigns.md. Regardless: never include `sendingSettings.strategy`/`scheduledAt`, and never call `/send`.
- Omitting `audience` targets all subscribers — only do this if the user explicitly chose "everyone".
- Edits: `PATCH /api/campaigns/{id}` partially updates email content fields (subject, preheader, templateID...). Only `draft` campaigns can be edited — anything else returns **409 Conflict**.
- Create/update/delete endpoints are limited to **15 req/min**.

## Verifying the draft

```bash
set -a; source .env; set +a; \
curl -s "https://api.omnisend.com/api/campaigns/${CAMPAIGN_ID}" \
  -H "Authorization: Omnisend-API-Key $OMNISEND_API_KEY" \
  -H "Omnisend-Version: 2026-03-15"
```

Confirm `status` is `"draft"` (other statuses: scheduled, started, paused, sent, canceled, onHold, error, stopped, expired — if it's anything but `draft`, stop and tell the user). In the UI the user finds it under **Campaigns** in the Omnisend app, opens the draft, previews (the imported template renders in the email builder), and sends it themselves.

## Manual fallback (file_only mode)

If the API key can't create templates/campaigns (older account, restricted key, endpoint errors): set `delivery.mode: file_only`, write `email.html`, `subject.txt`, `preview-text.txt` to the campaign folder, and give the user these paste instructions:

1. Omnisend app → **Store settings → Saved templates → Import template** → choose **Paste in code** (or **Import HTML** for the .html file). Remove `<!DOCTYPE>` and `<head>` tags first — Omnisend strips/rejects them. Verified at https://support.omnisend.com/en/articles/2964086-import-custom-html-email-templates
2. Then **Campaigns → New campaign → email**, pick the saved template, and paste the subject + preview text from the files.
3. Alternative for snippets: the email builder's **HTML block** (drag "Custom HTML" item into the layout) — body-content HTML only; `<script>`, `<iframe>`, `<div>`, `<font>` unsupported.

## Uploading images

**No public media/asset upload API.** Host images at the client's website (absolute HTTPS URLs in the HTML) or have the user upload via the Omnisend UI image picker and copy the URL. Imported-template HTML must reference full URLs — relative paths fail import.

## A/B subject line variants

The campaign object includes an `abTest` field, but the docs we could fetch don't spell out its shape or whether the public API can configure subject-line splits. ⚠️ unverified — confirm at https://api-docs.omnisend.com/reference/campaigns.md. Until confirmed: **record both subject variants in the campaign's meta.yaml** and instruct the user to configure the A/B test manually in the Omnisend campaign editor before sending.

## Campaign reports (read-only — campaign-analyst agent)

`POST /api/analytics/reports` (yes, POST — it's a query API and is read-only). Up to 4 queries per request; metrics grouped by message **send date**. Verified at https://api-docs.omnisend.com/reference/reports.md

```bash
set -a; source .env; set +a; \
jq -n --arg cid "$CAMPAIGN_ID" '{
  queries: [{
    alias: "campaign-stats",
    metrics: [{name:"sent"},{name:"openedUnique"},{name:"openRate"},
              {name:"clickedUnique"},{name:"clickRate"},{name:"attributedRevenue"}],
    dateRange: {interval: "last30Days"},
    filters: [{name:"marketingActivityID", operator:"in", values:[$cid]}]
  }]
}' > report.json && \
curl -s -X POST "https://api.omnisend.com/api/analytics/reports" \
  -H "Authorization: Omnisend-API-Key $OMNISEND_API_KEY" \
  -H "Omnisend-Version: 2026-03-15" \
  -H "Content-Type: application/json" \
  --data @report.json
```

Useful metrics: `sent`, `failed`, `failRate`, `markedAsSpamRate`, `openedUnique`, `openRate`, `clickedUnique`, `clickRate`, `attributedRevenue`, `attributedOrders`. Dimensions: `timestamp` (hour/day/week/month), `marketingActivityID`, `messageChannel`, `marketingActivityType`. Constraints: custom ranges ≤1 year; daily granularity ≤60 days; hourly ≤7 days. **Analytics rate limit: 10 req/min and 55 req/day** — cache results; do not poll.

## Rate limits & error handling

Verified at https://api-docs.omnisend.com/reference/rate-limit-timeouts-errors.md

- List endpoints: **100 req/min** - Create/update/delete: **15 req/min** - Analytics: **10 req/min, 55 req/day**.
- Exceeding limits → **429** with a problem+json body (`{"type":"https://problems.omnisend.com/rate-limit-exceeded", "title":"Rate limit exceeded", "status":429}`); some responses include a `retryAfter` (seconds) in the body. Back off (30s → 120s → 480s) — for analytics, just stop and report.
- On any 4xx: print the platform error JSON **verbatim** to the user, then stop. 402 on campaign endpoints = audience exceeds the account's billing tier. 409 on PATCH = campaign is no longer a draft.

## ⛔ FORBIDDEN — never call these

Sending is a HUMAN action performed in the Omnisend UI. The agent must never call:

- `POST /api/campaigns/{id}/send` — this single endpoint both **sends immediately AND schedules** ("start sending or schedule the campaign"). NEVER call it, with any payload.
- `POST /api/campaigns/{id}/cancel` — don't manipulate in-flight sends either.
- Any legacy send-triggering endpoint on `https://api.omnisend.com/v3/...` (e.g. v3 campaign start/send actions).
- Do not set `sendingSettings` (`strategy`, `scheduledAt`) on POST/PATCH `/api/campaigns` — that is scheduling by another name.

No test-send endpoint was found in the public API; test sends happen in the Omnisend UI ("send test" in the campaign editor) by the human. If any workflow suggests scheduling "for convenience": refuse. Drafts only.
