#!/usr/bin/env python3
"""
Summarise what one run actually logged, and build the Slack message from it.

    START=$(python3 run_report.py --mark-start)
    ... process the receipts ...
    python3 run_report.py --csv accounting/expenses.csv --since "$START" \
        --review-file accounting/receipts/_processed-receipts/needs-review.md

    # after the Slack post has gone out:
    python3 run_report.py --csv accounting/expenses.csv --since "$START" \
        --log accounting/receipts/_processed-receipts/receipts-notified.log --channel C0123ABCDEF --posted

The numbers in the Slack message come out of the ledger, never out of the
model's memory of the run. If a receipt failed to commit it is not in the CSV,
so it is not in the total -- which is the whole point of reading it back.

Totals are gross, tax included. Tax is recorded per row in the ledger but is
deliberately not broken out in the client-facing summary.

Exit codes: 0 rows were logged, 1 nothing logged in the window, 2 bad input.
Stdlib only.
"""

import argparse
import csv
import json
import sys
from datetime import datetime
from decimal import Decimal, InvalidOperation
from pathlib import Path

SYMBOLS = {"GBP": "£", "USD": "$", "EUR": "€", "JPY": "¥", "CAD": "CA$", "AUD": "A$"}


def fail(msg):
    print(f"ERROR: {msg}", file=sys.stderr)
    sys.exit(2)


def now_stamp():
    return datetime.now().replace(microsecond=0).isoformat()


def amount(currency, total):
    sym = SYMBOLS.get(currency.upper())
    return f"{sym}{total:,.2f}" if sym else f"{total:,.2f} {currency.upper()}"


def join(parts):
    if len(parts) <= 1:
        return "".join(parts)
    return f"{', '.join(parts[:-1])} and {parts[-1]}"


def rows_since(csv_path, since):
    if not csv_path.is_file():
        fail(f"ledger not found: {csv_path}")
    with csv_path.open(newline="", encoding="utf-8") as fh:
        rows = list(csv.DictReader(fh))
    out = []
    for r in rows:
        stamp = (r.get("processed_at") or "").strip()
        if not stamp:
            continue
        try:
            if datetime.fromisoformat(stamp) >= since:
                out.append(r)
        except ValueError:
            continue
    return out


def totals_by_currency(rows):
    totals = {}
    for r in rows:
        cur = (r.get("currency") or "").strip().upper() or "???"
        try:
            totals[cur] = totals.get(cur, Decimal("0.00")) + Decimal(r.get("gross_amount") or "0")
        except InvalidOperation:
            continue
    return totals


def build_message(rows, totals):
    n = len(rows)
    noun = "receipt" if n == 1 else "receipts"
    money = join([amount(cur, totals[cur]) for cur in sorted(totals)])
    return f"{n} {noun} processed and logged — {money} total."


def write_review_file(path, rows, stamp):
    flagged = [r for r in rows if (r.get("needs_review") or "").strip().lower() == "yes"]
    if not flagged:
        return 0
    path.parent.mkdir(parents=True, exist_ok=True)
    new_file = not path.exists() or path.stat().st_size == 0
    with path.open("a", encoding="utf-8") as fh:
        if new_file:
            fh.write("# Receipts needing review\n\n"
                     "Rows the automated run could not resolve on its own. "
                     "Fix the row in `accounting/expenses.csv`, then delete the entry here.\n")
        fh.write(f"\n## Run {stamp}\n\n")
        for r in flagged:
            fh.write(
                f"- **{r.get('merchant') or 'unknown merchant'}** "
                f"{r.get('purchase_date') or 'no date'} "
                f"{r.get('currency') or ''} {r.get('gross_amount') or '?'} "
                f"(confidence {r.get('confidence') or '?'})\n"
                f"  - {r.get('review_notes') or 'no reason recorded'}\n"
                f"  - `{r.get('file_path') or 'no file path'}`\n"
            )
    return len(flagged)


def main():
    ap = argparse.ArgumentParser(description="Summarise one run and build its Slack message.")
    ap.add_argument("--mark-start", action="store_true",
                    help="Print a timestamp to pass back as --since, then exit")
    ap.add_argument("--csv", help="Path to expenses.csv")
    ap.add_argument("--since", help="Only count rows processed at or after this ISO timestamp")
    ap.add_argument("--client", default="", help="Client name, for the log entry")
    ap.add_argument("--channel", default="", help="Slack channel ID, for the log entry")
    ap.add_argument("--review-file", help="Append this run's flagged rows to this markdown file")
    ap.add_argument("--log", help="Append a JSON line recording this summary")
    ap.add_argument("--posted", action="store_true", help="Record the Slack post as sent")
    args = ap.parse_args()

    if args.mark_start:
        print(now_stamp())
        return 0

    if not args.csv or not args.since:
        fail("--csv and --since are both required (or pass --mark-start)")
    try:
        since = datetime.fromisoformat(args.since.strip())
    except ValueError:
        fail(f"--since must be an ISO timestamp, got {args.since!r}")

    csv_path = Path(args.csv).expanduser()
    rows = rows_since(csv_path, since)
    totals = totals_by_currency(rows)
    stamp = now_stamp()

    flagged = [r for r in rows if (r.get("needs_review") or "").strip().lower() == "yes"]
    result = {
        "client": args.client,
        "since": since.isoformat(),
        "generated_at": stamp,
        "receipts_logged": len(rows),
        "totals": {cur: f"{total:.2f}" for cur, total in sorted(totals.items())},
        "needs_review_count": len(flagged),
        "needs_review": [
            {
                "merchant": r.get("merchant"),
                "purchase_date": r.get("purchase_date"),
                "gross_amount": r.get("gross_amount"),
                "confidence": r.get("confidence"),
                "review_notes": r.get("review_notes"),
                "file_path": r.get("file_path"),
            }
            for r in flagged
        ],
        "slack_message": build_message(rows, totals) if rows else "",
        "post_to_slack": bool(rows),
    }

    if args.review_file and rows:
        result["review_file_entries"] = write_review_file(
            Path(args.review_file).expanduser(), rows, stamp)

    if args.log:
        log_path = Path(args.log).expanduser()
        log_path.parent.mkdir(parents=True, exist_ok=True)
        with log_path.open("a", encoding="utf-8") as fh:
            fh.write(json.dumps({
                "at": stamp,
                "client": args.client,
                "channel": args.channel,
                "receipts_logged": result["receipts_logged"],
                "totals": result["totals"],
                "needs_review_count": result["needs_review_count"],
                "message": result["slack_message"],
                "posted": bool(args.posted),
            }) + "\n")

    print(json.dumps(result, indent=2))

    if not rows:
        print("\nNothing was logged in this window. Do not post to Slack.", file=sys.stderr)
        return 1
    return 0


if __name__ == "__main__":
    sys.exit(main())
