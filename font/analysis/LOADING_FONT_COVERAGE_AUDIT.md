# LOADING_FONT_COVERAGE_AUDIT

## Current scope and runtime status

本文件当前只覆盖已测试的 Loading / 载入动画角色语录，不扩展到菜单、HUD、无线电、任务界面或其它 SMALL_JPN 使用场景。

```ini
LOADING_REQUIRED_GLYPHS = 35
LOADING_EXISTING_GLYPHS = 11
LOADING_MISSING_GLYPHS = 24
LOADING_RUNTIME_FONTDATA = JPN/001cbbd1.xpr
LOADING_RUNTIME_ATLAS = JPN/001cbbd1.xpr own TX2D
TEST_A_001C_OWN_TX2D_RUNTIME = PASS
MEN_U+4EEC_TECHNICAL_POC = RUNTIME_SUCCESS
MEN_U+4EEC_FINAL_STYLE = PENDING
```

TEST A 只修改 `001cbbd1.xpr` 自带 TX2D 中 `我 U+6211`、glyph index 239 的像素；实机 Loading 页面中的“我”发生变化。因此当前补字研究收敛到单文件 `JPN/001cbbd1.xpr`。这不表示 `00c7c9f9.xpr` 不会参与其它渲染路径，只表示它不是当前 Loading 补字 PoC 的已确认目标。

## Source confirmation

- Actual production file: `D:\GAME\test\steam 合金装备大师合集2 合金装备和平行者汉化补丁\JPVoice_CNText_V2\translations\loose_olang\00D0C740.csv`
- unique_index 37 (Miller): `我们只会战斗……\n但我们要活得不受国家局势摆布。`
- unique_index 39 (Galvez): `中美洲是连接北美大陆和南美大陆的脐带。\n我们想要这里。`
- The English names are excluded; only CJK ideographs in the quote bodies are audited.

## Evidence boundary

仓库没有保存本次实机截图的逐字 OCR/像素标注。下面的 35 字集合以当前两段实际 Loading 文本、既有 coverage audit 和本轮实机 PoC 为范围依据；`screenshot` 列表示已确认的 Loading 显示/点号分类，不扩展为全游戏缺字结论。

## Reconstructed character sets

- LOADING_EXISTING_GLYPHS (11 unique): `我 要 国 家 中 美 北 大 和 南 想`
- LOADING_MISSING_GLYPHS (24 unique): `们 只 会 战 斗 但 活 得 不 受 局 势 摆 布 洲 是 连 接 陆 的 脐 带 这 里`
- Miller explicit SMALL_JPN missing: `们 只 会 战 斗 但 活 得 不 受 局 势 摆 布`。
- Galvez explicit Loading probe: `陆 U+9646` missing from SMALL_JPN; the complete missing set for this document is exactly the 24 characters listed above.

## Font statistics

| font | visible_total | visible_present | visible_missing | dot_total | dot_present | dot_missing | match rate |
|---|---:|---:|---:|---:|---:|---:|---:|
| MLG0007-base | 11 | 5 | 6 | 24 | 5 | 19 | 68.57% |
| MLG000E-base | 11 | 2 | 9 | 24 | 3 | 21 | 65.71% |
| JPN001C | 11 | 11 | 0 | 24 | 0 | 24 | 100.0% |
| JPN00C7 | 11 | 11 | 0 | 24 | 10 | 14 | 71.43% |
| MLG_CN0007 | 11 | 11 | 0 | 24 | 24 | 0 | 31.43% |
| MLG_CN000E | 11 | 11 | 0 | 24 | 24 | 0 | 31.43% |

## Per-character matrix

`VISIBLE`/`MISSING_AS_DOT` is the Loading-only display classification; font cells are actual charmap presence, not a claim about other game scenes.

