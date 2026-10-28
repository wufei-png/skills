import json
import os
from pathlib import Path
import subprocess
import sys
import tempfile
import unittest


HELPER = Path(__file__).resolve().parents[2] / "skills/creative/suno-studio-download/scripts/download.py"
ID1 = "11111111-1111-4111-8111-111111111111"
ID2 = "22222222-2222-4222-8222-222222222222"

FAKE_SUNO = r'''#!/usr/bin/env python3
import json
import os
from pathlib import Path
import sys
import wave

state_path = Path(os.environ["SUNO_TEST_STATE"])
state = json.loads(state_path.read_text())
args = sys.argv[1:]
state["calls"].append(args)
if args[0] == "credits":
    snapshot = state["snapshots"].pop(0)
    state_path.write_text(json.dumps(state))
    if snapshot is None:
        print(json.dumps({"status": "error"}))
        sys.exit(1)
    print(json.dumps({"status": "success", "data": snapshot}))
elif args[0] == "download" and "--help" in args:
    state_path.write_text(json.dumps(state))
    print(json.dumps({"status": "success", "data": {"usage": "--source studio --format wav"}}))
elif args[0] == "download":
    output = Path(args[args.index("--output") + 1])
    path = output / ("song-" + args[1][:8] + ".wav")
    with wave.open(str(path), "wb") as audio:
        audio.setnchannels(1)
        audio.setsampwidth(2)
        audio.setframerate(8000)
        audio.writeframes(b"\0\0" * 80)
    state_path.write_text(json.dumps(state))
    if state.get("fail_download"):
        print(json.dumps({"status": "error"}))
        sys.exit(1)
    print(json.dumps({"status": "success", "data": {"downloaded": [str(path)], "failed": []}}))
else:
    state_path.write_text(json.dumps(state))
    sys.exit(2)
'''


def snapshot(used=8, additional=3, credits=100, studio=True):
    return {
        "accessible_features": [{"name": "studio"}] if studio else [],
        "total_credits_left": credits,
        "download_usage": {
            "current_period_downloads_used": used,
            "current_period_downloads_limit": 15,
            "additional_download_remaining": additional,
        },
    }


class DownloadWorkflowTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.root = Path(self.temp.name)
        self.addCleanup(self.temp.cleanup)
        fake = self.root / "suno"
        fake.write_text(FAKE_SUNO)
        fake.chmod(0o755)
        self.state_path = self.root / "state.json"
        self.output = self.root / "output"

    def run_helper(self, snapshots, *args, fail_download=False):
        self.state_path.write_text(json.dumps({"snapshots": snapshots, "calls": [], "fail_download": fail_download}))
        env = os.environ.copy()
        env["PATH"] = str(self.root) + os.pathsep + env.get("PATH", "")
        env["SUNO_TEST_STATE"] = str(self.state_path)
        result = subprocess.run(
            [sys.executable, str(HELPER), "--output", str(self.output), *args],
            capture_output=True, text=True, env=env, timeout=20,
        )
        events = [json.loads(line) for line in result.stdout.splitlines()]
        state = json.loads(self.state_path.read_text())
        return result, events, state["calls"]

    def test_check_is_read_only(self):
        result, events, calls = self.run_helper([snapshot()], "--check")
        self.assertEqual(result.returncode, 0, result.stderr)
        self.assertEqual(events[0]["status"], "ready")
        self.assertEqual([c[0] for c in calls], ["download", "credits"])
        self.assertIn("--help", calls[0])
        self.assertFalse(self.output.exists())

    def test_serial_studio_downloads_preserve_existing_files(self):
        self.output.mkdir()
        original = self.output / "song-11111111.wav"
        original.write_bytes(b"existing")
        result, events, calls = self.run_helper(
            [snapshot(), snapshot(), snapshot(), snapshot()],
            "https://suno.com/song/" + ID1, ID2,
        )
        self.assertEqual(result.returncode, 0, result.stderr)
        self.assertEqual([c[0] for c in calls], ["download", "credits", "download", "credits", "credits", "download", "credits"])
        for command in (calls[2], calls[5]):
            self.assertEqual(command[command.index("--source") + 1], "studio")
            self.assertEqual(command[command.index("--format") + 1], "wav")
            self.assertIn("--no-browser", command)
        completed = [event for event in events if event["status"] == "downloaded"]
        self.assertEqual(len(completed), 2)
        self.assertEqual(original.read_bytes(), b"existing")
        self.assertTrue(Path(completed[0]["path"]).name.endswith(" (1).wav"))
        self.assertTrue(all(Path(event["path"]).is_file() for event in completed))

    def test_additional_counter_decrease_stops_batch_after_first_song(self):
        result, events, calls = self.run_helper([snapshot(), snapshot(additional=2)], ID1, ID2)
        self.assertEqual(result.returncode, 1)
        self.assertEqual(sum(c[0] == "download" and "--help" not in c for c in calls), 1)
        self.assertEqual(events[-1]["counters_after"]["additional_remaining"], 2)
        self.assertTrue(events[-1]["counter_change"])
        self.assertTrue(Path(events[-1]["path"]).is_file())

    def test_unreadable_initial_counter_never_downloads(self):
        incomplete = snapshot()
        del incomplete["download_usage"]["additional_download_remaining"]
        result, events, calls = self.run_helper([incomplete], ID1)
        self.assertEqual(result.returncode, 1)
        self.assertEqual(events[-1]["status"], "stopped")
        self.assertEqual([c[0] for c in calls], ["download", "credits"])

    def test_missing_studio_access_never_falls_back_to_library(self):
        result, events, calls = self.run_helper([snapshot(studio=False)], ID1)
        self.assertEqual(result.returncode, 1)
        self.assertIn("Studio access", events[-1]["error"])
        self.assertEqual([c[0] for c in calls], ["download", "credits"])
        self.assertFalse(self.output.exists())

    def test_post_download_read_failure_retains_file_and_stops_batch(self):
        result, events, calls = self.run_helper([snapshot(), None], ID1, ID2)
        self.assertEqual(result.returncode, 1)
        self.assertIn("counter check failed", events[-1]["error"])
        self.assertTrue(Path(events[-1]["path"]).is_file())
        self.assertEqual(sum(c[0] == "download" and "--help" not in c for c in calls), 1)

    def test_concurrent_counter_change_stops_before_next_song(self):
        result, events, calls = self.run_helper([snapshot(), snapshot(), snapshot(used=9)], ID1, ID2)
        self.assertEqual(result.returncode, 1)
        self.assertIn("between downloads", events[-1]["error"])
        self.assertEqual(sum(c[0] == "download" and "--help" not in c for c in calls), 1)

    def test_failed_download_is_checked_and_staged_file_is_retained(self):
        result, events, calls = self.run_helper([snapshot(), snapshot()], ID1, ID2, fail_download=True)
        self.assertEqual(result.returncode, 1)
        self.assertEqual(calls[-1][0], "credits")
        self.assertTrue(any(Path(events[-1]["staging_directory"]).glob("*.wav")))
        self.assertEqual(sum(c[0] == "download" and "--help" not in c for c in calls), 1)

    def test_invalid_probe_response_still_checks_counters_and_keeps_staging(self):
        probe = self.root / "ffprobe"
        probe.write_text(f"#!{sys.executable}\nprint('null')\n")
        probe.chmod(0o755)
        result, events, calls = self.run_helper([snapshot(), snapshot()], ID1, ID2)
        self.assertEqual(result.returncode, 1)
        self.assertIn("ffprobe", events[-1]["error"])
        self.assertEqual(events[-1]["counters_after"]["additional_remaining"], 3)
        self.assertTrue(any(Path(events[-1]["staging_directory"]).glob("*.wav")))
        self.assertEqual(sum(c[0] == "download" and "--help" not in c for c in calls), 1)

    def test_duplicate_ids_are_rejected_before_any_cli_call(self):
        result, events, calls = self.run_helper([], ID1, "https://suno.com/song/" + ID1)
        self.assertEqual(result.returncode, 1)
        self.assertIn("duplicate", events[-1]["error"])
        self.assertEqual(calls, [])

    def test_malformed_url_is_rejected_without_echoing_it(self):
        result, events, calls = self.run_helper([], "https://[bad/song/?token=secret")
        self.assertEqual(result.returncode, 1)
        self.assertIn("URL", events[-1]["error"])
        self.assertNotIn("secret", result.stdout)
        self.assertEqual(calls, [])


if __name__ == "__main__":
    unittest.main()
