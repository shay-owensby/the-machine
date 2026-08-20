#!/usr/bin/env python3
"""Render a report's Markdown into one self-contained HTML file.

    python3 render_report.py --report 2026-08-19-google-ads.md \
                             --analysis _data/..._analysis.json \
                             --project-root .

Everything ends up inside the single output file: the stylesheet, the Inter
subset, and every chart as inline SVG or an embedded data URI. There is nothing
beside it to lose, so the file can be mailed as one attachment, dropped in a
shared drive, or printed, and it looks the same in all three.

The Markdown stays on disk as the source of record. It is what an agent reads
when it needs to revise the report, and what survives if this renderer changes.

Exit codes
    0  rendered
    2  the report or analysis file could not be read
    3  a chart the report references was not on disk (rendered anyway, with
       the gap stated in place of the chart)
"""

import argparse
import base64
import json
import os
import re
import sys

_HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, _HERE)

import brand as _brand          # noqa: E402
import css as _css              # noqa: E402
import fmt as _fmt              # noqa: E402
import markdown as _md          # noqa: E402
import tiles as _tiles          # noqa: E402
import tokens as _t             # noqa: E402

FONT_FILE = os.path.join(os.path.dirname(_HERE), "fonts", "Inter-latin-var.woff2")
TILES_MARKER = re.compile(r"<!--\s*tiles\s*-->", re.I)

# The headline KPIs each report leads with. A skill that is not listed falls
# back to the first comparable KPIs in the analysis file's own order.
HEADLINE_KPIS = {
    "google-ads": ["cost", "conversions", "cost_per_conversion", "roas",
                   "clicks", "conversion_rate"],
    "google-analytics": ["sessions", "activeUsers", "engagementRate",
                         "keyEvents", "engagedSessions", "averageSessionDuration"],
    "google-search-console": ["clicks", "impressions", "ctr", "position"],
}


def die(code, message):
    sys.stderr.write("error: %s\n" % message)
    sys.exit(code)


def read_text(path):
    with open(path, "r", encoding="utf-8") as fh:
        return fh.read()


# --------------------------------------------------------------------------
# Charts
# --------------------------------------------------------------------------

def _clean_svg(markup, alt):
    """Strip the XML preamble and make the SVG an accessible, fluid figure."""
    markup = re.sub(r"<\?xml[^>]*\?>", "", markup)
    markup = re.sub(r"<!DOCTYPE[^>]*>", "", markup, flags=re.I)
    markup = markup.strip()

    m = re.search(r"<svg\b([^>]*)>", markup)
    if not m:
        return None
    attrs = m.group(1)

    # A fixed width and height would stop the chart scaling with the column.
    # The viewBox matplotlib writes carries the aspect ratio, so both go.
    new_attrs = re.sub(r'\s(width|height)="[^"]*"', "", attrs)
    if "viewBox" not in new_attrs:
        wm = re.search(r'width="([\d.]+)(?:pt)?"', attrs)
        hm = re.search(r'height="([\d.]+)(?:pt)?"', attrs)
        if wm and hm:
            new_attrs += ' viewBox="0 0 %s %s"' % (wm.group(1), hm.group(1))
    new_attrs += ' role="img" preserveAspectRatio="xMidYMid meet"'

    markup = markup[:m.start()] + "<svg" + new_attrs + ">" + markup[m.end():]
    if alt:
        title = ("<title>%s</title>"
                 % alt.replace("&", "&amp;").replace("<", "&lt;"))
        markup = re.sub(r"(<svg[^>]*>)", r"\1" + title, markup, count=1)
    return markup


def make_figure_resolver(base_dir, manifest_by_file, missing):
    """Return the callback markdown.py uses for every standalone image."""

    def resolve(src, alt):
        if src.startswith(("http://", "https://", "data:")):
            return None

        path = src if os.path.isabs(src) else os.path.join(base_dir, src)
        name = os.path.basename(src)
        entry = manifest_by_file.get(name, {})
        note = entry.get("note")
        caption = ('<figcaption>%s</figcaption>' % _md._inline(note)) if note else ""

        # Prefer the SVG twin of a referenced PNG: the report template is
        # written against PNGs so it stays readable as Markdown, but the HTML
        # should carry vectors.
        candidates = [path]
        stem, ext = os.path.splitext(path)
        if ext.lower() == ".png":
            candidates.insert(0, stem + ".svg")

        for candidate in candidates:
            if not os.path.isfile(candidate):
                continue
            if candidate.lower().endswith(".svg"):
                markup = _clean_svg(read_text(candidate), alt)
                if markup:
                    return "<figure>%s%s</figure>" % (markup, caption)
            with open(candidate, "rb") as fh:
                data = base64.b64encode(fh.read()).decode("ascii")
            mime = "image/png" if candidate.lower().endswith(".png") else "image/jpeg"
            return ('<figure><img src="data:%s;base64,%s" alt="%s">%s</figure>'
                    % (mime, data, _md._esc(alt), caption))

        # Referenced but absent. Say so where the chart would have been rather
        # than shipping a broken image or, worse, quietly dropping it.
        missing.append(src)
        reason = entry.get("reason") or ("The chart file %s was not found "
                                         "beside this report." % name)
        return ('<div class="no-chart"><span class="label">Chart not shown</span>'
                '<br>%s</div>' % _md._inline(reason))

    return resolve


