# SMALL_JPN FontData / FontTexture 配对分析

本报告为只读分析；本轮没有修改或重建任何 XPR。

来源标签固定为：官方 JPN small = `001cbbd1.xpr`，官方 JPN large = `00c7c9f9.xpr`；官方 MLG small = `000ebbe8.xpr`，官方 MLG large = `0007ccd8.xpr`。本报告中的 MLG donor/比较数据来自 MLG lane，不代表官方 JPN depot 同时包含 `0007/000e`。

## 当前 Loading 状态覆盖

本报告后续结论只服务于当前两段 Loading 角色语录，不代表全游戏 SMALL_JPN 缺字审计。

```ini
LOADING_REQUIRED_GLYPHS = 35
LOADING_EXISTING_GLYPHS = 11
LOADING_MISSING_GLYPHS = 24
LOADING_FONTDATA = JPN/001cbbd1.xpr
LOADING_CONFIRMED_ATLAS = JPN/001cbbd1.xpr own TX2D
TEST_A_001C_OWN_TX2D_RUNTIME = PASS
```

TEST A 已实机确认：只改 `001cbbd1.xpr` 自带 TX2D 中 glyph 239（`我 U+6211`）后，Loading 页面中的“我”发生变化。因此当前 Loading 补字目标是单文件 `001cbbd1.xpr`。`00c7c9f9.xpr` 的纹理比较仅保留为历史静态交叉分析，不能再写成已确认的 Loading 配对关系。

## 结论摘要

- `001cbbd1.xpr` 的 `USER/FontData`：359 条 record，358 个 mapped codepoint。
- `00c7c9f9.xpr` 的 `TX2D/FontTexture`：4096×4096，format=2，pitch=4096。
- `001c` 自带的 TX2D 是 `2048×1024`；因此这里明确区分“001c 自带纹理”和用户指定的 `00c7` 纹理，不能把二者静默视为同一张 atlas。
- 001c 记录 UV 对 001c 自带纹理越界：`0`；对 00c7 纹理越界：`0`。
- 未被 001c charmap 正向引用的 record：`0`。这些 record 是否可复用必须结合像素和 runtime 验证，不能仅凭未映射判定为空槽。

## 文件与资源布局

| XPR | encrypted SHA256 | decrypted SHA256 | header/data | USER | TX2D | FontData | texture |
|---|---|---|---|---|---|---|---|
| SMALL_JPN_DATA_001C | `5625066b835e6f26f310781fbbd3ef4f9ea93a77be2a4044289c11b74a767414` | `f4fdb335a56f81bee4e4a13be71f5518827ebcf42fbfa86d30d2f1de3c6dd025` | `0x21810/0x200000` | `0x90+0x214CA` | `0x5C+0x34` | records=359, mapped=358, record_rel=`0x1FE5A`, prefix=`0167` | 2048×1024, pitch=2048, fmt=2, tiled=0, endian=0 |
| SMALL_JPN_TEXTURE_00C7 | `1f7a18f28d0d67d7a6a65a5286a1e48c97d595829b4c99325fb2b5772b921e8d` | `31b8eb9a7c86b1429fb7fa0d12688c65c9123e307c5f0e8c42f1df67a7cd9e6b` | `0x29010/0x1000000` | `0x90+0x28F32` | `0x5C+0x34` | records=2309, mapped=2308, record_rel=`0x1FEE2`, prefix=`0905` | 4096×4096, pitch=4096, fmt=2, tiled=0, endian=0 |
| MLG_CN_BIG_0007 | `149668d9facf5491b0a8a2b93b87ef3ff3e290ac139e1404aad30aac25d8c73c` | `90ba15daced7bf7cb2b2d24731d0c99c049716f2101262510b2ae554d27157ff` | `0x2C870/0x1000000` | `0x90+0x2C768` | `0x5C+0x34` | records=3209, mapped=3208, record_rel=`0x1FED8`, prefix=`none` | 4096×4096, pitch=4096, fmt=2, tiled=0, endian=0 |
| MLG_CN_SMALL_000E | `025fa6553ea4200f8f0fe4d9ccfe1ae9178f87c69e1bf87704aec84aae65fa80` | `d283efc593971187725ee18f60394a0fe053009c85b284e816e9e6d4ac119b86` | `0x2C800/0x1000000` | `0x90+0x2C378` | `0x5C+0x34` | records=3146, mapped=3145, record_rel=`0x1FED8`, prefix=`none` | 4096×4096, pitch=4096, fmt=2, tiled=0, endian=0 |

