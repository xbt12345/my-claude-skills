import argparse
import json
from collections import Counter
from datetime import date, datetime, timedelta
from pathlib import Path

try:
    from scripts.feedback_store import aggregate_rows, read_records
except ModuleNotFoundError:
    from feedback_store import aggregate_rows, read_records


def parse_row_date(row):
    value = row.get("date") or row.get("timestamp")
    if not value:
        return None
    try:
        return datetime.fromisoformat(str(value).replace("Z", "+00:00")).date()
    except ValueError:
        return None


def load_rows(path, with_meta=False):
    rows, corrupt_rows = read_records(path)
    return (rows, corrupt_rows) if with_meta else rows


def filter_recent(rows, as_of, days):
    start = as_of - timedelta(days=days - 1)
    return [
        row
        for row in rows
        if row.get("mode") in {"Express", "Guided", "Harness"}
        and (row_date := parse_row_date(row)) is not None
        and start <= row_date <= as_of
    ]


def mean(values):
    return round(sum(values) / len(values), 2) if values else None


def analyze_rows(rows, minimum_runs=5, failure_threshold=3):
    rows = aggregate_rows(rows)
    failures = Counter(
        row.get("failure_category")
        for row in rows
        if row.get("outcome") == "failed" and row.get("failure_category")
    )
    repeated = {
        category: count
        for category, count in sorted(failures.items())
        if count >= failure_threshold
    }
    passed = sum(row.get("outcome") == "passed" for row in rows)
    decided = sum(row.get("outcome") in {"passed", "failed"} for row in rows)
    abandoned = sum(row.get("event") == "abandoned" for row in rows)
    retries = [
        row.get("usage", {}).get("retries")
        for row in rows
        if isinstance(row.get("usage", {}).get("retries"), (int, float))
    ]
    questions = [
        row.get("usage", {}).get("questions")
        for row in rows
        if isinstance(row.get("usage", {}).get("questions"), (int, float))
    ]
    prompt_tokens = [
        row.get("usage", {}).get("estimated_prompt_tokens")
        for row in rows
        if isinstance(
            row.get("usage", {}).get("estimated_prompt_tokens"), (int, float)
        )
    ]

    if len(rows) < minimum_runs:
        decision = "insufficient-data"
    elif repeated:
        decision = "review-required"
    else:
        decision = "stable"

    return {
        "decision": decision,
        "runs": len(rows),
        "minimum_runs": minimum_runs,
        "passed": passed,
        "failed": decided - passed,
        "abandoned": abandoned,
        "pass_rate": round(passed / decided, 4) if decided else None,
        "modes": dict(Counter(row.get("mode", "unknown") for row in rows)),
        "repeated_failures": repeated,
        "all_failure_categories": dict(sorted(failures.items())),
        "mean_retries": mean(retries),
        "mean_questions": mean(questions),
        "mean_estimated_prompt_tokens": mean(prompt_tokens),
        "review_goals": [
            row.get("goal_summary")
            for row in rows
            if row.get("failure_category") in repeated and row.get("goal_summary")
        ][:10],
        "blind_eval_required": decision == "review-required",
    }


def to_markdown(report, days):
    lines = [
        "# Meta-Prompt 七日反思",
        "",
        f"- 决策：`{report['decision']}`",
        f"- 窗口：最近 {days} 天",
        f"- 有效运行：{report['runs']}（最低门槛 {report['minimum_runs']}）",
        f"- 通过率：{report['pass_rate']}",
        f"- 重复失败：{report['repeated_failures'] or '无'}",
        f"- 遗弃运行：{report['abandoned']}",
        f"- 需要盲评：{report['blind_eval_required']}",
        f"- 平均追问：{report['mean_questions']}",
        f"- 平均重试：{report['mean_retries']}",
        f"- 平均估算 Prompt Token：{report['mean_estimated_prompt_tokens']}",
        "",
    ]
    if report["decision"] == "insufficient-data":
        lines.append("结论：数据不足，只记录，不修改 Skill。")
    elif report["decision"] == "stable":
        lines.append("结论：没有达到重复失败门槛，只记录，不修改 Skill。")
    else:
        lines.append("结论：仅审查重复失败类别；先增加失败测试，再做最小改动。")
    return "\n".join(lines) + "\n"


def main():
    root = Path(__file__).resolve().parents[1]
    parser = argparse.ArgumentParser(description="Build a low-cost weekly reflection gate.")
    parser.add_argument("--path", type=Path, default=root / "feedback/runs.jsonl")
    parser.add_argument("--days", type=int, default=7)
    parser.add_argument("--as-of", type=date.fromisoformat, default=date.today())
    parser.add_argument("--minimum-runs", type=int, default=5)
    parser.add_argument("--failure-threshold", type=int, default=3)
    parser.add_argument("--json-out", type=Path, default=root / "feedback/weekly-review.json")
    parser.add_argument("--md-out", type=Path, default=root / "feedback/weekly-review.md")
    args = parser.parse_args()

    raw_rows, corrupt_rows = load_rows(args.path, with_meta=True)
    rows = filter_recent(raw_rows, args.as_of, args.days)
    report = analyze_rows(rows, args.minimum_runs, args.failure_threshold)
    report["as_of"] = args.as_of.isoformat()
    report["days"] = args.days
    report["corrupt_rows"] = corrupt_rows

    args.json_out.parent.mkdir(parents=True, exist_ok=True)
    args.json_out.write_text(
        json.dumps(report, ensure_ascii=False, indent=2) + "\n", encoding="utf-8"
    )
    args.md_out.write_text(to_markdown(report, args.days), encoding="utf-8")
    print(json.dumps(report, ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()
