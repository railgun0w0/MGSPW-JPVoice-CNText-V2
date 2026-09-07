# Sol Translation Progress

Branch: `sol-translation`

Purpose: durable checkpoint for translation work under `work/luna_translation_templates/` so work can resume safely across chat turns.

Historical checkpoint archive:
- `SOL_TRANSLATION_PROGRESS_ARCHIVE_2026-09-07_10603.md` — exact pre-compaction tracker snapshot through 10603 rows / 177 file_ids / SLOT 80/144.

## Rules
- JPN is the sole semantic and structural authority; MLG_CN / ENG are auxiliary only.
- Preserve markup, controls, placeholders, indices/references, ordering, timing, significant whitespace and resource identity.
- Work only under `work/luna_translation_templates/` / `sol_translation_mappings/`; do not touch formal build inputs or DAT/KEY.
- Use pending-review semantics; never mark Sol output `APPROVED`.
- Large files may use contiguous shards + manifest.
- For multiline CSVs, use logical `unique_index`, never physical line number.
- Bind current-row identity strictly by `unique_index` + `jpn_text`; previous/next are context only.
- If a mapping/shard already exists, fetch and verify it rather than overwriting concurrent progress.
- Completed file_ids are committed and immediately reflected in this tracker.

## Current totals
| Metric | Progress |
|---|---:|
| Total template file_ids | 241 |
| Total template rows | 21041 |
| Translation work safely persisted | **10668 / 21041 rows** |
| file_ids with complete persisted translation | **180 / 241** |
| YPK_GTT | **36 / 36 complete** |
| OHD | **1 / 1 complete** |
| LOOSE_OLANG | **14 / 14 complete** |
| STAGEDAT_OLANG | **46 / 46 complete** |
| SLOT_OLANG | **83 / 144 complete** |

## Resource-class accounting
- YPK_GTT: **2080 rows / 36 complete file_ids**.
- OHD: **226 rows / 1 complete file_id**.
- LOOSE_OLANG: **1719 rows / 14 complete file_ids**.
- STAGEDAT_OLANG: **5687 rows / 46 complete file_ids**.
- SLOT_OLANG: **956 rows / 83 complete file_ids**.

## STAGEDAT checkpoint
STAGEDAT_OLANG is complete (46 / 46). `LANG_MISSION_INFO` manifest commit: `9738fa4604e7ba659bc9a6fa95b54c95c819590e`.

## Archive boundary
- Full detailed history through `5D3B0112` is preserved byte-for-byte in `SOL_TRANSLATION_PROGRESS_ARCHIVE_2026-09-07_10603.md`.
- Boundary mapping: `5D3B0112` — 23 rows, commit `866a6f5f0e279aba9a96ffce338961cbfd7b51a4`.
- Boundary totals: **10603 / 21041 rows**, **177 / 241 file_ids**, SLOT **80 / 144**, **891 rows**.

## Post-archive SLOT checkpoints
- `5DCDD1C4` 25; briefing-files UI/speaker table follows JPN structure: fixed `BRIEFING FILES`, `NEXT`, `UNKNOWN`, `BACK` identities remain untranslated; `・`, adjacent `$1$2`, fullwidth digits `１/２`, ideographic separator in save/quit, fullwidth `＆` in `Snake＆Miller`, and `－－` placeholder are preserved. Mapping `d066c8ce1066e6455f7570e76477b559359561b8`.
- `5DA7D877` 16; high-reuse map/HUD identity table preserves every JPN fixed ASCII label exactly, including `CAFETAL AROMA ENCANTADO`, `CRATER BASE`, `LOS CANTOS` variants, `TARGET`, `SNAKE`, and `GOAL`. Mapping `038d9f6c529d55601843cd57b4eaa0e1b5ba2389`.
- `5D483717` 24; AI-weapon battle/system table follows JPN rather than auxiliary narrowing: abdomen threat and direct attack semantics are retained, `潰してやる！！` keeps double exclamation, paired punctuation variants remain distinct, and `応急処置` is rendered as emergency handling rather than auxiliary override. Mapping `6ee6f323de2a440252a1ec074c6bcda76b941e0b`.

## Important review / risk notes
- Auxiliary controls absent from JPN are always rejected.
- `<R=...,...>` control count/order must remain; display text may be localized while reading may use confirmed Latin/English.
- Fixed JPN model/code/crossover/location/UI identities are not normalized from auxiliary naming.
- Source whitespace can be structural: single-space rows, trailing ASCII spaces/newlines, fullwidth spaces, control-internal spaces and exact placeholder order must survive.
- Japanese-version cast/staff credits are authoritative over English-dub substitutions.
- `LANG_SYSTEM`: JPN `576KB` overrides auxiliary `544KB`; `サイバーバル` remains unresolved/flagged.
- `LANG_MISSION_ENDTELOP`: shifted auxiliary mission-title mapping rejected.
- `LANG_MYOUTER_STAFF_COMMENT`: JPN `祖母` overrides auxiliary `mother`; source `(不要)` placeholders remain.
- `LANG_MYOUTER_TOP`: source `METAL GEAR ZEK` spelling and unique 159 trailing ASCII whitespace preserved.
- `LANG_MISSION_RESULT`, `LANG_WEAPON_TEXT`, `LANG_MISSION_INFO`: JPN controls/identities/placeholder spacing and repaired boundaries remain authoritative.

## Next resource class
`SLOT_OLANG` — **83 / 144 complete**. Continue the next unstarted small SLOT after checking for newer concurrent mappings.

## Last safe checkpoint
- Safe translation total: **10668 rows / 180 complete file_ids**.
- SLOT_OLANG: **83 / 144 complete; 956 rows**.
- Latest completed artifact: `sol_translation_mappings/SLOT_OLANG/5D483717.json`.
- Latest mapping commit: `6ee6f323de2a440252a1ec074c6bcda76b941e0b`.
- Resume next: **next unstarted small SLOT_OLANG file_id**.
