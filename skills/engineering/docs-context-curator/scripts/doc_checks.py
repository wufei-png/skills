#!/usr/bin/env python3
# SPDX-License-Identifier: MIT
"""Read-only, scoped documentation inventory and migration checks. No semantic verdicts."""
from __future__ import annotations

import argparse
import json
import os
import re
import subprocess
import sys
from html.parser import HTMLParser
from pathlib import Path, PurePosixPath
from urllib.parse import urljoin, urlsplit
from urllib.request import url2pathname


DOC_SUFFIXES = {".md", ".markdown", ".rst", ".adoc", ".txt", ".html", ".htm"}
TEMPLATE_MARKERS = ("{{", "${", "<%")
LIMITATIONS = [
    "Caller-supplied scopes and exclusions; Git ignores do not include .rgignore.",
    "Static Markdown/HTML paths and literal candidates only; no dynamic, website-root, template, or native-format resolver.",
    "No fragment, remote URL, semantic, clean-checkout, or agent-reading validation.",
]


class InputError(ValueError):
    pass


def relative_path(value: str, *, allow_root: bool = False) -> Path:
    if not isinstance(value, str) or not value or "\\" in value or "\0" in value:
        raise InputError(f"invalid relative path: {value!r}")
    parts = PurePosixPath(value)
    if parts.is_absolute() or ".." in parts.parts or re.match(r"^[A-Za-z]:", value):
        raise InputError(f"path must stay within the project: {value!r}")
    if not parts.parts and not allow_root:
        raise InputError("a file or subtree path is required")
    return Path(*parts.parts)


def checked_path(root: Path, value: str, *, allow_root: bool = False) -> Path:
    rel = relative_path(value, allow_root=allow_root)
    path = root / rel
    cursor = root
    for part in rel.parts:
        cursor /= part
        if cursor.is_symlink():
            raise InputError(f"symlink requires project-specific handling: {value}")
    if not path.resolve().is_relative_to(root):
        raise InputError(f"path escapes project: {value}")
    return path


def within(path: str, prefix: str) -> bool:
    return prefix == "." or path == prefix or path.startswith(prefix.rstrip("/") + "/")


