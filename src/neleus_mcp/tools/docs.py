from __future__ import annotations

import json
import os
import re
from functools import lru_cache
from pathlib import Path
from typing import Any

# Environment variables the user can set to point at the manifest.
# NELEUS_DOCS_MANIFEST_PATH: direct path to page-manifest.json
# NELEUS_DOCS_REPO: path to the neleus repo root (manifest resolved from there)
_MANIFEST_PATH_ENV = "NELEUS_DOCS_MANIFEST_PATH"
_REPO_ROOT_ENV = "NELEUS_DOCS_REPO"
_MANIFEST_RELATIVE = Path("docs/assets/ai/page-manifest.json")


def _candidate_paths() -> list[Path]:
    candidates: list[Path] = []

    if val := os.environ.get(_MANIFEST_PATH_ENV):
        candidates.append(Path(val).expanduser())

    if val := os.environ.get(_REPO_ROOT_ENV):
        candidates.append(Path(val).expanduser() / _MANIFEST_RELATIVE)

    # Sibling-repo layout: /projects/neleus and /projects/neleus-mcp
    candidates.append(Path(__file__).resolve().parents[3].parent / "neleus" / _MANIFEST_RELATIVE)

    return candidates


def _resolve_manifest() -> Path:
    for path in _candidate_paths():
        if path.is_file():
            return path
    checked = ", ".join(str(p) for p in _candidate_paths())
    raise FileNotFoundError(
        f"Neleus docs manifest not found. Checked: {checked}. "
        f"Set {_MANIFEST_PATH_ENV} or {_REPO_ROOT_ENV}, "
        f"or run 'mkdocs build' in the neleus repo first."
    )


@lru_cache(maxsize=1)
def _load_manifest() -> dict[str, Any]:
    return json.loads(_resolve_manifest().read_text(encoding="utf-8"))


def _pages() -> dict[str, dict[str, Any]]:
    pages = _load_manifest().get("pages")
    if not isinstance(pages, dict):
        raise ValueError("page-manifest.json is missing a valid 'pages' object.")
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
        # Exact phrase matches weighted highest; token matches as fallback
        if q in title:
            score += 60
        if q in route.lower():
            score += 40
        if q in summary:
            score += 30
        if q in markdown:
            score += 20
        for t in tokens:
            if t in title:
                score += 10
            if t in section:
                score += 4
            if t in summary:
                score += 4
            if t in markdown:
                score += 2

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
        raise ValueError(
            f"Unknown route {route!r}. Known routes: {known}"
        )
    result = _page_summary(key, page)
    result["markdown"] = page.get("markdown", "")
    return result
