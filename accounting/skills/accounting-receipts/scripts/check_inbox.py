#!/usr/bin/env python3
"""
Check this client's receipt drop folder, and find where to report on it.

    python3 check_inbox.py                       # from the client project root
    python3 check_inbox.py --project-root ~/clients/acme

Lists the receipts waiting in <project root>/accounting/receipts/ and reads
SLACK_CHANNEL_ID out of <project root>/.env so the run knows which channel its
summary belongs in.

Files already filed under processed-receipts/ are not pending -- that is what
makes a scheduled run idempotent: an empty inbox means no work, no ledger row
and no Slack message.

Only the Slack channel key is ever read out of .env. No other secret in that
file is parsed, printed, or returned.

Exit codes: 0 receipts are waiting, 1 nothing pending, 2 bad input. Stdlib only.
"""

import argparse
import json
import re
import sys
from pathlib import Path

# EVERY file in the drop folder is a receipt. These sets do not decide what gets
# processed -- they only say how a file will need to be opened. A format nobody
# recognises is still a receipt waiting to be read, not a file to skip.
DIRECTLY_READABLE = {".jpg", ".jpeg", ".png", ".gif"}
NEEDS_CONVERSION = {".heic", ".heif", ".webp", ".tif", ".tiff", ".bmp"}
PDF = {".pdf"}

CHANNEL_KEYS = ("SLACK_CHANNEL_ID", "SLACK_CHANNEL")
CHANNEL_RE = re.compile(r"^[CGD][A-Z0-9]{6,}$")


def read_channel(env_path):
    """(channel_id, key_used, note). Reads only the Slack channel keys."""
    if not env_path.is_file():
        return None, None, "no .env in the project root"
    try:
        text = env_path.read_text(encoding="utf-8", errors="replace")
    except OSError as e:
        return None, None, f"could not read .env: {e}"

    found = {}
    for line in text.splitlines():
        line = line.strip()
        if not line or line.startswith("#"):
            continue
        if line.startswith("export "):
            line = line[7:].lstrip()
        key, sep, value = line.partition("=")
        if not sep:
            continue
        key = key.strip()
        if key not in CHANNEL_KEYS:
            continue
        value = value.split(" #")[0].strip().strip("'\"").strip()
        if value:
            found[key] = value

    for key in CHANNEL_KEYS:
        if key in found:
            value = found[key]
            note = None
            if not CHANNEL_RE.match(value):
                note = (f"{key} is {value!r}, which is not a channel ID "
                        "(IDs look like C0123ABCDEF) -- resolve it before posting")
            return value, key, note
    return None, None, f"none of {'/'.join(CHANNEL_KEYS)} set in .env"


def classify(path):
    """How this file will need to be opened. Never whether to open it."""
    ext = path.suffix.lower()
    if ext in PDF:
        return "pdf"
    if ext in DIRECTLY_READABLE:
        return "image"
    if ext in NEEDS_CONVERSION:
        return "needs conversion"
    return "unrecognised format -- still a receipt, still must be read"


def pending_files(inbox):
    """EVERY file in the drop folder. No filtering by name, extension or anything
    else: the folder is the filter, and the only thing in it that is not a
    receipt awaiting processing is the processed-receipts/ subfolder.

    Hidden files (.DS_Store and friends) are OS clutter, not uploads, so they are
    listed separately rather than counted as receipts -- but they are still
    listed, because nothing here disappears without being named.
    """
    receipts, hidden = [], []
    if not inbox.is_dir():
        return receipts, hidden
    for p in sorted(inbox.rglob("*")):
        if not p.is_file():
            continue
        if "processed-receipts" in p.relative_to(inbox).parts:
            continue
        if p.name.startswith("."):
            hidden.append(str(p))
            continue
        receipts.append({"path": str(p), "name": p.name, "open_as": classify(p)})
    return receipts, hidden


def main():
    ap = argparse.ArgumentParser(description="Check this client's receipt drop folder.")
    ap.add_argument("--project-root", default=".",
                    help="Client project root (default: the working directory)")
    args = ap.parse_args()

    root = Path(args.project_root).expanduser().resolve()
    if not root.is_dir():
        print(f"ERROR: not a directory: {root}", file=sys.stderr)
        return 2

    inbox = root / "accounting" / "receipts"
    receipts, hidden = pending_files(inbox)
    channel, key, note = read_channel(root / ".env")

    result = {
        "client": root.name,
        "project_root": str(root),
        "inbox": str(inbox),
        "inbox_exists": inbox.is_dir(),
        "pending_count": len(receipts),
        "pending_files": receipts,
        "hidden_files_ignored": hidden,
        "slack_channel_id": channel,
        "slack_channel_key": key,
        "slack_note": note,
        "note": (f"All {len(receipts)} file(s) are receipts to process. This count "
                 "is the number to reconcile against at the end of the run."),
    }
    print(json.dumps(result, indent=2))

    if not inbox.is_dir():
        print(f"\nNo drop folder at {inbox} -- nothing to process.", file=sys.stderr)
        return 1
    if not receipts:
        print("\nNo receipts waiting. Nothing to do.", file=sys.stderr)
        return 1
    return 0


if __name__ == "__main__":
    sys.exit(main())
