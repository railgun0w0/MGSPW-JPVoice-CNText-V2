# MGSPW 字库资源分析

> **ARCHIVED / HISTORICAL REFERENCE — 2026-09-14 snapshot.** 本文保留阶段性结构分析、coverage 和实验背景，但早于最终 JPN001c runtime dimension 根因。当前权威结论、Golden Baseline 与下一阶段设计见 [`../doc/README.md`](../doc/README.md)。不得用本文的旧风险判断覆盖 `font/doc/`。

更新时间：2026-09-14
范围：官方 clean JPN 字库、当前 V2 中文测试包、旧 Experimental/MLG 字库候选、已有静态/格式分析工具。
本轮只读；没有修改 clean JPN、translation mapping、production translation、DAT、KEY 或任何字库资源。

> 2026-09-16 状态收敛：本文关于 expanded `001c` / 约 17 MiB 输入的崩溃记录只描述**未同步 runtime Width/Height**的历史路径。full dump 与后续实机已经证明，`main+0x436AB`/`main+0x436B5` patch 为 `4096×4096` 后，patched MLG000e pure rekey 可正常启动并显示中文。当前结论见 [`../doc/FONT_TECHNICAL_ARCHIVE.md`](../doc/FONT_TECHNICAL_ARCHIVE.md)。

## 结论摘要

Peace Walker 的文字渲染不是一套字体，而是至少三条资源链：

1. `FONT/*.xpr`：XPR2 字库包，负责比例字体文字；当前证据与实机结果表明它覆盖主对白、字幕和 BRIEFING 等大字号文本路径。
2. `Text/*.txp`、`loading/*.txp` 以及 SLOT 内嵌 `.txp`：大量 UI atlas。已完整确认其中一套 caps-only UI grid 的字节到 cell 映射；其余 atlas 目前只能可靠识别为 font-like，不能凭外观猜测映射。
3. `JPN/disc0_rel/009645fa.PDT` 内的 `db_font.txp`、`fontprint.txp`：STAGEDAT 内嵌的 DDS 字库/字体纹理资源，容器已定位，但 glyph rectangle table 和具体 UI 调用尚未完全解出。

当前“多数中文能显示、少数小 UI 不显示”最符合以下组合原因：

- **A：使用了另一套字体 —— 已确认存在。** executable 将 `FontTexture` 和 `FontData` 分别绑定到大小不同的 XPR selector；TXP 还存在独立 UI atlas。
- **B/C：mapping 或 atlas 缺字 —— 已由数据直接证明会发生。** clean JPN 是子集字库；当前 CN 扩展候选仍有未映射 code point，且小 XPR 的 `001cbbd1.xpr` 未进入当前中文包。
- **D：字符编码过滤 —— 对 XPR 主路径不是首要原因。** XPR charmap 直接按 UCS-2/Unicode code point 索引；但 caps-only TXP 路径确实使用单字节 cell mapping，存在代码页/字节过滤风险。
- **E：字号或 font selector 不同 —— 已确认存在。** 官方 JPN 只有 `00c7c9f9.xpr`（大）和 `001cbbd1.xpr`（小）；二者分别使用 4096×4096 与 2048×1024 atlas，且 `FontData`/`FontTexture` selector 不同。
- **F：shader/render path 限制 —— 本轮没有直接证据。** 不能完全排除，但当前证据优先指向资源选择、charmap 和 atlas 覆盖。

因此，下一步应先按实际 UI 调用路径补齐 coverage audit，再决定是否扩展小字库；不建议把当前大 XPR 直接覆盖到小 UI selector，也不建议照搬旧 MLG_CN 的 3 文件组合。

## 1. 搜索范围与来源

### 官方 clean JPN

根目录：

`D:\GAME\test\JPN\MGS_PW\mgspw`

直接搜索得到：

| 资源 | 结果 |
|---|---:|
| `FONT/*.xpr` | 2 个：`001cbbd1.xpr`（small）和 `00c7c9f9.xpr`（large） |
| `Text/*.txp`、`loading/*.txp` | 8 个文件，其中 7 个含 TXP texture，1 个为 0 texture 包 |
| 非脚本二进制 | `.PDT`、`.DAT`、`.KEY`、`.bin`、`.cmf`、`.vpo`、`.fpo` 等；没有发现另一个显式命名的 font/glyph/charmap 文件 |
| executable 字符串 | 命中 `\\FONT\\`、`FontTexture`、`FontData`、`pspfont_*`、`area_%02d_pspfont`、`key_page2_txt_%02d_pspfont` |

