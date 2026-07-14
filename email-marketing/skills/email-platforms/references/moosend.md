# Moosend — API Reference (email-marketing plugin)

> Moosend is an email-marketing platform (owned by Sitecore since 2021) with a full REST API for lists, campaigns, and reports.
> API base URL: `https://api.moosend.com/v3` (verified)
> Docs home: https://docs.moosend.com/developers/api-documentation/en/index-en.html (API Reference Knowledge Base)
> Interactive reference: https://moosendapp.docs.apiary.io/ (JS-rendered; official wrappers at https://github.com/moosend also document every endpoint)

## Capabilities summary

| Capability | Supported via API? | Notes |
|---|---|---|
| Create DRAFT campaign | ✅ Yes | `POST /campaigns/create.{Format}` — created unsent, "as a draft, ready for sending or testing" (verified in official docs) |
| Custom HTML body | ⚠️ Indirect only | Content is imported from a URL via `WebLocation` — there is **no** `HtmlContent` body parameter on create (see below) |
| Preview text | ❌ Not exposed | No preview-text/preheader parameter in the create/update campaign API — embed `<span style="display:none">` preheader in the HTML instead |
| A/B testing | ✅ Yes | `ABCampaignType`, `SubjectB`, `WebLocationB` on create; AB summary report endpoint |
| Media/image upload | ❌ No API | No media-library endpoint exists in v3 — host images on the client's website/CDN |
| Reports (opens/clicks) | ✅ Yes, read-only | Summary, link activity, activity-by-country, AB summary |

**Sitecore note:** Moosend was acquired by Sitecore in 2021. The product still operates under the Moosend brand and the v3 API remains publicly available — docs are live at docs.moosend.com (verified 2026-07). API keys are self-serve from account settings; no special developer-program application is required for existing accounts. If docs.moosend.com is ever restructured, check https://moosend.com/ and Sitecore's developer portal.

## Authentication

