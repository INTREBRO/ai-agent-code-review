"""Acquire reproducible PR diffs and bounded source from the pinned base tree."""

import hashlib
import json
import os
import re
import tempfile
from pathlib import Path, PurePosixPath
from urllib.parse import quote, urlparse

import requests


MAX_PATCH_BYTES = 1_000_000
MAX_SOURCE_BYTES = 64_000
MAX_SOURCE_FILES = 200
HUNK = re.compile(r"^@@ -\d+(?:,\d+)? \+(\d+)(?:,\d+)? @@")
SLUG = re.compile(r"[a-z0-9][a-z0-9-]*\Z")
SHA40 = re.compile(r"[0-9a-f]{40}\Z")


def fetch_url(url: str) -> bytes:
    """Fetch a public GitHub URL with an optional token for API rate limits."""
    headers = {"Accept": "application/vnd.github+json"}
    if urlparse(url).hostname == "api.github.com" and os.getenv("GITHUB_TOKEN"):
        headers["Authorization"] = f"Bearer {os.environ['GITHUB_TOKEN']}"
    response = requests.get(url, headers=headers, timeout=30, stream=True)
    response.raise_for_status()
    chunks = []
    total = 0
    for chunk in response.iter_content(chunk_size=64_000):
        total += len(chunk)
        if total > 2_000_000:
            raise ValueError("GitHub response exceeds 2000000 bytes")
        chunks.append(chunk)
    return b"".join(chunks)


def _safe_path(path: str) -> str:
    if not isinstance(path, str) or not path or "\\" in path:
        raise ValueError("unsafe source path")
    parsed = PurePosixPath(path)
    if parsed.is_absolute() or ".." in parsed.parts or "." in parsed.parts:
        raise ValueError("unsafe source path")
    return path


def _added_lines(patch: str) -> set[int]:
    added = set()
    new_line = None
    for text in patch.splitlines():
        match = HUNK.match(text)
        if match:
            new_line = int(match.group(1))
        elif new_line is not None:
            if text.startswith("+"):
                added.add(new_line)
                new_line += 1
            elif text.startswith(" "):
                new_line += 1
    return added


def _identity(case: dict):
    case_id = case.get("id")
    pr_url = case.get("pr_url")
    if not isinstance(case_id, str) or not SLUG.fullmatch(case_id):
        raise ValueError("unsafe case id")
    parsed = urlparse(pr_url or "")
    parts = parsed.path.strip("/").split("/")
    if parsed.scheme != "https" or parsed.hostname != "github.com" or len(parts) != 4 or parts[2] != "pull" or not parts[3].isdigit():
        raise ValueError("invalid pr_url")
    for field in ("base_sha", "head_sha"):
        value = case.get(field)
        if not isinstance(value, str) or not SHA40.fullmatch(value):
            raise ValueError(f"invalid {field}")
    return case_id, parts[0], parts[1]


def _cache_file(cache_root: Path, case_id: str) -> Path:
    cache_root = Path(cache_root)
    if cache_root.is_symlink():
        raise ValueError("cache root cannot be a symlink")
    cache_root.mkdir(parents=True, exist_ok=True)
    cache_file = cache_root / f"{case_id}.json"
    if cache_file.is_symlink() or cache_root.resolve() not in cache_file.resolve().parents:
        raise ValueError("unsafe cache path")
    return cache_file


