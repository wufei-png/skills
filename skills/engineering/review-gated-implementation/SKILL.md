---
name: review-gated-implementation
description: Implement an authorized change in dependency order, reviewing, checking, and committing each independently valid stage.
disable-model-invocation: true
---

# Review-Gated Implementation

Implement an already-authorized change as a sequence of reviewed commits.

## Plan

Use the user's stage limit when provided; otherwise use at most 10 stages. If a sound breakdown requires more, stop and report why rather than forcing unrelated work together.

Record `START_BASE=$(git rev-parse HEAD)` and the current worktree status so the final review can exclude unrelated pre-existing changes.

Split the change into dependency-ordered stages. Each stage must:

- depend only on earlier stages;
- deliver one meaningful, independently checkable result;
- have acceptance criteria that do not depend on future stages;
- verify the stage contract rather than implementation details;
- be worth independent review and one clean commit that leaves the repository valid.

Prefer vertical slices. Prove uncertain integration paths early. For wide or compatibility-sensitive changes, add the new form, migrate callers in safe batches, then remove the old form.

Use a preparatory-refactor stage only when it creates a materially safer seam for later work. Use an integration-only stage only when independently valid intermediate states are genuinely impossible.

State the plan briefly:

```text
1. <Stage> — delivers <result>; depends on <earlier stages or none>; check with <commands>.
```

If implementation evidence invalidates the plan, revise only unfinished stages.

## Execute

Work one stage at a time in the current tree. Never stage or commit unrelated pre-existing changes.

For each stage:

1. Record `STAGE_BASE=$(git rev-parse HEAD)`, implement only that stage, and run its checks.
2. Stage explicit paths and inspect the staged diff.
3. Use `$delegated-change-review` on that staged diff with the stage goal, acceptance criteria, non-goals, `STAGE_BASE`, and check results.
4. After accepted fixes are applied, restage, rerun the checks, and commit. Run only one review per stage.

After the final stage, check the complete task and run the full applicable checks. Use `$delegated-change-review` once on the task-related change from `START_BASE`, rerun the checks after accepted fixes, and commit any remaining fixes.

## Report

Report the commits, checks and results, review outcomes, deferred findings, and remaining risks or blockers.
