"""Deterministic, key-free retrieval from explicitly supplied base-tree files."""

import re
from collections import Counter


TOKEN = re.compile(r"[A-Za-z_][A-Za-z_0-9]*")
WINDOW_LINES = 30
MAX_WINDOW_CHARS = 1200


def _terms(text: str) -> list[str]:
    return [match.group().lower() for match in TOKEN.finditer(text)]


def retrieve_context(base_files: dict[str, str], query: str, max_chars: int = 6000) -> list[dict]:
    """Rank fixed line windows by query-term overlap and cap returned text."""
    if max_chars <= 0:
        return []
    terms = set(_terms(query))
    if not terms:
        return []
    candidates = []
    for path, source in sorted(base_files.items()):
        lines = source.splitlines()
        for offset in range(0, len(lines), WINDOW_LINES):
            content = "\n".join(lines[offset:offset + WINDOW_LINES]).strip()[:MAX_WINDOW_CHARS]
            if not content:
                continue
            counts = Counter(_terms(content))
            score = sum(min(counts[term], 3) for term in terms)
            if score:
                candidates.append({"path": path, "line": offset + 1, "content": content, "score": score})
    candidates.sort(key=lambda item: (-item["score"], item["path"], item["line"]))
    results = []
    remaining = max_chars
    for item in candidates:
        if remaining <= 0:
            break
        content = item["content"][:remaining]
        if content:
            results.append(dict(item, content=content))
            remaining -= len(content)
    return results
