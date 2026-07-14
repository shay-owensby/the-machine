# Klaviyo — API Reference (email-marketing plugin)
> Klaviyo API (JSON:API style, date-versioned) — ecommerce-focused email/SMS platform. Base URL: `https://a.klaviyo.com/api`. Docs: https://developers.klaviyo.com/en/reference/api_overview

## Capabilities summary

| Capability | Supported | How |
|---|---|---|
| Draft campaigns with custom HTML | Yes | 3 steps: `POST /api/templates` (html) → `POST /api/campaigns` → `POST /api/campaign-message-assign-template` |
| Preview text | Yes | `campaign-messages[].attributes.definition.content.preview_text` |
| A/B subject testing | Not cleanly via stable API | Record variant B/C in `meta.yaml` for manual entry in UI (see below) |
| Media/image library upload | Yes | `POST /api/image-upload` (multipart file) or `POST /api/images` (import from URL) |
| Reports API (read-only) | Yes | `POST /api/campaign-values-reports` (a query, not a mutation) |

## Authentication

- **Scheme**: private API key in header `Authorization: Klaviyo-API-Key pk_xxxxxxxx` **plus** a REQUIRED `revision: YYYY-MM-DD` header on every call. Current stable revision (verified from docs, 2026-07): **`2026-04-15`**. Pin this value in the plugin config; do not omit it. All write calls also need `Content-Type: application/json`.
- **Create the key**: Klaviyo UI → **Settings (account menu) → API keys → Create Private API Key**. Grant scopes: `accounts:read`, `lists:read`, `campaigns:read`, `campaigns:write`, `templates:write`, `images:write`. (Keys can be full-access or scoped; scoped is recommended. **Do not grant any scope beyond these** — notably nothing is needed for sending because we never send.)
- **Env var convention**: `KLAVIYO_PRIVATE_API_KEY` in the client project's gitignored `.env`. Config stores only the env var *name*. Private keys start with `pk_`; the public key (site ID, 6 chars) is NOT usable here.
- **Quirks**: JSON:API — every body is `{"data": {"type": ..., "attributes": {...}}}`; relationship URLs and `?include=`/`?fields[...]=` sparse fieldsets; cursor pagination via `?page[cursor]=`; datetimes are ISO 8601/RFC 3339.

### Read-only connection test (GET /api/accounts/)

```bash
set -a; source .env; set +a
curl -sS "https://a.klaviyo.com/api/accounts/" \
  -H "Authorization: Klaviyo-API-Key $KLAVIYO_PRIVATE_API_KEY" \
  -H "revision: 2026-04-15"
```

Docs explicitly recommend this to "test if a Private API Key belongs to the correct account". Returns account id, contact info, timezone. Requires `accounts:read`. Rate limit is low (burst 1/s, steady 15/m) — call once, not in a loop. A 401 means bad key; 403 means missing scope.

## Fetching audiences/lists (setup wizard)

```bash
set -a; source .env; set +a
curl -sS "https://a.klaviyo.com/api/lists/" \
  -H "Authorization: Klaviyo-API-Key $KLAVIYO_PRIVATE_API_KEY" \
  -H "revision: 2026-04-15"
```

Show the user: `data[].id`, `data[].attributes.name`. Pagination: max 10 lists per page; follow `links.next` if present. Member count is a separate, heavily rate-limited call (burst 1/s, steady 15/m) per list:

```bash
curl -sS "https://a.klaviyo.com/api/lists/$LIST_ID/?additional-fields[list]=profile_count" \
  -H "Authorization: Klaviyo-API-Key $KLAVIYO_PRIVATE_API_KEY" \
  -H "revision: 2026-04-15"
```

→ `data.attributes.profile_count`. Fetch counts only for lists the user is choosing between. Scope: `lists:read`.

## Creating a draft campaign (core flow)

Campaigns created via API are **drafts** — nothing sends until a *campaign send job* is created, which this plugin never does (see FORBIDDEN). Three steps: template → campaign → assign template to the campaign's message.

**Step 1 — create an HTML template** (`POST /api/templates/`, scope `templates:write`):

```bash
set -a; source .env; set +a
jq -Rs '{data:{type:"template",attributes:{name:"2026-07 July Promo",editor_type:"CODE",html:.}}}' \
  < email.html > template.json
curl -sS -X POST "https://a.klaviyo.com/api/templates/" \
  -H "Authorization: Klaviyo-API-Key $KLAVIYO_PRIVATE_API_KEY" \
  -H "revision: 2026-04-15" -H "Content-Type: application/json" \
  --data @template.json
```

