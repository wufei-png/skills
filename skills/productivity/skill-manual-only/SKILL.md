---
name: skill-manual-only
description: Make user-selected skills require explicit invocation by setting and verifying both host-specific metadata fields while preserving their instructions and other configuration.
disable-model-invocation: true
---

# Manual-only Skills

For the skills the user specifies, create or update these YAML boolean fields without duplicate keys:

- In the `SKILL.md` frontmatter: `disable-model-invocation: true`.
- In `agents/openai.yaml`, under `policy`: `allow_implicit_invocation: false`.

Leave all other fields and content unchanged. Verify both values and report changed paths.
