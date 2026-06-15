# Meta-Prompt Skill 完整说明

> 面向后续维护、优化与评测。日常使用不必读取本文件；执行规则以 `SKILL.md` 为准，结构化契约以 `schemas/` 为准，当前测量以测试与 `evals/` 生成报告为准。

## 1. Skill 是什么

Meta-Prompt 是一个提示词编译与验证 Skill。它不把用户原话机械扩写成更长的 Prompt，而是先识别现实目标、成功证据、审美方向和失败边界，再生成目标模型更容易执行、结果可以验收、Token 成本受控的任务协议。

核心公式：

```text
原始表达
→ 现实目标
→ 好坏标准
→ 最小充分 Prompt
→ 验收与失败处理
```

它解决的不是“怎样写得像提示词”，而是以下工程问题：

- 用户说的是手段，真实需要的是结果。
- 目标、约束、审美和输出格式相互冲突。
- Prompt 看似完整，但没有可观察的成功标准。
- 模型不知道工具、权限、运行时或人工确认边界。
- 任务失败后只能重来，无法定位失败变量。
- 为追求完整感生成 mega-prompt，导致 Token、延迟和注意力浪费。

## 2. 功能范围

### 主要功能

1. 生成、优化、重写或调试 Prompt。
2. 从模糊需求中梳理真实目标、受众、交付物与完成证据。
3. 在写作、视觉、品牌、产品和创意任务中确认审美方向。
4. 识别隐藏约束、失败模式、错误前提和最高优先级冲突。
5. 针对 ChatGPT、Claude、Codex、通用 Coding Agent 和图像模型适配 Prompt。
6. 把需求编译成 `Requirement → Instruction → Acceptance Test → Failure Handling`。
7. 比较 baseline 与 candidate Prompt。
8. 用回归集、多元场景基准和 Token 审计验证优化效果。
9. 记录运行 trace，区分估算 Token、实际 Token、缓存、工具结果、追问和重试。

### 不负责

- 不替代缺失的数据、权限、浏览、真实用户反馈或专业责任。
- 不保证最终模型一定正确。
- 不把订阅额度换算成虚构 API 成本。
- 不以角色包装、虚构履历或名人名称代替判断规则。
- 用户明确要求使用 Meta-Prompt 时先交付优化后的 Prompt，再按执行意图决定继续或询问。
- 不存放具体项目的目标、审美、场景历史和一次性案例。

## 3. 使用方法

### 自然语言触发

常见请求：

```text
帮我优化这个提示词……
把这段需求改成 Codex 能直接执行的 Prompt
这个 Prompt 为什么效果不稳定
比较这两个 Prompt
先帮我梳理目标和审美，再生成最终提示词
把这个复杂任务做成可验收的 Harness Prompt
减少 Prompt Token，但不能降低效果
```

日常对话无需说出这些触发词。全局轻量门卫先按复杂度选择 Express、Guided 或 Harness；简单任务不会为了“使用 Skill”额外展开说明。

### 命令入口

```text
/meta-prompt compare   比较 baseline 与 candidate
/meta-prompt stats     汇总 feedback/runs.jsonl
/meta-prompt validate  执行基础结构验证
```

脚本入口：

```powershell
python scripts/compile_prompt.py --help
python scripts/compare_prompts.py --help
python scripts/stats.py --help
python scripts/run_diverse_benchmark.py --help
python scripts/token_audit.py --help
python scripts/validate_skill.py
```

### 默认交付

```markdown
**需求确认**
- 真实目标
- 关键假设
- 最高优先级约束

**优化后 Prompt**
[可直接使用]

**验证**
- 可观察验收条件
```

用户明确只要 Prompt 时，只返回 Prompt。

## 4. 三种路由模式

| 模式 | 适用任务 | 默认 Prompt 预算 | 默认输出预算 |
|---|---|---:|---:|
| Express | 单步、低风险、目标明确 | 180 tokens | 500 tokens |
| Guided | 存在一个关键歧义或审美未知项 | 350 | 900 |
| Harness | 高风险、多阶段、涉及工具、状态或回归验证 | 700 | 1600 |

### Express

只保留目标、最高约束、动作和输出。适用于格式优化、明确的小任务和低失败成本场景。

### Guided

每轮只询问一个会实质改变结果的最高信息增益问题。能够安全推断时列出假设并继续，避免把需求梳理变成问卷。

### Harness

