---
name: skill-manual-only
description: Set and verify host-specific manual-only metadata for selected skills, preserving other configuration and reporting conflicts.
disable-model-invocation: true
---

# Manual-only Skills

For the skills the user specifies, create or update these YAML boolean fields without duplicate keys:

- In the `SKILL.md` frontmatter: `disable-model-invocation: true`.
- In `agents/openai.yaml`, under `policy`: `allow_implicit_invocation: false`.

These fields control implicit invocation only in hosts that support them. Report conflicts without changing them, such as `user-invocable: false` for Claude Code or VS Code, or `metadata.opencode/autoinvoke: true` for OpenCode 2.

For a skill bundled or intended for an OpenAI plugin, ensure `interface.display_name` and `interface.short_description` in `agents/openai.yaml` are non-empty strings. Keep valid existing values. For missing or invalid values, copy the corresponding non-empty strings from `SKILL.md` frontmatter or `metadata`, including `metadata.short-description`; otherwise derive them from `name` and `description`. Report any values that cannot be supplied.

Preserve all other fields and content. Inspect both files before editing; if either has invalid YAML, duplicate keys, or a required mapping with the wrong type, report the issue and leave both unchanged. Verify the parsed booleans and absence of duplicate keys; report verification results, changed paths, and conflicts. Claim host behavior only if tested.
