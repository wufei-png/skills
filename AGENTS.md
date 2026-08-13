# Repository Guidelines

## Project Structure & Module Organization

Installable skills live in `skills/productivity/` and `skills/engineering/`. Each kebab-case skill directory has a `SKILL.md` entrypoint and an `agents/openai.yaml` metadata file; add `scripts/`, `references/`, or local fixtures only when the skill needs them. Python regression suites are grouped by product under `tests/<skill-name>/`. `docs/archive/` preserves upstream or historical documentation, while `README.md` and `README_CN.md` are the current catalog. Keep license provenance in `LICENSES/`.

## Build, Test, and Development Commands

This repository has no build step or local package manifest. Run checks from the repository root:

```bash
NO_COLOR=1 npx -y skills@latest add . --list
python3 -m unittest discover -s tests/codex-session-recovery -p 'test_*.py' -v
python3 -m unittest discover -s tests/opencode-session-toolkit -p 'test_*.py' -v
git diff --check
```

The first command verifies that the catalog discovers every skill. The two Python commands run the maintained regression suites, and `git diff --check` catches whitespace errors. CI runs the same discovery, metadata, and unit-test checks on pushes and pull requests.

## Coding Style & Naming Conventions

Use kebab-case for skill directories and keep the frontmatter `name` identical to the directory name. Write concise, behavior-changing instructions in Markdown. All current skills are manual-only: pair `disable-model-invocation: true` in `SKILL.md` with `policy.allow_implicit_invocation: false` in `agents/openai.yaml`. Keep paired variants described in the root README behaviorally parallel except for their stated difference.

Python targets 3.11 and follows the existing standard-library style: four-space indentation, `snake_case` functions, `PascalCase` classes, type hints, and `pathlib.Path`. No repository-wide formatter is configured, so preserve nearby formatting.

## Testing Guidelines

Tests use `unittest`. Name files `test_*.py`, classes `*Test`, and methods `test_<expected_behavior>`. Put deterministic fixtures beside the matching suite and never depend on a real user session database or home directory. There is no numeric coverage gate; add focused regression tests for changed script behavior and repository-contract tests for packaging rules.

## Commit & Pull Request Guidelines

Recent history uses short Conventional Commit-style subjects such as `feat:`, `docs:`, `refactor:`, `chore:`, and `ci:`. Use an imperative, lowercase summary and keep each commit to one intent. Pull requests should identify affected skills, explain catalog or paired-variant impact, list validation commands and results, and link an issue when applicable. Include screenshots only for visual documentation changes.
