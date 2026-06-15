import json
import re
import unittest
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]


class MetaPromptStructureTests(unittest.TestCase):
    @unittest.skipUnless((ROOT.parents[2] / "AGENTS.md").is_file(), "requires local agent environment")
    def test_global_policy_declares_automatic_meta_prompt_routing(self):
        policy = ROOT.parents[2] / "AGENTS.md"
        text = policy.read_text(encoding="utf-8")
        self.assertIn("Meta-Prompt 自动路由", text)
        self.assertIn("无需用户说出触发词", text)
        self.assertIn("Express", text)
        self.assertIn("Guided", text)
        self.assertIn("Harness", text)

    def test_skill_declares_explicit_optimization_execution_protocol(self):
        text = (ROOT / "SKILL.md").read_text(encoding="utf-8")
        self.assertIn("显式优化请求", text)
        self.assertIn("先交付优化后的 Prompt", text)
        self.assertIn("直接继续执行", text)
        self.assertIn("询问是否执行", text)

    def test_reorganized_skill_has_only_runtime_and_maintenance_assets(self):
        required = [
            "references/architecture.md",
            "references/domain-patterns.md",
        ]
        forbidden = [
            "templates",
            "archive",
            "SPRINT.md",
            "REVIEW.md",
            "evals/sample-spec.json",
        ]

        for relative in required:
            self.assertTrue((ROOT / relative).is_file(), relative)
        for relative in forbidden:
            self.assertFalse((ROOT / relative).exists(), relative)

        skill = (ROOT / "SKILL.md").read_text(encoding="utf-8")
        self.assertIn("references/architecture.md", skill)
        self.assertIn("references/domain-patterns.md", skill)

    def test_required_phase1_files_exist(self):
        required = [
            "references/diagnosis.md",
            "references/goal-elicitation.md",
            "references/taste-elicitation.md",
            "schemas/goal-contract.yaml",
            "schemas/taste-contract.yaml",
        ]
        missing = [path for path in required if not (ROOT / path).is_file()]
        self.assertEqual(missing, [])

    def test_skill_is_a_compact_router(self):
        text = (ROOT / "SKILL.md").read_text(encoding="utf-8")
        self.assertLessEqual(len(text.splitlines()), 220)
        for reference in [
            "references/diagnosis.md",
            "references/goal-elicitation.md",
            "references/taste-elicitation.md",
        ]:
            self.assertIn(reference, text)
        self.assertIn("Express", text)
        self.assertIn("Guided", text)
        self.assertIn("Harness", text)

    def test_goal_contract_has_required_fields(self):
        schema = json.loads(
            (ROOT / "schemas/goal-contract.yaml").read_text(encoding="utf-8")
        )
        required = set(schema["required"])
        self.assertTrue(
            {
                "surface_request",
                "real_outcome",
                "audience",
                "deliverable",
                "success_evidence",
                "assumptions",
            }.issubset(required)
        )

    def test_taste_contract_supports_pairwise_preferences(self):
        schema = json.loads(
            (ROOT / "schemas/taste-contract.yaml").read_text(encoding="utf-8")
        )
        properties = schema["properties"]
        self.assertIn("positive_references", properties)
        self.assertIn("negative_references", properties)
        self.assertIn("pairwise_preferences", properties)
        self.assertIn("taste_axes", properties)

    def test_domain_patterns_declare_applicability_and_avoid_fake_authority(self):
        forbidden = [
            re.compile(r"\d+\s*年.{0,20}经验"),
            re.compile(r"资深(?:助教|专家|分析师|顾问)"),
            re.compile(r"爆款文章编辑"),
            re.compile(r"顶级(?:专家|顾问)"),
            re.compile(r"^\[角色\]", re.MULTILINE),
            re.compile(r"置信度：\{\{X%\}\}"),
        ]
        failures = []
        path = ROOT / "references/domain-patterns.md"
        text = path.read_text(encoding="utf-8")
        if "触发条件" not in text or "不适用条件" not in text:
            failures.append("domain-patterns.md: missing applicability metadata")
        for pattern in forbidden:
            if pattern.search(text):
                failures.append(f"domain-patterns.md: forbidden {pattern.pattern}")
        self.assertEqual(failures, [])


if __name__ == "__main__":
    unittest.main()
