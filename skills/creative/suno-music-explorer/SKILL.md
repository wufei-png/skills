---
name: suno-music-explorer
description: Explore Suno music from a blank canvas or bounded brief through budget-capped hypotheses, real listening, and human final selection. Use for iterative exploration, not one-off Creates or work beginning from an existing clip or upload.
disable-model-invocation: true
---

# Suno Music Explorer

Find the strongest supported musical direction within a bounded Suno budget. Audio is the evidence; prompt elegance and generation count are not. Use `$suno-create` for every submission and install both skills.

## Scope

Start from either a blank canvas or a brief containing a few hard boundaries. Treat everything else as explorable preference. In blank-canvas mode, invent the search space instead of asking for genre, BPM, instruments, mood, lyrics, or references.

Do not use this skill for a one-off Create, form filling, or exploration that begins from an existing clip, uploaded audio, Cover, or Extend.

## Establish the grant

Before any Create:

1. Separate non-negotiable constraints from soft preferences.
2. Obtain a maximum Create count and, if the user provides one, a credit cap. A vague request such as “go explore” is not an unlimited spending grant.
3. Treat each cap as a ceiling, never a quota. Stop early when the evidence or a safety condition calls for it.
4. If the limit is one Create, route to `$suno-create`. Two Creates permit only simplified exploration. Three is the minimum for a targeted variant.
5. Resolve the persistent ledger as described in [references/ledger.md](references/ledger.md). Confirm before creating a new `.suno-explorer/` directory.

The grant authorizes sequential submissions within its remaining limits. It does not authorize retries after ambiguous outcomes, spending beyond a changed provider price, or unrelated account actions.

## Explore

### Probe

Write two distinct identities as short record blurbs: emotional promise, vocal or instrumental stance, harmonic world, and production character. Vary the identity, not just tags. Submit one Create for each identity. Never repeat an unchanged prompt to manufacture confidence.

If the grant is only two Creates, audition the candidates and report a `probe winner`. Stop there.

### Listen and choose a direction

Audition actual audio before spending further. If reliable audio access is available, analyze composition, hook, transitions, performance artifacts, and production, then ask the user for the comparison that matters. If audio access is unavailable, present the candidate links or IDs and wait for the user's listening result.

Do not continue, rank by metadata, or infer quality from prompts when nobody has listened. If both identities are weak, introduce at most one new identity only when the remaining grant still leaves room for a targeted variant; otherwise stop.

### Targeted variants

Choose the stronger identity and change one or two named variables per Create. Generate a repair, focused improvement, adventurous variant, or challenger. Preserve beneficial accidents and distinguish current quality from potential.

After three total Creates, the strongest candidate is only a `provisional leader`. Additional challengers describe exploration depth; they never prove quality automatically.

### Finish

Stop when the cap is reached, two purposeful mutation rounds fail to improve the leader, the remaining defects are not worth another Create, or the user stops. A user who actually listened and explicitly chose a result creates a `human-selected final`. Otherwise report only `best-so-far`.

The agent may recommend a final based on listening evidence, but it cannot replace the user's final auditory judgment.

## Submission and recovery

Give `$suno-create` the current package, remaining grant, ledger path, and hypothesis. Submit one Create at a time. After each attempt, record the submission state before deciding what happens next.

An ambiguous submission pauses exploration. Reconcile the Suno library and ledger; never switch transport and resubmit the same package unless non-submission is confirmed and the grant still covers it.

Communicate at grant or ledger decisions, listening gates, anomalies, cap changes, and the final handoff. Keep routine ledger updates quiet. Use the user's language.

## Red flags

Unbounded spend; unchanged rerolls; multiple simultaneous Creates; continuing unheard; funding the least-bad direction; treating challenger count as quality proof; retrying an ambiguous submission; calling an unconfirmed result final
