# Meta-Prompt

> 把原始表达编译成**目标明确、审美可确认、模型可执行、结果可验证、成本受控**的任务协议。

Meta-Prompt 不是「把你的话扩写成更长的 prompt」。它先识别你真正要的结果、好坏标准、失败边界，再生成目标模型更容易执行、输出可以验收、Token 成本受控的任务协议。

```
原始表达 → 现实目标 → 好坏标准 → 最小充分 Prompt → 验收与失败处理
```

## 它解决什么

- 你说的是手段，真正需要的是结果
- 目标、约束、审美、输出格式互相冲突，没有优先级
- Prompt 看似完整，却没有可观察的成功标准
- 模型不知道工具、权限、运行时、人工确认边界
- 为追求「完整感」生成 mega-prompt，浪费 Token、延迟和注意力

## 核心机制：三模式路由

按复杂度选**最低充分模式**，不因任务「看起来专业」而升级。

| 模式 | 何时用 | Prompt / Output 预算 |
|---|---|---:|
| **Express** | 单步、低风险、目标明确 | 180 / 500 tokens |
| **Guided** | 有一个关键歧义或审美未知项 | 350 / 900 |
| **Harness** | 高风险、多阶段、涉及工具或回归验证 | 700 / 1600 |

## 工作流

```
Route → Goal → Taste? → Diagnose → Compile → Budget Gate → Evaluate
```

1. **Route** — 按歧义/风险/阶段数选模式
2. **Goal** — 把表面请求转成 Goal Contract：真实结果、受众、交付物、不可变约束、可观察成功证据
3. **Taste**（写作/视觉/品牌/创意任务）— 用正反样本和 A/B 偏好提取可观察审美轴，方向未确认前不产高成本产物
4. **Diagnose** — 找目标/前提/评价/约束四类错位，定位唯一最高优先级约束
5. **Compile** — 每个需求编译为 `Requirement → Instruction → Acceptance Test → Failure Handling`
6. **Budget Gate** — 删空字段、角色包装、不可验收形容词；超预算降 detail level 而非硬截断
7. **Evaluate** — 检查目标未漂移、需求有验收、失败可观察、候选优于 baseline、Token 达标

## 用法

### 自然语言触发

直接描述需求即可，日常对话由轻量门卫自动选模式：

```
帮我优化这个提示词……
把这段需求改成 coding agent 能直接执行的 Prompt
这个 Prompt 为什么效果不稳定
比较这两个 Prompt
减少 Prompt Token，但不能降低效果
```

### 显式命令

```
/meta-prompt compare    比较 baseline / candidate
/meta-prompt stats      汇总运行 trace
/meta-prompt validate   基础结构验证
```

### 默认输出

```markdown
**需求确认**
- 真实目标 / 关键假设 / 最高优先级约束

**优化后 Prompt**
[可直接使用]

**验证**
- 可观察验收条件
```

只要 Prompt 时，只返回 Prompt。

## 项目结构

```
meta-prompt/
├── SKILL.md              # 常驻路由器（≈1.5k tokens），触发/路由/工作流/红线
├── references/           # 按需加载的细节模块
│   ├── architecture.md       完整说明（维护时读）
│   ├── goal-elicitation.md   目标梳理
│   ├── taste-elicitation.md  审美采集
│   ├── diagnosis.md          错位诊断
│   ├── compiler.md           编译规则
│   ├── evaluation.md         评估门槛
│   ├── model-adapters.md     多模型适配（ChatGPT/Claude/Gemini/Image/Coding Agent）
│   ├── domain-patterns.md    领域判断模块（AI/学习/写作/投资/项目）
│   └── token-economy.md      Token 与成本
├── schemas/              # 机器可验证的契约（Goal/Taste/Prompt-Spec/Eval/Trace）
├── scripts/              # 确定性工具（编译/比较/审计/反馈/验证）
├── tests/                # 63 个单测：结构 + 回归 + 多元基准
├── evals/                # 33 场景跨领域基准 + 生成报告
└── feedback/             # 低成本运行日志（默认仅脱敏摘要）
```

## 设计原则

- **渐进加载** — 主入口只做路由，细节按需读取，不全量进上下文
- **可验收优先** — 拒绝「高级/专业/震撼」等不可验收词，每个需求绑定验收测试
- **失败显式编码** — 写出「如果 X 失败 → Y」的分支，而非只有正向流程
- **成本即目标函数** — 优化单位是「单位成功任务成本」，不是「prompt 越短越好」
- **不补偿现实缺口** — 不用 prompt 替代缺失的数据、权限或真实反馈

## 红线

不生成 mega-prompt 制造完整感 · 不用抽象质量词代替验收 · 不捏造准确率/成本 · 不用 Prompt 补偿缺失的数据或权限 · 不展示隐藏推理。

## 开发

```bash
python -m unittest discover -s tests     # 63 单测
python scripts/validate_skill.py         # 结构验证
python scripts/run_diverse_benchmark.py  # 33 场景基准
python scripts/token_audit.py            # Token 审计
```

> 记录反馈时用 stdin 传 JSON，不要用 `--data`（Windows 控制台经 argv 传中文会丢成 `?`）：
> ```bash
> echo '{"mode":"Guided","goal_summary":"...","passed":true}' | python scripts/log_run.py
> ```

## License

MIT
