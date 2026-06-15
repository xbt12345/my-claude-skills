import argparse
import json
from pathlib import Path


ADAPTERS = {
    "chatgpt": "json_schema",
    "claude": "xml_sections",
    "gemini": "sectioned_text",
    "image": "visual_prompt",
    "coding-agent": "agent_protocol",
}

MODE_BUDGETS = {
    "Express": 180,
    "Guided": 350,
    "Harness": 700,
}

OUTPUT_BUDGETS = {
    "Express": 500,
    "Guided": 900,
    "Harness": 1600,
}


def _require(spec, fields):
    missing = [field for field in fields if field not in spec]
    if missing:
        raise ValueError(f"missing required fields: {', '.join(missing)}")


def estimate_tokens(text):
    try:
        import tiktoken

        encoding = tiktoken.get_encoding("o200k_base")
        return len(encoding.encode(text)), "o200k_base"
    except (ImportError, KeyError, OSError):
        # Conservative fallback for mixed Chinese/English instructions.
        return max(1, (len(text) + 1) // 2), "char-fallback"


def _join_values(label, values):
    values = [str(value).strip() for value in values or [] if str(value).strip()]
    return f"{label}: {'; '.join(values)}" if values else None


def _deliverable_text(deliverable):
    if not deliverable:
        return ""
    if isinstance(deliverable, str):
        return deliverable
    deliverable_type = deliverable.get("type") or deliverable.get("format")
    sections = deliverable.get("sections", [])
    parts = []
    if deliverable_type:
        parts.append(str(deliverable_type))
    if sections:
        parts.append("sections=" + "/".join(str(item) for item in sections))
    if deliverable.get("max_words"):
        parts.append(f"max_words={deliverable['max_words']}")
    return "; ".join(parts) or json.dumps(deliverable, ensure_ascii=False)


def _requirement_lines(requirements, detail):
    lines = []
    for item in requirements:
        core = f"{item['id']} {item['requirement']}: {item['prompt_instruction']}"
        if detail == "full":
            core += (
                f" | Test: {item['acceptance_test']}"
                f" | Fail: {item['failure_handling']}"
            )
        elif detail == "test":
            core += f" | Test: {item['acceptance_test']}"
        lines.append(core)
    return lines


def _common_context(goal, detail):
    lines = []
    if detail in {"guided", "full"} and goal.get("audience"):
        lines.append(f"Audience: {goal['audience']}")
    if detail == "full":
        for label, field in [
            ("Inputs", "available_inputs"),
            ("约束", "constraints"),
            ("非目标", "non_goals"),
            ("Success", "success_evidence"),
            ("Assumptions", "assumptions"),
        ]:
            line = _join_values(label, goal.get(field, []))
            if line:
                lines.append(line)
    elif detail == "guided":
        for label, field in [
            ("约束", "constraints"),
            ("非目标", "non_goals"),
            ("Assumptions", "assumptions"),
        ]:
            line = _join_values(label, goal.get(field, []))
            if line:
                lines.append(line)
    return lines


def _render_text(spec, detail):
    goal = spec["goal_contract"]
    detail_map = {
        "minimal": "minimal",
        "guided": "test",
        "full": "full",
    }
    lines = [
        f"Goal: {goal['real_outcome']}",
        f"Priority: {spec['highest_priority_constraint']}",
    ]
    lines.extend(_common_context(goal, detail))
    lines.append("Requirements:")
    lines.extend(
        f"- {line}"
        for line in _requirement_lines(spec["requirements"], detail_map[detail])
    )
    evidence = spec.get("evidence_and_uncertainty", [])
    if detail == "full" and evidence:
        lines.append("Evidence: " + "; ".join(evidence))
    failure_modes = spec.get("failure_modes", [])
    if detail == "full" and failure_modes:
        lines.append("Avoid: " + "; ".join(failure_modes))
    deliverable = _deliverable_text(spec["deliverable"])
    if deliverable:
        lines.append("Output: " + deliverable)
    final_check = spec.get("final_check", [])
    if detail == "full" and final_check:
        lines.append("Final check: " + "; ".join(final_check))
    elif final_check:
        lines.append("Check: " + final_check[0])
    return "\n".join(lines)


def _render_image(spec, detail):
    taste = spec.get("taste_contract") or {}
    goal = spec["goal_contract"]
    lines = [
        f"PURPOSE: {goal['real_outcome']}",
        f"EFFECT: {taste.get('desired_effect', '按真实目标建立视觉效果')}",
    ]
    must_have = taste.get("must_have", [])
    must_avoid = taste.get("must_avoid", [])
    if must_have:
        lines.append("MUST: " + "; ".join(must_have))
    lines.append("EXECUTION:")
    lines.extend(
        f"- {line}"
        for line in _requirement_lines(
            spec["requirements"], "full" if detail == "full" else "minimal"
        )
    )
    if must_avoid:
        lines.append("EXCLUDE: " + "; ".join(must_avoid))
    if spec.get("final_check"):
        lines.append("CHECK: " + "; ".join(spec["final_check"]))
    return "\n".join(lines)


def _render_coding_agent(spec, detail):
    prompt = _render_text(spec, detail)
    if detail == "full":
        prompt += (
            "\nTool Policy: use declared workspace tools; request approval before "
            "irreversible actions."
            "\nCheckpoint: run each acceptance test and record evidence."
        )
    return prompt


def _render(spec, detail):
    runtime = spec["target_runtime"]
    if runtime == "image":
        return _render_image(spec, detail)
    if runtime == "coding-agent":
        return _render_coding_agent(spec, detail)
    return _render_text(spec, detail)


def _detail_sequence(mode):
    return {
        "Express": ["minimal"],
        "Guided": ["guided", "minimal"],
        "Harness": ["full", "guided", "minimal"],
    }[mode]


def _compile_with_budget(spec, budget):
    attempts = []
    for detail in _detail_sequence(spec["mode"]):
        prompt = _render(spec, detail)
        token_count, estimator = estimate_tokens(prompt)
        attempts.append(
            {
                "detail": detail,
                "estimated_tokens": token_count,
            }
        )
        if token_count <= budget:
            return prompt, token_count, estimator, detail, attempts
    return prompt, token_count, estimator, detail, attempts


def compile_prompt(spec):
    _require(
        spec,
        [
            "goal_contract",
            "mode",
            "target_runtime",
            "highest_priority_constraint",
            "requirements",
            "deliverable",
            "final_check",
        ],
    )
    runtime = spec["target_runtime"]
    mode = spec["mode"]
    if runtime not in ADAPTERS:
        raise ValueError(f"unsupported runtime: {runtime}")
    if mode not in MODE_BUDGETS:
        raise ValueError(f"unsupported mode: {mode}")

    requested_budget = spec.get("token_budget") or {}
    prompt_budget = requested_budget.get("max_prompt_tokens", MODE_BUDGETS[mode])
    max_output_tokens = requested_budget.get(
        "max_output_tokens", OUTPUT_BUDGETS[mode]
    )
    prompt, token_count, estimator, detail, attempts = _compile_with_budget(
        spec, prompt_budget
    )

    runtime_config = {
        "chatgpt": {"output_constraint": "json_schema", "human_approval": "on_high_risk"},
        "claude": {"output_constraint": "sectioned_text", "human_approval": "on_high_risk"},
        "gemini": {"output_constraint": "sectioned_text", "human_approval": "on_high_risk"},
        "image": {"output_constraint": "visual_prompt", "human_approval": "on_final_taste"},
        "coding-agent": {
            "output_constraint": "agent_protocol",
            "human_approval": "on_irreversible_action",
        },
    }[runtime]
    runtime_config["max_output_tokens"] = max_output_tokens

    links = [
        {
            "id": item["id"],
            "instruction": item["prompt_instruction"],
            "acceptance_test": item["acceptance_test"],
            "failure_handling": item["failure_handling"],
        }
        for item in spec["requirements"]
    ]
    usage = {
        "estimated_prompt_tokens": token_count,
        "prompt_budget": prompt_budget,
        "within_budget": token_count <= prompt_budget,
        "estimator": estimator,
        "detail_level": detail,
        "attempts": attempts,
    }
    return {
        "adapter": ADAPTERS[runtime],
        "prompt": prompt,
        "runtime": runtime_config,
        "usage": usage,
        "trace": {
            "trace_version": "1.0",
            "target_runtime": runtime,
            "adapter": ADAPTERS[runtime],
            "mode": mode,
            "goal": spec["goal_contract"]["real_outcome"],
            "requirement_links": links,
            "assumptions": spec["goal_contract"].get("assumptions", []),
            "usage": {
                key: usage[key]
                for key in [
                    "estimated_prompt_tokens",
                    "prompt_budget",
                    "within_budget",
                    "estimator",
                ]
            },
        },
    }


def main():
    parser = argparse.ArgumentParser(description="Compile a Prompt Spec for a target runtime.")
    parser.add_argument("spec", type=Path)
    parser.add_argument("--output", type=Path)
    args = parser.parse_args()
    result = compile_prompt(json.loads(args.spec.read_text(encoding="utf-8")))
    rendered = json.dumps(result, ensure_ascii=False, indent=2)
    if args.output:
        args.output.write_text(rendered + "\n", encoding="utf-8")
    else:
        print(rendered)


if __name__ == "__main__":
    main()
