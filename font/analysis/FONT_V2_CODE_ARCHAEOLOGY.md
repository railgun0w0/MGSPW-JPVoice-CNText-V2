# 原 V2 FONT 代码考古报告

> **ARCHIVED / HISTORICAL REFERENCE.** 本文记录原 V2 copy/rekey 工具链与 provenance，适合追溯历史实现，不是当前 production baseline 或 self-owned builder 设计。最新权威入口见 [`../doc/README.md`](../doc/README.md)。

日期：2026-09-14

范围：只读检查当前工作区、V2 Git 的所有可见 refs/分支/历史对象，以及相邻的 Experimental、字体分析和 Phase2 目录。没有运行 FONT 构建，没有重建 XPR，没有覆盖或修改任何 FONT/XPR；本次只新增本报告。

## 结论摘要

找到的原 V2 FONT 生成链是：原第三方 MLG 汉化字体作为输入，两个文件原样复制，并把 MLG large `0007` 的同一份明文 XPR2 以 JPN large `00c7` 文件名 seed 重新加密。

```text
补丁源 FONT/0007ccd8.xpr
  -> OuterCrypt 以 0007ccd8.xpr 解密
  -> 明文 XPR2 原样保留
  -> OuterCrypt 以 00c7c9f9.xpr 重新加密
  -> payload-stage2/mgspw/FONT/00c7c9f9.xpr
```

对应代码位于：

- `D:\GAME\test\steam 合金装备大师合集2 合金装备和平行者汉化补丁\JPVoice_CNText_Experimental\Build-ExperimentalPayload.ps1`
- `D:\GAME\test\steam 合金装备大师合集2 合金装备和平行者汉化补丁\JPVoice_CNText_Experimental\tools\OuterCrypt.cpp`
- `D:\GAME\test\steam 合金装备大师合集2 合金装备和平行者汉化补丁\JPVoice_CNText_Experimental\tools\OuterCrypt.exe`

这是本次考古找到的唯一一个同时满足以下条件的实现：明确列出三个原 V2 FONT 输出名、执行 XPR 解密/重加密、允许改变 XPR 文件名而不改变明文逻辑内容，并且留下了与当前 V2 patched FONT provenance 完全相同的磁盘产物。

最终判断：

| 项目 | 结论 |
|---|---|
| MLG patched `0007ccd8.xpr -> patched output 0007ccd8.xpr` | `PROVEN`：简单 copy，未经过 FONT 内容重建 |
| MLG patched `000ebbe8.xpr -> patched output 000ebbe8.xpr` | `PROVEN`：简单 copy，未经过 FONT 内容重建 |
| MLG patched `0007ccd8.xpr -> patched JPN output 00c7c9f9.xpr` | `PROVEN`；现有输出满足 `EXACT_REPRODUCTION_CONFIRMED` |
| 原 V2 工具链源码是否存在于 V2 Git | `UNKNOWN`：V2 Git 没有跟踪这套旧 FONT 生成脚本；脚本存在于相邻非 Git Experimental 工作区 |
| 后来的 selector-aware `Build-FontXprV2.py` 是否是原 V2 工具 | `PROVEN`：不是。它是当前工作树中新加入的、未被 Git 跟踪的另一条 clean-JPN 重建路线 |

## 1. 主生成脚本

### 1.1 `Build-ExperimentalPayload.ps1`

路径：

`D:\GAME\test\steam 合金装备大师合集2 合金装备和平行者汉化补丁\JPVoice_CNText_Experimental\Build-ExperimentalPayload.ps1`

文件 SHA256：`67788523EDCC24C4A799C474BA8D98AE3C1103A2A0C1273746ABCC148DBBBF58`

关键代码位置：

- 第 84–90 行：FONT map
- 第 98–123 行：copy、decrypt、XPR2 magic 检查、按目标文件名重新加密
- 第 335 行：payload 构建完成标记

核心 map 是：

```powershell
'0007ccd8.xpr' = @('0007ccd8.xpr', '00c7c9f9.xpr')
'000ebbe8.xpr' = @('000ebbe8.xpr')
```

脚本将源路径设置为：

```text
$PatchRoot\mgspw\FONT\<sourceName>
```

在当前工作区，实际补丁源目录是：

`D:\GAME\test\steam 合金装备大师合集2 合金装备和平行者汉化补丁\mgspw\FONT`

