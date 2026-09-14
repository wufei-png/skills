# Explorer ledger

Use the ledger to recover a run, enforce its grant, and avoid duplicate submissions. Do not treat it as a song archive.

## Resolve the directory

Apply this order exactly:

1. A path explicitly supplied by the user.
2. The nearest existing `.suno-explorer/` found by walking from the working directory toward the filesystem root.
3. `.suno-explorer/` under the only workspace root in scope.

An existing directory may be read automatically. Before creating a proposed directory, show its resolved path and obtain confirmation. If there is no unique workspace root, ask for a path or offer a session-only ledger. Do not create a directory in an arbitrary current working directory and do not edit `.gitignore`.

Use the bundled helper for deterministic resolution:

```bash
python3 <skill-directory>/scripts/ledger.py resolve \
  --start "$PWD" \
  --workspace-root /path/to/workspace
```

Add `--user-path /chosen/path` when supplied. Repeat `--workspace-root` for every root actually in scope; the helper will refuse to choose among multiple roots.

After confirmation, initialize a run:

```bash
python3 <skill-directory>/scripts/ledger.py init \
  --ledger-dir /resolved/.suno-explorer \
  --session-id 20260914-example \
  --create-limit 3 \
  --confirm-create
```

Omit `--confirm-create` when the directory already exists. Use `--credit-limit` only when the user supplied one.

## Record minimum recovery state

The JSON ledger stores the grant, aggregate spend, phase, compact events, decision label, and next action. Events may include a hypothesis summary, submission state, provider candidate IDs or URLs, content hashes, and listening status.

Do not store credentials, cookies, tokens, full lyrics, full style prompts, account balances, or audio data. Keep full creative packages in a user-authorized artifact location and reference them by path and hash when needed.

Append a compact event and update totals atomically:

```bash
python3 <skill-directory>/scripts/ledger.py record \
  --file /resolved/.suno-explorer/runs/20260914-example.json \
  --event-json '{"kind":"submission","summary":"identity A probe confirmed","candidate_ids":["id-1","id-2"]}' \
  --creates-spent 1 \
  --phase listen \
  --next-action "audition identity A candidates"
```

Totals are absolute, not increments. Validate before resuming:

```bash
python3 <skill-directory>/scripts/ledger.py validate \
  --file /resolved/.suno-explorer/runs/20260914-example.json
```

Allowed decision labels are `probe-winner`, `provisional-leader`, `best-so-far`, and `human-selected-final`. The helper rejects totals beyond the grant and common sensitive fields.
