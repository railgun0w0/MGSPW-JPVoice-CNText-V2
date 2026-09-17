# FONT Technical State（Reference Summary）

本文件是旧位置保留的 FONT 状态摘要。最新权威入口是 `font/doc/README.md`；正式根因归档、Golden Baseline 与下一阶段设计分别位于 `font/doc/FONT_TECHNICAL_ARCHIVE.md`、`FONT_PRODUCTION_BASELINE.md`、`FONT_CUSTOM_BUILD_PLAN.md`。涉及 JPN001c 2 MiB/4096×4096/runtime dimension 的结论以 `font/doc/` 为准。本文只整理已经存在的报告、manifest、静态读回和实机记录；不替代、删除或重写历史实验产物。

整理日期：2026-09-16（Asia/Hong_Kong）

## 当前状态摘要

```ini
GOLDEN_V2_FONT_PIPELINE = PRESERVED

MAIN_00C7_FORMAT = UNDERSTOOD
MAIN_00C7_APPEND_RUNTIME = VALIDATED_ON_PATCHED_MLG0007_DERIVED_00C7
GENERATED_GLYPH_RUNTIME = VALIDATED

LOADING_FONT_PATH = RUNTIME_CONFIRMED
LOADING_GLYPH_REPLACEMENT = VALIDATED
LOADING_FONT_STYLE = UNRESOLVED

JPN001C_RUNTIME_DIMENSION_PATCH_PROVEN = YES
JPN001C_4096x4096_RUNTIME_PATCH_PROVEN = YES
JPN001C_PATCHED_MLG000E_RUNTIME_COMPATIBILITY = PROVEN
JPN001C_FIXED_2_MIB_CAPACITY = RETRACTED
CLEAN_JPN_001C_STOCK_2048x1024_CAPACITY = SUFFICIENT
STOCK_PROFILE = 51PX_PADDING1
EXE_PATCH_REQUIRED = NO
CLEAN_JPN_001C_STOCK_SELF_OWNED_RUNTIME = PROVEN

FINAL_MAIN_FONT_STYLE = UNDECIDED
FINAL_SMALL_FONT_STYLE = UNDECIDED
FINAL_GLYPH_SOURCE_POLICY = SELF_OWNED_REBUILD_DECIDED

LARGE_MULTI_GLYPH_RELOCATION = UNRESOLVED
PRODUCTION_FONT_BUILDER = NOT_COMPLETED
```

Phase 2B.1 stock-geometry salvage is now `RUNTIME_CONFIRMED` for the exact
`LOOSE_OLANG/00D0C740` selector corpus: a self-owned Noto Sans SC Bold
`51px / padding 1` fixture fits the clean JPN001c `2048×1024` atlas with
`549` records / `548` mapped and no crop, overlap, or overflow; the user then
confirmed normal game entry and correct Loading display without fallback dots.
The proof is selector-specific: the other 709 UNKNOWN resource groups remain
unproven. It does not decide the final small-font profile.

本文使用以下证据标签：

| 标签 | 含义 |
|---|---|
| `RUNTIME_CONFIRMED` | 有明确实机 fixture/结果，运行时行为已验证。 |
| `STATIC_CONFIRMED` | 有文件、parser、hash、byte diff 或 manifest 证据，但不等于实机通过。 |
| `HYPOTHESIS` | 有结构或行为上的合理解释，尚未达到确认标准。 |
| `UNRESOLVED` | 当前证据不足以做出安全结论。 |
| `FAILED / DEPRECATED EXPERIMENT` | 实验已失败或被后续更强证据取代；保留作为历史证据。 |

## 1. Golden V2 FONT pipeline

状态：`RUNTIME_CONFIRMED`（原 V2 成功路线）+ `STATIC_CONFIRMED`（代码考古与 byte-identical/rekey 证据）。

原 V2 默认 FONT 路线必须保留：

```text
MLG_CN/0007ccd8.xpr
    → 简单复制
    → JPN_CN/0007ccd8.xpr

MLG_CN/000ebbe8.xpr
    → 简单复制
    → JPN_CN/000ebbe8.xpr

MLG_CN/0007ccd8.xpr
    → 用 0007 文件名 seed 解密
    → plaintext XPR2 逻辑内容不变
    → 用 00c7 文件名 seed 重新加密
    → JPN_CN/00c7c9f9.xpr
```

