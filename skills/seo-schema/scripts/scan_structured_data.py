#!/usr/bin/env python3
"""Extract structured-data signals and common static-source issues from HTML."""

from __future__ import annotations

import argparse
import json
import re
import sys
import urllib.error
import urllib.parse
import urllib.request
from html.parser import HTMLParser
from pathlib import Path
from typing import Any


PLACEHOLDER_RE = re.compile(
    r"(?:REPLACE_WITH|INSERT_|TODO|TBD|YOUR_(?:URL|NAME|VALUE)|EXAMPLE\.COM)", re.I
)
ABSOLUTE_URL_PROPERTIES = {
    "url",
    "image",
    "logo",
    "sameAs",
    "contentUrl",
    "embedUrl",
    "thumbnailUrl",
    "mainEntityOfPage",
}


class DuplicateKeyError(ValueError):
    pass


def no_duplicate_keys(pairs: list[tuple[str, Any]]) -> dict[str, Any]:
    result: dict[str, Any] = {}
    for key, value in pairs:
        if key in result:
            raise DuplicateKeyError(f"duplicate JSON key: {key}")
        result[key] = value
    return result


class StructuredDataParser(HTMLParser):
    def __init__(self) -> None:
        super().__init__(convert_charrefs=True)
        self.jsonld_blocks: list[dict[str, Any]] = []
        self.microdata: list[dict[str, Any]] = []
        self.rdfa: list[dict[str, Any]] = []
        self._script: dict[str, Any] | None = None
        self._tag_index = 0

    def handle_starttag(self, tag: str, attrs: list[tuple[str, str | None]]) -> None:
        self._tag_index += 1
        data = {key.lower(): value for key, value in attrs}
        locator = f"{tag}[{self._tag_index}]"

        if (
            tag.lower() == "script"
            and (data.get("type") or "").lower().split(";")[0].strip()
            == "application/ld+json"
        ):
            self._script = {"locator": locator, "text": ""}

        micro_keys = ("itemscope", "itemtype", "itemprop", "itemid", "itemref")
        if any(key in data for key in micro_keys):
            self.microdata.append(
                {
                    "locator": locator,
                    "tag": tag,
                    "attributes": {
                        key: data.get(key) for key in micro_keys if key in data
                    },
                }
            )

        rdfa_keys = (
            "typeof",
            "property",
            "vocab",
            "prefix",
            "resource",
            "about",
            "rel",
            "rev",
        )
        if any(key in data for key in rdfa_keys):
            self.rdfa.append(
                {
                    "locator": locator,
                    "tag": tag,
                    "attributes": {
                        key: data.get(key) for key in rdfa_keys if key in data
                    },
                }
            )

    def handle_startendtag(
        self, tag: str, attrs: list[tuple[str, str | None]]
    ) -> None:
        self.handle_starttag(tag, attrs)

    def handle_data(self, data: str) -> None:
        if self._script is not None:
            self._script["text"] += data

    def handle_endtag(self, tag: str) -> None:
        if tag.lower() == "script" and self._script is not None:
            self.jsonld_blocks.append(self._script)
            self._script = None

    def close(self) -> None:
        super().close()
        if self._script is not None:
            self.jsonld_blocks.append(self._script)
            self._script = None


def issue(
    severity: str, code: str, message: str, locator: str | None = None
) -> dict[str, str]:
    result = {"severity": severity, "code": code, "message": message}
    if locator:
        result["locator"] = locator
    return result


def read_source(
    source: str, timeout: float, max_bytes: int
) -> tuple[str, dict[str, Any]]:
    if source == "-":
        raw = sys.stdin.buffer.read(max_bytes + 1)
        if len(raw) > max_bytes:
            raise ValueError(f"stdin exceeds --max-bytes ({max_bytes})")
        return raw.decode("utf-8", errors="replace"), {
            "kind": "stdin",
            "bytes": len(raw),
        }

    parsed = urllib.parse.urlparse(source)
    if parsed.scheme in {"http", "https"}:
        request = urllib.request.Request(
            source,
            headers={
                "User-Agent": "seo-schema-static-scanner/1.0 (+structured-data-audit)"
            },
        )
        try:
            with urllib.request.urlopen(request, timeout=timeout) as response:
                content_type = response.headers.get_content_type()
                if content_type not in {"text/html", "application/xhtml+xml"}:
                    raise ValueError(f"expected HTML but received {content_type}")
                raw = response.read(max_bytes + 1)
                if len(raw) > max_bytes:
                    raise ValueError(f"response exceeds --max-bytes ({max_bytes})")
                charset = response.headers.get_content_charset() or "utf-8"
                return raw.decode(charset, errors="replace"), {
                    "kind": "url",
                    "requested_url": source,
                    "final_url": response.geturl(),
                    "status": getattr(response, "status", None),
                    "content_type": content_type,
                    "charset": charset,
                    "bytes": len(raw),
                }
        except urllib.error.HTTPError as exc:
            raise RuntimeError(f"HTTP {exc.code} while fetching {source}") from exc
        except urllib.error.URLError as exc:
            raise RuntimeError(f"could not fetch {source}: {exc.reason}") from exc

    path = Path(source).expanduser()
    if not path.is_file():
        raise FileNotFoundError(f"HTML file not found: {path}")
    if path.stat().st_size > max_bytes:
        raise ValueError(f"file exceeds --max-bytes ({max_bytes})")
    raw = path.read_bytes()
    return raw.decode("utf-8", errors="replace"), {
        "kind": "file",
        "path": str(path.resolve()),
        "bytes": len(raw),
    }


