#!/usr/bin/env python3
"""
Check this client's receipt drop folder, and find where to report on it.

    python3 check_inbox.py                       # from the client project root
    python3 check_inbox.py --project-root ~/clients/acme

Lists the receipts waiting in <project root>/accounting/receipts/ and reads
SLACK_CHANNEL_ID out of <project root>/.env so the run knows which channel its
summary belongs in.

The three per-client reference files are surfaced here too: `receipts.md` (this
client's filing rules), `categories.md` (this client's expense taxonomy) and
`whitelist.md` (vendors this client has already approved, which are never
written into needs-review.md). All three live in the client project, so each
client controls their own. A client with no categories.md gets one seeded from
the skill's template; a missing whitelist.md simply means nobody is whitelisted.

The accounting folders are created if they are not there. A client project
without an accounting/ folder is a new client, not an error -- scaffolding it
here means the drop folder exists before anyone is asked to drop anything in
it. Creating a directory that already exists does nothing, so this is safe to
run every night.

Files already filed under _processed-receipts/ are not pending -- that is what
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


# The folders every client project needs. `_processed-receipts/` is both the
# archive and the home for the run's own bookkeeping (needs-review.md and
# receipts-notified.log), which keeps them out of the inbox -- anything sitting
# loose in accounting/receipts/ is a receipt waiting to be processed, and a log
# file left there would be read as one.
SCAFFOLD = (
    ("accounting",),
    ("accounting", "_references"),
    ("accounting", "receipts"),
    ("accounting", "receipts", "_processed-receipts"),
)


# The expense taxonomy is per-client: each client keeps their own list at
# accounting/_references/categories.md and can add categories to it. The copy in
# assets/ is only a starting point for a client who has no list yet -- once
# seeded, the client's file is the authority and this script never touches it
# again.
CATEGORIES_TEMPLATE = Path(__file__).resolve().parent.parent / "assets" / "categories.template.md"
# Everything above this marker in the template is a note to whoever maintains the
# skill. The client receives only what is below it -- a seeded file that opens by
# calling itself a template would be telling the reader the opposite of the truth.
SEED_MARKER = "<!-- seed-from-here -->"


def scaffold(root):
    """Create the accounting tree if it is missing. Returns what was created."""
    created = []
    for parts in SCAFFOLD:
        d = root.joinpath(*parts)
        if not d.exists():
            d.mkdir(parents=True, exist_ok=True)
            created.append(str(d))
    return created


def seed_categories(categories_path):
    """Give a client with no taxonomy the default one. Never overwrites."""
    if categories_path.exists() or not CATEGORIES_TEMPLATE.is_file():
        return None
    try:
        body = CATEGORIES_TEMPLATE.read_text(encoding="utf-8")
        if SEED_MARKER in body:
            body = body.split(SEED_MARKER, 1)[1].lstrip("\n")
        categories_path.write_text(body, encoding="utf-8")
    except OSError:
        return None
    return str(categories_path)


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
    receipt awaiting processing is the _processed-receipts/ subfolder.

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
        if "_processed-receipts" in p.relative_to(inbox).parts:
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

    created = scaffold(root)
    inbox = root / "accounting" / "receipts"
    archive = inbox / "_processed-receipts"
    receipts, hidden = pending_files(inbox)
    channel, key, note = read_channel(root / ".env")

    # Surfaced here so a run cannot start without being told the rulebook exists.
    refs = root / "accounting" / "_references"
    rules = refs / "receipts.md"
    categories = refs / "categories.md"
    # Absent is a meaningful, safe answer here -- no whitelist means no vendor has
    # been pre-approved, so nothing gets waved through. That is why this one is
    # never seeded: a seeded whitelist would be an empty promise either way, and
    # inventing one would be inventing an approval the client never gave.
    whitelist = refs / "whitelist.md"
    seeded = seed_categories(categories)

    result = {
        "client": root.name,
        "project_root": str(root),
        "inbox": str(inbox),
        "archive": str(archive),
        "review_file": str(archive / "needs-review.md"),
        "notified_log": str(archive / "receipts-notified.log"),
        "created_folders": created,
        "pending_count": len(receipts),
        "pending_files": receipts,
        "hidden_files_ignored": hidden,
        "slack_channel_id": channel,
        "slack_channel_key": key,
        "slack_note": note,
        "client_rules": str(rules),
        "client_rules_exist": rules.is_file(),
        "client_categories": str(categories),
        "client_categories_seeded": seeded,
        "client_whitelist": str(whitelist),
        "client_whitelist_exists": whitelist.is_file(),
        "note": (f"All {len(receipts)} file(s) are receipts to process. This count "
                 "is the number to reconcile against at the end of the run."),
        "read_first": (
            (f"READ {rules} BEFORE EXTRACTING ANYTHING. It carries this client's "
             "standing filing rules, which override the skill's judgement calls."
             if rules.is_file() else
             f"No client rulebook at {rules} -- say so in the report and carry on.")
            + f" READ {categories} TOO: it is this client's own expense taxonomy "
              "and the category column may only contain strings from it."
            + (f" AND READ {whitelist}: those vendors are already approved by this "
               "client and never go into needs-review.md."
               if whitelist.is_file() else
               f" There is no whitelist at {whitelist} -- no vendor is pre-approved, "
               "so flag on the merits as usual.")
        ),
    }
    print(json.dumps(result, indent=2))

    if created:
        print(f"\nCreated {len(created)} folder(s) for a client that had none.",
              file=sys.stderr)
    if seeded:
        print(f"\nSeeded {seeded} from the skill's default taxonomy. It is this "
              "client's file now -- edit it there, not in the skill.", file=sys.stderr)
    if not receipts:
        print("\nNo receipts waiting. Nothing to do.", file=sys.stderr)
        return 1
    return 0


if __name__ == "__main__":
    sys.exit(main())
