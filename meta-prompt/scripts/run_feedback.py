import argparse
import hashlib
import json
import re
import sys
import uuid
from datetime import datetime, timedelta
from pathlib import Path

try:
    from scripts.feedback_store import (
        aggregate_rows,
        append_event,
        looks_like_mojibake,
        normalize_event,
        read_records,
    )
except ModuleNotFoundError:
    from feedback_store import (
        aggregate_rows,
        append_event,
        looks_like_mojibake,
        normalize_event,
        read_records,
    )


ONLY_PATTERNS = [
    r"只(?:需要|要)?优化",
    r"仅优化",
    r"(?:不要|无需|不必).{0,4}执行",
    r"只(?:给|输出).{0,8}(?:prompt|提示词)",
    r"\boptimi[sz]e only\b",
    r"\bdo not execute\b",
]
EXECUTE_PATTERNS = [
    r"优化后.{0,8}(?:直接)?执行",
    r"优化并执行",
    r"直接执行",
    r"完成(?:该|这个)?任务",
    r"\boptimi[sz]e and execute\b",
    r"\bexecute after optimi[sz]ing\b",
]


def derive_execution_intent(original_request, explicit_request):
    if not explicit_request:
        return "implicit_task"
    text = str(original_request or "").strip().lower()
    if any(re.search(pattern, text, re.IGNORECASE) for pattern in ONLY_PATTERNS):
        return "optimize_only"
    if any(re.search(pattern, text, re.IGNORECASE) for pattern in EXECUTE_PATTERNS):
        return "optimize_and_execute"
    return "ask_after_optimization"


def prompt_fingerprint(original_request):
    if not original_request:
        return None
    return hashlib.sha256(str(original_request).encode("utf-8")).hexdigest()


def _pending_path(pending_dir, run_id):
    run_id = str(run_id)
    if not re.fullmatch(r"[A-Za-z0-9._-]{1,80}", run_id):
        raise ValueError("run_id contains unsafe characters")
    return Path(pending_dir) / f"{run_id}.json"


def _atomic_json_write(path, data):
    path = Path(path)
    path.parent.mkdir(parents=True, exist_ok=True)
    temporary = path.with_suffix(path.suffix + f".{uuid.uuid4().hex}.tmp")
    temporary.write_text(
        json.dumps(data, ensure_ascii=False, separators=(",", ":")) + "\n",
        encoding="utf-8",
    )
    temporary.replace(path)


def start_run(log_path, pending_dir, data):
    payload = dict(data)
    payload.setdefault("run_id", uuid.uuid4().hex)
    payload["event"] = "started"
    if payload.get("original_request"):
        payload.setdefault("prompt_fingerprint", prompt_fingerprint(payload["original_request"]))
    payload.pop("original_request", None)
    event = normalize_event(payload)
    append_event(log_path, event)
    _atomic_json_write(_pending_path(pending_dir, event["run_id"]), event)
    return event


def _existing_terminal(log_path, run_id):
    rows, _ = read_records(log_path)
    terminals = [
        row
        for row in rows
        if row.get("record_version") == "2.0"
        and row.get("run_id") == run_id
        and row.get("event") in {"completed", "failed", "abandoned"}
    ]
    return terminals[-1] if terminals else None


def finish_run(log_path, pending_dir, run_id, data):
    pending_path = _pending_path(pending_dir, run_id)
    if not pending_path.exists():
        existing = _existing_terminal(log_path, run_id)
        if existing:
            return existing
        raise FileNotFoundError(f"no pending run: {run_id}")

    started = json.loads(pending_path.read_text(encoding="utf-8"))
    payload = dict(started)
    payload.update(dict(data))
    payload["run_id"] = run_id
    payload["event"] = "failed" if payload.get("outcome") == "failed" else "completed"
    payload.pop("timestamp", None)
    event = normalize_event(payload)
    append_event(log_path, event)
    pending_path.unlink(missing_ok=True)
    return event


def abandon_stale(log_path, pending_dir, older_than, now=None):
    now = now or datetime.now().astimezone()
    pending_dir = Path(pending_dir)
    if not pending_dir.exists():
        return []
    abandoned = []
    for path in sorted(pending_dir.glob("*.json")):
        try:
            started = json.loads(path.read_text(encoding="utf-8"))
            timestamp = datetime.fromisoformat(
                str(started["timestamp"]).replace("Z", "+00:00")
            )
        except (KeyError, ValueError, json.JSONDecodeError):
            continue
        if now - timestamp < older_than:
            continue
        payload = dict(started)
        payload.pop("timestamp", None)
        payload.update({"event": "abandoned", "outcome": "unknown", "executed": False})
        append_event(log_path, payload)
        path.unlink(missing_ok=True)
        abandoned.append(started["run_id"])
    return abandoned


def summarize(log_path):
    rows, corrupt_rows = read_records(log_path)
    return {"runs": aggregate_rows(rows), "corrupt_rows": corrupt_rows}


def _read_payload(raw):
    if raw is not None:
        payload = json.loads(raw)
    else:
        value = sys.stdin.buffer.read().decode("utf-8-sig")
        if not value.strip():
            raise ValueError("provide --data or JSON on stdin")
        payload = json.loads(value)
    if isinstance(payload, dict) and looks_like_mojibake(payload.get("goal_summary")):
        print(
            "warning: goal_summary 疑似编码丢失，请改用 stdin 传 JSON 而非 --data",
            file=sys.stderr,
        )
    return payload


def main():
    if hasattr(sys.stdout, "reconfigure"):
        sys.stdout.reconfigure(encoding="utf-8")
    root = Path(__file__).resolve().parents[1]
    parser = argparse.ArgumentParser(description="Manage Meta-Prompt feedback lifecycle.")
    parser.add_argument("--path", type=Path, default=root / "feedback/runs.jsonl")
    parser.add_argument("--pending-dir", type=Path, default=root / "feedback/pending")
    subparsers = parser.add_subparsers(dest="command", required=True)

    start = subparsers.add_parser("start")
    start.add_argument("--data")

    finish = subparsers.add_parser("finish")
    finish.add_argument("run_id")
    finish.add_argument("--data")

    abandon = subparsers.add_parser("abandon")
    abandon.add_argument("--stale", type=int, default=3600)

    subparsers.add_parser("summarize")
    args = parser.parse_args()

    if args.command == "start":
        result = start_run(args.path, args.pending_dir, _read_payload(args.data))
    elif args.command == "finish":
        result = finish_run(
            args.path, args.pending_dir, args.run_id, _read_payload(args.data)
        )
    elif args.command == "abandon":
        result = {
            "abandoned": abandon_stale(
                args.path, args.pending_dir, timedelta(seconds=args.stale)
            )
        }
    else:
        result = summarize(args.path)
    print(json.dumps(result, ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()
