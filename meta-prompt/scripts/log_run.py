import argparse
import json
import sys
from pathlib import Path
import uuid

try:
    from scripts.feedback_store import append_event, looks_like_mojibake
except ModuleNotFoundError:
    from feedback_store import append_event, looks_like_mojibake

USAGE_FIELDS = {
    "estimated_prompt_tokens",
    "actual_input_tokens",
    "cached_input_tokens",
    "actual_output_tokens",
    "tool_result_tokens",
    "questions",
    "retries",
}


def append_run(path, data):
    passed = data.get("passed")
    runtime = data.get("runtime", "other")
    if runtime not in {"codex", "claude-code", "other"}:
        runtime = "other"
    if data.get("execution_requested"):
        intent = "optimize_and_execute"
    elif data.get("explicit_request"):
        intent = "ask_after_optimization"
    else:
        intent = "implicit_task"
    usage = {
        key: data[key]
        for key in USAGE_FIELDS
        if isinstance(data.get(key), (int, float))
    }
    event = {
        "record_version": "2.0",
        "run_id": data.get("run_id", f"compat-{uuid.uuid4().hex}"),
        "event": "failed" if passed is False else "completed",
        "runtime": runtime,
        "model": data.get("model", ""),
        "mode": data.get("mode", "Express"),
        "execution_intent": intent,
        "explicit_request": bool(data.get("explicit_request", False)),
        "goal_summary": data.get("goal_summary", ""),
        "executed": bool(data.get("executed", False)),
        "outcome": (
            "passed" if passed is True else "failed" if passed is False else "unknown"
        ),
        "failure_category": data.get("failure_category"),
        "pattern_tags": data.get("pattern_tags", []),
        "user_feedback": data.get("user_feedback", ""),
        "usage": usage,
    }
    if data.get("timestamp"):
        event["timestamp"] = data["timestamp"]
    return append_event(path, event)


def main():
    if hasattr(sys.stdout, "reconfigure"):
        sys.stdout.reconfigure(encoding="utf-8")
    if hasattr(sys.stderr, "reconfigure"):
        sys.stderr.reconfigure(encoding="utf-8")
    parser = argparse.ArgumentParser(description="Append a compact Meta-Prompt run record.")
    parser.add_argument(
        "--path",
        type=Path,
        default=Path(__file__).resolve().parents[1] / "feedback/runs.jsonl",
    )
    parser.add_argument(
        "--data",
        help="JSON object. If omitted, read JSON from stdin. raw_prompt is discarded.",
    )
    args = parser.parse_args()
    payload = (
        args.data
        if args.data is not None
        else sys.stdin.buffer.read().decode("utf-8-sig")
    )
    if not payload.strip():
        parser.error("provide --data or JSON on stdin")
    data = json.loads(payload)
    if looks_like_mojibake(data.get("goal_summary")):
        print(
            "warning: goal_summary 疑似编码丢失，请改用 stdin 传 JSON 而非 --data",
            file=sys.stderr,
        )
    row = append_run(args.path, data)
    print(json.dumps(row, ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()
