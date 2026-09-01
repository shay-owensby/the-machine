# Structured-data validation

Use this procedure for URL, HTML, source-code, or pasted-markup audits.

## Authoritative sources

Requirements change. Verify them live at audit time rather than relying on a memorized property list:

- Current stable Schema.org release: <https://schema.org/version/latest/>
- Schema.org releases and status context: <https://schema.org/docs/releases.html>
- Schema.org term definitions and machine-readable vocabulary: <https://schema.org/docs/developers.html>
- Schema.org evolution and `supersededBy`: <https://schema.org/docs/howwework.html>
- Schema.org Markup Validator: <https://validator.schema.org/>
- Google supported structured-data features: <https://developers.google.com/search/docs/appearance/structured-data/search-gallery>
- Google general structured-data guidelines: <https://developers.google.com/search/docs/appearance/structured-data/sd-policies>
- Google Rich Results Test: <https://search.google.com/test/rich-results>
- Google review-snippet rules: <https://developers.google.com/search/docs/appearance/structured-data/review-snippet>

Prefer these primary sources. Use the feature-specific Google guide linked from the Search Gallery as the definitive source for its required/recommended properties and policies.

## Acquire the right representation

1. For a URL, retrieve the raw response source and record the final URL, status, content type, canonical URL, robots/noindex state when visible, and any redirects.
2. Also inspect the rendered DOM when markup may be injected, changed, or removed by JavaScript. Distinguish **raw-source findings** from **rendered-DOM findings**.
3. For local HTML or pasted source, state that crawlability, rendering, headers, canonicalization, and production parity were not tested.
4. Never bypass authentication, bot controls, or other access restrictions. If access fails, accept supplied source or markup and narrow the conclusion.

For static HTML, run:

```bash
python3 scripts/scan_structured_data.py <URL-or-HTML-path>
```

The scanner extracts JSON-LD and inventories Microdata and RDFa. It performs deterministic JSON and common-shape checks; it does not replace live vocabulary or Google feature validation.

## Detect all formats

### JSON-LD

- Inspect every `<script type="application/ld+json">`, including multiple nodes, arrays, and `@graph` containers.
- Parse as strict JSON. Report malformed JSON, duplicate keys, empty blocks, comments/trailing commas, invalid top-level values, and placeholder tokens.
- Inventory every `@type`, `@id`, and relationship. Follow nested entities and references instead of validating only the outer node.

### Microdata

- Search for `itemscope`, `itemtype`, `itemprop`, `itemid`, and `itemref`.
- Reconstruct the item hierarchy. Flag orphan `itemprop` values, missing/invalid `itemtype`, broken `itemref`, and conflicting nested scopes.

### RDFa

- Search for `typeof`, `property`, `vocab`, `prefix`, `resource`, `about`, and `rel`/`rev` where relevant.
- Resolve vocabulary/prefix context and entity relationships. Flag properties without a usable subject/type and unresolvable or conflicting vocabulary declarations.

If the same entity appears in multiple formats, compare it for contradictory names, URLs, dates, offers, ratings, identifiers, or types. Do not recommend duplicate markup merely to use more formats.

## Validation layers

Run all applicable layers and label the source of each finding.

### 1. Syntax and graph integrity

- Valid JSON and JSON-LD shape; canonical `https://schema.org` context for generated markup.
- `@type` is present where an entity needs typing; `@id` values are stable, absolute URLs or purposeful same-document fragments.
- References resolve consistently; duplicated entities do not conflict.
- Property values use the expected shape and type: scalar versus object/array, URL, ISO date/time/duration, number, currency, enumeration, or nested entity.
- URLs are absolute where consumers require them and use the production canonical host.

### 2. Schema.org vocabulary status

For every type and property—not just the main type:

1. Confirm that its canonical term page exists in the current stable release.
2. Confirm its domain/range is appropriate for the entity/value.
3. Reject terms marked pending, superseded, deprecated, or attic/retired. Follow `supersededBy` to a stable replacement when available.
4. Do not treat a staging-only term as active.

