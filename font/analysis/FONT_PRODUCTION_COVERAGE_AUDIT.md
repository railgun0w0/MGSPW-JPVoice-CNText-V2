# FONT production coverage audit

本报告是只读审计；本轮未修改 FONT/XPR、翻译源、构建产物，也未生成 glyph 或执行 build。

## 结论摘要

Production unique display chars: 2902
Covered by MLG_CN-0007: 2681
Missing from MLG_CN-0007: 221
Recoverable from JPN-00C7: 62
Recoverable only from other official JPN fonts: 0
Missing from all six fonts: 151

分类计数：CN_ALREADY_COVERED=2689；JPN_RECOVERABLE=62；TRUE_NEW_GLYPH=151。
独立诊断子集（MLG_CN-0007=NO 且 JPN-00C7=YES，不论 MLG_CN-000E）：68。其中严格属于 JPN_RECOVERABLE 的数量为 62。

### 指定字符复查

| 字符 | 码点 | 次数 | 分类 | MLG_CN-0007 | MLG_CN-000E | MLG-0007-base | MLG-000E-base | JPN-001C | JPN-00C7 |
|---|---:|---:|---|---|---|---|---|---|---|
| 拘 | U+62D8 | 61 | JPN_RECOVERABLE | NO | NO | NO | NO | NO | YES |
| 曝 | U+66DD | 2 | JPN_RECOVERABLE | NO | NO | NO | NO | NO | YES |
| 厥 | U+53A5 | 37 | TRUE_NEW_GLYPH | NO | NO | NO | NO | NO | NO |
| 磋 | U+78CB | 10 | TRUE_NEW_GLYPH | NO | NO | NO | NO | NO | NO |

## TRUE_NEW_GLYPH（按 production 出现次数降序）

