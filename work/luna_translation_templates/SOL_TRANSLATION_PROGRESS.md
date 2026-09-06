# Sol Translation Progress

Branch: `sol-translation`

Purpose: track translation progress for `work/luna_translation_templates/` so work can resume safely across chat turns.

## Rules

- JPN is the sole semantic authority.
- MLG_CN / ENG are auxiliary evidence only; do not trust ordinal alignment blindly.
- Preserve structure, markup, control tokens, indices, references, timing and metadata.
- Write translations only to `cn_text` plus mechanical translation/QC fields allowed by `TRANSLATION_GUIDE.md`.
- Keep `build_status=NOT_BUILT` and `ingame_status=NOT_TESTED`.
- Use `TRANSLATED_PENDING_REVIEW`, never `APPROVED`.
- Do not build DAT/KEY or touch formal `translations/` / manifest.
- For large CSVs where connector writes require full-file replacement, persist a per-file translation mapping first before mechanical merge so completed translation work cannot be lost.

## Completed (merged into 28-column CSV)

| Resource class | file_id | Rows | Commit | Notes |
|---|---:|---:|---|---|
| YPK_GTT | `1C79F3AD` | 8 | `573836a53c3adad52c28a0e85572b4b6f4f98fd6` | Full file translated; two rows had no reliable auxiliary mapping and were translated from JPN/context only. Existing MLG/ENG over-expansion on bird count was not copied. |
| YPK_GTT | `1C79F36D` | 22 | `44bd91ff8ad6d424b58b23610a4d51d7501adf9f` | Full file translated; multiple NO_RELIABLE_GTT_MAPPING rows translated from JPN/context. Ruby `<R=父さん,ミ・ビエホ>` converted to `<R=老爸,MI VIEJO>` while preserving control structure. |
| YPK_GTT | `1C79F2ED` | 39 | `4441e4ddb97a89ceee9f4a6a7b4220d5fa63e10b` | Full file translated. Early section had many NO_RELIABLE_GTT_MAPPING rows; translated from JPN/context. Ruby converted to Chinese display text + Latin readings (`SNIPER`, `SNIPE`, `TERMINAL`, `CAFETAL`, `SOMBRILLA DE POBRE`, `CHAMPA`). |
| YPK_GTT | `1C79F3ED` | 46 | `f5d2b02baace9ab133ccf983ae15cc65d95adb56` | Full file translated. Training terminology normalized (`训练间`, `目标`, `计时挑战`); ruby converted to Chinese display text + Latin readings (`KILL HOUSE`, `POP-UP`, `TARGET`, `LOS`, `HOLD UP`). |

## Persisted translations pending mechanical CSV merge

| Resource class | file_id | Rows | Mapping commit | Mapping path | Notes |
|---|---:|---:|---|---|---|
| YPK_GTT | `1C79F42D` | 80 | `1adb7231a2d7048de526a4b821ea1a94865e7180` | `sol_translation_mappings/YPK_GTT/1C79F42D.json` | Full file translated; Monster Hunter crossover; shifted auxiliary mappings ignored and review flags retained. |
| YPK_GTT | `1C79F46D` | 93 | `066f4c34feb13b46a68682977d767775b6884e70` | `sol_translation_mappings/YPK_GTT/1C79F46D.json` | Full file translated. Deliberate AI corruption/test phrases, station names, corrupted pi, MGS2 gibberish and late AI dialogue preserved from JPN rather than repaired from auxiliary references. |

## Totals

- Completed merged file_ids: 4 / 241
- Completed merged template rows: 115 / 21041
- Persisted pending-merge file_ids: 2
- Persisted pending-merge rows: 173
- Total translation work safely persisted: 288 rows
- YPK_GTT translation coverage: 6 / 36 (4 merged + 2 pending merge)

## Current queue

Continue remaining YPK_GTT resources. For larger files, translate complete file -> persist JSON mapping -> mechanically merge later. Next: choose another unprocessed YPK_GTT resource; prioritize manageable complete files before very large resources.

## Risk / review log

- `1C79F3AD`: `核が撃たれれば鳥たちもたくさん死ぬわ…` translated from JPN as `核弹一旦发射，很多鸟儿也会死……`; did not inherit auxiliary `millions of birds` because JPN does not contain that quantity.
- `1C79F36D`: rows with `エルード` translated semantically as grabbing/hanging from an edge (`抓住边缘` / `抓边`) rather than blindly copying auxiliary `荡过去`; review against final in-game terminology later.
- `1C79F36D`: `cn_utf8_bytes` may be slightly larger than JPN bytes on a small number of rows; this is not itself proof of overflow because YPK uses record/alignment capacity. Local capacity validator must decide before approval/build.
- `1C79F2ED`: used `绞刑台镇` for `エル・カダルソ` based on attached MLG_CN terminology; keep as terminology-review item if a project-wide glossary later chooses transliteration instead.
- `1C79F2ED`: `グンネラ・インシグニス` rendered as `大叶蚁塔` following attached MLG_CN terminology; botanical/common-name consistency should be checked globally later.
- `1C79F3ED`: `ほぼそうだ` translated as `八九不离十` rather than auxiliary `毫无疑问`, preserving JPN uncertainty level.
- `1C79F42D`: some MLG/ENG candidates are visibly shifted (especially early Monster Hunter crossover lines); ignored when JPN/context disagree.
- `1C79F42D`: preserved JPN distinction `耐性` as `抗性`, not auxiliary `免疫`.
- `1C79F42D`: did not inherit auxiliary bullfighter metaphor for `猪突猛進`; JPN-only translation persisted.
- `1C79F42D`: review flags persisted for `SOMOZA`, `Cecile`, cat-speech style, Stun Rod terminology, Monster Hunter catchphrase, and onomatopoeia.
- `1C79F46D`: preserved JPN's corrupted numeric strings literally; did not replace `3.2546373469888888…` with mismatching auxiliary digits.
- `1C79F46D`: station-name strings were treated as intentional AI/test speech, not replaced by unrelated auxiliary pi text.
- `1C79F46D`: MGS2-style gibberish (`要ハサミだ`, `61！`) preserved as `我要剪刀！`, `61！`; attached references are visibly shifted and ignored.
- `1C79F46D`: canonical-lore wording (`绝对之敌`, `相对之敌`, `贤者们`, `Cobra部队`) and `REPTILE` are flagged for global terminology review, not silently normalized.
