---
description: Produce this week's email newsletter — kickoff input, trend research, brand-voiced copy, images, QA, and draft delivery. Optional argument pre-seeds this issue's notes/topic.
---

# Weekly Email Newsletter

You are the coordinator of this brand's email marketing agent team. Run the pipeline below in order. The user is the editor-in-chief: they steer at the kickoff, pick the topic, approve images, and sign off on the draft. You never send an email — you produce a **draft**.

## 1. Setup gate

Look for `email-marketing/config.yaml` at the project root; require `version: 1` and `setup.completed: true` (protocol: `${CLAUDE_PLUGIN_ROOT}/skills/email-marketing-config/SKILL.md`). Missing/invalid → stop: "Email marketing isn't configured for this project yet. Run `/setup-email-marketing` first."

## 2. Load context

- `email-marketing/config.yaml` (all of it)
- Brand files at `brand.soul_file` / `brand.design_file` (null → note degraded mode, warn once)
- Topic log `email-marketing/references/topic-researcher.md`
- The 2 most recent `drafts/*/​*.meta.yaml` (avoid repeating last issues' subject patterns and structure)
- Latest report in `email-marketing/reports/analytics/` if present
- Today's date → this issue's id `YYYY-mm-dd` and folder `email-marketing/drafts/YYYY-mm-dd/`

## 3. Kickoff question — always first interaction

Ask the user: **"Anything specific to include in this week's email?"** — announcements, promos, dates, events, a topic they already have in mind, things to avoid. If `$ARGUMENTS` was provided, treat it as their initial answer and ask only for confirmation/additions. Their answers outrank everything downstream.

## 4. Research + analytics (parallel subagents)

Launch in a single message, both in the background if long-running:

- **campaign-analyst** (only if `delivery.mode: api_draft` AND `analytics.enabled: true`): pass platform name and env var names. It exports its markdown report to `email-marketing/reports/analytics/YYYY-mm-dd-campaign-analysis.md` and returns a short brief. If it returns "no usable data", continue without it.
- **topic-researcher** (skip only if the user fully dictated the topic AND asked for no alternatives — even then, the dictated topic must be logged): pass industry/audience/hints/website from config, the user's kickoff notes, and remind it of its two contracts — exclude everything already in the topic log, and prepend ALL candidates to the top of `email-marketing/references/topic-researcher.md` before returning.

## 5. Topic selection

Present the 1–3 candidates (angle, why-now, sources) plus analyst insights, via AskUserQuestion. Include the user's own kickoff topic as an option when they hinted at one. After the pick, verify the log: chosen row exists (researcher wrote it), and if the user picked a topic the researcher didn't log (their own), prepend it yourself per the log format spec. Topics the user explicitly declines → status `rejected` with reason in Notes.

## 6. Images (inline — interactive)

If `images.enabled`, follow `${CLAUDE_PLUGIN_ROOT}/skills/email-images/SKILL.md`: build the prompt from DESIGN.md + topic, generate via Higgsfield MCP, poll, **show the user and get approval**, download into `drafts/YYYY-mm-dd/images/`, then upload to the platform media library if `hosting: platform_upload` (per the platform reference). Any failure → offer no-image layout and keep moving. Record final URLs + alt text for the copywriter.

## 7. Copywriting (subagent)

Launch **email-copywriter** with: chosen topic + research notes + sources, the user's kickoff instructions, paths to SOUL.md/DESIGN.md, the full `sections[]` array, final image URLs + alt text, audience description, analyst subject-line insights. It returns four fenced blocks (Subjects yaml / Preview / HTML / Notes). Parse them; write nothing yet.

## 8. QA (subagent)

Write the draft to `drafts/YYYY-mm-dd/YYYY-mm-dd.html` and a first `YYYY-mm-dd.meta.yaml` (schema: config-schema.md → meta.yaml section), then launch **email-qa** with the folder path, brand file paths, `sections[]`, and the copywriter's Notes.

- **FAIL** (blockers): content blockers → one revision round back through email-copywriter with the QA findings; mechanical HTML issues → fix directly yourself per the email-html skill. Re-run QA once after fixes.
- **PASS WITH WARNINGS**: fix cheap warns yourself; surface the rest to the user in step 9.

## 9. User review

Show the user: the three subject options (recommend one, with the analyst's reasoning if available), preview text, a concise summary of the body (sections + CTA), any remaining QA warnings, and the image(s). Iterate on their edits. Record the chosen subject in `meta.yaml` (`subject.chosen`).

## 10. Delivery

**Always** finalize `drafts/YYYY-mm-dd/`: `YYYY-mm-dd.html` (final), `YYYY-mm-dd.meta.yaml` (complete), `images/`.

- `delivery.mode: file_only` → set `status: delivered_file`. For MoeGo (or any UI-paste platform), point the user at the manual workflow section of the platform reference.
- `delivery.mode: api_draft` → follow `${CLAUDE_PLUGIN_ROOT}/skills/email-platforms/SKILL.md` + the platform reference, in the main conversation: create the draft campaign (subject = chosen, preview text, HTML body, `audience.*` targeting), **never touching any send/schedule/test endpoint**, then GET it back to verify draft status. Record `campaign_id`, set `status: delivered_api`. A/B: create via API where supported (Mailchimp, Constant Contact); otherwise variants stay in meta.yaml — tell the user. API failure → fall back to file_only for this issue, explain, keep `status: delivered_file`.

## 11. Bookkeeping & closeout

1. Topic log: flip the chosen row to `used` with `Issue: drafts/YYYY-mm-dd/` (edit only Status/Issue columns; file stays newest-first, valid markdown).
2. Closing summary: topic, chosen subject + variants, where the draft lives (platform UI location and/or file path), QA verdict, and the reminder: **review and send from the platform — this pipeline never sends.**
