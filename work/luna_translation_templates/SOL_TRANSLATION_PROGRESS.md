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
| Translation work safely persisted | **7022 / 21041 rows** |
| file_ids with complete persisted translation | **89 / 241** |
| YPK_GTT | **36 / 36 complete** |
| OHD | **1 / 1 complete** |
| LOOSE_OLANG | **14 / 14 complete** |
| STAGEDAT_OLANG | **38 / 46 complete** |
| SLOT_OLANG | **0 / 144** |

## Resource-class accounting
- YPK_GTT: **2080 rows / 36 complete file_ids**.
- OHD: **226 rows / 1 complete file_id**.
- LOOSE_OLANG: **1719 rows / 14 complete file_ids**.
- STAGEDAT_OLANG: **2997 rows / 38 complete file_ids**.

## Recent completed STAGEDAT
- `LANG_GAMEOVER.OLANG` — 124 rows; JPN dialogue and Japanese voice cast preserved over English-dub substitutions.
- `LANG_VOCALOID_KEYBOARD.OLANG` — 175 rows, four shards + manifest; pronunciation highlighting and phoneme data preserved, only UI/help/errors localized.
- `LANG_EXTRA.OLANG` — 141 rows; JPN action direction and controls/placeholders preserved.
- `LANG_GETTITLE_INSIGNIA_LIST.OLANG` — 217 rows, three shards + manifest; codename labels fixed, Rank A/B/C preserved, `$1/$2/$3m` thresholds retained.
- `LANG_ITEM_SHORT_NAME.OLANG` — 228 rows, three shards + manifest; fixed ASCII short names/internal IDs/ammunition or equipment codes/brand/costume codes identity-preserve JPN. Auxiliary version substitutions such as `AXE→COLOGNE`, `LIOLAEUS→RATHALOS`, `BAD SMELL→STENCH`, `GIA-LIQ-*` replacements, `BOX SMOKE→SMOKE BOX`, and `M.RCV.→P.RCV.` are rejected.
- `LANG_ITEM_TEXT.OLANG` — **803 rows, 17 shards + manifest, complete**. JPN item descriptions, Japanese-version brand/collab identities, controls and fixed short names are authoritative over auxiliary version/dummy substitutions.

### `LANG_ITEM_TEXT` review/risk notes
- AXE, Mountain Dew, Pepsi NEX, Doritos, FOX and Japanese-version item identities are preserved over auxiliary dummy/version substitutions.
- Project terminology keeps `Naked` rather than auxiliary `赤身`; fixed internal `IT_*` identifiers remain unchanged.
- Explicit weapon variants are translated from JPN semantics rather than auxiliary abbreviations: LIFE/精神恢复弹, 烟雾榴弹, 榴弹, 霰弹, 激光 combinations, etc.
- `unique_index 229` preserves the JPN hidden message `看到这个，就说明你做了不该做的事……`; shifted smoke-box auxiliary text was rejected.
- Gear REX material rows retain JPN contraction semantics; Monster Hunter material grade terms such as `重牙` / `刚翼` are preserved.
- Document-type distinctions such as `取材メモ`, `台割`, `栽培説明書` are retained instead of flattening everything to generic design specs.
- Runtime controls are introduced only when present in JPN; known controls include `<I=USE>`, `<I=ACT>`, `<I=AIM>`, `<I=ATK>`.
- From unique_index 636 onward, fixed ASCII short labels/codes identity-preserve JPN. Auxiliary substitutions such as `LIOLAEUS→RATHALOS`, `BAD SMELL→STENCH`, `GIA-LIQ-*` replacements, `BOX SMOKE→SMOKE BOX`, and `M.RCV.→P.RCV.` are rejected.
- Complete manifest: `sol_translation_mappings/STAGEDAT_OLANG/LANG_ITEM_TEXT.OLANG.manifest.json`.
- Manifest commit: `6ac775ea651e3404b1537bc75ed399eb8d1a8ec5`.

## Important review / risk notes
- Auxiliary controls absent from JPN are always rejected.
- Japanese-version cast/staff credits are authoritative over English-dub substitutions.
- `LANG_SYSTEM`: JPN `576KB` overrides auxiliary `544KB`; `サイバーバル` remains unresolved/flagged.
- `LANG_MISSION_ENDTELOP`: shifted auxiliary mission-title mapping rejected; hunting double-angle titles remain parser-false-positive review items.
- `LANG_GETTITLE_INSIGNIA_LIST`: Mother Base / NAKED / mech-hunting / sync / CO-OP In terminology remains reviewable without blocking progress.

## Remaining STAGEDAT
`LANG_MISSION_INFO.OLANG`, `LANG_MISSION_RESULT.OLANG`, `LANG_MYOUTER_DEVELOP.OLANG`, `LANG_MYOUTER_DEVELOP_METAL.OLANG`, `LANG_MYOUTER_STAFF.OLANG`, `LANG_MYOUTER_STAFF_COMMENT.OLANG`, `LANG_MYOUTER_TOP.OLANG`, `LANG_WEAPON_TEXT.OLANG`.

## Last safe checkpoint
- Safe translation total: **7022 rows / 89 complete file_ids**.
- STAGEDAT_OLANG: **38 / 46 complete**.
- Latest completed artifact: `sol_translation_mappings/STAGEDAT_OLANG/LANG_ITEM_TEXT.OLANG.manifest.json`.
- Latest manifest commit: `6ac775ea651e3404b1537bc75ed399eb8d1a8ec5`.
- Resume next at: **one of the remaining STAGEDAT files; prefer smallest complete file_id first**.
