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
- For CSVs with embedded newlines, never use physical line numbers as row identity; anchor work to logical `unique_index`.

## Current totals

| Metric | Progress |
|---|---:|
| Total template file_ids | 241 |
| Total template rows | 21041 |
| Translation work safely persisted | **4242 / 21041 rows** |
| file_ids with complete persisted translation | **64 / 241** |
| YPK_GTT | **36 / 36 complete** |
| OHD | **1 / 1 complete** |
| LOOSE_OLANG | **14 / 14 complete** |
| STAGEDAT_OLANG | **13 / 46 complete** |
| SLOT_OLANG | **0 / 144** |

## Completed resource accounting

### YPK_GTT
- **2080 rows / 36 file_ids complete**.
- 21 file_ids / 491 rows already merged into 28-column Luna CSVs.
- 15 file_ids / 1589 rows fully translated and persisted as mappings pending mechanical CSV merge.

### OHD
- `1E4C1146`: **226 / 226 rows complete**, four shards + manifest.

### LOOSE_OLANG
- **1719 / 1719 rows, 14 / 14 file_ids complete**.
- `007E2F18`: **1094 / 1094 rows complete**, 11 shards + manifest.

### STAGEDAT_OLANG
- **217 rows / 13 file_ids complete** so far.
- `LANG_DEMOSKIPTELOP.OLANG`: **1 / 1**.
- `LANG_EMERGENCYTELOP.OLANG`: **5 / 5**.
- `LANG_COMMUNICATIONSTELOP.OLANG`: **5 / 5**.
- `LANG_BRIEFING.OLANG`: **25 / 25**.
- `LANG_CHARAEDIT.OLANG`: **46 / 46**.
- `LANG_DEMOTELOP4.OLANG`: **47 / 47**.
- `LANG_DEMOTELOP.OLANG`: **34 / 34**.
- `LANG_TITLE_NAMEENTRY.OLANG`: **4 / 4**, mapping blob `05bbabecbb4641389b25f578756f4228a5cb436b`.
- `LANG_WALKMAN.OLANG`: **9 / 9**, mapping blob `ae4ec4a8613eb23327c1658cea037f01d942896f`.
- `LANG_MAP_FLOOR.OLANG`: **9 / 9**, mapping blob `f106fbcecd8bdbde5eeaa4f7a6f0cafe05f11d63`.
- `LANG_SPOOKY_COMMON.OLANG`: **7 / 7**, mapping blob `fe6d2fad1c78cf88580077b99d456fadeeb32b45`.
- `LANG_PSP_KEYBOARD.OLANG`: **6 / 6**, mapping blob `e9e2f3cb59552a4990f825e8fd62fb20aba42371`.
- `LANG_SYNC.OLANG`: **19 / 19**, mapping blob `473b68213629440261fd3ff4d74f684192ae7135`.

## Next target

Continue remaining **STAGEDAT_OLANG (33 file_ids)**, then SLOT_OLANG unless a resource-specific structural problem justifies changing order.

Prefer complete small/medium STAGEDAT files when practical. Before translating a queued file, check whether its mapping already exists; if it does and coverage is complete, count it and move on rather than overwriting.

## Important review / risk notes

- JPN always wins over shifted, combined, over-expanded, or version-specific MLG_CN / ENG auxiliary text.
- STAGEDAT mappings preserve page/DAR/RBX/entity/reference structure; only translation mappings are persisted here.
- `LANG_CHARAEDIT.OLANG`: JPN `メモリースティック™` has no control tokens. Auxiliary `<I=BL>/<I=TM>` insertion was rejected.
- `LANG_DEMOTELOP4.OLANG`: JPN Japanese voice-cast names were preserved; English-dub cast substitutions were rejected.
- `LANG_DEMOTELOP.OLANG`: late auxiliary rows around `恋の抑止力` / `HEAVENS DIVIDE` were sequence-shifted; music titles and vocalist credits follow JPN directly. `ボスケ・デル・アルバ` is provisionally `黎明森林` and remains terminology-review material.
- `LANG_TITLE_NAMEENTRY.OLANG`: the explicit allowed-symbol list omitted by auxiliary CN was restored from JPN.
- `LANG_WALKMAN.OLANG`: JPN literal `○` has no control token; auxiliary `<I=○>` insertion was rejected.
- `LANG_MAP_FLOOR.OLANG`: JPN basement floor labels `B4F` etc. were preserved; auxiliary dropped the `F` suffix.
- `LANG_SPOOKY_COMMON.OLANG`: JPN says playback has stopped and asks whether to skip; auxiliary softened/changed those meanings.
- `LANG_PSP_KEYBOARD.OLANG`: `%d` placeholders preserved.
- `LANG_SYNC.OLANG`: clear UI labels localized; ambiguous abbreviations such as `LV/S/B/ZZZ/STN/CQC` preserved.

## Last safe checkpoint

- Safe translation total: **4242 rows / 64 complete file_ids**.
- Resource-class checkpoint: **STAGEDAT_OLANG 13 / 46 complete**.
- Latest confirmed STAGEDAT mapping: `sol_translation_mappings/STAGEDAT_OLANG/LANG_SYNC.OLANG.json`.
- Resume next at: **STAGEDAT_OLANG, next untranslated file_id**.
