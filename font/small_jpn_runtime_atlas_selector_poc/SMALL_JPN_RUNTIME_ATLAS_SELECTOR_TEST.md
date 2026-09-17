# SMALL_JPN Runtime Atlas Selector Test

本轮为只读构建验证之外的独立实验文件生成；没有修改 Golden、charmap、USER、GlyphRecord、glyph count 或另一份 XPR。

## 测试设计

- 字符：`我 U+6211`；001c charmap index=`239`。
- record UV：`(1733, 470, 1799, 536)`；目标像素尺寸：`66×66`。
- 测试标记：同一份 66×66 高对比灰度 box/X pattern；A/B 使用完全相同的 marker bytes。
- 两个文件都直接从 clean JPN 原文件独立生成。

## TEST A：001c own TX2D

- 输入：`D:\GAME\test\steam 合金装备大师合集2 合金装备和平行者汉化补丁\JPVoice_CNText_V2\font\JPN\001cbbd1.xpr`
- 输出：`D:\GAME\test\steam 合金装备大师合集2 合金装备和平行者汉化补丁\JPVoice_CNText_V2\font\small_jpn_runtime_atlas_selector_poc\TEST_A_001C_OWN_TX2D\001cbbd1.xpr`
- 原始 encrypted SHA256：`5625066b835e6f26f310781fbbd3ef4f9ea93a77be2a4044289c11b74a767414`
- 输出 encrypted SHA256：`f6dfc503d7fa5791ffb7f5a1709029afcb8294fc21878806c3da64bd583d74cc`
- 原始 decrypted SHA256：`f4fdb335a56f81bee4e4a13be71f5518827ebcf42fbfa86d30d2f1de3c6dd025`
- 输出 decrypted SHA256：`6adbcfbb1c3db6c933b07cf699fffae2131d58819eb553385e9bafcd20e915f9`
- filename seed：`0xF2C6C89B`；文件大小：`2234396` → `2234396` bytes。
- 纹理物理起点：`0x2181C`；pitch=2048。
- 解密差异：`4179` bytes，全部位于目标矩形行区间；目标外差异=`0`。
- 静态验证：`PASS`；parser errors=`[]`。

## TEST B：00c7 TX2D

- 输入：`D:\GAME\test\steam 合金装备大师合集2 合金装备和平行者汉化补丁\JPVoice_CNText_V2\font\JPN\00c7c9f9.xpr`
- 输出：`D:\GAME\test\steam 合金装备大师合集2 合金装备和平行者汉化补丁\JPVoice_CNText_V2\font\small_jpn_runtime_atlas_selector_poc\TEST_B_00C7_TX2D\00c7c9f9.xpr`
- 原始 encrypted SHA256：`1f7a18f28d0d67d7a6a65a5286a1e48c97d595829b4c99325fb2b5772b921e8d`
- 输出 encrypted SHA256：`1b25cee5fa1549d7256ff599f920cd2cd1fd89c17e8c4ea7bb14b964b6fa442a`
- 原始 decrypted SHA256：`31b8eb9a7c86b1429fb7fa0d12688c65c9123e307c5f0e8c42f1df67a7cd9e6b`
- 输出 decrypted SHA256：`4a106dc0bbfa27b6f5705f3caea4021f48e0048871ad42c3501e7c05835317dd`
- filename seed：`0x3AF33BE1`；文件大小：`16945180` → `16945180` bytes。
- 纹理物理起点：`0x2901C`；pitch=4096。
- 解密差异：`4255` bytes，全部位于目标矩形行区间；目标外差异=`0`。
- 静态验证：`PASS`；parser errors=`[]`。

## 精确修改范围

线性 format=2 atlas 每行是一个连续 66-byte span；具体 66 个行区间、绝对文件偏移和完整 diff 已写入 `selector_test_manifest.json`。除这些目标行外，解密 XPR byte diff 必须为 0。

## 实机判定（历史测试设计表）

下表是 TEST B 尚未决定是否需要执行时的原始判定表；当前 Loading 结论以文末 TEST A 实机结果为准。

1. 恢复 clean `001cbbd1.xpr` 和 `00c7c9f9.xpr`。
2. 只安装 TEST A，打开 Loading 页面观察 `我`。
3. 恢复 clean 文件，再只安装 TEST B，观察同一个 `我`。

| TEST A | TEST B | 结论 |
|---|---|---|
| 改变 | 不改变 | Loading 使用 001c own TX2D |
| 不改变 | 改变 | Loading 使用跨 XPR 的 00c7 TX2D |
| 改变 | 改变 | 两份资源均被读取，停止继续 patch，重新检查 selector/binding |
| 不改变 | 不改变 | 当前观察路径未读取这两个目标区域，停止继续 patch，检查缓存/其它 resource binding |

本轮不加入 `们`，不 append GlyphRecord，不改 glyph count，不改 charmap。

## 后续实机结果更新

TEST A 已实机通过：只修改 `001cbbd1.xpr` 自带 TX2D 中 glyph 239（`我 U+6211`）后，Loading 页面中的“我”发生变化。

当前严谨结论：

- Loading 确实使用 `001cbbd1.xpr` 自带 TX2D。
- 当前 Loading 补字 PoC 收敛到单文件 `JPN/001cbbd1.xpr`。
- TEST B 未作为必要对照完成；不据此声称 `00c7c9f9.xpr` 不参与任何其它渲染路径。
- 本目录中的 TEST B 仅保留为历史静态 selector 对照，不是当前 Loading 补字目标。
