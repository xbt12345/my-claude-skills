# my-claude-skills

自建的 [Agent Skills](https://docs.anthropic.com/en/docs/claude-code/skills) 合集。每个子目录是一个独立、可移植的 skill，遵循 Agent Skills 标准，可在 Claude Code 及其他兼容 runtime（Codex、Cursor、OpenCode 等）中使用。

## Skills

| Skill | 一句话 | 状态 |
|---|---|---|
| [meta-prompt](./meta-prompt) | 把原始表达编译成目标明确、可验收、成本受控的任务协议——一个提示词编译与验证引擎 | v4.5 · 63 单测全绿 |

## 这些 skill 是什么

Skill = 一段渐进加载的专家知识 + 可执行脚本 + 验证套件。主入口 `SKILL.md` 常驻为「路由器」，按需加载细节，让 agent 在正确的判断规则下工作，而不是把所有内容塞进上下文。

## 安装（任选其一）

**Claude Code** — 复制或软链到 skills 目录：

```bash
# 复制
cp -r meta-prompt ~/.claude/skills/meta-prompt
# 或软链（便于随仓库更新）
ln -s "$(pwd)/meta-prompt" ~/.claude/skills/meta-prompt
```

**其他 runtime** — 放到该 runtime 的 skills 目录即可；skill 内容为 runtime 中立，不绑定单一平台。

安装后在对话里自然描述需求即可触发，或用 `/meta-prompt` 显式调用。

## 开发约定

- 每个 skill 自带 `tests/`，改动后跑 `python -m unittest discover -s <skill>/tests` 与 `python <skill>/scripts/validate_skill.py`。
- 单一事实源在本仓库；不要在多个 runtime 目录各维护一份副本。

## License

[MIT](./LICENSE)
