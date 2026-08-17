from __future__ import annotations

import json
import re
import subprocess
import unittest
from pathlib import Path


ROOT = Path(__file__).resolve().parents[2]
SKILLS_ROOT = ROOT / "skills"
EXPECTED_SKILLS = {
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
}


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

    def test_review_tests_manual_cases_reference_real_fixtures(self) -> None:
        root = ROOT / "tests" / "review-tests"
        manifest = json.loads((root / "cases.json").read_text(encoding="utf-8"))
        self.assertEqual("review-tests", manifest["skill"])
        for case in manifest["cases"]:
            with self.subTest(case=case["id"]):
                self.assertTrue((root / case["fixture"]).is_dir())


if __name__ == "__main__":
    unittest.main()
