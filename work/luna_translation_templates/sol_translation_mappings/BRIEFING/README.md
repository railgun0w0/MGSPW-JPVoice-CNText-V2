# BRIEFING translation mappings

This physical `BRIEFING` directory contains validated, per-file translation mappings for the frozen JPN-only corpus. The internal logical resource class remains `BRIEFING_NBE` for schema compatibility.

One validated mapping is retained per `BRIEFING/` template. Mapping rows bind the template's `file_id` and `unique_index`, and contain translated `cn_text`; `eng_reference` and `mlg_cn_reference` are auxiliary evidence and must never be treated as completed translations.

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

Translation and the formal production CSV merge are complete. Do not create packet-level, `partNNN.json`, or replacement queue artifacts. `translations/briefing/` now contains 469 production CSVs / 5,645 rows and is the direct input for the future dedicated oEbN builder. The remaining work is:

1. rerun `node tools/Compile-BriefingProductionTranslations.mjs --check` from the repository root;
2. implement a dedicated clean-JPN BRIEFING oEbN builder using physical `file_id + unique_index + stream/block/text` identity;
3. run rebuilt-DAT parser, text, capacity and non-target byte-difference checks;
4. integrate the validated result into the unified test package;
5. perform separate FILES/MISSION in-game verification and update build/test status.

The current generic `Compile-ProductionTranslations.py` / `compiled_translation_manifest.csv` path does not include BRIEFING. Do not deduplicate these physical rows by Japanese text or pass them to an OLANG/GTT builder. See `docs/BRIEFING_BUILD_HANDOFF.md` for the authoritative handoff.

Before entering the next phase, run `python tools/rebuild_translation_state.py --check` from `work/luna_translation_templates/`. It must report 710/710 file_ids, 26,686/26,686 rows, zero remaining/partial file_ids, and zero validation errors.
