---
name: suno-create
description: Submit authorized Suno Creates through Playwright or Computer Use, reconcile uncertain outcomes, or prepare a manual package. Use for Suno generation and Create-form execution, not creative exploration or post-generation editing.
disable-model-invocation: true
---

# Suno Create

Submit one or a bounded serial batch of explicitly authorized Suno Creates. Verify requested settings at runtime and stop when a required field or outcome is uncertain.

This skill executes a supplied package; it does not invent an exploration strategy. Use `$suno-music-explorer` when the user wants iterative discovery.

## Required package

Collect a separate package for every requested Create: mode, prompt or lyrics, style, exclusions, title, instrumental state, model, duration, vocal gender, official Max Mode setting, requested influence controls, estimated credits, and any audio reference, Persona, or Extend source. Record the audio source and provenance when upload is requested. Duration, vocal gender, and Max Mode must be explicit; never infer them from prose or a prompt tag. Never carry values forward from an unrelated package.

Before submission, obtain direct authorization or use the remaining grant from a calling workflow. Confirm that it covers the exact package or batch, maximum Create count, spend bound, and current provider cost. If price, candidate count, model, or supported fields cannot be verified, do not spend.

## Choose the transport

Use the first path that can set and read back every requested field:

1. An authenticated Suno tab controlled by [CUA Playwright](references/browser.md#cua-advanced-form) (`tab.playwright`), when available.
2. The [Playwright CLI runner](references/browser.md#playwright-runner) for a supported vocal package or bounded serial batch with an authenticated persistent profile or a compatible single-context CDP endpoint.
3. [Computer Use](references/browser.md#computer-use-fallback) when the logged-in page exposes the needed controls and their selected values can be verified.
4. A reviewed manual package when the complete request cannot be verified through an available browser path.

The [macOS CUA adapter](scripts/suno-cua-batch.mjs) prepares and reads back Advanced v6 vocal and instrumental packages. `prepare()` and `read()` stop before Create. The caller enforces the approved count and spend, durably arms a ledger, clicks Create once, and reconciles candidate IDs and spend.

If a path proves incapable before Create, select the next capable path. If Create was attempted or its outcome is ambiguous, stop and reconcile before changing paths.

## Submit serially

1. Identify the in-scope Create page by its current URL and visible account context. Inspect account readiness, cost, model options, and controls before changing the form. For direct browser interaction, use visible semantic labels or fresh element references after navigation or re-rendering. Dismiss only overlays that block the task.
2. Normalize slider values only from observed transport schemas. Do not assume that UI and CLI scales match.
3. For every package, set and read back title, prompt or lyrics, style, exclusions, instrumental or vocal choice, model, duration, vocal gender, official Max Mode, and each requested influence or reference control.
4. Immediately before each final action, re-check the authorization and expected spend.
5. Trigger Create exactly once per authorized package, serially.
6. Capture the submission state, returned candidate IDs or URLs, observed spend when available, and enough package identity to reconcile every attempt.

Do not download generated media unless separately requested. A Create authorization does not authorize paid formats, publication, sharing, deletion, account changes, or reuse of uploaded material.

## Reconcile before retrying

Classify the attempt as `confirmed`, `failed-before-submit`, or `ambiguous`.

- `confirmed`: require a visible new generation pair, provider confirmation, or matching new library entries. Record and return the candidate identifiers.
- `failed-before-submit`: a failure known to precede Create allows a different capable transport while the original authorization remains unspent.
- `ambiguous`: stop. Check the Suno library, account history, browser result, and ledger for a matching title, timestamp, or package fingerprint. Never resubmit until non-submission is confirmed.

For a CLI ledger in `armed` or `ambiguous`, use the [runner's recovery procedure](references/browser.md#playwright-runner) only after confirming that no matching generation was created. If the result remains uncertain, ask the user.

CAPTCHA, expired login, inaccessible controls, unexpected price changes, or inability to verify the final action require user intervention. Do not loop through retries.

## Return

Report the transport, package fingerprint or concise summary, outcome classification, candidate identifiers or manual handoff, observed spend if known, and any unresolved uncertainty. Do not claim that generated audio is good without listening evidence.

For a manual handoff, provide field values, expected spend when known, and a pre-submit checklist, including any sign-in prerequisite.
