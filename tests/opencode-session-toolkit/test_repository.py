from __future__ import annotations

import re
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
SKILL = ROOT / "skills" / "productivity" / "opencode-session-toolkit"


class RepositoryTest(unittest.TestCase):
    def test_skill_entrypoints_are_concise_and_reference_real_files(self) -> None:
        skill_md = SKILL / "SKILL.md"
        text = skill_md.read_text(encoding="utf-8")
        self.assertLessEqual(len(text.splitlines()), 120, skill_md)
        self.assertRegex(
            text,
            r"\A---\nname: opencode-session-toolkit\ndescription: .+\n"
            r"disable-model-invocation: true\n---",
        )
        for relative in re.findall(r"`(references/[^`]+\.md)`", text):
            self.assertTrue(
                (SKILL / relative).is_file(), f"missing {SKILL / relative}"
            )

    def test_runtime_package_does_not_contain_maintainer_install_docs(self) -> None:
        for markdown in SKILL.rglob("*.md"):
            text = markdown.read_text(encoding="utf-8").lower()
            self.assertNotIn("github release", text, markdown)
            self.assertNotIn("skills@latest add", text, markdown)


if __name__ == "__main__":
    unittest.main()
