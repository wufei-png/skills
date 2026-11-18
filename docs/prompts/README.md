# 任务提示词模板 / Task Prompt Templates

复制模板，填写尖括号里的内容。保留需要的 `[可选]` 指令并去掉标记，其余可选行整行删除。

Copy a Chinese prompt and fill in the angle-bracket placeholders. Remove the `[可选]` markers from the lines you keep and delete the other optional lines.

## 协作与交付 / Collaboration and delivery

- [设计决策 / Design decisions](./design-decision.md)
- [只读评审与意见核实 / Read-only review and finding verification](./review-changes.md)
- [实施与验证 / Implementation and verification](./implement-and-verify.md)
- [研判来源不明的工作区改动 / Triage unexplained Git changes](./commit-changes.md#研判来源不明的工作区改动)
- [按意图提交与交付收尾 / Grouped commits and delivery review](./commit-changes.md)
- [跨会话交接与接手 / Session handoff and resumption](./session-handoff.md)
- [资料调研 / Research](./research.md)
- [技术文档修订与交付清稿 / Technical editing and delivery cleanup](./revise-technical-writing.md)
- [提示词改动评估 / Prompt change evaluation](./evaluate-prompt-change.md)

## 游戏 / Games

- [游戏体验评审 / Game experience review](./game-experience-review.md)
- [游戏美术与交互排查 / Game art and interaction review](./game-art-interaction.md)
- [游戏对白与叙事修订 / Game dialogue and narrative revision](./game-dialogue-and-narrative.md)

## 音乐 / Music

- [歌曲构思与批次配置 / Song concepts and batch planning](./music-brief.md)
- [歌词与配置复核 / Lyrics and configuration review](./music-review.md)
- [Suno 授权生成与续跑 / Authorized Suno creation and resumption](./suno-create.md)

## 填写示例 / Filled example

```text
请只读评审 tests/test_cache.py，以 docs/cache.md 的超时约定为准。
用 $review-tests 检查测试能否发现刷新失败后丢失上次成功结果的回归。
给出已确认问题的位置、触发条件和影响。
```

## 维护 / Maintenance

- 优先更新已有模板。任务输入、授权或验收有实质差异时，增加变体。
- 保留能改变执行的措辞，复用 Skill。用占位符替换项目或私有资料。
- 用同一组用例核验行为变化。 [提示词改动评估](./evaluate-prompt-change.md)
