import argparse
import json
import re
from collections import defaultdict
from pathlib import Path

try:
    from scripts.compile_prompt import compile_prompt
except ModuleNotFoundError:
    from compile_prompt import compile_prompt


ROOT = Path(__file__).resolve().parents[1]

DOMAINS = [
    "product-design",
    "framework-building",
    "knowledge-review",
    "system-architecture",
    "requirements-implementation",
    "skill-authoring",
    "automation",
    "knowledge-base",
    "web-research",
    "creative-ideation",
    "optimization-roadmap",
]

DOMAIN_BLUEPRINTS = {
    "product-design": {
        "audience": "产品负责人和设计团队",
        "deliverable": "可验证的产品方案",
        "checks": ["用户问题", "原型", "实验", "非目标"],
        "prompts": [
            "帮我设计一个AI读书笔记产品",
            "优化现有任务管理工具的新用户体验",
            "设计面向独立创作者的AI内容工作台并规划MVP",
        ],
        "goals": [
            "验证用户是否需要从笔记自动生成复习行动",
            "降低新用户首次完成核心任务前的流失",
            "验证创作者是否愿意把选题到发布的关键流程迁入同一工作台",
        ],
        "requirements": [
            ("用户问题", "定义目标用户、现有替代方案和可验证痛点"),
            ("原型", "设计最低成本原型，不先开发完整功能"),
            ("实验", "给出成功阈值、失败信号和下一步决策"),
        ],
        "constraint": "优先验证真实行为，不以功能数量或界面完整度代替需求证据",
        "failure": "功能清单完整，但没有用户行为验证路径",
    },
    "framework-building": {
        "audience": "需要重复使用该框架的决策者",
        "deliverable": "可复用且有边界的分析框架",
        "checks": ["变量", "判据", "边界", "反例"],
        "prompts": [
            "帮我搭一个判断AI工具值不值得用的框架",
            "建立创业机会评估框架",
            "设计一个跨领域决策框架并避免套模板",
        ],
        "goals": [
            "让使用者能基于同一组判据比较AI工具",
            "让创业者能淘汰伪机会并确定最小验证动作",
            "让框架在不同领域迁移时保留核心机制并暴露失效边界",
        ],
        "requirements": [
            ("变量", "定义少量真正改变结论的变量"),
            ("判据", "规定变量冲突时的选择规则"),
            ("边界", "说明适用条件、失效条件和反例"),
        ],
        "constraint": "框架必须改变判断，不得只是分类术语或问题清单",
        "failure": "框架结构整齐，但无法淘汰任何方案",
    },
    "knowledge-review": {
        "audience": "准备复习和迁移知识的学习者",
        "deliverable": "主动回忆驱动的复习系统",
        "checks": ["主动回忆", "间隔复习", "错题", "迁移"],
        "prompts": [
            "整理这章内容让我复习",
            "把一本书做成两周复习计划",
            "整合课程PPT、笔记和错题，搭建期末复习系统",
        ],
        "goals": [
            "让学习者能回忆本章核心机制并识别误解",
            "两周后仍能解释、预测并迁移书中原则",
            "在有限时间内优先掌握高价值考点并通过模拟题验证",
        ],
        "requirements": [
            ("主动回忆", "每个知识块配套闭卷问题"),
            ("间隔复习", "按遗忘风险安排复习间隔"),
            ("错题", "记录错误类型、错误原因、纠正依据和下一次再测时间"),
            ("迁移", "加入反例、变式和跨情境应用"),
        ],
        "constraint": "不能把阅读、摘抄或看懂当作掌握证据",
        "failure": "总结完整，但学习者无法闭卷解释或做题",
    },
    "system-architecture": {
        "audience": "架构师、开发团队和运维负责人",
        "deliverable": "可落地且可验证的系统架构方案",
        "checks": ["NFR", "故障域", "威胁模型", "可观测性"],
        "prompts": [
            "设计一个文件上传系统架构",
            "搭建支持十万用户的知识库系统",
            "设计多租户AI Agent平台，要求安全、可扩展、可恢复",
        ],
        "goals": [
            "在明确流量与可靠性要求下完成文件上传闭环",
            "在成本边界内支持检索、更新和权限隔离",
            "形成可演进的多租户运行平台并控制工具调用风险",
        ],
        "requirements": [
            ("NFR", "量化容量、延迟、可用性和成本边界"),
            ("故障域", "识别单点、降级路径、恢复目标和数据一致性"),
            ("威胁模型", "覆盖租户隔离、注入、密钥和越权调用"),
            ("可观测性", "定义日志、指标、trace和告警"),
        ],
        "constraint": "架构选择必须绑定负载、故障和安全假设",
        "failure": "列出组件图，但没有容量、失败或恢复证据",
    },
    "requirements-implementation": {
        "audience": "产品、工程和验收人员",
        "deliverable": "从需求到实现与验收的执行协议",
        "checks": ["需求追踪", "非目标", "测试", "回滚"],
        "prompts": [
            "分析这个登录需求并实现",
            "把支付需求拆成开发任务",
            "实现一个跨模块权限系统并保证不破坏现有行为",
        ],
        "goals": [
            "交付可验证的登录行为而不是只完成页面",
            "让支付需求能按依赖实现并通过异常场景验收",
            "在保持兼容性的前提下统一授权决策与审计",
        ],
        "requirements": [
            ("需求追踪", "建立需求到代码、测试和验收的映射"),
            ("非目标", "明确本次不处理的范围"),
            ("测试", "测试先行覆盖正常、异常和边界路径"),
            ("回滚", "定义发布检查点和失败回滚"),
        ],
        "constraint": "每项实现必须有对应验收证据，不能以代码完成代替需求完成",
        "failure": "代码可运行，但关键需求没有测试或行为映射",
    },
    "skill-authoring": {
        "audience": "未来调用该Skill的Agent",
        "deliverable": "可发现、可执行、可前向测试的Skill",
        "checks": ["触发条件", "渐进加载", "RED", "前向测试"],
        "prompts": [
            "写一个处理会议纪要的skill",
            "优化现有投资分析skill",
            "把复杂研究流程固化成可维护的skill",
        ],
        "goals": [
            "让Agent在会议纪要任务中稳定提取决定与行动",
            "降低Skill误触发并提高证据和风险处理质量",
            "让研究流程可复用、可验证且不污染上下文",
        ],
        "requirements": [
            ("触发条件", "描述具体使用症状与不适用场景"),
            ("渐进加载", "主文件只保留核心流程，重材料放references"),
            ("RED", "修改前建立会失败的压力场景"),
            ("前向测试", "用隔离任务验证Skill泛化"),
        ],
        "constraint": "Skill必须改变Agent行为，不能只是记录一次解决过程",
        "failure": "文档很长，但Agent无法判断何时加载或如何验收",
    },
    "automation": {
        "audience": "流程所有者和维护人员",
        "deliverable": "可观测、可恢复的自动化流程",
        "checks": ["触发器", "幂等", "重试", "人工升级"],
        "prompts": [
            "自动整理每天收到的邮件",
            "搭建内容发布自动化流程",
            "优化跨系统订单同步，减少重复和漏单",
        ],
        "goals": [
            "自动归类邮件并把高风险内容交给人工",
            "稳定完成素材校验、排期、发布和结果记录",
            "在网络失败和重复事件下保持订单最终一致",
        ],
        "requirements": [
            ("触发器", "明确事件来源、过滤和启动条件"),
            ("幂等", "重复执行不得产生重复副作用"),
            ("重试", "定义可重试错误、退避和死信处理"),
            ("人工升级", "高风险或多次失败时转人工"),
        ],
        "constraint": "优先保证可恢复与可追踪，不以无人参与为目标",
        "failure": "正常路径自动化，但失败后重复执行或静默丢失",
    },
    "knowledge-base": {
        "audience": "知识库维护者和检索使用者",
        "deliverable": "可检索、可演进、可治理的知识库方案",
        "checks": ["schema", "来源", "去重", "衰减"],
        "prompts": [
            "帮我搭个人知识库",
            "优化团队AI知识库",
            "整合文章、项目经验和决策记录，建立长期知识系统",
        ],
        "goals": [
            "让高价值知识能在需要时被准确找到",
            "减少重复、过期和来源不明内容对回答的污染",
            "让经验、原则和决策形成可追踪连接并持续更新",
        ],
        "requirements": [
            ("schema", "定义实体、元数据、关系和最小存储单位"),
            ("来源", "保留出处、日期、证据等级和访问路径"),
            ("去重", "规定相似条目合并与冲突处理"),
            ("衰减", "标记时效、复核周期和失效条件"),
        ],
        "constraint": "结构必须服务未来检索与更新，不能只追求分类完整",
        "failure": "内容大量积累，但重复、过期且无法定位来源",
    },
    "web-research": {
        "audience": "需要依据研究结果做决策的用户",
        "deliverable": "有来源、时效和不确定性标注的研究报告",
        "checks": ["一手来源", "发布日期", "引用", "分歧证据"],
        "prompts": [
            "上网研究最近的AI Agent趋势",
            "调研三个Prompt优化项目并比较",
            "研究某新兴技术的历史、竞品、用户反馈和未来路径",
        ],
        "goals": [
            "识别近期真正改变Agent落地的机制而非新闻列表",
            "按真实使用场景选择可采用的Prompt优化方案",
            "形成能支持投入决策的纵向历史与横向竞争判断",
        ],
        "requirements": [
            ("一手来源", "优先官方文档、仓库、论文和作者原帖"),
            ("发布日期", "区分发布日、事件日和当前有效性"),
            ("引用", "关键事实附精确URL和访问日期"),
            ("分歧证据", "主动搜索反例、争议和失败反馈"),
        ],
        "constraint": "任何关键判断必须绑定可核实来源和时效边界",
        "failure": "引用很多二手摘要，却无法确认原始事实或当前状态",
    },
    "creative-ideation": {
        "audience": "需要选择创意方向的创作者",
        "deliverable": "可比较、可发展、符合审美边界的创意方向",
        "checks": ["A/B", "审美轴", "约束", "变体"],
        "prompts": [
            "给我一些短视频创意",
            "优化品牌活动创意，想要克制但有记忆点",
            "为AI知识栏目建立独特内容母题和长期创意机制",
        ],
        "goals": [
            "找到与受众痛点相关且可低成本试拍的方向",
            "让活动在不喧闹的前提下形成单一记忆锚点",
            "形成可连续生产但不重复的内容创意空间",
        ],
        "requirements": [
            ("A/B", "提供差异明确的方向并请求比较理由"),
            ("审美轴", "把克制、温度、新颖等偏好转为可观察维度"),
            ("约束", "明确不可牺牲项与禁止结果"),
            ("变体", "在稳定母题下定义可探索范围"),
        ],
        "constraint": "先确认审美边界，再扩展创意数量",
        "failure": "点子数量很多，但同质、不可执行或不符合用户品味",
    },
    "optimization-roadmap": {
        "audience": "负责持续改进的流程或产品所有者",
        "deliverable": "基于瓶颈、实验和停止条件的优化路径",
        "checks": ["基线", "瓶颈", "实验", "停止条件"],
        "prompts": [
            "帮我优化工作效率",
            "优化一个转化率不高的注册流程",
            "规划Agent系统从能用到可靠的迭代路线",
        ],
        "goals": [
            "识别最消耗时间且可改变的工作环节",
            "定位注册漏斗的主要损失并验证改动因果",
            "按失败频率和风险逐步提高Agent任务完成率",
        ],
        "requirements": [
            ("基线", "记录当前表现、成本和失败分布"),
            ("瓶颈", "定位限制整体结果的首要约束"),
            ("实验", "每轮只验证一个关键假设并保留对照"),
            ("停止条件", "定义达标、无改善、超预算或升级条件"),
        ],
        "constraint": "优先优化真实瓶颈，不按容易测量的指标排序",
        "failure": "列出大量改进建议，却没有基线、顺序或证伪机制",
    },
}