- Scheme: API key passed as the **`apikey` query-string parameter** on every request (verified). No Authorization header.
- Env var (this plugin): `MOOSEND_API_KEY` — stored in the gitignored `.env`; config files store only the env var NAME.
- Where the user finds the key: Moosend UI → **More → Settings → API key** (left sidebar). The page lets them copy the existing key or "Generate API key" for a new one. (Verified: https://docs.moosend.com/users/moosend/en/use-the-api-key-to-connect-to-the-moosend-web-api.html)

**Read-only connection test** (safe — fetches mailing lists, changes nothing):

```bash
set -a; source .env; set +a
curl -s "https://api.moosend.com/v3/lists.json?apikey=${MOOSEND_API_KEY}" | head -c 2000
```

Success: HTTP 200 with `"Code": 0` and a `Context.MailingLists` array. `"Code"` non-zero or an `Error` string means a bad key.

## Fetching mailing lists

Endpoint: `GET /lists.{Format}` — all active mailing lists. Paged variant: `GET /lists/{Page}/{PageSize}.{Format}`. Optional query params (per official PHP wrapper docs): `WithStatistics` (fetch subscriber stats), `ShortBy` (sic — sort property), `SortMethod` (`ASC`/`DESC`).

```bash
set -a; source .env; set +a
curl -s "https://api.moosend.com/v3/lists.json?apikey=${MOOSEND_API_KEY}&WithStatistics=true"
```

Show the user, per list: `ID` (needed for campaign creation), `Name`, `ActiveMemberCount`, `Status`, `CreatedOn`. Store the chosen list ID in the plugin config as `list_id`.

Mailing-list details for one list: `GET /lists/{MailingListID}/details.{Format}` (verified: docs article 54571 "Get mailing list details").

## Creating a draft campaign

Endpoint: `POST /campaigns/create.{Format}` (verified). **This creates the campaign UNSENT, as a draft** — official docs: "This method does not send the campaign, but rather creates it as a draft, ready for sending or testing." That is exactly the plugin's contract; no extra flag is needed to keep it a draft.

Verified request parameters (from official docs + moosend/api-wrappers-java `CampaignsApi.md`):

| Param | Required | Notes |
|---|---|---|
| `Name` | yes | Internal campaign name — use `YYYY-mm-dd <campaign slug>` |
| `Subject` | yes | Subject line from meta.yaml |
| `SenderEmail` | yes | Must be a **verified sender** in the account (check `GET /senders/find_all.{Format}` ⚠️ unverified path — confirm at https://moosendapp.docs.apiary.io/) |
| `ReplyToEmail` | no | Defaults to sender |
| `ConfirmationToEmail` | no | Gets a confirmation email |
| `WebLocation` | yes* | **Public URL from which Moosend imports the HTML body** (see below) |
| `MailingLists` | yes | Target list ID(s); optional `SegmentID` per list |
| `ABCampaignType`, `SubjectB`, `WebLocationB` | no | A/B fields — see A/B section |

**CRITICAL — how HTML content works:** the create/update campaign API does **not** accept inline HTML (`HtmlContent`/`PlainContent` are *response* fields on campaign details, not create parameters). Campaign content "must be specified from a web location": Moosend fetches the HTML from the `WebLocation` URL at creation time.

Practical recommendation for this plugin:
1. **Preferred:** upload the draft's `YYYY-mm-dd.html` to a publicly reachable URL the orchestrator controls (client website, S3/Netlify/Vercel static hosting) and pass that URL as `WebLocation`. The URL only needs to stay up until the campaign is created (verify persistence behavior before deleting the file — ⚠️ unverified whether Moosend snapshots or re-fetches; confirm at https://moosendapp.docs.apiary.io/).
2. **Fallback (no hosting available):** create the draft with subject/sender/list only against a placeholder `WebLocation`, or skip API content entirely and have the human paste the HTML using Moosend's UI campaign editor ("Import from URL" / HTML editor). Record which path was used in the meta.yaml.

```bash
set -a; source .env; set +a
curl -s -X POST "https://api.moosend.com/v3/campaigns/create.json?apikey=${MOOSEND_API_KEY}" \
  -H "Content-Type: application/json" \
  -d '{
    "Name": "2026-07-14 summer-grooming-promo",
    "Subject": "Beat the heat — summer grooming special",
    "SenderEmail": "hello@clientdomain.com",
    "ReplyToEmail": "hello@clientdomain.com",
    "WebLocation": "https://clientdomain.com/email-drafts/2026-07-14.html",
    "MailingLists": [{ "MailingListID": "LIST-ID-FROM-CONFIG" }]
  }'
```

Success: `"Code": 0` and `Context` = the new **CampaignID** (save it to meta.yaml as `platform_campaign_id`). ⚠️ The exact JSON body shape (`MailingLists` array-of-objects vs. flat `MailingListID`) is unverified from the rendered docs — confirm at https://moosendapp.docs.apiary.io/ before first live use; the XML/form-encoded variant is also accepted per the wrappers.

To modify an existing draft: `POST /campaigns/{CampaignID}/update.{Format}` — same parameters; only drafts can be updated (verified via official Java wrapper docs).

## Verifying the draft

```bash
set -a; source .env; set +a
curl -s "https://api.moosend.com/v3/campaigns/${CAMPAIGN_ID}/view.json?apikey=${MOOSEND_API_KEY}"
```

`GET /campaigns/{CampaignID}/view.{Format}` (verified) returns `Name`, `Subject`, `WebLocation`, `HTMLContent`, `PlainContent`, `Sender`, `Status`, `ScheduledFor`, `DeliveredOn`, `ABCampaignData`, `MailingLists`, timestamps. Confirm after creation that:
- `Status` indicates draft (not sent/scheduled) and `DeliveredOn`/`ScheduledFor` are null,
- `HTMLContent` matches the imported draft HTML,
then tell the human the draft is ready to review and send from the Moosend UI.

Listing campaigns: `GET /campaigns.{Format}` (all) or `GET /campaigns/{Page}.{Format}` / `GET /campaigns/{Page}/{PageSize}.{Format}` (paged, per official wrappers).

## Uploading images

**No media-library API exists** in v3 — none of the official wrappers or the docs Knowledge Base expose an image/asset upload endpoint (verified by absence in the complete wrapper endpoint lists). Fallback: host images on the client's website or other public hosting and use absolute URLs in the draft HTML. Since the HTML itself is imported from `WebLocation`, relative image paths resolving against that host can work, but absolute URLs are safer.

## A/B variants

Supported at creation time via `POST /campaigns/create.{Format}` extra params (verified in official wrapper docs): `ABCampaignType`, `SubjectB` ("Subject B"), `WebLocationB`. AB results are read via `GET /campaigns/{CampaignID}/view_ab_summary.{Format}` (verified).

⚠️ unverified: allowed `ABCampaignType` values and winner-selection/test-percentage/test-duration parameters — confirm at https://moosendapp.docs.apiary.io/ before creating an AB draft via API. If the shape can't be confirmed at run time, fall back to the plugin's standard behavior: create a plain draft for variant A and record variant B's subject/preview in `meta.yaml` for the human to configure in the Moosend UI.

## Campaign reports (read-only)

All verified paths:

| Report | Endpoint |
|---|---|
| Summary (recipients, opens, clicks, bounces, unsubs, forwards) | `GET /campaigns/{CampaignID}/view_summary.{Format}` |
| Activity detail (per type) | `GET /campaigns/{CampaignID}/stats/{Type}.{Format}` — ⚠️ `{Type}` values (e.g. `Opened`, `LinkClicked`) unverified; confirm at https://moosendapp.docs.apiary.io/ |
| Opens by country | `GET /campaigns/{CampaignID}/stats/countries.{Format}` |
| Link click activity | `GET /campaigns/{CampaignID}/stats/links.{Format}` |
| A/B summary per version | `GET /campaigns/{CampaignID}/view_ab_summary.{Format}` |

```bash
set -a; source .env; set +a
curl -s "https://api.moosend.com/v3/campaigns/${CAMPAIGN_ID}/view_summary.json?apikey=${MOOSEND_API_KEY}"
```

## Rate limits & error handling

Official limits (verified: docs article 54558 "API rate limiting") — enforced **per API key per endpoint**; exceeding returns body `"Code": 429, "Error": "RATE-LIMITING"`:

| Endpoint | Limit |
|---|---|
| `GET /campaigns/{id}/stats/{Type}.{Format}` | **2 calls / 60 s** (very tight — cache report results) |
| `POST /subscribers/{list}/subscribe.{Format}` | 10 / 10 s |
| `POST /subscribers/{list}/subscribe-many.{Format}` | 2 / 10 s |
| Unsubscribe endpoints | 20 / 10 s |
| Delete subscriber (single / many) | 40 / 10 s / 8 / 10 s |
| Transactional send | 6 / 1 s (not used by this plugin) |

Campaign create/list endpoints have no published limit — still be polite (1 req/s). Error handling: every response carries `Code` (0 = success), `Error` (message or null), `Context` (payload). Treat non-zero `Code` as failure even on HTTP 200; on `Code: 429` back off 60 s and retry once.

## ⛔ FORBIDDEN — never call

Sending happens **only** in the Moosend UI, by the human. The agent must NEVER call:

- `POST /campaigns/{CampaignID}/send.{Format}` — sends immediately to all recipients (path verified)
- `POST /campaigns/{CampaignID}/schedule.{Format}` — schedules delivery (⚠️ exact path unverified but the operation exists — treat any endpoint containing `schedule` as forbidden; confirm at https://moosendapp.docs.apiary.io/)
- `POST /campaigns/{CampaignID}/unschedule.{Format}` — don't touch scheduling state at all
- `POST /campaigns/transactional/send.{Format}` — transactional sending
- Any `ScheduledFor` / scheduling field on create or update calls — omit entirely

Also avoid destructive endpoints unless the human explicitly asks in the current session: `DELETE` on campaigns, lists, or subscribers. `POST /campaigns/{CampaignID}/send_test.{Format}` (test-send to specific addresses — ⚠️ path unverified) does email real inboxes; only use it if the human explicitly requests a test send and supplies the addresses.
