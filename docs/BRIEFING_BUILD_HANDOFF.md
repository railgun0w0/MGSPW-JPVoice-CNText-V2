# BRIEFING 构建交接

更新时间：2026-09-13（Asia/Hong_Kong）

本文是当前 clean JPN BRIEFING 中文文本进入后续构建的权威交接说明。它记录已经完成的输入、可重复执行的静态门槛，以及尚未实现的 DAT 写入边界。

## 当前完成状态

- BRIEFING FILES：363 blocks / 4,810 JPN rows。
- BRIEFING MISSION：106 blocks / 835 JPN rows。
- 合计：469 blocks / 5,645 JPN rows。
- 翻译 mapping：469/469 file_ids、5,645/5,645 rows。
- 正式 production CSV：`translations/briefing/` 下 469 个 CSV、5,645 行。
- 静态合并结果：控制结构、UTF-8、可见假名、物理 row 身份、block 容量和 CSV round-trip 均通过；469 blocks 全部 `NORMAL_FIT`，0 `HARD_OVERFLOW`。
- 尚未完成：BRIEFING oEbN DAT builder、重建后的 parser/byte round-trip、统一测试包集成和实机验证。

`translation_status=APPROVED` 和 `build_status=READY` 表示译文已通过进入 builder 前的静态门槛，不表示已经写入 DAT。当前 `ingame_status` 仍为 `NOT_TESTED`。

## 权威输入与派生输出

权威层级如下：

1. `work/luna_translation_templates/BRIEFING/*.csv`：冻结的 JPN 物理 row 模板；JPN 文本、顺序和结构身份权威，只读。
2. `work/luna_translation_templates/sol_translation_mappings/BRIEFING/*.json`：人工审定的中文 mapping 权威。
3. `translations/briefing/*.csv`：由前两层确定性合并得到的正式 BRIEFING production CSV；后续 builder 的直接翻译输入。
4. `build/translation/briefing_production_merge_report.json`：本地生成的静态合并报告，不是翻译输入。

物理目录名使用 `BRIEFING` / `translations/briefing`，现有 CSV 和 mapping 内的逻辑资源类仍是 `BRIEFING_NBE`。builder 应按 `file_id` 前缀区分 `BRIEFING_FILES_BLOCK_*` 与 `BRIEFING_MISSION_BLOCK_*`，不得按目录名猜测另一套 schema。

## 可重复生成与检查

在仓库根目录执行：

```powershell
node tools/Compile-BriefingProductionTranslations.mjs --write
node tools/Compile-BriefingProductionTranslations.mjs --check
python work/luna_translation_templates/tools/rebuild_translation_state.py --check
```

Node 环境必须能解析项目既有依赖 `@oai/artifact-tool`。`--write` 只重建 `translations/briefing/` 和本地 merge report；`--check` 不写文件，只验证已提交 CSV 与模板/mapping 的确定性结果完全相同。两个模式都不读取、修改或生成 DAT/KEY。

该 compiler 是确定性本地合并/校验工具，不调用任何外部翻译模型，也不重新翻译文本。缺少 Node 依赖时应使用当前工作区提供的依赖运行时，不得以下载 NMT/LLM 模型代替构建步骤。

继续构建前必须看到：

```text
PRODUCTION_FILES=469
TRANSLATION_ROWS=5645
BRIEFING_FILES=363/4810
BRIEFING_MISSION=106/835
CONTROL_ERRORS=0
KANA_ROWS=0
HARD_OVERFLOW_BLOCKS=0
ARTIFACT_TOOL_CSV_ROUNDTRIP_FILES=469
```

全局 state check 还必须保持 710/710 file_ids、26,686/26,686 rows、`VALIDATION_ERRORS=0`。

## 与旧五类 production 流程的边界

现有 `tools/Compile-ProductionTranslations.py` 和 `build/translation/compiled_translation_manifest.csv` 只覆盖 YPK_GTT、OHD、LOOSE_OLANG、STAGEDAT_OLANG、SLOT_OLANG 五类资源：241 file_ids、21,041 个去重翻译行、91,609 个对象绑定。