def _level(index):
    return ["guided", "harness", "harness"][index]


def _runtime(domain, index):
    if domain == "creative-ideation" and index == 1:
        return "image"
    if domain in {
        "system-architecture",
        "requirements-implementation",
        "skill-authoring",
        "automation",
        "knowledge-base",
    }:
        return "coding-agent"
    if index == 0:
        return "chatgpt"
    return "claude"


def generate_scenarios():
    scenarios = []
    for domain_index, domain in enumerate(DOMAINS, start=1):
        blueprint = DOMAIN_BLUEPRINTS[domain]
        for index, raw_request in enumerate(blueprint["prompts"]):
            requirements = []
            for requirement, instruction in blueprint["requirements"]:
                requirements.append(
                    {
                        "requirement": requirement,
                        "instruction": instruction,
                        "acceptance": f"交付物明确覆盖“{requirement}”并给出可检查证据",
                        "failure": f"缺少“{requirement}”时不得宣称完成",
                    }
                )
            scenarios.append(
                {
                    "id": f"D{domain_index:02d}-{index + 1}",
                    "domain": domain,
                    "difficulty": ["basic", "intermediate", "advanced"][index],
                    "raw_request": raw_request,
                    "mode": _level(index).title(),
                    "target_runtime": _runtime(domain, index),
                    "audience": blueprint["audience"],
                    "clarified_goal": blueprint["goals"][index],
                    "deliverable": blueprint["deliverable"],
                    "constraints": [
                        "优先使用已有材料与低成本验证",
                        "所有关键假设必须显式标记",
                    ],
                    "non_goals": ["不以生成文档本身作为成功"],
                    "success_evidence": [
                        f"使用者能根据{blueprint['deliverable']}做出下一步选择",
                        "至少一个失败条件可在执行前被识别",
                    ],
                    "assumptions": ["未提供的数据先列为待验证假设"],
                    "highest_priority_constraint": blueprint["constraint"],
                    "domain_checks": blueprint["checks"],
                    "failure_modes": [blueprint["failure"]],
                    "requirements": requirements,
                }
            )
    return scenarios


