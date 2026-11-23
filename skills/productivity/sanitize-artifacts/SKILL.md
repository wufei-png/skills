---
name: sanitize-artifacts
description: Prepare selected user-facing artifacts for delivery by removing prompt, conversation, and production residue while preserving facts, necessary constraints, attribution, and intended behavior.
disable-model-invocation: true
---

# Sanitize Artifacts

Remove production residue from visible content and, when applicable, hidden content.

## Scope

- Use artifacts explicitly named or selected by the user, including artifacts from earlier work. When the request refers to the current task and there is one clear deliverable, use that deliverable. Do not treat every dirty or recently viewed file as authorized scope. Ask when the target is ambiguous.
- Identify the source of truth before editing. When an artifact is generated, update its source and regenerate it when practical instead of patching disposable output.
- Work on a delivery copy before removing hidden data that might be difficult to restore. Do not erase collaboration history from an artifact that is still being actively edited unless the user requested that result.

## Decide What Belongs

Classify each candidate item by its value to the audience:

1. **Audience content:** keep it and improve its clarity when needed.
2. **Production guidance:** apply it through the artifact's structure, wording, defaults, and examples without exposing the instruction itself.
3. **Production residue:** remove prompt text, conversation history, intermediate reasoning, corrective feedback, avoided approaches, tool narration, scaffolding, and examples that were supplied only to communicate intent.

Remove phrases such as "as requested", "the prompt says", or "unlike the previous version" when they only explain the production process. Do not copy a prompt example into the artifact unless the audience needs that example.

Preserve assumptions, compatibility limits, safety or legal warnings, citations, copyright and license notices, attribution, provenance, required disclosures, accessibility content, and anything else the audience needs for correct or safe use. Keep purely internal implementation or production constraints out of the deliverable. Remove only clearly accidental credentials or personal or confidential data that the audience does not need. When intent is uncertain, preserve it and report the uncertainty or ask for confirmation.

## Inspect the Whole Artifact

1. Read the artifact as a new audience member. Check its purpose, audience, terminology, assumptions, headings, captions, links, examples, and voice.
2. Use appropriate format-specific tools when available. Inspect comments, tracked changes, speaker notes, document properties, author and path metadata, hidden rows or sheets, invisible or off-canvas objects, embedded files, and cached data when the format can carry them.
3. Rewrite the artifact itself instead of adding explanations about the cleanup. Keep one coherent voice and remove seams left by iterative feedback.
4. Verify facts, links, citations, required disclosures, and intended behavior. Render or open the delivery format when layout or hidden surfaces matter, then inspect it again.
   For batch checks of local file links in Markdown or HTML, consult the `docs-context-curator` skill when available.

## Output

For text returned in chat, put the revised artifact first. Add a change summary only when the user asks for one.

For files, save the deliverable in the requested location. Otherwise, update the selected text source or create the delivery copy required for safe format-specific cleanup. Report changed paths and checks outside the artifact.

Report the scope of format-specific inspection outside the artifact, including the surfaces checked and any surface the available tools could not inspect. Do not claim an exhaustive security or privacy scan.
