import copy
import json
import unittest
from pathlib import Path

from evaluation.real_pr_schema import validate_manifest


SOURCE_REVISIONS = {
    "cloud-aeye-cpp": "60733901a3deef2c7128b883cde420fea86d2186",
    "aacr-bench": "68a569759289a83654a59d06db2a72910edf0a4a",
}


def valid_manifest():
    return {
        "version": 1,
        "sources": SOURCE_REVISIONS.copy(),
        "cases": [{
            "id": "sample-1",
            "source": "cloud-aeye-cpp",
            "pr_url": "https://github.com/example/repo/pull/1",
            "base_sha": "a" * 40,
            "head_sha": "b" * 40,
            "language": "Python",
            "diff_sha256": "c" * 64,
            "expected": [{
                "id": "bug-1",
                "path": "src/example.py",
                "line": 2,
                "category": "defect",
                "description": "Off-by-one boundary",
                "evidence_url": "https://github.com/example/repo/pull/1#discussion_r123",
                "verification": "verified",
            }],
        }],
    }


class RealPrSchemaTests(unittest.TestCase):
    def test_accepts_traceable_case(self):
        manifest = valid_manifest()
        self.assertIs(validate_manifest(manifest), manifest)

    def test_rejects_missing_pr_url_and_invalid_sha(self):
        manifest = valid_manifest()
        del manifest["cases"][0]["pr_url"]
        with self.assertRaisesRegex(ValueError, "pr_url"):
            validate_manifest(manifest)
        manifest = valid_manifest()
        manifest["cases"][0]["base_sha"] = "short"
        with self.assertRaisesRegex(ValueError, "base_sha"):
            validate_manifest(manifest)

    def test_rejects_duplicate_case_and_expected_ids(self):
        manifest = valid_manifest()
        manifest["cases"].append(copy.deepcopy(manifest["cases"][0]))
        with self.assertRaisesRegex(ValueError, "duplicate case"):
            validate_manifest(manifest)
        manifest = valid_manifest()
        manifest["cases"][0]["expected"] *= 2
        with self.assertRaisesRegex(ValueError, "duplicate expected"):
            validate_manifest(manifest)

    def test_requires_verified_evidence_not_ai_claim_alone(self):
        manifest = valid_manifest()
        manifest["cases"][0]["expected"][0]["verification"] = "candidate"
        with self.assertRaisesRegex(ValueError, "verification"):
            validate_manifest(manifest)
        manifest = valid_manifest()
        manifest["cases"][0]["expected"][0]["evidence_url"] = "https://invalid.example/comment"
        with self.assertRaisesRegex(ValueError, "evidence_url"):
            validate_manifest(manifest)

    def test_rejects_source_revision_drift(self):
        manifest = valid_manifest()
        manifest["sources"]["cloud-aeye-cpp"] = "0" * 40
        with self.assertRaisesRegex(ValueError, "sources"):
            validate_manifest(manifest)

    def test_accepts_aacr_only_with_verified_evidence(self):
        manifest = valid_manifest()
        manifest["cases"][0]["source"] = "aacr-bench"
        self.assertIs(validate_manifest(manifest), manifest)

    def test_clean_case_requires_manual_evidence(self):
        manifest = valid_manifest()
        manifest["cases"][0]["expected"] = []
        with self.assertRaisesRegex(ValueError, "clean_verification"):
            validate_manifest(manifest)

    def test_shipped_manifest_has_traceable_scope(self):
        path = Path(__file__).resolve().parents[1] / "evaluation" / "real_pr_manifest.json"
        manifest = validate_manifest(json.loads(path.read_text(encoding="utf-8")))
        self.assertGreaterEqual(len(manifest["cases"]), 15)
        self.assertLessEqual(len(manifest["cases"]), 30)
        self.assertGreater(sum(case["source"] == "cloud-aeye-cpp" for case in manifest["cases"]),
                           sum(case["source"] == "aacr-bench" for case in manifest["cases"]))
        self.assertTrue(all("#discussion_r" in issue["evidence_url"]
                            for case in manifest["cases"] for issue in case["expected"]))


if __name__ == "__main__":
    unittest.main()