原 V2 没有重建内部 `FontData` 或 `TX2D`。官方 JPN base 只有 `00c7c9f9.xpr`（large）与 `001cbbd1.xpr`（small）；`001cbbd1.xpr` 不属于原稳定 V2 的默认输出，后来作为 Loading/SMALL_JPN 的独立运行时资源被单独定位，不能反推为主字体默认 pipeline。

```ini
GOLDEN_V2_FONT_PIPELINE = PRESERVE
```

证据：[`FONT_V2_CODE_ARCHAEOLOGY.md`](../font/analysis/FONT_V2_CODE_ARCHAEOLOGY.md)。该报告也记录了历史上找到的 copy/rekey 工具链，以及原始 V2 builder 未进入 Git 的事实。

## 2. 六套 unique logical fonts

状态：`STATIC_CONFIRMED`。

逻辑内容去重后保留六套：官方 JPN 两套、MLG 原始两套、MLG 中文扩展两套。这里的本地六套分析对象不是“clean JPN 六套”。

```text
JPN-001C
JPN-00C7
MLG-0007
MLG-000E
MLG_CN-0007
MLG_CN-000E
```

`JPN_CN` 只用于 provenance 验证，不作为第七套字体重复统计：

```text
JPN_CN/0007ccd8.xpr == MLG_CN-0007 byte-for-byte
JPN_CN/000ebbe8.xpr == MLG_CN-000E byte-for-byte
JPN_CN/00c7c9f9.xpr == MLG_CN-0007 plaintext re-encrypted with the 00c7 seed
```

相关证据位于 `font/analysis/FONT_THREEWAY_CENSUS.md`、`font/analysis/FONT_SIX_UNIQUE_CHARMAP.csv`。历史 copy/rekey provenance 另见已入库的 [`FONT_V2_CODE_ARCHAEOLOGY.md`](../font/analysis/FONT_V2_CODE_ARCHAEOLOGY.md)。

## 3. 主字体 00c7 append 技术

状态：patched MLG_CN0007-derived、以 `00c7` seed rekey 的基线为 `RUNTIME_CONFIRMED`；clean JPN00c7 self-owned full-rebuild runtime compatibility 已由 Phase 2A 实机 fixture `PROVEN`。append-only semantics beyond that fixture remain `UNRESOLVED`。

本节旧称“clean-JPN-00c7 append”不正确。现有 TEST2B、TEST3B 与 `厥` glyph PoC 的输入链具有以下可区分计数：

| baseline | glyph records | mapped codepoints | provenance |
|---|---:|---:|---|
| clean JPN `00c7c9f9.xpr` | `2309` | `2308` | 官方 JPN large，未作为现有 `3209→3210` PoC 的输入 |
| patched `MLG_CN/0007ccd8.xpr` plaintext rekeyed as `00c7c9f9.xpr` | `3209` | `3208` | TEST2B / TEST3B / `厥` glyph PoC 的实际 baseline |

当前已验证的主字体访问链为：

```text
Unicode charmap
    → glyph index N
    → GlyphRecord[N]
    → atlas UV rectangle
    → TX2D bitmap
```

记录索引语义为 `DIRECT`：`charmap value N → GlyphRecord[N]`。下表只描述 patched MLG_CN0007-derived/rekeyed 00c7 baseline 的实机边界结果：

| 实验 | 结果 | 说明 |
|---|---|---|
| 现有 glyph remap | `PASS` | 已有 glyph 可被新 codepoint 直接引用。 |
| max existing index `3208` | `PASS` | `U+FF1B ；` 被 `U+53A5` 引用后正常显示。 |
| append `3209`，不更新 count | `FAIL / blank` | runtime 不接受未登记的新 index。 |
| append `3209` + count patch | `PASS` | `USER +0x1FED4` 的 BE u32 `3209 → 3210`。 |
| new atlas slot | `PASS` | 新 UV 和 TX2D 空白区域均被接受。 |
| generated real glyph `厥` | `PASS` | 新 Unicode glyph 在 00c7 运行时正常显示。 |
| 多 glyph 产物 `厥 + 拘` | `STATIC_CONFIRMED` | 当前仓库有完整静态 manifest；未找到独立的 `拘束` 实机记录，因此不在本文升级为多 glyph runtime 结论。 |

