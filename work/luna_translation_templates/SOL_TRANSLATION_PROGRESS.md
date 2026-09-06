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

## Current totals

| Metric | Progress |
|---|---:|
| Total template file_ids | 241 |
| Total template rows | 21041 |
| Translation work safely persisted | **7168 / 21041 rows** |
| file_ids with complete persisted translation | **90 / 241** |
| YPK_GTT | **36 / 36 complete** |
| OHD | **1 / 1 complete** |
| LOOSE_OLANG | **14 / 14 complete** |
| STAGEDAT_OLANG | **39 / 46 complete** |
| SLOT_OLANG | **0 / 144** |

## Resource-class accounting
- YPK_GTT: **2080 rows / 36 complete file_ids**.
- OHD: **226 rows / 1 complete file_id**.
- LOOSE_OLANG: **1719 rows / 14 complete file_ids**.
- STAGEDAT_OLANG: **3143 rows / 39 complete file_ids**.

## Recent completed STAGEDAT
- `LANG_ITEM_TEXT.OLANG` — 803 rows, 17 shards + manifest; JPN item descriptions/brands/controls/fixed short names override auxiliary dummy/version substitutions.
- `LANG_MYOUTER_STAFF.OLANG` — **146 rows, two shards + manifest, complete**. Fixed ASCII UI codes are preserved; Japanese staff/team/tutorial text is localized. JPN Waiting Room composition, Sickbay forced discharge, roster assignment, tranquilizer-gun development and team functions override auxiliary paraphrases/omissions.

### `LANG_MYOUTER_STAFF` review/risk notes
- `<SKILL>`, `<BAD STATE>`, `<PARAMETER>`, `%d`, `$1` and all `<I=...>` controls preserve JPN identity/order/count.
- `医疗班与医务室` preserves the JPN tutorial scope; auxiliary Medical Team-only truncation is rejected.
- Mother Base composition preserves JPN `战斗班 / 研发班 / 等待室`; auxiliary Medical Team substitution is rejected.
- `军人` remains generic JPN military-person wording instead of auxiliary `普通士兵` expansion.
- Row 74 `センス` is translated provisionally as `感知能力` and remains terminology-review material.
- Complete manifest: `sol_translation_mappings/STAGEDAT_OLANG/LANG_MYOUTER_STAFF.OLANG.manifest.json`.
- Manifest commit: `8ad7ce9ccb0655316f83f5956c158ab4856e240b`.

## Important review / risk notes
- Auxiliary controls absent from JPN are always rejected.
- Japanese-version cast/staff credits are authoritative over English-dub substitutions.
- `LANG_SYSTEM`: JPN `576KB` overrides auxiliary `544KB`; `サイバーバル` remains unresolved/flagged.
- `LANG_MISSION_ENDTELOP`: shifted auxiliary mission-title mapping rejected; hunting double-angle titles remain parser-false-positive review items.
- `LANG_GETTITLE_INSIGNIA_LIST`: Mother Base / NAKED / mech-hunting / sync / CO-OP In terminology remains reviewable without blocking progress.
- `LANG_ITEM_TEXT`: AXE/brand/Japanese-version item identity, explicit JPN weapon variants, hidden row 229, fixed ASCII short labels/codes and document types remain authoritative over auxiliary substitutions.

## Remaining STAGEDAT
`LANG_MISSION_INFO.OLANG`, `LANG_MISSION_RESULT.OLANG`, `LANG_MYOUTER_DEVELOP.OLANG`, `LANG_MYOUTER_DEVELOP_METAL.OLANG`, `LANG_MYOUTER_STAFF_COMMENT.OLANG`, `LANG_MYOUTER_TOP.OLANG`, `LANG_WEAPON_TEXT.OLANG`.

## Last safe checkpoint
- Safe translation total: **7168 rows / 90 complete file_ids**.
- STAGEDAT_OLANG: **39 / 46 complete**.
- Latest completed artifact: `sol_translation_mappings/STAGEDAT_OLANG/LANG_MYOUTER_STAFF.OLANG.manifest.json`.
- Latest manifest commit: `8ad7ce9ccb0655316f83f5956c158ab4856e240b`.
- Resume next at: **STAGEDAT_OLANG/LANG_MYOUTER_DEVELOP.OLANG, unique_index 0**.