| char | codepoint | screenshot | MLG0007-base | MLG000E-base | JPN001C | JPN00C7 | MLG_CN0007 | MLG_CN000E |
|---|---|---|---|---|---|---|---|---|
| 我 | U+6211 | 37:VISIBLE;39:VISIBLE | NO | NO | YES | YES | YES | YES |
| 们 | U+4EEC | 37:MISSING_AS_DOT;39:MISSING_AS_DOT | NO | NO | NO | NO | YES | YES |
| 只 | U+53EA | 37:MISSING_AS_DOT | NO | NO | NO | NO | YES | YES |
| 会 | U+4F1A | 37:MISSING_AS_DOT | NO | YES | NO | YES | YES | YES |
| 战 | U+6218 | 37:MISSING_AS_DOT | NO | NO | NO | NO | YES | YES |
| 斗 | U+6597 | 37:MISSING_AS_DOT | NO | NO | NO | NO | YES | YES |
| 但 | U+4F46 | 37:MISSING_AS_DOT | NO | NO | NO | NO | YES | YES |
| 要 | U+8981 | 37:VISIBLE;39:VISIBLE | YES | YES | YES | YES | YES | YES |
| 活 | U+6D3B | 37:MISSING_AS_DOT | NO | NO | NO | YES | YES | YES |
| 得 | U+5F97 | 37:MISSING_AS_DOT | YES | NO | NO | YES | YES | YES |
| 不 | U+4E0D | 37:MISSING_AS_DOT | YES | YES | NO | YES | YES | YES |
| 受 | U+53D7 | 37:MISSING_AS_DOT | YES | NO | NO | YES | YES | YES |
| 国 | U+56FD | 37:VISIBLE | YES | NO | YES | YES | YES | YES |
| 家 | U+5BB6 | 37:VISIBLE | NO | NO | YES | YES | YES | YES |
| 局 | U+5C40 | 37:MISSING_AS_DOT | NO | NO | NO | YES | YES | YES |
| 势 | U+52BF | 37:MISSING_AS_DOT | NO | NO | NO | NO | YES | YES |
| 摆 | U+6446 | 37:MISSING_AS_DOT | NO | NO | NO | NO | YES | YES |
| 布 | U+5E03 | 37:MISSING_AS_DOT | NO | NO | NO | YES | YES | YES |
| 中 | U+4E2D | 39:VISIBLE | YES | NO | YES | YES | YES | YES |
| 美 | U+7F8E | 39:VISIBLE | NO | NO | YES | YES | YES | YES |
| 洲 | U+6D32 | 39:MISSING_AS_DOT | NO | NO | NO | NO | YES | YES |
| 是 | U+662F | 39:MISSING_AS_DOT | NO | NO | NO | YES | YES | YES |
| 连 | U+8FDE | 39:MISSING_AS_DOT | NO | NO | NO | NO | YES | YES |
| 接 | U+63A5 | 39:MISSING_AS_DOT | YES | NO | NO | YES | YES | YES |
| 北 | U+5317 | 39:VISIBLE | NO | NO | YES | YES | YES | YES |
| 大 | U+5927 | 39:VISIBLE | YES | YES | YES | YES | YES | YES |
| 陆 | U+9646 | 39:MISSING_AS_DOT | NO | NO | NO | NO | YES | YES |
| 和 | U+548C | 39:VISIBLE | NO | NO | YES | YES | YES | YES |
| 南 | U+5357 | 39:VISIBLE | YES | NO | YES | YES | YES | YES |
| 的 | U+7684 | 39:MISSING_AS_DOT | YES | YES | NO | YES | YES | YES |
| 脐 | U+8110 | 39:MISSING_AS_DOT | NO | NO | NO | NO | YES | YES |
| 带 | U+5E26 | 39:MISSING_AS_DOT | NO | NO | NO | NO | YES | YES |
| 想 | U+60F3 | 39:VISIBLE | NO | NO | YES | YES | YES | YES |
| 这 | U+8FD9 | 39:MISSING_AS_DOT | NO | NO | NO | NO | YES | YES |
| 里 | U+91CC | 39:MISSING_AS_DOT | NO | NO | NO | NO | YES | YES |

## Font identities and deduplication

- 下表中的其它字体只保留为本 Loading 35 字 coverage 的历史对照，不代表本轮要修改、替换或继续研究这些资源。
- `JPN_CN` is not recomputed: its 0007/000e/00c7 logical contents are known copies/rekeys used only for provenance.
- JPN001C/JPN00C7 are the only official JPN FONT files. MLG0007/000e are the official MLG comparison sources; MLG_CN0007/000e are the expanded Chinese patch contents.

| label | records | mapped | atlas | path |
|---|---:|---:|---|---|
| MLG0007-base | 643 | 642 | `4096x4096` | `D:\GAME\test\steam 合金装备大师合集2 合金装备和平行者汉化补丁\JPVoice_CNText_V2\font\MLG\0007ccd8.xpr` |
| MLG000E-base | 459 | 458 | `2048x1024` | `D:\GAME\test\steam 合金装备大师合集2 合金装备和平行者汉化补丁\JPVoice_CNText_V2\font\MLG\000ebbe8.xpr` |
| JPN001C | 359 | 358 | `2048x1024` | `D:\GAME\test\steam 合金装备大师合集2 合金装备和平行者汉化补丁\JPVoice_CNText_V2\font\JPN\001cbbd1.xpr` |
| JPN00C7 | 2309 | 2308 | `4096x4096` | `D:\GAME\test\steam 合金装备大师合集2 合金装备和平行者汉化补丁\JPVoice_CNText_V2\font\JPN\00c7c9f9.xpr` |
| MLG_CN0007 | 3209 | 3208 | `4096x4096` | `D:\GAME\test\steam 合金装备大师合集2 合金装备和平行者汉化补丁\JPVoice_CNText_V2\font\MLG_CN\0007ccd8.xpr` |
| MLG_CN000E | 3146 | 3145 | `4096x4096` | `D:\GAME\test\steam 合金装备大师合集2 合金装备和平行者汉化补丁\JPVoice_CNText_V2\font\MLG_CN\000ebbe8.xpr` |

## Conclusion

BEST_MATCH_FONT = JPN001C
MATCH_CONFIDENCE = HIGH-CONFIDENCE

`JPN001C / SMALL_JPN` explains the Loading visible/missing combination: the 11 existing characters are mapped, while the 24 listed missing characters have charmap value 0 and fall through to record 0. The TEST A runtime mutation confirms that Loading uses the `001cbbd1.xpr` own TX2D. The previous `001c FontData + 00c7 FontTexture` wording is retired as a confirmed Loading pairing.

当前 production JPN patch 已覆盖 JPN large `00c7`，但默认没有生成对应的 patched JPN small `001c`。Loading 使用官方 JPN `001cbbd1.xpr`，因此会继续落回 clean SMALL_JPN，导致这 230 个中文 code point 缺失；MLG `000e` 与 JPN `001c` 是官方 small 配对，但不能把 MLG `000e` 的存在误写成已经提供了 patched JPN `001c`。

`们 U+4EEC` now has a successful technical one-glyph runtime PoC in the single-file `001c` path, but its visual style is not final. It therefore remains in `LOADING_MISSING_GLYPHS / FINAL_GLYPH_PENDING`; the 24-character count is intentionally unchanged.
