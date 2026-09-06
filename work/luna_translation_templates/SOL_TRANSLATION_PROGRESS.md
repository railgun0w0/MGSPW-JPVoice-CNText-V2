# Sol Translation Progress

Branch: `sol-translation`

Purpose: durable checkpoint for translation work under `work/luna_translation_templates/` so work can resume safely across chat turns.

## Rules

- JPN is the sole semantic and structural authority.
- MLG_CN / ENG are auxiliary evidence only; never force positional or semantic alignment when they conflict with JPN.
- Preserve markup, controls, indices/references, ordering, timing and resource identity.
- Translation work stays under `work/luna_translation_templates/` and `work/luna_translation_templates/sol_translation_mappings/`.
- Do not modify formal `translations/`, compiled manifest, DAT/KEY, or run a production build from this branch checkpoint.
- Use pending-review semantics; never mark a translation `APPROVED` merely because Sol produced it.
- Large files are persisted as complete per-file JSON mappings, sharded when needed, before any mechanical CSV merge.

## Current totals

| Metric | Progress |
|---|---:|
| Total template file_ids | 241 |
| Total template rows | 21041 |
| Translation work safely persisted | **2310 / 21041 rows** |
| file_ids with complete persisted translation | **38 / 241** |
| YPK_GTT | **36 / 36 complete** |
| OHD | **1 / 1 complete** |
| LOOSE_OLANG | **1 / 14 complete** |
| STAGEDAT_OLANG | 0 / 46 |
| SLOT_OLANG | 0 / 144 |

### YPK_GTT accounting

- 21 file_ids / 491 rows are already merged into the 28-column Luna CSVs.
- 15 file_ids / 1589 rows are fully translated and safely persisted as mappings pending mechanical CSV merge.
- Total YPK_GTT translated: **2080 rows, 36/36 file_ids**.

### OHD accounting

- `1E4C1146`: **226 / 226 rows translated**, stored in four contiguous shards plus manifest.
- Manifest: `sol_translation_mappings/OHD/1E4C1146.manifest.json`
- Manifest commit: `009ad3c14e8dc24e8afc821ade0f82fdd04f70a5`
- Shards: 0-56 / 57-113 / 114-169 / 170-225.
- Longest Chinese text in the mapping is 36 UTF-8 bytes versus fixed 128-byte OHD records; final builder validation remains authoritative.

### LOOSE_OLANG accounting

- `00327F6A`: **4 / 4 rows translated**, mapping commit `cdb82257ba1ca12be52458645ee5d80b62c48d02`.
- Mapping: `sol_translation_mappings/LOOSE_OLANG/00327F6A.json`
- 13 LOOSE_OLANG file_ids remain.

## Completed merged YPK_GTT CSVs

`1C79F3AD`, `1C79F36D`, `1C79F2ED`, `1C79F3ED`, `1C7CF2AD`, `1C7B736D`, `1C7AF2AD`, `1C7AF2ED`, `1C7B73AD`, `1C7BF36D`, `1C7A73AD`, `1C7AF3AD`, `1C7C72AD`, `1C7BF2AD`, `1C7C73AD`, `1C7B72AD`, `1C7CF3AD`, `1C7CF2ED`, `1C7C736D`, `1C7BF2ED`, `1C7B72ED`.

## Persisted YPK_GTT mappings pending CSV merge

