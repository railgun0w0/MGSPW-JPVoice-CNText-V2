# FONT ingame missing-glyph cases

只读考古报告。本文保留多个历史场景案例，但当前 Loading 工作范围只包括 CASE-008/009 的两段角色语录。其它案例不得混入本轮 Loading 的 24 个缺字集合。本阶段没有修改任何 FONT/XPR，没有重建 XPR，也没有生成测试包。

## Current Loading scope

```ini
LOADING_REQUIRED_GLYPHS = 35
LOADING_EXISTING_GLYPHS = 11
LOADING_MISSING_GLYPHS = 24
LOADING_FONTDATA = JPN/001cbbd1.xpr
LOADING_RUNTIME_ATLAS = JPN/001cbbd1.xpr own TX2D
TEST_A_001C_OWN_TX2D_RUNTIME = PASS
```

当前 Loading 缺字集合仅为：`们 只 会 战 斗 但 活 得 不 受 局 势 摆 布 洲 是 连 接 陆 的 脐 带 这 里`。CASE-001 至 CASE-007 的其它场景探针继续保留为历史记录，不计入这个集合。

## 结论摘要

| 案例 | 生产来源 | 可确认探针 | 结论 |
|---|---|---|---|
| CASE-001 | LOOSE_OLANG/007E2F18.csv:1039 | 拘 U+62D8 | STATIC_CONFIRMED |
| CASE-002 | SLOT_OLANG/5D3B3A9A.csv:10 | 拘 U+62D8 | STATIC_CONFIRMED |
| CASE-003 | LOOSE_OLANG/007E2F18.csv:1034 | 拘 U+62D8 | STATIC_CONFIRMED |
| CASE-004 | SLOT_OLANG/5D420130.csv:122 | 厥 U+53A5 | STATIC_CONFIRMED |
| CASE-005 | SLOT_OLANG/5DDB94DF.csv:2 | 磋 U+78CB | STATIC_CONFIRMED |
| CASE-006 | BRIEFING_MISSION_BLOCK_36D0B0.csv:7 | 曝 U+66DD | STATIC_CONFIRMED |
| CASE-007 | BRIEFING_FILES_BLOCK_000D00.csv:3 | 拘 U+62D8 | STATIC_CONFIRMED |
| CASE-008 | LOOSE_OLANG/00D0C740.csv:37 | Loading + TEST A | LOADING_RUNTIME_CONFIRMED |
| CASE-009 | LOOSE_OLANG/00D0C740.csv:39 | Loading + TEST A | LOADING_RUNTIME_CONFIRMED |
| CASE-010 | 当前生产元数据无法唯一绑定 | 未建立 | UNKNOWN |

## 三套 Golden / comparison FONT

这里的 `JPN_CN` 路径表示当前 patched output/provenance，不是官方 JPN depot；官方 JPN base 只有 `001cbbd1.xpr`（small）和 `00c7c9f9.xpr`（large）。

样本文件：

- font/JPN_CN/0007ccd8.xpr（BIG_CN）
- font/JPN_CN/000ebbe8.xpr（SMALL_CN）
- font/JPN/001cbbd1.xpr（SMALL_JPN）

| 字库 | atlas | glyph records | mapped codepoints | CJK |
|---|---:|---:|---:|---:|
| BIG_CN | 4096x4096 | 3209 | 3208 | 2880 |
| SMALL_CN | 4096x4096 | 3146 | 3145 | 2831 |
| SMALL_JPN | 2048x1024 | 359 | 358 | 217 |

关键 charmap 结果：

| 字符 | Unicode | BIG_CN | SMALL_CN | SMALL_JPN |
|---|---|---|---|---|
| 拘 | U+62D8 | NO | NO | NO |
| 厥 | U+53A5 | NO | NO | NO |
| 磋 | U+78CB | NO | NO | NO |
| 曝 | U+66DD | NO | NO | NO |
| 陆 | U+9646 | YES，glyph 3046 | YES，glyph 2980 | NO |

因此，CASE-001 至 CASE-007 的探针字符在三套当前 Golden charmap 中都不存在；这足以确认它们不是某一套字库之间的简单 route 差异，而是当前 FONT 对这些实际生产文本缺字。CASE-008/009 的中文字符在 CN 字库中存在，不能仅凭静态 charmap 把画面上的点号归因于 CN 字库缺字。

## 案例逐项证据

### CASE-001

来源：translations/loose_olang/007E2F18.csv，unique_index 1039。

生产文本：

    要把拘束中的对手投出去，\n拘束时输入<I=MOVE>。

探针为 拘 U+62D8。该字符在 BIG_CN、SMALL_CN、SMALL_JPN 均无映射，状态 STATIC_CONFIRMED。

### CASE-002

来源：translations/slot_olang/5D3B3A9A.csv，unique_index 10。

生产文本：CQC／拘束。

探针为 拘 U+62D8。三套 charmap 均无映射，状态 STATIC_CONFIRMED。

### CASE-003

来源：translations/loose_olang/007E2F18.csv，unique_index 1034。

