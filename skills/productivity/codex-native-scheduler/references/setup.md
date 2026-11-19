# Install and upgrade

Use Python 3.11+ and an authenticated Codex CLI on the host that owns the chat.
Chat reminders use `codex queue` with macOS launchd or Linux user systemd.
Windows Task Scheduler supports unattended CLI runs.

```bash
npx skills@latest add wufei-png/skills --skill codex-native-scheduler --agent codex -g -y --copy
scheduler_cli="$HOME/.agents/skills/codex-native-scheduler/scripts/codex-schedule"
python3 "$scheduler_cli" doctor
python3 "$scheduler_cli" init
```

For macOS and Linux without Node:

```bash
curl -fsSL https://raw.githubusercontent.com/wufei-png/skills/main/scripts/install-codex-native-scheduler.sh | sh
```

Set `PYTHON` for the shell installer if `python3` is older than 3.11.

## Keep existing jobs

Copy the update to the same installed location. Jobs retain the absolute
`runner_entrypoint` shown by `show JOB` and the state directory used at creation.
The default install path and state directory are `~/.agents/skills/codex-native-scheduler`
and `$CODEX_HOME/codex-native-scheduler` (`~/.codex/codex-native-scheduler` by default).
Run `init` for a new state directory.

For a custom install, give the shell installer `--target PATH` with the existing
skill directory that contains `scripts/codex-schedule`. Use the real path if a
symlink was involved. The installer backs up an existing installation by
default and accepts `--ref REF` to install a specific revision of this collection.

## Manage from a terminal

Run the installed script with the configured Python. The legacy npm
`codex-schedule` launcher also finds the default installed script.

```bash
python3 "$scheduler_cli" list
python3 "$scheduler_cli" status JOB
python3 "$scheduler_cli" runs JOB
python3 "$scheduler_cli" pause JOB
python3 "$scheduler_cli" resume JOB
```

For a custom state directory, pass `--state-dir PATH` before the command. See
[operational semantics](semantics.md) for native scheduling and job lifecycle.
