---
name: higgsfield-image-generation
description: Generate exactly three project-compliant image candidates through the Higgsfield MCP, preferring gpt_image_2 and following the required client reference at _references/higgsfield/higgsfield-image-generation.md. Use when another skill delegates Higgsfield asset generation or a direct request asks for Higgsfield images; do not use for prompt-only planning or another image provider.
---

# Higgsfield Image Generation

Generate the image layer through the connected Higgsfield MCP and present three candidates so the user can select the strongest one.

## Required input contract

Before any generation call, identify the active client project root and read the complete client reference at `./_references/higgsfield/higgsfield-image-generation.md`. Resolve `./` against the client project root, not the invoking skill's directory or an incidental current working directory. The caller should provide:

- the client project root or unambiguous project context;
- the image prompt or creative brief;
- the intended placement or use when it affects composition;
- any approved reference images or elements.

For direct invocation, use the active client project. If the project root is unclear, or the canonical reference file is missing or unreadable, ask for the correct project root or reference file before generating. Do not search for or fall back to legacy guideline filenames.

Extract the allowed and forbidden aspect ratios, required composition and safe areas, visual style, palette, subject or product constraints, text and logo rules, exclusions, reference-asset requirements, and output conventions. Do not invent a client default. If the brief conflicts materially with the client reference, surface the conflict and wait for direction.

## Generation rules

- Use the Higgsfield image-generation tools. Do not silently substitute another provider.
- Prefer model ID `gpt_image_2`. Use another model only when the user or invoking skill explicitly requests it, or when `gpt_image_2` cannot meet a required constraint and the user approves the change.
- Choose an aspect ratio allowed by the client reference and appropriate for the intended placement. Never use a ratio that the reference forbids. If several ratios are valid and placement does not resolve the choice, ask before spending credits.
- Convert the brief and client rules into one finalized generation prompt. Keep that prompt, the model, aspect ratio, reference inputs, and other critical settings identical across the three candidates so the user is selecting visual variation rather than comparing changed requirements.
- Apply `resolution` and `quality` when the client reference specifies them; otherwise leave them unset and use the model defaults.
- Generate exactly three candidates for each distinct prompt-and-placement pair. In the normal path, call `higgsfield_generate_image` once with `params.model: "gpt_image_2"` and `params.count: 3`.
- If free-trial unlimited usage is offered, ask the user the tool-provided choice verbatim. With `use_unlim: true`, submit three one-result requests because unlimited calls cap `count` at one. Use `higgsfield_generate_image_batch`, wait on all returned job IDs with `higgsfield_jobs_wait`, then display the completed set once with `higgsfield_show_generation_by_ids`.
- Inspect returned `adjustments`. A server fallback must not violate the client reference; if it does, do not present the adjusted result as compliant.
- If a candidate fails, retry only the missing slot once with the same approved settings. If three completed candidates still cannot be produced, report the failure and ask before incurring further generation cost.

Use `higgsfield_models_get` for `gpt_image_2` only when its current aspect ratios, reference-media roles, or parameters must be verified. Upload required user-provided image attachments with `higgsfield_media_upload_and_confirm`, then pass the returned media IDs in the roles supported by the model.

## Handoff

Present the three completed images together as Candidate 1, Candidate 2, and Candidate 3. State the model, aspect ratio, and any server adjustment or known limitation. Preserve the finalized prompt and generation IDs when available, then ask the user or invoking skill to select a candidate. Do not choose a winner unless selection was part of the request.
