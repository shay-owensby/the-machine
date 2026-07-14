# Pre-Flight QA Checklist

Run every category on every draft. Report findings as a table: `| # | Severity | Category | Finding | Fix |` with severity **blocker** (must fix before delivery), **warn** (fix recommended), **nit**. End with a verdict: `PASS`, `PASS WITH WARNINGS`, or `FAIL`.

## 1. Subject line & preview text

- [ ] Subject ≤ 50 chars (warn to 60; blocker above 80)
- [ ] Preview text 40–90 chars; complements (doesn't repeat) the subject
- [ ] A/B variants genuinely differ in strategy (curiosity vs benefit vs specificity), not just wording
- [ ] No ALL-CAPS words, ≤ 1 exclamation mark, ≤ 1 emoji, no "Re:/Fwd:" fakery (blocker — deceptive)
- [ ] Hidden preheader span present and matches meta.yaml preview text

## 2. Spam triggers

Flag (warn) if copy leans on these — one instance is context-dependent, clusters are blockers:

- Money/pressure: `free!!!`, `act now`, `limited time only`, `urgent`, `don't miss out`, `once in a lifetime`, `winner`, `cash`, `$$$`, `100% free`, `risk-free`, `no obligation`, `guarantee(d)`
- Shady mechanics: `click here` as the only anchor text, `open immediately`, `this is not spam`, `unsubscribe` in body copy (platform footer handles it)
- Formatting spam-signals: ALL CAPS sentences, red text, > 3 consecutive `!` or `?`, excessive currency symbols
- Image-to-text balance: email must NOT be one giant image; meaningful text should carry the message with images blocked

## 3. Links

- [ ] Every `href` absolute `https://` (blocker: `http://` on client-owned pages, `localhost`, relative paths, empty `#`)
- [ ] Every link fetched and resolves (2xx/3xx) — check each with WebFetch or `curl -sIL`
- [ ] Anchor text meaningful (not bare URLs, not "click here" everywhere)
- [ ] UTM parameters consistent across links if the client uses them
- [ ] CTA URL goes where the CTA promises

## 4. Images

- [ ] Every `<img>` has non-empty, descriptive `alt`
- [ ] Explicit `width`/`height` attributes + `display:block`
- [ ] URLs are `https://` and actually load (check each)
- [ ] Hosting matches config: `platform_upload` → platform CDN domain, not the generator's; `hosted_url` → confirm meta.yaml carries `re_host_before_send: true` (warn)
- [ ] Retina sizing (file ~2× display width); no image over ~500KB

## 5. HTML structure & rendering

- [ ] Body fragment only — no `<html>/<head>/<body>`, no unsubscribe/footer address (platform supplies) unless the platform reference requires a full document
- [ ] Tables with `role="presentation"`; no flex/grid/float layout
- [ ] All CSS inline; no `<style>` blocks, no external CSS, no webfonts without stacked fallback
- [ ] Spacing via `td` padding, not margins
- [ ] No JS, forms, video, or CSS animation
- [ ] Width 600px max, centered; would read fine on a 375px phone (single column, ≥ 14px fonts, ≥ 44px tap targets)
- [ ] Total HTML size < 100KB (blocker — Gmail clips), target < 70KB (warn above)

## 6. Dark mode & accessibility

- [ ] No pure `#FFFFFF`/`#000000` (use near-values that invert gracefully)
- [ ] Text contrast ≥ 4.5:1 against its background
- [ ] Transparent images survive a dark backdrop
- [ ] Reading order sensible when linearized; headings hierarchical (h1 → h2)
- [ ] Language is readable aloud (screen readers): no meaning carried by color or emoji alone

## 7. Brand & content compliance

- [ ] Voice matches SOUL.md (tone, vocabulary, phrases to avoid); if `soul_file: null`, confirm the degraded-voice warning is present
- [ ] Colors/styling consistent with DESIGN.md mapping
- [ ] Business-fact claims (services, products, prices, locations, credentials, guarantees) trace to ABOUT.md or the user's kickoff notes; anything in neither is a blocker
- [ ] All config `sections[]` present, in the right positions and order; dynamic sections show FRESH content (not last issue's)
- [ ] Factual claims in the copy are supported by the research sources; dates/prices/offers confirmed with the user's kickoff input
- [ ] No fabricated testimonials, reviews, or statistics (blocker)
- [ ] Nothing contradicts the user's kickoff instructions for this issue

## 8. Metadata & bookkeeping

- [ ] meta.yaml complete: date, topic + slug, subject a/b/c, preview_text, images with alt + hosting, platform, status
- [ ] Draft folder named `YYYY-mm-dd`, files named `YYYY-mm-dd.html` / `YYYY-mm-dd.meta.yaml`
- [ ] Topic logged in `references/topic-researcher.md` (newest-first) — chosen row will flip to `used` at delivery
