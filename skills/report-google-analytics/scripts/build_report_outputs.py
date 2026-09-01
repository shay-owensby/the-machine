#!/usr/bin/env python3
"""Build accessible SVG charts and a self-contained HTML analytics report."""

from __future__ import annotations

import argparse
import hashlib
import html
import json
import math
import re
import shutil
import subprocess
import tempfile
from pathlib import Path
from typing import Any


CHART_RE = re.compile(
    r"(?P<image>!\[[^\]\n]*\]\([^)\n]+-assets/[a-z0-9-]+\.svg\)\n)?"
    r"(?P<comment><!--\s*report-chart\s*\n(?P<payload>\{.*?\})\s*\n-->)",
    re.DOTALL,
)
ID_RE = re.compile(r"^[a-z0-9]+(?:-[a-z0-9]+)*$")
PALETTE = ("#2563eb", "#0891b2", "#7c3aed", "#b54708")
DASHES = ("", "12 7", "3 6", "16 5 3 5")
INK = "#172033"
MUTED = "#5b6475"
GRID = "#d9e0ea"
NAVY = "#0b1f3a"
BG = "#ffffff"


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser()
    parser.add_argument("report", help="Completed Markdown report")
    parser.add_argument("--output", help="HTML output path; defaults to the Markdown path with .html")
    parser.add_argument(
        "--stylesheet",
        default=str(Path(__file__).resolve().parent.parent / "assets" / "report.css"),
        help="Shared analytics report stylesheet",
    )
    parser.add_argument("--pandoc", help="Pandoc executable; defaults to PATH lookup")
    return parser.parse_args()


