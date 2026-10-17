# Optional check interface

Use Python 3.11+ and the standard library. Resolve `<skill-directory>` from the loaded skill location; paths below are placeholders. Existing project tooling takes precedence when it covers the task.

```bash
python3 <skill-directory>/scripts/doc_checks.py --help
python3 <skill-directory>/scripts/doc_checks.py inventory --root <project-root> --path docs --exclude docs/archive
python3 <skill-directory>/scripts/doc_checks.py refs --root <project-root> --target docs/old.md --path docs --path tests --path tools
python3 <skill-directory>/scripts/doc_checks.py links --root <project-root> --path README.md --path docs/current
python3 <skill-directory>/scripts/doc_checks.py moves --root <project-root> --plan <scratch-directory>/moves.json
```

All commands are read-only. `inventory` emits file metadata and document titles, not bodies. `refs` emits source locations and matched destination tokens, not complete source lines. `links` checks existing static local destinations. `moves` checks a supplied path mapping; it never moves or rewrites files.

The temporary move plan is a JSON array:

```json
[{"source": "docs/old.md", "target": "archive/notes/old.md"}]
```

Targets are explicit; the helper does not pick an archive root, flatten paths, or assign lifecycle state. Directory sources are allowed, but overlapping sources/targets, occupied targets, and symlinks require resolution before proceeding.

## Selection and output

- `inventory`, `refs`, and `links` require repeated `--path` scopes. `--exclude` omits a relative file or subtree. Scopes and exclusions are literal paths, not globs. Supply the actual archive exclusions for the task. No archive directory is inferred.
- In a Git working tree, selection includes tracked and untracked non-ignored files. Git's standard ignore rules apply, not `.rgignore`. The agent must pass archive exclusions explicitly. `--include-ignored` opts into filesystem traversal of the supplied scopes, including ignored files. Non-Git projects use scoped filesystem traversal.
- Paths are project-relative POSIX paths. Reject absolute scope/move paths, `..`, backslashes, and symlinked paths. The explicit project root itself is resolved once, so system aliases such as a symlinked temporary root work.
- JSON is the output interface. `--limit` (default 40) and `--offset` page items. `total` and `has_more` describe unshown items. Coverage reports selected/read/skipped files and a bounded sample of skipped paths.
- Text reads are limited by `--max-bytes` (default 1 MiB per file). Binary, oversized, unsafe, or unreadable text sources are reported as skipped. Narrow a scope or deliberately raise the limit when appropriate.
- Exit `0` means no detected check failure; exit `1` means link/move findings or an incomplete scan; exit `2` means an invalid command, path, or plan. A zero result is bounded by the declared coverage.

## Supported checks and limits

Static link extraction covers common inline Markdown destinations, Markdown reference definitions, and HTML `href`/`src`/`poster` with the first HTML `<base>`. It skips HTML comments, fenced examples, and inline code, including code spans wrapped across lines within a paragraph. Relative URL escapes are decoded; URL fragments and remote URLs are not validated. Root-relative website URLs and templates, including those in an HTML `<base>`, need the project's own resolver; dependent relative links remain unresolved. This is not a full CommonMark, documentation-build, or anchor validator.

`refs` also searches literal target paths and basenames in selected UTF-8 text, including code, tests, and configuration. Literal hits are **candidates**, not proven consumers. Dynamic paths, custom URI schemes, generated includes, notebook attachments, and engine-specific resource loading need native tooling or a task-local adapter. No match never proves the absence of dependencies.

`links` tests filesystem presence, not tracked availability, semantic correctness, or build success. `moves` checks paths and collisions, not outbound-link repair, content preservation, permissions at publish time, or atomic rollback. Validate the actual diff and consumers separately.
