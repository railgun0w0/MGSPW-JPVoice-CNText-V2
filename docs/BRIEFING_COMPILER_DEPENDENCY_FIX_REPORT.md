# BRIEFING Compiler Dependency Fix Report

Date: 2026-09-17  
Branch: `sol-translation`

## Finding

`tools/Compile-BriefingProductionTranslations.mjs` previously imported `Workbook` from `@oai/artifact-tool`. The package was used only for CSV parsing (`Workbook.fromCSV`), used-range dimensions, CSV round-trip parsing, and a small inspection of two representative output regions. The compiler's CSV writer, quoting, UTF-8 handling, control-token checks, mapping validation, capacity checks, and file I/O were already local.

The repository has no `package.json`, lockfile, vendored `node_modules`, or public dependency declaration. A normal checkout therefore failed before compilation with `MODULE_NOT_FOUND: @oai/artifact-tool`; the package existed only in an unavailable internal/runtime environment.

## Resolution

Solution A was selected: the internal runtime dependency was removed. The compiler now uses a small local RFC-4180-compatible parser for quoted fields, doubled quotes, commas, CRLF/LF, multiline fields, BOM removal, and dimension checks. The existing deterministic `encodeCsv` writer remains unchanged. Representative inspection is now a local deterministic region check. No builder, mapping schema, production CSV schema, or translation data was changed.

## Verification

After the change:

- `node tools/Compile-BriefingProductionTranslations.mjs --write`: PASS, 469 files / 5,645 rows, 0 control errors, 0 kana rows, 0 hard overflows.
- `node tools/Compile-BriefingProductionTranslations.mjs --check`: PASS, read-only, exit code 0.
- Byte-level comparison against the pre-change `translations/briefing/` snapshot: 469/469 files unchanged.
- Field comparison: `cn_text`, `jpn_text`, `unique_index`, `cn_control_tokens`, and `jpn_control_tokens` all changed in 0 rows.
- `python tools/Build-BriefingDat.py --check --dat <clean JPN 0076531d.DAT>`: PASS, 469 target blocks / 5,645 rows, 0 binding errors, 0 control errors, 0 capacity errors, 0 JPN round-trip errors.

The generated merge report changed only because its diagnostic field names now describe the local CSV checks; production CSVs did not change.

## Scope confirmation

- Translation changes: **NO**
- Mapping changes: **NO**
- Builder changes: **NO**
- BRIEFING data-model changes: **NO**
- Production CSV changes: **NO**

