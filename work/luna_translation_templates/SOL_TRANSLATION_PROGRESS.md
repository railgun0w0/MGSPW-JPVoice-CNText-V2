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

## Completed

| Resource class | file_id | Rows | Commit | Notes |
|---|---:|---:|---|---|
| YPK_GTT | `1C79F3AD` | 8 | `573836a53c3adad52c28a0e85572b4b6f4f98fd6` | Full file translated; two rows had no reliable auxiliary mapping and were translated from JPN/context only. Existing MLG/ENG over-expansion on bird count was not copied. |
| YPK_GTT | `1C79F36D` | 22 | `44bd91ff8ad6d424b58b23610a4d51d7501adf9f` | Full file translated; multiple NO_RELIABLE_GTT_MAPPING rows translated from JPN/context. Ruby `<R=父さん,ミ・ビエホ>` converted to `<R=老爸,MI VIEJO>` while preserving control structure. |

## Totals

- Completed file_ids: 2 / 241
- Completed template rows: 30 / 21041
- YPK_GTT completed: 2 / 36

## Current queue

Continue with small complete YPK_GTT file_ids first, then larger YPK_GTT files. Next target: `1C79F2ED` unless a smaller unprocessed complete file is identified.

## Risk / review log

- `1C79F3AD`: `核が撃たれれば鳥たちもたくさん死ぬわ…` translated from JPN as `核弹一旦发射，很多鸟儿也会死……`; did not inherit auxiliary `millions of birds` because JPN does not contain that quantity.
- `1C79F36D`: rows with `エルード` translated semantically as grabbing/hanging from an edge (`抓住边缘` / `抓边`) rather than blindly copying auxiliary `荡过去`; review against final in-game terminology later.
- `1C79F36D`: `cn_utf8_bytes` may be slightly larger than JPN bytes on a small number of rows; this is not itself proof of overflow because YPK uses record/alignment capacity. Local capacity validator must decide before approval/build.
