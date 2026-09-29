"""Map a unified PR patch to commentable old/new file lines."""

import re


HUNK = re.compile(r"^@@ -(\d+)(?:,\d+)? \+(\d+)(?:,\d+)? @@")


def changed_locations(patch):
    locations = set()
    old_line = new_line = None
    for text in patch.splitlines():
        match = HUNK.match(text)
        if match:
            old_line, new_line = map(int, match.groups())
            continue
        if old_line is None:
            continue
        if text.startswith("-"):
            locations.add((old_line, "LEFT"))
            old_line += 1
        elif text.startswith("+"):
            locations.add((new_line, "RIGHT"))
            new_line += 1
        elif text.startswith(" "):
            old_line += 1
            new_line += 1
    return locations


def place_issue(issue, filename, patch):
    line = issue.get("line")
    side = issue.get("side")
    if issue.get("file") != filename or isinstance(line, bool) or not isinstance(line, int) or line < 1:
        return None
    if side not in (None, "LEFT", "RIGHT"):
        return None
    locations = changed_locations(patch)
    for candidate in ((side,) if side else ("RIGHT", "LEFT")):
        if (line, candidate) in locations:
            return {"path": filename, "line": line, "side": candidate}
    return None
