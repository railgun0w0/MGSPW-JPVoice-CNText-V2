# SMALL_JPN / MLG_CN common glyph comparison

本报告只做静态解密、FontData/FontTexture 解析和 bitmap PNG 导出；没有 runtime probe，也没有修改任何 XPR。基准字体是已确认的 Loading 小字体 `JPN/001cbbd1.xpr`。

## 文件摘要

| font | records | mapped | atlas | format/pitch | encrypted SHA256 | decrypted SHA256 |
|---|---:|---:|---|---|---|---|
| JPN001C | 359 | 358 | 2048×1024 | 2/2048 | `5625066b835e6f26f310781fbbd3ef4f9ea93a77be2a4044289c11b74a767414` | `f4fdb335a56f81bee4e4a13be71f5518827ebcf42fbfa86d30d2f1de3c6dd025` |
| MLG0007 | 3209 | 3208 | 4096×4096 | 2/4096 | `149668d9facf5491b0a8a2b93b87ef3ff3e290ac139e1404aad30aac25d8c73c` | `90ba15daced7bf7cb2b2d24731d0c99c049716f2101262510b2ae554d27157ff` |
| MLG000E | 3146 | 3145 | 4096×4096 | 2/4096 | `025fa6553ea4200f8f0fe4d9ccfe1ae9178f87c69e1bf87704aec84aae65fa80` | `d283efc593971187725ee18f60394a0fe053009c85b284e816e9e6d4ac119b86` |

## 共同字符逐字数据

字段中的 PNG 使用原始 atlas 灰度 bitmap；`_x4.png` 是仅用于查看的 nearest-neighbor 放大版本。

### `我 U+6211`

| font | mapping count | glyph index | rect | size | bearing_x | width | advance | bitmap SHA256 | PNG |
|---|---:|---:|---|---|---:|---:|---:|---|---|
| JPN001C | 1 | 239 | `(1733, 470, 1799, 536)` | 66×66 | 3 | 66 | 68 | `1c0896037932cff12dcef63b093f825e9a4ab1e6b2b0c8ba80d5423d72691490` | [../small_jpn_mlg_common_glyphs/JPN001C/U6211_我_x4.png](../small_jpn_mlg_common_glyphs/JPN001C/U6211_我_x4.png) |
| MLG0007 | 1 | 1531 | `(2709, 1497, 2767, 1564)` | 58×67 | 4 | 58 | 62 | `e47a64c240f2dba9db672df64650fe4b43a0eab16b29302ae7e3147928565071` | [small_jpn_mlg_common_glyphs/MLG0007/U6211_我_x4.png](../small_jpn_mlg_common_glyphs/MLG0007/U6211_我_x4.png) |
| MLG000E | 1 | 1413 | `(2772, 1701, 2830, 1768)` | 58×67 | 4 | 58 | 62 | `e47a64c240f2dba9db672df64650fe4b43a0eab16b29302ae7e3147928565071` | [small_jpn_mlg_common_glyphs/MLG000E/U6211_我_x4.png](../small_jpn_mlg_common_glyphs/MLG000E/U6211_我_x4.png) |

### `中 U+4E2D`

| font | mapping count | glyph index | rect | size | bearing_x | width | advance | bitmap SHA256 | PNG |
|---|---:|---:|---|---|---:|---:|---:|---|---|
| JPN001C | 1 | 143 | `(1059, 269, 1125, 335)` | 66×66 | 8 | 66 | 70 | `c1d538cd5da0fc712d250c0c8ad5befd114b7cab196d2c65fd213bf68c8fdd67` | [small_jpn_mlg_common_glyphs/JPN001C/U4E2D_中_x4.png](../small_jpn_mlg_common_glyphs/JPN001C/U4E2D_中_x4.png) |
| MLG0007 | 1 | 308 | `(3885, 137, 3943, 204)` | 58×67 | 4 | 58 | 62 | `1819df40ce52b9a4b7f6c071139738d2967e17c264a5d4ee2bc95af6d2bacd3a` | [small_jpn_mlg_common_glyphs/MLG0007/U4E2D_中_x4.png](../small_jpn_mlg_common_glyphs/MLG0007/U4E2D_中_x4.png) |
| MLG000E | 1 | 488 | `(1827, 749, 1885, 816)` | 58×67 | 4 | 58 | 62 | `1819df40ce52b9a4b7f6c071139738d2967e17c264a5d4ee2bc95af6d2bacd3a` | [small_jpn_mlg_common_glyphs/MLG000E/U4E2D_中_x4.png](../small_jpn_mlg_common_glyphs/MLG000E/U4E2D_中_x4.png) |

### `国 U+56FD`