这个目录没有名为 `MLG_CN` 的子目录；它是原汉化补丁的全局 FONT 目录。其 `0007ccd8.xpr` 和 `000ebbe8.xpr` 与当前 V2 的 `MLG_CN` 同名文件逐字节相同，因此在逻辑上就是本次目标的 MLG patched FONT 输入；它们不是官方 JPN `00c7/001c` base。

对 map 中第一个元素，脚本直接执行：

```text
source FONT/0007ccd8.xpr
 -> Add-PayloadFile FONT/0007ccd8.xpr
```

对 `00c7c9f9.xpr`，脚本执行：

```text
sourceName = 0007ccd8.xpr
targetName = 00c7c9f9.xpr
建立临时 hard link
OuterCrypt(nativeSource, nativePlain, sourceName)
检查 nativePlain 前四字节为 XPR2
OuterCrypt(nativePlain, nativeEncrypted, targetName)
Add-PayloadFile(nativeEncrypted, FONT/00c7c9f9.xpr)
```

脚本没有 XPR parser、USER/FontData parser、TX2D parser、glyph builder、atlas builder 或 charmap writer。它只验证解密后是 `XPR2`，因此这条路径不会修改 XPR2 内部逻辑内容。

### 1.2 `001cbbd1.xpr` 的处理

脚本第 92–96 行显示：

```powershell
if ($IncludeExpandedSmallJapaneseFont) {
    $fontMap['000ebbe8.xpr'] = @('000ebbe8.xpr', '001cbbd1.xpr')
}
```

所以 `001cbbd1.xpr` 不是默认原 V2 输出。它是显式 `-IncludeExpandedSmallJapaneseFont` 诊断选项下，将大号中文候选扩到日文小号 selector 的实验输出。脚本注释记录的约 17 MiB 小号扩展崩溃属于未同步 runtime Width/Height 的历史结果；后续 full dump 定位到 hardcoded `2048×1024` target，`4096×4096` runtime patch 已使同一 pure-rekey plaintext 实机通过。该考古事实不把第三方字体升级为未来 production dependency。

这正好解释了原 V2 patched JPN output 只有三个文件，而不是四个文件：它覆盖了 MLG `0007/000e` 两个原名文件，并额外生成了 JPN large `00c7`，没有默认生成 JPN small `001c`。

## 2. `OuterCrypt` 工具行为

### 2.1 源码与二进制

源码：

`D:\GAME\test\steam 合金装备大师合集2 合金装备和平行者汉化补丁\JPVoice_CNText_Experimental\tools\OuterCrypt.cpp`

源码 SHA256：`DEF0B6E5B15ACBD09C9CBEF892E81B2C3FD2B0C19E80477CDF7D509EBCCFAA22`

二进制：

`D:\GAME\test\steam 合金装备大师合集2 合金装备和平行者汉化补丁\JPVoice_CNText_Experimental\tools\OuterCrypt.exe`

二进制 SHA256：`47F83E0E07631C626B915FCBE160EEE63E3E0B7BD6C341A22E33DB6D092BBA1F`

相同二进制副本也存在于：

`D:\GAME\test\MGSPW_FontAnalyze2\OuterCrypt.exe`

该副本 SHA256 相同。

### 2.2 参数和 seed

工具用法是：

```text
OuterCrypt.exe <input> <output> [key-filename] [max-bytes]
```

如果提供第三参数，就使用该参数作为 key filename；否则使用输入文件名。`filename_seed()` 从路径最后一个分隔符之后开始，只计算扩展名前的文件名字符。随后使用该 seed 初始化 PC outer stream，并从偏移 `0x14` 开始对数据按 4 字节 XOR；常量为 `0xB9D3018F`。

因此它明确支持：

```text
同一份 XPR2 明文
 -> 以 0007ccd8.xpr 的 seed 解密
 -> 以 00c7c9f9.xpr 的 seed 重新加密
```

解密和加密是同一个 XOR transform；工具自身不区分方向。文件内容和文件名 seed 是分开的，改变 key filename 只改变外层密文，不改变明文 XPR2。

### 2.3 对用户要求的字段影响

| 字段 | 原 V2 FONT 路径是否修改 |
|---|---|
| USER / FontData | 否；只做外层 XOR transform |
| charmap | 否 |
| glyph records | 否 |
| atlas width/height | 否 |
| atlas bitmap / FontTexture 内容 | 否 |
| TX2D descriptor | 否 |
| XPR2 header/resource layout | 否 |
| 外层加密字节 | 是；根据目标文件名重新计算 |

现有三路 census 对解密后的完整逻辑 XPR 做了独立确认：patched `JPN_CN/00c7c9f9.xpr` 与 patched `MLG_CN/0007ccd8.xpr` 的 USER、charmap、glyph records、atlas 和 TX2D 均一致；二者仅磁盘外层密文字节不同。