class Scan:
    def __init__(self, args: argparse.Namespace):
        self.root = Path(args.root).expanduser().resolve()
        if not self.root.is_dir():
            raise InputError("--root must be an existing project directory")
        self.args = args
        self.skipped: dict[str, str] = {}
        self.read_count = 0
        self.selection = "explicit-move-plan"
        self.files: list[Path] = []

    def skip(self, path: str, reason: str) -> None:
        self.skipped[path] = reason

    def select(self) -> list[Path]:
        scopes = []
        for value in self.args.path:
            path = checked_path(self.root, value, allow_root=True)
            if not path.exists():
                raise InputError(f"scope does not exist: {value}")
            scopes.append(path.relative_to(self.root).as_posix())
        excludes = [relative_path(v).as_posix() for v in self.args.exclude]
        candidates: set[str] = set()
        git_files = None
        if not self.args.include_ignored:
            try:
                result = subprocess.run(
                    ["git", "--literal-pathspecs", "-C", str(self.root), "ls-files", "-z", "--cached", "--others", "--exclude-standard", "--", *scopes],
                    capture_output=True, check=False,
                )
                if result.returncode == 0:
                    git_files = result.stdout.decode("utf-8").split("\0")
            except (OSError, UnicodeError):
                pass
        if git_files is not None:
            self.selection = "git-tracked-and-untracked-nonignored"
            candidates.update(filter(None, git_files))
        else:
            self.selection = "scoped-filesystem"
            for scope in scopes:
                start = self.root / scope
                if start.is_file():
                    candidates.add(scope)
                    continue
                for current, dirs, files in os.walk(start, followlinks=False, onerror=lambda e: self.skip(str(e.filename), "unreadable directory")):
                    base = Path(current)
                    kept = []
                    for name in dirs:
                        path = base / name
                        rel = path.relative_to(self.root).as_posix()
                        if name == ".git" or any(within(rel, item) for item in excludes):
                            continue
                        if path.is_symlink():
                            self.skip(rel, "symlink")
                        else:
                            kept.append(name)
                    dirs[:] = kept
                    candidates.update((base / name).relative_to(self.root).as_posix() for name in files)
        for rel in sorted(candidates):
            if ".git" in PurePosixPath(rel).parts or any(within(rel, item) for item in excludes):
                continue
            try:
                path = checked_path(self.root, rel)
                if path.is_file():
                    self.files.append(path)
                else:
                    self.skip(rel, "missing or non-regular file")
            except (InputError, OSError) as exc:
                self.skip(rel, str(exc))
        return self.files

    def read(self, path: Path) -> str | None:
        rel = path.relative_to(self.root).as_posix()
        try:
            if path.stat().st_size > self.args.max_bytes:
                self.skip(rel, "exceeds --max-bytes")
                return None
            with path.open("rb") as stream:
                raw = stream.read(self.args.max_bytes + 1)
            if len(raw) > self.args.max_bytes:
                self.skip(rel, "exceeds --max-bytes")
                return None
            if b"\0" in raw:
                self.skip(rel, "binary content")
                return None
            text = raw.decode("utf-8")
            self.read_count += 1
            return text
        except (OSError, UnicodeError) as exc:
            self.skip(rel, f"unreadable UTF-8: {type(exc).__name__}")
            return None

    def report(self, items: list[dict], *, failed: bool = False) -> int:
        offset, limit = self.args.offset, self.args.limit
        payload = {
            "command": self.args.command,
            "items": items[offset:offset + limit],
            "total": len(items),
            "offset": offset,
            "has_more": offset + limit < len(items),
            "coverage": {
                "selection": self.selection,
                "files_selected": len(self.files),
                "files_read": self.read_count,
                "skipped": len(self.skipped),
                "skipped_examples": [{"path": p, "reason": r} for p, r in sorted(self.skipped.items())[:5]],
                "limitations": LIMITATIONS,
            },
        }
        print(json.dumps(payload, ensure_ascii=False, indent=2))
        return 1 if failed or self.skipped else 0


def prose(text: str) -> str:
    """Mask code and comments while retaining source line numbers for links."""
    lines = []
    fence = ""
    for line in text.splitlines(keepends=True):
        match = re.match(r"^ {0,3}(`{3,}|~{3,})(.*)$", line.rstrip("\r\n"))
        if fence:
            if match and match[1][0] == fence[0] and len(match[1]) >= len(fence) and not match[2].strip():
                fence = ""
            lines.append("\n" if line.endswith("\n") else "")
        elif match:
            fence = match[1]
            lines.append("\n" if line.endswith("\n") else "")
        else:
            lines.append(line)
    return re.sub(
        r"<!--.*?(?:-->|\Z)|(?<!`)(`+)(?!`)(?:(?!\r?\n[ \t]*\r?\n).)*?(?<!`)\1(?!`)",
        lambda match: re.sub(r"[^\r\n]", " ", match[0]),
        "".join(lines),
        flags=re.DOTALL,
    )


def destination(text: str, start: int) -> str | None:
    index = start
    while index < len(text) and text[index].isspace():
        index += 1
    if index == len(text):
        return None
    if text[index] == "<":
        end = text.find(">", index + 1)
        return text[index + 1:end] if end >= 0 else None
    token = []
    depth = 0
    while index < len(text):
        char = text[index]
        if char == "\\" and index + 1 < len(text):
            index += 1
            token.append(text[index])
        elif char == ")":
            if not depth:
                break
            depth -= 1
            token.append(char)
        elif char == "(":
            depth += 1
            token.append(char)
        elif char.isspace():
            break
        else:
            token.append(char)
        index += 1
    return "".join(token) or None


