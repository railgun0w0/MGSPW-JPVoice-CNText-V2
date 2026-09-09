# JPVoice_CNText_V2 技术基础

整理日期：2026-09-05（Asia/Hong_Kong）

## 证据优先级与范围

本文件的优先级从高到低为：

1. 2026-09-05 前用户给出的实机结果、MLG_CN 全量布局分析和 V2 定向构建结果。
2. `D:\GAME\test\MGSPW_GTT_DUMP\20260902-174047\FINAL_REPORT.md` 及其 byte-for-byte 导出。
3. `JPVoice_CNText_Experimental\HANDOFF_TEXT_LOCALIZATION.md`、旧构建报告与代码。
4. `MGSPW_JPVoice_ENText_Phase2\evidence_milestone1\MILESTONE1_REPORT.md` 及严格 RBX 导出。
5. 尚无实机或独立复核支撑的旧推断。

发生冲突时，高优先级证据覆盖低优先级结论。本文记录格式与构建基础；是否生成或安装补丁仍以每次任务的明确授权为准。

## 全项目翻译权威与参考顺序

以下规则适用于整个日语语音 + 中文字幕补丁，不限于 YPK/GTT；后续处理 OHD、OLANG、STAGEDAT、loose language resources 及其他已可靠解析的日文文本时均须遵守：

1. 目标 JPN 资源中的日文原文是语义第一权威；目标 JPN 文件的 record/item 顺序、控制结构、容量和容器布局是结构第一权威。
2. 翻译应先根据日文原文、同一对象的上下文、人物语气和场景直接确定中文含义。
3. 现成 MLG_CN 汉化只作为辅助参考，可借鉴已验证的术语、专名和简洁表达；不得在与日文冲突时覆盖日文含义，也不得把 MLG/ENG 的物理结构复制到 JPN。
4. ENG 原文只用于日文歧义消解或对照检查，优先级低于 JPN；不能因英文措辞不同而改写明确的日文含义。
5. 若 MLG_CN 存在多个 payload/文本 variant，翻译参考默认只取按现有导出/枚举顺序得到的第一个 variant；其余 variant 不进入常规翻译选择流程。该简化只影响辅助译文来源，最终语义与结构仍以 JPN 为权威。
6. 最终中文必须回到目标 JPN 对象逐项复核：语义、分段/条目身份、控制符、容量和 round-trip 均通过后才能构建。

因此，全项目的翻译链是：`JPN 原文直接翻译 -> MLG_CN 辅助参考 -> ENG 必要时消歧 -> 以 JPN 复核并按 JPN 结构写回`。跨区域 mapping 只用于寻找参考译文和覆盖审计，不授予结构身份。

本轮还进行了只读/临时目录 round-trip 抽查：JPN KEY 2,139 项无修改重编码 byte-exact；SLOT page 88 解码、CNF no-op rebuild、页重编码解码均通过；14 个 loose OLANG（18,666 references）解密后按原文件名重加密全部 byte-exact；STAGEDAT 557 页可读，page 31 重编码解码通过。游戏源文件没有写入。

# VERIFIED_REUSABLE

## 1. PC filename-seeded outer transform

- seed 取文件名第一个 `.` 之前的 ASCII stem，逐字节：`seed = u32(seed * 0x2356F + byte * 0x1D35)`。
- 伪随机流为旧工具中的 624-word PC stream；每个 word 再异或 `0xB9D3018F`。
- 文件起点处理等价于先跳过 `0x14` bytes；处理文件内续段时还要加该续段的 file offset。
- 变换为对称 XOR，同一 key filename 再执行一次即可还原。
- 已在 loose OLANG、KEY、STAGEDAT/SLOT 页面流程和 `OuterCrypt` 的既有输出中交叉验证。

可提升实现：`Patch-StageDatPage.py` 的 `filename_seed` / `PcStream` / `outer_transform`，以及 `OuterCrypt.cpp`。V2 应只保留一份带 test vectors 的公共实现。

## 2. SLOT DAT/KEY 固定布局解包与回包

### KEY

- PC HD KEY 经 outer transform 后为：12-byte salts（`<III>`）+ N 个 20-byte entries（`<IIiII>`）。
- entry 的 `first` / `last` 低 20 bits 是 0x1000-sector 索引：
  - `start = (first & 0xFFFFF) * 0x1000`
  - `end = (last & 0xFFFFF) * 0x1000`
  - `capacity = end - start`
- 高位、signed hash 与两个 unknown 字段均须原样保留。
- JPN `002aba34.KEY` 为 42,792 bytes / 2,139 pages；MLG KEY 为 42,752 bytes / 2,137 pages。
- no-op `decode_key -> encode_key` 已 byte-exact 验证。

