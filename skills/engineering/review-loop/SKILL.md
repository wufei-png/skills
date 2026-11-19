---
name: review-loop
description: Run a bounded code-review and fix loop with fresh, read-only reviewer subagents.
license: MIT-0
disable-model-invocation: true
---

# Review Loop

Use the user's positive round limit, or `3` by default.

For each round:

1. Start one fresh subagent with `fork_turns: "none"` and `$review-agent` skill. Give it the current review target, goal, acceptance criteria, comparison base, and check results. It may inspect relevant code, tests, and call sites but must only review.
   Ask the reviewer to consult the `karpathy-guidelines` skill when available.
2. Wait for its conclusion without rushing a healthy reviewer. Verify every P0-P3 finding yourself. Record rejected findings with the reason.
3. Apply accepted findings one at a time through the implementation owner when one exists, or fix them yourself, then rerun the relevant checks after each fix.
4. Repeat with another fresh reviewer only if a P0-P2 finding was accepted and rounds remain. Report the round limit as a residual risk only if it prevents that follow-up review, naming the fixes still awaiting review.

## Finalize

Summarize each round's findings and decisions, fixes, verification, unverified items, and remaining risks.