| font | mapping count | glyph index | rect | size | bearing_x | width | advance | bitmap SHA256 | PNG |
|---|---:|---:|---|---|---:|---:|---:|---|---|
| JPN001C | 1 | 189 | `(285, 403, 351, 469)` | 66×66 | 6 | 66 | 68 | `cd192d6eeadbef3c3159506e3f1e71f0d4a9eb5f48228d42821bad403186f884` | [small_jpn_mlg_common_glyphs/JPN001C/U56FD_国_x4.png](../small_jpn_mlg_common_glyphs/JPN001C/U56FD_国_x4.png) |
| MLG0007 | 1 | 369 | `(3659, 205, 3717, 272)` | 58×67 | 4 | 58 | 62 | `c092058f6dd1f08d7f47dd30fdaa28bde82c0cb45432b8df5469a58f2015be15` | [small_jpn_mlg_common_glyphs/MLG0007/U56FD_国_x4.png](../small_jpn_mlg_common_glyphs/MLG0007/U56FD_国_x4.png) |
| MLG000E | 1 | 976 | `(3906, 1225, 3964, 1292)` | 58×67 | 4 | 58 | 62 | `c092058f6dd1f08d7f47dd30fdaa28bde82c0cb45432b8df5469a58f2015be15` | [small_jpn_mlg_common_glyphs/MLG000E/U56FD_国_x4.png](../small_jpn_mlg_common_glyphs/MLG000E/U56FD_国_x4.png) |

### `家 U+5BB6`

| font | mapping count | glyph index | rect | size | bearing_x | width | advance | bitmap SHA256 | PNG |
|---|---:|---:|---|---|---:|---:|---:|---|---|
| JPN001C | 1 | 211 | `(1818, 403, 1884, 469)` | 66×66 | 2 | 66 | 68 | `f757d404a51f96b37606e8fdf65b1f6769708dfc6ef99a31bdf77d56f5c3844b` | [small_jpn_mlg_common_glyphs/JPN001C/U5BB6_家_x4.png](../small_jpn_mlg_common_glyphs/JPN001C/U5BB6_家_x4.png) |
| MLG0007 | 1 | 1279 | `(3213, 1225, 3271, 1292)` | 58×67 | 4 | 58 | 62 | `47dc0e10b2ffcc5ea539ffc1b1f699c3e02ac85a4045e0b225d0e4b6ca3bd4c9` | [small_jpn_mlg_common_glyphs/MLG0007/U5BB6_家_x4.png](../small_jpn_mlg_common_glyphs/MLG0007/U5BB6_家_x4.png) |
| MLG000E | 1 | 1136 | `(1701, 1429, 1759, 1496)` | 58×67 | 4 | 58 | 62 | `47dc0e10b2ffcc5ea539ffc1b1f699c3e02ac85a4045e0b225d0e4b6ca3bd4c9` | [small_jpn_mlg_common_glyphs/MLG000E/U5BB6_家_x4.png](../small_jpn_mlg_common_glyphs/MLG000E/U5BB6_家_x4.png) |

### `大 U+5927`

| font | mapping count | glyph index | rect | size | bearing_x | width | advance | bitmap SHA256 | PNG |
|---|---:|---:|---|---|---:|---:|---:|---|---|
| JPN001C | 1 | 201 | `(1120, 403, 1186, 469)` | 66×66 | 3 | 66 | 69 | `ce3ce4e476a1f5e54ded045b6e8cd0db4ce92de176b875b4181d6d7a7bd0ae20` | [small_jpn_mlg_common_glyphs/JPN001C/U5927_大_x4.png](../small_jpn_mlg_common_glyphs/JPN001C/U5927_大_x4.png) |
| MLG0007 | 1 | 381 | `(383, 273, 441, 340)` | 58×67 | 4 | 58 | 62 | `6bcb187c4e95aadd81412d132099ccc618255810e325c047b9a01fdf76ec81d0` | [small_jpn_mlg_common_glyphs/MLG0007/U5927_大_x4.png](../small_jpn_mlg_common_glyphs/MLG0007/U5927_大_x4.png) |
| MLG000E | 1 | 333 | `(1454, 409, 1512, 476)` | 58×67 | 4 | 58 | 62 | `6bcb187c4e95aadd81412d132099ccc618255810e325c047b9a01fdf76ec81d0` | [small_jpn_mlg_common_glyphs/MLG000E/U5927_大_x4.png](../small_jpn_mlg_common_glyphs/MLG000E/U5927_大_x4.png) |

## `我 U+6211` mapping count

- `MLG0007`：U+6211 在 dense charmap 中有 **1 个有效 codepoint mapping**，指向 glyph index 1531。
- `MLG000E`：U+6211 在 dense charmap 中有 **1 个有效 codepoint mapping**，指向 glyph index 1413。
- `JPN001C`：U+6211 有 **1 个有效 codepoint mapping**，指向 glyph index 239。
- 本报告同时检查了 glyph index 的反向引用计数；未把同一 glyph 被其它 codepoint 引用误算为 U+6211 的多个 mapping。

## MLG0007 vs MLG000E

