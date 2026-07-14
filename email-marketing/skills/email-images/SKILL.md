---
name: email-images
description: Generate and place newsletter imagery via the Higgsfield MCP connector, styled from the client's DESIGN.md. Use when an email issue needs a hero or section image — covers prompting, approval, download, and hosting strategy.
---

# Email Images (Higgsfield MCP)

Images are an enhancement, **never a blocker**: if anything in this pipeline fails or is unavailable, fall back to a no-image layout (or a user-supplied image) and keep the issue moving.

## 1. Availability check

Confirm the Higgsfield MCP tools are reachable (e.g. `mcp__claude_ai_Higgsfield__generate_image`; load schemas via ToolSearch if deferred). If absent: tell the user the Higgsfield connector isn't enabled in this session, offer (a) no-image layout or (b) a path/URL to an image they supply. Do not retry endlessly.

## 2. Prompt construction — DESIGN.md governs style, ABOUT.md governs subject matter

Read the client's `brand.design_file` (path from config). Build the image prompt from:
- **Palette**: the exact hex values / color names DESIGN.md specifies
- **Style**: DESIGN.md's stated aesthetic (photography vs illustration, mood, composition rules), plus any master style prompt or negative/avoid list it contains — reuse those verbatim when present
- **Subject**: this issue's topic, concretized (not "pet grooming" but "a golden retriever being brushed outdoors in warm morning light")
- `images.style_notes` from config (additive only — never contradicting DESIGN.md)

Never invent brand style not in DESIGN.md. If `design_file: null`, use a clean, neutral editorial style, note the degradation to the user.

Check the client's `brand.about_file` before concretizing the subject: the image must depict what the business actually does — never a service, product, setting, or scenario the client doesn't actually offer per ABOUT.md. If `about_file: null`, keep the subject matter generic to the configured `brand.industry` rather than inventing specifics, and note the degradation.

**Text in images**: avoid rendering text entirely if possible (generators misspell; email clients block images). If DESIGN.md's style demands headline text, keep it to 1–4 words, spell them out exactly in the prompt, and proofread the result letter-by-letter before accepting.

## 3. Sizing

- Hero: wide banner, ~2:1 — generate at ~1200×600 (2× retina for 600px display width)
- Section images: ~1200×800 or square 800×800 depending on layout
- Model choice: use Higgsfield's recommendation flow (`models_explore` action `recommend`) when unsure; otherwise the default image model

## 4. Generate → poll → approve

1. Call `generate_image` with the constructed prompt + aspect ratio.
2. Generation is async: poll `job_status` politely (a few seconds between checks) until complete.
3. **Show the user the result and get approval before using it.** Offer one regeneration round with adjusted prompt if they want changes; more rounds only if they ask.

## 5. Download — always

Higgsfield returns URLs on its CDN with unknown persistence. Immediately download every approved image into the issue folder:

```bash
curl -sL -o "email-marketing/drafts/YYYY-mm-dd/images/hero.png" "<higgsfield_url>"
```

The local file is the source of truth; record it plus its alt text in `meta.yaml`.

## 6. Hosting — which URL goes in the HTML

Per `images.hosting` in config:

- **`platform_upload`** (recommended for `api_draft`): upload the downloaded file to the email platform's media library per `${CLAUDE_PLUGIN_ROOT}/skills/email-platforms/references/<platform>.md`, and use the returned platform CDN URL in the HTML. If the platform has no media API (see reference), fall back to `hosted_url` behavior and say so.
- **`hosted_url`** (file_only default): use the Higgsfield URL in the HTML **and** set `re_host_before_send: true` on the image entry in `meta.yaml`, telling the user to re-upload the local file when building the email in their platform UI (generator URLs may expire and hurt deliverability).

## 7. Accessibility & QA handoff

Every image gets descriptive alt text written at generation time (what's IN the image, not the topic name). The email-qa agent will verify URLs load, alt text exists, sizing attributes are present, and hosting matches config — make its job easy by recording everything in `meta.yaml`.
