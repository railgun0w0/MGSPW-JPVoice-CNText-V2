# Translation Source-of-Truth Audit

> **ARCHIVED / HISTORICAL SNAPSHOT / PRE-MIGRATION / SUPERSEDED**
>
> This audit records the repository state before the 2026-09-17 canonical
> migration. Its reported mixed YPK authority and 21 JSON-less YPK files are
> historical facts and must not be rewritten. Current authority is defined by
> [`TRANSLATION_CANONICAL_UNIFICATION_REPORT.md`](TRANSLATION_CANONICAL_UNIFICATION_REPORT.md),
> the committed `sol_translation_mappings/` tree, and the production compiler.

Audit date: 2026-09-17 (Asia/Hong_Kong)  
Repository: `railgun0w0/MGSPW-JPVoice-CNText-V2`  
Branch / audited HEAD: `sol-translation` / `b58695fe005f50402ad31c27e2053b6d2e18801f`  
Scope: translation authority, compiler inputs/outputs, builder inputs, generated manifests, and JSON/CSV consistency. No translation or build artifact was modified.

## Executive Summary

1. **Current authority by class:** `LOOSE_OLANG`, `SLOT_OLANG`, `STAGEDAT_OLANG`, `OHD`, and `BRIEFING_NBE` are `JSON_CANONICAL_CSV_GENERATED`. `YPK_GTT` is `MIXED_WITH_DEFINED_PRECEDENCE`: 15 file_ids / 1,589 rows use mapping JSON; 21 file_ids / 491 rows use the committed template CSV itself because no mapping JSON exists. The selection order implemented by `rebuild_translation_state.py::audit_file` is complete manifest JSON > complete descriptor/sharded JSON > complete flat JSON > complete translated template CSV.
2. **`translations/**/*.csv` is generated for all six classes.** It is not the authoritative human translation store according to the production compiler code. It is a production materialization. YPK_GTT, OHD, and BRIEFING builders read it directly; the three OLANG builders instead read `build/translation/compiled_translation_manifest.csv`.
3. **`sol_translation_mappings` is still a real production source for the old five classes, but not for every old-five file_id.** It supplies 220/241 file_ids and 20,550/21,041 unique translation rows. The remaining 21 YPK_GTT file_ids / 491 rows come from translated template CSVs. The old-five compiler actually calls the mapping-state loader and consumes its canonical representation; these JSON files have not merely become archival recovery records.
4. **BRIEFING has a separate JSON -> CSV path.** `tools/Compile-BriefingProductionTranslations.mjs::main` reads 469 JPN template CSVs plus 469 mapping JSONs and emits 469 `translations/briefing/*.csv` files. It does not use the old-five compiler or its 91,609-row manifest.
5. **No current production builder reads canonical translation JSON directly.** YPK_GTT, OHD, and BRIEFING read production CSV; LOOSE/SLOT/STAGEDAT OLANG read the compiled manifest. `tools/Build-JpnYpk-1C79F2AD.py` does read `translations/1C79F2AD_cn.json`, but it is a targeted historical/golden path, not the all-YPK production builder.
6. **There is no unresolved canonical precedence, but the repository has double-authority risk surfaces.** The compiler's precedence is defined, yet generated CSV/manifest files remain directly editable builder inputs, YPK authoring is split across JSON and template CSV, two file_ids retain conflicting complete JSON representations, and an older alternate writer can target the same production filenames. Ten risk findings are enumerated below.
7. **JSON/production-CSV content divergence exists in 3 rows across 3 SLOT_OLANG file_ids.** All three are deliberate compiler normalization of a whitespace-only JPN source: JSON has `cn_text=""`; generated CSV preserves the source spaces (`" "` or `"   "`). There are no translated-wording divergences. Additionally, two file_ids have conflicting complete JSON representations; their explicit manifest JSON is canonical and the older flat/descriptor representation is not consumed.
8. **Safest future bulk-replacement entry:** edit the canonical authoring layer, never `translations/**/*.csv` or the compiled manifest. Today that means canonical mapping JSON for 689 file_ids and the translated template CSV for the 21 JSON-less YPK_GTT file_ids, followed by both production compilers and freshness checks. The recommended end-state is one canonical mapping representation for all 710 file_ids, with CSV and manifest treated as reproducible, non-authorable outputs.

