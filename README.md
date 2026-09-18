# JPVoice_CNText_V2

这是从 clean JPN original 构建完整“日语语音 + 简体中文字幕/文本”补丁的 V2 重构工程。不再考虑让英文汉化版调用日语语音包，也不把 ENG/MLG_CN 的资源结构直接移植到 JPN。

当前已经有两个实机通过的 JPN-authoritative 基准：

- YPK/GTT `1C79F2AD`：98 records / 123 timed segments，fixed-layout multi-segment repack。
- SLOT OLANG `5D3AF52D`：110 条去重日文完成上下文翻译，显式映射回 118 个 JPN references，只重建目标 RBX body 与所在 CNF page。

两条路线均从 clean JPN 构建，并已在 Steam 日语资源路径实机通过。当前 MVP 已冻结，工程进入 RC QA、release assembly 和后续 gameplay QA 阶段。

技术基线：

- [TECHNICAL_FOUNDATION.md](docs/TECHNICAL_FOUNDATION.md)：按 `VERIFIED_REUSABLE`、`OBSOLETE_OR_WRONG`、`UNKNOWN_NEEDS_REVALIDATION` 整理的格式与重建基础。
- [FONT_TECHNICAL_STATE.md](docs/FONT_TECHNICAL_STATE.md)：旧位置保留的 FONT 状态摘要；最新权威结论以 `font/doc/` 为准。
- [FONT_STATUS_MATRIX.csv](docs/FONT_STATUS_MATRIX.csv)：FONT 状态键值索引，runtime 最终结论回链 `font/doc/`。
- [font/doc/README.md](font/doc/README.md)：FONT 正式文档权威入口与文档分工。
- [FONT_TECHNICAL_ARCHIVE.md](font/doc/FONT_TECHNICAL_ARCHIVE.md)：JPN001c crash、runtime dimension 根因、4096×4096 实机结论与实验资产索引。
- [FONT_PRODUCTION_BASELINE.md](font/doc/FONT_PRODUCTION_BASELINE.md)：当前可工作的 EXE/large/small Golden Baseline 与 runtime patch 安全约束。
- [FONT_CUSTOM_BUILD_PLAN.md](font/doc/FONT_CUSTOM_BUILD_PLAN.md)：从 clean JPN 构建完全自有 large/small 中文字库的下一阶段设计。
- [LEGACY_TOOL_AUDIT.md](docs/LEGACY_TOOL_AUDIT.md)：旧工程工具逐项审计与 V2 处置方式。
- [CURRENT_DIRECTION.md](docs/CURRENT_DIRECTION.md)：当前翻译、构建、验收顺序与明确禁止项。
- [BRIEFING_BUILD_HANDOFF.md](docs/BRIEFING_BUILD_HANDOFF.md)：BRIEFING production 输入、专用 builder 约束与后续 round-trip/实机流程。
- [font/analysis/README.md](font/analysis/README.md)：V2 FONT/JPN/MLG 分析报告、coverage 数据、glyph/atlas 输出和示例的集中目录。

旧五类资源仍需复用的 SLOT/CNF、RBX、DAR、OHD、loose OLANG 与 STAGEDAT 底层实现，已固定收录在 `tools/legacy_support/`。正式构建入口位于父级 `tools/`，不再从相邻的 `JPVoice_CNText_Experimental` 目录动态加载代码；`legacy_support` 中各脚本的历史 `main`、旧映射策略和硬编码目标仍不属于 production 入口。

V2 的硬规则：

1. 原始 JPN/ENG/working ENG_CN 文件只读。
2. 所有输出进入 V2 自己的 `work/`、`reports/`、`build/`；不得原地覆盖输入。
3. GTT 必须是 multi-segment / multi-string 模型；旧 single-string builder 永久隔离。
4. 不以 page、`page % 6`、lane 或跨区域 record ordinal 作为未经证明的身份。
5. 每一层重建都必须独立 round-trip；容器通过不等于运行时映射成立。
6. 全补丁以 JPN 日文原文为语义权威、以目标 JPN 资源为结构权威；MLG_CN 仅辅助参考术语与表达，ENG 仅在必要时用于消歧。
7. OLANG 不按 MLG/ENG reference index、entity key occurrence 或旧 `semantic_partial` 结果直接移植；先完成 JPN 上下文工作表，再显式回填全部 JPN references。
8. `translation_worklist.csv` 是 file_id 级管理索引；`work/luna_translation_templates/sol_translation_mappings/<resource_class>/*.json`（BRIEFING_NBE 的物理目录名为 `BRIEFING`）是六类资源统一的 canonical 翻译来源，模板 CSV 主要提供 JPN 结构/上下文，并保留少量 legacy 译文供追溯但不再具备 authoring 权威。`translations/<resource_class>/<file_id>.csv`、旧五类 `compiled_translation_manifest.csv` 和各类 report 都是 production compiler 生成的物化产物，不得直接作为翻译 source-of-truth。旧五类资源由 manifest 或 production CSV 进入现有构建器；BRIEFING 由 `translations/briefing/*.csv` 进入专用 oEbN builder，不得按文本去重后硬并入旧 manifest。
9. 所有正式候选从 clean JPN original 生成，不在旧 Experimental DAT 或现成 ENG/CN 补丁上叠加。

