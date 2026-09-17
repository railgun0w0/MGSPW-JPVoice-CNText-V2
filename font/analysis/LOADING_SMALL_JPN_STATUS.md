# Loading / SMALL_JPN 当前状态

这是当前 Loading 字体工作的入口文档。本阶段只覆盖载入动画中的两段角色语录，不覆盖其它菜单、HUD、无线电、任务界面或全游戏 SMALL_JPN 缺字。

## 当前文本范围

```text
我们只会战斗……
但我们要活得不受国家局势摆布。

中美洲是连接北美大陆和南美大陆的脐带。
我们想要这里。
```

去重后共 35 个汉字。

### 已有并实机正常显示：11

```text
我 要 国 家 中 美 北 大 和 南 想
```

### 原版缺失并显示为 `·`：24

```text
们 只 会 战 斗 但 活 得 不 受 局 势 摆 布
洲 是 连 接 陆 的 脐 带 这 里
```

状态冻结为：

```ini
LOADING_REQUIRED_GLYPHS = 35
LOADING_EXISTING_GLYPHS = 11
LOADING_MISSING_GLYPHS = 24
```

`们` 虽已有技术 PoC，但视觉风格未定，仍计入 24 个 `FINAL_GLYPH_PENDING` 缺字。

## 已确认字体路径

```ini
LOADING_FONTDATA = JPN/001cbbd1.xpr
LOADING_RUNTIME_ATLAS = JPN/001cbbd1.xpr own TX2D
```

TEST A 只修改 `001cbbd1.xpr` 自带 TX2D 中 `我 U+6211`、glyph index 239 的图像；实机 Loading 页面中的“我”发生变化。因此当前 Loading 补字研究收敛到单文件 `001cbbd1.xpr`。

不再把 `001c FontData + 00c7 FontTexture` 写成已确认的 Loading 配对关系。`00c7c9f9.xpr` 是否参与其它渲染路径不属于当前 Loading 补字 PoC 必须解决的问题。

## 当前缺字机制

`001cbbd1.xpr` 原版结构：

- dense charmap
- GlyphRecord table
- 自带 TX2D，尺寸 `2048×1024`
- record count `359`
- mapped codepoint `358`
- record 0 未被正常字符正向映射，但有实际非零像素
- 没有确认安全的 `UNUSED_EMPTY` GlyphRecord

当前 24 个 Loading 缺字的结构链路：

```text
charmap value = 0
        ↓
GlyphRecord 0
        ↓
fallback / missing glyph
        ↓
实机显示为 ·
```

## `们 U+4EEC` 技术 PoC

```ini
ONE_GLYPH_POC_STATUS = RUNTIME_SUCCESS
VISUAL_STYLE_STATUS = NOT_FINAL
FINAL_GLYPH_STATUS = PENDING
```

已实机确认 `们` 可以正常显示，不再显示为 `·`。技术链路已验证：

```text
charmap mapping
→ append GlyphRecord
→ 001c own TX2D 新 bitmap
→ Loading runtime 成功读取
```

但当前 `们` 字形与原版 SMALL_JPN 其它中文字风格不统一，因此不能标记为最终完成，也不能据此决定其它 23 个字的最终字体来源或 rasterization 方案。

## 当前冻结项

本阶段暂停：

- 字体风格和 donor 字体研究；
- 全游戏 SMALL_JPN 缺字扫描；
- 其它场景分析；
- 批量生成 24 个字；
- 修改任何 FONT/XPR、translation 或 Golden 文件。

## 相关文档

- `LOADING_FONT_COVERAGE_AUDIT.md`：Loading 35 字 coverage 与 11/24 分类。
- `SMALL_JPN_FONT_PAIR_ANALYSIS.md`：001c 单文件结构及历史 00c7 交叉分析。
- `SMALL_JPN_ONE_GLYPH_PATCH_PLAN.md`：`们` PoC 的设计、结果与冻结状态。
- `font/small_jpn_men_append_poc/small_jpn_men_manifest.json`：技术 PoC manifest，已区分 runtime 成功与视觉未定。
