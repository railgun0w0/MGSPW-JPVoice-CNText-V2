# BRIEFING_NBE JPN-only Luna templates

本目录是已冻结 B81 corpus 的 JPN-only 翻译模板：

- BRIEFING FILES：363 blocks / 4,810 JPN rows
- BRIEFING MISSION：106 blocks / 835 JPN rows
- 合计：469 blocks / 5,645 JPN rows

`jpn_text` 是唯一结构和语义权威。`eng_reference` 与 `mlg_cn_reference` 来自 ENG-topology 资源，只按已确认的 scene id、语义和上下文对齐；未通过可靠性门槛的辅助参考保持空白，不按 block/index ordinal 硬套。

这批模板尚未翻译、未构建、未进入 DAT。

可重复生成脚本：

- `tools/Align-JpnBriefingReferences.py`
- `tools/Prepare-JpnBriefingTemplates.mjs`
