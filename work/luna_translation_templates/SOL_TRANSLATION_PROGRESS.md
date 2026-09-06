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
| Translation work safely persisted | **2931 / 21041 rows** |
| file_ids with complete persisted translation | **50 / 241** |
| YPK_GTT | **36 / 36 complete** |
| OHD | **1 / 1 complete** |
| LOOSE_OLANG | **13 / 14 complete** |
| STAGEDAT_OLANG | 0 / 46 |
| SLOT_OLANG | 0 / 144 |

## Completed resource accounting

### YPK_GTT
- **2080 rows / 36 file_ids complete**.
- 21 file_ids / 491 rows already merged into 28-column Luna CSVs.
- 15 file_ids / 1589 rows fully translated and persisted as mappings pending mechanical CSV merge.
- Large manifests: `1C0FB26B` (268 rows / 4 shards) and `1C7679A5` (346 rows / 6 shards).

### OHD
- `1E4C1146`: **226 / 226 rows complete**, four shards + manifest.
- Manifest commit: `009ad3c14e8dc24e8afc821ade0f82fdd04f70a5`.

### LOOSE_OLANG completed

| file_id | Rows | Commit / manifest | Notes |
|---|---:|---|---|
| `00327F6A` | 4 | `cdb82257ba1ca12be52458645ee5d80b62c48d02` | old-save / TRADE / HOST prompts |
| `00C6A046` | 8 | `41778032c63e89a53943f158c0fbc03f0e6e3b6b` | save/system-data prompts |
| `0060E2F2` | 19 | `cf2385956d482e425012f4924e119eefa293da0d` | VERSUS OPS search/voice-chat UI |
| `0043DA6E` | 21 | `3ce04cd2bdfca96f0235dc95aff7d800c910a463` | Xbox LIVE / network errors |
| `00C79B17` | 26 | `234bf8e873d048888e6a5dd0ff35e145fe6ed52c` | rescue/location + old control tutorial |
| `0005EE2F` | 31 | `0485204e4b23132537f135b968619ca085b0bace` | data-management / extra settings |
| `00D345A5` | 41 | manifest `55c4d109288c7f81d6b788fbdbc86ae03c2a4db4` | item/weapon descriptions, two shards |
| `0072F326` | 42 | `f3b5f5efdcb40822381d95a1dcf18d5b209ce4a5` | save/storage/control prompts |
| `00225520` | 54 | `d0882164395d5af9da02f0a70e9f3147e09fe257` | model viewer / key help / weapon descriptions |
| `0066E64E` | 66 | `35f736bb6c40460648784e649cf4f1e79f03062e` | compact control/menu help labels |
| `00D0C740` | 68 | `b38689089c30bac8e3b95975e4800c6bc6864d5d` | UI + The Boss/Paz/story quote bank |
| `00CB1FB7` | 106 | `6aab159d96993753753e1c032d87ac76aee82946` | CO-OPS matchmaking/search UI |
| `005184E3` | 139 | manifest `cbf434cdb1e0f25d2a53aa7fff17d9eb61614bf1` | camera/menu, soldier chatter, missions, tutorial, versus UI; two shards |

LOOSE_OLANG translated rows: **625 / 1719**.

## Current queue

Only one LOOSE_OLANG file remains:

1. `007E2F18` — **1094 rows**

Persist `007E2F18` in contiguous shards with a manifest. After it is complete, LOOSE_OLANG will be **14 / 14** and total safely persisted translation will be **4025 rows / 51 file_ids**.

After LOOSE_OLANG, continue STAGEDAT_OLANG, then SLOT_OLANG unless a resource-specific structural problem justifies changing order.

## Important review / risk notes

- JPN always wins over shifted, combined, or over-expanded MLG_CN / ENG auxiliary text.
- Keep `無力化` distinct from lethal `破壊/殲滅` where gameplay meaning requires it.
- Existing normalized ruby/readings include `COMPA`, `LAB`, `ZEKE`, `ELUDE`, `SNEAKING MISSION`, `MAP`, `OPTIONS`; preserve structural markup exactly during merge.
- `0072F326`: JPN `モンスターハンターポータブル<I=REG>` preserved; auxiliary `FREEDOM<I=TM>` rejected. `[lack_strage_*]` runtime placeholders preserved.
- `00225520`: all dynamic key-help tokens preserved. Soul-in/out label provisionally rendered as battle-cry use/cancel and remains terminology-review material.
- `0066E64E`: auxiliary variants frequently labelled valid JPN functions as unused; JPN labels such as camera operation, discard, delete, display mode and list mode were kept distinct.
- `00D0C740`: multiple auxiliary story quotes contained sentences absent from JPN or omitted JPN clauses. The Boss/Paz/Strangelove-era lines were rebuilt from JPN rather than copying those additions.
- `00CB1FB7`: `難易度5` had an aggregated auxiliary variant `难度5以上`; exact JPN `难度5` was used. `$1` and `<I=CAN>` preserved.
- `005184E3`: `<ADD STAGE>` is preserved exactly as a runtime angle token; auxiliary `<添加关卡>` rejected. Literal `BACK` help text is kept instead of auxiliary `<I=SEL>`. Tutorial roll-result additions absent from JPN were omitted. `%d`, `<I=REG>`, color tags and copyright tags preserved.

## Last safe checkpoint

- Latest completed mapping manifest: `sol_translation_mappings/LOOSE_OLANG/005184E3.manifest.json`
- Manifest commit: `cbf434cdb1e0f25d2a53aa7fff17d9eb61614bf1`
- Safe translation total: **2931 rows / 50 file_ids**.
- Resume next at: **LOOSE_OLANG `007E2F18`, unique_index 0**.
