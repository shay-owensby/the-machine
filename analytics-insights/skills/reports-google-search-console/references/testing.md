# Testing and validation

Retrieval is separated from analysis so the analytical half — where the judgement
lives, and where a bug produces a confidently wrong sentence rather than a crash
— can be tested against fixed data, offline, in a second.

```bash
python3 scripts/run_tests.py            # 475 assertions, no network
python3 scripts/run_tests.py --verbose  # name every case
```

## What is covered

| Area | Cases |
|---|---|
| Credentials | Missing `agency.env`; missing individual variables; quoted and `export`-prefixed values; a GSC-specific refresh token taking precedence over the shared one |
| Client config | Missing `GSC_SITE_URL`; a bare hostname rejected with both valid forms offered; domain and URL-prefix normalisation; trailing slash; `SC-Domain:` casing; brand terms, country, report days, search types; CLI override |
| Secrets | No credential value appears in `describe_config()`; credentials render as `present`; the property identifier is safe to print |
| Auth failures | `invalid_grant` explained; `invalid_client` names the variables; `invalid_scope` explains that an Ads-only token cannot read Search Console |
| API errors | API-not-enabled 403 points at Cloud; permission 403 points at Search Console's user settings; 404 explains exact identifiers; 400 names the dimension rules |
| Pagination | Full pages are followed to the end; `startRow` advances; request count recorded; a complete extract is marked complete |
| Row caps | `max_rows` stops paging and marks the extract truncated rather than silently short |
| Empty responses | A response with no rows returns empty, not an exception, and not zeros |
| Resilience | Transient 503 retried; 401 forces one token refresh; persistent 429 raises a retryable error with an explanation |
| Freshness | The latest finalised date is discovered rather than assumed; the lag is measured; provisional days are counted and excluded; `dataState` is `final` for the report and `all` only for the probe |
| Periods | 30 days ending on the latest finalised date; comparison window adjacent, equal length, non-overlapping; `lag_days` moves both |
| Arithmetic | Percentage change from zero is undefined; `safe_div` never returns 0 for 0/0; position is impression-weighted; a row with no position is skipped, not zeroed |
| **Average position** | 12 → 8 is negative, reads "down", and is an **improvement**; 5 → 9 is a **decline** |
| Materiality | A 44% swing on nine clicks is not material and reads flat while still reporting its absolute change |
| Healthy property | Growth verdicts; CTR opportunities judged against the property's own band median; recommendations name specific pages; ranking opportunities confined to positions 4-20; brand split runs because terms are configured |
| CTR decline | The stable-position/falling-CTR finding fires; clicks falling faster than impressions is called out; attribution lands on CTR; position is not blamed; the SERP-layout caveat is attached |
| Visibility loss | Visibility losses reported separately from click losses; losses classified by kind; an indexing risk raised from URL Inspection, prioritised High, and separated from the 30-day trend |
| Zero comparison period | No percentage change; verdict `new`; current values still reported; a `no_baseline` finding that forbids calling it growth; the KPI table prints `n/a`, never a zero |
| Low traffic | No material verdict; small sample recorded; no high-severity finding asserted |
| Truncated extract | The cap surfaces as a warning and a `warn` check; a recommendation to re-run in slices; the KPIs stated as unaffected; a flat property described as flat |
| Partial retrieval | Failed datasets are unavailable rather than empty; errors carried through; core KPIs still report; no table rendered for a missing dataset; no brand split without configured terms |
| Domain property | Property type recognised; Image search kept separate and never added to web totals; sitemap problems surfaced; a real spike detected while ordinary weekend dips are not |
| Invariants (every fixture) | No NaN or Infinity; both periods stated; no percentage from a zero baseline; unavailable KPIs never printed as numbers; every finding carries evidence, severity and confidence; every recommendation carries all its fields and cites a finding; no vague advice; standing limitations present; clicks never equated with sessions; thresholds published; the CTR benchmark disclaims industry data |
| Reconciliation | Query clicks below property clicks; coverage expressed as a percentage; the gap explained as withheld rows |
| **End-to-end retrieval** | `fetch_search_console.py` driven against a scripted API: the property check, the freshness probe, period arithmetic, every dataset query, the dated output folder, the filename, a failed optional dataset exiting 1 with its reason recorded, search appearance queried alone, every reporting query using `dataState=final`, and no credential reaching the raw file |
| Wrong property | A property the identity cannot read exits 3, makes **no data query at all**, and writes nothing |
| Charts | Eight or more draw for a complete property; files exist; each has title, alt and an explanation; the manifest writes back; an undrawable chart is skipped **with a printable reason** |

