# JPVoice_CNText_V2 最终方向

更新日期：2026-09-14（Asia/Hong_Kong）

## 一、最终目标

从干净 JPN 原版构建完整的：

**日语语音 + 简体中文字幕/文本补丁。**

不再考虑以下路线：

- 让英文汉化版调用日语语音包。
- 将 ENG 或 MLG_CN 的资源结构移植到 JPN。
- 以旧 Experimental DAT 为基础继续叠加修改。

所有正式构建都必须从 clean JPN original 开始。

## 二、权威顺序

### 结构权威

JPN 决定：

- 使用哪些资源。
- file_id 和 physical occurrence。
- record/entity/reference 数量。
- 对象顺序。
- timed segment 数量。
- timing、trigger、style。
- metadata。
- frame、容量和容器布局。

ENG/MLG_CN 的 page、tag、record、entity、reference、segment index 均不能直接作为 JPN 身份。

### 语义权威

翻译依据按以下顺序排列：

1. JPN 日文原文。
2. 同一 JPN file_id 的完整剧情上下文。
3. MLG_CN 的中文措辞和术语。
4. ENG 的剧情说明与日文歧义消解。

只有经过语义确认的 ENG/CN 参考才能采用。

如果 MLG_CN 存在多个 variant，默认只使用枚举顺序中的第一个 variant 作为翻译参考；它仍然不能决定 JPN 结构或对象身份。

## 三、三层翻译数据结构

`translation_worklist.csv` 是 file_id 级全局管理索引，负责资源规模、优先级、翻译状态、构建状态、实机状态和正式翻译文件位置。它不再按日文全局去重保存最终译文，也不直接作为构建输入。

`translations/<resource_class>/<file_id>.csv` 是人工翻译权威。每个剧情资源单独保存完整上下文，包括：

- JPN 原文顺序。
- 前后文。
- record/reference/segment 归属。
- entity 或 timing 信息。
- 控制符。
- ENG/CN 候选参考。
- 最终中文和审核状态。

`compiled_translation_manifest.csv` 是旧五类资源的正式构建输入。它由对应 `APPROVED` file_id CSV 自动生成，每行绑定一个具体 JPN record、reference 或 timed segment。BRIEFING 保留独立的物理 row topology，以 `translations/briefing/*.csv` 作为专用 oEbN builder 的直接输入，不进入现有 91,609 行 manifest。

原来的全局日文去重与参考汇总保留为 `translation_text_catalog.csv`，只用于搜索重复文本、术语和 ENG/MLG_CN 候选，不决定最终译文。

完整关系为：

旧五类关系为：

`translation_worklist.csv（管理） -> 单个 file_id CSV（翻译权威） -> compiled_translation_manifest.csv（JPN 对象绑定） -> clean JPN build`

BRIEFING 关系为：

`JPN block 模板 + per-file mapping -> translations/briefing/*.csv -> 专用 oEbN builder -> clean JPN build`

## 四、各资源的处理方式

### YPK/GTT

按 JPN record 和 timed segment 翻译。

必须保持：record 数量和顺序、segment_count、header_size、record_size、aligned_size、record offset、timing、trigger、style、其他 metadata 和整个 YPK 物理布局。

中文 timed strings 连续写入，重新计算 text boundaries。

```text
required = 所有中文 UTF-8 bytes + 每段一个 NUL
hard_capacity = aligned_size - header_size
```

允许使用原 record 的 alignment slack，但不允许修改 record_size、扩大 aligned frame、移动后续 record 或扩大整个 YPK。overflow 时先人工缩短译文，仍放不下则停止并报告。

### OHD

按 JPN OHD record 翻译，保持 record 数量、顺序、metadata、固定布局和文本字段之外的所有 bytes。

只在目标文本字段中写入 `UTF-8 text + NUL + zero padding`。超出固定文本容量时不得截断或自动扩展 record。

### SLOT/loose OLANG

按 JPN reference 翻译，保持 JPN header/aux 数据、entity table、entity key、reference span、reference 数量/顺序，以及每个 reference 的 language key 和 flag。

只重建 UTF-8/NUL 字符串 body 和 body-relative text offsets。OLANG 字符串 body 和 segment 总长度可以变化；所在 CNF 的后续 tag offsets 可按格式规则重算，但其他资源 payload 必须 byte-identical。

不得使用旧 `semantic_partial`、entity key occurrence 或 reference ordinal 直接移植 ENG/CN 文本。

### STAGEDAT

先解析 JPN STAGEDAT 中的 DAR/RBX/OLANG，再按 JPN 内嵌 reference 翻译。保持 page 数量/顺序、DAR entry 顺序、RBX entity/reference metadata、非目标 entry payload、page offset/key 和原 allocation。