The principal documentation conflict is explicit: root `README.md:37` and `translations/README.md` call `translations/<resource_class>/<file_id>.csv` the translation authority, while `tools/Compile-ProductionTranslations.py` says the mapping repository is the fact source and writes those CSVs at lines 887-895. Actual code behavior wins for this audit.

## Current Translation Architecture

### Old five classes

```text
clean JPN extraction / tracked JPN reference master
  + work/luna_translation_templates/<CLASS>/<file_id>.csv
  + canonical translation chosen by rebuild_translation_state.py
      - mapping JSON / manifest / shards for 220 file_ids, or
      - translated YPK template CSV for 21 file_ids
                    |
                    v
tools/Compile-ProductionTranslations.py
        |-----------------------------|
        v                             v
translations/<class>/<file_id>.csv    build/translation/compiled_translation_manifest.csv
(unique translation rows)             (expanded physical object bindings)
        |                             |
        | YPK_GTT / OHD builders      | LOOSE/SLOT/STAGEDAT OLANG builders
        v                             v
component or final rebuilt resource / DAT / PDT
```

The production CSV and compiled manifest are **sibling outputs** of the compiler. The manifest is not generated by reading the just-written production CSV. `build_manifest()` receives the in-memory `compiled` mappings, writes `cn_text`, and records `source_translation_file` only as provenance metadata (`Compile-ProductionTranslations.py:641-700`). The three OLANG builders do not dereference that field.

`translation_worklist.csv`, `fixed_capacity_issues.csv`, and `production_merge_report.json` are also compiler outputs. They are not translation inputs.

### BRIEFING

```text
work/luna_translation_templates/reference_masters/jpn_briefing_master.csv
  + work/luna_translation_templates/BRIEFING/<file_id>.csv
  + work/luna_translation_templates/sol_translation_mappings/BRIEFING/<file_id>.json
                    |
                    v
tools/Compile-BriefingProductionTranslations.mjs::main
                    |
                    v
translations/briefing/<file_id>.csv
                    |
                    v
tools/Build-BriefingDat.py::load_production
  + frozen JPN master cross-check
                    |
                    v
rebuilt clean-JPN 0076531d.DAT
```

There is no BRIEFING translation manifest between CSV and builder. The old-five manifest intentionally contains no `BRIEFING_NBE` rows.

## Resource Class Matrix

| Resource Class | file_ids / unique rows | Canonical Source | Mapping JSON coverage | Production CSV | Production Compiler | Builder translation input | Status |
|---|---:|---|---:|---|---|---|---|
| LOOSE_OLANG | 14 / 1,719 | mapping JSON | 14/14 | generated, 14 files | `Compile-ProductionTranslations.py` | compiled manifest | `JSON_CANONICAL_CSV_GENERATED` |
| SLOT_OLANG | 144 / 11,329 | mapping JSON; manifest JSON wins for `5D06A8D5` | 144/144 | generated, 144 files | `Compile-ProductionTranslations.py` | compiled manifest | `JSON_CANONICAL_CSV_GENERATED` |
| STAGEDAT_OLANG | 46 / 5,687 | mapping JSON; manifest JSON wins for `LANG_VOCALOID_KEYBOARD.OLANG` | 46/46 | generated, 46 files | `Compile-ProductionTranslations.py` | compiled manifest | `JSON_CANONICAL_CSV_GENERATED` |
| OHD | 1 / 226 | sharded mapping manifest | 1/1 | generated, 1 file | `Compile-ProductionTranslations.py` | `translations/ohd/1E4C1146.csv` | `JSON_CANONICAL_CSV_GENERATED` |
| YPK_GTT | 36 / 2,080 | 15 JSON; 21 translated template CSV | 15/36 | generated, 36 files | `Compile-ProductionTranslations.py` | `translations/ypk_gtt/*.csv` | `MIXED_WITH_DEFINED_PRECEDENCE` |
| BRIEFING_NBE | 469 / 5,645 physical rows | mapping JSON | 469/469 | generated, 469 files | `Compile-BriefingProductionTranslations.mjs` | `translations/briefing/*.csv` | `JSON_CANONICAL_CSV_GENERATED` |