# --------------------------------------------------------------------------
# Tiles from an analysis file
# --------------------------------------------------------------------------

def build_tiles(analysis, source_hint=None):
    if not analysis:
        return ""
    by_key = analysis.get("kpis_by_key") or {}
    if not by_key:
        kpis = analysis.get("kpis") or []
        by_key = {k.get("key"): k for k in kpis if k.get("key")}
    if not by_key:
        return ""

    schema = analysis.get("schema") or ""
    key = source_hint
    if not key:
        for candidate in HEADLINE_KPIS:
            if candidate in schema:
                key = candidate
                break
    preferred = HEADLINE_KPIS.get(key) or [k.get("key") for k in analysis.get("kpis", [])]

    selected = _tiles.select(by_key, [p for p in preferred if p], limit=6)
    if not selected:
        return ""

    currency = (analysis.get("account") or {}).get("currency")
    series = _daily_series(analysis, [k.get("key") for k in selected])
    return _tiles.grid(selected, currency, series)


def _daily_rows(analysis):
    """The current period's daily rows, flattened to ``{metric: value}``.

    The skills' analysis files disagree on where the daily series lives and what
    shape it has, so the adapter is here rather than being pushed back into each
    of them -- their schemas are published contracts that other things read.

      reports-google-ads          trend.daily[]              flat keys
      reports-google-analytics    sections.trends.current[]  {date, values{}}

    An unrecognised shape returns nothing, and the tiles simply carry no
    sparkline. It never guesses.
    """
    trend = analysis.get("trend") or {}
    daily = trend.get("daily")
    if isinstance(daily, list) and daily:
        current = [r for r in daily
                   if isinstance(r, dict) and r.get("period") in (None, "current")]
        return current or [r for r in daily if isinstance(r, dict)]

    trends = ((analysis.get("sections") or {}).get("trends") or {})
    rows = trends.get("current")
    if isinstance(rows, list) and rows:
        flat = []
        for row in rows:
            if not isinstance(row, dict):
                continue
            values = row.get("values")
            flat.append(dict(values) if isinstance(values, dict) else row)
        return flat
    return []


def _daily_series(analysis, keys):
    """Per-day values for the sparklines, current period only."""
    rows = _daily_rows(analysis)
    if not rows:
        return {}
    out = {}
    for key in keys:
        values = [row.get(key) for row in rows]
        if sum(1 for v in values if v is not None) >= 3:
            out[key] = values
            continue
        # Ratio KPIs are rarely stored per day, but they are derivable from the
        # two counts that are -- and a tile row where half the tiles have a
        # trend line and half do not looks broken rather than sparse.
        derived = _derive(rows, key)
        if derived:
            out[key] = derived
    return out


# numerator, denominator, and whether the result is a percentage
_RATIOS = {
    "cost_per_conversion": ("cost", "conversions", False),
    "roas": ("conversions_value", "cost", False),
    "ctr": ("clicks", "impressions", True),
    "conversion_rate": ("conversions", "clicks", True),
    "average_cpc": ("cost", "clicks", False),
    "engagementRate": ("engagedSessions", "sessions", True),
    "sessionKeyEventRate": ("keyEvents", "sessions", True),
}


def _derive(rows, key):
    spec = _RATIOS.get(key)
    if not spec:
        return None
    num_key, den_key, as_pct = spec
    values = []
    for row in rows:
        num, den = row.get(num_key), row.get(den_key)
        if num is None or not den:
            values.append(None)          # undefined, never zero
        else:
            values.append((num / den) * (100.0 if as_pct else 1.0))
    return values if sum(1 for v in values if v is not None) >= 3 else None


# --------------------------------------------------------------------------
# Shell
# --------------------------------------------------------------------------

def colophon(analysis, brand_obj, report_path):
    bits = []
    if analysis:
        acct = analysis.get("account") or {}
        if acct.get("name"):
            bits.append("Account <b>%s</b>%s"
                        % (_md._esc(acct["name"]),
                           " (%s)" % _md._esc(str(acct["customer_id"]))
                           if acct.get("customer_id") else ""))
        if analysis.get("generated_at"):
            bits.append("Analysis generated %s" % _md._esc(analysis["generated_at"]))
        if analysis.get("schema"):
            bits.append("Schema <code>%s</code>" % _md._esc(analysis["schema"]))
    bits.append("Source document <code>%s</code>" % _md._esc(os.path.basename(report_path)))

    lines = ["<p>%s</p>" % " · ".join(bits)]
    lines.append("<p>Every figure in this report is taken from the analysis file "
                 "named above. Metrics the account did not return are marked "
                 "not available and are never shown as zero.</p>")
    return '<footer class="colophon">%s</footer>' % "".join(lines)