只重建目标内嵌 OLANG 和对应 STAGEDAT page。压缩结果超过原 page capacity 时只报告 overflow，不启用尚未实机验证的 relocation/repacked fallback。

### BRIEFING oEbN

按冻结 JPN lane 的物理 block 和 block 内 text index 翻译。469 个 block / 5,645 行不做文本去重；必须以 `file_id + unique_index` 以及 `stream/block/text` 身份精确写回，不能只按日文内容匹配。

production merge 与专用 `tools/Build-BriefingDat.py` 已完成。builder 从冻结 clean JPN `0076531d.DAT` 开始，固定 block 起点/总长/header，重写 offset table 与 UTF-8/NUL body，并保留 0..3 byte opaque alignment tail。离线结果为 469/469 blocks、5,645/5,645 中文 rows exact，2,292 个非目标 oEbN block 不变，目标 block 外 ciphertext 改动 0；具体交接见 `BRIEFING_BUILD_HANDOFF.md`。

## 五、控制符与文本规则

必须识别并保护 `<R=...,...>`、`<I=...>`、`<->`、`$1`、`$2` 以及其他 `<...>` 和 `$...` 控制内容。

`<R>` 的结构和顺序必须保留；显示字和 ruby 内容可以按照中文显示、英文术语进行本地化。程序参数、图标编号和运行时占位符不得丢失或擅自改写。

所有文本必须是严格 UTF-8，具有正确 NUL terminator，不截断多字节字符，不遗留未经确认的日文假名，并采用符合显示容量和剧情节奏的换行。“没有假名”只属于辅助检查，不代表翻译正确或覆盖完整。

## 六、统一构建流程

旧五类 builder 所需的已审计底层 parser/codec 已收录在 `tools/legacy_support/`，所有正式入口默认使用仓库内副本，不再要求工作区旁存在 `JPVoice_CNText_Experimental/tools`。该目录只提供底层实现；不得直接运行其中的历史 main 或恢复已被否决的映射策略。

1. 从 `translation_worklist.csv` 选择待处理 file_id。
2. 生成 `translations/<resource_class>/<file_id>.csv` 完整 JPN 上下文工作表。
3. 重新组织 MLG_CN/ENG 候选参考，不继承旧行号。
4. 以日文和剧情上下文完成中文翻译。
5. 将确认译文写入 file_id CSV 的 `cn_text`，审核后标记为 `APPROVED`。
6. 旧五类从已批准 file_id CSV 生成 `compiled_translation_manifest.csv`；BRIEFING 从模板与 mapping 确定性生成 `translations/briefing/*.csv`，保持物理 row 身份。
   旧五类 compiler 的结构输入固定为已提交的 `work/luna_translation_templates/reference_masters/`；`translation_worklist.csv` 与 `compiled_translation_manifest.csv` 均从这些 master 和当前 mapping 确定性生成。`build/translation/` 只保存输出，不再要求预存本机缓存作为输入。
7. 检查控制符、UTF-8、NUL、容量和对象覆盖。
8. 从 clean JPN original 重建目标资源。
9. 重建对应 CNF/SLOT/STAGEDAT 页面。
10. 在原 allocation 内重新压缩和加密。
11. 重新 decode/parse，执行结构与文本 round-trip。
12. 生成测试文件并按资源、场景进游戏验证。
13. 更新 worklist 的构建/实机状态；通过后纳入统一 clean-JPN build。

## 七、每次构建的验收标准

每批资源至少必须满足：所有目标 JPN 对象均有明确译文；不依赖未经确认的跨区域 ordinal mapping；record/entity/reference 数量正确；metadata、控制结构、UTF-8/NUL、容量和 parser round-trip 通过；非目标 payload byte-identical；SLOT/STAGEDAT allocation 不变；DAT 总大小符合 fixed-layout 要求；KEY 保持原样；overflow/unresolved 明确列出；游戏内顺序、换行、ruby、字库和后续流程正常。

## 八、已确认基准

### `1C79F2AD`

YPK/GTT 基准：98 records、123 timed segments；multi-segment fixed-frame repack、Miller 三段字幕、alignment slack 和后续 timing 均已通过实机测试。

### `5D3AF52D`

SLOT OLANG 基准：118 JPN references、110 条唯一日文和 110 条上下文翻译；已显式映射回 118 references，entity/reference metadata、同页非目标 payload、原 SLOT allocation、DAT 大小和 KEY 均保持，并已通过实机测试。

## 九、翻译数据结构当前状态

