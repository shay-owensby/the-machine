# Validation and fixtures

This skill has no automated test suite. Validation is the fixtures below, run
by hand through the offline pipeline, plus `check_config.py` against a live
property for the cases fixtures cannot reach.

```bash
python3 scripts/make_fixtures.py --list   # what each fixture pins down
python3 scripts/make_fixtures.py          # write them to assets/fixtures/
```

Nothing here touches the network.

---

## Why the pipeline is in five pieces

```
ga4_common.py   config, auth, HTTP, error classification
     ↓
fetch_ga4.py    API → raw.json                      (the only networked step)
     ↓
analyze_ga4.py  raw.json → analysis.json + CSVs + tables
     ↓
make_charts.py  analysis.json → PNGs + manifest
     ↓
the agent       analysis.json → the Markdown report
```

Each step reads a file and writes a file. That is what makes the four steps
after retrieval exercisable offline: the analytical rules can be run against a
property that has no key events, or lost four days of data, or launched last
week, without waiting for a real client property to be in that state — and
without spending quota to reproduce a bug twice.

`raw.json` is also the audit trail: what the property actually said on the day
the report was written.

---

## The fixtures

`python3 scripts/make_fixtures.py --list`

| Fixture | The case it pins down |
|---|---|
| `leadgen-healthy` | Normal lead-gen property, growth, full metric availability |
| `ecommerce-growth` | Store with revenue, item data, and a weakening checkout step |
| `no-key-events` | Key events defined, none fired — conversions unreportable |
| `zero-previous` | Comparison period genuinely all zeros |
| `low-traffic` | Volumes too small for stable rate metrics |
| `tracking-outage` | Four days with no rows and a key event that stopped firing |
| `partial-failure` | Quota errors killed two optional datasets |
| `legacy-conversions` | Property answering to `conversions`, not `keyEvents` |
| `not-set-heavy` | Large `(not set)`/`(other)` buckets plus cardinality data loss |
| `no-admin-api` | Admin API disabled: no property name, no key-event definitions |
| `unsupported-metrics` | Property schema missing several KPIs |

They are synthetic — no client data — and deliberately round, so a result can
be checked by eye. They are realistic where it matters: GA4 rates as ratios in
0–1, durations in seconds, dates as `YYYYMMDD`, `(not set)` rows, response
metadata carrying `dataLossFromOtherRow` and `emptyReason`, **absent** keys
where a property reports nothing, and absent rows for days with no data.

---

## What to check a change against

Run a fixture through the pipeline and confirm the behaviour the skill
promises still holds:

```bash
python3 scripts/analyze_ga4.py --raw assets/fixtures/leadgen-healthy_raw.json --out /tmp/ga4
python3 scripts/make_charts.py --analysis /tmp/ga4/analysis.json --out /tmp/ga4/charts
```

**Secrets** — no generated output file contains a credential; `describe_config`
renders none; `check_config` prints none in any mode. Check this on every
change that touches configuration or output.

**Analytical honesty** — unavailable never becomes zero, in JSON, tables or CSV
· a zero baseline gives an undefined percentage, never infinity or 100% · zero
key events is reported as none recorded, not as a decline · a collection gap
caveats every decline it could explain and drops it to low confidence · falling
sessions with rising outcomes is not called a decline · a 212-session property
produces no high-severity conclusions.

**Structure** — an absent dataset produces an absent section, not an empty one ·
the ecommerce section appears only with revenue · no empty `ecommerce.csv` is
written to fill the folder · `daily.csv` marks a day with no data instead of
writing zeros · legacy `conversions` normalises to key events while preserving
the property's wording.

**Recommendations** — every one traces back to a finding by ID, and carries
action, reason, evidence, expected impact, priority and confidence.

**Charts** — every manifest entry either exists on disk with alt text and an
embeddable relative path, or carries a reason it was not drawn · a property
with no key events gets no key-event chart.

**Refusals** — malformed JSON, an unknown schema and a missing file are each
refused with exit code 2.

**Retrieval logic** cannot run offline: requests chunked inside the API's shape
limits with the sort metric in every chunk, so the chunks describe the same
rows · merging never invents a zero for a row a later chunk did not return ·
the default window is 30 completed days, adjacent, never including today ·
`GA4_LAG_DAYS` moves it and says so · unequal and overlapping periods are
warned about · the property schema decides what is requested, renamed
dimensions fall back, and an unreadable schema degrades open rather than
dropping every field.

---

## Cases the fixtures cannot cover

These need a live property, and `check_config.py` is the tool for all of them:

| Case | How to verify |
|---|---|
| Valid authentication | `check_config.py` → exit 0 |
| Inaccessible property | Point `--property-id` at one not shared with the identity → exit 3 with the access hint |
| API not enabled | Disable the Data API in a scratch Cloud project → exit 3, `SERVICE_DISABLED` |
| Quota exhaustion | Run repeatedly against one property until `RESOURCE_EXHAUSTED` → exit 4, backoff visible |
| Property with no traffic | A new property → the zero-sessions warning |
| Transient failures | Exercised by the backoff path; the retry notes print to stderr |

---

## Adding a fixture

1. Add a `fx_<name>()` in `scripts/make_fixtures.py` returning `envelope(...)`.
2. Register it in the `FIXTURES` dict with a one-line description of the case
   it pins down.
3. `python3 scripts/make_fixtures.py`
4. Run it through `analyze_ga4.py` and confirm the behaviour you meant to
   protect actually holds.

Omit a metric to represent "this property does not report it". **Do not set it
to zero** — that is the exact bug the fixtures exist to catch.
