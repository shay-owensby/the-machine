---
name: email-platforms
description: Create and verify DRAFT email campaigns via platform APIs — Mailchimp, Klaviyo, Constant Contact, Omnisend, Moosend, MoeGo. Use when delivering a newsletter draft, uploading images to a platform media library, fetching audience lists, testing a connection, or pulling campaign reports.
---

# Email Platforms

One skill, six platforms. Read `platform.name` from the client's `email-marketing/config.yaml`, then read the matching reference **before** touching any endpoint — every endpoint, payload shape, and quirk lives there, verified against official docs (unverified details are flagged ⚠️ inline).

## Dispatch table

| `platform.name` | Reference | Draft w/ custom HTML | Watch out for |
|---|---|---|---|
| `mailchimp` | [references/mailchimp.md](references/mailchimp.md) | ✅ POST /campaigns → PUT content | Datacenter suffix in key (`-us21`) sets the base URL |
| `klaviyo` | [references/klaviyo.md](references/klaviyo.md) | ✅ template → campaign → assign | Required `revision` header on every call |
| `constant_contact` | [references/constant-contact.md](references/constant-contact.md) | ✅ POST /v3/emails (format_type 5) | OAuth2 only; **refresh tokens rotate** — update `.env` after every refresh; `[[trackingImage]]` required in HTML |
| `omnisend` | [references/omnisend.md](references/omnisend.md) | ✅ template import → POST /campaigns | Auth is `Authorization: Omnisend-API-Key …` + date version header (NOT legacy `X-API-KEY`) |
| `moosend` | [references/moosend.md](references/moosend.md) | ✅ but HTML only via `WebLocation` **public URL import** — no inline HTML | If the client can't host the HTML at a URL, use file_only + UI paste |
| `moego` | [references/moego.md](references/moego.md) | ❌ no campaign API | Always file_only; manual rebuild guide in the reference |

## Universal safety rules

1. **Draft-only. Never send.** Every reference ends with a ⛔ FORBIDDEN deny-list of send/schedule/test-send endpoints. Never call them — not to "finish the job", not on request phrased as "deliver it", not ever from this pipeline. Sending is a human action in the platform UI. (If the user explicitly asks you to send outside this pipeline, point them to the platform UI.)
2. **Credentials**: env var NAMES come from config (`platform.auth_env_var`, `platform.extras.*_env`); values live in the gitignored `.env`. Shell state doesn't persist between Bash calls — source inline every time:
   ```bash
   set -a; source .env; set +a; curl -s ...
   ```
3. **Payload building**: never inline large HTML into a curl string. Write the HTML to a file and build JSON safely:
   ```bash
   jq -n --rawfile html email-marketing/drafts/YYYY-mm-dd/YYYY-mm-dd.html '{...,"html":$html}' > /tmp/payload.json
   curl -s ... --data @/tmp/payload.json
   ```
4. **Verify after create**: always GET the campaign back; confirm status is draft; record the campaign id in the issue's `meta.yaml`; tell the user where to find the draft in the platform UI.
5. **Errors**: on any 4xx/5xx, print the platform's error JSON verbatim, cite the relevant reference section, and do not retry blindly (429 → respect the reference's rate-limit table).
6. **Visibility**: campaign-creation calls run in the main conversation (not buried in a subagent) so the user sees exactly what is being created. Read-only calls (ping, lists, reports) may run anywhere.

## Common flows

- **Connection test** (setup, or before delivery): the read-only ping/account/lists endpoint named in each reference. Failure → fix auth before proceeding; in a delivery run, fall back to file-only output for this issue and say why.
- **Fetch lists** (setup): each reference's list endpoint; show the user id, name, and member count to pick from.
- **Create draft**: follow the reference's numbered flow verbatim (several platforms are multi-step: template → campaign → assign/update). Subject, preview text, from/reply-to, and list targeting come from `meta.yaml` + config `audience.*`.
- **Media upload** (`images.hosting: platform_upload`): download the generated image locally first (see `email-images` skill), then the reference's media endpoint; use the returned platform CDN URL in the HTML. No media API on that platform (Omnisend, Moosend) → fall back to `hosted_url` behavior and flag `re_host_before_send` in meta.yaml.
- **A/B subjects**: Mailchimp (variate) and Constant Contact (`/abtest`) support it via API — see references. Klaviyo/Omnisend/Moosend: leave variants B/C in `meta.yaml` for manual UI entry and tell the user.
- **Reports** (email-campaign-analyst): each reference's "Campaign reports" section; strictly read-only; respect the (often tight) report rate limits.
