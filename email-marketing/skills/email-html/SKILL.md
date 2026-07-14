---
name: email-html
description: Author and review email-client-safe HTML for newsletter bodies. Use when writing, editing, or QA-ing email HTML — table layout, inline CSS, 600px width, dark mode, Outlook/Gmail quirks, bulletproof buttons.
---

# Email-Safe HTML

Email HTML is not web HTML. Gmail, Outlook (Word rendering engine!), Apple Mail, and mobile clients each strip or mangle different things. These rules are non-negotiable unless a platform reference says otherwise.

Use [references/html-boilerplate.md](references/html-boilerplate.md) as the starting skeleton and [references/qa-checklist.md](references/qa-checklist.md) before any draft ships.

## Scope: body only

The client's header and footer (logo, address, unsubscribe) are configured **on the email platform**. Produce only the body fragment between them. Never include `<html>`, `<head>`, `<body>` tags, unsubscribe links, or a footer address block — the platform supplies those. (Exception: a platform reference may state its content endpoint requires a full document; follow the reference.)

## Hard rules

**Layout**
- Nested `<table role="presentation">` layout only — no flexbox, no grid, no floats, no `<div>`-based columns.
- Outer wrapper: `width="600"` with `max-width: 600px` and centered; single column preferred; stack any columns on mobile.
- Spacing via padding on `<td>` — never margins (Outlook drops them unpredictably).

**CSS**
- Every style inline on the element. No `<style>` blocks (Gmail clips them in some contexts), no external stylesheets, no CSS shorthand that Outlook misreads (write `padding-top/right/bottom/left` if in doubt).
- Fonts: web-safe stacks only — e.g. `font-family: Arial, Helvetica, sans-serif` or `Georgia, 'Times New Roman', serif`. Map DESIGN.md fonts to the closest web-safe stack; webfonts only as progressive enhancement with a stacked fallback.
- No JS, no forms, no `<video>`, no CSS animation, no background images for critical content.

**Images**
- Explicit `width` and `height` attributes AND inline `style="max-width:100%; height:auto; display:block;"`.
- Meaningful `alt` text on every image; styled alt (inline color/font on the `<img>`) so images-off still reads.
- Serve 2× resolution for retina (1200px-wide file displayed at 600).
- Absolute `https://` URLs only. Total image weight sensible (<1MB per email); email must make sense with all images blocked.

**Buttons**
- Bulletproof buttons: a padded `<td>` with `bgcolor`, border-radius, and a padded inline-block `<a>` — not an image, not CSS-only. One primary CTA per email; repeat it at the bottom for long emails.

**Dark mode**
- Avoid pure `#FFFFFF` backgrounds and pure `#000000` text (some clients invert; near-values like `#FEFEFE`/`#111111` invert more gracefully).
- Logos/graphics with transparent backgrounds must survive both light and dark backdrops (add a subtle outline or padding plate if DESIGN.md colors would vanish).
- Don't rely on color alone to convey meaning.

**Size**
- Total HTML under **100KB** or Gmail clips the message (hiding content and tracking). Aim under 70KB. If dynamic sections balloon the size, truncate with "read more" links.

**Links**
- Absolute `https://` only; no `localhost`, no bare domains, no `mailto:` typos. Add the client's UTM convention consistently if one exists (`utm_source=newsletter&utm_medium=email&utm_campaign=<slug>`).

## Subject line & preview text

- Subject: aim ≤ 50 characters (mobile truncation); no ALL CAPS words, no more than one `!` or emoji, avoid spam triggers (see qa-checklist).
- Preview text: 40–90 characters that **complements** the subject (continues the thought) rather than repeating it. Supplied to the platform's preview/preheader field when the API supports it; also add the hidden-preheader span from the boilerplate as a fallback, followed by the whitespace-padding hack so trailing body text doesn't leak into the inbox preview.

## Rendering sections from config

The client config's `sections[]` array defines recurring blocks. Render them in position order (`top` → main body → `after_body` → `bottom`), preserving array order within a position. `static` sections render their `content` verbatim (convert markdown to email-safe HTML); `dynamic` sections are fetched fresh from `source` each issue (e.g. latest blog post: title, one-line teaser, image if available, link).
