from __future__ import annotations

import datetime as dt
import os
import subprocess
import tempfile
import unittest
from pathlib import Path
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
        self.enterContext(
            mock.patch(
                "codex_scheduler.delivery.backend_for", return_value=self.backend
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
        self.send = self.enterContext(
            mock.patch(
                "codex_scheduler.delivery.subprocess.run",
                return_value=subprocess.CompletedProcess(
                    [], 0, f"Queued message message-1 for thread {THREAD}.\n", ""
                ),
            )
        )

    def invoke(self, *args: str) -> dict:
        return dispatch(
            parser().parse_args(["--state-dir", str(self.store.root), *args])
        )

    def create(self, *args: str) -> str:
        created = self.invoke(
            "create",
            "--cwd",
            str(self.root),
            "--session-mode",
            "queue_existing",
            "--every",
            "1h",
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
        self.assertEqual(self.send.call_args.args[0], argv)
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