### 001c FontData 内部布局

- USER payload 起点：file `0x90`，大小 `0x214CA`。
- 固定头：relative `0x0000..0x15`；`last_code` 位于 relative `0x14`，值 `U+FF1F`。
- dense charmap：relative `0x16..0x1FE57`，file `0xA6..0x1FEE7`，每项 big-endian u16。
- 记录计数字段：relative `0x1FE58` / file `0x1FEE8`，raw `0167` = `359`。
- GlyphRecord table：relative `0x1FE5A` / file `0x1FEEA`，stride 16 bytes，结束于 relative `0x214CA`；无 suffix `0` bytes。
- record 字段按现有 parser 为 `u0,v0,u1,v1,bearing_x_raw,width,advance,reserved`，均 big-endian u16；没有在记录后发现额外 sentinel/trailer。

## 001c record / 00c7 atlas 历史交叉比较

001c 的 FontData 记录本身只保存 UV 和 metrics。此前将这些 UV 应用到 00c7 TX2D，是为了排查候选 selector；这不是当前 Loading 的已确认运行时关系，也不是本轮补字目标。

- 001c 记录矩形联合包围盒：`(2,1)-(2040,804)`。矩形面积和=1481964，矩形间重叠面积（简单两两计数）=0。
- 001c 自带纹理与 00c7 在这 359 个相同 UV 矩形上的像素块完全相同数：`1/359`；非零像素数量相同数：`1/359`。因此静态上不能把 00c7 视为 001c 自带 atlas 的 byte-identical 替代。
- TEST A 已提供更直接的 runtime 证据：`001cbbd1.xpr` 自带 TX2D 参与 Loading 渲染。当前不再把 `001c FontData + 00c7 FontTexture` 写成 Loading 的确认配对；是否存在其它资源同时参与不属于当前 PoC 必须解决的问题。
- 00c7 atlas 总像素：16777216；按 001c records 计算的剩余物理区域非常大，不能据此断言 runtime 可安全追加，仍需确认 slot/record 容量。
- 001c 自带 TX2D：2048×1024；00c7 TX2D：4096×4096。两者都是 format=2、linear、8-bit texel，但尺寸不同。
- 001c record 矩形尺寸分布（前 8 项）：`[((66, 66), 317), ((46, 66), 3), ((45, 66), 3), ((50, 66), 3), ((53, 66), 3), ((23, 66), 3), ((1, 66), 2), ((20, 66), 2)]`；其中 `317` 条是完整 66×66 CJK-like cell，其余是窄字/ASCII 等不同 width。
- 00c7 自己的 FontData 有 `2309` 条 record、`2308` 个正向 mapped codepoint；其自身 record 矩形尺寸分布前 8 项：`[((66, 66), 1987), ((33, 66), 27), ((61, 66), 18), ((60, 66), 15), ((48, 66), 14), ((31, 66), 12), ((64, 66), 12), ((34, 66), 11)]`。这组 2309 records 不能直接替代 001c 的 359-index 表。

## 实际字符验证

- `中 U+4E2D`: 001c `143; rect=(1059, 269, 1125, 335); own_nz=1247; 00c7_nz=1112`; 00c7 own FontData lookup `303; rect=(3256, 202, 3322, 268)`
- `们 U+4EEC`: 001c `0; rect=(4, 1, 25, 67); own_nz=183; 00c7_nz=132`; 00c7 own FontData lookup `0; rect=(6, 1, 27, 67)`
- `陆 U+9646`: 001c `0; rect=(4, 1, 25, 67); own_nz=183; 00c7_nz=132`; 00c7 own FontData lookup `0; rect=(6, 1, 27, 67)`
- `拘 U+62D8`: 001c `0; rect=(4, 1, 25, 67); own_nz=183; 00c7_nz=132`; 00c7 own FontData lookup `998; rect=(3260, 1006, 3326, 1072)`
- `我 U+6211`: 001c `239; rect=(1733, 470, 1799, 536); own_nz=1887; 00c7_nz=984`; 00c7 own FontData lookup `961; rect=(694, 1006, 760, 1072)`

