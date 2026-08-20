"""The KPI stat-tile grid and its sparklines.

The tile row is the report's executive summary in one glance: the four to six
figures a decision-maker checks first, each with its change and the shape of
the period behind it.

It is built in HTML and inline SVG rather than as an image, for three reasons.
It stays selectable and searchable, so a client can copy a figure out of it. It
is set in the same type as the paragraph beneath it. And it re-flows on a phone,
which a PNG of six tiles cannot.

The rules that keep it honest are the same ones the charts follow:

* An unavailable metric shows "not available", never a zero and never a dash
  that could be read as a zero.
* A change against a zero baseline is undefined; the tile shows the absolute
  change and says the baseline was zero.
* Colour never carries the verdict alone — every delta is written out in words
  ("better" / "worse"), which is what survives greyscale printing and what a
  screen reader announces.
"""

import os
import sys

try:
    from . import tokens as _t
    from . import fmt as _f
except ImportError:
    sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
    import tokens as _t
    import fmt as _f


# What the verdict means in words. This is the channel that is not colour, and
# it is the one that survives a greyscale printer and a screen reader.
#
# There is deliberately no arrow. The signed percentage already states the
# direction, so an arrow beside it is the same fact drawn twice -- and it
# actively misleads on the two cases that matter most: an arrow pointing up
# next to the word "better" on a falling CPA, and an arrow pointing up next to
# a change too small to be material.
VERDICT_WORD = {
    "improved": "better",
    "declined": "worse",
    "ambiguous": "",
    "flat": "not material",
    "new": "new this period",
    "unknown": "",
}


def _esc(text):
    return (str(text).replace("&", "&amp;").replace("<", "&lt;")
            .replace(">", "&gt;").replace('"', "&quot;"))


# --------------------------------------------------------------------------
# Sparkline
# --------------------------------------------------------------------------

def sparkline(values, width=158, height=26, label=None):
    """A bare inline-SVG trend line: no axis, no fill, no gridlines.

    It answers one question — was the period a drift, a spike or a cliff — and
    deliberately cannot be read for values. The figures are in the tile above
    it and the table below it.

    A flat series is drawn as a flat line rather than being scaled to noise,
    which is the usual way a sparkline manufactures a story.
    """
    pts = [v for v in (values or []) if v is not None]
    if len(pts) < 3:
        return ""

    lo, hi = min(pts), max(pts)
    span = hi - lo
    pad = 3.0
    inner_h = height - pad * 2

    n = len(pts)
    step = (width - 2.0) / (n - 1)

    def y(v):
        if span == 0:
            return height / 2.0
        return pad + inner_h - ((v - lo) / span) * inner_h

    coords = [(1.0 + i * step, y(v)) for i, v in enumerate(pts)]
    path = " ".join(("M" if i == 0 else "L") + "%.1f %.1f" % c
                    for i, c in enumerate(coords))
    last = coords[-1]

    title = ("<title>%s</title>" % _esc(label)) if label else ""
    return (
        '<svg class="sparkline" viewBox="0 0 %d %d" width="%d" height="%d" '
        'preserveAspectRatio="none" role="img" aria-hidden="%s">%s'
        '<path d="%s" fill="none" stroke="%s" stroke-width="1.25" '
        'stroke-linejoin="round" stroke-linecap="round" '
        'vector-effect="non-scaling-stroke"/>'
        '<circle cx="%.1f" cy="%.1f" r="1.9" fill="%s"/>'
        '</svg>'
        % (width, height, width, height, "false" if label else "true", title,
           path, _t.INK_FAINT, last[0], last[1], _t.INK_MUTED)
    )


# --------------------------------------------------------------------------
# Tile
# --------------------------------------------------------------------------

def tile(kpi, currency=None, series=None):
    """One tile from a KPI record in the analysis schema.

    Expects ``label``, ``unit``, ``current``, ``previous``, ``percent_change``,
    ``absolute_change``, ``availability``, ``direction`` and ``verdict``.
    """
    label = kpi.get("label") or kpi.get("key") or ""
    availability = kpi.get("availability", "available")

    if availability == "unavailable" or kpi.get("current") is None:
        note = kpi.get("notes") or []
        reason = note[0] if note else "Not returned for this account."
        return (
            '<div class="tile unavailable">'
            '<div class="label">%s</div>'
            '<div class="figure">%s</div>'
            '<div class="delta d-flat"><span class="verdict">%s</span></div>'
            '</div>' % (_esc(label), _f.NA, _esc(reason))
        )

    figure = _f.by_unit(kpi.get("current"), kpi.get("unit"), currency, compact=True)
    verdict = kpi.get("verdict") or "unknown"
    pct = kpi.get("percent_change")
    absolute = kpi.get("absolute_change")

    if pct is None and kpi.get("previous") in (0, None):
        # Undefined, not zero. Say so rather than printing a change.
        delta_text = _f.by_unit(absolute, kpi.get("unit"), currency, compact=True)
        delta = ('<span class="d-ambiguous">%s</span>'
                 '<span class="verdict">vs a zero baseline</span>'
                 % _esc(delta_text if absolute is not None else "—"))
    else:
        word = VERDICT_WORD.get(verdict, "")
        shown = _f.percent_change(pct) if pct is not None else "—"
        delta = ('<span class="d-%s">%s</span>' % (_esc(verdict), _esc(shown)))
        if word:
            delta += '<span class="verdict">%s</span>' % _esc(word)

    spark = sparkline(series, label="%s, day by day over the period" % label) if series else ""
    spark_html = '<div class="spark">%s</div>' % spark if spark else ""

    return ('<div class="tile">'
            '<div class="label">%s</div>'
            '<div class="figure">%s</div>'
            '<div class="delta">%s</div>'
            '%s</div>' % (_esc(label), _esc(figure), delta, spark_html))


def grid(kpis, currency=None, series_for=None, limit=6):
    """The tile row.

    ``series_for`` is an optional ``key -> [values]`` mapping for sparklines.
    Capped at ``limit``: past six tiles the row stops being a glance and
    becomes a table that happens to be laid out in boxes.
    """
    if not kpis:
        return ""
    series_for = series_for or {}
    chosen = kpis[:limit]
    cells = [tile(k, currency, series_for.get(k.get("key"))) for k in chosen]
    return ('<div class="tiles" style="--cols:%d">%s</div>'
            % (columns(len(chosen)), "".join(cells)))


def columns(n):
    """Column count that leaves no orphan on the last row.

    Six tiles laid out five-across leaves a single bordered box sitting alone
    under an empty row, which reads as a rendering fault rather than a layout.
    Six go three-across, in two even rows.
    """
    if n <= 4:
        return max(n, 1)
    if n % 3 == 0:
        return 3
    if n % 4 == 0:
        return 4
    return n


def select(kpis_by_key, preferred, limit=6):
    """Pick the headline KPIs in a fixed order, skipping what is unavailable.

    Each skill passes its own ``preferred`` list, so the Ads report leads with
    spend and CPA and the Analytics report leads with sessions and engagement,
    while both produce the same component.
    """
    out = []
    for key in preferred:
        rec = kpis_by_key.get(key)
        if not rec:
            continue
        if rec.get("availability") == "unavailable" and len(out) >= 3:
            continue                      # do not fill the row with absences
        out.append(rec)
        if len(out) >= limit:
            break
    return out