clean JPN 的 `FONT` 位于安装根的共享目录，未发现独立的 `ENG\\...\\FONT` 目录；`MLG`/`JPN` 是文本和容器语言 lane，不能据此推导存在另一份 ENG 字库。

### 比对工具与证据

本轮使用了已有的只读解析器：

- `D:\GAME\test\PWLT_probe_20260910\src\pwfont.py`
- `D:\GAME\test\PWLT_probe_20260910\src\pwfonts.py`
- `D:\GAME\test\PWLT_probe_20260910\src\pwfontatlas.py`
- `D:\GAME\test\PWLT_probe_20260910\docs\FORMATS.md`
- `D:\GAME\test\MGS_PW_JPCN_Patch\MGS_PW_日版汉化独立分析报告.md`
- clean JPN executable：`D:\GAME\test\JPN\MGS_PW\mgspw\METAL GEAR SOLID PEACE WALKER.exe`

XPR 解密分析使用了已有只读 raw 副本：

`D:\GAME\test\MGSPW_FontAnalyze2`

这些 raw 文件只是分析输入，没有回写游戏资源。

## 2. XPR2 字库拓扑

### 2.1 容器格式

下面的四文件是本地为 JPN/MLG 对比而汇集的分析集合；其中官方 JPN depot 原生只有 `001cbbd1.xpr` 和 `00c7c9f9.xpr`。四个文件均可解析为：

```text
'XPR2'
  resource[0..1]
    TX2D  "FontTexture"
    USER  "FontData"
```

整个 XPR 不是 PSP `.PGF`，而是 HD 版 XPR2 bundle。字段均为 big-endian。

`TX2D`：

- 8-bit alpha texture，`FMT_8`
- linear、untiled、无 mip、无 swizzle
- atlas 数据可直接按 `height × width` 读取

`USER / FontData`：

- `+0x14`：最高 code point
- `+0x16`：`u16 charmap[codepoint]`
- charmap 按实际 Unicode/UCS-2 code point 索引，不是 Shift-JIS，也不是连续的文本序号
- glyph 0 是 `.notdef`
- 每个 glyph record 为 16 bytes、8 个 big-endian `u16`：
  `u0, v0, u1, v1, bearingX, width, advance, reserved`
- `advance`、`width`、`bearingX` 和 UV 都在 glyph record 中，不在另一个外部宽度表中

对应的绝对偏移由 XPR header 决定；本批文件的 charmap 通常在 `0xA6`，glyph records 在 `0x1FF68` 附近。不同文件的 header/resource size 会使后续绝对偏移略有变化，不能硬编码成统一值。

### 2.2 JPN/MLG 对比集合中的四个 XPR

以下表格保留历史分析数据，但来源标签已按官方 depot 拆开：`0007/000e` 是 MLG 字体，`00c7/001c` 是 JPN 字体。若本地目录同时出现四个文件，它表示比较集合，不表示官方 JPN FONT 同时包含四个 XPR。

| 文件 | executable 资源角色 | 文件大小 | atlas | cell/line height | glyph records | mapped code points | CJK Unified |
|---|---|---:|---:|---:|---:|---:|---:|
| `MLG/0007ccd8.xpr` | MLG large / `FontData` comparison selector | 16,918,556 | 4096×4096 | 67 | 643 | 642 | 323 |
| `MLG/000ebbe8.xpr` | MLG small / `FontTexture` comparison selector | 2,236,444 | 2048×1024 | 67 | 459 | 458 | 155 |
| `JPN/001cbbd1.xpr` | 官方 JPN small / `FontData` selector | 2,234,396 | 2048×1024 | 66 | 359 | 358 | 217 |
| `JPN/00c7c9f9.xpr` | 官方 JPN large / `FontTexture` selector | 16,945,180 | 4096×4096 | 66 | 2309 | 2308 | 1966 |

解析到的关键偏移：

