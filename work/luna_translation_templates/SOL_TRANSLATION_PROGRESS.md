# Sol Translation Progress

Branch: `sol-translation`

Purpose: durable checkpoint for translation work under `work/luna_translation_templates/` so work can resume safely across chat turns.

## Rules
- JPN is the sole semantic and structural authority; MLG_CN / ENG are auxiliary only.
- Preserve markup, controls, placeholders, indices/references, ordering, timing, significant whitespace and resource identity.
- Work only under `work/luna_translation_templates/` / `sol_translation_mappings/`; do not touch formal build inputs or DAT/KEY.
- Use pending-review semantics; never mark Sol output `APPROVED`.
- Large files may use contiguous shards + manifest.
- For multiline CSVs, use logical `unique_index`, never physical line number.
- Bind current-row identity strictly by `unique_index` + `jpn_text`; previous/next are context only.
- If a mapping/shard already exists, fetch and verify it rather than overwriting concurrent progress.

## Current totals

| Metric | Progress |
|---|---:|
| Total template file_ids | 241 |
| Total template rows | 21041 |
| Translation work safely persisted | **9835 / 21041 rows** |
| file_ids with complete persisted translation | **116 / 241** |
| YPK_GTT | **36 / 36 complete** |
| OHD | **1 / 1 complete** |
| LOOSE_OLANG | **14 / 14 complete** |
| STAGEDAT_OLANG | **46 / 46 complete** |
| SLOT_OLANG | **19 / 144 complete** |

## Resource-class accounting
- YPK_GTT: **2080 rows / 36 complete file_ids**.
- OHD: **226 rows / 1 complete file_id**.
- LOOSE_OLANG: **1719 rows / 14 complete file_ids**.
- STAGEDAT_OLANG: **5687 rows / 46 complete file_ids**.
- SLOT_OLANG: **123 rows / 19 complete file_ids**.

## STAGEDAT checkpoint
STAGEDAT_OLANG is complete (46 / 46). Recent large completions include `LANG_MISSION_RESULT.OLANG` (357), `LANG_WEAPON_TEXT.OLANG` (388), and `LANG_MISSION_INFO.OLANG` (482). `LANG_MISSION_INFO` manifest commit: `9738fa4604e7ba659bc9a6fa95b54c95c819590e`.

## Completed SLOT checkpoints
- `5D02EB62` — 1 row.
- `5D0A5DB1` — 5 rows.
- `5D1708FB` — 5 rows.
- `5D0A7130` — 7 rows.
- `5D06A8D5` — 69 rows, two shards + manifest `d45b0971ddf094c5b3e55b60c9edbe4ba006eb24`.
- `5D3AF952` — 1 row; `見つかった！` -> `被发现了！`, review-flagged.
- `5D22E834` — 1 row; `静かに！` -> `安静！`, auxiliary parentheses rejected.
- `5DBF136F` — 1 row; all-training semantics preserved, latest mapping `72745e87cb16f239b5e6c0be99f186937329e8f9`.
- `5D3AFE0D` — 2 rows; punctuation follows JPN.
- `5D3B01ED` — 2 rows; trailing ASCII space on unique 0 preserved.
- `5D7E43B7` — 2 rows; `REPTILE POD` / `AIPOD` identities preserved.
- `5D62E635` — 2 rows; internal ASCII space and no-final-punctuation structure preserved.
- `5D3B092D` — 2 rows; Monster Hunter cat speech, internal spaces preserved.
- `5D3AF62D` — 4 rows; shifted auxiliary rejected; `<R=...,...>` ruby preserved.
- `5DA57DF4` — 4 rows; `電磁くすぐり棒` retained semantically as `电磁挠痒棒`, latest mapping `ff335021e65049696e4c9d5b643c5f6805a2f845`.
- `5D5D0A44` — 1 dedup row / 49 references; one newline preserved.
- `5DBA016B` — 5 rows; JPN crossover identities preserved over international substitutions.
- `5D3AF58D` — 5 rows; single ideographic-space placeholder, trailing ASCII space and internal ideographic space preserved. Mapping `52de256d49202fc2cf53c29a012d5883ac55ee44`.
- `5D3AF90D` — **4 rows complete**. Torture/self-termination clause keeps JPN internal ideographic space; one ruby control is preserved with `Chicolibri` reading; a single ideographic-space placeholder is not replaced by shifted auxiliary `Amanda`. Mapping commit `698e7f44165fc3f125c0c0260bc360cbbcaf45ee`.

## Important review / risk notes
- Auxiliary controls absent from JPN are always rejected.
- `<R=...,...>` control count/order must remain; display text may be localized while reading may use confirmed Latin/English.
- Japanese-version cast/staff credits are authoritative over English-dub substitutions.
- Fixed JPN model/code/crossover identities are not normalized from auxiliary international naming.
- Source whitespace can be structural: single-space rows, trailing ASCII spaces/newlines, fullwidth spaces and exact placeholder order must survive.
- `LANG_SYSTEM`: JPN `576KB` overrides auxiliary `544KB`; `サイバーバル` remains unresolved/flagged.
- `LANG_MISSION_ENDTELOP`: shifted auxiliary mission-title mapping rejected.
- `LANG_MYOUTER_STAFF_COMMENT`: JPN `祖母` overrides auxiliary `mother`; source `(不要)` placeholders remain.
- `LANG_MYOUTER_TOP`: source `METAL GEAR ZEK` spelling and unique 159 trailing ASCII whitespace preserved.
- `LANG_MISSION_RESULT`: `BLAVO`, `ALFA`, fixed ASCII labels, placeholder spacing and hero-spirit punctuation follow JPN.
- `LANG_WEAPON_TEXT`: JPN controls/model identities authoritative; auxiliary normalizations rejected.
- `LANG_MISSION_INFO`: identity follows `unique_index + jpn_text`; 298/299/300 boundary and shared DEMO rows were rechecked; auxiliary-added `<I=CPY>` around `©CAPCOM CO., LTD.` rejected.

## Next resource class
`SLOT_OLANG` — **19 / 144 complete**. Continue the next unstarted small SLOT after checking for newer concurrent mappings.

## Last safe checkpoint
- Safe translation total: **9835 rows / 116 complete file_ids**.
- SLOT_OLANG: **19 / 144 complete; 123 rows**.
- Latest completed artifact: `sol_translation_mappings/SLOT_OLANG/5D3AF90D.json`.
- Latest mapping commit: `698e7f44165fc3f125c0c0260bc360cbbcaf45ee`.
- Resume next: **next unstarted small SLOT_OLANG file_id**.
