# BRIEFING_NBE translation mappings

This directory contains validated, per-file translation mappings for the frozen JPN-only `BRIEFING_NBE` corpus.

Create one validated mapping per `BRIEFING_NBE` template as translation work is completed. Mapping rows must bind the template's `file_id` and `unique_index`, and must contain translated `cn_text`; `eng_reference` and `mlg_cn_reference` are auxiliary evidence and must never be copied here as if they were completed translations.

## Completion checkpoint

- completed: 469 / 469 file_ids;
- completed rows: 5,645 / 5,645;
- BRIEFING FILES: 363 blocks / 4,810 rows;
- BRIEFING MISSION: 106 blocks / 835 rows;
- remaining: 0;
- `NEXT_FILE_ID=NONE`.

The temporary browser-workflow queue has been removed from this formal mapping directory after completion. The 469 per-file mapping JSON files and the generated `TRANSLATION_STATE.md` are authoritative.

Japanese source text plus the complete block context remains authoritative; MLG_CN and ENG are auxiliary only, as defined by `TRANSLATION_GUIDE.md`.

## Next phase

Translation is complete. Do not create packet-level, `partNNN.json`, or replacement queue artifacts. The remaining work is:

1. merge the validated mappings into formal translation CSVs;
2. run build-time structural and capacity checks;
3. build the patch;
4. perform in-game verification;
5. update build/test documentation from those results.

Before entering the next phase, run `python tools/rebuild_translation_state.py --check` from `work/luna_translation_templates/`. It must report 710/710 file_ids, 26,686/26,686 rows, zero remaining/partial file_ids, and zero validation errors.
