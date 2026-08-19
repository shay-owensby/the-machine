#!/usr/bin/env python3
"""
Commit one processed receipt: move the original into the month archive, then
append its row to the expense ledger.

    python3 file_receipt.py \
      --csv accounting/expenses.csv \
      --receipts-root accounting/receipts/processed-receipts \
      --source ~/Downloads/IMG_1234.jpg \
      --merchant "Shell Service Station" --date 2026-03-14 --currency GBP \
      --gross 48.20 --tax 8.03 --receipt-number "A-99231" \
      --category "Fuel & Mileage" --confidence 0.94

    python3 file_receipt.py --audit --csv <csv> --receipts-root <root>

Owns everything that has to be deterministic: arithmetic re-checks, duplicate
detection, the YYYYMM_MonthName folder, collision-safe filenames, CSV quoting,
and rollback if the append fails after the move.

Exit codes: 0 written, 2 bad input, 3 suspected duplicate, 4 filesystem failure.
Stdlib only.
"""

import argparse
import csv
import json
import os
import re
import shutil
import sys
from datetime import datetime, date
from decimal import Decimal, InvalidOperation
from pathlib import Path

COLUMNS = [
    "merchant", "purchase_date", "currency", "gross_amount", "tax_amount",
    "net_amount", "receipt_number", "category", "confidence", "needs_review",
    "review_notes", "file_path", "processed_at",
]

MONTHS = ["January", "February", "March", "April", "May", "June",
          "July", "August", "September", "October", "November", "December"]

TOLERANCE = Decimal("0.011")  # a cent, plus room for float noise


def fail(msg, code=2):
    print(f"ERROR: {msg}", file=sys.stderr)
    sys.exit(code)


def money(raw, field):
    """'£1,234.56' -> Decimal('1234.56'). Rejects anything that isn't a number."""
    if raw is None or str(raw).strip() == "":
        return None
    s = re.sub(r"[^\d.\-]", "", str(raw).strip())
    if s in ("", "-", "."):
        fail(f"--{field} is not a number: {raw!r}")
    try:
        return Decimal(s).quantize(Decimal("0.01"))
    except InvalidOperation:
        fail(f"--{field} is not a number: {raw!r}")


def parse_date(raw):
    try:
        return date.fromisoformat(raw.strip())
    except ValueError:
        fail(f"--date must be ISO YYYY-MM-DD (resolve the format before calling this): {raw!r}")


def slug(text, limit=40):
    s = re.sub(r"[^a-z0-9]+", "-", str(text).lower()).strip("-")
    return (s[:limit].rstrip("-")) or "unknown"


def norm_merchant(text):
    return re.sub(r"[^a-z0-9]", "", str(text).lower())


def read_rows(csv_path):
    if not csv_path.exists():
        return []
    with csv_path.open(newline="", encoding="utf-8") as fh:
        return list(csv.DictReader(fh))


def check_schema(csv_path):
    if not csv_path.exists():
        return
    with csv_path.open(newline="", encoding="utf-8") as fh:
        header = next(csv.reader(fh), None)
    if header and header != COLUMNS:
        fail(
            "existing CSV has a different column schema -- refusing to append.\n"
            f"  found:    {header}\n"
            f"  expected: {COLUMNS}\n"
            "Show the user the mismatch; do not migrate the file unilaterally.",
            code=2,
        )


def find_duplicate(rows, merchant, iso_date, gross, receipt_number):
    m = norm_merchant(merchant)
    num = (receipt_number or "").strip().lower()
    for i, r in enumerate(rows, start=2):  # +2: header is line 1
        same_merchant = norm_merchant(r.get("merchant", "")) == m
        if num and same_merchant and (r.get("receipt_number", "") or "").strip().lower() == num:
            return i, r, "same receipt number from the same merchant"
        if same_merchant and r.get("purchase_date", "") == iso_date:
            try:
                if Decimal(r.get("gross_amount") or "0") == gross:
                    return i, r, "same merchant, date and gross amount"
            except InvalidOperation:
                continue
    return None


def unique_destination(folder, stem, suffix):
    dest = folder / f"{stem}{suffix}"
    n = 2
    while dest.exists():
        dest = folder / f"{stem}-{n}{suffix}"
        n += 1
    return dest


def relative_to_cwd(path):
    try:
        return str(path.resolve().relative_to(Path.cwd().resolve()))
    except ValueError:
        return str(path.resolve())


def audit(csv_path, receipts_root):
    rows = read_rows(csv_path)
    missing = [
        {"line": i, "merchant": r.get("merchant"), "file_path": r.get("file_path")}
        for i, r in enumerate(rows, start=2)
        if not (r.get("file_path") and Path(r["file_path"]).exists())
    ]
    booked = {Path(r["file_path"]).resolve() for r in rows if r.get("file_path")}
    orphans = []
    if receipts_root.exists():
        orphans = [
            str(p) for p in sorted(receipts_root.rglob("*"))
            if p.is_file() and not p.name.startswith(".") and p.resolve() not in booked
        ]
    result = {
        "rows": len(rows),
        "missing_files": missing,
        "orphan_files": orphans,
        "clean": not missing and not orphans,
    }
    print(json.dumps(result, indent=2))
    return 0 if result["clean"] else 1


