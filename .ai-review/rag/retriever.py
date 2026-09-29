"""Cosine similarity search over the local index."""

import math


def _similarity(left, right):
    if len(left) != len(right):
        raise ValueError("Embedding dimensions differ")
    norm = math.sqrt(sum(value * value for value in left)) * math.sqrt(sum(value * value for value in right))
    return sum(a * b for a, b in zip(left, right)) / norm if norm else 0.0


def retrieve(index, query, embeddings, limit=3):
    if not index["chunks"] or not query.strip():
        return []
    vector = embeddings.embed([query])[0]
    ranked = sorted(index["chunks"], key=lambda chunk: _similarity(chunk["vector"], vector), reverse=True)
    return ranked[:limit]
