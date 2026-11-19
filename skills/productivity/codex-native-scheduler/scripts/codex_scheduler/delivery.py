"""Deliver scheduled prompts to an existing Codex thread."""

from __future__ import annotations

import os
import re
import shlex
import subprocess
from pathlib import Path
from typing import Any

from .backends import backend_for
from .errors import SchedulerError
from .storage import Store
from .util import atomic_write_text, iso, read_json, run_checked

QUEUE_MODE = "queue_existing"
QUEUE_RECEIPT = re.compile(r"^Queued message (\S+) for thread (\S+)\.$", re.M)
QUEUE_PARSE_ERROR = re.compile(
    r"^error: (?:unexpected argument '[^']+' found|unrecognized subcommand 'queue')$",
    re.M,
)


def queue_supports_resume(command: list[str], environment: dict[str, str]) -> bool:
    try:
        help_output = run_checked([*command, "queue", "--help"], env=environment)
    except (OSError, subprocess.TimeoutExpired) as exc:
        raise SchedulerError(f"cannot check Codex queue support: {exc}") from exc
    if help_output.returncode or not all(
        flag in help_output.stdout for flag in ("--thread", "--message")
    ):
        raise SchedulerError("install a Codex CLI with the queue command")
    return "--resume" in help_output.stdout


def _message(store: Store, job: dict[str, Any], run_id: str, prompt: str) -> str:
    prefix = shlex.join(
        [
            job["python_command"],
            job["runner_entrypoint"],
            "--state-dir",
            str(store.root),
        ]
    )
    status = f"{prefix} show {job['id']}"
    ack = f"{prefix} ack {job['id']} {run_id}"
    instructions = (
        f"Run `{status}`. Continue only if `pending_run_id` equals `{run_id}`. "
        f"Perform the task below, then run `{ack}`. "
        "For a paused, cancelled, or decommissioned job, acknowledge it and stop."
    )
    if job.get("stop_when"):
        instructions += (
            " Add `--pause` to the acknowledgement only after verifying this condition. "
            f"{job['stop_when']}\nReport if `native_pause_pending` is true."
        )
    return f"{instructions}\n\n{prompt}"


def deliver(
    store: Store, run: dict[str, Any], run_dir: Path, job: dict[str, Any]
) -> dict[str, Any]:
    thread = job["fixed_session_id"]
    launch_failed = False
    try:
        prompt = (run_dir / "prompt.txt").read_text(encoding="utf-8")
        argv = [*job["codex"]["command"], "queue", "--thread", thread]
        if job["queue_resume"]:
            argv.append("--resume")
        argv.extend(["--message", _message(store, job, run["id"], prompt)])
        result = subprocess.run(
            argv,
            cwd=job["cwd"],
            env=job["environment"],
            stdin=subprocess.DEVNULL,
            capture_output=True,
            text=True,
            errors="replace",
            timeout=job["timeout_seconds"] or 30,
            check=False,
        )
        stdout, stderr, exit_code = result.stdout, result.stderr, result.returncode
    except subprocess.TimeoutExpired as exc:
        stdout = (exc.stdout or b"").decode(errors="replace")
        stderr = (exc.stderr or b"").decode(errors="replace")
        exit_code = None
    except (OSError, ValueError) as exc:
        # The subprocess was never launched, so this occurrence cannot be queued.
        stdout, stderr, exit_code = "", str(exc), None
        launch_failed = True

    receipt = QUEUE_RECEIPT.search(stdout)
    if receipt and receipt[2] == thread:
        outcome = {"status": "queued", "queued_message_id": receipt[1]}
    elif launch_failed:
        outcome = {"status": "failed", "error": "could not launch codex queue"}
    elif exit_code == 2 and not stdout.strip() and QUEUE_PARSE_ERROR.search(stderr):
        outcome = {"status": "failed", "error": "Codex rejected the queue command"}
    else:
        outcome = {
            "status": "delivery_unknown",
            "error": "Codex did not confirm queue acceptance",
        }
    atomic_write_text(run_dir / "stdout.log", stdout)
    atomic_write_text(run_dir / "stderr.log", stderr)
    with store.short_lock(job["id"]):
        current = store.load_job(job["id"])
        # The target can acknowledge as soon as it receives the prompt.
        run = read_json(run_dir / "run.json")
        run.update(outcome, finished_at=iso(), exit_code=exit_code)
        run["resume_warning"] = (
            "Warning: message was queued, but could not resume" in stderr
        )
        store.save_run(run)
        if run["status"] == "failed" and current["pending_run_id"] == run["id"]:
            current["pending_run_id"] = None
            current["updated_at"] = iso()
            store.save_job(current)
    return run


def pause_queue_job(store: Store, job: dict[str, Any]) -> dict[str, Any]:
    if job["status"] == "active":
        job["status"] = "paused"
    job["native_pause_pending"] = True
    job["updated_at"] = iso()
    store.save_job(job)
    backend = backend_for(job["backend"], state_root=store.root)
    try:
        backend.unregister(job)
        native = backend.status(job)
    except (SchedulerError, OSError, subprocess.TimeoutExpired) as exc:
        native = {"registered": None, "error": str(exc)}
    if native.get("error"):
        native["registered"] = None
    if native.get("registered") is False:
        job.pop("native_pause_pending")
        store.save_job(job)
    return native


def acknowledge(
    store: Store, job_id: str, run_id: str, *, pause: bool
) -> dict[str, Any]:
    if not store.job_dir(job_id).is_dir():
        raise SchedulerError(f"job not found: {job_id}")
    with store.short_lock(job_id):
        job = store.load_job(job_id)
        if job["session_mode"] != QUEUE_MODE or (
            job["fixed_session_id"] != os.environ.get("CODEX_THREAD_ID")
        ):
            raise SchedulerError("ack must run from the target Codex thread")
        if job["pending_run_id"] != run_id:
            raise SchedulerError("run ID does not match the pending delivery")
        if pause and not job.get("stop_when"):
            raise SchedulerError("this job has no authorized stop condition")
        run = read_json(store.run_dir(job_id, run_id) / "run.json")
        run.setdefault("acknowledged_at", iso())
        store.save_run(run)
        native = pause_queue_job(store, job) if pause else None
        job["pending_run_id"] = None
        job["updated_at"] = iso()
        store.save_job(job)
        return {
            "job_id": job_id,
            "run_id": run_id,
            "acknowledged_at": run["acknowledged_at"],
            "status": job["status"],
            "native_pause_pending": bool(job.get("native_pause_pending")),
            "native": native,
        }
