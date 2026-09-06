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
| Translation work safely persisted | **4781 / 21041 rows** |
| file_ids with complete persisted translation | **77 / 241** |
| YPK_GTT | **36 / 36 complete** |
| OHD | **1 / 1 complete** |
| LOOSE_OLANG | **14 / 14 complete** |
| STAGEDAT_OLANG | **26 / 46 complete** |
| SLOT_OLANG | **0 / 144** |

## Resource-class accounting

- YPK_GTT: **2080 rows / 36 file_ids complete**.
- OHD: **226 rows / 1 file_id complete**.
- LOOSE_OLANG: **1719 rows / 14 file_ids complete**.
- STAGEDAT_OLANG: **756 rows / 26 file_ids complete**.

### STAGEDAT completed

`LANG_DEMOSKIPTELOP.OLANG` (1), `LANG_EMERGENCYTELOP.OLANG` (5), `LANG_COMMUNICATIONSTELOP.OLANG` (5), `LANG_BRIEFING.OLANG` (25), `LANG_CHARAEDIT.OLANG` (46), `LANG_DEMOTELOP4.OLANG` (47), `LANG_DEMOTELOP.OLANG` (34), `LANG_TITLE_NAMEENTRY.OLANG` (4), `LANG_WALKMAN.OLANG` (9), `LANG_MAP_FLOOR.OLANG` (9), `LANG_SPOOKY_COMMON.OLANG` (7), `LANG_PSP_KEYBOARD.OLANG` (6), `LANG_SYNC.OLANG` (19), `LANG_TITLEMENU.OLANG` (17), `LANG_DEMOTELOP2.OLANG` (76), `LANG_V_THEATER020.OLANG` (16), `LANG_V_THEATER010.OLANG` (24), `LANG_MYOUTER_UTIL.OLANG` (33), `LANG_TITLE_OPTIONS.OLANG` (27), `LANG_HTTP_ERROR.OLANG` (30), `LANG_KEYHELP.OLANG` (23), `LANG_PW_COMMON.OLANG` (35), `LANG_MYOUTER_STAFF_SOLTYPE.OLANG` (63), `LANG_PAUSEMENU.OLANG` (75), `LANG_VOCALOID.OLANG` (64), `LANG_ONLINE_ERROR.OLANG` (56).

## Important review / risk notes

- JPN always wins over shifted, combined, over-expanded, or version-specific auxiliary text.
- Auxiliary-inserted controls absent from JPN were rejected in CHAR_EDIT, WALKMAN, TITLEMENU, HTTP_ERROR and PW_COMMON.
- `LANG_DEMOTELOP4`: English-dub cast substitution rejected; JPN Japanese voice cast preserved.
- `LANG_DEMOTELOP`: late shifted auxiliary around `恋の抑止力` / `HEAVENS DIVIDE` rejected; `ボスケ・デル・アルバ` → `黎明森林` remains terminology-review material.
- `LANG_DEMOTELOP2`: Japanese-version cast/staff are authoritative. English-dub cast substitutions in MLG_CN / ENG were rejected. Credit role terminology follows `LANG_DEMOTELOP4`; trailing date/location test-style rows were translated from JPN without importing auxiliary `(不要)` prefixes.
- `LANG_V_THEATER010` and `LANG_V_THEATER020`: ruby/control structure preserved exactly; shifted auxiliary dialogue was rejected where it disagreed with the JPN sequence.
- `LANG_MYOUTER_UTIL`: `<I=CAN>/<I=DEC>` controls and space-only placeholders preserved; source `(不要)` markers retained; auxiliary-untranslated JPN descriptions localized directly from JPN.
- `LANG_TITLE_OPTIONS`: button/ruby/control structure preserved; JPN version-specific labels and literal marks win over auxiliary substitutions.
- `LANG_HTTP_ERROR`: only `$1/$2/$3` are JPN controls; literal `PlayStation®Network` and `PSP®` are preserved, auxiliary `<I=REG>/<I=TM>` insertions rejected.
- `LANG_KEYHELP`: high reference_count rows are exact-deduped JPN text; auxiliary behavior expansions and multi-candidate shifts rejected.
- `LANG_PW_COMMON`: literal □/△/×/○ button glyphs preserved as text; no auxiliary `<I=...>` icon controls introduced. CO-OPS/CH/TOP preserved where fixed or semantically ambiguous.
- `LANG_MYOUTER_STAFF_SOLTYPE`: no JPN controls. UT model codes preserved with localized colors; brand/collab labels follow JPN instead of auxiliary `NORMAL`; source `(不要)` markers retained. `Basilisk` remains terminology-review material.
- `LANG_PAUSEMENU`: no JPN controls. Mission abort/restart warnings preserve “revert to pre-mission state” semantics; radio terms follow JPN rather than Codec expansion; `プリビアスタイプ` → `2槽位切换型` remains terminology-review material.
- `LANG_VOCALOID`: row 34 preserves JPN control sequence `<I=REG>`×2 then `<I=TM>`×5 and rejects auxiliary `<I=BL>` insertion; row 62 preserves `$1/$2`. JPN CO-OP In/Out, ENTRY GATE→CO-OPS COMM., dialogue/lyrics distinctions and ZEKE battle wording override auxiliary substitutions.
- `LANG_ONLINE_ERROR`: 56 rows complete. `$1`, `<I=DEC>`, `<I=CAN>`, `<I=△>` controls/placeholders preserved. Auxiliary “kicked” additions were rejected where JPN only states team-kill/idle timeout or connection refusal semantics.
- `LANG_TITLE_NAMEENTRY`: explicit allowed-symbol list from JPN preserved.
- `LANG_MAP_FLOOR`: JPN `B4F/B3F/B2F/B1F` preserved; auxiliary dropped `F`.
- `LANG_SYNC`: unclear abbreviations `LV/S/B/ZZZ/STN` preserved rather than guessed.
- `LANG_TITLEMENU`: `NIHON-GO` follows JPN as `日语`; auxiliary `ENGLISH` is treated as version substitution. Memory Stick™ rows remain plain text with no invented icon controls.

## Last safe checkpoint

- Safe translation total: **4781 rows / 77 complete file_ids**.
- Resource-class checkpoint: **STAGEDAT_OLANG 26 / 46 complete**.
- Latest completed STAGEDAT mapping: `sol_translation_mappings/STAGEDAT_OLANG/LANG_ONLINE_ERROR.OLANG.json`.
- Latest STAGEDAT mapping commit: `3568c09fb036634fb7ce0d3f8c1eae6f3296b97d`.
- Resume next at: **STAGEDAT_OLANG/LANG_DATAINSTALL.OLANG, unique_index 0**.
