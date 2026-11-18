from __future__ import annotations

import subprocess
import tempfile
import unittest
from pathlib import Path

from skill_contract import (
    InstallerError,
    compare_sets,
    inspect_skill_tree,
    parse_installer_output,
    verify_installer,
)

INSTALLER_OUTPUT = """\
\x1b[?25l│
◇  Found 2 skills
\x1b[?25h│
◇  Available Skills
│
│    game-experience-review
│
│      Review game experience through independent, code-informed perspectives.
│
│    wait-what
│
└  Use --skill <name> to install specific skills
"""


def installer_output(*names: str) -> str:
    listed = "\n│\n".join(f"│    {name}" for name in names)
    return (
        f"│\n◇  Found {len(names)} skills\n│\n◇  Available Skills\n│\n"
        f"{listed}\n│\n└  Use --skill <name> to install specific skills\n"
    )


def runner_for(output: str, returncode: int = 0, stderr: str = ""):
    def runner(command, **kwargs):
        return subprocess.CompletedProcess(command, returncode, output, stderr)

    return runner


class InstallerOutputParsingTest(unittest.TestCase):
    def test_installer_output_shape_is_parsed(self) -> None:
        self.assertEqual(
            ["game-experience-review", "wait-what"],
            parse_installer_output(INSTALLER_OUTPUT),
        )

    def test_truncated_output_is_rejected(self) -> None:
        truncated = INSTALLER_OUTPUT.split("└", 1)[0]
        with self.assertRaisesRegex(InstallerError, "truncated"):
            parse_installer_output(truncated)

    def test_missing_listing_is_rejected(self) -> None:
        with self.assertRaisesRegex(InstallerError, "no skill names"):
            parse_installer_output("◇  Available Skills\n│\n└  Use --skill <name>\n")

    def test_missing_summary_is_rejected(self) -> None:
        output = INSTALLER_OUTPUT.replace("◇  Found 2 skills\n", "")
        with self.assertRaisesRegex(InstallerError, "Found N skills"):
            parse_installer_output(output)

    def test_count_mismatch_is_rejected(self) -> None:
        output = INSTALLER_OUTPUT.replace("Found 2 skills", "Found 3 skills")
        with self.assertRaisesRegex(InstallerError, "reports 3 skills but lists 2"):
            parse_installer_output(output)

    def test_duplicate_names_are_rejected(self) -> None:
        with self.assertRaisesRegex(InstallerError, "duplicate skills"):
            parse_installer_output(installer_output("alpha", "alpha"))

    def test_invalid_names_are_rejected(self) -> None:
        with self.assertRaisesRegex(InstallerError, "invalid skill names"):
            parse_installer_output(installer_output("Not_Kebab"))


class TreeFixture(unittest.TestCase):
    def setUp(self) -> None:
        self.temporary = tempfile.TemporaryDirectory()
        self.addCleanup(self.temporary.cleanup)
        self.root = Path(self.temporary.name)
        self.skills = self.root / "skills"
        for category in ("creative", "engineering", "productivity"):
            (self.skills / category).mkdir(parents=True)

    def add_skill(
        self,
        name: str,
        category: str = "productivity",
        *,
        entrypoint: bool = True,
        metadata: bool = True,
        manual_only: bool = True,
        policy: bool = True,
    ) -> Path:
        skill_dir = self.skills / category / name
        skill_dir.mkdir(parents=True)
        if entrypoint:
            flag = "true" if manual_only else "false"
            (skill_dir / "SKILL.md").write_text(
                f"---\nname: {name}\ndescription: Synthetic contract fixture.\n"
                f"disable-model-invocation: {flag}\n---\n",
                encoding="utf-8",
            )
        if metadata:
            (skill_dir / "agents").mkdir()
            policy_text = (
                "policy:\n  allow_implicit_invocation: false"
                if policy
                else "policy:\n  allow_implicit_invocation: true"
            )
            (skill_dir / "agents" / "openai.yaml").write_text(
                f'interface:\n  display_name: "{name}"\n'
                f'  short_description: "Synthetic contract fixture for tests."\n'
                f'  default_prompt: "Use ${name} for the synthetic task."\n'
                f"{policy_text}\n",
                encoding="utf-8",
            )
        return skill_dir