| char | bitmap identical | record identical | dimensions same |
|---|---|---|---|
| 我 | True | False | True |
| 中 | True | False | True |
| 国 | True | False | True |
| 家 | True | False | True |
| 大 | True | False | True |

如果 `bitmap identical=True`，表示抽取出的 bitmap byte-for-byte 相同；即使 atlas 坐标和 GlyphRecord 中的 UV 不同，也属于同一像素内容。

## 与 JPN001C 的接近度

比较规则：尺寸距离为 rect width/height 的 L1 差；metrics 距离为 `bearing_x + width + advance` 的绝对差之和；bitmap style 使用两者分别 resize 到 66×66 后的灰度 MAE，仅作静态相似度指标。

| char | MLG0007 dim/metrics/MAE | MLG000E dim/metrics/MAE | 静态更接近 |
|---|---|---|---|
| 我 | `9/15/46.9741` | `9/15/46.9741` | TIE |
| 中 | `9/20/30.4497` | `9/20/30.4497` | TIE |
| 国 | `9/16/69.2658` | `9/16/69.2658` | TIE |
| 家 | `9/16/61.8985` | `9/16/61.8985` | TIE |
| 大 | `9/16/37.8180` | `9/16/37.8180` | TIE |

五个共同字的 MLG-0007 / MLG-000E 抽取 bitmap 全部完全相同；因此 bitmap 风格不存在 0007 vs 000e 的差异。

由于两套 MLG 的共同字 bitmap 若完全相同，且它们的 rect/cell 与 JPN001C 尺寸不同，则对 JPN001C 的接近度主要由 cell 尺寸和 metrics 决定，而不是 donor 像素内容决定。

## 当前 Loading 24 个缺字在 MLG_CN 中的覆盖

| char | codepoint | JPN001C | MLG0007 | MLG000E |
|---|---|---|---|---|
| 们 | U+4EEC | NO | YES (glyph 729) | YES (glyph 552) |
| 只 | U+53EA | NO | YES (glyph 985) | YES (glyph 820) |
| 会 | U+4F1A | NO | YES (glyph 745) | YES (glyph 301) |
| 战 | U+6218 | NO | YES (glyph 1534) | YES (glyph 1416) |
| 斗 | U+6597 | NO | YES (glyph 1725) | YES (glyph 1617) |
| 但 | U+4F46 | NO | YES (glyph 758) | YES (glyph 579) |
| 活 | U+6D3B | NO | YES (glyph 1978) | YES (glyph 1887) |
| 得 | U+5F97 | NO | YES (glyph 425) | YES (glyph 1307) |
| 不 | U+4E0D | NO | YES (glyph 307) | YES (glyph 293) |
| 受 | U+53D7 | NO | YES (glyph 356) | YES (glyph 811) |
| 局 | U+5C40 | NO | YES (glyph 1315) | YES (glyph 1177) |
| 势 | U+52BF | NO | YES (glyph 910) | YES (glyph 742) |
| 摆 | U+6446 | NO | YES (glyph 1677) | YES (glyph 1565) |
| 布 | U+5E03 | NO | YES (glyph 1358) | YES (glyph 1225) |
| 洲 | U+6D32 | NO | YES (glyph 1977) | YES (glyph 1886) |
| 是 | U+662F | NO | YES (glyph 1758) | YES (glyph 1652) |
| 连 | U+8FDE | NO | YES (glyph 2903) | YES (glyph 2836) |
| 接 | U+63A5 | NO | YES (glyph 449) | YES (glyph 1537) |
| 陆 | U+9646 | NO | YES (glyph 3046) | YES (glyph 2980) |
| 的 | U+7684 | NO | YES (glyph 528) | YES (glyph 390) |
| 脐 | U+8110 | NO | YES (glyph 2527) | YES (glyph 2455) |
| 带 | U+5E26 | NO | YES (glyph 1366) | YES (glyph 1233) |
| 这 | U+8FD9 | NO | YES (glyph 2899) | YES (glyph 2832) |
| 里 | U+91CC | NO | YES (glyph 2966) | YES (glyph 2901) |

覆盖结论：MLG-0007 `24/24`，MLG-000E `24/24`；两套 MLG 对当前 Loading 24 个缺字均有有效 mapping。

## 结论

1. `我 U+6211` 在 MLG-0007 和 MLG-000E 中各只有一个有效 codepoint mapping，分别指向不同 glyph index。
2. MLG-0007/000E 的共同字 rect 通常为 58×67，而 JPN001C 的中文 cell 为 66×66；尺寸并不相同。
3. 五个共同字的 MLG-0007/000E bitmap 是否相同已逐字验证，结果见表；本次输出会明确给出 byte-level SHA256。
4. 两套 MLG 均覆盖当前 Loading 的全部 24 个缺字，但这只是 coverage/bitmap 静态事实，不改变当前单文件 001c Loading PoC 结论。
5. 本轮没有提出 runtime remap、没有构建 XPR、没有修改 XPR。
