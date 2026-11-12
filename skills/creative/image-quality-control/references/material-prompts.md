# Material-specific prompt modules

Use only the module appropriate to the image. Replace bracketed fields with the actual scene and material. These are starting points for visual judgment, not universally validated denoising settings.

## Shared structure

Describe the subject, medium, composition and lighting first. Then identify quiet regions, detail-bearing edges, and the intended bright accents. For corrections, explicitly identify the edit target and repeat the invariants.

```text
Keep [quiet region] as connected tonal masses with restrained variation
appropriate to [material]. Let [silhouette / broad brushwork / curvature]
carry the form, and concentrate fine detail in [focal feature]. Keep
[intentional highlights or texture] legible. Reduce distracting isolated
bright pinpoints and repetitive microtexture only in [affected region].
```

## Transparent glass and water

Preserve visible reflections and light paths without making transparent materials dull or opaque.

```text
Preserve the intended transparency of [glass / water], with quiet areas where
appropriate. Keep structural edges, waterlines, reflections and caustics that
are actually visible. Reduce distracting tiny glints and scratch networks only
in [affected transparent area]. Preserve existing light sources and paths and
the intended variation in surrounding materials.
```

For an edit, state the framing and relevant existing features, such as material shape, water level or background geometry, as invariants. Do not infer a specific percentage improvement from this wording.

## Painterly oil, pastel and opaque paint

The selected artwork determines how loose, broken and tactile the painting should remain. Use its brushwork as the reference level.

```text
Preserve the selected reference's palette, color relationships, directional
brushwork and tactile irregular edges. Organize [water / fabric / background]
into connected painted planes with varied broad marks. Group distracting
tiny light fragments into a few irregular highlight passages along the same
light direction. Keep variation in length, spacing and broken edges, with
substantial painted interiors. Preserve intentional dry-brush breaks and
focal accents; avoid a uniform microtexture layer or global smoothing.
```

Do not impose an exact number of highlight bands by default: that can create mechanical repetition. Do not apply a calmer experimental revision when the user chose a more expressive predecessor.

### Optional brush-width increase

Use this module when the user identifies overly fine brushwork or asks to widen it. Brush scale, mark count, and fine texture are separate controls. Include an approximate factor only when the user provides one. Merge distracting small marks only when lower density fits the user's intent.

```text
Repaint the same scene with connected brush marks wider than in the edit
target at the same image size. Model existing elements as coherent masses
appropriate to their materials. Keep focal objects readable. Preserve the
intended mark density, fine textures, varied stroke directions and selected
bristled edges. Avoid adding unwanted stipple, scratches or white pinholes.
Preserve composition, palette and light; widen strokes rather than blur them.
```

Any requested factor is a qualitative target, not a guaranteed pixel measurement. Use the exact problem image as the edit target, compare matching native details, and describe the achieved change honestly. Do not apply a requested change to unrelated images.

## Matte clay, plaster and sculptural architecture

Use large forms, spatial depth and light to carry the artwork. Low-contrast material variation may remain.

```text
Use continuous matte [clay / plaster] surfaces with subtle low-contrast
variation. Describe volume through broad reflected light, rounded edges and
coherent shadows. Keep the main silhouette and negative spaces clearly
readable. Reserve surface detail for places that explain material and scale;
keep non-focal planes quiet without glitter, granular highlights or dense
scratch patterns.
```

For negative-space architecture, describe what forms the subject and its actual depth and scale. Preserve any visible cut-wall depth in thick openings. Check whether the intended void is misread as a painted emblem or solid sculpture; leave important extremities enough space.

## Intentionally textured work

For print grain, ink hatching, dry-brush illustration, rough canvas, snow, stars or sparkling water, retain the texture that defines the intended style. Apply local constraints only when its density or distribution harms the image. The user may intentionally prefer a lively or fragmented surface.

## Targeted correction scaffold

```text
The edit target is [exact image/version]. Change [specific defect] only in
[material/region]. Keep [composition, subject identity, silhouette, palette,
light direction, structural highlights and defining texture]. Preserve
[necessary fine detail]. Save the result as a new revision for comparison.
```
