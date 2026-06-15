import argparse
import json
from pathlib import Path
from statistics import mean, median

try:
    from scripts.compile_prompt import MODE_BUDGETS, compile_prompt, estimate_tokens
    from scripts.run_diverse_benchmark import build_candidate_spec, load_scenarios
except ModuleNotFoundError:
    from compile_prompt import MODE_BUDGETS, compile_prompt, estimate_tokens
    from run_diverse_benchmark import build_candidate_spec, load_scenarios


ROOT = Path(__file__).resolve().parents[1]

PRICE_PER_MILLION = {
    "gpt-5.5": {"input": 5.0, "cached_input": 0.5, "output": 30.0},
    "claude-opus-4.6": {"input": 5.0, "cached_input": 0.5, "output": 25.0},
    "claude-sonnet-4.6": {"input": 3.0, "cached_input": 0.3, "output": 15.0},
}


def _tokens(text):
    return estimate_tokens(text)[0]


def static_context():
    skill = ROOT / "SKILL.md"
    references = sorted((ROOT / "references").glob("*.md"))
    schemas = sorted((ROOT / "schemas").glob("*"))
    rows = []
    for path in [skill, *references, *schemas]:
        text = path.read_text(encoding="utf-8")
        rows.append(
            {
                "file": str(path.relative_to(ROOT)),
                "chars": len(text),
                "tokens": _tokens(text),
            }
        )
    return {
        "skill_entry_tokens": rows[0]["tokens"],
        "all_disclosable_tokens": sum(row["tokens"] for row in rows),
        "files": rows,
    }


def prompt_context(scenarios):
    rows = []
    for scenario in scenarios:
        result = compile_prompt(build_candidate_spec(scenario))
        rows.append(
            {
                "id": scenario["id"],
                "mode": scenario["mode"],
                "runtime": scenario["target_runtime"],
                "tokens": result["usage"]["estimated_prompt_tokens"],
                "budget": result["usage"]["prompt_budget"],
                "within_budget": result["usage"]["within_budget"],
                "detail_level": result["usage"]["detail_level"],
                "max_output_tokens": result["runtime"]["max_output_tokens"],
            }
        )
    tokens = [row["tokens"] for row in rows]
    by_mode = {}
    for mode in MODE_BUDGETS:
        mode_rows = [row for row in rows if row["mode"] == mode]
        if mode_rows:
            by_mode[mode] = {
                "count": len(mode_rows),
                "mean_tokens": round(mean(row["tokens"] for row in mode_rows), 1),
                "max_tokens": max(row["tokens"] for row in mode_rows),
                "budget": MODE_BUDGETS[mode],
                "pass_rate": round(
                    sum(row["within_budget"] for row in mode_rows) / len(mode_rows), 4
                ),
            }
    return {
        "count": len(rows),
        "mean_tokens": round(mean(tokens), 1),
        "median_tokens": median(tokens),
        "min_tokens": min(tokens),
        "max_tokens": max(tokens),
        "sum_tokens": sum(tokens),
        "budget_pass_rate": round(
            sum(row["within_budget"] for row in rows) / len(rows), 4
        ),
        "by_mode": by_mode,
        "rows": rows,
    }


def equivalent_costs(static, prompts):
    output_assumption = {
        "Express": 300,
        "Guided": 600,
        "Harness": 1000,
    }
    scenarios = prompts["rows"]
    costs = {}
    for model, prices in PRICE_PER_MILLION.items():
        prompt_only = prompts["mean_tokens"] * prices["output"] / 1_000_000
        entry_input = static["skill_entry_tokens"] * prices["input"] / 1_000_000
        cached_entry = (
            static["skill_entry_tokens"] * prices["cached_input"] / 1_000_000
        )
        estimated_execution = mean(
            row["tokens"] * prices["input"] / 1_000_000
            + output_assumption[row["mode"]] * prices["output"] / 1_000_000
            for row in scenarios
        )
        costs[model] = {
            "generate_prompt_as_output_usd": round(prompt_only, 6),
            "skill_entry_uncached_input_usd": round(entry_input, 6),
            "skill_entry_cached_input_usd": round(cached_entry, 6),
            "execute_compiled_prompt_estimate_usd": round(estimated_execution, 6),
            "note": "API-equivalent estimate; subscription quota is not dollar billing.",
        }
    return costs


