# MGSPW FONT Technical Archive

归档日期：2026-09-16（Asia/Hong_Kong）
目标分支：`sol-translation`

本文件是 MGSPW JPVoice_CNText_V2 当前字体逆向结论的技术权威档案。事实来源限于当前仓库中的字体/XPR、分析报告、manifest、测试脚本与 fixture，以及相邻 `JPVoice_CNText_Experimental` 工作区保存的 full dump 报告、runtime 导出、rekey 审计和用户已确认的实机结果。本轮没有重新进行大规模逆向，也没有修改任何 production 字体、EXE 或翻译资源。

证据标签：

| 标签 | 含义 |
|---|---|
| `PROVEN` | 有 byte-level、dump、round-trip 或明确实机结果支持。 |
| `HIGH CONFIDENCE` | 多项证据一致，但尚缺独立实机或完整端到端验证。 |
| `HISTORICAL / RETRACTED` | 曾用于指导实验，已被更强证据推翻，不得作为当前结论。 |
| `UNKNOWN` | 现有资料不足；不得自行补全。 |

## 1. Current canonical conclusions

```ini
JPN001C_RUNTIME_DIMENSION_PATCH_PROVEN = YES
JPN001C_4096x4096_RUNTIME_PATCH_PROVEN = YES
JPN001C_PATCHED_MLG000E_RUNTIME_COMPATIBILITY = PROVEN
JPN001C_FIXED_2_MIB_CAPACITY = RETRACTED
JPN001C_4096x4096_UNSUPPORTED = RETRACTED
```

当前 production 阻碍的最终解释是：JPN small-font active path 以硬编码 `2048×1024` 创建并 Map 目标纹理，同时按 XPR 的真实 `data_size` 执行 1:4 decode/expansion。当输入 atlas 大于 `2048×1024` 时，目标容量与转换长度失配；修改 XPR TX2D geometry 本身不会改变该 active runtime initializer。同步 patch runtime Width/Height 后，`2048×1025` 与 `4096×4096` 均已实机通过。

## 2. Official font topology — `PROVEN`

| lane | size/path | selector |
|---|---|---|
| MLG / international | large | `0007ccd8.xpr` |
| MLG / international | small | `000ebbe8.xpr` |
| JPN | large | `00c7c9f9.xpr` |
| JPN | small | `001cbbd1.xpr` |

对应关系：

```text
0007ccd8.xpr  <->  00c7c9f9.xpr   (large)
000ebbe8.xpr  <->  001cbbd1.xpr   (small)
```

不得再描述为“clean JPN 有四套字体”。`0007/000e` 属于 MLG/reference lane；`00c7/001c` 才是 JPN runtime native font path。仓库把多 lane 文件集中在 `font/` 下是为比较和 provenance 分析，不改变官方拓扑。

主要证据：[`FONT_SOURCE_TOPOLOGY.md`](../../font/analysis/FONT_SOURCE_TOPOLOGY.md)、[`FONT_THREEWAY_CENSUS.md`](../../font/analysis/FONT_THREEWAY_CENSUS.md)。

## 3. OuterCrypt / pure rekey — `PROVEN`

- OuterCrypt seed 由 filename stem 决定；扩展名前的文件名参与 `filename_seed()`。
- pure rekey 只改变文件名相关的外层 XOR 加密层。
- 合格的 pure rekey 必须满足：源文件按源 selector 解密、同一 plaintext 按目标 selector 重加密、目标回读后与源 decrypted XPR plaintext byte-for-byte identical。
- pure rekey 不修改 USER/FontData、charmap、GlyphRecord、TX2D descriptor、atlas bitmap 或 XPR2 resource topology。

已经实机证明：

```text
clean MLG 000ebbe8.xpr
  -> decrypt with 000e seed
  -> plaintext unchanged
  -> encrypt with 001c seed
  -> JPN runtime loads successfully
```

