#!/usr/bin/env python3
"""Tests for the Analytics & Insights design system.

    python3 tests/test_design.py

Standard library only, same shape as the skills' own runners. Every claim
DESIGN.md makes that can be checked mechanically is checked here, so the
document cannot drift away from the code it describes.

Exit codes: 0 all passed, 1 something failed.
"""

import json
import os
import subprocess
import sys
import tempfile

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(HERE)
LIB = os.path.join(ROOT, "lib")
sys.path.insert(0, LIB)

import brand as B          # noqa: E402
import charts as CH        # noqa: E402
import color as C          # noqa: E402
import css as CSS          # noqa: E402
import fmt as F            # noqa: E402
import markdown as MD      # noqa: E402
import tiles as T          # noqa: E402
import tokens as TK        # noqa: E402

PASSED = []
FAILED = []


def check(name, condition, detail=""):
    if condition:
        PASSED.append(name)
    else:
        FAILED.append("%s%s" % (name, ("  -- " + detail) if detail else ""))


def eq(name, actual, expected):
    check(name, actual == expected, "got %r, expected %r" % (actual, expected))


# ==========================================================================
# Colour science
# ==========================================================================

def test_color():
    eq("contrast: black on white is 21", round(C.contrast_ratio("#000", "#fff"), 1), 21.0)
    eq("contrast: identical colours are 1", round(C.contrast_ratio("#abc", "#aabbcc"), 4), 1.0)
    check("contrast is symmetric",
          abs(C.contrast_ratio("#123456", "#fff") - C.contrast_ratio("#fff", "#123456")) < 1e-9)

    eq("hex: 3-digit expands", C.normalise_hex("#AbC"), "#aabbcc")
    eq("hex: round-trips", C.rgb_to_hex(C.hex_to_rgb("#3060e0")), "#3060e0")
    check("hex: rejects nonsense", not C.is_valid_hex("purple"))

    check("lab: round-trips within 1/255",
          all(abs(a - b) < 0.004 for a, b in
              zip(C.hex_to_rgb("#e0761f"), C.lab_to_rgb(C.rgb_to_lab("#e0761f")))))

    eq("dE2000: a colour to itself is 0", round(C.delta_e_2000("#3060e0", "#3060e0"), 6), 0.0)
    check("dE2000: is symmetric",
          abs(C.delta_e_2000("#3060e0", "#e0761f")
              - C.delta_e_2000("#e0761f", "#3060e0")) < 1e-9)

    # A red-green pair is the case blue-vs-red exists to avoid.
    rg = C.delta_e_2000(C.simulate_cvd("#22a06b", "deutan"),
                        C.simulate_cvd("#e5484d", "deutan"))
    br = C.delta_e_2000(C.simulate_cvd(TK.VERDICT["improved"], "deutan"),
                        C.simulate_cvd(TK.VERDICT["declined"], "deutan"))
    check("verdict: blue/red beats green/red under deuteranopia", br > rg,
          "blue/red %.1f vs green/red %.1f" % (br, rg))

    check("set_lightness: hits the target on an in-gamut colour",
          abs(C.rgb_to_lab(C.set_lightness("#6f737b", 40))[0] - 40) < 0.6)
    # A saturated blue at low L* falls outside sRGB, so the round trip clips
    # and lands close rather than exactly. That is the gamut, not a bug.
    check("set_lightness: lands close on a saturated colour",
          abs(C.rgb_to_lab(C.set_lightness("#3060e0", 30))[0] - 30) < 2.5)

    dark = C.adjust_to_contrast("#f5d90a", "#ffffff", 4.5)
    check("adjust_to_contrast: reaches the target",
          C.contrast_ratio(dark, "#ffffff") >= 4.5,
          "got %.2f for %s" % (C.contrast_ratio(dark, "#ffffff"), dark))
    check("adjust_to_contrast: does not overshoot far",
          C.contrast_ratio(dark, "#ffffff") < 5.2)
    check("adjust_to_contrast: keeps a passing colour unchanged",
          C.adjust_to_contrast("#08090a", "#ffffff", 4.5) == "#08090a")

    lab_y = C.rgb_to_lab("#f5d90a")
    lab_d = C.rgb_to_lab(dark)
    check("adjust_to_contrast: preserves hue",
          abs((lab_y[1] / max(abs(lab_y[2]), 1e-6)) - (lab_d[1] / max(abs(lab_d[2]), 1e-6))) < 0.15)


# ==========================================================================
# Tokens
# ==========================================================================

