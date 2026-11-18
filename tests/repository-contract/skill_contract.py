"""Repository layout and installer discovery contracts for the skill catalog."""

from __future__ import annotations

import os
import re
import subprocess
from dataclasses import dataclass
from pathlib import Path
from typing import Any, Callable

ROOT = Path(__file__).resolve().parents[2]
SKILLS_ROOT = ROOT / "skills"
EXPECTED_CATEGORIES = ("creative", "engineering", "productivity")
EXPECTED_SKILLS = {
    "consensus-change-review",
    "consensus-gated-grilling",
    "consensus-review-loop",
    "codex-session-recovery",
    "codex-thread-report",
    "delegated-change-review",
    "docs-context-curator",
    "game-experience-review",
    "godot-silent-review",
    "grilling",
    "image-quality-control",
    "implement-in-stages",
    "improve-code-comments",
    "opencode-session-toolkit",
    "reference-image-prompt",
    "review-gated-grilling",
    "review-gated-implementation",
    "review-loop",
    "review-tests",
    "sanitize-artifacts",
    "skill-manual-only",
    "suno-create",
    "suno-music-explorer",
    "suno-studio-download",
    "wait-what",
    "worktree-triage",
}
SKILL_NAME = re.compile(r"[a-z0-9]+(?:-[a-z0-9]+)*")
ANSI_ESCAPE = re.compile(r"\x1b(?:[@-Z\\-_]|\[[0-?]*[ -/]*[@-~])")
INSTALLER_TIMEOUT_SECONDS = 300
InstallerRunner = Callable[..., Any]


class InstallerError(RuntimeError):
    """The installer could not produce a trustworthy discovery result."""


@dataclass(frozen=True)
class SkillTree:
    names: list[str]
    errors: list[str]


@dataclass(frozen=True)
class InstallerReport:
    repository_names: list[str]
    discovered_names: list[str]
    errors: list[str]


def frontmatter(text: str) -> dict[str, str]:
    match = re.match(r"\A---\n(.*?)\n---(?:\n|\Z)", text, re.DOTALL)
    if not match:
        return {}
    fields: dict[str, str] = {}
    for line in match.group(1).splitlines():
        if line and not line.startswith((" ", "\t")) and ":" in line:
            key, value = line.split(":", 1)
            fields[key] = value.strip()
    return fields


def compare_sets(label: str, expected: set[str], actual: list[str]) -> list[str]:
    expected_set = set(expected)
    actual_set = set(actual)
    errors: list[str] = []
    missing = sorted(expected_set - actual_set)
    extra = sorted(actual_set - expected_set)
    if missing:
        errors.append(f"{label}: missing {', '.join(missing)}")
    if extra:
        errors.append(f"{label}: unexpected {', '.join(extra)}")
    return errors


def inspect_skill_tree(skills_root: Path = SKILLS_ROOT) -> SkillTree:
    errors: list[str] = []
    names: list[str] = []
    if not skills_root.is_dir():
        return SkillTree([], [f"skills root is not a directory: {skills_root}"])

    categories = sorted(path for path in skills_root.iterdir() if path.is_dir())
    present_categories = {path.name for path in categories}
    for expected in EXPECTED_CATEGORIES:
        if expected not in present_categories:
            errors.append(f"missing skill category: {expected}")
    for category in categories:
        relative_category = category.relative_to(skills_root).as_posix()
        if category.name not in EXPECTED_CATEGORIES:
            errors.append(f"unexpected skill category: {relative_category}")
        for skill_dir in sorted(path for path in category.iterdir() if path.is_dir()):
            name = skill_dir.name
            relative = skill_dir.relative_to(skills_root).as_posix()
            names.append(name)
            if not SKILL_NAME.fullmatch(name):
                errors.append(f"skill directory is not kebab-case: {relative}")
            skill_file = skill_dir / "SKILL.md"
            if not skill_file.is_file():
                errors.append(f"missing SKILL.md: {relative}")
            else:
                fields = frontmatter(skill_file.read_text(encoding="utf-8"))
                if fields.get("name") != name:
                    errors.append(
                        f"{relative}: SKILL.md name is {fields.get('name')!r}, "
                        f"expected {name!r}"
                    )
                if fields.get("disable-model-invocation") != "true":
                    errors.append(
                        f"{relative}: SKILL.md must set disable-model-invocation: true"
                    )
            metadata_file = skill_dir / "agents" / "openai.yaml"
            if not metadata_file.is_file():
                errors.append(f"missing agents/openai.yaml: {relative}")
            else:
                metadata = metadata_file.read_text(encoding="utf-8")
                if "policy:\n  allow_implicit_invocation: false" not in metadata:
                    errors.append(
                        f"{relative}: agents/openai.yaml must set "
                        "policy.allow_implicit_invocation: false"
                    )

    paths_by_name: dict[str, list[str]] = {}
    for category in categories:
        for skill_dir in sorted(path for path in category.iterdir() if path.is_dir()):
            paths_by_name.setdefault(skill_dir.name, []).append(
                skill_dir.relative_to(skills_root).as_posix()
            )
    for name, paths in sorted(paths_by_name.items()):
        if len(paths) > 1:
            errors.append(f"duplicate skill name {name}: {', '.join(paths)}")
    return SkillTree(names, errors)


