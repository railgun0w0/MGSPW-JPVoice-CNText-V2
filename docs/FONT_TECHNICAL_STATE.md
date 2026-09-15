# FONT Technical State（Canonical）

本文件是当前 `sol-translation` 分支的 FONT 状态唯一入口。它只整理已经存在的报告、manifest、静态读回和实机记录；不替代、删除或重写历史实验产物。历史报告中仍保留的 `PENDING`、`UNRESOLVED` 或旧失败解释，应以本文的证据等级和“状态收敛”说明为准。

整理日期：2026-09-15（Asia/Hong_Kong）

## 当前状态摘要

```ini
GOLDEN_V2_FONT_PIPELINE = PRESERVED

MAIN_00C7_FORMAT = UNDERSTOOD
MAIN_00C7_APPEND_RUNTIME = VALIDATED
GENERATED_GLYPH_RUNTIME = VALIDATED

LOADING_FONT_PATH = RUNTIME_CONFIRMED
LOADING_GLYPH_REPLACEMENT = VALIDATED
LOADING_FONT_STYLE = UNRESOLVED

FINAL_MAIN_FONT_STYLE = UNDECIDED
FINAL_SMALL_FONT_STYLE = UNDECIDED
FINAL_GLYPH_SOURCE_POLICY = UNDECIDED

LARGE_MULTI_GLYPH_RELOCATION = UNRESOLVED
PRODUCTION_FONT_BUILDER = NOT_COMPLETED
```

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

原 V2 没有重建内部 `FontData` 或 `TX2D`。`001cbbd1.xpr` 不属于原稳定 V2 的默认输出；它后来作为 Loading/SMALL_JPN 的独立运行时资源被单独定位，不能反推为主字体默认 pipeline。

```ini
GOLDEN_V2_FONT_PIPELINE = PRESERVE
```

证据：[`FONT_V2_CODE_ARCHAEOLOGY.md`](../FONT_V2_CODE_ARCHAEOLOGY.md)。该报告也记录了历史上找到的 copy/rekey 工具链，以及原始 V2 builder 未进入 Git 的事实。

## 2. 六套 unique logical fonts

状态：`STATIC_CONFIRMED`。

逻辑内容去重后保留六套：

```text
JPN-0007
JPN-000E
JPN-001C
JPN-00C7
MLG-0007
MLG-000E
```

`JPN_CN` 只用于 provenance 验证，不作为第七套字体重复统计：

```text
JPN_CN/0007ccd8.xpr == MLG-0007 logical content
JPN_CN/000ebbe8.xpr == MLG-000E logical content
JPN_CN/00c7c9f9.xpr == MLG-0007 logical content re-encrypted with 00c7 seed
```

相关证据：[`FONT_THREEWAY_CENSUS.md`](../FONT_THREEWAY_CENSUS.md)、[`FONT_SIX_UNIQUE_CHARMAP.csv`](../FONT_SIX_UNIQUE_CHARMAP.csv)。

## 3. 主字体 00c7 append 技术

状态：`RUNTIME_CONFIRMED`。

当前已验证的主字体访问链为：

```text
Unicode charmap
    → glyph index N
    → GlyphRecord[N]
    → atlas UV rectangle
    → TX2D bitmap
```

记录索引语义为 `DIRECT`：`charmap value N → GlyphRecord[N]`。当前 00c7 的主要实机边界结果如下：

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

这不是原先误判的 alignment padding。单字 append 已证明：旧 glyph index、旧 GlyphRecord、旧 charmap entry 和旧 atlas 像素可以保持不变，新增 record、count mirror、USER size、charmap entry 和新 slot 可以被 runtime 接受。

相关证据：[`FONT_GLYPH_INDEX_BOUNDARY_AUDIT.md`](../font_poc_00c7_diagnostics_boundary/FONT_GLYPH_INDEX_BOUNDARY_AUDIT.md)、[`TEST2B_COUNT_PATCH`](../font_poc_00c7_diagnostics_boundary/TEST2B_COUNT_PATCH/FONT_00C7_TEST2B_COUNT_PATCH.md)、[`TEST3B_NEW_ATLAS_WITH_COUNT`](../font_poc_00c7_diagnostics_boundary/TEST3B_NEW_ATLAS_WITH_COUNT/FONT_00C7_TEST3B_NEW_ATLAS_WITH_COUNT.md)、[`FONT_REAL_GLYPH_JUE.md`](../font_poc_00c7_diagnostics_boundary/TEST_REAL_GLYPH_JUE/FONT_REAL_GLYPH_JUE.md)。

## 4. Generated glyph 与风格实验

状态：运行时技术链为 `RUNTIME_CONFIRMED`；最终字体来源为 `UNRESOLVED` / `UNDECIDED`。

- `Noto Sans SC Bold`：D profile，`56px`，`58×67` cell，目标 `厥` bbox 约 `[2,7,56,59]`，baseline ink bottom `y=59`。D 已实机比较通过，并保留为当前 generated fallback profile。
- `Microsoft YaHei UI Bold`：实际 metadata 为 `C:\\Windows\\Fonts\\msyhbd.ttc` face `1`，family `Microsoft YaHei UI`，style `Bold`；`55px`、Pillow/FreeType BASIC、8-bit L 灰度。该 `厥` 版本已实机正常运行，视觉效果可接受。
- YaHei 曾出现一次闪退，但后续未能稳定复现。二进制差分报告确认：XPR 结构、文件大小、外层加密 round-trip 均有效，所有 plaintext 差异都在目标 atlas slot 内，slot 外差异为 `0`。因此不能写成“YaHei 会导致闪退”。

