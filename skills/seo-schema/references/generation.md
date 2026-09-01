# JSON-LD generation

Use this procedure to create or repair structured data for a page.

## 1. Classify the page from content

Identify the page's single main purpose from its title, headings, primary visible content, calls to action, URL pattern, canonical URL, and site context. Examples include homepage/about organization, local business location, article/news/blog post, product detail, product variant, category/list, service, event, job, recipe, course, profile, software app, video, dataset, discussion, or contact page.

Do not choose a type because it offers an attractive rich result. Choose the most specific stable type that truthfully describes the page's main entity. State confidence and what ambiguity remains.

## 2. Select a coherent graph

- Choose one primary page entity and supporting entities only when they are visible or verifiable and materially help describe it.
- Common supporting entities may include `WebSite`, `WebPage` or a more specific page subtype, `Organization`/`Person`, `BreadcrumbList`, `ImageObject`, `VideoObject`, `Offer`, or `PostalAddress`; include them only when applicable.
- Reuse stable absolute `@id` values to connect entities instead of duplicating conflicting copies. Keep sitewide entity IDs consistent with existing canonical markup.
- Do not add standalone types solely because they exist on Schema.org. If a type has no current Google rich result, it may still be semantically useful, but explain that distinction.
- Before using a type/property, verify it on the current stable Schema.org term page and confirm it is not pending, superseded, deprecated, or attic/retired.

## 3. Gather facts and map requirements

Create an internal fact table with: property, value, evidence/source, visibility on page, required/recommended/optional status for the current Google feature, and confidence.

- Include all Google-required properties for an intended supported feature.
- Include applicable recommended properties when truthful and available; do not stuff markup with weak, redundant, or unverifiable values.
- Do not translate absence into a zero, empty string, generic fallback, or invented value.
- Keep dates/times, durations, money/currency, availability, ratings, URLs, identifiers, and images in the formats required by the current feature guide.
- Use the page's canonical production URLs. Images and referenced resources must be crawlable/indexable when Google requires it.

## 4. Handle missing facts

Prefer omitting optional properties. When a required or strategically important fact is missing:

1. Ask for it if the user can reasonably supply it and it changes the implementation.
2. If a template is still useful, use an unmistakable syntactically valid string such as `REPLACE_WITH_VERIFIED_CANONICAL_URL` or `REPLACE_WITH_VERIFIED_VALUE`.
3. Label the entire snippet **draft—do not deploy**.
4. List every placeholder and the expected format/evidence.

Do not claim a placeholder draft passes semantic or Google eligibility validation. It may pass JSON parsing only.

## 5. Review and rating safeguards

Before generating `Review`, `AggregateRating`, `review`, or `aggregateRating`, verify:

- The reviews/ratings represent genuine experiences and are visible to users on the marked page.
- Any incentive is clearly and prominently disclosed.
- Counts, averages, scale, authorship, dates, and reviewed item are verifiable.
- Ratings are not aggregated from other websites.
- The reviewed entity and publisher arrangement complies with the current Google review-snippet rules, including restrictions on self-serving `LocalBusiness`/`Organization` reviews.

Reject fake reviews and undisclosed incentivized reviews. Do not “sanitize” fabricated data into markup. Explain which rule blocks it and provide a compliant option such as omitting review markup or collecting and displaying genuine first-party reviews with proper disclosures.

## 6. Generate JSON-LD

- Determine the current local date immediately before export, create `./seo-aeo/schema/YYYYmmdd/` with all missing parents, and write the JSON-LD payload to `./seo-aeo/schema/YYYYmmdd/generated-schema.json` as strict, pure JSON. Replace `YYYYmmdd` with the actual run date. Do not include `<script>` tags, Markdown fences, comments, trailing commas, executable expressions, or explanatory text.
- Prefer `"@context": "https://schema.org"` and a compact `@graph` when multiple connected top-level entities are needed.
- Preserve Unicode normally. Escape only as JSON requires.
- Keep values aligned with visible content and existing canonical sitewide entities.
- Avoid emitting a second competing block when an existing CMS/plugin block should be corrected instead; recommend the safest integration point.
- Show the implementation wrapper in `schema-report.md` when useful: place the exact contents of `generated-schema.json` inside `<script type="application/ld+json">...</script>` without changing the JSON.

## 7. Validate before presenting

1. Parse the exact saved `./seo-aeo/schema/YYYYmmdd/generated-schema.json` file as strict JSON and check duplicate keys/placeholders.
2. Validate every type, property, domain, range, enumeration, and term status against the current stable Schema.org vocabulary.
3. Validate required and recommended properties plus content rules against the current feature-specific Google guide.
4. Run the Schema.org Markup Validator and, for supported features, the Google Rich Results Test when tools/access allow.
5. Recompare every emitted value with visible content and supplied facts.

Only say **validated** with scope, for example: “JSON syntax and stable Schema.org terms validated; Google Rich Results Test pending because the page is not deployed.” Do not use an unqualified “fully valid.”

## Artifact contents

Write `./seo-aeo/schema/YYYYmmdd/schema-report.md` with:

- **Page type:** classification, evidence, confidence.
- **Recommended graph:** primary/supporting types and why they apply.
- **Missing information:** facts required to finish or strengthen the graph.
- **Generated file status:** what `generated-schema.json` contains and whether it is deployable, a placeholder draft, or intentionally empty.
- **Validation result:** passes, errors, warnings, placeholder status, Google feature eligibility, and tests not run.
- **Implementation:** where/how to add or replace markup, duplication risks, and post-deployment retest steps.

Write the schema itself only to the `generated-schema.json` file in the same dated directory. For audits plus generation, precede the generation sections in the report with missing opportunities and prioritized fixes from the validation procedure. If directory creation or writing fails, do not use a fallback destination; report the intended dated path and error. Return clickable links to both files at their final dated paths.
