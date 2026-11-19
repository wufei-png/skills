from __future__ import annotations

import tempfile
import unittest
from pathlib import Path
from unittest import mock

from support import SCRIPTS  # noqa: F401

# isort: split
from codex_scheduler.cli import parser
from codex_scheduler.errors import SchedulerError
from codex_scheduler.jobs import create_job, update_job
from codex_scheduler.runner import _codex_arguments
from codex_scheduler.storage import Store


class JobCreationTests(unittest.TestCase):
    def test_create_parser_accepts_existing_session_id(self) -> None:
        args = parser().parse_args(
            [
                "create",
                "--session-mode",
                "resume_fixed",
                "--session-id",
                "019f8ad6-436d-7d43-b980-2ce65da33755",
                "--at",
                "5h",
                "--prompt",
                "Review the changes.",
            ]
        )
        self.assertEqual(
            args.session_id,
            "019f8ad6-436d-7d43-b980-2ce65da33755",
        )

    def test_existing_session_requires_resume_fixed(self) -> None:
        with tempfile.TemporaryDirectory() as temporary:
            with self.assertRaisesRegex(
                SchedulerError,
                "--session-id requires --session-mode resume_fixed",
            ):
                self._create(Path(temporary), session_mode="new_each_run")

    def test_existing_session_requires_a_uuid(self) -> None:
        with tempfile.TemporaryDirectory() as temporary:
            for session_id in ("", " ", "--last", "not-a-uuid"):
                with self.subTest(session_id=session_id):
                    with self.assertRaisesRegex(
                        SchedulerError,
                        "--session-id must be a Codex session UUID",
                    ):
                        self._create(
                            Path(temporary),
                            session_mode="resume_fixed",
                            session_id=session_id,
                        )

    def test_existing_session_requires_direct_workspace(self) -> None:
        with tempfile.TemporaryDirectory() as temporary:
            with self.assertRaisesRegex(
                SchedulerError,
                "--session-id requires --workspace direct",
            ):
                self._create(
                    Path(temporary),
                    session_mode="resume_fixed",
                    workspace_mode="worktree",
                )

    def test_existing_session_rejects_codex_setting_overrides(self) -> None:
        with tempfile.TemporaryDirectory() as temporary:
            for options in (
                {"profile": "automation"},
                {"codex_config": ['model="gpt-5.6-sol"']},
            ):
                with self.subTest(options=options):
                    with self.assertRaisesRegex(
                        SchedulerError,
                        "--session-id cannot be combined",
                    ):
                        self._create(
                            Path(temporary),
                            session_mode="resume_fixed",
                            **options,
                        )

    def test_existing_session_is_persisted_and_resumed_without_overrides(
        self,
    ) -> None:
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary)
            store = Store(root / "state")
            store.initialize()
            store.config_path.write_text(
                'schema_version = 1\nbackend = "auto"\n\n'
                '[defaults]\nprofile = "automation"\n',
                encoding="utf-8",
            )
            created = self._create(
                root,
                store=store,
                session_mode="resume_fixed",
            )
            persisted = store.load_job(created["id"])

            self.assertEqual(
                persisted["fixed_session_id"],
                "019f8ad6-436d-7d43-b980-2ce65da33755",
            )
            self.assertTrue(persisted["session_seeded"])
            self.assertIsNone(persisted["codex"]["profile"])
            self.assertEqual(persisted["codex"]["config"], [])

            arguments = _codex_arguments(
                persisted,
                cwd=root,
                final_path=root / "final.txt",
                session_id=persisted["fixed_session_id"],
            )
            resume_index = arguments.index("resume")
            session_index = arguments.index("019f8ad6-436d-7d43-b980-2ce65da33755")
            self.assertLess(resume_index, session_index)
            self.assertEqual(arguments[-1], "-")
            self.assertNotIn("-p", arguments)
            self.assertNotIn("-c", arguments)

    def test_existing_session_can_seed_a_recurring_job(self) -> None:
        with tempfile.TemporaryDirectory() as temporary:
            created = self._create(
                Path(temporary),
                session_mode="resume_fixed",
                schedule={
                    "kind": "every",
                    "seconds": 3600,
                    "anchor": "2999-01-01T00:00:00+00:00",
                },
            )
            self.assertEqual(created["schedule"]["kind"], "every")
            self.assertTrue(created["session_seeded"])

    def test_existing_session_rejects_setting_updates_until_reset(self) -> None:
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary)
            store = Store(root / "state")
            created = self._create(
                root,
                store=store,
                session_mode="resume_fixed",
            )
            codex = {
                **created["codex"],
                "profile": "automation",
                "config": ['model_reasoning_effort="high"'],
            }
            with self.assertRaisesRegex(
                SchedulerError,
                "cannot be changed while continuing",
            ):
                update_job(
                    store,
                    created,
                    changes={"codex": codex},
                    prompt=None,
                    reset_session=False,
                )

            with mock.patch("codex_scheduler.jobs.backend_for") as backend_for:
                backend_for.return_value.register.return_value = None
                updated = update_job(
                    store,
                    created,
                    changes={"codex": codex},
                    prompt=None,
                    reset_session=True,
                )
            self.assertFalse(updated["session_seeded"])
            self.assertIsNone(updated["fixed_session_id"])
            self.assertEqual(updated["codex"]["profile"], "automation")

    @staticmethod
    def _create(
        root: Path,
        *,
        session_mode: str,
        workspace_mode: str = "direct",
        store: Store | None = None,
        profile: str | None = None,
        codex_config: list[str] | None = None,
        schedule: dict | None = None,
        session_id: str | None = "019f8ad6-436d-7d43-b980-2ce65da33755",
    ) -> dict:
        with (
            mock.patch(
                "codex_scheduler.jobs.selected_backend",
                return_value="launchd",
            ),
            mock.patch(
                "codex_scheduler.jobs.configured_commands",
                return_value=("/usr/bin/python3", ["codex"]),
            ),
            mock.patch("codex_scheduler.jobs.backend_for") as backend_for,
        ):
            backend_for.return_value.register.return_value = None
            return create_job(
                store or Store(root / "state"),
                prompt="Review the changes.",
                name="test",
                cwd=root,
                schedule=schedule or {"kind": "at", "at": "2999-01-01T00:00:00+00:00"},
                backend_name=None,
                session_mode=session_mode,
                session_id=session_id,
                workspace_mode=workspace_mode,
                base_policy="latest",
                base_ref=None,
                allow_dirty=False,
                overlap_policy="skip",
                profile=profile,
                codex_config=codex_config or [],
                codex_path=None,
                env_names=[],
                env_assignments=[],
                timeout_seconds=None,
                count=None,
                until=None,
                retention={"mode": "forever"},
            )


if __name__ == "__main__":
    unittest.main()
