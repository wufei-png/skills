#!/usr/bin/env python3
"""Serial, counter-observed whole-song Studio WAV downloads via suno-cli."""

import argparse
import json
import os
from pathlib import Path
import shutil
import subprocess
import sys
import tempfile
from urllib.parse import urlsplit
from uuid import UUID


class Stop(Exception):
    pass


def song_id(value):
    if "://" in value:
        try:
            parts = urlsplit(value)
            hostname = parts.hostname
        except ValueError:
            raise Stop("Invalid song URL") from None
        path = parts.path.strip("/").split("/")
        if parts.scheme != "https" or hostname not in {"suno.com", "www.suno.com"} or len(path) != 2 or path[0] != "song":
            raise Stop("Unsupported song URL")
        value = path[1]
    try:
        return str(UUID(value))
    except (ValueError, AttributeError):
        raise Stop(f"Invalid song ID: {value}") from None


def cli(*args, timeout=60):
    try:
        result = subprocess.run(
            ["suno", *args, "--json", "--no-browser"],
            capture_output=True, text=True, errors="replace", timeout=timeout, check=False,
        )
    except FileNotFoundError:
        raise Stop("suno CLI not found on PATH") from None
    except subprocess.TimeoutExpired:
        raise Stop(f"suno {args[0]} timed out; outcome may be uncertain") from None
    try:
        payload = json.loads(result.stdout)
    except json.JSONDecodeError:
        raise Stop(f"suno {args[0]} returned unreadable JSON (exit {result.returncode})") from None
    if result.returncode != 0 or not isinstance(payload, dict) or payload.get("status") != "success" or not isinstance(payload.get("data"), dict):
        raise Stop(f"suno {args[0]} failed (exit {result.returncode}); check login, network, and provider status")
    return payload["data"]


def check_cli():
    usage = cli("download", "--help").get("usage")
    if not isinstance(usage, str) or not all(flag in usage for flag in ("--source", "studio", "--format", "wav")):
        raise Stop("The installed CLI does not advertise the required Studio WAV options")


def account():
    data = cli("credits")
    features = data.get("accessible_features")
    usage = data.get("download_usage")
    if not isinstance(features, list) or not any(isinstance(f, dict) and f.get("name") == "studio" for f in features):
        raise Stop("Studio access is missing or cannot be verified")
    if not isinstance(usage, dict):
        raise Stop("Download usage is unavailable")
    fields = {
        "monthly_used": usage.get("current_period_downloads_used"),
        "monthly_limit": usage.get("current_period_downloads_limit"),
        "additional_remaining": usage.get("additional_download_remaining"),
        "generation_credits": data.get("total_credits_left"),
    }
    if any(type(value) is not int or value < 0 for value in fields.values()):
        raise Stop("A required account counter is missing or invalid")
    return fields


def validate_wav(path):
    if path.suffix.lower() != ".wav" or not path.is_file() or path.stat().st_size < 44:
        raise Stop("Downloaded file is missing or too small to be a WAV")
    with path.open("rb") as audio:
        header = audio.read(12)
    if header[:4] not in (b"RIFF", b"RF64") or header[8:12] != b"WAVE":
        raise Stop("Downloaded file does not have a WAV header")
    probe = shutil.which("ffprobe")
    if probe:
        try:
            result = subprocess.run(
                [probe, "-v", "error", "-show_entries", "stream=codec_type", "-of", "json", str(path)],
                capture_output=True, text=True, errors="replace", timeout=30, check=False,
            )
            info = json.loads(result.stdout)
            streams = info.get("streams") if isinstance(info, dict) else None
            if result.returncode or not isinstance(streams, list) or not any(
                isinstance(stream, dict) and stream.get("codec_type") == "audio" for stream in streams
            ):
                raise Stop("ffprobe could not identify an audio stream")
        except (OSError, subprocess.TimeoutExpired, json.JSONDecodeError):
            raise Stop("ffprobe could not verify the downloaded WAV") from None
    return "wav-header-and-ffprobe" if probe else "wav-header"


def publish(source, output):
    for number in range(10000):
        name = source.name if number == 0 else f"{source.stem} ({number}){source.suffix}"
        target = output / name
        try:
            # Staging is inside output, so this is an exclusive same-filesystem publish.
            os.link(source, target)
            return target
        except FileExistsError:
            continue
        except OSError as error:
            raise Stop(f"Could not save without overwriting: {error.strerror}") from None
    raise Stop("Too many existing files with the same name")


def emit(value):
    print(json.dumps(value, ensure_ascii=False), flush=True)


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("songs", nargs="*", help="selected Suno song URLs or UUIDs")
    parser.add_argument("--output", default="~/Downloads/Suno", help="destination directory")
    parser.add_argument("--check", action="store_true", help="check Studio access and counters without downloading")
    args = parser.parse_args()
    if args.check and args.songs:
        parser.error("--check does not accept song IDs")
    if not args.check and not args.songs:
        parser.error("provide at least one explicitly selected song ID or URL")
    try:
        ids = [song_id(value) for value in args.songs]
        if len(set(ids)) != len(ids):
            raise Stop("The requested song list contains duplicate IDs")
        check_cli()
        before = account()
        if args.check:
            emit({"status": "ready", "source": "studio", "format": "wav", "counters": before})
            return 0
        output = Path(args.output).expanduser().resolve()
        output.mkdir(parents=True, exist_ok=True)
        for index, clip_id in enumerate(ids):
            if index:
                next_before = account()
                if next_before != before:
                    raise Stop("Counters changed between downloads; no further song was attempted")
                before = next_before
            emit({"status": "downloading", "id": clip_id, "counters_before": before})
            staging = Path(tempfile.mkdtemp(prefix=".suno-studio-", dir=output))
            record = {"id": clip_id, "source": "studio", "format": "wav", "counters_before": before}
            try:
                result = cli("download", clip_id, "--format", "wav", "--source", "studio", "--output", str(staging), timeout=900)
                paths = result.get("downloaded")
                if not isinstance(paths, list) or len(paths) != 1 or result.get("failed") != []:
                    raise Stop("CLI did not confirm exactly one downloaded file")
                source = Path(paths[0]).resolve(strict=True)
                if source.parent != staging.resolve():
                    raise Stop("CLI returned a file outside the staging directory")
                record["validation"] = validate_wav(source)
                record["path"] = str(publish(source, output))
            except (Stop, OSError, TypeError) as error:
                record["error"] = str(error)
            try:
                after = account()
                record["counters_after"] = after
                if after != before:
                    record["counter_change"] = True
                    record.setdefault("error", "Account counters changed; cause is not established")
            except Stop as error:
                record["error"] = f"{record.get('error', '')} Post-download counter check failed: {error}".strip()
                after = None
            if "path" in record or not any(staging.iterdir()):
                shutil.rmtree(staging)
            else:
                record["staging_directory"] = str(staging)
            record["status"] = "stopped" if "error" in record else "downloaded"
            emit(record)
            if "error" in record:
                return 1
            before = after
        return 0
    except (Stop, OSError) as error:
        emit({"status": "stopped", "error": str(error)})
        return 1


if __name__ == "__main__":
    sys.exit(main())
