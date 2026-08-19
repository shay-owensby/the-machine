---
name: accounting-receipts
description: Read receipt and invoice images or PDFs, extract the bookkeeping fields (merchant, date, gross total, VAT/tax, receipt number, category, confidence), append one row per receipt to a single expenses.csv ledger, and file the original into accounting/receipts/processed-receipts/YYYYMM_MonthName/. Also runs unattended as a scheduled task in a client project: it picks up whatever has been dropped into that client's accounting/receipts/ folder, processes it, and posts a one-line summary to their Slack channel from SLACK_CHANNEL_ID in .env. Use this skill whenever the user hands over a receipt, an invoice, a photo of a receipt, a scan, a folder of receipts, or says "process these receipts", "log this expense", "do my expenses", "add this to the books", "what's the VAT on this", "file these for the accountant", "sort out my receipts", "expense this", "bookkeeping", or "record this purchase". Use it too for the scheduled run — "process the receipt inbox", "check the drop folder", "any receipts waiting", "do the nightly receipts". Also use it when a receipt arrives as an email attachment or a download and the natural next step is getting it into the expense ledger.
---

# Accounting Receipts

Turn a pile of receipt images into two things that survive an audit: **one row per receipt in a single CSV ledger**, and **the original image filed by month** where an accountant can find it in seconds.

**The core discipline: read the image, do not infer the receipt.** Every number in the ledger must be one you actually saw on the page. A confidently wrong figure is far worse than a blank cell with a review flag — the blank gets fixed in ten seconds, the wrong figure gets filed with a tax return. When you cannot read something, say so and flag it. Never guess a total, never invent a receipt number, never assume a date format.

---

## Two ways this runs

**On demand.** Someone hands you files or a folder. Start at Step 1.

**Scheduled.** Nobody hands you anything and nobody is watching. Files have been
uploaded into this client's `accounting/receipts/` drop folder and their
scheduled task has woken you up to deal with them. Start at Step 0 and finish
with the Slack post in Step 8.

**Definition of done for a scheduled run:** every file that was in the drop
folder is either a ledger row or a named exception in the report, *and* the
summary has been posted to the client's Slack channel (or its failure reported).
Both halves, every time.

Each client has their own task, running in their own project directory. A
scheduled run never reaches outside the project root it started in.

The reading of a receipt is identical either way. What changes unattended: the
drop folder is the only input, you cannot stop and ask, and the client's Slack
channel hears the result. The full contract for that mode — `.env` handling, what
to do when a receipt fails, and what to do when the scripts cannot run at all —
is in `references/scheduled-runs.md`. Read it before your first scheduled run.

---

## Outputs

Everything is written into the **client project root** — the current working directory:

```
.env                                          SLACK_CHANNEL_ID for this client
accounting/
  expenses.csv                                one flat file, one header row, one row per receipt
  needs-review.md                             what a run could not resolve on its own
  receipts-notified.log                       one JSON line per Slack post
  receipts/                                   THE DROP FOLDER -- uploads land here
    IMG_4471.HEIC                             waiting to be processed
    invoice-march.pdf
    processed-receipts/
      202603_March/
        2026-03-14_shell-service-station_48.20.jpg
        2026-03-22_amazon-business_129.99.pdf
      202604_April/
        ...
```

Loose files in `accounting/receipts/` are the **inbox**; everything under
`processed-receipts/` is **done**. Processing moves a file from the first to the
second, which is the only state a scheduled run needs — an empty inbox means
there is no work, so a nightly run on a quiet week does nothing and says
nothing.

Two path roots are in play throughout, and mixing them up is the one mechanical
error that will bite: `scripts/` and `references/` are relative to **this skill's
directory**, while `accounting/` is relative to the **client project root**. Use
absolute paths for the scripts if there is any doubt.

`expenses.csv` is a **running ledger, appended to** — never overwritten, never re-created from scratch. It opens in Excel or Google Sheets as a single sheet. Column schema and filing rules: `references/csv-and-filing.md`.

