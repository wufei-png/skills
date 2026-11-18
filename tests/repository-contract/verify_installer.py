#!/usr/bin/env python3
"""Compare the repository skill tree with the installer's discovery output."""

from __future__ import annotations

import argparse
import sys

from skill_contract import ROOT, verify_installer


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--package",
        required=True,
        help='installer package to execute, for example "skills@1.9.0" or "skills@latest"',
    )
    arguments = parser.parse_args()
    report = verify_installer(arguments.package, ROOT)
    print(
        f"Repository skills ({len(report.repository_names)}): "
        f"{', '.join(sorted(report.repository_names))}"
    )
    print(
        f"Installer discovery ({len(report.discovered_names)}): "
        f"{', '.join(sorted(report.discovered_names))}"
    )
    if report.errors:
        print(f"{arguments.package} skill discovery failed:", file=sys.stderr)
        for error in report.errors:
            print(f"- {error}", file=sys.stderr)
        return 1
    print(f"{arguments.package}: installer discovery matches the repository skill tree")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
