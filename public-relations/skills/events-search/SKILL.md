---
name: events-search
description: Find local events — festivals, fairs, expos, charity runs, markets, community days, school and civic events — where a business should buy a booth or a sponsorship, then qualify the finalists with cost, attendance, deadlines, and organizer contacts. Use when the user asks to find events, look for booth or vendor opportunities, find sponsorships, find festivals or expos in the area, build an events calendar, asks "where should we have a booth", "what's happening around here we could sponsor", "find local events for [client]", or wants an existing events report refreshed. Brand-agnostic — the business it serves is read from the project's events-search-parameters.md, never assumed.
---

# Events Search

Turn a business's location and category into a ranked, verified shortlist of local
events worth a booth or a sponsorship — with the numbers and deadlines that make
each one a decision rather than a suggestion.

**The core discipline: read the brief, sweep wide, then dig deep on few.** The
failure mode of this work is a confident list of twelve events with wrong dates,
guessed booth prices, and three deadlines that passed last month. A shortlist of
six events with verified costs and a named organizer beats a list of forty every
time.

## Step 0 — Read the parameters file. This is a hard gate.

Before any search, before any assumption about the business, read:

```
Public Relations/Events/references/events-search-parameters.md
```

relative to the current working directory (the client project root).

**Never search from memory, from the project folder's name, or from a business
carried over from an earlier session.** This skill is brand-agnostic; the
parameters file is the only thing that makes a run specific.

Required fields:

| Field | Purpose |
|---|---|
| **Business Category** | What the business does — drives category-native events and audience overlap |
| **Business Address** | The centre of the search ring |
| **Search Radius** | How far out to look, in miles |
| **Slack Channel ID** | Where the finished report is delivered (Step 7) |

The file is open-ended — read and honour anything else it carries: target
customer, budget ceiling, blackout dates, events already worked or declined,
competitors to watch, brand cautions, staffing limits.

The Slack Channel ID normally sits under a `## Report Delivery` heading. If it
appears in more than one place and the values disagree, stop and ask — do not
pick one.

**If the file is missing:** stop. Ask the user for the required fields with
AskUserQuestion, create the directory, write the file from
`assets/events-search-parameters-template.md`, then continue. Do not proceed on a
verbally-supplied brief without writing it down — the next run needs it too.

**If a required field is blank or ambiguous:** ask for that field only.

Then echo what you read back in one line and get on with it. Don't ask the user
to confirm a file they wrote themselves.

## Outputs

Written into the client project:

```
Public Relations/Events/YYYY-MM-DD-events-report.md
```

One dated snapshot per run. Create the parent directory before writing. Never
overwrite a prior run's report — the history of what was considered and rejected
is worth keeping.

The file is the full report. A **summary** of it is then delivered to the Slack
channel named in the parameters file (Step 7) — Slack caps a message at 5,000
characters, so the channel gets the decision, not the document.

## Step 1 — Build the geographic frame

Search engines cannot search "within 25 miles." They search place names. So turn
the radius into a list of names before doing anything else.

1. Resolve the address to city, county, and metro area.
2. Enumerate every town, city, and unincorporated community inside the radius —
   by name. A 25-mile ring around a mid-sized city is typically 8–20 named
   places. Note the county seats and the towns with fairgrounds.
3. Note the regional draw: a metro's flagship festival pulls attendees from far
   outside the ring, and that widens who is worth reaching, not where to look.
4. Fix the date window: today through today + 12 months.

Record the ring in the report. Every discovery query in Step 2 anchors to a named
place in it.

## Step 2 — Discovery sweep: breadth, not depth

Fan out parallel subagents, one per source class in
`references/discovery-sources.md`. Twelve source classes are listed there; the
ones that matter most are rarely the ones a general web search surfaces.

Each subagent returns raw candidates only — name, date(s), place, source URL, one
line on what it is. **No scoring, no judgement, and above all no invention.** An
event it cannot find a URL for is reported as "referenced but no source found,"
not quietly dropped and not confidently described.

Expect 40–80 raw candidates before filtering. Under 15 means the sweep was too
narrow — widen the ring or add source classes. Do not pad the list to hit a
number.

Dedupe on name + date + venue. The same festival appears on the chamber calendar,
Eventbrite, the local TV station, and its own site, usually with three different
dates — keep the one from the organizer's own page and note the conflict.

## Step 3 — Score and shortlist

Apply the rubric in `references/fit-scoring.md`. Score in two lanes, and take
finalists from both:

- **Category-native** — the pet expo for the groomer, the home show for the
  contractor. Obvious, high intent, often expensive and crowded with competitors.
- **General community** — the fall festival, the school carnival, the charity 5K.
  Lower intent per head, far higher volume, far cheaper, and usually where a
  local service business actually wins. A business with no obvious niche event
  lives entirely in this lane.

Score everything. Shortlist 8–12 finalists. Keep the rest in the report under
**Considered and passed**, each with a one-line reason. That tier is what stops
the same dead ends being re-researched next quarter.

## Step 4 — Deep dossier on the finalists only

Per finalist, capture the fields in `references/event-dossier.md`: exact dates,
venue, attendance with the year it refers to, booth cost and sponsorship tiers,
application deadline and whether applications are open, organizer name with email
and phone, vendor rules, category exclusivity, load-in, power and tent
requirements, and any restriction that would exclude this business outright.

**The deadline field is what makes this report actionable.** Anything closing
within 30 days is flagged **ACT NOW** and rises to the top of the report
regardless of score.

## Step 5 — Verify before writing. Do not skip.

Hand the drafted finalists to a *fresh* subagent whose only job is to refute
them. Four fields get hallucinated, every time: **dates, costs, deadlines,
attendance.** Each must trace to a URL fetched during this run.

Reliability convention, used throughout the report:

- Plain text — confirmed on the organizer's own page this run
- `[unconfirmed]` — only source is an aggregator or a third party
- `[conflicting]` — credible sources disagree; never act on it without calling
- `[stale — 2025 event]` — carried from a prior year's page

An event whose next-year dates are not announced is a real finding. Write "2025
was Sept 12–14; 2026 not yet announced — watch <URL>." Never extrapolate a date
from last year's, and never round a price you did not read.

Full prompt and the date-rollover trap: `references/verification.md`.

## Step 6 — Write the report

Use `assets/events-report-template.md`. Ordered: ACT NOW deadlines, then
finalists by score, then considered-and-passed, then the parameters and sources
used. Every event carries its source URL.

## Step 7 — Deliver the summary to Slack

Read the **Slack Channel ID** from the parameters file. Compose the summary using
`assets/slack-summary-template.md`: the ACT NOW deadlines, the top three
finalists with the one reason each, the counts, and the single biggest gap.
Budget 3,000 characters; 5,000 is the hard ceiling.

Show the composed message and the destination channel ID to the user, then send
it with `slack_send_message`. Return the message permalink.

**Never guess a channel.** If the Slack Channel ID is missing or blank, write the
report, tell the user Slack delivery was skipped and why, and stop there — do not
search for a channel by name and do not fall back to another channel.

Message shape, character budget, and the four ways this fails:
`references/slack-delivery.md`.

## Step 8 — Report to the user

Lead with the three events you would actually spend the money on and why, the
nearest deadline, and the biggest gap you hit (a calendar you could not access, a
cost nobody publishes). Give the report path and the Slack permalink. Do not
recap the report — they can read it.

## Standing rules

- **The parameters file is the brief.** Never substitute your own read of what
  the business does, and never let a previous client's context leak into this run.
- **Never invent a date, a price, a deadline, or an attendance figure.** An
  unknown is a deliverable: "booth cost not published — organizer contact below."
- **A dead event is a finding.** Defunct, relocated, renamed, or cancelled — say
  so, with the year it last ran. It stops the user chasing it.
- **Cost is not the same as cost-to-reach.** A $1,200 booth in front of 20,000
  qualified people beats a $150 table in front of 300. Score the ratio, and say
  when a cheap event is the worse buy.
- **Flag pay-to-play.** Some "expos" sell booths to a room made mostly of other
  vendors. Attendee-to-vendor ratio is the tell; if it cannot be established, say
  so rather than assuming reach.
- **Note competitor presence** when the past vendor list is public. It cuts both
  ways — it proves the audience and it crowds the field.
- **The radius is a guideline.** An unusually strong event just outside it gets
  included and flagged as outside the ring, with the drive time.
- **Nothing goes to Slack that has not been verified.** The channel is the
  client's. A wrong date posted there is a phone call to the client, not a line
  in a file. Step 5 runs before Step 7, always.
- **Sponsorship and booth are different products.** Sponsorship buys logo and
  mention; a booth buys conversations. Say which one an event is actually good
  for, and note when a sponsor tier includes booth space.
