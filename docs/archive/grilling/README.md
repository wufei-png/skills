# Grilling

Adaptive grilling: one question by default, dependency-safe batching on demand,
and only genuine decisions reach the user.

## Difference From Upstream

The upstream
[mattpocock/skills `productivity/grilling`](https://github.com/mattpocock/skills/blob/main/skills/productivity/grilling/SKILL.md)
asks the entire dependency-ready frontier in each round and prescribes a fixed
question format. This variant retains dependency-aware exploration while
keeping the interaction user-paced:

- Ask one question at a time by default. A user-provided per-turn maximum is a
  ceiling; batch only tightly related questions whose prerequisites are settled
  and whose answers do not depend on one another.
- Resolve clearly preferable choices under established constraints and facts
  available from context or tools without asking the user. Surface only genuine
  tradeoffs, with alternatives, comparison, and a recommendation.
- Revisit settled decisions when new answers invalidate their assumptions, then
  finish with a verified design summary and explicit implementation
  authorization before code changes.

## Install

### With `npx skills add`

Install the skill directly from this GitHub repository:

```bash
npx skills add wufei-png/grilling -g -y --agent codex
```

To install only this skill when the repository contains more skills in the
future:

```bash
npx skills add wufei-png/grilling --skill grilling -g -y --agent codex
```

### With `curl`

Install the complete skill into the shared user skill directory:

```bash
mkdir -p "$HOME/.agents/skills/grilling/agents"
curl -fsSL \
  https://raw.githubusercontent.com/wufei-png/grilling/main/SKILL.md \
  -o "$HOME/.agents/skills/grilling/SKILL.md"
curl -fsSL \
  https://raw.githubusercontent.com/wufei-png/grilling/main/agents/openai.yaml \
  -o "$HOME/.agents/skills/grilling/agents/openai.yaml"
```

## Publish

Publish this skill to ClawHub from the repository root:

```bash
clawhub skill publish . \
  --slug grilling \
  --name "Grilling" \
  --owner wufei-png \
  --source-repo wufei-png/grilling \
  --source-commit "$(git rev-parse HEAD)" \
  --source-ref main \
  --source-path . \
  --changelog "Describe the release"
```

Add `--dry-run` to preview the release without publishing it.
