# Required Workplace Postings — Tracking Framework

A **framework** for tracking mandatory workplace notices/postings across the client's jurisdictions and worksites — including remote workers. It is deliberately **jurisdiction-agnostic and non-authoritative**: it does **not** list which posters a given jurisdiction requires, because that list changes and varies by jurisdiction, worksite, size, and industry. The actual required posters are sourced at run time from the **official labor/employment agency** for each `legal.jurisdictions` entry and filled into the table below.

> ⚠️ **Never present a poster list as authoritative from memory.** Do not fabricate poster names, editions, revision dates, or agency URLs. If you don't have the current official list, say so and point the user to the agency's official posting page to obtain it.

## How to build the tracker

1. **Scope.** From config, take `legal.jurisdictions`, every worksite in `company.locations`, `company.size`, `company.industry`, and `company.remote_policy`. Multiple jurisdictions and multiple worksites each get their own rows. Refuse to reason about a jurisdiction not in `legal.jurisdictions` — flag it as out of scope and ask the user to add it.
2. **Source the current list.** For each jurisdiction, direct the user to (or have them provide) the **official labor agency's** current mandatory-posting list — typically federal/national + regional/state + sometimes city/local levels stack. Record where each requirement came from. Do not assert a poster is required unless it's on that official list.
3. **Fill the table.** One row per required notice per applicable worksite/jurisdiction. Populate the **source** column with the official agency page. Mark every row "verify against current `<jurisdiction>` list".
4. **Cover remote workers** (see below) — physical posting alone rarely satisfies the duty for remote staff.
5. **Set a review cadence.** Posting requirements and poster editions change; record a "last verified" date and a next-review date. Re-verify against the agency list periodically and whenever headcount crosses a likely threshold or a new worksite/jurisdiction is added.

## Jurisdiction & worksite levels to check

Requirements commonly **stack** across levels — record each separately so nothing is missed:
- **National / federal** `<per legal.jurisdictions>`
- **Regional / state / province** `<per legal.jurisdictions and company.locations>`
- **City / local** — some localities add their own *(verify whether any apply)*
- **Industry-specific** — certain industries carry extra required notices *(verify against `company.industry`)*
- **Size-triggered** — some notices only apply above a headcount threshold *(never state the threshold — verify)*

## Posting tracker (fill per `legal.jurisdictions` × worksite)

| Notice / poster | Jurisdiction & level | Worksite(s) it applies to | Required-when (size/industry trigger) | Displayed? (status) | Location at worksite / distribution method | Edition / last-verified date | Official source to verify |
|---|---|---|---|---|---|---|---|
| `<notice name — from the official agency list, not from memory>` | `<jurisdiction + level>` | `<worksite / all>` | `<all employers / size-triggered — verify / industry — verify>` | `Posted` / `Missing` / `Outdated edition` / `Unknown — verify` | `<physical location, e.g. break room; and/or remote distribution method>` | `<edition & date last checked>` | `<official labor agency posting page URL>` |
| _(add one row per required notice per jurisdiction/worksite)_ | | | | | | | |

> ⚠️ **Draft — requires review by qualified HR/legal counsel before use.** Stamp this on any instantiated posting tracker.

## Remote & hybrid workers

Physical break-room posters usually do **not** satisfy notice duties for employees who don't regularly visit that worksite. For anyone remote/hybrid (`company.remote_policy`):
- Determine each remote employee's **work jurisdiction** — a remote worker can pull an additional jurisdiction (and its posting duties) into scope even if the company has no office there. Flag any such jurisdiction not already in `legal.jurisdictions`.
- Provide notices through a channel the jurisdiction accepts for remote delivery — **verify the accepted method** (e.g. a dedicated internal notices page, emailed/acknowledged notices, an intranet posting). Do not assume electronic delivery is sufficient; confirm against the agency's guidance.
- Keep **distribution records** (what was sent, to whom, when, acknowledgment) as the evidence that the duty was met.

## Recordkeeping for postings

- Keep evidence that each required notice is displayed/distributed: a dated worksite posting log or photos, and remote-distribution records.
- Record the poster **edition/revision** where agencies update them — an outdated edition can count as non-compliant.
- Store the tracker and evidence in `legal-compliance/`; keep any employee-identifiable acknowledgment records in the confidential zone (`confidentiality.records_dir`).

## Reminders

- The tracker is a **compliance-support draft for counsel review**, not legal advice or a guarantee that postings are complete.
- Poster lists come from the **official labor agency** at run time — never fabricated or recalled from memory.
- Every row is scoped to `legal.jurisdictions` and flagged "verify against current list". Refuse out-of-scope jurisdictions; flag remote-worker jurisdictions not yet in config.
- Save to `legal-compliance/`.
