# Meta-Prompt Token Economy Research · 2026-06-12

## 结论

高质量与低 Token 不是靠统一压缩比例兼得，而是靠分层：

```text
低风险任务少加载、少追问、短协议
高风险任务保留验收与失败处理
完整状态进入 trace，不重复进入执行 Prompt
```

总成本应按成功任务计算：

```text
输入 + 输出 + 工具结果 + 追问 + 重试/返工
```

只压缩输入、但增加失败和重试，属于伪优化。

## 已采用机制

1. Progressive Disclosure：主入口只负责路由，references 按需加载。
2. Express / Guided / Harness 独立 Prompt 与 Output 预算。
3. 空字段不渲染。
4. Harness 使用紧凑 Requirement/Test/Fail 矩阵。
5. 完整 trace 与执行 Prompt 分离。
6. 超预算按 detail level 降级，不截断语义。
7. 输出预算显式进入 runtime。
8. telemetry 区分 estimated、actual、cached、output、tool、questions、retries。
9. 固定前缀优先，动态内容后置，提升缓存机会。
10. 长上下文先检索/过滤；只有数千 Token 以上再考虑模型压缩。

## 依据

- OpenAI Prompt Caching：重复前缀可显著降低延迟与缓存输入成本。
  https://developers.openai.com/api/docs/guides/prompt-caching
- OpenAI Token Counting：发送前计数，用于成本估计和模型路由。
  https://developers.openai.com/api/docs/guides/token-counting
- OpenAI Latency Optimization：过滤上下文、稳定共享前缀、动态内容后置。
  https://developers.openai.com/api/docs/guides/latency-optimization
- Anthropic Skills：Skills 使用 progressive disclosure 管理上下文。
  https://docs.anthropic.com/en/docs/claude-code/skills
- Anthropic Prompt Caching：5 分钟 cache write 为 1.25x，cache hit 为 0.1x 基础输入价。
  https://docs.anthropic.com/en/docs/build-with-claude/prompt-caching
- Anthropic Token Counting：调用前管理 rate limit、成本和长度。
  https://docs.anthropic.com/en/docs/build-with-claude/token-counting
- LLMLingua / LongLLMLingua：长上下文压缩可降低成本，但存在信息丢失与领域迁移风险。
  https://arxiv.org/abs/2310.05736
  https://arxiv.org/abs/2310.06839
- DSPy：用数据集与 metric 优化质量，并可把更小模型纳入成本目标。
  https://dspy.ai/getting-started/gepa-optimization/

## 不采用

- 不把 LLMLingua 默认用于 300–500 Token Prompt：额外模型与信息损失不划算。
- 不为缓存阈值填充无效文本。
- 不用字符硬截断满足预算。
- 不把 Claude/Codex 订阅额度伪装成 API 美元账单。

## 当前测量

- Skill 入口：1,529 → 1,082 tokens，下降 29.2%。
- 33 个 Prompt 均值：558.3 → 410.1，下降 26.5%。
- 33/33 预算通过。
- 领域覆盖与 traceability 保持 100%。
- 历史日志不能隔离 Skill 净成本；必须从本版本开始记录 per-run telemetry。