| 文件 | USER size | atlas texels | charmap | glyph records |
|---|---:|---:|---:|---:|
| `MLG/0007ccd8.xpr` | 141,064 | `0x2281C` | `0xA6`，0..`0xFF5E` | `0x1FF68` |
| `MLG/000ebbe8.xpr` | 138,120 | `0x2201C` | `0xA6`，0..`0xFF5E` | `0x1FF68` |
| `JPN/001cbbd1.xpr` | 136,394 | `0x2181C` | `0xA6`，0..`0xFF1F` | `0x1FEE8` |
| `JPN/00c7c9f9.xpr` | 167,730 | `0x2901C` | `0xA6`，0..`0xFF63` | `0x1FF70` |

这里的 `FontData`/`FontTexture` 是 executable 使用的 selector 分组，不是说 XPR 文件内部只有一种资源；每个 XPR 内部都同时有 `TX2D` 和 `USER`。

### 2.3 executable selector 证据

clean JPN executable 中的可读字符串片段为：

```text
\\FONT\\
FontTexture
000ebbe8.xpr
00c7c9f9.xpr
FontData
0007ccd8.xpr
001cbbd1.xpr
```

同时存在 `pspfont_queue_sema`、`pspfont_mlbuffer`、`pspfont_queue`、`area_%02d_pspfont`、`key_page2_txt_%02d_pspfont` 等字符串。

这说明：

- 大/小字号不是同一文件的简单尺寸变化；
- 纹理 selector 与数据/metrics selector 分开管理；
- 不能只替换一个 XPR 就假设所有 UI 都切换到新字库；
- `FontData=001cbbd1` 的小字号路径是当前中文包必须重点核对的 selector。

### 2.4 atlas/record 空间

clean JPN 的 XPR charmap 是稀疏的子集表：

- `0007ccd8`：642 个 mapped code points，所有 643 个 record 都被引用
- `000ebbe8`：458 个 mapped code points，所有 459 个 record 都被引用
- `001cbbd1`：358 个 mapped code points，所有 359 个 record 都被引用
- `00c7c9f9`：2308 个 mapped code points，所有 2309 个 record 都被引用

这意味着不能直接把“未使用 glyph record”当作安全空位。atlas 底部确实存在空行，但新增字符通常需要：

1. 保留/重用已有或新增的 glyph record；
2. 在空 atlas 区域写入 bitmap；
3. 更新对应 Unicode charmap；
4. 保留旧 code point、UV、advance 和 selector 配对。

当前分析只确认数据结构，没有执行上述修改。

## 3. TXP UI atlas

### 3.1 clean JPN TXP inventory

已有 TXP parser 对 clean JPN 的实际统计：

| 文件 | texture 数量 | 被识别为 font-like |
|---|---:|---:|
| `Text/0024e502.txp` | 35 | 15 |
| `Text/005302d4.txp` | 255 | 47 |
| `Text/005318e4.txp` | 84 | 24 |
| `Text/005318e5.txp` | 84 | 24 |
| `Text/0082988a.txp` | 84 | 25 |
| `Text/008299c5.txp` | 84 | 24 |
| `loading/00887993.txp` | 未被当前 detector 计入 font-like | — |
| `Text/0083be4a.txp` | 0 | 0 |
| **合计** | **626** | **159** |

`loading/00887993.txp` 是大纹理包，但当前 font-like detector 没有把它归入已解码 font sheet；不能据此断言它不含任何文字纹理。它应在后续按 loading UI 的实际 draw call 单独核对。

### 3.2 已完整确认的 caps-only UI face

canonical sheet：

`Text/008299c5.txp#10`

实测：

- 512×512
- DXT5 / TXP format 11
- cell：28×48
- 16 个逻辑列；每一行的第一个 cell 位于右侧 `x=484`，其余 15 个从左侧排列
- byte mapping：`cell = byte - 0x20`
- `0x20..0x8F` 对应前 7 行的地址空间；当前 sheet 的前 6 行完整、row 6 只有少量 glyph
- 标准空闲扩展 band 为 `0x90..0xBF`，即 48 个 cell
- 该 face 没有普通 lowercase；原游戏把部分重音大写字母放在相应低字节位置

此 sheet 的像素内容在以下四个包的 texture 10 中重复：

- `005318e4.txp`
- `005318e5.txp`
- `0082988a.txp`
- `008299c5.txp`

四份都必须视为同一 UI face 的候选副本。只改其中一份可能不会改变实际画面。

### 3.3 TXP 内嵌 SLOT 字库

已有 `pwfonts` 分析工具还识别出 SLOT 内嵌的 `.txp` sheets；旧分析统计为 215 个 font-like sheets，其中 160 个使用上述 caps grid，113 个位于 SLOT。标准 band 检查结果为：

