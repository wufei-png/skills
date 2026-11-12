---
name: image-quality-control
description: Review and refine AI-generated or edited raster artwork, controlling distracting detail while preserving the intended style and important features.
disable-model-invocation: true
---

# Image Quality Control

Review generated or edited raster artwork against the user's visual intent. For requested generation or edits, use the host's imagegen skill or tool and the target project's guidance. Reviewing an existing image does not authorize generation or editing. If requested generation or visual inspection is unavailable, say so without claiming results.

## Establish the visual intent

1. Read relevant available style guidance, selected references, prompts, and feedback. Use the reference the user selected; do not silently substitute a cleaner but aesthetically different revision.
2. Separate medium and style from subject and scene. Identify focal features, quiet areas, meaningful highlights, and intentional grain or broken paint.
3. Label every input as a style reference, edit target, or supporting input.

## Generate with appropriate detail

- Consult the applicable portions of [material prompts](references/material-prompts.md) when useful.
- Describe the desired surface and highlight organization positively before adding concise avoidance instructions. Use broad tonal masses where the style calls for them; keep expressive detail where it serves the image.
- Apply constraints to the relevant material or region. Do not attach the same scratch, grain, sparkle, or paper-gap treatment to every surface.
- For painterly detail-density feedback, distinguish brush width, mark count, and fine surface texture. Use the optional brush-widening module only when widening is desired; treat relative width factors as visual targets and preserve the selected style's focal accents.
- Preserve requested stylistic texture, stars, catchlights, foam, or other intentional bright marks. Visual cleanliness must serve the artwork rather than determine its style.
- For a new scene in a selected style, start from its selected reference rather than chaining unrelated previous variations. For an explicit local correction, attach that exact version as the edit target.

## Review and correct

1. Inspect the actual output at thumbnail and original resolution; use [visual review](references/visual-review.md) when useful. A prompt requirement is a target, not evidence that the output achieved it.
2. If a defect materially harms the artwork, identify its region, material, and appearance. Distinguish unwanted isolated specks from necessary light, texture, or deliberate abstraction.
3. When a correction is requested, make a targeted follow-up that states both the correction and the invariants. Avoid expanding the edit into a general style redesign. Reference-based generation is not guaranteed to preserve pixels outside the named region.
4. After a correction, compare the whole images and matching native-resolution details. Check whether apparent cleanliness came with lost brushwork, plastic surfaces, weakened lighting, changed identity, or overly regular highlight placement.
5. Keep a promising image with an explicit limitation when the remaining issue is an aesthetic tradeoff. Stop repeated smoothing when it weakens the chosen style; retain alternatives for user judgment.

Use visual inspection for this workflow. Do not require automated speckle detection, quantitative noise thresholds, or candidate-count targets.

## Deliver and record

- Save workspace-bound outputs. Preserve original references, artworks, and prior or approved versions; keep QA crops and contact sheets separate.
- Record actual prompts, tool arguments, input paths and roles, dimensions, and version relationships as needed by the user or project. Do not guess undisclosed settings or costs.
- Report visible successes, uncertainties, and style tradeoffs. Do not treat style approval as approval of individual images or claim user approval without it; respect requested review gates.
- Display each requested image inline when helpful, with stable numbering and a clear label. A contact sheet complements individual images, especially when the user asks to see every output.
