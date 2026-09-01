---
name: seo-schema
description: Detect, audit, validate, troubleshoot, and generate Schema.org structured data for webpages, preferring JSON-LD and checking Microdata, RDFa, current term status, and Google rich-result eligibility. Use for schema markup audits, structured-data errors, rich-result readiness, missing schema opportunities, or implementation-ready JSON-LD.
---

# SEO Schema

Audit or create structured data that accurately represents visible page content. Treat Schema.org validity and Google rich-result eligibility as separate conclusions: valid Schema.org markup does not necessarily qualify for a Google feature.

## Choose the mode

- For an existing page, URL, HTML file, or pasted source, perform an audit. Read [references/validation.md](references/validation.md) before inspecting it.
- When asked to create or revise markup, read [references/generation.md](references/generation.md). If existing markup is available, also read the validation reference and audit before generating.
- When asked for both, audit first, then generate only the changes supported by the page.

## Core constraints

- Prefer JSON-LD for new markup. Detect and report JSON-LD, Microdata, and RDFa already present; do not assume JSON-LD is the only source of entities.
- Base every entity and value on visible page content, supplied business facts, or another source the user has authorized. Never invent people, ratings, prices, availability, dates, identifiers, addresses, policies, or relationships.
- Use clearly marked placeholders when a necessary fact is unavailable. Label any code containing placeholders **draft—do not deploy** and enumerate each unresolved value.
- Check every emitted type and property against the current official Schema.org release. Do not emit pending, superseded, deprecated, or attic terms. Recommend the stable replacement when one exists.
- Check Google eligibility against the current Search Gallery, general structured-data guidelines, and the feature-specific Google documentation. Never infer Google support from Schema.org validity alone.
- For reviews, reject fabricated reviews, reviews not based on genuine experience, undisclosed incentivized reviews, imported/aggregated ratings from other websites, and self-serving review markup that violates Google's rules. Explain the rejection and offer a compliant alternative if one exists.
- Do not promise a rich result. Valid markup only establishes eligibility; search engines decide whether to display it.

## Required artifacts

Immediately before writing the deliverables, determine the current local date in `YYYYmmdd` format and set the output directory to:

```text
./seo-aeo/schema/YYYYmmdd/
```

Resolve `.` against the active project root/current working directory. Replace `YYYYmmdd` with the actual run date, not the page's publication date, audit period, or another content date. Create the date directory and all missing parents before writing; the current-date folder is expected not to exist. Do not redirect these artifacts to the working-directory root or another default location.

Save both completed deliverables directly in that created date directory:

- `schema-report.md` — the evidence-backed audit, recommendations, validation results, implementation guidance, and limitations.
- `generated-schema.json` — the strict, pure JSON-LD document only. Do not include Markdown fences, an HTML `<script>` wrapper, comments, or explanatory text in this file.

Produce both files for every completed run. Generate the safest truthful graph supported by the evidence, even when a requested review or other entity must be omitted for policy reasons. If no meaningful entity can be generated without inventing facts, write a syntactically valid JSON-LD document with `"@context": "https://schema.org"` and an empty `"@graph"`, mark it **non-deployable** in `schema-report.md`, and identify the minimum facts needed to replace it. If placeholders are necessary, keep the JSON syntactically valid, mark the file **draft—do not deploy** in the report, and list every placeholder.

Before finishing, parse the saved `generated-schema.json` as strict JSON and verify that the saved report accurately states whether it is deployable, draft, or intentionally empty. If the output directory cannot be created or written, do not silently fall back to another directory; report the exact intended path and failure. Return clickable links to both artifacts using their final dated paths.

## Report contents

Return an evidence-backed result containing:

1. **Page classification** — primary page type and confidence, with the visible evidence used.
2. **Detected markup** — each JSON-LD block and each Microdata/RDFa item, including conflicts or duplicates.
3. **Validation findings** — errors, warnings, and opportunities separated by severity. Identify whether each finding is a JSON/format issue, Schema.org vocabulary issue, Google eligibility issue, or content-policy issue.
4. **Recommended schema** — primary and supporting types, why each belongs, and any missing facts that prevent complete markup.
5. **Generated schema status** — summarize what was written to `generated-schema.json`, including omitted entities, placeholders, and deployability.
6. **Implementation and retest steps** — placement, conflicts to remove, validators to run, and post-deployment checks.

If the page cannot be fetched or fully rendered, continue with the available evidence, state the limitation precisely, and request only the minimum missing input needed for a conclusive result.
