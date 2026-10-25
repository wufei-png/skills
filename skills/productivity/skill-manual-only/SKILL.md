---
name: skill-manual-only
description: Make user-selected skills require explicit invocation by setting and verifying both host-specific metadata fields while preserving their instructions and other configuration.
disable-model-invocation: true
---

# Manual-only Skills

Apply only to skills the user identifies. Resolve each source or installed path and any symlink target before editing; changing a symlink target changes every linked installation. Do not expand scope to other skills or copies without authorization.

Preserve skill instructions, references, licenses, and unrelated metadata. Set these YAML boolean values, updating an existing key rather than adding a duplicate:

- In the `SKILL.md` frontmatter: `disable-model-invocation: true`.
- In `agents/openai.yaml`, under `policy`: `allow_implicit_invocation: false`.

Create missing frontmatter or metadata only when the target is an identifiable skill. Retain its name, description, interface, and dependencies; create only the missing fields and containers. If YAML is malformed or has conflicting duplicate keys, report the issue before changing that file.

Parse both files after editing and verify the values are booleans at the correct paths, with unique keys. When source and installed copies are both in scope, verify each distinct target. Already-correct files stay unchanged; repeating this operation must produce no diff.

These settings require explicit invocation in supporting hosts. Names and descriptions may still appear in discovery metadata; do not claim the skill is hidden, fully disabled, or excluded from all context. Upstream replacement can remove local settings, so recheck after an update.

Report changed paths, each field's verified value, and any unresolved target. Follow the user's existing authorization for commits, pushes, and installation; changing invocation metadata does not authorize them by itself.