## 3. 三个原 V2 输出的实际证据

### 3.1 源和输出 SHA256

| 角色 | 文件 | 大小 | 磁盘 SHA256 |
|---|---|---:|---|
| MLG patched source | `mgspw/FONT/0007ccd8.xpr` | 16,959,612 | `149668D9FACF5491B0A8A2B93B87EF3FF3E290AC139E1404AAD30AAC25D8C73C` |
| MLG patched source | `mgspw/FONT/000ebbe8.xpr` | 16,959,500 | `025FA6553EA4200F8F0FE4D9CCFE1AE9178F87C69E1BF87704AEC84AAE65FA80` |
| stage2 output | `payload-stage2/mgspw/FONT/00c7c9f9.xpr` | 16,959,612 | `BF1D2F6D9727A71C734E69B2F6406503818E4C5B21A7F548FBC80D9DEEC9B793` |
| current V2 patched output | `font/JPN_CN/0007ccd8.xpr` | 16,959,612 | `149668D9FACF5491B0A8A2B93B87EF3FF3E290AC139E1404AAD30AAC25D8C73C` |
| current V2 patched output | `font/JPN_CN/000ebbe8.xpr` | 16,959,500 | `025FA6553EA4200F8F0FE4D9CCFE1AE9178F87C69E1BF87704AEC84AAE65FA80` |
| current V2 patched output | `font/JPN_CN/00c7c9f9.xpr` | 16,959,612 | `BF1D2F6D9727A71C734E69B2F6406503818E4C5B21A7F548FBC80D9DEEC9B793` |

结论：

- `0007ccd8`：源、stage2、V2 JPN_CN 三者完全相同。
- `000ebbe8`：源、stage2、V2 JPN_CN 三者完全相同。
- `00c7c9f9`：stage2 输出与 V2 JPN_CN 完全相同。
- 因此已有磁盘产物满足 `EXACT_REPRODUCTION_CONFIRMED`。本轮没有重新执行工具，也没有创建临时 XPR；直接利用原有 stage2 输出和当前 V2 文件的 SHA256/字节比较完成验证。

### 3.2 生成日志和 manifest

`payload-stage2\stage2-build-reports\build-resume-20260831-191025.stdout.log` 记录了：

```text
KEY=0007ccd8.xpr
SEED=0x03201d67
BYTES=16959612
KEY=00c7c9f9.xpr
SEED=0x3af33be1
BYTES=16959612
```

`payload-stage2\experimental-payload-manifest.json` 记录三个 FONT 文件和上述三个输出 SHA256。manifest 的生成时间为 `2026-08-31T22:01:51.3502552+08:00`，与该阶段 payload 的文件时间和日志一致。

`JPVoice_CNText_Experimental\README.md` 记录该阶段流程为“把大号中文字库重新加密到日语大号字体选择器”，并说明默认安全版本保留日版小号字体。该报告只把 README/日志作为历史工作区证据，不把它当作新的 runtime 推断。

## 4. 原 V2 FONT 完整流程

按源码和现有产物还原，流程是：

1. 以原汉化补丁全局 `mgspw\FONT` 为 FONT 输入；其中 `0007ccd8.xpr` 和 `000ebbe8.xpr` 就是当前 census 中的 MLG_CN 对应文件。
2. `0007ccd8.xpr` 直接 copy 到输出 `FONT\0007ccd8.xpr`。
3. `000ebbe8.xpr` 直接 copy 到输出 `FONT\000ebbe8.xpr`。
4. 对同一份 `0007ccd8.xpr` 建立临时链接，以源文件名 `0007ccd8.xpr` 解密。
5. 只检查解密结果前四字节为 `XPR2`，不解析、不重建、不修改 XPR2 内部资源。
6. 用目标文件名 `00c7c9f9.xpr` 作为新 seed 对同一明文重新加密。
7. 将重加密结果写为 `FONT\00c7c9f9.xpr`。
8. 默认不生成 `001cbbd1.xpr`；只有显式诊断开关才把 `000ebbe8` 扩展映射到 `001cbbd1`。
9. 由 `Assemble-JpnCnTestPackage.py` 将已有三个 FONT 文件复制进 V2 `build/readiness/full_package`；该步骤不是 FONT 生成步骤。

## 5. 其他候选脚本/工具的排除结果

### 5.1 `tools/Assemble-JpnCnTestPackage.py`

路径：