def prepare_case(case: dict, cache_root: Path, fetch=fetch_url) -> dict:
    """Return exact pinned diff plus old source, never a checkout of PR head."""
    case_id, owner, repo = _identity(case)
    cache_file = _cache_file(cache_root, case_id)
    expected_hash = case.get("diff_sha256")
    if not isinstance(expected_hash, str) or not re.fullmatch(r"[0-9a-f]{64}", expected_hash):
        raise ValueError("diff_sha256 must be a SHA-256 digest")
    if cache_file.exists():
        try:
            cached = json.loads(cache_file.read_text(encoding="utf-8"))
            source_hashes = cached["provenance"]["source_sha256"]
            if (cached["provenance"].get("cache_version") == 2
                    and cached["provenance"]["diff_sha256"] == expected_hash
                    and cached["provenance"]["base_sha"] == case["base_sha"]
                    and cached["provenance"]["head_sha"] == case["head_sha"]
                    and hashlib.sha256(cached["diff"].encode()).hexdigest() == expected_hash
                    and cached["diff"] == "\n".join(
                        f"diff --git a/{item['path']} b/{item['path']}\n{item['patch']}"
                        for item in sorted(cached["patches"], key=lambda item: item["path"]))
                    and source_hashes == {path: hashlib.sha256(content.encode()).hexdigest()
                                          for path, content in cached["base_files"].items()}):
                return cached
        except (OSError, ValueError, KeyError, TypeError):
            pass

    compare_url = f"https://api.github.com/repos/{owner}/{repo}/compare/{case['base_sha']}...{case['head_sha']}"
    comparison = json.loads(fetch(compare_url))
    files = comparison.get("files")
    if not isinstance(files, list):
        raise ValueError("GitHub comparison has no file list")
    patched = sorted((item for item in files if isinstance(item.get("patch"), str)), key=lambda item: item["filename"])
    for item in patched:
        _safe_path(item["filename"])
    diff = "\n".join(f"diff --git a/{item['filename']} b/{item['filename']}\n{item['patch']}" for item in patched)
    if len(diff.encode()) > MAX_PATCH_BYTES:
        raise ValueError("diff exceeds 1000000 bytes")
    digest = hashlib.sha256(diff.encode()).hexdigest()
    if digest != expected_hash:
        raise ValueError("diff_sha256 mismatch: pinned comparison changed or is unavailable")
    changed = {item["filename"]: _added_lines(item["patch"]) for item in patched}
    for issue in case.get("expected", []):
        if issue["line"] not in changed.get(issue["path"], set()):
            raise ValueError(f"expected line is not newly changed: {issue['path']}:{issue['line']}")

    base_files = {}
    skipped = []
    for item in patched:
        path = item["filename"]
        if item.get("status") == "added":
            skipped.append(f"{path}: added file has no base version")
            continue
        if len(base_files) >= MAX_SOURCE_FILES:
            skipped.append(f"{path}: source file limit reached")
            continue
        old_path = _safe_path(item.get("previous_filename", path) if item.get("status") == "renamed" else path)
        raw_url = f"https://raw.githubusercontent.com/{owner}/{repo}/{case['base_sha']}/{quote(old_path, safe='/')}"
        raw = fetch(raw_url)
        if len(raw) > MAX_SOURCE_BYTES:
            skipped.append(f"{path}: source file exceeds {MAX_SOURCE_BYTES} bytes")
            continue
        try:
            base_files[path] = raw.decode("utf-8")
        except UnicodeError:
            skipped.append(f"{path}: source file is not UTF-8")

    result = {"diff": diff, "patches": [{"path": item["filename"], "patch": item["patch"]} for item in patched],
              "base_files": base_files,
              "provenance": {"pr_url": case["pr_url"], "base_sha": case["base_sha"],
                             "head_sha": case["head_sha"], "diff_sha256": digest,
                             "cache_version": 2,
                             "source_scope": "changed files at base commit only", "skipped_sources": skipped,
                             "source_sha256": {path: hashlib.sha256(content.encode()).hexdigest()
                                               for path, content in base_files.items()}}}
    with tempfile.NamedTemporaryFile("w", encoding="utf-8", dir=cache_file.parent, prefix=f"{case_id}-", suffix=".tmp", delete=False) as stream:
        json.dump(result, stream, ensure_ascii=False)
        temporary = Path(stream.name)
    os.replace(temporary, cache_file)
    return result
