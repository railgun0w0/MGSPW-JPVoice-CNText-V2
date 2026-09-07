# Sol Translation Progress

Branch: `sol-translation`

Purpose: durable checkpoint for translation work under `work/luna_translation_templates/` so work can resume safely across chat turns.

## Rules
- JPN is the sole semantic and structural authority; MLG_CN / ENG are auxiliary only.
- Preserve markup, controls, placeholders, indices/references, ordering, timing and resource identity.
- Work only under `work/luna_translation_templates/` / `sol_translation_mappings/`; do not touch formal build inputs or DAT/KEY.
- Use pending-review semantics; never mark Sol output `APPROVED`.
- Large files may use contiguous shards + manifest.
- For multiline CSVs, use logical `unique_index`, never physical line number.
- If a mapping/shard already exists, fetch and verify it rather than overwriting concurrent progress.

## Current totals

| Metric | Progress |
|---|---:|
| Total template file_ids | 241 |
| Total template rows | 21041 |
| Translation work safely persisted | **8283 / 21041 rows** |
| file_ids with complete persisted translation | **93 / 241** |
| YPK_GTT | **36 / 36 complete** |
| OHD | **1 / 1 complete** |
| LOOSE_OLANG | **14 / 14 complete** |
| STAGEDAT_OLANG | **42 / 46 complete** |
| SLOT_OLANG | **0 / 144** |

## Resource-class accounting
- YPK_GTT: **2080 rows / 36 complete file_ids**.
- OHD: **226 rows / 1 complete file_id**.
- LOOSE_OLANG: **1719 rows / 14 complete file_ids**.
- STAGEDAT_OLANG: **4258 rows / 42 complete file_ids**.

## Recent completed STAGEDAT
- `LANG_ITEM_TEXT.OLANG` — 803 rows, 17 shards + manifest.
- `LANG_MYOUTER_STAFF.OLANG` — 146 rows, two shards + manifest.
- `LANG_MYOUTER_DEVELOP.OLANG` — 167 rows, two shards + manifest.
- `LANG_MYOUTER_DEVELOP_METAL.OLANG` — 592 rows, seven shards + manifest.
- `LANG_VOCALOID_KEYBOARD.OLANG` — 175 rows, three shards + manifest. English pronunciation examples and VOCALOID phoneme data are preserved; only actual keyboard/help/error UI is localized.
- `LANG_MYOUTER_STAFF_COMMENT.OLANG` — **356 rows, eight shards + manifest, complete**. Manifest: `sol_translation_mappings/STAGEDAT_OLANG/LANG_MYOUTER_STAFF_COMMENT.OLANG.manifest.json`; manifest commit `e294ee5247aa314057782e99dae9fcf59d73e81f`.

## Important review / risk notes
- Auxiliary controls absent from JPN are always rejected.
- Japanese-version cast/staff credits are authoritative over English-dub substitutions.
- `LANG_SYSTEM`: JPN `576KB` overrides auxiliary `544KB`; `サイバーバル` remains unresolved/flagged.
- `LANG_MISSION_ENDTELOP`: shifted auxiliary mission-title mapping rejected; hunting double-angle titles remain parser-false-positive review items.
- `LANG_GETTITLE_INSIGNIA_LIST`: Mother Base / NAKED / mech-hunting / sync / CO-OP In terminology remains reviewable without blocking progress.
- `LANG_ITEM_TEXT`: AXE/brand/Japanese-version item identity, explicit JPN weapon variants, hidden row 229, fixed ASCII short labels/codes and document types remain authoritative over auxiliary substitutions.
- `LANG_MYOUTER_DEVELOP_METAL`: ZEKE configuration, parts, VOCALOID/AI settings and 400 AI memory-board identifiers follow JPN identity; fixed English codes remain fixed. `Basilisk` remains terminology-review material.
- `LANG_MYOUTER_DEVELOP`: runtime controls/placeholders remain aligned with JPN; source `(不要)` rows remain; generic shortage/cannot-develop rows are not specialized from shifted auxiliary variants.
- `LANG_VOCALOID_KEYBOARD`: rows 5-57 are English pronunciation examples with highlighted spans and remain English; rows 58-108 and 124-174 are phoneme symbols/examples and remain exact. Square-bracket phoneme syntax is data, not runtime control markup.
- `LANG_MYOUTER_STAFF_COMMENT`: all 356 rows complete. Auxiliary omissions/expansions were corrected against JPN. JPN `祖母` overrides auxiliary `mother`; `無力化` stays distinct from killing; `Hold Up`, `Mother Base`, `ENTRY GATE`, `CO-OPS COMM.`, `BRIEFING FILES`, weapon labels and UI terms retain source identity. Source `(不要)` temporary voice-actor placeholders at rows 330 and 335 are preserved. Rows 331-342 are named-character dialogue and rows 343-346 are character biographies, reviewed separately from generic soldier chatter. Rows 347-355 preserve established Latin character names.

## Remaining STAGEDAT
`LANG_MISSION_INFO.OLANG`, `LANG_MISSION_RESULT.OLANG`, `LANG_MYOUTER_TOP.OLANG`, `LANG_WEAPON_TEXT.OLANG`.

## Last safe checkpoint
- Safe translation total: **8283 rows / 93 complete file_ids**.
- STAGEDAT_OLANG: **42 / 46 complete**.
- Latest completed artifact: `sol_translation_mappings/STAGEDAT_OLANG/LANG_MYOUTER_STAFF_COMMENT.OLANG.manifest.json`.
- Latest manifest commit: `e294ee5247aa314057782e99dae9fcf59d73e81f`.
- Resume next: choose the smallest remaining STAGEDAT file and persist complete mappings/shards before updating this tracker again.
