# Pay Band Framework

A reusable methodology for building and maintaining salary bands and for running an internal pay-equity check. This is a **framework, not a data set** — every number below is a clearly-marked *example*. Real bands come from real market data you supply. Fill every `<placeholder>`; delete guidance in _italics_.

> ⚠️ **Never invent market data.** Bands must be built from a real, named source (a purchased salary survey, an aggregator you subscribe to, or benchmark figures the client supplies). If no source is available, stop and request one — do **not** populate a band with guessed or memory-recalled numbers. Pay-equity, pay-transparency, minimum-wage, and overtime rules are jurisdiction-specific: scope any such claim to `legal.jurisdictions`, name the jurisdiction, and flag it for counsel. When `legal.counsel_review: true`, stamp the finished structure with "⚠️ Draft — requires review by qualified HR/legal counsel before use".

## Step 1 — Job leveling (do this before any band)

Bands hang off levels, so level first. Define:

- **Job families** — groups of related roles (e.g. Engineering, Sales, Operations).
- **A level ladder** — consistent levels across families, often parallel IC and manager tracks (e.g. L1–L6 IC, M3–M6 manager).
- **Level descriptors** — for each level, describe scope, complexity, autonomy, and impact so two people can slot a role to the same level. Levels — not titles — are what you benchmark and check for equity.

| Level | Track | Scope / autonomy _(descriptor)_ | Typical titles |
|---|---|---|---|
| `L2` | IC | _Executes defined work with guidance_ | `<title>` |
| `L4` | IC | _Owns projects independently; ambiguity_ | `<title>` |
| `M4` | Mgr | _Leads a team; owns outcomes_ | `<title>` |

_Example rows — replace with the client's real ladder._

## Step 2 — Choose a market-data source (real, named)

Pick and **record** the source, its effective date, and the cut you're using. Bands built on stale or mismatched data are worse than no bands.

- **Source type** — purchased survey (e.g. an industry compensation survey), a subscription aggregator, or client-supplied benchmarks. Note the source name and vintage.
- **Match the cut** — role scope, geography, industry, company size/stage. A mismatched benchmark (wrong geo or size) silently biases the whole band.
- **Pick the percentile to your philosophy** — targeting the market median means anchoring the midpoint to the survey's 50th percentile; a "lead the market" posture anchors higher. The philosophy (from the skill) decides this, not the reference.
- **Age the data** if it's more than a few months old, using a stated, defensible aging assumption — and label it as an assumption.

> If the user asks for a band and supplies no source, respond: "I can't invent market numbers. Point me at a real survey or supply benchmark figures (source + effective date) and I'll build the band."

## Step 3 — Set range min / midpoint / max and range spread

The **midpoint** anchors to your chosen market percentile. Build the range around it with a **range spread** (the % width from min to max), typically wider at senior levels.

- **Midpoint** = market anchor (e.g. survey 50th percentile for that level/geo).
- **Range spread** = (Max − Min) ÷ Min. Common: ~30–40% for junior/support, ~40–50% for professional, ~50%+ for senior/leadership. _These are illustrative norms, not rules — set to your philosophy._
- From a midpoint and a spread: **Min** = Midpoint ÷ (1 + spread/2); **Max** = Min × (1 + spread).

| Level | Midpoint _(from market)_ | Spread | Min | Max |
|---|---|---|---|---|
| `L2` | `$60,000` *(example)* | 40% | `$50,000` | `$70,000` |
| `L4` | `$95,000` *(example)* | 45% | `$78,350` | `$113,600` |
| `M4` | `$140,000` *(example)* | 50% | `$112,000` | `$168,000` |

**All figures above are placeholders to show the shape of the table — do not use them as real bands.**

## Step 4 — Compa-ratio

Compa-ratio measures where a person (or an offer) sits in their band:

**Compa-ratio = actual base ÷ band midpoint.**

- **1.00** = paid exactly at midpoint (typically a fully-competent performer).
- **< 0.80–0.85** = low in band (new, developing, or a possible equity/retention flag).
- **> 1.15–1.20** = high in band (deep expertise, or a role that has outgrown its level — review).

Use compa-ratio to sanity-check offers (Step: offer modeling) and to spot outliers in an equity check. A group whose average compa-ratio is systematically lower is a signal to investigate.

## Step 5 — Band overlap

Adjacent bands normally overlap — a senior person in a lower band can out-earn a junior person in the next band up, which is fine. Track overlap so bands stay coherent:

**Overlap % = (Max of lower band − Min of upper band) ÷ (Max of lower band − Min of lower band).**

Very high overlap (bands nearly identical) means the levels aren't differentiated enough; near-zero overlap can create pay cliffs at promotion. Aim for moderate, deliberate overlap.

## Step 6 — Geographic differentials

When the company spans locations or hires remotely (`company.locations`, `company.remote_policy`), decide the geo strategy and apply it consistently:

- **Location-based** — adjust bands by market using a stated geo factor per location (e.g. a "national" band × a location index). Record the index source; don't guess it.
- **Location-agnostic** — one national band regardless of location (simpler, often costlier).

State which model the client uses and apply it uniformly. Geo factors, like base market data, must come from a real source — not invented.

## Step 7 — Internal pay-equity check

Run on **supplied** compensation data only. The goal: find pay differences for comparable work that aren't explained by legitimate, job-related factors.

1. **Group comparable roles** — same level and job family (and geo, if location-based). Compare like with like.
2. **Identify legitimate explanatory factors** — level, location, tenure, performance rating, relevant experience. Agree these with the client up front.
3. **Compare** — look at average pay and average compa-ratio across the groups being examined (e.g. by gender, race/ethnicity, or other protected characteristic **as defined by the applicable jurisdiction**). Surface gaps that remain after accounting for the legitimate factors.
4. **Flag, don't conclude.** A raw gap is a prompt to investigate, not proof of discrimination. Larger analyses warrant a proper regression run under counsel/privilege — note when the data volume calls for that.
5. **Recommend remediation** — where an unexplained gap holds up, propose adjustments and a review cadence.

> Pay-equity law — which characteristics are protected, what counts as "comparable work", disclosure and privilege rules — is **jurisdiction-specific**. Scope every claim to `legal.jurisdictions`, name the jurisdiction, flag for counsel, and consider running the analysis under legal privilege. Never present an equity finding as a settled legal conclusion.

| Comparison group | N | Avg base | Avg compa-ratio | Gap vs. reference _(after controls)_ |
|---|---|---|---|---|
| `Group A` | `12` | `$91,200` *(example)* | `0.98` | `—` |
| `Group B` | `9` | `$86,400` *(example)* | `0.92` | `-5.3% — investigate` |

**Example rows only — populate exclusively from supplied pay data.**

## Reminders

- Bands and equity findings are **drafts for HR/counsel review**, not legal advice or a compliance guarantee.
- Every number traces to a real, named source; if it doesn't, it doesn't go in the band.
- Individual pay data is confidential PII — keep it in-project; identifiable per-person records go to the confidential zone (`reports/employee-reports/`), summaries to `compensation-benefits/` and, where relevant, `reports/analytics/`.
