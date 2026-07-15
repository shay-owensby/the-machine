# Grant Research Report — output template

Write the report to `grants/reports/research/YYYY-MM-DD-grant-research.md` (create the directory if needed). Use this exact structure. Order grants by score, highest first. Every scored grant must carry a verified official source URL and a full sub-score breakdown, so a human can audit and overrule any number.

Keep prose tight — this is a decision tool, not an essay. If a field is genuinely unknown after verification, write "Not stated on source" rather than guessing.

```markdown
# Grant Research — {Organization Name}
**Prepared:** {YYYY-MM-DD} · **As of / dates verified:** {YYYY-MM-DD}
**Profile searched:** {field} · {geography} · {org type/tax status} · needs: {short summary}

## Summary
{1–2 sentences: how many opportunities were searched, verified, and included; how many
disqualified/excluded; the headline — e.g. "3 strong-fit grants, 2 worth watching."}

| # | Grant | Funder | Amount | Deadline (days left) | Score | Recommendation |
|---|-------|--------|--------|----------------------|-------|----------------|
| 1 | {program} | {funder} | {$ range} | {YYYY-MM-DD} ({N}d) | **{0–100}** | {Pursue / Pursue if capacity / Consider / Watchlist} |
| 2 | … | | | | | |

---

## 1. {Grant / Program name} — Score {0–100} · {Recommendation}
- **Funder:** {name} ({funder type: federal / state / community foundation / corporate / …})
- **Award:** {amount or range} · {grant type: operating / project / capital / equipment / seed}
- **Deadline:** {YYYY-MM-DD} — **{N} days left** {or: Rolling / Anticipated next cycle: {window}}
- **Eligibility:** {one-line snapshot of who qualifies} → **{org meets it / borderline: … / needs: …}**
- **Eligible use:** {what the money may fund}
- **Source:** {official URL you fetched} (verified {YYYY-MM-DD})

**Score breakdown**
| Dimension | Score | Why |
|---|---|---|
| Mission & Program Alignment | {n}/30 | {one line} |
| Eligibility Fit | {n}/20 | {one line} |
| Award Likelihood / Competitiveness | {n}/20 | {one line} |
| Funding & Award-Size Fit | {n}/15 | {one line} |
| Readiness & Timing | {n}/15 | {one line} |
| **Total** | **{n}/100** | |

**Recommendation:** {1–2 sentences — pursue/skip and the single most important reason. Note the
weakest dimension and any prerequisite, e.g. "needs audited financials" or "LOI first."}

---

## 2. {next grant, same structure} …

---

## Considered but excluded
Grants surfaced during research and deliberately left off the pursue list — so the reasoning is visible.

| Grant | Funder | Why excluded |
|-------|--------|-------------|
| {program} | {funder} | Disqualified — {e.g. funder restricts to [State]; org is elsewhere} |
| {program} | {funder} | Expired — deadline {date} already passed |
| {program} | {funder} | Score {n} — {weak-fit reason} |

## Notes & caveats
- {Anything the user should verify themselves — e.g. an unconfirmed applicant pool, a paywalled
  detail, an anticipated deadline, or a funder the org may have prior context on.}
- {If research tools were degraded or a context file was thin, say so and how it limited scoring.}
```

## Rules for filling it in

- **Rank by total score, descending.** Ties broken by deadline urgency (sooner first) then alignment.
- **Never include an expired grant in the main list.** Expired grants only appear in "Considered but excluded" with the passed date shown, and only if they were surfaced and worth noting (e.g. a recurring grant to watch next cycle).
- **Disqualified grants** live in "Considered but excluded," never in the ranked list, with the one disqualifying reason.
- Every scored grant's five sub-scores must sum to the stated total — do the arithmetic.
- Keep the "Why" cells to one line each; they exist so a human can agree or overrule at a glance.
