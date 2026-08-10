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

- [`review-tests`](./skills/engineering/review-tests/SKILL.md) — 以只读方式审查项目测试套件，返回按优先级排序、有证据支持的缺陷。
- [`review-loop`](./skills/engineering/review-loop/SKILL.md) — 使用全新、只读审查子 Agent 运行有轮次上限的审查与修复循环。
- [`delegated-change-review`](./skills/engineering/delegated-change-review/SKILL.md) — 为 `review-gated-implementation` 提供单轮只读审查门。
- [`review-gated-implementation`](./skills/engineering/review-gated-implementation/SKILL.md) — 将已授权变更拆成依赖有序、可独立验证、逐阶段审查并提交的实现过程。

当前目录中的所有 skill 在 Codex 中都只能手动调用：各自的 `agents/openai.yaml` 都设置了 `policy.allow_implicit_invocation: false`。新增 `review-tests` 之前已有的 skill 还保留了 `disable-model-invocation: true`，供识别该兼容字段的运行时使用。这些审查 skill 以 Codex 为主要运行环境，需要全新子 Agent 机制，并在标明的位置依赖内置 `$review-agent` skill。Reviewer 不编辑实现文件；是否运行测试或检查由 reviewer 根据具体问题自行决定。实现 owner 仍负责裁决发现、应用接受的修复及最终验证。

## 来源

| 迁移内容 | 来源快照 |
| --- | --- |
| `grilling` | [`wufei-png/grilling@64853fe`](https://github.com/wufei-png/grilling/tree/64853fedfc2d02f53013bb8c1666c6316760d289) |
| `review-loop` | 基于 [`wufei-png/agent-review-skills@df3a8e6`](https://github.com/wufei-png/agent-review-skills/tree/df3a8e6c76cab0433d10529b50cc6dae573eb9c0)，并恢复了仅手动调用字段 |
| `delegated-change-review` | `SKILL.md` 来自本地用户 skill 快照，SHA-256 `e6266516eacc80eb6fdd1859a0d52e457edb2fa3f2c499655a713fd2e92fea44`；UI 元数据已移除独立提交请求 |
| `review-gated-implementation` | 本地用户 skill 快照，SHA-256 `3e9f33b12e135d8491a0d31b70413c576f4ba0582c90713894e646c89d31608a` |

两个来源仓库的原始文档原样保存在 [`docs/archive`](./docs/archive/) 中，作为历史来源材料；当前策略以上文为准。上表保留了来源仓库及其完整 Git 历史的链接。

`review-tests` 是原创综合设计，参考了 [OpenAI Codex `review-agent@83a4187`](https://github.com/openai/codex/blob/83a418783707f4446aa832b2799d6cacfef75011/codex-rs/skills/src/assets/samples/review-agent/SKILL.md) 的 defect-first 合同、[levnikolaevich/claude-code-skills@ac4f240](https://github.com/levnikolaevich/claude-code-skills/blob/ac4f240070065a8fcebb8ada19a93e07cdd12266/plugins/codebase-audit-suite/skills/ln-23-test-suite-auditor/SKILL.md) 的证据规则、[posit-dev/skills@6d48d6b](https://github.com/posit-dev/skills/blob/6d48d6bef92ff3f2194d5b00e61974e61125711e/posit-dev/review-testing/SKILL.md) 的测试设计审查维度，以及 [obra/superpowers@caa1826](https://github.com/obra/superpowers/blob/caa1826cbadeb88f88c7ad7b3f66178cba01e57d/skills/test-driven-development/writing-good-tests.md) 的独立 oracle 指导。未直接迁入上游文件。

## 许可证

本仓库采用 [MIT License](./LICENSE)。迁入内容对应的 MIT-0 及上游 MIT 声明保存在 [`LICENSES`](./LICENSES/) 中。
