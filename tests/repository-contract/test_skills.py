from __future__ import annotations

import json
import re
import subprocess
import unittest
from pathlib import Path


ROOT = Path(__file__).resolve().parents[2]
SKILLS_ROOT = ROOT / "skills"
EXPECTED_SKILLS = {
    "consensus-change-review",
    "consensus-gated-grilling",
    "consensus-review-loop",
    "codex-session-recovery",
    "delegated-change-review",
    "grilling",
    "implement-in-stages",
    "improve-code-comments",
    "opencode-session-toolkit",
    "review-gated-grilling",
    "review-gated-implementation",
    "review-loop",
    "review-tests",
    "sanitize-artifacts",
    "suno-create",
    "suno-music-explorer",
}
VALID_PRIORITIES = {"P0", "P1", "P2", "P3"}


def skill_directories() -> list[Path]:
    return sorted(
        path.parent for path in SKILLS_ROOT.glob("*/*/SKILL.md")
    )


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


class SkillRepositoryContractTest(unittest.TestCase):
    def test_catalog_has_expected_skills(self) -> None:
        names = {path.name for path in skill_directories()}
        self.assertEqual(EXPECTED_SKILLS, names)

    def test_entrypoints_and_metadata_match(self) -> None:
        for skill_dir in skill_directories():
            with self.subTest(skill=skill_dir.name):
                text = (skill_dir / "SKILL.md").read_text(encoding="utf-8")
                fields = frontmatter(text)
                self.assertEqual(skill_dir.name, fields.get("name"))
                self.assertTrue(fields.get("description"))
                self.assertLessEqual(
                    len(re.findall(r"[A-Za-z0-9_$-]+", fields["description"])),
                    40,
                    "Keep always-loaded descriptions concise",
                )
                self.assertEqual("true", fields.get("disable-model-invocation"))

                metadata_path = skill_dir / "agents" / "openai.yaml"
                metadata = metadata_path.read_text(encoding="utf-8")
                self.assertIn("interface:\n", metadata)
                self.assertIn("policy:\n  allow_implicit_invocation: false", metadata)
                interface: dict[str, str] = {}
                for key in ("display_name", "short_description", "default_prompt"):
                    match = re.search(rf"(?m)^  {key}: \"(.+)\"$", metadata)
                    self.assertIsNotNone(match)
                    interface[key] = match.group(1)
                self.assertGreaterEqual(len(interface["short_description"]), 25)
                self.assertLessEqual(len(interface["short_description"]), 64)
                self.assertIn(f"${skill_dir.name}", interface["default_prompt"])

                referenced_paths = re.findall(
                    r"`((?:\./)?(?:references|scripts)/[^`\s]+)`", text
                )
                referenced_paths.extend(
                    re.findall(
                        r"<skill-directory>/((?:references|scripts)/[^\s\\\"]+)",
                        text,
                    )
                )
                for relative in referenced_paths:
                    relative = relative.removeprefix("./")
                    self.assertTrue(
                        (skill_dir / relative).is_file(),
                        f"missing {skill_dir / relative}",
                    )

    def test_runtime_skill_folders_exclude_test_artifacts(self) -> None:
        for skill_dir in skill_directories():
            tracked = subprocess.check_output(
                [
                    "git",
                    "ls-files",
                    "--cached",
                    "--others",
                    "--exclude-standard",
                    "-z",
                    str(skill_dir.relative_to(ROOT)),
                ],
                cwd=ROOT,
            ).decode().split("\0")
            for relative_text in filter(None, tracked):
                path = Path(relative_text)
                if not (ROOT / path).is_file():
                    continue
                self.assertNotIn("tests", path.parts, path)
                self.assertNotIn("__pycache__", path.parts, path)
                self.assertNotEqual(".pyc", path.suffix, path)
                self.assertNotIn(path.name, {".DS_Store", "dot_DS_Store"})

    def test_cleanup_skills_keep_scope_and_disclosure_boundaries(self) -> None:
        required_by_skill = {
            "engineering/improve-code-comments": (
                "do not treat every pre-existing dirty file as authorized scope",
                "Preserve copyright and license notices",
                "Do not use word blacklists, comment counts, or density targets",
                "Leave the comment in place until that knowledge has a durable home",
            ),
            "productivity/sanitize-artifacts": (
                "Do not treat every dirty or recently viewed file as authorized scope",
                "This is not a general security, malware, or data-loss-prevention audit",
                "required disclosures",
                "available tools could not inspect",
            ),
        }
        for relative, required_phrases in required_by_skill.items():
            text = (SKILLS_ROOT / relative / "SKILL.md").read_text(
                encoding="utf-8"
            )
            with self.subTest(skill=relative):
                for phrase in required_phrases:
                    self.assertIn(phrase, text)

    def test_paired_variants_keep_their_shared_contracts(self) -> None:
        pairs = {
            (
                "productivity/grilling",
                "productivity/review-gated-grilling",
            ): (
                "Interview me relentlessly",
                "decision tree in dependency order",
                "per-turn maximum as a ceiling",
                "wait for feedback",
                "explain which scenarios favor each option and let the user choose",
                "Do not modify code before approval.",
            ),
            (
                "engineering/implement-in-stages",
                "engineering/review-gated-implementation",
            ): (
                "at most 10 stages",
                "independently checkable result",
                "verify the stage contract rather than implementation details",
                "in the current tree",
                "revise only unfinished stages",
                "Never stage or commit unrelated pre-existing changes.",
            ),
        }
        for relative_pair, required_phrases in pairs.items():
            texts = [
                (SKILLS_ROOT / relative / "SKILL.md").read_text(encoding="utf-8")
                for relative in relative_pair
            ]
            for phrase in required_phrases:
                with self.subTest(pair=relative_pair, phrase=phrase):
                    for text in texts:
                        self.assertIn(phrase, text)

    def test_consensus_variants_keep_their_bounded_protocol(self) -> None:
        paths = (
            SKILLS_ROOT / "productivity/consensus-gated-grilling/SKILL.md",
            SKILLS_ROOT / "engineering/consensus-change-review/SKILL.md",
            SKILLS_ROOT / "engineering/consensus-review-loop/SKILL.md",
        )
        required_phrases = (
            "at most two exchange rounds",
            "fresh, read-only tie-breaker",
            "ask the user to adjudicate",
        )
        for path in paths:
            text = path.read_text(encoding="utf-8")
            with self.subTest(skill=path.parent.name):
                for phrase in required_phrases:
                    self.assertIn(phrase, text)

    def test_consensus_variants_preserve_base_contracts(self) -> None:
        required_by_skill = {
            "productivity/consensus-gated-grilling": (
                "decision tree in dependency order",
                "available context or tools",
                "per-turn maximum as a ceiling",
                "with the conversation context",
                "or the positive number the user requested",
                "distinct, non-leading perspectives",
                "Never silently self-review or reduce their number.",
                "when relevant, implementation authorization",
                "Do not modify code before approval.",
            ),
            "engineering/consensus-change-review": (
                "without rushing a healthy reviewer",
                "Record rejected findings with the reason.",
                "through the implementation owner when one exists, or fix them yourself",
                "If none are accepted and none are disputed, skip to the summary.",
            ),
            "engineering/consensus-review-loop": (
                "relevant code, tests, and call sites",
                "without rushing a healthy reviewer",
                "Record rejected findings with the reason.",
                "through the implementation owner when one exists, or fix them yourself",
                "After the last allowed round, report that boundary as a residual risk.",
            ),
        }
        for relative, required_phrases in required_by_skill.items():
            text = (SKILLS_ROOT / relative / "SKILL.md").read_text(encoding="utf-8")
            with self.subTest(skill=relative):
                for phrase in required_phrases:
                    self.assertIn(phrase, text)

    def test_suno_explorer_declares_create_companion(self) -> None:
        explorer = (
            SKILLS_ROOT / "creative/suno-music-explorer/SKILL.md"
        ).read_text(encoding="utf-8")
        self.assertIn("`$suno-create`", explorer)
        self.assertIn("install both skills", explorer)

    def test_manual_evaluation_cases_reference_real_fixtures(self) -> None:
        manifests = sorted(ROOT.glob("tests/**/cases.json"))
        self.assertTrue(manifests)
        for manifest_path in manifests:
            with self.subTest(manifest=manifest_path):
                root = manifest_path.parent
                manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
                skill = manifest.get("skill")
                self.assertIn(skill, EXPECTED_SKILLS)
                self.assertEqual(root.name, skill)

                execution = manifest.get("execution")
                self.assertIsInstance(execution, dict)
                self.assertEqual(
                    {"isolation", "context", "evaluation"}, set(execution)
                )
                for value in execution.values():
                    self.assertIsInstance(value, str)
                    self.assertTrue(value.strip())

                cases = manifest.get("cases")
                self.assertIsInstance(cases, list)
                self.assertTrue(cases)
                case_ids: set[str] = set()
                for case in cases:
                    self.assertIsInstance(case, dict)
                    case_id = case.get("id")
                    self.assertIsInstance(case_id, str)
                    self.assertTrue(case_id.strip())
                    self.assertNotIn(case_id, case_ids)
                    case_ids.add(case_id)

                    prompt = case.get("prompt")
                    self.assertIsInstance(prompt, str)
                    self.assertTrue(prompt.strip())
                    fixture = case.get("fixture")
                    self.assertIsInstance(fixture, str)
                    fixture_path = root / fixture
                    fixture_root = (root / "fixtures").resolve()
                    resolved_fixture = fixture_path.resolve()
                    self.assertTrue(
                        resolved_fixture.is_relative_to(fixture_root),
                        f"fixture escapes {fixture_root}: {fixture_path}",
                    )
                    self.assertTrue(resolved_fixture.is_dir(), resolved_fixture)
                    for child in resolved_fixture.rglob("*"):
                        if child.is_symlink():
                            self.assertTrue(
                                child.resolve().is_relative_to(resolved_fixture),
                                f"fixture symlink escapes its case: {child}",
                            )

                    expectations = case.get("expectations")
                    self.assertIsInstance(expectations, dict)
                    required = expectations.get("required")
                    forbidden = expectations.get("forbidden")
                    self.assertIsInstance(required, list)
                    self.assertIsInstance(forbidden, list)
                    for forbidden_item in forbidden:
                        self.assertIsInstance(forbidden_item, str)
                        self.assertTrue(forbidden_item.strip())
                    for required_item in required:
                        self.assertIsInstance(required_item, dict)
                        criterion = required_item.get("issue") or required_item.get(
                            "criterion"
                        )
                        self.assertIsInstance(criterion, str)
                        self.assertTrue(criterion.strip())
                        anchor = required_item.get("anchor")
                        self.assertIsInstance(anchor, str)
                        self.assertTrue(anchor.strip())
                        priorities = required_item.get("priorities")
                        self.assertIsInstance(priorities, list)
                        self.assertTrue(
                            set(priorities).issubset(VALID_PRIORITIES),
                            required_item,
                        )


if __name__ == "__main__":
    unittest.main()
