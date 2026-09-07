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
| Translation work safely persisted | **10087 / 21041 rows** |
| file_ids with complete persisted translation | **138 / 241** |
| YPK_GTT | **36 / 36 complete** |
| OHD | **1 / 1 complete** |
| LOOSE_OLANG | **14 / 14 complete** |
| STAGEDAT_OLANG | **46 / 46 complete** |
| SLOT_OLANG | **41 / 144 complete** |

## Resource-class accounting
- YPK_GTT: **2080 rows / 36 complete file_ids**.
- OHD: **226 rows / 1 complete file_id**.
- LOOSE_OLANG: **1719 rows / 14 complete file_ids**.
- STAGEDAT_OLANG: **5687 rows / 46 complete file_ids**.
- SLOT_OLANG: **375 rows / 41 complete file_ids**.

## STAGEDAT checkpoint
STAGEDAT_OLANG is complete (46 / 46). `LANG_MISSION_INFO` manifest commit: `9738fa4604e7ba659bc9a6fa95b54c95c819590e`.

## Recent SLOT checkpoints
- `5D3AF56D` 5; ruby controls OUT/SPEAR/BARGE/POINT BRAVO/CHRYSALIS and structural spaces preserved. Mapping `8449769c0f65820c61743abbd3fd076643be558e`.
- `5D218EA9` 9; fixed WALKMAN/device labels preserved; no auxiliary-added `<I=○>`. Mapping `1186584e4f4f2ff3278b509ab215957b46029428`.
- `5DA7D876` 10; fixed stage/location labels preserved exactly, including `RlO DEL JADE`. Mapping `54d4d4872010a7dfd2f0b17755e9335de9601254`.
- `5D3B020D` 8; dialogue continuity maintained; significant spaces and GONDOLA ruby preserved. Mapping `554a2e287de5463299698f738193c42e5924d6e1`.
- `5D56AA31` 12; fixed scanner/status JPN labels preserved over auxiliary substitutions. Mapping `bedd25df8614e873e8885ee2723a1b2b80a8d38b`.
- `5D3B060D` 8; current-row JPN restored; BIGBOSS/ZEKE ruby and spaces preserved. Mapping `eb2a3ce096138921c4c5cbd8f5fca319ea3ad322`.
- `5D3AF992` 10; shifted auxiliary rejected; Zadornov search/truck/facility and fixed dramatic lines restored. Mapping `30846c387ea2606356c90fd534fd6bd8f00767e9`.
- `5DA7D875` 8; fixed map/location identities preserved exactly. Mapping `a6b266c24774a61730c2e0b187ff4a84d46fb470`.
- `5D1A33A9` 14; Peace Walker scanner identities preserved exactly. Mapping `1e9c8b72dc23e48c08baada430ec3d69781f33a1`.
- `5D3B01CD` 10; literal triangle button, Peace Walker chase dialogue and Nicaragua/BIGBOSS rubies follow JPN. Mapping `19edae2cd8fe2c4f4b5d2b37b48880df2dc837c3`.
- `5DCE245A` 11; boss/mecha combat lines preserve JPN intensity and system brevity. Mapping `cdfc6947844c33af54eedaf3d422da25b95cbeb9`.
- `5D3B01AD` 11; shifted auxiliary rejected; chase-speed 30 context and client ruby preserved. Mapping `6dcdba566c99ab5b59f3019e1ca43432ec262efa`.
- `5D1A33A7` 16; PUPA scanner identities preserved exactly. Mapping `d1679bbcabfd397ab0b250c852fc0ce2916b1aea`.
- `5D1A33A6` 17; CHRYSALIS scanner identities and exact single-space placeholder preserved. Mapping `6dff8038be07de0934b721e9838289a1c1d45a16`.
- `5D3AFD6D` 9; platform/cerebral-AI and horse dialogue, ruby argument spaces, MAMMAL POD/THE BOSS/ANDALUSIAN readings and trailing whitespace preserved. Mapping `62929e6387c0412477f2746ee1c3799645cc1091`.
- `5D3AF60D` 12; auxiliary shifted/merged lines rejected; ideographic-space placeholder, HOMBRE NUEVO/COMPA/VENCEREMOS ruby controls and final trailing ASCII space preserved. Mapping `640f731cf2c2f3518ac72a31c984e5dd062503c1`.
- `5D1A33A8` 27; COCOON scanner identities and component/attribute labels preserved exactly. Mapping `5180e1e91a506cb4993adb15a175e4bd27400f93`.
- `5D1A33AA` 14; reused Peace Walker scanner identity table preserved exactly. Mapping `c6ce0f06910f82929f9b0aad85d75d6e5459b8d2`.
- `5D9A9677` — **19 rows complete**. Fixed HUD/aim/status labels remain exactly JPN (`LOCKED ON`, `AUTO AIM`, `NO USE`, `RELOAD`, `SYNCING...`, `IN SYNC`, etc.); auxiliary `N/A` and `RELOADING` substitutions were rejected. Mapping commit `e1f8f36bcff2786b12f4160d659ffccd25a16825`.

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
`SLOT_OLANG` — **41 / 144 complete**. Continue the next unstarted small SLOT after checking for newer concurrent mappings.

## Last safe checkpoint
- Safe translation total: **10087 rows / 138 complete file_ids**.
- SLOT_OLANG: **41 / 144 complete; 375 rows**.
- Latest completed artifact: `sol_translation_mappings/SLOT_OLANG/5D9A9677.json`.
- Latest mapping commit: `e1f8f36bcff2786b12f4160d659ffccd25a16825`.
- Resume next: **next unstarted small SLOT_OLANG file_id**.