runtime-visible glyph count 位于：

```text
USER +0x1FED4
big-endian u32

3209 = 0x00000C89
3210 = 0x00000C8A
```

这不是原先误判的 alignment padding。单字 append 已证明：在 patched MLG_CN0007-derived/rekeyed 00c7 baseline 上，旧 glyph index、旧 GlyphRecord、旧 charmap entry 和旧 atlas 像素可以保持不变，新增 record、count mirror、USER size、charmap entry 和新 slot 可以被 runtime 接受。该结果不能直接升级为 clean JPN00c7 `2309→2310` 的 append-only 结构证明；另有 Phase 2A clean-JPN full-rebuild fixture 已通过真实运行验证，但其证明范围不包含该 append-only 语义。

相关证据位于 `font/font_poc_00c7_diagnostics_boundary/`；这些是实验/回归资产，不属于 production 结论入口。

## 4. Generated glyph 与风格实验

状态：patched MLG_CN0007-derived PoC 的运行时技术链为 `RUNTIME_CONFIRMED`；production 来源策略已经决定为 `SELF_OWNED_REBUILD`，具体 source font 与 large/small raster profile 仍为 `UNDECIDED`。

- `Noto Sans SC Bold`：D profile，`56px`，`58×67` cell，目标 `厥` bbox 约 `[2,7,56,59]`，baseline ink bottom `y=59`。D 已实机比较通过，并保留为当前 generated fallback profile。
- `Microsoft YaHei UI Bold`：实际 metadata 为 `C:\\Windows\\Fonts\\msyhbd.ttc` face `1`，family `Microsoft YaHei UI`，style `Bold`；`55px`、Pillow/FreeType BASIC、8-bit L 灰度。该 `厥` 版本已实机正常运行，视觉效果可接受。
- YaHei 曾出现一次闪退，但后续未能稳定复现。二进制差分报告确认：XPR 结构、文件大小、外层加密 round-trip 均有效，所有 plaintext 差异都在目标 atlas slot 内，slot 外差异为 `0`。因此不能写成“YaHei 会导致闪退”。

```ini
YAHEI_CRASH = NOT_REPRODUCIBLE
FINAL_GLYPH_SOURCE_POLICY = SELF_OWNED_REBUILD_DECIDED
```

相关证据位于 `font/font_poc_00c7_diagnostics_boundary/`，包括 `TEST_REAL_GLYPH_JUE_STYLE_TUNING/` 与 `TEST_YAHEI_UI_BOLD_JUE/`；这些是实验/回归资产，不属于 production 结论入口。

## 5. JPN donor 与 generated glyph

状态：`STATIC_CONFIRMED` + 局部 `RUNTIME_CONFIRMED`；production 路线已决定为 `SELF_OWNED_REBUILD`。

`拘 U+62D8` 在 clean JPN `00c7` 中存在原生 glyph；同一字符也已经用 generated font 成功生成并进入 patched MLG_CN0007-derived 主字体 PoC。现有报告显示两种来源的视觉风格有明显差别。production 不再在“保留 MLG”“MLG + donor hybrid”“self-owned rebuild”三条路线之间摇摆：正式方向固定为从 clean JPN selectors 构建完全自有字库，不把第三方 MLG bitmap 作为依赖。clean JPN 非 Han/ASCII/kana/game-specific glyph 的保留规则，以及 Han 使用 SC glyph 覆盖的策略，以 `font/doc/FONT_CUSTOM_BUILD_PLAN.md` 为准。

```ini
FINAL_GLYPH_SOURCE_POLICY = SELF_OWNED_REBUILD_DECIDED
```

仍未决定的是具体开源 source font、large/small pixel size、baseline/advance/profile 与最终视觉 QA 标准；这些实现参数不改变 self-owned rebuild 的既定方向。

## 6. Loading quote / SMALL_JPN FONT

状态：`RUNTIME_CONFIRMED`。

最新实际 Loading 实验收敛到单文件、自带 TX2D 的路径：

