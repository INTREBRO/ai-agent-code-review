"""Bounded source discovery, chunking and a local JSON embedding cache."""

import hashlib
import json
import os
from pathlib import Path


EXTENSIONS = {".py", ".js", ".jsx", ".ts", ".tsx", ".java", ".go", ".rs", ".md"}
EXCLUDED = {".git", ".venv", "venv", "node_modules", "dist", "build", "coverage", "__pycache__", "htmlcov"}
MAX_FILES = 200
MAX_FILE_BYTES = 64_000
CHUNK_LINES = 80
MAX_CHUNK_CHARS = 8000
MAX_CHUNKS = 400


def discover_files(root):
    root = Path(root).resolve()
    found = []
    for directory, folders, files in os.walk(root):
        folders[:] = sorted(folder for folder in folders if folder not in EXCLUDED and not folder.startswith("."))
        for name in sorted(files):
            path = Path(directory) / name
            if name.startswith(".") or path.suffix.lower() not in EXTENSIONS or path.is_symlink():
                continue
            if path.stat().st_size <= MAX_FILE_BYTES:
                found.append(path)
                if len(found) >= MAX_FILES:
                    return found
    return found


def build_index(root, embeddings, cache_path):
    root = Path(root).resolve()
    cache_path = Path(cache_path)
    chunks = []
    for path in discover_files(root):
        try:
            lines = path.read_text(encoding="utf-8").splitlines()
        except (UnicodeError, OSError):
            continue
        for offset in range(0, len(lines), CHUNK_LINES):
            content = "\n".join(lines[offset:offset + CHUNK_LINES]).strip()[:MAX_CHUNK_CHARS]
            if content:
                chunks.append({"path": path.relative_to(root).as_posix(), "line": offset + 1, "content": content})
                if len(chunks) >= MAX_CHUNKS:
                    break
        if len(chunks) >= MAX_CHUNKS:
            break
    digest = hashlib.sha256(json.dumps(chunks, sort_keys=True).encode("utf-8")).hexdigest()
    if cache_path.is_file():
        try:
            cached = json.loads(cache_path.read_text(encoding="utf-8"))
            if cached.get("digest") == digest and cached.get("model") == embeddings.model:
                return cached
        except (ValueError, OSError):
            pass
    vectors = []
    for offset in range(0, len(chunks), 8):
        batch = chunks[offset:offset + 8]
        vectors.extend(embeddings.embed([item["content"] for item in batch]))
    if len(vectors) != len(chunks):
        raise ValueError("Embedding count does not match chunk count")
    index = {"model": embeddings.model, "digest": digest, "chunks": [dict(chunk, vector=vector) for chunk, vector in zip(chunks, vectors)]}
    cache_path.parent.mkdir(parents=True, exist_ok=True)
    cache_path.write_text(json.dumps(index, ensure_ascii=False), encoding="utf-8")
    return index
