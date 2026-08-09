---
name: review-gated-implementation
description: Execute an already-defined code change as dependency-ordered, independently verifiable stages, each gated by verification, review, and commit.
disable-model-invocation: true
---

# Review-Gated Implementation

Implement an already-authorized change as a sequence of small, reviewed commits. Assume the task, scope, repository context, and implementation and commit authority are already established.

Use `$delegated-change-review` for every stage review and the final whole-change review.

## 1. Plan the stages

Use the user's stage limit when provided; otherwise use at most 10 stages. If a sound breakdown requires more, stop and report why rather than forcing unrelated work together.

Record the current commit as `START_BASE`, then split the change into dependency-ordered stages. Each stage must:

- depend only on `START_BASE` and earlier stages;
- deliver one meaningful, independently verifiable result that downstream stages can rely on;
- have acceptance criteria that do not depend on future stages;
- verify the stage contract rather than implementation details;
- be worth independent review and one clean commit that leaves the repository valid.

Prefer vertical slices. Prove uncertain integration paths early. For wide or compatibility-sensitive changes, add the new form, migrate callers in safe batches, then remove the old form.

Use a preparatory-refactor stage only when it creates a materially safer seam for later work. Use an integration-only stage only when independently valid intermediate states are genuinely impossible.

State the plan briefly:

```text
1. <Stage> — delivers <observable result>; depends on <earlier stages or none>; verify with <checks>.
```

If implementation evidence invalidates the plan, revise only unfinished stages and state the change.

## 2. Execute each stage

Work on one stage at a time in the same working tree. Preserve unrelated pre-existing changes and never stage or commit them.

For each stage:

1. Record `STAGE_BASE=$(git rev-parse HEAD)`.
2. Implement only the stage. Run narrow checks while working, then all checks required by its acceptance criteria.
3. Stage the changes with explicit paths. Inspect `git diff --cached --stat` and `git diff --cached`.
4. Use `$delegated-change-review` on the staged diff. Provide the stage goal, acceptance criteria, non-goals, `STAGE_BASE`, and fresh verification evidence. Keep the staged diff current after accepted fixes.
5. Re-run required verification against the final candidate, re-inspect the staged diff, and commit using the repository's convention. Record the commit SHA and any deferred non-blocking finding.

Do not start the next stage until the current stage is committed and passes its required verification. If the stage boundary becomes unsound, split or redesign only unfinished work.

## 3. Run the integration gate

After all stages are committed:

1. Audit the complete change against the task requirements.
2. Run the full applicable test, typecheck, lint, build, integration, and smoke checks.
3. Use `$delegated-change-review` on the complete candidate from `START_BASE`. Provide the requirements and fresh verification evidence.
4. Apply accepted integration fixes, re-run affected and full applicable verification, inspect the final diff, and commit fixes in the minimum number of coherent commits.

Do not claim completion until the integration delegated-change-review has finished and the current `HEAD` passes the full applicable verification.

## Report

Report:

- stages and commit SHAs;
- verification commands and results;
- stage and integration review outcomes;
- deferred non-blocking findings and rationale;
- unverified items, remaining risks, or blockers.
