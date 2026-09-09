# 旧工程工具审计

状态含义：

- `PROMOTE_CORE`：底层格式/密码/round-trip 逻辑可提取到 V2，但仍要去硬编码并加测试。
- `PARTIAL`：只有明确列出的部分可用；main workflow 或映射策略不能照搬。
- `QUARANTINE`：包含已被反证的 GTT 或 lane/page 模型，不得导入 V2。
- `REFERENCE_ONLY`：只作为样本、报告或第三方对照。
- `OUT_OF_SCOPE`：本轮文本容器基础不纳入。

## 可提升或部分提升

| 旧资产 | 状态 | V2 可用部分 | 禁止/限制 |
|---|---|---|---|
| `tools/Patch-StageDatPage.py` | PROMOTE_CORE | PC outer/inner crypto；STAGEDAT header/table/page decode/encode；fixed-offset page patch；diff-range audit | main 只支持单页；不得据此声称 overflow repack 已验证 |
| `tools/Build-JpnSlot.py` | PARTIAL | KEY decode/encode；SLOT page decode/encode；CNF parse/rebuild；fixed-layout writeback | main 的 110-page hard count、nearby regional page matching、允许 kind 政策不是通用事实 |
| `tools/Build-JpnSlotFullOlang.py` | PARTIAL | `encode_page_best`；保留 JPN entity/reference metadata 的 RBX text body rebuild/verification | `merge_semantic_partial` 只是 entity key occurrence + reference ordinal 配对；已被 `5D3AF52D` 的错配反证，禁止进入 V2 mapping |
| `tools/Build-JpnInitCache.py` | PARTIAL | DAR parse/build；RBX parse/build；metadata preservation checks | 六个 hardcoded targets 与 JPN/`_en` 对应不应进入 core |
| `tools/Build-JpnLooseOlang.py` | PARTIAL | filename crypto；loose RBX decrypt/encrypt；reference-preserving rebuild | hardcoded MAP、anchor heuristics、manual overrides 需重验；kana=0 不是 coverage proof |
| Phase2 `tools/export_olang_rbx.py` | PROMOTE_CORE | 最严格的只读 RBX bounds/coverage/UTF-8/NUL/body-gap exporter | language labels与 terminal role仍要明确标为 inference |
| `tools/Build-JpnStageDatText.py` | PARTIAL | 557-page遍历；DAR/RBX局部替换；original-offset writer | entity mapping/manual overrides需重验；0x800 repack fallback 未获运行时验证 |
| `tools/Extract-AllJpnText.py` | PARTIAL | SLOT/CNF、loose RBX、STAGEDAT/DAR 与 generic UTF-8/UTF-16 扫描框架 | GTT branch 采用 first-NUL，必须删除后接入新 parser |
| `tools/Inventory-SlotOlang.py` | PROMOTE_CORE | SLOT OLANG 只读 inventory | 结果只能说明静态内容 |
| `tools/Query-SlotInventory.py` | PROMOTE_CORE | 对 inventory 的查询 | 依赖输入 inventory 的版本与证据等级 |
| `tools/Inspect-StageOlang.py` | PROMOTE_CORE | STAGEDAT/DAR/RBX 定点检查 | 不证明运行时选择 |
| `tools/Audit-LooseOlangKana.py` | PARTIAL | 输出质量审计 | 无假名不能证明完整汉化 |
| `tools/OuterCrypt.cpp/.exe` | PROMOTE_CORE | 独立 filename-seeded outer transform/test vector | 默认会写 output，只能写 V2 work 目录 |
| `tools/Rekey-Olang.cpp/.exe` | PARTIAL | rekey 机制与 round-trip test | rekey-as-localization 策略已被反证 |
| `tools/Build-JpnSlotNativeVoiceText.py` 的 OHD 函数 | PARTIAL | 16/128/60 OHD parser 与 fixed-field rebuild | 同文件的全部 GTT 函数禁止复用 |
| `tools/Build-JpnSlotVoiceByMetadata.py` 的 OHD 函数 | PARTIAL | OHD text field zero-padding 和 target-metadata preservation | main workflow 与 GTT identity/builder 禁止复用 |
| `tools/Chrysalis.exe` 与 source | REFERENCE_ONLY | SLOT/STAGEDAT/CNF 结构交叉对照、只读 extraction | 没有完整 repacker；init extraction 曾失败并漏 `init.rlc` |

## 无线电隔离区

