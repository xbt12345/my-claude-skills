import json
import importlib.util
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path

from scripts.compile_prompt import MODE_BUDGETS, compile_prompt
from scripts.compare_prompts import compare_prompts
from scripts.stats import aggregate_runs
from scripts.validate_skill import collect_errors


ROOT = Path(__file__).resolve().parents[1]


class EvaluationHarnessTests(unittest.TestCase):
    def test_weekly_reflection_requires_real_data_thresholds(self):
        script = ROOT / "scripts/weekly_reflect.py"
        self.assertTrue(script.is_file())
        spec = importlib.util.spec_from_file_location("weekly_reflect", script)
        module = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(module)

        sparse = [
            {"date": "2026-06-09", "passed": False, "failure_category": "taste"},
            {"date": "2026-06-10", "passed": True, "failure_category": None},
        ]
        result = module.analyze_rows(sparse, minimum_runs=5, failure_threshold=3)
        self.assertEqual(result["decision"], "insufficient-data")

        repeated = [
            {"date": "2026-06-08", "passed": False, "failure_category": "routing"},
            {"date": "2026-06-09", "passed": False, "failure_category": "routing"},
            {"date": "2026-06-10", "passed": False, "failure_category": "routing"},
            {"date": "2026-06-11", "passed": True, "failure_category": None},
            {"date": "2026-06-12", "passed": True, "failure_category": None},
        ]
        result = module.analyze_rows(repeated, minimum_runs=5, failure_threshold=3)
        self.assertEqual(result["decision"], "review-required")
        self.assertEqual(result["repeated_failures"], {"routing": 3})

    def test_run_logger_appends_compact_feedback_without_raw_prompt(self):
        script = ROOT / "scripts/log_run.py"
        self.assertTrue(script.is_file())
        spec = importlib.util.spec_from_file_location("log_run", script)
        module = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(module)

        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory) / "runs.jsonl"
            row = module.append_run(
                path,
                {
                    "mode": "Guided",
                    "goal_summary": "优化产品需求提示词",
                    "explicit_request": True,
                    "execution_requested": False,
                    "executed": False,
                    "passed": True,
                    "pattern_tags": ["requirements"],
                    "raw_prompt": "不应写入日志",
                },
            )
            saved = json.loads(path.read_text(encoding="utf-8"))

        self.assertNotIn("raw_prompt", row)
        self.assertNotIn("raw_prompt", saved)
        self.assertEqual(saved["mode"], "Guided")
        self.assertEqual(saved["goal_summary"], "优化产品需求提示词")

    def test_run_logger_cli_accepts_json_from_stdin(self):
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory) / "runs.jsonl"
            result = subprocess.run(
                [sys.executable, str(ROOT / "scripts/log_run.py"), "--path", str(path)],
                input=json.dumps(
                    {
                        "mode": "Harness",
                        "goal_summary": "测试标准输入",
                        "passed": True,
                    },
                    ensure_ascii=False,
                ),
                text=True,
                capture_output=True,
                encoding="utf-8",
            )
            self.assertEqual(result.returncode, 0, result.stderr)
            self.assertIn("测试标准输入", result.stdout)
            saved = json.loads(path.read_text(encoding="utf-8"))
        self.assertEqual(saved["goal_summary"], "测试标准输入")

    def sample_spec(self):
        return {
            "goal_contract": {
                "surface_request": "分析市场",
                "real_outcome": "决定是否启动小规模试验",
                "audience": "产品负责人",
                "deliverable": "决策简报",
                "constraints": ["两周内完成"],
                "non_goals": ["不直接开发完整产品"],
                "success_evidence": ["能选择试验或放弃并说明理由"],
                "assumptions": ["预算上限为10万元"],
            },
            "taste_contract": None,
            "mode": "Harness",
            "target_runtime": "claude",
            "highest_priority_constraint": "每个结论必须绑定行动判据",
            "requirements": [
                {
                    "id": "R1",
                    "requirement": "比较进入与不进入的机会成本",
                    "prompt_instruction": "给出双向机会成本及其证据",
                    "acceptance_test": "读者能说明淘汰一个方案的理由",
                    "failure_handling": "数据不足时标为假设并降低结论强度",
                }
            ],
            "failure_modes": ["只罗列趋势，不说明行动含义"],
            "evidence_and_uncertainty": ["区分事实、假设与未知项"],
            "deliverable": {"format": "markdown", "max_words": 1200},
            "final_check": ["检查 R1 是否有证据和验收结果"],
        }

    def test_phase2_schemas_are_json_compatible(self):
        for name in ["prompt-spec.yaml", "eval-case.yaml"]:
            data = json.loads((ROOT / "schemas" / name).read_text(encoding="utf-8"))
            self.assertEqual(data["type"], "object")
            self.assertTrue(data["required"])

    def test_regression_suite_has_minimum_coverage(self):
        cases = json.loads(
            (ROOT / "evals/regression.json").read_text(encoding="utf-8")
        )
        self.assertGreaterEqual(len(cases), 20)
        categories = {case["category"] for case in cases}
        self.assertTrue(
            {
                "express",
                "ambiguity",
                "taste",
                "risk",
                "prompt-bloat",
                "goal-misalignment",
            }.issubset(categories)
        )

    def test_candidate_with_traceability_scores_higher_than_vague_baseline(self):
        baseline = "请作为专业专家，深入全面地分析这个问题，给出高质量建议。"
        candidate = """
        [Real Objective] 让产品负责人能选择是否进入该市场。
        [Highest-Priority Constraint] 每个结论必须绑定会改变决策的判据。
        [Requirement R1] 比较进入与不进入的机会成本。
        [Evidence & Uncertainty] 区分事实、假设与未知项。
        [Acceptance Test E1] 读者能选择进入、试验或放弃并说明淘汰理由。
        [Failure Handling] 缺少市场数据时降低结论强度。
        """
        result = compare_prompts(baseline, candidate)
        self.assertGreater(result["candidate"]["score"], result["baseline"]["score"])
        self.assertGreater(result["delta"], 0)

    def test_stats_aggregate_jsonl_runs(self):
        rows = [
            {
                "model": "claude",
                "passed": True,
                "failure_category": None,
                "actual_input_tokens": 100,
                "cached_input_tokens": 40,
                "actual_output_tokens": 50,
            },
            {"model": "claude", "passed": False, "failure_category": "taste"},
            {
                "model": "chatgpt",
                "passed": True,
                "failure_category": None,
                "actual_input_tokens": 200,
                "actual_output_tokens": 70,
            },
        ]
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory) / "runs.jsonl"
            path.write_text(
                "\n".join(json.dumps(row, ensure_ascii=False) for row in rows),
                encoding="utf-8",
            )
            result = aggregate_runs(path)
        self.assertEqual(result["runs"], 3)
        self.assertEqual(result["passed"], 2)
        self.assertEqual(result["models"]["claude"], 2)
        self.assertEqual(result["failure_categories"]["taste"], 1)
        self.assertEqual(result["usage"]["actual_input_tokens"]["total"], 300)
        self.assertEqual(result["usage"]["actual_output_tokens"]["observations"], 2)

    def test_skill_validator_reports_no_errors(self):
        self.assertEqual(collect_errors(ROOT), [])

    def test_compile_supports_five_runtime_adapters(self):
        expected = {
            "chatgpt": "json_schema",
            "claude": "xml_sections",
            "gemini": "sectioned_text",
            "image": "visual_prompt",
            "coding-agent": "agent_protocol",
        }
        for runtime, adapter in expected.items():
            spec = self.sample_spec()
            spec["target_runtime"] = runtime
            result = compile_prompt(spec)
            self.assertEqual(result["adapter"], adapter)
            self.assertTrue(result["prompt"])
            self.assertEqual(result["trace"]["requirement_links"][0]["id"], "R1")

    def test_coding_agent_compiles_tool_policy_and_checkpoints(self):
        spec = self.sample_spec()
        spec["target_runtime"] = "coding-agent"
        result = compile_prompt(spec)
        self.assertIn("Tool Policy", result["prompt"])
        self.assertIn("Checkpoint", result["prompt"])
        self.assertEqual(result["runtime"]["human_approval"], "on_irreversible_action")

    def test_compile_preserves_goal_constraints_and_non_goals(self):
        result = compile_prompt(self.sample_spec())
        self.assertIn("两周内完成", result["prompt"])
        self.assertIn("不直接开发完整产品", result["prompt"])

    def test_image_adapter_uses_taste_and_avoids_fake_role(self):
        spec = self.sample_spec()
        spec["target_runtime"] = "image"
        spec["taste_contract"] = {
            "desired_effect": "克制、温暖、可信",
            "positive_references": ["自然中广角"],
            "negative_references": ["霓虹HDR"],
            "pairwise_preferences": [],
            "must_have": ["单一主视觉"],
            "must_avoid": ["无来源光效"],
            "flexible_dimensions": ["云层形态"],
            "taste_axes": {"saturation": "低到中"},
        }
        result = compile_prompt(spec)
        self.assertIn("克制、温暖、可信", result["prompt"])
        self.assertNotRegex(result["prompt"], r"\d+\s*年.{0,20}经验")

    def test_compile_rejects_unknown_runtime(self):
        spec = self.sample_spec()
        spec["target_runtime"] = "unknown"
        with self.assertRaisesRegex(ValueError, "unsupported runtime"):
            compile_prompt(spec)

    def test_each_mode_respects_its_default_prompt_budget(self):
        for mode, budget in MODE_BUDGETS.items():
            spec = self.sample_spec()
            spec["mode"] = mode
            result = compile_prompt(spec)
            self.assertLessEqual(result["usage"]["estimated_prompt_tokens"], budget)
            self.assertTrue(result["usage"]["within_budget"])

    def test_empty_context_fields_are_not_rendered(self):
        spec = self.sample_spec()
        spec["goal_contract"]["available_inputs"] = []
        spec["goal_contract"]["assumptions"] = []
        result = compile_prompt(spec)
        self.assertNotIn("Available inputs", result["prompt"])
        self.assertNotIn("Assumptions", result["prompt"])
        self.assertNotIn("[]", result["prompt"])

    def test_compact_prompt_keeps_full_traceability_outside_prompt(self):
        spec = self.sample_spec()
        spec["mode"] = "Express"
        result = compile_prompt(spec)
        link = result["trace"]["requirement_links"][0]
        self.assertEqual(link["acceptance_test"], "读者能说明淘汰一个方案的理由")
        self.assertEqual(
            link["failure_handling"],
            "数据不足时标为假设并降低结论强度",
        )

    def test_compile_reports_input_and_output_token_budgets(self):
        spec = self.sample_spec()
        spec["token_budget"] = {
            "max_prompt_tokens": 240,
            "max_output_tokens": 700,
        }
        result = compile_prompt(spec)
        self.assertEqual(result["usage"]["prompt_budget"], 240)
        self.assertEqual(result["runtime"]["max_output_tokens"], 700)
        self.assertIn(result["usage"]["estimator"], {"o200k_base", "char-fallback"})


if __name__ == "__main__":
    unittest.main()
