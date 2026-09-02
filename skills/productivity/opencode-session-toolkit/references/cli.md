# CLI behavior

Run commands from the skill directory. Put `--db-path` after the subcommand when overriding `opencode db path`. Treat `<command> --help` as the option authority.

`doctor` reads schema metadata only, not transcript content. Add `--integrity` when an explicit SQLite `PRAGMA integrity_check` is needed; it is not part of the default probe.

## Filters and output

Repeated values for one filter are OR alternatives; different filter categories combine with AND. Text filters are literal, case-insensitive substrings, so `%` and `_` are not SQL wildcards.

`list` excludes archived sessions by default and returns 20 rows ordered by update time and session id. Displayed times are UTC ISO-8601. Naive datetimes and date-only bounds use the machine's local timezone; a date-only end includes that whole day.

Table output is for people and JSON is stable for tools. User errors exit with code 2 and a concise `error:` on stderr.

## Transcripts and search

`show SESSION_ID` includes text and short tool summaries. It omits reasoning, complete tool inputs and outputs, raw message JSON, and other non-display parts unless `--include-sensitive` is explicit.

`search TEXT` reports matching sessions without surrounding message snippets. Use `show` on a selected session to avoid exposing unrelated payloads.

## Export

`export` uses the same filters as `list`; require `--all` when no filter is present. Use `--dry-run` to preview matched paths and conflicts without writing.

Markdown creates one file per session using a sanitized title, UTC creation time, and session id. JSONL creates `sessions.jsonl`. Exports are preflighted before any write:

- identical files remain unchanged;
- changed files stop the entire export before new files are written;
- `--overwrite` replaces changed files through same-directory atomic renames.

`--include-sensitive` keeps the same explicit opt-in as `show` and emits a warning on stderr.

`export --sanitize` calls the installed OpenCode CLI once per selected session as `opencode export SESSION_ID --sanitize` and stores the native JSON output without rewriting or locally sanitizing it. It uses the database resolved by `opencode db path`; `--db-path`, `--format jsonl`, and `--include-sensitive` are rejected. Native stdout is captured directly to a temporary file and must be one valid JSON object; a nonzero exit, status prefix, truncation, or invalid JSON aborts the whole batch and leaves no new output.

All export files are staged and published as one batch. A normal publish failure rolls already-published files back; existing files are still preflighted, and `--overwrite` remains required for changed output.
