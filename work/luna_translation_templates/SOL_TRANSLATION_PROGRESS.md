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
| Translation work safely persisted | **9919 / 21041 rows** |
| file_ids with complete persisted translation | **126 / 241** |
| YPK_GTT | **36 / 36 complete** |
| OHD | **1 / 1 complete** |
| LOOSE_OLANG | **14 / 14 complete** |
| STAGEDAT_OLANG | **46 / 46 complete** |
| SLOT_OLANG | **29 / 144 complete** |

## Resource-class accounting
- YPK_GTT: **2080 rows / 36 complete file_ids**.
- OHD: **226 rows / 1 complete file_id**.
- LOOSE_OLANG: **1719 rows / 14 complete file_ids**.
- STAGEDAT_OLANG: **5687 rows / 46 complete file_ids**.
- SLOT_OLANG: **207 rows / 29 complete file_ids**.

## STAGEDAT checkpoint
STAGEDAT_OLANG is complete (46 / 46). Recent large completions include `LANG_MISSION_RESULT.OLANG` (357), `LANG_WEAPON_TEXT.OLANG` (388), and `LANG_MISSION_INFO.OLANG` (482). `LANG_MISSION_INFO` manifest commit: `9738fa4604e7ba659bc9a6fa95b54c95c819590e`.

## Completed SLOT checkpoints
- `5D02EB62` 1; `5D0A5DB1` 5; `5D1708FB` 5; `5D0A7130` 7.
- `5D06A8D5` 69, two shards + manifest `d45b0971ddf094c5b3e55b60c9edbe4ba006eb24`.
- `5D3AF952` 1; `5D22E834` 1; `5DBF136F` 1; `5D3AFE0D` 2; `5D3B01ED` 2.
- `5D7E43B7` 2; fixed `REPTILE POD` / `AIPOD` identities preserved.
- `5D62E635` 2; `5D3B092D` 2; `5D3AF62D` 4 with ruby preserved.
- `5DA57DF4` 4; `電磁くすぐり棒` -> `电磁挠痒棒`, latest `ff335021e65049696e4c9d5b643c5f6805a2f845`.
- `5D5D0A44` 1 dedup row / 49 refs; one newline preserved.
- `5DBA016B` 5; JPN crossover identities preserved over international substitutions.
- `5D3AF58D` 5; structural spaces preserved. Mapping `52de256d49202fc2cf53c29a012d5883ac55ee44`.
- `5D3AF90D` 4; torture/self-termination clause, ruby and space placeholder follow JPN. Mapping `698e7f44165fc3f125c0c0260bc360cbbcaf45ee`.
- `5DA7D87B` 7; fixed uppercase shooting-range/location labels preserved. Mapping `7b5f2934e05e35bbf8f5f7f30e2bcfc79741f757`.
- `5DE2E8B4` 6; shifted auxiliary rejected; prison/guard dialogue restored from JPN. Latest `5119c9c121cd811d7a0cf4198b638ec0a339ded0`.
- `5DC637BF` 9; floor codes `B4F` through `5F` preserved exactly. Mapping `37b4f9fd5ec548054a63d805d2b0c3f2284e3076`.
- `5D3AF56D` 5; ruby controls OUT/SPEAR/BARGE/POINT BRAVO/CHRYSALIS and structural spaces preserved. Mapping `8449769c0f65820c61743abbd3fd076643be558e`.
- `5D218EA9` 9; fixed WALKMAN/device labels preserved; no auxiliary-added `<I=○>`. Mapping `1186584e4f4f2ff3278b509ab215957b46029428`.
- `5DA7D876` 10; fixed stage/location labels preserved exactly, including `RlO DEL JADE`. Mapping `54d4d4872010a7dfd2f0b17755e9335de9601254`.
- `5D3B020D` 8; dialogue context maintained; significant spaces and GONDOLA ruby preserved. Mapping `554a2e287de5463299698f738193c42e5924d6e1`.
- `5D56AA31` 12; fixed scanner/status JPN labels preserved over auxiliary substitutions. Mapping `bedd25df8614e873e8885ee2723a1b2b80a8d38b`.
- `5D3B060D` 8; current-row JPN restored; BIGBOSS/ZEKE ruby and spaces preserved. Mapping `eb2a3ce096138921c4c5cbd8f5fca319ea3ad322`.
- `5D3AF992` — **10 rows complete**. Shifted auxiliary dialogue rejected; Zadornov search/truck/facility lines restored from current JPN; `監督！`, elongated `太陽ぉおお！！`, fixed `METAL… GEAR…`, and passive `見つかった！` semantics preserved, including significant spaces. Mapping commit `30846c387ea2606356c90fd534fd6bd8f00767e9`.

## Important review / risk notes
- Auxiliary controls absent from JPN are always rejected.
- `<R=...,...>` control count/order must remain; display text may be localized while reading may use confirmed Latin/English.
- Fixed JPN model/code/crossover/location/UI identities are not normalized from auxiliary naming.
- Source whitespace can be structural: single-space rows, trailing ASCII spaces/newlines, fullwidth spaces and exact placeholder order must survive.
- Japanese-version cast/staff credits are authoritative over English-dub substitutions.
- `LANG_SYSTEM`: JPN `576KB` overrides auxiliary `544KB`; `サイバーバル` remains unresolved/flagged.
- `LANG_MISSION_ENDTELOP`: shifted auxiliary mission-title mapping rejected.
- `LANG_MYOUTER_STAFF_COMMENT`: JPN `祖母` overrides auxiliary `mother`; source `(不要)` placeholders remain.
- `LANG_MYOUTER_TOP`: source `METAL GEAR ZEK` spelling and unique 159 trailing ASCII whitespace preserved.
- `LANG_MISSION_RESULT`, `LANG_WEAPON_TEXT`, `LANG_MISSION_INFO`: JPN controls/identities/placeholder spacing and repaired boundaries remain authoritative.

## Next resource class
`SLOT_OLANG` — **29 / 144 complete**. Continue the next unstarted small SLOT after checking for newer concurrent mappings.

## Last safe checkpoint
- Safe translation total: **9919 rows / 126 complete file_ids**.
- SLOT_OLANG: **29 / 144 complete; 207 rows**.
- Latest completed artifact: `sol_translation_mappings/SLOT_OLANG/5D3AF992.json`.
- Latest mapping commit: `30846c387ea2606356c90fd534fd6bd8f00767e9`.
- Resume next: **next unstarted small SLOT_OLANG file_id**.
