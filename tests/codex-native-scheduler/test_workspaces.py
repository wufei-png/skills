from __future__ import annotations

import subprocess
import tempfile
import unittest
from pathlib import Path

from support import job

# isort: split
from codex_scheduler.errors import SchedulerError
from codex_scheduler.workspaces import (
    ensure_direct_workspace,
    prepare_workspace,
    remove_safe_worktrees,
    worktree_risks,
    worktree_settings,
)


def git(cwd: Path, *arguments: str) -> str:
    return subprocess.run(
        ["git", "-C", str(cwd), *arguments],
        check=True,
        text=True,
        stdout=subprocess.PIPE,
    ).stdout.strip()


class WorkspaceTests(unittest.TestCase):
    def make_repository(self, root: Path) -> Path:
        repository = root / "repo"
        repository.mkdir()
        git(repository, "init", "-b", "main")
        git(repository, "config", "user.email", "test@example.com")
        git(repository, "config", "user.name", "Test")
        (repository / "file.txt").write_text("initial\n")
        git(repository, "add", "file.txt")
        git(repository, "commit", "-m", "initial")
        return repository

    def test_direct_dirty_requires_acknowledgement(self) -> None:
        with tempfile.TemporaryDirectory() as temporary:
            repository = self.make_repository(Path(temporary))
            (repository / "file.txt").write_text("dirty\n")
            with self.assertRaises(SchedulerError):
                ensure_direct_workspace(repository, allow_dirty=False)
            self.assertTrue(ensure_direct_workspace(repository, allow_dirty=True))

    def test_direct_workspace_is_rechecked_at_run_time(self) -> None:
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary)
            repository = self.make_repository(root)
            metadata = job(repository)
            metadata["workspace"]["is_git"] = True
            metadata["workspace"]["allow_dirty"] = False
            (repository / "file.txt").write_text("became dirty\n")
            with self.assertRaises(SchedulerError):
                prepare_workspace(
                    metadata,
                    "run-one",
                    state_root=root / "state",
                )

    def test_worktree_latest_resolves_local_branch(self) -> None:
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary)
            repository = self.make_repository(root)
            metadata = job(repository)
            metadata["workspace"] = worktree_settings(
                repository,
                base_policy="latest",
                base_ref=None,
            )
            cwd, record = prepare_workspace(
                metadata,
                "run-one",
                state_root=root / "state",
            )
            self.assertTrue(cwd.is_dir())
            self.assertEqual(
                record["base_commit"],
                git(repository, "rev-parse", "HEAD"),
            )
            self.assertTrue(record["branch"].startswith("codex-schedule/"))

    def test_explicit_base_ref_overrides_current_branch(self) -> None:
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary)
            repository = self.make_repository(root)
            git(repository, "switch", "-q", "-c", "alternate")
            (repository / "file.txt").write_text("alternate\n")
            git(repository, "add", "file.txt")
            git(repository, "commit", "-m", "alternate")
            alternate_commit = git(repository, "rev-parse", "HEAD")
            git(repository, "switch", "-q", "main")
            metadata = job(repository)
            metadata["workspace"] = worktree_settings(
                repository,
                base_policy="latest",
                base_ref="alternate",
            )
            _cwd, record = prepare_workspace(
                metadata,
                "run-explicit-ref",
                state_root=root / "state",
            )
            self.assertEqual(record["base_commit"], alternate_commit)

    def test_non_git_worktree_is_rejected(self) -> None:
        with tempfile.TemporaryDirectory() as temporary:
            with self.assertRaises(SchedulerError):
                worktree_settings(
                    Path(temporary),
                    base_policy="latest",
                    base_ref=None,
                )

    def test_dirty_and_unmerged_worktrees_block_removal(self) -> None:
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary)
            repository = self.make_repository(root)
            metadata = job(repository)
            metadata["workspace"] = worktree_settings(
                repository,
                base_policy="latest",
                base_ref=None,
            )
            cwd, _ = prepare_workspace(
                metadata,
                "run-one",
                state_root=root / "state",
            )
            (cwd / "file.txt").write_text("dirty\n")
            risks = worktree_risks(metadata, state_root=root / "state")
            self.assertEqual(risks[0]["reason"], "uncommitted changes")
            with self.assertRaises(SchedulerError):
                remove_safe_worktrees(metadata, state_root=root / "state")

            git(cwd, "add", "file.txt")
            git(cwd, "commit", "-m", "scheduled change")
            metadata["workspace"] = {
                "mode": "direct",
                "allow_dirty": True,
                "is_git": True,
            }
            risks = worktree_risks(metadata, state_root=root / "state")
            self.assertEqual(risks[0]["reason"], "unmerged commits")

    def test_clean_worktree_can_be_removed_safely(self) -> None:
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary)
            repository = self.make_repository(root)
            metadata = job(repository)
            metadata["workspace"] = worktree_settings(
                repository,
                base_policy="snapshot",
                base_ref=None,
            )
            cwd, record = prepare_workspace(
                metadata,
                "run-one",
                state_root=root / "state",
            )
            removed = remove_safe_worktrees(
                metadata,
                state_root=root / "state",
            )
            self.assertEqual(removed, [record["path"]])
            self.assertFalse(cwd.exists())


if __name__ == "__main__":
    unittest.main()
