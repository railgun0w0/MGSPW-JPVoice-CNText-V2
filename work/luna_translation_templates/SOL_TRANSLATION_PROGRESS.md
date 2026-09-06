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

## Totals

- Completed file_ids: 1 / 241
- Completed template rows: 8 / 21041
- YPK_GTT completed: 1 / 36

## Current queue

Continue with small complete YPK_GTT file_ids first, then larger YPK_GTT files. Update this file after each batch/commit.

## Risk / review log

- `1C79F3AD`: `核が撃たれれば鳥たちもたくさん死ぬわ…` translated from JPN as `核弹一旦发射，很多鸟儿也会死……`; did not inherit auxiliary `millions of birds` because JPN does not contain that quantity.