Schema.org itself does not define universal “required properties.” Its vocabulary validity is separate from consumer requirements.

### 3. Google feature eligibility

1. Match each entity to a currently supported Search Gallery feature, if any.
2. Open that feature's current Google guide and check every required property, then every applicable recommended property and content/technical policy.
3. Identify Schema.org-valid entities with no supported Google rich result as **valid vocabulary, no current Google rich-result feature**.
4. Test code or the accessible URL in the Rich Results Test. Use the Schema.org Markup Validator for vocabulary-wide validation.
5. Treat validator warnings as improvement opportunities unless the guide makes them required. Never claim eligibility when a critical error or policy violation remains.

## Common errors to test

- Missing/incorrect `@context` or `@type`; misspelled or wrongly cased terms.
- Invalid/superseded types or properties; properties placed on an incompatible type.
- Required Google properties absent, empty, or represented with the wrong value type.
- Markup that contradicts or is absent from visible page content.
- A generic type used where a more specific accurate type is available.
- Organization/website markup repeated as the primary entity on every page without page-specific markup.
- Multiple plugins/templates emitting overlapping, conflicting entities.
- Broken `@id` links or inconsistent IDs for the same entity across pages.
- Relative, blocked, non-canonical, staging, redirected, or non-indexable URLs/images.
- Invalid dates, time zones, durations, prices, currencies, availability, counts, or rating bounds.
- Aggregate rating arithmetic that cannot be substantiated by visible first-party review data.
- Marking up category/list pages as a single product, recipe, event, job, or other detail entity.
- Event/job/offer content that is expired but still marked active.
- FAQ or HowTo markup assumed to be Google-supported without checking the current Search Gallery and eligibility restrictions.
- Markup injected only after an interaction, blocked from crawlers, hidden, or different between raw and rendered content.
- Review policy violations, including fake, undisclosed incentivized, imported aggregate, or ineligible self-serving reviews.

## Error handling

- **Fetch failure, timeout, DNS/TLS error:** report the exact failure and URL; do not infer that markup is absent. Offer source/pasted HTML as the next input.
- **403, bot challenge, login, robots restriction:** do not circumvent it. Audit supplied source or user-authorized rendered output and mark crawlability unverified.
- **Non-HTML response or oversized input:** stop safely, report the content type/size limit, and request the relevant HTML or markup.
- **Malformed JSON-LD:** preserve a short locator/block number, not an enormous source dump. Continue scanning other blocks and formats.
- **Client-rendering uncertainty:** inspect a rendered DOM when possible; otherwise label dynamic markup unverified.
- **Validator unavailable:** complete local syntax/content checks, link the validator, and explicitly mark external validation pending.
- **Conflicting official sources:** use the current feature-specific Google guide for Google eligibility and the stable Schema.org release for vocabulary status; document the conflict.
- **Insufficient facts:** do not fill gaps by guessing. Either omit optional properties or generate a clearly labeled non-deployable placeholder draft.

## Severity

- **Error:** invalid syntax/vocabulary, deprecated term, missing Google-required property, contradiction, or policy violation that blocks validity/eligibility.
- **Warning:** likely quality, rendering, duplication, consistency, or recommended-property issue that may reduce usefulness but is not proven blocking.
- **Opportunity:** relevant, truthful schema is absent or can be strengthened with verifiable recommended properties.
- **Pass:** a tested layer passed; state what was actually tested rather than “fully valid.”

## Save the result

Immediately before export, determine the current local date in `YYYYmmdd` format and create `./seo-aeo/schema/YYYYmmdd/`, including all missing parents. Write all findings, evidence, fixes, missing opportunities, limitations, and test scope to `./seo-aeo/schema/YYYYmmdd/schema-report.md`. Write the recommended JSON-LD graph to `./seo-aeo/schema/YYYYmmdd/generated-schema.json` following the generation reference. Even for an audit-only prompt, produce the safest truthful recommended graph supported by the page; never copy known-invalid or policy-violating markup into the generated file. Do not fall back to another directory if the dated destination cannot be created or written.
