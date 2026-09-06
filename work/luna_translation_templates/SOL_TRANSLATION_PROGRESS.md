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
| Translation work safely persisted | **4188 / 21041 rows** |
| file_ids with complete persisted translation | **58 / 241** |
| YPK_GTT | **36 / 36 complete** |
| OHD | **1 / 1 complete** |
| LOOSE_OLANG | **14 / 14 complete** |
| STAGEDAT_OLANG | **7 / 46 complete** |
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
- **163 rows / 7 file_ids complete** so far.
- `LANG_DEMOSKIPTELOP.OLANG`: **1 / 1**, commit `41e634c3c3c23530379d3fefd920d427540d189e`.
- `LANG_EMERGENCYTELOP.OLANG`: **5 / 5**, commit `03311c8a86834788942f4d0189e82dba29da82e9`.
- `LANG_COMMUNICATIONSTELOP.OLANG`: **5 / 5**, commit `8099350a0c545d823d7560f849b8c6d2f4934bec`.
- `LANG_BRIEFING.OLANG`: **25 / 25**, commit `7a05bbdfe9822679df24fd18d870cff5503f307e`.
- `LANG_CHARAEDIT.OLANG`: **46 / 46**, commit `1ed668ba5b2dac1638c93f6911a9a543476d9e41`.
- `LANG_DEMOTELOP4.OLANG`: **47 / 47**, commit `7360603b8c58811f43e4159d150239e0f7d6aea8`.
- `LANG_DEMOTELOP.OLANG`: **34 / 34**, commit `d04bae2dd9fcca5e47a5078498cf492c0826670c`.

## Next target

Continue remaining **STAGEDAT_OLANG (39 file_ids)**, then SLOT_OLANG unless a resource-specific structural problem justifies changing order.

Small-file priority queue: `LANG_TITLE_NAMEENTRY.OLANG`, `LANG_WALKMAN.OLANG`, `LANG_MAP_FLOOR.OLANG`, `LANG_SPOOKY_COMMON.OLANG`, `LANG_PSP_KEYBOARD.OLANG`, `LANG_SYNC.OLANG`, then larger files.

## Important review / risk notes

- JPN always wins over shifted, combined, over-expanded, or version-specific MLG_CN / ENG auxiliary text.
- STAGEDAT mappings preserve page/DAR/RBX/entity/reference structure; only translation mappings are persisted here.
- `LANG_CHARAEDIT.OLANG`: JPN `メモリースティック™` has no control tokens. Auxiliary `<I=BL>/<I=TM>` insertion was rejected.
- `LANG_DEMOTELOP4.OLANG`: JPN Japanese voice-cast names were preserved; English-dub cast substitutions were rejected.
- `LANG_DEMOTELOP.OLANG`: late auxiliary rows around `恋の抑止力` / `HEAVENS DIVIDE` were sequence-shifted; music titles and vocalist credits follow JPN directly. `ボスケ・デル・アルバ` is provisionally `黎明森林` and remains terminology-review material.

## Last safe checkpoint

- Safe translation total: **4188 rows / 58 complete file_ids**.
- Resource-class checkpoint: **STAGEDAT_OLANG 7 / 46 complete**.
- Latest completed STAGEDAT mapping: `sol_translation_mappings/STAGEDAT_OLANG/LANG_DEMOTELOP.OLANG.json`.
- Latest STAGEDAT mapping commit: `d04bae2dd9fcca5e47a5078498cf492c0826670c`.
- Resume next at: **STAGEDAT_OLANG/LANG_TITLE_NAMEENTRY.OLANG, unique_index 0**.