- 35 个 caps sheet 的 `0x90..0xBF` 全部可用
- 125 个 caps sheet 已占用或空位不一致，不能用一份共享 mapping 安全覆盖

这不是 XPR 的 Unicode charmap。它是独立的单字节 cell 机制，不能用 XPR 的 codepoint 覆盖结论替代。

## 4. STAGEDAT 内嵌字体资源

位置：

`JPN/disc0_rel/009645fa.PDT`

已有 PDT/QAR 分析确认：

- STAGEDAT 是 557 entity 的 PDT；
- 其中存在 `db_font.txp`、`fontprint.txp` 字样/资源；
- 这些对象不是标准 TXP master table，而是 raw blob 中嵌入 DDS texture；
- `fontprint.txp` 至少含有 512×128 和 256×128 的 DXT5 sheet；
- 当前工具尚未定位其 glyph rectangle table、codepoint/byte mapping 或 advance table。

因此当前不能可靠回答 `db_font`/`fontprint` 分别对应哪个具体 HUD/loading/stage UI，也不能安全将它们归入 XPR 或 caps TXP 的 mapping。它们必须保留为独立后续分析项。

## 5. 官方 JPN、原 ENG、MLG/中文补丁对比

### 5.1 原 ENG 对照

当前 clean JPN 安装中的官方 JPN `FONT` 是安装根共享资源，原版 JPN depot 只提供 `001c/00c7` 两个 XPR；没有另一个外部 `ENG/MGS_PW/mgspw/FONT` 可供本轮作为 clean ENG XPR 直接比较。MLG `0007/000e` 来自独立的 MLG/reference collection，不能据目录名推导为 JPN 文件。

### 5.2 现有 MLG_CN/中文候选

现有旧 Experimental 阶段包：

`D:\GAME\test\steam 合金装备大师合集2 合金装备和平行者汉化补丁\JPVoice_CNText_Experimental\payload-stage2\mgspw\FONT`

包含：

- `0007ccd8.xpr`：16,959,612 bytes
- `000ebbe8.xpr`：16,959,500 bytes
- `00c7c9f9.xpr`：16,959,612 bytes
- 没有 `001cbbd1.xpr`

解密后的两个候选内容为：

| 候选 | atlas | glyph records | mapped code points | CJK |
|---|---:|---:|---:|---:|
| `cn-a`，用于 `0007ccd8` 和 `00c7c9f9` | 4096×4096 | 3209 / 3208 mapped | 3208 | 2880 |
| `cn-b`，用于 `000ebbe8` | 4096×4096 | 3146 / 3145 mapped | 3145 | 2831 |

对比结果：

- `cn-a` 的前 643 个 glyph records 与 MLG `0007ccd8` 完全一致；该 MLG 字库中原有的 642 个 charmap 映射也全部保持不变。
- `cn-b` 的前 459 个 glyph records 与 MLG `000ebbe8` 完全一致；该 MLG 字库中原有的 458 个 charmap 映射也全部保持不变。
- 也就是说，这两个候选看起来是“保留原 record 前缀并追加中文”的扩展，不是简单删除原字形。
- 但 `cn-a` 同时被加密写入 `00c7c9f9`，这会让当前中文包的 `00c7` 内容来源于 MLG `0007` 风格候选，而不是官方 JPN 原始 `00c7` 的 2308-record 内容；这属于必须在正式字库方案中显式决定的结构差异。
- 当前 V2 `tools/Assemble-JpnCnTestPackage.py` 固定只复制 patched `0007ccd8.xpr`、patched `000ebbe8.xpr`、patched `00c7c9f9.xpr` 三个文件，未复制 patched `001cbbd1.xpr`。

旧 Experimental 构建脚本记录过：在**没有 runtime dimension patch**时，把约 2 MiB 的日版小字体 selector 换成约 17 MiB 输入会在资源初始化阶段崩溃；`001cbbd1` 扩展因此曾被设为诊断用 opt-in。该失败后来被定位为 hardcoded `2048×1024` target 与真实 input length 的错配，不再支持“17 MiB 本身不可用”的结论。

这解释了当前实机现象：大部分中文路径使用已有扩展大字库能够显示，但走 clean 小 UI selector 的文字仍可能只能使用原日文 glyph；保留 `NEW GAME`、`LOAD GAME`、`DELETE` 为 JPN ASCII 后可以正常显示，说明该路径的原 glyph/index/advance 可用，而中文 glyph 没有进入同一路径。