def load_scenarios(path):
    return json.loads(Path(path).read_text(encoding="utf-8"))


def build_candidate_spec(scenario):
    requirements = []
    for index, requirement in enumerate(scenario["requirements"], start=1):
        requirements.append(
            {
                "id": f"R{index}",
                "requirement": requirement["requirement"],
                "prompt_instruction": requirement["instruction"],
                "acceptance_test": requirement["acceptance"],
                "failure_handling": requirement["failure"],
            }
        )
    taste_contract = None
    if scenario["domain"] == "creative-ideation":
        taste_contract = {
            "desired_effect": "方向差异明确、审美边界稳定、可继续发展",
            "positive_references": [],
            "negative_references": [],
            "pairwise_preferences": [],
            "must_have": ["单一主创意命题", "可比较方向"],
            "must_avoid": ["同质化点子堆积"],
            "flexible_dimensions": ["叙事视角", "媒介形式"],
            "taste_axes": {"novelty": "熟悉与实验之间", "restraint": "克制"},
        }
    return {
        "goal_contract": {
            "surface_request": scenario["raw_request"],
            "real_outcome": scenario["clarified_goal"],
            "audience": scenario["audience"],
            "decision_or_action": "根据交付结果选择下一步行动",
            "deliverable": scenario["deliverable"],
            "available_inputs": [],
            "constraints": scenario["constraints"],
            "non_goals": scenario["non_goals"],
            "success_evidence": scenario["success_evidence"],
            "critical_unknowns": ["真实数据、用户反馈或环境约束"],
            "assumptions": scenario["assumptions"],
        },
        "taste_contract": taste_contract,
        "mode": scenario["mode"],
        "target_runtime": scenario["target_runtime"],
        "highest_priority_constraint": scenario["highest_priority_constraint"],
        "requirements": requirements,
        "failure_modes": scenario["failure_modes"],
        "evidence_and_uncertainty": [
            "区分已知事实、用户提供信息、假设和未知项",
            "无法核实时降低结论强度或提出验证动作",
        ],
        "deliverable": {
            "type": scenario["deliverable"],
            "sections": ["目标", "方案", "证据", "风险", "验收"],
        },
        "final_check": [
            "真实目标没有被交付物替代",
            "每个Requirement均有Acceptance Test",
            "最高优先级约束在冲突时优先",
        ],
    }


