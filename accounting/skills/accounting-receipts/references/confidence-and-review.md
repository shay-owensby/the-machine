# Confidence scoring and review flags

Two columns work together:

- `confidence` — a number from `0.00` to `1.00` saying how much of the row you read
  directly off the image versus inferred.
- `needs_review` — `yes` or `no`. A human has to look at this one before it goes to
  the accountant.
- `review_notes` — one short sentence saying **what** to check. Never leave a
  `needs_review = yes` row with an empty note; a flag without a reason just makes the
  user re-open every image, which is the work the skill was supposed to remove.

## Confidence bands

| Band | Meaning |
|---|---|
| `0.95 – 1.00` | Every field read cleanly off a sharp image. Merchant, date, gross, tax and number all printed and legible. Arithmetic reconciles exactly. |
| `0.85 – 0.94` | All the money is certain; something minor was inferred — merchant name tidied from a card descriptor, tax computed from a printed rate, receipt number absent. |
| `0.70 – 0.84` | One material field required real judgement: a date format resolved from locale, a partly obscured total read from context, a hand-written amount. |
| `0.50 – 0.69` | Significant uncertainty. A key figure is a best reading, not a clear one. Always `needs_review = yes`. |
| `below 0.50` | You are largely guessing. Do not write speculative values — write what you could read, blank the rest, and flag. |

Anything below `0.85` should have a review note explaining what pulled it down, even
when `needs_review` is `no`.

**Score honestly.** The whole value of the column is that the user can skim the ledger
and only re-open the images below their tolerance. A run where everything is `0.97`
because it looked tidy is worse than no score at all.

## Conditions that force `needs_review = yes`

Regardless of how high the confidence is:

1. **No legible gross amount**, or the total block is cropped or obscured.
2. **No date**, or a date you could not disambiguate (`03/04/26` with nothing to
   resolve it).
3. **The arithmetic will not reconcile** — `gross − tax ≠ net` beyond a cent.
4. **Foreign currency** — anything not in the ledger's usual currency. Someone must
   choose an exchange rate.
5. **Suspected duplicate** — the ledger already holds a matching merchant/date/amount,
   or this looks like the card slip for an itemised receipt already booked.
6. **Apparently personal spending** — groceries, personal clothing, a domestic
   utility, anything with no visible business purpose. Flag it plainly. Do not decide
   on the user's behalf that it is deductible, and do not hide it under a business
   category.
7. **Category is `Uncategorised`.**
8. **The document is not a simple receipt** — a proforma, a quote, a statement, a
   deposit or part-payment, a refund or credit note, a receipt covering multiple
   months of service.
9. **VAT is claimed but no VAT number is printed**, on anything material — the VAT may
   not be reclaimable.
10. **Handwritten receipts**, and anything where the total was altered by hand.
11. **The image contained more than one receipt**, on every row it produced.
12. **A round-number total with no itemisation** above a material amount — worth a
    human glance before it goes in the books.

## Writing the review note

One sentence, specific, and actionable. It should tell the user what to do, not what
went wrong internally.

Good:
- `Date could be 2026-03-04 or 2026-04-03 — no day above 12 on the receipt; confirm.`
- `VAT rate not printed; 0.00 assumed as no VAT number is shown. Confirm supplier is not registered.`
- `Possible duplicate of the 2026-03-14 Shell entry — this may be the card slip.`
- `Groceries — confirm the business purpose before claiming.`

Useless:
- `Low confidence.`
- `Check this.`
- `OCR uncertain.`
