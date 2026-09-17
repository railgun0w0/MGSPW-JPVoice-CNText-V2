# TEST-2B count-field patch

本测试只针对 `00c7c9f9.xpr`，沿用 TEST-2 的 charmap、append donor record 和 USER 增长，额外只改 count-like mirror。未修改 atlas、其他 FONT、translation 或 Golden。

## 变更

- `U+53A5 → glyph 3209`，raw charmap：`0000` → `0c89`。
- `USER +0x1FED4` / file `0x1FF64`：`00000c89` (`3209`) → `00000C8A` (`3210`)。
- `glyph #3209` exact donor `昏 U+660F` record：`00bd06e900f7072c0004003a003e0000`。
- USER size：`0x2C768` → `0x2C778`；atlas 不变。

## 静态回读

- status：`PASS`；parser errors：`[]`。
- record count：`3210`；mapped count：`3209`。
- `U+53A5 → 3209`；#3209 == donor：`True`。
- old records unchanged：`True`；old mappings unchanged except target：`True`。
- atlas byte-identical：`True`。
- encrypted SHA256：`e09080ce5ff686f2a026c847135931ede4b7869dc4490f51d5cbbe2281343744`；decrypted SHA256：`279e34a9795cdc6887cd876c1c11605a2eedeab1ab0f1262a0092bf24c4f28d9`。

## 实机预期

安装后唯一预期结果：`……而昏昏`。

如果 TEST-2B PASS，则 `0x1FF64` 的 u32 值可确认是 runtime-visible glyph record count；届时再修正 parser 识别该字段。当前不自动修改 parser，等待实机结果。

## 手动步骤

1. 恢复 Golden `00c7c9f9.xpr`。
2. 安装 `TEST2B_COUNT_PATCH/00c7c9f9.xpr`。
3. 查看同一句文本，预期显示 `……而昏昏`。
4. 记录 `PASS / FAIL / CRASH / VISUAL_CORRUPTION`。
5. 测试结束后恢复 Golden。
