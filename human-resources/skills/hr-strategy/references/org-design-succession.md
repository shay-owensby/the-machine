# Organizational Design & Succession Planning

Two linked frameworks: how to structure an organization to deliver its strategy, and how to secure the pipeline behind its critical roles. Both are **methodologies, not data** — every value below is a clearly-marked *example*. Fill every `<placeholder>`; delete guidance in _italics_.

> ⚠️ Org structures and succession maps are **drafts for leadership/HR review**, not decisions. Any restructuring that changes or eliminates roles is jurisdiction- and headcount-specific (notice, selection fairness, consultation, severance) — scope to `legal.jurisdictions`, flag for counsel, and stamp "⚠️ Draft — requires review by qualified HR/legal counsel before use" when `legal.counsel_review: true`. Succession data (readiness, flight risk, performance judgments about named people) is confidential PII — keep it in `reports/employee-reports/`, never in the shareable `strategy/` folder, and populate only from supplied data.

---

# Part 1 — Organizational Design

## Principle 1 — Group the work to the strategy

Design from the outcomes the business must deliver, then group the work that produces them. Each grouping optimizes something and taxes something else — name the trade-off.

| Grouping model | Optimizes for | Taxes | Fits when |
|---|---|---|---|
| **Functional** | Deep expertise, efficiency | Cross-function speed | One product/market; scale economies matter |
| **Product / divisional** | Speed, product ownership | Duplicated functions | Multiple distinct products/lines |
| **Geographic** | Local responsiveness | Consistency across regions | Strong regional differences |
| **Customer / segment** | Segment focus | Duplication across segments | Distinct customer types |
| **Matrix** | Two priorities at once (e.g. product × region) | Dual reporting, decision friction | Genuinely need both axes; mature enough to manage it |

Pick the model whose *optimize* matches the strategy's top priority and whose *tax* the business can afford.

## Principle 2 — Spans and layers

- **Span of control** = direct reports per manager. Wider spans flatten the org, cut cost, and push autonomy down — but overload managers if the work needs heavy coordination or coaching. Narrow spans suit complex, high-judgment, or safety-critical work.
- **Layers** = management levels from top to front line. Each layer adds cost and slows decisions; too few overloads managers and starves development. Watch for **layers with a span of one** ("manager of one") — usually a redesign smell.
- Report span/layer figures as **diagnostics computed from real headcount** (see the span-of-control metric in the hr-metrics catalog), not targets pulled from the air. Weigh `company.size` and `company.remote_policy` — distributed teams often need deliberate coordination design, not just wider spans.

| Layer | Role | Reports | Avg span _(diagnostic)_ |
|---|---|---|---|
| `1` | `Owner/CEO` | `4` | `4` |
| `2` | `Function leads` | `18` | `4.5` |
| `3` | `Team managers` | `40` | `5.7` |

_Example diagnostics — compute from the client's real roster._

## Principle 3 — Role clarity and decision rights

Ambiguous decision rights, not boxes on a chart, are what usually break a redesign. For each key outcome or process, make explicit **who decides**.

| Decision / process | Responsible _(does it)_ | Accountable _(owns outcome, one)_ | Consulted | Informed |
|---|---|---|---|---|
| `<decision>` | `<role>` | `<role>` | `<roles>` | `<roles>` |

- Exactly **one** Accountable per decision. Two "owners" means no owner.
- Pair the RACI (or equivalent) with a one-line **role charter** per key role: what it owns, its top handoffs, and the decisions it holds. Consistency here is what makes the structure operate.

## Restructuring hand-off (stop at the people layer)

When a redesign implies role changes or eliminations, describe the **structure** — new grouping, spans, reporting lines, role changes — and stop. Eliminations, selections, and severance are drafts that go to HR/counsel: jurisdiction- and headcount-specific, flagged, banner-stamped, never presented as cleared. Route the legal analysis to `legal-compliance/`.

---

# Part 2 — Succession Planning

## Step 1 — Critical-role register

Flag roles whose vacancy would most damage the business — by impact, skill scarcity, and single-point-of-failure risk — not merely seniority.

| Role | Why critical | Impact if vacant | Single point of failure? |
|---|---|---|---|
| `<role>` | `Scarce skill / key relationships` | `High` | `Yes` |

## Step 2 — Incumbent risk (confidential)

For each critical role, capture vacancy risk from **supplied** data only — never inferred or invented about a named person.

| Role | Incumbent | Vacancy risk _(retire / flight / planned move)_ | Horizon |
|---|---|---|---|
| `<role>` | `<name — confidential>` | `Planned retirement` *(supplied)* | `12–18 mo` |

> Flight-risk and performance judgments about named individuals are sensitive. Keep this table in `reports/employee-reports/`, not `strategy/`.

## Step 3 — Successors and readiness

Name potential successors per critical role and rate readiness on a consistent scale.

| Readiness level | Meaning |
|---|---|
| **Ready now** | Could step in immediately |
| **Ready 1–2 yrs** | Needs targeted development / exposure |
| **Ready 3+ yrs** | High potential, early in the path |
| **Emergency cover only** | Can hold the role short-term, not a permanent successor |

| Role | Successor | Readiness | Key gap to close |
|---|---|---|---|
| `<role>` | `<name>` | `Ready 1–2 yrs` | `Broader P&L exposure` |
| `<role>` | `<name>` | `Emergency cover only` | `—` |

**A critical role with no "ready now" or "ready 1–2 yrs" successor is a workforce-planning gap** — loop it back to the build-vs-buy decision in `workforce-planning-framework.md` (Step 5).

## Step 4 — Development actions

For each successor, the specific moves to close the readiness gap. Hand execution to `training-development/`; keep the individual plan confidential.

| Successor | Development action | Type | By when | Owner |
|---|---|---|---|---|
| `<name>` | `Lead cross-region project` | `Stretch assignment` | `Q4` | `<manager>` |
| `<name>` | `Pair with incumbent` | `Mentoring` | `Ongoing` | `<incumbent>` |

## Reminders

- Structure serves strategy — pick groupings and spans for what the business must deliver, and make decision rights explicit.
- Succession data is confidential PII: supplied data only, stored in `reports/employee-reports/`.
- Restructurings are drafts for HR/counsel — jurisdiction- and headcount-specific, flagged, never asserted as cleared.
