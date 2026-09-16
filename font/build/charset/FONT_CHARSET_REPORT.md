# MGSPW production FONT charset report

Status: **PASS** (deterministic census; selector split remains intentionally unresolved)

## Scope

- Old five-class compiled production objects: `build/translation/compiled_translation_manifest.csv`, **91,609** rows.
- `BRIEFING_NBE`: `translations/briefing/*.csv`, **469** files / **5,645** physical rows.
- Total production text rows scanned: **97,254**.
- Aggregate source identity SHA256: `0538f62774d749a7a30a0d6f3f399cf909bdd2412f6b054dfc81062def03caa1`.
- Excluded: historical experiments, backups, fixtures, reference translations, JPN/ENG/MLG_CN auxiliary text, templates, worklists, documentation, and package/readiness duplicates.
- Old five-class mappings are represented exactly once through their current object-level compiled manifest; `BRIEFING_NBE` is represented exactly once through its physical production CSV rows.

## Counts

- Total display-relevant Unicode codepoint occurrences: **1,253,865**.
- Unique codepoints: **2,904**.
- Rows containing only stripped control/layout syntax: **28**.

| category | unique codepoints | occurrences |
|---|---:|---:|
| Han | 2,721 | 784,082 |
| ASCII (including U+0020 layout space) | 91 | 327,941 |
| Unicode decimal digits | 17 | 36,373 |
| Latin | 72 | 242,963 |
| Kana | 16 | 1,011 |
| Chinese punctuation policy set | 21 | 128,667 |
| Japanese/fullwidth punctuation policy set | 21 | 107,382 |
| All Unicode punctuation | 52 | 152,350 |
| Unicode symbols | 24 | 2,299 |
| Characters above U+FFFF | 0 | 0 |

The policy-set rows overlap by design: for example `。` is relevant to both Chinese and Japanese punctuation review. `is_punctuation` in the CSV is the Unicode general-category result.

## Resource-class coverage

| resource class | physical production rows |
|---|---:|
| LOOSE_OLANG | 2,963 |
| OHD | 904 |
| SLOT_OLANG | 68,684 |
| STAGEDAT_OLANG | 16,922 |
| YPK_GTT | 2,136 |
| BRIEFING_NBE | 5,645 |

## Control and visibility rules

- `<R=base,reading>` contributes `base` and `reading`, because both payloads can render; Ruby delimiters and separators do not enter the charset.
- `<I=...>`, `<C=...>`, `<->`, named runtime angle controls, `$NAME`, printf placeholders, escaped/physical CR-LF-tab, and Unicode control/format characters are removed.
- Human-readable angle-bracket titles remain text, matching the production compiler's control classification.
- U+0020/U+00A0/U+3000 are retained as render-relevant layout glyphs; other separator controls are excluded.
- No resource control bytes or CSV metadata columns are decoded as text.

## Selector requirement

Every row currently uses `UNKNOWN / UNION_REQUIRED`. The corpus does not provide a fully proven large/small selector assignment, so Phase 1 deliberately builds and simulates the complete union instead of guessing.

## Output contract

- `font_charset.txt`: ascending-codepoint literal union charset.
- `font_charset.csv`: per-codepoint count, resource classes, Unicode metadata, flags, and selector requirement.