The 241 old-five file_ids contain 21,041 unique translation rows. Their compiled object manifest has 91,609 rows: YPK_GTT 2,136; OHD 904; LOOSE_OLANG 2,963; STAGEDAT_OLANG 16,922; SLOT_OLANG 68,684.

## Canonical Selection and Compiler Evidence

`work/luna_translation_templates/tools/rebuild_translation_state.py` is imported by the old-five compiler:

- `load_templates()` reads all six template directories and validates `file_id` plus contiguous `unique_index` (`194-260`).
- `csv_translation_representation()` recognizes committed template rows whose `translation_status` starts with `TRANSLATED`; this is how the 21 legacy YPK CSV authorities are recovered (`502-571`). Seven rows have an explicitly handled legacy one-cell shift.
- `audit_file()` loads flat JSON and `.manifest.json`, resolves shards, validates exact index coverage, and chooses the canonical complete representation (`601-696`).
- The exact priority is explicit manifest > descriptor with members > flat mapping > translated template CSV (`661-679`).
- `tools/Compile-ProductionTranslations.py::main` imports that module, audits every old-five template, and passes each `audit.canonical` to `compile_files()` (`804-843`).
- `compile_files()` joins canonical `cn_text` to the clean template by `unique_index` (`331-468`). It emits normalized production rows; it does not take `cn_text` from `translations/**/*.csv` except to preserve stable `build_status`/`ingame_status` when old and new text are exactly equal (`314-326`, `371-388`).
- The same in-memory compiled map expands through tracked JPN masters into the object manifest (`641-700`).

The old-five compiler's `RESOURCE_CLASSES` deliberately excludes BRIEFING (`29-35`). BRIEFING has its own compiler.

## LOOSE_OLANG

### Source files

- JPN template: `work/luna_translation_templates/LOOSE_OLANG/<file_id>.csv`.
- Object/structure master: `work/luna_translation_templates/reference_masters/jpn_loose_olang_master.csv`.
- Chinese authority: canonical roots under `work/luna_translation_templates/sol_translation_mappings/LOOSE_OLANG/`.
- Mapping layout: 11 flat roots, 3 manifest roots, 15 referenced shards; 29 physical JSON artifacts total.

### Translation authority and compile path

All 14 file_ids have exact complete JSON coverage. The production compiler reads those JSON representations and writes 14 `translations/loose_olang/*.csv` files plus 2,963 expanded manifest bindings. The production CSV is generated, not a separately maintained authority.

### Builder path

`tools/Build-JpnLooseOlangFromManifest.py::read_manifest` filters `resource_class == "LOOSE_OLANG"` and `translation_status == "APPROVED"` (`49-58`). `translated_texts()` takes `cn_text` directly from those manifest rows (`62-97`). It does not open `translations/loose_olang/*.csv`. The final material is rebuilt loose OLANG files under the selected output root.

### JSON/CSV relationship and risks

JSON/CSV comparison is 1,719/1,719 identities matched and text-equal. Risk: changing canonical JSON does nothing to a build until the compiler rewrites the manifest; changing the production CSV alone also does nothing to this builder.

## SLOT_OLANG

### Source files

- JPN template: `work/luna_translation_templates/SLOT_OLANG/<file_id>.csv`.
- Object master: `reference_masters/jpn_slot_olang_master.csv`.
- Chinese authority: canonical JSON under `sol_translation_mappings/SLOT_OLANG/`.
- Mapping layout: 141 canonical flat roots, 3 canonical manifest roots, referenced shards; 159 physical JSON artifacts.

### Translation authority and defined JSON precedence

All 144 file_ids are JSON-authoritative. `5D06A8D5` has two complete, conflicting representations: `5D06A8D5.json` and `5D06A8D5.manifest.json`. The state code explicitly chooses the manifest. The flat JSON is therefore legacy/non-production despite being complete.

### Builder path

`tools/Build-JpnSlotOlangFromManifest.py::read_manifest` reads approved `SLOT_OLANG` rows from `build/translation/compiled_translation_manifest.csv` (`54-65`). Its text replacement reads `row["cn_text"]` (`70-112`). Output is a component `002aba34.DAT/.KEY`, later merged by `tools/Build-JpnUnifiedSlot.py` with YPK and OHD component DATs.

### JSON/CSV relationship and risks

