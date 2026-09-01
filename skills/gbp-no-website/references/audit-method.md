# Browser audit method

Use this method for every `gbp-no-website` audit. Google Maps results are ranked, personalized, dynamic, and sometimes capped, so “comprehensive” means a systematic, reproducible best-effort sweep with explicit coverage evidence—not a guarantee that Google exposed every profile in its index.

## 1. Establish scope

Normalize the request into:

- target category as supplied by the user;
- target city and two-letter state abbreviation when known;
- local audit date, time, and time zone.

The geographic default is the named city, not the wider metro. Include a storefront profile when its displayed address is in the target city. Include a service-area business with a hidden address only when its GBP identifies the target city as its location or service area. Exclude an adjacent-city listing when the profile provides no evidence that it belongs in the requested city scope.

Treat each distinct GBP location as a separate profile. Include active and temporarily closed businesses, marking temporary closure. Exclude permanently closed listings, obvious duplicates, internal departments that are not independently relevant businesses, and listings that are not reasonably within the requested category.

## 2. Build discovery queries

Start with the exact query:

`<category> in <city>, <state>`

Then use only variants that improve recall without broadening intent:

- singular/plural or common spacing variants;
- an obvious Google category-label equivalent;
- a common trade synonym when it describes the same buyer intent.

Examples include `electrician` and `electrical contractor`, but not the much broader `home services`. Record every query used. Do not add a variant when it would pull a materially different type of business.

## 3. Cover the map area

For each useful query variant:

1. Load the city-level results and scroll the result feed until Google stops adding listings or explicitly signals the end.
2. Open and record every distinct in-scope profile exposed by the feed; do not audit only the first page or top-ranked results.
3. Zoom and pan across the labeled city area using overlapping viewports. Use roughly 25–35% overlap so edge listings are not missed.
4. In each viewport, run “Search this area” (or the current equivalent), scroll its result feed to the end, and record new profiles.
5. Use a closer zoom for dense clusters or map areas where the result count appears capped. Use neighborhood-name searches as a supplemental pass when they reveal areas that the city-level feed did not cover well.
6. Revisit the city-level view after the tiled sweep and perform a validation pass.

Do not use a fixed lead quota. The audit is driven by area coverage and result saturation.

### Completion condition

Mark the audit `Complete — comprehensive best effort` only when:

- the full visible city area was covered with overlapping viewports;
- every useful query variant was scrolled through available results;
- dense/capped areas received a closer pass;
- the final validation pass produced no unreviewed in-scope profiles;
- every discovered in-scope profile was verified or explicitly logged as unresolved; and
- no access control or technical failure left a material portion of the scope unaudited.

Otherwise mark it `Partial` and state exactly what was completed, what remains, and why. If Google displays a result cap, say so even when all displayed results were reviewed.

## 4. Deduplicate profiles

Prefer stable identifiers in this order:

1. Google Maps place URL, place ID, or CID;
2. exact phone number plus normalized business name;
3. normalized business name plus full displayed address;
4. normalized business name plus displayed service area when the address is hidden.

Strip ordinary tracking parameters from stored Maps links when possible. Record alternate names as notes. Do not merge separate locations merely because they share a brand or phone system.

## 5. Verify website status

Open each distinct profile's detail view. Inspect the primary actions and business-information sections, scrolling or expanding details as needed.

Classify each profile as one of:

- `No website on GBP` — no primary Website action or Website field is present;
- `Website attached` — a primary Website action or field is present, regardless of destination quality;
- `Unresolved` — the profile could not be opened or the detail view could not be reliably inspected;
- `Out of scope` — wrong geography, category, closure status, or duplicate.

Only `No website on GBP` belongs in the opportunities table. Do not use a missing website button on the result card as proof. Do not click the Website action: its presence is sufficient for classification.

Capture these fields when Google displays them:

- business name;
- primary category;
- street address or displayed service area;
- phone number;
- rating and review count;
- Google Maps profile URL;
- closure status;
- the discovery query or map area;
- a concise verification note, normally `No Website action shown in GBP detail view`.

Use `Not displayed` rather than guessing missing values.

## 6. Maintain an audit ledger

Maintain a deduplicated ledger while browsing. At minimum, track:

| Field | Purpose |
|---|---|
| Profile key | Deduplication identifier |
| Business name | Human-readable identity |
| Address/service area | Geographic scope check |
| Maps URL | Recheckable source |
| Discovery query/area | Coverage evidence |
| Website classification | Qualification decision |
| Notes | Closure, ambiguity, or exception |

Counts in the final report must reconcile with this ledger:

`unique in-scope profiles audited = no website + website attached + unresolved`

Report out-of-scope records and duplicates separately; do not include them in the unique in-scope total.

If the browser session is interrupted, retain enough ledger detail to resume without starting over.

## 7. Write the Markdown report

Use this structure inside the dated file. When the file contains multiple audits, keep one top-level dated title and add each audit as a separate second-level section.

```markdown
# Website Opportunities — YYYY-MM-DD

## <Category> — <City, ST>

**Status:** Complete — comprehensive best effort | Partial  
**Audited:** YYYY-MM-DD HH:MM <time zone>  
**Source:** Google Maps browser audit

### Summary

| Metric | Count |
|---|---:|
| Discovery records inspected | 0 |
| Unique in-scope profiles audited | 0 |
| No website on GBP | 0 |
| Website attached | 0 |
| Unresolved | 0 |
| Out of scope | 0 |
| Duplicates collapsed | 0 |

### Website opportunities

| Business | Category | Address / service area | Phone | Rating | Reviews | Google Maps | Verification |
|---|---|---|---|---:|---:|---|---|
| Example Co. | Plumber | Example address | (555) 555-5555 | 4.8 | 42 | [Open GBP](https://maps.google.com/...) | No Website action shown in GBP detail view |

### Coverage

| Query or map area | Available results reviewed | New unique profiles | Notes |
|---|---:|---:|---|

### Unresolved profiles

List profiles that could not be verified, or write `None`.

### Scope and limitations

Describe city-boundary treatment, query variants, map tiling, result caps, access interruptions, and the fact that Google Maps results can change. State whether the completion condition was met.
```

If no profiles qualify, keep the opportunities heading and write `No qualifying profiles were found in the audited Google Maps results.` Do not omit the summary or coverage evidence.

Link directly to each Google Maps profile. Escape pipe characters in table cells. Avoid claiming that a business has no website anywhere; say only that no website was attached to its GBP at the recorded audit time.