def parse_installer_output(output: str) -> list[str]:
    text = ANSI_ESCAPE.sub("", output)
    lines = text.replace("\r\n", "\n").replace("\r", "\n").split("\n")
    start = next(
        (index for index, line in enumerate(lines) if "Available Skills" in line),
        None,
    )
    if start is None:
        raise InstallerError(
            "installer output has no 'Available Skills' section; "
            "the command failed or its output format changed"
        )
    footer = next(
        (
            index
            for index in range(start + 1, len(lines))
            if "Use --skill" in lines[index]
        ),
        None,
    )
    if footer is None:
        raise InstallerError(
            "installer output is truncated before 'Use --skill'; "
            "refusing to infer skills from partial output"
        )

    names: list[str] = []
    for line in lines[start + 1 : footer]:
        match = re.fullmatch(r"[│|]\s{4}(\S+)\s*", line)
        if match:
            names.append(match.group(1))
    if not names:
        raise InstallerError(
            "installer listed no skill names; the command failed or its output format changed"
        )

    invalid = sorted(name for name in names if not SKILL_NAME.fullmatch(name))
    if invalid:
        raise InstallerError(
            f"installer reported invalid skill names: {', '.join(invalid)}"
        )
    duplicates = sorted({name for name in names if names.count(name) > 1})
    if duplicates:
        raise InstallerError(
            f"installer reported duplicate skills: {', '.join(duplicates)}"
        )

    summary = re.search(r"Found\s+(\d+)\s+skills", text)
    if summary is None:
        raise InstallerError("installer output has no 'Found N skills' summary")
    found_count = int(summary.group(1))
    if found_count != len(names):
        raise InstallerError(
            f"installer summary reports {found_count} skills but lists {len(names)} names"
        )
    return names


def run_installer(
    package: str,
    root: Path,
    runner: InstallerRunner = subprocess.run,
    timeout: int = INSTALLER_TIMEOUT_SECONDS,
) -> str:
    command = ["npx", "-y", package, "add", ".", "--list"]
    environment = os.environ.copy()
    environment["NO_COLOR"] = "1"
    try:
        completed = runner(
            command,
            cwd=root,
            capture_output=True,
            text=True,
            env=environment,
            timeout=timeout,
        )
    except (OSError, subprocess.TimeoutExpired) as error:
        raise InstallerError(f"could not run {package}: {error}") from error
    if completed.returncode != 0:
        detail = (completed.stderr or completed.stdout or "").strip()
        raise InstallerError(
            f"{package} exited with {completed.returncode}: {detail[-4000:]}"
        )
    return completed.stdout


def verify_installer(
    package: str,
    root: Path = ROOT,
    expected: set[str] = EXPECTED_SKILLS,
    runner: InstallerRunner = subprocess.run,
    timeout: int = INSTALLER_TIMEOUT_SECONDS,
) -> InstallerReport:
    tree = inspect_skill_tree(root / "skills")
    errors = list(tree.errors)
    errors.extend(compare_sets("repository contract", expected, tree.names))
    try:
        discovered = parse_installer_output(
            run_installer(package, root, runner=runner, timeout=timeout)
        )
    except InstallerError as error:
        errors.append(str(error))
        return InstallerReport(tree.names, [], errors)
    errors.extend(compare_sets("installer discovery", tree.names, discovered))
    return InstallerReport(tree.names, discovered, errors)
