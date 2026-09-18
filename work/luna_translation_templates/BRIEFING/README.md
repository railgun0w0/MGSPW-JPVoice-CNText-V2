# BRIEFING（仅 JPN lane）Luna 翻译模板

物理目录名为 `BRIEFING`；为兼容既有 5,645 行模板和 mapping，文件内部逻辑资源类仍为 `resource_class=BRIEFING_NBE`。

本目录是已冻结 B81 corpus 中 **JPN lane 的待汉化翻译单元**：

- BRIEFING FILES：363 blocks / 4,810 JPN rows
- BRIEFING MISSION：106 blocks / 835 JPN rows
- 合计：469 blocks / 5,645 JPN rows

这里的“仅 JPN lane”是语料范围和结构范围声明：469 个 CSV 全部对应 JPN BRIEFING block，5,645 个 translation rows 全部以非空 `jpn_text` 为源文。目录中没有把 ENG/FRA/DEU/ITA/ESP lane 的 block 建成独立翻译单元，也没有 FRA/DEU/ITA/ESP 文本列；它不是 B79 六语言 oEbN census 的模板化副本。

旧初版的 2,461 个 translation unit / 42,079 个全语言物理文本对象 / 42,002 行统计已废弃；这些错误分组模板不属于本目录当前 corpus。

CSV 中仍保留 `eng_reference` 和 `mlg_cn_reference`：前者是英文理解辅助，后者是旧汉化措辞参考。这些字段会出现英文或旧中文，因此“仅 JPN lane”不等于 CSV 内只能出现日文字符；它表示 **只有 `jpn_text` 是待翻译源文和结构/语义权威**。当前辅助覆盖为 ENG 5,095 rows、旧 MLG-CN 5,085 rows，其余未可靠对齐的 reference 留空。

当前 5,645 个模板行的 `cn_text` 均保持为空；模板是只读输入，不以回填 CSV 表示翻译进度。正式译文存放在 `../sol_translation_mappings/BRIEFING/`。截至 `2026-09-13`，469 个 file_id / 5,645 rows 已全部完成，剩余 0，`NEXT_FILE_ID=NONE`。译文仍以 JPN 为权威，reference 仅作为辅助；不得按 ENG/MLG block/index 顺序解释或重排现有 mapping。

这批模板已经完成翻译 mapping，并已由 `tools/Compile-BriefingProductionTranslations.mjs` 确定性合并为 `translations/briefing/` 下 469 个正式 CSV / 5,645 rows。静态校验、专用 clean-JPN oEbN builder、parser/text/diff round-trip 均 PASS：0 漏行、0 重复、0 控制结构错误、0 hard overflow；FILES/MISSION 已完成实机中文显示验证，当前状态为 `INGAME_PASS`。后续只需对新增或修改文本做同样的布局审计和实机回归。

后续不得直接编辑本目录模板或从模板构建 DAT。应先运行 production compiler 的 `--check`，再按 `docs/BRIEFING_BUILD_HANDOFF.md` 使用正式 CSV 实现 clean-JPN builder。

可重复生成脚本：

- `tools/Align-JpnBriefingReferences.py`
- `tools/Prepare-JpnBriefingTemplates.mjs`
