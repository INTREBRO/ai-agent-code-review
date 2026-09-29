"""Validation for pinned, manually checked real pull-request cases."""

import re
from pathlib import PurePosixPath
from urllib.parse import urlparse


SOURCE_REVISIONS = {
    "cloud-aeye-cpp": "60733901a3deef2c7128b883cde420fea86d2186",
    "aacr-bench": "68a569759289a83654a59d06db2a72910edf0a4a",
}
SHA40 = re.compile(r"[0-9a-f]{40}\Z")
SHA64 = re.compile(r"[0-9a-f]{64}\Z")
CASE_ID = re.compile(r"[a-z0-9][a-z0-9-]*\Z")
PR_PATH = re.compile(r"/([^/]+)/([^/]+)/pull/([1-9][0-9]*)\Z")


def _string(value, name):
    if not isinstance(value, str) or not value.strip():
        raise ValueError(f"{name} must be a nonempty string")


def _github_url(value, name):
    _string(value, name)
    parsed = urlparse(value)
    if parsed.scheme != "https" or parsed.netloc.lower() != "github.com" or not parsed.path:
        raise ValueError(f"{name} must be a GitHub HTTPS URL")
    return parsed


def validate_manifest(data: dict) -> dict:
    """Return a valid manifest, otherwise raise a precise ValueError."""
    if not isinstance(data, dict) or type(data.get("version")) is not int or data["version"] != 1:
        raise ValueError("manifest version must be 1")
    if data.get("sources") != SOURCE_REVISIONS:
        raise ValueError("sources must pin both approved benchmark revisions")
    cases = data.get("cases")
    if not isinstance(cases, list) or not cases:
        raise ValueError("cases must be a nonempty list")
    seen_cases = set()
    for case in cases:
        if not isinstance(case, dict):
            raise ValueError("case must be an object")
        case_id = case.get("id")
        if not isinstance(case_id, str) or not CASE_ID.fullmatch(case_id):
            raise ValueError("case id must be lowercase letters, numbers and hyphens")
        if case_id in seen_cases:
            raise ValueError(f"duplicate case id: {case_id}")
        seen_cases.add(case_id)
        if case.get("source") not in SOURCE_REVISIONS:
            raise ValueError(f"{case_id}: source must be an approved benchmark")
        pr = _github_url(case.get("pr_url"), "pr_url")
        if not PR_PATH.fullmatch(pr.path):
            raise ValueError(f"{case_id}: pr_url must point to a pull request")
        for field in ("base_sha", "head_sha"):
            value = case.get(field)
            if not isinstance(value, str) or not SHA40.fullmatch(value):
                raise ValueError(f"{case_id}: {field} must be a full 40-character SHA")
        digest = case.get("diff_sha256")
        if not isinstance(digest, str) or not SHA64.fullmatch(digest):
            raise ValueError(f"{case_id}: diff_sha256 must be a SHA-256 hex digest")
        _string(case.get("language"), "language")
        expected = case.get("expected")
        if not isinstance(expected, list):
            raise ValueError(f"{case_id}: expected must be a list")
        if not expected:
            clean = case.get("clean_verification")
            if not isinstance(clean, dict) or clean.get("status") != "verified":
                raise ValueError(f"{case_id}: clean_verification requires manual evidence")
            _github_url(clean.get("evidence_url"), "clean_verification.evidence_url")
            _string(clean.get("rationale"), "clean_verification.rationale")
        seen_expected = set()
        for issue in expected:
            if not isinstance(issue, dict):
                raise ValueError(f"{case_id}: expected issue must be an object")
            issue_id = issue.get("id")
            if not isinstance(issue_id, str) or not CASE_ID.fullmatch(issue_id):
                raise ValueError(f"{case_id}: expected id is invalid")
            if issue_id in seen_expected:
                raise ValueError(f"{case_id}: duplicate expected id: {issue_id}")
            seen_expected.add(issue_id)
            path = issue.get("path")
            if not isinstance(path, str) or not path or PurePosixPath(path).is_absolute() or ".." in PurePosixPath(path).parts or "\\" in path:
                raise ValueError(f"{case_id}: expected path is unsafe")
            line = issue.get("line")
            if type(line) is not int or line < 1:
                raise ValueError(f"{case_id}: expected line must be positive")
            for field in ("category", "description"):
                _string(issue.get(field), field)
            _github_url(issue.get("evidence_url"), "evidence_url")
            if issue.get("verification") != "verified":
                raise ValueError(f"{case_id}: verification must be verified")
    return data