因此 clean MLG000e 与 clean JPN001c 的 FontData 结构差异不意味着 JPN runtime 无法加载 MLG000e。patched MLG000e 的同一兼容性也在 runtime dimension patch 后得到最终实机证明。

追溯注意：`MLG000E_JPN001C_REKEY_AUDIT.md` 的旧 A/B/C 表仍把 clean MLG000e rekey 样本 B 标为“待实机”；该行是最终实机确认之前的历史状态，已被本归档记录的 clean-rekey 实机结果取代，不得继续引用为 current status。

主要证据：[`MLG000E_JPN001C_REKEY_AUDIT.md`](../../../JPVoice_CNText_Experimental/MLG000E_JPN001C_REKEY_AUDIT.md)、[`PATCHED_MLG000E_REKEY_V2_AUDIT.md`](../../../JPVoice_CNText_Experimental/PATCHED_MLG000E_REKEY_V2_AUDIT.md)、[`FONT_V2_CODE_ARCHAEOLOGY.md`](../../font/analysis/FONT_V2_CODE_ARCHAEOLOGY.md)。

## 4. Clean JPN001c structure — `PROVEN`

以下只记录 parser、hash 与现有报告明确确认的数据：

| field | clean `font/JPN/001cbbd1.xpr` |
|---|---:|
| encrypted size | `2,234,396` / `0x22181C` |
| encrypted SHA256 | `5625066b835e6f26f310781fbbd3ef4f9ea93a77be2a4044289c11b74a767414` |
| decrypted SHA256 | `f4fdb335a56f81bee4e4a13be71f5518827ebcf42fbfa86d30d2f1de3c6dd025` |
| XPR header size | `0x21810` |
| XPR data_size | `0x200000` |
| resource count | `2` (`TX2D/FontTexture`, `USER/FontData`) |
| TX2D descriptor | file `0x5C`, size `0x34` |
| texture data offset | `0x2181C` |
| USER | file `0x90`, size `0x214CA` |
| FontData fixed header | USER relative `0x0000..0x15` |
| last_code | `U+FF1F` |
| dense charmap | USER relative `0x16..0x1FE57`; BE u16 entries |
| glyph-count prefix | USER relative `0x1FE58`, raw `0167` = `359` |
| GlyphRecord table | USER relative `0x1FE5A`; 359 records; stride `0x10` |
| mapped codepoints | `358` |
| record suffix | none; record table ends at USER end |
| cell height | `66` / `66` |
| TX2D | `2048×1024`, pitch `2048`, format `2`, tiled `0`, endian `0` |
| texture storage | linear 8-bit texel, `1 byte/pixel` |

GlyphRecord fields are parsed as eight big-endian u16 values:

```text
u0, v0, u1, v1, bearing_x_raw, width, advance, reserved
```

Confirmed mapping examples:

| codepoint | glyph index | record/rect evidence |
|---|---:|---|
| `中 U+4E2D` | `143` | record file `0x207DA`; rect `(1059,269)-(1125,335)`; width `66`, bearing `8`, advance `70` |
| `我 U+6211` | `239` | rect `(1733,470)-(1799,536)`; runtime TX2D replacement changed the Loading-page glyph |
| `们 U+4EEC` | `0` | missing/fallback path in clean 001c |
| `陆 U+9646` | `0` | missing/fallback path in clean 001c |
| `拘 U+62D8` | `0` | missing/fallback path in clean 001c |

Record `0` is unmapped by the forward charmap but contains nonzero fallback pixels; it is not a safe free glyph slot.

主要证据：[`SMALL_JPN_FONT_PAIR_ANALYSIS.md`](../../font/analysis/SMALL_JPN_FONT_PAIR_ANALYSIS.md)、[`SMALL_JPN_APPEND_RECORD_LAYOUT.md`](../../font/analysis/SMALL_JPN_APPEND_RECORD_LAYOUT.md)、[`SMALL_JPN_RUNTIME_ATLAS_SELECTOR_TEST.md`](../../small_jpn_runtime_atlas_selector_poc/SMALL_JPN_RUNTIME_ATLAS_SELECTOR_TEST.md)。