class HtmlLinks(HTMLParser):
    def __init__(self):
        super().__init__(convert_charrefs=True)
        self.base: str | None = None
        self.links: list[tuple[int, str, str]] = []

    def handle_starttag(self, tag, attrs):
        values = dict(attrs)
        if tag == "base":
            if self.base is None and values.get("href") is not None:
                self.base = values["href"]
            return
        for key in ("href", "src", "poster"):
            if values.get(key):
                self.links.append((self.getpos()[0], values[key], "html"))

    handle_startendtag = handle_starttag


def static_links(path: Path, text: str) -> list[tuple[int, str, str, str | None]]:
    cleaned = prose(text) if path.suffix.lower() in {".md", ".markdown"} else text
    html = HtmlLinks()
    html.feed(cleaned)
    base: str | None = path.as_uri()
    if html.base is not None:
        if html.base.startswith("/") or any(marker in html.base for marker in TEMPLATE_MARKERS):
            base = None
        else:
            base = urljoin(base, html.base)
    found = [(line, token, kind, base) for line, token, kind in html.links]
    if path.suffix.lower() in {".md", ".markdown"}:
        for line_no, line in enumerate(cleaned.splitlines(), 1):
            positions = [match.end() for match in re.finditer(r"\]\(", line)]
            definition = re.match(r"^ {0,3}\[[^\]]+\]:\s*", line)
            if definition:
                positions.append(definition.end())
            for position in positions:
                token = destination(line, position)
                if token:
                    found.append((line_no, token, "markdown", path.as_uri()))
    return sorted(set(found))


def local_destination(root: Path, token: str, base: str | None) -> tuple[Path | None, str | None]:
    if not token or token.startswith(("#", "/")) or any(marker in token for marker in TEMPLATE_MARKERS):
        return None, None
    value = urlsplit(urljoin(base or "", token))
    if value.scheme != "file" or value.netloc:
        return None, None
    path = Path(url2pathname(value.path))
    try:
        rel = path.relative_to(root).as_posix()
        return checked_path(root, rel, allow_root=True), None
    except (ValueError, OSError) as exc:
        return None, str(exc)


def inventory(scan: Scan) -> int:
    items = []
    for path in scan.select():
        item = {"path": path.relative_to(scan.root).as_posix(), "bytes": path.stat().st_size}
        if path.suffix.lower() in DOC_SUFFIXES:
            text = scan.read(path)
            if text is not None:
                title = next((line.strip().lstrip("# ") for line in prose(text).splitlines() if line.strip().startswith("#")), None)
                item["title"] = title[:200] if title else None
        items.append(item)
    return scan.report(items)


def refs(scan: Scan) -> int:
    target = checked_path(scan.root, scan.args.target)
    if not target.exists():
        raise InputError("--target must exist for reference lookup")
    target_rel = target.relative_to(scan.root).as_posix()
    items = []
    for path in scan.select():
        if path == target:
            continue
        text = scan.read(path)
        if text is None:
            continue
        rel = path.relative_to(scan.root).as_posix()
        if path.suffix.lower() in {".md", ".markdown", ".html", ".htm"}:
            for line, token, kind, base in static_links(path, text):
                resolved, _ = local_destination(scan.root, token, base)
                if resolved is not None and (resolved == target or (target.is_dir() and resolved.is_relative_to(target))):
                    items.append({"path": rel, "line": line, "kind": kind, "token": token})
        needles = (target_rel, target.name + "/" if target.is_dir() else target.name)
        for number, line in enumerate(text.splitlines(), 1):
            needle = next((value for value in needles if value in line), None)
            if needle:
                items.append({"path": rel, "line": number, "kind": "literal-candidate", "token": needle})
    return scan.report(items)


def links(scan: Scan) -> int:
    items = []
    for path in scan.select():
        if path.suffix.lower() not in {".md", ".markdown", ".html", ".htm"}:
            continue
        text = scan.read(path)
        if text is None:
            continue
        for line, token, kind, base in static_links(path, text):
            resolved, error = local_destination(scan.root, token, base)
            if error or (resolved is not None and not resolved.exists()):
                items.append({"path": path.relative_to(scan.root).as_posix(), "line": line, "kind": "unsafe-path" if error else "missing-path", "token": token})
    return scan.report(items, failed=bool(items))


