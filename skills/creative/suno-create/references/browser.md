# Browser transport

Use an available browser automation capability that can control a user-authorized, logged-in Suno session. Do not require a particular CLI, operating system, browser profile path, debug port, or pre-existing tab name.

## Attach safely

Prefer an already authenticated browser surface explicitly placed in scope by the user. If none is available, ask the user to open and authenticate Suno; do not collect credentials. Select the intended Create page by its current URL and visible account context rather than a remembered tab index.

Inspect the page before acting. Use semantic labels or fresh element references, and refresh them after navigation or major re-rendering. Close overlays only when they obstruct the authorized task.

## Fill and verify

1. Select the requested simple or custom mode.
2. Inspect the model and controls currently offered.
3. Fill only package fields supported by the page.
4. Read every material value back after filling, including title, lyrics or prompt, style, exclusions, instrumental or vocal choices, model, duration, and influence controls when present.
5. Compare the verified form with the package and expected cost.
6. Trigger the uniquely identified Create action once.

Do not mutate the page through unstructured JavaScript when the available browser tool provides inspectable fill and click operations. Do not upload audio unless the package, provenance, and separate upload authorization are explicit.

## Determine the outcome

Treat a visible new generation pair, provider confirmation, or matching new library entries as confirmed. Treat a failure known to occur before the final action as failed-before-submit. Network uncertainty, duplicated events, lost browser control, or an unclear post-click state is ambiguous and must be reconciled before any retry.

If no capable authenticated browser tool is available, return a manual package with field names, values, expected spend, and a final pre-submit checklist. Preparing that package does not authorize the agent to click Create later.
