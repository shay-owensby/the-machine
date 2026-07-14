# Constant Contact — API Reference (email-marketing plugin)

> Constant Contact is an SMB email-marketing platform. API base URL: `https://api.cc.email/v3` — doc home: https://developer.constantcontact.com (V3 API).

## Capabilities summary

| Capability | Supported | How |
|---|---|---|
| Draft campaigns with custom HTML | **Yes** | `POST /v3/emails` with `format_type: 5` (custom code email) + `html_content`. Created in `Draft` status. |
| Preview text (preheader) | Yes | `preheader` field on the campaign activity (format types 3–5). |
| A/B subject-line testing | Yes (API) | `POST /v3/emails/activities/{campaign_activity_id}/abtest` — subject-line only. |
| Media / image upload | Yes | `POST /v3/library/files` (multipart) → hosted URL for use in HTML. |
| Reports API (read-only) | Yes | `/v3/reports/summary_reports/...` and `/v3/reports/email_reports/{campaign_activity_id}/...` |

Delivery mode: **api_draft** — the plugin creates the draft via API; the human reviews and sends from the Constant Contact UI. The agent must NEVER call the schedule or send endpoints (see ⛔ at the bottom).

## Authentication

Constant Contact V3 is **OAuth2 only** — there are no plain API keys. Practical CLI flow:

