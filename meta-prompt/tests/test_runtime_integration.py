import unittest
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
HOME = ROOT.parents[2]


class RuntimeIntegrationTests(unittest.TestCase):
    def test_skill_uses_explicit_execution_intent_and_lifecycle(self):
        text = (ROOT / "SKILL.md").read_text(encoding="utf-8")

        self.assertIn("optimize_only", text)
        self.assertIn("optimize_and_execute", text)
        self.assertIn("ask_after_optimization", text)
        self.assertIn("run_feedback.py start", text)
        self.assertIn("run_feedback.py finish", text)
        self.assertNotIn("Prompt 本身包含明确可执行任务", text)

    @unittest.skipUnless((HOME / "AGENTS.md").is_file(), "requires local agent environment")
    def test_global_policy_does_not_infer_intent_from_optimized_prompt(self):
        text = (HOME / "AGENTS.md").read_text(encoding="utf-8")

        self.assertIn("optimize_only", text)
        self.assertIn("optimize_and_execute", text)
        self.assertIn("ask_after_optimization", text)
        self.assertNotIn("Prompt 含明确执行任务则继续执行", text)

    @unittest.skipUnless(
        (HOME / ".agents/harness/hooks/session-stop.sh").is_file(),
        "requires local agent environment",
    )
    def test_claude_stop_hook_runs_no_model_stale_cleanup(self):
        text = (
            HOME / ".agents/harness/hooks/session-stop.sh"
        ).read_text(encoding="utf-8")

        self.assertIn("run_feedback.py", text)
        self.assertIn("abandon --stale", text)
        self.assertNotIn("blind_eval.py", text)

    @unittest.skipUnless(
        (HOME / ".codex/automations/meta-prompt/automation.toml").is_file(),
        "requires local agent environment",
    )
    def test_weekly_automation_gates_blind_evaluation(self):
        text = (
            HOME / ".codex/automations/meta-prompt/automation.toml"
        ).read_text(encoding="utf-8")

        self.assertIn("blind_eval_required", text)
        self.assertIn("scripts/blind_eval.py", text)
        self.assertRegex(text, r"最多(?:选择)? 3")

    def test_validator_requires_new_runtime_assets(self):
        text = (ROOT / "scripts/validate_skill.py").read_text(encoding="utf-8")

        for relative in [
            "schemas/run-record.yaml",
            "evals/blind-holdout.json",
            "scripts/feedback_store.py",
            "scripts/run_feedback.py",
            "scripts/blind_eval.py",
        ]:
            self.assertIn(relative, text)


if __name__ == "__main__":
    unittest.main()
