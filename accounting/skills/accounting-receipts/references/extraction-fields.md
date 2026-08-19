# Extraction fields

One pass per receipt, field by field. Everything here assumes you are **looking at
the image** — these rules resolve what you see, they do not substitute for seeing it.

The governing rule for every field below: **if it is not legible on the page, leave
it empty and flag it.** An empty cell costs the user ten seconds. A plausible-looking
wrong cell costs them an amended return.

---

## merchant

The trading name of who was paid — the name a human would recognise, not the legal
entity buried in the footer and not the payment processor.

- Prefer the name printed largest at the top, or in the logo.
- Strip branch noise: `TESCO STORES 4471 CARDIFF` → `Tesco`. Keep the branch out of
  the merchant column; it belongs in review notes only if it matters.
- Strip legal suffixes for consistency (`Ltd`, `Limited`, `PLC`, `Inc`, `LLC`, `GmbH`)
  unless the suffix is genuinely part of the trading name.
- Card-machine descriptors (`SQ *BLUE BOTTLE`, `PAYPAL *STEAM`, `SumUp`) are the
  *processor*, not the merchant. Take the name after the `*`. If only the processor
  is visible, use it and flag — `Stripe` is not a supplier.
- Online invoices: the seller in the "From" block, never the "Bill to" block. Reading
  the customer's own name into `merchant` is a classic and embarrassing error.
- Be consistent across the ledger. If `Amazon Business` is already in the CSV, do not
  start writing `Amazon.co.uk` — grep the existing merchant column first.

## purchase_date

The date the transaction happened. On an invoice that is the **invoice date**, not the
due date, not the payment date, not the delivery date, not the date printed on a
statement that happens to list the purchase.

Normalise to `YYYY-MM-DD`.

### The ambiguity trap — read this every time

`03/04/2026` is **not a date**. It is March 4th or April 3rd depending on where the
receipt was printed, and picking wrong silently moves an expense into the wrong month
and possibly the wrong tax year.

Resolve it, in this order:

1. **A day number above 12 anywhere on the receipt** settles the format instantly
   (`17/04/26` can only be DD/MM). Check every date on the page, including the card
   slip's timestamp.
2. **Currency and locale** — GBP/EUR receipts are DD/MM; USD receipts are MM/DD.
   Addresses, postcodes, phone formats and the spelling of "authorisation" all help.
3. **A written month** (`4 Mar 2026`, `MAR 04`) anywhere on the page overrides
   everything — prefer it if it is present.
4. **A two-digit year in the middle** (`2026-04-03` vs `03-04-2026`) — ISO order is
   unambiguous when the year leads.

If none of those resolve it, **leave the date as your best reading, set
`needs_review`, and say in the notes which two dates it could be.** Do not quietly
pick one.

Other date traps:
- Receipts printed just after midnight carry the previous trading day's date in the
  header and the real date in the timestamp. Use the transaction timestamp.
- A year missing entirely (common on till rolls) — infer from the surrounding batch
  only if the rest of the batch is unambiguous, and flag it either way.

## currency

Three-letter ISO code: `GBP`, `EUR`, `USD`, `AUD`, `CAD`.

- The symbol usually settles it, but `$` alone does not — USD, CAD, AUD, NZD and SGD
  all use it. Use the address, the VAT/GST wording, or an explicit code on the page.
- A receipt with a foreign currency **always** gets `needs_review`, even when the
  extraction is perfect. Someone has to decide the conversion rate, and it is not you.
- Never convert a foreign amount into the home currency yourself. Record what was
  printed.

## gross_amount

**What was actually charged** — the amount that left the account, VAT included.

Take it from, in order of preference: `Total`, `Amount Due`, `Balance Due`,
`Card Payment`, `Amount`.

Do not take:
- `Subtotal` / `Net` — that is the pre-tax figure and belongs in `net_amount`.
- `Cash Tendered` or `Change` — arithmetic about the customer's wallet.
- A pre-authorisation figure on a hotel or fuel slip — the hold, not the charge.
- The largest number on the page. It is frequently a phone number, a loyalty balance,
  or a line item quantity.

Include in gross: service charge, delivery, booking fees, and any tip that was
actually charged on the card. Exclude a handwritten tip that was never processed.

Split payments (part card, part cash, part voucher): gross is the **full value of the
goods**, not one tender line. If a voucher or credit reduced what was payable, gross
is the reduced amount actually due.

Refunds and credit notes: record the amount as **negative** and put `credit note` or
`refund` in the review notes.

## tax_amount

The VAT / GST / sales tax **contained in** the gross amount.

- Take the stated VAT figure whenever one is printed — the VAT summary box at the
  bottom of a UK till receipt, or the tax line on an invoice.
- **Multiple rates on one receipt** (a supermarket run with 0% food and 20%
  standard-rated items) — sum every VAT line. Do not take just the largest.
- **Only a rate is shown, on a VAT-inclusive total:**
  `tax = gross × rate ÷ (100 + rate)`
  So £48.20 at 20% is `48.20 × 20 ÷ 120 = 8.03`. It is **not** `48.20 × 0.20 = 9.64`.
  This one error accounts for more bad receipt data than everything else combined.
- **Only a rate is shown, on a VAT-exclusive total:** the total is the net; gross is
  `net × (100 + rate) ÷ 100` and tax is the difference. Read which one the receipt
  means before you calculate.
- Coded receipts (`A` = 20%, `B` = 5%, `Z`/`*` = 0%) — the key is usually at the foot
  of the receipt. Use it; do not assume the letters.
- **No VAT number and no VAT line** usually means a non-registered supplier: tax is
  `0.00`, and that is a real answer, not a missing one. Note it.
- Never derive VAT by assuming a rate the receipt does not state.

## net_amount

`gross − tax`, to two decimal places. If the receipt prints a net/subtotal that
disagrees with your subtraction by more than a cent, **you have misread one of the
three numbers** — go back to the image. Do not reconcile the discrepancy by
overwriting the figure you like least. `scripts/file_receipt.py` enforces this.

## receipt_number

The supplier's own reference for the document: invoice number, receipt number, bill
number, order number, transaction ID.

- Copy it **character for character**, including prefixes and leading zeros
  (`INV-0042` is not `42`).
- Preference order when several are printed: invoice number → receipt number → order
  number → transaction/auth ID.
- Do **not** use: the till or terminal number, the store number, the loyalty card
  number, the VAT registration number, the card's last four digits, or the auth code
  on the card slip (unless nothing else exists — then use it and say so in the notes).
- Plenty of small receipts genuinely have no number. Leave it empty. An empty
  `receipt_number` alone is not grounds for a review flag.

## Documents that are not single receipts

- **Two receipts in one photo** → two rows, both `file_path` pointing at the same
  filed image. Note "2 of 2 in image" in the review notes so the pair stays traceable.
- **Multi-page invoice** → one row. The total is on the last page; the invoice number
  is usually on the first.
- **Itemised receipt plus its card slip** → one expense. Prefer the itemised receipt
  (it carries the VAT breakdown), file it, and mention the slip in the notes.
- **A bank or card statement** → not a receipt. Do not create rows from it. Say so.
- **A quote, order confirmation, or proforma** → nothing was paid yet. Do not book it.
  Name it in the report and leave it where it is.
