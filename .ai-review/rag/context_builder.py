"""Render retrieved chunks within a fixed prompt budget."""


def build_context(chunks, max_chars=6000):
    parts = []
    used = 0
    for chunk in chunks:
        item = f'{chunk["path"]}:{chunk["line"]}\n{chunk["content"]}\n'
        remaining = max_chars - used
        if remaining <= 0:
            break
        parts.append(item[:remaining])
        used += min(len(item), remaining)
    return "\n".join(parts)[:max_chars]
