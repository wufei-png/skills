# Reference-image prompt skills: evaluation and integration

Reassessed 2026-11-11 (Asia/Shanghai). The initial local skill independently restated much of the generic image-analysis, prompt and QC loop. That duplication was not sufficiently justified: Unimage's API helper is optional, so its existence is not a reason to avoid reusing the skill documentation.

| Project | Relevant capabilities | Decision |
| --- | --- | --- |
| [Unimage](https://github.com/huanmu-team/unimage) | MIT-licensed skill with six guides for scene audit, details, composition, prompt synthesis, draft validation and QC. Its optional backend script is not needed to use those guides. | Closest fit. Vendor the original entrypoint, six guides and license at a pinned commit. The adapter adds multiple-reference style extraction, project-aware provenance, visual review and user approval. |
| [image-reverse-prompt-skill](https://github.com/xyun1996/image-reverse-prompt-skill) | MIT-licensed structured visual schema and model-specific prompt compilation; its optional CLI supports configured providers. | Useful for schema and multi-model output, but its extra machinery is not required for this workflow. Keep as a reference rather than install a second overlapping core. |
| [Idea2Img](https://github.com/zyang-ur/idea2img) | Iterative multimodal image-design research implementation requiring separately configured model access. | Useful research context, not required as a second runtime. |
| [GIRL](https://github.com/WaynePincence/GIRL) | Describes generate/identify/refine/loop. | Its README labels usable workflow and code as work in progress. |

The vendor snapshot is documentation only; no upstream helper script is installed or run. The adapter treats Unimage's prompt length, formatting and score examples as guidance, and follows the active host's image-generation tools and target project's quality rules. `image-quality-control` is available separately for detailed visual review; neither skill automatically invokes the other. Source and license records are also maintained in the repository catalog and `LICENSES/`; the included license travels with a standalone skill installation.
