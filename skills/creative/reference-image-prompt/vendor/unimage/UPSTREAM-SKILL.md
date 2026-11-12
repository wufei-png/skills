---
name: unimage
description: Reverse-engineer a reference image into a production-ready prompt, then optionally validate drafts and repair drift after generation. Use when the user wants image-to-prompt, reverse prompt, reference-image replication, or source-vs-replica analysis. | 把参考图逆向成可直接用于生产的 prompt，并可在出图后做验证和纠偏。适用于 reverse prompt、参考图复刻、图转 prompt、原图与生成图差异分析。
metadata:
  short-description: Image-to-prompt reverse engineering with validation
user-invocable: true
allowed-tools: Read, Write, Edit, Bash
---

# Unimage

Turn a reference image into a prompt that can actually survive generation drift.

## Language

- Detect the user's language and stay in it.
- Unless the user asks otherwise, return the final generation prompt in English.

## Supported Modes

Route the request before doing work:

- `Reverse Prompt Mode`: the user gives one source image and wants a production-ready prompt.
- `Draft Validation Mode`: the user wants you to test or compare prompt candidates with a live image backend.
- `QC / Repair Mode`: the user gives both the original image and a generated replica, and wants gap analysis plus a corrected prompt.

## Core Rules

- Truth over decorative detail. Only include visible facts or strong inferences that matter.
- Preserve asset type. A candid snapshot stays a candid snapshot.
- Never guess identities, IP, brands, or product models unless confidence is very high.
- Visible text must be copied exactly when it matters.
- Spatial facts outrank empty hype words.
- If a generator is available, prefer a small empirical validation loop over stuffing more adjectives into the prompt.

## Workflow

### 1. Intake

Collect only the minimum context needed:

- What is the target use case, replication, inspiration, or QC?
- What image model or backend will the prompt be used on, if known?
- Does the user care most about identity, text, layout, lighting, materials, or overall vibe?

If the user only wants a prompt, do not over-interrogate.

### 2. Scene Auditor

Read [references/scene_auditor.md](references/scene_auditor.md) and follow it.

This stage decides:

- asset type
- entity certainty
- typography-driven flag
- coordinate-mapping trigger
- fidelity anchors

### 3. Detail Scanner + Spatial Architect

Read both:

- [references/detail_scanner.md](references/detail_scanner.md)
- [references/spatial_architect.md](references/spatial_architect.md)

If your runtime supports subagents, run these two stages in parallel. Otherwise do them sequentially.

### 4. Prompt Engine

Read [references/prompt_engine.md](references/prompt_engine.md) and synthesize the first-pass prompt.

Default output:

- one English prompt paragraph
- optional short `Avoid:` sentence only when a few failure modes are likely
- short config suggestions when the target backend exposes structured controls

### 5. Draft Validation

If a live generator is available, or the user explicitly asks to “补足一轮 / validate / try a few prompt variants”, read [references/draft_validation.md](references/draft_validation.md) and run that loop.

Use the bundled helper script when appropriate:

```bash
python3 scripts/e2e_unimage_eval.py --prompt-file <candidate-a> --prompt-file <candidate-b>
```

Do not block on this step when the user only wants the prompt draft.

### 6. QC / Repair

If the user provides both source and replica images, or says the first result is wrong and wants corrections, read [references/qc_inspector.md](references/qc_inspector.md).

Return:

- a short gap analysis
- 3 concrete corrections
- a revised prompt
- revised structured settings if they matter

## Output Contract

### Reverse Prompt Mode

Return:

1. the final prompt
2. optional `Config:` lines for aspect ratio, prompt enhancement, and a short negative prompt if needed

### Draft Validation Mode

Return:

1. which prompt candidate won
2. what failed in the others
3. the refined prompt to keep using

### QC / Repair Mode

Return:

1. fidelity score or pass/fail assessment
2. the highest-value mismatches
3. the repaired prompt and settings

## Bundled Files

- `references/scene_auditor.md`
- `references/detail_scanner.md`
- `references/spatial_architect.md`
- `references/prompt_engine.md`
- `references/draft_validation.md`
- `references/qc_inspector.md`
- `scripts/unimage_tool.py`
- `scripts/e2e_unimage_eval.py`

When dispatching a subagent, pass the relevant stage file content plus any upstream outputs it needs.