class SkillTreeContractTest(TreeFixture):
    def test_valid_tree_matches_expected_names(self) -> None:
        self.add_skill("alpha")
        tree = inspect_skill_tree(self.skills)
        self.assertEqual([], tree.errors)
        self.assertEqual(["alpha"], tree.names)

    def test_complete_directory_removal_is_reported(self) -> None:
        self.add_skill("alpha")
        errors = compare_sets(
            "repository contract",
            {"alpha", "beta"},
            inspect_skill_tree(self.skills).names,
        )
        self.assertEqual(["repository contract: missing beta"], errors)

    def test_extra_directory_is_reported(self) -> None:
        self.add_skill("alpha")
        self.add_skill("beta")
        errors = compare_sets(
            "repository contract", {"alpha"}, inspect_skill_tree(self.skills).names
        )
        self.assertEqual(["repository contract: unexpected beta"], errors)

    def test_missing_entrypoint_is_reported(self) -> None:
        self.add_skill("alpha", entrypoint=False)
        errors = inspect_skill_tree(self.skills).errors
        self.assertTrue(any("missing SKILL.md" in error for error in errors), errors)

    def test_missing_metadata_is_reported(self) -> None:
        self.add_skill("alpha", metadata=False)
        errors = inspect_skill_tree(self.skills).errors
        self.assertTrue(
            any("missing agents/openai.yaml" in error for error in errors), errors
        )

    def test_manual_only_entrypoint_flag_is_required(self) -> None:
        self.add_skill("alpha", manual_only=False)
        errors = inspect_skill_tree(self.skills).errors
        self.assertTrue(
            any("disable-model-invocation: true" in error for error in errors), errors
        )

    def test_manual_only_metadata_policy_is_required(self) -> None:
        self.add_skill("alpha", policy=False)
        errors = inspect_skill_tree(self.skills).errors
        self.assertTrue(
            any("allow_implicit_invocation: false" in error for error in errors),
            errors,
        )

    def test_duplicate_names_across_categories_are_reported(self) -> None:
        self.add_skill("alpha", "productivity")
        self.add_skill("alpha", "engineering")
        errors = inspect_skill_tree(self.skills).errors
        self.assertTrue(
            any("duplicate skill name alpha" in error for error in errors), errors
        )

    def test_unexpected_category_is_reported(self) -> None:
        self.add_skill("alpha", "other")
        errors = inspect_skill_tree(self.skills).errors
        self.assertTrue(
            any("unexpected skill category" in error for error in errors), errors
        )

    def test_non_kebab_skill_name_is_reported(self) -> None:
        self.add_skill("Not_Kebab")
        errors = inspect_skill_tree(self.skills).errors
        self.assertTrue(any("not kebab-case" in error for error in errors), errors)


class InstallerVerificationTest(TreeFixture):
    def test_installer_and_repository_tree_agree(self) -> None:
        self.add_skill("alpha")
        report = verify_installer(
            "skills@1.9.0",
            self.root,
            {"alpha"},
            runner=runner_for(installer_output("alpha")),
        )
        self.assertEqual([], report.errors)
        self.assertEqual(["alpha"], report.repository_names)
        self.assertEqual(["alpha"], report.discovered_names)

    def test_installer_nonzero_exit_is_a_failure(self) -> None:
        self.add_skill("alpha")
        report = verify_installer(
            "skills@1.9.0",
            self.root,
            {"alpha"},
            runner=runner_for("", returncode=1, stderr="npm ERR! network failure"),
        )
        self.assertEqual([], report.discovered_names)
        self.assertTrue(
            any(
                "exited with 1" in error and "network failure" in error
                for error in report.errors
            ),
            report.errors,
        )

    def test_truncated_installer_output_is_not_inferred(self) -> None:
        self.add_skill("alpha")
        truncated = installer_output("alpha").split("└", 1)[0]
        report = verify_installer(
            "skills@latest",
            self.root,
            {"alpha"},
            runner=runner_for(truncated),
        )
        self.assertEqual([], report.discovered_names)
        self.assertTrue(
            any("truncated" in error for error in report.errors), report.errors
        )

    def test_installer_omission_and_addition_are_both_reported(self) -> None:
        self.add_skill("alpha")
        report = verify_installer(
            "skills@latest",
            self.root,
            {"alpha"},
            runner=runner_for(installer_output("beta")),
        )
        self.assertIn("installer discovery: missing alpha", report.errors)
        self.assertIn("installer discovery: unexpected beta", report.errors)

    def test_missing_repository_directory_blocks_installer_check(self) -> None:
        self.add_skill("alpha")
        report = verify_installer(
            "skills@1.9.0",
            self.root,
            {"alpha", "beta"},
            runner=runner_for(installer_output("alpha")),
        )
        self.assertIn("repository contract: missing beta", report.errors)


if __name__ == "__main__":
    unittest.main()
