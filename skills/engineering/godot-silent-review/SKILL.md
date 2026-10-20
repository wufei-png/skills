---
name: godot-silent-review
description: Review Godot screenshots and motion keyframes without desktop windows through an existing project-local Web capture runner. Requires a compatible runner and excludes continuous video.
disable-model-invocation: true
---

# Godot Silent Review

Review the selected project's rendered frames; keep capture tools and game assets in that project.

1. Find the target Godot project from the user's path or current working directory and verify its `project.godot`. Never infer the target from this skill's installation directory. If several projects fit and context does not resolve the choice, ask which one.
2. Read the target's applicable repository guidance, capture documentation and runner. For Uncounted, read `references/uncounted.md`. Other projects need an existing runner with the same silent-execution and report contract below; if none is available, report the missing support. Do not create a capture system as part of a review.
3. Before executing, verify that Godot import/export uses `--headless`, every browser launch explicitly uses an independent `chrome-headless-shell` in headless mode, and missing dependencies stop execution. Reject a runner that can fall back to system Chrome, a native Godot window or a window moved offscreen. Keep generated files in the target project's ignored output directory.
4. Run the documented command from the target project, rebuilding current sources into a new result directory. Use the user's requested sizes or the project's documented default; add supported sizes when the review needs adaptation checks. If dependencies are missing or capture fails, report the error and available log path. Do not automatically install dependencies, reuse an older Web pack, or switch to graphical/video runners.
5. Read the report path emitted by this invocation. Require `status: passed`, `fresh_export: true`, the requested sizes, every expected stage, existing `frames[].file` images and a matching export SHA-256. Inspect diagnostics as well as exit status. Old reports and a PASS alone do not establish a current visual result.
6. Actually inspect the relevant images, including before/after keyframes for movement or contact issues. Reply in the user's language with findings, useful screenshot links and the report link. Separate observed visual results from script assertions, and disclose uncovered states or uninspected images. Identify the actual Web renderer and review font; these frames do not establish native font equivalence, native performance, listening quality, continuous animation timing or a human playthrough.
