# Clean JPN FONT build semantics

This report is generated only from `font/JPN/00c7c9f9.xpr` and `font/JPN/001cbbd1.xpr`. No MLG/MLG_CN FontData, charmap, GlyphRecord, or bitmap is an input.

## PROVEN_FROM_FILE_STRUCTURE

| selector | encrypted bytes / SHA256 | decrypted SHA256 | XPR header_size | data_size | texture payload offset | atlas / pitch / format | USER offset / size | last_code | mapped / records | count prefix | record start / suffix |
|---|---|---|---:|---:|---:|---|---|---|---:|---|---|
| 00c7c9f9.xpr | 16,945,180 / `1f7a18f28d0d67d7a6a65a5286a1e48c97d595829b4c99325fb2b5772b921e8d` | `31b8eb9a7c86b1429fb7fa0d12688c65c9123e307c5f0e8c42f1df67a7cd9e6b` | `0x29010` | `0x1000000` | `0x2901C` | 4096×4096 / 4096 / 2, tiled=0, endian=0 | `0x90` / `0x28F32` | U+FF63 | 2,308 / 2,309 | 2-byte BE `0905` = 2309 | USER+`0x1FEE2` / 0 bytes |
| 001cbbd1.xpr | 2,234,396 / `5625066b835e6f26f310781fbbd3ef4f9ea93a77be2a4044289c11b74a767414` | `f4fdb335a56f81bee4e4a13be71f5518827ebcf42fbfa86d30d2f1de3c6dd025` | `0x21810` | `0x200000` | `0x2181C` | 2048×1024 / 2048 / 2, tiled=0, endian=0 | `0x90` / `0x214CA` | U+FF1F | 358 / 359 | 2-byte BE `0167` = 359 | USER+`0x1FE5A` / 0 bytes |

Both clean files independently expose a **2-byte big-endian glyph-count prefix**. For clean 00c7 it is `0x0905 = 2309`; for clean 001c it is `0x0167 = 359`. In each file the prefix value equals the exact number of following 16-byte GlyphRecords, and the record table ends exactly at USER end (no suffix/trailer). This conclusion does not reuse the patched MLG_CN0007 4-byte count-mirror PoC.

GlyphRecord layout in both clean files is eight big-endian u16 fields (stride `0x10`): `u0, v0, u1, v1, bearing_x_raw, width, advance, reserved`.

### Resource descriptors

| selector | index | identity | descriptor offset | payload offset | payload size | name offset | raw 24-byte descriptor |
|---|---:|---|---:|---:|---:|---:|---|
| 00c7c9f9.xpr | 0 | TX2D/FontTexture | `0x10` | `0x5C` | `0x34` | `0x44` | `545832440000005000000034000000000000003800000000` |
| 00c7c9f9.xpr | 1 | USER/FontData | `0x28` | `0x90` | `0x28F32` | `0x50` | `555345520000008400028f32000000000000004400000000` |
| 001cbbd1.xpr | 0 | TX2D/FontTexture | `0x10` | `0x5C` | `0x34` | `0x44` | `545832440000005000000034000000000000003800000000` |
| 001cbbd1.xpr | 1 | USER/FontData | `0x28` | `0x90` | `0x214CA` | `0x50` | `5553455200000084000214ca000000000000004400000000` |

For both files, resource 0 `TX2D/FontTexture` is at file `0x5C`, size `0x34`; resource 1 `USER/FontData` begins at `0x90`. The raw atlas begins at `0x0C + header_size`, and its offset has residue `0x1C mod 0x800`. Dense charmap entries are big-endian u16 and begin at USER+`0x16`; the record-prefix boundary is the charmap end rounded up to an 8-byte boundary.

### Deterministic USER-growth and relocation probes

The probes below append copies of a clean record only in memory to previously unmapped codepoints. They prove which file fields a structurally valid rebuild changes; they are **not runtime glyph validation**.

| selector | original USER→texture slack | one-record USER size | one-record texture offset | first probe crossing alignment | relocated texture offset | header_size delta | data_size delta |
|---|---:|---:|---:|---:|---:|---:|---:|
| 00c7c9f9.xpr | `0x5A` | `0x28F42` | `0x2901C` | 6 records | `0x2981C` | `+0x800` | `+0x0` |
| 001cbbd1.xpr | `0x2C2` | `0x214DA` | `0x2181C` | 45 records | `0x2201C` | `+0x800` | `+0x0` |

