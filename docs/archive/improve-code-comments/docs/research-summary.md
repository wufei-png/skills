# Research Summary

## Decision

Create a lightweight local skill instead of directly installing or forking an existing one.

No existing candidate was both broad enough and sufficiently constrained for the target behavior: audit comments first, avoid bulk comment churn, and apply focused comment-only changes where comments improve long-term understanding.

## Sources Reviewed

| Source | Useful idea | Decision |
|---|---|---|
| `petekp/claude-code-setup@code-comments` | Co-located comments, plain language, explain why not what | Adopt the philosophy, but reject default file headers for every file |
| `levnikolaevich/claude-code-skills@ln-613-code-comments-auditor` | Audit-first workflow, file:line findings, severity, stale/commented-out detection | Adopt audit-first and severity; do not copy the heavy pipeline |
| `ertugrul-dmr/clean-code-skills@clean-comments` | Remove redundant, stale, metadata, and commented-out comments | Adopt removal rules |
| `gohypergiant/agent-skills@accelint-ts-documentation` | Public API vs internal-code tiers; preserve tool directives | Adopt the tiering; keep language-specific details out of core skill |
| `paulkinlan/co-do@comment-analyzer` | Verify comment accuracy, numeric thresholds, fallback behavior, references, comment rot | Adopt accuracy checks |
| `cxuu/golang-skills@go-documentation` | Public/exported symbols deserve stronger docs; trivial internal code does not | Adopt the boundary, not Go-specific conventions |
| `third774/dotfiles@documenting-code-comments` | Preserve institutional knowledge during refactors | Adopt preserve-before-delete rule |
| `aj-geddes/useful-ai-prompts@code-documentation` | Comprehensive API documentation templates | Do not adopt by default; too likely to over-document business code |
| `pipecat-ai/pipecat@docstring` and PyTorch-style docstring skills | Follow project-specific docstring conventions | Adopt style detection, not their project-specific formats |

## Subagent Findings

The subagent found no better direct-fit comment skill. It recommended self-building a lightweight skill and borrowing broader process ideas:

- from high-spread review/interview skills: ask and inspect before changing;
- from large real-world repos: follow existing project docstring conventions;
- from code-review skills: require evidence, severity, and actionable locations;
- from ADR skills: move long architectural explanation out of inline comments.

## Final Form

The final skill is instruction-only:

- no scripts;
- no reference files for v1;
- one concise `SKILL.md`;
- installable from `improve-code-comments/` and optionally copied into Codex with `install.sh`;
- designed for explicit invocation and implicit use when comment/docstring quality is the task.
