# Grant Fit Score — 0–100 Scoring Rubric

This rubric turns a fuzzy question — *"is this grant worth applying for?"* — into a single, auditable number. The score blends two things a decision-maker actually cares about:

- **Fit** — should the org *want* this money? (alignment, use, amount)
- **Likelihood** — can the org *realistically win* it? (eligibility, competitiveness)

The point isn't false precision. It's a consistent, transparent yardstick so twenty grants can be ranked against each other and a human can see *why* each landed where it did — and overrule you when they know something about a funder that a web page doesn't say. Always show your sub-scores and reasoning; a number with no justification is useless.

## Step 0 — Eligibility gate (do this before scoring anything)

Before you award a single point, decide whether the organization is actually **eligible**. Check the funder's stated requirements against `ORGANIZATION.md`:

- Organization type & tax status (501(c)(3), fiscal-sponsored, government body, school, tribal, for-profit, individual)
- Geography (does the org's location fall inside the funder's service area?)
- Field / sector / eligible use
- Organization age, budget size ceilings/floors, staffing minimums
- Any hard requirements: audited financials, matching funds, prior 990s, specific accreditations

Three outcomes:

| Gate result | What to do |
|---|---|
| **Clearly ineligible** | Mark **DISQUALIFIED**. Total score ≤ 15. Record the one disqualifying reason. Keep it out of the pursue list, but still list it in the report appendix so the user sees it was considered and why it was dropped. |
| **Eligibility unclear / unverifiable** | Proceed to scoring, but flag "⚠ verify eligibility" and cap **Eligibility Fit** at 10/20. Never assume eligibility to inflate a score. |
| **Clearly eligible** | Proceed to full scoring below. |

A common trap: a grant that aligns *beautifully* with the mission but the org can't legally receive (wrong tax status, wrong state, individuals-only). Alignment never rescues ineligibility — the gate comes first for a reason.

## The five dimensions (sum to 100)

Score each dimension independently, then add them. For each, pick the band that best matches the evidence and record a one-line justification.

### 1. Mission & Program Alignment — 30 points

How closely the funder's stated priorities, funding areas, and target populations match this org's mission (`MISSION-STATEMENT.md`) and current goals/projects (`GOALS.md`). This is the heaviest dimension because a funder who explicitly funds your exact work is the single strongest signal.

- **26–30 — Bullseye.** The funder explicitly funds this exact field, population, and geography. The org's work reads like the RFP's example projects.
- **18–25 — Strong.** Clearly within the funder's core priorities; a natural, easy narrative.
- **10–17 — Partial / adjacent.** Plausible overlap, but not a stated priority; the proposal would have to argue the connection.
- **1–9 — Tangential.** You'd have to stretch or reframe the org's work to fit. Usually a sign to skip.

### 2. Eligibility Fit — 20 points

Given the org passed the gate, *how cleanly and completely* does it meet every criterion — comfortably, or by squeaking past one borderline requirement?

- **17–20 — Meets every criterion comfortably**, no caveats.
- **11–16 — Meets all criteria, but one is borderline** (budget just under a cap, geography just inside the line, org age near a minimum).
- **5–10 — Meets on paper with a workaround** required (needs a fiscal sponsor, a partner org, a governance change). Also the ceiling when eligibility is unverifiable.
- **0–4 — Barely / uncertain.** If it's this low, re-check whether it should have been gated out.

### 3. Award Likelihood / Competitiveness — 20 points

The realistic probability of *winning* if the org applies. Weigh whatever the source reveals:

- Number and size of awards vs. the estimated applicant pool
- Geographic or sector restriction (a narrower eligible pool = better odds)
- Open call vs. **invitation-only** (invitation-only without a relationship = longshot)
- Signals the funder favors prior grantees, members, or existing relationships
- Published acceptance rates, if any
- First-time vs. renewal cycle; whether the org has funder history

Scoring:

- **17–20 — Odds in the org's favor.** Restricted local pool, many awards, or a warm relationship signal.
- **11–16 — Competitive but realistic.** A normal, winnable open call.
- **5–10 — Highly competitive.** National open call, low base rate, no edge.
- **0–4 — Longshot.** Prestige national award or invitation-only with no relationship.

When the applicant pool or acceptance rate is genuinely unknowable from the source, say so and score in the 11–16 middle unless other signals (restriction, award count) justify moving it.