## 5. The 2 MiB crash investigation: evidence chain

### 5.1 Initial boundary observations — `PROVEN`

| geometry | payload/data_size | result before runtime patch |
|---|---:|---|
| `2048×1023` | `0x1FF800` | works |
| `2048×1024` | `0x200000` | works |
| `2048×1025` | `0x200800` | crashes |

Equal-payload geometry tests also entered the game:

| geometry | payload/data_size | result before runtime patch |
|---|---:|---|
| `2048×1024` | `0x200000` | works |
| `1024×2048` | `0x200000` | works |
| `4096×512` | `0x200000` | works |

These tests ruled out a fixed XPR geometry rule requiring width `2048`, height `1024`, or pitch `2048`. They established a boundary symptom, not an intrinsic 2 MiB format limit.

### 5.2 Full-dump proof — `PROVEN`

The first real failure was:

```text
exception: C0000005 WRITE
fault RVA: main+0x1DE60
instruction: mov word ptr [rax-2],0xFFFF
input length: 0x200800
mapped target region: 0x800000 bytes
decode/expansion: 1 input byte -> 4 output bytes
```

Capacity arithmetic:

```text
0x200000 * 4 = 0x800000   fits the mapped target exactly
0x200800 * 4 = 0x802000   requires 0x2000 additional bytes
```

The faulting write address was exactly `mapped_region_end`, so the first overflow occurs at the first output unit beyond the `0x800000` allocation. This was not a shell-size guess, D3D Map failure, or a later glyph-table parse error.

主要证据：[`JPN001C_0x200800_CRASH_DUMP_ANALYSIS.md`](../../../JPVoice_CNText_Experimental/JPN001C_0x200800_CRASH_DUMP_ANALYSIS.md)、[`JPN001C_TARGET_BUFFER_ALLOCATION_ROOT_CAUSE.md`](../../../JPVoice_CNText_Experimental/JPN001C_TARGET_BUFFER_ALLOCATION_ROOT_CAUSE.md)。

## 6. Runtime dimension root cause — `PROVEN`

Changing the XPR TX2D packed dimensions to `2048×1025` did not change the active runtime object. The active path initializes dimensions at the caller:

```asm
main+0x436AB: mov r9d,0x400
main+0x436B1: lea rdx,[rbp-0x50]
main+0x436B5: mov r8d,0x800
main+0x436BB: lea rcx,[rip+...]
main+0x436C2: call main+0x42CD0
```

Therefore:

```text
Width  = r8d = 0x800 = 2048
Height = r9d = 0x400 = 1024
```

Proven propagation chain:

```text
hardcoded caller Width/Height
  -> source descriptor +0x0C / +0x10
  -> runtime object +0x24 Width / +0x28 Height
  -> D3D11_TEXTURE2D_DESC
  -> CreateTexture2D
  -> Map
  -> decode/copy target
```

The input length follows a separate source:

```text
XPR/resource true data_size
  -> source descriptor +0x30 low dword
  -> runtime object +0x48
  -> decode/copy input length
```

Thus the crash condition is:

```text
XPR data_size > Width * Height
=> decode output (data_size * 4) > mapped RGBA8 target (Width * Height * 4)
=> C0000005 WRITE at mapped region end
```

XPR TX2D geometry is valid metadata, but this JPN001c active initializer does not use the modified TX2D geometry to select its final target Width/Height.

主要证据：[`JPN001C_XPR_DIMENSION_METADATA_TRACE.md`](../../../JPVoice_CNText_Experimental/JPN001C_XPR_DIMENSION_METADATA_TRACE.md)、[`JPN001C_2048x1025_SYNC_RUNTIME_DIFF.md`](../../../JPVoice_CNText_Experimental/JPN001C_2048x1025_SYNC_RUNTIME_DIFF.md)。

