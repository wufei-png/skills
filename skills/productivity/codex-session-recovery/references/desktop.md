# Desktop visibility

Use this flow only after the user explicitly requests Desktop visibility and a recovered thread is uniquely identified or selected. A Codex Desktop context is not enough.

## Required capabilities

Confirm the current conversation exposes:

- `fork_thread` to create a visible fork;
- `set_thread_title` and `set_thread_pinned` to label and pin it;
- `list_threads` or `read_thread` to verify it.

If a required capability is missing or the recovered id is inaccessible, return CLI commands instead. Do not edit local files or SQLite state as a fallback.

## Flow

1. Keep the recovered thread id for the final report.
2. Show the proposed fork, title, and pin. Execute only after the user authorizes those actions; skip this wait if they already did.
3. Fork it, give the new task a clear recovery title, and pin it.
4. Verify the visible task.
5. Report the new visible id, the recovered source id, and CLI fallbacks.

Create a fresh pointer task only when the user explicitly requests one and `create_thread` is available. Describe any result accurately as a visible fork or pointer, not an import of the JSONL transcript.
