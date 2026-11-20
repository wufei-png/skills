# Install DocMate

Use the dedicated upgrade command below for an existing DocMate installation.

## Standard installation

Install the English skill with `npx` and create a catalog outside the skill
directory. Edit the example paths and choose a repair mode before invoking
`$docmate`. Catalog validation uses Node.js.

```sh
npx skills@latest add wufei-png/skills --skill docmate --agent codex -g -y --copy
docmate_skill="$HOME/.agents/skills/docmate"
docmate_config="${XDG_CONFIG_HOME:-$HOME/.config}/docmate"
(umask 077 && mkdir -p "$docmate_config"
  if [ ! -e "$docmate_config/catalog.json" ] && [ ! -L "$docmate_config/catalog.json" ]; then
    cp "$docmate_skill/references/docmate.catalog.example.json" "$docmate_config/catalog.json"
  fi)
```

After editing the catalog, check it with the installed validator.

```sh
bash "$docmate_skill/scripts/validate_catalog.sh" "$docmate_config/catalog.json"
```

See the [catalog reference](catalog.md) for the fields. Standard skill
reinstalls replace files in the skill directory. The catalog in the user
configuration directory persists across those updates.

## Upgrade an existing installation

Upgrade a shared or Codex install with the following command from a clone of
`wufei-png/skills`.

```sh
bash scripts/install-docmate.sh --upgrade
```

An installation made with `--install-mode single` on another host uses its
original host. For example, an OpenClaw install uses the following command.

```sh
bash scripts/install-docmate.sh --upgrade --install-mode single --hosts openclaw
```

The installer validates the existing catalog before updating the installed
skill and supporting files. It keeps the catalog at its current path,
preserves host links, and detects the installed language. Pass
`--language en` or `--language zh` to select a language explicitly. Use the
dedicated command for later upgrades of installations that use a language
template or a catalog path inside the skill directory.

Run the same upgrade from GitHub by piping the installer to `bash -s -- --upgrade`.

```sh
curl -fsSL https://raw.githubusercontent.com/wufei-png/skills/main/scripts/install-docmate.sh | bash -s -- --upgrade
```

## Dedicated installation with repository selection

Use Bash, Git and Node.js. Start the interactive installer from GitHub with
the following command.

```bash
curl -fsSL https://raw.githubusercontent.com/wufei-png/skills/main/scripts/install-docmate.sh | bash
```

Interactive installs use keyboard menus when a TTY is available: Up/Down moves,
Space selects, and Enter selects or confirms depending on the menu.

DocMate can install either the English or Chinese skill template. Interactive
installs ask for the language. Non-interactive installs default to English for
backward compatibility; pass `--language zh` to install the Chinese skill or
`--language en` to be explicit.

Install from a local clone with explicit repositories:

```bash
bash scripts/install-docmate.sh --yes --repo /absolute/path/to/docs-repo
```

Install the Chinese skill template non-interactively:

```bash
bash scripts/install-docmate.sh --yes --language zh --repo /absolute/path/to/docs-repo
```

Install from a local clone by scanning a repository prefix directory:

```bash
bash scripts/install-docmate.sh --yes --auto-scan \
  --scan-root /absolute/path/to/repo-prefix-a \
  --scan-root /absolute/path/to/repo-prefix-b \
  --scan-depth 2
```

Auto scan defaults to depth `2`. In interactive installs, the installer accepts
repository prefix directories one per line, then asks for the scan depth; for
scripts, repeat `--scan-root PATH` for each prefix and use `--scan-depth N` or
`DOCMATE_SCAN_MAX_DEPTH=N`.

Use `--update-mode auto`, `--update-mode ask`, or `--update-mode off` to choose
the global documentation repair mode. `ask` is the default and always asks
before editing docs or opening a PR/MR; `auto` repairs only high-confidence
confirmed gaps; `off` only reports gaps.

Agent platform modes:

- `global` (default): install once to `~/.agents/skills/docmate` and enable all
  detected agent platforms: OpenClaw, Claude Code, OpenCode, Codex, and Hermes.
- `single`: install directly to one agent platform, for example
  `--install-mode single --hosts openclaw`.
- `custom`: install once to `~/.agents/skills/docmate` and enable the agent
  platforms selected by `--hosts`, for example `--hosts openclaw,codex`.
- `--hosts all` remains supported for script compatibility and selects every
  supported agent platform.

The canonical install path for `global` and `custom` installs is:

```text
~/.agents/skills/docmate
```

The installer links that directory into selected agent platform skill locations
for OpenClaw, Claude Code, OpenCode, and Hermes. Codex uses the canonical
`~/.agents/skills/docmate` directory directly, so the `codex` platform does not
create a separate `~/.codex` link.

With the default `--existing backup`, a dedicated installation saves replaced
directories and catalogs under
`${XDG_STATE_HOME:-$HOME/.local/state}/docmate/backups/install-*`. An upgrade
copies the old skill directory to that location. The installer prints the
backup path on success and on failure after a backup. Use it to restore the
previous files if needed.

The installer writes a new catalog outside the skill directory. Shared
installs and single-host Codex installs use
`${XDG_CONFIG_HOME:-$HOME/.config}/docmate/catalog.json`. Other single-host
installs use `catalogs/<host>.json` in the same configuration directory.
The installer links the path `references/docmate.catalog.json` to the
chosen external catalog. Edit the `Catalog` path it prints. Passing repository
selection options starts a new configuration. Use `--upgrade` to preserve a
configured catalog.

`repos[].description` and `repos[].aliases` are optional fields. To auto-fill
missing descriptions, use the [one-time prompt](fill-catalog-descriptions.md)
in your agent and provide the actual catalog path printed by
the installer. Fill `repos[].aliases` manually with short names users may type
for the project.
`repos[].baseBranchCandidates` is seeded from a remote default branch verified
with `gh`, `glab`, or `git`. If remote detection fails, local HEAD or `main` is
an unverified candidate, not a known remote default. Verify the remote base
before repair and edit the candidate when needed.

`--project PATH` is still accepted as a backward-compatible alias for
`--repo PATH`.

When a `--repo` path is not itself a git repository, the installer scans under
that path for git repositories, prints the detected candidates, and asks before
adding them. With `--yes`, detected repositories are added automatically.