## 7. 2048×1025 runtime PoC — `PROVEN`

Input XPR:

```text
Width     = 2048
Height    = 1025
data_size = 0x200800
```

Runtime patch:

```text
main+0x436AB Height: 0x400 -> 0x401
main+0x436B5 Width:  0x800 -> 0x800 (unchanged)
```

Instruction bytes:

```text
Height original: 41 B9 00 04 00 00
Height patched:  41 B9 01 04 00 00
Width unchanged: 41 B8 00 08 00 00
```

User-confirmed real-machine result: the game successfully entered instead of crashing.

```ini
JPN001C_RUNTIME_DIMENSION_PATCH_PROVEN = YES
```

This retracts the claim that JPN001c can only process `0x200000` / 2 MiB. The tested failure was caused by an unsynchronized runtime target, not an intrinsic format capacity.

## 8. Patched MLG000e 4096×4096 final runtime validation — `PROVEN`

Input/reference artifact:

```text
third-party patched MLG_CN/000ebbe8.xpr
TX2D       = 4096x4096
pitch      = 4096
data_size  = 0x1000000
records    = 3146
mapped     = 3145
USER size  = 0x2C378
```

Operation:

```text
decrypt as 000ebbe8.xpr
-> keep decrypted XPR plaintext byte-for-byte identical
-> encrypt as 001cbbd1.xpr
```

Runtime patch:

```text
main+0x436AB Height: 1024 -> 4096
main+0x436B5 Width:  2048 -> 4096
```

Real-machine result:

- game starts normally;
- the original `main+0x1DE60` overflow no longer occurs;
- small UI / Loading missing Chinese glyphs and `·` fallback disappear;
- actual Chinese glyphs render correctly.

```ini
JPN001C_4096x4096_RUNTIME_PATCH_PROVEN = YES
JPN001C_PATCHED_MLG000E_RUNTIME_COMPATIBILITY = PROVEN
```

This proves that 4096×4096 itself is supported after the target descriptor is synchronized; a 16 MiB TX2D is not itself the problem; 3146 GlyphRecords and the patched USER are not the crash cause; and the patched shell is not the crash cause. The core blocker was the JPN runtime initializer's hardcoded `2048×1024` target dimensions.

Important scope: this third-party font is a compatibility proof, reverse-engineering reference, and runtime-capacity proof. It is not the future production dependency.

## 9. Large font 00c7 final confirmed state

### Proven working compatibility route — `PROVEN`

The JPN large selector is `00c7c9f9.xpr`. The existing working V2 route is:

```text
patched MLG large 0007ccd8.xpr
  -> decrypt with 0007 seed
  -> keep XPR2 plaintext unchanged
  -> encrypt with 00c7 seed
  -> JPN large 00c7c9f9.xpr
```

The resulting `00c7c9f9.xpr` is byte-identical at the decrypted/plaintext level to the patched MLG0007 source and is an exact reproduction of the historical V2 output. Its atlas is already `4096×4096`, pitch `4096`, format `2`, linear 8-bit; the JPN large path does not require the JPN001c small-path runtime dimension patch.

Separately, clean-JPN-00c7 append PoCs proved the native data chain:

- direct charmap index semantics;
- runtime-visible glyph count mirror at `USER +0x1FED4`;
- append index `3209` works after count `3209 -> 3210`;
- a new atlas slot works;
- a generated real `厥 U+53A5` glyph renders in game.

These PoCs prove native 00c7 extensibility, but the repository does not yet contain a completed, publicly releasable, full-corpus, self-owned production builder. That remaining productionization work is described in `FONT_CUSTOM_BUILD_PLAN.md`.

### Unknown / not yet productionized

