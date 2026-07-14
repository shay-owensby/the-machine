# MoeGo — Platform Reference (email-marketing plugin)

> MoeGo (moego.pet) is a pet-care business platform — grooming/boarding POS, online booking, and CRM — with a built-in "Marketing" module for email campaigns. It is **not** a general email-marketing tool, and its email campaigns cannot be driven by API.

## API availability (researched 2026-07-14)

MoeGo **does** publish an Open API, but it does **not** cover marketing/email campaigns, and access is gated:

- Official API repo: https://github.com/MoeGolibrary/moegoapis (OpenAPI/protobuf definitions; Postman workspace: https://www.postman.com/moegoapis/moego-apis/)
- Base domain: `openapi.moego.pet` (paths like `/v1/customer`, `/v1/appointment`, `/v1/order`, `/v1/webhooks`)
- Modules exposed: authentication, customers & pets, scheduling/appointments/online booking, orders & payments, retail & inventory, memberships, webhooks/settings, agreements & feedback, analytics. **No marketing, email, or campaign module exists** (verified against the repo docs 2026-07).
- Access: API keys are not self-serve — "work directly with your dedicated Customer Success Manager" to apply for keys.
- Help center for the marketing feature (UI only): https://help.moego.pet/en/articles/11356992-marketing-campaign-emails-overview

**Conclusion: no public campaign API → MoeGo is a FILE-ONLY platform in this plugin.** Drafts are produced as local files; the human rebuilds and sends them inside MoeGo.

## Plugin behavior

- During setup, `delivery.mode` is **forced to `file_only`**. Do not offer `api_draft` mode.
- Collect **no credentials**: no API key, no login, nothing in `.env` for this platform.
- Make **no API calls ever** — not even "read-only tests" against `openapi.moego.pet` (access is CSM-gated and irrelevant to campaigns).
- The plugin's only outputs are the drafts folder files (below) plus this manual workflow guidance shown to the user.

## Manual workflow guide (what the human does in MoeGo)

Where campaigns live (verified from the help center article above):

1. Open the **MoeGo desktop web app** (campaign creation is desktop-web only).
2. Go to **Marketing → Email campaigns**.
3. Requirements: **Growth plan or higher**, the "Access Marketing campaign" staff permission, and available **email campaign credits** (cost scales with recipient count — check credits before building).

**Custom HTML: not supported.** MoeGo's editor offers ready-made templates and a drag-and-drop editor ("Alpha", modular content blocks); the help docs mention adding text, images, buttons, links, attachments, and personalized content — **no HTML-paste or code editor is documented**. Therefore the human must *rebuild* the draft in MoeGo's builder rather than importing it.

How to use the plugin's drafts folder in MoeGo:

- `drafts/YYYY-mm-dd/YYYY-mm-dd.html` — the designed email body. Open it in a browser and use it as the **visual + copy reference**: recreate the layout section-by-section with MoeGo's content blocks, copy/paste the text, and re-upload the same images (from `drafts/YYYY-mm-dd/images/`) into MoeGo's editor.
- `drafts/YYYY-mm-dd/YYYY-mm-dd.meta.yaml` — contains:
  - `subject.chosen` (and variants `subject.a/b/c`) → paste the chosen one into MoeGo's campaign **subject** field.
  - `preview_text` → ⚠️ unverified whether MoeGo exposes a preview-text/preheader field (not documented in the help article — confirm at https://help.moego.pet/en/articles/11356992-marketing-campaign-emails-overview). If there is no field, put the preview text as the first (visually hidden or small) text line of the email body.
  - Unused subject variants → MoeGo has no documented A/B testing; either send two campaigns to manually split client filters, or use the chosen variant and keep the others for next time.
- Save the campaign as a **draft** in MoeGo (drafts and test emails are supported), send a **test email** to yourself, review, and only then send or schedule — the human performs the send in the MoeGo UI, never the plugin.

## Audience notes

MoeGo targets recipients from its own CRM, not uploaded lists: the campaign builder uses **client and pet filters** to build the recipient list (e.g., client attributes and pet attributes; verified from the help article). Before sending, MoeGo checks **recipient eligibility**: a client must have an email address on file and be **subscribed via their email-channel marketing preference** — unsubscribed or email-less clients are excluded automatically. When the plugin's campaign brief specifies an audience (e.g., "clients not visited in 90 days"), translate it into MoeGo filter suggestions in the handoff notes; exact available filters vary — confirm in the UI.

## Re-check note (for future agents)

MoeGo actively expands its Open API (github.com/MoeGolibrary/moegoapis gains modules over time, and API access currently runs through a CSM application process — effectively a waitlist). **Periodically re-check** (every few months, or when the user mentions MoeGo API access):

1. Look for a `marketing`, `campaign`, or `message` module in the repo's `docs/openapi` directory and the Postman workspace.
2. Check https://help.moego.pet and https://www.moego.pet for "Open API" or developer-program announcements.
3. If a campaign-creation endpoint appears, flag to the user that `api_draft` mode could be added for MoeGo — but keep the plugin's hard rule: create drafts only, never send or schedule.
