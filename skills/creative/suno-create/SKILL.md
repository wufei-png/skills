---
name: suno-create
description: Submit one authorized Suno Create through the best available transport, reconcile uncertain outcomes, or prepare a manual submission package. Use for Suno generation and Create-form execution, not creative exploration or post-generation editing.
disable-model-invocation: true
---

# Suno Create

Submit exactly one authorized Suno Create. Prefer reliable structured capabilities, verify mutable provider details at runtime, and fail closed when the outcome is uncertain.

This skill executes a supplied package; it does not invent an exploration strategy. Use `$suno-music-explorer` when the user wants iterative discovery.

## Required package

Collect only fields relevant to this submission: mode, prompt or lyrics, style, exclusions, title, instrumental state, model, supported controls, and optional artifact references. Distinguish required values from preferences. Never carry values forward from an unrelated package.

Before submission, obtain either direct authorization for this Create or the remaining bounded grant from a calling workflow. Confirm that the grant still covers the current provider cost. If price, candidate count, model, or supported fields cannot be verified, disclose the uncertainty before spending.

## Choose the transport

Use the first capable path:

1. A working Suno-specific structured adapter such as OpenCLI.
2. An available browser automation tool attached to a user-authorized, logged-in Suno session.
3. A reviewed manual submission package for the user.

Choose by current capability, not by operating system or remembered UI. A field unsupported by the adapter is a reason to choose the browser before submission. An adapter failure after an attempted submission is not permission to retry in the browser.

For OpenCLI capability discovery and recovery, read [references/opencli.md](references/opencli.md). For browser execution, read [references/browser.md](references/browser.md). Read only the reference for the selected path.

## Submit once

1. Inspect current account readiness, cost, model options, and relevant controls without mutating them.
2. Normalize slider values only from observed transport schemas. Do not assume that UI and CLI scales match.
3. Fill the package and verify every material field after filling.
4. Immediately before the final action, re-check the authorization and expected spend.
5. Trigger Create exactly once.
6. Capture the submission state, returned candidate IDs or URLs, observed spend when available, and enough package identity to reconcile the attempt.

Do not download generated media unless separately requested. A Create authorization does not authorize paid formats, publication, sharing, deletion, account changes, or reuse of uploaded material.

## Reconcile before retrying

Classify the attempt as `confirmed`, `failed-before-submit`, or `ambiguous`.

- `confirmed`: record the candidate identifiers and return them.
- `failed-before-submit`: a different capable transport may be selected while the original authorization remains unspent.
- `ambiguous`: stop. Check the Suno library, account history, adapter output, and calling ledger for a matching title, timestamp, or package fingerprint. Never resubmit until non-submission is confirmed.

CAPTCHA, expired login, inaccessible controls, unexpected price changes, or inability to verify the final action require user intervention. Do not loop through retries.

## Return

Report the transport, package fingerprint or concise summary, outcome classification, candidate identifiers or manual handoff, observed spend if known, and any unresolved uncertainty. Do not claim that generated audio is good without listening evidence.
