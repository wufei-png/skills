from __future__ import annotations

import os
import subprocess
import sys
import tarfile
import tempfile
import unittest
from pathlib import Path

from support import ROOT


@unittest.skipIf(os.name == "nt", "The shell installer targets macOS and Linux")
class ShellInstallerTests(unittest.TestCase):
    def test_upgrade_keeps_its_backup_outside_skill_search_path(self) -> None:
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary)
            archive = root / "source.tar.gz"
            source = ROOT / "skills/productivity/codex-native-scheduler"
            with tarfile.open(archive, "w:gz") as bundle:
                for path in ("SKILL.md", "scripts/codex-schedule"):
                    bundle.add(
                        source / path,
                        arcname=f"snapshot/skills/productivity/codex-native-scheduler/{path}",
                    )
            curl = root / "curl"
            curl.write_text('#!/bin/sh\ncp "$SCHEDULER_TEST_ARCHIVE" "$4"\n')
            curl.chmod(0o755)
            environment = dict(
                os.environ,
                HOME=str(root),
                PATH=f"{root}{os.pathsep}{os.environ.get('PATH', '')}",
                PYTHON=sys.executable,
                SCHEDULER_TEST_ARCHIVE=str(archive),
            )
            command = ["sh", str(ROOT / "scripts/install-codex-native-scheduler.sh")]
            for _ in range(2):
                result = subprocess.run(
                    command, env=environment, capture_output=True, text=True
                )
                self.assertEqual(result.returncode, 0, result.stdout + result.stderr)

            agents = root / ".agents"
            self.assertEqual(
                [agents / "skills/codex-native-scheduler/SKILL.md"],
                list((agents / "skills").rglob("SKILL.md")),
            )
            backups = list((agents / "skill-backups").rglob("SKILL.md"))
            self.assertEqual(len(backups), 1)
            self.assertEqual(
                backups[0].read_bytes(), (source / "SKILL.md").read_bytes()
            )