`D:\GAME\test\steam 合金装备大师合集2 合金装备和平行者汉化补丁\JPVoice_CNText_V2\tools\Assemble-JpnCnTestPackage.py`

Git 来源：

- 首次出现于 commit `52fd9319fbae4a5f1e61b6e40fd49b009742739f`（2026-09-09，`Add V2 source, docs, tools, and translations`）。
- 在 commit `c3847b6bd30bb433e2ce919da31edd026b1cc86c` 中随 briefing pipeline 更新。

该脚本的行为是：

```python
font_names = ["0007ccd8.xpr", "000ebbe8.xpr", "00c7c9f9.xpr"]
shutil.copy2(source, destination)
```

它只复制已存在的三文件；没有 XPR 解密、seed、repack、USER/TX2D/glyph/atlas/charmap 操作。因此它是打包工具，不是原 FONT 生成工具。

### 5.2 当前工作树的 `tools/Build-FontXprV2.py`

路径：

`D:\GAME\test\steam 合金装备大师合集2 合金装备和平行者汉化补丁\JPVoice_CNText_V2\tools\Build-FontXprV2.py`

该文件当前为 Git 未跟踪文件，文件开头自称：

```text
Build selector-aware MGSPW XPR fonts from the local JPN/MLG comparison bundles.
```

它读取本地四文件 JPN/MLG comparison collection，调用 `core.pc_crypto` 解密，解析 `core.xpr_font`，按 production corpus 和 selector fixture 生成/写出新的 USER、TX2D、glyph、atlas、charmap 等内容。它是后来出现的 selector-aware 实验路线，和本报告确认的原 V2 外层 rekey 路线不同；不能用它解释原 V2 三文件的来源。

相关文件 `core\xpr_font.py`、`core\pc_crypto.py` 也都是当前 V2 工作树的未跟踪分析/实验文件，不属于 V2 Git 的原始 FONT builder。

### 5.3 `Rekey-Olang.cpp/.exe`

路径：

`D:\GAME\test\steam 合金装备大师合集2 合金装备和平行者汉化补丁\JPVoice_CNText_Experimental\tools\Rekey-Olang.cpp`

该工具确实也使用 filename seed，但它会检查 RBX magic 并改写 OLANG/RBX 内部 ID，目标是 OLANG 文本，不是 XPR。不能作为 FONT builder；不能把它与 `OuterCrypt` 混为一谈。

### 5.4 Phase2、第三方工具和字体分析目录

- `D:\GAME\test\MGSPW_JPVoice_ENText_Phase2\Probe-PcOuterDecrypt.cpp/.exe`：用于 PDT 外层解密探测，没有 XPR 生成流程。
- `D:\GAME\test\MGSPW_JPVoice_ENText_Phase2\Rekey-Olang.cpp/.exe`：用于 OLANG 内部 ID rekey，没有 XPR 路径。
- `third_party\PeaceWalkerTools\Formats\PGF.cs`：PSP PGF 解析代码，不是当前 HD XPR2 builder；没有发现与三个 FONT 文件对应的 XPR repack 入口。
- `D:\GAME\test\MGSPW_FontAnalyze2`：含 `OuterCrypt.exe` 的同 hash 副本以及 `jp-0007.raw`、`jp-00c7.raw`、`cn-a.raw` 等只读分析副本；没有发现脚本或 XPR 重建源码。`cn-a.enc` 与当前 `0007ccd8.xpr` 同 hash，`cn-b.enc` 与当前 `000ebbe8.xpr` 同 hash。

## 6. Git 历史审计

### 6.1 V2 可见分支和 tags

检查了：

- `main`
- `sol-translation`
- `codex-rescue-20260912`
- 对应 `origin/*` refs
- 所有 tags（没有发现 tags）
- HEAD 和 branch reflog

V2 Git 从最早的 source/tool drop `52fd9319fbae4a5f1e61b6e40fd49b009742739f` 起就没有跟踪 `font/`、`JPN_CN/`、`MLG_CN/`、`.xpr`、`OuterCrypt.cpp/.exe` 或 FONT builder。当前 `font/` 和 `Build-FontXprV2.py` 是工作树未跟踪内容；这些目录名是本地 provenance/分析布局，不改变官方 JPN 只有 `001c/00c7` 的事实。

因此不存在一个可以在 V2 Git 中指认的“最早出现 patched JPN FONT”的 commit：patched FONT 从未进入该 Git 历史。

### 6.2 删除历史、历史 tree、unreachable objects

执行了：

