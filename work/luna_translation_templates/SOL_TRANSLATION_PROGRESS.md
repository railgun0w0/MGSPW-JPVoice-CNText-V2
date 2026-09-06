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
| Translation work safely persisted | **7927 / 21041 rows** |
| file_ids with complete persisted translation | **92 / 241** |
| YPK_GTT | **36 / 36 complete** |
| OHD | **1 / 1 complete** |
| LOOSE_OLANG | **14 / 14 complete** |
| STAGEDAT_OLANG | **41 / 46 complete** |
| SLOT_OLANG | **0 / 144** |

## Resource-class accounting
- YPK_GTT: **2080 rows / 36 complete file_ids**.
- OHD: **226 rows / 1 complete file_id**.
- LOOSE_OLANG: **1719 rows / 14 complete file_ids**.
- STAGEDAT_OLANG: **3902 rows / 41 complete file_ids**.

## Recent completed STAGEDAT
- `LANG_ITEM_TEXT.OLANG` — 803 rows, 17 shards + manifest; JPN item descriptions/brands/controls/fixed short names override auxiliary dummy/version substitutions.
- `LANG_MYOUTER_STAFF.OLANG` — 146 rows, two shards + manifest, complete. Fixed ASCII UI codes are preserved; Japanese staff/team/tutorial text is localized.
- `LANG_MYOUTER_DEVELOP.OLANG` — 167 rows, two shards + manifest, complete.
- `LANG_MYOUTER_DEVELOP_METAL.OLANG` — **592 rows, seven shards + manifest, complete**. ZEKE configuration, parts, VOCALOID/AI settings and 400 AI memory-board identifiers follow JPN identity.

### `LANG_MYOUTER_DEVELOP_METAL` review/risk notes
- Fixed ZEKE UI labels/colors/timing/part/line/body codes remain exact where JPN uses fixed English identifiers; auxiliary renames such as `OPTIONAL PARTS`, `LEG PARTS`, `VIEWER CONTROLS`, scrap-code renames, etc. were rejected.
- JPN-only semantic details in ZEKE/part descriptions are preserved, including attack/defense/accuracy/evasion increases.
- `攻撃汎用` has no numeral in JPN and remains `通用攻击`; auxiliary-added `1` was rejected.
- Plain-text `Memory Stick™` / `PlayStation®Network` remain plain text; auxiliary icon/trademark controls absent from JPN were rejected.
- AI memory-board blocks 191-590 preserve exact JPN machine, numeric identity and material. Deterministic localization: `Ctl/Atk/Sns/Mbl → 控/攻/感/移`, `Pt/Au/Ag/Cu/Fe → 铂/金/银/铜/铁`.
- `Basilisk` remains terminology-review material; source trailing spaces and `(不要)` markers were retained where applicable.
- Complete manifest: `sol_translation_mappings/STAGEDAT_OLANG/LANG_MYOUTER_DEVELOP_METAL.OLANG.manifest.json`.
- Manifest commit: `09b2ef273c08f5d12afc71578ce1b9b0b050501c`.

### `LANG_MYOUTER_DEVELOP` review/risk notes
- Runtime controls/placeholders `<I=DEC>/<I=CAN>/<I=□>/<I=△>`, `<$1>`, `$1/$2`, `%s/%d` stay aligned with JPN.
- Generic JPN inventory-shortage / cannot-develop rows are not specialized into shifted auxiliary item/weapon/material variants.
- Source `(不要)` tutorial/development rows remain present and translated rather than silently dropped.
- `METAL GEAR ZEKE` and Mother Base identity follow JPN.
- `ROD` is preserved as a fixed category label pending terminology review; `制止力` and `集弹性能` remain terminology-review items.

## Important review / risk notes
- Auxiliary controls absent from JPN are always rejected.
- Japanese-version cast/staff credits are authoritative over English-dub substitutions.
- `LANG_SYSTEM`: JPN `576KB` overrides auxiliary `544KB`; `サイバーバル` remains unresolved/flagged.
- `LANG_MISSION_ENDTELOP`: shifted auxiliary mission-title mapping rejected; hunting double-angle titles remain parser-false-positive review items.
- `LANG_GETTITLE_INSIGNIA_LIST`: Mother Base / NAKED / mech-hunting / sync / CO-OP In terminology remains reviewable without blocking progress.
- `LANG_ITEM_TEXT`: AXE/brand/Japanese-version item identity, explicit JPN weapon variants, hidden row 229, fixed ASCII short labels/codes and document types remain authoritative over auxiliary substitutions.

## Remaining STAGEDAT
`LANG_MISSION_INFO.OLANG`, `LANG_MISSION_RESULT.OLANG`, `LANG_MYOUTER_STAFF_COMMENT.OLANG`, `LANG_MYOUTER_TOP.OLANG`, `LANG_WEAPON_TEXT.OLANG`.

## Last safe checkpoint
- Safe translation total: **7927 rows / 92 complete file_ids**.
- STAGEDAT_OLANG: **41 / 46 complete**.
- Latest completed artifact: `sol_translation_mappings/STAGEDAT_OLANG/LANG_MYOUTER_DEVELOP_METAL.OLANG.manifest.json`.
- Latest manifest commit: `09b2ef273c08f5d12afc71578ce1b9b0b050501c`.
- Resume next at: **STAGEDAT_OLANG/LANG_MYOUTER_STAFF_COMMENT.OLANG, unique_index 0**.
