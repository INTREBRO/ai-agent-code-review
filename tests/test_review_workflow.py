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

    def test_inline_comment_uses_changed_line_and_does_not_duplicate_on_rerun(self):
        module = load_reviewer()
        client = module.GitHubClient("token", "owner/repo", "3")
        issue = {"file": "auth.py", "line": 10, "side": "RIGHT", "severity": "warning", "message": "Check input", "suggestion": "Validate"}
        self.assertTrue(callable(getattr(client, "sync_inline_comments", None)))
        module.requests.get.return_value = response([])
        module.requests.post.return_value = response({"id": 101})
        self.assertEqual([], client.sync_inline_comments([issue], "head-sha"))
        first = module.requests.post.call_args.kwargs["json"]
        self.assertEqual(("auth.py", 10, "RIGHT", "head-sha"),
                         (first["path"], first["line"], first["side"], first["commit_id"]))
        module.requests.get.return_value = response([{
            "id": 101, "body": first["body"], "user": {"login": "github-actions[bot]"}
        }])
        self.assertEqual([], client.sync_inline_comments([issue], "head-sha"))
        self.assertEqual(1, module.requests.post.call_count)

    def test_inline_post_failure_returns_finding_for_summary(self):
        module = load_reviewer()
        client = module.GitHubClient("token", "owner/repo", "3")
        issue = {"file": "auth.py", "line": 10, "side": "RIGHT", "message": "Check input"}
        self.assertTrue(callable(getattr(client, "sync_inline_comments", None)))
        module.requests.get.return_value = response([])
        module.requests.post.side_effect = RuntimeError("GitHub rejected comment")
        with patch.object(module.sys, "stdout", io.StringIO()):
            self.assertEqual([issue], client.sync_inline_comments([issue], "head-sha"))

    def test_main_reports_inline_result_and_keeps_summary_comment(self):
        module = load_reviewer()
        module.OPENAI_API_KEY = "key"
        module.GITHUB_TOKEN = "token"
        module.PR_NUMBER = "3"
        module.REPO_NAME = "owner/repo"
        module.requests.get.side_effect = [
            response([{"filename": "auth.py", "patch": "@@ -1 +1 @@\n-old\n+unsafe_change"}]),
            response({"head": {"sha": "head-sha"}}),
            response([]),
            response([]),
        ]
        module.requests.post.side_effect = [
            response({"choices": [{"message": {"content": json.dumps({
                "issues": [{"severity": "warning", "line": 1, "message": "Check input"}], "summary": "One issue"
            })}}]}),
            response({"id": 101}),
            response({"id": 9}),
        ]
        previous = Path.cwd()
        with tempfile.TemporaryDirectory() as directory, patch.dict(os.environ, {"AI_PROVIDER": "openai", "RAG_ENABLED": "false"}), \
             patch.object(module.sys, "stdout", io.StringIO()):
            try:
                os.chdir(directory)
                module.main()
                report = json.loads(Path("review-report.json").read_text(encoding="utf-8"))
            finally:
                os.chdir(previous)
        self.assertEqual(1, report["inline_comments"]["posted"])
        self.assertEqual(1, report["issue_count"])
        self.assertEqual(3, module.requests.post.call_count)

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

    def test_deepseek_review_uses_its_endpoint_and_model(self):
        module = load_reviewer()
        module.requests.post.return_value = response({"choices": [{"message": {"content": '{"issues": [], "summary": "ok"}'}}]})
        with patch.dict(os.environ, {"AI_PROVIDER": "deepseek", "DEEPSEEK_MODEL": "deepseek-flash"}):
            result = module.AICodeReviewer("test-deepseek-key").generate_review("+ change", "auth.py")
        self.assertEqual([], result["issues"])
        args, kwargs = module.requests.post.call_args
        self.assertEqual("https://api.deepseek.com/chat/completions", args[0])
        self.assertEqual("deepseek-flash", kwargs["json"]["model"])
        self.assertEqual({"type": "json_object"}, kwargs["json"].get("response_format"))
        self.assertEqual("Bearer test-deepseek-key", kwargs["headers"]["Authorization"])

    def test_review_exposes_usage_for_cost_reporting(self):
        module = load_reviewer()
        module.requests.post.return_value = response({
            "choices": [{"message": {"content": '{"issues": [], "summary": "ok"}'}}],
            "usage": {"prompt_tokens": 120, "completion_tokens": 30, "total_tokens": 150},
        })
        with patch.dict(os.environ, {"AI_PROVIDER": "deepseek"}):
            reviewer = module.AICodeReviewer("test-key")
            result = reviewer.generate_review("+ change", "auth.py")
        self.assertEqual([], result["issues"])
        self.assertEqual(150, reviewer.last_usage["total_tokens"])
        self.assertEqual('{"issues": [], "summary": "ok"}', reviewer.last_raw_response)

    def test_explicit_provider_for_evaluation_does_not_change_environment(self):
        module = load_reviewer()
        with patch.dict(os.environ, {"AI_PROVIDER": "openai"}):
            reviewer = module.AICodeReviewer("test-key", provider="deepseek")
            self.assertEqual("openai", os.environ["AI_PROVIDER"])
        self.assertEqual("deepseek", reviewer.provider)

    def test_deepseek_run_does_not_require_openai_key_when_rag_disabled(self):
        module = load_reviewer()
        module.OPENAI_API_KEY = None
        module.DEEPSEEK_API_KEY = "test-deepseek-key"
        module.GITHUB_TOKEN = "token"
        module.PR_NUMBER = "3"
        module.REPO_NAME = "owner/repo"
        module.requests.get.return_value = response([])
        with patch.dict(os.environ, {"AI_PROVIDER": "deepseek", "RAG_ENABLED": "false"}), patch.object(module.sys, "stdout", io.StringIO()):
            try:
                module.main()
            except SystemExit:
                self.fail("DeepSeek review must not require an OpenAI key")
        module.requests.post.assert_not_called()

    def test_unknown_provider_is_rejected_before_network_calls(self):
        module = load_reviewer()
        with patch.dict(os.environ, {"AI_PROVIDER": "unknown"}):
            with self.assertRaisesRegex(ValueError, "AI_PROVIDER"):
                module.AICodeReviewer("test-key")

    def test_deepseek_without_openai_key_skips_rag_embeddings(self):
        module = load_reviewer()
        module.OPENAI_API_KEY = None
        module.DEEPSEEK_API_KEY = "test-deepseek-key"
        module.GITHUB_TOKEN = "token"
        module.PR_NUMBER = "3"
        module.REPO_NAME = "owner/repo"
        module.requests.get.return_value = response([])
        previous = Path.cwd()
        with tempfile.TemporaryDirectory() as directory, \
             patch.dict(os.environ, {"AI_PROVIDER": "deepseek", "RAG_ENABLED": "true"}), \
             patch.object(module, "OpenAIEmbeddings") as embeddings, \
             patch.object(module.sys, "stdout", io.StringIO()) as output:
            try:
                os.chdir(directory)
                module.main()
            finally:
                os.chdir(previous)
        self.assertEqual(0, embeddings.call_count)
        self.assertIn("RAG", output.getvalue())

    def test_malformed_model_output_is_not_treated_as_no_issues(self):
        module = load_reviewer()
        with self.assertRaises((ValueError, json.JSONDecodeError)):
            module.AICodeReviewer("key")._parse_review("not JSON")

    def test_model_parse_failure_reports_safe_response_metadata(self):
        module = load_reviewer()
        module.requests.post.return_value = response({
            "choices": [{"finish_reason": "length", "message": {"content": ""}}],
            "usage": {"prompt_tokens": 200, "completion_tokens": 2000, "total_tokens": 2200},
        })
        with patch.dict(os.environ, {"AI_PROVIDER": "deepseek"}):
            with self.assertRaisesRegex(ValueError, "finish_reason=length.*content_length=0.*completion_tokens=2000"):
                module.AICodeReviewer("key").generate_review("+ change", "auth.py")

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
            response({"head": {"sha": "head-sha"}}),
            response([]),
            response([]),
        ]
        module.requests.post.side_effect = [
            response({"choices": [{"message": {"content": json.dumps({
                "issues": [{"severity": "warning", "line": 1, "message": "Check input", "suggestion": "Validate input"}],
                "summary": "One issue",
            })}}]}),
            response({"id": 101}),
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
