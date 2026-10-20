# Uncounted capture profile

Use this profile for the Uncounted Godot project (`config/name="未计入"`) when it contains `tests/run_offscreen_web.py` and `tests/capture_scene_refinement.gd`. Read the target's current `docs/development.md` and runner before execution; this profile describes that runner, not a bundled capture tool.

## Prerequisites and command

The macOS runner needs Python 3, Node.js, Playwright, an executable independent `chrome-headless-shell`, the project's pinned Godot engine and matching Web debug export template. Its review copy bundles a local CJK system font. Keep the engine, browser, font copy and generated artifacts in the target project or its existing local caches; none is distributed with this skill.

From the target project root:

```sh
python3 tests/run_offscreen_web.py --sizes 1280
```

For a layout review across the supported sizes:

```sh
python3 tests/run_offscreen_web.py --sizes 960,1280,1600
```

The default route is `capture_scene_refinement`. It must acknowledge all ten checkpoints in order:

1. `cabin-speech`
2. `door-conversation`
3. `vehicle-contact`
4. `choices`
5. `battery-contact`
6. `boarded`
7. `closed-with-battery`
8. `arrived-with-battery`
9. `observation`
10. `history-large`

Do not shorten `--stages`: the Web harness waits at each checkpoint. Select which resulting images to inspect instead. Other chapters and the prologue are not covered by this route.

## Result contract

Each invocation rebuilds current sources. It prints `OUTPUT` for a new `build/offscreen-review/<run-id>/` directory, then `REPORT` after successful capture. There is no `--skip-pack` mode.

Read that invocation's `offscreen-report.json` and require:

- `status: passed`, `fresh_export: true`, the requested `sizes` and the complete ordered `stages` list.
- One existing `frames[].file` per requested width and stage, with the expected 16:9 dimensions.
- `export_pck_sha256` matching that directory's `index.pck`; `harness_sha256` identifies the adapted capture script.
- Diagnostics in `logs_<width>` without script errors, failed assertions or warnings. Import, export and capture logs also live in the run directory.
- `renderer`, `headless_shell` and `review_font` identifying the actual render path; `native_device_validation` and `listening` remain false.

Inspect relevant before/after images such as vehicle/battery contact, boarding, closed doors and arrival. Report only what was inspected. SwiftShader and the bundled review font can differ from native rendering; keyframes cannot establish continuous motion or dialogue timing. The local font copy and exported game remain local review materials, not distributable assets.
