#!/usr/bin/env python3
"""Resolve and maintain a minimal Suno explorer ledger."""

from __future__ import annotations

import argparse
import json
import os
import re
import sys
import tempfile
from pathlib import Path
from typing import Any


SCHEMA_VERSION = 1
PHASES = {"probe", "listen", "variant", "paused", "finished"}
DECISIONS = {
    "probe-winner",
    "provisional-leader",
    "best-so-far",
    "human-selected-final",
}
FORBIDDEN_KEY_PARTS = {
    "account_balance",
    "audio_data",
    "audio_bytes",
    "cookie",
    "credential",
    "full_lyrics",
    "full_prompt",
    "password",
    "secret",
    "style_prompt",
    "token",
}
SESSION_ID = re.compile(r"[A-Za-z0-9][A-Za-z0-9._-]{0,95}\Z")


class LedgerError(ValueError):
    pass


def resolved(path: str | Path) -> Path:
    return Path(path).expanduser().resolve()


def nearest_existing_ledger(start: Path) -> Path | None:
    current = start if start.is_dir() else start.parent
    for parent in (current, *current.parents):
        candidate = parent / ".suno-explorer"
        if candidate.is_dir():
            return candidate
    return None


def run_files(ledger_dir: Path) -> list[str]:
    runs_dir = ledger_dir / "runs"
    if not runs_dir.is_dir():
        return []
    return [str(path.resolve()) for path in sorted(runs_dir.glob("*.json"))]


def resolve_ledger(
    start: Path,
    user_path: str | None,
    workspace_roots: list[str],
) -> dict[str, Any]:
    if user_path:
        candidate = resolved(user_path)
        if candidate.exists() and not candidate.is_dir():
            raise LedgerError(f"ledger path is not a directory: {candidate}")
        return {
            "status": "existing" if candidate.is_dir() else "proposed",
            "ledger_dir": str(candidate),
            "source": "user",
            "requires_confirmation": not candidate.is_dir(),
            "runs": run_files(candidate) if candidate.is_dir() else [],
        }

    existing = nearest_existing_ledger(resolved(start))
    if existing:
        return {
            "status": "existing",
            "ledger_dir": str(existing),
            "source": "ancestor",
            "requires_confirmation": False,
            "runs": run_files(existing),
        }

    roots = sorted({resolved(root) for root in workspace_roots})
    if len(roots) == 1:
        candidate = roots[0] / ".suno-explorer"
        return {
            "status": "proposed",
            "ledger_dir": str(candidate),
            "source": "workspace",
            "requires_confirmation": True,
        }

    return {
        "status": "unresolved",
        "ledger_dir": None,
        "source": "workspace",
        "requires_confirmation": False,
        "reason": "no workspace root" if not roots else "multiple workspace roots",
        "workspace_roots": [str(root) for root in roots],
    }


def ensure_no_sensitive_keys(value: Any, trail: tuple[str, ...] = ()) -> None:
    if isinstance(value, dict):
        for key, child in value.items():
            normalized = str(key).lower().replace("-", "_")
            if any(part in normalized for part in FORBIDDEN_KEY_PARTS):
                location = ".".join((*trail, str(key)))
                raise LedgerError(f"sensitive field is not allowed: {location}")
            ensure_no_sensitive_keys(child, (*trail, str(key)))
    elif isinstance(value, list):
        for index, child in enumerate(value):
            ensure_no_sensitive_keys(child, (*trail, str(index)))


def validate_ledger(data: Any) -> dict[str, Any]:
    if not isinstance(data, dict):
        raise LedgerError("ledger must be a JSON object")
    ensure_no_sensitive_keys(data)
    if data.get("schema_version") != SCHEMA_VERSION:
        raise LedgerError(f"schema_version must be {SCHEMA_VERSION}")
    if not SESSION_ID.fullmatch(str(data.get("session_id", ""))):
        raise LedgerError("invalid session_id")

    grant = data.get("grant")
    spent = data.get("spent")
    if not isinstance(grant, dict) or not isinstance(spent, dict):
        raise LedgerError("grant and spent must be objects")
    create_limit = grant.get("create_limit")
    creates_spent = spent.get("creates")
    if not isinstance(create_limit, int) or create_limit < 2:
        raise LedgerError("grant.create_limit must be an integer of at least 2")
    if not isinstance(creates_spent, int) or not 0 <= creates_spent <= create_limit:
        raise LedgerError("spent.creates must be within the Create grant")

    credit_limit = grant.get("credit_limit")
    credits_spent = spent.get("credits")
    if credit_limit is not None and (
        not isinstance(credit_limit, int) or credit_limit <= 0
    ):
        raise LedgerError("grant.credit_limit must be a positive integer or null")
    if credits_spent is not None and (
        not isinstance(credits_spent, int) or credits_spent < 0
    ):
        raise LedgerError("spent.credits must be a non-negative integer or null")
    if credit_limit is not None and credits_spent is not None:
        if credits_spent > credit_limit:
            raise LedgerError("spent.credits exceeds the credit grant")

    if data.get("phase") not in PHASES:
        raise LedgerError(f"phase must be one of {sorted(PHASES)}")
    if not isinstance(data.get("events"), list):
        raise LedgerError("events must be a list")
    decision = data.get("decision")
    if decision is not None and decision not in DECISIONS:
        raise LedgerError(f"decision must be null or one of {sorted(DECISIONS)}")
    if not isinstance(data.get("next_action"), str):
        raise LedgerError("next_action must be a string")
    return data


