# 翻译文件结构

`translation_worklist.csv` 是 file_id 级管理索引；它记录资源规模、翻译状态、构建状态、实机状态和正式翻译文件位置，不作为剧情逐句翻译或最终对象绑定的直接输入。

`work/luna_translation_templates/sol_translation_mappings/<resource_class>/<file_id>.json`（BRIEFING_NBE 的物理目录名为 `BRIEFING`）是人工维护的 canonical 翻译权威。每份 mapping 只保存经校验的 `unique_index`、中文正文、控制符和审核标记；JPN 结构与上下文仍来自对应模板 CSV。`translations/<resource_class>/<file_id>.csv` 是 production compiler 由 canonical JSON 确定性生成的物化产物，不应直接编辑。

`compiled_translation_manifest.csv` 当前由旧五类 canonical JSON 生成，每行绑定一个具体 JPN record/reference/timed segment。现有统一构建器只读取该 manifest，不从 ENG/MLG_CN 的物理索引推断身份；manifest 与 production CSV 都是可重建的 generated output。

`briefing/` 是 BRIEFING 的独立正式 production 目录：469 个物理 block CSV / 5,645 个 JPN rows。它不在现有 91,609 行 `compiled_translation_manifest.csv` 内，也不得按 `jpn_text` 去重后硬并入旧五类流程。后续专用 oEbN builder 必须按 `file_id + unique_index` 以及 CSV 中的物理 `stream/block/text` 身份写回 clean JPN DAT。完整交接见 `docs/BRIEFING_BUILD_HANDOFF.md`。

两个 production freshness gate 均为只读检查：`python tools/Compile-ProductionTranslations.py --check` 与 `node tools/Compile-BriefingProductionTranslations.mjs --check`。

`translation_text_catalog.csv` 保留全局日文去重、术语检索和 ENG/MLG_CN 候选汇总功能，但不决定最终译文。

当前已落盘的正式翻译包括六类 canonical mapping JSON，以及由 compiler 生成的旧五类 production CSV、BRIEFING 下完整的 469 个 production CSV。任何批量翻译替换都应先改 canonical JSON，再运行对应 compiler 和 freshness check；不要把生成 CSV 当作第二个 authoring source。
