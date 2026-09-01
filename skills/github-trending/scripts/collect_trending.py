#!/usr/bin/env python3
"""Collect AI-workflow repositories from GitHub's daily Trending page."""

from __future__ import annotations

import argparse
import base64
import json
import re
import sys
from html.parser import HTMLParser
from pathlib import Path
from typing import Any
from urllib.error import HTTPError, URLError
from urllib.parse import quote
from urllib.request import Request, urlopen


TRENDING_URL = "https://github.com/trending?since=daily"
API_ROOT = "https://api.github.com"
USER_AGENT = "github-trending-codex-skill/1.0"
VOID_TAGS = {"area", "base", "br", "col", "embed", "hr", "img", "input", "link", "meta", "param", "source", "track", "wbr"}
REPO_PATH = re.compile(r"^/([A-Za-z0-9](?:[A-Za-z0-9-]{0,38})/[A-Za-z0-9._-]+)$")
STARS_TODAY = re.compile(r"([0-9][0-9,]*)\s+stars?\s+today", re.IGNORECASE)
PLATFORM_PATTERNS = {
    "ChatGPT/OpenAI": [
        re.compile(r"\bchatgpt\b", re.IGNORECASE),
        re.compile(r"\bopenai(?:[- ]compatible)?\b", re.IGNORECASE),
        re.compile(r"\bgpt[- ]?[345](?:\.\d+)?\b", re.IGNORECASE),
    ],
    "Claude/Anthropic": [
        re.compile(r"\bclaude(?:\s+code)?\b", re.IGNORECASE),
        re.compile(r"\banthropic\b", re.IGNORECASE),
    ],
    "Grok/xAI": [
        re.compile(r"\bgrok(?:[- ]?[0-9]+)?\b", re.IGNORECASE),
        re.compile(r"\bxai\b|\bx\.ai\b", re.IGNORECASE),
    ],
}


class TrendingParser(HTMLParser):
    """Extract repository paths and daily star counts from Trending cards."""

    def __init__(self) -> None:
        super().__init__(convert_charrefs=True)
        self.depth = 0
        self.repo: str | None = None
        self.text_parts: list[str] = []
        self.items: list[dict[str, Any]] = []

    def handle_starttag(self, tag: str, attrs: list[tuple[str, str | None]]) -> None:
        attr = dict(attrs)
        classes = set((attr.get("class") or "").split())
        if tag == "article" and "Box-row" in classes and self.depth == 0:
            self.depth = 1
            self.repo = None
            self.text_parts = []
            return

        if self.depth:
            if tag not in VOID_TAGS:
                self.depth += 1
            if tag == "a" and self.repo is None:
                match = REPO_PATH.match(attr.get("href") or "")
                if match:
                    self.repo = match.group(1)

    def handle_startendtag(self, tag: str, attrs: list[tuple[str, str | None]]) -> None:
        return

    def handle_endtag(self, tag: str) -> None:
        if not self.depth:
            return
        self.depth -= 1
        if self.depth == 0:
            if self.repo:
                text = " ".join(" ".join(self.text_parts).split())
                match = STARS_TODAY.search(text)
                self.items.append(
                    {
                        "full_name": self.repo,
                        "stars_today": int(match.group(1).replace(",", "")) if match else None,
                    }
                )
            self.repo = None
            self.text_parts = []

    def handle_data(self, data: str) -> None:
        if self.depth and data.strip():
            self.text_parts.append(data.strip())


def read_env_value(path: Path, key: str) -> str | None:
    if not path.is_file():
        raise FileNotFoundError(f"Environment file not found: {path}")
    for raw_line in path.read_text(encoding="utf-8").splitlines():
        line = raw_line.strip()
        if not line or line.startswith("#"):
            continue
        if line.startswith("export "):
            line = line[7:].lstrip()
        name, separator, value = line.partition("=")
        if separator and name.strip() == key:
            value = value.strip()
            if len(value) >= 2 and value[0] == value[-1] and value[0] in {"'", '"'}:
                value = value[1:-1]
            return value or None
    return None


def request_bytes(url: str, token: str | None = None, accept: str | None = None) -> bytes:
    headers = {"User-Agent": USER_AGENT}
    if token:
        headers["Authorization"] = f"Bearer {token}"
        headers["X-GitHub-Api-Version"] = "2022-11-28"
    if accept:
        headers["Accept"] = accept
    request = Request(url, headers=headers)
    with urlopen(request, timeout=30) as response:
        return response.read()


