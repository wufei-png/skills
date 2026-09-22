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

Use `--help` for all options. The main filters are `--cwd`, `--since`, `--until`, `--timezone`, and `--query`; archived sessions, subagents, prompt snippets, unknown-time records under date filters, and index-referenced paths require explicit flags (`--include-archived`, `--include-subagents`, `--show-prompts`, `--include-unknown-time`, and `--show-paths`). Prefer JSON when another tool consumes the result.

The index or transcript filename provides the canonical thread id; other observed `id`, `thread_id`, or `session_id` values are reported as aliases and merged into that record. Report its thread name, cwd, time, archived or subagent status, `match_score` and `matching_reasons` as given, source path, and exact `codex resume` and `codex fork` commands. The score ranks candidates within one search; it is not a probability or percentage and may exceed 100. The JSON field was renamed from `confidence` to `match_score`, with no old-field alias. If nothing matches, state the filters and suggest relaxing one at a time.

## Desktop visibility

A Codex Desktop context is not enough. When the user explicitly requests Desktop visibility and the candidate is unique or already selected, follow `references/desktop.md`. If the candidate is ambiguous, ask the user to choose first. Otherwise remain CLI-first.
