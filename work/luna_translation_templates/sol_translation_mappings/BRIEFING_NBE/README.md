# BRIEFING_NBE translation mappings

This directory contains validated, per-file translation mappings for the frozen JPN-only `BRIEFING_NBE` corpus.

Create one validated mapping/manifest set per `BRIEFING_NBE` template as translation work is completed. Mapping rows must bind the template's `file_id` and `unique_index`, and must contain translated `cn_text`; `eng_reference` and `mlg_cn_reference` are auxiliary evidence and must never be copied here as if they were completed translations.

Current checkpoint (`2026-09-12`):

- completed: 3 / 469 file_ids, 25 / 5,645 rows;
- completed file_ids: `BRIEFING_FILES_BLOCK_000000`, `BRIEFING_FILES_BLOCK_000790`, `BRIEFING_FILES_BLOCK_000A80`;
- next file_id: `BRIEFING_FILES_BLOCK_000D00`;
- remaining: 466 file_ids / 5,620 rows.

Continue in template filename order, one complete `file_id` at a time. Write the result as `BRIEFING_NBE/<file_id>.json` using the existing schema and do not create packet-level or `partNNN.json` translation artifacts. After committing mappings, run `python tools/rebuild_translation_state.py --write` from `work/luna_translation_templates/`, followed by `--check`.
