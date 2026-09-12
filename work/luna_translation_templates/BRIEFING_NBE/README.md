# BRIEFING_NBE（仅 JPN lane）Luna 翻译模板

本目录是已冻结 B81 corpus 中 **JPN lane 的待汉化翻译单元**：

- BRIEFING FILES：363 blocks / 4,810 JPN rows
- BRIEFING MISSION：106 blocks / 835 JPN rows
- 合计：469 blocks / 5,645 JPN rows

这里的“仅 JPN lane”是语料范围和结构范围声明：469 个 CSV 全部对应 JPN BRIEFING block，5,645 个 translation rows 全部以非空 `jpn_text` 为源文。目录中没有把 ENG/FRA/DEU/ITA/ESP lane 的 block 建成独立翻译单元，也没有 FRA/DEU/ITA/ESP 文本列；它不是 B79 六语言 oEbN census 的模板化副本。

旧初版的 2,461 个 translation unit / 42,079 个全语言物理文本对象 / 42,002 行统计已废弃；这些错误分组模板不属于本目录当前 corpus。

CSV 中仍保留 `eng_reference` 和 `mlg_cn_reference`：前者是英文理解辅助，后者是旧汉化措辞参考。这些字段会出现英文或旧中文，因此“仅 JPN lane”不等于 CSV 内只能出现日文字符；它表示 **只有 `jpn_text` 是待翻译源文和结构/语义权威**。当前辅助覆盖为 ENG 5,095 rows、旧 MLG-CN 5,085 rows，其余未可靠对齐的 reference 留空。

当前 5,645 个 `cn_text` 均为空，全部尚待正式汉化。不得把 reference 当成已完成译文，也不得按 ENG/MLG block/index 顺序硬套。

这批模板尚未翻译、未构建、未进入 DAT。

可重复生成脚本：

- `tools/Align-JpnBriefingReferences.py`
- `tools/Prepare-JpnBriefingTemplates.mjs`
