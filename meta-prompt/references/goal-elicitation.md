# Goal Elicitation

## 目标

把“生成什么”改写为“谁使用结果后能做出什么改变”。

## 信息增益路由

按以下顺序寻找未知项：

1. 答案不同是否会改变任务方向？
2. 能否从上下文可靠推断？
3. 错误假设是否难以逆转或验证？
4. 是否必须由用户提供，而非工具查得？

只询问当前最高信息增益问题。每轮一个问题；回答后回写 Contract，再检查剩余歧义。低影响未知项使用显式默认值。

## Goal Contract

```yaml
surface_request: 用户原话要什么
real_outcome: 希望现实中改变什么状态
audience: 谁使用或接收结果
decision_or_action: 结果支持什么决定或行动
deliverable: 交付物及使用场景
available_inputs: 已有材料、数据、工具
constraints: 时间、预算、权限、合规、长度
non_goals: 明确不解决什么
success_evidence: 可观察的完成证据
critical_unknowns: 会改变方向的未知项
assumptions: 为继续执行采用的假设
```

## 确认门槛

- Express：内部形成，不阻断执行。
- Guided：公开关键假设；方向分叉时请求确认。
- Harness：执行或生成高成本最终产物前确认 Contract。

不要把确认变成让用户重写需求。先提出可编辑的理解，再让用户纠偏。
