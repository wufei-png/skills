---
name: consensus-change-review
description: Resolve disputed review findings through bounded subagent exchange before applying fixes.
disable-model-invocation: true
---

# Consensus Change Review

1. Start one fresh subagent with `fork_turns: "none"` and `$review-agent` skill. Give it the review target, goal, acceptance criteria, comparison base, and check results. It may inspect relevant code, tests, and call sites but must only review.
2. Wait for its conclusion without rushing a healthy reviewer.
3. Verify every P0-P3 finding yourself. Record rejected findings with the reason. Classify material disagreements as disputed. If none are accepted and none are disputed, skip to the summary.
4. For each material dispute, state the provisional disposition, disputed premise, and evidence to the original reviewer. Allow at most two exchange rounds; each response must maintain, revise, or withdraw the finding with evidence.
5. If the dispute remains, start one fresh, read-only tie-breaker with neutral context and both positions. If it still cannot resolve the dispute, ask the user to adjudicate; do not apply or silently reject the finding.
6. Apply accepted findings one at a time through the implementation owner when one exists, or fix them yourself, then rerun the relevant checks after each fix.
7. Summarize the change, findings and decisions, fixes, verification, unverified items, and remaining risks.
