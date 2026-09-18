# BRIEFING 构建交接

更新时间：2026-09-14（Asia/Hong_Kong）

本文是当前 clean JPN BRIEFING 中文文本构建与实机交接的权威说明。专用 fixed-layout builder、离线 round-trip、RC1 staging 和已知长句显式换行修订已经完成；2026-09-14 实机已确认 FILES/MISSION 能命中中文。Ruby canonical 同步记录见 `docs/RUBY_CANONICAL_CHECKPOINT_2026-09-14.md`。

## 当前完成状态

- BRIEFING FILES：363 blocks / 4,810 JPN rows。
- BRIEFING MISSION：106 blocks / 835 JPN rows。
- 合计：469 blocks / 5,645 JPN rows。
- 翻译 mapping：469/469 file_ids、5,645/5,645 rows。
- 正式 production CSV：`translations/briefing/` 下 469 个 CSV、5,645 行。
- 静态合并结果：控制结构、UTF-8、物理 row 身份、block 容量和 CSV round-trip 均通过；469 blocks 全部 fit，0 overflow。
- 专用 builder：`tools/Build-BriefingDat.py`，支持 `--check` 和正式构建，只接受冻结 clean JPN SHA-256 `683fef2d...d94e372`。
- 独立 candidate：`build/readiness/briefing/MGS_PW/mgspw/JPN/disc0_rel/0076531d.DAT`，SHA-256 `360125f3...80373eb`。
- 离线验证：469/469 blocks、5,645/5,645 中文 rows exact；2,292 个非目标 oEbN block 不变；目标 block 外 ciphertext 改动 0；DAT size 4,142,432 不变。
- 全量回读：945 allocations、2,761 oEbN、2,727 text-bearing、34 empty、42,079 rows、0 parser failure。
- 历史统一 readiness 包：`build/readiness/full_package/`，21 files、1,134,808,848 bytes，逐文件 SHA-256 mismatch 为 0；该包及其中 0007/000E 字体行只作历史/reference evidence。
- 当前 RC1 正式 package：`build/rc1/staging/`，20 files，包括 18 个 translated resource outputs 与 `00c7c9f9.xpr`、`001cbbd1.xpr` 两个 self-owned clean-JPN font outputs；manifest、SHA256 和 staging consistency 均 PASS。
- 实机回归：BRIEFING FILES 和任务结束 MISSION 文本已能正常以中文显示，原“无线电仍为日文”问题已解决。
- 实机长句排版：字幕界面不自动折行的问题已通过在对应 mapping `cn_text` 内加入显式 LF 修复；已知两条 FILES/MISSION 样本、新包重建和 layout audit 均通过。
- BRIEFING 当前状态：469 blocks / 5,645 rows，FILES/MISSION 实机显示通过，已知 `BRIEFING_LINE_WRAP_OVERFLOW=0`；后续只保留新增场景的回归检查。

production CSV 内的 `translation_status=APPROVED` / `build_status=READY` 是可重复生成的输入门槛；资源级离线状态为 `OFFLINE_BUILT_PASS`。为保持 compiler 确定性，不把 469 个 CSV 的输入状态改写为派生构建状态。当前 BRIEFING 实机状态为 `INGAME_PASS`：运行时命中、中文显示和已知长句换行均通过；后续新增文本仍需遵守同一布局审计。

## 权威输入与派生输出

权威层级如下：

1. `work/luna_translation_templates/BRIEFING/*.csv`：冻结的 JPN 物理 row 模板；JPN 文本、顺序和结构身份权威，只读。
2. `work/luna_translation_templates/sol_translation_mappings/BRIEFING/*.json`：人工审定的中文 mapping 权威。
3. `translations/briefing/*.csv`：由前两层确定性合并得到的正式 BRIEFING production CSV；builder 的直接翻译输入。
4. `build/translation/briefing_production_merge_report.json`：本地生成的静态合并报告，不是翻译输入。
5. `tools/Build-BriefingDat.py`：clean-JPN fixed-layout builder 与全盘回读/差异审计实现。
6. `build/readiness/briefing/reports/briefing_build_report.json`：本地离线构建 PASS 证据。

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

