# Employee-Relations Documentation Templates

ER documentation is evidence. If it isn't written down it didn't happen — and if it's written badly (opinion, characterization, undated, inconsistent) it becomes a liability. Every ER record follows the same discipline:

- **Factual and behavior-based** — what was said, done, observed; specifics, quotes, dates, places. Not "he was hostile / has a bad attitude" but "on 3 June at 2pm he said, in front of two colleagues, '…'".
- **Objective and neutral** — no conclusions of law, no character judgments, no assumptions about motive.
- **Dated and attributed** — every entry dated, author named, contemporaneous where possible.
- **Consistent** — like situations documented and handled the same way.
- **Confidential** — stored in-project under `employee-relations/`, need-to-know only; never in a shareable area or external service. When `legal.counsel_review: true`, formal outputs (findings, discipline) carry the counsel-review banner.
- **Never invented** — use only supplied/placeholder facts; never fabricate a person, event, quote, or date.

> Legal characterizations ("this was harassment/discrimination/retaliation") are for counsel, not these records — document the facts and whether they violate **policy**, and flag the legal question. Retention periods are jurisdiction-specific — verify with counsel.

---

## Template A — Case / concern intake record

```
CONFIDENTIAL — EMPLOYEE RELATIONS
Case intake record

Case ID:               <slug/number>            Date opened:  <YYYY-MM-DD>
Recorded by:           <name / role>
Intake method:         <direct / manager / hotline / other>

Reporting party:       <name or ref>            Role/dept:    <...>
Party(ies) involved:   <name(s) or ref>         Role/dept:    <...>

Concern category:      <interpersonal / harassment* / discrimination* / retaliation* /
                        safety-violence* / wage-hour* / policy violation / performance /
                        protected-activity* / union/CBA* / other>
                        (* = legally loaded — flag for counsel; scope to legal.jurisdictions)

What is alleged (factual, specific — what/when/where/who was present):
  <chronological account in the reporter's terms; quote where possible>

Witnesses named:       <names/refs>
Evidence referenced:   <documents, messages, records — location, not pasted PII>
What the reporter is seeking: <...>
Confidentiality noted to reporter: <yes — explained need-to-know limits>
Immediate risk / interim measures: <safety, ongoing harm, retaliation risk; any neutral
                        interim steps taken>
Anti-retaliation reminder given: <yes>

Triage decision:       <conflict resolution / grievance / formal investigation / refer to counsel>
Counsel flagged:       <yes/no — why>            Assigned to: <...>
Next step & owner:     <...>                       Target date: <...>
```

## Template B — Investigation summary memo

Stamp with the counsel-review banner when `legal.counsel_review: true`. This memo reports facts and findings on a reasonable-basis standard as a **recommendation for HR/counsel** — not a legal ruling.

```
CONFIDENTIAL — EMPLOYEE RELATIONS — PREPARED IN SUPPORT OF HR/COUNSEL REVIEW
⚠️ Draft — requires review by qualified HR/legal counsel before use.   [if counsel_review]
Investigation summary memo

Case ID: <...>                    Prepared by: <name/role>     Date: <YYYY-MM-DD>
Investigator: <name/role>        Period of investigation: <start>–<end>

1. Allegation(s) & scope
   <the specific allegations examined; policies potentially implicated; questions to answer>

2. Process
   <who was interviewed and when (complainant, respondent, witnesses); documents/evidence
    reviewed; confidentiality and anti-retaliation reminders given>

3. Facts established
   <factual, behavior-based account; what is corroborated vs. disputed; distinguish
    firsthand observation from hearsay; dates/quotes>

4. Credibility assessment (where accounts conflict)
   <factors applied — plausibility, consistency, corroboration, motive/bias, demeanor,
    record — and the reasoning, per allegation>

5. Findings (per allegation — reasonable-basis / more-likely-than-not standard)
   Allegation 1: <substantiated / not substantiated / inconclusive> — <facts + reasoning;
                 which policy is/ isn't violated>
   Allegation 2: <...>
   (State these as recommendations for the client to adopt/revise, not as legal conclusions.
    Legal characterization is flagged for counsel, not asserted here.)

6. Legal / labor flags
   <harassment / discrimination / retaliation / protected-activity / safety / (if union) CBA
    implications — scoped to legal.jurisdictions, routed to counsel>

7. Recommended options & next steps
   <proportionate options for the client to decide; closure communications; retaliation
    monitoring plan; retention note (jurisdiction-specific — verify)>
```

## Template C — Disciplinary-action / coaching memo

Use for a coaching conversation, verbal-warning record, written warning, or final warning. Stamp with the counsel-review banner when `legal.counsel_review: true`. Keep it factual — it may be read later by the employee, HR, counsel, or a tribunal.

```
CONFIDENTIAL — EMPLOYEE RELATIONS
⚠️ Draft — requires review by qualified HR/legal counsel before use.   [if counsel_review]

Type: <coaching note / verbal warning (documented) / written warning / final warning>
Employee: <name or ref>          Role/dept: <...>          Date: <YYYY-MM-DD>
Issued by: <manager/HR name & role>

1. Issue (factual, behavior-based)
   <what happened — specific behavior, dates, facts; quote where relevant. Not character.>

2. Policy / expectation involved
   <the specific policy or clearly-communicated expectation at issue>

3. Prior related discussions (for consistency & progression)
   <dates and nature of any earlier coaching/warnings on this issue>

4. Impact
   <the concrete effect on work, team, safety, customers — factual>

5. Expected change & support
   <the specific behavior required going forward; any support/training offered; timeframe>

6. Consequence of no improvement
   <the next step if the issue continues — proportionate and consistent with policy>

7. Employee response
   <space for the employee's comments/acknowledgment>

Acknowledged (receipt, not necessarily agreement): __________  Date: ______
Manager/HR: __________  Date: ______

(Note: at-will vs. just-cause, notice, final-pay, and protected-activity constraints are
 jurisdiction-specific — scope to legal.jurisdictions and verify with counsel before acting.
 Termination hands off to offboarding/.)
```