用于工程任务、复杂调研、系统设计、自动化和高风险决策。保留需求追踪、工具边界、检查点、失败处理与回归验证。

路由原则：默认选择“最低充分模式”，任务显得专业不是升级理由。

### 显式优化后的执行协议

用户明确指定使用 Meta-Prompt 时：

1. 先输出优化后的 Prompt。
2. 用户明确要求只优化或不要执行时停止。
3. Prompt 含有明确可执行任务时，输出后直接执行。
4. Prompt 只是模板、规范或执行对象不明确时，询问用户是否执行。
5. 不可逆操作、安全审批和平台权限始终优先。

## 5. 完整工作流

```text
Route
→ Goal
→ Taste（适用时）
→ Diagnose
→ Compile
→ Budget Gate
→ Evaluate
```

### Route

根据歧义、风险、阶段数、工具依赖和失败成本选择模式。

### Goal

把表面请求转化为 Goal Contract：

- 用户真正要改变的现实状态。
- 受众和交付物。
- 不可改变的约束和非目标。
- 可观察的成功证据。
- 当前假设和关键未知项。

复杂任务使用 `schemas/goal-contract.yaml`。

### Taste

适用于写作、视觉、品牌、产品体验和创意任务。

优先级：

1. 用户明确的正反样本。
2. 对样本做两两偏好比较。
3. 提取可观察审美轴，如密度、留白、色温、节奏、材质、态度和信息层级。
4. 没有样本时给 2-3 个差异方向。
5. 审美方向未确认前，不生成高成本最终产物。

复杂审美任务使用 `schemas/taste-contract.yaml`。

### Diagnose

诊断四类错位：

- 目标错位：用户要求的动作并不能产生真实结果。
- 前提错位：缺少数据、权限、材料或可行条件。
- 评价错位：使用“高级、专业、震撼”等不可验收词。
- 约束错位：多个要求冲突但没有优先级。

输出应找到唯一最高优先级约束，并把失败模式写成可观察结果。

### Compile

每个核心需求编译为：

```text
Requirement
→ Instruction
→ Acceptance Test
→ Failure Handling
```

执行 Prompt 只放当前模型必须知道的信息；完整追踪保存在 trace，避免每轮重复传输。

### Budget Gate

依次删除：

1. 空字段。
2. 重复背景。
3. 不改变行为的角色包装。
4. 已由运行时或系统指令提供的规则。
5. 不能被执行或验收的形容词。
6. 对当前任务无关的参考材料。

超预算时按 detail level 降级，不做字符硬截断。

### Evaluate

检查：

- 目标未漂移。
- 每个核心需求都有对应验收。
- 失败可以观察和定位。
- Candidate 明确优于 baseline。
- Holdout 场景没有退化。
- Prompt 和输出预算通过。

生成者自评不构成独立质量证据。

## 6. Harness 架构

Meta-Prompt 的 Harness 由五层组成：

```text
Guides       SKILL.md + references/
Contracts    schemas/
Execution    scripts/
Verification tests/ + evals/
Feedback     feedback/runs.jsonl
```

### Guides

定义如何判断和执行。采用渐进加载：`SKILL.md` 常驻为路由器，细节按需读取。

### Contracts

把自然语言要求变成机器可验证的数据结构：

- `goal-contract.yaml`：目标、受众、交付物、成功证据和假设。
- `taste-contract.yaml`：正反样本、两两偏好和审美轴。
- `prompt-spec.yaml`：编译器输入。
- `eval-case.yaml`：评测案例。
- `run-trace.yaml`：运行成本和质量追踪。

这些 `.yaml` 当前使用 JSON 兼容语法，便于 Python 标准库直接解析。

### Execution

编译、比较、统计、基准和 Token 审计由确定性脚本执行。脚本减少模型临时重写逻辑造成的漂移。

### Verification

分三层：

1. 结构测试：文件、字段、路由和安全约束。
2. 回归测试：固定案例防止旧能力退化。
3. 多元基准：33 个场景覆盖 11 个领域。

### Feedback

真实运行数据写入 `feedback/runs.jsonl`。仅记录显式优化、Guided/Harness 或失败运行；普通 Express 成功任务跳过。默认不保存原始 Prompt，只保存目标摘要、模式标签、执行状态、反馈、失败类别和 Token 字段。

每周反思先运行确定性脚本：

