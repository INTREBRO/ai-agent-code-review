import hashlib
import json
import tempfile
import unittest
from pathlib import Path

from evaluation.prepare import prepare_case


PATCH = "@@ -1 +1 @@\n-old\n+new"
DIFF = "diff --git a/src/example.py b/src/example.py\n" + PATCH
BASE_SHA = "a" * 40
HEAD_SHA = "b" * 40
COMPARE_URL = f"https://api.github.com/repos/example/repo/compare/{BASE_SHA}...{HEAD_SHA}"
RAW_URL = f"https://raw.githubusercontent.com/example/repo/{BASE_SHA}/src/example.py"


def case():
    return {
        "id": "example-pr1", "pr_url": "https://github.com/example/repo/pull/1",
        "base_sha": BASE_SHA, "head_sha": HEAD_SHA,
        "diff_sha256": hashlib.sha256(DIFF.encode()).hexdigest(),
    }


def compare_response(path="src/example.py", status="modified", previous_filename=None):
    item = {"filename": path, "patch": PATCH, "status": status}
    if previous_filename:
        item["previous_filename"] = previous_filename
    return json.dumps({"files": [item]}).encode()


class RealPrPrepareTests(unittest.TestCase):
    def test_pinned_diff_uses_only_base_source_and_reuses_cache(self):
        requested = []
        payloads = {COMPARE_URL: compare_response(), RAW_URL: b"old\n"}

        def fetch(url):
            requested.append(url)
            return payloads[url]

        with tempfile.TemporaryDirectory() as directory:
            first = prepare_case(case(), Path(directory), fetch)
            self.assertEqual(DIFF, first["diff"])
            self.assertEqual([{"path": "src/example.py", "patch": PATCH}], first["patches"])
            self.assertEqual({"src/example.py": "old\n"}, first["base_files"])
            self.assertEqual([COMPARE_URL, RAW_URL], requested)
            second = prepare_case(case(), Path(directory), fetch)
            self.assertEqual(first, second)
            self.assertEqual(2, len(requested))
            self.assertTrue(all(HEAD_SHA not in url for url in requested if "raw.githubusercontent" in url))

    def test_tampered_cached_source_is_refetched(self):
        payloads = {COMPARE_URL: compare_response(), RAW_URL: b"old\n"}
        requested = []

        def fetch(url):
            requested.append(url)
            return payloads[url]

        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            prepare_case(case(), root, fetch)
            cache_file = root / "example-pr1.json"
            cached = json.loads(cache_file.read_text(encoding="utf-8"))
            cached["base_files"]["src/example.py"] = "untrusted head content"
            cache_file.write_text(json.dumps(cached), encoding="utf-8")
            restored = prepare_case(case(), root, fetch)
        self.assertEqual("old\n", restored["base_files"]["src/example.py"])
        self.assertEqual(4, len(requested))

    def test_tampered_cached_patch_is_refetched(self):
        payloads = {COMPARE_URL: compare_response(), RAW_URL: b"old\n"}
        calls = []

        def fetch(url):
            calls.append(url)
            return payloads[url]

        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            prepare_case(case(), root, fetch)
            cache_file = root / "example-pr1.json"
            cached = json.loads(cache_file.read_text(encoding="utf-8"))
            cached["patches"][0]["patch"] = "+untrusted head content"
            cache_file.write_text(json.dumps(cached), encoding="utf-8")
            restored = prepare_case(case(), root, fetch)
        self.assertEqual(PATCH, restored["patches"][0]["patch"])
        self.assertEqual(4, len(calls))

    def test_digest_mismatch_is_rejected(self):
        bad_case = case()
        bad_case["diff_sha256"] = "0" * 64
        with tempfile.TemporaryDirectory() as directory:
            with self.assertRaisesRegex(ValueError, "diff_sha256"):
                prepare_case(bad_case, Path(directory), lambda url: compare_response())

    def test_renamed_file_reads_previous_name_from_base(self):
        renamed = {COMPARE_URL: compare_response(path="src/new.py", status="renamed", previous_filename="src/old.py"),
                   f"https://raw.githubusercontent.com/example/repo/{BASE_SHA}/src/old.py": b"old\n"}
        renamed_case = case()
        renamed_case["diff_sha256"] = hashlib.sha256(
            ("diff --git a/src/new.py b/src/new.py\n" + PATCH).encode()).hexdigest()
        with tempfile.TemporaryDirectory() as directory:
            result = prepare_case(renamed_case, Path(directory), lambda url: renamed[url])
        self.assertEqual({"src/new.py": "old\n"}, result["base_files"])

    def test_rejects_unsafe_paths_before_fetching_source(self):
        unsafe = {COMPARE_URL: compare_response(path="../../secret.py")}
        with tempfile.TemporaryDirectory() as directory:
            with self.assertRaisesRegex(ValueError, "unsafe"):
                prepare_case(case(), Path(directory), lambda url: unsafe[url])

    def test_expected_location_must_be_an_added_line(self):
        annotated = case()
        annotated["expected"] = [{"path": "src/example.py", "line": 3}]
        with tempfile.TemporaryDirectory() as directory:
            with self.assertRaisesRegex(ValueError, "expected line"):
                prepare_case(annotated, Path(directory), lambda url: {COMPARE_URL: compare_response()}[url])

    def test_skips_oversized_source_and_records_reason(self):
        payloads = {COMPARE_URL: compare_response(), RAW_URL: b"a" * 64_001}
        with tempfile.TemporaryDirectory() as directory:
            result = prepare_case(case(), Path(directory), lambda url: payloads[url])
        self.assertEqual({}, result["base_files"])
        self.assertEqual(["src/example.py: source file exceeds 64000 bytes"], result["provenance"]["skipped_sources"])


if __name__ == "__main__":
    unittest.main()
