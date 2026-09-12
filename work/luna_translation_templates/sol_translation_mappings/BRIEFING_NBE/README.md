# BRIEFING_NBE translation mappings

This directory contains validated, per-file translation mappings for the frozen JPN-only `BRIEFING_NBE` corpus.

Create one validated mapping per `BRIEFING_NBE` template as translation work is completed. Mapping rows must bind the template's `file_id` and `unique_index`, and must contain translated `cn_text`; `eng_reference` and `mlg_cn_reference` are auxiliary evidence and must never be copied here as if they were completed translations.

## Required reading before translating

Always read and follow these files before continuing BRIEFING_NBE translation:

1. `work/luna_translation_templates/TRANSLATION_GUIDE.md` — the authoritative project translation rules.
2. `work/luna_translation_templates/BRIEFING_NBE/README.md` — BRIEFING_NBE template/resource notes.
3. `work/luna_translation_templates/sol_translation_mappings/BRIEFING_NBE/TRANSLATION_QUEUE.md` — the fixed 001–469 work order and current completed/remaining state.

Do not invent translation rules from chat memory. Japanese source text plus the complete current block context remains authoritative; MLG_CN and ENG are auxiliary only, as defined by `TRANSLATION_GUIDE.md`.

## Resume translation work

Do **not** scan the complete template directory or all mapping files merely to discover what to translate next.

1. Open `TRANSLATION_QUEUE.md`.
2. Take the first entry under `## Remaining`.
3. Check whether that exact file_id mapping already exists. If it does, mapping existence is authoritative: move that fixed-number entry to `Completed`, update the counts, and repeat until the first remaining item truly has no mapping.
4. Translate that complete file_id according to `TRANSLATION_GUIDE.md` and the BRIEFING_NBE template README.
5. Write `BRIEFING_NBE/<file_id>.json` using the existing mapping schema, commit it, then read it back from GitHub and verify it.
6. Only after successful read-back, update `TRANSLATION_QUEUE.md`: remove the same fixed-number line from `Remaining`, append it to `Completed`, change `[ ]` to `[x]`, and update `Remaining` / `Completed` counts.
7. Continue immediately with the new first item under `Remaining`.

The numeric IDs in `TRANSLATION_QUEUE.md` are permanent canonical sequence numbers. Never renumber, reorder, or rebuild the queue from only missing mappings.

Existing mapping files are always the final truth for whether a file_id is complete; the queue is a fast resume index. If the two disagree after an interruption, reconcile the queue to the mappings before translating.

Continue one complete `file_id` at a time. Do not create packet-level or `partNNN.json` translation artifacts.

For the browser translation workflow, do not manually edit generated global state/progress/checkpoint files merely to record each translated file. The mapping plus `TRANSLATION_QUEUE.md` is sufficient for resuming work; run the repository state rebuild/check tooling separately when a synchronized global checkpoint is required.
