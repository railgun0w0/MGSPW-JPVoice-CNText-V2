# V2 Production Merge / Build Readiness Checkpoint

更新时间：2026-09-08（Asia/Hong_Kong）

本 checkpoint 保存本轮“241 个 mapping 合并到 production，并开始统一构建前验证”的实际进度。Steam 游戏目录未修改，所有临时构建均位于 V2 `build/readiness/`。

## 已完成

- 从 `sol-translation` mapping checkpoint `7ad72340123073397b7faef8f4a3f3df9691228c` 读取并校验 241/241 个 mapping；状态 checkpoint 为 `038e933`。
- 生成 241 个正式 production CSV，共 21,041 条 file_id 内精确去重译文：
  - YPK_GTT：36
  - OHD：1
  - LOOSE_OLANG：14
  - STAGEDAT_OLANG：46
  - SLOT_OLANG：144
- 生成对象级 `compiled_translation_manifest.csv`：91,609 行。
- 机械修正 7 条旧 YPK CSV 列位移；重新计算 1,780 条不准确的 `cn_utf8_bytes`；3 条纯空格 JPN 文本按原样保留。
- 控制符 / markup / placeholder inventory：0 error。
- 实机通过的 golden 优先于新 mapping：
  - YPK/GTT `1C79F2AD`
  - SLOT OLANG `5D3AF52D`
- 现有 regression：10/10 PASS。
- CSV artifact-tool 抽查：PASS。

## 固定容量结果

- GTT records：
  - NORMAL_FIT：1,815
  - ALIGNMENT_SPILL：67
  - HARD_OVERFLOW：0
- OHD physical records：904/904 fit，0 HARD_OVERFLOW。
- 最初发现的 29 个 GTT HARD_OVERFLOW 分布在 10 个 file_id：
  - `1C0FB26B`：4
  - `1C677327`：1
  - `1C7679A5`：9
  - `1C79F36D`：1
  - `1C79F46D`：2
  - `1C7A72ED`：1
  - `1C7A736D`：1
  - `1C7B72AD`：2
  - `1C7C72ED`：1
  - `1CC276E9`：7

29 个原 hard-overflow record 的短译文已按人工 CSV 固化：20 条转为 normal fit、9 条使用原 alignment slack，0 条仍 overflow。仍然禁止截断或扩大 GTT frame。

## 已通过容器级 round-trip

### SLOT OLANG

- 144 个 file_id
- 742 个 physical occurrences
- 68,684 条 manifest JPN reference bindings
- 110 个 SLOT pages
- 0 block overflow
- 非目标 tag payload、RBX metadata、DAT allocation 和 KEY 保持验证通过

### Loose OLANG

- 14 个文件
- 2,963 个目标 JPN references
- 0 structural failure
- 非目标 language references 保持不变

### STAGEDAT OLANG

- 14 个 pages
- 123 个 embedded OLANG entries
- 16,922 个目标 JPN references
- 0 block overflow
- 原 page offset/key、非目标 DAR payload 和 RBX metadata 保持验证通过

## 本轮后续已完成

1. 全部 36 个 YPK/GTT 完成 fixed-frame repack：77 occurrences、1,882 records、2,136 timed segments、49 pages、0 block overflow。
2. OHD 完成 fixed-record rebuild：4 occurrences、904 physical records、4 pages、0 overflow。
3. SLOT OLANG、YPK/GTT、OHD 已合并为一个 clean-JPN SLOT DAT：823 个目标 tag、110 pages、0 block overflow。
4. 14 个 loose OLANG、STAGEDAT 与 3 个已验证中文字库已组成 20 文件统一测试包。
5. Steam 游戏目录尚未修改；剩余工作只有统一安装与实机验收。

## 本轮代码

- `tools/Compile-ProductionTranslations.py`
- `tools/Verify-ProductionCsvs.mjs`
- `tools/Build-JpnLooseOlangFromManifest.py`
- `tools/Build-JpnStageDatOlangFromManifest.py`
- `tools/Build-JpnSlotOlangFromManifest.py`：修正多语言 RBX 中非目标 sentinel reference 被误当作待翻译 reference 的问题。

## 关键输出

- `build/translation/compiled_translation_manifest.csv`
- `build/translation/translation_worklist.csv`
- `build/translation/fixed_capacity_issues.csv`
- `build/translation/production_merge_report.json`
- `build/readiness/slot_olang_structure_report.json`
- `build/readiness/loose_olang_structure_report.json`
- `build/readiness/stagedat_structure_report.json`
- `build/readiness/ypk_gtt_roundtrip_report.json`
- `build/readiness/ohd_structure_report.json`
- `build/readiness/unified_slot_structure_report.json`
- `build/readiness/full_package_report.json`
- `build/readiness/full_package/`

恢复工作时先阅读本文件。不要重新翻译 21,041 条已完成译文；下一步从统一测试包的实机验收开始。