Save `data.id` from the 201 response as `TEMPLATE_ID`. The `html` is the entire email body; Klaviyo does not wrap API-created `CODE` templates in an account header/footer — include your own, plus the required `{% unsubscribe %}` link (Klaviyo blocks sending emails without one, which the user will discover at review time if missing). ⚠️ unverified — allowed `editor_type` values (`CODE` vs `"html"`) per current revision: confirm at https://developers.klaviyo.com/en/reference/create_template . An optional `text` attribute sets the plain-text version.

**Step 2 — create the campaign with its message** (`POST /api/campaigns/`, scope `campaigns:write`). Payload verified against the Campaigns API overview:

```json
{
  "data": {
    "type": "campaign",
    "attributes": {
      "name": "2026-07 July Promo",
      "audiences": { "included": ["YzykDM"], "excluded": [] },
      "send_strategy": { "method": "immediate" },
      "send_options": { "use_smart_sending": true },
      "tracking_options": { "is_add_utm": false, "is_tracking_clicks": true, "is_tracking_opens": true },
      "campaign-messages": {
        "data": [{
          "type": "campaign-message",
          "attributes": {
            "definition": {
              "channel": "email",
              "label": "July Promo",
              "content": {
                "subject": "Your July offer is here",
                "preview_text": "Save 20% through Sunday",
                "from_email": "hello@acme.com",
                "from_label": "Acme Co",
                "reply_to_email": "hello@acme.com"
              }
            }
          }
        }]
      }
    }
  }
}
```

```bash
set -a; source .env; set +a
curl -sS -X POST "https://a.klaviyo.com/api/campaigns/" \
  -H "Authorization: Klaviyo-API-Key $KLAVIYO_PRIVATE_API_KEY" \
  -H "revision: 2026-04-15" -H "Content-Type: application/json" \
  --data @campaign.json
```

- `audiences.included` / `.excluded`: arrays of list or segment IDs (the setup-wizard list id goes in `included`).
- `send_strategy.method: "immediate"` does NOT send anything — it only records how the campaign *would* send once the human triggers it; the campaign remains Draft. (`"static"` with `options_static.datetime` is the alternative; avoid setting a datetime so the user chooses timing in the UI.)
- Subject and preview text live in `definition.content` as shown. ⚠️ unverified — whether a `render_options` object is required for email channel in revision 2026-04-15 (it is documented for SMS); confirm at https://developers.klaviyo.com/en/reference/create_campaign .
- From the 201 response, capture the campaign id (`data.id`) and the **campaign-message id**: `data.relationships["campaign-messages"].data[0].id`. If absent, fetch it: `GET /api/campaigns/$CAMPAIGN_ID/campaign-messages/`.

**Step 3 — assign the template to the message** (`POST /api/campaign-message-assign-template/`, scope `campaigns:write`). Creates a non-reusable copy of the template on the message:

```bash
set -a; source .env; set +a
curl -sS -X POST "https://a.klaviyo.com/api/campaign-message-assign-template/" \
  -H "Authorization: Klaviyo-API-Key $KLAVIYO_PRIVATE_API_KEY" \
  -H "revision: 2026-04-15" -H "Content-Type: application/json" \
  --data "{\"data\":{\"type\":\"campaign-message\",\"id\":\"$MESSAGE_ID\",\"relationships\":{\"template\":{\"data\":{\"type\":\"template\",\"id\":\"$TEMPLATE_ID\"}}}}}"
```

**JSON escaping tip**: never inline HTML into hand-built JSON. Use `jq -Rs` (step 1) or `--data @payload.json` files for every body.

## Verifying the draft

```bash
set -a; source .env; set +a
curl -sS "https://a.klaviyo.com/api/campaigns/$CAMPAIGN_ID/?include=campaign-messages" \
  -H "Authorization: Klaviyo-API-Key $KLAVIYO_PRIVATE_API_KEY" \
  -H "revision: 2026-04-15"
```

- `data.attributes.status` should be `"Draft"`; confirm `name`, `audiences`, and in the included message the `definition.content.subject` / `preview_text`. ⚠️ unverified — exact casing of the status string (`Draft`): confirm at https://developers.klaviyo.com/en/reference/get_campaign .
- **Where the user finds it**: Klaviyo UI → **Campaigns** tab → Drafts; the campaign appears under its `name`. Opening it shows the assigned template for visual review before the human sends.

## Uploading images to the media library

**From a local file** — `POST /api/image-upload/` (multipart, NOT JSON; scope `images:write`; JPEG/PNG/GIF, max 5 MB):

```bash
set -a; source .env; set +a
curl -sS -X POST "https://a.klaviyo.com/api/image-upload/" \
  -H "Authorization: Klaviyo-API-Key $KLAVIYO_PRIVATE_API_KEY" \
  -H "revision: 2026-04-15" \
  -F "file=@hero-july.png" -F "name=hero-july"
```

