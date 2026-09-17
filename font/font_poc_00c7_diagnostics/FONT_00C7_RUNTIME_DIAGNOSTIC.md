# 00c7 FONT runtime 分层诊断 PoC

本目录只针对 `00c7c9f9.xpr`。Golden 文件未覆盖，未修改 translation、其他 FONT、游戏安装目录；没有制作 POC-B。

## 核心静态结果

- TEST-1、TEST-2、TEST-3 均完成 filename-seed 加密、解密 readback 和 XPR2 parser 校验。
- 三个测试的静态验证均为 `PASS`。这不等于 runtime 已通过；仍需按报告末尾顺序实机测试。
- Golden `昏 U+660F` 的实际 glyph index：`1751`。
- donor record：`00bd06e900f7072c0004003a003e0000`。
- donor atlas rectangle：`[189, 1769, 247, 1836]`。

## Donor：昏 U+660F

- glyph index：`1751`
- GlyphRecord fields：`{"u0": 189, "v0": 1769, "u1": 247, "v1": 1836, "bearing_x_raw": 4, "bearing_x": 4, "width": 58, "advance": 62, "reserved": 0}`
- raw 16 bytes：`00bd06e900f7072c0004003a003e0000`
- atlas rectangle：`[189, 1769, 247, 1836]`
- donor bitmap：{"width": 58, "height": 67, "nonzero_pixel_count": 1890, "ink_bbox_exclusive": [5, 7, 53, 59], "sha256": "5a9e1499de669ec55a699988fc8ddd43a2a29ace252b4f2308e51e6f22728167", "min_nonzero": 1, "max_nonzero": 255}

## Golden 参考 CJK records

以下完整 record 均直接从 Golden 00c7 读取：

| 字符 | codepoint | glyph index | raw 16 bytes | UV | bearing_x | width | advance |
|---|---|---:|---|---|---:|---:|---:|
| 昏 | U+660F | 1751 | `00bd06e900f7072c0004003a003e0000` | `[189, 1769, 247, 1836]` | 4 | 58 | 62 |
| 厢 | U+53A2 | 966 | `0f8103750fbb03b80004003a003e0000` | `[3969, 885, 4027, 952]` | 4 | 58 | 62 |
| 决 | U+51B3 | 846 | `01f80331023203740004003a003e0000` | `[504, 817, 562, 884]` | 4 | 58 | 62 |
| 缺 | U+7F3A | 2452 | `0d4a09910d8409d40004003a003e0000` | `[3402, 2449, 3460, 2516]` | 4 | 58 | 62 |
| 卷 | U+5377 | 954 | `0c8d03750cc703b80004003a003e0000` | `[3213, 885, 3271, 952]` | 4 | 58 | 62 |
| 厌 | U+538C | 961 | `0e4603750e8003b80004003a003e0000` | `[3654, 885, 3712, 952]` | 4 | 58 | 62 |

## 三个测试的变量边界

| 测试 | 新增变量 | 不变内容 | 预期文字 |
|---|---|---|---|
| TEST-1 | 仅 `charmap[U+53A5] = glyph_of_昏` | record count、USER size、atlas | `昏昏` |
| TEST-2 | TEST-1 + append exact donor record #3209 | atlas 不变，旧 records/mapping 不变 | `昏昏` |
| TEST-3 | TEST-2 + donor bitmap copy 到新 slot，#3209 UV 改为新 slot | 旧 atlas pixels 不变 | `昏昏` |

## 输出与静态验证

### TEST1_CHARMAP_EXISTING

- 输出：`D:\GAME\test\steam 合金装备大师合集2 合金装备和平行者汉化补丁\JPVoice_CNText_V2\font\font_poc_00c7_diagnostics\TEST1_CHARMAP_EXISTING\00c7c9f9.xpr`
- encrypted SHA256：`3bdcfbae1e681aaf2f4e48f16d87099a056c4f0b04303632bb72e5d35110069f`
- decrypted SHA256：`0fc4c675f8991c00415f2b41159bc5e577b8a80b5d2a8063eda0dd2dbe8131ce`
- filename seed：`0x3AF33BE1`
- target raw charmap：`06d7`，mapping = `1751`
- record count：`3209`；USER size：`0x2C768`
- parser errors：`[]`
- atlas diff：`{"changed_byte_count": 0, "changed_range_count": 0, "changed_ranges_first_20": [], "changed_min": null, "changed_max_exclusive": null}`
- atlas changed outside `[x=0..57,y=3333..3399]`：`0`
- old records unchanged：`True`
- old charmap unchanged except target：`True`
- result：`PASS`

### TEST2_APPENDED_RECORD_EXISTING_ATLAS

- 输出：`D:\GAME\test\steam 合金装备大师合集2 合金装备和平行者汉化补丁\JPVoice_CNText_V2\font\font_poc_00c7_diagnostics\TEST2_APPENDED_RECORD_EXISTING_ATLAS\00c7c9f9.xpr`
- encrypted SHA256：`87e25d3ad995fecad1e6c4f18a20af46493ef2a2fe5612fbf196b93dfff9ae48`
- decrypted SHA256：`37aead1f053f18bf0621a7e9e077b9c3bef7bc27d98801e2acc58798bd82d233`
- filename seed：`0x3AF33BE1`
- target raw charmap：`0c89`，mapping = `3209`
- record count：`3210`；USER size：`0x2C778`
- parser errors：`[]`
- atlas diff：`{"changed_byte_count": 0, "changed_range_count": 0, "changed_ranges_first_20": [], "changed_min": null, "changed_max_exclusive": null}`
- atlas changed outside `[x=0..57,y=3333..3399]`：`0`
- old records unchanged：`True`
- old charmap unchanged except target：`True`
- result：`PASS`

