# Expense categories

A **fixed** taxonomy. Write one of these strings into the `category` column exactly as
spelled here. Do not invent new categories, do not pluralise differently, do not add a
sub-category with a slash — a ledger with `Travel`, `travel` and `Travel/Transport` in
it cannot be filtered, which defeats the purpose of the column.

| Category | What lands here |
|---|---|
| `Travel & Transport` | Trains, flights, taxis, rideshare, buses, parking, tolls, car hire |
| `Fuel & Mileage` | Petrol, diesel, EV charging, mileage reimbursements |
| `Accommodation` | Hotels, serviced apartments, short-let stays for work |
| `Meals & Subsistence` | Solo or team meals while working or travelling; coffee runs |
| `Client Entertainment` | Meals, drinks, events and gifts where a client was present or the recipient |
| `Office Supplies` | Stationery, printing, consumables, kitchen and cleaning supplies |
| `IT Equipment` | Laptops, phones, monitors, peripherals, cables, storage |
| `Software & Subscriptions` | SaaS, licences, hosting, domains, app stores, AI tools |
| `Marketing & Advertising` | Ad spend, sponsorships, print, promotional items, stock media |
| `Professional Fees` | Accountants, solicitors, consultants, contractors, agency invoices |
| `Training & Development` | Courses, certifications, conferences, books, memberships |
| `Postage & Shipping` | Couriers, postage, packaging materials, freight |
| `Telecoms & Internet` | Mobile plans, broadband, VoIP, SIMs, roaming |
| `Utilities` | Electricity, gas, water, waste for business premises |
| `Rent & Facilities` | Office rent, coworking, storage, service charges |
| `Bank & Payment Fees` | Card processing fees, bank charges, FX fees, interest |
| `Insurance` | Professional indemnity, public liability, contents, cyber, vehicle |
| `Repairs & Maintenance` | Equipment repair, servicing, cleaning contracts, premises upkeep |
| `Staff Welfare` | Team lunches, staff events, refreshments, wellbeing spend |
| `Uncategorised` | Nothing above fits, or the business purpose is genuinely unclear |

## Choosing between the close calls

These four pairs account for nearly every miscategorisation:

- **Meals & Subsistence vs Client Entertainment** — who ate. A client or prospect at
  the table makes it entertainment (which is often treated very differently for tax).
  If the receipt shows a cover count above one and you have no idea who was there,
  categorise as `Meals & Subsistence` and note the uncertainty.
- **Meals & Subsistence vs Staff Welfare** — one person working makes it subsistence;
  the team as a group makes it welfare.
- **IT Equipment vs Office Supplies** — durable and depreciable is equipment; consumed
  and replaced is supplies. A £900 monitor is equipment, a £9 mouse mat is supplies.
- **Software & Subscriptions vs Professional Fees** — buying a tool is software;
  buying someone's time is a professional fee. An agency retainer that includes tool
  access is still a professional fee.

## Rules

1. **One category per row.** If a receipt genuinely straddles two (a supermarket run
   with both office coffee and a client gift), categorise by the larger share and note
   the split in the review notes.
2. **Category never drives the review flag on its own** — an uncertain category is
   normal and is what the confidence score is for. `Uncategorised` is the exception:
   it always gets `needs_review`.
3. **Match the ledger's history.** Before categorising, glance at how the same
   merchant was categorised previously in `expenses.csv` and stay consistent unless
   the earlier call was clearly wrong.
4. **Personal-looking spending is not a category problem.** Do not bury a personal
   purchase under a plausible business heading. Flag it — see
   `confidence-and-review.md`.
