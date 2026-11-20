# Install and upgrade

Install on the scheduling host with Python 3.11+ and an authenticated Codex CLI.

```sh
npx skills@latest add wufei-png/skills --skill codex-native-scheduler --agent codex -g -y --copy
```

On macOS or Linux without Node, use the shell installer. Set `PYTHON` to select
the interpreter when needed.

```sh
curl -fsSL https://raw.githubusercontent.com/wufei-png/skills/main/scripts/install-codex-native-scheduler.sh | sh
```

On macOS or Linux, run `doctor` to initialize state and check the host.

```sh
scheduler_cli="$HOME/.agents/skills/codex-native-scheduler/scripts/codex-schedule"
python3 "$scheduler_cli" doctor
```

For Windows CLI jobs, use PowerShell.

```powershell
$scheduler_cli = Join-Path $HOME '.agents/skills/codex-native-scheduler/scripts/codex-schedule'
python $scheduler_cli doctor
```

Use the same script for each subcommand. For a custom state directory, pass
`--state-dir PATH` before the subcommand.

## Upgrade existing jobs

Install in place to preserve the absolute `runner_entrypoint` shown by `show JOB`.
Keep the job's state directory. The default is
`$CODEX_HOME/codex-native-scheduler` (`~/.codex/codex-native-scheduler` by default).
For a custom install, pass `--target PATH` with the real skill directory to
the shell installer. It supports `--ref REF` and puts backups under
`~/.agents/skill-backups/` by default. Move older sibling `.backup-*` directories
out of the skill search path if they appear as duplicate skills.
The legacy npm launcher also uses the default installed script.

On macOS, user agents can lose their native registration on logout or restart.
Linux transient timers are lost when their user manager is recreated. Use
`status JOB` to check `native.registered` separately from the scheduled
`next_due` time. To re-register an active job, run
`update JOB --prompt-file /path/to/the/original-prompt.txt`.
