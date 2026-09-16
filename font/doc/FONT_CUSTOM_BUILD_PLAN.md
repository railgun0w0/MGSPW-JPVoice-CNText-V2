# MGSPW Self-Owned Font Build Plan

Status: final release design remains open; Phase 1/2A technical builder fixtures exist, but no final release pair is productionized.

## Current Phase 2B strategy checkpoint (2026-09-16)

For the small selector, use a selector-specific minimal corpus first. The current required corpus is only the compiled `LOOSE_OLANG/00D0C740` rows (the known 001c Loading source); the full project-wide 2,904-codepoint union must not be used as an automatic 001c build input.

The stock `001cbbd1.xpr` geometry remains the first target: `2048×1024`, pitch `2048`, format `2`, tiled `0`, endian `0`, with no EXE patch. Phase 2B.1 kept the exact selector corpus, source font, and policy, then salvaged the stock geometry at `51px / padding 1`: `549` GlyphRecords / `548` mapped, padded area `2,054,339`, packed height `1017`, with no crop, overlap, or overflow. The exact fixture was subsequently confirmed in-game, so `001C_STOCK_2048x1024_CAPACITY = SUFFICIENT`, `STOCK_PROFILE = 51px / padding 1`, and `CLEAN_JPN_001C_STOCK_SELF_OWNED_RUNTIME = PROVEN` for the selector-specific corpus; `EXE_PATCH_REQUIRED = NO`. The `50px / padding 1` fallback was not tested because 51/1 met the acceptance criteria. The other 709 UNKNOWN resource groups remain outside the proof scope, and no 4096×4096 output was generated.

## 1. Goal and source boundary

Build a completely self-owned Chinese font pair from the clean JPN selectors:

```text
font/JPN/00c7c9f9.xpr   (large)
font/JPN/001cbbd1.xpr   (small)
```

The build uses the project's own production charset and user-selected source fonts. It must not depend on a third-party localization XPR, its glyph bitmaps, or its FontData. Existing patched MLG fonts may remain test or reverse-engineering references but are not build inputs for the release artifacts.

## 2. First candidate set

Create three local visual candidates:

1. Sarasa UI SC
2. Source Han Sans SC
3. Microsoft YaHei UI Bold

Microsoft YaHei UI Bold is allowed only as a local visual-test candidate. Do not commit or distribute:

- the Microsoft font file;
- production XPRs generated from Microsoft YaHei UI Bold;
- reusable glyph bitmap caches generated from it.

The public release should prefer an open-source candidate after license review and visual QA. The exact font version, upstream download, license text, face index, and file SHA256 must be pinned in the future build manifest; those values are currently `UNKNOWN` and must not be guessed.

## 3. Fair-comparison build contract

The first comparison round must keep these parameters identical across all three candidates:

- atlas geometry per selector;
- charset and codepoint ordering;
- raster pixel size;
- cell/padding rules;
- baseline and vertical alignment policy;
- bearing and advance policy;
- grayscale/rasterizer settings;
- packing algorithm and deterministic ordering;
- XPR/USER/TX2D metadata policy;
- runtime patch configuration and QA fixtures.

Only the Chinese glyph source font changes. No candidate may receive hand-tuned metrics, a different glyph subset, a different packing heuristic, or a different fallback order during the first comparison round.

The first common expanded-atlas target should be `4096×4096`, pitch `4096`, format `2`, tiled `0`, endian `0`, one byte per texel for both selectors. This geometry is native to clean JPN00c7 and is runtime-proven for JPN001c when the dimension patch is applied. If future charset census proves it insufficient, changing the geometry requires a new design checkpoint and new runtime validation; it must not vary by candidate.

## 4. Glyph-source policy

Preserve clean JPN glyphs for:

- ASCII;
- Latin characters;
- digits;
- kana;
- game-specific symbols and punctuation whose original rendering is intentional.

Rasterize Han characters actually used by the Chinese translation from the selected SC candidate font.

For a Han codepoint already present in clean JPN, the SC glyph is allowed to replace the JPN glyph. This prevents Japanese regional glyph forms from leaking into Chinese text and keeps the Han style consistent. Every replacement must be recorded in the glyph manifest as an SC-source override rather than silently labeled as preserved JPN.

Fallback order for the design:

```text
non-Han preserved set -> clean JPN glyph
translation Han set   -> selected SC source font, including same-codepoint override
unrequested character -> not added speculatively
```

The builder must not copy bitmap glyphs from third-party MLG_CN XPRs. Those files may be used only for visual comparison or runtime compatibility tests outside the production build graph.

This production direction is decided: `SELF_OWNED_REBUILD`. MLG-only and MLG/JPN-donor hybrid outputs are not competing production routes. The exact approved open-source font and the large/small raster profiles remain design decisions.

Provenance guardrail: existing TEST2B, TEST3B and `厥` append PoCs started from patched MLG_CN0007 plaintext rekeyed as `00c7` (`3209 records / 3208 mapped`), not clean JPN00c7 (`2309 records / 2308 mapped`). They may inform implementation, but the builder must independently validate clean JPN00c7 count-prefix, USER growth, relocation and rebuild semantics.

## 5. Charset census

The future builder begins from a deterministic census of every production translation resource, not a hand-maintained approximate list.

Required census outputs:

- unique Unicode codepoints;
- occurrence count;
- resource classes and file IDs using each codepoint;
- visible/control classification;
- large/small selector requirements based on confirmed runtime fixtures;
- preserved-JPN versus SC-generated source decision;
- unsupported or ambiguous characters that require review.