def _contains_any(text, patterns):
    return any(re.search(pattern, text, flags=re.IGNORECASE) for pattern in patterns)


def _baseline_general_score(text):
    checks = [
        (2, [r"目标", r"为了", r"让我", r"决定"]),
        (1, [r"用户", r"团队", r"受众", r"读者"]),
        (1, [r"报告", r"方案", r"系统", r"计划", r"框架"]),
        (2, [r"必须", r"优先", r"限制", r"预算", r"时间"]),
        (1, [r"证据", r"数据", r"来源"]),
        (2, [r"验收", r"通过", r"成功标准", r"测试"]),
        (1, [r"失败", r"异常", r"风险"]),
        (1, [r"步骤", r"依赖", r"实现"]),
        (1, [r"模型", r"工具", r"联网", r"权限"]),
    ]
    return sum(weight for weight, patterns in checks if _contains_any(text, patterns))


def _candidate_general_score(spec):
    score = 0
    goal = spec["goal_contract"]
    score += 2 if goal.get("real_outcome") else 0
    score += 1 if goal.get("audience") else 0
    score += 1 if goal.get("deliverable") else 0
    score += 2 if spec.get("highest_priority_constraint") else 0
    score += 1 if spec.get("evidence_and_uncertainty") else 0
    score += 2 if all(item.get("acceptance_test") for item in spec["requirements"]) else 0
    score += 1 if spec.get("failure_modes") else 0
    score += 1 if all(item.get("id") for item in spec["requirements"]) else 0
    score += 1 if spec.get("target_runtime") else 0
    return score


