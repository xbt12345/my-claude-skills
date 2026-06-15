# Evaluation Harness

## 评估顺序

1. **结构断言**：必需字段、格式、长度、禁用模式。
2. **需求覆盖**：每个 Requirement 是否映射 Prompt 指令与 Acceptance Test。
3. **目标评估**：完成交付物后是否推动真实结果。
4. **Pairwise**：candidate 是否比 baseline 更明确、更短或更可验证。
5. **Taste 评估**：主观任务由用户或授权评审者在盲测中选择。
6. **Holdout**：未参与优化的案例是否退化。
7. **Trace 评估**：工具、权限、成本、停止条件和人工确认点是否正确。
8. **成本评估**：Prompt/Output 是否在预算内；是否因压缩增加追问、重试或返工。

## 评分边界

- 确定性规则适合 Schema、字段、禁词和权限。
- LLM judge 适合目标对齐、证据边界和可执行性，但必须用人工样本校准。
- 用户 Taste 不转换成伪精确百分比。
- 单次生成者自评不能作为通过证据。

## 真实盲评门槛

- 仅当七日真实记录中同类失败至少 3 次，且有效运行至少 5 次时启动。
- 使用 `evals/blind-holdout.json` 中未参与规则调优的案例；单周最多 3 个。
- 基线与候选随机映射为 A/B。评审输入不得包含版本身份、改动说明或预期答案。
- 优先使用不同模型评审，记为 `model_independent`；同模型全新隔离上下文记为
  `context_independent`；非隔离自评记为 `not_independent`，不得支持自动修改。
- 候选须获得有效样本过半胜出、无关键约束退化，且 Token 均值增幅不超过 10%。
- `scripts/blind_eval.py` 只准备和评分盲评文件，不自行调用模型或消耗订阅额度。

## 最小 Eval Case

```yaml
id: 唯一标识
category: express | ambiguity | taste | risk | prompt-bloat | goal-misalignment
input: 用户原始请求
expected_mode: Express | Guided | Harness
needs_taste: true | false
assertions:
  - 可观察行为
```

## 回归门槛

- Express 不得追问或生成 mega-prompt。
- Guided 每轮只问一个最高信息增益问题。
- Taste 未确认时只生成低成本候选，不生成高成本最终产物。
- Harness 必须有 Requirement → Prompt → Test 映射。
- Candidate 不得偷偷改变 Goal Contract。
- 新版本必须通过全部 P0 案例，并且 holdout 不出现新 P0 失败。
- Token 优化必须同时报告长度降幅、领域覆盖、追踪率和预算通过率。

## 停止条件

- 达到验收门槛。
- 连续两轮没有改善。
- 达到成本或轮次预算。
- 需要现实数据、专业资质或用户审美判断。
