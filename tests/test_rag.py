import importlib.util
import json
import io
import sys
import tempfile
import unittest
from unittest.mock import patch
from types import ModuleType
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / ".ai-review"))

from rag.context_builder import build_context
from rag.indexer import build_index, discover_files
from rag.retriever import retrieve


class FakeEmbeddings:
    model = "fake-v1"

    def embed(self, texts):
        return [[float("login" in text.lower()), float("cache" in text.lower())] for text in texts]


class RagTests(unittest.TestCase):
    def test_discovers_source_and_excludes_hidden_and_generated_files(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            (root / "auth.py").write_text("def login(): pass", encoding="utf-8")
            (root / ".env").write_text("SECRET=1", encoding="utf-8")
            (root / "node_modules").mkdir()
            (root / "node_modules" / "other.py").write_text("bad", encoding="utf-8")
            self.assertEqual(["auth.py"], [item.relative_to(root).as_posix() for item in discover_files(root)])

    def test_index_retrieves_relevant_chunk_and_respects_budget(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            (root / "auth.py").write_text("def login():\n    return user\n", encoding="utf-8")
            (root / "cache.py").write_text("def cache():\n    return value\n", encoding="utf-8")
            index = build_index(root, FakeEmbeddings(), root / "index.json")
            self.assertEqual(2, len(index["chunks"]))
            self.assertEqual("auth.py", retrieve(index, "login", FakeEmbeddings(), limit=1)[0]["path"])
            context = build_context(retrieve(index, "login", FakeEmbeddings()), max_chars=120)
            self.assertIn("auth.py", context)
            self.assertLessEqual(len(context), 120)
            self.assertEqual(2, len(json.loads((root / "index.json").read_text(encoding="utf-8"))["chunks"]))

    def test_review_prompt_only_adds_context_when_provided(self):
        spec = importlib.util.spec_from_file_location("reviewer", ROOT / ".ai-review" / "ai-agent-review.py")
        module = importlib.util.module_from_spec(spec)
        with patch.dict(sys.modules, {"requests": ModuleType("requests")}):
            spec.loader.exec_module(module)
        reviewer = module.AICodeReviewer("test")
        plain = reviewer._build_prompt("+ change", "auth.py")
        contextual = reviewer._build_prompt("+ change", "auth.py", "auth.py:1\ndef login(): pass")
        self.assertNotIn("def login(): pass", plain)
        self.assertIn("def login(): pass", contextual)

    def test_cache_is_reused_and_invalidated_after_source_change(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            source = root / "auth.py"
            source.write_text("def login(): pass", encoding="utf-8")
            cache = root / "index.json"
            provider = FakeEmbeddings()
            first = build_index(root, provider, cache)
            with patch.object(provider, "embed", side_effect=AssertionError("cache was not used")):
                self.assertEqual(first, build_index(root, provider, cache))
            source.write_text("def login(): return user", encoding="utf-8")
            self.assertNotEqual(first["digest"], build_index(root, provider, cache)["digest"])

    def test_index_failure_falls_back_to_diff_review(self):
        spec = importlib.util.spec_from_file_location("reviewer", ROOT / ".ai-review" / "ai-agent-review.py")
        module = importlib.util.module_from_spec(spec)
        with patch.dict(sys.modules, {"requests": ModuleType("requests")}):
            spec.loader.exec_module(module)
        module.OPENAI_API_KEY = "test"
        module.GITHUB_TOKEN = "test"
        module.PR_NUMBER = "1"
        module.REPO_NAME = "owner/repo"
        with tempfile.TemporaryDirectory() as directory:
            with patch.object(module, "build_index", side_effect=RuntimeError("offline")), \
                 patch.object(module, "GitHubClient") as github, \
                 patch.object(module, "AICodeReviewer") as reviewer, \
                 patch.dict(module.os.environ, {"RAG_ENABLED": "true"}), \
                 patch.object(module.sys, "stdout", io.StringIO()), \
                 patch("builtins.open", create=True):
                github.return_value.get_pr_diff.return_value = [{"filename": "auth.py", "patch": "+ change"}]
                reviewer.return_value.generate_review.return_value = {"issues": [], "summary": "reviewed"}
                module.main()
                reviewer.return_value.generate_review.assert_called_once_with("+ change", "auth.py", "")
                github.return_value.post_review_comment.assert_called_once_with([], "auth.py: reviewed")


if __name__ == "__main__":
    unittest.main()