def walk_json(value: Any, path: str = "$"):
    yield path, value
    if isinstance(value, dict):
        for key, child in value.items():
            yield from walk_json(child, f"{path}.{key}")
    elif isinstance(value, list):
        for index, child in enumerate(value):
            yield from walk_json(child, f"{path}[{index}]")


def analyze_jsonld(
    block: dict[str, Any], index: int
) -> tuple[dict[str, Any], list[dict[str, str]]]:
    locator = block["locator"]
    text = block["text"].strip().lstrip("\ufeff")
    findings: list[dict[str, str]] = []
    summary: dict[str, Any] = {
        "block": index,
        "locator": locator,
        "characters": len(text),
        "types": [],
        "ids": [],
        "contexts": [],
        "placeholder_paths": [],
    }
    if not text:
        findings.append(
            issue("error", "empty-jsonld", "JSON-LD block is empty", locator)
        )
        summary["parsed"] = False
        return summary, findings

    try:
        value = json.loads(text, object_pairs_hook=no_duplicate_keys)
    except (json.JSONDecodeError, DuplicateKeyError) as exc:
        findings.append(issue("error", "invalid-json", str(exc), locator))
        summary["parsed"] = False
        return summary, findings

    summary["parsed"] = True
    summary["top_level"] = type(value).__name__
    if not isinstance(value, (dict, list)):
        findings.append(
            issue(
                "error",
                "invalid-top-level",
                "JSON-LD top level should be an object or array",
                locator,
            )
        )

    root_context = None
    if isinstance(value, dict):
        root_context = value.get("@context")
    elif isinstance(value, list):
        root_context = next(
            (
                item.get("@context")
                for item in value
                if isinstance(item, dict) and "@context" in item
            ),
            None,
        )
    if root_context is None:
        findings.append(
            issue("warning", "missing-context", "No top-level @context was found", locator)
        )

    for json_path, child in walk_json(value):
        if isinstance(child, dict):
            schema_type = child.get("@type")
            if isinstance(schema_type, str):
                summary["types"].append(
                    {"path": f"{json_path}.@type", "value": schema_type}
                )
            elif isinstance(schema_type, list):
                for item in schema_type:
                    if isinstance(item, str):
                        summary["types"].append(
                            {"path": f"{json_path}.@type", "value": item}
                        )
            schema_id = child.get("@id")
            if isinstance(schema_id, str):
                summary["ids"].append(
                    {"path": f"{json_path}.@id", "value": schema_id}
                )
            context = child.get("@context")
            if context is not None:
                summary["contexts"].append(
                    {"path": f"{json_path}.@context", "value": context}
                )
            for key in ABSOLUTE_URL_PROPERTIES.intersection(child):
                values = child[key] if isinstance(child[key], list) else [child[key]]
                for item in values:
                    candidate = item.get("@id") if isinstance(item, dict) else item
                    if isinstance(candidate, str) and not PLACEHOLDER_RE.search(
                        candidate
                    ):
                        parsed = urllib.parse.urlparse(candidate)
                        if not parsed.scheme and not candidate.startswith("#"):
                            findings.append(
                                issue(
                                    "warning",
                                    "relative-url",
                                    f"{json_path}.{key} contains a relative URL",
                                    locator,
                                )
                            )
        elif isinstance(child, str) and PLACEHOLDER_RE.search(child):
            summary["placeholder_paths"].append(json_path)

    if summary["placeholder_paths"]:
        findings.append(
            issue(
                "warning",
                "placeholders",
                "JSON-LD contains unresolved placeholder values",
                locator,
            )
        )
    for entry in summary["contexts"]:
        context = entry["value"]
        if isinstance(context, str) and context.rstrip("/") == "http://schema.org":
            findings.append(
                issue(
                    "warning",
                    "http-context",
                    "Use https://schema.org for generated JSON-LD",
                    locator,
                )
            )
    return summary, findings


