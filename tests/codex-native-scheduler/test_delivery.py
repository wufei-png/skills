from __future__ import annotations

import datetime as dt
import os
import subprocess
import tempfile
import unittest
from pathlib import Path
from types import SimpleNamespace
from unittest import mock

from support import SCRIPTS  # noqa: F401

# isort: split
from codex_scheduler.cli import dispatch, parser
from codex_scheduler.errors import SchedulerError
from codex_scheduler.runner import trigger_job
from codex_scheduler.storage import Store
from codex_scheduler.util import read_json

THREAD = "019f8ad6-436d-7d43-b980-2ce65da33755"
OTHER_THREAD = "019f8ad6-436d-7d43-b980-2ce65da33756"
PROMPT = "Check the result.\nKeep `$value`, quotes ' and \" unchanged.\n"


class QueueDeliveryTests(unittest.TestCase):
    def setUp(self) -> None:
        temporary = self.enterContext(tempfile.TemporaryDirectory())
        self.root = Path(temporary)
        self.store = Store(self.root / "state")
        self.enterContext(mock.patch.dict(os.environ, {"CODEX_THREAD_ID": THREAD}))
        self.backend = self.enterContext(
            mock.patch("codex_scheduler.jobs.backend_for")
        ).return_value
        for module in ("delivery", "runner"):
            self.enterContext(
                mock.patch(
                    f"codex_scheduler.{module}.backend_for", return_value=self.backend
                )
            )
        self.backend.status.return_value = {"registered": False}
        self.enterContext(
            mock.patch("codex_scheduler.jobs.selected_backend", return_value="systemd")
        )
        self.enterContext(
            mock.patch(
                "codex_scheduler.jobs.configured_commands",
                return_value=("/path with space/python3", ["codex"]),
            )
        )
        self.enterContext(
            mock.patch(
                "codex_scheduler.delivery.run_checked",
                return_value=subprocess.CompletedProcess(
                    [],
                    0,
                    "Usage: codex queue --message TEXT --thread UUID --resume",
                    "",
                ),
            )
        )
        self.send = mock.Mock(
            return_value=subprocess.CompletedProcess(
                [], 0, f"Queued message message-1 for thread {THREAD}.\n", ""
            )
        )
        self.enterContext(
            mock.patch(
                "codex_scheduler.delivery.subprocess",
                SimpleNamespace(
                    run=self.send,
                    DEVNULL=subprocess.DEVNULL,
                    TimeoutExpired=subprocess.TimeoutExpired,
                ),
            )
        )

    def invoke(self, *args: str) -> dict:
        return dispatch(
            parser().parse_args(["--state-dir", str(self.store.root), *args])
        )

    def create(self, *args: str, schedule: tuple[str, str] = ("--every", "1h")) -> str:
        created = self.invoke(
            "create",
            "--cwd",
            str(self.root),
            "--session-mode",
            "queue_existing",
            *schedule,
            "--prompt",
            PROMPT,
            *args,
        )
        self.assertEqual(created["fixed_session_id"], THREAD)
        self.assertEqual(self.store.prompt(created["id"]), PROMPT)
        return created["id"]

    def tick(self, job_id: str, hours: int) -> dict | None:
        job = self.store.load_job(job_id)
        anchor = dt.datetime.fromisoformat(job["schedule"]["anchor"])
        with mock.patch(
            "codex_scheduler.runner.now_local",
            return_value=anchor + dt.timedelta(hours=hours),
        ):
            return trigger_job(self.store, job_id)

    def test_fixed_prompt_waits_for_ack_and_owning_thread_pauses(self) -> None:
        job_id = self.create("--stop-when", "The checks pass")
        first = self.tick(job_id, 0)
        self.assertEqual(first["status"], "queued")
        self.assertEqual(first["queued_message_id"], "message-1")
        self.assertNotIn("acknowledged_at", first)
        argv = self.send.call_args.args[0]
        self.assertEqual(argv[:5], ["codex", "queue", "--thread", THREAD, "--resume"])
        self.assertIn(f"ack {job_id} {first['id']}`", argv[-1])
        self.assertIn(f"`pending_run_id` equals `{first['id']}`", argv[-1])
        self.assertTrue(argv[-1].endswith(PROMPT))
        self.assertIn("The checks pass", argv[-1])
        self.assertIn("'/path with space/python3'", argv[-1])
        self.assertIsNone(self.tick(job_id, 0))
        self.assertEqual(self.tick(job_id, 1)["status"], "skipped_pending")
        self.send.assert_called_once()

        with (
            mock.patch.dict(os.environ, {"CODEX_THREAD_ID": OTHER_THREAD}),
            self.assertRaisesRegex(SchedulerError, "target Codex thread"),
        ):
            self.invoke("ack", job_id, first["id"], "--pause")
        self.backend.unregister.assert_not_called()
        self.invoke("ack", job_id, first["id"])
        second = self.tick(job_id, 2)
        second_argv = self.send.call_args.args[0]
        self.assertEqual(second_argv[:-1], argv[:-1])
        self.assertTrue(second_argv[-1].endswith(PROMPT))
        self.assertIn(f"ack {job_id} {second['id']}`", second_argv[-1])
        self.assertNotIn(second["id"], argv[-1])
        self.assertNotIn(first["id"], second_argv[-1])
        with self.assertRaisesRegex(SchedulerError, "pending delivery"):
            self.invoke("ack", job_id, first["id"], "--pause")
        result = self.invoke("ack", job_id, second["id"], "--pause")
        self.assertEqual(result["status"], "paused")
        self.assertEqual(result["native"], {"registered": False})
        self.assertFalse(result["native_pause_pending"])
        self.backend.unregister.assert_called_once()
        logged = read_json(self.store.run_dir(job_id, second["id"]) / "run.json")
        self.assertEqual(logged["status"], "queued")
        self.assertEqual(logged["acknowledged_at"], result["acknowledged_at"])
        self.assertIsNone(self.tick(job_id, 3))
        self.assertEqual(self.invoke("run-now", job_id)["status"], "cancelled")
        self.assertEqual(self.send.call_count, 2)

    def test_macos_sandbox_can_pause_without_process_start_time(self) -> None:
        job_id = self.create("--stop-when", "The checks pass")
        run = self.tick(job_id, 0)
        with (
            mock.patch("codex_scheduler.util.sys.platform", "darwin"),
            mock.patch("codex_scheduler.util.run_checked", side_effect=PermissionError),
        ):
            result = self.invoke("ack", job_id, run["id"], "--pause")

        self.assertEqual(result["status"], "paused")
        self.assertTrue(result["acknowledged_at"])
        self.assertFalse(result["native_pause_pending"])
        self.assertFalse((self.store.job_dir(job_id) / ".state.lock").exists())

    def test_unknown_delivery_survives_schedule_update_without_replay(self) -> None:
        job_id = self.create()
        self.send.side_effect = subprocess.TimeoutExpired(["codex", "queue"], 30)
        first = self.invoke("run-now", job_id)
        self.assertEqual(first["status"], "delivery_unknown")
        updated = self.invoke("update", job_id, "--every", "2h")
        self.assertEqual(updated["schedule"]["seconds"], 7200)
        self.assertEqual(updated["pending_run_id"], first["id"])
        self.assertEqual(self.invoke("run-now", job_id)["status"], "skipped_pending")
        self.send.assert_called_once()
        with self.assertRaisesRegex(SchedulerError, "no authorized stop condition"):
            self.invoke("ack", job_id, first["id"], "--pause")
        with self.assertRaisesRegex(SchedulerError, "pending queue"):
            self.invoke("retry", first["id"])

    def test_skipped_one_shot_completes_and_keeps_the_pending_receipt(self) -> None:
        local_zone = dt.timezone(dt.timedelta(hours=8))
        with mock.patch(
            "codex_scheduler.cli.now_local",
            return_value=dt.datetime(2026, 11, 20, 12, tzinfo=local_zone),
        ):
            job_id = self.create(schedule=("--at", "2h"))
        first = self.invoke("run-now", job_id)
        scheduled_at = self.store.load_job(job_id)["schedule"]["at"]
        due = dt.datetime.fromisoformat(scheduled_at).astimezone(dt.UTC)

        with mock.patch("codex_scheduler.runner.now_local", return_value=due):
            skipped = trigger_job(self.store, job_id)
            self.assertEqual(skipped["status"], "skipped_pending")
            finished = self.invoke("show", job_id)
            self.assertEqual(finished["status"], "completed")
            self.assertEqual(finished["stats"]["last_result"], "skipped_pending")
            self.assertEqual(finished["stats"]["scheduled_started"], 0)
            self.assertEqual(finished["pending_run_id"], first["id"])
            self.backend.unregister.assert_called_once()

            receipt = self.invoke("ack", job_id, first["id"])
            self.assertEqual(receipt["status"], "completed")
            self.assertIsNone(self.invoke("show", job_id)["pending_run_id"])
            self.assertIsNone(trigger_job(self.store, job_id))
            self.send.assert_called_once()
            with self.assertRaisesRegex(SchedulerError, "create a new job"):
                self.invoke("retry", skipped["id"])

    def test_queue_argument_rejection_releases_the_pending_receipt(self) -> None:
        job_id = self.create()
        self.send.side_effect = [
            subprocess.CompletedProcess(
                [], 2, "", "error: unexpected argument '--resume' found\n"
            ),
            self.send.return_value,
        ]

        rejected = self.tick(job_id, 0)
        self.assertEqual(rejected["status"], "failed")
        self.assertEqual(rejected["exit_code"], 2)
        self.assertIsNone(self.invoke("show", job_id)["pending_run_id"])

        following = self.tick(job_id, 1)
        self.assertEqual(following["status"], "queued")
        self.assertEqual(self.invoke("show", job_id)["pending_run_id"], following["id"])

    def test_cli_failure_without_a_clear_rejection_keeps_the_receipt(self) -> None:
        job_id = self.create()
        self.send.return_value = subprocess.CompletedProcess(
            [], 2, "", "error: connection closed while waiting for queue confirmation"
        )

        unknown = self.tick(job_id, 0)
        self.assertEqual(unknown["status"], "delivery_unknown")
        self.assertEqual(self.invoke("show", job_id)["pending_run_id"], unknown["id"])
        self.assertEqual(self.tick(job_id, 1)["status"], "skipped_pending")
        self.send.assert_called_once()

    def test_resume_warning_keeps_the_queue_receipt(self) -> None:
        job_id = self.create()
        self.send.return_value.stderr = (
            "Warning: message was queued, but could not resume thread"
        )
        run = self.invoke("run-now", job_id)
        self.assertEqual(run["status"], "queued")
        self.assertTrue(run["resume_warning"])
        self.assertEqual(self.invoke("show", job_id)["pending_run_id"], run["id"])

    def test_native_pause_is_deferred_until_the_scheduler_wakes(self) -> None:
        job_id = self.create("--stop-when", "The checks pass")
        run = self.invoke("run-now", job_id)
        self.backend.status.return_value = {
            "registered": False,
            "error": "systemd user bus unavailable",
        }
        result = self.invoke("ack", job_id, run["id"], "--pause")
        self.assertTrue(result["native_pause_pending"])
        self.assertIsNone(result["native"]["registered"])
        self.assertEqual(self.invoke("show", job_id)["status"], "paused")
        self.assertIsNone(self.invoke("show", job_id)["pending_run_id"])
        self.assertEqual(self.invoke("run-now", job_id)["status"], "cancelled")
        self.backend.status.return_value = {"registered": False}
        self.assertIsNone(self.tick(job_id, 0))
        self.assertFalse(self.invoke("show", job_id).get("native_pause_pending"))
        self.send.assert_called_once()
