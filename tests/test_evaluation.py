import importlib
import unittest


BENCHMARK = {
    "version": 1,
    "cases": [
        {"id": "sql", "category": "security", "difficulty": "simple", "diff": "+ unsafe query", "expected": [
            {"id": "sql-1", "file": "db.py", "line": 2, "description": "SQL injection"}
        ]},
        {"id": "clean", "category": "correctness", "difficulty": "simple", "diff": "+ safe change", "expected": []},
    ],
}


class EvaluationTests(unittest.TestCase):
    def evaluator(self):
        try:
            return importlib.import_module("evaluation.score")
        except ModuleNotFoundError:
            self.fail("evaluation.score is missing")

    def test_scores_human_matched_issues_and_false_positives(self):
        evaluator = self.evaluator()
        predictions = {"cases": [
            {"id": "sql", "issues": [{"file": "db.py", "line": 2, "message": "Unsafe SQL", "matched_expected_id": "sql-1"}]},
            {"id": "clean", "issues": [{"file": "safe.py", "line": 1, "message": "Maybe risky", "matched_expected_id": None}]},
        ]}
        result = evaluator.score(BENCHMARK, predictions)
        self.assertEqual((1, 1, 0), (result["true_positives"], result["false_positives"], result["false_negatives"]))
        self.assertEqual(0.5, result["precision"])
        self.assertEqual(1.0, result["recall"])
        self.assertEqual(1, result["by_category"]["security"]["true_positives"])

    def test_rejects_duplicate_case_ids_and_unadjudicated_predictions(self):
        evaluator = self.evaluator()
        duplicate = {"version": 1, "cases": BENCHMARK["cases"] * 2}
        with self.assertRaisesRegex(ValueError, "duplicate"):
            evaluator.validate_benchmark(duplicate)
        missing_label = {"cases": [
            {"id": "sql", "issues": [{"file": "db.py", "line": 2, "message": "Unsafe SQL"}]},
            {"id": "clean", "issues": []},
        ]}
        with self.assertRaisesRegex(ValueError, "matched_expected_id"):
            evaluator.score(BENCHMARK, missing_label)

    def test_comparison_requires_same_case_set_and_reports_negative_delta(self):
        evaluator = self.evaluator()
        baseline = {"cases": [
            {"id": "sql", "issues": [{"file": "db.py", "line": 2, "message": "Unsafe SQL", "matched_expected_id": "sql-1"}]},
            {"id": "clean", "issues": []},
        ]}
        rag = {"cases": [{"id": "sql", "issues": []}, {"id": "clean", "issues": []}]}
        result = evaluator.compare(BENCHMARK, baseline, rag)
        self.assertEqual(-1.0, result["delta_recall"])
        with self.assertRaisesRegex(ValueError, "case"):
            evaluator.compare(BENCHMARK, baseline, {"cases": [{"id": "sql", "issues": []}]})

    def test_empty_predictions_have_zero_precision_and_recall(self):
        evaluator = self.evaluator()
        result = evaluator.score(BENCHMARK, {"cases": [{"id": "sql", "issues": []}, {"id": "clean", "issues": []}]})
        self.assertEqual(0.0, result["precision"])
        self.assertEqual(0.0, result["recall"])
        self.assertEqual(1, result["false_negatives"])

    def test_invalid_prediction_case_id_has_clear_validation_error(self):
        evaluator = self.evaluator()
        invalid = {"cases": [{"id": [], "issues": []}, {"id": "clean", "issues": []}]}
        with self.assertRaisesRegex(ValueError, "case id"):
            evaluator.score(BENCHMARK, invalid)

    def test_invalid_match_id_has_clear_validation_error(self):
        evaluator = self.evaluator()
        invalid = {"cases": [
            {"id": "sql", "issues": [{"file": "db.py", "line": 2, "message": "Unsafe", "matched_expected_id": []}]},
            {"id": "clean", "issues": []},
        ]}
        with self.assertRaisesRegex(ValueError, "matched_expected_id"):
            evaluator.score(BENCHMARK, invalid)


if __name__ == "__main__":
    unittest.main()