def atomic_write(path: Path, text: str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with tempfile.NamedTemporaryFile(
        "w", encoding="utf-8", dir=path.parent, prefix=f".{path.name}.", delete=False
    ) as handle:
        handle.write(text)
        temporary = Path(handle.name)
    temporary.replace(path)


def xml(value: object) -> str:
    return html.escape(str(value), quote=True)


def fmt(value: float) -> str:
    absolute = abs(value)
    if absolute >= 1_000_000:
        return f"{value / 1_000_000:.1f}M"
    if absolute >= 1_000:
        return f"{value / 1_000:.1f}K"
    if absolute >= 100:
        return f"{value:.0f}"
    if absolute >= 10:
        return f"{value:.1f}"
    if absolute == 0:
        return "0"
    return f"{value:.2f}"


def number(value: Any, label: str) -> float | None:
    if value is None:
        return None
    if isinstance(value, bool) or not isinstance(value, (int, float)):
        raise ValueError(f"{label} must contain only numbers or null")
    result = float(value)
    if not math.isfinite(result):
        raise ValueError(f"{label} contains a non-finite number")
    return result


def normalize_spec(raw: dict[str, Any], index: int) -> dict[str, Any]:
    chart_id = raw.get("id")
    chart_type = raw.get("type")
    title = raw.get("title")
    labels = raw.get("labels")
    series = raw.get("series")

    if not isinstance(chart_id, str) or not ID_RE.fullmatch(chart_id):
        raise ValueError(f"chart {index}: id must be lowercase words separated by hyphens")
    if chart_type not in {"line", "bar", "horizontal-bar"}:
        raise ValueError(f"chart {chart_id}: unsupported type {chart_type!r}")
    if not isinstance(title, str) or not title.strip():
        raise ValueError(f"chart {chart_id}: title is required")
    if not isinstance(labels, list) or not 2 <= len(labels) <= 90:
        raise ValueError(f"chart {chart_id}: labels must contain 2 to 90 values")
    labels = [str(label) for label in labels]
    if not isinstance(series, list) or not 1 <= len(series) <= 4:
        raise ValueError(f"chart {chart_id}: series must contain 1 to 4 entries")

    clean_series: list[dict[str, Any]] = []
    for series_index, item in enumerate(series, 1):
        if not isinstance(item, dict):
            raise ValueError(f"chart {chart_id}: series {series_index} must be an object")
        name = item.get("name")
        values = item.get("values")
        if not isinstance(name, str) or not name.strip():
            raise ValueError(f"chart {chart_id}: series {series_index} needs a name")
        if not isinstance(values, list) or len(values) != len(labels):
            raise ValueError(f"chart {chart_id}: series {name!r} must match the label count")
        clean_series.append({
            "name": name.strip(),
            "values": [number(v, f"chart {chart_id} series {name!r}") for v in values],
        })

    if not any(v is not None for item in clean_series for v in item["values"]):
        raise ValueError(f"chart {chart_id}: all values are null")
    if chart_type in {"bar", "horizontal-bar"} and len(labels) > 20:
        raise ValueError(f"chart {chart_id}: bar charts support at most 20 labels")

    return {
        "id": chart_id,
        "type": chart_type,
        "title": title.strip(),
        "subtitle": str(raw.get("subtitle", "")).strip(),
        "x_label": str(raw.get("x_label", "")).strip(),
        "y_label": str(raw.get("y_label", "")).strip(),
        "include_zero": bool(raw.get("include_zero", chart_type != "line")),
        "labels": labels,
        "series": clean_series,
    }


def bounds(spec: dict[str, Any]) -> tuple[float, float, list[float]]:
    values = [value for item in spec["series"] for value in item["values"] if value is not None]
    low = min(values)
    high = max(values)
    if spec["include_zero"] or spec["type"] != "line":
        low = min(low, 0.0)
        high = max(high, 0.0)
    if low == high:
        padding = abs(low) * 0.1 or 1.0
        low -= padding
        high += padding

    raw_step = (high - low) / 5
    magnitude = 10 ** math.floor(math.log10(raw_step))
    fraction = raw_step / magnitude
    nice_fraction = 1 if fraction <= 1 else 2 if fraction <= 2 else 5 if fraction <= 5 else 10
    step = nice_fraction * magnitude
    nice_low = math.floor(low / step) * step
    nice_high = math.ceil(high / step) * step
    ticks: list[float] = []
    value = nice_low
    for _ in range(8):
        if value > nice_high + step * 0.01:
            break
        ticks.append(value)
        value += step
    return nice_low, nice_high, ticks


def svg_header(spec: dict[str, Any], width: int, height: int) -> list[str]:
    description = "; ".join(
        f"{item['name']}: {sum(v is not None for v in item['values'])} plotted values"
        for item in spec["series"]
    )
    return [
        f'<svg xmlns="http://www.w3.org/2000/svg" width="{width}" height="{height}" '
        f'viewBox="0 0 {width} {height}" role="img" aria-labelledby="chart-title chart-desc">',
        f'<title id="chart-title">{xml(spec["title"])}</title>',
        f'<desc id="chart-desc">{xml(description)}</desc>',
        f'<rect width="{width}" height="{height}" rx="20" fill="{BG}"/>',
        f'<text x="56" y="54" fill="{NAVY}" font-family="Inter,Arial,sans-serif" '
        f'font-size="28" font-weight="700">{xml(spec["title"])}</text>',
    ]


def render_vertical(spec: dict[str, Any]) -> str:
    width, height = 1200, 650
    left, right, top, bottom = 102, 42, 116, 112
    plot_w, plot_h = width - left - right, height - top - bottom
    low, high, ticks = bounds(spec)

    def y(value: float) -> float:
        return top + (high - value) / (high - low) * plot_h

    parts = svg_header(spec, width, height)
    if spec["subtitle"]:
        parts.append(
            f'<text x="56" y="84" fill="{MUTED}" font-family="Inter,Arial,sans-serif" '
            f'font-size="16">{xml(spec["subtitle"])}</text>'
        )
    for tick in ticks:
        yy = y(tick)
        parts.append(
            f'<line x1="{left}" y1="{yy:.2f}" x2="{left + plot_w}" y2="{yy:.2f}" '
            f'stroke="{GRID}" stroke-width="1"/>'
        )
        parts.append(
            f'<text x="{left - 14}" y="{yy + 5:.2f}" text-anchor="end" fill="{MUTED}" '
            f'font-family="Inter,Arial,sans-serif" font-size="13">{xml(fmt(tick))}</text>'
        )

    labels = spec["labels"]
    label_step = max(1, math.ceil(len(labels) / 10))
    x_step = plot_w / max(1, len(labels) - (1 if spec["type"] == "line" else 0))

    if spec["type"] == "line":
        for series_index, item in enumerate(spec["series"]):
            color = PALETTE[series_index]
            dash = (
                f' stroke-dasharray="{DASHES[series_index]}"'
                if DASHES[series_index]
                else ""
            )
            points: list[str] = []
            for i, value in enumerate(item["values"]):
                if value is None:
                    if len(points) > 1:
                        parts.append(
                            f'<polyline points="{" ".join(points)}" fill="none" stroke="{color}"{dash} '
                            'stroke-width="4" stroke-linecap="round" stroke-linejoin="round"/>'
                        )
                    points = []
                    continue
                xx = left + i * x_step
                yy = y(value)
                points.append(f"{xx:.2f},{yy:.2f}")
                parts.append(
                    f'<circle cx="{xx:.2f}" cy="{yy:.2f}" r="4.5" fill="{BG}" '
                    f'stroke="{color}" stroke-width="3"><title>{xml(labels[i])}: '
                    f'{xml(item["name"])} {xml(value)}</title></circle>'
                )
            if len(points) > 1:
                parts.append(
                    f'<polyline points="{" ".join(points)}" fill="none" stroke="{color}"{dash} '
                    'stroke-width="4" stroke-linecap="round" stroke-linejoin="round"/>'
                )
    else:
        group_w = plot_w / len(labels)
        bar_w = min(38, group_w * 0.72 / len(spec["series"]))
        zero_y = y(0)
        for label_index, label in enumerate(labels):
            center = left + group_w * (label_index + 0.5)
            for series_index, item in enumerate(spec["series"]):
                value = item["values"][label_index]
                if value is None:
                    continue
                xx = center - (len(spec["series"]) * bar_w) / 2 + series_index * bar_w
                yy = min(y(value), zero_y)
                bar_h = max(1.5, abs(y(value) - zero_y))
                parts.append(
                    f'<rect x="{xx:.2f}" y="{yy:.2f}" width="{bar_w - 3:.2f}" '
                    f'height="{bar_h:.2f}" rx="3" fill="{PALETTE[series_index]}">'
                    f"<title>{xml(label)}: {xml(item['name'])} {xml(value)}</title></rect>"
                )

    for index, label in enumerate(labels):
        if index % label_step != 0 and index != len(labels) - 1:
            continue
        xx = left + index * x_step if spec["type"] == "line" else left + (index + 0.5) * (plot_w / len(labels))
        parts.append(
            f'<text x="{xx:.2f}" y="{top + plot_h + 28}" text-anchor="middle" fill="{MUTED}" '
            f'font-family="Inter,Arial,sans-serif" font-size="12">{xml(label[:18])}</text>'
        )

    if spec["x_label"]:
        parts.append(
            f'<text x="{left + plot_w / 2:.2f}" y="{height - 24}" text-anchor="middle" '
            f'fill="{INK}" font-family="Inter,Arial,sans-serif" font-size="14">{xml(spec["x_label"])}</text>'
        )
    if spec["y_label"]:
        parts.append(
            f'<text x="24" y="{top + plot_h / 2:.2f}" text-anchor="middle" '
            f'transform="rotate(-90 24 {top + plot_h / 2:.2f})" fill="{INK}" '
            f'font-family="Inter,Arial,sans-serif" font-size="14">{xml(spec["y_label"])}</text>'
        )

    legend_x = left
    for series_index, item in enumerate(spec["series"]):
        offset = series_index * 220
        parts.append(
            f'<rect x="{legend_x + offset}" y="{height - 68}" width="15" height="15" rx="3" '
            f'fill="{PALETTE[series_index]}"/>'
        )
        parts.append(
            f'<text x="{legend_x + offset + 23}" y="{height - 55}" fill="{INK}" '
            f'font-family="Inter,Arial,sans-serif" font-size="13">{xml(item["name"][:24])}</text>'
        )
    parts.append("</svg>")
    return "\n".join(parts)


def render_horizontal(spec: dict[str, Any]) -> str:
    width = 1200
    height = max(620, 190 + len(spec["labels"]) * 38)
    left, right, top, bottom = 260, 50, 116, 92
    plot_w, plot_h = width - left - right, height - top - bottom
    low, high, ticks = bounds(spec)

    def x(value: float) -> float:
        return left + (value - low) / (high - low) * plot_w

    parts = svg_header(spec, width, height)
    if spec["subtitle"]:
        parts.append(
            f'<text x="56" y="84" fill="{MUTED}" font-family="Inter,Arial,sans-serif" '
            f'font-size="16">{xml(spec["subtitle"])}</text>'
        )
    for tick in ticks:
        xx = x(tick)
        parts.append(
            f'<line x1="{xx:.2f}" y1="{top}" x2="{xx:.2f}" y2="{top + plot_h}" '
            f'stroke="{GRID}" stroke-width="1"/>'
        )
        parts.append(
            f'<text x="{xx:.2f}" y="{top + plot_h + 25}" text-anchor="middle" fill="{MUTED}" '
            f'font-family="Inter,Arial,sans-serif" font-size="13">{xml(fmt(tick))}</text>'
        )

    row_h = plot_h / len(spec["labels"])
    bar_h = min(20, row_h * 0.7 / len(spec["series"]))
    zero_x = x(0)
    for label_index, label in enumerate(spec["labels"]):
        center = top + row_h * (label_index + 0.5)
        parts.append(
            f'<text x="{left - 16}" y="{center + 5:.2f}" text-anchor="end" fill="{INK}" '
            f'font-family="Inter,Arial,sans-serif" font-size="13">{xml(label[:30])}</text>'
        )
        for series_index, item in enumerate(spec["series"]):
            value = item["values"][label_index]
            if value is None:
                continue
            yy = center - (len(spec["series"]) * bar_h) / 2 + series_index * bar_h
            xx = min(x(value), zero_x)
            bar_w = max(1.5, abs(x(value) - zero_x))
            parts.append(
                f'<rect x="{xx:.2f}" y="{yy:.2f}" width="{bar_w:.2f}" height="{bar_h - 3:.2f}" '
                f'rx="3" fill="{PALETTE[series_index]}"><title>{xml(label)}: '
                f'{xml(item["name"])} {xml(value)}</title></rect>'
            )

    if spec["x_label"]:
        parts.append(
            f'<text x="{left + plot_w / 2:.2f}" y="{height - 24}" text-anchor="middle" '
            f'fill="{INK}" font-family="Inter,Arial,sans-serif" font-size="14">{xml(spec["x_label"])}</text>'
        )

    legend_x = left
    for series_index, item in enumerate(spec["series"]):
        offset = series_index * 220
        parts.append(
            f'<rect x="{legend_x + offset}" y="{height - 66}" width="15" height="15" rx="3" '
            f'fill="{PALETTE[series_index]}"/>'
        )
        parts.append(
            f'<text x="{legend_x + offset + 23}" y="{height - 53}" fill="{INK}" '
            f'font-family="Inter,Arial,sans-serif" font-size="13">{xml(item["name"][:24])}</text>'
        )
    parts.append("</svg>")
    return "\n".join(parts)


def render_chart(spec: dict[str, Any]) -> str:
    return render_horizontal(spec) if spec["type"] == "horizontal-bar" else render_vertical(spec)


def extract_title(markdown: str, fallback: str) -> str:
    match = re.search(r"^#\s+(.+?)\s*$", markdown, re.MULTILINE)
    if not match:
        return fallback
    return re.sub(r"[*_\`]", "", match.group(1)).strip()


def build() -> int:
    args = parse_args()
    report_path = Path(args.report).resolve()
    output_path = Path(args.output).resolve() if args.output else report_path.with_suffix(".html")
    stylesheet_path = Path(args.stylesheet).resolve()

    if not report_path.is_file() or report_path.suffix.lower() != ".md":
        raise SystemExit(f"Markdown report not found: {report_path}")
    if not stylesheet_path.is_file():
        raise SystemExit(f"Stylesheet not found: {stylesheet_path}")

    markdown = report_path.read_text(encoding="utf-8")
    matches = list(CHART_RE.finditer(markdown))
    if len(matches) < 2:
        raise SystemExit("At least two report-chart directives are required")

    parsed: list[tuple[re.Match[str], dict[str, Any]]] = []
    seen: set[str] = set()
    try:
        for index, match in enumerate(matches, 1):
            raw = json.loads(match.group("payload"))
            if not isinstance(raw, dict):
                raise ValueError(f"chart {index}: directive must contain a JSON object")
            spec = normalize_spec(raw, index)
            if spec["id"] in seen:
                raise ValueError(f"duplicate chart id: {spec['id']}")
            seen.add(spec["id"])
            parsed.append((match, spec))
    except (json.JSONDecodeError, ValueError) as exc:
        raise SystemExit(f"Invalid report-chart directive: {exc}") from exc

    assets_dir = report_path.parent / f"{report_path.stem}-assets"
    assets_dir.mkdir(parents=True, exist_ok=True)
    replacements: list[tuple[int, int, str]] = []
    for match, spec in parsed:
        svg_path = assets_dir / f"{spec['id']}.svg"
        atomic_write(svg_path, render_chart(spec))
        image_line = f"![{spec['title']}]({assets_dir.name}/{spec['id']}.svg)\n"
        replacements.append((match.start(), match.end(), image_line + match.group("comment")))

    updated = markdown
    for start, end, replacement in reversed(replacements):
        updated = updated[:start] + replacement + updated[end:]
    if updated != markdown:
        atomic_write(report_path, updated)

    source_hash = hashlib.sha256(updated.encode("utf-8")).hexdigest()
    css = stylesheet_path.read_text(encoding="utf-8")
    css_hash = hashlib.sha256(css.encode("utf-8")).hexdigest()
    render_markdown = CHART_RE.sub(lambda match: match.group("image") or "", updated)

    pandoc = args.pandoc or shutil.which("pandoc")
    if not pandoc:
        raise SystemExit("Pandoc is required to build the HTML report but was not found")

    temp_md: Path | None = None
    temp_html: Path | None = None
    try:
        with tempfile.NamedTemporaryFile("w", encoding="utf-8", suffix=".md", dir=report_path.parent, delete=False) as handle:
            handle.write(render_markdown)
            temp_md = Path(handle.name)
        output_path.parent.mkdir(parents=True, exist_ok=True)
        with tempfile.NamedTemporaryFile("w", encoding="utf-8", suffix=".html", dir=output_path.parent, delete=False) as handle:
            temp_html = Path(handle.name)

        title = extract_title(updated, report_path.stem)
        command = [
            pandoc,
            str(temp_md),
            "--from=gfm+raw_html",
            "--to=html5",
            "--standalone",
            "--embed-resources",
            "--toc",
            "--toc-depth=2",
            f"--resource-path={report_path.parent}",
            "--metadata",
            f"pagetitle={title}",
            "--output",
            str(temp_html),
        ]
        completed = subprocess.run(command, capture_output=True, text=True)
        if completed.returncode:
            message = completed.stderr.strip() or completed.stdout.strip()
            raise SystemExit(f"Pandoc failed: {message}")

        document = temp_html.read_text(encoding="utf-8")
        document = re.sub(
            r"(<table\b.*?</table>)",
            r'<div class="table-wrap">\1</div>',
            document,
            flags=re.DOTALL | re.IGNORECASE,
        )
        toc_match = re.search(r'<nav id="TOC"[^>]*>.*?</nav>', document, re.DOTALL)
        h1_match = re.search(r"<h1\b[^>]*>.*?</h1>", document, re.DOTALL)
        if toc_match and h1_match and toc_match.start() < h1_match.start():
            toc = toc_match.group(0)
            document = document[:toc_match.start()] + document[toc_match.end():]
            h1_match = re.search(r"<h1\b[^>]*>.*?</h1>", document, re.DOTALL)
            if h1_match:
                document = document[:h1_match.end()] + "\n" + toc + document[h1_match.end():]
        metadata = (
            f'<meta name="source-markdown-sha256" content="{source_hash}">\n'
            f'<meta name="analytics-report-css-sha256" content="{css_hash}">\n'
            f'<style id="analytics-report-style">\n{css}\n</style>\n'
        )
        if "</head>" not in document:
            raise SystemExit("Pandoc output is missing a head element")
        atomic_write(output_path, document.replace("</head>", metadata + "</head>", 1))
    finally:
        if temp_md and temp_md.exists():
            temp_md.unlink()
        if temp_html and temp_html.exists():
            temp_html.unlink()

    print(f"Markdown report ready: {report_path}")
    print(f"HTML report ready: {output_path}")
    print(f"Charts ready: {assets_dir}")
    return 0


if __name__ == "__main__":
    raise SystemExit(build())