- `translation_worklist.csv` 的 241/241 个 file_id 已完成，file_id 内精确去重译文为 21,041/21,041 行。
- `compiled_translation_manifest.csv` 已将正式译文展开为 91,609 个真实 JPN 对象绑定。
- 36 个 YPK/GTT、1 个 OHD、144 个 SLOT OLANG、14 个 loose OLANG、46 个 STAGEDAT OLANG file_id 均已进入 production。
- BRIEFING 的 469 blocks / 5,645 个 JPN 物理 rows 已进入独立 production 并完成离线构建：FILES 363/4,810，MISSION 106/835；静态检查、clean-JPN build、全量 parser/text/diff round-trip 均 PASS。2026-09-14 实机 smoke test 已证明 FILES/MISSION 能命中中文，但发现长句不自动换行的排版阻塞。
- 29 个初始 GTT hard-overflow record 已按人工审定短译文固化；在后续容量修复后，全体 GTT 为 1,812 normal fit、70 alignment spill、0 hard overflow。
- 统一 SLOT 构建从 clean JPN 合并 742 个 SLOT OLANG、77 个 YPK/GTT 和 4 个 OHD physical occurrences，共 823 个目标 tag、110 pages、0 block overflow。
- 14 个 loose OLANG、123 个 STAGEDAT embedded OLANG entries 以及中文字库已与统一 SLOT 组成 `build/readiness/full_package/`。
- `1C79F2AD` 和 `5D3AF52D` 的 golden 仅保留为历史/结构 regression fixture；production compiler 不读取其中文正文，也不以其覆盖当前 mapping。2026-09-14 已将剩余 16 个 Ruby canonical mismatch 按最终表同步到 JSON mapping，并重建对应 production CSV：587 个 unique JPN Ruby pairs、1,251 个目标 occurrences、`UNMAPPED_PAIR=0`、`RUBY_COUNT_MISMATCH=0`、production canonical mismatch 为 0。

## 十、接下来的执行顺序

当前采用 **MVP 优先**：先形成可构建、可 round-trip、可安装验证的完整六类资源候选；旧五类翻译单元去重模型的重构不作为 MVP 前置条件。

1. 离线阶段已完成：专用 BRIEFING builder、parser/text/diff round-trip，以及包含六类资源和字体的 21 文件统一 readiness 包。
2. 标题 UI ASCII 保留修复已于 2026-09-09 实机通过；后续翻译不得把已确认的纯 ASCII UI 再改成依赖未覆盖中文字形的 CJK。
3. 2026-09-14 已实机确认任务结束无线电命中中文；BRIEFING layout audit 当前仍报告 2 条 FILES 行宽超限，下一步修订对应 mapping 中的显式 LF 换行，先复测 `BRIEFING_FILES_BLOCK_000D00/0` 和 `BRIEFING_MISSION_BLOCK_36DD60/15`，再集中验收剧情字幕、任务结算字段、任务说明、过场字幕、ruby、字库和日语语音。
4. 对发现的问题记录 resource class、file_id、原文/现译文和场景；只修订对应权威 CSV/mapping，再从 production compile 开始全量重建。
5. 实机问题清零后冻结正式发布包和恢复/安装说明。

### MVP 后润色/优化 backlog

旧五类模板目前在每个 `file_id` 内按完全相同的 `jpn_text` 自动聚合，并用多个 reference/entity identity 展开回物理对象。这适合复用大量固定 UI 文本，但把“文本相同”默认等同于“译文必须相同”，不能表达部分同文异境的语气差异。

该问题已记录为 MVP 后优化，不阻塞当前 BRIEFING 构建。MVP 完成并取得实机基线后，再执行：

1. 审计旧五类所有 `source_objects > 1` 聚合行的场景、说话者、前后文和现译文风险。
2. 只拆分确有上下文差异或语义风险的 translation units，避免无收益地重译全部 91,609 个物理对象。
3. 将通用 compiler 的译文主键由隐式 `file_id + jpn_text` 迁移为稳定 object/translation-unit identity；相同译文只能显式复用。
4. 保持对象级 manifest 全覆盖，并对 schema 迁移前后执行逐对象回归，确保 MVP 已验证文本不发生无意变化。

### 2026-09-09 实机回归确认

标题菜单 `NEW GAME`、`LOAD GAME`、`DELETE` 的英文标签已恢复并在 Steam 实机正常显示。
本次修复覆盖全局筛出的 351 条高风险 ASCII UI 文本，采用 JPN 原文作为回退，不改变
JPN 结构、record/reference 数量、时序或 metadata。统一包安装校验为 `VERIFY_MISMATCHES=0`。

该结果只证明标题/UI 英文缺字回归已解决。任务后无线电覆盖又于 2026-09-14 实机确认为中文，但暴露了 BRIEFING 长句不自动换行的新问题。其他中文缺字、结算语义和长文本排版仍按 `V1_INGAME_ISSUES_2026-09-09.md` 继续验收。

核心路线可以概括为：

**以 JPN 为唯一结构与语义主体，以 worklist 管理 file_id，以单个 file_id CSV 保存权威译文，以 compiled manifest 绑定具体 JPN 对象，并从 clean JPN 重建。**
