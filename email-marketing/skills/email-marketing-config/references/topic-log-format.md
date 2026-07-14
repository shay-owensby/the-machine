# Topic Suggestion Log — Format & Dedup Rules

Location: `<client-project>/email-marketing/references/topic-researcher.md`

This file is the **single source of truth** for topic deduplication. The topic-researcher agent MUST read it before researching and MUST prepend every new suggestion to it — logging is mandatory, not optional. Entries are **newest-first**: new date sections are inserted at the TOP, directly below the header block.

## File template (written by setup)

```markdown
# Topic Suggestion Log

<!-- MACHINE-MANAGED FILE — newest entries at the top.
     The topic-researcher agent prepends a dated section per run.
     Status lifecycle: suggested -> used | rejected.
     Never suggest a topic that semantically duplicates ANY row below,
     regardless of status. Do not edit rows except the Status/Issue columns. -->

<!-- LOG:BEGIN -->
<!-- LOG:END -->
```

## Entry format (one section per run, prepended after `<!-- LOG:BEGIN -->`)

```markdown
## 2026-07-14

| Date | Topic | Slug | Status | Issue | Sources | Notes |
|------|-------|------|--------|-------|---------|-------|
| 2026-07-14 | Summer coat care for double-coated breeds | summer-coat-care | used | drafts/2026-07-14/ | [1](https://example.com/a), [2](https://example.com/b) | user pick |
| 2026-07-14 | Back-to-school grooming schedules | back-to-school-grooming | suggested | | [1](https://example.com/c) | |
| 2026-07-14 | Heat-stroke warning signs for pets | pet-heatstroke-signs | rejected | | [1](https://example.com/d) | user: too grim |
```

Rules:
- Valid GitHub-flavored markdown at all times — every row keeps all 7 columns; pipes inside topics are escaped (`\|`).
- **Prepend**: the new `## YYYY-mm-dd` section goes immediately after `<!-- LOG:BEGIN -->`, above all older sections. Never append to the bottom; never rewrite older sections.
- Every candidate presented to the user gets a row with status `suggested` — written BEFORE the user picks, so nothing is ever lost.
- The orchestrator later updates only the Status and Issue columns of the chosen row (`suggested` → `used`, Issue → `drafts/YYYY-mm-dd/`). Topics the user explicitly declines become `rejected` with the reason in Notes.

## Status lifecycle

`suggested` → `used` (became an issue) or `rejected` (user declined). Rows never leave the file.

## Deduplication rules (both must pass)

1. **Slug match** — normalize the candidate title to a kebab-case slug (lowercase, strip stop-words and punctuation); if the slug matches any existing row's Slug, it is a duplicate.
2. **Semantic match** — compare meaning, not strings. "5 winter coat tips" duplicates "Winter coat care guide". "Holiday gift ideas for dog lovers 2025" vs "2026" is still a duplicate unless the angle is genuinely new.

Duplicates are excluded regardless of status — a `rejected` topic stays excluded unless the user explicitly revives it. A `used` topic may only return if the user asks for a follow-up/update angle, and then it must be logged as a new row with a distinct slug (e.g. `summer-coat-care-2027-update`) and a Notes reference to the original.

If the log file is missing in a configured project, recreate it from the template above (empty log), warn the user that dedup history was lost, then proceed.
