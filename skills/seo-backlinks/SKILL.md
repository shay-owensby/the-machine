---
name: seo-backlinks
description: Analyze backlink profiles with the DataForSEO MCP, including referring domains, anchor-text distribution, suspicious-link triage, competitor link gaps, new and lost links, and verification of supplied backlink lists. Use for `/seo backlinks` commands or requests for a DataForSEO-backed backlink audit; do not use for internal-link audits or link-building outreach.
---

# SEO Backlinks

Produce evidence-backed backlink analysis from the DataForSEO Backlinks API through the configured DataForSEO MCP. Treat the provider index as an observed sample, not a complete census of the web.

## Route the command

Interpret these command forms exactly; angle-bracketed values are user inputs, not literal text:

- `/seo backlinks <url>` — full profile: baseline, referring domains, anchor distribution, suspicious-link triage, new/lost trend, and an automatically discovered competitor gap.
- `/seo backlinks gap <url1> <url2>` — domains linking to `url2` but not `url1`, with `url1` as the site to improve and `url2` as the competitor.
- `/seo backlinks toxic <url>` — suspicious-link and referring-domain investigation. Use “toxic” as the user's requested command label, but report risk and evidence rather than claiming certain harm.
- `/seo backlinks new <url>` — new and lost backlinks and referring domains. Default to the latest 90 complete days, grouped by week, unless the user supplies another window.
- `/seo backlinks verify <url> --links <file>` — verify the supplied source links against live and lost DataForSEO backlink observations for the target URL/domain.

Also route natural-language requests to the closest mode. If a required URL or `--links` file is genuinely missing, ask for only that input. Preserve page scope when the user supplies a page URL; do not silently broaden it to the whole domain.

Before calling data tools, read [references/dataforseo-workflows.md](references/dataforseo-workflows.md). For `toxic`, full profile, or any risk/remediation request, also read [references/risk-and-reporting.md](references/risk-and-reporting.md).

## Data acquisition rules

- Use the DataForSEO MCP dependency. Tool names may vary by MCP release, so select the tool whose documented operation matches the endpoint in the workflow reference; never invent a tool name or field.
- Use the Backlinks API `live` methods. Record each endpoint, retrieval timestamp, target normalization, filters, status mode, pagination/limits, returned count, total count when supplied, and DataForSEO task cost when exposed.
- Normalize a domain/subdomain target without scheme or `www.` when the endpoint requires it. Preserve an absolute URL for page-level targets. Keep a display copy of the user's original input.
- Default to `include_subdomains: true`, `exclude_internal_backlinks: true`, and `rank_scale: one_hundred` where supported. State these choices in the report. Do not apply a dofollow-only filter unless the user asks; nofollow, UGC, and sponsored links remain relevant evidence.
- Paginate enough to support the conclusion. If provider limits, cost controls, tool availability, or result volume prevent full retrieval, state the exact sampled coverage and lower confidence accordingly.
- Check top-priority or high-risk source pages individually when the available tools permit it. Do not claim a live placement solely because it appeared historically in the index.
- If the DataForSEO MCP is unavailable, disconnected, or returns an unrecoverable error, stop the affected analysis and report the missing dependency or error. Do not fabricate metrics or silently switch to another backlink vendor.

## Analysis standards

- Distinguish total backlinks from unique referring domains and main domains.
- Segment anchors into branded, naked URL, generic, topical/partial-match, exact commercial, image/empty, and other. Show both link-count and referring-domain distributions when the API response supports them.
- Interpret concentrations in context. Repeated sitewide links, redirects, canonicals, image links, and multiple links from one domain must not be presented as equivalent independent endorsements.
- Base opportunity ranking on topical fit, editorial plausibility, source quality, destination fit, followability, estimated replicability, and risk. Do not rank by DataForSEO Rank alone.
- Separate observed facts, calculated values, and analyst inference. Label calculations and include denominators.
- Do not promise ranking improvement or treat correlation as causation.

## Deliverables

Immediately before writing, determine the current local date and year. Resolve `.` against the active project root/current working directory and create:

```text
./seo-aeo/seo-backlinks/<YYYY>/
```

Save the paired deliverables with the same default basename:

```text
<YYYYmmdd>-backlinks-analysis.md
<YYYYmmdd>-backlinks-analysis.html
```

Use the run date, not the site's publication date or analysis-window end date. If both default paths already exist, preserve them and append `-2`, `-3`, and so on to both basenames. Never overwrite an existing report unless the user explicitly asks.

The Markdown and HTML must contain materially identical findings. The HTML must be a complete standalone UTF-8 document with readable responsive tables, print styles, visible source links, and no external runtime dependency. Escape all imported values before inserting them into HTML. Write both files only after the evidence has been gathered; if the output directory cannot be written, report the intended path and do not fall back elsewhere.

Follow the mode-specific report contract in [references/risk-and-reporting.md](references/risk-and-reporting.md). Include at minimum:

1. executive summary and prioritized actions;
2. scope, target(s), run date, analysis window, DataForSEO endpoints, and coverage limitations;
3. requested analysis tables and distributions;
4. evidence-backed risks or gaps with confidence labels;
5. methodology, definitions, and provider limitations.

Before finishing, verify that both files exist, open the HTML enough to confirm valid structure and escaped content, and confirm that the headline figures agree across formats. Return clickable links to both artifacts.

## Safeguards

- A DataForSEO spam score is a screening signal, not proof that a link is harmful or manipulative.
- Do not recommend removal or disavow from a score, TLD, language, country, low Rank, or exact-match anchor alone.
- Do not create, upload, or modify a disavow file, contact publishers, buy placements, or perform outreach without explicit authorization.
- If a manual action, known paid-link campaign, hacked placement, or existing disavow file is relevant, distinguish that evidence from algorithmic speculation and recommend qualified manual review before irreversible action.
