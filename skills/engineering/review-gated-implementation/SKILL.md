---
name: review-gated-implementation
description: Implement an already-defined code change as dependency-ordered, independently checkable stages, reviewing and committing each before continuing.
disable-model-invocation: true
---

# Review-Gated Implementation

Implement an already-authorized change as a sequence of small commits.

## Plan the stages

Use the user's stage limit when provided; otherwise use at most 10 stages. If a sound breakdown requires more, stop and report why rather than forcing unrelated work together.

Record the current commit as `START_BASE` for the final review.

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
1. <Stage> — delivers <observable result>; depends on <earlier stages or none>; check with <commands>.
```

If implementation evidence invalidates the plan, revise only unfinished stages.

## Execute

Work one stage at a time in the current tree. Never stage or commit unrelated pre-existing changes.

For each stage:

1. Record `STAGE_BASE=$(git rev-parse HEAD)`.
2. Implement only that stage and run its checks.
3. Stage explicit paths and inspect the staged diff.
4. Use `$delegated-change-review` on the staged diff with the stage goal, acceptance criteria, non-goals, `STAGE_BASE`, and check results.
5. After accepted fixes, restage, re-run those checks, then commit and continue. Run only one review per stage.

After the final stage:

1. Confirm the complete change against the task requirements and run the full applicable checks.
2. Use `$delegated-change-review` on the complete candidate from `START_BASE` with the requirements and check results.
3. Apply needed fixes, re-run the full applicable checks, then commit any remaining fixes.

## Report

Report the commits, checks and results, review outcomes, deferred findings, and any remaining risks or blockers.
