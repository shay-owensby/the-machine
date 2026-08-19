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

# Same set prepare_receipts.py will accept; anything else in the drop folder is
# reported as ignored rather than silently swallowed.
RECEIPT_EXTS = {
    ".jpg", ".jpeg", ".png", ".gif", ".pdf",
    ".heic", ".heif", ".webp", ".tif", ".tiff", ".bmp",
}

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


def pending_files(inbox):
    """Loose receipts in the drop folder, plus anything there that is not one."""
    receipts, ignored = [], []
    if not inbox.is_dir():
        return receipts, ignored
    for p in sorted(inbox.rglob("*")):
        if not p.is_file() or p.name.startswith("."):
            continue
        if "processed-receipts" in p.relative_to(inbox).parts:
            continue
        (receipts if p.suffix.lower() in RECEIPT_EXTS else ignored).append(str(p))
    return receipts, ignored


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
    receipts, ignored = pending_files(inbox)
    channel, key, note = read_channel(root / ".env")

    result = {
        "client": root.name,
        "project_root": str(root),
        "inbox": str(inbox),
        "inbox_exists": inbox.is_dir(),
        "pending_count": len(receipts),
        "pending_files": receipts,
        "ignored_files": ignored,
        "slack_channel_id": channel,
        "slack_channel_key": key,
        "slack_note": note,
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