def overlaps(left: str, right: str) -> bool:
    return within(left.casefold(), right.casefold()) or within(right.casefold(), left.casefold())


def moves(scan: Scan) -> int:
    plan = Path(scan.args.plan)
    if plan.stat().st_size > scan.args.max_bytes:
        raise InputError("move plan exceeds --max-bytes")
    entries = json.loads(plan.read_text(encoding="utf-8"))
    if not isinstance(entries, list) or not entries:
        raise InputError("move plan must be a nonempty JSON array")
    validated = []
    findings = []
    for entry in entries:
        if not isinstance(entry, dict) or set(entry) != {"source", "target"}:
            raise InputError("each move must have only source and target")
        source = checked_path(scan.root, entry["source"])
        target = checked_path(scan.root, entry["target"])
        a, b = source.relative_to(scan.root).as_posix(), target.relative_to(scan.root).as_posix()
        validated.append((a, b))
        if not source.exists() or not (source.is_file() or source.is_dir()):
            findings.append({"source": a, "target": b, "kind": "missing-or-special-source"})
        if target.exists():
            findings.append({"source": a, "target": b, "kind": "occupied-target"})
        if overlaps(a, b):
            findings.append({"source": a, "target": b, "kind": "overlapping-source-target"})
        for parent in target.parents:
            if parent == scan.root:
                break
            if parent.exists() and not parent.is_dir():
                findings.append({"source": a, "target": b, "kind": "target-parent-is-file"})
                break
        if source.is_dir():
            for current, dirs, files in os.walk(source, followlinks=False):
                if any((Path(current) / name).is_symlink() for name in dirs + files):
                    findings.append({"source": a, "target": b, "kind": "source-bundle-contains-symlink"})
                    break
    for index, (source, target) in enumerate(validated):
        for other_source, other_target in validated[:index]:
            if overlaps(source, other_source) or overlaps(target, other_target) or overlaps(source, other_target) or overlaps(target, other_source):
                findings.append({"source": source, "target": target, "kind": "conflicting-moves", "other_source": other_source, "other_target": other_target})
    return scan.report(findings, failed=bool(findings))


def positive(value: str) -> int:
    number = int(value)
    if number <= 0:
        raise argparse.ArgumentTypeError("must be positive")
    return number


def parser() -> argparse.ArgumentParser:
    result = argparse.ArgumentParser(description=__doc__)
    commands = result.add_subparsers(dest="command", required=True)
    for name in ("inventory", "refs", "links", "moves"):
        command = commands.add_parser(name)
        command.add_argument("--root", required=True, help="explicit project root")
        command.add_argument("--limit", type=positive, default=40)
        command.add_argument("--offset", type=int, default=0)
        command.add_argument("--max-bytes", type=positive, default=1024 * 1024)
        if name == "moves":
            command.add_argument("--plan", required=True, help="temporary JSON source/target array; never executed")
        else:
            command.add_argument("--path", action="append", required=True, help="relative file or subtree; repeat for multiple scopes")
            command.add_argument("--exclude", action="append", default=[], help="relative file or subtree to exclude")
            command.add_argument("--include-ignored", action="store_true", help="use filesystem traversal within the explicit scopes")
        if name == "refs":
            command.add_argument("--target", required=True)
    return result


def main(argv: list[str] | None = None) -> int:
    args = parser().parse_args(argv)
    try:
        if args.offset < 0:
            raise InputError("--offset must be nonnegative")
        scan = Scan(args)
        return {"inventory": inventory, "refs": refs, "links": links, "moves": moves}[args.command](scan)
    except (ValueError, OSError, UnicodeError, TypeError) as exc:
        print(json.dumps({"command": args.command, "error": str(exc)}, ensure_ascii=False))
        return 2


if __name__ == "__main__":
    raise SystemExit(main())