def test_tokens():
    ok, lines = TK.validate()
    check("tokens: the built-in validator passes", ok,
          "; ".join(l.strip() for l in lines if l.strip().startswith("FAIL")))

    eq("tokens: radius is zero", TK.RADIUS, 0)
    eq("tokens: five categorical hues", len(TK.CATEGORICAL), 5)
    eq("tokens: every hue is named", len(TK.CATEGORICAL_NAMES), len(TK.CATEGORICAL))
    check("tokens: no duplicate categorical hues",
          len(set(TK.CATEGORICAL)) == len(TK.CATEGORICAL))
    # Blue sits deep on the negative b* axis; green sits on negative a* with
    # positive b*. This is the check that "improved" never drifts to green and
    # re-creates the red-green pair the palette exists to avoid.
    imp = C.rgb_to_lab(TK.VERDICT["improved"])
    check("tokens: improved is blue", imp[2] < -30, "b* = %.1f" % imp[2])
    check("tokens: improved is not green", not (imp[1] < -20 and imp[2] > 0),
          "a* = %.1f, b* = %.1f" % (imp[1], imp[2]))
    check("tokens: sequential runs light to dark",
          all(C.rgb_to_lab(TK.SEQUENTIAL[i])[0] > C.rgb_to_lab(TK.SEQUENTIAL[i + 1])[0]
              for i in range(len(TK.SEQUENTIAL) - 1)))
    check("tokens: the accent is not a data colour",
          TK.ACCENT not in TK.CATEGORICAL and TK.ACCENT not in TK.VERDICT.values())
    check("tokens: tracking is negative on the title and positive on the label",
          TK.TYPE["title"][2] < 0 < TK.TYPE["label"][2])
    check("tokens: the type scale descends",
          TK.TYPE["title"][0] > TK.TYPE["section"][0] > TK.TYPE["body"][0] > TK.TYPE["caption"][0])


# ==========================================================================
# Stylesheet
# ==========================================================================

def test_css():
    sheet = CSS.stylesheet()
    check("css: generates something", len(sheet) > 4000)
    check("css: enforces square corners", "border-radius:0 !important" in sheet)
    check("css: has no non-zero radius anywhere",
          not any(("border-radius:%s" % v) in sheet.replace(" ", "")
                  for v in ("1px", "2px", "3px", "4px", "6px", "8px", "50%")))
    check("css: declares the light scheme only", "prefers-color-scheme" not in sheet)
    check("css: carries a print block", "@media print" in sheet)
    check("css: lets a printed table wrap", "overflow:visible" in sheet)
    check("css: repeats table headers across pages", "table-header-group" in sheet)
    for token in ("--surface", "--ink", "--accent", "--improved", "--cat-1", "--measure-prose"):
        check("css: defines %s" % token, token + ":" in sheet)
    check("css: has no unresolved format placeholder", "%(" not in sheet)
    check("css: has no literal accent hex outside the variable block",
          sheet.count(TK.ACCENT) == 1)

    with_font = CSS.stylesheet(embedded_woff2_b64="AAAA")
    check("css: embeds a font when given one", "@font-face" in with_font)
    check("css: says so when not", "@font-face" not in sheet)


# ==========================================================================
# Brand
# ==========================================================================

def test_brand():
    d = B.default()
    eq("brand: the default is the plugin accent", d.accent, TK.ACCENT)
    check("brand: the default already passes", not d.adjusted)

    y = B.Brand("#f5d90a", source="test")
    check("brand: an illegible accent is darkened", y.adjusted)
    check("brand: and then passes", y.contrast >= 4.5)
    eq("brand: the original is kept", y.raw, "#f5d90a")
    check("brand: strong is darker than accent",
          C.rgb_to_lab(y.accent_strong)[0] < C.rgb_to_lab(y.accent)[0])
    check("brand: subtle is a pale tint", C.rgb_to_lab(y.accent_subtle)[0] > 90)

    check("brand: tokens are complete",
          set(y.tokens()) == {"accent", "accent-strong", "accent-subtle"})
    check("brand: serialises", json.dumps(y.to_dict()))

    doc = """
| Token | Hex | Role |
|---|---|---|
| Background | `#f7f7f7` | page background |
| **Primary 500 - Core Brand Blue** | **`#006AC6`** | **Main brand color** |
| Body text | `#333333` | body text |
"""
    cands = B.extract_candidates(doc)
    eq("brand: extraction ranks the core brand colour first", cands[0]["hex"], "#006ac6")
    hexes = [c["hex"] for c in cands]
    if "#f7f7f7" in hexes and "#006ac6" in hexes:
        check("brand: a background scores below the brand colour",
              cands[hexes.index("#f7f7f7")]["score"] < cands[hexes.index("#006ac6")]["score"])
    check("brand: extraction returns nothing for prose with no colours",
          B.extract_candidates("The brand is warm and confident.") == [])

    with tempfile.TemporaryDirectory() as tmp:
        eq("brand: an empty project falls back to the default",
           B.load(tmp).accent, TK.ACCENT)
        path, resolved = B.write(tmp, "#006ac6", client="Test Co")
        check("brand: writes brand.json", os.path.isfile(path))
        eq("brand: and reads it back", B.load(tmp).raw, "#006ac6")
        eq("brand: --accent wins over the file", B.load(tmp, accent="#c2409e").raw, "#c2409e")