def _domain_coverage(text, checks):
    hits = sum(check.lower() in text.lower() for check in checks)
    return hits / len(checks)


def evaluate_scenario(scenario, spec):
    compiled = compile_prompt(spec)
    baseline = scenario["raw_request"]
    candidate_text = compiled["prompt"]
    baseline_general = _baseline_general_score(baseline)
    candidate_general = _candidate_general_score(spec)
    baseline_domain = _domain_coverage(baseline, scenario["domain_checks"])
    candidate_domain = _domain_coverage(
        json.dumps(spec, ensure_ascii=False) + candidate_text,
        scenario["domain_checks"],
    )
    baseline_efficiency = 1.0
    candidate_efficiency = max(0.0, 1 - max(0, len(candidate_text) - 3500) / 3500)
    baseline_score = round(
        100 * (0.60 * baseline_general / 12 + 0.25 * baseline_domain + 0.15 * baseline_efficiency),
        1,
    )
    candidate_score = round(
        100 * (0.60 * candidate_general / 12 + 0.25 * candidate_domain + 0.15 * candidate_efficiency),
        1,
    )
    requirement_links = compiled["trace"]["requirement_links"]
    traceability_rate = (
        sum(
            bool(item["instruction"] and item["acceptance_test"] and item["failure_handling"])
            for item in requirement_links
        )
        / len(requirement_links)
        if requirement_links
        else 0
    )
    return {
        "id": scenario["id"],
        "domain": scenario["domain"],
        "difficulty": scenario.get("difficulty", "custom"),
        "mode": scenario["mode"],
        "runtime": scenario["target_runtime"],
        "baseline_prompt": baseline,
        "candidate_prompt": candidate_text,
        "baseline_score": baseline_score,
        "candidate_score": candidate_score,
        "delta": round(candidate_score - baseline_score, 1),
        "baseline_general": baseline_general,
        "candidate_general": candidate_general,
        "baseline_domain_coverage": round(baseline_domain, 3),
        "candidate_domain_coverage": round(candidate_domain, 3),
        "baseline_chars": len(baseline),
        "candidate_chars": len(candidate_text),
        "candidate_tokens": compiled["usage"]["estimated_prompt_tokens"],
        "prompt_token_budget": compiled["usage"]["prompt_budget"],
        "within_token_budget": compiled["usage"]["within_budget"],
        "detail_level": compiled["usage"]["detail_level"],
        "traceability_rate": round(traceability_rate, 3),
    }


