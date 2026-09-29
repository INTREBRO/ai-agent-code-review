import importlib
import sys
import unittest
from pathlib import Path


sys.path.insert(0, str(Path(__file__).resolve().parents[1] / ".ai-review"))


class DiffLineTests(unittest.TestCase):
    def mapper(self):
        try:
            return importlib.import_module("diff_lines")
        except ModuleNotFoundError:
            self.fail("diff_lines module is missing")

    def test_maps_added_and_deleted_lines_across_hunks(self):
        mapper = self.mapper()
        patch = "@@ -10,2 +10,2 @@\n-old\n+new\n context\n@@ -30 +30 @@\n-before\n+after"
        self.assertEqual({(10, "LEFT"), (10, "RIGHT"), (30, "LEFT"), (30, "RIGHT")}, mapper.changed_locations(patch))

    def test_prefers_added_line_and_rejects_nonchanged_line(self):
        mapper = self.mapper()
        patch = "@@ -10,2 +10,2 @@\n-old\n+new\n context"
        self.assertEqual({"path": "a.py", "line": 10, "side": "RIGHT"}, mapper.place_issue({"file": "a.py", "line": 10}, "a.py", patch))
        self.assertIsNone(mapper.place_issue({"file": "a.py", "line": 11}, "a.py", patch))

    def test_rejects_wrong_path_and_invalid_hints(self):
        mapper = self.mapper()
        patch = "@@ -1 +1 @@\n-old\n+new"
        self.assertIsNone(mapper.place_issue({"file": "old.py", "line": 1}, "new.py", patch))
        self.assertIsNone(mapper.place_issue({"file": "new.py", "line": "1"}, "new.py", patch))
        self.assertIsNone(mapper.place_issue({"file": "new.py", "line": 1, "side": "SIDEWAYS"}, "new.py", patch))


if __name__ == "__main__":
    unittest.main()