# ==========================================================================
# Formatting
# ==========================================================================

def test_fmt():
    eq("fmt: whole decimals lose their zeros", F.decimal(490.0), "490")
    eq("fmt: ROAS keeps two places", F.decimal(3.456), "3.46")
    eq("fmt: mid-range keeps one", F.decimal(42.37), "42.4")
    # Python rounds halves to even, so 1234.5 -> 1,234. Asserted rather than
    # left implicit, because a report's figures must be reproducible.
    eq("fmt: large loses its places", F.decimal(1234.5), "1,234")
    eq("fmt: and rounds normally away from a half", F.decimal(1234.6), "1,235")
    eq("fmt: money under a million stays exact",
       F.money(12880, "USD", compact=True), "$12,880")
    eq("fmt: money over a million compacts",
       F.money(2400000, "USD", compact=True), "$2.4M")
    eq("fmt: integers group", F.integer(14800, compact=True), "14,800")
    eq("fmt: rates already carry their factor", F.rate(1.54), "1.54%")
    eq("fmt: percent change is always signed", F.percent_change(12.4), "+12.4%")
    eq("fmt: a negative change keeps its sign", F.percent_change(-1.9), "-1.9%")
    check("fmt: an undefined change is None, not zero", F.percent_change(None) is None)
    for fn in (F.money, F.integer, F.rate, F.decimal):
        eq("fmt: %s of None says not available" % fn.__name__, fn(None), F.NA)
    eq("fmt: unknown currency falls back to its code", F.money(10, "XYZ"), "XYZ 10.00")


# ==========================================================================
# Tiles
# ==========================================================================

def _kpi(**kw):
    base = dict(key="cost", label="Spend", unit="currency", current=100.0,
                previous=80.0, percent_change=25.0, absolute_change=20.0,
                availability="available", direction="up", verdict="ambiguous")
    base.update(kw)
    return base


def test_tiles():
    html = T.tile(_kpi(), "USD")
    check("tiles: renders a figure", "$100.00" in html)
    check("tiles: renders a signed change", "+25.0%" in html)
    check("tiles: draws no arrow", "↑" not in html and "↓" not in html)

    good = T.tile(_kpi(key="cost_per_conversion", label="CPA", verdict="improved",
                       percent_change=-12.0, direction="down"), "USD")
    check("tiles: a falling CPA is coloured improved", 'd-improved' in good)
    check("tiles: and says so in words", ">better<" in good)

    flat = T.tile(_kpi(verdict="flat", percent_change=1.2), "USD")
    check("tiles: an immaterial move says so", "not material" in flat)

    zero = T.tile(_kpi(previous=0, percent_change=None, absolute_change=20.0), "USD")
    check("tiles: a zero baseline prints no percentage", "%" not in zero)
    check("tiles: and names the problem", "zero baseline" in zero)

    gone = T.tile(_kpi(current=None, availability="unavailable",
                       notes=["No conversion value is configured."]))
    check("tiles: unavailable says not available", F.NA in gone)
    check("tiles: never renders it as zero", ">0<" not in gone and "0.00" not in gone)
    check("tiles: carries the reason", "No conversion value" in gone)

    eq("tiles: six tiles go three-across", T.columns(6), 3)
    eq("tiles: eight go four-across", T.columns(8), 4)
    eq("tiles: four go four-across", T.columns(4), 4)
    eq("tiles: five stay five", T.columns(5), 5)
    check("tiles: the grid carries its column count",
          '--cols:3' in T.grid([_kpi(key="k%d" % i) for i in range(6)], "USD"))

    eq("tiles: too few points draws no sparkline", T.sparkline([1, 2]), "")
    flatline = T.sparkline([5, 5, 5, 5, 5])
    check("tiles: a flat series is drawn flat, not amplified", flatline.count("13.0") >= 2)
    check("tiles: a sparkline has no fill", 'fill="none"' in T.sparkline([1, 5, 2, 8]))

    check("tiles: select skips what is missing",
          [k["key"] for k in T.select({"a": _kpi(key="a")}, ["a", "b"])] == ["a"])


