---
name: grilling
description: Resolve a plan, decision, or idea through dependency-ordered questions about genuine tradeoffs, then confirm the design before implementation.
disable-model-invocation: true
---

Work through the decision tree in dependency order.

Resolve factual questions from available context or tools. Choose an option directly when the established constraints clearly favor it. Ask only about genuine tradeoffs. Explain when each viable option fits. Recommend one when established priorities support it. Otherwise, let the user choose.

Batch closely related questions whose prerequisites are settled and whose answers do not depend on one another. Ask one ready question if no batch fits. Respect any per-turn limit the user sets. Wait for answers before choosing the next round.

Reopen a settled decision when new information invalidates its assumptions.

When no material decision remains, summarize the design and ask once for confirmation and, when relevant, implementation authorization. Do not modify code before approval.