- A complete self-owned large-font rebuild from clean JPN00c7 for the full translation charset is `NOT YET PRODUCTIONIZED`.
- A fully validated large multi-glyph relocation/repack pipeline remains `UNKNOWN` beyond the existing append PoCs.
- The exact future release font among the open-source candidates is `UNKNOWN`.

主要证据：[`FONT_V2_CODE_ARCHAEOLOGY.md`](../../font/analysis/FONT_V2_CODE_ARCHAEOLOGY.md)、[`FONT_GLYPH_INDEX_BOUNDARY_AUDIT.md`](../../font_poc_00c7_diagnostics_boundary/FONT_GLYPH_INDEX_BOUNDARY_AUDIT.md)、[`FONT_00C7_TEST2B_COUNT_PATCH.md`](../../font_poc_00c7_diagnostics_boundary/TEST2B_COUNT_PATCH/FONT_00C7_TEST2B_COUNT_PATCH.md)、[`FONT_REAL_GLYPH_JUE.md`](../../font_poc_00c7_diagnostics_boundary/TEST_REAL_GLYPH_JUE/FONT_REAL_GLYPH_JUE.md)。

## 10. Retired / retracted hypotheses

| retired hypothesis | status | why it was overturned |
|---|---|---|
| “JPN001c has a fixed 2 MiB capacity” | `HISTORICAL / RETRACTED` | `2048×1025 / 0x200800` works when Height is patched to `0x401`; `4096×4096 / 0x1000000` works when Width/Height are patched to `0x1000`. |
| “4096×4096 geometry itself is unsupported by JPN001c” | `HISTORICAL / RETRACTED` | The patched 4096×4096 MLG000e plaintext loads and renders Chinese after runtime dimension synchronization. |
| “width must be 2048” | `HISTORICAL / RETRACTED` | `1024×2048` and `4096×512` equal-capacity fixtures entered before the patch; 4096×4096 entered after the patch. |
| “height must be 1024” | `HISTORICAL / RETRACTED` | `1024×2048` entered before the patch; runtime-patched `2048×1025` and `4096×4096` entered. |
| “pitch must be 2048” | `HISTORICAL / RETRACTED` | Equal-capacity alternate geometries ruled out a fixed pitch rule; the proven 4096×4096 input uses pitch 4096. |
| “patched MLG000e USER / 3146 records cause the crash” | `HISTORICAL / RETRACTED` | The same byte-identical plaintext works when runtime dimensions match the atlas. |
| “the patched shell causes the crash” | `HISTORICAL / RETRACTED` | Full dump locates the first fault in the target decode write at mapped-region end; the same shell succeeds after the dimension patch. |
| “Chinese must be compressed back into 2048×1024” | `HISTORICAL / RETRACTED` | 4096×4096 is proven at runtime and eliminates the missing glyphs. |
| “a roughly 17 MiB file itself causes the crash” | `HISTORICAL / RETRACTED` | The same 16,959,500-byte artifact works after target dimensions are synchronized. |
| “changing XPR TX2D height alone changes runtime Height” | `HISTORICAL / RETRACTED` | Dumped active path still used caller-provided `0x400`; Width/Height are hardcoded before resource construction. |
| “Loading uses 001c FontData with 00c7 TX2D” | `HISTORICAL / RETRACTED` | Replacing only glyph 239 in 001c's own TX2D changed the in-game Loading glyph. |

## 11. Experimental Evidence Index

No item listed below is deleted by this archive pass. `SAFE TO ARCHIVE` means it should eventually be moved out of Git or primary working storage after hashes and derived evidence are preserved; it does not authorize deletion now.

### Crash dumps and runtime exports

