import json
import io
import tempfile
import unittest
from pathlib import Path
from unittest.mock import Mock, patch

from evaluation.run import DeepSeekReviewer, main, run_cases
from tests.test_real_pr_schema import valid_manifest


def prepared(patches=None):
    return {
        "id": "case-1",
        "patches": patches or [{"path": "src/auth.py", "patch": "@@ -1 +1 @@\n-old\n+authenticate(user)"}],
        "base_files": {"src/auth.py": "def authenticate(user):\n    return user.token\n"},
        "provenance": {"base_sha": "a" * 40, "head_sha": "b" * 40, "diff_sha256": "c" * 64},
    }


class FakeReviewer:
    model = "deepseek-flash"

    def __init__(self, result=None):
        self.calls = []
        self.result = result or {"issues": [], "summary": "ok", "usage": {"total_tokens": 12}, "raw_response": '{"issues": []}'}

    def __call__(self, patch, path, context):
        self.calls.append((patch, path, context))
        return self.result


class RealPrRunTests(unittest.TestCase):
    def test_dry_run_never_calls_model(self):
        reviewer = FakeReviewer()
        with tempfile.TemporaryDirectory() as directory:
            report = run_cases({"cases": [{"id": "case-1"}]}, [prepared()], "diff", Path(directory), reviewer, 0, True)
            self.assertEqual([], list(Path(directory).rglob("*.json")))
        self.assertEqual(0, report["calls_made"])
        self.assertEqual(1, report["planned_files"])
        self.assertEqual([], reviewer.calls)

    def test_call_cap_and_resume_are_per_file(self):
        patches = [{"path": "a.py", "patch": "+one"}, {"path": "b.py", "patch": "+two"}]
        reviewer = FakeReviewer()
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            first = run_cases({"cases": [{"id": "case-1"}]}, [prepared(patches)], "diff", root, reviewer, 1, False)
            self.assertEqual((1, 1), (first["calls_made"], first["completed_files"]))
            second = run_cases({"cases": [{"id": "case-1"}]}, [prepared(patches)], "diff", root, reviewer, 1, False)
            self.assertEqual((1, 2), (second["calls_made"], second["completed_files"]))
            third = run_cases({"cases": [{"id": "case-1"}]}, [prepared(patches)], "diff", root, reviewer, 1, False)
            self.assertEqual(0, third["calls_made"])
            artifacts = list(root.rglob("*.json"))
        self.assertEqual(2, len(artifacts))
        self.assertEqual(2, len(reviewer.calls))

    def test_malformed_model_result_is_error_not_clean(self):
        reviewer = FakeReviewer({"summary": "missing issues"})
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            report = run_cases({"cases": [{"id": "case-1"}]}, [prepared()], "diff", root, reviewer, 1, False)
            artifact = json.loads(next(root.rglob("*.json")).read_text(encoding="utf-8"))
        self.assertEqual(1, report["failed_files"])
        self.assertEqual("error", artifact["status"])
        self.assertNotIn("issues", artifact)

    def test_context_is_the_only_input_difference(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            diff_reviewer, lexical_reviewer = FakeReviewer(), FakeReviewer()
            run_cases({"cases": [{"id": "case-1"}]}, [prepared()], "diff", root, diff_reviewer, 1, False)
            run_cases({"cases": [{"id": "case-1"}]}, [prepared()], "lexical", root, lexical_reviewer, 1, False)
        self.assertEqual(diff_reviewer.calls[0][:2], lexical_reviewer.calls[0][:2])
        self.assertEqual("", diff_reviewer.calls[0][2])
        self.assertIn("user.token", lexical_reviewer.calls[0][2])

    def test_oversized_patch_is_skipped_not_truncated(self):
        reviewer = FakeReviewer()
        huge = prepared([{"path": "src/auth.py", "patch": "+" + "x" * 12_001}])
        with tempfile.TemporaryDirectory() as directory:
            report = run_cases({"cases": [{"id": "case-1"}]}, [huge], "diff", Path(directory), reviewer, 1, False)
        self.assertEqual(0, report["calls_made"])
        self.assertEqual(1, report["skipped_files"])

    def test_deepseek_adapter_returns_parsed_issues_usage_and_raw_text(self):
        reply = Mock()
        reply.json.return_value = {
            "choices": [{"message": {"content": '{"issues": [{"line": 1, "message": "Bug"}], "summary": "Found"}'}}],
            "usage": {"prompt_tokens": 42, "completion_tokens": 9, "total_tokens": 51},
        }
        reply.raise_for_status.return_value = None
        with patch("requests.post", return_value=reply) as request:
            adapter = DeepSeekReviewer("test-key")
            result = adapter("+bad", "a.py", "base context")
        self.assertEqual("Bug", result["issues"][0]["message"])
        self.assertEqual(51, result["usage"]["total_tokens"])
        self.assertIn("Found", result["raw_response"])
        self.assertEqual("https://api.deepseek.com/chat/completions", request.call_args.args[0])

    def test_cli_dry_run_has_no_model_call(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            manifest_file = root / "manifest.json"
            manifest_file.write_text(json.dumps(valid_manifest()), encoding="utf-8")
            prepared_case = prepared()
            with patch("evaluation.run.prepare_case", return_value=prepared_case), \
                 patch("evaluation.run.DeepSeekReviewer", side_effect=AssertionError("model created")), \
                 patch("sys.stdout", new_callable=io.StringIO) as output:
                code = main(["--manifest", str(manifest_file), "--cache-root", str(root / "cache"),
                             "--out", str(root / "out"), "--mode", "diff"])
            self.assertEqual(0, code)
            self.assertEqual(0, json.loads(output.getvalue())["calls_made"])

    def test_cli_refuses_live_run_without_call_cap(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            manifest_file = root / "manifest.json"
            manifest_file.write_text(json.dumps(valid_manifest()), encoding="utf-8")
            with patch("sys.stderr", new_callable=io.StringIO), self.assertRaises(SystemExit):
                main(["--manifest", str(manifest_file), "--cache-root", str(root / "cache"),
                      "--out", str(root / "out"), "--mode", "diff", "--live"])


if __name__ == "__main__":
    unittest.main()