对当前 Loading 缺字中的 `们/陆`，以及交叉验证字符 `拘`，001c 的 dense charmap 值均为 0；它们都会落到 record 0 的 fallback/missing-glyph 路径。00c7 自身 FontData 是否存在对应字符不改变当前 Loading 单文件补字结论。

### 001c 中一个正常中文 `中` 的完整 record

`中 U+4E2D` -> glyph index `143` -> record file offset `0x207DA` -> raw `0423010D0465014F0008004200460000` -> rect `(1059, 269, 1125, 335)`, width=66, bearing_x=8, advance=70。

## 未使用 record / 空槽

- record `0`: `UNUSED_NONEMPTY`, mapped=`none`, rect=(4,1)-(25,67), 001c nonzero=183, 00c7-at-same-UV nonzero=132, raw=`00040001001900430003001500170000`。
- 结论：没有 `UNUSED_EMPTY` record。唯一未被正向 charmap 映射的 record 0 有非零像素，且其矩形是 fallback/missing-glyph 候选；不能作为 `们` 的安全空 glyph slot。

当前 Loading 24 个缺字的共同结构状态是：`charmap value=0 -> GlyphRecord 0 -> fallback/missing glyph -> 实机显示为 ·`。这里的 24 个字符仅指 Loading 文本集合，不包含其它场景发现的 SMALL_JPN 缺字。

## MLG_CN donor 兼容性

MLG 两套字体的 `们` 都已存在；以下是历史 donor 兼容性事实，不代表当前要继续研究 donor 风格，也不代表当前 Loading 目标应切换到 MLG XPR。
- MLG-0007: `们` -> index 729, record=052B02A9056502EC0004003A003E0000, rect=(1323, 681, 1381, 748), bitmap=58x67, bbox=[3,7,54,59], coverage=0.3994, mean=172.19
- MLG-000E: `们` -> index 552, record=06E40331071E03740004003A003E0000, rect=(1764, 817, 1822, 884), bitmap=58x67, bbox=[3,7,54,59], coverage=0.3994, mean=172.19

- 三套资源的 FontTexture 都是 format=2、tiled=0、endian=0 的 8-bit 线性灰度存储；因此像素编码层面可转换。
- MLG 的字面通常使用更大的 atlas cell/metrics，而 001c 是 SMALL_JPN；不能直接把 MLG 的 16-byte record 原样复制到 001c。至少要把 bitmap 重采样/栅格化到 SMALL_JPN 可用的槽尺寸，并重新设置 UV、width、bearing_x、advance。
- 若 001c 确有安全的未映射空 record，可保持 glyph count 不变，只改 charmap、该 record 和一个未占用纹理矩形；若未映射 record 是 fallback/missing glyph，则不能复用。

## 当前 one-glyph patch 结论

- 没有可确认安全的空 glyph record：record 0 虽未被正向 charmap 使用，但有实际 fallback 像素，禁止复用。
- 因此最小可行方案不是覆盖现有 record，而是 append 一个新 16-byte record，并同步更新 001c 的 2-byte glyph count、USER size、charmap；本轮不自动扩容，也不修改 XPR。
- 不能仅修改 001c charmap 指向 00c7 自己的 `们` record：001c 与 00c7 的 GlyphRecord 表属于不同 FontData，index/UV/metrics 不共享。

`们 U+4EEC` 的单字 PoC 已经实机成功，但当前 bitmap 与原版 SMALL_JPN 中文字风格不统一，因此状态是 `TECHNICAL_POC_RUNTIME_SUCCESS`，不是最终字形完成。

## 明确未知 / 暂不扩展

- `00c7` 是否参与其它字体路径不在当前 Loading 补字 PoC 范围内。
- 最终字体来源、glyph 风格、rasterization、字号/baseline/metrics 仍未决定；本轮冻结，不继续研究。
- 当前不批量处理其余 23 个 Loading 缺字，也不扩展到其它 SMALL_JPN 场景。
