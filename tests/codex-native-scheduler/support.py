"""Test helpers."""

from __future__ import annotations

import os
import sys
from pathlib import Path
from typing import Any

ROOT = Path(__file__).resolve().parents[2]
SCRIPTS = ROOT / "skills" / "productivity" / "codex-native-scheduler" / "scripts"
sys.path.insert(0, str(SCRIPTS))

from codex_scheduler.storage import Store  # noqa: E402
from codex_scheduler.util import SCHEMA_VERSION, iso  # noqa: E402


def job(
    root: Path,
    *,
    command: list[str] | None = None,
    schedule: dict[str, Any] | None = None,
    session_mode: str = "new_each_run",
    overlap: str = "skip",
    environment: dict[str, str] | None = None,
) -> dict[str, Any]:
    now = iso()
    return {
        "schema_version": SCHEMA_VERSION,
        "id": "job-20260720T100000Z-00000001",
        "name": "test",
        "revision": 1,
        "status": "active",
        "created_at": now,
        "updated_at": now,
        "backend": "systemd",
        "schedule": schedule or {"kind": "daily", "hour": 12, "minute": 0},
        "limits": {"count": None, "until": None},
        "stats": {
            "scheduled_started": 0,
            "consecutive_failures": 0,
            "last_scheduled_for": None,
            "last_run_id": None,
            "last_result": None,
        },
        "cwd": str(root),
        "workspace": {
            "mode": "direct",
            "allow_dirty": True,
            "is_git": False,
        },
        "session_mode": session_mode,
        "session_generation": 1,
        "fixed_session_id": None,
        "overlap_policy": overlap,
        "codex": {
            "command": command or [sys.executable, "-c", "raise SystemExit(1)"],
            "profile": None,
            "config": [],
            "strict_config": True,
        },
        "environment": environment
        or {
            "HOME": str(root),
            "PATH": os.environ.get("PATH", ""),
            "PYTHONUNBUFFERED": "1",
        },
        "environment_missing": [],
        "timeout_seconds": None,
        "retention": {"mode": "forever"},
        "python_command": sys.executable,
        "runner_entrypoint": str(SCRIPTS / "codex-schedule"),
    }


def store_with_job(root: Path, metadata: dict[str, Any]) -> Store:
    store = Store(root / "state")
    store.create_job(metadata, "Perform the test task.")
    return store
