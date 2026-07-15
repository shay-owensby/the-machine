# Workforce Planning Framework

A reusable method for forecasting the workforce a business plan requires and building the plan to close the gap. This is a **framework, not a data set** — every number below is a clearly-marked *example*. Real forecasts come from the client's real business plan, real headcount, and real historical rates. Fill every `<placeholder>`; delete guidance in _italics_.

> ⚠️ **Never invent workforce numbers.** Demand figures come from the supplied business plan; supply and loss figures from real headcount and the client's own historical attrition/retirement/mobility rates. If an input is missing, mark it a placeholder and ask — do **not** guess. Any **reduction** scenario is a structural draft only: notice periods, selection fairness, consultation, and severance are jurisdiction- and headcount-specific — scope to `legal.jurisdictions`, flag for counsel, and (when `legal.counsel_review: true`) stamp "⚠️ Draft — requires review by qualified HR/legal counsel before use". Aggregate; suppress small groups that could re-identify people.

## Step 1 — Anchor to the business plan (demand drivers)

Before forecasting a single role, list the business plan elements that create workforce demand and the driver that connects each to headcount. No driver, no defensible number.

| Business driver _(from the plan)_ | Time horizon | Workforce implication | Driver metric _(basis)_ |
|---|---|---|---|
| `Enter new region` | `Q3` | `New site team` | `Site staffing model × 1 site` |
| `Revenue +25%` | `12 mo` | `More delivery capacity` | `Revenue ÷ revenue-per-head` |
| `Launch product line` | `9 mo` | `New skill sets` | `Roadmap → role map` |

_Example rows — replace with the client's real plan._ Horizon is usually 12 months for an operating plan; run a longer horizon (2–3 yrs) for strategic roles with long lead times.

## Step 2 — Forecast demand

For each role/skill, state the **target** headcount the plan requires and *when*. Build the target from the driver in Step 1, not a round number.

| Role / skill | Level | Current | Target (end of horizon) | Driver / rationale |
|---|---|---|---|---|
| `Delivery specialist` | `L3` | `8` | `11` *(example)* | `Revenue-per-head model` |
| `Regional manager` | `M4` | `2` | `3` *(example)* | `New site` |

**Figures are placeholders showing the table shape — do not treat as real targets.**

## Step 3 — Inventory current supply and expected losses

Baseline from real data, then subtract expected losses over the horizon. Use the client's **own historical rates** — never a generic industry number presented as theirs.

- **Current supply** = actual headcount by role/level/location/employment type (from HRIS export or supplied roster).
- **Expected losses** = expected exits over the horizon: voluntary attrition (apply the client's historical voluntary-turnover rate), known retirements, and expected internal moves out of the role.
- **Available supply** = current supply − expected losses.

| Role / skill | Current supply | Historical attrition | Expected losses | Available supply |
|---|---|---|---|---|
| `Delivery specialist` | `8` | `12%/yr` *(client's own rate)* | `1` | `7` |
| `Regional manager` | `2` | `—` | `0` | `2` |

## Step 4 — Gap analysis

For each role/skill:

**Gap = Target demand (Step 2) − Available supply (Step 3).**

- **Positive gap** = shortfall → plan to build/buy/borrow (Step 6).
- **Negative gap** = surplus → plan to redeploy, retrain, slow hiring, or (with full legal flagging) reduce.

| Role / skill | Target | Available | Gap | Read |
|---|---|---|---|---|
| `Delivery specialist` | `11` | `7` | `+4` | `Shortfall — act` |
| `Back-office clerk` | `3` | `5` | `-2` | `Surplus — redeploy/reduce (flag legal)` |

## Step 5 — Build vs. buy vs. borrow

Choose a play per positive gap. Weigh lead time, cost, how core the capability is, and internal readiness (link to the succession register in `org-design-succession.md`).

| Play | Use when | Route to |
|---|---|---|
| **Build** | Capability is core; internal candidates are near-ready; you have lead time | `training-development/` + succession plan |
| **Buy** | Skill is scarce internally; need capability faster than you can grow it | `recruitment/` |
| **Borrow** | Need is temporary, spiky, or non-core; `employment_types` allows contingent | Contingent/contractor plan |

## Step 6 — Scenario planning

Re-run the gap under at least three business outlooks so the plan survives a changed forecast. Change the demand drivers (Step 1), not the method.

| Role / skill | Growth (+) | Flat (base) | Reduction (−) |
|---|---|---|---|
| `Delivery specialist` | `+6` | `+4` | `+1` |
| `Back-office clerk` | `0` | `-2` | `-4` |

> The **reduction** column models *structure and numbers only*. Do not name individuals or model selections here. A reduction is a draft that must go to HR/counsel — jurisdiction- and headcount-specific obligations apply. See the safety banner above.

## Step 7 — Action plan

Turn the chosen scenario into owned, dated actions.

| Action | Role / skill | Play | Count | Start by | Owner | Hand-off |
|---|---|---|---|---|---|---|
| `Open reqs` | `Delivery specialist` | `Buy` | `3` | `Q2` | `<owner>` | `recruitment/` |
| `Promote + develop` | `Delivery specialist` | `Build` | `1` | `Q2` | `<owner>` | `training-development/` |

Record the **assumptions** underneath (attrition rate used, revenue-per-head, business-plan version and date). A forecast without its assumptions can't be re-checked when reality moves.

## Reminders

- Every number traces to a supplied source (business plan, headcount, the client's own historical rates); if it doesn't, it's a placeholder and a question, not a forecast.
- Reductions are structural drafts for HR/counsel — jurisdiction- and headcount-specific, flagged, never asserted as cleared.
- Aggregate; suppress small cuts that could re-identify people. Plans are drafts for leadership/HR review, not guarantees.
