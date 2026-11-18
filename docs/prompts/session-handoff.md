# 跨会话交接与接手

## 准备交接

```text
请为 <后续任务> 在 <保存位置或对话中> 准备交接稿。核对 <当前记录和实际状态>，写清目标、已确认决定、已完成事项及证据、当前检查点、下一步和完成条件。
写明仍需决定的问题和后续动作的授权状态。对提交、生成或发布等可能重复执行的步骤，附上可供核对的提交号、回执或记录位置。
[可选] 交接稿完成后，我授权用 $codex-thread-report 将它发给 <目标 Codex 会话链接或 ID>。
```

发送到现有 Codex 会话的流程见 [codex-thread-report](../../skills/productivity/codex-thread-report/SKILL.md)。

## 接手已确认任务

```text
请根据 <交接稿或计划> 继续 <目标>，做到 <完成条件>。
[可选] 先用 $codex-session-recovery 查找 <会话 ID、项目或关键词> 对应的历史会话。
核对当前工作区、证据和执行记录，确认哪些步骤已经完成，从第一个未完成且已授权的步骤继续。
遇到提交、生成或发布结果不明时，先查实际状态再决定能否续跑。若新证据影响已确认的决定，指出变化和需要确认的事项。
```

本地会话查找流程见 [codex-session-recovery](../../skills/productivity/codex-session-recovery/SKILL.md)。
