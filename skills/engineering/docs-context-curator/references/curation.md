# Curation details

Use this reference for a migration involving historical bundles, an archive index, or local-only build evidence. It supplements the workflow; it does not require this layout in every project.

## Preserve context without loading it by default

Keep an existing useful entry point. It should state the current status or its owner, governing sources, and which document to read for a task. A rare operational rule can remain current while living behind a conditional pointer. A completed implementation plan can move to history while its remaining acceptance requirements stay in the current pending-check list.

An authorization recorded in a historical run applies to that run. Moving the record must not promote its commands or approvals into current operating instructions.

## Move bundles deliberately

- Prefer a directory move when an HTML review and its images, JSON snapshots, or logs form a bundle.
- Check both links into the bundle and relative links out of it. Honor HTML `<base>` before judging relative URLs. A repair to a link is different from changing a recorded observation; retain the latter.
- Treat code and configuration references as migration consumers. A fixture used by a test belongs with fixtures rather than inside an archive hidden from normal tooling. Update the literal path and prove the consumer still works; do not relax the assertion.
- Preserve licensing, attribution, editable-source references, and original research. When a generated page changes, find its generator before repairing disposable output.
- Detect same-name destinations, existing targets, overlapping directory moves, and symlinked paths before moving. Keep a path map in task scratch space when useful; a permanent project manifest is not required.
- Use Git diff/history and per-batch validation for recovery. A read-only helper is not a transactional migration or rollback system.

## Keep the history index useful

Use the existing index when one exists. Otherwise, a small Markdown table is enough:

```markdown
# History

Read only to investigate a prior decision, build, or compatibility issue.

| Topic and former name | Record | Consult when | Current source |
| --- | --- | --- | --- |
| Initial input prototype; whitebox | [Prototype notes](input-prototype.md) | Tracing the original device assumptions | [Input contract](../docs/input.md) |
```

These are example destinations, not files to create mechanically. Include dates or aliases when they help identify a record; do not manufacture summaries, counts, acceptance results, or required metadata fields. Split a large index by real lookup topics only when needed. Keep old command transcripts and complete narratives in their record.

Ordinary entry points can state where history lives and when lookup is justified. They should not require opening the history index or enumerate every old review. For a history question, search a narrow index or topic first, then read the selected record.

## Clean-checkout validation

Distinguish tracked material from ignored caches and build products. A local HTML page can work only because an ignored directory exists. Preserve the recorded build identity, but describe the local artifact as a path plus reproducible commands and prerequisites. Do not substitute a current build's hash or claimed result for an old one.

Check representative references against tracked files as well as the local filesystem when clean-checkout availability matters. Keep platform, human, performance, and listening results pending unless the corresponding evidence exists.

## Reading-path evaluation

After migration, use separate fresh contexts for an ordinary development question and a historical question. Record the host, task, observed file reads, whether current rules were found, and whether the historical record was retrievable. Compare a helper-assisted run with existing commands or a temporary-script run only when actually measuring that tradeoff. CI's deterministic helper tests and manual case manifests do not run or substitute for this evaluation.
