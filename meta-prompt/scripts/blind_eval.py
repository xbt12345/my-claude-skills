import argparse
import json
import random
from pathlib import Path


VALID_INDEPENDENCE = {
    "model_independent",
    "context_independent",
    "not_independent",
}


def anonymize_pair(baseline, candidate, seed):
    candidate_first = random.Random(seed).choice([False, True])
    if candidate_first:
        public = {"A": candidate, "B": baseline}
        private_mapping = {"A": "candidate", "B": "baseline"}
    else:
        public = {"A": baseline, "B": candidate}
        private_mapping = {"A": "baseline", "B": "candidate"}
    return {
        "seed": seed,
        "public": public,
        "private_mapping": private_mapping,
    }


def build_judge_packet(case, pair):
    return {
        "case_id": case["id"],
        "task": case["task"],
        "constraints": list(case.get("constraints", [])),
        "rubric": list(case.get("rubric", [])),
        "outputs": dict(pair["public"]),
        "instructions": [
            "逐项按量表比较 A 与 B。",
            "只能选择 A、B 或 tie。",
            "单独标记是否存在关键约束退化。",
            "不要猜测输出来源。",
        ],
    }


def deblind_result(judge_result, private_mapping):
    winner = judge_result.get("winner")
    if winner in {"A", "B"}:
        winner = private_mapping[winner]
    elif winner != "tie":
        raise ValueError("winner must be A, B, or tie")
    return {
        "winner": winner,
        "critical_regression": bool(judge_result.get("critical_regression", False)),
        "reason": str(judge_result.get("reason", "")).strip()[:500],
    }


def evaluate_decision(results, independence, token_growth):
    if independence not in VALID_INDEPENDENCE:
        raise ValueError("invalid independence level")
    candidate_wins = sum(item.get("winner") == "candidate" for item in results)
    baseline_wins = sum(item.get("winner") == "baseline" for item in results)
    ties = sum(item.get("winner") == "tie" for item in results)
    report = {
        "approved": False,
        "reason": "candidate_did_not_win",
        "independence": independence,
        "candidate_wins": candidate_wins,
        "baseline_wins": baseline_wins,
        "ties": ties,
        "token_growth": token_growth,
    }
    if independence == "not_independent":
        report["reason"] = "insufficient_independence"
    elif any(item.get("critical_regression") for item in results):
        report["reason"] = "critical_regression"
    elif token_growth > 0.10:
        report["reason"] = "token_growth_exceeded"
    elif results and candidate_wins > len(results) / 2:
        report["approved"] = True
        report["reason"] = "candidate_majority"
    return report


def prepare_cases(holdout, outputs, seed):
    packets = []
    private = []
    for index, case in enumerate(holdout):
        case_outputs = outputs[case["id"]]
        pair = anonymize_pair(
            case_outputs["baseline"], case_outputs["candidate"], seed + index
        )
        packets.append(build_judge_packet(case, pair))
        private.append(
            {
                "case_id": case["id"],
                "seed": pair["seed"],
                "private_mapping": pair["private_mapping"],
            }
        )
    return {"judge_packets": packets, "private_mappings": private}


def main():
    parser = argparse.ArgumentParser(description="Prepare or score blind A/B evaluation.")
    subparsers = parser.add_subparsers(dest="command", required=True)

    prepare = subparsers.add_parser("prepare")
    prepare.add_argument("--holdout", type=Path, required=True)
    prepare.add_argument("--outputs", type=Path, required=True)
    prepare.add_argument("--seed", type=int, default=1)
    prepare.add_argument("--public-out", type=Path, required=True)
    prepare.add_argument("--private-out", type=Path, required=True)

    decide = subparsers.add_parser("decide")
    decide.add_argument("--results", type=Path, required=True)
    decide.add_argument("--independence", choices=sorted(VALID_INDEPENDENCE), required=True)
    decide.add_argument("--token-growth", type=float, required=True)
    args = parser.parse_args()

    if args.command == "prepare":
        holdout = json.loads(args.holdout.read_text(encoding="utf-8-sig"))
        outputs = json.loads(args.outputs.read_text(encoding="utf-8-sig"))
        prepared = prepare_cases(holdout, outputs, args.seed)
        args.public_out.parent.mkdir(parents=True, exist_ok=True)
        args.private_out.parent.mkdir(parents=True, exist_ok=True)
        args.public_out.write_text(
            json.dumps(prepared["judge_packets"], ensure_ascii=False, indent=2) + "\n",
            encoding="utf-8",
        )
        args.private_out.write_text(
            json.dumps(prepared["private_mappings"], ensure_ascii=False, indent=2) + "\n",
            encoding="utf-8",
        )
        result = {"prepared": len(prepared["judge_packets"])}
    else:
        results = json.loads(args.results.read_text(encoding="utf-8-sig"))
        result = evaluate_decision(results, args.independence, args.token_growth)
    print(json.dumps(result, ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()
