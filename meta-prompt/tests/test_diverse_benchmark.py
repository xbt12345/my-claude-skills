import json
import subprocess
import sys
import unittest
from pathlib import Path

from scripts.run_diverse_benchmark import (
    DOMAINS,
    build_candidate_spec,
    evaluate_scenario,
    load_scenarios,
)


ROOT = Path(__file__).resolve().parents[1]


class DiverseBenchmarkTests(unittest.TestCase):
    def test_benchmark_has_33_scenarios_and_all_requested_domains(self):
        scenarios = load_scenarios(ROOT / "evals/diverse-scenarios.json")
        self.assertGreaterEqual(len(scenarios), 33)
        counts = {}
        for scenario in scenarios:
            counts[scenario["domain"]] = counts.get(scenario["domain"], 0) + 1
        self.assertEqual(set(counts), set(DOMAINS))
        self.assertTrue(all(count >= 3 for count in counts.values()))

    def test_each_scenario_has_domain_specific_hidden_checks(self):
        scenarios = load_scenarios(ROOT / "evals/diverse-scenarios.json")
        for scenario in scenarios:
            self.assertGreaterEqual(len(scenario["domain_checks"]), 3, scenario["id"])
            self.assertTrue(scenario["clarified_goal"], scenario["id"])
            self.assertTrue(scenario["success_evidence"], scenario["id"])

    def test_candidate_preserves_goal_and_passes_traceability(self):
        scenario = {
            "id": "X01",
            "domain": "product-design",
            "raw_request": "设计一个AI笔记产品",
            "mode": "Harness",
            "target_runtime": "claude",
            "audience": "产品团队",
            "clarified_goal": "验证用户是否愿意持续使用AI复习功能",
            "deliverable": "可测试的MVP方案",
            "constraints": ["两周内验证"],
            "non_goals": ["完整开发"],
            "success_evidence": ["5名用户完成两次复习"],
            "assumptions": ["先做可点击原型"],
            "highest_priority_constraint": "优先验证行为，不堆功能",
            "domain_checks": ["用户问题", "原型", "实验"],
            "failure_modes": ["功能列表没有验证路径"],
            "requirements": [
                {
                    "requirement": "定义用户问题",
                    "instruction": "说明用户问题与现有替代方案",
                    "acceptance": "能指出一个可验证痛点",
                    "failure": "证据不足时列为假设",
                }
            ],
        }
        spec = build_candidate_spec(scenario)
        result = evaluate_scenario(scenario, spec)
        self.assertEqual(spec["goal_contract"]["real_outcome"], scenario["clarified_goal"])
        self.assertEqual(result["traceability_rate"], 1.0)
        self.assertGreater(result["candidate_score"], result["baseline_score"])

    def test_every_generated_candidate_covers_all_domain_checks(self):
        scenarios = load_scenarios(ROOT / "evals/diverse-scenarios.json")
        for scenario in scenarios:
            result = evaluate_scenario(scenario, build_candidate_spec(scenario))
            self.assertEqual(
                result["candidate_domain_coverage"],
                1.0,
                f"{scenario['id']} misses {scenario['domain_checks']}",
            )

    def test_benchmark_report_is_machine_readable(self):
        report_path = ROOT / "evals/diverse-benchmark-report.json"
        report = json.loads(report_path.read_text(encoding="utf-8"))
        self.assertIn("summary", report)
        self.assertIn("domains", report)
        self.assertGreaterEqual(report["summary"]["scenario_count"], 33)
        self.assertIn("prompt_expansion_ratio", report["summary"])
        self.assertIn("perfect_score_rate", report["summary"])
        self.assertFalse(report["method"]["independent_model_blind_test"])

    def test_default_mode_token_budgets_hold_across_diverse_scenarios(self):
        scenarios = load_scenarios(ROOT / "evals/diverse-scenarios.json")
        for scenario in scenarios:
            result = evaluate_scenario(scenario, build_candidate_spec(scenario))
            self.assertTrue(result["within_token_budget"], scenario["id"])

    def test_express_with_four_requirements_stays_compact_and_complete(self):
        scenario = load_scenarios(ROOT / "evals/diverse-scenarios.json")[9]
        scenario["mode"] = "Express"
        result = evaluate_scenario(scenario, build_candidate_spec(scenario))
        self.assertTrue(result["within_token_budget"])
        self.assertEqual(result["candidate_domain_coverage"], 1.0)
        self.assertEqual(result["traceability_rate"], 1.0)

    def test_runner_cli_executes_from_skill_root(self):
        result = subprocess.run(
            [sys.executable, "scripts/run_diverse_benchmark.py"],
            cwd=ROOT,
            capture_output=True,
            text=True,
            encoding="utf-8",
        )
        self.assertEqual(result.returncode, 0, result.stderr)


if __name__ == "__main__":
    unittest.main()