- 噫 U+566B — 76 次；SLOT_OLANG
- 诊 U+8BCA — 51 次；BRIEFING | SLOT_OLANG | STAGEDAT_OLANG
- 厥 U+53A5 — 37 次；SLOT_OLANG | STAGEDAT_OLANG
- 贤 U+8D24 — 25 次；BRIEFING | SLOT_OLANG | YPK_GTT
- 蚣 U+86A3 — 18 次；STAGEDAT_OLANG
- 蜈 U+8708 — 18 次；STAGEDAT_OLANG
- 赠 U+8D60 — 13 次；LOOSE_OLANG | SLOT_OLANG | STAGEDAT_OLANG
- 徊 U+5F8A — 12 次；BRIEFING | STAGEDAT_OLANG | YPK_GTT
- 徘 U+5F98 — 12 次；BRIEFING | STAGEDAT_OLANG | YPK_GTT
- 磋 U+78CB — 10 次；SLOT_OLANG | STAGEDAT_OLANG
- 窥 U+7AA5 — 8 次；BRIEFING | SLOT_OLANG | YPK_GTT
- 殃 U+6B83 — 7 次；SLOT_OLANG | STAGEDAT_OLANG
- 涨 U+6DA8 — 7 次；BRIEFING | SLOT_OLANG | STAGEDAT_OLANG
- 咧 U+54A7 — 6 次；LOOSE_OLANG
- 咫 U+54AB — 6 次；BRIEFING | SLOT_OLANG | STAGEDAT_OLANG
- 嘶 U+5636 — 6 次；SLOT_OLANG | YPK_GTT
- 鸭 U+9E2D — 6 次；SLOT_OLANG | STAGEDAT_OLANG
- 卜 U+535C — 5 次；SLOT_OLANG | STAGEDAT_OLANG
- 呕 U+5455 — 5 次；SLOT_OLANG | STAGEDAT_OLANG
- 嘱 U+5631 — 5 次；SLOT_OLANG | STAGEDAT_OLANG
- 嵌 U+5D4C — 5 次；SLOT_OLANG
- 憬 U+61AC — 5 次；BRIEFING
- 犷 U+72B7 — 5 次；BRIEFING | STAGEDAT_OLANG
- 蛤 U+86E4 — 5 次；BRIEFING | YPK_GTT
- 蟆 U+87C6 — 5 次；BRIEFING | YPK_GTT
- 递 U+9012 — 5 次；BRIEFING | LOOSE_OLANG | SLOT_OLANG | STAGEDAT_OLANG
- 酣 U+9163 — 5 次；SLOT_OLANG
- 吩 U+5429 — 4 次；SLOT_OLANG
- 咐 U+5490 — 4 次；SLOT_OLANG
- 寞 U+5BDE — 4 次；BRIEFING | YPK_GTT
- 捺 U+637A — 4 次；SLOT_OLANG
- 溪 U+6EAA — 4 次；BRIEFING | YPK_GTT
- 绷 U+7EF7 — 4 次；SLOT_OLANG
- 罕 U+7F55 — 4 次；BRIEFING | LOOSE_OLANG
- 峻 U+5CFB — 3 次；BRIEFING
- 翱 U+7FF1 — 3 次；SLOT_OLANG
- 舆 U+8206 — 3 次；SLOT_OLANG
- 购 U+8D2D — 3 次；BRIEFING | SLOT_OLANG
- 郑 U+90D1 — 3 次；BRIEFING
- 醇 U+9187 — 3 次；SLOT_OLANG
- 韧 U+97E7 — 3 次；BRIEFING | LOOSE_OLANG | SLOT_OLANG
- 鼎 U+9F0E — 3 次；BRIEFING | SLOT_OLANG
- 厮 U+53AE — 2 次；BRIEFING | YPK_GTT
- 哔 U+54D4 — 2 次；YPK_GTT
- 嚷 U+56B7 — 2 次；BRIEFING
- 孙 U+5B59 — 2 次；BRIEFING
- 宴 U+5BB4 — 2 次；STAGEDAT_OLANG
- 斩 U+65A9 — 2 次；STAGEDAT_OLANG
- 晋 U+664B — 2 次；BRIEFING | SLOT_OLANG
- 李 U+674E — 2 次；YPK_GTT
- 棵 U+68F5 — 2 次；BRIEFING
- 浏 U+6D4F — 2 次；STAGEDAT_OLANG
- 滥 U+6EE5 — 2 次；BRIEFING
- 漩 U+6F29 — 2 次；BRIEFING
- 焚 U+711A — 2 次；BRIEFING
- 痹 U+75F9 — 2 次；LOOSE_OLANG | SLOT_OLANG
- 眯 U+772F — 2 次；BRIEFING
- 羡 U+7FA1 — 2 次；BRIEFING | YPK_GTT
- 蕴 U+8574 — 2 次；SLOT_OLANG
- 谴 U+8C34 — 2 次；BRIEFING
- 蹑 U+8E51 — 2 次；BRIEFING
- 迢 U+8FE2 — 2 次；BRIEFING
- 钉 U+9489 — 2 次；BRIEFING
- 驰 U+9A70 — 2 次；BRIEFING | YPK_GTT
- 骋 U+9A8B — 2 次；BRIEFING | YPK_GTT
- Č U+010C — 1 次；BRIEFING
- 侃 U+4F83 — 1 次；SLOT_OLANG
- 侣 U+4FA3 — 1 次；YPK_GTT
- 倚 U+501A — 1 次；BRIEFING
- 冕 U+5195 — 1 次；BRIEFING
- 匀 U+5300 — 1 次；YPK_GTT
- 吝 U+541D — 1 次；SLOT_OLANG
- 咨 U+54A8 — 1 次；STAGEDAT_OLANG
- 咻 U+54BB — 1 次；YPK_GTT
- 啪 U+556A — 1 次；STAGEDAT_OLANG
- 嘎 U+560E — 1 次；YPK_GTT
- 噼 U+567C — 1 次；STAGEDAT_OLANG
- 垦 U+57A6 — 1 次；BRIEFING
- 奠 U+5960 — 1 次；BRIEFING
- 娴 U+5A34 — 1 次；BRIEFING
- 婴 U+5A74 — 1 次；LOOSE_OLANG
- 媲 U+5AB2 — 1 次；SLOT_OLANG
- 宰 U+5BB0 — 1 次；SLOT_OLANG
- 屹 U+5C79 — 1 次；BRIEFING
- 岂 U+5C82 — 1 次；BRIEFING
- 怔 U+6014 — 1 次；BRIEFING
- 恬 U+606C — 1 次；BRIEFING
- 惘 U+60D8 — 1 次；STAGEDAT_OLANG
- 惬 U+60EC — 1 次；BRIEFING
- 扒 U+6252 — 1 次；YPK_GTT
- 扼 U+627C — 1 次；BRIEFING
- 挞 U+631E — 1 次；BRIEFING
- 掂 U+6382 — 1 次；STAGEDAT_OLANG
- 揽 U+63FD — 1 次；BRIEFING
- 搂 U+6402 — 1 次；BRIEFING
- 擞 U+64DE — 1 次；STAGEDAT_OLANG
- 斧 U+65A7 — 1 次；BRIEFING
- 旷 U+65F7 — 1 次；BRIEFING
- 春 U+6625 — 1 次；BRIEFING
- 晦 U+6666 — 1 次；BRIEFING
- 棱 U+68F1 — 1 次；STAGEDAT_OLANG
- 槛 U+69DB — 1 次；BRIEFING
- 檐 U+6A90 — 1 次；YPK_GTT
- 沫 U+6CAB — 1 次；BRIEFING
- 沮 U+6CAE — 1 次；BRIEFING
- 泞 U+6CDE — 1 次；BRIEFING
- 涵 U+6DB5 — 1 次；LOOSE_OLANG
- 滔 U+6ED4 — 1 次；BRIEFING
- 滴 U+6EF4 — 1 次；BRIEFING
- 炉 U+7089 — 1 次；LOOSE_OLANG
- 煞 U+715E — 1 次；BRIEFING
- 牟 U+725F — 1 次；BRIEFING
- 玄 U+7384 — 1 次；BRIEFING
- 琐 U+7410 — 1 次；BRIEFING
- 畴 U+7574 — 1 次；BRIEFING
- 睿 U+777F — 1 次；BRIEFING
- 瞪 U+77AA — 1 次；BRIEFING
- 磐 U+78D0 — 1 次；BRIEFING
- 禅 U+7985 — 1 次；BRIEFING
- 籽 U+7C7D — 1 次；BRIEFING
- 糙 U+7CD9 — 1 次；BRIEFING
- 缀 U+7F00 — 1 次；BRIEFING
- 缨 U+7F28 — 1 次；BRIEFING
- 耽 U+803D — 1 次；BRIEFING
- 肖 U+8096 — 1 次；BRIEFING
- 胧 U+80E7 — 1 次；BRIEFING
- 舔 U+8214 — 1 次；BRIEFING
- 萍 U+840D — 1 次；SLOT_OLANG
- 萦 U+8426 — 1 次；BRIEFING
- 蚓 U+8693 — 1 次；YPK_GTT
- 蚯 U+86AF — 1 次；YPK_GTT
- 袒 U+8892 — 1 次；BRIEFING
- 诠 U+8BE0 — 1 次；SLOT_OLANG
- 询 U+8BE2 — 1 次；STAGEDAT_OLANG
- 诩 U+8BE9 — 1 次；BRIEFING
- 谣 U+8C23 — 1 次；BRIEFING
- 赝 U+8D5D — 1 次；BRIEFING
- 踞 U+8E1E — 1 次；BRIEFING
- 轿 U+8F7F — 1 次；BRIEFING
- 辖 U+8F96 — 1 次；SLOT_OLANG
- 迄 U+8FC4 — 1 次；BRIEFING
- 锚 U+951A — 1 次；YPK_GTT
- 锤 U+9524 — 1 次；BRIEFING
- 锵 U+9535 — 1 次；BRIEFING
- 霸 U+9738 — 1 次；BRIEFING
- 靡 U+9761 — 1 次；SLOT_OLANG
- 颖 U+9896 — 1 次；SLOT_OLANG
- 颠 U+98A0 — 1 次；BRIEFING
- 飓 U+98D3 — 1 次；SLOT_OLANG
- 馈 U+9988 — 1 次；BRIEFING
- 鼾 U+9F3E — 1 次；SLOT_OLANG

