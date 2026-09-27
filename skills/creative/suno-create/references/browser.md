# Browser transport

Follow the route order in the skill. The Playwright runner is the first browser path for packages it can represent and verify. Use Computer Use when the runner is unavailable or lacks a requested control, and the visible Suno page exposes that control with a value that can be read back. If neither path can verify the full package, prepare a manual handoff.

## Attach safely

Prefer an already authenticated browser surface explicitly placed in scope by the user. If none is available, ask the user to open and authenticate Suno; do not collect credentials. Select the intended Create page by its current URL and visible account context rather than a remembered tab index.

Inspect the page before acting. Use semantic labels or fresh element references, and refresh them after navigation or major re-rendering. Close overlays only when they obstruct the authorized task.

## Playwright runner

Invoke [scripts/suno-batch-playwright.mjs](../scripts/suno-batch-playwright.mjs) with Node.js from the installed skill bundle and use the manifest example as the format reference. A Playwright package or CLI must be available to the runtime. The manifest path is resolved from the working directory; package text paths are resolved from the manifest directory. The runner rejects absolute paths, traversal, and links that resolve outside it. It connects to a logged-in Chrome session exposed by CDP, opens a separate Create tab, and uses Playwright locators to set and read back each package. `--prepare-only` fills and verifies the form without clicking Create, then closes its temporary tab. The default path requires CDP at `http://127.0.0.1:9222`; use `--cdp-url` for an already configured endpoint. If the endpoint exposes multiple signed-in Suno contexts, the runner stops; select a single profile. It does not launch a browser or copy authentication state.

The runner supports vocal packages with simple or custom text, model, duration, Male/Female vocal gender, official Max Mode, Weirdness, and Style Influence. It does not support instrumental packages, audio reference upload, Audio Influence, Persona, or Extend. Reconcile the complete package against the manifest before using it; the runner rejects unknown manifest fields but cannot detect a requested value that was left out. Use Computer Use for an unsupported setting only when the live page exposes it and its value can be read back.

The runner turns the official Instrumental control off and reads it back, and treats Duration as the official duration input and slider, Vocal Gender as the Male/Female buttons, and Max Mode as the official Off/On buttons. It refuses to proceed if any selected state is unavailable or ambiguous. A prompt string such as `[Is_MAX_MODE: MAX]` is not a Max Mode setting. The currently observed selection classes are used only as a fallback when ARIA state is absent; if Suno changes those classes, the runner stops until its readback is updated and revalidated.

The runner also re-reads package text and requested sliders before submission. It writes a private, synced ledger before each Create, runs one package at a time, checks for one generation request and two new clip IDs, and records uncertain outcomes as `ambiguous`. Its output contains statuses and clip IDs without echoing song text. `estimatedCredits` and `--max-credits` are compared as declared estimates; the script does not independently price a generation. Verify current Suno pricing for every package first, and do not submit if it is uncertain. Never retry an ambiguous package until it has been reconciled against the Suno library.

If a ledger item is `armed` or `ambiguous`, first check Suno Library/history for a matching result. Only after confirming that no generation was created, run:

```bash
node /path/to/suno-create/scripts/suno-batch-playwright.mjs \
  --manifest batch.json \
  --reconcile-not-submitted package-id \
  --confirm-batch batch-id \
  --max-items 8 \
  --max-credits 80 \
  --ledger .suno-create/batches/run.json
```

Replace `/path/to/suno-create` with the installed skill directory. This records the operator's confirmation; it does not query Suno or prove absence. Use the same batch id and limits as the ledger. Then `--submit --resume` can continue. If the result is still uncertain or a generation exists, do not use this transition.

## Computer Use fallback

Use a visible, user-authorized Suno session when Playwright is unavailable or lacks a requested control. Inspect the current page with the available screenshot or accessibility view, identify controls by their current labels, and refresh observations after navigation or major re-rendering. Set only values in the authorized package, then read each one back before Create. This path can handle audio references, Audio Influence, Persona, or Extend only when the live page exposes the relevant control and the selected value can be verified. If the page cannot verify a requested setting, prepare a manual handoff.

1. Select the requested simple or custom mode.
2. Inspect the model and controls currently offered.
3. Fill only package fields supported by the page.
4. Read every material value back after filling, including title, lyrics or prompt, style, exclusions, instrumental or vocal choices, model, duration, vocal gender, the official Max Mode Off/On control, audio reference, Persona or Extend source, and influence controls when present.
5. Compare the verified form with the package and expected cost.
6. Trigger the uniquely identified Create action once.

Do not mutate the page through unstructured JavaScript when the available browser tool provides inspectable fill and click operations. Do not upload audio unless the package, provenance, and separate upload authorization are explicit.

## Determine the outcome

Treat a visible new generation pair, provider confirmation, or matching new library entries as confirmed. Treat a failure known to occur before the final action as failed-before-submit. Network uncertainty, duplicated events, lost browser control, or an unclear post-click state is ambiguous and must be reconciled before any retry.

If no capable authenticated browser tool is available, return a manual package with field names, values, expected spend, and a final pre-submit checklist. Preparing that package does not authorize the agent to click Create later.
