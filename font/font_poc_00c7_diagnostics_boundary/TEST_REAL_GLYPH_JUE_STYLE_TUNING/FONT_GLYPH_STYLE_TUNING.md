# FONT_GLYPH_STYLE_TUNING

本轮针对已经实机成功的 `厥 U+53A5` 做视觉风格拟合。A-D 均基于 `TEST_REAL_GLYPH_JUE`，仅替换 `[0,3333)-[58,3400)` 的 atlas bitmap；glyph count、charmap、GlyphRecord、metrics、USER 和 XPR descriptor/header 保持不变。

## 结论

推荐候选：`D`。该推荐依据 9 个现有 MLG 参考字的 bbox、覆盖率和非零灰度均值做静态比较，并已完成实机比较，效果优于 A。

当前状态：`STYLE_CANDIDATE_D_RUNTIME_COMPARED = PASS`；`CURRENT_GENERATED_GLYPH_PROFILE = D`。D 保留为当前 generated glyph fallback profile。

| 候选 | 方案 | bbox | 覆盖率 | 非零灰度均值 | 风格说明 | 静态验证 |
|---|---|---|---:|---:|---|---|
| A | `A` | `[2, 6, 56, 59]` | 42.357% | 210.069 | 当前成功版本：Medium 58px，原始灰度，不 embolden。 | `PASS` |
| B | `B` | `[1, 4, 57, 59]` | 59.444% | 227.045 | Medium 58px + 1px MaxFilter 加粗；笔画更重。 | `PASS` |
| C | `C` | `[1, 7, 55, 59]` | 42.048% | 204.395 | Medium 57px；字面略收小，baseline 保持一致。 | `PASS` |
| D | `D` | `[2, 7, 56, 59]` | 47.658% | 215.07 | Bold 56px；字面收小、笔画密度最高。 | `PASS` |

## 参考字

直接从当前 MLG TX2D 按 GlyphRecord UV 提取：

| 字符 | index | bbox | 覆盖率 | 非零灰度均值 |
|---|---:|---|---:|---:|
| 昏 | 1751 | `[5, 7, 53, 59]` | 48.636% | 181.555 |
| 眩 | 2254 | `[3, 6, 54, 58]` | 50.077% | 178.03 |
| 晕 | 1764 | `[4, 8, 53, 58]` | 46.5% | 194.145 |
| 棒 | 1865 | `[2, 7, 55, 59]` | 50.18% | 181.059 |
| 器 | 367 | `[2, 9, 55, 59]` | 53.448% | 185.293 |
| 厢 | 966 | `[3, 9, 55, 59]` | 54.735% | 181.244 |
| 厌 | 961 | `[2, 10, 55, 59]` | 42.434% | 181.056 |
| 决 | 846 | `[2, 7, 55, 59]` | 40.453% | 173.129 |
| 卷 | 954 | `[2, 6, 55, 58]` | 49.717% | 175.6 |

## Raster 参数

- A：`C:\Windows\Fonts\Noto Sans SC Medium (TrueType).otf`，58px，Pillow 9.0.1/FreeType BASIC，8-bit L 灰度抗锯齿，gamma 1.0。
- B：A 的 1px MaxFilter embolden，之后重新居中并将 ink bottom 校准到 y=59。
- C：同一 Medium 字体 57px，baseline bottom y=59。
- D：`C:\Windows\Fonts\Noto Sans SC Bold (TrueType).otf`，56px，baseline bottom y=59。
- 所有候选均为 58x67 cell，zero background/nonzero ink；没有修改 metrics。

## 产物

- 参考并排图：`D:\GAME\test\steam 合金装备大师合集2 合金装备和平行者汉化补丁\JPVoice_CNText_V2\font\font_poc_00c7_diagnostics_boundary\TEST_REAL_GLYPH_JUE_STYLE_TUNING\existing_reference_glyphs.png`
- A-D 候选图：`D:\GAME\test\steam 合金装备大师合集2 合金装备和平行者汉化补丁\JPVoice_CNText_V2\font\font_poc_00c7_diagnostics_boundary\TEST_REAL_GLYPH_JUE_STYLE_TUNING\glyph_jue_style_candidates.png`
- 参考 + 候选合并图：`D:\GAME\test\steam 合金装备大师合集2 合金装备和平行者汉化补丁\JPVoice_CNText_V2\font\font_poc_00c7_diagnostics_boundary\TEST_REAL_GLYPH_JUE_STYLE_TUNING\glyph_jue_style_candidates_with_references.png`
- 每个 `CANDIDATE_A` 至 `CANDIDATE_D` 子目录还包含可独立测试的 `00c7c9f9.xpr` 和 `bitmap_preview.png`。

## 建议

当前以 `D` 作为后续 generated glyph fallback profile。暂停 D/E/F 后续微调，不将任何候选扩展到 145 个字符；等待 PSP 汉化版字体/文本考古结果。若 PSP 没有可用同源 donor，则以 D 作为后续批量生成基线。
