---
name: email-topic-research
description: Research trending, brand-relevant newsletter topics with mandatory dedup against the project's topic log. Use when selecting or validating topics for an upcoming email issue.
---

# Email Topic Research

Goal: surface **1–3 topic candidates** for the next issue that are timely, on-brand, and have never been suggested before.

## Order of operations

### 1. Read the log FIRST — dedup is non-negotiable

Read `email-marketing/references/topic-researcher.md` in the client project (format spec: `${CLAUDE_PLUGIN_ROOT}/skills/email-marketing-config/references/topic-log-format.md`). Build the exclusion list from **every** row — `suggested`, `used`, and `rejected` alike. A candidate is a duplicate if its slug matches OR it semantically overlaps an existing row ("5 winter coat tips" duplicates "Winter coat care guide"). When in doubt, it's a duplicate — find a genuinely new angle instead.

If the log file is missing in a configured project, recreate it from the template (empty), note that dedup history was lost, and proceed.

### 2. Gather inputs

Read the client's `brand.about_file` (path from config) first — it's the primary source of what the business actually does and sells; ground every candidate in a real product, service, or offer it describes. If `about_file` is null, fall back to `brand.industry` and `brand.audience_description` from config and note the degradation. Also from `email-marketing/config.yaml`: `brand.topic_hints`, `brand.website`, `brand.timezone` (for seasonality). Plus, when provided by the orchestrator: the user's kickoff notes (highest priority — if the user already named a topic, validate and enrich it rather than replacing it) and the campaign-analyst's insights (lean toward what historically got opens/clicks).

### 3. Research — tool ladder

Work down the ladder; use what's available, degrade gracefully:

1. **Semrush MCP** (if connected): `trends_research` and `keyword_research` for search-demand signals in the client's niche; rising queries beat evergreen ones.
2. **WebSearch**: `"<industry> trends <Month Year>"`, `"<industry> news"`, seasonal hooks for the coming 2–3 weeks (holidays, weather, events, buying seasons — compute from today's date and the client timezone), competitor newsletter angles.
3. **WebFetch** the client's own site/blog (`brand.website`): what they've published lately (tie-in opportunities, and avoid suggesting what they just covered).

Collect 2–3 source URLs per candidate. No sources → not a candidate.

### 4. Score and select

Score each candidate on: audience relevance, timeliness (why THIS week?), fit with `topic_hints`, distance from everything in the log, actionability (can it carry a CTA?), and fit with what the brand actually offers per ABOUT.md — a topic the brand cannot credibly speak to, or cannot tie to a real service/product, scores zero. Keep the top 1–3 — genuinely distinct from each other, not three variations of one idea.

### 5. Log — mandatory, before returning

Prepend a new `## YYYY-mm-dd` section with ALL candidates (status `suggested`) to the TOP of `email-marketing/references/topic-researcher.md`, immediately after `<!-- LOG:BEGIN -->`, exactly per the format spec. Valid markdown, all 7 columns, newest-first. **Do this before returning results — a candidate that isn't logged doesn't exist.**

## Output contract

Return exactly this structure so the orchestrator can present it:

```markdown
## Topic candidates — YYYY-mm-dd

### 1. <Topic title>
- **Angle:** one sentence on the specific take for this brand
- **Why now:** one sentence on timeliness
- **Sources:** [<domain>](url), [<domain>](url)
- **Slug:** <kebab-slug>

### 2. …(same shape; 1–3 total)

Logged all N candidates to email-marketing/references/topic-researcher.md.
```