11,329 identities match. 11,326 texts are byte-equal; 3 differ only because `Compile-ProductionTranslations.py` replaces an empty mapped string with a whitespace-only JPN source (`393-407`):

| file_id | unique_index | JSON `cn_text` | production CSV `cn_text` | JPN source |
|---|---:|---|---|---|
| `5D1DF209` | 13 | empty | 3 spaces | 3 spaces |
| `5D5A5B84` | 5 | empty | 1 space | 1 space |
| `5D8AED23` | 0 | empty | 3 spaces | 3 spaces |

These are deterministic normalization differences, not semantic translation divergence. The builder reads the manifest, which currently matches the normalized production CSV for all 68,684 SLOT object rows.

## STAGEDAT_OLANG

### Source files

- JPN template: `work/luna_translation_templates/STAGEDAT_OLANG/<file_id>.csv`.
- Object master: `reference_masters/jpn_stagedat_text_master.csv`.
- Chinese authority: canonical JSON under `sol_translation_mappings/STAGEDAT_OLANG/`.
- Mapping layout: 34 canonical flat roots, 12 canonical manifest roots, referenced shards; 126 physical JSON artifacts.

### Translation authority and defined JSON precedence

All 46 file_ids are JSON-authoritative. `LANG_VOCALOID_KEYBOARD.OLANG` has a complete legacy descriptor/parts representation and a complete explicit manifest representation with 12 differing translation/control rows. The explicit `.manifest.json` and its members are canonical; the old descriptor plus four `part0N` files are not production inputs.

### Builder path

`tools/Build-JpnStageDatOlangFromManifest.py::read_manifest` filters approved STAGEDAT rows (`60-70`), and `translated_texts()` reads manifest `cn_text` (`73-108`). It rebuilds target RBX/OLANG entries inside the JPN STAGEDAT and emits `009645fa.PDT`. It does not open `translations/stagedat_olang/*.csv`.

### JSON/CSV relationship and risks

All 5,687 identities and texts are equal between the canonical JSON representation and production CSV. All 16,922 manifest object rows also equal the production CSV translation selected by `(resource_class, file_id, jpn_text)`.

## OHD

### Source files and authority

- JPN template: `work/luna_translation_templates/OHD/1E4C1146.csv`.
- Object master: `reference_masters/jpn_ohd_master.csv`.
- Chinese authority: `sol_translation_mappings/OHD/1E4C1146.manifest.json` plus four referenced shards.
- Generated production materialization: `translations/ohd/1E4C1146.csv`.

All 226 JSON identities and texts equal the production CSV.

### Builder path

Unlike the OLANG builders, `tools/Build-JpnOhdRoundTrip.py::read_translation` opens the CSV and maps exact `jpn_text -> cn_text` (`43-58`). `parse_args()` defaults `--translation` to `translations/ohd/1E4C1146.csv` (`125-158`), and `main()` loads it at line 170. The component SLOT DAT is then merged by `Build-JpnUnifiedSlot.py`.

### Risk

The declared canonical source is JSON, but the production builder accepts the generated CSV directly. A manual CSV change can therefore alter the OHD build without changing JSON; a later compiler run can overwrite that edit.

## YPK_GTT

### Source files

- JPN templates: `work/luna_translation_templates/YPK_GTT/<file_id>.csv`.
- Object master: `reference_masters/jpn_gtt_master.csv`.
- JSON mappings: 15/36 file_ids, 1,589 rows; 13 flat roots and 2 manifest roots with ten shards, 25 physical JSON artifacts.
- Template-CSV translations: 21/36 file_ids, 491 rows. These files have complete `TRANSLATED*` rows and no competing mapping JSON.
- Generated production materialization: 36 `translations/ypk_gtt/*.csv` files / 2,080 rows.

### Translation authority and precedence

This class is `MIXED_WITH_DEFINED_PRECEDENCE`. When a complete mapping JSON exists, it outranks a translated template CSV. When no mapping root exists, the complete translated template CSV is canonical. Seven legacy YPK rows are recovered from a known one-cell shift by `csv_translation_representation()`; the compiler normalizes them into the production schema.

The JSON-backed 1,589 rows match production CSV exactly. The remaining 491 production rows are correctly `csv_only_rows` in the literal JSON/CSV comparison because their authority is the template CSV, not JSON.

### Builder path

