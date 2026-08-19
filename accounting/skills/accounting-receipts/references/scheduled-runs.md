# The scheduled run

The skill runs in two modes. Everything about reading a receipt is identical in
both — the difference is only in how work arrives and who hears about it.

**On demand.** The user hands over files or a folder. You process them, you
report in prose, they are sitting right there to answer questions.

**Scheduled.** Nothing is handed over. Each client has their own scheduled task,
running in that client's project directory, that wakes you up to deal with
whatever has been dropped in their folder since last time. Nobody is watching.
That changes three things: the drop folder is the only input, the client's Slack
channel is the only output, and there is no one to answer a question mid-run.
What you would have asked about gets flagged and left for the morning instead.

**One task, one client.** A scheduled run never reaches outside the project root
it was started in. It does not look for other clients, it does not read another
client's folder, and it does not post anywhere but the channel in the `.env`
beside it.

---

## The drop folder

```
<client project root>/
  .env                                        SLACK_CHANNEL_ID lives here
  accounting/
    expenses.csv                              the ledger
    needs-review.md                           what the run could not resolve
    receipts-notified.log                     one JSON line per Slack post
    receipts/                                 <- THE DROP FOLDER. Upload here.
      IMG_4471.HEIC
      invoice-march.pdf
      processed-receipts/
        202603_March/                         <- filed originals land here
```

**Loose files in `accounting/receipts/` are the inbox — all of them.** Anything
under `processed-receipts/` has already been done and is invisible to the next
run. That subfolder is the *only* thing in there that is not work.

So the folder is the filter, and nothing else gets a vote. Do not glob for
`*receipt*`, do not judge a file by its extension, do not skip `08capcut.pdf`
because it does not look like a receipt — it is in the folder, so it is a
receipt. Take the list from `check_inbox.py` rather than listing the directory
yourself, and reconcile against its `pending_count` at the end of the run.

This is what makes the task safe to run every night: processing a receipt *moves*
it out of the inbox, so the next run finds nothing and does nothing. There is no
state file to corrupt and no "last run" timestamp to get wrong. **An empty inbox
means no work, no ledger row, and no Slack message.**

Never "tidy" the drop folder by deleting things out of it. A file only leaves the
inbox by being filed into `processed-receipts/`, and only `file_receipt.py` does
that.

## Starting the run

```bash
python3 scripts/check_inbox.py
```

Run from the client project root. It returns the receipts waiting, anything in
the folder that is not a receipt, and the `SLACK_CHANNEL_ID` from that client's
`.env`. Exit code `1` means the inbox is empty — a normal, quiet night. Say so in
one line and stop; do not go hunting for work elsewhere.

The check reads **only** the Slack channel key out of `.env`. Every other value
in that file is a secret that has nothing to do with receipts: do not read it, do
not echo it, and never let one reach a Slack message or a run report.

**Everything is relative to the client project root, so stay in it.** Every
`accounting/…` path in this skill resolves from the working directory, and
`file_receipt.py` records `file_path` relative to it too. If a task is ever
pointed at the wrong folder, `file_receipt.py` catches it: before moving
anything, it checks that the receipt, the ledger and the archive all belong to
the same project, and exits `2` if they do not. A misconfigured task fails loudly
on its first receipt instead of quietly writing into the wrong client's books.

Mark the start before processing anything; the report needs it:

```bash
START=$(python3 scripts/run_report.py --mark-start)
```

## When something goes wrong

A failure on one receipt is not a failure of the run. Record it, finish the rest,
and name every failure in the final report.

| What happened | What to do |
|---|---|
| A receipt is unreadable | Leave it in the drop folder, do not file it, note it in `needs-review.md`. It will be picked up again next run — that is fine and intended. |
| `file_receipt.py` exits `3` (duplicate) | Leave that file in the drop folder. **Never `--force` unattended.** Log it for a human. |
| Arithmetic will not reconcile | Go back to the image once. If it still will not, leave the file in the inbox and flag it. Do not "fix" it with a guess. |
| No `SLACK_CHANNEL_ID` in `.env` | Still process the receipts — the ledger is the point. Skip the post and say so in the report, so the key gets added. |
| The Slack post fails | The ledger is already correct and stays that way. Log the failure with `--log` (without `--posted`) and report it. Do not re-run the processing to "retry" — the inbox is already empty, so there is nothing to reprocess. |
| A file in the drop folder is not a receipt | Leave it where it is and name it. A bank statement or a signed contract does not go in the expense ledger and does not get quietly filed. |
| The scripts will not run at all | Stop. Write no rows. See "When the scripts cannot run" below. |

## When the scripts cannot run

If `python3` is unavailable, the sandbox is down, the disk is full, or
`file_receipt.py` fails for an environmental reason, the run is **blocked, not
degraded**. Do not work around it:

- **Do not hand-write rows into `expenses.csv`.** A row is a claim that the
  original has been filed at `file_path`. Writing one while the move cannot
  happen makes that claim false, and the Step 7 audit will report a ledger
  pointing at files that are not there.
- **Do not move receipts by hand** with `mv` or `cp`. The destination folder,
  the collision-safe name, the duplicate check and the arithmetic re-check all
  live in the script.
- **Do not post to Slack.** Nothing was logged, so there is nothing to summarise.

Leave the receipts in the drop folder, report the failure and its actual cause,
and let the next run pick them up once the environment is fixed. Nothing is lost:
the inbox is the queue.

## What is not allowed to happen unattended

The whole point of a scheduled run is that it is trustworthy without supervision.
That buys a stricter rule set than an on-demand run:

- **Never `--force` past a suspected duplicate.** On demand you would open both
  images and decide. Unattended, you cannot — so the answer is always "leave it".
- **Never invent a value to avoid a review flag.** A flagged row costs someone ten
  seconds in the morning. A wrong row costs them a corrected tax return.
- **Never post to a channel you did not read out of this client's own `.env`.**
- **Never post a total you did not read back out of the ledger.** See
  `slack-summary.md`.
