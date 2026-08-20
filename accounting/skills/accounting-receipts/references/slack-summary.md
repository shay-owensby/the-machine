# The Slack summary

One message, to one client channel, at the end of that client's run. It exists so
the client knows their receipts landed — not so they can audit them from Slack.

**Brief and concise means brief and concise.** One line. If someone wants the
detail, it is in `expenses.csv`, which is the actual deliverable.

---

## The message

```
2 receipts processed and logged — £48.20 and $12.40 total.
```

That is the whole format, and `run_report.py` builds it for you:

- **Count of receipts** logged in this run.
- **Total gross**, which is **tax-inclusive**. Tax is recorded per row in the
  ledger; it is deliberately *not* a separate line in the client message. Do not
  add "(£8.03 VAT)" — that was an explicit decision, not an oversight.
- One total **per currency** when a run spans more than one. Never add totals
  across currencies.

Do not add to it. No merchant list, no category breakdown, no per-receipt lines,
no emoji header, no "let me know if you have questions", no @-mentions. If you
find yourself wanting a second line, the answer is no.

## What never goes in the channel

**Review flags stay out of the client channel.** A row you were unsure about is
your problem to close, not theirs, and "3 receipts need review" in their channel
reads as *your* process failing in front of them. Flagged rows go to
`accounting/receipts/_processed-receipts/needs-review.md` and into the run report, where they get fixed.

Also never in the message: file paths, confidence scores, anything read out of
`.env`, and any receipt you did not successfully log.

## Getting the numbers right

Build the message from the ledger, after the receipts are filed — never from your
own running tally of the session:

```bash
python3 scripts/run_report.py \
  --csv accounting/expenses.csv --since "$START" --client "<name>" \
  --review-file accounting/receipts/_processed-receipts/needs-review.md
```

It reads back every row appended since `$START` and returns the count, the totals
by currency, the flagged rows, and the exact `slack_message` string to send.

This matters more than it looks. If a receipt failed to commit — a filesystem
error, a duplicate stop — it is not in the CSV, so it is not in the total, and the
client is told the truth. A tally you kept in your head during the run would have
counted it. **Send the `slack_message` string verbatim.**

Exit code `1` means nothing was logged. Then there is no message: **stay silent
rather than posting "0 receipts processed".** A quiet channel on a quiet night is
correct behaviour.

## Sending it

Channel ID comes from `SLACK_CHANNEL_ID` in **that client's own** `.env`, as
returned by `check_inbox.py`. Post with the Slack MCP tool:

```
mcp__claude_ai_Slack__slack_send_message
  channel_id: <SLACK_CHANNEL_ID for this client>
  text:       <the slack_message string, verbatim>
```

If `check_inbox.py` returned a `slack_note` — no `.env`, no key set, or a value
that is a channel *name* like `#accounts` rather than an ID like `C0123ABCDEF` —
**do not guess and do not search Slack for a matching channel.** Process the
receipts, skip the post, and name the client in the report so the key gets fixed
once, properly.

If the Slack connector is not available in the run (a scheduled session may not
have the interactively-authorised connector loaded), that is a reportable
failure, not a reason to find another route. Do not fall back to a webhook, a
token, or a different channel.

## Recording what was sent

After the post succeeds:

```bash
python3 scripts/run_report.py \
  --csv accounting/expenses.csv --since "$START" --client "<name>" \
  --channel "<channel id>" --log accounting/receipts/_processed-receipts/receipts-notified.log --posted
```

Same window, same numbers, now written to an append-only log. Omit `--posted` if
the send failed. Unattended messages to client channels need a record of what was
said and when — that log is it.