Existing `font/analysis/production_character_inventory.csv`, coverage matrices, Loading corpus reports, and current translation masters are evidence inputs. The builder must regenerate the census from current tracked translation sources and fail if the generated result differs from the checked manifest without an explicit review.

## 6. Output matrix

Each candidate produces a complete pair:

```text
font_candidates/
  sarasa_ui_sc/
    00c7c9f9.xpr
    001cbbd1.xpr
    FONT_GLYPH_MANIFEST.csv
    FONT_BUILD_MANIFEST.json
    FONT_VALIDATION_REPORT.md
  source_han_sans_sc/
    00c7c9f9.xpr
    001cbbd1.xpr
    FONT_GLYPH_MANIFEST.csv
    FONT_BUILD_MANIFEST.json
    FONT_VALIDATION_REPORT.md
  microsoft_yahei_ui_bold/
    00c7c9f9.xpr
    001cbbd1.xpr
    FONT_GLYPH_MANIFEST.csv
    FONT_BUILD_MANIFEST.json
    FONT_VALIDATION_REPORT.md
```

This is `3 fonts × 2 selectors = 6 XPR files` for local comparison. The Microsoft-derived directory must remain local/ignored and must never be included in a public package or committed artifact set.

## 7. Required future builder capabilities

The production builder should provide one deterministic pipeline with these stages:

1. charset census;
2. source-font identity and license validation;
3. glyph rasterization;
4. metric normalization for large and small paths;
5. deterministic atlas packing;
6. charmap rebuild;
7. GlyphRecord rebuild;
8. USER/FontData rebuild, including independently validated selector-specific count semantics;
9. TX2D descriptor and bitmap rebuild;
10. XPR header/resource-offset/size rebuild;
11. selector-specific OuterCrypt encryption;
12. decrypt/reparse round-trip validation;
13. bounds, overlap, count, mapping, and atlas-capacity validation;
14. glyph manifest and build manifest generation;
15. runtime fixture package generation without modifying the production game install.

The builder must understand the selectors separately. Large 00c7 and small 001c have different clean FontData layouts and count prefixes; it must not pretend they are interchangeable merely because both can use a 4096×4096 texture.

## 8. `FONT_GLYPH_MANIFEST.csv`

At minimum, emit these columns exactly:

```text
codepoint
character
glyph_index
atlas_x
atlas_y
width
height
bearing
advance
glyph_source
font_file
font_size
```

Recommended additional columns for auditability:

```text
selector
source_glyph_id
baseline
pixel_bbox
bitmap_sha256
is_han_override
resource_usage_count
```

`glyph_source` should use explicit values such as `CLEAN_JPN_PRESERVED`, `SARASA_UI_SC`, `SOURCE_HAN_SANS_SC`, or `MICROSOFT_YAHEI_UI_BOLD_LOCAL_TEST`. It must never obscure a third-party XPR donor behind a generic value.

## 9. Round-trip and static validation policy

For each of the six local candidate XPRs:

- decrypt with its selector filename seed and require `XPR2` magic;
- reparse resource descriptors and ensure all ranges are in bounds and non-overlapping;
- verify XPR `data_size == atlas_width * atlas_height` for 8-bit linear TX2D;
- verify texture dimensions, pitch, format, tiled, and endian fields;
- verify every mapped charmap entry references an existing GlyphRecord;
- verify every glyph rectangle is inside the atlas and respects packing constraints;
- verify count mirrors/prefixes agree with the actual record count;
- verify preserved glyphs/metrics selected by policy are byte-identical or manifest-explained;
- verify each required codepoint is present and no unrequested codepoint was silently substituted;
- encrypt, decrypt again, and require byte-identical rebuilt plaintext;
- generate hashes for input font, clean XPR, plaintext output, encrypted output, atlas, USER, charmap, and GlyphRecord table.

Any mismatch fails the build; no partial output is promoted.

## 10. Runtime validation matrix

All three candidates must be tested with the same scenes and settings:

- title and menu Latin/ASCII regression;
- normal large UI Chinese strings;
- Briefing and long-text clipping;
- Loading quote small-font fixture;
- small UI glyph coverage;
- representative dense strokes at native resolution and configured upscale modes;
- punctuation, kana, digits, symbols, and controller-icon regressions;
- baseline, advance, kerning-like spacing, cropping, bleeding, and texture-edge artifacts;
- startup/reload cycles and scene transitions.

For `001cbbd1.xpr` at 4096×4096, use only the exact-version runtime patch policy in [`FONT_PRODUCTION_BASELINE.md`](FONT_PRODUCTION_BASELINE.md). A candidate is invalid if it relies on disabling byte verification or applying the patch before runtime unpacking finishes.

## 11. Candidate decision gate

The open-source release candidate should be selected only after:

- all static validations pass;
- all required glyphs render;
- no ASCII/kana/symbol regression is observed;
- large and small paths both pass the shared runtime fixture set;
- license and redistribution requirements are documented;
- visual review compares the same screenshots/crops under identical settings;
- the chosen font version and source file hashes are pinned.

The Microsoft candidate may inform visual preference but cannot win the public-release gate unless separate redistribution rights are established; by current policy it remains local-test-only.

## 12. Explicit non-goals for this archive pass

- Do not implement or modify the builder.
- Do not generate any of the six XPR candidates.
- Do not rasterize or cache glyphs.
- Do not download, copy, or commit font files.
- Do not modify the EXE, production XPRs, translation resources, or game install.
- Do not delete historical fixtures or crash dumps.
