# YAHEI_UI_BOLD_JUE_TEST

本候选直接基于已实机通过的 Candidate D，仅替换 `厥 U+53A5` 当前 atlas slot 的 bitmap。没有修改 glyph count、charmap、USER size、GlyphRecord、metrics、UV、XPR descriptors 或 atlas slot。

## 字体与参数

- actual font file: `C:\Windows\Fonts\msyhbd.ttc`
- actual family/style: `['Microsoft YaHei UI']` / `['Bold', 'Fet', 'Fett', 'Félkövér', 'Gras', 'Grassetto', 'Halvfet', 'Kalın', 'Krepko', 'Lihavoitu', 'Lodia', 'Negreta', 'Negrita', 'Negrito', 'Pogrubiony', 'Tučné', 'Vet', 'fed', 'tučné', 'Έντονα', 'Полужирный']`；face index=`1`
- font size: `55px`
- x/y offset: `x=0, y=0`；draw_x=`1`；baseline_y=`52`
- bbox: `[1, 8, 56, 59]`；ink bottom=`59`
- coverage: `50.335%`；nonzero grayscale mean=`217.133`
- rasterizer: `Pillow 9.0.1 FreeTypeFont/ImageDraw, layout_engine=BASIC`；hinting: `Pillow default FreeType load flags; hinting not explicitly disabled`
- antialias/grayscale: `8-bit L-mode grayscale antialiasing`；`direct 0..255 L-mode; zero background, nonzero ink`

## 静态校验

- status: `PASS`；parser errors=`[]`
- old USER unchanged：`True`
- old charmap unchanged：`True`
- GlyphRecord/metrics/UV unchanged：`True`
- descriptors/header unchanged：`True`
- `U+53A5 → 3209`；glyph count=`3210`；USER size=`0x2C778`
- only target atlas slot changed：`True`；changed bytes=`1067`

## MLG 参考字

参考字为当前 MLG TX2D 按 GlyphRecord UV 直接提取：`昏、眩、晕、棒、器、厢、厌、决、卷`。详细 index、UV、bbox、coverage 和灰度统计记录在同目录的 JSON manifest。

| 版本 | 来源 | size | offset | bbox | coverage | gray mean | runtime |
|---|---|---:|---|---|---:|---:|---|
| D | Noto Sans SC Bold | 56 | control | `[2,7,56,59]` | 47.658% | 215.070 | PASS |
| YaHei UI Bold | Microsoft YaHei UI Bold | 55 | `0,0` | `[1, 8, 56, 59]` | 50.335% | 217.133 | CRASH |

## 输出

- XPR：`D:\GAME\test\steam 合金装备大师合集2 合金装备和平行者汉化补丁\JPVoice_CNText_V2\font\font_poc_00c7_diagnostics_boundary\TEST_YAHEI_UI_BOLD_JUE\CANDIDATE_YAHEI_UI_BOLD\00c7c9f9.xpr`
- bitmap preview：`D:\GAME\test\steam 合金装备大师合集2 合金装备和平行者汉化补丁\JPVoice_CNText_V2\font\font_poc_00c7_diagnostics_boundary\TEST_YAHEI_UI_BOLD_JUE\CANDIDATE_YAHEI_UI_BOLD\bitmap_preview.png`
- metadata/完整统计：`yahei_ui_bold_manifest.json`

当前 D 已实机确认；YaHei UI Bold 已实机报告闪退。静态校验 PASS 不能覆盖该 runtime 结果，因此不要继续使用该候选；保留 D 为当前可用 profile。
