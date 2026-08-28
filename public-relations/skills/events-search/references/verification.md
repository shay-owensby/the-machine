# Verification

Run this before writing the report, with a **fresh** subagent that has not seen
the research. Its job is to refute, not to confirm. A verifier that returns
"everything checks out" has not done the work.

## The four fields that get hallucinated

In order of frequency:

1. **Dates** — extrapolated from last year, or lifted from a stale aggregator
2. **Costs** — remembered from a similar event, or rounded from a range
3. **Deadlines** — inferred from the event date rather than read
4. **Attendance** — repeated from a marketing claim as though it were measured

Every one of these must trace to a URL fetched during this run. Not "the
organizer's site" — the specific page.

## The date-rollover trap

The single most common error in this work. A search for "{CITY} fall festival"
returns a page that ranks well precisely because it has ranked for a year — last
year's page, with last year's dates, still live at the same URL.

Three defences:

- Read the year on the page, not just the month and day.
- Check the day of week: if the page says "Saturday, September 14" and September
  14 next year is a Monday, that page is last year's.
- Prefer a page that names the upcoming year explicitly, and cross-check against
  one other source.

When the next edition's dates genuinely are not announced, that is the finding.
Write it as: **"2025: Sept 12–14. 2026 dates not announced — watch <URL>."** Never
project a date forward, not even for an event that has run the same weekend for
thirty years.

## Verifier prompt

> You are auditing a list of events researched for a business considering booths
> and sponsorships. Your only job is to find what is wrong. Do not confirm
> anything that is right; return only problems.
>
> For each event, check:
> - Do the dates appear on the organizer's own current page, for the correct
>   year? Check the day of week against the date.
> - Is the stated booth or sponsorship cost on a page you can open right now, and
>   is that document for this year's edition?
> - Is the application deadline read from an actual form or prospectus, or
>   inferred?
> - Does the attendance figure have a source and a year, and is the source the
>   organizer's own marketing?
> - Does the organizer contact exist on a page you can open?
> - Is the event still running at all — not cancelled, relocated, renamed, or
>   defunct?
>
> Return: claims that are wrong, claims that are overstated, and claims that
> cannot be verified either way. Cite a URL for each judgement. Do not rewrite
> the list.

## Applying the results

Correct what is wrong. **Keep the flags rather than deleting the shaky claims** —
a report that tells the user which three numbers to confirm by phone is more
useful than one that reads uniformly confident and is wrong twice.

Tags used in the report:

- Plain text — confirmed on the organizer's own current page, this run
- `[unconfirmed]` — only source is an aggregator, a third party, or the
  organizer's marketing without a document behind it
- `[conflicting]` — credible sources disagree; the report says which sources and
  what each claims
- `[stale — 2025 event]` — carried from a prior edition, retained because it is
  the best available signal

If verification kills a finalist outright — the event is defunct, or the deadline
passed last month — move it to **Considered and passed** with the reason. Do not
silently drop it; the fact that it was checked is worth recording.
