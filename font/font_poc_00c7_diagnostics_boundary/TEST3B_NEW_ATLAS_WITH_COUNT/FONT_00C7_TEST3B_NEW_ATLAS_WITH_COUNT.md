# TEST-3B_NEW_ATLAS_WITH_COUNT

基于已通过实机的 TEST-2B，仅新增变量：将 `昏 U+660F` 的原始 bitmap 逐行复制到新 atlas slot，并把 #3209 UV 改到该 slot。未生成厥、未修改其他 glyph、未 relocation texture。

## 变更

- `U+53A5 → 3209`。
- count mirror file `0x1FF64`：`00000c89` (`3209`) → `00000C8A` (`3210`)。
- #3209 record：`00000d05003a0d480004003a003e0000`；metrics 沿用 donor `昏`，UV=`(0, 3333, 58, 3400)`。
- donor `昏` index=`1751`，record=`00bd06e900f7072c0004003a003e0000`，rectangle=`[189, 1769, 247, 1836]`。
- TX2D storage：format=`2`，tiled=`0`，endian=`0`，pitch=`4096`；复制方式为逐行按 pitch 写入。

## 静态验证

- status：`PASS`；parser errors：`[]`。
- glyph count=`3210`；USER size=`0x2C778`；atlas changed bytes=`1890`。
- old records unchanged：`True`。
- old mappings unchanged except U+53A5：`True`。
- #3209 points to new slot：`True`。
- destination bitmap equals donor：`True`。
- atlas changes outside `x=0..57,y=3333..3399`：`0`。
- encrypted SHA256：`b133fdd122ef150f40ee04cb624a38568c1a239ab8ccddf64844f488dcd0f1d9`；decrypted SHA256：`ab6ce7abfc419421c2dd39371304c9848b0026a59f97335add6076878f7cf343`。

## 实机预期

唯一预期：`……而昏昏`。若 PASS，则 append-only 新 atlas slot 路线成立；下一轮才替换 slot bitmap 为真正的厥。

## 手动步骤

1. 恢复 Golden `00c7c9f9.xpr`。
2. 安装 `TEST3B_NEW_ATLAS_WITH_COUNT/00c7c9f9.xpr`。
3. 测试同一句文本，预期显示 `……而昏昏`。
4. 记录 `PASS / FAIL / CRASH / VISUAL_CORRUPTION`。
5. 测试结束后恢复 Golden。
