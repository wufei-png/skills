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


def skill_markdown(frontmatter_text: str) -> str:
    return f"---\n{frontmatter_text}\n---\n# Synthetic\n"


def metadata_with(policy_body: str) -> str:
    return (
        'interface:\n  display_name: "Alpha"\n'
        '  short_description: "Synthetic contract fixture for tests."\n'
        '  default_prompt: "Use $alpha."\n'
        f"policy:\n{policy_body}\n"
    )


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
        entrypoint_text: str | None = None,
        metadata_text: str | None = None,
    ) -> Path:
        skill_dir = self.skills / category / name
        skill_dir.mkdir(parents=True)
        if entrypoint:
            flag = "true" if manual_only else "false"
            text = entrypoint_text or (
                f"---\nname: {name}\ndescription: Synthetic contract fixture.\n"
                f"disable-model-invocation: {flag}\n---\n"
            )
            (skill_dir / "SKILL.md").write_text(text, encoding="utf-8")
        if metadata:
            (skill_dir / "agents").mkdir()
            policy_text = (
                "policy:\n  allow_implicit_invocation: false"
                if policy
                else "policy:\n  allow_implicit_invocation: true"
            )
            text = metadata_text or (
                f'interface:\n  display_name: "{name}"\n'
                f'  short_description: "Synthetic contract fixture for tests."\n'
                f'  default_prompt: "Use ${name} for the synthetic task."\n'
                f"{policy_text}\n"
            )
            (skill_dir / "agents" / "openai.yaml").write_text(text, encoding="utf-8")
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
        self.assertTrue(any("boolean true" in error for error in errors), errors)

    def test_manual_only_metadata_policy_is_required(self) -> None:
        self.add_skill("alpha", policy=False)
        errors = inspect_skill_tree(self.skills).errors
        self.assertTrue(
            any("boolean false" in error for error in errors),
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


class ManualOnlyYamlContractTest(TreeFixture):
    def assert_contract_error(
        self,
        pattern: str,
        *,
        entrypoint_text: str | None = None,
        metadata_text: str | None = None,
    ) -> list[str]:
        self.add_skill(
            "alpha",
            entrypoint_text=entrypoint_text,
            metadata_text=metadata_text,
        )
        errors = inspect_skill_tree(self.skills).errors
        self.assertTrue(errors)
        self.assertTrue(any(pattern in error for error in errors), errors)
        return errors

    def test_policy_string_is_rejected(self) -> None:
        errors = self.assert_contract_error(
            "boolean false",
            metadata_text=metadata_with("  allow_implicit_invocation: false-positive"),
        )
        self.assertTrue(any("false-positive" in error for error in errors), errors)

    def test_quoted_policy_value_is_rejected(self) -> None:
        self.assert_contract_error(
            "boolean false",
            metadata_text=metadata_with('  allow_implicit_invocation: "false"'),
        )

    def test_numeric_policy_value_is_rejected(self) -> None:
        self.assert_contract_error(
            "boolean false",
            metadata_text=metadata_with("  allow_implicit_invocation: 0"),
        )

    def test_block_scalar_cannot_mask_true_policy(self) -> None:
        errors = self.assert_contract_error(
            "boolean false",
            metadata_text=(
                "description: |\n"
                "  policy:\n"
                "  allow_implicit_invocation: false\n"
                "policy:\n"
                "  allow_implicit_invocation: true\n"
            ),
        )
        self.assertTrue(any("got True" in error for error in errors), errors)

    def test_block_scalar_without_real_policy_is_rejected(self) -> None:
        self.assert_contract_error(
            "policy mapping",
            metadata_text=(
                "description: |\n  policy:\n  allow_implicit_invocation: false\n"
            ),
        )

    def test_missing_policy_is_rejected(self) -> None:
        self.assert_contract_error(
            "policy mapping",
            metadata_text=(
                'interface:\n  display_name: "Alpha"\n'
                '  short_description: "Synthetic contract fixture for tests."\n'
                '  default_prompt: "Use $alpha."\n'
            ),
        )

    def test_non_mapping_policy_is_rejected(self) -> None:
        self.assert_contract_error(
            "policy mapping",
            metadata_text="policy: disabled\n",
        )

    def test_duplicate_policy_key_is_rejected(self) -> None:
        errors = self.assert_contract_error(
            "duplicate mapping key",
            metadata_text=(
                "policy:\n  allow_implicit_invocation: false\n"
                "policy:\n  allow_implicit_invocation: false\n"
            ),
        )
        self.assertTrue(any("'policy'" in error for error in errors), errors)

    def test_duplicate_policy_value_is_rejected(self) -> None:
        self.assert_contract_error(
            "duplicate mapping key",
            metadata_text=(
                "policy:\n  allow_implicit_invocation: false\n"
                "  allow_implicit_invocation: false\n"
            ),
        )

    def test_non_string_metadata_key_is_rejected(self) -> None:
        self.assert_contract_error(
            "non-string mapping key",
            metadata_text="true: value\n",
        )

    def test_merge_keys_are_rejected(self) -> None:
        self.assert_contract_error(
            "merge keys",
            metadata_text=(
                "base: &base\n"
                "  allow_implicit_invocation: false\n"
                "policy:\n"
                "  <<: *base\n"
            ),
        )

    def test_invalid_metadata_yaml_is_rejected(self) -> None:
        self.assert_contract_error(
            "invalid YAML",
            metadata_text="policy: [unterminated\n",
        )

    def test_non_mapping_metadata_is_rejected(self) -> None:
        self.assert_contract_error(
            "expected a YAML mapping",
            metadata_text="- policy\n",
        )

    def test_multiple_metadata_documents_are_rejected(self) -> None:
        self.assert_contract_error(
            "invalid YAML",
            metadata_text=(
                "policy:\n  allow_implicit_invocation: false\n"
                "---\n"
                "policy:\n  allow_implicit_invocation: true\n"
            ),
        )

    def test_string_true_flag_is_rejected(self) -> None:
        self.assert_contract_error(
            "boolean true",
            entrypoint_text=skill_markdown(
                'name: alpha\ndescription: Synthetic.\ndisable-model-invocation: "true"'
            ),
        )

    def test_numeric_true_flag_is_rejected(self) -> None:
        self.assert_contract_error(
            "boolean true",
            entrypoint_text=skill_markdown(
                "name: alpha\ndescription: Synthetic.\ndisable-model-invocation: 1"
            ),
        )

    def test_false_flag_is_rejected(self) -> None:
        self.assert_contract_error(
            "boolean true",
            entrypoint_text=skill_markdown(
                "name: alpha\ndescription: Synthetic.\ndisable-model-invocation: false"
            ),
        )

    def test_missing_flag_is_rejected(self) -> None:
        self.assert_contract_error(
            "must set disable-model-invocation: true",
            entrypoint_text=skill_markdown("name: alpha\ndescription: Synthetic."),
        )

    def test_duplicate_flag_is_rejected(self) -> None:
        errors = self.assert_contract_error(
            "duplicate mapping key",
            entrypoint_text=skill_markdown(
                "name: alpha\ndescription: Synthetic.\n"
                "disable-model-invocation: true\n"
                "disable-model-invocation: true"
            ),
        )
        self.assertTrue(
            any("disable-model-invocation" in error for error in errors), errors
        )

    def test_block_scalar_cannot_mask_false_flag(self) -> None:
        self.assert_contract_error(
            "boolean true",
            entrypoint_text=skill_markdown(
                "name: alpha\ndescription: |\n"
                "  disable-model-invocation: true\n"
                "disable-model-invocation: false"
            ),
        )

    def test_invalid_frontmatter_yaml_is_rejected(self) -> None:
        self.assert_contract_error(
            "invalid YAML",
            entrypoint_text=skill_markdown("name: [unterminated"),
        )

    def test_non_mapping_frontmatter_is_rejected(self) -> None:
        self.assert_contract_error(
            "expected a YAML mapping",
            entrypoint_text=skill_markdown("- alpha"),
        )

    def test_missing_frontmatter_closing_is_rejected(self) -> None:
        self.assert_contract_error(
            "closing ---",
            entrypoint_text="---\nname: alpha\ndisable-model-invocation: true\n",
        )


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
