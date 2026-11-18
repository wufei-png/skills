# 任务提示词模板 / Task Prompt Templates

选择符合任务与授权范围的模板，复制代码块并替换尖括号里的内容。需要某条 `[可选]` 指令时，保留正文并去掉标记，其余可选行整行删除。

Choose a scenario, copy its Chinese prompt, and fill in the angle-bracket placeholders. Keep the relevant `[可选]` instructions, remove their markers, and delete the other optional lines.

## 协作与交付 / Collaboration and delivery

| 中文 | English |
| --- | --- |
| [设计决策](./design-decision.md) | [Design decisions](./design-decision.md) |
| [只读评审与意见核实](./review-changes.md) | [Read-only review and finding verification](./review-changes.md) |
| [实施与验证](./implement-and-verify.md) | [Implementation and verification](./implement-and-verify.md) |
| [按意图提交与交付收尾](./commit-changes.md) | [Grouped commits and delivery review](./commit-changes.md) |
| [跨会话交接与接手](./session-handoff.md) | [Session handoff and resumption](./session-handoff.md) |
| [资料调研](./research.md) | [Research](./research.md) |
| [技术文档修订与交付清稿](./revise-technical-writing.md) | [Technical editing and delivery cleanup](./revise-technical-writing.md) |
| [提示词改动评估](./evaluate-prompt-change.md) | [Prompt change evaluation](./evaluate-prompt-change.md) |

## 游戏 / Games

| 中文 | English |
| --- | --- |
| [游戏体验评审](./game-experience-review.md) | [Game experience review](./game-experience-review.md) |
| [游戏美术与交互排查](./game-art-interaction.md) | [Game art and interaction review](./game-art-interaction.md) |
| [游戏对白与叙事修订](./game-dialogue-and-narrative.md) | [Game dialogue and narrative revision](./game-dialogue-and-narrative.md) |

## 音乐 / Music

| 中文 | English |
| --- | --- |
| [歌曲构思与批次配置](./music-brief.md) | [Song concepts and batch planning](./music-brief.md) |
| [歌词与配置复核](./music-review.md) | [Lyrics and configuration review](./music-review.md) |
| [Suno 授权生成与续跑](./suno-create.md) | [Authorized Suno creation and resumption](./suno-create.md) |

## 填写示例 / Filled example

以选用 `review-tests` 评审缓存测试为例。 [只读评审与意见核实](./review-changes.md)

```text
请只读评审 tests/test_cache.py，以 docs/cache.md 的超时约定为准。
用 $review-tests 检查测试能否发现刷新失败后丢失上次成功结果的回归。
给出已确认问题的位置、触发条件和影响。
```

## 维护 / Maintenance

- 按任务意图查找已有模板。需要不同输入、授权或验收方式时，再增加场景或变体。
- 从实际请求和纠偏中保留会改变执行的措辞。通用流程引用 Skill，项目、账号和内部资料使用通用占位符。
- 需要验证改动效果时，用同一组用例对照前后的输出和执行结果。 [提示词改动评估](./evaluate-prompt-change.md)
