---
name: context-soul-writer
description: Interview a user deeply to create, verify, or refresh `_context/soul.md`, the project source of truth for brand voice and writing behavior. Use when a client needs brand voice guidelines, tone calibration, verbal identity, writing rules, or an existing soul file made more specific and usable.
---

# Context Soul Writer

Build an evidence-backed voice guide that another writer can apply without guessing. Optimize for authenticity, specificity, and practical usefulness rather than finishing quickly.

## Ownership Boundary

`soul.md` owns how the brand sounds: voice, tone, reader relationship, diction, rhythm, mechanics, storytelling and persuasion style, stylistic guardrails, and calibrated examples. `about.md` owns what is true about the business: identity, offers, audiences, positioning, proof inventory, operations, policies, approved factual claims, official names, and conversion destinations.

Use facts from `about.md` to make voice questions realistic, but do not re-interview for or restate those facts in `soul.md`. For shared edges, divide ownership cleanly: `about.md` stores the proof or claim; `soul.md` stores how proof is presented. `about.md` stores the CTA action and destination; `soul.md` stores its tone and phrasing. `about.md` stores official terminology; `soul.md` stores stylistic vocabulary and ways of addressing the reader.

## Required Preflight

1. Resolve paths relative to the current client project.
2. Read `./_context/ABOUT.md` in full before asking substantive voice questions. Treat its business facts, audiences, offers, positioning, proof, claims, conversion paths, and constraints as context—not as proof of voice. Do not ask the user to repeat them.
3. If `about.md` is absent or unreadable, identify the exact expected path and pause the voice interview. Do not invent business context. Resume once the file exists, unless the user explicitly directs otherwise.
4. If `./_context/SOUL.md` exists, read it in full. Treat the session as a refresh or gap-filling pass: preserve still-confirmed guidance and focus on vague, contradictory, stale, or missing areas.
5. If a necessary business fact is missing or conflicts with the interview, flag it as an `about.md` dependency rather than resolving or duplicating it in `soul.md`.
6. Inspect other project material only when the user supplies it, points to it, or authorizes it as voice evidence. Never treat polished third-party copy as the client's natural voice without confirmation.

## Interview Method

At the start, explain that the interview will proceed in small rounds, may take many exchanges, and can be paused or resumed.

- Ask one coherent topic cluster per message, normally one to three questions. Use a single question when a deep answer is likely.
- Adapt every round to the user's prior answers and the facts in `about.md`. Do not dump a questionnaire or repeat resolved questions.
- Treat “relentless” as thorough and respectfully persistent, never coercive. Always permit `unknown`, `not applicable`, `skip`, or `come back later`.
- Challenge adjectives such as “authentic,” “bold,” “friendly,” or “professional.” Ask what each means in observable language, what its opposite looks like, and where the boundary is.
- Prefer evidence over preference: real samples, phrases the user says naturally, edits they make, brands they admire or reject, customer conversations, and before/after comparisons.
- Ask contrastive questions and force useful choices when answers remain broad: warmer or sharper, teacher or peer, polished or conversational, concise or expansive—and how far.
- Probe for context shifts. A single voice may change intensity by audience, channel, funnel stage, emotional situation, or risk level without becoming a different identity.
- Track confirmations, uncertainties, contradictions, skipped areas, and the evidence behind important guidance. Do not turn inference into fact.
- Periodically summarize the emerging voice in plain language and invite corrections.

Read [the interview and output guide](references/interview-guide.md) before conducting the interview. Cover every core area there; use optional probes only when they clarify this brand.

## Calibration

Once the voice model is substantially complete, write two or three short test passages relevant to the business using different situations or channels. Ask the user to react line by line: what feels right, what feels off, and how they would say it instead. Use their edits as higher-confidence evidence than abstract preferences.

If feedback conflicts with earlier guidance, surface the conflict and resolve it. Repeat calibration until the rules predict the user's choices reliably; do not stop after a merely acceptable sample.

## Completion Standard

The interview is complete only when:

- every core area is confirmed, explicitly unknown, not applicable, or intentionally skipped;
- vague qualities have been converted into observable writing behavior;
- important contradictions have been resolved or recorded;
- the voice has been tested with representative copy and corrected by the user;
- the user has reviewed a concise read-back of the proposed guide and approved writing it.

Do not claim completion because the conversation is long. If the user pauses, summarize completed areas, the next unanswered question, and what remains; preserve a resumable draft only with their permission.

## Deliverable

Write the approved guide to `./_context/SOUL.md`. Create `_context` only if the project context makes that safe and the user has authorized creation; otherwise report the blocker. Preserve unrelated existing content and user edits when refreshing the file.

The guide must be concise enough to use during drafting but specific enough to govern real choices. Include the source and confirmation status of important rules, an ISO `last_confirmed` date, unresolved questions, and examples that demonstrate the voice. Keep business facts in `about.md`; reference them from `soul.md` rather than duplicating a second business profile. Examples may use business facts for realism, but they are demonstrations—not a second factual record.

After writing, reread both `about.md` and `soul.md`, check for factual conflicts, placeholders, unsupported claims, and internal contradictions, then report the saved path and any unresolved items.

## Boundaries

The user is the authority on their voice. Public research may reveal brand presentation, but it cannot establish authentic intent; browse only when requested or authorized, cite what was researched, and let the user accept or reject it.

Do not request secrets, private customer data, or confidential material that is unnecessary for voice modeling. When examples contain sensitive information, ask for redacted excerpts.
