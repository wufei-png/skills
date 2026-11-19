from __future__ import annotations

import datetime as dt
import os
import plistlib
import subprocess
import tempfile
import unittest
import xml.etree.ElementTree as ET
from pathlib import Path
from unittest import mock

from support import job

# isort: split
from codex_scheduler.backends.launchd import LaunchdBackend
from codex_scheduler.backends.systemd import SystemdBackend
from codex_scheduler.backends.windows import TASK_NS, TaskSchedulerBackend


def completed(
    arguments: list[str],
    returncode: int = 0,
    stdout: str = "",
    stderr: str = "",
) -> subprocess.CompletedProcess[str]:
    return subprocess.CompletedProcess(arguments, returncode, stdout, stderr)


class BackendTests(unittest.TestCase):
    def test_launchd_plist_is_private_and_uses_gui_domain(self) -> None:
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary)
            metadata = job(
                root,
                schedule={"kind": "daily", "hour": 3, "minute": 15},
            )
            calls: list[list[str]] = []

            def execute(arguments, **_kwargs):
                calls.append(arguments)
                return completed(arguments)

            backend = LaunchdBackend(state_root=root / "state", execute=execute)
            launchctl = root / "launchctl"
            launchctl.write_text("fixture")
            with (
                mock.patch(
                    "codex_scheduler.backends.launchd.shutil.which",
                    return_value=str(launchctl),
                ),
                mock.patch(
                    "codex_scheduler.backends.launchd.os.getuid",
                    return_value=501,
                    create=True,
                ),
            ):
                backend.register(metadata)
            path = backend.plist_path(metadata)
            with path.open("rb") as handle:
                payload = plistlib.load(handle)
            self.assertEqual(
                payload["StartCalendarInterval"],
                {"Hour": 3, "Minute": 15},
            )
            self.assertEqual(calls[-1][1:3], ["bootstrap", "gui/501"])
            if os.name != "nt":
                self.assertEqual(path.stat().st_mode & 0o777, 0o600)

    def test_systemd_uses_transient_user_timer(self) -> None:
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary)
            metadata = job(
                root,
                schedule={
                    "kind": "every",
                    "seconds": 1800,
                    "anchor": "2026-07-20T12:30:00+08:00",
                },
            )
            calls: list[list[str]] = []

            def execute(arguments, **_kwargs):
                calls.append(arguments)
                return completed(arguments)

            commands = {name: root / name for name in ("systemd-run", "systemctl")}
            for command in commands.values():
                command.write_text("fixture")
            backend = SystemdBackend(state_root=root / "state", execute=execute)
            with mock.patch(
                "codex_scheduler.backends.systemd.shutil.which",
                side_effect=lambda name: str(commands[name]),
            ):
                backend.register(metadata)
            registration = calls[-1]
            systemd_run = str(commands["systemd-run"].resolve())
            anchor = dt.datetime.fromisoformat(
                metadata["schedule"]["anchor"]
            ).astimezone()
            self.assertIn("--user", registration)
            self.assertIn(
                f"--on-calendar={anchor.strftime('%Y-%m-%d %H:%M:%S')}",
                registration,
            )
            self.assertIn("--on-unit-active=1800s", registration)
            self.assertIn("--timer-property=Persistent=true", registration)
            self.assertIn("--collect", registration)
            self.assertEqual(registration.count(systemd_run), 2)
            self.assertIn("_execute-trigger", registration)

    def test_windows_xml_has_interactive_principal_and_parallel_policy(self) -> None:
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary)
            target = dt.datetime.now().astimezone() + dt.timedelta(hours=1)
            metadata = job(
                root,
                schedule={"kind": "at", "at": target.isoformat()},
                overlap="parallel",
            )
            backend = TaskSchedulerBackend(state_root=root / "state")
            tree = backend.make_xml(metadata)
            xml = ET.tostring(tree.getroot(), encoding="unicode")
            self.assertIn("InteractiveToken", xml)
            self.assertIn("Parallel", xml)
            self.assertIn(str(metadata["python_command"]), xml)
            namespace = {"t": TASK_NS}
            boundary = tree.find(".//t:StartBoundary", namespace)
            self.assertIsNotNone(boundary)
            self.assertTrue(
                backend.task_name(metadata).startswith("\\CodexNativeScheduler-")
            )

    def test_windows_recurring_xml_uses_repetition(self) -> None:
        metadata = job(
            Path("C:/repo"),
            schedule={
                "kind": "every",
                "seconds": 3600,
                "anchor": "2026-07-20T12:00:00+08:00",
            },
        )
        backend = TaskSchedulerBackend(state_root=Path("C:/state"))
        xml = ET.tostring(backend.make_xml(metadata).getroot(), encoding="unicode")
        self.assertIn("PT60M", xml)
        self.assertIn("StopAtDurationEnd", xml)
        trigger = (
            backend.make_xml(metadata).getroot().find(f".//{{{TASK_NS}}}TimeTrigger")
        )
        self.assertIsNotNone(trigger)
        names = [child.tag.rsplit("}", 1)[-1] for child in trigger]
        self.assertEqual(
            names,
            ["Repetition", "StartBoundary", "Enabled"],
        )


if __name__ == "__main__":
    unittest.main()
