# FONT_GLYPH_GRAY_SCALE_CANDIDATES

本轮仅基于候选 D 对 `厥 U+53A5` 的 atlas bitmap 做灰度线性缩放。没有更换字体、字号、metrics、charmap、glyph count、USER 或 XPR 结构。

## 规则

- E：`round(D_pixel × 0.84)`。
- F：`round(D_pixel × 0.90)`。
- 所有结果 clamp 到 `0..255`；原始非零像素最低保留为 `1`，确保 bbox 不因极低灰度消失。
- D 为候选 D 的 byte-identical copy。

## 实测结果

| 版本 | 灰度因子 | bbox | coverage | nonzero grayscale mean | 静态验证 |
|---|---:|---|---:|---:|---|
| D | 1.0 | `[2, 7, 56, 59]` | 47.658% | 215.07 | `PASS` |
| E | 0.84 | `[2, 7, 56, 59]` | 47.658% | 180.529 | `PASS` |
| F | 0.9 | `[2, 7, 56, 59]` | 47.658% | 193.904 | `PASS` |

## 保护检查

- 三个 XPR 都保持 `U+53A5 → 3209`、glyph count=`3210`、USER size=`0x2C778`。
- target GlyphRecord 和 metrics 完全保持 D。
- USER、charmap、全部 GlyphRecord、TX2D descriptor/header 均保持 D。
- E/F 相对 D 的 atlas 改动严格限制在 `x=0..57,y=3333..3399`。
- 每个文件均经过 `encrypt → decrypt → parser` 读回，parser errors=0。

## 文件

- 对照图：`D:\GAME\test\steam 合金装备大师合集2 合金装备和平行者汉化补丁\JPVoice_CNText_V2\font\font_poc_00c7_diagnostics_boundary\TEST_REAL_GLYPH_JUE_STYLE_GRAY_SCALE\glyph_jue_gray_scale_candidates.png`
- `D/00c7c9f9.xpr`：候选 D 原样复制。
- `E/00c7c9f9.xpr`：D 灰度 × 0.84。
- `F/00c7c9f9.xpr`：D 灰度 × 0.90。
- 详细 SHA256 和统计：`gray_scale_manifest.json`。

三个版本均未分别进行实机风格比较；D 的 glyph runtime 已成功，E/F 只改变像素灰度。