### SLOT page

- 每页在其 KEY allocation 中独立重置 outer stream，然后执行 inner XOR stream。
- inner 初值：`page_key = saltA ^ saltB`；`keyA = u32(((page_key ^ 0x6576) << 16) | page_key)`；`keyB = u32(page_key * saltC)`；每 4 bytes 后 `keyA = u32(keyA * 0x02E90EDD + keyB)`。
- 解密页头为 16 bytes `<HHIII>`：两个保留字段、padding、compressed_size、decompressed_size；正文是 zlib stream。
- 固定布局回包：重算 compressed/decompressed size，压缩流和页头写入原 capacity，剩余 allocation 清零后执行 inner + outer transform。
- 修改页必须 decode-back 等于目标明文；DAT 总大小和全部 page start/end 不变时，原 JPN KEY 可直接原样复制。

这是已验证的 fixed-layout page repack。它不等价于“可任意扩容并重写 KEY”；完整 relocation 见待验证项。

## 3. SLOT page 内的 HD CNF

- header：`<II>` = tag count + table pad。
- 每个 tag：16 bytes `<IIII>` = file_id、pad_a、offset、pad_b。
- `kind = file_id >> 24`，低 24 bits 为资源 hash/id。
- CNF 数据区从 `align_up(8 + count * 16, 0x1000)` 开始；表尾到数据区之间的原 padding 必须保留。
- `0x00/0x7D/0x7E/0x7F` 是控制 tag，不作为普通文件段导出。普通段大小由下一个 tag offset 减当前 offset 得出。
- rebuild 时按原 tag 顺序拼接段、重算普通 tag offsets，并把 `0x7F` 的 offset 更新为重建后 region size；pad 字段原样保留。
- 空 replacement 的 `parse_cnf -> rebuild_cnf` 已在旧构建与本轮 page 88 抽查中 byte-exact。

注意：CNF builder 不应擅自给每个 segment 加通用对齐；replacement 必须已经携带该格式自身要求的 padding。GTT 的 16-byte record alignment、RBX segment 的 padding都由对应格式层负责。

## 4. Compression

- SLOT 与 STAGEDAT 均使用 zlib wrapper，不是 raw DEFLATE。
- SLOT 可尝试 zlib level 9 的 default/filtered/RLE/Huffman/fixed 策略，取能解回原数据且尺寸最小者；不足时旧工程使用 `zopfli --zlib --i15`。
- 任何压缩器都只是容量优化手段；正确性由解压 round-trip 和 allocation fit 决定，不要求压缩字节与原版一致。
- SLOT 容量计算必须包含 16-byte page header。
- STAGEDAT page plaintext 为 `u32 decompressed_size + zlib_stream`，table 的 size 是该 packed page 的有效长度。

## 5. RBX / OLANG

### Loose OLANG outer layer

- 文件若已以 `RBX\0` 开头可直接解析；否则按目标文件名 seed 执行 PC outer transform。
- 重加密必须使用最终目标文件名，不是源文件名。
- `Rekey-Olang` 的密码学动作（解密、修改 RBX id、按新文件名重加密）本身可复用；“通过 rekey 直接完成区域汉化”这一旧策略不可复用。

### RBX structure

- magic 为 `RBX\0`；RBX id 在 `+0x04`。
- `+0x10/+0x14/+0x18/+0x1C` 是四个 section-related u32。通用解析器应把第二个值作为 entity table offset；在已审计 loose corpus 中它等于首个 section offset + 8。
- entity 为 8 bytes `<IHH>`：key、reference_index、reference_count。
- reference 为 12 bytes `<III>`：numeric language/reference key、body-relative string offset、flag。
- body 是严格 UTF-8、NUL-terminated strings；旧重建器按 2-byte boundary 放置新字符串。
- 安全 rebuild 只保留目标 RBX 的 header/aux/entity 区、reference language key 与 flag，重算每个 reference 的 body offset 和字符串 body。
- RBX reference 可以合法指向原生空字符串。翻译 manifest 只需覆盖全部非空 JPN references；builder 必须原样保留空引用，且禁止遗漏或清空任何非空引用。
- rebuild 后必须重新解析并逐项验证文本、entity spans、language keys、flags、NUL、UTF-8 和 body bounds。

严格导出曾覆盖 100 个 RBX 文件且 0 parse failure：JPN loose 14 文件/18,666 references；MLG loose 14 文件/18,876 references；两组既有 init extraction 各 36 个 RBX。14 个 JPN loose OLANG 的 decrypt/re-encrypt 本轮再次 byte-exact。

