from __future__ import annotations

import importlib.util
import json
import shutil
import subprocess
import sys
import tempfile
import unittest
from datetime import datetime, timedelta
from pathlib import Path


REPO_ROOT = Path(__file__).resolve().parents[2]
SCANNER_PATH = (
    REPO_ROOT
    / "skills"
    / "productivity"
    / "codex-session-recovery"
    / "scripts"
    / "scan_codex_sessions.py"
)
FIXTURE_ROOT = Path(__file__).resolve().parent / "fixtures" / "codex_home"
PROJECT_CWD = "/Users/example/project"


def load_scanner():
    spec = importlib.util.spec_from_file_location("scan_codex_sessions", SCANNER_PATH)
    module = importlib.util.module_from_spec(spec)
    assert spec.loader is not None
    sys.modules[spec.name] = module
    spec.loader.exec_module(module)
    return module


class ScanCodexSessionsTest(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.codex_home = Path(self.tmp.name) / "codex_home_copy"
        shutil.copytree(FIXTURE_ROOT, self.codex_home)
        self.scanner = load_scanner()

    def tearDown(self):
        self.tmp.cleanup()

    def scan(self, **kwargs):
        defaults = {
            "codex_home": self.codex_home,
            "cwd": PROJECT_CWD,
            "since": None,
            "until": None,
            "timezone": "Asia/Shanghai",
            "query": None,
            "include_archived": False,
            "include_subagents": False,
            "limit": 20,
            "show_prompts": False,
        }
        defaults.update(kwargs)
        return self.scanner.scan(defaults)

    def ids(self, result):
        return [record["thread_id"] for record in result["records"]]

    def run_cli(self, *args):
        return subprocess.run(
            [sys.executable, str(SCANNER_PATH), *args],
            check=False,
            text=True,
            capture_output=True,
        )

    def test_default_scan_excludes_archived_and_subagent_sessions(self):
        result = self.scan()
        self.assertIn("active-main", self.ids(result))
        self.assertIn("duplicate-main", self.ids(result))
        self.assertNotIn("archived-main", self.ids(result))
        self.assertNotIn("subagent-main", self.ids(result))

    def test_include_archived_adds_archived_sessions(self):
        result = self.scan(include_archived=True)
        self.assertIn("archived-main", self.ids(result))

    def test_include_subagents_adds_subagent_sessions(self):
        result = self.scan(include_subagents=True)
        self.assertIn("subagent-main", self.ids(result))

    def test_malformed_lines_are_reported_without_failing_scan(self):
        result = self.scan()
        warnings = "\n".join(result["warnings"])
        self.assertIn("malformed JSON", warnings)
        self.assertIn("active-main", self.ids(result))

    def test_duplicate_active_and_archived_id_is_reported(self):
        result = self.scan(include_archived=True)
        duplicate = next(record for record in result["records"] if record["thread_id"] == "duplicate-main")
        self.assertIn("appears in active and archived sources", "\n".join(duplicate["warnings"]))

    def test_current_metadata_fields_are_exposed_and_searchable(self):
        session_index = self.codex_home / "session_index.jsonl"
        with session_index.open("a", encoding="utf-8") as handle:
            handle.write(
                '\n{"id":"named-main","thread_name":"Named recovery session",'
                '"updated_at":"2026-06-12T12:00:00+08:00",'
                '"path":"sessions/2026/06/12/rollout-2026-06-12T12-00-00-named-main.jsonl"}\n'
            )
        path = (
            self.codex_home
            / "sessions"
            / "2026"
            / "06"
            / "12"
            / "rollout-2026-06-12T12-00-00-named-main.jsonl"
        )
        path.write_text(
            '{"timestamp":"2026-06-12T12:00:00+08:00","type":"session_meta",'
            '"payload":{"id":"named-main","session_id":"named-session-id",'
            '"cwd":"/Users/example/project","parent_thread_id":"parent-main",'
            '"agent_role":"subagent"}}\n',
            encoding="utf-8",
        )

        result = self.scan(
            cwd=None,
            query="named recovery session",
            include_subagents=True,
        )
        record = next(item for item in result["records"] if item["thread_id"] == "named-main")

        self.assertEqual("Named recovery session", record["thread_name"])
        self.assertIn("named-session-id", record["aliases"])
        self.assertEqual("parent-main", record["parent_thread_id"])
        self.assertEqual("subagent", record["agent_role"])
        self.assertTrue(record["subagent"])

    def test_index_and_transcript_aliases_merge_to_index_canonical_id(self):
        session_index = self.codex_home / "session_index.jsonl"
        with session_index.open("a", encoding="utf-8") as handle:
            handle.write(
                '\n{"id":"canonical-main","thread_name":"Canonical session",'
                '"updated_at":"2026-06-12T12:30:00+08:00",'
                '"path":"sessions/2026/06/12/rollout-2026-06-12T12-30-00-transcript-alias.jsonl"}\n'
            )
        path = (
            self.codex_home
            / "sessions"
            / "2026"
            / "06"
            / "12"
            / "rollout-2026-06-12T12-30-00-transcript-alias.jsonl"
        )
        path.write_text(
            '{"timestamp":"2026-06-12T12:30:00+08:00","type":"session_meta",'
            '"payload":{"session_id":"canonical-main","cwd":"/Users/example/project"}}\n',
            encoding="utf-8",
        )

        result = self.scan(cwd=None, query="Canonical session")
        matching = [item for item in result["records"] if item["thread_id"] == "canonical-main"]

        self.assertEqual(1, len(matching))
        self.assertIn("transcript-alias", matching[0]["aliases"])
        self.assertNotIn("canonical-main", matching[0]["aliases"])

    def test_parent_thread_id_alone_does_not_mark_subagent(self):
        session_index = self.codex_home / "session_index.jsonl"
        with session_index.open("a", encoding="utf-8") as handle:
            handle.write(
                '\n{"id":"forked-main","thread_name":"Forked user thread",'
                '"updated_at":"2026-06-12T13:00:00+08:00",'
                '"path":"sessions/2026/06/12/rollout-2026-06-12T13-00-00-forked-main.jsonl"}\n'
            )
        path = (
            self.codex_home
            / "sessions"
            / "2026"
            / "06"
            / "12"
            / "rollout-2026-06-12T13-00-00-forked-main.jsonl"
        )
        path.write_text(
            '{"timestamp":"2026-06-12T13:00:00+08:00","type":"session_meta",'
            '"payload":{"id":"forked-main","cwd":"/Users/example/project",'
            '"parent_thread_id":"active-main","source":"cli"}}\n',
            encoding="utf-8",
        )

        result = self.scan(cwd=None)
        record = next(item for item in result["records"] if item["thread_id"] == "forked-main")

        self.assertIn("forked-main", self.ids(result))
        self.assertFalse(record["subagent"])
        self.assertEqual("active-main", record["parent_thread_id"])

    def test_invalid_utf8_transcript_is_reported_without_failing_scan(self):
        path = (
            self.codex_home
            / "sessions"
            / "2026"
            / "06"
            / "12"
            / "rollout-2026-06-12T14-00-00-bad-utf8.jsonl"
        )
        path.write_bytes(b"\xff\xfe not utf-8\n")

        result = self.scan(cwd=None)

        self.assertIn("active-main", self.ids(result))
        self.assertTrue(
            any("unreadable" in warning for warning in result["warnings"]),
            result["warnings"],
        )

    def test_unknown_time_requires_explicit_opt_in_when_date_filtered(self):
        session_index = self.codex_home / "session_index.jsonl"
        with session_index.open("a", encoding="utf-8") as handle:
            handle.write('\n{"id":"unknown-time","cwd":"/Users/example/project"}\n')

        filtered = self.scan(since="2026-06-12", cwd=None)
        included = self.scan(
            since="2026-06-12", cwd=None, include_unknown_time=True
        )

        self.assertNotIn("unknown-time", self.ids(filtered))
        self.assertIn("unknown-time", self.ids(included))

    def test_referenced_paths_are_opt_in(self):
        default = self.scan(cwd=None)
        explicit = self.scan(cwd=None, show_paths=True)
        active_default = next(
            item for item in default["records"] if item["thread_id"] == "active-main"
        )
        active_explicit = next(
            item for item in explicit["records"] if item["thread_id"] == "active-main"
        )

        self.assertNotIn("referenced_paths", active_default)
        self.assertIn("referenced_paths", active_explicit)
        self.assertTrue(active_explicit["referenced_paths"])

    def test_multiple_active_transcripts_are_reported(self):
        path = (
            self.codex_home
            / "sessions"
            / "2026"
            / "06"
            / "12"
            / "rollout-2026-06-12T12-45-00-active-alias.jsonl"
        )
        path.write_text(
            '{"timestamp":"2026-06-12T12:45:00+08:00","type":"session_meta",'
            '"payload":{"id":"active-main","cwd":"/Users/example/project"}}\n',
            encoding="utf-8",
        )

        result = self.scan(cwd=None)
        active = next(item for item in result["records"] if item["thread_id"] == "active-main")

        self.assertIn("multiple active transcript sources", "\n".join(active["warnings"]))

    def test_date_filter_uses_configured_timezone(self):
        result = self.scan(since="2026-06-12", include_archived=True)
        self.assertIn("active-main", self.ids(result))
        self.assertNotIn("archived-main", self.ids(result))

    def test_date_filter_defaults_to_local_timezone(self):
        local_midnight = datetime(2026, 6, 12, tzinfo=self.scanner.local_timezone())
        before_local_midnight = local_midnight - timedelta(minutes=30)
        path = (
            self.codex_home
            / "sessions"
            / "2026"
            / "06"
            / "11"
            / "rollout-2026-06-11T23-30-00-before-local-midnight.jsonl"
        )
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(
            "\n".join(
                [
                    (
                        '{"timestamp":"%s","type":"session_meta",'
                        '"payload":{"id":"before-local-midnight","cwd":"%s","source":"cli"}}'
                    )
                    % (before_local_midnight.isoformat(), PROJECT_CWD),
                    (
                        '{"timestamp":"%s","type":"response_item",'
                        '"payload":{"type":"message","role":"user",'
                        '"content":[{"type":"input_text","text":"timezone boundary session"}]}}'
                    )
                    % (before_local_midnight.isoformat(),),
                ]
            ),
            encoding="utf-8",
        )

        result = self.scan(since="2026-06-12", timezone=None)

        self.assertNotIn("before-local-midnight", self.ids(result))
        self.assertEqual(str(self.scanner.local_timezone()), result["filters"]["timezone"])

    def test_naive_transcript_timestamps_do_not_crash_date_filtering(self):
        path = (
            self.codex_home
            / "sessions"
            / "2026"
            / "06"
            / "12"
            / "rollout-2026-06-12T13-00-00-naive-main.jsonl"
        )
        path.write_text(
            "\n".join(
                [
                    '{"timestamp":"2026-06-12T13:00:00","type":"session_meta","payload":{"id":"naive-main","cwd":"/Users/example/project","source":"cli"}}',
                    '{"timestamp":"2026-06-12T13:02:00","type":"response_item","payload":{"type":"message","role":"user","content":[{"type":"input_text","text":"naive timestamp session"}]}}',
                ]
            ),
            encoding="utf-8",
        )

        result = self.scan(since="2026-06-12T00:00:00+08:00", until="2026-06-13T00:00:00+08:00")

        self.assertIn("naive-main", self.ids(result))
        warnings = "\n".join(result["warnings"])
        self.assertIn("naive timestamp", warnings)

    def test_query_filter_matches_user_prompt_text(self):
        result = self.scan(query="keepsake")
        self.assertEqual(["active-main"], self.ids(result))

    def test_missing_codex_home_json_output_is_serializable_and_actionable(self):
        missing_home = self.codex_home.parent / "missing-codex-home"
        completed = self.run_cli("--codex-home", str(missing_home), "--format", "json")

        self.assertEqual(0, completed.returncode, completed.stderr)
        payload = json.loads(completed.stdout)
        self.assertEqual(str(missing_home), payload["codex_home"])
        self.assertEqual(str(missing_home), payload["filters"]["codex_home"])
        self.assertIn("does not exist", "\n".join(payload["warnings"]))

    def test_invalid_since_and_timezone_return_cli_errors_without_traceback(self):
        invalid_since = self.run_cli(
            "--codex-home", str(self.codex_home), "--since", "not-a-date"
        )
        invalid_timezone = self.run_cli(
            "--codex-home", str(self.codex_home), "--timezone", "Not/AZone"
        )

        self.assertNotEqual(0, invalid_since.returncode)
        self.assertIn("error:", invalid_since.stderr)
        self.assertNotIn("Traceback", invalid_since.stderr)
        self.assertNotEqual(0, invalid_timezone.returncode)
        self.assertIn("error:", invalid_timezone.stderr)
        self.assertNotIn("Traceback", invalid_timezone.stderr)

    def test_non_positive_limit_returns_cli_error_without_traceback(self):
        for invalid_limit in ("0", "-1"):
            with self.subTest(limit=invalid_limit):
                completed = self.run_cli(
                    "--codex-home", str(self.codex_home), "--limit", invalid_limit
                )

                self.assertNotEqual(0, completed.returncode)
                self.assertIn("error:", completed.stderr)
                self.assertIn("limit must be positive", completed.stderr)
                self.assertNotIn("Traceback", completed.stderr)

    def test_scan_rejects_non_positive_limit(self):
        for invalid_limit in (0, -1):
            with self.subTest(limit=invalid_limit):
                with self.assertRaisesRegex(
                    self.scanner.ScannerInputError, "limit must be positive"
                ):
                    self.scan(limit=invalid_limit)

    def test_index_only_stale_record_gets_weaker_evidence_warning(self):
        session_index = self.codex_home / "session_index.jsonl"
        with session_index.open("a", encoding="utf-8") as handle:
            handle.write(
                '\n{"id":"stale-index-only","thread_name":"keepsake index",'
                '"cwd":"/Users/example/project",'
                '"updated_at":"2026-06-12T14:00:00+08:00",'
                '"path":"sessions/missing/rollout-2026-06-12T14-00-00-stale-index-only.jsonl"}\n'
            )

        result = self.scan(query="keepsake")
        stale = next(record for record in result["records"] if record["thread_id"] == "stale-index-only")
        active = next(record for record in result["records"] if record["thread_id"] == "active-main")

        self.assertLess(stale["match_score"], active["match_score"])
        self.assertIn("query match", stale["matching_reasons"])
        self.assertIn("query match", active["matching_reasons"])
        self.assertIn("index-only evidence", "\n".join(stale["matching_reasons"] + stale["warnings"]))

    def test_index_only_naive_timestamp_does_not_crash_sorting(self):
        session_index = self.codex_home / "session_index.jsonl"
        session_index.write_text(
            "\n".join(
                [
                    (
                        '{"id":"index-aware","cwd":"/Users/example/project",'
                        '"updated_at":"2026-06-12T16:00:00+08:00",'
                        '"path":"sessions/missing/rollout-2026-06-12T16-00-00-index-aware.jsonl"}'
                    ),
                    (
                        '{"id":"index-naive","cwd":"/Users/example/project",'
                        '"updated_at":"2026-06-12T17:00:00",'
                        '"path":"sessions/missing/rollout-2026-06-12T17-00-00-index-naive.jsonl"}'
                    ),
                ]
            ),
            encoding="utf-8",
        )
        shutil.rmtree(self.codex_home / "sessions")

        result = self.scan()

        self.assertEqual(["index-naive", "index-aware"], self.ids(result))
        self.assertIn("naive timestamp", "\n".join(result["warnings"]))

    def test_malformed_filename_timestamp_does_not_crash_scan(self):
        path = (
            self.codex_home
            / "sessions"
            / "2026"
            / "06"
            / "12"
            / "rollout-2026-06-12T99-99-99-bad-clock.jsonl"
        )
        path.write_text(
            '{"type":"response_item","payload":{"type":"message","role":"user","content":[{"type":"input_text","text":"bad clock fallback"}]}}\n',
            encoding="utf-8",
        )

        result = self.scan(cwd=None, query="bad clock fallback")

        self.assertEqual(["bad-clock"], self.ids(result))
        self.assertIsNone(result["records"][0]["updated_at"])

    def test_filename_only_fallback_parses_id_and_timestamp(self):
        path = (
            self.codex_home
            / "sessions"
            / "2026"
            / "06"
            / "12"
            / "rollout-2026-06-12T15-30-45-filename-only-main.jsonl"
        )
        path.write_text(
            '{"type":"response_item","payload":{"type":"message","role":"user","content":[{"type":"input_text","text":"filename fallback session"}]}}\n',
            encoding="utf-8",
        )

        result = self.scan(cwd=None, query="filename fallback")
        record = result["records"][0]

        self.assertEqual("filename-only-main", record["thread_id"])
        self.assertEqual("2026-06-12T15:30:45+08:00", record["updated_at"])
        self.assertIn("filename fallback timestamp", "\n".join(record["matching_reasons"] + record["warnings"]))

    def test_json_output_contains_recovery_commands(self):
        result = self.scan()
        active = next(record for record in result["records"] if record["thread_id"] == "active-main")
        self.assertEqual("codex resume active-main", active["resume_command"])
        self.assertEqual("codex fork active-main", active["fork_command"])
        self.assertNotIn("deep_link", active)

    def test_cli_json_exposes_uncapped_integer_match_score_without_old_field(self):
        completed = self.run_cli(
            "--codex-home", str(self.codex_home),
            "--cwd", PROJECT_CWD,
            "--query", "keepsake",
            "--timezone", "Asia/Shanghai",
            "--format", "json",
        )

        self.assertEqual(0, completed.returncode, completed.stderr)
        records = json.loads(completed.stdout)["records"]
        self.assertEqual(["active-main"], [record["thread_id"] for record in records])
        record = records[0]
        self.assertEqual(105, record["match_score"])
        self.assertIs(type(record["match_score"]), int)
        self.assertNotIn("confidence", record)
        self.assertEqual(
            [
                "cwd exact match",
                "active source",
                "main session",
                "query match",
                "has user prompts",
            ],
            record["matching_reasons"],
        )
        self.assertTrue(record["source_paths"])
        self.assertEqual("codex resume active-main", record["resume_command"])
        self.assertEqual("codex fork active-main", record["fork_command"])

    def test_table_output_mentions_match_score_and_commands(self):
        result = self.scan(query="keepsake")
        table = self.scanner.format_table(result)
        self.assertIn("active-main", table)
        self.assertIn("match_score: 105", table)
        self.assertNotIn("confidence", table.lower())
        self.assertIn("codex resume active-main", table)

    def test_table_output_includes_recovery_details_and_prompt_snippets(self):
        result = self.scan(query="keepsake", show_prompts=True)
        table = self.scanner.format_table(result)

        self.assertIn("matching reasons:", table)
        self.assertIn("source paths:", table)
        self.assertIn("codex fork active-main", table)
        self.assertIn("first prompt: restore keepsake quest main session", table)
        self.assertIn("last prompt: restore keepsake quest main session", table)

    def test_missing_identity_fields_are_reported_without_failing_scan(self):
        session_index = self.codex_home / "session_index.jsonl"
        with session_index.open("a", encoding="utf-8") as handle:
            handle.write('\n{"cwd":"/Users/example/project","updated_at":"2026-06-12T12:00:00+08:00"}\n')

        nameless_path = self.codex_home / "sessions" / "bad" / "nameless.jsonl"
        nameless_path.parent.mkdir(parents=True, exist_ok=True)
        nameless_path.write_text(
            "\n".join(
                [
                    '{"timestamp":"2026-06-12T12:00:00+08:00","type":"session_meta","payload":{"cwd":"/Users/example/project"}}',
                    '{"timestamp":"2026-06-12T12:01:00+08:00","type":"response_item","payload":{"type":"message","role":"user","content":[{"type":"input_text","text":"nameless event"}]}}',
                ]
            ),
            encoding="utf-8",
        )

        result = self.scan()
        warnings = "\n".join(result["warnings"])

        self.assertIn("missing thread id", warnings)
        self.assertIn("session_index.jsonl", warnings)
        self.assertIn("nameless.jsonl", warnings)
        self.assertIn("active-main", self.ids(result))

    def test_empty_state_table_mentions_searched_paths_and_resume_all(self):
        empty_home = Path(self.tmp.name) / "empty_codex_home"
        empty_home.mkdir()
        result = self.scan(codex_home=empty_home, cwd="/no/matches")
        table = self.scanner.format_table(result)

        self.assertIn("searched paths:", table)
        self.assertIn("sessions/**/*.jsonl", table)
        self.assertIn("codex resume --all", table)

    def test_fixture_copy_is_not_real_codex_home(self):
        self.assertNotEqual(Path.home() / ".codex", self.codex_home)
        env_home = self.scanner.default_codex_home()
        self.assertNotEqual(env_home.resolve(), self.codex_home.resolve())


if __name__ == "__main__":
    unittest.main()
