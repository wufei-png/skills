# Browser transport

## Playwright runner

Invoke [scripts/suno-batch-playwright.mjs](../scripts/suno-batch-playwright.mjs) with Node.js from the installed skill bundle and validate the complete manifest against the [example format](./batch-manifest.example.json). A Playwright package or CLI is required. Install its managed Chrome for Testing browser once with `playwright-cli install-browser chromium`. The manifest path is resolved from the working directory; package text paths are resolved from the manifest directory. The runner rejects absolute paths, traversal, and links that resolve outside it. By default, it launches a dedicated persistent browser profile at `~/.suno-batch-playwright/chrome-profile`, opens a separate Create tab, and uses Playwright locators to set and read back each package. Profile files remain outside the repository and the profile directory is restricted to the current user on macOS/Linux. Run `--setup-profile` once to open this isolated profile at Suno; sign in manually in Chrome for Testing, return to the terminal, and press Enter. The runner verifies the signed-in credits control and closes the browser, preserving the session for later runs. The default profile is separate from the regular Chrome profile and receives no copied login data. Any `--profile-dir` value must also be a dedicated directory. The runner does not open an HTTP debugging port. `--prepare-only` fills and verifies the form without clicking Create, then closes its temporary tab.

For an existing, user-authorized CDP endpoint, pass `--cdp-url <endpoint>` instead of using the persistent profile. If that endpoint exposes multiple signed-in Suno contexts, the runner stops; select a single profile. Do not expose the default Chrome profile over CDP. Chrome 136 and later require remote-debugging switches to use a non-default data directory; Chrome recommends Chrome for Testing for browser automation.

The runner supports vocal packages with simple or custom text, model, duration, Male/Female vocal gender, official Max Mode, Weirdness, and Style Influence. It does not support instrumental packages, audio reference upload, Audio Influence, Persona, or Extend. Reconcile the complete package against the manifest before using it; the runner rejects unknown manifest fields but cannot detect a requested value that was left out. Use Computer Use for an unsupported setting only when the live page exposes it and its value can be read back.

The runner verifies vocal state from the official Instrumental control when present, or from nonempty lyrics in Advanced mode. Set `durationMode` to `Auto` with `durationSeconds` 0, or to `Custom` with positive whole seconds. When `durationMode` is omitted, 0 means Auto and positive seconds mean Custom. Custom duration is verified through the official input and slider; Auto is verified through its selected button and the absence of Custom duration controls. Vocal Gender uses the Male/Female buttons and Max Mode uses the official Off/On buttons. The runner refuses to proceed if any selected state is unavailable or ambiguous. A prompt string such as `[Is_MAX_MODE: MAX]` is not a Max Mode setting. The currently observed selection classes are used only as a fallback when ARIA state is absent; if Suno changes those classes, the runner stops until its readback is updated and revalidated.

For an authorized `--submit`, pass an exact `--confirm-batch` value, explicit `--max-items` and `--max-credits`, and a `--ledger` path. The runner re-reads package text and sliders, writes a private, synced ledger before each Create, runs one package at a time, checks for one generation request and two new clip IDs, and records uncertain outcomes as `ambiguous`. Its output contains statuses and clip IDs. `estimatedCredits` and `--max-credits` are declared estimates, so verify the current cost for each package before submission.

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

## CUA Advanced form

- Verify instrumental state from empty Lyrics and an unselected Vocal Gender (`null`). For this macOS adapter, clear the editor with `Meta+A` and `Backspace`, fill any nonempty lyrics, and verify the resulting DOM paragraphs joined by single newlines.
- Use visible controls outside `aria-hidden` sections. Prefer explicit selected state over class-based fallback. Read back Weirdness and Style Influence on the 0–100 scale, Variety on the 0–4 scale with value 0, and Personalize Off and Max Mode using the official controls. Select a capable route for any requested reference or mode the adapter cannot verify.
- For Custom duration, set `durationSeconds`, check it against the live range, and confirm that the time input and slider agree. For Auto, use the Duration reset control if the Auto button is absent, then verify Auto is selected and the Custom controls are gone.