## 6. 当前 UI 到字体资源的映射

下表区分“已确认”“强推断”和“尚未定位”，避免把不同字体系统混为一谈。

| UI/文本类别 | 当前最可信资源 | 证据状态 | 当前 CN 风险 |
|---|---|---|---|
| 主对白/无线电/字幕 | 当前 patched JPN large 路径；`FontData=0007ccd8`、`FontTexture=00c7c9f9` 是最可信的大 selector 组合 | 字体格式、字幕工具、实机中文显示相互支持 | 当前大候选覆盖较好，但仍需按最终 corpus 做 codepoint audit |
| BRIEFING FILES/MISSION | 同一 XPR2 比例字体路径 | BRIEFING 中文及换行已在当前包实机显示，XPR 是当前唯一已验证的 Unicode 比例字库路径 | 少数未覆盖中文或日文 ruby 仍可能产生 tofu |
| 标题画面 / Loading 等小 UI | 官方 JPN small `001cbbd1.xpr` 自带 `FontData` 与 TX2D；官方 MLG small 对应文件是 `000ebbe8.xpr` | Loading 已通过修改 `001c` 自带 TX2D 实机确认 | 当前 production 没有 patched JPN `001c`；CJK 不应默认认为可显示 |
| 部分 OLANG caps-only UI | `Text/*.txp` texture 10 及 SLOT caps sheets | byte mapping 已由原文本和 atlas grid 交叉验证 | 受单字节 mapping、重复包和 sheet 空位差异影响 |
| 其他菜单/小 HUD/按钮/数字/图标 | 多个 TXP font-like sheet，可能另有 STAGEDAT fontprint/db_font | 只确认资源存在，尚未完成逐 UI draw-call mapping | 可能是另一套 atlas、byte mapping 或 size path |
| loading/stage 专用文字 | `loading/*.txp`、STAGEDAT 内嵌字体候选 | 资源存在；`loading/00887993.txp` 当前 detector 未分类 | 不能仅按 XPR coverage 判断 |

## 7. “某些小 UI 中文不显示”的逐项判定

### A. 另一套字体

**确认存在，且是首要怀疑项。**

executable 直接列出两组 selector：

- `FontTexture`：官方 JPN small `001cbbd1.xpr` 自带 TX2D、官方 JPN large `00c7c9f9.xpr`；历史 selector 字符串还会出现 MLG `000ebbe8.xpr`。
- `FontData`：官方 JPN `001cbbd1.xpr`、`00c7c9f9.xpr`；当前 patched large 路径使用 `0007ccd8`/`00c7c9f9` 的 MLG->JPN rekey 关系。

官方 JPN 只有两个文件：`001c` small、`00c7` large。`0007/000e` 属于 MLG 对比/补丁来源；本地四文件分析集合、TXP 和 STAGEDAT 不能被统称为官方 JPN 的四字体集合。

### B. glyph mapping 缺失

**对 XPR 已确认会发生。** clean JPN charmap 只有数百到两千多个 mapped code points，未映射 code point 返回 glyph 0。当前 CN 候选增加了大量 charmap entry，但不是所有最终 corpus 字符都覆盖。

### C. atlas 没有对应汉字

**对 XPR 和 TXP 都可能发生。** XPR 的 record 会指向 atlas UV；TXP caps face 只有固定 cell。当前 CN 大候选的 atlas 扩展并不能自动扩展 clean 小 UI atlas。

### D. 字符编码被过滤

**分路径判断。** XPR 直接按 Unicode/UCS-2 查表，当前没有证据说明中文被 Shift-JIS 过滤；TXP caps face 使用低字节 cell mapping，非 ASCII/CJK 需要先通过项目自己的字节编码策略才能命中对应 cell，因此该路径存在过滤/编码限制。

### E. 字号/font ID 不同

**确认存在。** 67/66 高度、2048×1024/4096×4096 atlas、不同 selector 和不同 glyph set 都说明不能以一个“全局字体覆盖率”替代按 UI 路径的检查。

### F. shader/render path 限制