当前状态：

- 当前六类翻译共 710/710 个 file_id、26,686/26,686 条 translation rows 完成。旧五类资源仍为 241 file_ids / 21,041 个去重翻译行，对象级 `compiled_translation_manifest.csv` 共 91,609 行。
- 旧五类 production compiler 读取 Git 已跟踪的 JPN 模板与 `sol_translation_mappings` canonical JSON，并从零生成 production CSV、worklist 与 91,609 行 manifest；被忽略的 `build/translation/` 仅为输出目录，不是前置输入。可用 `python tools/Compile-ProductionTranslations.py --check` 检查所有旧五类物化产物是否新鲜。
- BRIEFING 已生成独立正式 production CSV，并完成专用 clean-JPN fixed-layout 构建：469 blocks / 5,645 个 JPN 物理 rows，其中 FILES 363/4,810、MISSION 106/835；静态合并、全盘 parser/text/diff round-trip 均通过。`node tools/Compile-BriefingProductionTranslations.mjs --check` 是 BRIEFING production freshness gate；2026-09-14 实机已确认 FILES/MISSION 正常显示中文；两条已知长句已加入显式 LF，layout audit 当前为 0 overflow。
- `MVP_STATUS = COMPLETE`。BRIEFING 专用 builder、round-trip 和 FILES/MISSION 实机验证均已通过；当前优先级是 RC QA、release assembly、clean-install smoke 与 gameplay QA。旧五类模板按 `file_id + jpn_text` 自动聚合的同文异境风险属于后续翻译润色/schema 优化，不阻塞 RC1。
- 36 个 YPK/GTT 已完成 fixed-frame repack：1,882 records、2,136 timed segments，1,812 normal fit、70 alignment spill、0 hard overflow。现有容量结果保持不变；alignment spill、容量余量和后续压缩/排版优化统一列为中文润色完成后的后续优化项目，不作为当前生产阻塞。
- 144 个 SLOT OLANG 已覆盖 742 个 physical occurrences；OHD `1E4C1146` 已覆盖 4 个 occurrence、904 个 physical records；14 个 loose OLANG 与 123 个 STAGEDAT embedded OLANG entry 均已完成 round-trip。
- `Build-JpnUnifiedSlot.py` 已从 clean JPN 合并 SLOT OLANG、YPK/GTT、OHD：823 个目标 tag、110 个 SLOT pages、0 block overflow，DAT 大小与 KEY 保持不变。
- 当前 RC1 正式 package 是 20 files：18 个 translated resource outputs，加上 `00c7c9f9.xpr` 与 `001cbbd1.xpr` 两个 self-owned clean-JPN font outputs；`build/rc1/` 的 manifest、hash 和 staging consistency 均 PASS。
- `build/readiness/full_package/` 的旧 21-file package 以及 0007/000E 字体行只保留为历史/reference evidence，不属于当前 RC1 production package。当前仍需执行 clean-install smoke 与更广泛 gameplay QA。
- 标题 UI 的 `NEW GAME`、`LOAD GAME`、`DELETE` 英文标签已通过实机验证。此次 ASCII UI 回归修复共恢复/保留 351 条高风险文本，后续不得把纯 ASCII UI 默认改成依赖未覆盖中文 glyph 的译文。
- 任务结束无线电资源已实机命中中文，BRIEFING 已完成已知长句换行修复；任务结算武器经验字段和固定 UI 长文本也已实机通过。当前剩余验收重点收敛为中文/日文缺字；GTT 容量与 alignment 优化统一留待中文润色后处理。
