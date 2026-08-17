---
name: codex-session-recovery
description: Find local Codex sessions read-only and provide CLI recovery commands. Use for missing history, prior thread lookup, resume or fork help, and explicitly requested Desktop visibility.
disable-model-invocation: true
---

# Codex Session Recovery

Recover access to local Codex history without mutating live state by default.

## Safety

- Read local Codex JSONL only. Prefer copied fixtures or temporary copies for testing.
- Exclude archived and subagent sessions unless requested. Show only short prompt snippets unless the user requests more.
- Never edit `$CODEX_HOME`, SQLite-backed state, rollout files, or provider or account metadata. Never copy or import JSONL into live Codex state.
- Do not create or manage Desktop threads unless the user explicitly requests Desktop visibility. A Codex Desktop context is not enough.

## Find sessions

Use the bundled scanner. Resolve `<skill-directory>` from this loaded skill's location; do not assume it is installed under `$CODEX_HOME/skills`.

```bash
python "<skill-directory>/scripts/scan_codex_sessions.py" \
  --codex-home "${CODEX_HOME:-$HOME/.codex}" \
  --cwd "/Users/example/project" \
  --since "2026-06-10" \
  --timezone "Asia/Shanghai" \
  --format table
```

From this repository checkout:

```bash
python skills/productivity/codex-session-recovery/scripts/scan_codex_sessions.py \
  --codex-home /tmp/copied-codex-home \
  --format json
```

Use `--help` for all options. The main filters are `--cwd`, `--since`, `--until`, `--timezone`, and `--query`; archived sessions, subagents, and prompt snippets require explicit include flags. Prefer JSON when another tool consumes the result.

For each likely session, report its thread id, cwd, time, archived or subagent status, matching reasons, confidence, source path, and exact `codex resume` and `codex fork` commands. If nothing matches, state the filters and suggest relaxing one at a time.

## Desktop visibility

A Codex Desktop context is not enough. When the user explicitly requests Desktop visibility and the candidate is unique or already selected, follow `references/desktop.md`. If the candidate is ambiguous, ask the user to choose first. Otherwise remain CLI-first.
