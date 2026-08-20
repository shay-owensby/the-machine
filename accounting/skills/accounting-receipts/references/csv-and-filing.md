# The ledger and the archive

Two artefacts, both inside the **client project root** (the current working directory):

```
accounting/
  expenses.csv
  receipts/
    _processed-receipts/
      needs-review.md
      receipts-notified.log
      YYYYMM_MonthName/
```

Any of these folders that do not exist yet get created by `check_inbox.py` at
the start of a scheduled run, and by the writing scripts themselves otherwise.
The run's own bookkeeping — `needs-review.md` and `receipts-notified.log` — sits
inside `_processed-receipts/` rather than beside the ledger, because everything
loose in `accounting/receipts/` is treated as a receipt awaiting processing and
a log file left there would be read as one.

## The CSV

**One file, one header row, one row per receipt.** No second sheet, no summary block,
no blank spacer rows, no totals row at the bottom — a totals row breaks every filter
and pivot the user will build on top of it. Report totals in prose; keep the file flat.

`accounting/expenses.csv` is **append-only**. It accumulates across every run, month
after month. Never regenerate it, never re-sort it, never rewrite it to "tidy it up".
If a row is wrong, edit that one row in place and tell the user what changed.

### Columns, in order

| # | Column | Format | Notes |
|---|---|---|---|
| 1 | `merchant` | text | Trading name, consistent across the ledger |
| 2 | `purchase_date` | `YYYY-MM-DD` | Transaction date, never the due date |
| 3 | `currency` | ISO 4217 | `GBP`, `EUR`, `USD` … |
| 4 | `gross_amount` | `0.00` | What was charged, tax included. Negative for refunds |
| 5 | `tax_amount` | `0.00` | VAT/GST contained in gross. `0.00` is a valid answer |
| 6 | `net_amount` | `0.00` | `gross − tax` |
| 7 | `receipt_number` | text | Verbatim, empty if none printed |
| 8 | `category` | text | Exactly one string from this client's `accounting/_references/categories.md` |
| 9 | `confidence` | `0.00`–`1.00` | See `confidence-and-review.md` |
| 10 | `needs_review` | `yes` / `no` | `no` for a vendor on this client's `whitelist.md`, unless the *reading* is in doubt |
| 11 | `review_notes` | text | Required when `needs_review` is `yes`. Also carries `Whitelisted vendor — approved without review.` |
| 12 | `file_path` | text | **Post-move** path, relative to the project root |
| 13 | `processed_at` | `YYYY-MM-DDTHH:MM:SS` | Written by the script |

Amounts carry no currency symbol and no thousands separator — `1234.56`, not
`£1,234.56`. Symbols turn the column into text and Excel will refuse to sum it.

`scripts/file_receipt.py` writes every row, so quoting, escaping and column order are
handled. Do not append rows to the CSV by hand with `echo` or `>>` — a merchant name
containing a comma will silently shift every column after it.

## The archive

Month folders are named `YYYYMM_MonthName` from the **purchase date**, not from today:

```
202601_January   202602_February  202603_March      202604_April
202605_May       202606_June      202607_July       202608_August
202609_September 202610_October   202611_November   202612_December
```

Filed name: `YYYY-MM-DD_merchant-slug_gross.ext`, e.g.
`2026-03-14_shell-service-station_48.20.jpg`. The date leads so the folder sorts
chronologically; the merchant and amount make a receipt findable without opening it.
The original extension and file contents are preserved untouched.

Collisions get `-2`, `-3` appended before the extension — two genuinely separate
purchases from the same merchant, on the same day, for the same amount do happen.

### Rules

1. **Move, never copy and never delete.** After a successful run the original location
   is empty and the archive holds the file. The user should never end up with two
   copies drifting apart, and never with zero.
2. **File the original**, not the JPEG the prep script produced from a HEIC and not the
   downscaled copy. The archive keeps the best available fidelity.
3. **Order of operations: move the file, then append the row.** If the append fails,
   the script moves the file back. A row pointing at a file that is not there is worse
   than a file that has not been booked yet — the second is findable by the audit, the
   first looks like data.
4. **Never write into an existing month folder's files.** Adding is fine; overwriting
   is not.

## Duplicate policy

Before a row is written, the script checks the existing ledger for:

- the same normalised merchant **and** the same date **and** the same gross amount; or
- the same non-empty `receipt_number` from the same merchant.

Either match exits with code `3` and writes nothing. That is a stop sign, not a
speed bump.

**Go and look at both images before doing anything else.** The common cases:

- *Same expense, photographed twice* (or the itemised receipt plus its card slip) —
  book it once. File the better image, and either discard the second from the input or
  leave it in place and name it in the report.
- *Genuinely two purchases* — two coffees from the same shop on the same day at the
  same price is entirely ordinary. Re-run with `--force`, and put the reason in
  `--review-notes` so the pair does not look like a mistake to whoever audits it later.
- *A refund matching an earlier charge* — not a duplicate. Book it as a negative gross
  with `refund` in the notes; `--force` is appropriate here too.

Never resolve a duplicate by editing the merchant or amount to make the check pass.

## Recovering a broken run

`python3 scripts/file_receipt.py --audit --csv <csv> --receipts-root <root>` reports:

- **Missing files** — a CSV row whose `file_path` does not exist. Either the file was
  moved by hand afterwards, or the run died between the two steps. Find the file and
  correct the row's path; do not delete the row.
- **Orphan files** — an archived receipt with no CSV row. The move succeeded and the
  append did not. View the image again and re-run `file_receipt.py` with `--source`
  pointing at its archived location; the script handles a source that is already
  inside the archive.

Run the audit at the end of every session, before reporting.