`tools/Build-JpnAllYpkGttRoundTrip.py::read_translation` opens production CSV (`42-58`). `--translations-dir` defaults to `translations/ypk_gtt` (`87-119`); `main()` globs every CSV and loads them at `138-144`, then selects `cn_text` by exact JPN text (`201-215`). The output component SLOT DAT is merged by `Build-JpnUnifiedSlot.py`.

`tools/Build-JpnYpk-1C79F2AD.py` is not the production all-YPK builder. It reads `translations/1C79F2AD_cn.json` and is retained by the golden/regression path.

### Risks

- The class has two authoring formats, so there is no single physical bulk-edit directory.
- The production builder reads generated CSV, so manual CSV changes can affect the build until overwritten by the compiler.
- The seven shifted legacy template rows are canonical inputs in malformed historical layout, though the current state loader recovers them deterministically.

## BRIEFING_NBE

### Source files

- Structural/JPN template: `work/luna_translation_templates/BRIEFING/<file_id>.csv`, 469 files / 5,645 physical rows.
- Structural master: `work/luna_translation_templates/reference_masters/jpn_briefing_master.csv`.
- Chinese authority: `work/luna_translation_templates/sol_translation_mappings/BRIEFING/<file_id>.json`, 469 flat JSONs / 5,645 rows.
- Production materialization: `translations/briefing/<file_id>.csv`, 469 files / 5,645 rows.

### Compiler path

`tools/Compile-BriefingProductionTranslations.mjs::main` sets the template, mapping, and output roots at lines 264-279; requires the template and mapping filename sets to be identical (`282-303`); reads each template and JSON mapping (`327-345`); joins by contiguous `unique_index`; and writes production CSVs (`454`, `535-537`). `--check` reconstructs every expected CSV and requires byte equality with the checked-in production file (`538-553`).

### Builder path

`tools/Build-BriefingDat.py::parse_args` defaults `--production-dir` to `translations/briefing` and `--master` to `reference_masters/jpn_briefing_master.csv` (`108-136`). `load_production()` reads exactly 469 CSVs, validates 5,645 contiguous physical identities, checks JPN text and block metadata against the master, and then consumes `cn_text` (`203-274`). `main()` calls `load_master()` and `load_production()` at lines 536-537. No JSON is opened by the builder.

### JSON/CSV relationship and verification

All 469 file sets exist; all 5,645 `(file_id, unique_index)` identities match; all 5,645 `cn_text` values are equal. There are no JSON-only, CSV-only, or text-different BRIEFING rows.

The dedicated compiler `--check` could not be executed in this shell because `@oai/artifact-tool` is absent from both the default and bundled Node package paths. No package was installed. This does not make the flow unclear: the compiler code was inspected, the committed merge report records a PASS, and an independent row-level comparison reproduced exact JSON/CSV equality. The absence of the dependency is an environment reproducibility issue to fix separately.

## Legacy / Fixture / Reference Files

The audit searched all 2,254 Git-tracked `*.json`/`*.csv` files plus the ignored active `build/translation/` outputs.

