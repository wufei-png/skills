from __future__ import annotations

import datetime as dt
import os
import subprocess
import sys
import tempfile
import time
import unittest
from pathlib import Path
from unittest import mock

from support import job, store_with_job

# isort: split
from codex_scheduler.cli import dispatch, parser
from codex_scheduler.errors import SchedulerError
from codex_scheduler.jobs import resume_job
from codex_scheduler.runner import (
    _run_with_overlap,
    execute_run,
    reconcile_stale_runs,
    retry_run,
    run_now,
    stop_run,
    trigger_job,
)
from codex_scheduler.util import (
    process_start_token,
    read_json,
    terminate_process_tree,
)

FIXTURE = Path(__file__).with_name("fixtures") / "fake_codex.py"


class RunnerTests(unittest.TestCase):
    def prepare(
        self,
        root: Path,
        *,
        mode: str,
        counter: Path | None = None,
        session_mode: str = "new_each_run",
    ):
        environment = {
            "HOME": str(root),
            "PATH": os.environ.get("PATH", ""),
            "PYTHONUNBUFFERED": "1",
            "FAKE_CODEX_MODE": mode,
        }
        if counter:
            environment["FAKE_CODEX_COUNTER"] = str(counter)
        metadata = job(
            root,
            command=[sys.executable, str(FIXTURE)],
            session_mode=session_mode,
            environment=environment,
        )
        metadata["codex"]["profile"] = "automation"
        metadata["codex"]["config"] = [
            'sandbox_mode="danger-full-access"',
            'approval_policy="never"',
            "arbitrary.future_key=true",
        ]
        store = store_with_job(root, metadata)
        run, run_dir = store.new_run(
            metadata,
            trigger="run_now",
            scheduled_for=None,
            occurrence_key=None,
        )
        return metadata, store, run, run_dir

    def test_success_persists_jsonl_final_and_session(self) -> None:
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary)
            metadata, store, run, run_dir = self.prepare(root, mode="success")
            result = execute_run(
                store,
                run,
                run_dir,
                metadata,
                resume_session=None,
            )
            self.assertEqual(result["status"], "succeeded")
            self.assertEqual(result["session_id"], "session-test")
            self.assertEqual(
                (run_dir / "final.txt").read_text(),
                "fixture final reply\n",
            )
            command = read_json(run_dir / "attempts" / "1" / "command.json")[
                "arguments"
            ]
            self.assertIn("--strict-config", command)
            self.assertEqual(command.count("-c"), 3)
            self.assertIn("arbitrary.future_key=true", command)

    def test_transient_pre_turn_failure_retries_three_times(self) -> None:
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary)
            counter = root / "counter"
            metadata, store, run, run_dir = self.prepare(
                root,
                mode="transient",
                counter=counter,
            )
            with mock.patch("codex_scheduler.runner.time.sleep"):
                result = execute_run(
                    store,
                    run,
                    run_dir,
                    metadata,
                    resume_session=None,
                )
            self.assertEqual(result["status"], "succeeded")
            self.assertEqual(result["attempts"], 3)
            self.assertEqual(counter.read_text(), "3")

    def test_deterministic_pre_turn_failure_is_not_retried(self) -> None:
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary)
            metadata, store, run, run_dir = self.prepare(
                root,
                mode="deterministic",
            )
            result = execute_run(
                store,
                run,
                run_dir,
                metadata,
                resume_session=None,
            )
            self.assertEqual(result["status"], "failed")
            self.assertEqual(result["attempts"], 1)

    def test_stop_during_retry_backoff_does_not_launch_again(self) -> None:
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary)
            counter = root / "counter"
            metadata, store, run, run_dir = self.prepare(
                root, mode="transient", counter=counter
            )
            with mock.patch(
                "codex_scheduler.runner.time.sleep",
                side_effect=lambda _: stop_run(store, run["id"]),
            ):
                result = execute_run(store, run, run_dir, metadata, resume_session=None)
            self.assertEqual(result["status"], "cancelled")
            self.assertEqual(result["attempts"], 1)
            self.assertEqual(counter.read_text(), "1")

    def test_manual_retry_resumes_captured_session(self) -> None:
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary)
            metadata, store, run, run_dir = self.prepare(root, mode="success")
            original = execute_run(
                store,
                run,
                run_dir,
                metadata,
                resume_session=None,
            )
            current_job = store.load_job(metadata["id"])
            current_job["revision"] = 2
            store.save_job(current_job)
            retried = retry_run(store, original["id"])
            self.assertEqual(retried["status"], "succeeded")
            self.assertEqual(retried["retry_of"], original["id"])
            self.assertEqual(retried["job_revision"], 1)
            retried_dir = store.run_dir(metadata["id"], retried["id"])
            command = read_json(retried_dir / "attempts" / "1" / "command.json")[
                "arguments"
            ]
            self.assertIn("resume", command)
            self.assertIn("session-test", command)
            self.assertLess(command.index("-p"), command.index("resume"))
            self.assertLess(command.index("-C"), command.index("resume"))
            self.assertEqual(command[command.index("-C") + 1], str(root))

    def test_real_unknown_configuration_error_is_not_retried(self) -> None:
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary)
            counter = root / "counter"
            metadata, store, run, run_dir = self.prepare(
                root,
                mode="unknown_configuration",
                counter=counter,
            )
            result = execute_run(
                store,
                run,
                run_dir,
                metadata,
                resume_session=None,
            )
            self.assertEqual(result["status"], "failed")
            self.assertEqual(result["attempts"], 1)
            self.assertEqual(counter.read_text(), "1")

    def test_failed_latest_attempt_removes_stale_final_reply(self) -> None:
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary)
            counter = root / "counter"
            metadata, store, run, run_dir = self.prepare(
                root,
                mode="stale_final",
                counter=counter,
            )
            with mock.patch("codex_scheduler.runner.time.sleep"):
                result = execute_run(
                    store,
                    run,
                    run_dir,
                    metadata,
                    resume_session=None,
                )
            self.assertEqual(result["status"], "failed")
            self.assertEqual(result["attempts"], 2)
            self.assertFalse((run_dir / "final.txt").exists())

    def test_workspace_preparation_error_becomes_failed_run(self) -> None:
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary)
            metadata, store, _run, _run_dir = self.prepare(
                root,
                mode="success",
            )
            missing = root / "missing"
            metadata["cwd"] = str(missing)
            store.save_job(metadata)
            result = run_now(store, metadata["id"])
            self.assertEqual(result["status"], "failed")
            self.assertIn("working directory does not exist", result["error"])
            current = store.load_job(metadata["id"])
            self.assertEqual(current["stats"]["consecutive_failures"], 1)

    def test_skipped_overlap_does_not_consume_count(self) -> None:
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary)
            metadata, store, _run, _run_dir = self.prepare(
                root,
                mode="success",
            )
            metadata["schedule"] = {
                "kind": "at",
                "at": "2026-07-20T10:00:00+00:00",
            }
            store.save_job(metadata)
            store.acquire_active(
                metadata["id"],
                run_id="run-existing",
                pid=os.getpid(),
                start_token=process_start_token(os.getpid()),
            )
            run, run_dir = store.new_run(
                metadata,
                trigger="scheduled",
                scheduled_for="2026-07-20T10:00:00+00:00",
                occurrence_key="2026-07-20T10:00Z",
            )
            with mock.patch("codex_scheduler.runner.backend_for") as backend:
                result = _run_with_overlap(
                    store,
                    metadata,
                    run,
                    run_dir,
                    scheduled=True,
                    resume_session=None,
                )
            self.assertEqual(result["status"], "skipped_overlap")
            current = store.load_job(metadata["id"])
            self.assertEqual(current["stats"]["scheduled_started"], 0)
            self.assertEqual(current["status"], "completed")
            backend.return_value.unregister.assert_called_once()

    def test_rescheduled_one_shot_runs_at_the_new_time(self) -> None:
        due = dt.datetime(2026, 7, 20, 10, tzinfo=dt.UTC)
        rescheduled = due + dt.timedelta(hours=1)
        root = Path(self.enterContext(tempfile.TemporaryDirectory()))
        metadata = job(
            root,
            command=[sys.executable, str(FIXTURE)],
            schedule={"kind": "at", "at": due.isoformat()},
        )
        store = store_with_job(root, metadata)
        job_id = metadata["id"]
        update = parser().parse_args(
            ["--state-dir", str(store.root), "update", job_id, "--at", "1h"]
        )
        backend = mock.Mock()

        def reschedule_before_finish(*args, **kwargs):
            dispatch(update)
            return execute_run(*args, **kwargs)

        with (
            mock.patch("codex_scheduler.jobs.backend_for", return_value=backend),
            mock.patch("codex_scheduler.runner.backend_for", return_value=backend),
            mock.patch("codex_scheduler.cli.now_local", return_value=due),
            mock.patch("codex_scheduler.runner.now_local", return_value=due) as clock,
        ):
            with mock.patch(
                "codex_scheduler.runner.execute_run",
                side_effect=reschedule_before_finish,
            ):
                original = trigger_job(store, job_id)
            self.assertEqual(original["status"], "succeeded")
            current = store.load_job(job_id)
            self.assertEqual(current["schedule"]["at"], rescheduled.isoformat())
            self.assertEqual(current["status"], "active")
            self.assertEqual(current["stats"]["last_run_id"], original["id"])
            backend.register.assert_called_once()
            backend.unregister.assert_not_called()

            clock.return_value = rescheduled
            following = trigger_job(store, job_id)
            self.assertEqual(following["status"], "succeeded")
            self.assertEqual(following["scheduled_for"], rescheduled.isoformat())
            self.assertEqual(store.load_job(job_id)["status"], "completed")
            backend.unregister.assert_called_once()

    def test_parallel_scheduled_run_stops_if_job_was_cancelled(self) -> None:
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary)
            metadata, store, _run, _run_dir = self.prepare(
                root,
                mode="success",
            )
            metadata["overlap_policy"] = "parallel"
            metadata["status"] = "cancelled"
            store.save_job(metadata)
            run, run_dir = store.new_run(
                metadata,
                trigger="scheduled",
                scheduled_for="2026-07-20T10:00:00+00:00",
                occurrence_key="2026-07-20T10:00Z",
            )
            result = _run_with_overlap(
                store,
                metadata,
                run,
                run_dir,
                scheduled=True,
                resume_session=None,
            )
            self.assertEqual(result["status"], "cancelled")
            self.assertEqual(
                store.load_job(metadata["id"])["stats"]["scheduled_started"],
                0,
            )

    def test_parallel_scheduled_run_cannot_overshoot_count(self) -> None:
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary)
            metadata, store, _run, _run_dir = self.prepare(
                root,
                mode="success",
            )
            metadata["overlap_policy"] = "parallel"
            metadata["limits"]["count"] = 1
            metadata["stats"]["scheduled_started"] = 1
            store.save_job(metadata)
            run, run_dir = store.new_run(
                metadata,
                trigger="scheduled",
                scheduled_for="2026-07-20T11:00:00+00:00",
                occurrence_key="2026-07-20T11:00Z",
            )
            result = _run_with_overlap(
                store,
                metadata,
                run,
                run_dir,
                scheduled=True,
                resume_session=None,
            )
            self.assertEqual(result["status"], "cancelled")
            self.assertEqual(
                store.load_job(metadata["id"])["stats"]["scheduled_started"],
                1,
            )

    def test_stale_parallel_run_is_marked_abandoned(self) -> None:
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary)
            metadata, store, run, run_dir = self.prepare(
                root,
                mode="success",
            )
            run["status"] = "running"
            run["runner_pid"] = 99999999
            run["runner_start_token"] = "stale"
            store.save_run(run)
            reconciled = reconcile_stale_runs(store, metadata["id"])
            self.assertEqual(reconciled, [run["id"]])
            current = read_json(run_dir / "run.json")
            self.assertEqual(current["status"], "abandoned")
            self.assertEqual(
                store.load_job(metadata["id"])["stats"]["consecutive_failures"],
                1,
            )

    def test_three_failures_pause_and_manual_success_does_not_resume(self) -> None:
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary)
            metadata, store, _run, _run_dir = self.prepare(
                root,
                mode="deterministic",
            )
            with mock.patch("codex_scheduler.runner.backend_for") as backend:
                for _ in range(3):
                    self.assertEqual(
                        run_now(store, metadata["id"])["status"],
                        "failed",
                    )
            paused = store.load_job(metadata["id"])
            self.assertEqual(paused["status"], "paused")
            self.assertEqual(paused["stats"]["consecutive_failures"], 3)
            backend.return_value.unregister.assert_called_once()

            paused["environment"]["FAKE_CODEX_MODE"] = "success"
            store.save_job(paused)
            self.assertEqual(
                run_now(store, metadata["id"])["status"],
                "succeeded",
            )
            after_success = store.load_job(metadata["id"])
            self.assertEqual(after_success["stats"]["consecutive_failures"], 0)
            self.assertEqual(after_success["status"], "paused")

    def test_completed_recurring_job_cannot_be_resumed(self) -> None:
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary)
            metadata, store, _run, _run_dir = self.prepare(
                root,
                mode="success",
            )
            metadata["status"] = "completed"
            store.save_job(metadata)
            with self.assertRaises(SchedulerError):
                resume_job(store, metadata)

    def test_reset_session_rejects_late_session_from_old_generation(self) -> None:
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary)
            metadata, store, _run, _run_dir = self.prepare(
                root,
                mode="success",
                session_mode="resume_fixed",
            )
            old_snapshot = dict(metadata)
            current = store.load_job(metadata["id"])
            current["session_generation"] = 2
            current["fixed_session_id"] = None
            store.save_job(current)
            run, run_dir = store.new_run(
                old_snapshot,
                trigger="run_now",
                scheduled_for=None,
                occurrence_key=None,
                job_snapshot=old_snapshot,
            )
            result = _run_with_overlap(
                store,
                old_snapshot,
                run,
                run_dir,
                scheduled=False,
                resume_session=None,
            )
            self.assertEqual(result["status"], "succeeded")
            self.assertIsNone(store.load_job(metadata["id"])["fixed_session_id"])

    def test_bounded_retention_is_applied_after_each_run(self) -> None:
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary)
            environment = {
                "HOME": str(root),
                "PATH": os.environ.get("PATH", ""),
                "PYTHONUNBUFFERED": "1",
                "FAKE_CODEX_MODE": "success",
            }
            metadata = job(
                root,
                command=[sys.executable, str(FIXTURE)],
                environment=environment,
            )
            metadata["retention"] = {
                "mode": "bounded",
                "days": None,
                "retain_runs": 1,
            }
            store = store_with_job(root, metadata)
            first = run_now(store, metadata["id"])
            second = run_now(store, metadata["id"])
            runs = {run["id"]: run for run in store.list_runs(metadata["id"])}
            self.assertTrue(runs[first["id"]]["tombstone"])
            self.assertFalse(runs[second["id"]].get("tombstone", False))

    def test_stop_terminates_active_codex_run(self) -> None:
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary)
            metadata, store, _run, _run_dir = self.prepare(root, mode="sleep")
            entrypoint = metadata["runner_entrypoint"]
            process = subprocess.Popen(
                [
                    sys.executable,
                    entrypoint,
                    "--state-dir",
                    str(store.root),
                    "run-now",
                    metadata["id"],
                ],
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                text=True,
            )
            try:
                run = None
                deadline = time.monotonic() + 10
                while time.monotonic() < deadline:
                    run = next(
                        (
                            candidate
                            for candidate in store.list_runs(metadata["id"])
                            if candidate["status"] == "running"
                        ),
                        None,
                    )
                    if run:
                        break
                    time.sleep(0.1)
                self.assertIsNotNone(run)
                assert run is not None
                stopped = stop_run(store, run["id"])
                process.wait(timeout=15)
                self.assertEqual(stopped["status"], "cancelled")
                self.assertFalse(process.poll() is None)
            finally:
                for candidate in store.list_runs(metadata["id"]):
                    if candidate.get("codex_pid"):
                        terminate_process_tree(candidate["codex_pid"])
                if process.poll() is None:
                    process.terminate()
                    process.wait(timeout=10)
                process.communicate()


if __name__ == "__main__":
    unittest.main()
