import unittest
import json
import subprocess
import sys
import tempfile
from pathlib import Path

from scripts.blind_eval import (
    anonymize_pair,
    build_judge_packet,
    evaluate_decision,
)


class BlindEvaluationTests(unittest.TestCase):
    def test_ab_mapping_is_seed_reproducible(self):
        first = anonymize_pair("baseline text", "candidate text", seed=42)
        second = anonymize_pair("baseline text", "candidate text", seed=42)

        self.assertEqual(first, second)
        self.assertEqual(set(first["public"]), {"A", "B"})
        self.assertEqual(set(first["private_mapping"].values()), {"baseline", "candidate"})

    def test_public_judge_packet_hides_candidate_identity(self):
        case = {
            "id": "h1",
            "task": "优化一个产品需求",
            "constraints": ["不得改变目标"],
            "rubric": ["目标保持", "可验证性"],
        }
        pair = anonymize_pair("方案甲正文", "方案乙正文", seed=7)

        packet = build_judge_packet(case, pair)
        serialized = str(packet).lower()

        self.assertIn("A", packet["outputs"])
        self.assertIn("B", packet["outputs"])
        self.assertNotIn("baseline", serialized)
        self.assertNotIn("candidate", serialized)
        self.assertNotIn("private_mapping", serialized)

    def test_not_independent_cannot_approve_change(self):
        decision = evaluate_decision(
            [{"winner": "candidate", "critical_regression": False}],
            independence="not_independent",
            token_growth=0.0,
        )

        self.assertFalse(decision["approved"])
        self.assertEqual(decision["reason"], "insufficient_independence")

    def test_majority_win_without_constraint_regression_can_approve(self):
        decision = evaluate_decision(
            [
                {"winner": "candidate", "critical_regression": False},
                {"winner": "candidate", "critical_regression": False},
                {"winner": "baseline", "critical_regression": False},
            ],
            independence="model_independent",
            token_growth=0.05,
        )

        self.assertTrue(decision["approved"])
        self.assertEqual(decision["candidate_wins"], 2)

    def test_token_growth_over_ten_percent_blocks_approval(self):
        decision = evaluate_decision(
            [
                {"winner": "candidate", "critical_regression": False},
                {"winner": "candidate", "critical_regression": False},
                {"winner": "baseline", "critical_regression": False},
            ],
            independence="context_independent",
            token_growth=0.101,
        )

        self.assertFalse(decision["approved"])
        self.assertEqual(decision["reason"], "token_growth_exceeded")

    def test_critical_regression_blocks_approval(self):
        decision = evaluate_decision(
            [
                {"winner": "candidate", "critical_regression": False},
                {"winner": "candidate", "critical_regression": True},
                {"winner": "candidate", "critical_regression": False},
            ],
            independence="model_independent",
            token_growth=-0.1,
        )

        self.assertFalse(decision["approved"])
        self.assertEqual(decision["reason"], "critical_regression")

    def test_cli_accepts_utf8_bom_files_from_powershell(self):
        root = Path(__file__).resolve().parents[1]
        with tempfile.TemporaryDirectory() as directory:
            directory = Path(directory)
            results = directory / "results.json"
            results.write_text(
                json.dumps(
                    [
                        {"winner": "candidate", "critical_regression": False},
                        {"winner": "candidate", "critical_regression": False},
                        {"winner": "baseline", "critical_regression": False},
                    ]
                ),
                encoding="utf-8-sig",
            )
            completed = subprocess.run(
                [
                    sys.executable,
                    str(root / "scripts/blind_eval.py"),
                    "decide",
                    "--results",
                    str(results),
                    "--independence",
                    "model_independent",
                    "--token-growth",
                    "0.05",
                ],
                capture_output=True,
                text=True,
                encoding="utf-8",
            )

        self.assertEqual(completed.returncode, 0, completed.stderr)
        self.assertTrue(json.loads(completed.stdout)["approved"])


if __name__ == "__main__":
    unittest.main()