---

## The pipeline

### Step 0 — Check the inbox (scheduled runs only)

Work from the **client project root**. Every `accounting/…` path below is
relative to it, and `file_receipt.py` records `file_path` relative to the working
directory, so staying put is what keeps the ledger pointing at its own files.

```bash
python3 scripts/check_inbox.py
```

Every file waiting, how each one will need to be opened, and the
`SLACK_CHANNEL_ID` from this client's `.env`. Exit code `1` means the inbox is
empty — a normal, quiet night. Say so in one line and stop; do not go looking for
work elsewhere.

**The folder is the filter.** Every loose file in `accounting/receipts/` is a
receipt to process — the only other thing that lives there is the
`processed-receipts/` subfolder. Nothing else about a file decides whether it
counts:

- **Never filter by filename.** Do not `ls *receipt*`, do not glob, do not grep
  the folder, do not skip a file because its name looks like something else.
  `08capcut.pdf` is a receipt. `IMG_4471.HEIC` is a receipt. `invoice_final`
  with no extension at all is a receipt.
- **Never filter by extension.** An unrecognised format is a receipt you have to
  work harder to open, not a file to pass over.
- **Take the file list from `check_inbox.py`**, not from your own listing of the
  directory. It reports every file and it is the count you reconcile against.

`pending_count` is a contract: when the run ends, that many files must each be
either written to the ledger or named in the report with a reason. A receipt that
is neither is a receipt that went missing.

Mark the start of the run before processing anything; Step 8 needs it:

```bash
START=$(python3 scripts/run_report.py --mark-start)
```

### Step 1 — Gather and prepare the inputs

Run the prep script over whatever the user pointed you at — a single file, several files, or a folder:

```bash
python3 scripts/prepare_receipts.py <paths...> --workdir "$SCRATCHPAD/receipt-prep"
```

On a scheduled run there is nothing to point at but the drop folder:

```bash
python3 scripts/prepare_receipts.py accounting/receipts --workdir "$SCRATCHPAD/receipt-prep"
```

It walks the inputs, skips anything already sitting under `processed-receipts/`, converts HEIC/WEBP/TIFF to JPEG, downscales oversized photos so fine print survives the read, counts PDF pages, and writes a manifest listing every receipt to be processed.

Read the manifest before going further. If it found nothing, say so rather than inventing work. If it found far more or far fewer files than the user implied, mention the count before you start.

The prep script does not filter by filename or extension either — a format it does not recognise gets an entry with a warning, never a silent skip. **Check `found` against Step 0's `pending_count`.** If they disagree, stop and work out why before processing anything; the difference is a file about to be lost.

### Step 2 — View every receipt, one at a time

**Use the Read tool on each `view_path` in the manifest.** This is the one part of the job Bash cannot do — you have to actually look at the image. For PDFs, Read the file with the `pages` parameter.

Non-negotiable: **never write a row for a receipt you have not viewed.** Do not extrapolate one receipt's fields from another, do not process a file based on its filename, and do not batch-assume a run of receipts from the same merchant are identical.

Look at each image properly before extracting:

- Read the whole page, top to bottom, including the small print under the total — VAT summaries and invoice numbers hide there.
- Zoom mentally on the total block. Distinguish **Total / Amount Due / Balance** (what was charged) from **Subtotal**, **Cash Tendered**, **Change**, **Tip**, and **Card pre-auth**.
- Check whether one image contains **more than one receipt**, and whether a multi-page PDF is one invoice or several. One row per *receipt*, not per page or per file.
- If the image is blurred, cropped, glare-blown or upside down, say which fields you genuinely cannot read. That is a real answer.

Field-by-field extraction rules, and the traps that produce wrong numbers, are in `references/extraction-fields.md`. Read it before your first extraction of a session — especially the date-ambiguity and VAT-from-rate sections.

### Step 3 — Normalise and check the arithmetic

