# OpenCLI transport

Use this path only when `opencli` is installed, its Suno adapter is available, and it supports every required package field.

The capability check covers every requested value, not only values accepted as command options. Confirm that the adapter can set and read back duration, vocal gender, the official Max Mode state, Audio Influence, audio references, and Persona or Extend settings when they are part of the package. A prompt label such as `[Is_MAX_MODE: MAX]` is not an official Max Mode setting. If any value cannot be verified before Create, use the next capable path.

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

A green `doctor` proves the base browser bridge, not the Suno adapter's write readiness. If the read-only Suno status check fails, do not attempt Create through that adapter; select the next capable path before spending.

## Submit

Build the command from the discovered schema. This custom-mode shape shows common text fields; it is not complete until every requested package field has a supported option and a verified readback:

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

Do not run this shape unchanged when the package also requires duration, vocal gender, Max Mode, Audio Influence, an audio reference, Persona, or Extend. Add the installed adapter's current options only when its read-only result confirms those values. If it cannot, continue to the next capable path before Create.

Record the exact command shape with sensitive content replaced by hashes or artifact paths. A timeout or nonzero exit after navigation or submission is `ambiguous`, not automatically failed.

## Reconcile

Use the adapter's current read-only list or library command to search for the attempted title, timestamp, and package identity. Restarting a daemon may repair later read-only checks, but it does not prove the prior Create failed. Do not submit again merely because completion polling failed or stdout was empty.

If the adapter lacks a required field or cannot read it back before submission, select Playwright or Computer Use according to the browser capability checks. If CAPTCHA is reported, stop and ask the user to complete the provider challenge.
