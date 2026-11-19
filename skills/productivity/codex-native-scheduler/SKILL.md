---
name: codex-native-scheduler
description: Schedule prompts for an existing Codex chat on macOS or Linux, or schedule unattended Codex CLI runs. Use when asked to create, change, inspect, or stop a native scheduled job.
disable-model-invocation: true
---

# Codex Native Scheduler

Run the bundled `scripts/codex-schedule` with Python 3.11+. Run `doctor` on first
use. See [installation and upgrades](references/setup.md) when setting up a host
or migrating an existing installation.

## Send a prompt to a chat

Run on the saved chat's host with its Codex installation. Use the exact UUID
for another chat. For the current chat, `queue_existing` uses
`CODEX_THREAD_ID`. Check `list` for the same job before creating it. Use a state
directory the target chat can write (`--state-dir` before the subcommand).

```console
codex-schedule create --name progress-check --every 1h \
  --session-mode queue_existing --prompt-file ./check.txt \
  --stop-when "The run is complete and cleanup is confirmed."
```

Use `--stop-when` for a condition the user authorizes the chat to verify and act
on. Each reminder includes the receipt command. The scheduler skips subsequent
ticks until the receipt arrives. Report queue acceptance and the chat's reply
separately.

## Start a scheduled run

Use `create` with one schedule and one prompt source. Set `--cwd` to the
intended project and use `--workspace worktree` to isolate recurring edits.
`new_each_run` starts a fresh session. `resume_fixed` reuses a session for
background execution. To seed it, pass `--session-id UUID --workspace direct`
and use that session's working directory. Codex applies its existing permissions.

## Manage a job

`status JOB` shows the target, next due time, and native state. Use
`update JOB --every 2h` to change the interval. Use `pause JOB` and `resume JOB`
for future runs. Use `run-now` only when asked to run immediately.
`runs JOB` and `run-show RUN` show the evidence for individual runs.

Read [operational details](references/semantics.md) for delivery recovery,
profiles, schedule behavior, and cleanup.