For every receipt, before it goes anywhere near the ledger:

- **Dates** become `YYYY-MM-DD`. `03/04/2026` is not a date until you know the locale — resolve it, or flag it.
- **Money** becomes a bare decimal with two places, no symbol, no thousands separator. The currency goes in its own column.
- **`gross − tax = net`** must reconcile to within one cent. If it does not, you have misread one of the three. Go back to the image; do not paper over it with arithmetic.
- If only a VAT *rate* is shown on a VAT-inclusive total, the tax is `gross × rate ÷ (100 + rate)` — **not** `gross × rate ÷ 100`. This is the single most common extraction error.

### Step 4 — Categorise

Pick exactly one category from the fixed taxonomy in `references/categories.md`. The list is fixed so the ledger stays filterable — do not invent new category names. When nothing fits or the business purpose is genuinely unclear, use `Uncategorised` and flag for review rather than forcing a bad fit.

### Step 5 — Score confidence and flag for review

Give every row a confidence between `0.00` and `1.00`, plus a `needs_review` flag with a short reason. The scoring bands and the conditions that force a review flag regardless of score — unreadable total, ambiguous date, VAT that will not reconcile, foreign currency, suspected duplicate, apparently personal spending — are in `references/confidence-and-review.md`.

Be honest here. Confidence is what tells the user which rows they can trust without re-opening the image, so an inflated score destroys the whole point of the column.

### Step 6 — Commit: write the row, then file the image

One call per receipt:

```bash
python3 scripts/file_receipt.py \
  --csv accounting/expenses.csv \
  --receipts-root accounting/receipts/processed-receipts \
  --source "/path/to/original/IMG_1234.jpg" \
  --merchant "Shell Service Station" --date 2026-03-14 --currency GBP \
  --gross 48.20 --tax 8.03 --receipt-number "A-99231" \
  --category "Fuel & Mileage" --confidence 0.94
```

The script owns everything that must be deterministic: it re-checks the arithmetic, refuses suspected duplicates, works out the `YYYYMM_MonthName` folder, moves the original in under a collision-safe name, and appends the row with the **post-move path** in `file_path`. Run it with `--dry-run` first if you want to see the destination before anything moves.

Move the **original** file, not the converted or downscaled copy from the prep workdir. The archive should hold the highest-fidelity version that came in.

Exit code `3` means "suspected duplicate". Do not reflexively re-run with `--force` — go look. An itemised receipt and its card slip are two images of one expense and belong in the ledger once. Full duplicate policy: `references/csv-and-filing.md`.

### Step 7 — Reconcile and report

```bash
python3 scripts/file_receipt.py --audit --csv accounting/expenses.csv --receipts-root accounting/receipts/processed-receipts
```

The audit catches rows pointing at files that are not there and filed files that never made it into the ledger. Fix anything it finds before reporting.

Then close the loop on the inbox:

```bash
python3 scripts/check_inbox.py
```

Whatever is still sitting in the drop folder is what this run did *not* process. Every one of those files must appear in the report with a reason — unreadable, suspected duplicate, not a business expense. An empty inbox and a clean audit together mean nothing was lost.

Then read the run back out of the ledger — never off your own tally of the session, which will happily count a receipt that failed to commit:

```bash
python3 scripts/run_report.py --csv accounting/expenses.csv --since "$START" \
  --client "<client name>" --review-file accounting/needs-review.md
```

It returns the count, the totals by currency, the flagged rows, and the exact message for Step 8. Exit code `1` means nothing was logged. Set `$START` at the top of an on-demand run too (`--mark-start`) if you want the same read-back.

Then tell the user, in prose:

- How many receipts were processed, and the total gross and total tax by currency.
- The month folders that were written to.
- **The review list** — every `needs_review` row, with the specific reason and what you need from them to close it. This is the part they act on, so lead the summary with the count and put the detail here.
- Anything skipped, and why (unreadable, not a receipt, already in the ledger).
- Whether the Slack summary went out, and if not, why.