## The fixtures

`assets/fixtures/*_raw.json`, generated by `scripts/make_fixtures.py`:

| Fixture | The awkward case |
|---|---|
| `healthy` | Growth across the board, every dataset present, brand terms configured |
| `ctr-decline` | Rankings and impressions held; CTR and clicks fell — the case most often blamed on rankings |
| `visibility-loss` | Pages lost impressions; one is no longer indexed; one sharp single-day drop |
| `zero-previous` | Newly verified property; the comparison period has no rows at all |
| `low-traffic` | Small local property where a 46% swing is six clicks |
| `truncated` | Large property whose query extract hit the row cap |
| `partial` | Search appearance and countries failed to retrieve |
| `domain-property` | Domain property with Image search as a separate dataset, plus sitemap problems |

They are API-shaped: fractional CTR, 1-based position, dimension keys, and
**absent rows** where a period has no data. That last detail is what makes them
worth having — the unavailable-versus-zero rule is only testable against data
that actually omits things.

Numbers are deterministic (fixed seeds) so assertions can be exact. Regenerate
after changing the generator:

```bash
python3 scripts/make_fixtures.py
python3 scripts/make_fixtures.py --list
```

## Testing against a real property without writing a report

```bash
python3 scripts/check_config.py --project-root ~/clients/<client>        # access
python3 scripts/fetch_search_console.py --project-root ~/clients/<client> \
  --out /tmp/gsc-test --flat --days 7 --skip query_page,countries        # small, cheap
python3 scripts/analyze_search_performance.py --raw /tmp/gsc-test/*_raw.json
```

A seven-day window with the optional datasets skipped is a handful of calls. Keep
the raw file: it becomes a fixture for any bug you find, once the property and
URLs are replaced with placeholders.

## Adding a case

1. Add an `fx_*` function to `make_fixtures.py` returning `envelope(...)` with
   the datasets that matter. Omit what the case is about — omission is the
   scenario.
2. Register it in `FIXTURES` with a one-line description.
3. Add a `test_*` in `run_tests.py` asserting on the **analysis output**, not on
   internals: what the KPI table says, which findings fired, what `data_quality`
   warns about.
4. `python3 make_fixtures.py && python3 run_tests.py`.

## Checking the tests actually bite

A suite that passes against broken code is worse than no suite. Mutate something
and confirm failures:

```bash
cp scripts/gsc_common.py /tmp/backup.py
# make percent_change() return 100.0 instead of None against a zero baseline
python3 scripts/run_tests.py     # expect: 8 failures naming the zero-baseline rule
cp /tmp/backup.py scripts/gsc_common.py

cp scripts/analyze_search_performance.py /tmp/backup2.py
# invert the better_when == "lower" branch in change_record()
python3 scripts/run_tests.py     # expect: 3 failures naming average position
cp /tmp/backup2.py scripts/analyze_search_performance.py
```

Both mutations are the errors that would otherwise reach a client as a confident
sentence. Worth repeating after any substantial change to the analysis engine.

## Before a client report goes out

- [ ] `check_config.py` returns 0 and the **property is the client's**, including
      the right protocol, subdomain and property type
- [ ] Both date ranges and the latest finalised date appear in the report header
- [ ] Every figure in the report exists in `analysis.json` (spot-check three)
- [ ] Every `data_quality.warnings` entry is reflected in the report
- [ ] No metric marked `unavailable` appears as a number or a zero
- [ ] No percentage change is quoted against a zero baseline
- [ ] Average position improvements are described as improvements
- [ ] Query-level totals are not presented as the property's total traffic
- [ ] Every recommendation names a query or page and cites a figure
- [ ] CTR recommendations do not promise ranking improvements
- [ ] Charts referenced in the report exist on disk; skipped charts are not described
- [ ] No branded/non-branded claim without configured brand terms
- [ ] Nothing in the report or logs contains a credential value