def api_json(path: str, token: str) -> dict[str, Any]:
    payload = request_bytes(
        f"{API_ROOT}{path}",
        token=token,
        accept="application/vnd.github+json",
    )
    return json.loads(payload.decode("utf-8"))


def readme_text(full_name: str, token: str) -> str:
    try:
        payload = api_json(f"/repos/{quote(full_name, safe='/')}/readme", token)
    except HTTPError as error:
        if error.code == 404:
            return ""
        raise
    if payload.get("encoding") != "base64" or not payload.get("content"):
        return ""
    try:
        return base64.b64decode(payload["content"], validate=False).decode("utf-8", errors="replace")
    except (ValueError, TypeError):
        return ""


def compatibility_evidence(readme: str) -> tuple[list[str], dict[str, str]]:
    platforms: list[str] = []
    evidence: dict[str, str] = {}
    flattened = " ".join(readme.split())
    for platform, patterns in PLATFORM_PATTERNS.items():
        matches = [match for pattern in patterns if (match := pattern.search(flattened))]
        if not matches:
            continue
        match = min(matches, key=lambda item: item.start())
        start = max(0, match.start() - 140)
        end = min(len(flattened), match.end() + 180)
        snippet = flattened[start:end].strip()
        if start:
            snippet = "…" + snippet
        if end < len(flattened):
            snippet += "…"
        platforms.append(platform)
        evidence[platform] = snippet
    return platforms, evidence


def collect(token: str, limit: int) -> dict[str, Any]:
    html = request_bytes(TRENDING_URL).decode("utf-8", errors="replace")
    parser = TrendingParser()
    parser.feed(html)
    if not parser.items:
        raise RuntimeError("GitHub Trending returned no parseable repository cards")

    results: list[dict[str, Any]] = []
    seen: set[str] = set()
    warnings: list[str] = []
    for rank, candidate in enumerate(parser.items, start=1):
        full_name = candidate["full_name"]
        normalized = full_name.casefold()
        if normalized in seen:
            continue
        seen.add(normalized)
        try:
            metadata = api_json(f"/repos/{quote(full_name, safe='/')}", token)
            if metadata.get("private") or int(metadata.get("stargazers_count") or 0) <= 50:
                continue
            readme = readme_text(full_name, token)
        except HTTPError as error:
            warnings.append(f"Could not inspect {full_name}: GitHub API returned HTTP {error.code}")
            continue

        platforms, evidence = compatibility_evidence(readme)
        if not platforms:
            continue
        results.append(
            {
                "trending_rank": rank,
                "full_name": metadata.get("full_name", full_name),
                "url": metadata.get("html_url", f"https://github.com/{full_name}"),
                "description": metadata.get("description"),
                "total_stars": metadata.get("stargazers_count"),
                "stars_today": candidate.get("stars_today"),
                "language": metadata.get("language"),
                "topics": metadata.get("topics") or [],
                "platforms": platforms,
                "compatibility_evidence": evidence,
                "updated_at": metadata.get("updated_at"),
            }
        )
        if len(results) >= limit:
            break

    return {
        "source": TRENDING_URL,
        "scope": "daily, all languages, public repositories",
        "minimum_total_stars_exclusive": 50,
        "candidate_count": len(parser.items),
        "result_count": len(results),
        "results": results,
        "warnings": warnings,
    }


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--env-file", default="./.env", help="Path containing GITHUB_TOKEN")
    parser.add_argument("--limit", type=int, default=10, help="Maximum results; hard-capped at 10")
    return parser.parse_args()


def main() -> int:
    args = parse_args()
    limit = max(1, min(args.limit, 10))
    try:
        token = read_env_value(Path(args.env_file), "GITHUB_TOKEN")
        if not token:
            raise ValueError(f"GITHUB_TOKEN is missing from {args.env_file}")
        result = collect(token, limit)
    except (FileNotFoundError, ValueError, RuntimeError, HTTPError, URLError, TimeoutError) as error:
        print(json.dumps({"error": str(error)}, indent=2), file=sys.stderr)
        return 1
    print(json.dumps(result, indent=2, ensure_ascii=False))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
