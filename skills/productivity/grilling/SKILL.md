---
name: grilling
description: Interview the user relentlessly about a plan, decision, or idea.
disable-model-invocation: true
---

Interview me relentlessly, working through the decision tree in dependency order.

When one option is clearly preferable under the established constraints, choose it without discussion. Ask only about decisions that involve genuine tradeoffs; for each, list the viable options, compare their tradeoffs, and recommend one.

Ask one question at a time and wait for feedback. If the user gives a per-turn maximum, treat it as a ceiling: ask multiple questions only when they are tightly related, their prerequisites are settled, and none depends on another's answer.

Revisit settled decisions when new answers invalidate their assumptions.

If a factual question can be resolved from available context or tools, resolve it yourself instead of asking the user.

When no material decision remains unresolved, summarize the design and ask once to confirm it and, when in scope, authorize its implementation; do not modify code until approved.