### Step 8 — Post the summary to the client's Slack channel (required)

**This step is part of the job, not an optional extra.** A run that filed the
receipts and wrote the ledger but never posted is an **incomplete run**, and the
person who scheduled it has no way to know it happened. The run is done when the
summary has been posted — or when its failure has been reported with a reason.

The channel ID always comes from `SLACK_CHANNEL_ID` in the `.env` at the **client
project root** — the same folder holding `accounting/`. `check_inbox.py` returned
it back in Step 0; if you no longer have it to hand, read it again:

```bash
grep -E '^(export )?SLACK_CHANNEL_ID=' .env | head -1
```

One message, one line, to that channel:

```
mcp__claude_ai_Slack__slack_send_message
  channel_id: <SLACK_CHANNEL_ID from check_inbox.py>
  text:       <the slack_message string from run_report.py, verbatim>
```

```
2 receipts processed and logged — £48.20 and $12.40 total.
```

Counts and a tax-inclusive total. **No tax line, no merchant list, no review flags** — flagged rows are your problem to close, and they belong in `needs-review.md`, not in the client's channel. Nothing was logged? Post nothing; silence on a quiet night is correct.

Then record what went out:

```bash
python3 scripts/run_report.py --csv accounting/expenses.csv --since "$START" \
  --client "<client name>" --channel "<channel id>" \
  --log accounting/receipts-notified.log --posted
```

Message rules, the missing-channel case, and what never goes in a client channel: `references/slack-summary.md`.

---

## Rules that are not negotiable

1. **Never invent a value.** A field that is not on the receipt is empty and flagged, not filled in from context.
2. **Never write a row for an image you have not viewed.**
3. **Never overwrite or rewrite `expenses.csv`.** It is append-only. If a row is wrong, fix that row in place and say what you changed.
4. **Never delete an original receipt.** Processing means *moving* it into the archive. If a move fails, the file stays where it is and the row does not get written.
5. **Never double-book.** Check the ledger before adding; a suspected duplicate stops the run for that receipt.
6. **Do not silently drop a file.** Every file the drop folder held at the start of the run ends it either as a ledger row or as a named line in the report with a reason. Never filter the folder by filename, pattern or extension — the folder is the filter, and anything loose in it is a receipt.
7. **Never post a number you did not read back out of the ledger.** The Slack total comes from `run_report.py`, not from your own count of the session.
8. **Never post to a channel you did not read out of this client's `.env`.** No guessing from the client's name, no searching Slack for a likely match.
9. **The run is not finished until the summary is posted.** Filing the receipts and writing the ledger is most of the work but not all of it. Post it, or report exactly why you could not — never end a run silently having skipped it.
10. **Never write a row when the scripts cannot run.** A row claims the original is filed at `file_path`. If `file_receipt.py` cannot execute, that claim would be false — leave the receipts in the drop folder and report the blocker. Never hand-write the CSV and never move receipts with `mv`.
11. **Never `--force` past a duplicate unattended.** On demand you would open both images and decide; on a scheduled run you cannot, so the file stays in the drop folder for a human.

## When to stop and ask

Keep going without asking for ordinary judgement calls — an uncertain category or a slightly ambiguous merchant name is what the confidence score and review flag exist for. Stop and ask only when:

- A receipt appears to already be in the ledger and it is not obvious whether it is a genuine second purchase.
- The input contains documents that are not business expenses (a personal purchase, a bank statement, a contract) — name them and ask before filing anything.
- The user's `accounting/` folder already contains an `expenses.csv` with a **different column schema**. Do not migrate it unilaterally; show them the mismatch.

On a scheduled run there is nobody to ask. Every one of those becomes *leave the file in the drop folder, flag it in `needs-review.md`, name it in the report* — and the run carries on with the remaining receipts. Never resolve a stop-and-ask by guessing just because the question cannot be asked.