| Path/pattern | Classification | Actual role / consumer |
|---|---|---|
| canonical JSON roots and referenced shards under `sol_translation_mappings/` | `PRODUCTION_CANONICAL` | Read by mapping-state code and old-five or BRIEFING compiler. 807 of 813 physical mapping JSON artifacts are on a canonical path. |
| `work/luna_translation_templates/{five classes,BRIEFING}/*.csv` | `PRODUCTION_CANONICAL` for JPN identity/structure | Read by compilers. For 21 JSON-less YPK file_ids, these CSVs are also the Chinese translation authority. |
| `work/luna_translation_templates/reference_masters/*.csv` | `PRODUCTION_CANONICAL` for object/physical structure, not CN prose | Old-five compiler expands mappings through five masters; BRIEFING builder cross-checks its master directly. |
| `translations/{loose_olang,slot_olang,stagedat_olang,ohd,ypk_gtt,briefing}/*.csv` | `PRODUCTION_GENERATED` | Compiler output. Direct builder input only for YPK_GTT, OHD, BRIEFING; the OLANG copies are not read by their builders. |
| `build/translation/compiled_translation_manifest.csv` | `PRODUCTION_GENERATED` | Direct builder translation input for the three OLANG classes; also a generated object-binding census. Not an input to YPK/OHD/BRIEFING builders. |
| `build/translation/translation_worklist.csv` | `INTERMEDIATE` | Generated file_id management index; no current production builder reads it. |
| `build/translation/fixed_capacity_issues.csv`, `production_merge_report.json`, `briefing_production_merge_report.json` | `REFERENCE_ONLY` | Compiler reports/audit evidence, not translation sources. |
| `translations/1C79F2AD_cn.json` | `REGRESSION_FIXTURE` / historical single-file build input | Read by `tests/test_gtt_1C79F2AD_golden.py`, `Freeze-GttGolden-1C79F2AD.py`, and targeted `Build-JpnYpk-1C79F2AD.py`; not read by current all-YPK production compiler/builder. |
| `tests/fixtures/gtt_1C79F2AD/expected.json`, `tests/fixtures/olang_5D3AF52D/expected.json` | `REGRESSION_FIXTURE` | Golden structural expectations; not translation authority. |
| `work/luna_translation_templates/sol_translation_mappings/SLOT_OLANG/5D06A8D5.json` | `LEGACY_UNUSED` | Complete but conflicts with the canonical explicit manifest; priority code excludes it. |
| `.../STAGEDAT_OLANG/LANG_VOCALOID_KEYBOARD.OLANG.json` plus `.part01`-`.part04.json` | `LEGACY_UNUSED` | Complete older descriptor/parts representation; conflicts with and loses to the explicit manifest representation. |
| `doc/ruby_base_pair_canonical.csv` | `REFERENCE_ONLY` for translation-source audit | Maintenance rule table used by Ruby rewrite/audit tooling; not full translation prose and not read by production builders. |
| `build/rc1/RC1_FILE_MANIFEST.csv`, `docs/FINAL_PATCH_FILE_MANIFEST.csv` | `REFERENCE_ONLY` | Package/release records, not translation sources. |
| `font/build/**/{*MANIFEST*.json,*MANIFEST*.csv}` | `REGRESSION_FIXTURE` / font build metadata | Font-specific; outside the six translation flows. |
| `artifacts/miller/1C79F2AD_page88_tag14_record0_cn_rebuilt.json` | `REFERENCE_ONLY` | Historical analysis artifact; no production consumer found. |

`tools/Build-TranslationWorklist.mjs` is a notable legacy alternate writer. It can write `translations/slot_olang/*.csv`, `translation_worklist.csv`, and `compiled_translation_manifest.csv` from batch definitions and existing CSVs, but its tracked `work/translation_batches/slot_olang` inputs are absent and current production documentation does not invoke it. It must not be confused with `Compile-ProductionTranslations.py`.

## JSON / CSV Consistency Results

The literal comparison uses canonical JSON rows only, keyed by `(resource_class, file_id, unique_index)`, against `translations/<class>/<file_id>.csv`. `csv_only_rows` for the 21 JSON-less YPK files are expected and are not missing translations.

| resource_class | canonical JSON roots | physical JSON artifacts | CSV files | json_rows | csv_rows | matched_rows | text_equal_rows | text_different_rows | json_only_rows | csv_only_rows |
|---|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|
| LOOSE_OLANG | 14 | 29 | 14 | 1,719 | 1,719 | 1,719 | 1,719 | 0 | 0 | 0 |
| SLOT_OLANG | 144 | 159 | 144 | 11,329 | 11,329 | 11,329 | 11,326 | 3 | 0 | 0 |
| STAGEDAT_OLANG | 46 | 126 | 46 | 5,687 | 5,687 | 5,687 | 5,687 | 0 | 0 | 0 |
| OHD | 1 | 5 | 1 | 226 | 226 | 226 | 226 | 0 | 0 | 0 |
| YPK_GTT | 15 | 25 | 36 | 1,589 | 2,080 | 1,589 | 1,589 | 0 | 0 | 491 |
| BRIEFING_NBE | 469 | 469 | 469 | 5,645 | 5,645 | 5,645 | 5,645 | 0 | 0 | 0 |
| **Total** | **689** | **813** | **710** | **26,195** | **26,686** | **26,195** | **26,192** | **3** | **0** | **491** |

Additional consistency checks:

- All 710 file_ids are complete according to the repository's own state logic; 26,686/26,686 translation rows are persisted; validation errors = 0.
- The current 91,609-row old-five compiled manifest has exact `cn_text` equality with the current production CSV for every object row.
- State validation emits 430 warnings, principally stale `cn_utf8_bytes` metadata that compilers recompute, seven recovered legacy YPK column shifts, and the two conflicting complete JSON representations. These warnings do not change canonical selection.
- `SOL_TRANSLATION_PROGRESS.md`'s generated ledger/checkpoint metadata is stale relative to current HEAD, but it is documentation state and is not read by production compilers/builders.

Per-file statistics, canonical paths, compiler/builder paths, and the three normalized differences are in `TRANSLATION_SOURCE_OF_TRUTH_MATRIX.csv`.

## Double-Authority Risks

The following are ten concrete risk findings. They are risk surfaces, not ten unresolved precedence decisions; current code resolves precedence in every class.

1. **DA-01 — documentation contradicts code.** README files call `translations/**/*.csv` authoritative; production compiler code treats mappings/template CSV as facts and overwrites production CSV.
2. **DA-02 — canonical edits are not automatically propagated.** Editing JSON/template CSV does not update production CSV or manifest until a compiler write run.
3. **DA-03 — YPK builder trusts generated CSV.** Manual production-CSV edits can affect a build without updating canonical JSON/template CSV.
4. **DA-04 — OHD builder trusts generated CSV.** Same risk for OHD.
5. **DA-05 — BRIEFING builder trusts generated CSV.** Its `--check` can detect drift, but the builder itself does not invoke the compiler or compare JSON.
6. **DA-06 — OLANG CSV is a decoy build input.** Manual edits to the three OLANG production CSV directories do not affect their builders; the ignored manifest does. This can cause an operator to edit the wrong apparent authority.
7. **DA-07 — YPK has split canonical formats.** 15 file_ids are JSON-authoritative and 21 are template-CSV-authoritative.
8. **DA-08 — two file_ids retain conflicting complete JSON representations.** Explicit manifest precedence resolves them, but the losing files look valid and complete.
9. **DA-09 — an alternate legacy writer targets current filenames.** `Build-TranslationWorklist.mjs` can overwrite the worklist/manifest and SLOT CSV from a different, now-incomplete input model.
10. **DA-10 — old-five CSV status fields feed back into compiler output.** `load_existing_production()` preserves stable `build_status` and `ingame_status` when text is exact. Chinese prose authority remains canonical mapping/template, but the full generated CSV is not purely a function of canonical prose plus JPN templates.

The repository currently has **0 unclear class flows** and **0 unresolved canonical precedence cases**. It does have **3 normalized JSON/CSV text differences**, **2 intra-JSON legacy conflicts**, and the ten operational risk findings above.

## Recommended Canonical Model

Do not implement this recommendation as part of this audit.

1. Define one authoring contract for all 710 file_ids: one canonical mapping root per file_id, with manifest+shards allowed only for size. Migrate the 21 YPK template-CSV translations into that contract after a reviewed, lossless conversion.
2. Treat every file under `translations/` and every compiled manifest/worklist as generated and non-authorable. Put that statement in the root README and `translations/README.md`.
3. Add a deterministic old-five `--check` mode equivalent to the BRIEFING compiler's byte comparison. Require both compiler checks before any builder runs.
4. Make builders validate a compiler checkpoint/hash or invoke a read-only freshness check. Directly reading generated CSV is acceptable only if staleness is rejected.
5. Archive or clearly gate the losing JSON representations, the old single-file JSON builders, and `Build-TranslationWorklist.mjs` so they cannot be mistaken for production entry points.
6. Keep JPN templates/masters as structural authority and canonical mappings as Chinese prose authority; never mix those roles with release manifests, regression fixtures, or runtime build reports.

Until such a migration occurs, the safest bulk translation replacement procedure is:

1. Update canonical mapping JSON for the 689 JSON-backed file_ids.
2. Update only the authoritative template `cn_text` fields for the 21 JSON-less YPK file_ids.
3. Run mapping-state validation.
4. Run `Compile-ProductionTranslations.py --write` and `Compile-BriefingProductionTranslations.mjs --write` in a clean, dependency-complete checkout.
5. Compare/recheck generated CSV and manifests; then run builders. Do not hand-edit generated production CSV or `compiled_translation_manifest.csv`.
