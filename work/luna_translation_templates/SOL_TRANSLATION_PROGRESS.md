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
| Translation work safely persisted | **6769 / 21041 rows** |
| file_ids with complete persisted translation | **88 / 241** |
| YPK_GTT | **36 / 36 complete** |
| OHD | **1 / 1 complete** |
| LOOSE_OLANG | **14 / 14 complete** |
| STAGEDAT_OLANG | **37 / 46 complete + `LANG_ITEM_TEXT` 550 / 803 partial** |
| SLOT_OLANG | **0 / 144** |

## Resource-class accounting
- YPK_GTT: **2080 rows / 36 complete file_ids**.
- OHD: **226 rows / 1 complete file_id**.
- LOOSE_OLANG: **1719 rows / 14 complete file_ids**.
- STAGEDAT_OLANG: **2194 rows / 37 complete file_ids + 550 safely persisted rows in active `LANG_ITEM_TEXT.OLANG`**.

## Recent completed STAGEDAT
- `LANG_GAMEOVER.OLANG` — 124 rows; JPN dialogue and Japanese voice cast preserved over English-dub substitutions.
- `LANG_VOCALOID_KEYBOARD.OLANG` — 175 rows, four shards + manifest; pronunciation highlighting and phoneme data preserved, only UI/help/errors localized.
- `LANG_EXTRA.OLANG` — 141 rows; JPN action direction and controls/placeholders preserved.
- `LANG_GETTITLE_INSIGNIA_LIST.OLANG` — 217 rows, three shards + manifest; codename labels fixed, Rank A/B/C preserved, `$1/$2/$3m` thresholds retained.
- `LANG_ITEM_SHORT_NAME.OLANG` — 228 rows, three shards + manifest; fixed ASCII short names/internal IDs/ammunition or equipment codes/brand/costume codes identity-preserve JPN. Auxiliary version substitutions such as `AXE→COLOGNE`, `LIOLAEUS→RATHALOS`, `BAD SMELL→STENCH`, `GIA-LIQ-*` replacements, `BOX SMOKE→SMOKE BOX`, and `M.RCV.→P.RCV.` are rejected.

## Active large-file checkpoint — `LANG_ITEM_TEXT.OLANG`
- Template coverage: **803 logical rows, unique_index 0–802**.
- Safely persisted: **550 / 803 rows, unique_index 0–549 contiguous**.
- Shards present: `part01` 0–49, `part02` 50–99, `part03` 100–149, `part04` 150–199, `part05` 200–249, `part06` 250–299, `part07` 300–349, `part08` 350–399, `part09` 400–449, `part10` 450–499, `part11` 500–549.
- Latest shard commit: `010c2b0538caaeee5a4324cdb983ec0fdfcaca8f`.
- Resume next at: **unique_index 550**.

### `LANG_ITEM_TEXT` review/risk notes
- JPN remains authoritative over auxiliary dummy/version substitutions. AXE, Mountain Dew, Pepsi NEX, Doritos, FOX and Japanese-version item identities are preserved.
- Project terminology keeps `Naked` rather than auxiliary `赤身`; fixed internal `IT_*` identifiers remain unchanged.
- Explicit weapon variants are translated from JPN semantics rather than auxiliary abbreviations: LIFE/精神恢复弹, 烟雾榴弹, 榴弹, 霰弹, 激光 combinations, etc.
- `unique_index 229` is the JPN hidden message `看到这个，就说明你做了不该做的事……`; shifted smoke-box auxiliary text was rejected.
- Gear REX material rows retain JPN contraction semantics; Monster Hunter material grade terms such as `重牙` / `刚翼` are preserved.
- Document-type distinctions such as `取材メモ`, `台割`, `栽培説明書` are retained instead of flattening everything to generic design specs.
- Runtime controls are introduced only when present in JPN; known controls in completed shards include `<I=USE>`, `<I=ACT>`, `<I=AIM>`, `<I=ATK>`.
- Stylized source titles such as `『電磁ネット。』` / `『電磁波照射ガン。』` remain explicitly flagged for semantic/layout review rather than silently normalized away.

## Important review / risk notes
- Auxiliary controls absent from JPN are always rejected.
- Japanese-version cast/staff credits are authoritative over English-dub substitutions.
- `LANG_SYSTEM`: JPN `576KB` overrides auxiliary `544KB`; `サイバーバル` remains unresolved/flagged.
- `LANG_MISSION_ENDTELOP`: shifted auxiliary mission-title mapping rejected; hunting double-angle titles remain parser-false-positive review items.
- `LANG_GETTITLE_INSIGNIA_LIST`: Mother Base / NAKED / mech-hunting / sync / CO-OP In terminology remains reviewable without blocking progress.

## Remaining STAGEDAT
`LANG_ITEM_TEXT.OLANG` (active 550/803), `LANG_MISSION_INFO.OLANG`, `LANG_MISSION_RESULT.OLANG`, `LANG_MYOUTER_DEVELOP.OLANG`, `LANG_MYOUTER_DEVELOP_METAL.OLANG`, `LANG_MYOUTER_STAFF.OLANG`, `LANG_MYOUTER_STAFF_COMMENT.OLANG`, `LANG_MYOUTER_TOP.OLANG`, `LANG_WEAPON_TEXT.OLANG`.

## Last safe checkpoint
- Safe translation total: **6769 rows / 88 complete file_ids**, including **550 partial rows** of `LANG_ITEM_TEXT.OLANG`.
- STAGEDAT_OLANG: **37 / 46 complete**, plus active `LANG_ITEM_TEXT.OLANG` **550 / 803**.
- Latest safely persisted artifact: `sol_translation_mappings/STAGEDAT_OLANG/LANG_ITEM_TEXT.OLANG.part11.json`.
- Latest shard commit: `010c2b0538caaeee5a4324cdb983ec0fdfcaca8f`.
- Resume next at: **STAGEDAT_OLANG/LANG_ITEM_TEXT.OLANG, unique_index 550**.