```text
最近 7 天真实记录
→ 少于 5 次：insufficient-data，不修改
→ 同类失败少于 3 次：stable，不修改
→ 同类失败达到 3 次：review-required
→ 增加失败测试
→ 最小改动
→ 回归 + 基准 + Token 审计
```

该门槛避免自动化根据偶发案例改坏全局规则。

## 7. 文件职责

### 根目录

| 文件 | 职责 |
|---|---|
| `SKILL.md` | 触发、路由、核心流程、输出和红线 |

根目录不保留 Sprint、Review、README、项目案例或临时说明。

### references/

| 文件 | 何时读取 |
|---|---|
| `architecture.md` | 维护、调试、扩展或全面了解 Skill |
| `domain-patterns.md` | AI、学习、写作、投资、项目等领域需要成熟模式 |
| `goal-elicitation.md` | Guided/Harness 目标不完整 |
| `taste-elicitation.md` | 存在主观审美或体验判断 |
| `diagnosis.md` | 需要识别错位、失败模式和最高约束 |
| `compiler.md` | 编译复杂 Prompt |
| `evaluation.md` | 比较、回归和质量验收 |
| `model-adapters.md` | 已知目标运行时 |
| `token-economy.md` | Token、额度、缓存或成本优化 |

### schemas/

Schemas 是字段级单一真源。修改字段时同步更新编译器和测试。

### scripts/

| 脚本 | 职责 |
|---|---|
| `compile_prompt.py` | 将 Prompt Spec 编译为不同运行时 Prompt |
| `compare_prompts.py` | 比较 baseline/candidate 的结构覆盖 |
| `run_diverse_benchmark.py` | 运行 33 场景确定性结构基准 |
| `token_audit.py` | 统计静态上下文、Prompt Token 与预算 |
| `stats.py` | 汇总真实运行 trace |
| `log_run.py` | 追加经过裁剪的真实运行记录 |
| `weekly_reflect.py` | 无模型聚合七日数据并决定是否允许评审 |
| `validate_skill.py` | 检查目录、Schema、回归集和禁用模式 |

### tests/

| 测试 | 覆盖 |
|---|---|
| `test_structure.py` | 目录、引用、Schema 字段、渐进加载 |
| `test_harness.py` | 编译器、适配器、预算、trace 和评估 |
| `test_diverse_benchmark.py` | 场景覆盖、领域检查和报告生成 |

### evals/

| 文件类型 | 说明 |
|---|---|
| `regression.json` | 最小回归案例集 |
| `diverse-scenarios.json` | 33 个跨领域场景 |
| `*-report.json` | 机器可读生成报告 |
| `*-report.md` | 人类可读摘要 |
| `token-economy-research.md` | Token 机制研究与依据 |
| `web-research-process-case.md` | 上网调研过程对照案例 |

报告是可再生产物；场景集和研究文档是输入证据。

## 8. 模型适配

适配器目前覆盖：

- ChatGPT
- Claude
- Codex
- 通用 Coding Agent
- 图像模型

适配时主要改变：

- 工具与权限声明。
- 文件读写和执行边界。
- 输出格式。
- 检查点与人工确认点。
- 最大输出预算。
- 图像任务中的审美合同和视觉失败模式。

不会改变真实目标和验收标准。

## 9. 领域模式

`references/domain-patterns.md` 合并了原五个模板目录，并增加了通用项目整理经验。

支持：

- AI 与技术分析。
- 认知学习、长文消化和备考复习。
- 内容写作、标题与开头。
- 投资机会与多空决策。
- 项目、系统、自动化、知识库和 Skill 规划。

领域模式只提供判断模块，不能直接整份复制。每次必须重新确认 Goal、约束、证据日期和验收。

## 10. 已测优化效果

当前多元基准覆盖 33 个场景、11 个领域：

- 产品设计。
- 框架搭建。
- 知识复习。
- 系统架构。
- 需求分析与实现。
- Skill 编写。
- 自动化。
- 知识库。
- 上网调研。
- 创意启发。
- 优化路线。

最近一次确定性结构评测结果：

| 指标 | 结果 |
|---|---:|
| Baseline 均分 | 18.5 |
| Candidate 均分 | 100.0 |
| 平均结构提升 | 81.5 |
| Candidate 胜率 | 100% |
| 需求追踪率 | 100% |
| Token 预算通过率 | 100% |
| Candidate 平均 Prompt Token | 410.1 |

解释边界：

