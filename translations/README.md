# 翻译文件结构

`translation_worklist.csv` 是 file_id 级管理索引；它记录资源规模、翻译状态、构建状态、实机状态和正式翻译文件位置，不作为剧情逐句翻译或最终对象绑定的直接输入。

`translations/<resource_class>/<file_id>.csv` 是人工翻译权威。每份文件保留该 JPN 资源的完整对象顺序、上下文、控制符、最终中文和审核状态。

`compiled_translation_manifest.csv` 当前由旧五类 `APPROVED` file_id CSV 生成，每行绑定一个具体 JPN record/reference/timed segment。现有统一构建器只读取该 manifest，不从 ENG/MLG_CN 的物理索引推断身份。

`briefing/` 是 BRIEFING 的独立正式 production 目录：469 个物理 block CSV / 5,645 个 JPN rows。它不在现有 91,609 行 `compiled_translation_manifest.csv` 内，也不得按 `jpn_text` 去重后硬并入旧五类流程。后续专用 oEbN builder 必须按 `file_id + unique_index` 以及 CSV 中的物理 `stream/block/text` 身份写回 clean JPN DAT。完整交接见 `docs/BRIEFING_BUILD_HANDOFF.md`。

`translation_text_catalog.csv` 保留全局日文去重、术语检索和 ENG/MLG_CN 候选汇总功能，但不决定最终译文。

当前已落盘的正式翻译包括旧五类 production CSV，以及 `briefing/` 下完整的 469 个 BRIEFING CSV。BRIEFING 当前状态是 `APPROVED/READY/NOT_TESTED`，不是已构建或实机通过。
