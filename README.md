<p align="right"><strong>English</strong> · <a href="./README_CN.md">中文</a></p>

# Skills

Small, composable agent skills for clarifying decisions, delegating read-only reviews, and shipping changes through verified stages.

This repository borrows the useful shape of [mattpocock/skills](https://github.com/mattpocock/skills): skills are grouped by purpose, each skill is individually discoverable, required companions are stated explicitly, and the root documentation acts as the catalog. Package release machinery, plugin metadata, ADRs, and other infrastructure are intentionally omitted until this collection needs them.

## Install

Browse and install from the repository:

```bash
npx skills@latest add wufei-png/skills
```

Install one skill non-interactively:

```bash
npx skills@latest add wufei-png/skills --skill grilling -g -y --agent codex
```

`review-gated-implementation` delegates every review gate to `delegated-change-review`, so install them together:

```bash
npx skills@latest add wufei-png/skills \
  --skill review-gated-implementation \
  --skill delegated-change-review \
  -g -y --agent codex
```

`implement-in-stages` can be installed on its own:

```bash
npx skills@latest add wufei-png/skills \
  --skill implement-in-stages \
  -g -y --agent codex
```

## Validate

Validate catalog discovery, repository contracts, and changed-file whitespace from the repository root:

```bash
NO_COLOR=1 npx -y skills@latest add . --list
python3 -m unittest discover -s tests/repository-contract -p 'test_*.py' -v
git diff --check
```

For manual-only skills, also keep `disable-model-invocation: true` paired with `policy.allow_implicit_invocation: false`. OpenAI's base-schema `quick_validate.py` does not accept the Claude Code and Pi invocation field, so it is not a pass/fail gate for this cross-host catalog.

## Catalog

### Productivity

- [`grilling`](./skills/productivity/grilling/SKILL.md) — Resolve a decision through dependency-ordered questions about genuine tradeoffs.
- [`review-gated-grilling`](./skills/productivity/review-gated-grilling/SKILL.md) — Review each candidate question with fresh, read-only subagents before asking it.
- [`codex-session-recovery`](./skills/productivity/codex-session-recovery/SKILL.md) — Find local Codex sessions read-only and produce CLI-first recovery steps.
- [`opencode-session-toolkit`](./skills/productivity/opencode-session-toolkit/SKILL.md) — Inspect, search, diagnose, and export local OpenCode SQLite sessions safely.

### Engineering

- [`improve-code-comments`](./skills/engineering/improve-code-comments/SKILL.md) — Audit and improve comments and docstrings without changing executable code.
- [`review-tests`](./skills/engineering/review-tests/SKILL.md) — Audit a project test suite for prioritized, evidence-backed defects without modifying it.
- [`review-loop`](./skills/engineering/review-loop/SKILL.md) — Run a bounded review-and-fix loop with fresh, read-only reviewer subagents.
- [`delegated-change-review`](./skills/engineering/delegated-change-review/SKILL.md) — Run the single delegated review gate used by `review-gated-implementation`.
- [`review-gated-implementation`](./skills/engineering/review-gated-implementation/SKILL.md) — Execute an authorized change as dependency-ordered stages, reviewing and committing each after its checks pass.
- [`implement-in-stages`](./skills/engineering/implement-in-stages/SKILL.md) — Execute an authorized change as dependency-ordered stages, committing each after its checks pass.

## Paired variants

| Base skill                    | Variant                 | Intentional difference                                                                                        | Maintenance rule                                                                                                            |
| ----------------------------- | ----------------------- | ------------------------------------------------------------------------------------------------------------- | --------------------------------------------------------------------------------------------------------------------------- |
| `grilling`                    | `review-gated-grilling` | Adds fresh, read-only subagent review before each candidate question or permitted batch is shown to the user. | Keep the interview and authorization contract parallel; put reviewer behavior only in the gated variant.                    |
| `review-gated-implementation` | `implement-in-stages`   | Removes the per-stage and final delegated reviews, including review findings and outcome reporting.           | Keep planning, stage boundaries, checks, commits, and risk reporting parallel; put review behavior only in the gated skill. |

All skills in the current catalog are manual-only. Each `SKILL.md` sets `disable-model-invocation: true` for Claude Code and Pi, while the paired `agents/openai.yaml` sets `policy.allow_implicit_invocation: false` for ChatGPT and Codex. Keep both fields in sync. `review-gated-grilling` and the review skills are Codex-first because they expect a fresh subagent mechanism; the code review skills additionally use the built-in `$review-agent` skill where referenced. Reviewers do not edit implementation files or ask the user questions directly. Whether code reviewers run tests or checks is a review-strategy decision based on the concrete problem. The primary agent still adjudicates findings and owns the user-facing result.

## External projects

These skill-backed projects remain in their own repositories because their skills evolve atomically with dedicated CLIs, installers, services, tests, or runtime assets. They are linked here for discovery rather than copied into this lightweight catalog.

### Standalone skill products

- [`AgentRepoRouter`](https://github.com/wufei-png/AgentRepoRouter) — Routes coding tasks across repositories, project skills and agents, and native coding CLIs while keeping repository scanning, generated mappings, multi-host installation, and symlink management in one product.
- [`animated-sticker-maker`](https://github.com/wufei-png/animated-sticker-maker) — Turns a static reference image and motion prompt into a validated transparent animated sticker.
- [`codex-native-scheduler`](https://github.com/wufei-png/codex-native-scheduler) — Schedules and manages unattended Codex CLI jobs through native OS schedulers.
- [`DocMate`](https://github.com/wufei-png/DocMate) — Answers questions against a configured documentation repository catalog and can prepare tightly scoped documentation repairs.

### Skill-driven systems

- [`obsidian-vault-pr`](https://github.com/wufei-png/obsidian-vault-pr) — Provides safe, agent-driven change management for existing Git-managed Obsidian vaults through a dedicated CLI and review workflow.
- [`reviewworthy`](https://github.com/wufei-png/reviewworthy) — Provides policy-aware, maintainer-first workflows for human-owned, AI-assisted open-source contributions.
- [`git-evidence`](https://github.com/wufei-png/git-evidence) — Produces evidence-first engineering activity reports across GitHub, GitLab, and Gitee.
- [`review-agent-flow`](https://github.com/wufei-png/review-agent-flow) — Orchestrates GitLab human and AI review with local agent support and its own durable execution workflow.
- [`AI-Codereview-Gitlab-Opencode`](https://github.com/wufei-png/AI-Codereview-Gitlab-Opencode) — Runs multi-platform AI code review with an OpenCode Agent Review backend.

## Sources

| Imported content              | Source snapshot                                                                                                                                                                                                                                                           |
| ----------------------------- | ------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------- |
| `grilling`                    | [`wufei-png/grilling@64853fe`](https://github.com/wufei-png/grilling/tree/64853fedfc2d02f53013bb8c1666c6316760d289)                                                                                                                                                       |
| `review-loop`                 | Based on [`wufei-png/agent-review-skills@df3a8e6`](https://github.com/wufei-png/agent-review-skills/tree/df3a8e6c76cab0433d10529b50cc6dae573eb9c0), with the manual-only invocation field restored                                                                        |
| `delegated-change-review`     | `SKILL.md` from local user-skill snapshot, SHA-256 `e6266516eacc80eb6fdd1859a0d52e457edb2fa3f2c499655a713fd2e92fea44`; UI metadata updated to remove the standalone commit request                                                                                        |
| `review-gated-implementation` | Local user-skill snapshot, SHA-256 `3e9f33b12e135d8491a0d31b70413c576f4ba0582c90713894e646c89d31608a`                                                                                                                                                                     |
| `improve-code-comments`       | [`wufei-png/improve-code-comments@f8d0199`](https://github.com/wufei-png/improve-code-comments/tree/f8d019954c05b458c2fef11b3f6e555f5af733ed); installable files copied directly, with manual-only metadata added                                                         |
| `codex-session-recovery`      | [`wufei-png/codex-session-recovery@17fb753`](https://github.com/wufei-png/codex-session-recovery/tree/17fb75369d51173279989b9d0a0d6779a954ac71); copied with manual-only metadata, monorepo paths, and current CLI-first capability wording                               |
| `opencode-session-toolkit`    | English runtime and tests from [`wufei-png/opencode-session-toolkit@6fb12aa`](https://github.com/wufei-png/opencode-session-toolkit/tree/6fb12aa0a25667964ce1b1090e872194f9bb88c9); the Chinese package and independent release machinery were intentionally not migrated |

The original repository documentation is retained under [`docs/archive`](./docs/archive/) as historical source material; the current policy is documented above. The source repositories and their complete histories are linked above. `improve-code-comments`, `codex-session-recovery`, and `opencode-session-toolkit` are frozen distribution sources after this consolidation: future development and installation use this repository, with no independent installer, version, release archive, or ClawHub publishing flow maintained here.

`review-tests` is an original synthesis informed by the defect-first contract in [OpenAI Codex `review-agent@83a4187`](https://github.com/openai/codex/blob/83a418783707f4446aa832b2799d6cacfef75011/codex-rs/skills/src/assets/samples/review-agent/SKILL.md), the portfolio evidence rules in [levnikolaevich/claude-code-skills@ac4f240](https://github.com/levnikolaevich/claude-code-skills/blob/ac4f240070065a8fcebb8ada19a93e07cdd12266/plugins/codebase-audit-suite/skills/ln-23-test-suite-auditor/SKILL.md), the test-design review areas in [posit-dev/skills@6d48d6b](https://github.com/posit-dev/skills/blob/6d48d6bef92ff3f2194d5b00e61974e61125711e/posit-dev/review-testing/SKILL.md), and the independent-oracle guidance in [obra/superpowers@caa1826](https://github.com/obra/superpowers/blob/caa1826cbadeb88f88c7ad7b3f66178cba01e57d/skills/test-driven-development/writing-good-tests.md). No upstream files were imported.

`review-gated-grilling` is a self-contained variant derived from the current `grilling` contract. Its independent-first, evidence-led, adaptively stopped discussion gate is informed by [Liang et al.'s multi-agent debate](https://aclanthology.org/2024.emnlp-main.992/), [Zhu et al.'s analysis of confidence and diversity](https://aclanthology.org/2026.findings-acl.1694/), [Baltaji et al.'s conformity findings](https://aclanthology.org/2024.c3nlp-1.2/), and [gstack's fresh-context second-opinion workflow](https://github.com/garrytan/gstack/blob/main/office-hours/SKILL.md). No upstream files were imported.

`implement-in-stages` is a self-contained variant derived from `review-gated-implementation`. Their shared planning, execution, checks, commit, and reporting wording intentionally stays parallel so common updates can be synchronized directly.

## License

This repository, including the three consolidated `wufei-png` skills above, is released under the [MIT License](./LICENSE). Imported MIT-0 and upstream MIT notices are retained under [`LICENSES`](./LICENSES/).
