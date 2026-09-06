---
name: consensus-review-loop
description: Run a bounded review-and-fix loop with evidence-led subagent consensus.
license: MIT-0
disable-model-invocation: true
---

# Consensus Review Loop

Use the user's positive round limit, or `3` by default.

For each round:

1. Start one fresh subagent with `fork_turns: "none"` and `$review-agent` skill. Give it the current review target, goal, acceptance criteria, comparison base, and check results. It may inspect relevant code, tests, and call sites but must only review.
2. Wait for its conclusion without rushing a healthy reviewer. Verify every P0-P3 finding yourself. Record rejected findings with the reason. Classify material disagreements as disputed.
3. For each material dispute, state the provisional disposition, disputed premise, and evidence to the original reviewer. Allow at most two exchange rounds; each response must maintain, revise, or withdraw the finding with evidence.
4. If the dispute remains, start one fresh, read-only tie-breaker with neutral context and both evidence positions. If it still cannot resolve the dispute, ask the user to adjudicate; do not apply or silently reject the finding.
5. Apply accepted findings one at a time through the implementation owner when one exists, or fix them yourself, then rerun the relevant checks after each fix. Repeat with another fresh reviewer only when a P0-P2 finding was accepted and rounds remain. After the last allowed round, report that boundary as a residual risk.

Summarize each round's findings, decisions, fixes, verification, unverified items, and risks.
