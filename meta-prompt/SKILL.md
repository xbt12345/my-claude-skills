---
name: meta-prompt
description: Use when the user asks to generate, optimize, rewrite, refine, debug, compare, or evaluate prompts (优化提示词、改写/调试/比较 Prompt、帮我写个 Prompt、提示词工程), or when a complex task has ambiguous goals, subjective taste, hidden constraints, model-specific requirements, or non-obvious failure modes.
---

# Meta-Prompt

把原始表达编译成目标明确、审美可确认、模型可执行、结果可验证且成本受控的任务协议。

核心顺序：

```text
现实目标 → 好坏标准 → 最小充分 Prompt → 验收
```

## 路由

| 模式 | 使用条件 | 默认 Prompt / Output 预算 |
|---|---|---:|
| Express | 单步、低风险、目标明确 | 180 / 500 tokens |
| Guided | 一个关键歧义或审美未知项 | 350 / 900 |
| Harness | 高风险、多阶段、工具或回归验证 | 700 / 1600 |

默认选择最低充分模式。不能因为任务“看起来专业”升级。

Guided 每轮只问一个会改变结果的最高信息增益问题。能安全推断时，显式列假设并继续。

日常任务由全局轻量门卫自动选择路由，无需用户说出 Meta-Prompt 或自然语言触发词。Express 不加载详细 references；Guided/Harness 才加载必要模块。

涉及 Token、额度、长上下文或成本优化时，读取 `references/token-economy.md`。

维护、扩展或全面理解本 Skill 时读取 `references/architecture.md`；日常优化 Prompt 不加载该文件。

## 工作流

```text
Route → Goal → Taste? → Diagnose → Compile → Budget Gate → Evaluate
```

### 显式优化请求

用户明确指定使用本 Skill 优化提示词时：

1. 始终先交付优化后的 Prompt。
2. 只根据用户原始消息判定执行意图，不根据优化后 Prompt 的动作内容反推：
   - `optimize_only`：明确说“只优化”“不要执行”；交付后停止。
   - `optimize_and_execute`：明确说“优化并执行”“优化后直接做”；交付后直接继续执行。
   - `ask_after_optimization`：未说明是否执行；交付后询问是否执行。
3. 日常自动路由记为 `implicit_task`，保持原任务语义，不额外展示 Prompt 或询问执行。
4. 🛑 STOP：安全审批、不可逆操作确认和平台权限始终优先，任何执行意图都不能跳过。

### Goal

Guided/Harness 读取 `references/goal-elicitation.md`，确认：

- 真实结果、受众与交付物
- 不可改变约束、非目标
- 可观察成功证据
- 假设与关键未知项

复杂任务使用 `schemas/goal-contract.yaml`。

🔴 CHECKPOINT：Harness 在执行或生成高成本最终产物前，先向用户确认 Goal Contract。

### Taste

写作、视觉、品牌、产品体验或创意任务读取
`references/taste-elicitation.md`。

优先分析用户正反样本；没有样本时提供 2–3 个差异方向，用 A/B 理由提取可观察审美轴。

🔴 CHECKPOINT：审美方向未确认前，不生成高成本最终产物。

### Diagnose

Express 快速扫描；Guided/Harness 读取 `references/diagnosis.md`：

- 行家真正使用的判断信号
- 常见但不可用的失败产物
- 目标、前提、评价或隐藏约束错位
- 唯一最高优先级约束

禁止用虚构履历、机构、年限或名人替代判断规则。

任务属于 AI 分析、学习复习、内容写作、投资决策、项目/系统规划等领域，且需要成熟结构时，按需读取 `references/domain-patterns.md`。只选一个主模式，不整库复制。

### Compile

读取 `references/compiler.md`。每个核心需求形成：

```text
Requirement → Instruction → Acceptance Test → Failure Handling
```

只把当前模型执行需要的信息放入 Prompt；完整追踪信息可保存在 trace，避免重复传输。

目标运行时明确时读取 `references/model-adapters.md`。声明工具、权限、输出格式、成本预算与人工确认点。

编译器：`scripts/compile_prompt.py`。

### Budget Gate

