import hashlib
import json
import os
import time
from contextlib import contextmanager
from datetime import datetime
from pathlib import Path


VALID_EVENTS = {"started", "completed", "failed", "abandoned"}
TERMINAL_EVENTS = {"completed", "failed", "abandoned"}
VALID_INTENTS = {
    "optimize_only",
    "optimize_and_execute",
    "ask_after_optimization",
    "implicit_task",
}
VALID_MODES = {"Express", "Guided", "Harness"}
VALID_RUNTIMES = {"codex", "claude-code", "other"}
VALID_OUTCOMES = {"passed", "failed", "unknown"}
USAGE_FIELDS = {
    "estimated_prompt_tokens",
    "actual_input_tokens",
    "cached_input_tokens",
    "actual_output_tokens",
    "tool_result_tokens",
    "questions",
    "retries",
}
EVENT_FIELDS = {
    "record_version",
    "run_id",
    "event",
    "timestamp",
    "runtime",
    "model",
    "mode",
    "execution_intent",
    "explicit_request",
    "goal_summary",
    "prompt_fingerprint",
    "executed",
    "outcome",
    "failure_category",
    "pattern_tags",
    "user_feedback",
    "usage",
}


def _now():
    return datetime.now().astimezone().isoformat(timespec="seconds")


def _clean_text(value, limit):
    return str(value or "").strip()[:limit]


def looks_like_mojibake(text):
    """启发式检测 argv 编码丢失：含替换符，或非空白字符里问号占比过半。

    典型坏样本如 ``?????7??8???``（Windows 控制台经 argv 传中文丢失）。
    """
    s = str(text or "")
    if "�" in s:
        return True
    non_space = [c for c in s if not c.isspace()]
    if not non_space:
        return False
    questions = non_space.count("?")
    return questions >= 3 and questions / len(non_space) >= 0.5


def normalize_event(data):
    row = {key: value for key, value in dict(data).items() if key in EVENT_FIELDS}
    row.setdefault("record_version", "2.0")
    row.setdefault("timestamp", _now())

    required = {
        "run_id",
        "event",
        "runtime",
        "mode",
        "execution_intent",
        "explicit_request",
        "goal_summary",
    }
    missing = sorted(key for key in required if key not in row)
    if missing:
        raise ValueError(f"missing required fields: {', '.join(missing)}")
    if row["record_version"] != "2.0":
        raise ValueError("record_version must be 2.0")
    if row["event"] not in VALID_EVENTS:
        raise ValueError("invalid event")
    if row["runtime"] not in VALID_RUNTIMES:
        raise ValueError("invalid runtime")
    if row["mode"] not in VALID_MODES:
        raise ValueError("invalid mode")
    if row["execution_intent"] not in VALID_INTENTS:
        raise ValueError("invalid execution_intent")
    if not isinstance(row["explicit_request"], bool):
        raise ValueError("explicit_request must be boolean")
    if row.get("outcome") not in VALID_OUTCOMES | {None}:
        raise ValueError("invalid outcome")

    row["run_id"] = _clean_text(row["run_id"], 80)
    row["goal_summary"] = _clean_text(row["goal_summary"], 240)
    if not row["run_id"]:
        raise ValueError("run_id must not be empty")
    if "model" in row:
        row["model"] = _clean_text(row["model"], 80)
    if "failure_category" in row and row["failure_category"] is not None:
        row["failure_category"] = _clean_text(row["failure_category"], 80)
    if "user_feedback" in row:
        row["user_feedback"] = _clean_text(row["user_feedback"], 300)
    if "pattern_tags" in row:
        row["pattern_tags"] = [
            _clean_text(tag, 48)
            for tag in list(row["pattern_tags"])[:8]
            if _clean_text(tag, 48)
        ]
    if "usage" in row:
        row["usage"] = {
            key: value
            for key, value in dict(row["usage"]).items()
            if key in USAGE_FIELDS and isinstance(value, (int, float)) and value >= 0
        }
    return row


