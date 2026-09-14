from __future__ import annotations

import importlib.util
import json
import tempfile
import unittest
from pathlib import Path


ROOT = Path(__file__).resolve().parents[2]
SCRIPT = ROOT / "skills/creative/suno-music-explorer/scripts/ledger.py"
SPEC = importlib.util.spec_from_file_location("suno_explorer_ledger", SCRIPT)
assert SPEC and SPEC.loader
ledger = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(ledger)


class ResolveLedgerTest(unittest.TestCase):
    def test_user_path_has_priority(self) -> None:
        with tempfile.TemporaryDirectory() as temp:
            root = Path(temp)
            existing = root / "project/.suno-explorer"
            existing.mkdir(parents=True)
            chosen = root / "chosen"

            result = ledger.resolve_ledger(
                existing.parent,
                str(chosen),
                [str(existing.parent)],
            )

            self.assertEqual("proposed", result["status"])
            self.assertEqual(str(chosen.resolve()), result["ledger_dir"])
            self.assertTrue(result["requires_confirmation"])

    def test_nearest_existing_ancestor_wins(self) -> None:
        with tempfile.TemporaryDirectory() as temp:
            root = Path(temp)
            ledger_dir = root / ".suno-explorer"
            start = root / "one/two"
            ledger_dir.mkdir()
            start.mkdir(parents=True)
            runs = ledger_dir / "runs"
            runs.mkdir()
            run = runs / "existing.json"
            run.write_text("{}", encoding="utf-8")

            result = ledger.resolve_ledger(start, None, [])

            self.assertEqual("existing", result["status"])
            self.assertEqual(str(ledger_dir.resolve()), result["ledger_dir"])
            self.assertFalse(result["requires_confirmation"])
            self.assertEqual([str(run.resolve())], result["runs"])

    def test_unique_workspace_is_proposed(self) -> None:
        with tempfile.TemporaryDirectory() as temp:
            root = Path(temp)

            result = ledger.resolve_ledger(root, None, [str(root)])

            self.assertEqual("proposed", result["status"])
            self.assertEqual(
                str((root / ".suno-explorer").resolve()), result["ledger_dir"]
            )
            self.assertTrue(result["requires_confirmation"])

    def test_multiple_workspaces_are_unresolved(self) -> None:
        with tempfile.TemporaryDirectory() as temp:
            root = Path(temp)
            first = root / "first"
            second = root / "second"
            first.mkdir()
            second.mkdir()

            result = ledger.resolve_ledger(
                root,
                None,
                [str(first), str(second)],
            )

            self.assertEqual("unresolved", result["status"])
            self.assertEqual("multiple workspace roots", result["reason"])


class LedgerStateTest(unittest.TestCase):
    def test_init_requires_confirmation_for_new_directory(self) -> None:
        with tempfile.TemporaryDirectory() as temp:
            args = type(
                "Args",
                (),
                {
                    "ledger_dir": str(Path(temp) / "new-ledger"),
                    "session_id": "run-1",
                    "create_limit": 3,
                    "credit_limit": None,
                    "confirm_create": False,
                },
            )()

            with self.assertRaisesRegex(ledger.LedgerError, "requires"):
                ledger.command_init(args)

    def test_record_is_atomic_and_enforces_grant(self) -> None:
        with tempfile.TemporaryDirectory() as temp:
            ledger_dir = Path(temp) / ".suno-explorer"
            init_args = type(
                "Args",
                (),
                {
                    "ledger_dir": str(ledger_dir),
                    "session_id": "run-1",
                    "create_limit": 3,
                    "credit_limit": 30,
                    "confirm_create": True,
                },
            )()
            created = ledger.command_init(init_args)
            path = Path(created["file"])
            record_args = type(
                "Args",
                (),
                {
                    "file": str(path),
                    "event_json": json.dumps(
                        {
                            "kind": "submission",
                            "summary": "identity A confirmed",
                            "candidate_ids": ["one", "two"],
                        }
                    ),
                    "creates_spent": 1,
                    "credits_spent": 10,
                    "phase": "listen",
                    "decision": None,
                    "next_action": "audition candidates",
                },
            )()

            ledger.command_record(record_args)
            saved = json.loads(path.read_text(encoding="utf-8"))
            self.assertEqual(1, saved["spent"]["creates"])
            self.assertEqual("listen", saved["phase"])

            record_args.creates_spent = 4
            with self.assertRaisesRegex(ledger.LedgerError, "Create grant"):
                ledger.command_record(record_args)
            unchanged = json.loads(path.read_text(encoding="utf-8"))
            self.assertEqual(1, unchanged["spent"]["creates"])

    def test_sensitive_fields_are_rejected(self) -> None:
        data = {
            "schema_version": 1,
            "session_id": "run-1",
            "grant": {"create_limit": 3, "credit_limit": None},
            "spent": {"creates": 0, "credits": None},
            "phase": "probe",
            "events": [{"kind": "note", "summary": "bad", "cookie": "x"}],
            "decision": None,
            "next_action": "stop",
        }

        with self.assertRaisesRegex(ledger.LedgerError, "sensitive field"):
            ledger.validate_ledger(data)


if __name__ == "__main__":
    unittest.main()
