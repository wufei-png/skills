# Draft Validation

Use this guide to assess supplied drafts or to test a prompt with the intended generator when authorized.

The goal is not to make the prompt “sound better”. The goal is to find the candidate that obeys the hard visual constraints.

## Validation Loop

1. Inspect supplied drafts or generate the requested drafts. Keep fidelity anchors and relevant settings consistent when testing prompt variants.
2. For a controlled test, vary the phrasing most likely to affect the visual issue. Use previews when they can show the result clearly.
3. Rule out drafts that break hard constraints. Check the strongest viable draft for remaining mismatches and correct the ones that matter most.

## Check the requested constraints first

Choose constraints from the request and the intended role of each reference. Examples include:

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

## Report

Say which constraints held or failed. When comparing drafts, identify the strongest one if any satisfies the hard constraints. Include the refined prompt and relevant settings when needed.
