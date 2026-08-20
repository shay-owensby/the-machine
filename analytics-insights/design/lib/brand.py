"""Per-client accent resolution.

A report is for a client, so it carries the client's colour. It does not carry
the client's *data* colour: the categorical and verdict palettes in tokens.py
are fixed for every client, because the same chart must mean the same thing in
two reports read by two people, and because a brand colour is chosen for a logo
rather than for separability under deuteranopia.

What the accent touches is listed in DESIGN.md and is short: the masthead rule,
the section markers, links, and the one emphasised figure. Nothing that encodes
a number.

Resolution order
----------------
1. An explicit ``--accent`` on the command line.
2. ``analytics-insights/brand.json`` in the client project.
3. Candidates extracted from ``_context/DESIGN.md`` — *offered*, never applied
   silently. A wrong accent is a report that looks like another company's.
4. The plugin default (Linear indigo).

Any accent that fails 4.5:1 as text on the report surface is darkened along
CIELAB L* until it passes, preserving hue and chroma. The client's blue stays
their blue; it stops being illegible.
"""

import argparse
import json
import os
import re
import sys

try:
    from . import color as _c
    from . import tokens as _t
except ImportError:
    sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
    import color as _c
    import tokens as _t


BRAND_FILE = os.path.join("analytics-insights", "brand.json")
DESIGN_FILE = os.path.join("_context", "DESIGN.md")

# Words near a hex value that suggest it is the brand's primary colour.
_PRIMARY_HINTS = (
    "core brand", "main brand", "primary brand", "brand color", "brand colour",
    "primary 500", "primary", "brand", "core",
)
# Words that disqualify a hex from being the accent.
_REJECT_HINTS = (
    "background", "surface", "body text", "border", "neutral", "gray", "grey",
    "white", "black", "error", "danger", "success", "warning", "muted",
    "placeholder", "disabled", "shadow", "overlay",
)

_HEX_RE = re.compile(r"#(?:[0-9a-fA-F]{3}|[0-9a-fA-F]{6})\b")


class Brand(object):
    """A resolved accent, plus the provenance that produced it."""

    def __init__(self, accent, source, raw=None, client=None, note=None):
        self.raw = _c.normalise_hex(raw or accent)
        self.source = source
        self.client = client
        self.note = note
        self.accent = _c.adjust_to_contrast(self.raw, _t.SURFACE,
                                            _t.CONTRAST_FLOOR_TEXT)
        self.adjusted = self.accent != self.raw
        # Strong: a further step down for hover and for the masthead rule.
        self.accent_strong = _c.adjust_to_contrast(self.accent, _t.SURFACE, 7.0)
        # Subtle: a tint that keeps ink at full contrast when set on it.
        self.accent_subtle = _c.mix(_t.SURFACE, self.raw, 0.08)

    @property
    def contrast(self):
        return _c.contrast_ratio(self.accent, _t.SURFACE)

    def tokens(self):
        return {
            "accent": self.accent,
            "accent-strong": self.accent_strong,
            "accent-subtle": self.accent_subtle,
        }

    def to_dict(self):
        return {
            "client": self.client,
            "accent": self.raw,
            "resolved": self.tokens(),
            "source": self.source,
            "contrast_on_surface": round(self.contrast, 2),
            "adjusted_for_contrast": self.adjusted,
            "note": self.note,
        }

    def describe(self):
        out = ["accent      %s   (%s)" % (self.accent, self.source)]
        if self.adjusted:
            out.append("            darkened from %s to reach %.2f:1 on %s "
                       "(hue and chroma preserved)"
                       % (self.raw, self.contrast, _t.SURFACE))
        else:
            out.append("            %.2f:1 on %s, used as given"
                       % (self.contrast, _t.SURFACE))
        out.append("strong      %s" % self.accent_strong)
        out.append("subtle      %s" % self.accent_subtle)
        return "\n".join(out)


def default():
    return Brand(_t.ACCENT, source="plugin default (Linear indigo)")


# --------------------------------------------------------------------------
# Extraction from a client DESIGN.md
# --------------------------------------------------------------------------

