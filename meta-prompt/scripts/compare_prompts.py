import argparse
import json
import re
from pathlib import Path


POSITIVE_MARKERS = {
    "real_objective": (r"Real Objective|真实目标", 3),
    "priority": (r"Highest-Priority Constraint|最高优先级约束", 3),
    "requirement": (r"Requirement\s+R\d+|需求\s*R\d+", 2),
    "acceptance": (r"Acceptance Test|验收测试", 3),
    "evidence": (r"Evidence & Uncertainty|证据与不确定", 2),
    "failure": (r"Failure (?:Modes|Handling)|失败(?:模式|处理)", 2),
}

VAGUE_PATTERNS = [
    r"专业专家",
    r"深入全面",
    r"高质量",
    r"最佳方案",
    r"确保准确",
]


def score_prompt(text):
    components = {}
    score = 0
    for name, (pattern, weight) in POSITIVE_MARKERS.items():
        matched = bool(re.search(pattern, text, flags=re.IGNORECASE))
        components[name] = weight if matched else 0
        score += components[name]
    vague_hits = sum(bool(re.search(pattern, text)) for pattern in VAGUE_PATTERNS)
    components["vague_penalty"] = -2 * vague_hits
    score += components["vague_penalty"]
    if len(text) > 6000:
        components["bloat_penalty"] = -2
        score -= 2
    else:
        components["bloat_penalty"] = 0
    return {"score": score, "components": components, "characters": len(text)}


def compare_prompts(baseline, candidate):
    baseline_score = score_prompt(baseline)
    candidate_score = score_prompt(candidate)
    return {
        "baseline": baseline_score,
        "candidate": candidate_score,
        "delta": candidate_score["score"] - baseline_score["score"],
    }


def main():
    parser = argparse.ArgumentParser(description="Compare two prompt files.")
    parser.add_argument("baseline", type=Path)
    parser.add_argument("candidate", type=Path)
    args = parser.parse_args()
    result = compare_prompts(
        args.baseline.read_text(encoding="utf-8"),
        args.candidate.read_text(encoding="utf-8"),
    )
    print(json.dumps(result, ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()
