---
name: worktree-triage
description: Infer the purpose of unexplained Git changes, recommend what to keep, fix, or discard, and make verified local commits when authorized.
disable-model-invocation: true
---

# Worktree Triage

Default to read-only inspection that leaves files, the index, and refs untouched. If the user asks to complete the work directly, carry out the supported, verifiable batches in the same turn. Respect any narrower scope the user gives.

## Inspect the working tree

- Identify the repository, worktree, branch, and HEAD. Check for conflicts or an in-progress Git operation before planning writes.
- Prefix inspection with `git --no-optional-locks -c diff.autoRefreshIndex=false` to keep the index untouched. Inventory paths with `status --short --branch --untracked-files=all`. When ignored files matter, use scoped `status --short --ignored=matching -- <paths>` and confirm rules with `check-ignore -v`.
- Use paths and metadata only for files suspected to contain secrets. For other relevant paths, inspect staged and unstaged diffs separately with `--no-ext-diff --no-textconv`, and read relevant untracked files directly.
- Use the affected code, callers, tests, docs, and relevant Git history to establish what the changes do and why they might exist. Consult available handoffs or session records when they can resolve a question. Continue from repository evidence when the original session is missing.

## Decide what belongs together

Group files or diff hunks by purpose. Keep a fix with the tests, documentation, or lockfile changes it needs. For each group, identify the observed effect, likely intent, supporting or conflicting evidence, and the smallest meaningful check. Compare with the applicable branch or contract when the change may be obsolete or already integrated.

Recommend committing each group as is, committing it after a minimal repair, discarding it, or leaving it in place. A batch is ready when its purpose and current value are supported, its boundaries are clear, and it can be verified independently of pending changes. Leave uncertain changes in place, including staged content. In read-only mode, report the assessment and proposed checks.

## Execute authorized batches

1. Recheck HEAD, the worktree, and the index before writing. Resolve uncertainty about the commit branch or an active Git operation before committing there. Make a minimal repair only when the request permits it and the current contract makes the correction clear.
2. Record each candidate path's original index state before staging. For whole paths without unrelated staging on those paths, `git --literal-pathspecs commit --only -- <paths>` takes the working-tree versions and excludes staging elsewhere. For partial files or overlaps, proceed only when you can verify the commit and preserve the remaining staged and unstaged changes. Defer batches you cannot separate safely and continue with independent ones.
3. Stage explicit paths or hunks and inspect the exact candidate diff against its parent. For a path-limited commit, confirm each path's full contents match the staged candidate. Run checks in isolation when pending edits could affect the result. Recheck the candidate and its parent before committing, then verify the commit and remaining changes. If a batch stops before commit, restore only your staging where the index entries still match what you staged. Continue with independent batches.
4. Verify the scope and recoverability of discards, then apply them only to paths or hunks the user has clearly authorized. Treat branch switching and remote operations as separate requests.

Report each completed commit hash, its scope and check results, and the remaining changes. Ask concrete questions about the pending decisions after completing the independent batches.
