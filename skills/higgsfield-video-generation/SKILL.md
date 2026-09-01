---
name: higgsfield-video-generation
description: Generate exactly three project-compliant video candidates through the Higgsfield MCP after reading the required client reference at _references/higgsfield/higgsfield-video-generation.md. Use when another skill delegates Higgsfield video generation or a direct request asks for Higgsfield videos; do not use for prompt-only planning or another video provider.
---

# Higgsfield Video Generation

Generate three Higgsfield video candidates from one approved brief so the user can select the strongest direction.

## Required input contract

Before any model lookup, cost estimate, or generation call, identify the active client project root and read the complete client reference at `./_references/higgsfield/higgsfield-video-generation.md`. Resolve `./` against the client project root, not the invoking skill's directory or an incidental current working directory. The caller should provide:

- the client project root or unambiguous project context;
- the video prompt or creative brief;
- the intended placement or use;
- any approved image, video, audio, character, product, start-frame, or end-frame references.

For direct invocation, use the active client project. If the project root is unclear, or the canonical reference file is missing or unreadable, ask for the correct project root or reference file before generating. Do not search for or fall back to legacy guideline filenames.

Extract the allowed and forbidden aspect ratios; required duration, framing, safe areas, motion, pacing, camera behavior, transitions, visual style, palette, subject or product constraints, audio requirements, text and logo rules, exclusions, reference-asset roles, and output conventions. Do not invent client defaults. If the brief conflicts materially with the client reference, surface the conflict and wait for direction.

## Model and settings

- Use Higgsfield video-generation tools. Do not silently substitute another provider.
- Use a model explicitly required by the user, invoking skill, or client reference when it supports every required input and output constraint.
- Otherwise use Higgsfield's current general default, `seedance_2_5`, for ordinary text-to-video and multimodal reference consistency. Prefer `kling3_0` when the brief specifically requires multi-shot structure, audio, or motion transfer; prefer `minimax_h3` when it specifically requires 2K keyframes or combined image, video, and audio references.
- When the best fit remains unclear, call `higgsfield_models_recommend` with the concrete brief and input context. Before generation, call `higgsfield_models_get` for the selected model whenever duration, aspect ratio, parameters, or reference-media roles need verification.
- Choose an aspect ratio allowed by the client reference and suitable for the intended placement. Never use a forbidden ratio. If several ratios remain equally valid and placement does not resolve the choice, ask before spending credits.
- Apply the duration and model-specific settings from the client reference or brief. If duration is unspecified, use the selected model's default only when it fits the intended placement; otherwise ask. Do not rely on server coercion for a client-critical setting.
- Upload required user-provided attachments with `higgsfield_media_upload_and_confirm`, then pass their media IDs using roles supported by the selected model. For image-to-video, use the model's declared `start_image` or `image` role rather than `video`.

## Three-candidate generation

- Convert the brief and client rules into one finalized prompt that makes subject action, environment, camera movement, timing, and audio intent unambiguous. Keep the prompt, model, aspect ratio, duration, references, and all other critical settings identical across the three candidates.
- Generate exactly three candidates for each distinct prompt-and-placement pair. First call `higgsfield_estimate_video_cost` with the full settings and `count: 3`; this is read-only. Do not generate when the request only asks for planning, prompt writing, or a cost estimate.
- In the normal path, call `higgsfield_generate_video` once with the selected model and `params.count: 3`.
- If free-trial unlimited usage is offered, ask the user the tool-provided choice verbatim. With `use_unlim: true`, submit three one-result requests because unlimited calls cap `count` at one. Use `higgsfield_generate_video_batch`, wait on all returned job IDs with `higgsfield_jobs_wait`, then display the completed set once with `higgsfield_show_generation_by_ids`.
- Inspect returned `adjustments`. If the server caps the count, batch only the missing candidate slots with the same approved settings. Do not treat an adjusted result as compliant when its aspect ratio, duration, model, or reference handling violates the client reference.
- If a candidate fails, retry only the missing slot once with the same approved settings. If three completed candidates still cannot be produced, report the failure and ask before incurring further generation cost.

## Handoff

Present the three completed videos together as Candidate 1, Candidate 2, and Candidate 3. State the model, aspect ratio, duration, estimated total cost, and any server adjustment or known limitation. Preserve the finalized prompt and generation IDs when available, then ask the user or invoking skill to select a candidate. Do not choose a winner unless selection was part of the request.