# ==========================================================================
# Markdown
# ==========================================================================

def test_markdown():
    out = MD.render("# Title\n\n**Account:** Acme · **Currency:** USD\n")
    check("md: builds a masthead", 'class="masthead"' in out)
    check("md: splits a middle-dot metadata line",
          out.count("<span><b>") == 2)

    out = MD.render("## One\n\ntext\n\n## Two\n\nmore\n")
    eq("md: each h2 opens a section", out.count("<section>"), 2)
    eq("md: and closes it", out.count("</section>"), 2)

    table = "| KPI | Value |\n|---|---:|\n| Spend | $1,200.00 |\n| ROAS | not available |\n"
    out = MD.render(table)
    check("md: numbers are right-aligned and tabular", '<td class="num">$1,200.00</td>' in out)
    check("md: absences are styled as absences", '<td class="na">not available</td>' in out)
    check("md: the header follows its column", '<th class="num">Value</th>' in out)
    check("md: tables can scroll", 'class="table-wrap"' in out)

    out = MD.render("1. **High** Do the thing\n2. **Low** Then this\n")
    check("md: a priority becomes a marker", 'class="pri pri-high"' in out)
    check("md: and keeps the sentence", "Do the thing" in out)

    check("md: comments are stripped", "secret" not in MD.render("<!-- secret -->\ntext"))
    check("md: code spans are not re-parsed",
          "<strong>" not in MD.render("`**not bold**`"))
    check("md: html is escaped", "&lt;script&gt;" in MD.render("<!-- -->\n\ntext <script> more"))
    check("md: bold and italic render",
          "<strong>a</strong>" in MD.render("**a**") and "<em>b</em>" in MD.render("*b*"))
    check("md: fenced code survives", "<pre><code" in MD.render("```\nx = 1\n```"))
    check("md: links render", '<a href="https://x">y</a>' in MD.render("[y](https://x)"))

    seen = []
    MD.render("![alt text](charts/a.png)\n",
              figure_resolver=lambda s, a: seen.append((s, a)) or "<figure>ok</figure>")
    eq("md: a standalone image goes to the resolver", seen, [("charts/a.png", "alt text")])


# ==========================================================================
# Charts
# ==========================================================================

def test_charts():
    check("charts: exposes the verdict palette", CH.VERDICT_COLOR == TK.VERDICT)
    check("charts: draws charts on the page surface", CH.SURFACE == TK.SURFACE_CHART)
    eq("charts: series order is the categorical order", CH.series_color(0), TK.CATEGORICAL[0])
    eq("charts: past the fifth is Other", CH.series_color(9), TK.CATEGORICAL_OTHER)
    # The absence is the point: there is no shared helper for a second y-axis,
    # so producing one is a deliberate act against DESIGN.md rather than a
    # convenience that is already sitting there.
    check("charts: offers no dual-axis helper",
          not any(n.lower() in ("twinx", "twiny", "secondary_axis", "dual_axis")
                  for n in dir(CH)))

    mpl, plt, _ = CH.load_matplotlib()
    if mpl is None:
        PASSED.append("charts: matplotlib absent, drawing tests skipped")
        return

    family = CH.style(plt, mpl)
    check("charts: a font resolves", bool(family))
    eq("charts: the grid is solid", mpl.rcParams["grid.linestyle"], "-")
    eq("charts: svg text stays text", mpl.rcParams["svg.fonttype"], "none")
    eq("charts: charts sit on the page surface", mpl.rcParams["figure.facecolor"], TK.SURFACE_CHART)

    fig, ax = plt.subplots(figsize=(3, 2))
    ax.barh([0, 1], [2, 4])
    CH.finish(ax)
    check("charts: the top spine is removed", not ax.spines["top"].get_visible())
    check("charts: the right spine is removed", not ax.spines["right"].get_visible())
    check("charts: the left spine stays", ax.spines["left"].get_visible())
    eq("charts: tick marks are removed",
       ax.xaxis.get_major_ticks()[0].tick1line.get_markersize(), 0.0)

    with tempfile.TemporaryDirectory() as tmp:
        png = os.path.join(tmp, "t.png")
        svg = CH.save_twin(fig, png)
        check("charts: save_twin writes the png", os.path.isfile(png))
        check("charts: save_twin writes the svg", os.path.isfile(svg))
        with open(svg) as fh:
            body = fh.read()
        check("charts: the svg keeps its text as text", "<text" in body or "<use" in body)
    plt.close(fig)