**尚不能完全排除，但不是当前首要解释。** clean JPN 中存在 `SHADER` 资源，但本轮没有建立“特定缺字画面 → 特定 shader”因果链。若某字符已确认存在于实际 selector 的 charmap、glyph record 和 atlas，却仍不显示，再针对该 draw path 检查 shader、alpha threshold、UV 或 font state。

## 8. 只读 corpus coverage probe

为衡量风险，额外对当前 JSON mapping 中的 `cn_text` 做了只读 codepoint 统计：

- JSON mapping rows：20,863
- 唯一字符：2,799
- 其中 CJK Unified Ideographs：2,615
- `cn-a ∪ cn-b` 能命中的唯一字符：2,604
- 未命中的唯一字符：195，其中 CJK：178

示例未命中 CJK 字符包括：

`佐 侣 倚 冕 凹 匀 匠 匿 卜 厥 厮 吝 呕 咆 咧 咨 咫 咳 咻 哀 哔 啜 啪 嗅 嘎 嘱 嘶 噫 噼 嚷 垦 堤 奠 娴 婴 媲`

这不是最终“游戏缺字数量”：

- 该统计只覆盖当前 JSON mapping，不包含 legacy template CSV 的全部 rows；
- 同一字符可能只出现在不会走 XPR 的 TXP/STAGEDAT UI；
- 反过来，clean JPN 仍可能在未翻译的 runtime 文本中需要日文字符；
- `cn-a`/`cn-b` 的 union 也不能证明某个具体 UI selector 能同时访问两者。

因此它只能作为下一步按资源 class、font selector、UI 场景拆分 audit 的输入。

## 9. 推荐修改方案（本轮不执行）

### 第一优先级：建立 selector-aware coverage audit

为每条最终显示文本记录：

1. resource class / file / identity；
2. 实际 UI 场景；
3. 预计 font selector：`FontData`、`FontTexture` 或 TXP/STAGEDAT；
4. visible code points（单独处理 Ruby、control、placeholder）；
5. codepoint → glyph index → glyph record → atlas UV；
6. 所需的 `advance/width` 与原文对照。

### XPR 大字库

可在 atlas 空白区扩展，但必须保持：

- 原有 charmap 映射和 glyph index 不变；
- 原有 glyph UV/width/advance 不变；
- `FontData` 与 `FontTexture` selector 成对验证；
- 对 `0007/00c7` 和 `000e/001c` 分别验证，不能把文件名相近当成同一字库。

### 小 UI XPR

历史安全要求“不要在未知 runtime 约束下直接覆盖 17 MiB 候选”仍然成立，但原因已经明确：JPN001c 必须同步 runtime Width/Height。对已验证 EXE 1.3.1.0，4096×4096 patch 路线已实机通过；其它 EXE identity 仍必须 fail closed，不能套用未经验证的 RVA/bytes。

### TXP caps face

只在确认目标 sheet、字节 mapping 和所有重复副本后处理。`0x90..0xBF` 的空 band 不是所有 160 个 caps sheet 都可用；被占用或空位不一致的 sheet 不得覆盖。

### STAGEDAT / loading

先完成 `db_font`、`fontprint` 的 rectangle table、mapping 和实际 draw-call 定位，再决定是否需要字形扩充。不要将其当作 XPR 或 TXP 的别名处理。

## 10. 本轮没有做的事情

- 没有修改 clean JPN `FONT`、TXP、STAGEDAT 或 executable；
- 没有生成新的 XPR/TXP/字体；
- 没有修改 translation mapping、production CSV、DAT、KEY；
- 没有把 MLG_CN 字库复制回 JPN；
- 没有正式接入 compiler；
- 没有把 corpus 中缺失 code point 自动写回任何资源。

## 11. 最终判断

现有证据足以确认“少数小 UI 中文不显示”不是单纯的翻译文本问题，也不是所有中文都共用一张大 XPR atlas。至少存在：

```text
大 XPR Unicode 路径
小 XPR Unicode 路径
TXP 单字节 UI atlas 路径
STAGEDAT 内嵌字体路径（mapping 尚未完全解出）
```

当前最安全的方向是保留官方 JPN topology 和既有 ASCII fallback，先按 selector/UI 场景完成字体覆盖审计，再为大字体、小字体、TXP 和 STAGEDAT 分别设计可验证的补字方案。当前 production 已处理 JPN large `00c7` 路径，但没有对应的 patched JPN small `001c`；不能把旧 MLG 的三文件输出误写成完整的 JPN 双字体方案。