观察到的语言 key `0xD0E/0xD32/0xD45/0xD94/0xDB0/0xED0` 分别对应 en/fr/de/it/ja/es；这是大样本语义推断，数值与表记录是事实。V2 仍应保留未知 key，不把六语言序列当所有 RBX dialect 的硬编码前提。

### `5D3AF52D` 首个 V2 SLOT OLANG 实机基准

- 目标为 clean JPN SLOT 的 page 1864/tag 2/file_id `5D3AF52D`；原资源有 118 entities、118 references、110 条去重日文。
- JPN 是语义与结构权威。现成 MLG_CN 同场景资源只有 91 references，且条目存在拆分、合并和顺序差异；因此没有按 MLG/ENG reference index 直接移植。
- 翻译先按 JPN reference 的完整日文、相邻文本、scene/entity 上下文人工确定；MLG_CN 只辅助术语和措辞。110 条译文保存在上下文工作表，再按完整 JPN 文本映射回全部 118 个 reference；重复日文共享同一译文。
- rebuild 保留 JPN header/aux/entity bytes、entity table、reference 数量、每个 reference 的 language key 与 flag；只重建 UTF-8/NUL 字符串 body 和 body-relative offsets。
- ruby/control markup 的结构和出现顺序必须保留；`<R>` 的显示字与注音内容可本地化为中文/英文，`<I=...>`、`$1` 等程序参数不得改写或丢失。
- 目标 OLANG segment 由 7,344 bytes 变为 6,416 bytes；OLANG 允许字符串 body 长度变化，不要求 segment 固定大小。CNF 按原 tag 顺序重算后续 offsets，同页所有非目标 resource payload bytes 保持完全一致。
- SLOT page 的原 allocation 保持 6,266,880 bytes，压缩后无 overflow；DAT 总大小保持 543,858,688 bytes，原 KEY byte-identical。
- rebuild 后重新解码并解析：118/118 中文逐项一致，entity、reference metadata 和控制结构全部通过。该 DAT 已安装并由用户实机确认场景、字幕和后续流程正常。

这证明了可靠的 SLOT OLANG 路线是：`JPN 上下文工作表 -> 完成人工翻译 -> 明确映射回全部 JPN references -> 仅重建 RBX body -> 重建所在 CNF page -> 原 allocation 内编码 -> parse/decode round-trip -> 实机验证`。

## 6. DAR 与 STAGEDAT

### DAR

- `u32 file_count`。
- 每项：ASCII filename + NUL；对齐到 4；`u32 size`；对齐到 16；payload；单个 trailing NUL。
- rebuild 保留 entry 顺序和所有非目标 payload；严格 parser 还要求剩余尾部只有零。

### STAGEDAT container

- `009645fa.PDT` 已确认 557 pages。
- 前 40 bytes 为 header；outer offset=0。前 12 bytes 是 salts，其余 header 进入连续 inner stream；page_count 是 plaintext `+0x18` 的 u16。
- page table 从 file offset 40 开始，共 `page_count * 12` bytes；每项 `<III>` = packed size、key、offset。table 的 outer stream 从 file offset 40 继续，inner key 从 header tail 延续。
- 每个 packed page 自己重置 outer 与 inner stream，解出 `u32 decompressed_size + zlib_stream`。
- fixed-layout patch 只改 table 中该 page 的 size 和原 offset 处的 packed bytes；offset/key/其他 entry 保持不变，并受下一个 page offset 给出的 capacity 限制。
- 旧正式 JPN STAGEDAT 构建实际走 `original_offsets`：14 个 text pages、123 个 embedded RBX、17,478 references、0 overflow。安装后曾从游戏目录解包读回中文。这条 original-offset 路径可作为 V2 基线。

## 7. YPK / GTT：新的强制模型

### 已确认事实

- 一个 GTT record 可以包含多个 timed subtitle；`segment_count` 不是可忽略字段。
- record framing 至少包含：`GTT\0`、`segment_count`（+0x04）、`header_size`（+0x08）、`record_size`（+0x0C）；下一个 record 从 `align_up(record_offset + record_size, 16)` 开始。`record_size` 给出 nominal record 末端，但 text boundary 可以指向该末端至 16-byte aligned 末端之间的物理 slack。
- header 内含 text boundaries，所以既不能保留整个旧 header，也不能只改 `record_size`。
- Miller 回归基准：JPN file_id `1C79F2AD`，page 88/tag 14/record 0，`segment_count=3`，payload boundaries 为 `0-51, 51-96, 96-136`。三段分别独立 NUL-terminated，multi-string 中文替换已通过实机。
- ENG original -> working ENG_CN 已全量复核 5,878 个 modified GTT records：`segment_count/header_size/record_size/aligned_size/YPK size` 全部 0 变化。
- 对现成 MLG_CN 补丁进行独立 canonical/variant 布局分析后，语料覆盖 36 个 unique ENG YPK、48 个去重 CN payload variants、3,807 对对应 records：
  - `SAME_FRAME_FIT=3,647`
  - `ALIGNMENT_SPILL=160`
  - `FRAME_GREW=0`
  - `FRAME_SHRANK=0`
  - `SAME_FRAME_APPARENT_OVERFLOW=0`
  - `TOPOLOGY_CHANGED=0`
  - `RECORD_COUNT_CHANGED=0`