| file_id | Rows | Mapping / manifest commit |
|---|---:|---|
| `1C79F42D` | 80 | `1adb7231a2d7048de526a4b821ea1a94865e7180` |
| `1C79F46D` | 93 | `066f4c34feb13b46a68682977d767775b6884e70` |
| `1C7C72ED` | 47 | `f526465d7fc048b50b5a2b35126363bb52201abf` |
| `1C7BF3AD` | 51 | `47ba816d04f738f68d1073efe7cb863d225e0712` |
| `1C7BF32D` | 54 | `cc777507a8274fdb7df2a48cba5d28776db70121` |
| `1C7AF36D` | 30 | `07ec8216860c2fc880c0a89d6e39b7de4fdf981f` |
| `1C7A72AD` | 35 | `7847679a99b52ae1d341a8f10ff47296f173ed64` |
| `1C7A73ED` | 79 | `38f88b028fd279bb668c5fd1e95daf8d42a79807` |
| `1CC276E9` | 88 | `1a7979e8b8dba516d5be59133db5cf56d7d71efd` |
| `1C7A736D` | 93 | `5e10d9ff1e2fdb462029deff67dab07eebdd21f1` |
| `1C677327` | 100 | `667677e5f2ff74fc287c431067ebd75c1117bae0` |
| `1C79F2AD` | 110 | `14f3dfdd86aa19d0364692758d87f4d48fec58b8` |
| `1C7A72ED` | 115 | `d08bc35ec5303404242f1a705063cea067cb42f8` |
| `1C0FB26B` | 268 | manifest `3205e260b263389abfd88284056d48582137fe13` |
| `1C7679A5` | 346 | manifest `41c7d637f8893fdedd83974e0fd4a37a6c54ff7e` |

## Current queue

Continue LOOSE_OLANG by ascending row count:

1. `00C6A046` — 8 rows
2. `0060E2F2` — 19 rows
3. `0043DA6E` — 21 rows
4. `00C79B17` — 26 rows
5. `0005EE2F` — 31 rows
6. `00D345A5` — 41 rows
7. `0072F326` — 42 rows
8. `00225520` — 54 rows
9. `0066E64E` — 66 rows
10. `00D0C740` — 68 rows
11. `00CB1FB7` — 106 rows
12. `005184E3` — 139 rows
13. `007E2F18` — 1094 rows

After LOOSE_OLANG, continue STAGEDAT_OLANG then SLOT_OLANG unless a resource-specific structural problem justifies changing order.

## Important review / risk notes

- YPK_GTT auxiliary references are sometimes shifted or semantically over-expanded. JPN always wins. Known examples include bird-count `millions`, boathouse/FSLN-hut mismatch, gun-seat vs sniper mismatch, squirrel vs rabbit localization, railgun/Human Slingshot shifted blocks, and several combined/split auxiliary sentences.
- Keep `無力化` distinct from lethal `破壊/殲滅` where gameplay meaning requires it.
- Existing normalized ruby/readings include `COMPA`, `LAB`, `ZEKE`, `ELUDE`, `SNEAKING MISSION`, `MAP`, `OPTIONS`; preserve structural markup exactly during merge.
- `1C0FB26B` is a generic Extra Ops library; its 268-row mapping is sharded 4 ways and complete.
- `1C7679A5` is the generic mission/CO-OPS/support/costume library; its 346-row mapping is sharded 6 ways and complete. `人間パチン虎。` is provisionally `人间弹弓虎。` and remains terminology-review material.
- OHD `1E4C1146` uses fixed 128-byte records and exact page/record auxiliary mapping. Several auxiliary texts were nevertheless semantically wrong and were corrected from JPN: `すまなかった` -> `抱歉`, `異常なし` -> `无异常`, `ターゲット捕捉` -> `锁定目标`, `合体` -> `合体`, `避けろ` -> `躲开`, `突っ込むぞ` -> `冲进去`, `好きになれん` -> `喜欢不起来`.
- OHD stylized Latin strings `GO! GO! GO!`, `VIC BOSS!`, `VIC VOS!` are intentionally preserved.
- LOOSE_OLANG `00327F6A` has two empty auxiliary rows and one row whose purported `mlg_cn_reference` is actually English Xbox LIVE text; all three were translated directly from JPN. `HOST` and `TRADE` are preserved as interface terms in this pass.

## Last safe checkpoint

- Latest completed translation mapping: `LOOSE_OLANG/00327F6A.json`
- Commit: `cdb82257ba1ca12be52458645ee5d80b62c48d02`
- Safe translation total: **2310 rows / 38 file_ids**.
- Resume next at: **LOOSE_OLANG `00C6A046`**.
