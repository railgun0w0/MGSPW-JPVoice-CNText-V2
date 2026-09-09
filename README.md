# JPVoice_CNText_V2

这是从 clean JPN original 构建完整“日语语音 + 简体中文字幕/文本”补丁的 V2 重构工程。不再考虑让英文汉化版调用日语语音包，也不把 ENG/MLG_CN 的资源结构直接移植到 JPN。

当前已经有两个实机通过的 JPN-authoritative 基准：

- YPK/GTT `1C79F2AD`：98 records / 123 timed segments，fixed-layout multi-segment repack。
- SLOT OLANG `5D3AF52D`：110 条去重日文完成上下文翻译，显式映射回 118 个 JPN references，只重建目标 RBX body 与所在 CNF page。

两条路线均从 clean JPN 构建，并已在 Steam 日语资源路径实机通过。工程现已从格式验证阶段转入按资源扩大真实中文覆盖的实施阶段。

技术基线：

- [TECHNICAL_FOUNDATION.md](docs/TECHNICAL_FOUNDATION.md)：按 `VERIFIED_REUSABLE`、`OBSOLETE_OR_WRONG`、`UNKNOWN_NEEDS_REVALIDATION` 整理的格式与重建基础。
- [LEGACY_TOOL_AUDIT.md](docs/LEGACY_TOOL_AUDIT.md)：旧工程工具逐项审计与 V2 处置方式。
- [CURRENT_DIRECTION.md](docs/CURRENT_DIRECTION.md)：当前翻译、构建、验收顺序与明确禁止项。

V2 的硬规则：

1. 原始 JPN/ENG/working ENG_CN 文件只读。
2. 所有输出进入 V2 自己的 `work/`、`reports/`、`build/`；不得原地覆盖输入。
3. GTT 必须是 multi-segment / multi-string 模型；旧 single-string builder 永久隔离。
4. 不以 page、`page % 6`、lane 或跨区域 record ordinal 作为未经证明的身份。
5. 每一层重建都必须独立 round-trip；容器通过不等于运行时映射成立。
6. 全补丁以 JPN 日文原文为语义权威、以目标 JPN 资源为结构权威；MLG_CN 仅辅助参考术语与表达，ENG 仅在必要时用于消歧。
7. OLANG 不按 MLG/ENG reference index、entity key occurrence 或旧 `semantic_partial` 结果直接移植；先完成 JPN 上下文工作表，再显式回填全部 JPN references。
8. `translation_worklist.csv` 是 file_id 级管理索引；`translations/<resource_class>/<file_id>.csv` 是翻译权威；`compiled_translation_manifest.csv` 是唯一正式构建输入。
9. 所有正式候选从 clean JPN original 生成，不在旧 Experimental DAT 或现成 ENG/CN 补丁上叠加。

当前状态：

- 当前 catalog 内 241/241 个 file_id、21,041/21,041 条 file_id 内去重译文全部完成；对象级 `compiled_translation_manifest.csv` 共 91,609 行。
- 36 个 YPK/GTT 已完成 fixed-frame repack：1,882 records、2,136 timed segments，1,815 normal fit、67 alignment spill、0 hard overflow。人工缩短的 29 个原 overflow record 已固化到权威 mapping/CSV。
- 144 个 SLOT OLANG 已覆盖 742 个 physical occurrences；OHD `1E4C1146` 已覆盖 4 个 occurrence、904 个 physical records；14 个 loose OLANG 与 123 个 STAGEDAT embedded OLANG entry 均已完成 round-trip。
- `Build-JpnUnifiedSlot.py` 已从 clean JPN 合并 SLOT OLANG、YPK/GTT、OHD：823 个目标 tag、110 个 SLOT pages、0 block overflow，DAT 大小与 KEY 保持不变。
- `build/readiness/full_package/` 已组成 20 文件的统一测试包：合并 SLOT DAT/KEY、14 个 loose OLANG、STAGEDAT 和 3 个已验证中文字库。
- 2026-09-09 已将统一包安装到 `D:\GAME\steamapps\common\MGS_PW`，20 个文件写入后 `VERIFY_MISMATCHES=0`；原文件备份在 `JPVoice_CNText_V2\backups\` 下。
- 标题 UI 的 `NEW GAME`、`LOAD GAME`、`DELETE` 英文标签已通过实机验证。此次 ASCII UI 回归修复共恢复/保留 351 条高风险文本，后续不得把纯 ASCII UI 默认改成依赖未覆盖中文 glyph 的译文。
- 当前仍需集中验收中文缺字/日文缺字、任务结束后的无线电资源、任务结算武器经验字段和固定 UI 长文本排版；发现问题时回到对应 file_id 权威译文修订，再从 clean JPN 全量重建。
