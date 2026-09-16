# Clean JPN 001c selector-specific charset report

Status: **PASS** (selector-specific corpus; not a project-wide union).

## Scope

- Current compiled production source: `build/translation/compiled_translation_manifest.csv`.
- Selected proven corpus: `LOOSE_OLANG/00D0C740`; **68** production rows.
- Corpus identity SHA256: `62efb908e49a8b8a925273dde0bc84e6960826a442d4ee1deb4484321ac1906d`.
- `00D0C740` is proven to use 001c for the Loading path; whether it is the only 001c text source remains UNKNOWN.
- Historical experiments, backups, JPN/ENG/MLG_CN references, templates, worklists, documentation, and all non-proven selector groups are excluded.

## Counts

- Total visible Unicode codepoint occurrences: **1,593**.
- Unique codepoints: **441**.
- Unique Han: **398**.
- Rows empty after control stripping: **0**.

| category | unique codepoints | occurrences |
|---|---:|---:|
| Han | 398 | 1,125 |
| ASCII (including U+0020 layout space) | 31 | 283 |
| Unicode decimal digits | 2 | 2 |
| Latin | 26 | 251 |
| Kana | 0 | 0 |
| Chinese punctuation policy set | 12 | 185 |
| Japanese/fullwidth punctuation policy set | 8 | 143 |
| All Unicode punctuation | 13 | 187 |
| Unicode symbols | 1 | 1 |
| Characters above U+FFFF | 0 | 0 |

Han in this selector-specific corpus is always an SC-source candidate and is never retained from clean JPN Han records.
