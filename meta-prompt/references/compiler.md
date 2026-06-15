# Prompt Compiler

## 输入

编译器接收 `schemas/prompt-spec.yaml`：

- Goal Contract 是事实源。
- Taste Contract 只在主观任务中存在。
- Requirement 是最小追踪单位。
- Runtime 决定接口表达，不得改变目标。

## 编译规则

1. 将真实目标放在交付物之前。
2. 将唯一最高优先级约束放在任务动作之前。
3. 每个 Requirement 保留 ID，并绑定指令、验收和失败处理。
4. 将未知项写成假设、请求材料或降级结论。
5. 将格式要求编译为目标运行时支持的 Schema 或明确段落。
6. 删除不改变结果的角色、形容词、重复说明和低价值示例。
7. 读取 `token-economy.md`，按模式预算选择 detail level。
8. 空字段不渲染；完整追踪状态可放 trace，不在 Prompt 重复。

## 追踪矩阵

```text
R1 requirement
  → prompt_instruction
  → acceptance_test
  → failure_handling
```

不得出现：

- 没有 Prompt 指令的需求
- 没有验收的核心需求
- 验收测试要求 Prompt 从未生成的内容
- Adapter 偷偷改变目标、受众或审美

## 最小充分

如果删除某段不会改变模型选择、证据边界、工具行为、输出结构或验收结果，则删除。

不得用字符硬截断满足预算。超预算时按 Full → Guided → Minimal
降级，并在 trace 中记录实际 detail level。