```ini
YAHEI_CRASH = NOT_REPRODUCIBLE
FINAL_GLYPH_SOURCE_POLICY = UNDECIDED
```

相关证据：[`FONT_GLYPH_STYLE_TUNING.md`](../font_poc_00c7_diagnostics_boundary/TEST_REAL_GLYPH_JUE_STYLE_TUNING/FONT_GLYPH_STYLE_TUNING.md)、[`glyph_generation_profile_v1.json`](../font_poc_00c7_diagnostics_boundary/TEST_REAL_GLYPH_JUE_STYLE_TUNING/glyph_generation_profile_v1.json)、[`YAHEI_UI_BOLD_JUE_TEST.md`](../font_poc_00c7_diagnostics_boundary/TEST_YAHEI_UI_BOLD_JUE/YAHEI_UI_BOLD_JUE_TEST.md)、[`YAHEI_CRASH_DIFF_AUDIT.md`](../font_poc_00c7_diagnostics_boundary/TEST_YAHEI_UI_BOLD_JUE/YAHEI_CRASH_DIFF_AUDIT.md)。

## 5. JPN donor 与 generated glyph

状态：`STATIC_CONFIRMED` + 局部 `RUNTIME_CONFIRMED`；策略 `UNDECIDED`。

`拘 U+62D8` 在 clean JPN `00c7` 中存在原生 glyph；同一字符也已经用 generated font 成功生成并进入主字体 PoC。现有报告显示两种来源的视觉风格有明显差别，因此当前不能把“JPN donor 必定优先”或“generated glyph 必定优先”写死。

```ini
FINAL_GLYPH_SOURCE_POLICY = UNDECIDED
```

保留的设计选项是：

```text
A. 保留 MLG，只补缺字
B. MLG + JPN donor + generated fallback
C. 统一重建整套 CJK glyph
```

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

相关证据：[`LOADING_SMALL_JPN_STATUS.md`](../LOADING_SMALL_JPN_STATUS.md)、[`SMALL_JPN_FONT_PAIR_ANALYSIS.md`](../SMALL_JPN_FONT_PAIR_ANALYSIS.md)、[`SMALL_JPN_ONE_GLYPH_PATCH_PLAN.md`](../SMALL_JPN_ONE_GLYPH_PATCH_PLAN.md)、[`SMALL_JPN_RUNTIME_ATLAS_SELECTOR_TEST.md`](../small_jpn_runtime_atlas_selector_poc/SMALL_JPN_RUNTIME_ATLAS_SELECTOR_TEST.md)、[`small_jpn_men_manifest.json`](../small_jpn_men_append_poc/small_jpn_men_manifest.json)。

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

PSP 考古报告：[`PSP_CN_ARCHAEOLOGY.md`](../../JPVoice_CNText_Experimental/PSP_CN_ARCHAEOLOGY.md)。

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
| old expanded `001c` replacement | `FAILED / DEPRECATED EXPERIMENT` | 旧的广泛替换实验曾崩溃；不能否定后来针对 Loading 的 `001c` own-TX2D 单文件 PoC。 |
| append new index without glyph-count update | `FAILED / DEPRECATED EXPERIMENT` | 新 index `3209` 空白，直接暴露 runtime-visible glyph count mirror。 |
| original new-atlas test before count fix | `FAILED / DEPRECATED EXPERIMENT` | 产生横向纹理异常；后来先修 count，再以 donor bitmap 验证 new slot。 |
| YaHei one-off crash | `FAILED / DEPRECATED EXPERIMENT` | 结构化 diff 显示 slot 外差异为 `0`、加密有效；后续无法稳定复现，状态为 `YAHEI_CRASH=NOT_REPRODUCIBLE`。 |
| old append-capacity audit | `FAILED / DEPRECATED EXPERIMENT` | 曾把 record 前 4 bytes 视作 padding；TEST-2B 实机通过后，该解释被 count mirror 证据取代。 |

## 11. Open design decisions

以下设计决策全部保持 `UNDECIDED`，本轮不执行：

```text
A. 主字体保留现有 MLG，只补缺字
B. 主字体采用 MLG + JPN donor + generated fallback
C. 自己统一重建整套 CJK glyph
D. 主字体 generated profile 使用哪一种字体
E. Loading/SMALL 使用哪一种字体/profile
F. 主字体和 Loading 字体是否采用不同 raster profile
```

## 12. Current Next Steps（只记录，不执行）

1. 决定主 CJK 字库最终方案。
2. 决定 Loading/SMALL 字体视觉方案。
3. 实现并验证大规模 multi-glyph relocation。
4. 建立 production FONT builder。
5. 重新进行最终 production charset audit。
6. 进行全场景 FONT runtime QA。

## 13. 文档一致性说明

本 canonical 文档有意不删除历史实验报告。若历史报告保留了“等待 TEST-2B”“Loading path unresolved”或“YaHei crash”之类的当时状态，它们分别属于历史快照；当前解释以本文的后续 runtime/静态证据为准。当前没有发现证据支持“YaHei 必然闪退”或“Loading 必然使用 `001c FontData + 00c7 FontTexture`”。

本轮只更新文档和状态索引；没有生成、修改或安装任何 FONT/XPR，也没有修改 translation、builder 或游戏文件。
