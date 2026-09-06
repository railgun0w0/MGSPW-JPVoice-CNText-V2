# Sol Translation Progress

Branch: `sol-translation`

Purpose: durable checkpoint for translation work under `work/luna_translation_templates/` so work can resume safely across chat turns.

## Rules

- JPN is the sole semantic and structural authority.
- MLG_CN / ENG are auxiliary evidence only; never force positional or semantic alignment when they conflict with JPN.
- Preserve markup, controls, runtime placeholders, indices/references, ordering, timing and resource identity.
- Translation work stays under `work/luna_translation_templates/` and `work/luna_translation_templates/sol_translation_mappings/`.
- Do not modify formal `translations/`, compiled manifest, DAT/KEY, or run a production build from this branch checkpoint.
- Use pending-review semantics; never mark a Sol translation `APPROVED`.
- Large files may be persisted as contiguous shards plus a manifest.
- For CSVs with embedded newlines, anchor work to logical `unique_index`, never physical line number.

## Current totals

| Metric | Progress |
|---|---:|
| Total template file_ids | 241 |
| Total template rows | 21041 |
| Translation work safely persisted | **5991 / 21041 rows** |
| file_ids with complete persisted translation | **87 / 241** |
| YPK_GTT | **36 / 36 complete** |
| OHD | **1 / 1 complete** |
| LOOSE_OLANG | **14 / 14 complete** |
| STAGEDAT_OLANG | **36 / 46 complete** |
| SLOT_OLANG | **0 / 144** |

## Resource-class accounting

- YPK_GTT: **2080 rows / 36 file_ids complete**.
- OHD: **226 rows / 1 file_id complete**.
- LOOSE_OLANG: **1719 rows / 14 file_ids complete**.
- STAGEDAT_OLANG: **1966 rows / 36 file_ids complete**.

## STAGEDAT completed

`LANG_DEMOSKIPTELOP.OLANG` (1), `LANG_EMERGENCYTELOP.OLANG` (5), `LANG_COMMUNICATIONSTELOP.OLANG` (5), `LANG_BRIEFING.OLANG` (25), `LANG_CHARAEDIT.OLANG` (46), `LANG_DEMOTELOP4.OLANG` (47), `LANG_DEMOTELOP.OLANG` (34), `LANG_TITLE_NAMEENTRY.OLANG` (4), `LANG_WALKMAN.OLANG` (9), `LANG_MAP_FLOOR.OLANG` (9), `LANG_SPOOKY_COMMON.OLANG` (7), `LANG_PSP_KEYBOARD.OLANG` (6), `LANG_SYNC.OLANG` (19), `LANG_TITLEMENU.OLANG` (17), `LANG_DEMOTELOP2.OLANG` (76), `LANG_V_THEATER020.OLANG` (16), `LANG_V_THEATER010.OLANG` (24), `LANG_MYOUTER_UTIL.OLANG` (33), `LANG_TITLE_OPTIONS.OLANG` (27), `LANG_HTTP_ERROR.OLANG` (30), `LANG_KEYHELP.OLANG` (23), `LANG_PW_COMMON.OLANG` (35), `LANG_MYOUTER_STAFF_SOLTYPE.OLANG` (63), `LANG_PAUSEMENU.OLANG` (75), `LANG_VOCALOID.OLANG` (64), `LANG_ONLINE_ERROR.OLANG` (56), `LANG_DATAINSTALL.OLANG` (47), `LANG_WEAPON_SHORT_NAME.OLANG` (136), `LANG_STAGETELOP.OLANG` (107), `LANG_MYOUTER_STAFF_SKILL.OLANG` (74), `LANG_MISSION_ENDTELOP.OLANG` (107), `LANG_SYSTEM.OLANG` (82), `LANG_GAMEOVER.OLANG` (124), `LANG_VOCALOID_KEYBOARD.OLANG` (175), `LANG_EXTRA.OLANG` (141), `LANG_GETTITLE_INSIGNIA_LIST.OLANG` (217).

## Important review / risk notes

- JPN always wins over shifted, combined, over-expanded, or version-specific auxiliary text.
- Auxiliary-inserted controls absent from JPN are rejected; JPN literal text is not converted into icon/runtime controls just because an auxiliary bank did so.
- `LANG_DEMOTELOP2/4` and `LANG_GAMEOVER`: Japanese-version voice cast is authoritative; English-dub actor substitutions are rejected.
- `LANG_MISSION_ENDTELOP`: auxiliary mission-title stream is systematically shifted; titles were rebuilt from JPN. Double-angle hunting titles remain parser-false-positive review items.
- `LANG_SYSTEM`: JPN `576KB` overrides auxiliary `544KB`; unresolved source term `サイバーバル` remains flagged rather than guessed.
- `LANG_VOCALOID_KEYBOARD`: **175 rows complete as three contiguous shards plus manifest**. Pronunciation example highlighting preserves `<C=FF4040>...<C=R>`; raw phoneme symbols and bracketed phoneme examples remain exact; only UI/help/errors are localized.
- `LANG_EXTRA`: 141 rows complete; JPN action direction and controls/placeholders override auxiliary substitutions.
- `LANG_GETTITLE_INSIGNIA_LIST`: **217 rows complete as three shards plus manifest**. Rows 0-23 preserve fixed English codename labels; rows 24-47 preserve distinct range/cooperation/lethal-vs-nonlethal criteria; rows 48-152 preserve JPN Rank A/B/C even where auxiliary CN omitted it; rows 153-216 preserve threshold wording and `$1/$2/$3m` placeholder order. Mother Base / NAKED / mech-hunting / sync / CO-OP In terminology remains reviewable without blocking progress.

## Remaining STAGEDAT

`LANG_ITEM_SHORT_NAME.OLANG`, `LANG_ITEM_TEXT.OLANG`, `LANG_MISSION_INFO.OLANG`, `LANG_MISSION_RESULT.OLANG`, `LANG_MYOUTER_DEVELOP.OLANG`, `LANG_MYOUTER_DEVELOP_METAL.OLANG`, `LANG_MYOUTER_STAFF.OLANG`, `LANG_MYOUTER_STAFF_COMMENT.OLANG`, `LANG_MYOUTER_TOP.OLANG`, `LANG_WEAPON_TEXT.OLANG`.

## Last safe checkpoint

- Safe translation total: **5991 rows / 87 complete file_ids**.
- Resource-class checkpoint: **STAGEDAT_OLANG 36 / 46 complete**.
- Latest completed STAGEDAT mapping: `sol_translation_mappings/STAGEDAT_OLANG/LANG_GETTITLE_INSIGNIA_LIST.OLANG.manifest.json`.
- Latest STAGEDAT manifest commit: `c9c05d472a6f7989adf9ece80da53dd2f095305e`.
- Resume next at: **STAGEDAT_OLANG/LANG_ITEM_SHORT_NAME.OLANG, unique_index 0**.