def analyze_microdata(items: list[dict[str, Any]]) -> list[dict[str, str]]:
    findings: list[dict[str, str]] = []
    for item in items:
        attrs = item["attributes"]
        if "itemscope" in attrs and not attrs.get("itemtype"):
            findings.append(
                issue(
                    "warning",
                    "untyped-itemscope",
                    "Microdata itemscope has no itemtype",
                    item["locator"],
                )
            )
        if "itemprop" in attrs and not attrs.get("itemprop"):
            findings.append(
                issue(
                    "error",
                    "empty-itemprop",
                    "Microdata itemprop is empty",
                    item["locator"],
                )
            )
        itemtype = attrs.get("itemtype")
        if itemtype and "schema.org" not in itemtype:
            findings.append(
                issue(
                    "warning",
                    "non-schema-itemtype",
                    "Microdata itemtype does not reference schema.org",
                    item["locator"],
                )
            )
    return findings


def analyze_rdfa(items: list[dict[str, Any]]) -> list[dict[str, str]]:
    findings: list[dict[str, str]] = []
    has_vocab = any(item["attributes"].get("vocab") for item in items)
    for item in items:
        attrs = item["attributes"]
        if "property" in attrs and not attrs.get("property"):
            findings.append(
                issue(
                    "error",
                    "empty-rdfa-property",
                    "RDFa property is empty",
                    item["locator"],
                )
            )
        if "typeof" in attrs and not attrs.get("typeof"):
            findings.append(
                issue(
                    "error",
                    "empty-rdfa-typeof",
                    "RDFa typeof is empty",
                    item["locator"],
                )
            )
    if items and not has_vocab:
        findings.append(
            issue(
                "warning",
                "rdfa-vocab-unverified",
                "RDFa was found without an explicit vocab attribute; resolve prefixes/context manually",
            )
        )
    return findings


def build_report(source: str, timeout: float, max_bytes: int) -> dict[str, Any]:
    html, metadata = read_source(source, timeout, max_bytes)
    parser = StructuredDataParser()
    parser.feed(html)
    parser.close()

    findings: list[dict[str, str]] = []
    blocks: list[dict[str, Any]] = []
    for index, block in enumerate(parser.jsonld_blocks, start=1):
        summary, block_findings = analyze_jsonld(block, index)
        blocks.append(summary)
        findings.extend(block_findings)
    findings.extend(analyze_microdata(parser.microdata))
    findings.extend(analyze_rdfa(parser.rdfa))

    if not parser.jsonld_blocks and not parser.microdata and not parser.rdfa:
        findings.append(
            issue(
                "opportunity",
                "no-structured-data",
                "No JSON-LD, Microdata, or RDFa signals were found in static source",
            )
        )

    severity_order = {"error": 0, "warning": 1, "opportunity": 2, "info": 3}
    findings.sort(
        key=lambda item: (severity_order.get(item["severity"], 9), item["code"])
    )
    return {
        "source": metadata,
        "summary": {
            "jsonld_blocks": len(parser.jsonld_blocks),
            "microdata_elements": len(parser.microdata),
            "rdfa_elements": len(parser.rdfa),
            "errors": sum(item["severity"] == "error" for item in findings),
            "warnings": sum(item["severity"] == "warning" for item in findings),
            "opportunities": sum(
                item["severity"] == "opportunity" for item in findings
            ),
        },
        "jsonld": blocks,
        "microdata": parser.microdata,
        "rdfa": parser.rdfa,
        "findings": findings,
        "limitations": [
            "Static source only; JavaScript-rendered markup may differ.",
            "Live Schema.org term status, domain/range, Google feature requirements, and content truthfulness require separate validation.",
        ],
    }


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("source", help="HTTP(S) URL, HTML file path, or - for stdin")
    parser.add_argument(
        "--timeout", type=float, default=15.0, help="URL timeout in seconds (default: 15)"
    )
    parser.add_argument(
        "--max-bytes",
        type=int,
        default=10_000_000,
        help="maximum input bytes (default: 10000000)",
    )
    parser.add_argument("--compact", action="store_true", help="emit compact JSON")
    return parser.parse_args()


def main() -> int:
    args = parse_args()
    try:
        report = build_report(args.source, args.timeout, args.max_bytes)
    except (FileNotFoundError, OSError, RuntimeError, UnicodeError, ValueError) as exc:
        print(
            json.dumps(
                {"error": {"type": type(exc).__name__, "message": str(exc)}},
                ensure_ascii=False,
            ),
            file=sys.stderr,
        )
        return 2
    indent = None if args.compact else 2
    print(json.dumps(report, indent=indent, ensure_ascii=False, sort_keys=False))
    return 1 if report["summary"]["errors"] else 0


if __name__ == "__main__":
    raise SystemExit(main())
