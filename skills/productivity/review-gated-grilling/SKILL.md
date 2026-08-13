---
name: review-gated-grilling
description: Interview the user about a plan, decision, or idea after subagents review each candidate question and recommendation. Use only when explicitly invoked for multi-agent decision clarification.
disable-model-invocation: true
---

Interview me relentlessly, working through the decision tree in dependency order.

When one option is clearly preferable under the established constraints, choose it without discussion. Ask only about decisions that involve genuine tradeoffs; for each, list the viable options and compare their tradeoffs. Recommend one only when the established constraints and priorities support it; otherwise explain which scenarios favor each option and let the user choose.

Ask one question at a time and wait for feedback. If the user gives a per-turn maximum, treat it as a ceiling: ask multiple questions only when they are tightly related, their prerequisites are settled, and none depends on another's answer.

Revisit settled decisions when new answers invalidate their assumptions.

If a factual question can be resolved from available context or tools, resolve it yourself instead of asking the user.

Once a question or permitted batch remains, draft its options, tradeoffs, and any recommendation. Before showing it to me:

1. Start one fresh, read-only subagent with the conversation context, or the positive number I request. Give multiple reviewers distinct, non-leading perspectives. They must neither edit nor question me.
2. Have each independently challenge the question's necessity, option completeness, tradeoffs, and recommendation, citing evidence, omissions, the strongest countercase, and what would change the conclusion.
3. Synthesize evidence, not votes. On material disagreement, allow one focused exchange; then omit, revise, or ask. Disclose only unresolved disagreement material to my choice.

If the requested reviewers are unavailable, disclose it and ask whether to retry or continue without the gate; never silently self-review or reduce their number.

When no material decision remains unresolved, summarize the design and ask once to confirm it and, when in scope, authorize its implementation; do not modify code until approved.
