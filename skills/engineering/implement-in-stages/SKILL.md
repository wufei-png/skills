---
name: implement-in-stages
description: Implement an authorized change in dependency order, checking and committing each independently valid stage.
disable-model-invocation: true
---

# Implement in Stages

Implement an already-authorized change as a sequence of small commits.

## Plan

Use the user's stage limit when provided; otherwise use at most 10 stages. If a sound breakdown requires more, stop and report why rather than forcing unrelated work together.

Split the change into dependency-ordered stages. Each stage must:

- depend only on earlier stages;
- deliver one meaningful, independently checkable result;
- have acceptance criteria that do not depend on future stages;
- verify the stage contract rather than implementation details;
- be worth one clean commit that leaves the repository valid.

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

1. Implement only that stage and run its checks.
2. Stage explicit paths and inspect the staged diff.
3. Commit once the checks pass.

After the final stage, check the complete change against the task, run the full applicable checks, and commit any resulting verified fixes.

## Report

Report the commits, checks and results, and remaining risks or blockers.