```ini
LOADING_FONTDATA = JPN/001cbbd1.xpr
LOADING_FONT_TEXTURE = JPN/001cbbd1.xpr own TX2D
LOADING_FONT_PATH = RUNTIME_CONFIRMED
LOADING_GLYPH_REPLACEMENT = RUNTIME_CONFIRMED
```

这不是根据屏幕字号或 coverage 推断，而是由 runtime fixture 直接验证：只修改 `JPN/001cbbd1.xpr` 自带 TX2D 中 `我 U+6211`、glyph index `239` 的像素时，Loading 页面中的“我”发生变化。此前的 `FontData=001c + FontTexture=00c7` 组合属于旧交叉分析假设，不是当前 Loading PoC 已确认的配对关系。

当前 Loading 字体结构与主 00c7 分开：`001c` 自带 `2048×1024`、`format=2`、`tiled=0`、`endian=0` 的线性 8-bit TX2D；原 record count `359`、mapped codepoint `358`。 `们 U+4EEC` 技术 PoC 的实际参数如下：

| 项目 | 已读回事实 |
|---|---|
| FontData selector | `JPN/001cbbd1.xpr` |
| FontTexture selector | `JPN/001cbbd1.xpr own TX2D` |
| charmap/glyph source | `U+4EEC → 359`；追加一条 GlyphRecord；donor 来自 `MLG-0007` 的 `们` index `729`，再适配到 SMALL_JPN cell |
| count field | USER record 前缀 `0x0167 → 0x0168`；旧 count `359 → 360` |
| USER size | `0x214CA → 0x214DA` |
| new atlas slot | `[0,805)-[66,871)` |
| runtime fixture | Loading 语录页；`们` 不再显示为 `·` |
| 结果 | `RUNTIME_CONFIRMED` 技术 PoC；视觉样式仍未定 |

`LOADING_FONT_STYLE = UNRESOLVED`：功能层面已经成功显示新增字符，但小字号 glyph 与原版 Loading / SMALL_JPN 风格差异明显。本轮不继续解决风格问题。

历史收敛：旧文档曾将 `LOADING_FONT_PATH` 标为 `UNRESOLVED`，并使用 charmap coverage / selector 进行定位；该结论已被 `001c` own-TX2D runtime 替换实验取代，但旧报告保留供追溯。

相关证据位于 `font/analysis/`、`font/small_jpn_runtime_atlas_selector_poc/` 和 `font/small_jpn_men_append_poc/`；这些仍是实验/回归资产。

## 7. Main 与 Loading/SMALL 必须分开

状态：`RUNTIME_CONFIRMED`（不同路径已被实机区分）。

主字体 `00c7` 与 Loading/SMALL `001c` 是不同显示场景的不同 FontData/TX2D 组合。不能仅根据画面上的字号判断 selector，也不能假设一份 `00c7` 字体会解决所有 UI。后续 production builder 必须把：

```text
MAIN FONT path
LOADING / SMALL FONT path
```

作为两个独立目标维护，并分别做 runtime fixture。

## 8. PSP 汉化版考古

状态：`STATIC_CONFIRMED`，用途边界为 `HYPOTHESIS` / 参考资料，不是 PC bitmap 直接来源。

相邻 Experimental 工作区的考古报告记录：

- `PW.CHS` 已提取约 `13,975` 条中文记录；主要文本容器为 `PSP_GAME/USRDIR/PW.CHS`。
- PSP 字体为 `PSP_GAME/USRDIR/MGP.PGF`，PGF0 revision 2/version 6。
- 字体 metadata 为 `Microsoft YaHei UI`、`Bold`；实际 PGF 有 `4bpp` 压缩位图、Unicode charmap，约 `11,974` mapped codepoints / `11,975` glyph records。
- PSP 与当前 PC `MLG_CN` 是 `DIFFERENT_FONT`：PSP glyph 通常约 `18×17/18`、advance 约 `18`；PC MLG 为 `58×67` cell、advance `62`，灰度/栅格/笔画统计也不相同。
- PSP 资料可用于旧译语料、字体来源线索、字形风格参考和 Unicode coverage 参考；不能写成可以把 PSP PGF bitmap 无损搬进 PC XPR。

PSP 考古报告（`LOCAL-ONLY`，位于仓库外）：`JPVoice_CNText_Experimental/psp/PSP_CN_ARCHAEOLOGY.md`。

