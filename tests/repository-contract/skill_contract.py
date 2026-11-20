"""Repository layout and installer discovery contracts for the skill catalog."""

from __future__ import annotations

import os
import re
import subprocess
from dataclasses import dataclass
from pathlib import Path
from typing import Any, Callable

try:
    import yaml
except ImportError as error:
    raise RuntimeError(
        "PyYAML is required for repository contract checks; install it with "
        "'python3 -m pip install -r requirements-test.txt'"
    ) from error

ROOT = Path(__file__).resolve().parents[2]
SKILLS_ROOT = ROOT / "skills"
EXPECTED_CATEGORIES = ("creative", "engineering", "productivity")
EXPECTED_SKILLS = {
    "codex-native-scheduler",
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


class ContractError(RuntimeError):
    """A repository contract input is invalid or ambiguous."""


_BOOL_TAG = "tag:yaml.org,2002:bool"
_YAML_12_BOOLEAN_VALUES = {
    "true": True,
    "True": True,
    "TRUE": True,
    "false": False,
    "False": False,
    "FALSE": False,
}


class _UniqueKeyLoader(yaml.SafeLoader):
    """Safe YAML loader with YAML 1.2 booleans and unique string keys."""


def _construct_strict_bool(loader, node):
    if not isinstance(node, yaml.ScalarNode):
        raise ContractError("boolean value must be a scalar")
    value = loader.construct_scalar(node)
    if value in _YAML_12_BOOLEAN_VALUES:
        return _YAML_12_BOOLEAN_VALUES[value]
    raise ContractError(f"boolean values must be YAML 1.2 true or false, got {value!r}")


_UniqueKeyLoader.yaml_implicit_resolvers = {
    first: [(tag, regexp) for tag, regexp in entries if tag != _BOOL_TAG]
    for first, entries in yaml.SafeLoader.yaml_implicit_resolvers.items()
}
_UniqueKeyLoader.add_implicit_resolver(
    _BOOL_TAG,
    re.compile(r"^(?:true|True|TRUE|false|False|FALSE)$"),
    list("tTfF"),
)
_UniqueKeyLoader.yaml_constructors = dict(yaml.SafeLoader.yaml_constructors)
_UniqueKeyLoader.add_constructor(_BOOL_TAG, _construct_strict_bool)


def _construct_unique_mapping(loader, node, deep=False):
    if not isinstance(node, yaml.MappingNode):
        raise ContractError("expected a YAML mapping node")
    mapping: dict[str, Any] = {}
    for key_node, value_node in node.value:
        if key_node.tag == "tag:yaml.org,2002:merge":
            raise ContractError("YAML merge keys are not supported")
        key = loader.construct_object(key_node, deep=deep)
        if not isinstance(key, str):
            raise ContractError(f"non-string mapping key: {key!r}")
        if key in mapping:
            raise ContractError(f"duplicate mapping key: {key!r}")
        mapping[key] = loader.construct_object(value_node, deep=deep)
    return mapping


_UniqueKeyLoader.add_constructor(
    yaml.resolver.BaseResolver.DEFAULT_MAPPING_TAG,
    _construct_unique_mapping,
)


@dataclass(frozen=True)
class SkillTree:
    names: list[str]
    errors: list[str]


@dataclass(frozen=True)
class InstallerReport:
    repository_names: list[str]
    discovered_names: list[str]
    errors: list[str]


def load_yaml_mapping(text: str, label: str) -> dict[str, Any]:
    """Parse one YAML document as a string-keyed mapping, failing closed."""
    try:
        data = yaml.load(text, Loader=_UniqueKeyLoader)
    except ContractError as error:
        raise ContractError(f"{label}: {error}") from error
    except yaml.YAMLError as error:
        raise ContractError(f"{label}: invalid YAML: {error}") from error
    if not isinstance(data, dict):
        raise ContractError(
            f"{label}: expected a YAML mapping, got {type(data).__name__}"
        )
    return data


def frontmatter(text: str) -> dict[str, Any]:
    """Parse SKILL.md frontmatter, rejecting malformed or ambiguous YAML."""
    lines = text.splitlines()
    if not lines or not text.startswith("---") or lines[0].rstrip() != "---":
        raise ContractError(
            "SKILL.md must start with YAML frontmatter delimited by ---"
        )
    closing = next(
        (index for index in range(1, len(lines)) if lines[index].rstrip() == "---"),
        None,
    )
    if closing is None:
        raise ContractError("SKILL.md frontmatter is missing its closing ---")
    return load_yaml_mapping(
        "\n".join(lines[1:closing]),
        "SKILL.md frontmatter",
    )


def display_boolean(value: Any) -> str:
    return f"{value!r} ({type(value).__name__})"


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
                try:
                    fields = frontmatter(skill_file.read_text(encoding="utf-8"))
                except ContractError as error:
                    errors.append(f"{relative}: {error}")
                else:
                    if fields.get("name") != name:
                        errors.append(
                            f"{relative}: SKILL.md name is "
                            f"{fields.get('name')!r}, expected {name!r}"
                        )
                    if "disable-model-invocation" not in fields:
                        errors.append(
                            f"{relative}: SKILL.md must set "
                            "disable-model-invocation: true"
                        )
                    elif fields["disable-model-invocation"] is not True:
                        errors.append(
                            f"{relative}: SKILL.md disable-model-invocation must be "
                            f"boolean true, got "
                            f"{display_boolean(fields['disable-model-invocation'])}"
                        )
                    host_metadata = fields.get("metadata")
                    if (
                        isinstance(host_metadata, dict)
                        and host_metadata.get("opencode/autoinvoke") is True
                    ):
                        errors.append(
                            f"{relative}: metadata.opencode/autoinvoke enables implicit invocation"
                        )
            metadata_file = skill_dir / "agents" / "openai.yaml"
            if not metadata_file.is_file():
                errors.append(f"missing agents/openai.yaml: {relative}")
            else:
                try:
                    metadata = load_yaml_mapping(
                        metadata_file.read_text(encoding="utf-8"),
                        "agents/openai.yaml",
                    )
                except ContractError as error:
                    errors.append(f"{relative}: {error}")
                else:
                    policy = metadata.get("policy")
                    if not isinstance(policy, dict):
                        errors.append(
                            f"{relative}: agents/openai.yaml must contain a "
                            "policy mapping"
                        )
                    elif "allow_implicit_invocation" not in policy:
                        errors.append(
                            f"{relative}: agents/openai.yaml must set "
                            "policy.allow_implicit_invocation: false"
                        )
                    elif policy["allow_implicit_invocation"] is not False:
                        errors.append(
                            f"{relative}: policy.allow_implicit_invocation must be "
                            f"boolean false, got "
                            f"{display_boolean(policy['allow_implicit_invocation'])}"
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
