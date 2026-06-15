import json
import tempfile
import unittest
from pathlib import Path

from scripts.feedback_store import (
    aggregate_rows,
    append_event,
    looks_like_mojibake,
    read_records,
)


class MojibakeDetectionTests(unittest.TestCase):
    def test_flags_argv_encoding_loss(self):
        self.assertTrue(looks_like_mojibake("?????7??8???"))
        self.assertTrue(looks_like_mojibake("含�替换符"))

    def test_accepts_clean_text(self):
        self.assertFalse(looks_like_mojibake("优化一个公众号选题提示词"))
        self.assertFalse(looks_like_mojibake("optimize a coding prompt"))
        self.assertFalse(looks_like_mojibake(""))
        self.assertFalse(looks_like_mojibake("这真的好吗?"))


class FeedbackStoreTests(unittest.TestCase):
    def test_v2_events_merge_by_run_id(self):
        rows = [
            {
                "record_version": "2.0",
                "run_id": "r1",
                "event": "started",
                "timestamp": "2026-06-12T10:00:00+08:00",
                "runtime": "codex",
                "mode": "Guided",
                "execution_intent": "ask_after_optimization",
                "explicit_request": True,
                "goal_summary": "优化需求",
            },
            {
                "record_version": "2.0",
                "run_id": "r1",
                "event": "completed",
                "timestamp": "2026-06-12T10:05:00+08:00",
                "runtime": "codex",
                "mode": "Guided",
                "execution_intent": "ask_after_optimization",
                "explicit_request": True,
                "goal_summary": "优化需求",
                "executed": False,
                "outcome": "passed",
            },
        ]

        result = aggregate_rows(rows)

        self.assertEqual(len(result), 1)
        self.assertEqual(result[0]["run_id"], "r1")
        self.assertEqual(result[0]["outcome"], "passed")
        self.assertEqual(result[0]["event"], "completed")

    def test_legacy_row_remains_readable(self):
        result = aggregate_rows(
            [
                {
                    "date": "2026-06-12",
                    "mode": "Harness",
                    "goal_summary": "旧记录",
                    "passed": False,
                    "failure_category": "goal_drift",
                }
            ]
        )

        self.assertEqual(len(result), 1)
        self.assertEqual(result[0]["outcome"], "failed")
        self.assertEqual(result[0]["failure_category"], "goal_drift")

    def test_read_records_skips_corrupt_lines_and_reports_count(self):
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory) / "runs.jsonl"
            path.write_text(
                json.dumps(
                    {
                        "record_version": "2.0",
                        "run_id": "r1",
                        "event": "started",
                        "timestamp": "2026-06-12T10:00:00+08:00",
                        "runtime": "codex",
                        "mode": "Guided",
                        "execution_intent": "ask_after_optimization",
                        "explicit_request": True,
                        "goal_summary": "有效记录",
                    },
                    ensure_ascii=False,
                )
                + "\n{broken\n",
                encoding="utf-8",
            )

            rows, corrupt_rows = read_records(path)

        self.assertEqual(len(rows), 1)
        self.assertEqual(corrupt_rows, 1)

    def test_append_event_discards_raw_prompt_and_is_idempotent(self):
        event = {
            "record_version": "2.0",
            "run_id": "r1",
            "event": "started",
            "timestamp": "2026-06-12T10:00:00+08:00",
            "runtime": "codex",
            "mode": "Guided",
            "execution_intent": "ask_after_optimization",
            "explicit_request": True,
            "goal_summary": "优化需求",
            "raw_prompt": "不得保存",
        }
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory) / "runs.jsonl"
            first = append_event(path, event)
            append_event(path, event)
            saved = [
                json.loads(line)
                for line in path.read_text(encoding="utf-8").splitlines()
                if line.strip()
            ]

        self.assertNotIn("raw_prompt", first)
        self.assertEqual(len(saved), 1)


if __name__ == "__main__":
    unittest.main()
