"""Bounded, resumable evaluation of pinned PR patches."""

import argparse
import hashlib
import importlib.util
import json
import os
import sys
import tempfile
import time
from pathlib import Path
from types import SimpleNamespace

from evaluation.lexical_context import retrieve_context
from evaluation.prepare import prepare_case
from evaluation.real_pr_schema import validate_manifest


MAX_PATCH_CHARS = 12_000
MAX_CONTEXT_CHARS = 6_000
MAX_FILES_PER_CASE = 10


class DeepSeekReviewer:
    """Use the production review prompt/parser while exposing provider usage."""

    def __init__(self, api_key: str):
        script = Path(__file__).resolve().parents[1] / ".ai-review" / "ai-agent-review.py"
        spec = importlib.util.spec_from_file_location("evaluation_production_reviewer", script)
        module = importlib.util.module_from_spec(spec)
        sys.path.insert(0, str(script.parent))
        try:
            spec.loader.exec_module(module)
        finally:
            sys.path.pop(0)
        self._engine = module.AICodeReviewer(api_key, provider="deepseek")
        self.model = self._engine.model

    def __call__(self, patch: str, path: str, context: str) -> dict:
        result = self._engine.generate_review(patch, path, context)
        return dict(result, usage=self._engine.last_usage, raw_response=self._engine.last_raw_response)


def _artifact_path(out: Path, mode: str, case_id: str, path: str) -> Path:
    file_id = hashlib.sha256(path.encode()).hexdigest()[:16]
    return out / mode / case_id / f"{file_id}.json"


def _write_json(path: Path, value: dict) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with tempfile.NamedTemporaryFile("w", encoding="utf-8", dir=path.parent, suffix=".tmp", delete=False) as stream:
        json.dump(value, stream, ensure_ascii=False, indent=2)
        temporary = Path(stream.name)
    os.replace(temporary, path)


def _context_text(base_files: dict[str, str], patch: str) -> tuple[str, list[dict]]:
    snippets = retrieve_context(base_files, patch, max_chars=MAX_CONTEXT_CHARS)
    context = "\n\n".join(f"{item['path']}:{item['line']}\n{item['content']}" for item in snippets)
    return context[:MAX_CONTEXT_CHARS], snippets


def _validate_result(result: dict, path: str) -> list[dict]:
    if not isinstance(result, dict) or not isinstance(result.get("issues"), list):
        raise ValueError("model result must contain issues list")
    issues = []
    for issue in result["issues"]:
        if not isinstance(issue, dict) or type(issue.get("line")) is not int or issue["line"] < 1:
            raise ValueError("model issue line must be positive")
        if not isinstance(issue.get("message"), str) or not issue["message"].strip():
            raise ValueError("model issue message must be nonempty")
        issues.append(dict(issue, file=path))
    return issues


def run_cases(manifest: dict, cases: list[dict], mode: str, out: Path, reviewer,
              max_calls: int, dry_run: bool) -> dict:
    """Run up to max_calls file reviews, persisting each result before the next."""
    if mode not in {"diff", "lexical"}:
        raise ValueError("mode must be diff or lexical")
    if not dry_run and (type(max_calls) is not int or max_calls < 1):
        raise ValueError("live run requires a positive max_calls")
    known_ids = {case["id"] for case in manifest["cases"]}
    if any(case.get("id") not in known_ids for case in cases):
        raise ValueError("prepared case is not in manifest")
    out = Path(out)
    model = getattr(reviewer, "model", "unknown")
    report = {"mode": mode, "model": model, "case_ids": [case["id"] for case in cases],
              "planned_files": sum(min(len(case["patches"]), MAX_FILES_PER_CASE) for case in cases),
              "calls_made": 0, "completed_files": 0, "failed_files": 0, "skipped_files": 0,
              "results_dir": str(out / mode)}
    for case in cases:
        for entry in case["patches"][:MAX_FILES_PER_CASE]:
            path, patch = entry["path"], entry["patch"]
            context, snippets = _context_text(case["base_files"], patch) if mode == "lexical" else ("", [])
            input_record = {"case_id": case["id"], "path": path, "patch": patch,
                            "context": context, "model": model, "mode": mode,
                            "base_sha": case["provenance"]["base_sha"],
                            "head_sha": case["provenance"]["head_sha"]}
            input_hash = hashlib.sha256(json.dumps(input_record, sort_keys=True).encode()).hexdigest()
            artifact = _artifact_path(out, mode, case["id"], path)
            if artifact.is_file():
                try:
                    saved = json.loads(artifact.read_text(encoding="utf-8"))
                    if saved.get("input_hash") == input_hash and saved.get("status") == "ok":
                        report["completed_files"] += 1
                        continue
                except (OSError, ValueError):
                    pass
            if len(patch) > MAX_PATCH_CHARS:
                report["skipped_files"] += 1
                if not dry_run:
                    _write_json(artifact, {"status": "skipped", "reason": "patch exceeds 12000 characters",
                                           "input_hash": input_hash, "input": input_record})
                continue
            if dry_run:
                continue
            if report["calls_made"] >= max_calls:
                continue
            started = time.perf_counter()
            try:
                result = reviewer(patch, path, context)
                issues = _validate_result(result, path)
                value = {"status": "ok", "input_hash": input_hash, "input": input_record,
                         "retrieved_snippets": snippets, "issues": issues,
                         "summary": result.get("summary", ""), "usage": result.get("usage"),
                         "raw_response": result.get("raw_response"),
                         "elapsed_seconds": round(time.perf_counter() - started, 3)}
                report["completed_files"] += 1
            except Exception as error:
                value = {"status": "error", "input_hash": input_hash, "input": input_record,
                         "error_type": type(error).__name__,
                         "elapsed_seconds": round(time.perf_counter() - started, 3)}
                report["failed_files"] += 1
            report["calls_made"] += 1
            _write_json(artifact, value)
    return report


def main(argv=None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--manifest", type=Path, default=Path(__file__).with_name("real_pr_manifest.json"))
    parser.add_argument("--cache-root", type=Path, required=True)
    parser.add_argument("--out", type=Path, required=True)
    parser.add_argument("--mode", choices=("diff", "lexical"), required=True)
    parser.add_argument("--limit-cases", type=int, default=3)
    parser.add_argument("--max-calls", type=int, default=0)
    parser.add_argument("--live", action="store_true", help="Allow paid DeepSeek requests")
    args = parser.parse_args(argv)
    if args.limit_cases < 1:
        parser.error("--limit-cases must be positive")
    if args.live and args.max_calls < 1:
        parser.error("--live requires --max-calls N with N > 0")
    if args.live and not os.getenv("DEEPSEEK_API_KEY"):
        parser.error("--live requires DEEPSEEK_API_KEY")
    manifest = validate_manifest(json.loads(args.manifest.read_text(encoding="utf-8")))
    selected = manifest["cases"][:args.limit_cases]
    prepared = [dict(prepare_case(case, args.cache_root), id=case["id"]) for case in selected]
    reviewer = (DeepSeekReviewer(os.environ["DEEPSEEK_API_KEY"]) if args.live
                else SimpleNamespace(model=os.getenv("DEEPSEEK_MODEL", "deepseek-flash")))
    report = run_cases(manifest, prepared, args.mode, args.out, reviewer, args.max_calls, not args.live)
    print(json.dumps(report, ensure_ascii=False, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