### TEST3_APPENDED_RECORD_NEW_ATLAS

- 输出：`D:\GAME\test\steam 合金装备大师合集2 合金装备和平行者汉化补丁\JPVoice_CNText_V2\font\font_poc_00c7_diagnostics\TEST3_APPENDED_RECORD_NEW_ATLAS\00c7c9f9.xpr`
- encrypted SHA256：`e9957ee16a66c7a3e529efca1e0780937dc781bf1a3a3f88d956952cdbe973cb`
- decrypted SHA256：`6b5e905046a85110668fb241477b7defed0721a7b92d02984498da4df4f45d6c`
- filename seed：`0x3AF33BE1`
- target raw charmap：`0c89`，mapping = `3209`
- record count：`3210`；USER size：`0x2C778`
- parser errors：`[]`
- atlas diff：`{"changed_byte_count": 1890, "changed_range_count": 162, "changed_ranges_first_20": [[13680651, 13680668], [13680679, 13680686], [13680687, 13680688], [13684744, 13684746], [13684764, 13684785], [13688843, 13688879], [13688880, 13688881], [13692934, 13692935], [13692936, 13692976], [13692977, 13692978], [13697030, 13697031], [13697032, 13697074], [13701126, 13701127], [13701128, 13701169], [13705222, 13705223], [13705224, 13705258], [13709318, 13709319], [13709320, 13709345], [13709354, 13709360], [13713414, 13713415]], "changed_min": 13680651, "changed_max_exclusive": 13889585}`
- atlas changed outside `[x=0..57,y=3333..3399]`：`0`
- old records unchanged：`True`
- old charmap unchanged except target：`True`
- result：`PASS`

## 旧失败 POC-A 静态复盘

失败文件：`D:\GAME\test\steam 合金装备大师合集2 合金装备和平行者汉化补丁\JPVoice_CNText_V2\font\font_poc\POC_A_00C7\00c7c9f9.xpr`
- U+53A5 raw charmap：`0c89`，mapping = `3209`
- failed #3209 raw record：`00000d05003a0d480004003a003e0000`
- failed #3209 fields：`{"u0": 0, "v0": 3333, "u1": 58, "v1": 3400, "bearing_x_raw": 4, "bearing_x": 4, "width": 58, "advance": 62, "reserved": 0}`
- failed destination slot decoded bitmap：`{"width": 58, "height": 67, "nonzero_pixel_count": 1423, "ink_bbox_exclusive": [2, 7, 56, 59], "sha256": "f7399f7c0e03d27f130b00ad0e60e4db86f1d80644206d77a557e7df91a38a4f", "min_nonzero": 1, "max_nonzero": 255}`
- atlas changed outside destination slot：`0`
- TX2D unchanged：`True`；texture offset unchanged：`True`；data_size unchanged：`True`
- parser errors：`[]`
- outer encrypt/decrypt round-trip：`True`
- record UV：`58×67`；record width matches UV：`True`；record inside atlas：`True`
- slot dimensions：`[58, 67]`；background zero：`True`；positive nonzero ink polarity：`True`
- row-stride/overspill static check：`True`
- PGM dump：`D:\GAME\test\steam 合金装备大师合集2 合金装备和平行者汉化补丁\JPVoice_CNText_V2\font\font_poc_00c7_diagnostics\failed_poc_a_00c7_slot.pgm`

旧失败 POC-A 的 record 字段本身符合规划的 58×67 / bearing 4 / advance 62 结构；其 atlas destination 也可按当前 TX2D 的 linear 8-bit、pitch=4096 逐行解码为单个非零 bitmap。静态 diff 没有发现 destination 之外的 atlas 越界、整行误写、背景极性反转或 outer encryption round-trip 错误。

静态文件仍不能证明 runtime 对新 UV/record 的实际解释方式，也不能单凭 bitmap 反推出实机横向拉长纹理的来源；所以必须用 TEST-1/2/3 分层隔离。

## 结果判定表

- TEST-1 FAIL：charmap patch、00c7 packaging 或 encryption 层仍有问题。
- TEST-1 PASS + TEST-2 FAIL：USER growth、appended GlyphRecord 或 index 3209 runtime loading 有问题。
- TEST-1 PASS + TEST-2 PASS + TEST-3 FAIL：新 atlas slot、texture storage、UV、pitch 或 atlas 写入有问题。
- TEST-1 PASS + TEST-2 PASS + TEST-3 PASS：append-only runtime 路线成立；旧失败 POC-A 的问题集中到 generated 厥 raster、metrics 或 raster-to-atlas write path。

## 手动实机测试顺序

1. 恢复 Golden `00c7c9f9.xpr`。
2. 安装 `TEST1_CHARMAP_EXISTING/00c7c9f9.xpr`，检查是否显示为：`被击中的对手会承受不住而昏昏`。记录 `PASS / FAIL / CRASH / VISUAL_CORRUPTION`。
3. 恢复 Golden。
4. 安装 `TEST2_APPENDED_RECORD_EXISTING_ATLAS/00c7c9f9.xpr`，预期仍为 `...而昏昏`，记录结果。
5. 恢复 Golden。
6. 安装 `TEST3_APPENDED_RECORD_NEW_ATLAS/00c7c9f9.xpr`，预期仍为 `...而昏昏`，记录结果。
7. 测试结束后恢复 Golden。

本轮未自动安装、未修改 Golden、未修改 0007/000e/001c、未进入批量 glyph 或 relocation。
