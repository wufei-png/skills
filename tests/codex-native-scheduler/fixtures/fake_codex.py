#!/usr/bin/env python3
"""Codex JSONL fixture controlled through environment variables."""

from __future__ import annotations

import json
import os
import sys
import time
from pathlib import Path


def emit(event: dict[str, object]) -> None:
    print(json.dumps(event), flush=True)


def output_path(arguments: list[str]) -> Path | None:
    for flag in ("-o", "--output-last-message"):
        if flag in arguments:
            return Path(arguments[arguments.index(flag) + 1])
    return None


mode = os.environ.get("FAKE_CODEX_MODE", "success")
counter_path = os.environ.get("FAKE_CODEX_COUNTER")
attempt = 1
if counter_path:
    path = Path(counter_path)
    attempt = int(path.read_text() or "0") + 1 if path.exists() else 1
    path.write_text(str(attempt))

sys.stdin.read()
if mode == "stale_final":
    if attempt == 1:
        final = output_path(sys.argv)
        if final:
            final.write_text("stale reply from failed attempt\n")
        print("temporary transport failure", file=sys.stderr)
        raise SystemExit(1)
    print("configuration error: unknown field", file=sys.stderr)
    raise SystemExit(2)
if mode == "deterministic":
    print("configuration error: unknown field", file=sys.stderr)
    raise SystemExit(2)
if mode == "unknown_configuration":
    print(
        "unknown configuration field `future_key` in -c/--config override",
        file=sys.stderr,
    )
    raise SystemExit(2)
if mode == "transient" and attempt < 3:
    print("temporary transport failure", file=sys.stderr)
    raise SystemExit(1)

emit({"type": "thread.started", "thread_id": "session-test"})
emit({"type": "turn.started"})
if mode == "sleep":
    time.sleep(120)
if mode == "turn_failed":
    emit({"type": "turn.failed", "error": "fixture failure"})
    raise SystemExit(1)
emit({"type": "turn.completed"})
final = output_path(sys.argv)
if final:
    final.write_text("fixture final reply\n")