BRIEFING 不在该 91,609 行 manifest 内。不得为了复用旧流程而按 `jpn_text` 去重 BRIEFING，也不得把 5,645 行附加到旧 manifest 后直接交给现有 OLANG/GTT builder。BRIEFING 保留每个物理 JPN row，即使同一 block 或不同 block 的日文文本相同，也必须按物理身份分别写回。

在专用 BRIEFING builder 完成前，`translations/briefing/*.csv` 是独立的 production 输入。

## 专用 builder 必须遵守的绑定规则

每个 CSV 对应一个 JPN oEbN text-bearing block。builder 必须：

1. 只从当前 clean JPN `0076531d.DAT` 开始，不在旧 Experimental、MLG_CN、ENG 或已打补丁 DAT 上叠加。
2. 精确读取 469 个 production CSV 和 5,645 行，不漏、不重、不额外接受其他语言 lane。
3. 使用 `file_id + unique_index` 作为 production row 主键；`unique_index` 在每个 block 内必须从 0 连续递增。
4. 解析 `first_reference_index` 中的 `stream/block/text`，并与 `entity_context` 中的 `stream/block/block_file/text_base/capacity` 交叉验证。
5. 使用 `block_file` 锁定物理 oEbN block，并用 `text` 序号绑定该 block 内的 JPN row；不得只按日文内容匹配，也不得跨 block 去重。
6. 写入 `cn_text` 的严格 UTF-8 bytes，并为每条文本保留 NUL terminator；不得截断多字节字符。
7. 保留 oEbN 非文本结构、block 顺序、block 起点、非目标语言 lanes、空 block 和 DAT 中所有非目标 payload。
8. 每个 block 的全部 `cn_text UTF-8 bytes + 每行一个 NUL` 总量不得超过 `entity_context.capacity`。当前 production merge 已报告 469/469 fit，但 builder 必须再次从实际 clean DAT 验证容量，不能只相信 CSV 声明。
9. 保持 `<R=...,...>`、`<I=...>`、`<->`、`$...`、printf placeholder 等控制结构；不得把控制 token 当普通文本剥离。
10. 输出只能进入新的 `build/` 子目录；不得原地覆盖 clean JPN 输入，未经明确授权不得安装到游戏目录。

## builder 的强制验证

首个 builder 应先实现 `--check` 或 dry-run，再实现写入。正式结果至少要报告：

- 输入 production files/rows：469 / 5,645；
- FILES 与 MISSION：363/4,810、106/835；
- 命中物理 block/row：469 / 5,645；
- 缺失、重复、额外、JPN 基线不一致：全部 0；
- 控制结构、UTF-8/NUL、容量错误：全部 0；
- 重建后仍能以已确认 oEbN grammar 解析；
- 重建后 469 个目标 block 的中文逐行 exact match；
- 其余 2,292 个 oEbN block 和所有非目标 DAT 区域保持不变，或给出经过验证的最小必要差异清单；
- DAT 总大小、allocation 覆盖/间隙和 parser failure 状态；
- KEY 是否保持 byte-identical。

不要把“469 个 block 均静态 fit”写成“DAT 构建已完成”。只有 builder 输出、重解析和差异审计全部通过后，才能把 BRIEFING 标记为 `BUILT`；只有实机检查 FILES/MISSION 的显示、换行、ruby、顺序和调用路径后，才能标记为 `INGAME_PASS`。

## 后续执行顺序

1. 运行 production `--check` 与全局 translation state `--check`。
2. 实现只读 dry-run 的 BRIEFING oEbN builder，并验证上述精确绑定。
3. 从 clean JPN DAT 生成独立 BRIEFING build candidate。
4. 对 candidate 重新执行 oEbN parser、文本、容量、非目标差异和 DAT/KEY 验证。
5. 将通过验证的 BRIEFING DAT 与既有五类资源的统一测试包重新组装；不得在旧测试 DAT 上增量覆盖。
6. 安装前生成备份与文件 hash 清单，安装后验证 hash。
7. 分别实机检查 BRIEFING FILES 与 MISSION BRIEFING，记录 block/file_id、场景和问题行。
8. 只在对应 mapping 中修订问题，再从 production compile 开始全量重跑。

当前恢复点：翻译与 production merge 已完成；下一项工程工作是“专用 BRIEFING clean-JPN builder + round-trip”，不是继续翻译，也不是重复 B81 corpus 研究。