- 上述 48 个 CN variants 中，整个 YPK size 增长为 0；alignment spill 最多使用 9 bytes。就已观察到的现成可工作补丁而言，超过 nominal capacity 的文本会使用原 aligned slot 的 slack，没有发现扩大 record、移动后续 record或扩大 YPK 的实例。
- JPN canonical 导出当前覆盖 36 个去重 YPK、1,882 个 records、2,136 个 timed segments；均由 `parse_gtt_multi()` 按 `segment_count` 和 header boundaries 解析，不使用首 NUL 推断句数。

### V2 正确 repack 契约

1. 以目标 record 的 timing / trigger / style 和物理 record slot 为权威。
2. 中文 timed strings 按 segment 顺序编码为 UTF-8 + NUL，连续放入 payload。
3. 按每个新字符串的真实 start/end 重算 header 内全部 text boundaries；只保留非文本边界的 timing/trigger/style 字段。
4. 未使用的 payload/record allocation 清零。
5. `nominal_capacity = record_size - header_size`；`hard_capacity = aligned_capacity = align_up(record_size, 16) - header_size`。text bytes 和 boundaries 可以使用两者之差形成的 alignment slack，但不得侵入下一 record。
6. `record_size` 禁止修改。使用 alignment slack 不等于扩大 `record_size`，也不得按新文本实际长度回写 `record_size`。
7. segment_count、header_size、record_size、aligned_size、record 起止位置和整个 YPK size 必须全部保持不变；这与 working ENG_CN 的 5,878 条 modified records 全量结果一致。
8. 构建后重新解析，验证每段边界位于 aligned physical slot 内、段数相等、字符串逐段相等、非 boundary header 字段未变、所有 record offsets 和 YPK size 未变。

V2 需要独立的 `parse_gtt_multi` / `repack_gtt_multi`；旧 `decode_gtt_text` / `build_gtt_record` 不得被包装后继续使用。

### `1C79F2AD` 首个 V2 定向构建

- 翻译权威直接来自 JPN canonical YPK，不经过 ENG/CN/JPN mapping。
- 该 YPK 有 98 records / 123 timed segments；所有 record 顺序、segment_count、header_size、record_size、aligned_size、timing/metadata 和物理 offsets 保持不变，只改 UTF-8 text 与对应 boundaries。
- 97 records 落在 nominal capacity；1 record（record 52）为 alignment spill：`required=29`、`nominal_capacity=26`、`hard_capacity=40`，使用 3 bytes slack。
- `HARD_OVERFLOW=0`。rebuild 后由 `parse_gtt_multi()` 逐段 round-trip，123 段中文全部一致。
- JPN lane 中该 file_id 有 2 个 byte-identical physical occurrences，位于 page 88 与 page 94；同一份 rebuilt YPK 写入两处。
- 两个受影响 SLOT pages 均在原 allocation 内重编码成功，`PATCHED_BLOCKS=2`、`BLOCK_OVERFLOW=0`；DAT 总大小和原 KEY 不变。
- 测试 DAT 已部署到 Steam 的 JPN 资源目录。用户已实机确认 Miller record 0 的三段字幕和后续字幕 timing 正常。
- ruby 采用 `<R=中文显示字,ENGLISH TERM>`：本 YPK 已统一为 `着陆/LANDING`、`操作/ACTION`、`自动瞄准/AUTO AIM`、`敌兵/LIVE TARGET`、`地图/MAP`。`<R>` 结构保持不变；`<I=...>`、`$1` 等程序参数仍必须逐字保留。
- 首次测试中 `<R=地图,マップ>` 的 `図` 显示方框，确认是中文 XPR 字库缺少日文字形与 ruby 显示字未本地化所致，不是 GTT boundary/NUL 问题。安装已验证的三文件中文字库并将 ruby 显示/注音本地化后，最终版本重新构建。
- 原始/最终 YPK 已冻结在 `tests/fixtures/gtt_1C79F2AD`；`test_gtt_1C79F2AD_golden.py` 会逐 record 重放 repacker，验证全部 98 records / 123 segments、固定物理布局和 record 52 alignment spill。

