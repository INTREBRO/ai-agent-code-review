import unittest

from evaluation.lexical_context import retrieve_context


class LexicalContextTests(unittest.TestCase):
    def test_relevant_symbol_ranks_above_unrelated_file(self):
        files = {
            "auth.py": "def authenticate(user):\n    return user.token\n",
            "math.cpp": "int add(int a, int b) { return a + b; }\n",
        }
        results = retrieve_context(files, "authenticate token", max_chars=120)
        self.assertEqual("auth.py", results[0]["path"])
        self.assertEqual(1, results[0]["line"])
        self.assertIn("user.token", results[0]["content"])
        self.assertTrue(all(result["score"] > 0 for result in results))

    def test_equal_scores_use_path_then_line_order(self):
        files = {"z.cpp": "target\n" * 35, "a.c": "target\n" * 35}
        results = retrieve_context(files, "target", max_chars=1000)
        self.assertEqual("a.c", results[0]["path"])
        self.assertLessEqual(results[0]["line"], results[1]["line"] if results[1]["path"] == "a.c" else 999)

    def test_limits_total_content_and_handles_empty_query(self):
        files = {"one.py": "needle item\n" * 90, "two.rs": "needle item\n" * 90}
        results = retrieve_context(files, "needle", max_chars=90)
        self.assertLessEqual(sum(len(item["content"]) for item in results), 90)
        self.assertEqual([], retrieve_context(files, "", max_chars=90))
        self.assertEqual([], retrieve_context(files, "needle", max_chars=0))

    def test_never_reads_files_outside_supplied_base_map(self):
        results = retrieve_context({"base.go": "func valid() { return 1 }"}, "valid head_only_secret")
        self.assertEqual(["base.go"], [item["path"] for item in results])
        self.assertNotIn("head_only_secret", results[0]["content"])


if __name__ == "__main__":
    unittest.main()
