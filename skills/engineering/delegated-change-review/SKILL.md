---
name: delegated-change-review
description: Run one fresh, read-only code-review subagent, adjudicate its findings, apply accepted fixes, and verify them.
disable-model-invocation: true
---

# Delegated Change Review

1. Start one fresh subagent with `fork_turns: "none"` and `$review-agent` skill. Give it the review target, goal, acceptance criteria, comparison base, and check results. It may inspect relevant code, tests, and call sites but must only review.
2. Wait for its conclusion without rushing a healthy reviewer.
3. Verify every P0-P3 finding yourself. Record rejected findings with the reason. If none are accepted, skip to the summary. Otherwise apply accepted findings one at a time through the implementation owner when one exists, or fix them yourself, then rerun the relevant checks after each fix.
4. Summarize the change, findings and decisions, fixes, verification, unverified items, and remaining risks.
