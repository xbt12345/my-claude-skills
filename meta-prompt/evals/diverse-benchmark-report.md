# Meta-Prompt v4 多元场景评测

## 总览

| 指标 | 结果 |
|---|---:|
| 场景数 | 33 |
| 领域数 | 11 |
| Baseline 均分 | 18.5 |
| Candidate 均分 | 100.0 |
| 平均提升 | 81.5 |
| Candidate 胜率 | 100.0% |
| 需求追踪率 | 100.0% |
| Prompt 长度膨胀 | 43.3x |
| Candidate 满分率 | 100.0% |
| Candidate 平均 Token | 410.1 |
| Token 预算通过率 | 100.0% |

## 分领域

| 领域 | Baseline | Candidate | 提升 | 领域覆盖 |
|---|---:|---:|---:|---:|
| product-design | 18.3 | 100.0 | 81.7 | 100.0% |
| framework-building | 21.7 | 100.0 | 78.3 | 100.0% |
| knowledge-review | 23.7 | 100.0 | 76.3 | 100.0% |
| system-architecture | 20.0 | 100.0 | 80.0 | 100.0% |
| requirements-implementation | 21.7 | 100.0 | 78.3 | 100.0% |
| skill-authoring | 15.0 | 100.0 | 85.0 | 100.0% |
| automation | 16.7 | 100.0 | 83.3 | 100.0% |
| knowledge-base | 18.3 | 100.0 | 81.7 | 100.0% |
| web-research | 16.7 | 100.0 | 83.3 | 100.0% |
| creative-ideation | 15.0 | 100.0 | 85.0 | 100.0% |
| optimization-roadmap | 16.7 | 100.0 | 83.3 | 100.0% |

## 上网调研过程对照

- 宽泛单查询：决策级一手来源 3/5（60%），明确覆盖数据/metric 2/5（40%）。
- Meta-Prompt 协议：决策级一手来源 7/7（100%），明确覆盖数据/metric 6/7（85.7%）。
- 详细查询、来源和证据边界见 `evals/web-research-process-case.md`。

## 证据边界

- 本轮为确定性结构模拟，覆盖目标、约束、证据、验收、失败处理、运行时与领域要素。
- 分数衡量同源规则下的协议完整度，不是模型最终回答质量；满分集中代表量表饱和。
- Prompt 长度膨胀用于暴露过度提示风险，后续应按任务复杂度压缩，而非追求字段越多越好。
- Claude CLI 因额度耗尽未完成独立模型盲评；不能把结构分数直接等同于真实回答质量。
- 完整逐场景数据、Baseline 和 Candidate Prompt 位于 JSON 报告。
