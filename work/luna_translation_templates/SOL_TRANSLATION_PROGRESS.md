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
| Translation work safely persisted | **6219 / 21041 rows** |
| file_ids with complete persisted translation | **88 / 241** |
| YPK_GTT | **36 / 36 complete** |
| OHD | **1 / 1 complete** |
| LOOSE_OLANG | **14 / 14 complete** |
| STAGEDAT_OLANG | **37 / 46 complete** |
| SLOT_OLANG | **0 / 144** |

## Resource-class accounting
- YPK_GTT: **2080 rows / 36 file_ids**.
- OHD: **226 rows / 1 file_id**.
- LOOSE_OLANG: **1719 rows / 14 file_ids**.
- STAGEDAT_OLANG: **2194 rows / 37 file_ids**.

## Recent completed STAGEDAT
- `LANG_GAMEOVER.OLANG` — 124 rows; JPN dialogue and Japanese voice cast preserved over English-dub substitutions.
- `LANG_VOCALOID_KEYBOARD.OLANG` — 175 rows, three shards + manifest; pronunciation highlighting and phoneme data preserved, only UI/help/errors localized.
- `LANG_EXTRA.OLANG` — 141 rows; JPN action direction and controls/placeholders preserved.
- `LANG_GETTITLE_INSIGNIA_LIST.OLANG` — 217 rows, three shards + manifest; codename labels fixed, Rank A/B/C preserved, `$1/$2/$3m` thresholds retained.
- `LANG_ITEM_SHORT_NAME.OLANG` — **228 rows, three shards + manifest**; every JPN row is a fixed ASCII short name/internal ID/ammunition or equipment code/brand/costume code, so `cn_text` identity-preserves JPN. Auxiliary version substitutions such as `AXE→COLOGNE`, `LIOLAEUS→RATHALOS`, `BAD SMELL→STENCH`, `GIA-LIQ-*` replacements, `BOX SMOKE→SMOKE BOX`, and `M.RCV.→P.RCV.` are rejected.

## Important review / risk notes
- Auxiliary controls absent from JPN are always rejected.
- Japanese-version cast/staff credits are authoritative over English-dub substitutions.
- `LANG_SYSTEM`: JPN `576KB` overrides auxiliary `544KB`; `サイバーバル` remains unresolved/flagged.
- `LANG_MISSION_ENDTELOP`: shifted auxiliary mission-title mapping rejected; hunting double-angle titles remain parser-false-positive review items.
- `LANG_GETTITLE_INSIGNIA_LIST`: Mother Base / NAKED / mech-hunting / sync / CO-OP In terminology remains reviewable without blocking progress.

## Remaining STAGEDAT
`LANG_ITEM_TEXT.OLANG`, `LANG_MISSION_INFO.OLANG`, `LANG_MISSION_RESULT.OLANG`, `LANG_MYOUTER_DEVELOP.OLANG`, `LANG_MYOUTER_DEVELOP_METAL.OLANG`, `LANG_MYOUTER_STAFF.OLANG`, `LANG_MYOUTER_STAFF_COMMENT.OLANG`, `LANG_MYOUTER_TOP.OLANG`, `LANG_WEAPON_TEXT.OLANG`.

## Last safe checkpoint
- Safe translation total: **6219 rows / 88 complete file_ids**.
- STAGEDAT_OLANG: **37 / 46 complete**.
- Latest completed mapping: `sol_translation_mappings/STAGEDAT_OLANG/LANG_ITEM_SHORT_NAME.OLANG.manifest.json`.
- Latest manifest commit: `96d7c21d1c505dad9b8d4f8da972250db034f76d`.
- Resume next at: **STAGEDAT_OLANG/LANG_ITEM_TEXT.OLANG, unique_index 0**.
