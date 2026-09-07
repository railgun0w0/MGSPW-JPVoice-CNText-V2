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
- If a mapping/shard already exists, fetch and verify it rather than overwriting concurrent progress.

## Current totals

| Metric | Progress |
|---|---:|
| Total template file_ids | 241 |
| Total template rows | 21041 |
| Translation work safely persisted | **8485 / 21041 rows** |
| file_ids with complete persisted translation | **94 / 241** |
| YPK_GTT | **36 / 36 complete** |
| OHD | **1 / 1 complete** |
| LOOSE_OLANG | **14 / 14 complete** |
| STAGEDAT_OLANG | **43 / 46 complete** |
| SLOT_OLANG | **0 / 144** |

## Resource-class accounting
- YPK_GTT: **2080 rows / 36 complete file_ids**.
- OHD: **226 rows / 1 complete file_id**.
- LOOSE_OLANG: **1719 rows / 14 complete file_ids**.
- STAGEDAT_OLANG: **4460 rows / 43 complete file_ids**.

## Recent completed STAGEDAT
- `LANG_ITEM_TEXT.OLANG` — 803 rows, 17 shards + manifest.
- `LANG_MYOUTER_STAFF.OLANG` — 146 rows, two shards + manifest.
- `LANG_MYOUTER_DEVELOP.OLANG` — 167 rows, two shards + manifest.
- `LANG_MYOUTER_DEVELOP_METAL.OLANG` — 592 rows, seven shards + manifest.
- `LANG_VOCALOID_KEYBOARD.OLANG` — 175 rows, three shards + manifest. English pronunciation examples and VOCALOID phoneme data are preserved; only actual keyboard/help/error UI is localized.
- `LANG_MYOUTER_STAFF_COMMENT.OLANG` — 356 rows, eight shards + manifest, complete.
- `LANG_MYOUTER_TOP.OLANG` — **202 rows, four shards + manifest, complete**. Manifest commit `9d9f29398abf65415c3430e1736910bb17300d16`.

## Important review / risk notes
- Auxiliary controls absent from JPN are always rejected.
- Japanese-version cast/staff credits are authoritative over English-dub substitutions.
- `LANG_SYSTEM`: JPN `576KB` overrides auxiliary `544KB`; `サイバーバル` remains unresolved/flagged.
- `LANG_MISSION_ENDTELOP`: shifted auxiliary mission-title mapping rejected; hunting double-angle titles remain parser-false-positive review items.
- `LANG_ITEM_TEXT`: JPN weapon/item/brand identity, hidden rows, fixed ASCII short labels/codes and document types remain authoritative over auxiliary substitutions.
- `LANG_MYOUTER_DEVELOP_METAL`: ZEKE configuration, parts, VOCALOID/AI settings and AI memory-board identifiers follow JPN identity; fixed English codes remain fixed.
- `LANG_VOCALOID_KEYBOARD`: English pronunciation examples and phoneme syntax remain exact; only actual UI/help/error text is localized.
- `LANG_MYOUTER_STAFF_COMMENT`: all 356 rows complete. JPN `祖母` overrides auxiliary `mother`; `無力化` stays distinct from killing; source `(不要)` voice-actor placeholders remain; named-character dialogue and biographies were reviewed separately from generic staff chatter.
- `LANG_MYOUTER_TOP`: all 202 rows complete. Printf placeholders remain text placeholders and are not misclassified as runtime controls; `$1/$2/$3` order follows JPN. Source `(不要)` rows remain. Fixed ASCII labels such as `OUTER OPS`, `MECHA`, `KEY CONFIG`, `DEVELOP`, `MOTHER-BASE` follow JPN identity. Auxiliary errors claiming a battle begins instead of ends, euphemizing explicit soldier death, adding an extra support marker, inserting Memory Stick icon controls, and substituting `SENDBOX` were rejected. Source `METAL GEAR ZEK` spelling at row 96 is preserved and flagged as a likely source typo.

## Remaining STAGEDAT
`LANG_MISSION_INFO.OLANG`, `LANG_MISSION_RESULT.OLANG`, `LANG_WEAPON_TEXT.OLANG`.

## Last safe checkpoint
- Safe translation total: **8485 rows / 94 complete file_ids**.
- STAGEDAT_OLANG: **43 / 46 complete**.
- Latest completed artifact: `sol_translation_mappings/STAGEDAT_OLANG/LANG_MYOUTER_TOP.OLANG.manifest.json`.
- Latest manifest commit: `9d9f29398abf65415c3430e1736910bb17300d16`.
- Resume next: **STAGEDAT_OLANG/LANG_MISSION_RESULT.OLANG**, unless a newer concurrent checkpoint is present.
