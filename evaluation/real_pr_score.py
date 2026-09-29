"""Score manually adjudicated real-PR predictions; never infer false positives."""


def _counts():
    return {"true_positives": 0, "false_positives": 0, "false_negatives": 0}


def _rate(numerator, denominator):
    return numerator / denominator if denominator else 0.0


def score_adjudicated(manifest: dict, adjudication: dict) -> dict:
    """Require a verdict for every model issue in every pinned case."""
    cases = {case["id"]: case for case in manifest["cases"]}
    supplied = adjudication.get("cases") if isinstance(adjudication, dict) else None
    if not isinstance(supplied, list) or any(not isinstance(item, dict) for item in supplied):
        raise ValueError("adjudication cases must be a list of objects")
    ids = [item.get("id") for item in supplied]
    if len(ids) != len(set(ids)) or set(ids) != set(cases):
        raise ValueError("adjudication case ids must match manifest case ids exactly")
    totals = _counts()
    by_source = {}
    for prediction in supplied:
        case = cases[prediction["id"]]
        counts = by_source.setdefault(case["source"], _counts())
        expected = {issue["id"]: issue for issue in case["expected"]}
        issues = prediction.get("issues")
        if not isinstance(issues, list):
            raise ValueError("case issues must be a list")
        matched = set()
        for issue in issues:
            if not isinstance(issue, dict) or not isinstance(issue.get("file"), str) or not issue["file"]:
                raise ValueError("issue file is required")
            if type(issue.get("line")) is not int or issue["line"] < 1:
                raise ValueError("issue line must be positive")
            if not isinstance(issue.get("message"), str) or not issue["message"].strip():
                raise ValueError("issue message is required")
            verdict = issue.get("verdict")
            match_id = issue.get("matched_expected_id")
            if verdict == "matched":
                if match_id not in expected:
                    raise ValueError("matched verdict requires a known matched_expected_id")
                gold = expected[match_id]
                if issue["file"] != gold["path"] or issue["line"] != gold["line"]:
                    raise ValueError("matched issue location must equal expected path and line")
                if match_id in matched:
                    raise ValueError("duplicate match for expected issue")
                matched.add(match_id)
                metric = "true_positives"
            elif verdict == "false_positive" and match_id is None:
                metric = "false_positives"
            else:
                raise ValueError("every issue needs a human verdict and consistent matched_expected_id")
            totals[metric] += 1
            counts[metric] += 1
        misses = len(expected) - len(matched)
        totals["false_negatives"] += misses
        counts["false_negatives"] += misses
    totals["precision"] = _rate(totals["true_positives"], totals["true_positives"] + totals["false_positives"])
    totals["recall"] = _rate(totals["true_positives"], totals["true_positives"] + totals["false_negatives"])
    totals["by_source"] = by_source
    totals["case_count"] = len(cases)
    return totals


def compare_adjudicated(manifest: dict, baseline: dict, lexical: dict) -> dict:
    base = score_adjudicated(manifest, baseline)
    context = score_adjudicated(manifest, lexical)
    return {"baseline": base, "lexical": context,
            "delta_precision": context["precision"] - base["precision"],
            "delta_recall": context["recall"] - base["recall"]}
