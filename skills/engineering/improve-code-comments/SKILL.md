---
name: improve-code-comments
description: Audit or improve code comments and docstrings without changing executable logic. Use for stale, misleading, redundant, missing, low-value, or AI-sounding comments and TODO/FIXME/HACK notes.
disable-model-invocation: true
---

# Improve Code Comments

Improve comments with the smallest durable change. Edit comments and docstrings only; do not change executable logic, tests, configuration, or external documentation.

## Scope and Workflow

1. Read local guidance, nearby comment style, lint rules, and generated or vendored paths before judging comments.
2. Use paths, directories, or a Pull Request named by the user. For a current-task cleanup, use files recorded as created or edited during that task; do not treat every pre-existing dirty file as authorized scope. For a broad request, audit first and let the user choose targets. If neither the user nor the task establishes a candidate set, ask for one.
3. Read each in-scope comment with the code it describes. Verify factual claims against definitions, call paths, tests, and external contracts when needed.
4. Decide whether to keep, remove, rewrite, or report the comment before editing. Inspect the full confirmed scope before consolidating duplicated rationale.
5. Review only the changes made by this pass and confirm that they are comment-only. Run the narrow formatter or check required for comment syntax or generated documentation.

## What To Change

Use this order:

1. **Remove** comments that are stale, misleading, redundant, commented-out code, author or change-history notes, abandoned alternatives, untracked plans, or text that only lists current callers or describes another module's internals.
2. **Update** comments that contain useful context but no longer match current behavior.
3. **Rewrite** useful comments in short, direct language. Remove prompt or review history, before-state narration, persuasion, metaphors, and vague AI-style wording. Keep precise domain terms.
4. **Add** comments only for hidden intent: business rules, non-obvious constraints, edge cases, performance or security tradeoffs, workaround reasons, lifecycle requirements, surprising return values, or public API contracts.
5. **Recommend a non-comment fix** when a name, test, type, function boundary, ADR, or design document should carry the knowledge. Leave the comment in place until that knowledge has a durable home.

## Quality Rules

- Explain information that the code does not already make clear, especially why an order, default, exception, or workaround exists.
- Match the project's language and style. Do not impose Simple English, a docstring format, file headers, or one-line comments when local conventions require something else.
- Keep public or exported API documentation complete enough for callers. Internal comments should add context that names and types cannot carry.
- Preserve copyright and license notices, tool directives, compiler or formatter controls, coverage pragmas, doctest syntax, generated-code markers, and genuine security warnings exactly unless the user explicitly asks to change that item and the project permits it.
- Put one design reason at the place that owns the decision. When code is intentionally duplicated, keep each copy understandable on its own.
- Preserve accurate institutional knowledge. Do not delete a useful reason merely because its wording needs work.
- Do not use word blacklists, comment counts, or density targets as automatic edit rules. Judge words in context and each comment by its value.
- Keep TODO/FIXME/HACK comments only when they name a concrete action and give a blocker, issue or specification reference, owner, or removal condition.

## Accuracy Checks

Check claims about thresholds, units, ordering, fallbacks, errors, retries, null and empty cases, flags, side effects, public signatures, external-system behavior, and tool-marker semantics. Report a factual error separately from a wording improvement.

## Severity

- **Critical:** the comment could cause unsafe use, data loss, a security misunderstanding, or a false public contract.
- **High:** the comment is stale or misleading, contains commented-out code, or gives the wrong contract for a public API.
- **Medium:** the comment is redundant or vague, misses non-obvious rationale, or contains a weak TODO/FIXME/HACK note.
- **Low:** wording, placement, or optional clarity improvement.

## Output

For audits, return a summary followed by must-fix findings, useful improvements, recommended removals, and good existing patterns. Give each finding a `file:line`, severity, evidence, and proposed action.

For edits, summarize changed paths and validation. List factually wrong comments and non-comment fixes that remain separately.
