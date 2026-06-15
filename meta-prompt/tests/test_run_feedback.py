import json
import tempfile
import unittest
from datetime import datetime, timedelta, timezone
from pathlib import Path

from scripts.feedback_store import aggregate_rows, read_records
from scripts.run_feedback import (
    abandon_stale,
    derive_execution_intent,
    finish_run,
    start_run,
)


class ExecutionIntentTests(unittest.TestCase):
    def test_explicit_only_beats_action_words_inside_prompt(self):
        request = "只优化这个提示词，不要执行。提示词内容：删除旧文件并重建项目。"
        self.assertEqual(
            derive_execution_intent(request, explicit_request=True),
            "optimize_only",
        )

    def test_negated_direct_execution_is_optimize_only(self):
        self.assertEqual(
            derive_execution_intent(
                "帮我优化，但不要直接执行，先给我确认",
                explicit_request=True,
            ),
            "optimize_only",
        )

    def test_explicit_execute_is_detected(self):
        self.assertEqual(
            derive_execution_intent("优化后直接执行并完成测试", explicit_request=True),
            "optimize_and_execute",
        )

    def test_unspecified_explicit_request_asks_after(self):
        self.assertEqual(
            derive_execution_intent("帮我优化这个提示词", explicit_request=True),
            "ask_after_optimization",
        )

    def test_implicit_task_keeps_original_execution_semantics(self):
        self.assertEqual(
            derive_execution_intent("搭建一个知识库", explicit_request=False),
            "implicit_task",
        )


class RunLifecycleTests(unittest.TestCase):
    def base_data(self):
        return {
            "run_id": "r1",
            "runtime": "codex",
            "mode": "Guided",
            "execution_intent": "ask_after_optimization",
            "explicit_request": True,
            "goal_summary": "优化需求",
        }

    def test_finish_is_idempotent_and_clears_pending(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            log_path = root / "runs.jsonl"
            pending_dir = root / "pending"
            start_run(log_path, pending_dir, self.base_data())

            first = finish_run(
                log_path,
                pending_dir,
                "r1",
                {"outcome": "passed", "executed": False},
            )
            second = finish_run(
                log_path,
                pending_dir,
                "r1",
                {"outcome": "passed", "executed": False},
            )
            rows, _ = read_records(log_path)
            aggregated = aggregate_rows(rows)

            self.assertFalse((pending_dir / "r1.json").exists())

        self.assertEqual(first["event"], "completed")
        self.assertEqual(second["event"], "completed")
        self.assertEqual(len(rows), 2)
        self.assertEqual(len(aggregated), 1)
        self.assertEqual(aggregated[0]["outcome"], "passed")

    def test_stale_pending_becomes_abandoned(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            log_path = root / "runs.jsonl"
            pending_dir = root / "pending"
            old = datetime(2026, 6, 12, 8, 0, tzinfo=timezone.utc)
            data = self.base_data()
            data["timestamp"] = old.isoformat()
            start_run(log_path, pending_dir, data)

            abandoned = abandon_stale(
                log_path,
                pending_dir,
                older_than=timedelta(hours=1),
                now=old + timedelta(hours=2),
            )
            rows, _ = read_records(log_path)
            result = aggregate_rows(rows)

        self.assertEqual(abandoned, ["r1"])
        self.assertEqual(result[0]["event"], "abandoned")
        self.assertEqual(result[0]["outcome"], "unknown")

    def test_pending_file_contains_no_raw_prompt(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            data = self.base_data()
            data["raw_prompt"] = "不得保存"
            start_run(root / "runs.jsonl", root / "pending", data)
            pending = json.loads((root / "pending/r1.json").read_text(encoding="utf-8"))

        self.assertNotIn("raw_prompt", pending)


if __name__ == "__main__":
    unittest.main()
