# Token Economy

## 目标函数

优化单位不是“Prompt 越短越好”，而是：

```text
单位成功任务成本 =
输入 + 输出 + 工具结果 + 追问轮次 + 返工
```

不得为降低输入 Token 而增加失败率或返工。

## 默认预算

| 模式 | Prompt | Output | 加载策略 |
|---|---:|---:|---|
| Express | 180 | 500 | 只用主入口与最小编译 |
| Guided | 350 | 900 | 只加载 Goal/Taste 中必要模块 |
| Harness | 700 | 1600 | 按失败风险加载诊断、编译与评估 |

预算可由 `token_budget.max_prompt_tokens` 和
`token_budget.max_output_tokens` 覆盖。

## 压缩顺序

1. 删除空字段。
2. 删除重复角色、形容词和背景复述。
3. 公共规则只写一次。
4. Express 只传目标、最高约束、动作和输出。
5. Guided 增加关键上下文和验收。
6. Harness 使用紧凑 Requirement/Test/Fail 矩阵。
7. 完整追踪信息放 trace，不在 Prompt 中重复。
8. 仍超预算时降低 detail level；禁止盲目截断句子。

## 缓存

- 稳定的系统规则、Skill 入口和工具说明放前缀。
- 动态用户材料、检索结果和历史放后部。
- 不为达到缓存阈值主动填充无用文本。
- 缓存只降低重复输入成本，不降低输出 Token。

## 长上下文

- 先检索、过滤、去重，再考虑压缩。
- LLMLingua 类方法用于数千 Token 以上且可做质量回归的上下文。
- 当前数百 Token 的执行 Prompt 默认不调用额外压缩模型。

## Telemetry

仅记录显式优化、Guided/Harness 或失败运行；普通 Express 成功任务跳过，避免日志和工具调用反过来增加成本。

```text
date, mode, runtime, goal_summary, pattern_tags,
explicit_request, execution_requested, executed, passed,
failure_category, estimated_prompt_tokens,
actual_input_tokens, cached_input_tokens,
actual_output_tokens, tool_result_tokens,
questions, retries
```

默认不保存原始 Prompt 或敏感材料。记录时用 stdin 传 JSON，不要用 `--data`：Windows 控制台经 argv 传中文会丢成 `?`，污染 `goal_summary`。

```powershell
'{"mode":"Guided","goal_summary":"中文摘要","passed":true}' | python scripts/log_run.py
```

`run_feedback.py start/finish` 同理走 stdin。脚本检测到 `goal_summary` 含乱码替换符会向 stderr 告警。

每周先由 `weekly_reflect.py` 做无模型聚合。少于 5 次真实运行，或没有同类失败累计 3 次时，只报告、不修改 Skill。

订阅额度与 API 美元成本分开统计，不能混算。
