# BRIEFING_NBE translation mappings

This directory contains validated, per-file translation mappings for the frozen JPN-only `BRIEFING_NBE` corpus.

Create one validated mapping per `BRIEFING_NBE` template as translation work is completed. Mapping rows must bind the template's `file_id` and `unique_index`, and must contain translated `cn_text`; `eng_reference` and `mlg_cn_reference` are auxiliary evidence and must never be copied here as if they were completed translations.

## Required reading before translating

Always read and follow these files before continuing BRIEFING_NBE translation:

1. `work/luna_translation_templates/TRANSLATION_GUIDE.md` — the authoritative project translation rules.
2. `work/luna_translation_templates/BRIEFING_NBE/README.md` — BRIEFING_NBE template/resource notes.
3. `work/luna_translation_templates/sol_translation_mappings/BRIEFING_NBE/QUEUE.json` — the fixed 1–469 work order and current completed/remaining state.

Do not invent translation rules from chat memory. Japanese source text plus the complete current block context remains authoritative; MLG_CN and ENG are auxiliary only, as defined by `TRANSLATION_GUIDE.md`.

## Resume translation work

Do **not** scan the complete template directory or all mapping files merely to discover what to translate next.

1. Open `QUEUE.json`.
2. Take the first entry in `remaining`. Every entry is `[order, file_id]`.
3. The numeric `order` is permanent. Never renumber or reorder the 469 templates.
4. Check whether that exact file_id mapping already exists. If it does, mapping existence is authoritative: move that exact `[order, file_id]` entry from `remaining` to `completed`, update the two counts, and repeat until the first remaining item truly has no mapping.
5. Translate that complete file_id according to `TRANSLATION_GUIDE.md` and the BRIEFING_NBE template README.
6. Write `BRIEFING_NBE/<file_id>.json` using the existing mapping schema, commit it, then read it back from GitHub and verify it.
7. Only after successful read-back, update `QUEUE.json`: remove the same fixed-number entry from `remaining`, append it to `completed`, and update `remaining_count` / `completed_count`. Keep its `order` unchanged.
8. Continue immediately with the new first entry in `remaining`.

`QUEUE.json` is the single operational resume list. It contains the complete fixed order of all 469 BRIEFING_NBE templates: 363 `BRIEFING_FILES_BLOCK_*` templates followed by 106 `BRIEFING_MISSION_BLOCK_*` templates, in canonical filename order captured from the repository.

There is no separate cursor. The first entry of `remaining` is the resume pointer.

Existing mapping files are always the final truth for whether a file_id is complete; `QUEUE.json` is the fast resume index. If the two disagree after an interruption, reconcile `QUEUE.json` to the mappings before translating; never retranslate an existing mapping just because the queue is stale.

Continue one complete `file_id` at a time. Do not create packet-level or `partNNN.json` translation artifacts.

For the browser translation workflow, do not manually edit generated global state/progress/checkpoint files merely to record each translated file. The mapping plus `QUEUE.json` is sufficient for resuming work; run the repository state rebuild/check tooling separately when a synchronized global checkpoint is required.
