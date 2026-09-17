# FONT single-glyph runtime PoC

本目录是隔离测试输出。Golden FONT 未覆盖，未修改 translation、mapping 源文件或游戏安装目录；本轮只加入 `厥 U+53A5`，没有批量生成 glyph，也没有 full font rebuild。

## 结果摘要

两个变体都已完成“加密输出 → 按目标文件名 seed 解密 → XPR2 解析 → 结构校验”：

| 变体 | 输出 | 目标 seed | 结果 |
|---|---|---:|---|
| POC-A | `POC_A_00C7/00c7c9f9.xpr` | `0x3AF33BE1` | `STATIC_VALIDATION_PASS` |
| POC-B | `POC_B_0007/0007ccd8.xpr` | `0x03201D67` | `STATIC_VALIDATION_PASS` |

两份输出的 decrypted/plain SHA256 都是：

`3fb40b29e21304a66695998573f60bf1afd764b5e433b0a6bab40aa68bf9cb2a`

两份输出的 encrypted SHA256 不同：

- POC-A：`f75498d77cae8dd5d669683bb48bd72a242b310180bb26dada9c755271775075`
- POC-B：`c41a8b2e66f0801ddc3ce452cea100dbb23fc02bbe18cdf60c7b49e60a1764ab`

因此没有把相同 plaintext 直接复制成两个 encrypted XPR；每个输出都使用了自己的 filename seed。

## 输入与变更

输入 Golden：

`font/MLG_CN/0007ccd8.xpr`

输入 encrypted SHA256：

`149668d9facf5491b0a8a2b93b87ef3ff3e290ac139e1404aad30aac25d8c73c`

输入 decrypted SHA256：

`90ba15daced7bf7cb2b2d24731d0c99c049716f2101262510b2ae554d27157ff`

只做以下内部变更：

| 项目 | 原值 | 新值 |
|---|---:|---:|
| Unicode | 未映射 `U+53A5` | `U+53A5 → glyph 3209` |
| glyph count | 3209 | 3210 |
| USER/FontData size | `0x2C768` | `0x2C778` |
| 新 GlyphRecord | — | `u0=0,v0=3333,u1=58,v1=3400,bearing_x=4,width=58,advance=62,reserved=0` |
| atlas dimensions | `4096×4096` | 不变 |
| texture offset | `0x2C87C` | 不变 |
| XPR data_size | `0x1000000` | 不变 |

`record 0` 未复用。它仍保持原始未映射、带实际像素的 fallback/missing-glyph 候选。

## 厥 bitmap

复现脚本：[`tools/Build-SingleGlyphPoc.py`](../tools/Build-SingleGlyphPoc.py)

Raster 来源与参数：

- 文件：`C:\Windows\Fonts\Noto Sans SC (TrueType).otf`
- Regular face，FreeType/Pillow face index `0`
- 字号：`58 px`
- Pillow `ImageDraw`，`L` 模式，fill `255`
- anchor：`ls`（left-baseline）
- baseline：cell 内 `y=53`
- stroke width：`0`
- cell：`58×67`
- 生成 bbox：`[2, 7, 56, 59)`
- 非零像素：`1423`
- bitmap SHA256：`f7399f7c0e03d27f130b00ad0e60e4db86f1d80644206d77a557e7df91a38a4f`

该 bbox 与当前 MLG-0007 参考 CJK glyph 的实测 ink 范围保持同一量级；它是 runtime PoC bitmap，不宣称为最终美术字形。

## 静态回读校验

POC-A 和 POC-B 的 `poc_validation.json` 均记录了完整结果，关键断言全部通过：

- `U+53A5 → 3209`：通过。
- glyph `#3209` 记录完全匹配目标 16-byte record：通过。
- `atlas [0,3333)-[58,3400)` 存在非零像素：通过。
- 原有 3209 条 GlyphRecord byte-identical：通过。
- 除目标 entry 外，原 charmap bytes byte-identical：通过。
- 目标槽位之外，原 atlas pixels byte-identical：通过。
- TX2D descriptor/header、offset、size、dimensions：不变。
- XPR `data_size`：不变。
- parser errors：`0`。
- `validate_glyph_rectangles`：无错误。

输出目录：

- [`POC_A_00C7/00c7c9f9.xpr`](POC_A_00C7/00c7c9f9.xpr)
- [`POC_B_0007/0007ccd8.xpr`](POC_B_0007/0007ccd8.xpr)
- [`POC_A_00C7/poc_validation.json`](POC_A_00C7/poc_validation.json)
- [`POC_B_0007/poc_validation.json`](POC_B_0007/poc_validation.json)
- [`poc_results.json`](poc_results.json)

## 手动 runtime 测试

1. 备份当前实际安装目录中的 Golden FONT；测试前确认游戏未运行。
2. 仅将 `font/font_poc/POC_A_00C7/00c7c9f9.xpr` 覆盖到游戏实际使用的对应 FONT 目录。
3. 启动游戏，进入会显示“昏厥”的界面，检查 `厥` 是否正常显示。
4. 退出游戏，恢复 Golden `00c7c9f9.xpr`，确认恢复完成。
5. 仅将 `font/font_poc/POC_B_0007/0007ccd8.xpr` 覆盖到对应 FONT 目录。
6. 再进入同一界面测试“昏厥”。
7. 测试结束后再次恢复 Golden，不要把 `font/font_poc` 文件留作正式安装文件。

判定：POC-A 成功而 POC-B 失败，表示该界面实际依赖 `00c7c9f9`；反之表示依赖 `0007ccd8`。若两者都成功，则该界面可能同时加载两套字体或走共享/回退路径；若两者都失败，则说明 runtime 还存在本静态审计无法覆盖的约束（例如外层文件选择、缓存、版本校验或 append 格式限制）。

本报告只证明静态 PoC 输出结构正确；尚未宣称游戏 runtime 已接受，最终结论必须来自上述手动测试。
