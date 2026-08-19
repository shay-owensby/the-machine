#!/usr/bin/env python3
"""
Inventory and prepare receipt files so every one of them can be viewed.

    python3 prepare_receipts.py ~/Downloads/receipts --workdir /tmp/receipt-prep
    python3 prepare_receipts.py a.heic b.pdf c.jpg --workdir /tmp/receipt-prep

Walks the given files and folders, skips anything already filed under
processed-receipts/, converts formats the Read tool cannot open, downscales
oversized photos so the small print survives, counts PDF pages, and writes a
manifest.

The manifest's "view_path" is what to open with the Read tool. The "source" is
the original, and it is the source -- never the converted copy -- that gets
moved into the archive by file_receipt.py.

Stdlib only. Conversion uses macOS `sips`; without it, unconvertible formats are
reported as such rather than silently dropped.
"""

import argparse
import json
import re
import shutil
import subprocess
import sys
import tempfile
from pathlib import Path

READABLE = {".jpg", ".jpeg", ".png", ".gif"}
NEEDS_CONVERT = {".heic", ".heif", ".webp", ".tif", ".tiff", ".bmp"}
PDF = {".pdf"}
MAX_EDGE = 2400  # px on the long edge; beyond this the read gets slower, not sharper
MIN_EDGE = 700   # below this, receipt small print is usually already lost


def have(cmd):
    return shutil.which(cmd) is not None


def run(cmd):
    return subprocess.run(cmd, capture_output=True, text=True)


def pixel_size(path):
    """(width, height) via sips, or (0, 0) if unavailable."""
    if not have("sips"):
        return (0, 0)
    out = run(["sips", "-g", "pixelWidth", "-g", "pixelHeight", str(path)]).stdout
    w = re.search(r"pixelWidth:\s*(\d+)", out)
    h = re.search(r"pixelHeight:\s*(\d+)", out)
    return (int(w.group(1)) if w else 0, int(h.group(1)) if h else 0)


def pdf_page_count(path):
    """Page count without third-party libraries. Best effort, never raises."""
    if have("mdls"):
        out = run(["mdls", "-raw", "-name", "kMDItemNumberOfPages", str(path)]).stdout.strip()
        if out.isdigit() and int(out) > 0:
            return int(out)
    try:
        data = path.read_bytes()
    except OSError:
        return 1
    m = re.search(rb"/Type\s*/Pages\b[^>]*?/Count\s+(\d+)", data, re.S)
    if m:
        return max(1, int(m.group(1)))
    n = len(re.findall(rb"/Type\s*/Page(?![s/\w])", data))
    return max(1, n)


def collect(inputs, include_processed):
    """Every candidate receipt file under the given paths, de-duplicated, sorted."""
    seen, files, missing = set(), [], []
    for raw in inputs:
        p = Path(raw).expanduser()
        if not p.exists():
            missing.append(str(p))
            continue
        candidates = sorted(q for q in p.rglob("*") if q.is_file()) if p.is_dir() else [p]
        for q in candidates:
            q = q.resolve()
            if q in seen or q.name.startswith("."):
                continue
            # No extension filter. Every file handed in gets an entry, even one
            # in a format nothing here recognises -- it is reported as such and
            # accounted for, never dropped on the floor. Silently skipping a file
            # is how a receipt goes missing without anyone noticing.
            if not include_processed and "processed-receipts" in q.parts:
                continue
            seen.add(q)
            files.append(q)
    return files, missing


def prepare_one(src, outdir, index):
    """Return a manifest entry for one receipt file."""
    ext = src.suffix.lower()
    entry = {
        "index": index,
        "source": str(src),
        "view_path": str(src),
        "kind": "pdf" if ext in PDF else "image",
        "pages": 1,
        "actions": [],
        "warnings": [],
    }

    if ext in PDF:
        entry["pages"] = pdf_page_count(src)
        entry["actions"].append("read with the Read tool's `pages` parameter")
        if entry["pages"] > 1:
            entry["warnings"].append(
                f"{entry['pages']} pages -- may be one multi-page invoice or several receipts"
            )
        return entry

    if ext not in READABLE | NEEDS_CONVERT | PDF:
        entry["kind"] = "unknown"
        entry["actions"].append("unrecognised extension -- try the Read tool on it directly")
        entry["warnings"].append(
            f"unrecognised format {ext or '(no extension)'} -- this is still a file "
            "that must be accounted for: read it if you can, flag it if you cannot"
        )
        return entry

    if ext in NEEDS_CONVERT:
        if not have("sips"):
            entry["view_path"] = ""
            entry["warnings"].append(f"cannot convert {ext} -- `sips` not available")
            return entry
        dest = outdir / f"{index:03d}_{src.stem}.jpg"
        r = run(["sips", "-s", "format", "jpeg", str(src), "--out", str(dest)])
        if r.returncode != 0 or not dest.exists():
            entry["view_path"] = ""
            entry["warnings"].append(f"conversion from {ext} failed: {r.stderr.strip()[:200]}")
            return entry
        entry["view_path"] = str(dest)
        entry["actions"].append(f"converted {ext} -> .jpg for viewing")

    w, h = pixel_size(Path(entry["view_path"]))
    if max(w, h) > MAX_EDGE:
        dest = outdir / f"{index:03d}_{Path(entry['view_path']).stem}_small.jpg"
        r = run(["sips", "-Z", str(MAX_EDGE), str(entry["view_path"]), "--out", str(dest)])
        if r.returncode == 0 and dest.exists():
            entry["view_path"] = str(dest)
            entry["actions"].append(f"downscaled {w}x{h} -> long edge {MAX_EDGE}")
    elif 0 < max(w, h) < MIN_EDGE:
        entry["warnings"].append(
            f"low resolution ({w}x{h}) -- small print may be unreadable; expect a review flag"
        )
    return entry


def main():
    ap = argparse.ArgumentParser(description="Prepare receipt files for viewing.")
    ap.add_argument("inputs", nargs="+", help="Receipt files and/or folders")
    ap.add_argument("--workdir", help="Where converted copies go (default: a temp dir)")
    ap.add_argument("--include-processed", action="store_true",
                    help="Do not skip files already under processed-receipts/")
    args = ap.parse_args()

    outdir = Path(args.workdir).expanduser() if args.workdir else Path(tempfile.mkdtemp(prefix="receipt-prep-"))
    outdir.mkdir(parents=True, exist_ok=True)

    files, missing = collect(args.inputs, args.include_processed)
    entries = [prepare_one(f, outdir, i) for i, f in enumerate(files, 1)]

    result = {
        "workdir": str(outdir),
        "found": len(entries),
        "missing_inputs": missing,
        "unreadable": [e["source"] for e in entries if not e["view_path"]],
        "unrecognised_format": [e["source"] for e in entries if e["kind"] == "unknown"],
        "receipts": entries,
        "note": (f"{len(entries)} file(s) found. Every one must end the run either "
                 "written to the ledger or named in the report with a reason. "
                 "Nothing here was filtered by filename."),
    }
    (outdir / "manifest.json").write_text(json.dumps(result, indent=2))
    print(json.dumps(result, indent=2))

    if missing:
        print(f"\nWARNING: {len(missing)} input path(s) did not exist.", file=sys.stderr)
    if not entries:
        print("\nNo receipt files found. Nothing to process.", file=sys.stderr)
        return 1
    return 0


if __name__ == "__main__":
    sys.exit(main())
