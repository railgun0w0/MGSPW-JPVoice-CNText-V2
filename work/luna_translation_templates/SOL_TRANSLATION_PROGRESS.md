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
- For CSVs with embedded newlines, never use physical line numbers as row identity; anchor work to the logical `unique_index`.

## Current totals

| Metric | Progress |
|---|---:|
| Total template file_ids | 241 |
| Total template rows | 21041 |
| Translation work safely persisted | **4025 / 21041 rows** |
| file_ids with complete persisted translation | **51 / 241** |
| YPK_GTT | **36 / 36 complete** |
| OHD | **1 / 1 complete** |
| LOOSE_OLANG | **14 / 14 complete** |
| STAGEDAT_OLANG | **0 / 46** |
| SLOT_OLANG | **0 / 144** |

## Completed resource accounting

### YPK_GTT
- **2080 rows / 36 file_ids complete**.
- 21 file_ids / 491 rows already merged into 28-column Luna CSVs.
- 15 file_ids / 1589 rows fully translated and persisted as mappings pending mechanical CSV merge.
- Large manifests: `1C0FB26B` (268 rows / 4 shards) and `1C7679A5` (346 rows / 6 shards).

### OHD
- `1E4C1146`: **226 / 226 rows complete**, four shards + manifest.
- Manifest commit: `009ad3c14e8dc24e8afc821ade0f82fdd04f70a5`.

### LOOSE_OLANG
- **1719 / 1719 rows, 14 / 14 file_ids complete**.
- Completed file_ids: `00327F6A`, `00C6A046`, `0060E2F2`, `0043DA6E`, `00C79B17`, `0005EE2F`, `00D345A5`, `0072F326`, `00225520`, `0066E64E`, `00D0C740`, `00CB1FB7`, `005184E3`, `007E2F18`.
- `007E2F18`: **1094 / 1094 rows complete**, 11 shards + manifest.
- `007E2F18` manifest commit: `a38ac7ea2e4bb5dd92b246020d87295a8a9d2f21`.

#### `007E2F18` shards

| Shard | Range | Commit |
|---|---:|---|
| part01 | 0-99 | `7176c2e05248dcc2594c06657bdac2e0a3248d66` |
| part02 | 100-199 | `dc992f94dae894a42b590902e7147b8b76765d08` |
| part03 | 200-299 | `41a2f0833ec24752d69fb299710c8d6003e974cb` |
| part04 | 300-399 | `9194fa60e1a7094cec586c74804ef953e648f4df` |
| part05 | 400-499 | `a615baade644746ef1a894ed4bdd7746d45b2a2a` |
| part06 | 500-599 | `f6b0e862977f9f65fe119fdfd3c1887de7241808` |
| part07 | 600-699 | `ca1a3303e854d92731bfd8bae8cce0e1662dac1f` |
| part08 | 700-799 | `f15ac924881d94e0a1b85e97eb9d3227c692bfef` |
| part09 | 800-899 | `96eeae5c930cb4ffab554bea0472a161710ffefe` |
| part10 | 900-999 | `3b27914156ce89ca14c350b21b9cc6c833d7c59c` |
| part11 | 1000-1093 | `fdfbc5cc475b709041a444acee1daa985688cc08` |

## Next target

Continue with **STAGEDAT_OLANG**, then SLOT_OLANG unless a resource-specific structural problem justifies changing order.

The next STAGEDAT file_id should be selected from the current 46-file template set, translated by logical `unique_index`, persisted as mapping JSON, and only then considered for any later mechanical CSV merge.

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
- `007E2F18`: embedded-newline CSV work is anchored by logical `unique_index`, not physical line number. Late-file auxiliary rows are heavily sequence-shifted; JPN titles and controls were rebuilt directly. Part11 rejected a spurious auxiliary `<I=ATK>` insertion around `unique_index 1025`; the long VERSUS OPS help text preserves only JPN-declared `<I=ACT>`; `SUPER Magazine` / `SUPER M.` were preserved instead of shifted auxiliary `Liquid Magazine` / `LIQUID M.`.

## Last safe checkpoint

- Latest completed mapping manifest: `sol_translation_mappings/LOOSE_OLANG/007E2F18.manifest.json`
- Manifest commit: `a38ac7ea2e4bb5dd92b246020d87295a8a9d2f21`
- Safe translation total: **4025 rows / 51 complete file_ids**.
- Resource-class checkpoint: **LOOSE_OLANG 14 / 14 complete**.
- Resume next at: **STAGEDAT_OLANG, first untranslated file_id**.