Structural update rules established by the probes:

1. The BE u16 count prefix must equal the rebuilt record count. The dense charmap must reference only existing u16 glyph indices.
2. The USER descriptor size changes with charmap/alignment/record-table growth. USER offset remains `0x90` while the preceding descriptor/header topology is retained.
3. Texture payload offset is recomputed at the clean file's `0x1C mod 0x800` alignment residue. Once USER growth crosses the available gap, the XPR `header_size` at file `0x04` changes by the same relocation delta.
4. XPR `data_size` at file `0x08` equals the atlas byte count. It does not change for USER-only growth; it must become `0x1000000` for a 4096×4096 8-bit atlas.
5. Resource descriptor relative offsets/sizes at file `0x10` and `0x28` must be rewritten from the new layout. In the clean topology, TX2D and USER relative offsets remain stable while USER size grows; a generalized builder still computes every descriptor rather than assuming this.
6. TX2D geometry is packed in the 0x34-byte TX2D payload: pitch/tiled in fetch word at TX2D+`0x1C`, format/endian at +`0x20`, and width/height at +`0x24`. Atlas bytes follow the complete XPR header, not the TX2D resource payload.
7. OuterCrypt is applied only after the complete plaintext is rebuilt, using the destination selector filename stem. The seed is not copied from a donor file.

For a future 4096×4096 clean 001c rebuild, the builder must update TX2D width, height and pitch to 4096, retain format=2/tiled=0/endian=0, set XPR data_size and texture payload length to `0x1000000`, recompute USER size/resource descriptors/header_size/texture offset/alignment, and encrypt with the `001cbbd1` destination seed.

## PROVEN_FROM_EXISTING_RUNTIME

- The 001c runtime path and 001c-owned TX2D selection are proven by the existing runtime fixture.
- A 4096×4096 / 16 MiB small atlas is runtime-proven when the exact-version Width/Height runtime patch is synchronized to 4096×4096.
- The historical 2 MiB fixed-limit claim is retracted; Phase 1 does not reopen it.
- Existing 00c7 append/count/new-atlas runtime PoCs prove only the patched MLG_CN0007-derived plaintext selected as 00c7, not this clean JPN00c7 structure.

## NEEDS_NEW_RUNTIME_VALIDATION

- A clean-JPN00c7 self-owned build with its 2-byte BE count prefix, rebuilt USER and any texture relocation.
- A clean-JPN001c self-owned 4096×4096 output (the existing runtime proof used patched MLG000e plaintext as compatibility/capacity evidence).
- Full union-charset large and small outputs, including SC Han overrides, punctuation policy, metric policy and scene coverage.
- Multi-glyph relocation after all descriptor/header updates, even though the resulting plaintext reparses statically.

## UNKNOWN

- Whether clean JPN00c7 accepts a full rebuild at runtime; no claim is promoted from the 3209→3210 patched-MLG_CN PoC.
- The final large/small selector split for each production character; Phase 1 uses the union worst case.
- The final source policy for Chinese punctuation and overlapping Japanese/fullwidth punctuation.
- Final raster size, baseline, advance and packing profile for any of the three candidate source fonts.

## Future builder output contract

Each candidate will emit `00c7c9f9.xpr`, `001cbbd1.xpr`, `FONT_GLYPH_MANIFEST.csv`, `FONT_BUILD_MANIFEST.json`, and `FONT_VALIDATION_REPORT.md`. The glyph manifest contract includes: `selector, codepoint, character, glyph_index, atlas_x, atlas_y, width, height, bearing, advance, glyph_source, font_file, font_face_index, font_size, baseline, bitmap_sha256, is_han_override`.

The CLI already accepts `--font-file`, `--font-face-index`, clean base paths and `--output-dir`. Phase 1 never opens or embeds a font file. A later rasterization phase must keep charset, atlas geometry, pixel size, padding, rasterizer settings, baseline, advance and packing algorithm identical across Sarasa UI SC, Source Han Sans SC and Microsoft YaHei UI Bold; only the Chinese glyph source changes. Microsoft YaHei remains local-test-only.