### 4. Funding & Award-Size Fit — 15 points

Does the amount, and *what it funds*, match a real current need in `GOALS.md`? A grant that funds the wrong thing, or is too small to matter, or demands an unaffordable match, is a weaker fit even when perfectly aligned.

- **13–15 — Squarely fits a current, stated need.** Amount is meaningful; the eligible use (operating / project / capital / equipment) maps to a GOALS.md priority; any match is affordable.
- **8–12 — Useful but partial.** Too small to move the needle, or restricted to a secondary need.
- **3–7 — Awkward.** Requires a match the org likely can't meet, or funds something off-plan.
- **0–2 — Misfit.** Funds nothing the org needs, or is so large the org isn't a credible applicant.

### 5. Readiness & Timing — 15 points

Can the org actually submit a *competitive* application before the deadline? Weigh days remaining against the lift:

- Days until deadline (from the active-only filter)
- Application format — LOI/EOI vs. full proposal
- Required attachments the org may not have ready (audited financials, 990s, board list, logic model, letters of support)
- Rolling/recurring deadlines relieve time pressure

Scoring:

- **13–15 — Comfortable runway** and a light-to-moderate lift, **or** a rolling deadline.
- **8–12 — Doable but tight**, or a moderately heavy lift for the time available.
- **3–7 — Very tight** deadline or a heavy documentation lift relative to runway.
- **0–2 — Effectively impossible** to submit competitively in time. (Still list it if the deadline is in the future — just flag the crunch. For an *anticipated next cycle* with projected dates, cap this dimension at 8 since timing is unconfirmed.)

## Total → recommendation band

Sum the five dimensions for a 0–100 total, then map to a recommendation:

| Score | Band | Recommendation |
|---|---|---|
| **80–100** | Strong fit | **Pursue.** Prioritize — strong alignment and realistic odds. |
| **60–79** | Good fit | **Pursue if capacity.** Worth applying; note the weakest dimension. |
| **40–59** | Marginal | **Consider / watchlist.** Only if strategic or options are thin; or monitor for a better cycle. |
| **20–39** | Weak | **Skip** unless something changes. |
| **0–19** | Disqualified / poor | **Skip.** Ineligible or fundamentally misaligned. |

## Worked examples

**Example A — Local arts foundation, project grant.**
A community foundation in the org's own county funds youth arts education (the org's exact field), 501(c)(3) required (the org qualifies), awards ~15 grants of $5k–$15k a year, LOI due in 6 weeks, no match required.
- Mission & Program Alignment: **28** (bullseye — exact field + local)
- Eligibility Fit: **19** (clean 501(c)(3), in-county)
- Award Likelihood: **17** (local pool, many awards)
- Funding & Award-Size Fit: **13** ($10k fits a stated program need)
- Readiness & Timing: **14** (LOI, 6 weeks, no match)
- **Total: 91 → Pursue.**

**Example B — National innovation prize, invitation-adjacent.**
Prestigious $250k national award, open call, thousands of applicants, funds "bold ideas" loosely related to the org's work, full proposal + audited financials, due in 3 weeks.
- Mission & Program Alignment: **14** (adjacent, would need reframing)
- Eligibility Fit: **17** (eligible, but org is small for the field)
- Award Likelihood: **4** (national, thousands of applicants, no edge)
- Funding & Award-Size Fit: **5** ($250k is larger than the org can credibly absorb/report on)
- Readiness & Timing: **4** (heavy lift, 3 weeks)
- **Total: 44 → Consider / watchlist** (realistically, skip this cycle).

**Example C — Perfectly aligned but ineligible.**
A corporate foundation funds exactly the org's cause — but only supports organizations headquartered in a state the org isn't in.
- **Eligibility gate: DISQUALIFIED.** Total **10**, reason: "Funder restricts to [State]; org is in [Other State]." Listed in the report appendix, kept off the pursue list. Alignment is irrelevant here — the gate governs.

## Honesty checklist before you commit a score

- Did eligibility come *first*, and did a genuine disqualifier cap the score regardless of alignment?
- Is each sub-score backed by something on the **verified primary source**, not a search snippet?
- Where a factor was unknowable, did you say so and score conservatively rather than guess high?
- Would the one-line justifications let a human quickly agree or overrule each sub-score?
