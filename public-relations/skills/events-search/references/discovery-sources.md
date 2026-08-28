# Discovery sources

The best booth opportunities for a local business are almost never on page one of
a web search. They live on chamber calendars, parks-and-rec PDFs, and Facebook
pages run by a volunteer. Work the source classes deliberately.

Run one subagent per class, in parallel. Give each the town list, the category,
and the date window, and require a source URL per candidate.

## The twelve source classes

**1. Chambers, CVBs, and tourism boards** — one per town in the ring. The single
highest-yield class. Chambers also run their own expos and business-after-hours
events, and their member directory reveals who sponsors what.
Also check: Main Street programs, downtown associations, merchant associations.

**2. Municipal and county calendars** — city event calendars, parks and
recreation department schedules (often a seasonal PDF, not a web page), county
fair boards, extension offices. Parks-and-rec runs the summer concert series and
the movie-in-the-park nights that sell cheap vendor spots.

**3. Aggregators and ticketing platforms** — Eventbrite, Facebook Events,
Meetup, AllEvents.in, EventCrazy, 10times (B2B and trade shows), Festivals.com.
Broad but noisy and frequently stale. Treat every date from an aggregator as
`[unconfirmed]` until seen on the organizer's own page.

**4. Local news and alt-weekly calendars** — the newspaper's "things to do this
weekend," the TV station's community calendar, the alt-weekly's listings. These
catch the events with no website at all.

**5. Charity, nonprofit, and race calendars** — RunSignUp, Active.com, and
local 5K/walk/ride listings; hospital foundations; humane societies and animal
shelters; United Way; Rotary, Lions, Kiwanis, Optimist clubs. Charity events sell
sponsorship cheaply and hand over real goodwill. Match the cause to the category
where you honestly can, and say when the match is a stretch.

**6. Schools and universities** — district fall festivals and carnivals, PTA and
booster events, homecoming, university welcome weeks and family weekends,
athletic tailgates, career and vendor fairs. Reaching households with kids is the
whole point of this class.

**7. Category-native events** — the industry's own consumer and trade shows,
association calendars, hobby and breed clubs, enthusiast meetups. Derive the
search terms from the Business Category, and go one level out: adjacent
categories that share a customer are often the better buy because the field is
less crowded.

**8. Recurring commerce venues** — farmers markets, craft fairs, holiday and
maker markets, First Friday art walks, flea markets, swap meets. Weekly or
monthly recurrence means a low-cost, repeatable presence rather than one big bet.
Note season start and end dates and whether the vendor list is capped.

**9. Venue calendars** — fairgrounds, convention centre, expo centre, civic
centre, amphitheatre, minor-league ballpark, speedway. Working the venue's own
calendar surfaces the events whose organizers never show up in search.

**10. Faith and civic organizations** — church festivals and fall carnivals, VFW
and American Legion, community centres, public library systems, neighbourhood
associations, Juneteenth and heritage festivals, cultural associations.

**11. Lifestyle and consumer shows** — home and garden shows, bridal shows,
baby and family expos, health and wellness fairs, senior expos, employer wellness
fairs, home builder association parades. Broad-audience, professionally run,
priced accordingly.

**12. The competitor trail** — search competitors' and adjacent businesses'
social accounts and sites for "booth," "we'll be at," "come see us at,"
"sponsor," "vendor." This finds events no calendar lists, and it tells you where
the money in this category already goes.

## Query patterns

Substitute `{CITY}` from the town list, `{CATEGORY}` and `{YEAR}` from the brief.
Run each against several towns in the ring, not just the home city.

```
{CITY} {YEAR} festival vendor application
{CITY} chamber of commerce events calendar
{CITY} parks and recreation {YEAR} special events
{COUNTY} county fair vendor booth
{CITY} craft fair vendor application {YEAR}
{CITY} farmers market vendor application
{CITY} 5k walk run {YEAR} sponsor
{CITY} school district fall festival vendor
{CITY} {CATEGORY} expo
{CATEGORY} trade show {STATE} {YEAR}
{CITY} home garden show exhibitor
{CITY} health fair vendor booth
{VENUE NAME} events calendar {YEAR}
"{CITY}" ("vendor booth" OR "sponsorship opportunities") {YEAR}
```

Search for the vendor-facing page, not the attendee-facing one. "Vendor
application," "exhibitor prospectus," "sponsorship packet," and "become a
sponsor" are the phrases that land on the page with the prices on it.

## Tools

- `WebSearch` for discovery; `WebFetch` to open the organizer's own page.
- Firecrawl, when available: `firecrawl_search` for the sweep, `firecrawl_scrape`
  on calendar pages that render poorly, `firecrawl_map` to find a site's vendor
  or sponsor page when navigation hides it.
- Facebook Events is frequently unscrapable. When an event clearly lives only on
  Facebook, report it with the page URL and mark it **needs manual check** rather
  than guessing at its details.
- PDFs — vendor prospectuses and parks-and-rec schedules are usually PDFs. Fetch
  and read them; that is where the price list is.

## Subagent brief template

> You are searching for events in {SOURCE CLASS} within these places: {TOWNS}.
> Date window: {TODAY} through {TODAY + 12 months}.
> The business is a {CATEGORY} — use it only to judge whether an event is
> plausibly relevant; include general community events regardless of category.
> Return a flat list. Per event: name, date(s) or "not announced", town, venue,
> source URL, one sentence on what it is, and whether the page mentions vendors,
> booths, or sponsors.
> Do not score, rank, or recommend. Do not invent a date, price, or attendance
> figure. If you cannot find a source URL for an event you saw referenced, say so
> and include it anyway, marked "no source found."
