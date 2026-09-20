---
name: sanitize-artifacts
description: Prepare selected user-facing artifacts for delivery by removing prompt, conversation, and production residue while preserving facts, necessary constraints, attribution, and intended behavior.
disable-model-invocation: true
---

# Sanitize Artifacts

Make a selected artifact read as a coherent deliverable for its intended audience. Remove production residue from visible content and, when applicable, hidden content. This is not a general security, malware, or data-loss-prevention audit.

## Scope

- Use artifacts explicitly named or selected by the user. When the request refers to the current task and there is one clear deliverable, use that deliverable. Do not treat every dirty or recently viewed file as authorized scope; ask when the target is ambiguous.
- An explicitly selected artifact can come from the current session or earlier work.
- Identify the source of truth before editing. When an artifact is generated, update its source and regenerate it when practical instead of patching disposable output.
- Work on a delivery copy before removing hidden data that might be difficult to restore. Do not erase collaboration history from an artifact that is still being actively edited unless the user requested that result.

## Decide What Belongs

Classify each candidate item by its value to the audience:

1. **Audience content:** keep it and improve its clarity when needed.
2. **Production guidance:** apply it through the artifact's structure, wording, defaults, and examples without exposing the instruction itself.
3. **Production residue:** remove prompt text, conversation history, intermediate reasoning, corrective feedback, avoided approaches, tool narration, scaffolding, and examples that were supplied only to communicate intent.

Remove phrases such as "as requested", "the prompt says", or "unlike the previous version" when they only explain the production process. Do not copy a prompt example into the artifact unless the audience needs that example.

Constraints are not automatically residue. Preserve assumptions, compatibility limits, safety or legal warnings, citations, copyright and license notices, attribution, provenance, required disclosures, accessibility content, and anything else the audience needs for correct or safe use. Keep purely internal implementation or production constraints out of the deliverable. Remove only clearly accidental credentials or personal or confidential data that the audience does not need; when intent is uncertain, preserve it and report the uncertainty or ask for confirmation. Do not claim an exhaustive security or privacy scan.

## Inspect the Whole Artifact

1. Read the artifact as a new audience member. Check its purpose, audience, terminology, assumptions, headings, captions, links, examples, and voice.
2. Use appropriate format-specific tools when available. Inspect comments, tracked changes, speaker notes, document properties, author and path metadata, hidden rows or sheets, invisible or off-canvas objects, embedded files, and cached data when the format can carry them.
3. Rewrite the artifact itself instead of adding explanations about the cleanup. Keep one coherent voice and remove seams left by iterative feedback.
4. Verify facts, links, citations, required disclosures, and intended behavior. Render or open the delivery format when layout or hidden surfaces matter, then inspect it again.
5. Report any surface that available tools could not inspect. A text-only review is not proof that a packaged document contains no hidden data.

## Output

For text returned in chat, put the revised artifact first; do not preface it with cleanup or process commentary. Add a change summary only when the user asks for one.

For files, save the deliverable in the requested location. Otherwise, update the selected text source or create the delivery copy required for safe format-specific cleanup. Report changed paths, checks performed, and inspection limits outside the artifact. Do not modify unrelated files.
