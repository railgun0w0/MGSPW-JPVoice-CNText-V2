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
| Translation work safely persisted | **10264 / 21041 rows** |
| file_ids with complete persisted translation | **150 / 241** |
| YPK_GTT | **36 / 36 complete** |
| OHD | **1 / 1 complete** |
| LOOSE_OLANG | **14 / 14 complete** |
| STAGEDAT_OLANG | **46 / 46 complete** |
| SLOT_OLANG | **53 / 144 complete** |

## Resource-class accounting
- YPK_GTT: **2080 rows / 36 complete file_ids**.
- OHD: **226 rows / 1 complete file_id**.
- LOOSE_OLANG: **1719 rows / 14 complete file_ids**.
- STAGEDAT_OLANG: **5687 rows / 46 complete file_ids**.
- SLOT_OLANG: **552 rows / 53 complete file_ids**.

## STAGEDAT checkpoint
STAGEDAT_OLANG is complete (46 / 46). `LANG_MISSION_INFO` manifest commit: `9738fa4604e7ba659bc9a6fa95b54c95c819590e`.

## Recent SLOT checkpoints
- `5D3AF56D` 5; ruby controls OUT/SPEAR/BARGE/POINT BRAVO/CHRYSALIS and structural spaces preserved. Mapping `8449769c0f65820c61743abbd3fd076643be558e`.
- `5D218EA9` 9; fixed WALKMAN/device labels preserved; no auxiliary-added `<I=○>`. Mapping `1186584e4f4f5ed9fbabd6f9bf60a094a`.
- `5D3AF98D` 15; shifted truck/nuclear-warhead sequence, rubies and whitespace restored from JPN. Mapping `ed5c716b86406fb3778345cb708e34b59b84c5bb`.
- `5D3B3A9A` 17; control-tutorial separators and CQC hierarchy preserved. Mapping `d0e3e9f7ce4416883749fc68d39d2ec19381bac6`.
- `5D1B7B4B` 18; vocalizations and omitted production/variant notes restored. Mapping `dd15c154b2650d2ebd6a7d27c454b54ec0b0d826`.
- `5D3AFD4D` 15; soldier-spirit/loyalty/mission dialogue fragments and ruby/space structure preserved. Mapping `7eb920e7910813370c13fe019a6c081a7fa2c97f`.
- `5D2B7C21` 5; highly reused result/time labels preserve `YOU WON`, `YOU LOSE`, `CONTROL`, `TIME PENALTY -$1sec`, `TIME EXTEND +$1sec`; auxiliary normalization rejected. Mapping `a825a9fbc8187d5f63dcb5089a5ac52098bb8362`.
- `5DA7D879` 11; Costa Rica mine-base map identities preserved; JPN `AI WEAPON HANGAR` overrides auxiliary `PEACE WALKER HANGAR`. Mapping `6d48ddf91b9cd859856bd9ee035baab43e116a1d`.
- `5D3B010D` 21; interrogation/self-reproach dialogue restored from current JPN where auxiliary is heavily shifted; THE BOSS ruby, internal/fullwidth/trailing spaces, ellipsis/exclamation structure and abort/power-failure tail remain authoritative. Mapping `dbd75578b8192d7cbcc6dcb7f926755e03d78637`.
- `5DB85CF0` — **18 rows complete**. Staff-discharge UI follows current JPN: `NEW COMER` is preserved over auxiliary `NEW RECRUITS`; `%d` then `%2d` format-specifier order, both embedded newlines, zero-staff warning and discharge confirmation semantics remain intact. Mapping commit `156f56bc3b7c591cf3b92c593c2a544a5c6fbc25`.

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
`SLOT_OLANG` — **53 / 144 complete**. Continue the next unstarted small SLOT after checking for newer concurrent mappings.

## Last safe checkpoint
- Safe translation total: **10264 rows / 150 complete file_ids**.
- SLOT_OLANG: **53 / 144 complete; 552 rows**.
- Latest completed artifact: `sol_translation_mappings/SLOT_OLANG/5DB85CF0.json`.
- Latest mapping commit: `156f56bc3b7c591cf3b92c593c2a544a5c6fbc25`.
- Resume next: **next unstarted small SLOT_OLANG file_id**.
