# Sol Translation Progress

Branch: `sol-translation`

Purpose: durable checkpoint for translation work under `work/luna_translation_templates/` so work can resume safely across chat turns.

Historical checkpoints:
- `SOL_TRANSLATION_PROGRESS_ARCHIVE_2026-09-07_10603.md` — exact snapshot through **10603 rows / 177 file_ids / SLOT 80/144**.
- Pre-compaction tracker through **11449 rows / 201 file_ids / SLOT 104/144** is recoverable from Git commit `4815c7c74868cee726ec8849f067983e1ef24ceb`.

## Hard rules
- JPN is the sole semantic and structural authority; MLG_CN / ENG are auxiliary only.
- Preserve markup, controls, placeholders, indices/references, ordering, timing, significant whitespace and resource identity.
- Work only under `work/luna_translation_templates/sol_translation_mappings/`; do not modify formal `translations/`, manifest, DAT/KEY or build outputs.
- Use `TRANSLATED_PENDING_CSV_MERGE` / pending-review semantics; never mark Sol output `APPROVED`.
- Large files may use contiguous shards + manifest.
- For multiline CSVs, use logical `unique_index`, never physical line number.
- Current-row identity is strictly `unique_index + jpn_text`; previous/next text is context only.
- Existing mappings/shards must be fetched and verified before any write; never overwrite concurrent progress.
- Completed file_ids must be committed, read back for QA, then immediately reflected in this tracker.
- For uncertainty, make a conservative JPN-grounded judgment and record `review_flag`; do not stop for clarification.

## Current totals
| Metric | Progress |
|---|---:|
| Total template file_ids | 241 |
| Total template rows | 21041 |
| Translation work safely persisted | **11778 / 21041 rows** |
| file_ids with complete persisted translation | **208 / 241** |
| YPK_GTT | **36 / 36 complete** |
| OHD | **1 / 1 complete** |
| LOOSE_OLANG | **14 / 14 complete** |
| STAGEDAT_OLANG | **46 / 46 complete** |
| SLOT_OLANG | **111 / 144 complete** |

## Resource-class accounting
- YPK_GTT: **2080 rows / 36 complete file_ids**.
- OHD: **226 rows / 1 complete file_id**.
- LOOSE_OLANG: **1719 rows / 14 complete file_ids**.
- STAGEDAT_OLANG: **5687 rows / 46 complete file_ids**.
- SLOT_OLANG: **2066 rows / 111 complete file_ids**.

## Completed class checkpoints
- YPK_GTT complete: **36/36**.
- OHD complete: **1/1**.
- LOOSE_OLANG complete: **14/14**.
- STAGEDAT_OLANG complete: **46/46**. `LANG_MISSION_INFO` manifest commit `9738fa4604e7ba659bc9a6fa95b54c95c819590e`.

## Recent SLOT checkpoints
- `5D52801A` — 47 rows; ZEKE simulation/damage/battle-voice table follows current JPN short status and punctuation. `ZEKE`, fullwidth `Ｓ`, internal spaces, ellipses, questions and `！？` preserved; auxiliary expansions rejected. Mapping `5efdb81c96ed7e6d401a4e3db10eb39b89411f48`.
- `5DCBA83B` — 30 rows; VOCALOID/server conversion and network-error UI follows JPN request/conversion distinctions. `$1/$2/$3`, PlayStation®Network/PSP® literal signs, 3-attempt/1-day threshold and certificate wording preserved; auxiliary controls rejected. Mapping `2b5ed9a888bc12f6b7f9feb6f359acc3cee42f37`.
- `5D3B05B2` — 44 rows; Peace Walker sinking/Ghost in the Machine/The Boss ending dialogue rebuilt strictly from JPN after severe auxiliary shift. Ruby identities distinguish `意志/WILL`, `最期→结局/WILL`, and `她/The Boss`; 哺乳舱/爬虫舱 and functional compensation preserved. Mapping `fc6805c67c979ab09e95d6724f1e7afe8b2ea6b3`.
- `5DD9AF4C` — 33 rows; MODEL VIEWER / KEY HELP table preserves fixed ASCII identities, source-only controls, ASCII and ideographic-space placeholders, distinct Text/Article OFF wording, M1911A1/Kerotan `(不要)` descriptions with paragraph structure, GMP warning layout, and fixed YES/SKIP/OK/NO/CANCEL identities. Mapping `e654b678d5848eb32ae8892ac52fcf037e7ce1a4`.
- `5D3AF9AD` — 45 rows; nuclear-deterrence/Coldman-Huey dialogue follows JPN three-principle ordering and later auxiliary shift. Japanese quote types, newlines, ASCII/fullwidth spaces, `！？`, two ideographic-space placeholders, double trailing space on `創造物？`, Peace Walker terminology, and `脚/Peace Walker` plus `V/PEACE` ruby wordplay are preserved. Mapping `94d6cfcea50e495265d82493a7f896c0fc2cdd4c`.
- `5D09325F` — 107 rows in 3 contiguous shards; mission-result/title dictionary follows current JPN semantic titles while preserving fixed model/code identities. Aggregated auxiliary EXTRA OPS labels/numbers are rejected; leading/trailing whitespace, II/CUSTOM/model suffixes and hunting double-angle pseudo-controls are preserved. Manifest `1fac83a8da201434fc2a8f0f3eaad9fb0da006ce`.

## Important review / risk notes
- Auxiliary controls absent from JPN are always rejected.
- `<R=...,...>` count/order must remain; display text may be localized while readings retain source-confirmed Japanese/Latin/English identity.
- Fixed JPN model/code/crossover/location/UI identities are not normalized from auxiliary naming.
- Whitespace can be structural: single-space rows, multi-space placeholders, trailing ASCII spaces/newlines, fullwidth spaces, control-internal spaces and exact placeholder order must survive.
- Japanese-version cast/staff credits are authoritative over English-dub substitutions.
- Double-angle mission titles such as `<<HUNTING QUEST: ...>>` can be mechanically misdetected as control-like tokens; preserve current-JPN literal structure and flag the pseudo-control instead of treating it like `<I>/<R>/<C>` markup.
- Known historical review flags remain recorded in mappings / previous tracker history, including `LANG_SYSTEM` 576KB and unresolved `サイバーバル`, shifted auxiliary mission-title rows, and preserved source-specific spellings/placeholders.

## Next resource class
`SLOT_OLANG` — **111 / 144 complete**. Continue an unstarted SLOT only after checking the latest branch for concurrent mappings.

## Last safe checkpoint
- Safe translation total: **11778 / 21041 rows**.
- Complete file_ids: **208 / 241**.
- SLOT_OLANG: **111 / 144 complete; 2066 rows**.
- Latest completed artifact: `sol_translation_mappings/SLOT_OLANG/5D09325F.manifest.json`.
- Latest mapping commit: `1fac83a8da201434fc2a8f0f3eaad9fb0da006ce`.
- Resume next: **next unstarted SLOT_OLANG file_id after latest-branch race-check**.
