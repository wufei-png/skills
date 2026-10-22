---
name: game-experience-review
description: Review game experience through independent, code-informed player and critic perspectives, plan focused playtests, or compare builds with testable improvements.
disable-model-invocation: true
---

# Game Experience Review

Review what players perceive, decide, do, and receive in return. Recommend improvements; implement only within the user's authorized scope.

## Choose the task

Follow the requested task; default to `review`. Combine tasks only when requested.

| Task | Result |
| --- | --- |
| `review` | Assess a game or representative section and recommend supported improvements. |
| `plan` | Design a focused playtest; use existing material to frame questions, without adding an unsolicited game critique. |
| `compare` | Compare named builds at matched moments and conditions; report unmatched coverage separately. |

Resolve the target, audience, intended experience, and question from the request and current project guidance. Record the source/build or working-tree state, evidence versions, and relevant settings; do not relabel old evidence as current.

## Inspect relevant evidence

Every lens may read relevant code, content, tests, and documentation. Use material entry points and a task scope, not a fixed file whitelist; follow related implementation and evidence as needed. Trace player-visible information, available actions, rules, feedback, and consequences. Distinguish what the reviewer learns from source from what a player can know at that moment. Reading code supports informed analysis, not a claim of an unspoiled first encounter.

Reuse authorized project capture/replay tools and their dependency, window, save-isolation, and output rules. Missing support limits claims; it does not authorize building adapters or installing dependencies. Inspect actual material, not just passing assertions. State whether a claim comes from source, rendered frames, recorded motion, interaction, audio, or human sessions, and limit it accordingly. Code and static images cannot establish control feel; scripted success cannot establish natural discovery; agent behavior is not human response.

## Independent perspectives

Use three complementary, read-only reviewers by default; honor a requested count or focus. Usually choose a player perspective, a critic, and the most relevant specialist.

| Lens | Focus |
| --- | --- |
| First-time player perspective | What a newcomer can infer from presented goals, clues, actions, and recovery. |
| Genre player | Whether the core activity offers interesting decisions, variation, and reasons to continue. |
| Critic | How theme, mechanics, characters, pacing, and presentation create a distinctive experience worth preserving. |
| Narrative and systems | Motivation, knowledge boundaries, causality, costs, agency, and fair consequences. |
| Interaction and accessibility | Legibility, input, feedback, and recovery under the specified settings. |
| Project-specific | The central experience, such as supervisory judgment or mixed-experience co-op participation. |

Read `references/reviewer-packet.md`, fill its fields, and put the complete brief in each dispatch prompt; do not rely on skill inheritance. Start fresh contexts (`fork_turns: "none"` where supported), without parent history, proposed findings, or other reviewer reports. Role names alone do not establish independence. If isolation or a reviewer is unavailable, disclose incomplete independent coverage.

Only for a requested blind exercise, restrict access and record expectations before revealing code, solutions, or later outcomes. If this cannot be maintained, label the result retrospective analysis. Normal player-perspective review remains code-informed.

## Synthesize

Verify cited observations and investigate causes rather than automatically adopting a player's proposed fix. Merge common causes; preserve disagreement and effective choices. Separate observations from interpretations, risks, preferences, and hypotheses. Prioritize experience impact and evidence confidence separately; several agents are not several player samples. Do not force findings, resolve taste by voting, or treat deliberate uncertainty as a defect.

Return a concise result in the user's language, with scope, versions, perspectives, evidence, and limits:

- **Review:** Preserve effective moments; explain supported issues with locators, observation versus interpretation, impact/confidence, smallest useful change, tradeoff, and retest. No supported issue is a valid result.
- **Plan:** Give participants and prior knowledge, tasks, success/failure behavior signals, neutral debrief questions, and outcomes that would change the decision.
- **Compare:** Explain supported differences and unmatched coverage, preserving the same evidence limits for both builds.

End with up to three next actions and unresolved questions. Propose focused human checks where needed; do not fabricate reactions or generalize a short review to the whole game.