@contextmanager
def _locked_file(path):
    path = Path(path)
    path.parent.mkdir(parents=True, exist_ok=True)
    handle = path.open("a+", encoding="utf-8")
    try:
        if os.name == "nt":
            import msvcrt

            for _ in range(50):
                try:
                    handle.seek(0)
                    msvcrt.locking(handle.fileno(), msvcrt.LK_NBLCK, 1)
                    break
                except OSError:
                    time.sleep(0.02)
            else:
                raise TimeoutError(f"could not lock {path}")
        else:
            import fcntl

            fcntl.flock(handle.fileno(), fcntl.LOCK_EX)
        yield handle
    finally:
        try:
            if os.name == "nt":
                handle.seek(0)
                msvcrt.locking(handle.fileno(), msvcrt.LK_UNLCK, 1)
            else:
                fcntl.flock(handle.fileno(), fcntl.LOCK_UN)
        finally:
            handle.close()


def append_event(path, data):
    row = normalize_event(data)
    identity = (row["run_id"], row["event"], row["timestamp"])
    with _locked_file(path) as handle:
        handle.seek(0)
        for line in handle:
            try:
                existing = json.loads(line)
            except json.JSONDecodeError:
                continue
            if (
                existing.get("run_id"),
                existing.get("event"),
                existing.get("timestamp"),
            ) == identity:
                return row
        handle.seek(0, os.SEEK_END)
        handle.write(json.dumps(row, ensure_ascii=False, separators=(",", ":")) + "\n")
        handle.flush()
        os.fsync(handle.fileno())
    return row


def read_records(path):
    path = Path(path)
    if not path.exists():
        return [], 0
    rows = []
    corrupt = 0
    for line in path.read_text(encoding="utf-8").splitlines():
        if not line.strip():
            continue
        try:
            rows.append(json.loads(line))
        except json.JSONDecodeError:
            corrupt += 1
    return rows, corrupt


def _legacy_row(row, index):
    timestamp = row.get("timestamp") or f"{row.get('date', '1970-01-01')}T00:00:00+00:00"
    digest = hashlib.sha256(
        json.dumps(row, ensure_ascii=False, sort_keys=True).encode("utf-8")
    ).hexdigest()[:20]
    usage = {
        key: row[key]
        for key in USAGE_FIELDS
        if isinstance(row.get(key), (int, float)) and row[key] >= 0
    }
    passed = row.get("passed")
    if passed is True:
        event, outcome = "completed", "passed"
    elif passed is False:
        event, outcome = "failed", "failed"
    else:
        event, outcome = "completed", "unknown"
    return {
        "record_version": "1-compat",
        "run_id": f"legacy-{index}-{digest}",
        "event": event,
        "timestamp": timestamp,
        "date": row.get("date"),
        "runtime": row.get("runtime", "other"),
        "model": row.get("model"),
        "mode": row.get("mode", "Express"),
        "execution_intent": (
            "optimize_and_execute"
            if row.get("execution_requested")
            else "ask_after_optimization"
            if row.get("explicit_request")
            else "implicit_task"
        ),
        "explicit_request": bool(row.get("explicit_request", False)),
        "goal_summary": _clean_text(row.get("goal_summary"), 240),
        "executed": bool(row.get("executed", False)),
        "outcome": outcome,
        "passed": passed,
        "failure_category": row.get("failure_category"),
        "pattern_tags": row.get("pattern_tags", []),
        "user_feedback": row.get("user_feedback", ""),
        "usage": usage,
    }


def aggregate_rows(rows):
    grouped = {}
    for index, raw in enumerate(rows):
        if raw.get("record_version") == "2.0":
            try:
                row = normalize_event(raw)
            except ValueError:
                continue
        else:
            row = _legacy_row(raw, index)
        grouped.setdefault(row["run_id"], []).append(row)

    results = []
    for run_id, events in grouped.items():
        events.sort(key=lambda item: item.get("timestamp", ""))
        latest = dict(events[-1])
        terminal = [item for item in events if item.get("event") in TERMINAL_EVENTS]
        if terminal:
            latest = dict(terminal[-1])
        latest["run_id"] = run_id
        latest["event_count"] = len(events)
        latest.setdefault("outcome", "unknown")
        latest["passed"] = (
            True
            if latest["outcome"] == "passed"
            else False
            if latest["outcome"] == "failed"
            else None
        )
        latest.setdefault("date", latest.get("timestamp", "")[:10])
        for key in ("runtime", "model", "mode", "execution_intent", "goal_summary"):
            if not latest.get(key):
                for event in reversed(events):
                    if event.get(key):
                        latest[key] = event[key]
                        break
        results.append(latest)
    return sorted(results, key=lambda item: (item.get("timestamp", ""), item["run_id"]))