| 旧资产 | 状态 | 原因 |
|---|---|---|
| `tools/Build-JpnSlotNativeVoiceText.py` GTT 部分 | QUARANTINE | `decode_gtt_text` first-NUL；`build_gtt_record` 单字符串并缩短 record |
| `tools/Build-JpnSlotVoiceByMetadata.py` GTT 部分 | QUARANTINE | 每 record 仍只选择一个 text，并声称完整保留 JPN header |
| `tools/Build-JpnSlotAllVoiceLanes.py` | QUARANTINE | 六 lane 复制和 page grouping 策略已禁用 |
| `tools/Audit-SlotNativeVoiceText.py` | QUARANTINE | first-NUL、lead-byte、active lane 结论均不可继续使用；仅容器遍历代码可另抄到 core |
| `tools/Analyze-GttAlignment.py` | QUARANTINE | single-string payload 解码 |
| `tools/Inventory-SlotVoiceDiff.py` | QUARANTINE | 建立在旧 voice record/region 对齐模型上 |
| `tools/Inspect-SlotString.py` 的 GTT 路径 | QUARANTINE | 必须改为逐 segment 展示后才能使用 |
| `tools/gtt-cn-text-overrides.json` | REFERENCE_ONLY | 文本可作翻译候选；旧 file_id/index 绑定不可信 |
| `tools/gtt-jpn-extra-translations.json` | REFERENCE_ONLY | 同上，JPN-only 身份必须重建 |
| `build/text-only/slot-voice-metadata-report.json` | REFERENCE_ONLY | 可保留旧输出指纹；`jpn_gtt_headers_preserved` 已过期 |
| `build/text-only/slot-all-voice-lanes-report.json` | REFERENCE_ONLY | 记录历史实验，不是 V2 事实 |
| `MGSPW_GTT_PREFLIGHT/gtt_preflight.py` | PARTIAL | multi-segment framing/slot parser可作新 parser 起点 | 
| `MGSPW_GTT_PREFLIGHT/01_collect.py`、`02_analyze.py` 及 summary | QUARANTINE | 使用固定 `JPN=ENG+4`；统计必须重跑 |
| `MGSPW_GTT_DUMP/20260902-174047/*` | REFERENCE_ONLY | Miller byte-level 正/坏样本与 working ENG_CN boundary diff，适合作 regression fixture |

## OLANG、换行与翻译资料

以下 JSON/生成器不是格式核心，只能在 V2 重新验证目标 identity、原文、控制标记和索引后迁移：

- `slot-olang-map.json`
- `slot-special-translations.json`
- `slot-auto-uncovered.json`
- `slot-manual-uncovered.json`
- `slot-final-kana-overrides.json`
- `slot-all-olang-overrides.json`
- `slot-text-layout-overrides.json`
- `slot-wrap-policies.json`
- `stage-jpn-overrides.json`
- `stage-jpn-text-layout-overrides.json`
- `Generate-SlotOlangMap.py`
- `Resolve-SlotUncovered.py`
- `Generate-JpnSlotWrapOverrides.py`
- `Generate-JpnStageWrapOverrides.py`
- `Build-JpnSlotAllOlang.py`

其中换行和中文文本可作为 translation memory；旧 page/tag/reference index 不自动继承。

`5D3AF52D` 已提供具体反例：MLG_CN 场景为 91 references，JPN 目标为 118 references；旧 `semantic_partial` 会把“哥斯达黎加没有军队”等中文放到不相干的 JPN reference。V2 对 OLANG 的可复用部分仅限 RBX parser、metadata-preserving body rebuild、CNF/page encode 和 round-trip；译文身份必须由 JPN 上下文工作表显式确定。

## 本轮不纳入 V2 文本容器核心

以下资产与动画/视频诊断有关，保留在旧工程，不复制：

- `Analyze-AdemoHeaders.py`
- `Audit-JpnMoviePayloads.py`
- `Build-JpnAdemoNativeText.py`
- `Build-JpnMovieText.py`
- `Build-MovieContactSheet.py`
- `Inspect-Mp4Timeline.py`
- `Set-AdemoDiagnosticMode.ps1`
- `Set-MovieDiagnosticMode.ps1`

## V2 模块边界建议

当前 `core/rbx.py` 与 `core/gtt_multi.py` 已落地，均不包含翻译表或跨区域业务映射。其余模块继续按以下边界从旧代码提取：

- `core/pc_crypto.py`
- `core/slot_key.py`
- `core/slot_page.py`
- `core/cnf.py`
- `core/rbx.py`
- `core/dar.py`
- `core/stagedat.py`
- `core/gtt_multi.py`（全新实现）
- `core/ohd.py`
- `audit/roundtrip.py`
- `audit/region_identity.py`

任何 `core` 模块不得包含翻译表、page/lane 规则、源目录硬编码或安装动作。
