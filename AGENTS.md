# Repository Guidelines

## Project Structure & Module Organization

Installable skills live in `skills/productivity/`, `skills/engineering/`, and `skills/creative/`. Each kebab-case skill directory has a `SKILL.md` entrypoint and an `agents/openai.yaml` metadata file; add `scripts/`, `references/`, or local fixtures only when the skill needs them. Python regression suites are grouped by product under `tests/<skill-name>/`. `docs/archive/` preserves upstream or historical documentation, while `README.md` and `README_CN.md` are the current catalog. Keep license provenance in `LICENSES/`.

## Build, Test, and Development Commands

This repository has no build step or runtime package manifest. Contract tests use the pinned PyYAML dependency in `requirements-test.txt`. Run checks from the repository root:

```bash
python3 -m pip install --disable-pip-version-check -r requirements-test.txt
python3 -m unittest discover -s tests/repository-contract -p 'test_*.py' -v
python3 tests/repository-contract/verify_installer.py --package skills@1.9.0
python3 tests/repository-contract/verify_installer.py --package skills@latest
python3 -m unittest discover -s tests/docs-context-curator -p 'test_*.py' -v
python3 -m unittest discover -s tests/codex-native-scheduler -p 'test_*.py' -v
python3 -m unittest discover -s tests/codex-session-recovery -p 'test_*.py' -v
python3 -m unittest discover -s tests/opencode-session-toolkit -p 'test_*.py' -v
python3 -m unittest discover -s tests/suno-music-explorer -p 'test_*.py' -v
python3 -m unittest discover -s tests/suno-studio-download -p 'test_*.py' -v
node --test tests/suno-create/*.test.mjs
python3 -m pip install --disable-pip-version-check ruff==0.16.5
ruff check skills tests
ruff format --check .
git diff --check
```

The contract tests compare the skill tree with the independent `EXPECTED_SKILLS` set and validate entrypoints, metadata, unique names, and manual-only flags as YAML 1.2 booleans; only canonical `true`/`false` forms are accepted, not YAML 1.1 values such as `yes`/`no`/`on`/`off` or quoted strings. The installer commands verify that fixed and latest discovery both match the tree and the expected set. Install the pinned PyYAML dependency from `requirements-test.txt` before running the contract tests, and install Ruff 0.16.5 once before running the lint and format commands. `git diff --check` catches whitespace errors. CI runs the same checks on pushes and pull requests, and also runs the latest installer weekly.

## Coding Style & Naming Conventions

Use kebab-case for skill directories and keep the frontmatter `name` identical to the directory name. All current skills are manual-only: pair `disable-model-invocation: true` in `SKILL.md` with `policy.allow_implicit_invocation: false` in `agents/openai.yaml`. Keep paired variants described in the root README behaviorally parallel except for their stated difference.

Assume the model already knows common domain knowledge and practices. Keep only instructions that change behavior for the task: its workflow, decisions, safety limits, tool contracts, and output requirements. Arrange sections in task order and avoid duplicated rules or unnecessary mandatory steps and reads. Use short, familiar wording; avoid repeating general advice or inventing terms. Put rarely needed details in `references/` and read them only when relevant; put repeated, fragile operations in `scripts/`.

Python targets 3.11; skill scripts use the standard library, and contract tests use the pinned PyYAML dependency. Ruff 0.16.5 enforces lint and formatting for `skills` and `tests`; test fixtures under `tests/**/fixtures/**` are excluded from lint but still formatted, and archived documents under `docs/archive/` are excluded from formatting.

## Testing Guidelines

Tests use `unittest`. Keep fixtures deterministic and independent of real user databases or home directories. There is no numeric coverage gate; add focused regression tests for changed scripts and repository-contract tests for packaging rules.

## Commit & Pull Request Guidelines

Recent history uses short Conventional Commit-style subjects such as `feat:`, `docs:`, `refactor:`, `chore:`, and `ci:`. Use an imperative, lowercase summary and keep each commit to one intent. Pull requests should identify affected skills, explain catalog or paired-variant impact, list validation commands and results, and link an issue when applicable. Include screenshots only for visual documentation changes.