1. Create an app in the V3 developer portal (https://app.constantcontact.com/pages/dma/portal/) → get client ID + secret.
2. Run the **Authorization Code flow once** (browser): send the user to
   `https://authz.constantcontact.com/oauth2/default/v1/authorize?client_id=...&redirect_uri=...&response_type=code&scope=campaign_data+contact_data+offline_access&state=...`
   then exchange the returned `code` at the token endpoint below. `offline_access` is required to get a refresh token.
3. Thereafter, refresh tokens non-interactively.

- **Token endpoint (exchange + refresh):** `POST https://authz.constantcontact.com/oauth2/default/v1/token`
- **Scopes:** `campaign_data`, `contact_data`, `offline_access` (optionally `account_read`). Verified at https://developer.constantcontact.com/api_guide/server_flow.html
- **Access token TTL:** `expires_in: 28800` (8 hours) per the token response. ⚠️ docs elsewhere also mention 1440 minutes/24h — treat tokens as short-lived and refresh at the start of every session; confirm at https://developer.constantcontact.com/api_guide/server_flow.html
- **Refresh tokens ROTATE:** each refresh response returns a **new** `refresh_token`. The old one is invalidated — after every refresh, the agent must tell the user to update `.env` (or update it for them) with BOTH the new `CC_ACCESS_TOKEN` and the new `CC_REFRESH_TOKEN`.

Env vars (values live only in the client project's gitignored `.env`; plugin config stores env var NAMES only):

```
CC_CLIENT_ID=...
CC_CLIENT_SECRET=...
CC_ACCESS_TOKEN=...
CC_REFRESH_TOKEN=...
```

Refresh call (run at session start; shell state does not persist, so source `.env` inline in every Bash call):

```bash
set -a; source .env; set +a; \
curl -s -X POST \
  -H "Content-Type: application/x-www-form-urlencoded" \
  -H "Authorization: Basic $(printf '%s:%s' "$CC_CLIENT_ID" "$CC_CLIENT_SECRET" | base64)" \
  "https://authz.constantcontact.com/oauth2/default/v1/token?refresh_token=${CC_REFRESH_TOKEN}&grant_type=refresh_token"
```

Response contains `access_token`, `refresh_token` (new — save it!), `expires_in`. Write both back to `.env` before doing anything else.

**Connection test (read-only):**

```bash
set -a; source .env; set +a; \
curl -s -H "Authorization: Bearer $CC_ACCESS_TOKEN" \
  "https://api.cc.email/v3/contact_lists?limit=1"
```

A 200 with a `lists` array means the token works. A 401 means refresh (or re-authorize if the refresh token is dead).

## Fetching contact lists (setup wizard)

```bash
set -a; source .env; set +a; \
curl -s -H "Authorization: Bearer $CC_ACCESS_TOKEN" \
  "https://api.cc.email/v3/contact_lists?include_count=true&limit=50"
```

Show the user: `list_id`, `name` for each entry in `lists`. ⚠️ unverified — membership counts may require `include_membership_count=all`; confirm at https://developer.constantcontact.com/api_reference/index.html (GET /contact_lists). Store the chosen `list_id`(s) in the plugin config.

## Creating a draft campaign (core flow)

**This is a TWO-STEP flow** (verified at https://developer.constantcontact.com/api_guide/email_campaign_create.html):
1. `POST /v3/emails` creates the campaign + primary activity (in **Draft** status) — but you **cannot attach contact lists on the POST**.
2. `PUT /v3/emails/activities/{campaign_activity_id}` to set `contact_list_ids` (and any edits).

Notes:
- `format_type: 5` = custom code email (raw HTML you control; supports `<style>` and inline CSS).
- `html_content` **must contain `[[trackingImage]]`** somewhere in the `<body>` or open tracking breaks.
- `from_email` / `reply_to_email` must be addresses already verified in the Constant Contact account.
- `preheader` = preview text.

**JSON escaping tip:** never inline HTML into a quoted JSON string by hand. Write the HTML to a file and build the payload with `jq --rawfile`:

```bash
set -a; source .env; set +a; \
jq -n --rawfile html email.html \
  --arg name "2026-07 Newsletter" \
  --arg subject "July news from Acme" \
  --arg preheader "The three things worth your time this month" \
  --arg from_name "Acme Co" \
  --arg from_email "hello@acme.com" \
  '{
    name: $name,
    email_campaign_activities: [{
      format_type: 5,
      from_name: $from_name,
      from_email: $from_email,
      reply_to_email: $from_email,
      subject: $subject,
      preheader: $preheader,
      html_content: $html
    }]
  }' > payload.json && \
curl -s -X POST "https://api.cc.email/v3/emails" \
  -H "Authorization: Bearer $CC_ACCESS_TOKEN" \
  -H "Content-Type: application/json" \
  --data @payload.json
```

Response (201):

```json
{
  "campaign_id": "<uuid>",
  "current_status": "Draft",
  "type": "CUSTOM_CODE_EMAIL",
  "campaign_activities": [
    { "role": "primary_email", "campaign_activity_id": "<uuid>" }
  ]
}
```

Save `campaign_id` and the `primary_email` activity's `campaign_activity_id` to the campaign's meta.yaml.

**Step 2 — attach the contact list(s).** The PUT replaces the activity, so GET it first, add `contact_list_ids`, and PUT the full object back:

```bash
set -a; source .env; set +a; \
curl -s -H "Authorization: Bearer $CC_ACCESS_TOKEN" \
  "https://api.cc.email/v3/emails/activities/${ACTIVITY_ID}" > activity.json && \
jq --arg list "$LIST_ID" '.contact_list_ids = [$list]' activity.json > activity_upd.json && \
curl -s -X PUT "https://api.cc.email/v3/emails/activities/${ACTIVITY_ID}" \
  -H "Authorization: Bearer $CC_ACCESS_TOKEN" \
  -H "Content-Type: application/json" \
  --data @activity_upd.json
```

⚠️ unverified — whether PUT strictly requires the full activity body vs. accepting partials; confirm at https://developer.constantcontact.com/api_reference/index.html (PUT /emails/activities/{campaign_activity_id}). The GET-modify-PUT pattern above is safe either way.

## Verifying the draft

```bash
set -a; source .env; set +a; \
curl -s -H "Authorization: Bearer $CC_ACCESS_TOKEN" \
  "https://api.cc.email/v3/emails/${CAMPAIGN_ID}"
```

Confirm `current_status` is `"Draft"` and the activity list is intact. In the UI the user finds it under **Marketing → Campaigns** (Drafts filter), opens it, previews, and sends it themselves.

## Uploading images

`POST https://api.cc.email/v3/library/files` — multipart/form-data. ⚠️ unverified details (guide page returns 403 to fetchers) — confirm field names at https://developer.constantcontact.com/api_guide/library_add_files.html. Expected parts: the file binary, `folder_id` (0 or omitted for root), `source` (e.g. `MyComputer`).

```bash
set -a; source .env; set +a; \
curl -s -X POST "https://api.cc.email/v3/library/files" \
  -H "Authorization: Bearer $CC_ACCESS_TOKEN" \
  -F "file=@hero.png" -F "folder_id=0" -F "source=MyComputer"
```

The response/`Location` header yields a `file_id`; `GET /v3/library/files/{file_id}` returns the hosted `url` to use in `html_content`. ⚠️ unverified — confirm response shape at the same doc URL. Fallback: host images on the client's own website and reference absolute URLs.

## A/B subject line variants

Supported via API, subject-line only (verified at https://developer.constantcontact.com/api_guide/email_campaigns_ab_test_overview.html):

- Create: `POST /v3/emails/activities/{campaign_activity_id}/abtest` with `alternative_subject` (required), `test_size` (5–50, % of recipients), `winner_wait_duration` (hours before picking winner by opens).
- Inspect: `GET .../abtest` — Remove: `DELETE .../abtest` (reverts type AB_TEST → NEWSLETTER).

Creating the A/B test does NOT send anything — it only configures the draft. Still record both subject variants in the campaign's meta.yaml so the human sees them at review time. The winner is sent automatically by Constant Contact *after the human sends the campaign* from the UI.

## Campaign reports (read-only — campaign-analyst agent)

- Summary for up to 500 recent campaigns (`unique_counts`: sends, opens, clicks, forwards, optouts, abuse, bounces, not_opened):

```bash
set -a; source .env; set +a; \
curl -s -H "Authorization: Bearer $CC_ACCESS_TOKEN" \
  "https://api.cc.email/v3/reports/summary_reports/email_campaign_summaries"
```

- Per-activity link clicks: `GET /v3/reports/email_reports/{campaign_activity_id}/links` (per-link `unique_clicks`).
- Per-activity contact-level detail: `GET /v3/reports/email_reports/{campaign_activity_id}/tracking/sends` (verified); sibling paths `.../tracking/opens`, `.../tracking/clicks`, `.../tracking/bounces` ⚠️ unverified — confirm at https://developer.constantcontact.com/api_guide/email_reporting_overview.html

## Rate limits & error handling

- **10,000 requests/day** (resets 00:00 UTC) and a per-second throttle (docs cite max ~4 req/s). Exceeding returns **429** with `error_key: "quota_exceeded"` (daily) or `"throttled"` (burst). Verified at https://developer.constantcontact.com/api_guide/rate_limits.html
- On any 4xx: print the platform's error JSON **verbatim** to the user (CC errors are an array of `{error_key, error_message}`), then stop — do not retry blindly.
- On 401: refresh the token (see Authentication) and remind the user to persist the rotated refresh token.

## ⛔ FORBIDDEN — never call these

Sending is a HUMAN action performed in the Constant Contact UI. The agent must never call:

- `POST /v3/emails/activities/{campaign_activity_id}/schedules` — schedules/sends the campaign (a `scheduled_date` of "0" sends immediately). NEVER.
- `DELETE /v3/emails/activities/{campaign_activity_id}/schedules` — don't touch schedules at all.
- `POST /v3/emails/activities/{campaign_activity_id}/tests` — test-send to real inboxes (50/day cap). Only permitted if the user explicitly asks for a test send in the current session, with recipient addresses they provide.

If any tool/workflow suggests scheduling "for convenience": refuse. Drafts only.
