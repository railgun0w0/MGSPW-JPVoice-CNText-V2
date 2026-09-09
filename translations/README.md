# 翻译文件结构

`translation_worklist.csv` 是 file_id 级管理索引；它记录资源规模、翻译状态、构建状态、实机状态和正式翻译文件位置，不作为剧情逐句翻译或最终对象绑定的直接输入。

`translations/<resource_class>/<file_id>.csv` 是人工翻译权威。每份文件保留该 JPN 资源的完整对象顺序、上下文、控制符、最终中文和审核状态。

`compiled_translation_manifest.csv` 由所有 `APPROVED` 的 file_id CSV 生成，每行绑定一个具体 JPN record/reference/timed segment。统一构建器只读取该 manifest，不从 ENG/MLG_CN 的物理索引推断身份。

`translation_text_catalog.csv` 保留全局日文去重、术语检索和 ENG/MLG_CN 候选汇总功能，但不决定最终译文。

当前首个正式样板为 `slot_olang/5D3AF52D.csv`。
