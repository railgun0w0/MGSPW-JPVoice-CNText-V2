# V2 font analysis

这里集中保存 V2 的 PC FONT/JPN/MLG 分析报告、coverage 数据、glyph/atlas 结构输出和可视化结果。

最新权威文档位于 [`../doc/README.md`](../doc/README.md)。本目录默认是 evidence/analysis 区，不是 current production conclusion 的入口。

- 正式 XPR 仍在 `font/JPN/`、`font/MLG/`、`font/JPN_CN/`、`font/MLG_CN/`。
- 字体分析工具源码仍在 `tools/` 和 `work/`；它们的分析输出统一写入本目录。
- `font/font_poc*`、`font/small_jpn_*` 等包含测试包或实验 XPR 的目录已统一放在 `font/` 下；它们仍属于实验资源，不是 current production conclusion 的入口。
- PSP 字体分析属于另一个项目区域，不放在这里。

历史报告状态：

| report | status | reason |
|---|---|---|
| `FONT_ANALYSIS.md` | `ARCHIVED / HISTORICAL REFERENCE` | 2026-09-14 阶段性总览；早于最终 runtime dimension root cause。 |
| `FONT_SOURCE_TOPOLOGY.md` | `REFERENCE ONLY` | 四 selector 拓扑仍有效；production/runtime 状态以 `font/doc/` 为准。 |
| `FONT_V2_CODE_ARCHAEOLOGY.md` | `ARCHIVED / HISTORICAL REFERENCE` | 原 V2 copy/rekey 工具链考古；不是当前 self-owned build plan。 |
