# Game Experience Review evaluation

`cases.json` defines manual behavior checks. Repository-contract tests validate the manifest and fixture paths; they do not execute the review workflow. Fixtures are written synthetic records, not rendered captures or human sessions.

The current protocol allows source reading for every lens and reserves staged reveal for explicit blind exercises. The former `information-isolation` fixture is now `source-informed-player`; current expectations are in the manifest.

## Revised workflow check — 2026-10-22

- Skill SHA-256: `c72c6b2a954ad4f35d14a6048657733b49326ae3ea5c8d78acd2e864113ac84f`.
- Reviewer packet SHA-256: `02406239dc7bcd588d4d0f1d2e5d01055e776bd53bd3c3f584af084d1905b81b`.

Each coordinator received a copied skill directory and one fixture scope in a fresh context, without the expectations manifest. It read the packet reference and dispatched self-contained briefs to three fresh reviewers, with some reviews sequential because of the concurrency limit. The authoring agent compared the returned results with the criteria. Scope restrictions were instruction-based, not a filesystem sandbox.

| Case | Revised execution and result |
| --- | --- |
| `source-informed-player` | End-to-end coordinator and three independent reviewers completed. Every lens read `game.py`, intent, and both player transcripts. The synthesis identified the undisclosed investigation cutoff, used source to confirm consequences, preserved the hidden route, and explicitly distinguished informed analysis from blind or human evidence. |
| `mixed-experience-coop` | Plan-only end-to-end coordinator and three fresh reviewers completed using `gpt-6-luna` with reasoning effort `max`. The result proposed mixed-experience pairs, observable contribution/recovery signals, slot counterbalancing, and neutral debrief questions without asserting a game defect or treating scripted input as human evidence. |
| `mismatched-evidence` | Current fixture/manifest validated; revised behavioral execution pending. |
| `intentional-ambiguity` | Earlier result below covers the previous protocol only; revised behavioral execution pending. |
| `inherited-context` | Fixture/manifest validated; behavioral execution pending. |
| `explicit-blind-exercise` | Fixture/manifest validated; revised behavioral execution pending. |

The source-informed review recommended disclosing inspection closure before commitment, without revealing the hidden alternative. It separated high confidence in the omission from untested human interpretation, preserved the engineer's investigative clue, and did not modify the fixture. The plan-only check kept its sample size a formative proposal, required a playable build before execution, and left device behavior and natural coordination unverified. These checks cover revised coordination, source-reading, and plan routing; they do not establish real-player understanding or rendered game quality.

## Earlier smoke check — 2026-10-22

This historical record tested an earlier protocol and does not validate the revised skill.

Skill SHA-256: `1bf389631efd6a37e7cc9ab863339ea0512f2bc7e2f7afbee8c15249233e029e`.

Reviewers received temporary copies, fresh contexts, assigned lenses, and explicit file allowlists. They did not receive the expectations manifest or other reports. The authoring coordinator knew the criteria; this was a direct reviewer smoke check, not a blinded end-to-end coordinator evaluation. File-access scope was instruction-based and self-reported, not enforced by a filesystem sandbox.

| Case | Execution and observed result |
| --- | --- |
| `information-isolation` | Three independent lenses identified the undisclosed investigation cutoff, preserved undiscovered alternatives, and separated the text defect from untested human impact. Explanatory prose was then removed from the initial player packet and a fresh new-player reviewer retested it: expectations were recorded before the outcome, then compared afterward. No new-player report disclosed private design information. |
| `intentional-ambiguity` | Three fresh lenses returned no supported defect. They preserved uncertain motives, recognized disclosed audience and action boundaries, and limited claims to the written material. |
| `mismatched-evidence` | Fixture and manifest validated; behavioral execution pending. |
| `mixed-experience-coop` | Fixture and manifest validated; behavioral execution pending. |

The staged new-player record initially stated that investigation availability after evacuation was unknown. After receiving the outcome, it identified an undisclosed commitment boundary and proposed advance consequence wording without a route solution. The three narrative-decision reviewers independently found no corrective rewrite justified by their respective packets.

These checks support the tested reviewer behavior only. They do not establish real-player understanding, game quality, native rendering, listening comfort, or input-device behavior. Use the manifest protocol for future isolated evaluations and record their actual scope.
