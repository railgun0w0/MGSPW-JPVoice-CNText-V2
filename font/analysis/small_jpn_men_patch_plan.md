# SMALL_JPN `们 U+4EEC` one-glyph patch plan

## 已构建 PoC

测试文件：`D:\GAME\test\steam 合金装备大师合集2 合金装备和平行者汉化补丁\JPVoice_CNText_V2\font\small_jpn_men_append_poc\TEST_MEN_APPEND\001cbbd1.xpr`。它直接基于 clean `JPN/001cbbd1.xpr`，仅为 `们` append record/index，并在 001c own TX2D 的 `(0, 805, 66, 871)` 写入适配 bitmap。

## 修改内容

- `charmap[U+4EEC]`: `0 -> 359`。
- record count prefix: `0x0167 -> 0x0168`。
- USER size: `+16 bytes`。
- append record: `00000325004203670002004200440000`。
- atlas slot: `(0, 805, 66, 871)`，非零 pixels 仅写入该 66×66 区域。
- record 0 未复用；原 359 条旧记录和其它 charmap 均保持。

## Donor 与适配

使用 MLG-0007 中已有 `们` glyph index `729` 作为像素 donor；源尺寸 `58×67`，通过 LANCZOS 适配至 SMALL_JPN 的 66×66 cell。

## 手动测试

1. 备份并恢复 clean `001cbbd1.xpr`。
2. 安装 `D:\GAME\test\steam 合金装备大师合集2 合金装备和平行者汉化补丁\JPVoice_CNText_V2\font\small_jpn_men_append_poc\TEST_MEN_APPEND\001cbbd1.xpr` 到实际 SMALL_JPN 路径。
3. 打开 Loading 角色语录，检查 `我·只` 是否变为 `我们只`。
4. 记录 PASS / FAIL / CRASH / VISUAL_CORRUPTION。
5. 测试后恢复 clean 文件。

本 PoC 没有修改 `00c7c9f9.xpr`、其它 FONT、translation 或 Golden 文件。
