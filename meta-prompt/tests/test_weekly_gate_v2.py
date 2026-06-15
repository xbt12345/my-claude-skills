import json
import tempfile
import unittest
from datetime import date
from pathlib import Path

from scripts.weekly_reflect import analyze_rows, load_rows


def event(run_id, phase, outcome=None, failure_category=None):
    row = {
        "record_version": "2.0",
        "run_id": run_id,
        "event": phase,
        "timestamp": f"2026-06-12T10:{int(run_id[1:]):02d}:00+08:00",
        "runtime": "codex",
        "mode": "Guided",
        "execution_intent": "ask_after_optimization",
        "explicit_request": True,
        "goal_summary": f"运行 {run_id}",
    }
    if outcome is not None:
        row["outcome"] = outcome
    if failure_category is not None:
        row["failure_category"] = failure_category
    return row


class WeeklyGateV2Tests(unittest.TestCase):
    def test_weekly_gate_counts_aggregated_runs_not_events(self):
        rows = []
        for index in range(5):
            run_id = f"r{index}"
            rows.append(event(run_id, "started"))
            rows.append(event(run_id, "completed", "passed"))

        report = analyze_rows(rows, minimum_runs=5, failure_threshold=3)

        self.assertEqual(report["runs"], 5)
        self.assertEqual(report["passed"], 5)

    def test_corrupt_lines_are_reported_not_fatal(self):
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory) / "runs.jsonl"
            path.write_text(
                json.dumps(event("r1", "started"), ensure_ascii=False)
                + "\n{broken\n",
                encoding="utf-8",
            )

            rows, corrupt_rows = load_rows(path, with_meta=True)

        self.assertEqual(len(rows), 1)
        self.assertEqual(corrupt_rows, 1)

    def test_less_than_three_same_failures_never_requests_review(self):
        rows = [
            event("r0", "failed", "failed", "goal_drift"),
            event("r1", "failed", "failed", "goal_drift"),
            event("r2", "completed", "passed"),
            event("r3", "completed", "passed"),
            event("r4", "completed", "passed"),
        ]

        report = analyze_rows(rows, minimum_runs=5, failure_threshold=3)

        self.assertEqual(report["decision"], "stable")
        self.assertFalse(report["blind_eval_required"])

    def test_three_same_failures_after_minimum_runs_requests_review(self):
        rows = [
            event("r0", "failed", "failed", "goal_drift"),
            event("r1", "failed", "failed", "goal_drift"),
            event("r2", "failed", "failed", "goal_drift"),
            event("r3", "completed", "passed"),
            event("r4", "completed", "passed"),
        ]

        report = analyze_rows(rows, minimum_runs=5, failure_threshold=3)

        self.assertEqual(report["decision"], "review-required")
        self.assertTrue(report["blind_eval_required"])
        self.assertEqual(report["repeated_failures"], {"goal_drift": 3})


if __name__ == "__main__":
    unittest.main()
