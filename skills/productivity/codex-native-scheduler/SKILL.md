---
name: codex-native-scheduler
description: Schedule prompts for an existing Codex chat on macOS or Linux, or schedule unattended Codex CLI runs. Use when asked to create, change, inspect, or stop a native scheduled job.
disable-model-invocation: true
---

# Codex Native Scheduler

Run this skill's `scripts/codex-schedule` with Python 3.11+. See
[installation and upgrades](references/setup.md) for host setup.

## Choose a mode

- `queue_existing` sends to a chat on its macOS or Linux host. It uses
  `CODEX_THREAD_ID` by default. Pass `--session-id UUID` to name the target.
  Use `--state-dir PATH` before the subcommand if the chat needs a
  writable state directory.
- `new_each_run` starts a fresh CLI session. Set `--cwd` to the project and use
  `--workspace worktree` to isolate recurring edits.
- `resume_fixed` reuses a CLI session. To seed it, use `--session-id UUID`,
  `--workspace direct`, and that session's working directory.

## Create and verify

Use one schedule and one prompt source. Check `list` before recreating a job.
For a global install on macOS or Linux, run the script by path.

```sh
scheduler_cli="$HOME/.agents/skills/codex-native-scheduler/scripts/codex-schedule"
python3 "$scheduler_cli" create --name progress-check --every 1h \
  --session-mode queue_existing --prompt-file ./check.txt
python3 "$scheduler_cli" status progress-check
```

Check the target, next due time, and native registration in `status JOB`.
Use `--stop-when` only when the user authorizes the chat to verify a condition
and pause the schedule. Check `runs JOB` for queue acceptance and the chat
transcript for its reply.

## Manage a job

Use `update`, `pause`, or `resume` for future runs and `run-show RUN` for run
details. Use `run-now` only when asked to run immediately. See
[operational details](references/semantics.md) for recovery, profiles, and cleanup.
