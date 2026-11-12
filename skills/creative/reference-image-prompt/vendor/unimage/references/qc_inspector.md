# QC Inspector

Use this stage when the user provides both the source image and the generated replica, or when they say the first result is close but still wrong.

## What To Check

1. Identity / likeness
2. Spatial accuracy
3. Text accuracy
4. Material fidelity
5. Lighting direction
6. Crop and framing

## Rules

- Focus on the few mismatches that matter most.
- Do not write a generic “looks different” critique.
- Convert every important mismatch into a concrete correction to the next prompt.

## Output Format

```markdown
### Gap Analysis
- Fidelity Score: [0-100%]
- Pass: [what matched]
- Fail: [what drifted]

### Optimization Directives
1. ...
2. ...
3. ...

### Revised Prompt
<updated prompt>

### Config
- aspect_ratio: ...
- enhance_prompt: ...
- negative_prompt: ...
```

Only include config lines that materially improve control.