- 分数衡量同一规则下的结构完整度，不等于模型最终回答质量。
- Candidate 满分说明当前量表已饱和，不能据此声称真实任务成功率为 100%。
- 独立模型盲评曾因额度限制未完成。
- 后续最有价值的提升不是继续刷结构满分，而是真实任务盲评、失败率、重试次数和单位成功成本。

上网调研结构对照：

| 指标 | 宽泛单查询 | Meta-Prompt 协议 |
|---|---:|---:|
| 决策级一手来源覆盖 | 60% | 100% |
| 明确数据/metric 覆盖 | 40% | 85.7% |

该结果来自固定案例，不代表所有互联网调研任务。

## 11. Token 与资源消耗

### 当前可测数据

2026-06-12 目录整理后的审计：

| 项目 | 数值 |
|---|---:|
| `SKILL.md` 入口 | 1,451 tokens |
| `architecture.md`（仅维护时加载） | 5,007 tokens |
| `domain-patterns.md`（仅对应领域加载） | 2,087 tokens |
| 全部 references + schemas 理论全加载 | 约 13,700 tokens |
| 33 个编译 Prompt 平均 | 410.1 tokens |
| 中位数 | 477 |
| 范围 | 256-519 |
| Guided 平均 | 294.5 / 350 预算 |
| Harness 平均 | 467.9 / 700 预算 |
| 预算通过率 | 100% |
| 相对上一版 Prompt 均值 | 558.3 → 410.1，下降 26.5% |

相对整理前：

- 入口从最初 1,082 增至 1,451 tokens，增加 369 tokens；新增部分包含自动路由解释、显式执行协议和低成本反馈规则。
- 理论全加载约 13,700 tokens，主要来自维护说明和领域模式库。
- 该全加载数字不是正常运行成本。日常优化 Prompt 不读取 `architecture.md`；只有对应领域需要成熟结构时才读取 `domain-patterns.md`。
- 33 个实际编译 Prompt 均值仍为 410.1 tokens，说明目录说明文档没有进入执行 Prompt。
- 全局自动路由门卫相对改动前增加约 154 tokens/会话；它替代每次手动触发判断，详细规则仍按需加载。

### 成本组成

```text
总资源消耗 =
输入 Token
+ 输出 Token
+ 工具结果
+ 追问轮次
+ 重试与返工
+ 评测和维护成本
```

只减少输入 Prompt、却增加失败和重试，是伪优化。

### 低成本机制

1. Express / Guided / Harness 分级，不对简单任务全量展开。
2. 主入口只做路由，references 按需加载。
3. 空字段不渲染。
4. 完整 trace 与执行 Prompt 分离。
5. Harness 使用紧凑 Requirement/Test/Fail 矩阵。
6. 固定规则置于稳定前缀，动态材料后置，提高缓存机会。
7. 超预算时降低 detail level，而不是截断语义。
8. 只有长上下文达到数千 Token 后才考虑额外压缩模型。

### 不能准确测量的部分

- Codex 或 Claude 订阅额度不是 API Token 美元成本。
- 历史会话日志包含系统上下文、其他 Skills、工具结果和缓存，无法隔离 Meta-Prompt 的净消耗。
- 没有每次运行的 actual input/output/cached token 字段时，只能做估算。

要得到真实单位成功成本，应持续记录：

```text
actual_input_tokens
cached_input_tokens
actual_output_tokens
tool_result_tokens
question_count
retry_count
success
```

记录策略本身也受预算控制：成功 Express 不写日志；周任务先运行本地 Python 聚合，只有重复失败达到门槛才调用模型分析和测试。

## 12. 如何修改

### 修改触发条件

改 `SKILL.md` frontmatter 的 `description`，然后测试相邻任务是否误触发或漏触发。描述只写“何时使用”，不要概述完整流程。

### 修改核心行为

改 `SKILL.md`。保持它是紧凑路由器，不把详细研究和示例塞回入口。

### 修改目标梳理

改：

- `references/goal-elicitation.md`
- `schemas/goal-contract.yaml`
- 对应测试

### 修改审美机制

改：

- `references/taste-elicitation.md`
- `schemas/taste-contract.yaml`
- 图像适配测试

### 修改编译格式

改：

- `references/compiler.md`
- `schemas/prompt-spec.yaml`
- `scripts/compile_prompt.py`
- `tests/test_harness.py`

### 修改模型适配