- 删除空字段、重复背景、角色包装和不改变行为的说明。
- Express 只保留目标、最高约束、动作、输出。
- Harness 使用紧凑 Requirement/Test/Fail 矩阵。
- 超预算时按 detail level 降级，禁止盲目截断。
- 固定规则放稳定前缀，动态材料放后部，提高缓存命中。

### Evaluate

读取 `references/evaluation.md`，检查：

- 目标和用户原意未改变
- Requirement 有对应验收
- 失败可观察
- Candidate 优于 baseline
- Holdout 未退化
- Token 预算通过

生成者自评不能作为独立质量证据。

## 失败分支

| 触发 | 一线处理 | 仍不行时 |
|---|---|---|
| 原 Prompt 已最小充分 | 直接说明无需优化，最多指出 1–2 处微调 | 用户坚持时按 Guided 重新梳理目标 |
| 关键问题未获回答 | 列显式假设并继续，写入交付的「关键假设」 | 方向分叉时给 2 个分支版本供用户选择 |
| 约束冲突且无优先级 | 指出冲突，给唯一最高约束建议并附理由 | 未获确认时按保守取舍执行并显式标注 |
| 脚本不可用或报错 | 跳过记录与脚本验证，按规则手动执行，不阻塞交付 | 在答复末尾注明「未记录」 |
| reference 文件缺失 | 按本文件内嵌规则降级执行 | 提示运行 `python scripts/validate_skill.py` |
| 目标运行时未知 | 按通用对话或 coding-agent 适配并显式声明 | 不静默套用特定运行时语法 |

## 输出

默认只交付：

```markdown
**需求确认**
- 真实目标：
- 关键假设：
- 最高优先级约束：

**优化后 Prompt**
```text
[可直接使用]
```

**验证**
- [关键验收]
```

用户只要 Prompt 时，仅输出 Prompt。审美方向仅在适用时出现。

## 命令

日常：

- `/meta-prompt compare`：比较 baseline/candidate。
- `/meta-prompt stats`：汇总运行 trace。
- `/meta-prompt validate`：基础验证。

维护（仅反馈记录与每周反思时使用，完整脚本清单见 `references/architecture.md`）：

- `python scripts/run_feedback.py start` / `finish <run_id>`：运行记录起止。
- `python scripts/weekly_reflect.py`：七日数据门槛报告。
- `python scripts/blind_eval.py`：盲评包准备与决策门槛。
- `python scripts/token_audit.py`：Token 与 API 等价成本审计。

## 低成本反馈

- 仅记录显式优化、Guided/Harness 或失败运行；普通 Express 成功任务不记录。
- 符合范围时，优化前运行 `run_feedback.py start`，保存返回的 `run_id`；最终答复前运行
  `run_feedback.py finish <run_id>`。失败 Express 可通过兼容入口直接写终态。
- 🛑 记录脚本一律用 stdin 传 JSON，不用 `--data`：Windows 控制台经 argv 传中文会丢成 `?`。
  例：`'{"mode":"Guided","goal_summary":"中文摘要"}' | python scripts/run_feedback.py start`。
- 默认只写模式、脱敏目标摘要、Prompt 指纹、执行状态、反馈、失败类别和 Token 字段，不保存原始敏感 Prompt。
- 每周先运行确定性聚合；少于 5 次有效运行不优化。同类失败至少 3 次才进入改动评审。
- `blind_eval_required=false` 时只报告，不加载完整架构、不跑模型盲评、不修改 Skill。
- 达到门槛时最多选择 3 个 holdout。评审与生成模型不同为优先；非独立自评不得触发修改。

## 红线

- 不生成 mega-prompt 来制造完整感。
- 不用抽象质量词代替验收。
- 不捏造准确率、置信度或成本。
- 不用 Prompt 补偿缺失的数据、权限或现实反馈。
- 不把订阅额度与 API Token 美元成本混算。
- 不展示隐藏推理。

事实、分析、代码或建议结尾：

```text
⚡ 验证点：[最脆弱判断] → [最低成本核实方法]
```

<!-- v4.5 · 2026-06-14 · Feedback stdin Encoding Fix + Mojibake Guard -->