## 8. OHD

旧语料与构建报告稳定支持以下结构：16-byte OHD header；count 在 `+0x08`；每项 128 bytes；文本字段从 record `+0x3C` 开始（68-byte field）。安全写法是保留目标 OHD header 和每项前 60 bytes，只写 `UTF-8 + NUL + zero padding`，并保持文件总长和 record count。

该低层 parse/rebuild 已做结构 round-trip，且旧报告记录 1 个 canonical OHD、4 个 occurrence 的 metadata preservation。它没有受到 multi-string GTT 结论直接推翻；但 OHD 的跨区域语义映射和实机覆盖仍列入待复核。

## 9. Region facts

- JPN 运行资源在 `mgspw\JPN`。
- 英文原版与 working ENG_CN 的主资源在 `mgspw\MLG`，不是 `EXLANG`。
- JPN 主 SLOT 为 2,139 pages；MLG 为 2,137 pages。两个区域不能按同 page index、固定 page delta 或 record ordinal 自动视为同一语义。
- Miller 已证明同一事件可出现在不同 file_id/lane：JPN `1C79F2AD` 与 working ENG_CN 实际修改的 `1C79F20B` 不能仅凭 page/tag 强行配对。
- 区域目录选择是事实；跨区域资源身份必须另有 file structure、完整 multi-string 内容、metadata 与人工/实机证据。

# OBSOLETE_OR_WRONG

## GTT / YPK

- `payload.split(b"\0", 1)[0]` 单字符串模型错误。
- 旧 `build_gtt_record(header, text)` 把 record 拍平成单段、只重写 record_size 的模型错误。
- “完整保留 JPN GTT header”错误；text boundary 字段必须随新文本重算。
- 把 `segment_count` 只当身份元数据、却只提供一个中文字符串的 `Build-JpnSlotVoiceByMetadata.py` 路线错误。
- `Build-JpnSlotNativeVoiceText.py`、`Build-JpnSlotVoiceByMetadata.py` 的 GTT builder 禁止进入 V2。
- `Analyze-GttAlignment.py`、`Audit-SlotNativeVoiceText.py`、`Extract-AllJpnText.py` 中所有 first-NUL GTT 解码结果不能作为句数、正文或余量事实。
- “日版首 UTF-8 lead byte 被省略”的旧解释不能继续当格式事实。至少在新 multi-segment parser 按 boundary 重新解释前，`jpn_elided_lead` / `zero_prefix` 分类全部撤销。
- 旧坏补丁把 Miller 3 段压成 1 段、record 232 -> 135，同时保留旧 boundaries，已经由 byte diff 和实机伪字符/后续语音异常反证。

## lane / page / region mapping

- `page % 6 == 0` 是活动 lane：错误。
- `page % 6 == 4` 是活动 lane：不能推广为事实。
- 把 lane 0 文本复制到其余五 lane：废弃。
- 固定 `ENG page + 4 = JPN page`：禁止作为身份规则。
- 仅按六页分组 + record ordinal、或仅按 page/tag 配对跨区域 GTT：禁止。
- `Build-JpnSlotAllVoiceLanes.py` 的策略与报告、`MGSPW_GTT_PREFLIGHT` 的 `jpn_authority_plus_4` 输出不得作为 V2 映射输入。
- 旧 metadata identity 使用 single-string suffix，因此即使声明“不用 lane/ordinal”，也不足以证明 multi-segment record 身份。

## OLANG / coverage claims

- loose OLANG 不是单语言包；直接把“英文包”rekey 成日版文件的叙述错误。它们是多语言 RBX。
- `(entry_id, occurrence)` 在区域差异文件中会因重复 key 和插入项错位，不能单独配对。
- 旧 `semantic_partial` 实际按 entity key、重复 occurrence 和 reference ordinal 配对，并不构成语义匹配；`5D3AF52D` 已证明它会把不同台词错配，禁止作为 V2 自动翻译映射。
- MLG/ENG 与 JPN 的 reference 数量相同或相近，也不授予逐 index 身份。现成译文只能进入 translation memory，最终必须回到完整 JPN 原文和上下文人工确认。
- “剩余假名 0”只证明被扫描槽位没有假名，不证明所有可见文本已覆盖，也不证明运行时读取该副本。
- 旧 `slot-inventory-full-final.json` 是中间产物清单，不代表最终安装状态。

## 旧构建入口

