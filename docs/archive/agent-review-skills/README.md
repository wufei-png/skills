# Agent Review Skills

Two small, manual-first skills for delegating code review to a fresh, read-only subagent while keeping finding verification and fixes with the implementation owner.

These skills are Codex-first: they use `$review-agent` and `fork_turns: "none"`. The `SKILL.md` layout follows the portable Agent Skills convention, but other runtimes need an equivalent fresh-subagent mechanism.

## Skills

### `review-loop`

Use for a non-trivial change that may need several review/fix cycles. It defaults to three review cycles; the user may set `max_rounds`. The reviewer only reviews and reports findings. The primary agent verifies findings, then delegates accepted fixes to the implementation subagent when one owns the change, or fixes them directly.

### `delegated-code-review`

Use as a single review gate before handoff or commit. It performs one read-only review, verifies the findings, applies or delegates accepted fixes, tests them, and finalizes without another review.

Both skills focus on Critical, Important, and clearly worthwhile issues. Minor issues are recorded without blocking completion.

## Installation

### npx skills

Install either skill globally and copy it into the selected agent directories:

```bash
npx skills add wufei-png/agent-review-skills -s review-loop -g -a '*' -y --copy
npx skills add wufei-png/agent-review-skills -s delegated-code-review -g -a '*' -y --copy
```

### curl

This downloads the instruction and Codex metadata without executing remote code:

```bash
base_url=https://raw.githubusercontent.com/wufei-png/agent-review-skills/main
for skill_name in review-loop delegated-code-review; do
  skill_dir="$HOME/.agents/skills/$skill_name"
  mkdir -p "$skill_dir/agents"
  curl -fsSL "$base_url/skills/$skill_name/SKILL.md" -o "$skill_dir/SKILL.md"
  curl -fsSL "$base_url/skills/$skill_name/agents/openai.yaml" -o "$skill_dir/agents/openai.yaml"
done
```

### ClawHub

```bash
clawhub install @wufei-png/review-loop
clawhub install @wufei-png/delegated-code-review
```

## Which one should I use?

| Situation | Recommended skill |
| --- | --- |
| A substantial change needs bounded review/fix/review iteration | `review-loop` |
| A quick, single post-change review is enough | `delegated-code-review` |
| You are executing a multi-task implementation plan with task-level spec and quality gates | [`superpowers:subagent-driven-development`](https://github.com/obra/superpowers/blob/main/skills/subagent-driven-development/SKILL.md) |
| You want a conventional pre-merge reviewer with severity-based feedback | [`superpowers:requesting-code-review`](https://github.com/obra/superpowers/blob/main/skills/requesting-code-review/SKILL.md) |
| You want a broad correctness/readability/architecture/security/performance checklist | [`code-review-and-quality`](https://github.com/addyosmani/agent-skills/blob/main/skills/code-review-and-quality/SKILL.md) |
| You already use OpenClaw's engine-backed pre-commit review workflow | [`autoreview`](https://github.com/openclaw/agent-skills/blob/main/skills/autoreview/SKILL.md) |

## Comparison

The existing skills above cover much of the same review territory. This package is intentionally narrower:

- the reviewer is explicitly read-only and must not run tests;
- the reviewer receives a fresh, no-fork context;
- the implementation owner adjudicates findings and owns validation;
- accepted fixes can be delegated to the existing implementation subagent;
- Minor findings are recorded without blocking;
- `review-loop` and `delegated-code-review` provide bounded and single-pass variants without requiring a larger development methodology.

Use the established alternatives when their broader checklist, engine integration, or full plan-execution workflow is more useful than this small orchestration policy.

## License

MIT-0. See [LICENSE](LICENSE).
