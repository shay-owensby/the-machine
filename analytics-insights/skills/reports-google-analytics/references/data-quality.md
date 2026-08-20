# Data quality checks

Run before any conclusion is drawn. Each returns `pass`, `info`, `warn` or
`fail`, with a detail line written for a human. They land in
`data_quality.checks`, and anything material also becomes a warning in
`data_quality.warnings` and a `risk` finding.

`info` is not a problem — it is a fact worth stating, such as a property that
sells nothing having no ecommerce data.

| Check | Fails when | Why it changes the report |
|---|---|---|
| **Comparable periods** | The two windows are different lengths | Totals are not comparable and percentages mislead |
| **Comparison period has data** | The previous period recorded nothing | Every percentage is undefined; the report is a first baseline |
| **Enough traffic to draw conclusions** | Under 1,000 sessions in the period | Rate metrics and segment splits are volatile; prefer absolute numbers |
| **Key events retrievable** | No key-event metric in the schema | Conversion performance cannot be reported at all |
| **Key events recorded** | Zero in both periods | The report says none were recorded — never that conversions fell |
| **Key event definitions readable** | The Admin API did not answer, or none are configured | Which events count as key events is unknown, so their meaning cannot be stated |
| **Unattributed rows** | `(not set)` / `(other)` ≥ 5% (fails at ≥ 20%) | Those rows cannot be acted on and they distort every split |
| **Direct traffic stability** | Direct up ≥ 30% and ≥ 100 sessions | As often lost attribution as real direct demand |
| **Engagement and bounce rate** | — | Confirms they sum to 100%, so they are one finding |
| **Continuous daily collection** | Any day returned no rows | Period totals are missing those days |
| **Ecommerce data** | State is undetermined | Decides whether the section appears at all |
| **All requested datasets retrieved** | Any API request failed | Those sections are unavailable, which is not the same as empty |
| **Property schema loaded** | The metadata call failed | Requests were not filtered against this property's real schema |

---

## Warnings that come from the API itself

Captured from `ResponseMetaData` during retrieval and carried into the
analysis:

- **`dataLossFromOtherRow`** — the breakdown exceeded GA4's cardinality limit
  and rows were folded into an aggregated `(other)` row. Row-level figures are
  incomplete and shares of total will not add up.
- **`subjectToThresholding`** — rows were withheld for privacy. Small segments
  may be missing entirely.
- **`samplingMetadatas`** — the response is sampled. Figures are estimates, not
  counts, and the report must say so.
- **`emptyReason`** — GA4's own explanation for an empty result.
- **Row caps** — a breakdown that returned as many rows as it was allowed is
  the top of the list, not the whole property. Totals must not be summed from
  it.

---

## Retrieval failures

A failed request is recorded with its dataset, message, error code, HTTP
status, hint and whether it is retryable. The dataset it fed is `None` — never
`[]`.

That distinction carries all the way through: `None` means *we do not know*,
and the section is omitted from the report with a line saying why. `[]` would
mean *we know there is nothing*, which is a different and much stronger claim.

---

## The rule this exists to enforce

> **Do not report a measurement failure as a business result.**

When the data is consistent with both a performance change and a tracking
change, the report says both, names the check that would separate them, and
does not pick one. That is not hedging — it is the only honest reading of the
evidence, and it is the difference between a report a client can act on and one
that sends a team to fix a problem that does not exist.
