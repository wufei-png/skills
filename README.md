<p align="right"><strong>English</strong> · <a href="./README_CN.md">中文</a></p>

# Skills

Small, composable agent skills for clarifying decisions, delegating read-only reviews, and shipping changes through verified stages.

This repository borrows the useful shape of [mattpocock/skills](https://github.com/mattpocock/skills): skills are grouped by purpose, every skill remains independently installable, and the root documentation acts as the catalog. Package release machinery, plugin metadata, ADRs, and other infrastructure are intentionally omitted until this collection needs them.

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

## Catalog

### Productivity

- [`grilling`](./skills/productivity/grilling/SKILL.md) — Resolve a decision tree by asking only dependency-ready questions with genuine tradeoffs.

### Engineering

- [`review-tests`](./skills/engineering/review-tests/SKILL.md) — Audit a project test suite for prioritized, evidence-backed defects without modifying it.
- [`review-loop`](./skills/engineering/review-loop/SKILL.md) — Run a bounded review-and-fix loop with fresh, read-only reviewer subagents.
- [`delegated-change-review`](./skills/engineering/delegated-change-review/SKILL.md) — Perform the single read-only review gate used by `review-gated-implementation`.
- [`review-gated-implementation`](./skills/engineering/review-gated-implementation/SKILL.md) — Execute an authorized change as dependency-ordered, independently verified, reviewed, and committed stages.

All skills in the current catalog are manual-only in Codex: their `agents/openai.yaml` files set `policy.allow_implicit_invocation: false`. The pre-existing skills also retain `disable-model-invocation: true` for runtimes that recognize that compatibility field. The review skills are Codex-first. They expect a fresh subagent mechanism and the built-in `$review-agent` skill where referenced. Reviewers do not edit implementation files; whether they run tests or checks is a review-strategy decision based on the concrete problem. The implementation owner still adjudicates findings, applies accepted fixes, and owns final verification.

## Sources

| Imported content | Source snapshot |
| --- | --- |
| `grilling` | [`wufei-png/grilling@64853fe`](https://github.com/wufei-png/grilling/tree/64853fedfc2d02f53013bb8c1666c6316760d289) |
| `review-loop` | Based on [`wufei-png/agent-review-skills@df3a8e6`](https://github.com/wufei-png/agent-review-skills/tree/df3a8e6c76cab0433d10529b50cc6dae573eb9c0), with the manual-only invocation field restored |
| `delegated-change-review` | `SKILL.md` from local user-skill snapshot, SHA-256 `e6266516eacc80eb6fdd1859a0d52e457edb2fa3f2c499655a713fd2e92fea44`; UI metadata updated to remove the standalone commit request |
| `review-gated-implementation` | Local user-skill snapshot, SHA-256 `3e9f33b12e135d8491a0d31b70413c576f4ba0582c90713894e646c89d31608a` |

The original repository documentation is retained unchanged under [`docs/archive`](./docs/archive/) as historical source material; the current policy is documented above. The source repositories and their complete histories are linked above.

`review-tests` is an original synthesis informed by the defect-first contract in [OpenAI Codex `review-agent@83a4187`](https://github.com/openai/codex/blob/83a418783707f4446aa832b2799d6cacfef75011/codex-rs/skills/src/assets/samples/review-agent/SKILL.md), the portfolio evidence rules in [levnikolaevich/claude-code-skills@ac4f240](https://github.com/levnikolaevich/claude-code-skills/blob/ac4f240070065a8fcebb8ada19a93e07cdd12266/plugins/codebase-audit-suite/skills/ln-23-test-suite-auditor/SKILL.md), the test-design review areas in [posit-dev/skills@6d48d6b](https://github.com/posit-dev/skills/blob/6d48d6bef92ff3f2194d5b00e61974e61125711e/posit-dev/review-testing/SKILL.md), and the independent-oracle guidance in [obra/superpowers@caa1826](https://github.com/obra/superpowers/blob/caa1826cbadeb88f88c7ad7b3f66178cba01e57d/skills/test-driven-development/writing-good-tests.md). No upstream files were imported.

## License

This repository is released under the [MIT License](./LICENSE). Imported MIT-0 and upstream MIT notices are retained under [`LICENSES`](./LICENSES/).
