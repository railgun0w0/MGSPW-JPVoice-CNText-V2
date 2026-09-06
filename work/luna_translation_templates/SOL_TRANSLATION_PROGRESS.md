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
| YPK_GTT | `1C79F36D` | 22 | `44bd91ff8ad6d424b58b23610a4d51d7501adf9f` | Full file translated; multiple NO_RELIABLE_GTT_MAPPING rows translated from JPN/context. Ruby `<R=父さん,ミ・ビエホ>` converted to `<R=老爸,MI VIEJO>`. |
| YPK_GTT | `1C79F2ED` | 39 | `4441e4ddb97a89ceee9f4a6a7b4220d5fa63e10b` | Full file translated; many unreliable mappings handled from JPN/context; ruby converted to Chinese display text + Latin readings. |
| YPK_GTT | `1C79F3ED` | 46 | `f5d2b02baace9ab133ccf983ae15cc65d95adb56` | Full file translated; training terminology normalized; ruby/control structure preserved. |
| YPK_GTT | `1C7CF2AD` | 3 | `436145406a5ae0a82eb4d06e5dc8d400fdf5b914` | Armored-vehicle objective lines. |
| YPK_GTT | `1C7B736D` | 8 | `6e18e18e16d65eff96b501864d66c1b1cd8ec3f4` | Alert-door / Peace Walker hangar guidance; unreliable rows translated from JPN. |
| YPK_GTT | `1C7AF2AD` | 11 | `776b16b943937f5f94e9cc8088469623b5728ce1` | Compound infiltration/tutorial; visibly shifted cardboard-box/ESEARCH auxiliary refs ignored. |
| YPK_GTT | `1C7AF2ED` | 13 | `fd799bef10756ac58f83470ebb8340867a5cbde1` | Train/Basilisco/neutralization/plant lines; reused established botanical/ruby terminology consistently. |
| YPK_GTT | `1C7B73AD` | 17 | `c7915f47641632c576cb2db5d587732b42261096` | Bridge/control-tower/chaff guidance; contradictory launcher auxiliary wording ignored. |
| YPK_GTT | `1C7BF36D` | 17 | `7aeda6078d24489f41ab07460497f7355ceb0996` | Shutter button tutorial and Peace Walker hangar approach; `<I=ACT>` preserved. |
| YPK_GTT | `1C7A73AD` | 21 | `8bc6f3816abfe4ebd4dd30c5d026e8ed1896b240` | Dock/control-tower approach and chaff guidance; bird-count auxiliary over-expansion not copied; NICA ruby preserved as Chinese display + Latin reading. |

## Persisted translations pending mechanical CSV merge

| Resource class | file_id | Rows | Mapping commit | Mapping path | Notes |
|---|---:|---:|---|---|---|
| YPK_GTT | `1C79F42D` | 80 | `1adb7231a2d7048de526a4b821ea1a94865e7180` | `sol_translation_mappings/YPK_GTT/1C79F42D.json` | Full file translated; Monster Hunter crossover; shifted auxiliary mappings ignored and review flags retained. |
| YPK_GTT | `1C79F46D` | 93 | `066f4c34feb13b46a68682977d767775b6884e70` | `sol_translation_mappings/YPK_GTT/1C79F46D.json` | Full file translated; AI corruption/test phrases, station names, corrupted pi, MGS2 gibberish and late AI dialogue preserved from JPN. |

## Totals

- Completed merged file_ids: 11 / 241
- Completed merged template rows: 205 / 21041
- Persisted pending-merge file_ids: 2
- Persisted pending-merge rows: 173
- Total translation work safely persisted: 378 rows
- YPK_GTT translation coverage: 13 / 36 (11 merged + 2 pending merge)

## Current queue

Continue unprocessed YPK_GTT resources by ascending manageable size. Next candidates: `1C7AF3AD`, `1C7C72AD`, `1C7BF2AD`, `1C7C73AD`, then other small/medium files. Large files use complete-file JSON mapping before merge.

## Risk / review log

- `1C79F3AD`: did not inherit auxiliary `millions of birds`; JPN only says many birds would die.
- `1C79F36D`: `エルード` rendered semantically as grabbing/hanging from an edge; review final gameplay terminology globally.
- `1C79F2ED`: `绞刑台镇` / `大叶蚁塔` follow attached MLG terminology; review against eventual global glossary.
- `1C79F3ED`: `ほぼそうだ` rendered `八九不离十`, not auxiliary `毫无疑问`.
- `1C79F42D`: shifted Monster Hunter refs ignored; `耐性` kept as `抗性`, not `免疫`; bullfighter over-expansion not copied; review flags persisted for SOMOZA/Cecile/cat speech/Stun Rod/catchphrase/onomatopoeia.
- `1C79F46D`: corrupted numeric strings and station-name/test speech preserved literally; unrelated auxiliary pi text ignored; MGS2 gibberish `我要剪刀！` / `61！` preserved; lore terms and `REPTILE` flagged for terminology review.
- `1C7AF2AD`: auxiliary refs on `ダンボール？` / `何に使うんだ？` are shifted to later ESEARCH tutorial lines; JPN-only translations used.
- `1C7B73AD`: auxiliary says launcher is “Great, just what we need” while JPN says it is troublesome; JPN negative meaning used.
- `1C7A73AD`: repeated `核が撃たれれば鳥たちもたくさん死ぬわ…` again translated as many birds dying; did not copy auxiliary `millions` quantity absent from JPN.
