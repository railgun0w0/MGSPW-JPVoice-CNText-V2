# Sol Translation Progress

Branch: `sol-translation`

Purpose: durable checkpoint for translation work under `work/luna_translation_templates/` so work can resume safely across chat turns.

## Rules

- JPN is the sole semantic and structural authority.
- MLG_CN / ENG are auxiliary evidence only; never force positional or semantic alignment when they conflict with JPN.
- Preserve markup, controls, runtime placeholders, indices/references, ordering, timing and resource identity.
- Translation work stays under `work/luna_translation_templates/` and `work/luna_translation_templates/sol_translation_mappings/`.
- Do not modify formal `translations/`, compiled manifest, DAT/KEY, or run a production build from this branch checkpoint.
- Use pending-review semantics; never mark a translation `APPROVED` merely because Sol produced it.
- Large files are persisted as complete per-file JSON mappings, sharded when needed, before any mechanical CSV merge.
- For CSVs with embedded newlines, anchor work to logical `unique_index`, never physical line number.

## Current totals

| Metric | Progress |
|---|---:|
| Total template file_ids | 241 |
| Total template rows | 21041 |
| Translation work safely persisted | **4408 / 21041 rows** |
| file_ids with complete persisted translation | **69 / 241** |
| YPK_GTT | **36 / 36 complete** |
| OHD | **1 / 1 complete** |
| LOOSE_OLANG | **14 / 14 complete** |
| STAGEDAT_OLANG | **18 / 46 complete** |
| SLOT_OLANG | **0 / 144** |

## Resource-class accounting

- YPK_GTT: **2080 rows / 36 file_ids complete**.
- OHD: **226 rows / 1 file_id complete**.
- LOOSE_OLANG: **1719 rows / 14 file_ids complete**.
- STAGEDAT_OLANG: **383 rows / 18 file_ids complete**.

### STAGEDAT completed

`LANG_DEMOSKIPTELOP.OLANG` (1), `LANG_EMERGENCYTELOP.OLANG` (5), `LANG_COMMUNICATIONSTELOP.OLANG` (5), `LANG_BRIEFING.OLANG` (25), `LANG_CHARAEDIT.OLANG` (46), `LANG_DEMOTELOP4.OLANG` (47), `LANG_DEMOTELOP.OLANG` (34), `LANG_TITLE_NAMEENTRY.OLANG` (4), `LANG_WALKMAN.OLANG` (9), `LANG_MAP_FLOOR.OLANG` (9), `LANG_SPOOKY_COMMON.OLANG` (7), `LANG_PSP_KEYBOARD.OLANG` (6), `LANG_SYNC.OLANG` (19), `LANG_TITLEMENU.OLANG` (17), `LANG_DEMOTELOP2.OLANG` (76), `LANG_V_THEATER020.OLANG` (16), `LANG_V_THEATER010.OLANG` (24), `LANG_MYOUTER_UTIL.OLANG` (33).

## Important review / risk notes

- JPN always wins over shifted, combined, over-expanded, or version-specific auxiliary text.
- Auxiliary-inserted controls absent from JPN were rejected in CHAR_EDIT, WALKMAN and TITLEMENU.
- `LANG_DEMOTELOP4`: English-dub cast substitution rejected; JPN Japanese voice cast preserved.
- `LANG_DEMOTELOP`: late shifted auxiliary around `恋の抑止力` / `HEAVENS DIVIDE` rejected; `ボスケ・デル・アルバ` → `黎明森林` remains terminology-review material.
- `LANG_DEMOTELOP2`: Japanese-version cast/staff are authoritative. English-dub cast substitutions in MLG_CN / ENG were rejected. Credit role terminology follows `LANG_DEMOTELOP4`; trailing date/location test-style rows were translated from JPN without importing auxiliary `(不要)` prefixes.
- `LANG_V_THEATER010` and `LANG_V_THEATER020`: ruby/control structure preserved exactly; shifted auxiliary dialogue was rejected where it disagreed with the JPN sequence.
- `LANG_MYOUTER_UTIL`: `<I=CAN>/<I=DEC>` controls and space-only placeholders preserved; source `(不要)` markers retained; auxiliary-untranslated JPN descriptions localized directly from JPN.
- `LANG_TITLE_NAMEENTRY`: explicit allowed-symbol list from JPN preserved.
- `LANG_MAP_FLOOR`: JPN `B4F/B3F/B2F/B1F` preserved; auxiliary dropped `F`.
- `LANG_SYNC`: unclear abbreviations `LV/S/B/ZZZ/STN` preserved rather than guessed.
- `LANG_TITLEMENU`: `NIHON-GO` follows JPN as `日语`; auxiliary `ENGLISH` is treated as version substitution. Memory Stick™ rows remain plain text with no invented icon controls.

## Last safe checkpoint

- Safe translation total: **4408 rows / 69 complete file_ids**.
- Resource-class checkpoint: **STAGEDAT_OLANG 18 / 46 complete**.
- Latest completed STAGEDAT mapping: `sol_translation_mappings/STAGEDAT_OLANG/LANG_MYOUTER_UTIL.OLANG.json`.
- Latest STAGEDAT mapping commit: `31115ee787219bb8cc2d268893995b35ab75d57b`.
- Resume next at: **STAGEDAT_OLANG/LANG_TITLE_OPTIONS.OLANG, unique_index 0**.