def atomic_write(path: Path, data: dict[str, Any]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    descriptor, temporary = tempfile.mkstemp(
        prefix=f".{path.name}.", suffix=".tmp", dir=path.parent
    )
    try:
        with os.fdopen(descriptor, "w", encoding="utf-8") as handle:
            json.dump(data, handle, ensure_ascii=False, indent=2, sort_keys=True)
            handle.write("\n")
            handle.flush()
            os.fsync(handle.fileno())
        os.replace(temporary, path)
    except BaseException:
        Path(temporary).unlink(missing_ok=True)
        raise


def load(path: Path) -> dict[str, Any]:
    try:
        data = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError) as error:
        raise LedgerError(f"cannot read ledger {path}: {error}") from error
    return validate_ledger(data)


def command_resolve(args: argparse.Namespace) -> dict[str, Any]:
    return resolve_ledger(Path(args.start), args.user_path, args.workspace_root)


def command_init(args: argparse.Namespace) -> dict[str, Any]:
    ledger_dir = resolved(args.ledger_dir)
    if ledger_dir.exists() and not ledger_dir.is_dir():
        raise LedgerError(f"ledger path is not a directory: {ledger_dir}")
    if not ledger_dir.exists() and not args.confirm_create:
        raise LedgerError("creating a new ledger directory requires --confirm-create")
    if not SESSION_ID.fullmatch(args.session_id):
        raise LedgerError("invalid session_id")

    path = ledger_dir / "runs" / f"{args.session_id}.json"
    if path.exists():
        raise LedgerError(f"run already exists: {path}")
    data = validate_ledger(
        {
            "schema_version": SCHEMA_VERSION,
            "session_id": args.session_id,
            "grant": {
                "create_limit": args.create_limit,
                "credit_limit": args.credit_limit,
            },
            "spent": {"creates": 0, "credits": None},
            "phase": "probe",
            "events": [],
            "decision": None,
            "next_action": "prepare two identity probes",
        }
    )
    atomic_write(path, data)
    return {"status": "created", "file": str(path), "ledger": data}


def command_record(args: argparse.Namespace) -> dict[str, Any]:
    path = resolved(args.file)
    data = load(path)
    try:
        event = json.loads(args.event_json)
    except json.JSONDecodeError as error:
        raise LedgerError(f"event-json is invalid: {error}") from error
    if not isinstance(event, dict) or not isinstance(event.get("kind"), str):
        raise LedgerError("event-json must be an object with a string kind")
    if not isinstance(event.get("summary"), str) or not event["summary"].strip():
        raise LedgerError("event-json must include a non-empty summary")
    ensure_no_sensitive_keys(event)

    if args.creates_spent is not None:
        data["spent"]["creates"] = args.creates_spent
    if args.credits_spent is not None:
        data["spent"]["credits"] = args.credits_spent
    if args.phase is not None:
        data["phase"] = args.phase
    if args.decision is not None:
        data["decision"] = args.decision
    if args.next_action is not None:
        data["next_action"] = args.next_action
    data["events"].append(event)
    validate_ledger(data)
    atomic_write(path, data)
    return {"status": "updated", "file": str(path), "ledger": data}


def command_validate(args: argparse.Namespace) -> dict[str, Any]:
    path = resolved(args.file)
    data = load(path)
    return {"status": "valid", "file": str(path), "ledger": data}


def parser() -> argparse.ArgumentParser:
    root = argparse.ArgumentParser(description=__doc__)
    commands = root.add_subparsers(dest="command", required=True)

    resolve_parser = commands.add_parser("resolve")
    resolve_parser.add_argument("--start", default=".")
    resolve_parser.add_argument("--user-path")
    resolve_parser.add_argument("--workspace-root", action="append", default=[])
    resolve_parser.set_defaults(handler=command_resolve)

    init_parser = commands.add_parser("init")
    init_parser.add_argument("--ledger-dir", required=True)
    init_parser.add_argument("--session-id", required=True)
    init_parser.add_argument("--create-limit", type=int, required=True)
    init_parser.add_argument("--credit-limit", type=int)
    init_parser.add_argument("--confirm-create", action="store_true")
    init_parser.set_defaults(handler=command_init)

    record_parser = commands.add_parser("record")
    record_parser.add_argument("--file", required=True)
    record_parser.add_argument("--event-json", required=True)
    record_parser.add_argument("--creates-spent", type=int)
    record_parser.add_argument("--credits-spent", type=int)
    record_parser.add_argument("--phase", choices=sorted(PHASES))
    record_parser.add_argument("--decision", choices=sorted(DECISIONS))
    record_parser.add_argument("--next-action")
    record_parser.set_defaults(handler=command_record)

    validate_parser = commands.add_parser("validate")
    validate_parser.add_argument("--file", required=True)
    validate_parser.set_defaults(handler=command_validate)
    return root


def main() -> int:
    args = parser().parse_args()
    try:
        result = args.handler(args)
    except LedgerError as error:
        print(json.dumps({"error": str(error)}, ensure_ascii=False), file=sys.stderr)
        return 2
    print(json.dumps(result, ensure_ascii=False, indent=2, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
