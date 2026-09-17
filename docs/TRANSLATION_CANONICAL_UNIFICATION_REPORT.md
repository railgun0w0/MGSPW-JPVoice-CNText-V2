# Canonical Translation Unification Report

Date: 2026-09-17  
Branch: `sol-translation`

This report records the post-audit migration. The original `TRANSLATION_SOURCE_OF_TRUTH_AUDIT.md` remains the pre-migration baseline; `TRANSLATION_SOURCE_OF_TRUTH_MATRIX.csv` has been updated for the 21 migrated YPK file IDs.

## Result

- In the clean migration snapshot, all 710 file IDs and 26,686 translation rows resolve to mapping JSON through the state loader.
- The 21 JSON-less `YPK_GTT` files (491 unique rows) were generated mechanically from the loader's audited `template_csv` representation. The seven recoverable legacy column-shift rows were preserved exactly in canonical form.
- No builder was edited. No JPN text, Chinese text, control token, or object identity changed.
- `tools/Compile-ProductionTranslations.py --write` completed with 241 files / 21,041 unique rows, 91,609 manifest rows, 0 hard overflow, and 7 legacy-shift normalizations. A subsequent `--check` completed successfully without writing.

## JSON / CSV verification

The 21 generated JSON mappings match their former template-canonical rows at every `unique_index` (491/491 rows). The post-write comparisons found:

- production CSV Chinese text changes: **0**;
- manifest JPN/Chinese text or identity changes: **0**;
- manifest metadata-only changes: 6,740 rows (`mapping_source` on 497 physical YPK objects and `mapping_commit` on 6,740 rows), expected from canonical-source and checkpoint rematerialization;
- the compiler's deterministic writer would normalize one pre-existing mixed-EOL line (`translations/loose_olang/007E2F18.csv`); the working-tree CSV was left byte-for-byte untouched, and `--check` treats newline style as nonsemantic.

## Remaining noncanonical artifacts

The 21 translated YPK template CSVs remain on disk for structural traceability and regression recovery because existing translations were not deleted or rewritten. They are explicitly NONCANONICAL; JSON wins through the state loader and compiler. The validator reports these duplicate row-equivalent representations. The two pre-existing conflicting complete representations (`SLOT_OLANG/5D06A8D5` and `STAGEDAT_OLANG/LANG_VOCALOID_KEYBOARD.OLANG`) continue to use their explicit manifest as canonical and report the losing files as legacy/reference artifacts.

## BRIEFING

BRIEFING remains on its dedicated JSON → `translations/briefing/*.csv` → `Build-BriefingDat.py` path. No BRIEFING mapping or production CSV was changed by this migration. The local Node check could not start because the environment does not provide `@oai/artifact-tool`; this is an environment dependency issue, not a translation-state validation error.

## Recommended commit split

1. Add the 21 canonical YPK mapping JSON files.
2. Commit the compiler `--check`, state-validator wording, documentation, and matrix/report updates.
3. Commit regenerated old-five production materialization only after reviewing the metadata-only manifest diff.