def build_report(scenarios):
    results = []
    domains = defaultdict(list)
    for scenario in scenarios:
        result = evaluate_scenario(scenario, build_candidate_spec(scenario))
        results.append(result)
        domains[result["domain"]].append(result)
    domain_summary = {}
    for domain, rows in domains.items():
        domain_summary[domain] = {
            "count": len(rows),
            "baseline_mean": round(sum(row["baseline_score"] for row in rows) / len(rows), 1),
            "candidate_mean": round(sum(row["candidate_score"] for row in rows) / len(rows), 1),
            "delta_mean": round(sum(row["delta"] for row in rows) / len(rows), 1),
            "domain_coverage_mean": round(
                sum(row["candidate_domain_coverage"] for row in rows) / len(rows), 3
            ),
        }
    baseline_chars_mean = sum(row["baseline_chars"] for row in results) / len(results)
    candidate_chars_mean = sum(row["candidate_chars"] for row in results) / len(results)
    candidate_tokens_mean = sum(row["candidate_tokens"] for row in results) / len(results)
    return {
        "method": {
            "evidence_level": "deterministic-structural-simulation",
            "independent_model_blind_test": False,
            "limitation": "Claude CLI quota exhausted; output-quality blind judging not executed.",
            "score_interpretation": (
                "Scores measure protocol completeness under a same-source rubric; "
                "they are not end-output quality scores."
            ),
            "score_weights": {
                "general_protocol_quality": 0.60,
                "domain_specific_coverage": 0.25,
                "prompt_efficiency": 0.15,
            },
        },
        "summary": {
            "scenario_count": len(results),
            "domain_count": len(domains),
            "baseline_mean": round(
                sum(row["baseline_score"] for row in results) / len(results), 1
            ),
            "candidate_mean": round(
                sum(row["candidate_score"] for row in results) / len(results), 1
            ),
            "delta_mean": round(sum(row["delta"] for row in results) / len(results), 1),
            "candidate_win_rate": round(
                sum(row["delta"] > 0 for row in results) / len(results), 3
            ),
            "traceability_mean": round(
                sum(row["traceability_rate"] for row in results) / len(results), 3
            ),
            "baseline_chars_mean": round(
                baseline_chars_mean, 1
            ),
            "candidate_chars_mean": round(
                candidate_chars_mean, 1
            ),
            "prompt_expansion_ratio": round(
                candidate_chars_mean / baseline_chars_mean, 1
            ),
            "perfect_score_rate": round(
                sum(row["candidate_score"] == 100 for row in results) / len(results),
                3,
            ),
            "candidate_tokens_mean": round(candidate_tokens_mean, 1),
            "token_budget_pass_rate": round(
                sum(row["within_token_budget"] for row in results) / len(results),
                3,
            ),
        },
        "domains": domain_summary,
        "results": results,
    }