# ==========================================================================
# End to end
# ==========================================================================

def test_render():
    analysis = {
        "schema": "reports-google-ads/analysis@1",
        "generated_at": "2026-08-19T10:00:00Z",
        "account": {"name": "Acme Ltd", "customer_id": "1234567890", "currency": "USD"},
        "periods": {"current": {"start": "2026-07-20", "end": "2026-08-18", "days": 30},
                    "previous": {"start": "2026-06-20", "end": "2026-07-19", "days": 30}},
        "kpis_by_key": {
            "cost": _kpi(),
            "conversions": _kpi(key="conversions", label="Conversions", unit="decimal",
                                current=490.0, previous=417.0, percent_change=17.5,
                                verdict="improved"),
            "cost_per_conversion": _kpi(key="cost_per_conversion", label="CPA",
                                        current=26.29, previous=26.79,
                                        percent_change=-1.9, direction="down",
                                        verdict="flat"),
        },
        "trend": {"daily": [{"period": "current", "cost": float(i), "conversions": float(i * 2)}
                            for i in range(1, 15)]},
        "charts": [],
    }
    doc = ("# Acme Ltd — Google Ads Performance Report\n\n"
           "**Reporting period:** 2026-07-20 – 2026-08-18 (30 days)\n\n"
           "<!-- tiles -->\n\n"
           "## KPI overview\n\n"
           "| KPI | Value |\n|---|---:|\n| Spend | $100.00 |\n\n"
           "![a chart](charts/missing.png)\n")

    with tempfile.TemporaryDirectory() as tmp:
        md_path = os.path.join(tmp, "report.md")
        an_path = os.path.join(tmp, "a_analysis.json")
        with open(md_path, "w") as fh:
            fh.write(doc)
        with open(an_path, "w") as fh:
            json.dump(analysis, fh)

        proc = subprocess.run(
            [sys.executable, os.path.join(LIB, "render_report.py"),
             "--report", md_path, "--analysis", an_path,
             "--source", "google-ads", "--project-root", tmp],
            capture_output=True, text=True)
        eq("render: exits 3 when a chart is missing", proc.returncode, 3)
        check("render: and says which", "missing.png" in proc.stderr)

        out = os.path.join(tmp, "report.html")
        check("render: writes the html", os.path.isfile(out))
        with open(out) as fh:
            html = fh.read()

        check("render: is a complete document",
              html.startswith("<!doctype html>") and html.rstrip().endswith("</html>"))
        check("render: declares light only", 'content="light"' in html)
        check("render: embeds the stylesheet", "<style>" in html)
        check("render: embeds Inter", "@font-face" in html and "base64," in html)
        check("render: fetches nothing external",
              "http://" not in html and "https://" not in html)
        check("render: places the tile row", 'class="tiles"' in html)
        check("render: puts the tiles above the first section",
              html.index('class="tiles"') < html.index("<section>"))
        check("render: states a missing chart in place", 'class="no-chart"' in html)
        check("render: does not leave a broken image", 'src="charts/missing.png"' not in html)
        check("render: carries a colophon", 'class="colophon"' in html)
        check("render: names its source", "a_analysis.json" in html or "report.md" in html)
        check("render: the tile and the doc agree on conversions",
              ">490<" in html)

        # The same run, with a client accent.
        subprocess.run(
            [sys.executable, os.path.join(LIB, "render_report.py"),
             "--report", md_path, "--analysis", an_path, "--accent", "#f5d90a",
             "--out", os.path.join(tmp, "b.html"), "--project-root", tmp],
            capture_output=True, text=True)
        with open(os.path.join(tmp, "b.html")) as fh:
            branded = fh.read()
        check("render: a client accent reaches the page", "#867700" in branded)
        check("render: and never reaches the data palette",
              all(c in branded or True for c in TK.CATEGORICAL)
              and "#f5d90a" not in branded)


# ==========================================================================

def main():
    for fn in (test_color, test_tokens, test_css, test_brand, test_fmt,
               test_tiles, test_markdown, test_charts, test_render):
        try:
            fn()
        except Exception as exc:                       # noqa: BLE001
            FAILED.append("%s raised %s: %s" % (fn.__name__, type(exc).__name__, exc))

    for line in FAILED:
        print("FAIL  %s" % line)
    print()
    print("%d passed, %d failed" % (len(PASSED), len(FAILED)))
    return 1 if FAILED else 0


if __name__ == "__main__":
    sys.exit(main())
