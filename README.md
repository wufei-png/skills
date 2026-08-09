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

- [`review-loop`](./skills/engineering/review-loop/SKILL.md) — Run a bounded review-and-fix loop with fresh, read-only reviewer subagents.
- [`delegated-code-review`](./skills/engineering/delegated-code-review/SKILL.md) — Run the original single-pass review workflow from `agent-review-skills`.
- [`delegated-change-review`](./skills/engineering/delegated-change-review/SKILL.md) — Perform the single read-only review gate used by `review-gated-implementation`.
- [`review-gated-implementation`](./skills/engineering/review-gated-implementation/SKILL.md) — Execute an authorized change as dependency-ordered, independently verified, reviewed, and committed stages.

The review skills are Codex-first. They expect a fresh subagent mechanism and the built-in `$review-agent` skill where referenced. Reviewers do not edit implementation files; whether they run tests or checks is a review-strategy decision based on the concrete problem. The implementation owner still adjudicates findings, applies accepted fixes, and owns final verification.

## Sources

| Imported content | Source snapshot |
| --- | --- |
| `grilling` | [`wufei-png/grilling@64853fe`](https://github.com/wufei-png/grilling/tree/64853fedfc2d02f53013bb8c1666c6316760d289) |
| `review-loop`, `delegated-code-review` | [`wufei-png/agent-review-skills@df3a8e6`](https://github.com/wufei-png/agent-review-skills/tree/df3a8e6c76cab0433d10529b50cc6dae573eb9c0) |
| `delegated-change-review` | `SKILL.md` from local user-skill snapshot, SHA-256 `e6266516eacc80eb6fdd1859a0d52e457edb2fa3f2c499655a713fd2e92fea44`; UI metadata updated to remove the standalone commit request |
| `review-gated-implementation` | Local user-skill snapshot, SHA-256 `3e9f33b12e135d8491a0d31b70413c576f4ba0582c90713894e646c89d31608a` |

The original repository documentation is retained unchanged under [`docs/archive`](./docs/archive/) as historical source material; the current policy is documented above. The source repositories and their complete histories are linked above.

## License

This repository is released under the [MIT License](./LICENSE). Imported MIT-0 and upstream MIT notices are retained under [`LICENSES`](./LICENSES/).
