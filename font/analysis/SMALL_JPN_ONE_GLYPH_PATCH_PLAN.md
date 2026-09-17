# SMALL_JPN 单字 `们 U+4EEC` patch plan / result

```ini
SCOPE = LOADING_ONLY
ONE_GLYPH_POC_STATUS = RUNTIME_SUCCESS
VISUAL_STYLE_STATUS = NOT_FINAL
FINAL_GLYPH_STATUS = PENDING
RUNTIME_FONTDATA = JPN/001cbbd1.xpr
RUNTIME_ATLAS = JPN/001cbbd1.xpr own TX2D
LOADING_MISSING_SET_SIZE = 24
```

本文件保留原 one-glyph patch 设计信息，同时记录已经完成的 `们` 技术 PoC。它不代表最终字体方案，也不代表已经完成其它 Loading 缺字。

## 当前 Loading 范围

只覆盖以下两段 Loading 角色语录中的 35 个汉字：

```text
我们只会战斗……
但我们要活得不受国家局势摆布。

中美洲是连接北美大陆和南美大陆的脐带。
我们想要这里。
```

已有并实机正常显示 11 个：

```text
我 要 国 家 中 美 北 大 和 南 想
```

缺失并显示为 `·` 的 24 个：

```text
们 只 会 战 斗 但 活 得 不 受 局 势 摆 布
洲 是 连 接 陆 的 脐 带 这 里
```

`们` 虽然已有技术 PoC，但因视觉风格尚未最终确定，仍保留在 `LOADING_MISSING_GLYPHS / FINAL_GLYPH_PENDING`，所以缺字集合仍为 24 个。

## 已确认的 Loading 字体结构

- `JPN/001cbbd1.xpr` 包含 dense charmap、GlyphRecord table 和自带 TX2D。
- 自带 TX2D：`2048×1024`，format 2，linear 8-bit texture。
- 原版 record count：`359`；mapped codepoint：`358`。
- record 0 未被正常字符正向映射，但有实际非零像素，是 fallback/missing-glyph 候选，禁止复用。
- 没有确认安全的 `UNUSED_EMPTY` GlyphRecord。
- 当前 Loading 缺字链路：

```text
charmap value = 0
        ↓
GlyphRecord 0
        ↓
fallback / missing glyph
        ↓
实机显示为 ·
```

TEST A 已实机确认：只修改 `001cbbd1.xpr` 自带 TX2D 中 `我 U+6211`、glyph index 239 的像素后，Loading 页面中的“我”发生变化。因此当前补字 PoC 收敛到单文件 `001cbbd1.xpr`；不再把 `001c FontData + 00c7 FontTexture` 写成已确认的 Loading 配对关系。

## `们` 技术 PoC 结果

PoC 从 clean `001cbbd1.xpr` 独立生成：

- `U+4EEC`: `0 -> 359`
- GlyphRecord count：`359 -> 360`
- USER size：`0x214CA -> 0x214DA`
- 新 record：写入 001c 自带 TX2D 的新 atlas slot
- record 0：未复用
- 旧 359 条 GlyphRecord：保持不变
- 其它 charmap：保持不变

实机结果：

```text
们 可以正常作为汉字显示，不再显示为 ·
```

因此已确认：

```text
新增/修改 charmap mapping
        ↓
新增 GlyphRecord
        ↓
001c 自带 TX2D 新 bitmap
        ↓
Loading runtime 成功读取
        ↓
缺失字符能够显示
```

## 当前视觉状态

当前 `们` 只是 `TECHNICAL_POC`。它与原版 SMALL_JPN 其它中文字形风格明显不统一，因此：

- `ONE_GLYPH_POC_STATUS = RUNTIME_SUCCESS`
- `VISUAL_STYLE_STATUS = NOT_FINAL`
- `FINAL_GLYPH_STATUS = PENDING`

本文件不决定最终字体来源、donor 风格、rasterizer、字号、baseline 或 metrics，也不开始其它 23 个 Loading 缺字。

## 历史 patch 设计记录

由于没有安全的空 GlyphRecord，原设计采用 append-only：

1. 新增 16-byte GlyphRecord；
2. 更新 001c record count `0x0167 -> 0x0168`；
3. USER size 增加 16 bytes；
4. 增加 `U+4EEC -> new_index`；
5. 在 001c 自带 TX2D 的空白区域写入新 bitmap；
6. 保持所有旧 GlyphRecord、旧 glyph index 和其它 charmap 不变。

上述设计已经由 `们` 单字 PoC 在 runtime 层验证成功，但仅表示技术链路成立，不表示可以直接批量生成最终 24 字。

## 当前冻结项

本阶段不做：

- donor 字体或最终字形风格研究；
- 全游戏 SMALL_JPN 缺字扫描；
- 其它场景、菜单、HUD、无线电、任务界面分析；
- 批量补齐 24 个 Loading 缺字；
- 修改 Golden XPR 或 translation。
