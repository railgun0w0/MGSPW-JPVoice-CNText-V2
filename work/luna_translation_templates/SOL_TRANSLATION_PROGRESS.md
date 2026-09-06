# Sol Translation Progress

Branch: `sol-translation`

Purpose: durable checkpoint for translation work under `work/luna_translation_templates/` so work can resume safely across chat turns.

## Rules

- JPN is the sole semantic and structural authority.
- MLG_CN / ENG are auxiliary evidence only; never force positional or semantic alignment when they conflict with JPN.
- Preserve markup, controls, runtime placeholders, indices/references, ordering, timing and resource identity.
- Translation work stays under `work/luna_translation_templates/` and `work/luna_translation_templates/sol_translation_mappings/`.
- Do not modify formal `translations/`, compiled manifest, DAT/KEY, or run a production build from this branch checkpoint.
- Use pending-review semantics; never mark a translation `APPROVED` merely because Sol produced it.
- Large files are persisted as complete per-file JSON mappings, sharded when needed, before any mechanical CSV merge.

## Current totals

| Metric | Progress |
|---|---:|
| Total template file_ids | 241 |
| Total template rows | 21041 |
| Translation work safely persisted | **2498 / 21041 rows** |
| file_ids with complete persisted translation | **45 / 241** |
| YPK_GTT | **36 / 36 complete** |
| OHD | **1 / 1 complete** |
| LOOSE_OLANG | **8 / 14 complete** |
| STAGEDAT_OLANG | 0 / 46 |
| SLOT_OLANG | 0 / 144 |

## Completed resource accounting

### YPK_GTT
- **2080 rows / 36 file_ids complete**.
- 21 file_ids / 491 rows are already merged into the 28-column Luna CSVs.
- 15 file_ids / 1589 rows are fully translated and persisted as mappings pending mechanical CSV merge.
- Large complete manifests: `1C0FB26B` (268 rows, 4 shards, manifest commit `3205e260b263389abfd88284056d48582137fe13`) and `1C7679A5` (346 rows, 6 shards, manifest commit `41c7d637f8893fdedd83974e0fd4a37a6c54ff7e`).

### OHD
- `1E4C1146`: **226 / 226 rows complete**, four shards + manifest.
- Manifest commit: `009ad3c14e8dc24e8afc821ade0f82fdd04f70a5`.
- Fixed 128-byte records; longest CN mapping 36 UTF-8 bytes. Final builder validation remains authoritative.

### LOOSE_OLANG completed

| file_id | Rows | Commit / manifest | Notes |
|---|---:|---|---|
| `00327F6A` | 4 | `cdb82257ba1ca12be52458645ee5d80b62c48d02` | old-save / TRADE / HOST prompts; English masquerading as CN aux rejected |
| `00C6A046` | 8 | `41778032c63e89a53943f158c0fbc03f0e6e3b6b` | save/system-data prompts; identifiers preserved |
| `0060E2F2` | 19 | `cf2385956d482e425012f4924e119eefa293da0d` | VERSUS OPS search/voice-chat UI |
| `0043DA6E` | 21 | `3ce04cd2bdfca96f0235dc95aff7d800c910a463` | Xbox LIVE / gamer-profile / storage/network errors |
| `00C79B17` | 26 | `234bf8e873d048888e6a5dd0ff35e145fe6ed52c` | rescue/location + old control tutorial; aux-added roll results rejected |
| `0005EE2F` | 31 | `0485204e4b23132537f135b968619ca085b0bace` | data management / magazines / dialect & AI voice settings |
| `00D345A5` | 41 | manifest `55c4d109288c7f81d6b788fbdbc86ae03c2a4db4` | item/weapon/magazine descriptions; two shards |
| `0072F326` | 42 | `f3b5f5efdcb40822381d95a1dcf18d5b209ce4a5` | save/storage/online/control-type prompts; `<I=REG>` and `[lack_strage_*]` placeholders preserved |

## Current queue

Continue remaining LOOSE_OLANG by ascending row count:

1. `00225520` — 54 rows
2. `0066E64E` — 66 rows
3. `00D0C740` — 68 rows
4. `00CB1FB7` — 106 rows
5. `005184E3` — 139 rows
6. `007E2F18` — 1094 rows

After LOOSE_OLANG, continue STAGEDAT_OLANG then SLOT_OLANG unless a resource-specific structural problem justifies changing order.

## Important review / risk notes

- JPN always wins over shifted/combined/over-expanded MLG_CN or ENG auxiliary text.
- Keep `無力化` distinct from lethal `破壊/殲滅` where gameplay meaning requires it.
- Existing normalized ruby/readings include `COMPA`, `LAB`, `ZEKE`, `ELUDE`, `SNEAKING MISSION`, `MAP`, `OPTIONS`; preserve structural markup exactly during merge.
- OHD corrected several auxiliary semantic errors directly from JPN, including `すまなかった`, `異常なし`, `ターゲット捕捉`, `合体`, `避けろ`, `突っ込むぞ`, `好きになれん`.
- OHD stylized Latin strings `GO! GO! GO!`, `VIC BOSS!`, `VIC VOS!` are intentionally preserved.
- `00C79B17`: auxiliary adds “roll” outcomes not explicitly present in its JPN tutorial rows; those additions were rejected. Literal `(X)` / `RB` tutorial text is preserved where present.
- `0005EE2F`: old auxiliary omitted magazine-data semantics from combined data-management descriptions; restored from JPN. Arakawa magazine titles and dialect labels remain reviewable terminology.
- `00D345A5`: analyzer auxiliary candidates included unrelated `<I=STA>` behavior; rejected. Monster Hunter descriptions and long weapon descriptions follow JPN. Controls `<I=CPY>`, `<I=×>`, `<I=ATK>`, `<I=△>` preserved.
- `0072F326`: auxiliary sometimes substitutes generic game-data wording for JPN system-data wording. JPN wording was restored. JPN `モンスターハンターポータブル<I=REG>` remains Portable semantics with `<I=REG>`; auxiliary English-localization `FREEDOM<I=TM>` was rejected. Runtime placeholders `[lack_strage_system_capacity]` and `[lack_strage_save_capacity]` are preserved exactly.

## Last safe checkpoint

- Latest completed mapping: `sol_translation_mappings/LOOSE_OLANG/0072F326.json`
- Commit: `f3b5f5efdcb40822381d95a1dcf18d5b209ce4a5`
- Safe translation total: **2498 rows / 45 file_ids**.
- Resume next at: **LOOSE_OLANG `00225520`**.
