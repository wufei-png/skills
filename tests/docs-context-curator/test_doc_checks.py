from __future__ import annotations

import json
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path


ROOT = Path(__file__).resolve().parents[2]
SCRIPT = ROOT / "skills/engineering/docs-context-curator/scripts/doc_checks.py"


class DocumentationChecksTest(unittest.TestCase):
    def setUp(self):
        self.temporary = tempfile.TemporaryDirectory()
        self.addCleanup(self.temporary.cleanup)
        self.root = Path(self.temporary.name).resolve()

    def write(self, path, text):
        destination = self.root / path
        destination.parent.mkdir(parents=True, exist_ok=True)
        destination.write_text(text, encoding="utf-8")
        return destination

    def run_check(self, command, *options, code=0):
        result = subprocess.run(
            [sys.executable, str(SCRIPT), command, "--root", str(self.root), *options],
            capture_output=True, text=True,
        )
        self.assertEqual(code, result.returncode, result.stdout + result.stderr)
        self.assertNotIn("Traceback", result.stderr)
        return json.loads(result.stdout)

    def plan(self, entries):
        return str(self.write("moves.json", json.dumps(entries)))

    def snapshot(self):
        return {str(p.relative_to(self.root)): p.read_bytes() for p in self.root.rglob("*") if p.is_file() and not p.is_symlink()}

    def test_inventory_is_bounded_and_omits_bodies_and_excluded_history(self):
        self.write("docs/a.md", "# Current\nSECRET_BODY\n")
        self.write("docs/b.md", "# Other\n")
        self.write("docs/archive/old.md", "# Past\n")
        report = self.run_check("inventory", "--path", "docs", "--exclude", "docs/archive", "--limit", "1")
        self.assertEqual(2, report["total"])
        self.assertTrue(report["has_more"])
        self.assertEqual("Current", report["items"][0]["title"])
        self.assertNotIn("SECRET_BODY", json.dumps(report))
        second = self.run_check("inventory", "--path", "docs", "--exclude", "docs/archive", "--limit", "1", "--offset", "1")
        self.assertEqual("docs/b.md", second["items"][0]["path"])

    def test_git_selection_preserves_standard_ignores_and_untracked_files(self):
        subprocess.run(["git", "init", "-q", str(self.root)], check=True)
        self.write(".gitignore", "docs/generated/\n")
        self.write("docs/tracked.md", "# Tracked\n")
        subprocess.run(["git", "-C", str(self.root), "add", "docs/tracked.md"], check=True)
        self.write("docs/new.md", "# New\n")
        self.write("docs/generated/noise.md", "# Generated\n")
        report = self.run_check("inventory", "--path", "docs")
        self.assertEqual({"docs/new.md", "docs/tracked.md"}, {item["path"] for item in report["items"]})
        included = self.run_check("inventory", "--path", "docs", "--include-ignored")
        self.assertEqual(3, included["total"])

    def test_git_file_scopes_are_literal_paths(self):
        subprocess.run(["git", "init", "-q", str(self.root)], check=True)
        for scope, other in (
            ("docs/file[old].md", "docs/fileo.md"),
            ("docs/file?.md", "docs/filex.md"),
        ):
            with self.subTest(scope=scope):
                self.write(scope, "# Selected\n")
                self.write(other, "# Outside the selected scope\n")
                report = self.run_check("inventory", "--path", scope)
                self.assertEqual([scope], [item["path"] for item in report["items"]])
                self.assertEqual(1, report["coverage"]["files_read"])

    def test_reference_lookup_includes_code_tests_and_configuration_candidates(self):
        self.write("docs/old.md", "# Old\n")
        self.write("docs/index.md", "[Earlier](old.md)\n")
        self.write("tests/test_snapshot.py", 'snapshot = Path("docs/old.md").read_text()\n')
        self.write("config.json", '{"fixture": "docs/old.md"}\n')
        before = self.snapshot()
        report = self.run_check("refs", "--target", "docs/old.md", "--path", "docs", "--path", "tests", "--path", "config.json")
        records = {(item["path"], item["kind"]) for item in report["items"]}
        self.assertIn(("tests/test_snapshot.py", "literal-candidate"), records)
        self.assertIn(("config.json", "literal-candidate"), records)
        self.assertIn(("docs/index.md", "markdown"), records)
        self.assertEqual(before, self.snapshot())

    def test_reference_locations_handle_unicode_spaces_and_directory_targets(self):
        self.write("docs/旧记录/file one.md", "# Old\n")
        self.write("docs/index.md", "Intro\n[Old](%E6%97%A7%E8%AE%B0%E5%BD%95/file%20one.md)\n")
        report = self.run_check("refs", "--target", "docs/旧记录", "--path", "docs/index.md")
        self.assertEqual(1, report["total"])
        self.assertEqual(2, report["items"][0]["line"])

    def test_html_base_resolves_relative_links_from_the_declared_base(self):
        self.write("media/frame.png", "synthetic image placeholder")
        self.write("docs/review.html", '<base href="../media/"><img src="frame.png"><a href="missing.txt">Missing</a>')
        report = self.run_check("links", "--path", "docs/review.html", code=1)
        self.assertEqual(["missing.txt"], [item["token"] for item in report["items"]])
        refs = self.run_check("refs", "--target", "media/frame.png", "--path", "docs/review.html")
        self.assertIn("html", {item["kind"] for item in refs["items"]})

    def test_external_base_does_not_create_local_false_positives(self):
        self.write("docs/site.html", '<base href="https://example.invalid/docs/"><a href="remote.md">Remote</a>')
        report = self.run_check("links", "--path", "docs/site.html")
        self.assertEqual([], report["items"])

    def test_website_and_template_bases_leave_dependent_links_unresolved(self):
        missing_uri = (self.root / "docs/missing.png").as_uri()
        for base in ("/", "/docs/", "{{site.baseurl}}/", "${SITE_ROOT}/", "<% base %>/"):
            with self.subTest(base=base):
                html = f'<base href="{base}"><img src="frame.png">'
                self.write("docs/site.html", html)
                report = self.run_check("links", "--path", "docs/site.html")
                self.assertEqual([], report["items"])
                self.write("docs/site.html", html + f'<img src="{missing_uri}">')
                report = self.run_check("links", "--path", "docs/site.html", code=1)
                self.assertEqual([missing_uri], [item["token"] for item in report["items"]])

    def test_markdown_definitions_images_parentheses_and_escaped_urls(self):
        self.write("docs/guide(v2).md", "# Guide\n")
        self.write("docs/file one.md", "# Spaces\n")
        self.write("docs/index.md", '[Guide](guide(v2).md "Title")\n![Image](file%20one.md)\n[ref]: <file one.md> "Title"\n[Escaped](guide\\(v2\\).md)\n')
        self.assertEqual(0, self.run_check("links", "--path", "docs/index.md")["total"])

    def test_fenced_and_inline_examples_are_not_static_link_failures(self):
        self.write("docs/index.md", '# Guide\n```markdown\n[Example](absent.md)\n```\n`[Other](absent-2.md)`\n~~~text\n<a href="absent-3.md">Example</a>\n~~~\n[Real](missing.md)\n')
        report = self.run_check("links", "--path", "docs/index.md", code=1)
        self.assertEqual(["missing.md"], [item["token"] for item in report["items"]])
        self.assertEqual(9, report["items"][0]["line"])

    def test_commented_markdown_links_are_not_checked(self):
        for comment in (
            "<!-- [Old](retired.md) -->\n",
            "<!--\n[Old](retired.md)\n[old]: retired-reference.md\n-->\n",
            "<!-- Unmatched ` and [Old](retired.md) -->\n",
        ):
            with self.subTest(comment=comment):
                self.write("docs/index.md", comment + "[`Real`](missing.md)\n")
                report = self.run_check("links", "--path", "docs/index.md", code=1)
                self.assertEqual(["missing.md"], [item["token"] for item in report["items"]])
                self.assertEqual(comment.count("\n") + 1, report["items"][0]["line"])

    def test_multiline_inline_code_is_not_checked(self):
        for example in (
            "`Wrapped\n[Example](absent.md)\ncode`\n",
            '``Wrapped `\n<a href="absent.md">Example</a>\n<!-- unfinished comment``\n',
            "``Wrapped ```\n[Example](absent.md)\ncode``\n",
        ):
            with self.subTest(example=example):
                self.write("docs/index.md", example + "[Real](missing.md)\n")
                report = self.run_check("links", "--path", "docs/index.md", code=1)
                self.assertEqual(["missing.md"], [item["token"] for item in report["items"]])
                self.assertEqual(example.count("\n") + 1, report["items"][0]["line"])

    def test_unmatched_backticks_do_not_hide_links_in_later_paragraphs(self):
        for newline in ("\n", "\r\n"):
            with self.subTest(newline=newline):
                text = "Unmatched ` in this paragraph.\n\n[Real](missing.md)\n\nAnother unmatched ` here.\n"
                self.write("docs/index.md", text.replace("\n", newline))
                report = self.run_check("links", "--path", "docs/index.md", code=1)
                self.assertEqual(["missing.md"], [item["token"] for item in report["items"]])
                self.assertEqual(3, report["items"][0]["line"])

    def test_links_do_not_claim_fragment_remote_template_or_build_validation(self):
        self.write("docs/guide.md", "# Guide\n")
        self.write("docs/index.md", '[Local](guide.md#unknown-heading)\n[Remote](https://example.invalid/page)\n[Template]({{path}}/guide.md)\n[Site](/reference/)\n[Engine](res://docs/guide.md)\n')
        report = self.run_check("links", "--path", "docs/index.md")
        self.assertEqual([], report["items"])
        self.assertTrue(any("fragment" in item for item in report["coverage"]["limitations"]))

    def test_oversized_and_binary_sources_make_reference_scan_incomplete(self):
        self.write("docs/old.md", "# Old\n")
        self.write("sources/large.txt", "x" * 100)
        self.write("sources/binary.dat", "\0docs/old.md")
        report = self.run_check("refs", "--target", "docs/old.md", "--path", "sources", "--max-bytes", "30", code=1)
        self.assertEqual(0, report["total"])
        self.assertEqual(2, report["coverage"]["skipped"])

    def test_moves_use_supplied_destinations_and_do_not_write(self):
        self.write("docs/a/report.md", "# A\n")
        self.write("docs/b/report.md", "# B\n")
        plan = self.plan([
            {"source": "docs/a/report.md", "target": "history/a/report.md"},
            {"source": "docs/b/report.md", "target": "history/b/report.md"},
        ])
        before = self.snapshot()
        for _ in range(2):
            report = self.run_check("moves", "--plan", plan)
            self.assertEqual([], report["items"])
        self.assertEqual(before, self.snapshot())
        self.assertFalse((self.root / "history").exists())

    def test_moves_detect_same_name_collisions_and_case_collisions(self):
        self.write("docs/a.md", "# A\n")
        self.write("docs/b.md", "# B\n")
        for a, b in [("history/report.md", "history/report.md"), ("history/Report.md", "history/report.md")]:
            plan = self.plan([{"source": "docs/a.md", "target": a}, {"source": "docs/b.md", "target": b}])
            report = self.run_check("moves", "--plan", plan, code=1)
            self.assertIn("conflicting-moves", {item["kind"] for item in report["items"]})

    def test_moves_detect_occupied_targets_and_parent_files(self):
        self.write("docs/a.md", "# A\n")
        self.write("history", "Existing file\n")
        plan = self.plan([{"source": "docs/a.md", "target": "history/a.md"}])
        report = self.run_check("moves", "--plan", plan, code=1)
        self.assertEqual("target-parent-is-file", report["items"][0]["kind"])
        plan = self.plan([{"source": "docs/a.md", "target": "history"}])
        report = self.run_check("moves", "--plan", plan, code=1)
        self.assertIn("occupied-target", {item["kind"] for item in report["items"]})

    def test_directory_moves_reject_overlap_and_source_target_chains(self):
        self.write("docs/bundle/evidence.json", "{}\n")
        self.write("docs/other.md", "# Other\n")
        plan = self.plan([
            {"source": "docs/bundle", "target": "history/bundle"},
            {"source": "docs/bundle/evidence.json", "target": "history/snapshot.json"},
        ])
        self.assertIn("conflicting-moves", {item["kind"] for item in self.run_check("moves", "--plan", plan, code=1)["items"]})
        plan = self.plan([{"source": "docs/bundle", "target": "docs/bundle/archive"}])
        self.assertIn("overlapping-source-target", {item["kind"] for item in self.run_check("moves", "--plan", plan, code=1)["items"]})

    def test_invalid_scope_plan_and_traversal_return_structured_errors(self):
        for value in ("../outside", "/outside", "C:/outside", "docs\\outside"):
            report = self.run_check("inventory", "--path", value, code=2)
            self.assertIn("error", report)
        plan = self.write("moves.json", '[{"source": "../outside", "target": "history/outside"}]')
        self.assertIn("error", self.run_check("moves", "--plan", str(plan), code=2))
        plan.write_text("not JSON", encoding="utf-8")
        self.assertIn("error", self.run_check("moves", "--plan", str(plan), code=2))
        plan.write_text('[{"source": 123, "target": "history/a"}]', encoding="utf-8")
        self.assertIn("error", self.run_check("moves", "--plan", str(plan), code=2))

    def test_symlinked_scopes_and_bundles_are_not_followed(self):
        self.write("docs/real.md", "# Real\n")
        try:
            (self.root / "linked").symlink_to(self.root / "docs", target_is_directory=True)
        except (OSError, NotImplementedError):
            self.skipTest("symlinks unavailable")
        report = self.run_check("inventory", "--path", "linked", code=2)
        self.assertIn("symlink", report["error"])
        plan = self.plan([{"source": "docs", "target": "linked/archive"}])
        self.assertIn("error", self.run_check("moves", "--plan", plan, code=2))
        (self.root / "docs/link.md").symlink_to(self.root / "docs/real.md")
        plan = self.plan([{"source": "docs", "target": "history/docs"}])
        self.assertIn("source-bundle-contains-symlink", {item["kind"] for item in self.run_check("moves", "--plan", plan, code=1)["items"]})


if __name__ == "__main__":
    unittest.main()
