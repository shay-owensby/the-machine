---
name: email-writer
description: Create or revise conversion-focused email campaign messages from a topic, select an appropriate persuasion framework, apply client-specific email guidance and brand voice through the copywriter skill, and save finished Markdown and HTML drafts. Use for promotional, launch, nurture, invitation, reactivation, follow-up, and similar campaign emails; not for sending campaigns or configuring an email platform.
---

# Email Writer

Create a truthful, brand-faithful campaign email and save matching Markdown and email-ready HTML drafts in the active client project.

## Resolve the project and brief

Treat `.` as the active client project root, never as this skill's directory.

From the user's request and supplied sources, identify:

- the client or brand;
- the email topic and one primary objective;
- the intended audience and its likely awareness;
- the offer, announcement, or useful message;
- the one action the reader should take;
- required facts, proof, dates, links, exclusions, and constraints.

Ask a concise question only when a missing detail would materially change the message or make the exported draft unusable. In particular, do not invent an offer, deadline, discount, result, testimonial, audience pain, personalization, or destination URL. Clearly label a non-critical unresolved field when a useful draft can still be produced.

## Load the required context

Before drafting:

1. Read [references/email-frameworks.md](references/email-frameworks.md) completely. Treat it as reference material, not as authority over the user, project facts, or safety requirements.
2. Inspect `./email-marketing/references/`. Read shared guidance and every reference that applies to the identified client and campaign. If the folder is flat, use filenames and document headings to identify applicable files. Do not apply one client's rules to another client. If the client cannot be identified unambiguously, ask before drafting. If the folder does not exist or has no applicable reference, continue with the user's brief and brand context, state that client-specific email guidance was unavailable, and do not invent it.
3. Load and follow the `$copywriter` skill at `../copywriter/SKILL.md`. This skill is the channel-specific caller. Give it the deliverable, objective, audience, offer or message, required facts and sources, constraints, desired action, this skill directory, `references/email-frameworks.md`, and the applicable files from `./email-marketing/references/`.

The copywriter skill's required `./_context/ABOUT.md`, `./_context/SOUL.md`, and human-writing review remain mandatory according to its own rules.

## Choose the framework

Choose the framework only after understanding the topic, reader, objective, and CTA. Use the quick selection guide in `references/email-frameworks.md`; select the framework whose dominant job best matches the campaign.

Use one primary framework. Blend in a secondary technique only when it improves clarity without making the structure feel formulaic. Never expose framework labels inside the reader-facing body. If the evidence does not support a pain-based or transformation-based argument, choose a safer framework rather than manufacturing pain or outcomes.

Record the chosen framework and a one-sentence rationale in the Markdown draft's internal campaign notes. Do not include those notes in the reader-facing HTML.

## Draft the campaign

Unless the user or applicable project reference says otherwise, produce:

- one recommended subject line and two genuinely distinct alternatives;
- one preheader that complements rather than repeats the subject;
- a concise email body organized by the chosen framework;
- one primary CTA with destination URL or a reply-based action;
- the client-required sign-off and marketing footer.

Keep the message focused on one memorable idea and one primary action. Match claims, urgency, segmentation, personalization, formatting, compliance language, and link conventions to the supplied facts and applicable client references. Describe the result as conversion-focused; never promise conversion performance.

For a marketing footer, use the client's exact approved language and merge tags when available. If required footer information is missing, mark it conspicuously in both drafts, such as `[PHYSICAL MAILING ADDRESS REQUIRED]` or `[UNSUBSCRIBE URL REQUIRED]`, rather than inventing values.

## Export both files

Use the current local date in `YYYYmmdd` format. Create this directory if needed:

`./email-marketing/draft-emails/YYYYmmdd/`

The default pair is:

- `YYYYmmdd-email.md`
- `YYYYmmdd-email.html`

Keep the basename identical for the pair. Do not overwrite an existing draft unless the user explicitly asked to revise or replace it. For a new draft when the default pair already exists, use `YYYYmmdd-email-02`, then increment the two-digit suffix as needed.

The Markdown file must contain internal campaign notes, the three subject options, preheader, reader-facing body, CTA, and footer in a clean, editable structure.

The HTML file must contain the selected subject in the document title and an HTML comment, a hidden preheader, and only the reader-facing email. Produce a self-contained email document with semantic text, inline styles, a restrained 600px responsive layout, accessible link text, useful image alt text when images are supplied, and no JavaScript, external stylesheets, tracking pixels, invented images, or unsupported assets. Preserve the same wording, link destinations, sign-off, and footer as the Markdown version.

After writing, verify that both files exist, share the same basename, contain no accidental omissions between formats, and have no unlabeled invented or unresolved claims. Return clickable paths to both files and briefly identify the selected framework. Do not send, schedule, or publish the email unless the user separately asks and the required capability is available.