def main():
    ap = argparse.ArgumentParser(description="File one receipt and record it in the ledger.")
    ap.add_argument("--csv", required=True)
    ap.add_argument("--receipts-root", required=True)
    ap.add_argument("--audit", action="store_true", help="Reconcile ledger against archive and exit")

    ap.add_argument("--source", help="The ORIGINAL receipt file to archive")
    ap.add_argument("--merchant")
    ap.add_argument("--date", help="Transaction date, ISO YYYY-MM-DD")
    ap.add_argument("--currency", default="GBP")
    ap.add_argument("--gross", help="Amount charged, tax included (negative for a refund)")
    ap.add_argument("--tax", default="0.00", help="VAT/GST contained in gross")
    ap.add_argument("--net", help="Optional cross-check; defaults to gross - tax")
    ap.add_argument("--receipt-number", default="")
    ap.add_argument("--category", required=False, default="Uncategorised")
    ap.add_argument("--confidence", default="0.00")
    ap.add_argument("--needs-review", action="store_true")
    ap.add_argument("--review-notes", default="")
    ap.add_argument("--dry-run", action="store_true", help="Show what would happen; move nothing")
    ap.add_argument("--force", action="store_true", help="Proceed despite a suspected duplicate")
    args = ap.parse_args()

    csv_path = Path(args.csv).expanduser()
    receipts_root = Path(args.receipts_root).expanduser()

    if args.audit:
        sys.exit(audit(csv_path, receipts_root))

    check_schema(csv_path)  # a schema mismatch is a stop-and-ask, so check it first

    for required in ("source", "merchant", "date", "gross"):
        if not getattr(args, required):
            fail(f"--{required} is required (or pass --audit)")

    src = Path(args.source).expanduser()
    if not src.is_file():
        fail(f"source file not found: {src}", code=4)

    d = parse_date(args.date)
    gross = money(args.gross, "gross")
    tax = money(args.tax, "tax") or Decimal("0.00")
    net = money(args.net, "net")

    if gross is None:
        fail("--gross is required")
    if net is None:
        net = (gross - tax).quantize(Decimal("0.01"))
    elif abs((gross - tax) - net) > TOLERANCE:
        fail(
            f"arithmetic does not reconcile: gross {gross} - tax {tax} = {gross - tax}, "
            f"but --net says {net}. Re-read the receipt; one of the three is wrong.",
            code=2,
        )
    if gross >= 0 and tax > gross:
        fail(f"tax {tax} exceeds gross {gross} -- one of them was misread.", code=2)

    try:
        conf = Decimal(str(args.confidence)).quantize(Decimal("0.01"))
    except InvalidOperation:
        fail(f"--confidence is not a number: {args.confidence!r}")
    if not (Decimal("0") <= conf <= Decimal("1")):
        fail("--confidence must be between 0.00 and 1.00")

    needs_review = args.needs_review or conf < Decimal("0.70")
    if needs_review and not args.review_notes.strip():
        fail("--review-notes is required whenever a row is flagged for review "
             "(a flag with no reason makes the user re-open every image)")

    rows = read_rows(csv_path)
    dup = find_duplicate(rows, args.merchant, d.isoformat(), gross, args.receipt_number)
    if dup and not args.force:
        line, row, why = dup
        print(
            f"SUSPECTED DUPLICATE ({why}).\n"
            f"  existing line {line}: {row.get('purchase_date')} {row.get('merchant')} "
            f"{row.get('currency')} {row.get('gross_amount')} -> {row.get('file_path')}\n"
            "Look at both images before deciding. If they really are two separate "
            "purchases, re-run with --force and explain in --review-notes.",
            file=sys.stderr,
        )
        sys.exit(3)

    folder = receipts_root / f"{d.year}{d.month:02d}_{MONTHS[d.month - 1]}"
    stem = f"{d.isoformat()}_{slug(args.merchant)}_{gross}"
    notes = args.review_notes.strip()
    if dup and args.force:
        notes = (notes + f" [forced past suspected duplicate of line {dup[0]}]").strip()

    # Re-filing an orphan already sitting in the right archive folder must not
    # rename it into a "-2" copy -- it is the same receipt, just unrecorded.
    already_filed = (
        src.parent.resolve() == folder.resolve() and src.stem.startswith(stem)
    )

    if args.dry_run:
        planned = src if already_filed else unique_destination(folder, stem, src.suffix.lower())
        print(json.dumps({
            "dry_run": True,
            "would_move_to": str(planned),
            "already_in_place": already_filed,
            "duplicate_of_line": dup[0] if dup else None,
            "net_amount": str(net),
            "needs_review": "yes" if needs_review else "no",
        }, indent=2))
        return 0

    try:
        folder.mkdir(parents=True, exist_ok=True)
        dest = src if already_filed else unique_destination(folder, stem, src.suffix.lower())
        moved = not already_filed
        if moved:
            shutil.move(str(src), str(dest))
    except OSError as e:
        fail(f"could not file the receipt: {e}", code=4)

    row = {
        "merchant": args.merchant.strip(),
        "purchase_date": d.isoformat(),
        "currency": args.currency.strip().upper(),
        "gross_amount": f"{gross:.2f}",
        "tax_amount": f"{tax:.2f}",
        "net_amount": f"{net:.2f}",
        "receipt_number": args.receipt_number.strip(),
        "category": args.category.strip(),
        "confidence": f"{conf:.2f}",
        "needs_review": "yes" if needs_review else "no",
        "review_notes": notes,
        "file_path": relative_to_cwd(dest),
        "processed_at": datetime.now().replace(microsecond=0).isoformat(),
    }

    try:
        csv_path.parent.mkdir(parents=True, exist_ok=True)
        new_file = not csv_path.exists() or csv_path.stat().st_size == 0
        with csv_path.open("a", newline="", encoding="utf-8") as fh:
            w = csv.DictWriter(fh, fieldnames=COLUMNS)
            if new_file:
                w.writeheader()
            w.writerow(row)
    except OSError as e:
        if moved:
            shutil.move(str(dest), str(src))  # ledger is the record; don't strand the file
        fail(f"could not append to the ledger (receipt returned to {src}): {e}", code=4)

    print(json.dumps({"written": True, **row}, indent=2))
    return 0


if __name__ == "__main__":
    sys.exit(main())
