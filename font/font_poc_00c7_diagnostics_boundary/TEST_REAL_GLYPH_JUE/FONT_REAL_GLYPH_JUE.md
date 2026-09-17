# TEST_REAL_GLYPH_JUE

本测试直接基于已实机通过的 TEST-3B，只替换新 atlas slot 内的 bitmap。所有 USER、GlyphRecord、charmap、XPR descriptor 和目标 UV/metrics 保持不变；没有生成其他 glyph、没有修改 translation、没有覆盖 Golden。

## 文件

- 输入 TEST-3B：`D:\GAME\test\steam 合金装备大师合集2 合金装备和平行者汉化补丁\JPVoice_CNText_V2\font\font_poc_00c7_diagnostics_boundary\TEST3B_NEW_ATLAS_WITH_COUNT\00c7c9f9.xpr`
- 输出：`D:\GAME\test\steam 合金装备大师合集2 合金装备和平行者汉化补丁\JPVoice_CNText_V2\font\font_poc_00c7_diagnostics_boundary\TEST_REAL_GLYPH_JUE\00c7c9f9.xpr`
- encrypted SHA256：`c5b3db742e6dfc8ae0d8c4fc7f773f78b8eb8d8a1856635b7cad2cebe81f69e2`
- decrypted SHA256：`ea61d7eadbcf8f4bc7cf7eafe07fefb6dc498dc36561ecd1bdd269b7dd6c9ec5`

## 目标结构

- `U+53A5 → glyph 3209`。
- glyph count=`3210`；USER size=`0x2C778`。
- #3209 record 保持 TEST-3B 完全不变：`00000d05003a0d480004003a003e0000`。
- UV：`u0=0,v0=3333,u1=58,v1=3400`；bearing/width/advance 保持 TEST-3B。

## Raster 参数

- font file：`C:\Windows\Fonts\Noto Sans SC Medium (TrueType).otf`
- family：`Noto Sans SC Medium`；face index：`0`
- rasterizer：`Pillow 9.0.1 FreeTypeFont/ImageDraw`；font size：`58 px`
- hinting：`Pillow default FreeType load flags; hinting not explicitly disabled`
- antialias：`8-bit L-mode grayscale antialiasing`；grayscale：`direct 0..255; zero background, nonzero ink`
- anchor=`ls`；offset_x=`0`；baseline_y=`53`
- font bbox=`[0, -47, 58, 6]`；rendered bbox=`[2, 6, 56, 59]`
- bitmap：`{"width": 58, "height": 67, "nonzero_pixel_count": 1646, "ink_bbox_exclusive": [2, 6, 56, 59], "sha256": "b58e98da008775a42a2be9e675cdf4f808407f687a324513d7e1b6d063d2467d", "min_nonzero": 1, "max_nonzero": 255}`

该参数不是把 TTF 默认输出直接塞入 atlas：baseline 以现有 67px CJK glyph 的底部 y=59 校准，水平位置按 font bbox 在 58px cell 内居中；实际 bbox 与参考字的 x/y 范围逐项对照如下。

## 现有 glyph 对照

| 字符 | codepoint | index | record raw | UV | ink bbox | nonzero pixels |
|---|---|---:|---|---|---|---:|
| 厢 | U+53A2 | 966 | `0f8103750fbb03b80004003a003e0000` | `[3969, 885, 4027, 952]` | `[3, 9, 55, 59]` | 2127 |
| 厌 | U+538C | 961 | `0e4603750e8003b80004003a003e0000` | `[3654, 885, 3712, 952]` | `[2, 10, 55, 59]` | 1649 |
| 决 | U+51B3 | 846 | `01f80331023203740004003a003e0000` | `[504, 817, 562, 884]` | `[2, 7, 55, 59]` | 1572 |
| 卷 | U+5377 | 954 | `0c8d03750cc703b80004003a003e0000` | `[3213, 885, 3271, 952]` | `[2, 6, 55, 58]` | 1932 |
| 昏 | U+660F | 1751 | `00bd06e900f7072c0004003a003e0000` | `[189, 1769, 247, 1836]` | `[5, 7, 53, 59]` | 1890 |

- 参考预览：`D:\GAME\test\steam 合金装备大师合集2 合金装备和平行者汉化补丁\JPVoice_CNText_V2\font\font_poc_00c7_diagnostics_boundary\TEST_REAL_GLYPH_JUE\existing_reference_glyphs.png`
- 厥预览：`D:\GAME\test\steam 合金装备大师合集2 合金装备和平行者汉化补丁\JPVoice_CNText_V2\font\font_poc_00c7_diagnostics_boundary\TEST_REAL_GLYPH_JUE\generated_jue_preview.png`

## 静态读回结果

- status：`PASS`；parser errors：`[]`。
- TEST-3B USER byte-identical：`True`。
- TEST-3B GlyphRecords byte-identical：`True`。
- TEST-3B charmap byte-identical：`True`。
- TEST-3B XPR descriptor/header byte-identical：`True`。
- `U+53A5 = 3209`；glyph count=`3210`；USER size=`0x2C778`。
- #3209 record unchanged：`True`。
- new slot equals generated 厥：`True`。
- atlas changed bytes：`2105`；outside target slot：`0`。

## 手动实机测试

1. 恢复 Golden `00c7c9f9.xpr`。
2. 安装 `TEST_REAL_GLYPH_JUE/00c7c9f9.xpr`。
3. 进入同一句文本，唯一预期：`被击中的对手会承受不住而昏厥`。
4. 记录 `PASS / FAIL / CRASH / VISUAL_CORRUPTION`。
5. 测试结束后恢复 Golden。

当前状态：`APPEND_ONLY_RUNTIME_VALIDATED = YES`；`GENERATED_GLYPH_RUNTIME_VALIDATED = PENDING_MANUAL_TEST`。只有本测试实机 PASS 后，才将后者改为 YES；本轮不批量生成其他字符。
