# OpenCLI transport

Use this path only when `opencli` is installed, its Suno adapter is available, and it supports every required package field.

## Discover current behavior

Inspect instead of relying on examples:

```bash
opencli --version
opencli doctor
opencli suno --help -f yaml
opencli suno generate --help -f yaml
opencli suno status -f json
```

The installed adapter defines the current model default, slider scales, download behavior, timeouts, session options, and output schema. Use explicit package values when supplied; do not silently substitute remembered defaults.

A green `doctor` proves the base browser bridge, not the Suno adapter's write readiness. If the read-only Suno status check fails, do not attempt Create through that adapter; choose browser or manual fallback before spending.

## Submit

Build the command from the discovered schema. A typical custom-mode shape is:

```bash
opencli suno generate \
  --lyrics "$LYRICS" \
  --tags "$STYLE" \
  --negative-tags "$EXCLUDE" \
  --title "$TITLE" \
  --model "$MODEL" \
  --weirdness "$WEIRDNESS" \
  --style-weight "$STYLE_WEIGHT" \
  --sd true \
  -f json
```

Add `--instrumental` only when the package requires it. For simple mode, use the positional description and omit custom lyrics. Use the current adapter's no-download option; verify its meaning rather than copying the example blindly.

Record the exact command shape with sensitive content replaced by hashes or artifact paths. A timeout or nonzero exit after navigation or submission is `ambiguous`, not automatically failed.

## Reconcile

Use the adapter's current read-only list or library command to search for the attempted title, timestamp, and package identity. Restarting a daemon may repair later read-only checks, but it does not prove the prior Create failed. Do not submit again merely because completion polling failed or stdout was empty.

If the adapter lacks a required field, select browser transport before attempting submission. If CAPTCHA is reported, stop and ask the user to complete the provider challenge.
