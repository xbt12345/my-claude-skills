import argparse
import json
from collections import Counter
from pathlib import Path

try:
    from scripts.feedback_store import aggregate_rows, read_records
except ModuleNotFoundError:
    from feedback_store import aggregate_rows, read_records


def aggregate_runs(path):
    raw_rows, corrupt_rows = read_records(path)
    rows = aggregate_rows(raw_rows)
    rows = [row for row in rows if row.get("outcome") in {"passed", "failed"}]
    models = Counter(row.get("model", "unknown") for row in rows)
    failures = Counter(
        row["failure_category"]
        for row in rows
        if row.get("failure_category")
    )
    passed = sum(row.get("outcome") == "passed" for row in rows)
    token_fields = [
        "estimated_prompt_tokens",
        "actual_input_tokens",
        "cached_input_tokens",
        "actual_output_tokens",
        "tool_result_tokens",
        "questions",
        "retries",
    ]
    usage = {}
    for field in token_fields:
        values = [
            row.get("usage", {}).get(field)
            for row in rows
            if isinstance(row.get("usage", {}).get(field), (int, float))
        ]
        usage[field] = {
            "observations": len(values),
            "total": sum(values) if values else None,
            "mean": round(sum(values) / len(values), 2) if values else None,
        }
    return {
        "runs": len(rows),
        "passed": passed,
        "failed": len(rows) - passed,
        "pass_rate": round(passed / len(rows), 4) if rows else None,
        "models": dict(models),
        "failure_categories": dict(failures),
        "usage": usage,
        "corrupt_rows": corrupt_rows,
        "abandoned": sum(row.get("event") == "abandoned" for row in aggregate_rows(raw_rows)),
    }


def main():
    parser = argparse.ArgumentParser(description="Aggregate Meta-Prompt run traces.")
    parser.add_argument(
        "path",
        nargs="?",
        type=Path,
        default=Path(__file__).resolve().parents[1] / "feedback/runs.jsonl",
    )
    args = parser.parse_args()
    print(json.dumps(aggregate_runs(args.path), ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()