| asset | classification | purpose |
|---|---|---|
| `D:\GAME\test\mgspw_crash_dumps\METAL GEAR SOLID PEACE WALKER.exe_260916_051544.dmp` | `SAFE TO ARCHIVE` | Original `0x200800` full dump; ~6.79 GB. Preserve locally until external archival copy/hash is confirmed. |
| `D:\GAME\test\mgspw_crash_dumps\METAL GEAR SOLID PEACE WALKER.exe_260916_130921.dmp` | `SAFE TO ARCHIVE` | Synchronized-XPR/no-runtime-patch comparison dump; ~6.78 GB. |
| `JPVoice_CNText_Experimental/JPN001C_0x200800_runtime_decoded_text.bin` | `KEEP` | Decoded runtime `.text`; basis for RVAs and active initializer. |
| `.../JPN001C_0x200800_runtime_decoded_bind.bin` | `REFERENCE ONLY` | Decoded `.bind` export. |
| `.../JPN001C_0x200800_fault_function.bin` | `KEEP` | Compact fault-loop bytes. |
| `.../JPN001C_0x200800_caller_context.bin` | `KEEP` | Caller/resource-construction context. |
| `.../JPN001C_0x200800_runtime_exports.json` | `KEEP` | Export offsets, sizes, and SHA256 metadata. |

### Root-cause and rekey reports

| asset | classification | purpose |
|---|---|---|
| `JPN001C_0x200800_CRASH_DUMP_ANALYSIS.md` | `KEEP` | First-fault and 1:4 expansion proof. |
| `JPN001C_TARGET_BUFFER_ALLOCATION_ROOT_CAUSE.md` | `KEEP` | Mapped target allocation/capacity proof. |
| `JPN001C_XPR_DIMENSION_METADATA_TRACE.md` | `KEEP` | File-layer TX2D dimension trace; obsolete intermediate conclusion is explicitly retracted in-file. |
| `JPN001C_2048x1025_SYNC_RUNTIME_DIFF.md` | `KEEP` | Source descriptor, D3D desc, active hardcoded dimension path. |
| `JPN001C_TEXTURE_CAPACITY_ROOT_CAUSE.md` | `REFERENCE ONLY` | Historical static investigation; final runtime correction retained at top. |
| `MLG000E_JPN001C_REKEY_AUDIT.md` | `KEEP` | Clean/patched 000e→001c topology and compatibility audit. |
| `PATCHED_MLG000E_REKEY_V2_AUDIT.md` | `KEEP` | Byte-identical patched rekey and final runtime result. |
| `TX2D_RESIZE_BUILDER_AUDIT.md` | `REFERENCE ONLY` | Historical fixture-builder audit, not current production design. |

### Runtime patch and rekey PoC

| asset | classification | purpose |
|---|---|---|
| `JPVoice_CNText_Experimental/mgspw_001c_height_poc.cpp` | `KEEP` | ASLR-aware runtime Width/Height patch PoC with full-byte checks and fail-closed behavior. |
| `.../rekey_patched_mlg000e_4096_runtime.py` | `KEEP` | Pure rekey generator with plaintext equality verification. |
| `.../rekey_patched_mlg000e_v2.py` | `REFERENCE ONLY` | Earlier audit/rekey implementation. |
| `.../audit_clean_mlg000e_rekey.py` | `REFERENCE ONLY` | Clean/patched comparative audit generator. |
| `.../tools/OuterCrypt.cpp` and `OuterCrypt.exe` | `KEEP` | Historical authoritative filename-seeded outer transform implementation. |

### Fixture XPRs