def extract_candidates(text, limit=6):
    """Find plausible accent colours in a free-form DESIGN.md.

    Client DESIGN.md files are prose with tables, written by a different skill
    and never to a fixed schema, so this scores rather than parses. It returns
    an ordered list of ``{hex, context, score}`` for a human or an agent to
    choose from. It deliberately does not pick one.
    """
    found = {}
    for line in text.splitlines():
        for m in _HEX_RE.finditer(line):
            try:
                hexv = _c.normalise_hex(m.group(0))
            except ValueError:
                continue
            context = line.strip()
            low = context.lower()

            score = 0.0
            for i, hint in enumerate(_PRIMARY_HINTS):
                if hint in low:
                    score += 10.0 - i * 0.5
                    break
            if any(bad in low for bad in _REJECT_HINTS):
                score -= 8.0
            if "**" in context and hexv in context:
                score += 2.0        # bolded rows are the emphasised ones

            # A usable accent has some chroma and is not near-white or near-black.
            L, a, b = _c.rgb_to_lab(hexv)
            chroma = (a * a + b * b) ** 0.5
            if chroma < 8:
                score -= 6.0        # a grey cannot be an accent
            if L > 92 or L < 12:
                score -= 6.0

            prev = found.get(hexv)
            if prev is None or score > prev["score"]:
                found[hexv] = {"hex": hexv, "context": context[:120],
                               "score": round(score, 1)}

    ranked = sorted(found.values(), key=lambda d: (-d["score"], d["hex"]))
    return ranked[:limit]


# --------------------------------------------------------------------------
# Project resolution
# --------------------------------------------------------------------------

def _read(path):
    try:
        with open(path, "r", encoding="utf-8") as fh:
            return fh.read()
    except (IOError, OSError):
        return None


def load(project_root=".", accent=None, client=None):
    """Resolve the accent for a client project. Never guesses from DESIGN.md."""
    if accent:
        return Brand(accent, source="--accent", client=client)

    raw = _read(os.path.join(project_root, BRAND_FILE))
    if raw:
        try:
            data = json.loads(raw)
        except ValueError as exc:
            raise ValueError("%s is not valid JSON: %s" % (BRAND_FILE, exc))
        if data.get("accent"):
            return Brand(data["accent"], source=BRAND_FILE,
                         client=data.get("client") or client,
                         note=data.get("note"))

    return default()


def offer(project_root="."):
    """Candidates from the client's DESIGN.md, for confirmation."""
    text = _read(os.path.join(project_root, DESIGN_FILE))
    if not text:
        return None, []
    return os.path.join(project_root, DESIGN_FILE), extract_candidates(text)


def write(project_root, accent, client=None, note=None):
    """Record the confirmed accent so every later report uses the same one."""
    brand = Brand(accent, source="confirmed", client=client, note=note)
    path = os.path.join(project_root, BRAND_FILE)
    parent = os.path.dirname(path)
    if parent and not os.path.isdir(parent):
        os.makedirs(parent)
    payload = {
        "client": client,
        "accent": brand.raw,
        "note": note or "Accent for Analytics & Insights reports. The data "
                        "palette is fixed by the plugin and is not affected "
                        "by this value.",
    }
    with open(path, "w", encoding="utf-8") as fh:
        fh.write(json.dumps(payload, indent=2) + "\n")
    return path, brand


# --------------------------------------------------------------------------
# CLI
# --------------------------------------------------------------------------

def main(argv=None):
    p = argparse.ArgumentParser(
        description="Resolve the report accent colour for a client project.")
    p.add_argument("--project-root", default=".")
    p.add_argument("--accent", help="a hex colour to use or to confirm")
    p.add_argument("--client", help="client name, recorded in brand.json")
    p.add_argument("--suggest", action="store_true",
                   help="list accent candidates found in _context/DESIGN.md")
    p.add_argument("--write", action="store_true",
                   help="write the accent to analytics-insights/brand.json")
    p.add_argument("--json", action="store_true", help="machine-readable output")
    args = p.parse_args(argv)

    if args.suggest:
        path, cands = offer(args.project_root)
        if not path:
            print("No %s under %s — pass --accent explicitly, or accept the "
                  "plugin default." % (DESIGN_FILE, args.project_root))
            return 0
        if args.json:
            print(json.dumps({"design_file": path, "candidates": cands}, indent=2))
            return 0
        print("Accent candidates from %s" % path)
        print("These are scored guesses from prose. Confirm one before use — an")
        print("unconfirmed accent is how a report ends up in another company's")
        print("colour.\n")
        for c in cands:
            b = Brand(c["hex"], source="candidate")
            flag = "  (darkened to %s for legibility)" % b.accent if b.adjusted else ""
            print("  %s  score %5.1f%s" % (c["hex"], c["score"], flag))
            print("      %s" % c["context"])
        print("\nConfirm with:")
        print("  python3 brand.py --project-root %s --accent '#rrggbb' "
              "--client 'Name' --write" % args.project_root)
        return 0

    if args.write:
        if not args.accent:
            p.error("--write needs --accent")
        path, brand = write(args.project_root, args.accent, args.client)
        print("Wrote %s" % path)
        print(brand.describe())
        return 0

    brand = load(args.project_root, accent=args.accent, client=args.client)
    if args.json:
        print(json.dumps(brand.to_dict(), indent=2))
    else:
        print(brand.describe())
    return 0


if __name__ == "__main__":
    sys.exit(main())
