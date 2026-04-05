from __future__ import annotations

import json
import os
import re
import time
import urllib.request
from pathlib import Path
from typing import Any

_MANIFEST_URL = "https://auralshin.github.io/neleus/assets/ai/page-manifest.json"
_MANIFEST_URL_ENV = "NELEUS_DOCS_URL"      # override the URL entirely
_MANIFEST_PATH_ENV = "NELEUS_DOCS_MANIFEST_PATH"  # use a local file instead of fetching
_CACHE_TTL = 3600  # seconds; re-fetch at most once per hour

_cache: dict[str, Any] | None = None
_cache_at: float = 0.0


def _fetch_manifest() -> dict[str, Any]:
    # Local file override — useful during docs development or offline use.
    if path_override := os.environ.get(_MANIFEST_PATH_ENV):
        return json.loads(Path(path_override).expanduser().read_text(encoding="utf-8"))

    url = os.environ.get(_MANIFEST_URL_ENV, _MANIFEST_URL)
    with urllib.request.urlopen(url, timeout=10) as resp:
        return json.loads(resp.read().decode("utf-8"))


def _manifest() -> dict[str, Any]:
    global _cache, _cache_at
    if _cache is None or (time.monotonic() - _cache_at) > _CACHE_TTL:
        _cache = _fetch_manifest()
        _cache_at = time.monotonic()
    return _cache


def _pages() -> dict[str, dict[str, Any]]:
    pages = _manifest().get("pages")
    if not isinstance(pages, dict):
        raise ValueError("Neleus docs manifest is missing a valid 'pages' object.")
    return pages


def _normalize_route(route: str) -> str:
    r = route.strip().strip("/")
    if r in {"", "home", "index"}:
        return ""
    return r[:-3] if r.endswith(".md") else r


def _page_summary(route: str, page: dict[str, Any]) -> dict[str, Any]:
    return {
        "route": route,
        "title": page.get("title", ""),
        "section": page.get("section", ""),
        "summary": page.get("summary", ""),
        "canonical_url": page.get("canonical_url", ""),
        "markdown_url": page.get("markdown_url", ""),
        "source_path": page.get("source_path", ""),
    }


def list_docs() -> list[dict[str, Any]]:
    docs = [_page_summary(route, page) for route, page in _pages().items()]
    return sorted(docs, key=lambda d: (d["section"], d["title"], d["route"]))


def _excerpt(markdown: str, query: str, window: int = 220) -> str:
    flat = re.sub(r"\s+", " ", markdown).strip()
    if not flat:
        return ""
    idx = flat.lower().find(query.lower())
    if idx == -1:
        for token in re.split(r"\W+", query.lower()):
            if token:
                idx = flat.lower().find(token)
                if idx != -1:
                    break
    if idx == -1:
        return flat[:window].strip()
    start = max(0, idx - window // 3)
    end = min(len(flat), idx + (2 * window) // 3)
    snippet = flat[start:end].strip()
    if start > 0:
        snippet = f"...{snippet}"
    if end < len(flat):
        snippet = f"{snippet}..."
    return snippet


def search_docs(query: str, limit: int = 5) -> list[dict[str, Any]]:
    q = query.strip().lower()
    if not q:
        raise ValueError("query must not be empty")

    tokens = [t for t in re.split(r"\W+", q) if t]
    scored: list[tuple[int, dict[str, Any]]] = []

    for route, page in _pages().items():
        title = str(page.get("title", "")).lower()
        section = str(page.get("section", "")).lower()
        summary = str(page.get("summary", "")).lower()
        markdown = str(page.get("markdown", "")).lower()

        score = 0
        if q in title:       score += 60
        if q in route.lower(): score += 40
        if q in summary:     score += 30
        if q in markdown:    score += 20
        for t in tokens:
            if t in title:   score += 10
            if t in section: score += 4
            if t in summary: score += 4
            if t in markdown: score += 2

        if score <= 0:
            continue

        result = _page_summary(route, page)
        result["excerpt"] = _excerpt(str(page.get("markdown", "")), query)
        scored.append((score, result))

    scored.sort(key=lambda x: (-x[0], x[1]["section"], x[1]["title"]))
    return [r for _, r in scored[:limit]]


def read_doc(route: str) -> dict[str, Any]:
    key = _normalize_route(route)
    page = _pages().get(key)
    if page is None:
        known = ", ".join(sorted(_pages().keys()))
        raise ValueError(f"Unknown route {route!r}. Known routes: {known}")
    result = _page_summary(key, page)
    result["markdown"] = page.get("markdown", "")
    return result