| asset/group | classification | purpose |
|---|---|---|
| `TEST_CLEAN_MLG000E_AS_JPN001C.xpr` | `KEEP` | Clean cross-runtime rekey proof. |
| `TEST_PATCHED_MLG000E_AS_JPN001C_4096_RUNTIME.xpr` | `KEEP` | Final 4096×4096 runtime-proven artifact. |
| `TEST_PATCHED_MLG000E_AS_JPN001C_V2.xpr` | `REFERENCE ONLY` | Equivalent pure-rekey audit artifact. |
| `TEST_VALID_JPN001C_DIMENSION_SYNC_2048x1025.xpr` | `KEEP` | Clean-001c structure with synchronized file-layer 2048×1025 metadata. |
| `TEST_VALID_SHELL_2048x1023_AS_JPN001C.xpr`, `TEST_VALID_SHELL_2048x1025_AS_JPN001C.xpr` | `KEEP` | Boundary evidence around the clean 2048×1024 baseline. |
| `TEST_VALID_SHELL_1024x2048_AS_JPN001C.xpr`, `TEST_VALID_SHELL_4096x512_AS_JPN001C.xpr` | `KEEP` | Equal-capacity geometry evidence. |
| `TEST_VALID_SHELL_2048x2048`, `4096x1024` fixtures | `REFERENCE ONLY` | Pre-patch over-capacity failures. |
| patched-layout / clean-USER hybrid fixtures | `REFERENCE ONLY` | Isolation experiments; not production candidates. |
| superseded TX2D-only and old patched-shell variants | `OBSOLETE` | Retain only to reproduce retired hypotheses; never use as Golden. |

### V2 repository reports, scripts, and fixtures

| asset/group | classification | purpose |
|---|---|---|
| `font/analysis/FONT_SOURCE_TOPOLOGY.md` | `KEEP` | Official selector/lane topology. |
| `font/analysis/FONT_V2_CODE_ARCHAEOLOGY.md` | `KEEP` | Historical working 00c7 copy/rekey route. |
| `font/analysis/FONT_THREEWAY_CENSUS.md` and census CSVs | `KEEP` | Structural and charset inventory. |
| `font/analysis/SMALL_JPN_FONT_PAIR_ANALYSIS.md` | `KEEP` | Clean 001c structure and mappings. |
| `small_jpn_runtime_atlas_selector_poc/` | `KEEP` | Runtime proof that Loading uses 001c own TX2D. |
| `small_jpn_men_append_poc/` | `REFERENCE ONLY` | One-glyph native append technique; superseded as capacity solution by full 4096 path. |
| `font_poc_00c7_diagnostics_boundary/` | `KEEP` | 00c7 count, new-atlas, real-glyph, and style PoCs. |
| `font_poc_00c7_diagnostics/` | `REFERENCE ONLY` | Earlier diagnostics, including failures later explained by count semantics. |
| `core/xpr_font.py`, `tests/test_xpr_font.py` | `KEEP` | Current parser/rebuild and tests; not yet a production builder guarantee. |
| `tools/Build-FontXprV2.py` | `REFERENCE ONLY` | Experimental selector-aware builder; current full self-owned production builder remains not productionized. |
| font coverage/corpus CSVs under `font/analysis/` | `KEEP` | Charset census inputs for the next builder phase. |

### Historical build scripts

| asset/group | classification | purpose |
|---|---|---|
| `build_valid_shell_tx2d_boundary_sizes.py` | `REFERENCE ONLY` | Boundary fixture generation. |
| `build_valid_shell_tx2d_equal_capacity_shapes.py` | `REFERENCE ONLY` | Width/height/pitch hypothesis elimination. |
| `build_jpn001c_dimension_metadata_sync.py` | `REFERENCE ONLY` | File-layer dimension-sync fixture. |
| `build_test_tx2d_only.py`, `build_test_tx2d_size_variants.py` | `OBSOLETE` | Early isolation experiments; not current root-cause model. |
| `build_patched_shell_clean_user_clean_tx2d.py`, `build_patched_layout_clean_user_hybrid.py` | `OBSOLETE` | Historical hybrid hypotheses, retained for traceability only. |

## 12. Archive boundary

This archive records what is proven and what remains unimplemented. It does not declare the third-party MLG font a production dependency; it does not authorize shipping Microsoft font data; and it does not claim that the self-owned full-corpus builder already exists. The next implementation phase begins with `FONT_CUSTOM_BUILD_PLAN.md` after this documentation-only checkpoint.
