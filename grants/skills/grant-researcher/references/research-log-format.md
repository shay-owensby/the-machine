# Research Log — format

The research log at `grants/references/research-log.md` is the org's pipeline memory. It exists so future research runs can **dedup** (don't re-surface a grant already seen) and **track** what happened to each opportunity (pursued, skipped, watchlisted, won, lost). It's append-forward: each run prepends a dated section; older sections are never rewritten except to update a single grant's status when its situation changes.

## File structure

The file begins with a fixed header and a `<!-- LOG:BEGIN -->` marker. New dated sections go **immediately below the marker**, newest first. If the file doesn't exist, create it from the template below (and note in your run that prior history was unavailable).

```markdown
# Grant Research Log — {Organization Name}

This log records every grant surfaced by the grant-researcher, newest first. It powers
deduplication across runs and tracks each opportunity's status. Do not delete rows —
update an existing row's Status when things change (e.g. Applied, Awarded, Declined).

Status values: `surfaced` · `watchlist` · `pursuing` · `applied` · `awarded` · `declined` · `skipped` · `expired`

<!-- LOG:BEGIN -->

## {YYYY-MM-DD}

| Grant | Funder | Slug | Score | Deadline | Status | Report | Notes |
|-------|--------|------|-------|----------|--------|--------|-------|
| {program} | {funder} | {kebab-slug} | {0–100} | {YYYY-MM-DD or Rolling} | surfaced | {report filename} | {one line} |
| … | | | | | | | |
```

## Rules

- **Prepend, don't overwrite.** Each run adds one new `## YYYY-MM-DD` section at the top (just under `<!-- LOG:BEGIN -->`). Leave earlier sections intact.
- **Log every grant surfaced this run** — including disqualified/excluded ones (Status `skipped` or `expired`), so they aren't rediscovered as fresh next time.
- **Slug** is a stable kebab-case id derived from funder + program (e.g. `smith-family-arts-education`). It's the dedup key — before surfacing a grant as new, check whether its slug already appears anywhere in the log.
- **Dedup by slug AND by meaning.** "Smith Foundation Arts Grant" and "Smith Family Arts Education Fund" may be the same program — when in doubt, treat as a duplicate and update the existing row instead of adding one.
- **Updating a status:** when a previously-logged grant progresses (the user applied, or it was awarded/declined, or its deadline passed), edit that grant's existing row's Status in place rather than adding a duplicate. A grant whose deadline has passed with no action becomes `expired`.
- **Report** column holds the filename of the research report where this grant was detailed, so a row links back to its full write-up.
- Keep valid GitHub-flavored markdown — all eight columns present in every row.