## 统计口径与生产来源

- 旧五类最终对象记录：`build/translation/compiled_translation_manifest.csv`，共 91609 行；按 `resource_class` 分布：LOOSE_OLANG=2956, OHD=904, SLOT_OLANG=68482, STAGEDAT_OLANG=16863, YPK_GTT=2136。
- BRIEFING 正式输入：`translations/briefing/*.csv`，469 个文件、5645 行。
- 纳入分析的非空 production 文本记录：96986；`production_occurrences` 是清除控制语法后的实际显示 codepoint 出现次数，不是唯一行数。
- 未扫描 `ENG`、`MLG_CN` reference、`work/luna_translation_templates`、旧模板、backup/archive、README、测试输出或 readiness/package 输出；JPN_CN 也不作为独立字体集合。
- `<R=base,reading>` 的 base 与 reading 均计入，因为二者都是实际可显示文字；`<I=...>`、`<C=...>`、`<->`、美元/printf placeholder、换行、空白和 Unicode control/format 字符不计入。

## 六套 unique font content

| unique font | mapped count | atlas | cell | type | charmap SHA256 |
|---|---:|---|---:|---|---|
| MLG-0007-base | 642 | 4096x4096 | 67 | official MLG / large comparison source | `04ad5096500c7acd28ab8c511c61deed177cd5f2a62f14ccecf7bc86fd60e81a` |
| MLG-000E-base | 458 | 2048x1024 | 67 | official MLG / small comparison source | `699ad440d9a6841f88f65f2fa8c1b34803927decdef8f53e0d4f1b8d9dd8822a` |
| JPN-001C | 358 | 2048x1024 | 66 | clean JPN / small selector | `061ea5e7a15393a29c502a5c249e4bafe18fa94d8e4a36fe174bdad9c02acb47` |
| JPN-00C7 | 2308 | 4096x4096 | 66 | clean JPN / large selector | `16e44cfae602fa9ae8a57ab069c50d57ac1edc33d1520e8b96a143a9b2c0137d` |
| MLG_CN-0007 | 3208 | 4096x4096 | 67 | MLG Chinese extension / large | `6421c796e2befe2a489fc791fc8ad0678f0edeb3d9cd8dde3a2a6fb04515d594` |
| MLG_CN-000E | 3145 | 4096x4096 | 67 | MLG Chinese extension / small-source content | `97a9801d5167c9c0f25706aa51c7c19487e45b68bb5460ab36e5b35c86162db7` |

## 分类定义

- `CN_ALREADY_COVERED`：MLG_CN-0007 或 MLG_CN-000E 至少一个存在。
- `JPN_RECOVERABLE`：两套 MLG_CN 都不存在，但至少一套 official JPN (`001c/00c7`) 存在。
- `TRUE_NEW_GLYPH`：六套 font charmap 全部不存在。
- `production_recoverable_from_jpn00c7.csv` 只列严格 `JPN_RECOVERABLE` 且 JPN-00C7=YES 的字符；报告另列的 operational 子集还包括 MLG_CN-000E 已覆盖、但 MLG_CN-0007 缺失的字符。

## 输出文件

- `production_character_inventory.csv`：production 唯一显示字符、次数、来源、样例和六套覆盖状态。
- `production_font_coverage_matrix.csv`：精简覆盖矩阵。
- `production_recoverable_from_jpn00c7.csv`：可从 clean JPN-00C7 回收且两套 MLG_CN 均缺失的字符。
- `production_true_new_glyphs.csv`：六套字体均缺失的真正新 glyph 字符。