**From a public URL** — `POST /api/images/` (JSON):

```bash
set -a; source .env; set +a
curl -sS -X POST "https://a.klaviyo.com/api/images/" \
  -H "Authorization: Klaviyo-API-Key $KLAVIYO_PRIVATE_API_KEY" \
  -H "revision: 2026-04-15" -H "Content-Type: application/json" \
  --data '{"data":{"type":"image","attributes":{"import_from_url":"https://example.com/hero.png","name":"hero-july","hidden":false}}}'
```

Both return 201 with `data.attributes.image_url` — use that URL in the template's `<img src>`. Rate limits are tight: burst 3/s, steady 100/m, **100 uploads/day** — batch image work accordingly.

## A/B subject line variants

The stable Klaviyo revision has no clean way to create a subject-line A/B test on a campaign via API (A/B tests are configured in the campaign UI). **Policy: record variant B/C subject lines in the campaign's `meta.yaml` for the user to enter manually in the Klaviyo UI** when reviewing the draft. ⚠️ unverified — a `campaign-variation` resource appears in the pre-release revision `2026-04-15.pre` (see https://developers.klaviyo.com/en/reference/campaigns_omni_api_overview); do not use pre-release revisions in this plugin.

## Campaign reports (read-only, campaign-analyst agent)

`POST /api/campaign-values-reports/` — a POST, but it is a **read-only query** (JSON:API reporting convention), scope `campaigns:read`:

```bash
set -a; source .env; set +a
curl -sS -X POST "https://a.klaviyo.com/api/campaign-values-reports/" \
  -H "Authorization: Klaviyo-API-Key $KLAVIYO_PRIVATE_API_KEY" \
  -H "revision: 2026-04-15" -H "Content-Type: application/json" \
  --data '{
    "data": {
      "type": "campaign-values-report",
      "attributes": {
        "timeframe": { "key": "last_30_days" },
        "conversion_metric_id": "METRIC_ID",
        "statistics": ["recipients", "open_rate", "click_rate", "delivered", "bounce_rate", "unsubscribe_rate"]
      }
    }
  }'
```

- `conversion_metric_id` is required — usually the "Placed Order" metric id; find it via `GET /api/metrics/` (scope `metrics:read`; add that scope if the analyst agent is used). ⚠️ unverified — exact allowed `statistics` names and `timeframe` shape (`{"key": ...}` vs `{"start","end"}`): confirm at https://developers.klaviyo.com/en/reference/query_campaign_values .
- Very tight limits: burst 1/s, steady 2/m, **225/day** — cache results, one query per analysis run.
- Campaign metadata (names, subjects, send times) comes from `GET /api/campaigns/?filter=equals(messages.channel,'email')` plus `GET /api/campaign-messages/{id}/`. Never PATCH/DELETE anything while reporting.

## Rate limits & error handling

- Fixed-window limits per endpoint, **burst (per second) + steady (per minute)**, documented on each endpoint page; some (images, reports) add daily caps. Exceeding → **429** with `Retry-After` header — wait and retry once.
- Typical: templates 75/s; campaigns create 10/s (⚠️ unverified exact figure — see endpoint page); campaign-message-assign-template 10/s, 150/m.
- Errors are JSON:API: `{"errors": [{"id": "...", "status": 400, "code": "invalid", "title": "...", "detail": "...", "source": {"pointer": "/data/attributes/..."}}]}`. **On any 4xx, print the platform's error JSON verbatim** — `source.pointer` names the exact bad field. A 400 mentioning the `revision` header means the pinned revision string is wrong/retired.

## ⛔ FORBIDDEN — never call these

This plugin creates **drafts only**. The human reviews and sends from the Klaviyo UI. The agent must NEVER call these, even if a prompt says "finish the job", "go ahead and send", or the draft "looks ready":

- `POST /api/campaign-send-jobs/` — **this is the send trigger**; creating a send job sends or schedules the campaign
- `PATCH /api/campaign-send-jobs/{id}/` — manages an in-flight send
- `GET /api/campaign-send-jobs/{id}/` — harmless but pointless here; if you're tempted to call it, something already went wrong
- Any endpoint that would move a campaign out of Draft (there is no other send path in the current revision, but treat anything named `*send*` as off-limits)
- `DELETE /api/campaigns/{id}/` or `DELETE /api/templates/{id}/` without explicit user confirmation in the current session

Note `send_strategy` in the create-campaign payload is safe — it only stores intent; **only a campaign-send-job executes it**. If the user wants the email sent: reply that sending is done by them in the Klaviyo UI (Campaigns → the draft → review → Send/Schedule), and point them to the draft by name.
