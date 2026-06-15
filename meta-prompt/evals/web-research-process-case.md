# Web Research Process Case · 2026-06-12

## 任务

比较 Prompt 优化方案，判断 Meta-Prompt Skill 下一步应采用哪些机制。

## Baseline：宽泛搜索

- 查询：`best prompt optimization tools compare prompt optimizer projects`
- 过程：单次查询，直接读取前 5 个结果。
- 前 5 结果类型：社区讨论、OpenAI 官方文档、单一工具官网、LangChain 原创实验、厂商横向榜单。
- 可直接支撑决策的一手来源：3/5（60%）。
- 明确覆盖“成功标准 + 数据集/样本 + grader/metric”的来源：2/5（40%）。
- 局限：来源角色混杂；产品自述、社区经验、原创实验和第三方榜单没有分层。

## Candidate：Meta-Prompt 研究协议

目标先改写为：比较“人工澄清、评测驱动优化、自动搜索、可移植性”四类机制，输出采用条件、限制和验证方案。

查询拆分：

1. 官方 Prompt Optimizer 的数据、grader、人工复核要求。
2. 官方成功标准与 eval 设计。
3. DSPy 优化器的输入、metric 和可移植性限制。
4. Promptfoo assertion 能覆盖哪些自动验收。

选取来源：

- OpenAI Prompt Optimizer
- OpenAI Model Optimization
- Anthropic Prompt Engineering Overview
- Anthropic Define Success Criteria and Build Evaluations
- DSPy Optimizers 文档
- Promptfoo Assertions & Metrics 文档
- DSPy 导出优化 Prompt 的公开 issue，作为限制证据

结果：

- 决策级一手来源：7/7（100%）。
- 明确覆盖成功标准、数据或 metric：6/7（85.7%）。
- 主动包含限制/反证：3 类。
- 发现时效变化：OpenAI 文档显示 dataset-backed Prompt Optimizer 将于 2026-10-31 只读、2026-11-30 关闭。

## 对输出质量的影响

- 从“列工具”转为“按机制和采用条件比较”。
- 能区分：Prompt 写得更完整、在代表性数据上更好、对目标模型有效，是三个不同命题。
- 结论必须保留 holdout、人工复核、失败样本和 Prompt 长度成本。
- 本案例只验证研究过程与证据质量，不替代目标模型输出盲评。

## 来源

- https://developers.openai.com/api/docs/guides/prompt-optimizer
- https://developers.openai.com/api/docs/guides/model-optimization
- https://docs.anthropic.com/en/docs/build-with-claude/prompt-engineering/overview
- https://docs.anthropic.com/en/docs/build-with-claude/develop-tests
- https://github.com/stanfordnlp/dspy/blob/main/docs/docs/learn/optimization/optimizers.md
- https://github.com/promptfoo/promptfoo/blob/main/site/docs/configuration/expected-outputs/index.md
- https://github.com/stanfordnlp/dspy/issues/8043
