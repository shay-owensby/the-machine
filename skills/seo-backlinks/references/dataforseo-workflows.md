# DataForSEO Backlinks workflows

Use this reference to map each command to current Backlinks API operations exposed by the DataForSEO MCP. The official overview is <https://docs.dataforseo.com/v3/backlinks-overview/>. Verify current parameter names in the endpoint documentation when the MCP schema and this reference differ; the live tool schema and official documentation take precedence.

## Shared endpoint map

| Need | Backlinks API live operation | Official documentation |
|---|---|---|
| Profile totals and distributions | `backlinks/summary/live` | <https://docs.dataforseo.com/v3/backlinks-summary-live/> |
| Individual source links | `backlinks/backlinks/live` | <https://docs.dataforseo.com/v3/backlinks-backlinks-live/> |
| Anchor aggregation | `backlinks/anchors/live` | <https://docs.dataforseo.com/v3/backlinks-anchors-live/> |
| Referring-domain inventory | `backlinks/referring_domains/live` | <https://docs.dataforseo.com/v3/backlinks/referring_domains/live/> |
| Automatically identify comparable profiles | `backlinks/competitors/live` | <https://docs.dataforseo.com/v3/backlinks-competitors-live/> |
| Link intersection or exclusion gap | `backlinks/domain_intersection/live` | <https://docs.dataforseo.com/v3/backlinks/domain_intersection/live/> |
| New/lost trend | `backlinks/timeseries_new_lost_summary/live` | <https://docs.dataforseo.com/v3/backlinks/timeseries_new_lost_summary/live/> |
| Spam score for source domains/pages | `backlinks/bulk_spam_score/live` | <https://docs.dataforseo.com/v3/backlinks/bulk_spam_score/live/> |

DataForSEO documents these as live POST operations. A live request contains one task; the provider currently documents up to 30 simultaneous calls and 2,000 calls per minute. Do not treat those maximums as a request to spend freely. Reuse results, batch bulk spam-score targets, and stop when more data would not materially change the analysis.

## Full profile: `/seo backlinks <url>`

1. Retrieve Summary for the exact target scope, including all link attributes.
2. Retrieve Anchors, ordered by backlinks and then referring domains. Paginate enough to cover at least 90% of returned anchor backlinks when feasible; otherwise disclose the cutoff.
3. Retrieve Referring Domains ordered by referring-domain Rank/backlink contribution. Obtain the top cohort plus any domains surfaced by suspicious patterns.
4. Retrieve New & Lost Timeseries for the latest 12 complete months, grouped by month, to establish velocity and churn.
5. Retrieve Competitors. Select up to three credible topical competitors after excluding social platforms, generic hosting/CDN sites, directories, and obviously unrelated profiles. State why each was kept.
6. For each selected competitor, use Domain Intersection with the competitor as a `target` and the analyzed site as an `exclude_target` to identify referring domains that link to the competitor but not the analyzed site. Rank and deduplicate the combined gap.
7. Use Bulk Spam Score on the referring domains selected for risk triage, then apply the multi-signal method in `risk-and-reporting.md`.

If automatic competitor results are not topically credible, report that the automatic gap is inconclusive rather than manufacturing a competitor set.

## Gap: `/seo backlinks gap <url1> <url2>`

Treat `url1` as the target site and `url2` as the competitor.

- Retrieve Summary for both targets using identical scope and settings.
- Retrieve Domain Intersection with `url2` in `targets` and `url1` in `exclude_targets`. This yields domains linking to the competitor but not the target.
- Retrieve sufficient referring-domain detail for the highest-value gap domains.
- Categorize each opportunity as editorial/resource, association/partner, local/citation, directory/listing, media/PR, UGC/community, sponsorship/paid, or unclear.
- Score opportunity, not guaranteed value. Include target-page fit and a realistic acquisition motion; exclude or quarantine manipulative placements.

## Toxic triage: `/seo backlinks toxic <url>`

- Retrieve Summary and Referring Domains for the exact target.
- Retrieve individual Backlinks for suspicious domains and patterns, retaining source URL, target URL, anchor, surrounding text when available, first/last seen, lost state, attributes, semantic location, source country/IP/network, source/domain Rank, and redirect/indirect status.
- Batch source domains through Bulk Spam Score, up to the endpoint's documented limit.
- Compare recent new/lost velocity against the site's baseline using New & Lost Timeseries.
- Apply the evidence matrix in `risk-and-reporting.md`. Include benign explanations and an explicit manual-review queue.

## New/lost: `/seo backlinks new <url>`

- Use New & Lost Timeseries with a default range of the latest 90 complete days and `group_range: week`.
- Retrieve live and lost individual Backlinks whose first-seen/lost dates fall in the window when supported. Do not equate first seen by DataForSEO with the actual publication date.
- Report new/lost backlinks, new/lost referring domains, net change, gross churn, notable source domains, affected destination pages, anchor changes, and unusual spikes.
- Mark the final partial period separately if the API or chosen dates include one.

## Verify: `/seo backlinks verify <url> --links <file>`

1. Read the local file without modifying it. Accept newline text, CSV/TSV, JSON arrays/objects, or Markdown tables. Identify the source URL column by header (`source`, `source_url`, `url_from`, `backlink`, or close equivalent); ask only if multiple columns are equally plausible. Preserve original row identifiers and notes.
2. Normalize source URLs for comparison while retaining originals. Deduplicate exact normalized sources and report duplicates.
3. Query `backlinks/backlinks/live` for the target with `backlinks_status_type: live`, filtering by `url_from` in chunks compatible with the endpoint's current maximum filter count. Repeat with `backlinks_status_type: lost` for unmatched sources.
4. Classify each input row:
   - **Verified live** — DataForSEO currently reports a matching source-to-target link.
   - **Reported lost** — DataForSEO reports it in lost results.
   - **Different destination** — source is observed, but the destination differs materially from the requested target scope.
   - **Not found in provider index** — no matching observation; this is not proof the page lacks the link.
   - **Invalid/unreadable input** — source value cannot be interpreted as a URL.
5. Include observed target URL, anchor, attributes, first seen, last seen/lost date, redirect/indirect state, and notes. If direct page inspection is available, use it for high-priority unresolved rows and label that evidence separately from DataForSEO.

Do not report “verified” when only the source domain, rather than the specific source URL and destination relationship, matched.