`translations/briefing/*.csv` 仍是独立 production 输入，由专用 builder 直接消费。

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

builder 已实现以下门槛，任何后续重建仍必须全部通过：

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

本轮 builder 输出、重解析和差异审计已经全部通过，资源级为 `OFFLINE_BUILT_PASS`；2026-09-14 已完成 FILES/MISSION 的显示、换行、ruby、顺序和调用路径实机检查，BRIEFING 当前标记为 `INGAME_PASS`。

## 收尾结论（2026-09-14）

- 两条已知 FILES 行宽超限已在 mapping 中仅插入 LF 修复：`BRIEFING_FILES_BLOCK_036C20#7`、`BRIEFING_FILES_BLOCK_03A280#11`。
- 重新生成 production CSV 和 BRIEFING DAT 后，FILES/MISSION 行宽与显示行数审计均为 0 overflow；clean-JPN fixed-layout builder、容量检查、parser/text/diff round-trip 均通过。
- 历史 21 文件统一 readiness 包已完成实机验证；BRIEFING FILES 与任务结束 MISSION 均正常显示中文。该包不等同于当前 RC1 20-file production package。
- BRIEFING 当前不再有已知阻塞项；后续仅对新增或改动文本执行同样的 layout audit 和实机回归。

## 当前 RC QA 执行顺序

1. 运行 production `--check` 与全局 translation state `--check`。
2. 以 `build/rc1/staging/` 的 20-file manifest 为当前 package，执行 clean-install smoke；不得使用 Steam 当前 DAT、旧 Experimental 或 MLG/ENG DAT：

```powershell
python tools/Build-BriefingDat.py --dat 'D:\GAME\test\JPN\MGS_PW\mgspw\JPN\disc0_rel\0076531d.DAT' --check
python tools/Build-BriefingDat.py --dat 'D:\GAME\test\JPN\MGS_PW\mgspw\JPN\disc0_rel\0076531d.DAT'
Get-Content build/rc1/RC1_FILE_MANIFEST.csv
```

3. 安装前生成备份与 20 文件 hash 清单，安装后验证 hash。
4. 分别实机检查 BRIEFING FILES 与 MISSION BRIEFING，记录 block/file_id、场景和问题行。
5. 只在对应 mapping 中修订问题，再从 production compile 开始全量重跑。

当前恢复点：翻译、production merge、专用 clean-JPN builder、全盘 round-trip、差异审计、已知长句显式换行和当前 20-file RC1 staging 均已完成；实机已证明 FILES/MISSION 运行时命中、中文显示和已知长句排版正常。BRIEFING 已收尾，后续只需对新增翻译做同等布局回归，不重新进行结构研究。

## MVP 已完成与后续优化

`MVP_STATUS = COMPLETE`。当前第一优先级是 RC QA、release assembly、clean-install smoke 与 gameplay QA，不在 RC1 前扩张为旧五类翻译体系重构：

- MVP 已完成：BRIEFING 专用 oEbN builder、clean-JPN 重建、结构/文本 round-trip、RC1 staging 集成。
- MVP 实机验证：FILES/MISSION 运行时命中、中文显示和已知显式换行/长句排版已通过测试；BRIEFING 当前不再有已知阻塞，后续仅需随字库和新增文本继续回归。
- MVP 保持：BRIEFING 继续使用 5,645 个独立物理 translation rows，保证每个上下文可以单独译写并精确绑定。
- MVP 不做：不重新拆分或重译旧五类 21,041 个聚合 translation rows，不把全局通用 schema 改造作为 BRIEFING 构建前置条件。

已登记的 RC1 后优化方向：旧五类模板生成器当前以 `file_id + jpn_text` 自动聚合翻译单元，可能无法表达同一 file_id 内“日文完全相同但因上下文而需要不同中文”的情况。后续应审计所有 `source_objects > 1` 的聚合行，并将通用翻译身份逐步改为稳定 object/translation-unit identity；译文复用必须显式声明，`jpn_text` 只用于源文校验，不再作为唯一译文主键。无论翻译维护层是否复用，构建 manifest 都必须展开并保留全部物理对象。
