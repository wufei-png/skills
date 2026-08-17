---
name: review-gated-grilling
description: Resolve a plan, decision, or idea through dependency-ordered questions reviewed by fresh, read-only subagents before they reach the user.
disable-model-invocation: true
---

Interview me relentlessly, working through the decision tree in dependency order.

Resolve factual questions from available context or tools. Choose an option directly when the established constraints clearly favor it. Ask only about genuine tradeoffs: present viable options and compare when each fits. Recommend one only when established priorities support it; otherwise explain which scenarios favor each option and let the user choose.

Ask one question at a time and wait for feedback. Treat a user-provided per-turn maximum as a ceiling; batch only tightly related questions whose prerequisites are settled and whose answers do not depend on one another.

Reopen a settled decision when new information invalidates its assumptions.

Before showing a candidate question or permitted batch:

1. Draft its options, tradeoffs, and any supported recommendation.
2. Start one fresh, read-only subagent with the conversation context, or the positive number the user requested. Give multiple reviewers distinct, non-leading perspectives. They must not edit or question the user.
3. Have each independently challenge the question's necessity, option completeness, tradeoffs, and recommendation using evidence, the strongest countercase, and what would change the conclusion.
4. Synthesize evidence rather than votes. Allow one focused exchange for material disagreement, then omit, revise, or ask the question. Disclose only unresolved disagreement relevant to the user's choice.

If the requested reviewers are unavailable, disclose that and ask whether to retry or continue without the gate. Never silently self-review or reduce their number.

When no material decision remains, summarize the design and ask once for confirmation and, when relevant, implementation authorization. Do not modify code before approval.
