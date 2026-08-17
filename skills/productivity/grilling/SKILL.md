---
name: grilling
description: Resolve a plan, decision, or idea through dependency-ordered questions about genuine tradeoffs, then confirm the design before implementation.
disable-model-invocation: true
---

Interview me relentlessly, working through the decision tree in dependency order.

Resolve factual questions from available context or tools. Choose an option directly when the established constraints clearly favor it. Ask only about genuine tradeoffs: present viable options and compare when each fits. Recommend one only when established priorities support it; otherwise explain which scenarios favor each option and let the user choose.

Ask one question at a time and wait for feedback. Treat a user-provided per-turn maximum as a ceiling; batch only tightly related questions whose prerequisites are settled and whose answers do not depend on one another.

Reopen a settled decision when new information invalidates its assumptions.

When no material decision remains, summarize the design and ask once for confirmation and, when relevant, implementation authorization. Do not modify code before approval.
