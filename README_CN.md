<p align="right"><a href="./README.md">English</a> · <strong>中文</strong></p>

# Skills

一组小而可组合的 Agent Skills，用于澄清决策、委托只读审查，以及通过分阶段验证交付变更。

本仓库采用了 [mattpocock/skills](https://github.com/mattpocock/skills) 中适合当前规模的结构：按用途组织 skill、保持每个 skill 可独立安装，并由根目录文档提供完整索引。包发布、插件元数据、ADR 等基础设施会等到确有需要时再引入。

## 安装

浏览并选择要安装的 skill：

```bash
npx skills@latest add wufei-png/skills
```

非交互式安装单个 skill：

```bash
npx skills@latest add wufei-png/skills --skill grilling -g -y --agent codex
```

`review-gated-implementation` 会把每个审查门委托给 `delegated-change-review`，因此应一起安装：

```bash
npx skills@latest add wufei-png/skills \
  --skill review-gated-implementation \
  --skill delegated-change-review \
  -g -y --agent codex
```

## Skill 索引

### Productivity

- [`grilling`](./skills/productivity/grilling/SKILL.md) — 沿依赖顺序收敛决策树，只询问包含真实取舍且已具备前置条件的问题。

### Engineering

- [`review-loop`](./skills/engineering/review-loop/SKILL.md) — 使用全新、只读审查子 Agent 运行有轮次上限的审查与修复循环。
- [`delegated-code-review`](./skills/engineering/delegated-code-review/SKILL.md) — 保留 `agent-review-skills` 中原始的单轮审查流程。
- [`delegated-change-review`](./skills/engineering/delegated-change-review/SKILL.md) — 为 `review-gated-implementation` 提供单轮只读审查门。
- [`review-gated-implementation`](./skills/engineering/review-gated-implementation/SKILL.md) — 将已授权变更拆成依赖有序、可独立验证、逐阶段审查并提交的实现过程。

这些审查 skill 以 Codex 为主要运行环境，需要全新子 Agent 机制，并在标明的位置依赖内置 `$review-agent` skill。Reviewer 不编辑实现文件；是否运行测试或检查由 reviewer 根据具体问题自行决定。实现 owner 仍负责裁决发现、应用接受的修复及最终验证。

## 来源

| 迁移内容 | 来源快照 |
| --- | --- |
| `grilling` | [`wufei-png/grilling@64853fe`](https://github.com/wufei-png/grilling/tree/64853fedfc2d02f53013bb8c1666c6316760d289) |
| `review-loop`、`delegated-code-review` | [`wufei-png/agent-review-skills@df3a8e6`](https://github.com/wufei-png/agent-review-skills/tree/df3a8e6c76cab0433d10529b50cc6dae573eb9c0) |
| `delegated-change-review` | `SKILL.md` 来自本地用户 skill 快照，SHA-256 `e6266516eacc80eb6fdd1859a0d52e457edb2fa3f2c499655a713fd2e92fea44`；UI 元数据已移除独立提交请求 |
| `review-gated-implementation` | 本地用户 skill 快照，SHA-256 `3e9f33b12e135d8491a0d31b70413c576f4ba0582c90713894e646c89d31608a` |

两个来源仓库的原始文档原样保存在 [`docs/archive`](./docs/archive/) 中，作为历史来源材料；当前策略以上文为准。上表保留了来源仓库及其完整 Git 历史的链接。

## 许可证

本仓库采用 [MIT License](./LICENSE)。迁入内容对应的 MIT-0 及上游 MIT 声明保存在 [`LICENSES`](./LICENSES/) 中。
