"""Validate and score human-adjudicated PR review outputs without model calls."""

import argparse
import json
from pathlib import Path


def _nonempty_string(value, field):
    if not isinstance(value, str) or not value.strip():
        raise ValueError(f"{field} must be a nonempty string")


def _positive_line(value):
    if isinstance(value, bool) or not isinstance(value, int) or value < 1:
        raise ValueError("line must be a positive integer")


def validate_benchmark(benchmark):
    if not isinstance(benchmark, dict) or benchmark.get("version") != 1:
        raise ValueError("benchmark version must be 1")
    cases = benchmark.get("cases")
    if not isinstance(cases, list) or not cases:
        raise ValueError("benchmark cases must be a nonempty list")
    seen_cases = set()
    for case in cases:
        if not isinstance(case, dict):
            raise ValueError("case must be an object")
        for field in ("id", "category", "difficulty", "diff"):
            _nonempty_string(case.get(field), field)
        if case["id"] in seen_cases:
            raise ValueError(f"duplicate case id: {case['id']}")
        seen_cases.add(case["id"])
        expected = case.get("expected")
        if not isinstance(expected, list):
            raise ValueError("expected must be a list")
        seen_expected = set()
        for issue in expected:
            if not isinstance(issue, dict):
                raise ValueError("expected issue must be an object")
            for field in ("id", "file", "description"):
                _nonempty_string(issue.get(field), field)
            _positive_line(issue.get("line"))
            if issue["id"] in seen_expected:
                raise ValueError(f"duplicate expected id: {issue['id']}")
            seen_expected.add(issue["id"])
    return benchmark


def _counts():
    return {"true_positives": 0, "false_positives": 0, "false_negatives": 0}


def _rate(numerator, denominator):
    return numerator / denominator if denominator else 0.0


def score(benchmark, predictions):
    validate_benchmark(benchmark)
    if not isinstance(predictions, dict) or not isinstance(predictions.get("cases"), list):
        raise ValueError("prediction cases must be a list")
    expected_cases = {case["id"]: case for case in benchmark["cases"]}
    prediction_cases = predictions["cases"]
    ids = [case.get("id") for case in prediction_cases if isinstance(case, dict)]
    if len(ids) != len(prediction_cases) or any(not isinstance(case_id, str) for case_id in ids):
        raise ValueError("prediction case id must be a string")
    if len(set(ids)) != len(ids) or set(ids) != set(expected_cases):
        raise ValueError("prediction case ids must match benchmark case ids exactly")
    totals = _counts()
    by_category = {}
    for prediction in prediction_cases:
        case = expected_cases[prediction["id"]]
        category = case["category"]
        category_counts = by_category.setdefault(category, _counts())
        expected = {issue["id"]: issue for issue in case["expected"]}
        issues = prediction.get("issues")
        if not isinstance(issues, list):
            raise ValueError("issues must be a list")
        matched = set()
        for issue in issues:
            if not isinstance(issue, dict):
                raise ValueError("prediction issue must be an object")
            for field in ("file", "message"):
                _nonempty_string(issue.get(field), field)
            _positive_line(issue.get("line"))
            if "matched_expected_id" not in issue:
                raise ValueError("matched_expected_id is required for human adjudication")
            match_id = issue["matched_expected_id"]
            if match_id is not None:
                if not isinstance(match_id, str):
                    raise ValueError("matched_expected_id must be a string or null")
                if match_id not in expected:
                    raise ValueError(f"unknown matched_expected_id: {match_id}")
                if issue["file"] != expected[match_id]["file"] or issue["line"] != expected[match_id]["line"]:
                    raise ValueError(f"matched_expected_id location mismatch: {match_id}")
            metric = "true_positives" if match_id is not None and match_id not in matched else "false_positives"
            totals[metric] += 1
            category_counts[metric] += 1
            if metric == "true_positives":
                matched.add(match_id)
        misses = len(expected) - len(matched)
        totals["false_negatives"] += misses
        category_counts["false_negatives"] += misses
    totals["precision"] = _rate(totals["true_positives"], totals["true_positives"] + totals["false_positives"])
    totals["recall"] = _rate(totals["true_positives"], totals["true_positives"] + totals["false_negatives"])
    totals["by_category"] = by_category
    totals["case_count"] = len(expected_cases)
    return totals


def compare(benchmark, baseline, rag):
    base_score = score(benchmark, baseline)
    rag_score = score(benchmark, rag)
    return {
        "baseline": base_score,
        "rag": rag_score,
        "delta_precision": rag_score["precision"] - base_score["precision"],
        "delta_recall": rag_score["recall"] - base_score["recall"],
    }


def _read_json(path):
    return json.loads(Path(path).read_text(encoding="utf-8"))


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__)
    subcommands = parser.add_subparsers(dest="command", required=True)
    for command, names in (("validate", ("benchmark",)), ("score", ("benchmark", "predictions")),
                           ("compare", ("benchmark", "baseline", "rag"))):
        subcommand = subcommands.add_parser(command)
        for name in names:
            subcommand.add_argument(name)
    args = parser.parse_args(argv)
    try:
        benchmark = _read_json(args.benchmark)
        if args.command == "validate":
            validate_benchmark(benchmark)
            result = {"valid": True, "case_count": len(benchmark["cases"]), "quality_score": None}
        elif args.command == "score":
            result = score(benchmark, _read_json(args.predictions))
        else:
            result = compare(benchmark, _read_json(args.baseline), _read_json(args.rag))
    except (OSError, ValueError) as error:
        parser.error(str(error))
    print(json.dumps(result, ensure_ascii=False, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