改 `references/model-adapters.md` 与 `compile_prompt.py`，为新运行时增加测试；未知运行时必须明确拒绝或降级，不能静默套用。

### 修改领域模板

只改 `references/domain-patterns.md`。具体项目模板放项目知识库，不放回 Skill。

### 修改 Token 预算

改预算常量、`references/token-economy.md` 和测试。必须同时运行多元基准与 Token 审计，不能只看单个例子。

### 增加评测场景

改 `evals/diverse-scenarios.json`，保证：

- 有明确领域。
- 有隐藏检查。
- 不把 intended answer 泄露给 candidate。
- baseline 与 candidate 使用相同评分规则。
- 必要时保留 holdout，不让规则专门拟合公开案例。

## 13. 优化流程

推荐循环：

```text
收集真实失败
→ 建立最小失败测试
→ 运行并确认 RED
→ 修改最小规则或脚本
→ 回归测试 GREEN
→ 运行 33 场景基准
→ 运行 Token 审计
→ 检查真实任务的重试和成功成本
→ 记录结论
```

优化优先级：

1. 目标漂移和错误执行。
2. 缺少验收或失败处理。
3. 高风险任务缺少工具、权限或人工确认边界。
4. 简单任务过度追问或 Prompt 膨胀。
5. 领域覆盖和模型适配。
6. 文案与格式美化。

避免：

- 根据一个成功案例增加全局规则。
- 为了降低静态 Token 删除关键失败处理。
- 使用公开测试集反复调参后声称泛化提升。
- 把生成者自评当独立验证。
- 在 Skill 中保存具体项目和历史流水。

## 14. 测试与验收

标准命令：

```powershell
python -m unittest discover -s tests -v
python scripts/validate_skill.py
python scripts/run_diverse_benchmark.py
python scripts/token_audit.py
python scripts/weekly_reflect.py
```

结构验收：

- `SKILL.md` 不超过 220 行。
- 必要 references、schemas、scripts、tests 和 evals 存在。
- 没有 `templates/`、`archive/`、Sprint、Review 或项目专属文件。
- 没有 `__pycache__`、空文件和重复文件。
- Schema 可由 JSON parser 解析。
- 回归集不少于 20 个唯一案例。
- 领域模式包含触发和不适用边界，不含虚构权威。

行为验收：

- 目标和约束被保留。
- 支持五种运行时。
- Prompt 预算通过。
- 空字段不会渲染。
- 图像任务使用 Taste，不使用假角色。
- 多元场景隐藏检查全部覆盖。

## 15. 当前限制与后续路线

### 当前限制

1. 结构评分量表已经饱和。
2. 独立模型盲评不足。
3. 真实 per-run Token 和成功率数据很少。
4. Express 场景在当前 33 场景集中覆盖不足。
5. 生成报告属于确定性模拟，不等于真实用户满意度。

### 推荐路线

1. 建立 10-20 个真实匿名任务 holdout。
2. 使用不同模型进行盲评，隐藏 candidate 来源。
3. 记录成功、重试、追问和实际 Token。
4. 把指标从“结构满分”升级为“单位成功成本”。
5. 增加 Express 场景，检查简单任务是否被过度工程化。
6. 对常见失败做最小规则修复，避免继续扩大入口。

## 16. 版本与同步

- 规范路径：`<agents-home>\skills\meta-prompt`
- Claude Code 路径：`~/.claude-home\skills\meta-prompt`
- `.claude\skills` 当前通过 Junction 指向 `.agents\skills`。

因此两端看到的是同一份 Skill。不要在 Junction 两侧分别维护副本。

结构调整前应备份整个目录；删除和合并后同时验证两条路径。

## 17. 每周自动反思

计划时间：每周一 09:00，使用本地工作区执行。

低成本执行顺序：

1. 运行 `weekly_reflect.py`，只读取最近七天带有效路由模式的真实记录。
2. `insufficient-data` 或 `stable`：输出简短报告，不读取完整架构，不修改文件，不运行外部调研。
3. `review-required`：只读取重复失败类别对应记录和最相关规则文件。
4. 修改前备份；先写失败测试并确认 RED。
5. 做最小改动，运行单元测试、33 场景基准和 Token 审计。
6. 任一 P0 回归、预算通过率低于 100%，或 Prompt 均值明显恶化时放弃修改并恢复。

自动化不能根据成功次数或单个负面反馈直接重写 Skill。
