<p align="right"><a href="./README.md">English</a> · <strong>中文</strong></p>

# Skills

一组小而可组合的 Agent Skills，用于澄清决策、委托只读审查，以及通过分阶段验证交付变更。

本仓库采用了 [mattpocock/skills](https://github.com/mattpocock/skills) 中适合当前规模的结构：按用途组织 skill、保持每个 skill 可单独发现、明确说明必要的配套 skill，并由根目录文档提供完整索引。包发布、插件元数据、ADR 等基础设施会等到确有需要时再引入。

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

`implement-in-stages` 可以单独安装：

```bash
npx skills@latest add wufei-png/skills \
  --skill implement-in-stages \
  -g -y --agent codex
```

## 校验

在仓库根目录校验 skill 发现、仓库契约及已修改文件的空白格式：

```bash
NO_COLOR=1 npx -y skills@latest add . --list
python3 -m unittest discover -s tests/repository-contract -p 'test_*.py' -v
git diff --check
```

对于只能手动调用的 skill，还需保持 `disable-model-invocation: true` 与 `policy.allow_implicit_invocation: false` 成对存在。OpenAI 的基础 schema `quick_validate.py` 不接受 Claude Code 与 Pi 的调用字段，因此不作为这个跨宿主目录的通过门禁。

## Skill 索引

### Productivity

- [`grilling`](./skills/productivity/grilling/SKILL.md) — 通过依赖有序的问题收敛决策中的真实取舍。
- [`review-gated-grilling`](./skills/productivity/review-gated-grilling/SKILL.md) — 每次提问前由全新、只读的 subagent 审核候选问题。
- [`codex-session-recovery`](./skills/productivity/codex-session-recovery/SKILL.md) — 只读查找本地 Codex 会话，并生成 CLI 优先的恢复步骤。
- [`opencode-session-toolkit`](./skills/productivity/opencode-session-toolkit/SKILL.md) — 安全检查、搜索、诊断及导出本地 OpenCode SQLite 会话。

### Engineering

- [`improve-code-comments`](./skills/engineering/improve-code-comments/SKILL.md) — 在不修改可执行代码的前提下审查和改进注释与 docstring。
- [`review-tests`](./skills/engineering/review-tests/SKILL.md) — 以只读方式审查项目测试套件，返回按优先级排序、有证据支持的缺陷。
- [`review-loop`](./skills/engineering/review-loop/SKILL.md) — 使用全新、只读审查子 Agent 运行有轮次上限的审查与修复循环。
- [`delegated-change-review`](./skills/engineering/delegated-change-review/SKILL.md) — 为 `review-gated-implementation` 提供单轮委托审查门。
- [`review-gated-implementation`](./skills/engineering/review-gated-implementation/SKILL.md) — 将已授权变更拆成依赖有序的阶段，每阶段检查通过后审查并提交。
- [`implement-in-stages`](./skills/engineering/implement-in-stages/SKILL.md) — 将已授权变更拆成依赖有序的阶段，每阶段检查通过后提交。

## 配对变体

| 基础 skill                    | 变体                    | 有意保留的差异                                                             | 维护规则                                                                         |
| ----------------------------- | ----------------------- | -------------------------------------------------------------------------- | -------------------------------------------------------------------------------- |
| `grilling`                    | `review-gated-grilling` | 每个候选问题或允许的问题批次展示给用户前，增加全新、只读的 subagent 审查。 | 访谈和授权契约保持平行；reviewer 行为只放在 gated 变体中。                       |
| `review-gated-implementation` | `implement-in-stages`   | 删除逐阶段和最终 delegated review，包括 review finding 与 outcome 报告。   | 阶段规划、边界、检查、提交及风险报告保持平行；review 行为只放在 gated skill 中。 |

当前目录中的所有 skill 都只能手动调用。每个 `SKILL.md` 都通过 `disable-model-invocation: true` 管理 Claude Code 与 Pi；配套的 `agents/openai.yaml` 则通过 `policy.allow_implicit_invocation: false` 管理 ChatGPT 与 Codex，两处字段必须保持同步。`review-gated-grilling` 与审查 skill 以 Codex 为主要运行环境，因为它们需要全新 subagent 机制；代码审查 skill 还会在标明的位置依赖内置 `$review-agent`。Reviewer 不编辑实现文件，也不直接向用户提问；代码 reviewer 是否运行测试或检查，由具体问题的审查策略决定。主 Agent 仍负责裁决发现并对面向用户的最终结果负责。

## 外部项目

以下由 skill 驱动的项目继续在各自仓库维护，因为其 skill 需要与专用 CLI、安装器、服务、测试或运行时资产原子演进。这里仅提供发现入口，不将代码复制进这个轻量目录。

### 独立 Skill 产品

- [`AgentRepoRouter`](https://github.com/wufei-png/AgentRepoRouter) — 在仓库、项目级 skill/agent 与原生 coding CLI 之间路由任务，并将仓库扫描、映射配置生成、多 host 安装及软链接管理保留为一个完整产品。
- [`animated-sticker-maker`](https://github.com/wufei-png/animated-sticker-maker) — 将静态参考图与动作提示转换为经过验证的透明动态贴纸。
- [`codex-native-scheduler`](https://github.com/wufei-png/codex-native-scheduler) — 通过操作系统原生调度器安排和管理无人值守的 Codex CLI 任务。
- [`DocMate`](https://github.com/wufei-png/DocMate) — 基于配置好的文档仓库目录回答问题，并可准备范围严格受控的文档修复。

### Skill 驱动系统

- [`obsidian-vault-pr`](https://github.com/wufei-png/obsidian-vault-pr) — 通过专用 CLI 与审查流程，为已有 Git 管理的 Obsidian vault 提供安全的 Agent 驱动变更管理。
- [`reviewworthy`](https://github.com/wufei-png/reviewworthy) — 为人类主导、AI 辅助的开源贡献提供策略感知、维护者优先的工作流。
- [`git-evidence`](https://github.com/wufei-png/git-evidence) — 跨 GitHub、GitLab 与 Gitee 生成证据优先的工程活动报告。
- [`review-agent-flow`](https://github.com/wufei-png/review-agent-flow) — 结合本地 Agent 支持和独立的持久化执行流程，编排 GitLab 人工与 AI 审查。
- [`AI-Codereview-Gitlab-Opencode`](https://github.com/wufei-png/AI-Codereview-Gitlab-Opencode) — 以 OpenCode Agent Review 为后端运行多平台 AI 代码审查。

## 来源

| 迁移内容                      | 来源快照                                                                                                                                                                                                          |
| ----------------------------- | ----------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------- |
| `grilling`                    | [`wufei-png/grilling@64853fe`](https://github.com/wufei-png/grilling/tree/64853fedfc2d02f53013bb8c1666c6316760d289)                                                                                               |
| `review-loop`                 | 基于 [`wufei-png/agent-review-skills@df3a8e6`](https://github.com/wufei-png/agent-review-skills/tree/df3a8e6c76cab0433d10529b50cc6dae573eb9c0)，并恢复了仅手动调用字段                                            |
| `delegated-change-review`     | `SKILL.md` 来自本地用户 skill 快照，SHA-256 `e6266516eacc80eb6fdd1859a0d52e457edb2fa3f2c499655a713fd2e92fea44`；UI 元数据已移除独立提交请求                                                                       |
| `review-gated-implementation` | 本地用户 skill 快照，SHA-256 `3e9f33b12e135d8491a0d31b70413c576f4ba0582c90713894e646c89d31608a`                                                                                                                   |
| `improve-code-comments`       | [`wufei-png/improve-code-comments@f8d0199`](https://github.com/wufei-png/improve-code-comments/tree/f8d019954c05b458c2fef11b3f6e555f5af733ed)；直接复制可安装文件，并增加仅手动调用 metadata                      |
| `codex-session-recovery`      | [`wufei-png/codex-session-recovery@17fb753`](https://github.com/wufei-png/codex-session-recovery/tree/17fb75369d51173279989b9d0a0d6779a954ac71)；复制后仅调整手动调用策略、monorepo 路径及当前 CLI-first 能力表述 |
| `opencode-session-toolkit`    | 英文运行包和测试来自 [`wufei-png/opencode-session-toolkit@6fb12aa`](https://github.com/wufei-png/opencode-session-toolkit/tree/6fb12aa0a25667964ce1b1090e872194f9bb88c9)；中文包及独立发布机制不迁入              |

来源仓库的原始文档保存在 [`docs/archive`](./docs/archive/) 中，作为历史来源材料；当前策略以上文为准。上表保留了来源仓库及其完整 Git 历史链接。合并完成后，`improve-code-comments`、`codex-session-recovery` 和 `opencode-session-toolkit` 的旧仓库只作为冻结分发源；后续开发和安装统一使用本仓库，本仓库不再维护它们的独立 installer、版本、Release 压缩包或 ClawHub 发布流程。

`review-tests` 是原创综合设计，参考了 [OpenAI Codex `review-agent@83a4187`](https://github.com/openai/codex/blob/83a418783707f4446aa832b2799d6cacfef75011/codex-rs/skills/src/assets/samples/review-agent/SKILL.md) 的 defect-first 合同、[levnikolaevich/claude-code-skills@ac4f240](https://github.com/levnikolaevich/claude-code-skills/blob/ac4f240070065a8fcebb8ada19a93e07cdd12266/plugins/codebase-audit-suite/skills/ln-23-test-suite-auditor/SKILL.md) 的证据规则、[posit-dev/skills@6d48d6b](https://github.com/posit-dev/skills/blob/6d48d6bef92ff3f2194d5b00e61974e61125711e/posit-dev/review-testing/SKILL.md) 的测试设计审查维度，以及 [obra/superpowers@caa1826](https://github.com/obra/superpowers/blob/caa1826cbadeb88f88c7ad7b3f66178cba01e57d/skills/test-driven-development/writing-good-tests.md) 的独立 oracle 指导。未直接迁入上游文件。

`review-gated-grilling` 是从当前 `grilling` 契约派生的自包含变体。其“先独立判断、再基于证据有限讨论、按材料性自适应停止”的审查门参考了 [Liang 等人的多 Agent 辩论研究](https://aclanthology.org/2024.emnlp-main.992/)、[Zhu 等人对置信度与多样性的分析](https://aclanthology.org/2026.findings-acl.1694/)、[Baltaji 等人的从众效应研究](https://aclanthology.org/2024.c3nlp-1.2/) 及 [gstack 的全新上下文 second-opinion 工作流](https://github.com/garrytan/gstack/blob/main/office-hours/SKILL.md)。未直接迁入上游文件。

`implement-in-stages` 是从 `review-gated-implementation` 派生的自包含变体。两者共有的规划、执行、检查、提交与报告措辞有意保持平行，便于直接同步通用更新。

## 许可证

本仓库及上述三个合并后的 `wufei-png` skill 均采用 [MIT License](./LICENSE)。迁入内容对应的 MIT-0 及上游 MIT 声明保存在 [`LICENSES`](./LICENSES/) 中。
