# Draft Validation

Use this stage when you have access to the image generator that will actually be used.

The goal is not to make the prompt “sound better”. The goal is to find the candidate that obeys the hard visual constraints.

## Validation Loop

1. Build 2 to 3 prompt candidates that preserve the same fidelity anchors.
2. Vary only the phrasing most likely to affect composition or placement.
3. Generate low-cost drafts.
4. Reject any draft that breaks a hard constraint, even if it looks prettier.
5. Run a fast internal QC pass on the best surviving draft.
6. Apply only the 1 to 3 highest-value corrections.

## Hard Constraints To Check First

- asset type
- orientation and crop
- subject count
- exact visible text
- critical accessory
- dominant background relationship

## Repair Rules

- If the backend ignores aspect ratio or subject count, push those into structured config first.
- Do not keep piling on decorative adjectives when the failure is structural.
- Treat prompt tuning as an empirical search problem, not a poetry contest.

## Suggested Return Format

```text
Candidate A:
- kept:
- failed:

Candidate B:
- kept:
- failed:

Winner:
Revised Prompt:
Config:
```
