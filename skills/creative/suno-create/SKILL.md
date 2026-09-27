---
name: suno-create
description: Submit authorized Suno Creates through OpenCLI, Playwright, or Computer Use, reconcile uncertain outcomes, or prepare a manual package. Use for Suno generation and Create-form execution, not creative exploration or post-generation editing.
disable-model-invocation: true
---

# Suno Create

Submit one or a bounded serial batch of explicitly authorized Suno Creates. Verify requested settings at runtime and stop when a required field or outcome is uncertain.

This skill executes a supplied package; it does not invent an exploration strategy. Use `$suno-music-explorer` when the user wants iterative discovery.

## Required package

Collect a separate package for every requested Create: mode, prompt or lyrics, style, exclusions, title, instrumental state, model, duration, vocal gender, official Max Mode setting, requested influence controls, estimated credits, and any audio reference, Persona, or Extend source. Record the audio source and provenance when upload is requested. Duration, vocal gender, and Max Mode must be explicit; never infer them from prose or a prompt tag. Never carry values forward from an unrelated package.

Before submission, obtain direct authorization or use the remaining bounded grant from a calling workflow. Confirm that it covers the exact package set, maximum Create count, and current provider cost. If price, candidate count, model, or supported fields cannot be verified, do not spend.

## Choose the transport

Use the first path that can set and read back every requested field:

1. OpenCLI, if the installed Suno adapter supports the complete package and can verify it before Create.
2. The Playwright runner for a supported vocal package or bounded serial batch.
3. Computer Use for controls the runner does not support, when the logged-in Suno page exposes those controls and their selected values can be verified.
4. A reviewed manual package when no available path can verify the complete request.

The Playwright runner does not support instrumental packages, audio reference uploads, Audio Influence, Persona, or Extend. Use Computer Use for these only when the corresponding controls are available and can be read back. If a path proves incapable before Create, select the next capable path. If Create was attempted or its outcome is ambiguous, stop and reconcile before changing paths.

For OpenCLI capability discovery and recovery, read [references/opencli.md](references/opencli.md). For browser setup, supported fields, and recovery, read [references/browser.md](references/browser.md). Read only the reference for the selected path.

For Playwright, use [scripts/suno-batch-playwright.mjs](scripts/suno-batch-playwright.mjs) and the manifest format in [references/batch-manifest.example.json](references/batch-manifest.example.json). Validate the complete manifest first. A submission requires a logged-in Chrome session exposed through CDP, an exact `--confirm-batch` match, explicit `--max-items` and `--max-credits`, and a ledger path. The runner submits serially, never downloads audio, never retries an uncertain submission, and stops when a package is ambiguous. Do not pass `--submit` unless the authorization covers that exact package set and spend bound.

## Submit serially

1. Inspect current account readiness, cost, model options, and relevant controls without mutating them.
2. Normalize slider values only from observed transport schemas. Do not assume that UI and CLI scales match.
3. For every package, set and read back title, prompt or lyrics, style, exclusions, instrumental or vocal choice, model, duration, vocal gender, official Max Mode, and each requested influence or reference control.
4. Immediately before each final action, re-check the authorization and expected spend.
5. Trigger Create exactly once per authorized package, serially.
6. Capture the submission state, returned candidate IDs or URLs, observed spend when available, and enough package identity to reconcile every attempt.

Do not download generated media unless separately requested. A Create authorization does not authorize paid formats, publication, sharing, deletion, account changes, or reuse of uploaded material.

## Reconcile before retrying

Classify the attempt as `confirmed`, `failed-before-submit`, or `ambiguous`.

- `confirmed`: record the candidate identifiers and return them.
- `failed-before-submit`: a different capable transport may be selected while the original authorization remains unspent.
- `ambiguous`: stop. Check the Suno library, account history, adapter or browser result, and calling ledger for a matching title, timestamp, or package fingerprint. Never resubmit until non-submission is confirmed.

For a runner ledger in `armed` or `ambiguous`, use `--reconcile-not-submitted <package-id>` only after confirming in Suno Library/history that no matching generation was created. Run it with the same manifest, ledger, batch confirmation, and limits; it writes an operator-confirmed reconciliation record before `--resume` can retry the package. The command does not inspect Suno or prove absence itself. If the result remains uncertain, stop and ask the user.

CAPTCHA, expired login, inaccessible controls, unexpected price changes, or inability to verify the final action require user intervention. Do not loop through retries.

## Return

Report the transport, package fingerprint or concise summary, outcome classification, candidate identifiers or manual handoff, observed spend if known, and any unresolved uncertainty. Do not claim that generated audio is good without listening evidence.
