---
name: pr-competitor-search
description: Identify and document evidence-backed competitors in a client's local market using current web search. Use when asked for local competitor discovery, a local competitive landscape, or a PR-oriented competitor list; do not use for a full SEO, backlink, or paid-media audit.
---

# PR Competitor Search

Produce a current, source-linked Markdown report identifying the businesses that compete with the client in its defined local market.

## Required client rules

Work from the client project root. Before searching, read `./_references/public-relations/competitors.md` in full. Treat that file as authoritative for the client identity, offerings, geography or service area, inclusion and exclusion rules, terminology, and requested report details.

If the file is missing, say which path is required and stop. If a material fact needed to define the market is absent or contradictory, ask one focused question before searching. Do not guess the client's location, service area, primary offering, or competitor definition.

## Research

1. Translate the client rules into a short working definition of the market: offering, customer need, geography, and any mandatory exclusions.
2. Use current web search. Search the primary offering and close customer-language variants across the named city, nearby communities, and service area when allowed by the client rules. Include map or local-directory results as discovery sources when useful.
3. Verify each candidate against its official website or official business profile. Use an additional credible source when the service area, location, business identity, or competitive overlap is unclear. A search-result snippet alone is not sufficient evidence.
4. Include a business only when the available evidence shows both meaningful offering overlap and presence in, or active service to, the defined market. Apply all client-specific exclusions before ranking or writing.
5. Deduplicate brands, domains, aliases, and multiple locations belonging to the same business unless branch-level competition matters under the client rules.
6. Rank candidates by competitive relevance using observable evidence such as offering overlap, geographic overlap, customer segment, positioning, local prominence, and PR visibility. Do not infer revenue, market share, reputation, or business performance without evidence.
7. Separate confirmed facts from interpretation. Mark unresolved candidates as `Needs verification` rather than presenting them as confirmed competitors.

Prefer official business websites, official profiles, chambers or professional bodies, local news, and reputable directories. Link to the exact pages that support material claims. Note the access date for web research and avoid unsupported superlatives.

## Report

Write a useful, concise report containing:

- report date, client, and researched market;
- the market definition and client rules applied;
- an executive summary of the local competitive landscape;
- a competitor matrix with business name, website, location or service area, offering overlap, positioning or differentiator, relevance, verification status, and supporting links;
- brief profiles of the most relevant confirmed competitors, including why each competes and any observable PR or visibility signals relevant to the assignment;
- excluded or unresolved candidates when documenting them prevents ambiguity, with the reason;
- methodology, limitations, and research date.

Use the client file's requested structure or fields when it conflicts with this default. Do not pad the report to reach an arbitrary competitor count, and do not include a candidate merely because it ranks in search.

## Save and handoff

Create `./public-relations/competitors/` if needed. Save the finished Markdown report as:

`./public-relations/competitors/YYYYmmdd-competitors.md`

Use the report-generation date in the client timezone when the client rules specify one; otherwise use the system-local date. If that day's default file already exists, do not overwrite it without the user's approval.

Before finishing, confirm that every listed competitor satisfies the market definition, material claims have source links, duplicate businesses are merged, all client rules were applied, and no placeholders remain. Return a clickable link to the saved report and summarize the number of confirmed and unresolved candidates.

## Boundaries

- Research public web information only. Do not contact businesses, submit forms, create accounts, purchase data, or modify external systems.
- Do not fabricate facts, citations, locations, service areas, or competitive relationships.
- Keep personal data out of the report unless the client rules explicitly require a public spokesperson or owner relevant to PR analysis.
- This skill identifies competitors; it does not perform a full SEO, backlink, social, advertising, or financial analysis unless the user separately requests that work.
