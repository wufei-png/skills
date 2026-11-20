# Uncounted capture profile

Use this profile for the Uncounted Godot project (`config/name="未计入"`) when it contains `tests/run_offscreen_web.py` and `tests/capture_scene_refinement.gd`. Read the target's current `docs/development.md` and runner before execution; this profile describes that runner, not a bundled capture tool.

## Prerequisites and command

The macOS runner needs Python 3, Node.js, the environment's configured Playwright, its matching independent `chrome-headless-shell`, the project's pinned Godot engine and matching Web debug export template. The runner queries that Playwright's read-only `install --dry-run chromium-headless-shell` output for the required browser location; it does not pick unrelated cached revisions or install missing dependencies. Its review copy bundles a local CJK system font. Keep the engine, browser, font copy and generated artifacts in the target project or its existing local caches; none is distributed with this skill.

From the target project root:

```sh
python3 tests/run_offscreen_web.py
```

For a layout review across the supported sizes:

```sh
python3 tests/run_offscreen_web.py --sizes 960,1280,1600
```

Use the project's documented default or pass the requested `--sizes`. The Web harness follows the runner's checkpoint list for `capture_scene_refinement`. Run captures serially for the same project to reuse its import cache.

## Result contract

Each invocation rebuilds current sources. It prints `OUTPUT` for a new `build/offscreen-review/<run-id>/` directory, then `REPORT` after successful capture. There is no `--skip-pack` mode.

Read that invocation's `offscreen-report.json` and require:

- `status: passed`, `fresh_export: true`, the requested `sizes` and the runner's complete ordered `stages` list.
- One existing `frames[].file` per requested size and stage. Check both width and height.
- `export_pck_sha256` matching that directory's `index.pck`; `harness_sha256` identifies the adapted capture script.
- Diagnostics in `logs_<size>` without script errors, failed assertions or warnings. Import, export and capture logs also live in the run directory.
- `renderer`, `headless_shell` and `review_font` identifying the actual render path; `native_device_validation` and `listening` remain false.

Inspect relevant before/after images such as vehicle/battery contact, boarding, closed doors and arrival. Report only what was inspected. SwiftShader and the bundled review font can differ from native rendering; keyframes cannot establish continuous motion or dialogue timing. The local font copy and exported game remain local review materials, not distributable assets.