- `git log --all --full-history --diff-filter=D`
- 逐个检查所有可见 branch/tree 的 FONT/XPR/OuterCrypt 路径
- `git fsck --full --no-reflogs --unreachable`
- 检查所有 unreachable commit 的 tree 文件名
- 检查 reflog 中的 amend/删除轨迹

结果：

- 没有找到被删除的 FONT/XPR builder 文件。
- 没有找到被删除的 `Build-ExperimentalPayload.ps1` 或 `OuterCrypt.cpp` blob。
- unreachable commits 主要是 `build: regenerate production state from tracked masters` 的 amend 版本；其 FONT/XPR 相关命中只有 `core/pc_crypto.py`，没有 FONT 文件或 FONT builder。
- `V2_OLD_20260913` 是工作区快照，不是包含旧 FONT builder 的 Git 历史；其中仍没有 `Build-FontXprV2` 之外的原 V2 FONT builder。

所以旧 FONT 生成源码的唯一可用保存位置是相邻的非 Git Experimental 工作区，不能声称它有一个可恢复的 V2 commit ID。

## 7. 是否可以 byte-identical 重现三个 patched FONT XPR

### 7.1 已有产物层面

可以确认：

```text
0007ccd8.xpr  -> copy                    -> patched/0007ccd8.xpr  EXACT
000ebbe8.xpr  -> copy                    -> patched/000ebbe8.xpr  EXACT
0007ccd8.xpr  -> decrypt(old name)       -> XPR2 plaintext
             -> encrypt(new name 00c7)   -> patched JPN/00c7c9f9.xpr EXACT
```

三个目标文件都已有磁盘 SHA256 与原 V2 patched provenance 目录逐字节匹配，因此不是只有逻辑内容相同，而是：

`EXACT_REPRODUCTION_CONFIRMED`

### 7.2 本轮执行限制

本轮没有再次调用 `OuterCrypt.exe`，没有创建临时输出，也没有运行完整 `Build-ExperimentalPayload.ps1`。原因是用户明确要求只读考古、不要重建 XPR；已有 stage2 结果、manifest、日志和当前 V2 文件已经提供了 byte-identical 证据。

## 8. 尚未找到的部分

以下内容仍是 `UNKNOWN`：

1. `Build-ExperimentalPayload.ps1` 在外部工作区中的原始创建者、原始 commit 或第一次运行的完整命令行；该目录不是 Git repository。
2. `OuterCrypt.exe` 的原始编译工程参数、编译器版本和最初生成时间；源码与二进制功能一致，但没有工程文件或 Git commit 可追溯。
3. 是否曾经存在一个比 `Build-ExperimentalPayload.ps1` 更早、名字不同的同等 FONT wrapper；当前目录和 V2 Git 中没有找到证据。
4. 原 V2 的“实机通过”历史记录能确认到工作区 README/构建产物层面；本轮没有重新启动游戏，也没有把 runtime 行为作为代码考古的推断。

## 最终分档结论

### PROVEN

- 原 V2 的实际 FONT 行为是 copy 两个文件，再对 `0007ccd8` 做 filename-seeded outer decrypt/re-encrypt 生成 `00c7c9f9`。
- `OuterCrypt` 支持显式指定 key filename，seed 来自文件名 stem。
- 该路径不修改 USER、charmap、glyph、atlas、TX2D 或 XPR2 逻辑内容。
- 当前 V2 patched provenance 目录的三个 XPR 与已存在 stage2 产物逐字节相同。
- `0007ccd8` 和 `000ebbe8` 的 patched 版本是直接 copy；`00c7c9f9` 满足 `EXACT_REPRODUCTION_CONFIRMED`。
- 后来的 selector-aware `Build-FontXprV2.py` 不是原 V2 生成代码。

### HIGH-CONFIDENCE

- `Build-ExperimentalPayload.ps1 + tools/OuterCrypt.exe` 就是原 V2 已实机验证成功的 FONT 工具链；它是当前找到的唯一同时具备明确 map、目标文件名 rekey 行为、构建日志、manifest 和相同最终产物的实现。
- 原 V2 的默认安全 FONT 集合故意排除 `001cbbd1.xpr`；该文件属于后来诊断用的小 selector 扩展实验。

### UNKNOWN

- 这套旧工具链在原始项目中的正式 Git commit、原始版本标签和最初命令行无法从当前可见资料恢复。
- 不能证明不存在更早但已完全遗失的同功能 wrapper；只能说明当前所有可见目录、V2 Git 历史、删除历史和 unreachable trees 中未找到另一份候选实现。
