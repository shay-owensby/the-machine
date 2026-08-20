# Testing and validation

```bash
python3 tests/run_tests.py            # everything, offline, no credentials
python3 tests/run_tests.py --list     # what it checks
python3 tests/run_tests.py -k baseline
python3 tests/run_tests.py --keep     # keep the temp directory to inspect
```

Nothing in the suite touches the network. Configuration cases build throwaway
`.env` files in a temp directory; analytical cases run against
`assets/fixtures/`.

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
after retrieval testable offline: the analytical rules can be exercised against
a property that has no key events, or lost four days of data, or launched last
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

They are synthetic — no client data — and deliberately round, so a test can
assert on them. They are realistic where it matters: GA4 rates as ratios in
0–1, durations in seconds, dates as `YYYYMMDD`, `(not set)` rows, response
metadata carrying `dataLossFromOtherRow` and `emptyReason`, **absent** keys
where a property reports nothing, and absent rows for days with no data.

---

## What the suite covers

**Retrieval logic** (everything around the API call, which cannot run offline)
requests chunked inside the API's shape limits with the sort metric in every
chunk, so the chunks describe the same rows · merging never invents a zero for
a row a later chunk did not return · the default window is 30 completed days,
adjacent, never including today · `GA4_LAG_DAYS` moves it and says so ·
unequal and overlapping periods are warned about · the property schema decides
what is requested, renamed dimensions fall back, and an unreadable schema
degrades open rather than dropping every field.

**Configuration and credentials**
missing `agency.env` · a missing credential named individually · missing
property ID pointing at the client `.env` · measurement ID, UA ID, GTM ID and
junk each diagnosed separately · property IDs accepted in every shape people
paste them · a full configuration resolving cleanly.

**Secrets**
`describe_config` renders no credential value · `check_config` prints none in
any mode · no generated output file contains one. This runs on every pass.

**Analytical honesty**
unavailable never becomes zero, in JSON, tables or CSV · a zero baseline gives
an undefined percentage, never infinity or 100% · zero key events is reported as
none recorded, not as a decline · a collection gap caveats every decline it
could explain and drops it to low confidence · falling sessions with rising
outcomes is not called a decline · a 212-session property produces no
high-severity conclusions.

**Structure**
an absent dataset produces an absent section, not an empty one · the ecommerce
section appears only with revenue · no empty `ecommerce.csv` is written to fill
the folder · `daily.csv` marks a day with no data instead of writing zeros ·
legacy `conversions` normalises to key events while preserving the property's
wording.

**Recommendations**
every one traces back to a finding by ID, and carries action, reason, evidence,
expected impact, priority and confidence.

**Charts**
every manifest entry either exists on disk with alt text and an embeddable
relative path, or carries a reason it was not drawn · a property with no key
events gets no key-event chart.

**End to end**
`analyze_ga4.py` runs as a subprocess against every fixture · malformed JSON, an
unknown schema and a missing file are each refused with exit code 2.

---

## Cases the suite cannot cover offline

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
4. Add a test in `tests/run_tests.py` asserting the behaviour you want
   protected — a fixture with no test protects nothing.
5. `python3 tests/run_tests.py`

Omit a metric to represent "this property does not report it". **Do not set it
to zero** — that is the exact bug the fixtures exist to catch.
