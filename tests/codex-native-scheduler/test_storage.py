from __future__ import annotations

import datetime as dt
import tempfile
import unittest
from concurrent.futures import ThreadPoolExecutor
from pathlib import Path
from unittest import mock

from support import job, store_with_job

# isort: split
from codex_scheduler.errors import SchedulerError
from codex_scheduler.util import atomic_write_text, captured_environment, iso


class StorageTests(unittest.TestCase):
    def test_job_reference_cannot_escape_state_root(self) -> None:
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary)
            metadata = job(root)
            store = store_with_job(root, metadata)
            with self.assertRaises(SchedulerError):
                store.resolve_job("../../..")

    def test_occurrence_claim_is_atomic(self) -> None:
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary)
            metadata = job(root)
            store = store_with_job(root, metadata)
            payload = {"scheduled_for": iso()}
            self.assertTrue(
                store.claim_occurrence(metadata["id"], "2026-07-20T10:00", payload)
            )
            self.assertFalse(
                store.claim_occurrence(metadata["id"], "2026-07-20T10:00", payload)
            )

    def test_prune_leaves_a_tombstone(self) -> None:
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary)
            metadata = job(root)
            store = store_with_job(root, metadata)
            run, run_dir = store.new_run(
                metadata,
                trigger="run_now",
                scheduled_for=None,
                occurrence_key=None,
            )
            run["status"] = "succeeded"
            run["started_at"] = iso()
            run["finished_at"] = iso()
            store.save_run(run)
            atomic_write_text(run_dir / "final.txt", "done")
            store.prune_run(run)
            tombstone = store.list_runs(metadata["id"])[0]
            self.assertTrue(tombstone["tombstone"])
            self.assertFalse((run_dir / "final.txt").exists())
            self.assertEqual(tombstone["retry_of"], None)

    def test_retention_respects_count_and_age(self) -> None:
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary)
            metadata = job(root)
            metadata["retention"] = {
                "mode": "bounded",
                "days": 7,
                "retain_runs": 1,
            }
            store = store_with_job(root, metadata)
            old = dt.datetime.now(dt.UTC) - dt.timedelta(days=30)
            for _ in range(2):
                run, _ = store.new_run(
                    metadata,
                    trigger="run_now",
                    scheduled_for=None,
                    occurrence_key=None,
                )
                run["status"] = "succeeded"
                run["finished_at"] = old.isoformat()
                store.save_run(run)
            candidates = store.retention_candidates(metadata)
            self.assertEqual(len(candidates), 1)

    def test_stale_active_lock_has_one_replacement_owner(self) -> None:
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary)
            metadata = job(root)
            store = store_with_job(root, metadata)
            active = store.job_dir(metadata["id"]) / ".active"
            active.mkdir()
            from codex_scheduler.util import atomic_write_json

            atomic_write_json(
                active / "owner.json",
                {
                    "run_id": "run-stale",
                    "pid": 99999999,
                    "start_token": "stale",
                },
            )

            def acquire(index: int) -> bool:
                return store.acquire_active(
                    metadata["id"],
                    run_id=f"run-{index}",
                    pid=__import__("os").getpid(),
                    start_token=None,
                )[0]

            with ThreadPoolExecutor(max_workers=2) as executor:
                results = list(executor.map(acquire, (1, 2)))
            self.assertEqual(results.count(True), 1)
            self.assertEqual(results.count(False), 1)

    def test_windows_runtime_environment_keys_are_preserved_when_present(self) -> None:
        expected = {
            "USERPROFILE": r"C:\Users\tester",
            "APPDATA": r"C:\Users\tester\AppData\Roaming",
            "LOCALAPPDATA": r"C:\Users\tester\AppData\Local",
            "SystemRoot": r"C:\Windows",
            "COMSPEC": r"C:\Windows\System32\cmd.exe",
            "PATHEXT": ".COM;.EXE;.BAT;.CMD",
        }
        with mock.patch.dict("os.environ", expected, clear=False):
            captured, missing = captured_environment([], [])
        self.assertFalse(missing)
        for key, value in expected.items():
            self.assertEqual(captured[key], value)


if __name__ == "__main__":
    unittest.main()
