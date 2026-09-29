import importlib.util
import io
import json
import os
import sys
import tempfile
import unittest
from pathlib import Path
from types import ModuleType
from unittest.mock import Mock, patch


ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / ".ai-review"))


def load_reviewer():
    spec = importlib.util.spec_from_file_location("reviewer_for_workflow_tests", ROOT / ".ai-review" / "ai-agent-review.py")
    module = importlib.util.module_from_spec(spec)
    with patch.dict(sys.modules, {"requests": ModuleType("requests")}):
        spec.loader.exec_module(module)
    module.requests = Mock()
    return module


def response(payload):
    result = Mock()
    result.json.return_value = payload
    return result


class ReviewWorkflowTests(unittest.TestCase):
    def test_fetches_all_pr_file_pages(self):
        module = load_reviewer()
        module.requests.get.side_effect = [response([{"filename": f"file{i}.py"} for i in range(100)]), response([{"filename": "last.py"}])]
        files = module.GitHubClient("token", "owner/repo", "3").get_pr_diff()
        self.assertEqual(101, len(files))
        self.assertEqual("last.py", files[-1]["filename"])
        self.assertEqual(2, module.requests.get.call_count)

    def test_github_failure_is_not_reported_as_empty_diff(self):
        module = load_reviewer()
        module.requests.get.side_effect = RuntimeError("GitHub unavailable")
        with self.assertRaisesRegex(RuntimeError, "GitHub unavailable"):
            module.GitHubClient("token", "owner/repo", "3").get_pr_diff()

    def test_repeat_run_updates_its_existing_bot_comment(self):
        module = load_reviewer()
        module.requests.get.return_value = response([{
            "id": 42,
            "body": "<!-- ai-agent-code-review -->\nold review",
            "user": {"login": "github-actions[bot]", "type": "Bot"},
        }])
        client = module.GitHubClient("token", "owner/repo", "3")
        client.post_review_comment([{"severity": "warning", "file": "auth.py", "message": "Bug"}], "Reviewed")
        self.assertEqual(1, module.requests.patch.call_count)
        self.assertEqual(0, module.requests.post.call_count)
        self.assertIn("Bug", module.requests.patch.call_args.kwargs["json"]["body"])

    def test_model_error_fails_instead_of_posting_clean_review(self):
        module = load_reviewer()
        module.requests.post.side_effect = RuntimeError("OpenAI unavailable")
        with self.assertRaisesRegex(RuntimeError, "OpenAI unavailable"):
            module.AICodeReviewer("key").generate_review("+ change", "auth.py")

    def test_review_model_can_be_selected_for_demo(self):
        module = load_reviewer()
        module.requests.post.return_value = response({"choices": [{"message": {"content": '{"issues": [], "summary": "ok"}'}}]})
        with patch.dict(os.environ, {"OPENAI_MODEL": "gpt-4.1-mini"}):
            module.AICodeReviewer("key").generate_review("+ change", "auth.py")
        self.assertEqual("gpt-4.1-mini", module.requests.post.call_args.kwargs["json"]["model"])

    def test_malformed_model_output_is_not_treated_as_no_issues(self):
        module = load_reviewer()
        with self.assertRaises((ValueError, json.JSONDecodeError)):
            module.AICodeReviewer("key")._parse_review("not JSON")

    def test_pr_without_text_patch_reports_skipped_files_without_clean_comment(self):
        module = load_reviewer()
        module.OPENAI_API_KEY = "key"
        module.GITHUB_TOKEN = "token"
        module.PR_NUMBER = "3"
        module.REPO_NAME = "owner/repo"
        module.requests.get.return_value = response([{"filename": "image.png", "patch": None}])
        previous = Path.cwd()
        with tempfile.TemporaryDirectory() as directory, patch.dict(os.environ, {"RAG_ENABLED": "false"}), patch.object(module.sys, "stdout", io.StringIO()):
            try:
                os.chdir(directory)
                module.main()
                report = json.loads(Path("review-report.json").read_text(encoding="utf-8"))
            finally:
                os.chdir(previous)
        self.assertEqual(["image.png"], report["skipped_files"])
        self.assertEqual(0, report["reviewed_files"])
        module.requests.post.assert_not_called()

    def test_real_review_produces_report_and_comment(self):
        module = load_reviewer()
        module.OPENAI_API_KEY = "key"
        module.GITHUB_TOKEN = "token"
        module.PR_NUMBER = "3"
        module.REPO_NAME = "owner/repo"
        module.requests.get.side_effect = [
            response([{"filename": "auth.py", "patch": "@@ -1 +1 @@\n+unsafe_change"}]),
            response([]),
        ]
        module.requests.post.side_effect = [
            response({"choices": [{"message": {"content": json.dumps({
                "issues": [{"severity": "warning", "line": 1, "message": "Check input", "suggestion": "Validate input"}],
                "summary": "One issue",
            })}}]}),
            response({"id": 9}),
        ]
        previous = Path.cwd()
        with tempfile.TemporaryDirectory() as directory, patch.dict(os.environ, {"RAG_ENABLED": "false"}), patch.object(module.sys, "stdout", io.StringIO()):
            try:
                os.chdir(directory)
                module.main()
                report = json.loads(Path("review-report.json").read_text(encoding="utf-8"))
            finally:
                os.chdir(previous)
        self.assertEqual(1, report["issue_count"])
        self.assertEqual("auth.py", report["issues"][0]["file"])
        self.assertIn("<!-- ai-agent-code-review -->", module.requests.post.call_args.kwargs["json"]["body"])

    def test_report_keeps_summaries_from_each_reviewed_file(self):
        module = load_reviewer()
        module.OPENAI_API_KEY = "key"
        module.GITHUB_TOKEN = "token"
        module.PR_NUMBER = "3"
        module.REPO_NAME = "owner/repo"
        module.requests.get.side_effect = [
            response([{"filename": "auth.py", "patch": "+ auth"}, {"filename": "cache.py", "patch": "+ cache"}]),
            response([]),
        ]
        module.requests.post.side_effect = [
            response({"choices": [{"message": {"content": '{"issues": [], "summary": "Auth checked"}'}}]}),
            response({"choices": [{"message": {"content": '{"issues": [], "summary": "Cache checked"}'}}]}),
            response({"id": 9}),
        ]
        previous = Path.cwd()
        with tempfile.TemporaryDirectory() as directory, patch.dict(os.environ, {"RAG_ENABLED": "false"}), patch.object(module.sys, "stdout", io.StringIO()):
            try:
                os.chdir(directory)
                module.main()
                report = json.loads(Path("review-report.json").read_text(encoding="utf-8"))
            finally:
                os.chdir(previous)
        self.assertIn("auth.py: Auth checked", report["summary"])
        self.assertIn("cache.py: Cache checked", report["summary"])


if __name__ == "__main__":
    unittest.main()
