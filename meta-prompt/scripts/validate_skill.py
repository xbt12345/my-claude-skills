import json
import re
import sys
from pathlib import Path


REQUIRED_FILES = [
    "SKILL.md",
    "references/diagnosis.md",
    "references/goal-elicitation.md",
    "references/taste-elicitation.md",
    "references/evaluation.md",
    "references/compiler.md",
    "references/model-adapters.md",
    "references/token-economy.md",
    "references/architecture.md",
    "references/domain-patterns.md",
    "schemas/goal-contract.yaml",
    "schemas/taste-contract.yaml",
    "schemas/prompt-spec.yaml",
    "schemas/eval-case.yaml",
    "schemas/run-trace.yaml",
    "schemas/run-record.yaml",
    "evals/regression.json",
    "evals/blind-holdout.json",
    "evals/diverse-scenarios.json",
    "evals/diverse-benchmark-report.json",
    "evals/diverse-benchmark-report.md",
    "evals/web-research-process-case.md",
    "evals/token-audit-report.json",
    "evals/token-audit-report.md",
    "evals/token-economy-research.md",
    "scripts/compile_prompt.py",
    "scripts/run_diverse_benchmark.py",
    "scripts/token_audit.py",
    "scripts/feedback_store.py",
    "scripts/run_feedback.py",
    "scripts/blind_eval.py",
    "scripts/log_run.py",
    "scripts/weekly_reflect.py",
]

FORBIDDEN_DOMAIN_PATTERNS = [
    re.compile(r"\d+\s*年.{0,20}经验"),
    re.compile(r"资深(?:助教|专家|分析师|顾问)"),
    re.compile(r"爆款文章编辑"),
    re.compile(r"顶级(?:专家|顾问)"),
    re.compile(r"^\[角色\]", re.MULTILINE),
    re.compile(r"置信度：\{\{X%\}\}"),
]

FORBIDDEN_PATHS = [
    "templates",
    "archive",
    "SPRINT.md",
    "REVIEW.md",
    "evals/sample-spec.json",
]

PROJECT_SPECIFIC_PATTERNS = [
    re.compile(r"\u6ca7\u7c9f"),
]


def collect_errors(root):
    root = Path(root)
    errors = []
    for relative in REQUIRED_FILES:
        if not (root / relative).is_file():
            errors.append(f"missing file: {relative}")
    for relative in FORBIDDEN_PATHS:
        if (root / relative).exists():
            errors.append(f"forbidden path: {relative}")
    skill_path = root / "SKILL.md"
    if skill_path.exists():
        text = skill_path.read_text(encoding="utf-8")
        if len(text.splitlines()) > 220:
            errors.append("SKILL.md exceeds 220 lines")
        if not text.startswith("---\nname: meta-prompt\n"):
            errors.append("invalid SKILL.md frontmatter")

    schema_dir = root / "schemas"
    if schema_dir.exists():
        for path in schema_dir.glob("*.yaml"):
            try:
                json.loads(path.read_text(encoding="utf-8"))
            except (OSError, json.JSONDecodeError) as exc:
                errors.append(f"invalid schema {path.name}: {exc}")

    regression = root / "evals/regression.json"
    if regression.exists():
        try:
            cases = json.loads(regression.read_text(encoding="utf-8"))
            if len(cases) < 20:
                errors.append("regression suite has fewer than 20 cases")
            ids = [case.get("id") for case in cases]
            if len(ids) != len(set(ids)):
                errors.append("regression case ids are not unique")
        except (OSError, json.JSONDecodeError) as exc:
            errors.append(f"invalid regression suite: {exc}")

    domain_patterns = root / "references/domain-patterns.md"
    if domain_patterns.exists():
        text = domain_patterns.read_text(encoding="utf-8")
        if "触发条件" not in text or "不适用条件" not in text:
            errors.append("domain-patterns.md: missing applicability metadata")
        for pattern in FORBIDDEN_DOMAIN_PATTERNS:
            if pattern.search(text):
                errors.append("domain-patterns.md: forbidden fake authority")

    for path in root.rglob("*"):
        if not path.is_file():
            continue
        if path.suffix.lower() not in {".md", ".json", ".yaml", ".py", ".jsonl"}:
            continue
        text = path.read_text(encoding="utf-8", errors="replace")
        for pattern in PROJECT_SPECIFIC_PATTERNS:
            if pattern.search(text):
                errors.append(f"project-specific content: {path.relative_to(root)}")
    return errors


def main():
    root = Path(sys.argv[1]) if len(sys.argv) > 1 else Path(__file__).resolve().parents[1]
    errors = collect_errors(root)
    if errors:
        for error in errors:
            print(f"ERROR: {error}")
        raise SystemExit(1)
    print("Meta-Prompt validation passed")


if __name__ == "__main__":
    main()