def write_markdown(report, path):
    lines = [
        "# Meta-Prompt v4 多元场景评测",
        "",
        "## 总览",
        "",
        "| 指标 | 结果 |",
        "|---|---:|",
        f"| 场景数 | {report['summary']['scenario_count']} |",
        f"| 领域数 | {report['summary']['domain_count']} |",
        f"| Baseline 均分 | {report['summary']['baseline_mean']} |",
        f"| Candidate 均分 | {report['summary']['candidate_mean']} |",
        f"| 平均提升 | {report['summary']['delta_mean']} |",
        f"| Candidate 胜率 | {report['summary']['candidate_win_rate']:.1%} |",
        f"| 需求追踪率 | {report['summary']['traceability_mean']:.1%} |",
        f"| Prompt 长度膨胀 | {report['summary']['prompt_expansion_ratio']}x |",
        f"| Candidate 满分率 | {report['summary']['perfect_score_rate']:.1%} |",
        f"| Candidate 平均 Token | {report['summary']['candidate_tokens_mean']} |",
        f"| Token 预算通过率 | {report['summary']['token_budget_pass_rate']:.1%} |",
        "",
        "## 分领域",
        "",
        "| 领域 | Baseline | Candidate | 提升 | 领域覆盖 |",
        "|---|---:|---:|---:|---:|",
    ]
    for domain, data in report["domains"].items():
        lines.append(
            f"| {domain} | {data['baseline_mean']} | {data['candidate_mean']} | "
            f"{data['delta_mean']} | {data['domain_coverage_mean']:.1%} |"
        )
    lines.extend(
        [
            "",
            "## 上网调研过程对照",
            "",
            "- 宽泛单查询：决策级一手来源 3/5（60%），明确覆盖数据/metric 2/5（40%）。",
            "- Meta-Prompt 协议：决策级一手来源 7/7（100%），明确覆盖数据/metric 6/7（85.7%）。",
            "- 详细查询、来源和证据边界见 `evals/web-research-process-case.md`。",
            "",
            "## 证据边界",
            "",
            "- 本轮为确定性结构模拟，覆盖目标、约束、证据、验收、失败处理、运行时与领域要素。",
            "- 分数衡量同源规则下的协议完整度，不是模型最终回答质量；满分集中代表量表饱和。",
            "- Prompt 长度膨胀用于暴露过度提示风险，后续应按任务复杂度压缩，而非追求字段越多越好。",
            "- Claude CLI 因额度耗尽未完成独立模型盲评；不能把结构分数直接等同于真实回答质量。",
            "- 完整逐场景数据、Baseline 和 Candidate Prompt 位于 JSON 报告。",
        ]
    )
    Path(path).write_text("\n".join(lines) + "\n", encoding="utf-8")


def main():
    parser = argparse.ArgumentParser(description="Run the Meta-Prompt diverse benchmark.")
    parser.add_argument(
        "--scenarios",
        type=Path,
        default=ROOT / "evals/diverse-scenarios.json",
    )
    parser.add_argument(
        "--report",
        type=Path,
        default=ROOT / "evals/diverse-benchmark-report.json",
    )
    parser.add_argument(
        "--markdown",
        type=Path,
        default=ROOT / "evals/diverse-benchmark-report.md",
    )
    parser.add_argument("--generate", action="store_true")
    args = parser.parse_args()

    if args.generate or not args.scenarios.exists():
        args.scenarios.write_text(
            json.dumps(generate_scenarios(), ensure_ascii=False, indent=2) + "\n",
            encoding="utf-8",
        )
    scenarios = load_scenarios(args.scenarios)
    report = build_report(scenarios)
    args.report.write_text(
        json.dumps(report, ensure_ascii=False, indent=2) + "\n",
        encoding="utf-8",
    )
    write_markdown(report, args.markdown)
    print(json.dumps(report["summary"], ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()
