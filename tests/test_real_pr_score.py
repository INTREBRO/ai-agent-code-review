import unittest

from evaluation.real_pr_score import score_adjudicated, compare_adjudicated


MANIFEST = {"cases": [
    {"id": "one", "source": "cloud-aeye-cpp", "language": "C++", "expected": [
        {"id": "bug", "path": "a.cpp", "line": 8, "category": "logic_error"}]},
    {"id": "two", "source": "aacr-bench", "language": "Python", "expected": [
        {"id": "bug", "path": "b.py", "line": 3, "category": "logic_error"}]},
]}


class RealPrScoreTests(unittest.TestCase):
    def test_requires_complete_human_labels_and_counts_misses(self):
        labels = {"cases": [
            {"id": "one", "issues": [{"file": "a.cpp", "line": 8, "message": "bug", "verdict": "matched", "matched_expected_id": "bug"}]},
            {"id": "two", "issues": [{"file": "b.py", "line": 3, "message": "unrelated", "verdict": "false_positive", "matched_expected_id": None}]},
        ]}
        result = score_adjudicated(MANIFEST, labels)
        self.assertEqual((1, 1, 1), (result["true_positives"], result["false_positives"], result["false_negatives"]))
        self.assertEqual(.5, result["precision"])
        self.assertEqual(.5, result["recall"])
        self.assertEqual(1, result["by_source"]["aacr-bench"]["false_positives"])

    def test_unreviewed_issue_cannot_be_scored(self):
        labels = {"cases": [{"id": "one", "issues": [{"file": "a.cpp", "line": 8, "message": "x"}]},
                            {"id": "two", "issues": []}]}
        with self.assertRaisesRegex(ValueError, "verdict"):
            score_adjudicated(MANIFEST, labels)

    def test_case_coverage_must_be_complete(self):
        with self.assertRaisesRegex(ValueError, "case ids"):
            score_adjudicated(MANIFEST, {"cases": [{"id": "one", "issues": []}]})

    def test_matching_requires_exact_location_and_unique_gold(self):
        labels = {"cases": [{"id": "one", "issues": [
            {"file": "a.cpp", "line": 9, "message": "x", "verdict": "matched", "matched_expected_id": "bug"}]},
            {"id": "two", "issues": []}]}
        with self.assertRaisesRegex(ValueError, "location"):
            score_adjudicated(MANIFEST, labels)
        labels["cases"][0]["issues"][0]["line"] = 8
        labels["cases"][0]["issues"].append(dict(labels["cases"][0]["issues"][0]))
        with self.assertRaisesRegex(ValueError, "duplicate"):
            score_adjudicated(MANIFEST, labels)

    def test_compare_reports_delta_without_claiming_significance(self):
        empty = {"cases": [{"id": "one", "issues": []}, {"id": "two", "issues": []}]}
        hit = {"cases": [{"id": "one", "issues": [
            {"file": "a.cpp", "line": 8, "message": "x", "verdict": "matched", "matched_expected_id": "bug"}]},
            {"id": "two", "issues": []}]}
        self.assertEqual(.5, compare_adjudicated(MANIFEST, empty, hit)["delta_recall"])


if __name__ == "__main__":
    unittest.main()