- `Build-ExperimentalPayload.ps1` 混合了已废弃 GTT、动画和旧区域映射，不得作为 V2 build entrypoint。
- 旧 20-file payload、旧安装脚本和旧 build 报告只能作证据，不得复制为 V2 基线。

# UNKNOWN_NEEDS_REVALIDATION

## DAT/KEY/CNF

- SLOT page 扩容、重新排布全部 pages、更新 KEY first/last 的完整 repack 尚未验证。
- KEY signed hash 与两个 unknown 字段的生成语义未知；目前只验证“保留它们”的 fixed-layout 路径。
- CNF control tags（0x7D/0x7E/0x7F）的全部运行时语义、所有 kind 扩展名语义仍不完整。
- 除主 SLOT `002aba34.DAT` 外的第二个 DAT，以及其余 PDT/CMF 是否采用相同变体，不能外推。

## GTT / YPK

- GTT header 中每个 boundary 副本的完整通用 schema，需要用 5,878-record diff 产物生成字段级统计后再固化；Miller 的 3 段布局不能直接推广到所有 segment_count。
- alignment slack 已由 MLG_CN 的 160 条记录和 V2 JPN `1C79F2AD` record 52 的固定布局构建覆盖；后者仍需在游戏内实际触发并确认显示与后续 record 连续性。`record_size` 在 V2 中始终保持原值。
- ENG/working ENG_CN 的 5,878 条差分怎样可靠映射到全部 JPN records 尚未完成。V2 不接受 page/lane shortcut。
- JPN-only records、区域 record-count 差异、多 variant CN records、ruby/control tags 的逐段映射仍需证据化。
- 旧 preflight 的 topology、overflow 与 anomaly 数字依赖已禁用的 +4 mapping/旧 parser，应全部重跑。
- file_id 是否可跨 page 唯一标识语义、相同 file_id 多 variant 如何区分，需以 segment hash + 完整结构登记。

## OHD

- OHD 的 trigger/style 字段语义、JPN/MLG record 对应关系、是否存在非 128-byte dialect，以及运行时真正读取的 occurrence 需要独立 diff 和实机复核。

## OLANG / region mapping

- 11 个同名 loose OLANG byte-identical 是静态事实；三个 region-specific pairing 只部分完成 exact sequence alignment。
- `00c79b17 <-> 00cd740b` 没有 exact terminal entry，旧人工映射必须重新审查。
- 旧 SLOT OLANG mapping JSON、manual/auto overrides、wrap overrides 都与旧页/引用索引绑定；V2 使用前必须重新解析目标并验证 identity、原文和控制标记。
- `5D3AF52D` 已验证“JPN 上下文翻译工作表 + 118-reference 显式回填 + RBX body rebuild”路线，但这一成功不能自动证明其余 SLOT/loose/STAGEDAT OLANG 的旧映射正确。其余资源仍需各自生成 JPN 工作表并通过同一验收门。
- 运行时具体界面选择哪个 loose/SLOT/STAGEDAT 副本仍应以实机路径或访问证据确认。

## STAGEDAT

- 旧 `repacked_0x800_alignment` overflow fallback 在当前正式输出中没有被使用；其运行时有效性、lookup/index 关系和最终文件尾部规则需要单独验证。
- 既有 init extraction 曾漏掉 `data.cnf` 声明的 `init.rlc`，所以 Chrysalis init 输出只能视为 partial extraction。
- 其他 74 个 PDT、37 个 CMF、未知 STAGEDAT/DAR dialect 尚未统一验证。

## 当前决定与实施方向

最终方向确定为：从 clean JPN original 构建完整“日语语音 + 简体中文字幕/文本”补丁。不再考虑让英文汉化版调用日语语音包，也不再把 ENG/MLG_CN 的结构直接移植到 JPN。V2 已不再处于“继续证明基础格式”的阶段；`1C79F2AD` 已验证 fixed-layout multi-segment GTT，`5D3AF52D` 已验证 JPN-authoritative SLOT OLANG。后续重点是按已验证契约扩大真实中文覆盖。

统一原则为：

1. JPN 原文决定含义，JPN 对象决定结构；MLG_CN 只作 translation memory，ENG 只在必要时消歧。
2. `translation_worklist.csv` 只管理 file_id 级进度；单个 `translations/<resource_class>/<file_id>.csv` 是翻译权威；所有批准文件生成 `compiled_translation_manifest.csv`，再显式回填每个 JPN record/reference/timed segment。全局日文去重表只作术语和候选参考目录。
3. 每次只改授权的目标 payload；其余 payload 必须 byte-identical。容器 offsets 可按格式规则重算，但 page allocation、DAT 总大小和 KEY 保持不变，除非未来另行验证 relocation。
4. 每个资源都要通过 parser round-trip、metadata/control 检查、容器 decode-back 和 allocation fit；中间批次不安装，全部资源完成后统一实机验证，不再为已确认的底层格式反复写调查脚本。

