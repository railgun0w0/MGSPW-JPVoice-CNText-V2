# SMALL_JPN append-record layout audit

本报告基于 clean `JPN/001cbbd1.xpr` 做只读结构分析，并记录单字 `们 U+4EEC` PoC 的静态结果；Golden 未覆盖。

## Atlas capacity

- texture：`2048×1024`，format=2，tiled=0，endian=0，pitch=2048。
- 现有 GlyphRecord 最大 `v1`：`804`；全 atlas 非零像素 bbox：`[4, 1, 2024, 802]`。
- 保守安全空白区：`(0, 805, 2048, 1024)`，尺寸 `2048×219`，扫描非零像素 `0`。
- 该区域至少可按 66×66 网格容纳 31×3=93 个完整 cell；本轮只使用第一个 `(0,805)-(66,871)`。

## FontData layout

- charmap：USER relative `0x16`，`U+4EEC` file offset `0x9E7E`，原值 `0000`。
- record count prefix：file `0x1FEE8`，`0167` = 359；PoC 改为 `0168` = 360。
- old record table：file `0x1FEEA`，stride 16；new record index 359 追加在 old USER 末端。
- USER size：`0x214CA -> 0x214DA`，增加 16 bytes。
- new record raw：`00000325004203670002004200440000`，字段为 `u0=0,v0=805,u1=66,v1=871,bearing_x=2,width=66,advance=68,reserved=0`。

## PoC bitmap

- donor：MLG-0007 `们` index `729`，源 bitmap `58×67`，record/bitmap 只读提取。
- adaptation：使用 Pillow LANCZOS 将 donor 像素适配为 66×66；没有修改 donor XPR。
- donor bbox=[3, 7, 54, 59]；adapted bbox=[1, 6, 64, 59]；adapted coverage=0.446970；nonzero mean=154.01。
- metrics 采用 SMALL_JPN CJK 常见值：`bearing_x=2,width=66,advance=68,reserved=0`。

## Static validation

- result：`PASS`；parser errors=`[]`。
- old 359 GlyphRecords byte-identical：`True`。
- old charmap entries except U+4EEC byte-identical：`True`。
- glyph count 359→360：`True`。
- U+4EEC→359：`True`。
- atlas target slot：`(0, 805, 66, 871)`；目标外 atlas 像素不变：`True`。
- 输出 encrypted SHA256：`c0984f45c6c881892b9fa85be9fdb8c70e0833dfcd6c45bc1f0bca6ca5e47526`；decrypted SHA256：`592d9725ed270709e4541c39caf998cf3f0381262e8095aa9b3ba7f4639fb31c`。

## 重要限制

这只是单字 runtime PoC，不是正式字体 builder；尚未证明 001c append 方案对批量 glyph、资源缓存或所有 Loading 页面均稳定。
