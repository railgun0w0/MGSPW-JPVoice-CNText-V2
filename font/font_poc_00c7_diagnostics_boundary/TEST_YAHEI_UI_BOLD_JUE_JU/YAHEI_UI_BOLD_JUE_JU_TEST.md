# YAHEI_UI_BOLD_JUE_JU_TEST

本测试直接基于已实机正常的 Microsoft YaHei UI Bold `厥` XPR，只追加 `拘 U+62D8`；没有覆盖厥 slot，没有批量增加其它 glyph。

## 结构结果

- `U+53A5 厥 → 3209` 保留；`U+62D8 拘 → 3210`。
- glyph count：`3210 → 3211`；USER size：`0x2C778 → 0x2C788`。
- glyph-count mirror：USER+`0x1FED4`，`00000C8A → 00000C8B`。
- 新 slot：`(58, 3333, 116, 3400)`；实际扫描检查 `3210` 个旧 record，无重叠。
- 新 record：`003a0d0500740d480004003a003e0000`；metrics `bearing_x=4,width=58,advance=62`。

## YaHei UI Bold raster 参数

- font file：`C:\Windows\Fonts\msyhbd.ttc`；face index=`1`。
- metadata：family=`Microsoft YaHei UI`；style=`Bold`。
- size=`55px`；x/y offset=`0,0`；baseline_y=`51`。
- bbox=`[1, 6, 54, 59]`；coverage=`45.986%`；nonzero grayscale mean=`224.976`。
- rasterizer：`Pillow 9.0.1 FreeTypeFont/ImageDraw, layout_engine=BASIC`；antialias：`8-bit L-mode grayscale antialiasing`。

## 静态验证

- status：`PASS`；parser errors=`[]`。
- 厥 record/bitmap unchanged：`True`。
- old charmap entries unchanged except U+62D8：`True`。
- old GlyphRecords unchanged：`True`。
- texture format/dimensions/pitch/offset unchanged：`True`。
- atlas changed pixels=`1787`；outside new slot=`0`。
- outer encryption round-trip：`True`。

## 并排预览

- `yahei_jue_ju_preview.png` 顺序：厥、拘、束。

输出 XPR：`D:\GAME\test\steam 合金装备大师合集2 合金装备和平行者汉化补丁\JPVoice_CNText_V2\font\font_poc_00c7_diagnostics_boundary\TEST_YAHEI_UI_BOLD_JUE_JU\00c7c9f9.xpr`

实机测试目标：`拘束`。测试结束后恢复 Golden 或原已通过的 YaHei UI Bold 厥版本。
