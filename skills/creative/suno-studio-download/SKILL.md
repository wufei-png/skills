---
name: suno-studio-download
description: Download selected Suno songs as Studio WAVs with per-song account counter checks. Use only when explicitly invoked.
disable-model-invocation: true
---

# Suno Studio Download

Download explicitly selected song IDs or `https://suno.com/song/<id>` links as whole-song WAVs. This workflow requires Python 3.11+ and an authenticated [paperfoot/suno-cli](https://github.com/paperfoot/suno-cli).

1. Check the current network route. If the system uses a PAC, apply its Suno and S3/CDN routing to the CLI process environment, preserving existing exclusions. Never expose tokens or signed URLs. If login has expired, use `suno auth --login` and let the user complete any browser challenge.
2. Set `SUNO_SKILL_DIR` to the directory containing this `SKILL.md`, then run the read-only preflight with the same environment as the download:

   ```bash
   python3 "$SUNO_SKILL_DIR/scripts/download.py" --check
   ```

   Stop if Studio access or the download and generation-credit counters cannot be read.
3. Run the helper with the selected IDs or links. Pass each song as a separate argument; `--output` defaults to `~/Downloads/Suno`.

   ```bash
   python3 "$SUNO_SKILL_DIR/scripts/download.py" 'SONG_ID_OR_URL'
   ```

The helper uses `--source studio --format wav`, processes songs serially, checks counters before and after each completed attempt, and preserves existing files. It stops on a failed download, unreadable counters, or any observed counter change. Do not switch to a Library or automatic route, or retry an uncertain attempt. If interrupted, inspect any staging directory and re-read counters before proceeding.

Counter updates can be delayed or reflect concurrent activity; unchanged counters do not guarantee that a download is free. Report each song's saved path, observed counters, validation, and any uncertainty. Do not claim listening or audio quality verification without listening.