def build_report(scenarios, previous_mean_tokens=None):
    static = static_context()
    prompts = prompt_context(scenarios)
    reduction = None
    if previous_mean_tokens:
        reduction = round(
            1 - prompts["mean_tokens"] / float(previous_mean_tokens),
            4,
        )
    return {
        "method": {
            "tokenizer": "o200k_base when available; conservative char fallback otherwise",
            "scope": "static skill context and deterministic compiled prompts",
            "historical_usage_attribution": "unavailable",
            "historical_limit": (
                "Claude/Codex logs meter whole sessions and cached context; they do not "
                "isolate net tokens caused by one Skill."
            ),
        },
        "static_context": static,
        "compiled_prompts": prompts,
        "comparison": {
            "previous_mean_tokens": previous_mean_tokens,
            "current_mean_tokens": prompts["mean_tokens"],
            "reduction_rate": reduction,
        },
        "api_equivalent_costs": equivalent_costs(static, prompts),
    }


def write_markdown(report, path):
    static = report["static_context"]
    prompts = report["compiled_prompts"]
    comparison = report["comparison"]
    lines = [
        "# Meta-Prompt Token Audit",
        "",
        "## Measured",
        "",
        f"- SKILL.md entry: {static['skill_entry_tokens']} tokens",
        f"- All references + schemas if fully loaded: {static['all_disclosable_tokens']} tokens",
        f"- Compiled prompt mean: {prompts['mean_tokens']} tokens",
        f"- Range: {prompts['min_tokens']}–{prompts['max_tokens']} tokens",
        f"- Budget pass rate: {prompts['budget_pass_rate']:.1%}",
    ]
    if comparison["reduction_rate"] is not None:
        lines.append(
            f"- Previous mean: {comparison['previous_mean_tokens']} tokens; "
            f"reduction: {comparison['reduction_rate']:.1%}"
        )
    lines.extend(
        [
            "",
            "## By Mode",
            "",
            "| Mode | Count | Mean | Max | Budget | Pass |",
            "|---|---:|---:|---:|---:|---:|",
        ]
    )
    for mode, row in prompts["by_mode"].items():
        lines.append(
            f"| {mode} | {row['count']} | {row['mean_tokens']} | "
            f"{row['max_tokens']} | {row['budget']} | {row['pass_rate']:.1%} |"
        )
    lines.extend(
        [
            "",
            "## Evidence Boundary",
            "",
            "- Token counts cover static files and deterministic compiled prompts.",
            "- Historical Claude/Codex session usage cannot isolate the net cost caused by this Skill.",
            "- API-equivalent USD values are comparison estimates, not subscription charges.",
            "- Real optimization requires actual input/output/cached token fields recorded per run.",
        ]
    )
    Path(path).write_text("\n".join(lines) + "\n", encoding="utf-8")


def main():
    parser = argparse.ArgumentParser(description="Audit Meta-Prompt token costs.")
    parser.add_argument(
        "--scenarios",
        type=Path,
        default=ROOT / "evals/diverse-scenarios.json",
    )
    parser.add_argument("--previous-mean", type=float, default=558.3)
    parser.add_argument(
        "--output",
        type=Path,
        default=ROOT / "evals/token-audit-report.json",
    )
    parser.add_argument(
        "--markdown",
        type=Path,
        default=ROOT / "evals/token-audit-report.md",
    )
    args = parser.parse_args()
    report = build_report(load_scenarios(args.scenarios), args.previous_mean)
    args.output.write_text(
        json.dumps(report, ensure_ascii=False, indent=2) + "\n",
        encoding="utf-8",
    )
    write_markdown(report, args.markdown)
    print(json.dumps(report["comparison"], ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()

