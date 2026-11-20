from __future__ import annotations

import datetime as dt
import os
import time
import unittest
from unittest import mock

from support import SCRIPTS  # noqa: F401

# isort: split
from codex_scheduler.errors import SchedulerError
from codex_scheduler.schedules import (
    count_missed,
    latest_due,
    local_wall_time,
    make_schedule,
    next_due,
    occurrence_key,
)


class ScheduleTests(unittest.TestCase):
    def test_exactly_one_schedule_is_required(self) -> None:
        now = dt.datetime(2026, 7, 20, 10, tzinfo=dt.UTC)
        with self.assertRaises(SchedulerError):
            make_schedule(
                at=None,
                every=None,
                daily_at=None,
                weekly_at=None,
                now=now,
            )
        with self.assertRaises(SchedulerError):
            make_schedule(
                at="2h",
                every="1h",
                daily_at=None,
                weekly_at=None,
                now=now,
            )

    def test_every_keeps_anchor_and_coalesces(self) -> None:
        utc = dt.UTC
        schedule = {
            "kind": "every",
            "seconds": 3600,
            "anchor": "2026-07-20T10:00:00+00:00",
        }
        now = dt.datetime(2026, 7, 20, 13, 45, tzinfo=utc)
        self.assertEqual(
            latest_due(schedule, now),
            dt.datetime(2026, 7, 20, 13, tzinfo=utc),
        )
        self.assertEqual(
            next_due(schedule, now),
            dt.datetime(2026, 7, 20, 14, tzinfo=utc),
        )
        self.assertEqual(
            count_missed(
                schedule,
                dt.datetime(2026, 7, 20, 10, tzinfo=utc),
                dt.datetime(2026, 7, 20, 13, tzinfo=utc),
            ),
            2,
        )

    def test_daily_occurrence_key_ignores_dst_offset(self) -> None:
        schedule = {"kind": "daily", "hour": 1, "minute": 30}
        daylight = dt.datetime(
            2026,
            11,
            1,
            1,
            30,
            tzinfo=dt.timezone(dt.timedelta(hours=-4)),
        )
        standard = daylight.replace(tzinfo=dt.timezone(dt.timedelta(hours=-5)))
        self.assertEqual(
            occurrence_key(schedule, daylight),
            occurrence_key(schedule, standard),
        )

    @unittest.skipUnless(hasattr(time, "tzset"), "tzset is unavailable")
    def test_one_shot_uses_the_target_dates_local_offset(self) -> None:
        self.addCleanup(time.tzset)
        self.enterContext(mock.patch.dict(os.environ, {"TZ": "America/New_York"}))
        time.tzset()
        now = dt.datetime(2026, 3, 6, 12).astimezone()
        schedule = make_schedule(
            at="2026-03-09T09:00",
            every=None,
            daily_at=None,
            weekly_at=None,
            now=now,
        )
        self.assertEqual(schedule["at"], "2026-03-09T09:00:00-04:00")
        self.assertEqual(next_due(schedule, now).isoformat(), schedule["at"])

    @unittest.skipUnless(hasattr(time, "tzset"), "tzset is unavailable")
    def test_nonexistent_dst_wall_time_is_skipped(self) -> None:
        original = os.environ.get("TZ")
        try:
            with mock.patch.dict(os.environ, {"TZ": "America/New_York"}):
                time.tzset()
                self.assertIsNone(local_wall_time(dt.date(2026, 3, 8), 2, 30))
                schedule = {"kind": "daily", "hour": 2, "minute": 30}
                now = dt.datetime.fromtimestamp(
                    time.mktime((2026, 3, 8, 12, 0, 0, 0, 0, -1))
                ).astimezone()
                due = latest_due(schedule, now)
                self.assertEqual(due.date(), dt.date(2026, 3, 7))
                upcoming = next_due(schedule, now)
                self.assertEqual(upcoming.date(), dt.date(2026, 3, 9))
        finally:
            if original is None:
                os.environ.pop("TZ", None)
            else:
                os.environ["TZ"] = original
            time.tzset()


if __name__ == "__main__":
    unittest.main()