生产文本：

    要拘束对手，\n在对手附近长按<I=CQC>。

探针为 拘 U+62D8。三套 charmap 均无映射，状态 STATIC_CONFIRMED。

### CASE-004

来源：translations/slot_olang/5D420130.csv，unique_index 122。

生产文本：被击中的对手会承受不住而昏厥。

探针为 厥 U+53A5。三套 charmap 均无映射，状态 STATIC_CONFIRMED。

### CASE-005

来源：translations/slot_olang/5DDB94DF.csv，unique_index 2。

生产文本：Boss，请和我切磋！

探针为 磋 U+78CB。三套 charmap 均无映射，状态 STATIC_CONFIRMED。

### CASE-006

来源：translations/briefing/BRIEFING_MISSION_BLOCK_36D0B0.csv，unique_index 7。

生产文本：

    条约全面禁止核武器的试验、使用、\n进口和部署等行为……一旦事情曝光，\n<R=拉丁美洲禁止核武器组织,OPANAL>就会介入。这会成为国际问题。

探针为 曝 U+66DD。三套 charmap 均无映射，状态 STATIC_CONFIRMED。

### CASE-007

来源：translations/briefing/BRIEFING_FILES_BLOCK_000D00.csv，unique_index 3。

生产文本：首先，给你打昏的敌人或被拘束的俘虏装上气球。

探针为 拘 U+62D8。三套 charmap 均无映射，状态 STATIC_CONFIRMED。

### CASE-008

画面标记：Kazuhira Miller loading screen。当前最可靠的生产来源是 translations/loose_olang/00D0C740.csv，unique_index 37。

生产文本：

    我们只会战斗……\n但我们要活得不受国家局势摆布。

该行的英文本义参考是：Exactly. We know only how to fight... but we refuse to live our lives at the whim of the state. BIG_CN 与 SMALL_CN 对这行中文字符均有映射；SMALL_JPN 缺少 们、只、会、战、斗、但、活、得、不、受、局、势、摆、布 等字符。

静态 coverage 已显示 SMALL_JPN 的 11/35 与 24/35 分界；TEST A 又实机确认 `001cbbd1.xpr` 自带 TX2D 会改变 Loading 页面中的 `我`。当前 Loading 补字目标因此收敛为单文件 `JPN/001cbbd1.xpr`。状态 `LOADING_RUNTIME_CONFIRMED`。

### CASE-009

画面标记：Ramon Galvez Mena loading screen。当前最可靠的生产来源是 translations/loose_olang/00D0C740.csv，unique_index 39。

生产文本：

    中美洲是连接北美大陆和南美大陆的脐带。\n我们想要这里。

探针为 陆 U+9646；该行出现两次（北美大陆、南美大陆）。TEST A 已确认 Loading 使用 `JPN/001cbbd1.xpr` 自带 TX2D；`陆 U+9646` 在该文件 charmap 中为 0，因此属于当前 Loading 24 个缺字集合。状态 `LOADING_RUNTIME_CONFIRMED`。

### CASE-010

画面标记：Snake loading screen，用户提供的可见片段为 我来……利言 一类的粗略 OCR/视觉记录。

当前 production translations、角色评论/简介以及 loading-screen 相关元数据中，尚未找到能把该截图唯一绑定到具体文件、unique_index 和完整 Unicode 字符串的证据。现阶段不猜测 source，也不把任何字符列为 confirmed missing glyph。状态 UNKNOWN。

## route probe：U+62D8 拘

拘 同时出现在 CASE-001、CASE-002、CASE-003、CASE-007 的生产中文文本中，并且三套 Golden charmap 都没有 U+62D8。若这些画面确实直接显示对应生产文本，则无论 BIG_CN、SMALL_CN 还是 SMALL_JPN，都无法从当前字库取得 拘 的 glyph；这四个案例的静态缺字结论不依赖具体 route。

## loading-screen 案例组

CASE-008 与 CASE-009 的可靠生产文本均来自 LOOSE_OLANG/00D0C740.csv。两行去重后共 35 个汉字，其中 11 个在 `001c` 中已有、24 个为 charmap value 0。TEST A 实机确认 `001c` 自带 TX2D 参与 Loading 渲染，因此这两项升级为 `LOADING_RUNTIME_CONFIRMED`。

`们 U+4EEC` 已有成功的技术 one-glyph PoC，但视觉风格未定，仍保留在 Loading 的 24 个 `FINAL_GLYPH_PENDING` 缺字中。

## 最终状态

- STATIC_CONFIRMED：CASE-001 至 CASE-007。
- LOADING_RUNTIME_CONFIRMED：CASE-008、CASE-009。
- X64_REQUIRED：当前没有案例达到该级别；只有在 route 已确认且 charmap 有映射、但实机仍然错误时才需要进入 x64 级别调查。
- UNKNOWN：CASE-010。

本报告中的历史案例仍以现有文件和静态解析为基础；当前 Loading 的 TEST A 与 `们` one-glyph runtime PoC 结果记录在本仓库对应报告中。Golden、translation 和正式 FONT 未被修改。