## 9. 当前主字体 atlas / XPR 状态

状态：格式为 `STATIC_CONFIRMED`，单字/少量 append 为 `RUNTIME_CONFIRMED`，大规模扩展为 `UNRESOLVED`。

主 00c7 TX2D：

```ini
atlas = 4096x4096
pitch = 4096
format = 2
tiled = 0
endian = 0
storage = linear 1 byte/pixel
```

单字和少量 glyph append 已实机打通；但是一次增加大量 glyph 时，以下部分仍没有正式、可重复的 production builder：

```ini
USER_SECTION_GROWTH = NEEDS_BUILDER
RESOURCE_RELOCATION = NEEDS_BUILDER
TX2D_OFFSET_RELOCATION = NEEDS_BUILDER
LARGE_MULTI_GLYPH_RELOCATION = UNRESOLVED
PRODUCTION_FONT_BUILDER = NOT_COMPLETED
```

不要把单字 append PoC 当作大规模 relocation 已完成。

## 10. Failed / Deprecated experiments

以下实验全部保留；它们的失败结果是边界证据，不是当前推荐方案：

| 实验 | 状态 | 后来确认了什么 |
|---|---|---|
| selector-aware rebuild | `FAILED / DEPRECATED EXPERIMENT` | 大范围乱码；证明不能在未完成 selector/runtime 证据时重建多个字体路径。 |
| old expanded `001c` replacement without runtime dimension synchronization | `FAILED / DEPRECATED EXPERIMENT` | 后续 full dump 证明它把真实 input length 写入硬编码 `2048×1024` target；将 Width/Height patch 为 `4096×4096` 后，同一 patched MLG000e plaintext 已实机成功。不得再把旧失败解释为 2 MiB 固定上限、4096×4096 不支持或 USER/3146 records 不兼容。 |
| append new index without glyph-count update | `FAILED / DEPRECATED EXPERIMENT` | 新 index `3209` 空白，直接暴露 runtime-visible glyph count mirror。 |
| original new-atlas test before count fix | `FAILED / DEPRECATED EXPERIMENT` | 产生横向纹理异常；后来先修 count，再以 donor bitmap 验证 new slot。 |
| YaHei one-off crash | `FAILED / DEPRECATED EXPERIMENT` | 结构化 diff 显示 slot 外差异为 `0`、加密有效；后续无法稳定复现，状态为 `YAHEI_CRASH=NOT_REPRODUCIBLE`。 |
| old append-capacity audit | `FAILED / DEPRECATED EXPERIMENT` | 曾把 record 前 4 bytes 视作 padding；TEST-2B 实机通过后，该解释被 count mirror 证据取代。 |

## 11. Open design decisions

production 路线已经决定为 self-owned rebuild。以下实现参数保持 `UNDECIDED`，本轮不执行：

```text
A. 正式公开版本采用哪一种开源 source font
B. large 字体的 pixel size、baseline、advance 与 packing profile
C. Loading/SMALL 字体的 pixel size、baseline、advance 与 packing profile
D. large 与 small 是否采用不同 raster profile
```

## 12. Current Next Steps（只记录，不执行）

1. 在既定 self-owned rebuild 路线上决定正式开源 source font。
2. 决定 large 与 Loading/SMALL 的视觉 profile。
3. 针对 clean JPN00c7 `2309/2308` baseline 的 append-only relocation semantics（Phase 2A full-rebuild runtime 已另行 `PROVEN`）继续做独立验证。
4. 实现并验证大规模 multi-glyph relocation。
5. 建立 production FONT builder。
6. 重新进行最终 production charset audit，并完成全场景 FONT runtime QA。

## 13. 文档一致性说明

本 reference summary 有意不删除历史实验报告。若历史报告保留了“等待 TEST-2B”“Loading path unresolved”或“YaHei crash”之类的当时状态，它们分别属于历史快照；当前解释以 `font/doc/` 的正式归档和 baseline 为准。当前没有发现证据支持“YaHei 必然闪退”或“Loading 必然使用 `001c FontData + 00c7 FontTexture`”。

本轮只更新文档和状态索引；没有生成、修改或安装任何 FONT/XPR，也没有修改 translation、builder 或游戏文件。
