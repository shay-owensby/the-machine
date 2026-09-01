"""Validate the shared Markdown, SVG chart, and self-contained HTML report bundle."""

from __future__ import annotations

import hashlib
import re
from pathlib import Path


PLACEHOLDER_RE = re.compile(r"\{\{[A-Z0-9_]+\}\}")
CHART_DIRECTIVE_RE = re.compile(r"<!--\s*report-chart\s*\n\{.*?\}\s*\n-->", re.DOTALL)
CHART_IMAGE_RE = re.compile(
    r"!\[[^\]\n]+\]\((?P<path>[^)\n]+-assets/[a-z0-9-]+\.svg)\)"
)
SOURCE_META_RE = re.compile(
    r'<meta name="source-markdown-sha256" content="(?P<digest>[a-f0-9]{64})">'
)
CSS_META_RE = re.compile(
    r'<meta name="analytics-report-css-sha256" content="(?P<digest>[a-f0-9]{64})">'
)


def validate_report_bundle(report_path: Path, report_text: str) -> list[str]:
    errors: list[str] = []
    skill_root = Path(__file__).resolve().parent.parent
    stylesheet_path = skill_root / "assets" / "report.css"
    html_path = report_path.with_suffix(".html")
    expected_assets_dir = report_path.parent / f"{report_path.stem}-assets"

    directives = CHART_DIRECTIVE_RE.findall(report_text)
    if len(directives) < 2:
        errors.append("at least two report-chart directives are required")

    image_paths = [match.group("path") for match in CHART_IMAGE_RE.finditer(report_text)]
    if len(image_paths) != len(directives):
        errors.append("each report-chart directive must have one generated Markdown SVG image")

    for relative in image_paths:
        asset_path = (report_path.parent / relative).resolve()
        try:
            asset_path.relative_to(expected_assets_dir.resolve())
        except ValueError:
            errors.append(f"chart asset is outside the required assets directory: {relative}")
            continue
        if not asset_path.is_file():
            errors.append(f"chart asset missing: {relative}")
        elif "<svg" not in asset_path.read_text(encoding="utf-8"):
            errors.append(f"chart asset is not valid SVG text: {relative}")

    if not stylesheet_path.is_file():
        errors.append(f"shared stylesheet missing: {stylesheet_path}")
        return errors
    if not html_path.is_file():
        errors.append(f"companion HTML report missing: {html_path}")
        return errors

    css = stylesheet_path.read_text(encoding="utf-8")
    html_text = html_path.read_text(encoding="utf-8")
    source_hash = hashlib.sha256(report_text.encode("utf-8")).hexdigest()
    css_hash = hashlib.sha256(css.encode("utf-8")).hexdigest()

    source_match = SOURCE_META_RE.search(html_text)
    if not source_match or source_match.group("digest") != source_hash:
        errors.append("HTML is not synchronized with the current Markdown source")

    css_match = CSS_META_RE.search(html_text)
    if not css_match or css_match.group("digest") != css_hash:
        errors.append("HTML does not identify the current shared stylesheet")
    if f'<style id="analytics-report-style">\n{css}\n</style>' not in html_text:
        errors.append("HTML does not embed the exact shared stylesheet")

    unresolved = sorted(set(PLACEHOLDER_RE.findall(html_text)))
    if unresolved:
        errors.append("HTML contains unresolved placeholders: " + ", ".join(unresolved[:10]))
    if "<table" not in html_text:
        errors.append("HTML contains no report tables")
    if html_text.count("data:image/svg+xml") < len(directives):
        errors.append("HTML does not embed every generated SVG chart")
    if re.search(r"<script(?:\s|>)", html_text, re.IGNORECASE):
        errors.append("HTML must not contain JavaScript")
    if re.search(r"<link[^>]+rel=[\"']stylesheet[\"']", html_text, re.IGNORECASE):
        errors.append("HTML must not depend on an external stylesheet")
    if re.search(r"<img[^>]+src=[\"']https?://", html_text, re.IGNORECASE):
        errors.append("HTML must not load remote images")

    return errors