def document(title, body, style, lang="en"):
    return (
        '<!doctype html>\n'
        '<html lang="%s">\n<head>\n'
        '<meta charset="utf-8">\n'
        '<meta name="viewport" content="width=device-width, initial-scale=1">\n'
        '<meta name="color-scheme" content="light">\n'
        '<title>%s</title>\n'
        '<style>%s</style>\n'
        '</head>\n<body>\n<main class="report">\n%s\n</main>\n</body>\n</html>\n'
        % (lang, _md._esc(title), style, body)
    )


def extract_title(text, fallback):
    m = re.search(r"^#\s+(.+)$", text, re.M)
    return m.group(1).strip() if m else fallback


# --------------------------------------------------------------------------
# Main
# --------------------------------------------------------------------------

def main(argv=None):
    p = argparse.ArgumentParser(description=__doc__,
                                formatter_class=argparse.RawDescriptionHelpFormatter)
    p.add_argument("--report", required=True, help="the report Markdown file")
    p.add_argument("--analysis", help="the *_analysis.json the report was written from")
    p.add_argument("--out", help="output path (default: the report with .html)")
    p.add_argument("--project-root", default=".", help="where brand.json lives")
    p.add_argument("--accent", help="override the client accent, as a hex colour")
    p.add_argument("--source", choices=sorted(HEADLINE_KPIS),
                   help="which report this is, for headline KPI selection")
    p.add_argument("--no-tiles", action="store_true",
                   help="do not insert the KPI tile grid")
    p.add_argument("--no-font", action="store_true",
                   help="do not embed Inter; fall back to the system stack")
    args = p.parse_args(argv)

    if not os.path.isfile(args.report):
        die(2, "no report at %s" % args.report)
    text = read_text(args.report)
    base_dir = os.path.dirname(os.path.abspath(args.report))

    analysis = None
    if args.analysis:
        if not os.path.isfile(args.analysis):
            die(2, "no analysis file at %s" % args.analysis)
        try:
            analysis = json.loads(read_text(args.analysis))
        except ValueError as exc:
            die(2, "%s is not valid JSON: %s" % (args.analysis, exc))

    brand_obj = _brand.load(args.project_root, accent=args.accent)

    manifest_by_file = {}
    for entry in (analysis or {}).get("charts") or []:
        if entry.get("filename"):
            manifest_by_file[entry["filename"]] = entry
            manifest_by_file[os.path.splitext(entry["filename"])[0] + ".svg"] = entry

    # The tile grid replaces its marker, before comments are stripped.
    tiles_html = "" if args.no_tiles else build_tiles(analysis, args.source)
    if TILES_MARKER.search(text):
        text = TILES_MARKER.sub(tiles_html or "", text, count=1)
    elif tiles_html:
        # No marker: place the row directly under the masthead, which is where
        # it belongs and where a template that predates this renderer wants it.
        parts = re.split(r"(?m)^(##\s)", text, maxsplit=1)
        if len(parts) == 3:
            text = parts[0] + tiles_html + "\n\n" + parts[1] + parts[2]
        else:
            text = text + "\n\n" + tiles_html

    missing = []
    resolver = make_figure_resolver(base_dir, manifest_by_file, missing)
    body = _md.render(text, figure_resolver=resolver)
    body += "\n" + colophon(analysis, brand_obj, args.report)

    font_b64 = None
    if not args.no_font and os.path.isfile(FONT_FILE):
        with open(FONT_FILE, "rb") as fh:
            font_b64 = base64.b64encode(fh.read()).decode("ascii")

    style = _css.stylesheet(brand_obj, font_b64)
    title = extract_title(text, os.path.basename(args.report))
    html = document(title, body, style)

    out = args.out or os.path.splitext(args.report)[0] + ".html"
    with open(out, "w", encoding="utf-8") as fh:
        fh.write(html)

    size_kb = os.path.getsize(out) / 1024.0
    print("Wrote %s  (%.0f KB, self-contained)" % (out, size_kb))
    print("  accent   %s  (%s)" % (brand_obj.accent, brand_obj.source))
    print("  type     %s" % ("Inter, embedded" if font_b64 else "system stack"))
    print("  tiles    %s" % ("yes" if tiles_html else "none"))
    if missing:
        sys.stderr.write("warning: %d chart(s) referenced but not found; the "
                         "gap is stated in the report:\n" % len(missing))
        for s in missing:
            sys.stderr.write("  %s\n" % s)
        return 3
    return 0


if __name__ == "__main__":
    sys.exit(main())