正式实施顺序为：

1. 三层翻译数据已经落地：241 行 file_id 管理 worklist、68 个已批准 SLOT OLANG file_id 权威 CSV（2,119 条唯一译文）、2,351-reference compiled manifest；旧 13,676 条全局去重文本保留为参考 catalog。
2. `core/rbx.py`、manifest 驱动的通用 SLOT OLANG builder 与 `5D3AF52D` golden fixture 已完成；通用输出的 rebuilt segment SHA-256 与实机通过版本同为 `5ED9FD050F9CD38278BEEA4DAE2D9439C5C472806C89DBF811FF62B28469BF6C`。
3. SLOT OLANG `batch_001` 已新增 10 个 file_id、20 个 references；clean-JPN 批量构建覆盖 11 个资源/11 pages、0 block overflow。新增批次尚未安装或实机验收。
4. SLOT OLANG `batch_002` 又新增 10 个 file_id、75 个 canonical references。当前累计 21 个资源、196 条唯一译文、213 个 canonical reference bindings；manifest 的 occurrence 列表展开为 75 个物理 payload、488 个实际 references、67 pages，0 block overflow、0 非目标 payload 变化。
5. SLOT OLANG `batch_003` 又新增 5 个 file_id、55 个 canonical references。当前累计 26 个资源、250 条唯一译文、268 个 canonical bindings；clean-JPN 构建覆盖 80 个物理 payload、543 个实际 references、70 pages，0 block overflow、0 非目标 payload 变化。
6. SLOT OLANG `batch_004` 又新增 4 个 file_id、67 个 canonical references。当前累计 30 个资源、315 条唯一译文、335 个 canonical bindings；clean-JPN 构建覆盖 84 个物理 payload、610 个实际 references、72 pages，0 block overflow、0 非目标 payload 变化。
7. SLOT OLANG `batch_005` 又新增 4 个 file_id、139 个 canonical references。当前累计 34 个资源、372 条唯一译文、474 个 canonical bindings；clean-JPN 构建覆盖 90 个物理 payload、797 个实际 references、72 pages，0 block overflow、0 非目标 payload 变化。
8. SLOT OLANG `batch_006` 又新增 3 个 file_id、63 个 canonical references。当前累计 37 个资源、435 条唯一译文、537 个 canonical bindings；clean-JPN 构建覆盖 93 个物理 payload、860 个实际 references、74 pages，0 block overflow、0 非目标 payload 变化。
9. SLOT OLANG `batch_007` 又新增 3 个 file_id、71 个 canonical 非空 references。当前累计 40 个资源、504 条唯一译文、608 个 canonical bindings；clean-JPN 构建覆盖 96 个物理 payload、943 个实际 references、77 pages，0 block overflow、0 非目标 payload 变化。
10. SLOT OLANG `batch_008` 又新增 3 个 file_id、81 个 canonical 非空 references。当前累计 43 个资源、582 条唯一译文、689 个 canonical bindings；clean-JPN 构建覆盖 99 个物理 payload、1,027 个实际 references、80 pages，0 block overflow、0 非目标 payload 变化。
11. SLOT OLANG `batch_009` 又新增 3 个 file_id、94 个 canonical 非空 references。当前累计 46 个资源、676 条唯一译文、783 个 canonical bindings；clean-JPN 构建覆盖 102 个物理 payload、1,121 个实际 references、82 pages，0 block overflow、0 非目标 payload 变化。
12. SLOT OLANG `batch_010` 又新增 3 个 file_id、109 个 canonical 非空 references。当前累计 49 个资源、785 条唯一译文、892 个 canonical bindings；clean-JPN 构建覆盖 105 个物理 payload、1,230 个实际 references、84 pages，0 block overflow、0 非目标 payload 变化。
13. SLOT OLANG `batch_011` 又新增 2 个 file_id、94 个 canonical 非空 references。当前累计 51 个资源、879 条唯一译文、986 个 canonical bindings；clean-JPN 构建覆盖 107 个物理 payload、1,345 个实际 references、85 pages，0 block overflow、0 非目标 payload 变化。
14. SLOT OLANG `batch_012` 又新增 3 个 file_id、134 个 canonical 非空 references。当前累计 54 个资源、963 条唯一译文、1,120 个 canonical bindings；clean-JPN 构建覆盖 110 个物理 payload、1,499 个实际 references、86 pages，0 block overflow、0 非目标 payload 变化。
15. SLOT OLANG `batch_013` 又新增 2 个 file_id、106 个 canonical 非空 references。当前累计 56 个资源、1,062 条唯一译文、1,226 个 canonical bindings；clean-JPN 构建覆盖 112 个物理 payload、1,605 个实际 references、87 pages，0 block overflow、0 非目标 payload 变化。
16. SLOT OLANG `batch_014` 又新增 2 个 file_id、157 个 canonical 非空 references。当前累计 58 个资源、1,176 条唯一译文、1,383 个 canonical bindings；clean-JPN 构建覆盖 114 个物理 payload、1,771 个实际 references、89 pages，0 block overflow、0 非目标 payload 变化。
17. SLOT OLANG `batch_015` 又新增 2 个 file_id、142 个 canonical 非空 references。当前累计 60 个资源、1,307 条唯一译文、1,525 个 canonical bindings；clean-JPN 构建覆盖 116 个物理 payload、1,913 个实际 references、90 pages，0 block overflow、0 非目标 payload 变化。
18. SLOT OLANG `batch_016` 完成 `5D3AFE2D` 的 78 个 canonical 非空 references。当前累计 61 个资源、1,384 条唯一译文、1,603 个 canonical bindings；clean-JPN 构建覆盖 117 个物理 payload、1,991 个实际 references、91 pages，0 block overflow、0 非目标 payload 变化。
19. SLOT OLANG `batch_017` 完成 `5D3AF92D` 的 88 个 canonical references（81 条唯一译文）。当前累计 62 个资源、1,465 条唯一译文、1,691 个 canonical bindings；clean-JPN 构建覆盖 118 个物理 payload、2,079 个实际 references、92 pages，0 block overflow、0 非目标 payload 变化。
20. SLOT OLANG `batch_018` 完成 `5D3AF54D` 的 115 个 canonical references。当前累计 63 个资源、1,580 条唯一译文、1,806 个 canonical bindings；clean-JPN 构建覆盖 119 个物理 payload、2,194 个实际 references、93 pages，0 block overflow、0 非目标 payload 变化。
21. SLOT OLANG `batch_019` 完成 `5D3AF96D` 的 101 个 canonical references。当前累计 64 个资源、1,681 条唯一译文、1,907 个 canonical bindings；clean-JPN 构建覆盖 120 个物理 payload、2,295 个实际 references、94 pages，0 block overflow、0 非目标 payload 变化。
22. SLOT OLANG `batch_020` 完成 `5D3AFD0D` 的 120 个 canonical references（119 条唯一译文）。当前累计 65 个资源、1,800 条唯一译文、2,027 个 canonical bindings；clean-JPN 构建覆盖 121 个物理 payload、2,415 个实际 references、95 pages，0 block overflow、0 非目标 payload 变化。
23. SLOT OLANG `batch_021` 完成 `5D3AFD2D` 的 110 个 canonical references（106 条唯一译文）。当前累计 66 个资源、1,906 条唯一译文、2,137 个 canonical bindings；clean-JPN 构建覆盖 122 个物理 payload、2,525 个实际 references、96 pages，0 block overflow、0 非目标 payload 变化。
24. SLOT OLANG `batch_022` 完成 `5D3AFDED` 的 103 个 canonical references。当前累计 67 个资源、2,009 条唯一译文、2,240 个 canonical bindings；clean-JPN 构建覆盖 123 个物理 payload、2,628 个实际 references、96 pages，0 block overflow、0 非目标 payload 变化。
25. SLOT OLANG `batch_023` 完成 `5D3B058D` 的 111 个 canonical references（110 条唯一译文）。当前累计 68 个资源、2,119 条唯一译文、2,351 个 canonical bindings；clean-JPN 构建覆盖 124 个物理 payload、2,739 个实际 references、97 pages，0 block overflow、0 非目标 payload 变化。
13. 中间批次继续做翻译、clean-JPN 构建和自动结构验收，全部资源完成后统一安装并实机验证。
14. 使用相同 JPN-first 工作表流程处理 loose OLANG。
15. 处理 OHD：只写固定文本字段，保持 record count、metadata 和文件尺寸。
16. 处理 STAGEDAT embedded OLANG：沿用 original-offset fixed-layout page 路径，overflow 不启用未验证的 relocation fallback。
17. YPK/GTT 继续使用已验证的 `gtt_multi` fixed-slot 路线；与以上资源汇总后，从 clean JPN 生成统一候选补丁并做场景覆盖验收。

旧 ENG↔JPN mapping、page/lane 规律和 `semantic_partial` 可继续用于寻找候选参考或发现覆盖缺口，但不再决定 JPN 对象身份，也不阻塞直接从日文翻译。
