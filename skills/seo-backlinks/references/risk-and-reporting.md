# Risk analysis and report contracts

## Suspicious-link evidence matrix

DataForSEO Spam Score is a proprietary 0–100 screening metric. Preserve its raw value and call it `DataForSEO Spam Score`; do not rename it “toxicity.” Use descriptive bands only for triage: 0–29 lower, 30–59 elevated, 60–79 high, and 80–100 very high. A band never determines the final classification by itself.

Review evidence across these groups:

- **Source integrity:** hacked or injected page, counterfeit identity, spun/scraped content, uncontrolled outbound linking, obvious placement marketplace, malware/deception, deindexed or inaccessible source.
- **Link pattern:** exact-commercial anchor concentration, sitewide/template repetition, coordinated first-seen bursts, reciprocal/network footprints, unrelated language/topic/geography, identical surrounding text, abnormal redirect/canonical chains.
- **Placement and attributes:** editorial context, semantic location, dofollow/nofollow/UGC/sponsored, disclosure, destination relevance, and whether the placement plausibly serves a real audience.
- **Network evidence:** repeated IP/subnet ownership, referring-network concentration, shared templates/registrants where lawfully observable, and multiple domains behaving as one source.
- **History and context:** known purchased-link work, compromised site, negative-SEO event, manual action, migration, expired-domain history, or an existing disavow file.

Assign one of these conclusions:

- **High risk:** strong direct evidence of manipulation, compromise, or a coordinated scheme, normally supported by multiple independent signals.
- **Moderate risk:** several concerning signals but plausible benign explanations remain.
- **Low apparent risk:** no meaningful evidence beyond weak vendor or domain-level signals.
- **Unresolved/manual review:** insufficient source-page evidence, conflicting signals, or provider-only observation.

For every High or Moderate item, list the specific evidence, benign alternative, confidence (`high`, `medium`, or `low`), and next verification step. Use “suspected toxic” only as a user-facing synonym for High risk, never as a proven Google penalty.

## Required report content by mode

### Full profile

- Headline totals: backlinks, referring domains/main domains, live/lost, dofollow/nofollow, DataForSEO Rank and Spam Score with provider labels.
- Referring-domain distribution: strongest domains, concentration, countries/TLDs/platforms/networks when available, and destination-page distribution.
- Anchor distribution: categories plus leading raw anchors, percentages, denominators, and overconcentration notes.
- New/lost trend and churn.
- Risk summary and manual-review queue.
- Automatically discovered competitors and a deduplicated opportunity gap.
- Prioritized actions: protect/reclaim, investigate, and earn.

### Gap

- Like-for-like target comparison.
- Referring domains linking to the competitor but not the target.
- Opportunity category, evidence, topical fit, source quality, destination fit, replicability, risk, confidence, and recommended acquisition motion.
- A short rejected/quarantined list explaining why superficially strong domains were excluded.

### Toxic

- Risk distribution by conclusion, not just Spam Score band.
- Domain- and link-level evidence table.
- Anchor, network, country/TLD, placement, and velocity patterns.
- Manual-review queue and reversible next steps.
- Separate section for removal/disavow considerations. Default conclusion is no disavow action unless exceptional evidence supports further review; never generate or submit one without explicit authorization.

### New/lost

- Date-bucket table for new/lost backlinks and referring domains.
- Net change and gross churn calculations with formulas stated.
- Highest-value new links and most consequential losses.
- Destination pages and anchor categories affected.
- Spike/anomaly notes and provider first-seen limitation.

### Verify

- Input rows, unique valid source URLs, duplicates, invalid rows, and coverage.
- Row-level status table with the original source, normalized source, observed destination, anchor, attributes, first/last seen, lost date, evidence source, and notes.
- Summary counts and unresolved items requiring direct inspection.

## Presentation and calculation rules

- Put the decision summary first and the detailed evidence afterward.
- Use counts and percentages together. A percentage without a denominator is incomplete.
- Distinguish source URLs, referring domains, and referring main domains.
- Explain whether rows are complete, paginated, or sampled and what was used to sort the sample.
- Include DataForSEO retrieval time, task status/errors, task cost if returned, and the official Backlinks API overview link.
- Use compact charts only when they improve comprehension. In Markdown, use tables or text bars; in HTML, use accessible CSS bars with numeric labels, not JavaScript.
- Include a methodology/limitations section stating that index coverage, first-seen dates, Spam Score, and Rank are provider-specific and can change.

