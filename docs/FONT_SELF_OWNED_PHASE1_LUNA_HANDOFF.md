# SELF_OWNED FONT BUILDER — PHASE 1 Luna handoff (ARCHIVED PHASE-1 HANDOFF SNAPSHOT)

交接时间：2026-09-16（Asia/Hong_Kong）
仓库：`railgun0w0/MGSPW-JPVoice-CNText-V2`
本地 checkout：`D:\GAME\test\steam 合金装备大师合集2 合金装备和平行者汉化补丁\JPVoice_CNText_V2`
分支：`sol-translation`

> Current status: **Phase 1 complete and pushed**; `HEAD = 97a712bcce0fb45311ed548d4874299ba8fb4a38`.
>
> This is an archived Phase-1 handoff snapshot. Historical pause-point notes below are retained for provenance and are not a current pending-work list.

## 1. 必须继续遵守的 authoritative baseline

开始工作前已完整读取：

- `font/doc/README.md`
- `font/doc/FONT_TECHNICAL_ARCHIVE.md`
- `font/doc/FONT_PRODUCTION_BASELINE.md`
- `font/doc/FONT_CUSTOM_BUILD_PLAN.md`
- `docs/FONT_TECHNICAL_STATE.md`
- `docs/FONT_STATUS_MATRIX.csv`

继续保持：

- production direction = `SELF_OWNED_REBUILD`
- clean large base = `font/JPN/00c7c9f9.xpr`
- clean small base = `font/JPN/001cbbd1.xpr`
- 001c 4096×4096 runtime path = `PROVEN`
- 001c fixed 2 MiB limit = `RETRACTED`
- patched MLG_CN0007-derived 00c7 PoCs 不等于 clean JPN00c7 PoCs
- clean JPN00c7 self-owned full rebuild runtime compatibility = `PROVEN` (Phase 2A fixture; append-only semantics beyond that fixture remain separate/`UNKNOWN`)
- MLG/MLG_CN 只可作为 reference/proof，不可进入 production builder 输入图

不要重新研究 001c 2 MiB/4096×4096 根因，不要修改游戏安装目录，不要下载或提交字体。

## 2. 已完成并已提交

已完成用户指定的两处文档小修正，并已单独提交：

```text
23d262f docs: finalize font baseline corrections
```

内容：

1. `docs/FONT_STATUS_MATRIX.csv`
   - `MLG 0007/000E copy plus 0007 decrypt/rekey to 00C7`
   - 改为 `MLG_CN 0007/000E copy plus MLG_CN 0007 decrypt/rekey to 00C7`
2. `docs/FONT_TECHNICAL_STATE.md`
   - 整理日期改为 `2026-09-16`

Phase 1 完成时分支与 `origin/sol-translation` 已同步。基线提交为：

```text
44b7b160b1bd4df8d53e652c5103515f635b0a8d docs: correct font evidence provenance
```

## 3. Production charset 边界已经确认

当前应采用的实际 production 输入：

1. 旧五类对象级编译结果：
   - `build/translation/compiled_translation_manifest.csv`
   - 91,609 行
   - resource classes：`YPK_GTT`、`OHD`、`LOOSE_OLANG`、`STAGEDAT_OLANG`、`SLOT_OLANG`
2. `BRIEFING_NBE` 正式物理行：
   - `translations/briefing/*.csv`
   - 469 个文件 / 5,645 行

统计时旧五类 mapping/template 不应再重复计数；它们通过当前对象级 compiled manifest 表示。`BRIEFING_NBE` 不在旧五类 manifest 内，必须单独加入。

明确排除：

- `work/luna_translation_templates` 中的模板和辅助 reference 文本（只用于 compiler/mapping 一致性验证）
- ENG、MLG_CN、JPN auxiliary/reference 文本
- 历史实验译文、backup、fixture、旧汉化参考
- readiness/package 的重复副本
- 文档、worklist、测试输出

控制语法处理 WIP 规则：

- `<R=base,reading>` 保留可显示的 `base + reading`，排除 Ruby 语法本身
- 排除 `<I=...>`、`<C=...>`、`<->`、其它 runtime named angle controls
- 排除 `$NAME`、printf placeholders、转义或物理 CR/LF/TAB、Unicode control/format
- human-readable angle-bracket title 按现有 production compiler 规则保留
- U+0020/U+00A0/U+3000 作为 layout glyph 保留
- 当前 selector corpus 不能可靠拆分，全部标记 `UNKNOWN / UNION_REQUIRED`

## 4. Clean JPN 独立静态读取结果

以下均只来自 clean `font/JPN/00c7c9f9.xpr` 与 `font/JPN/001cbbd1.xpr`，没有读取 MLG/MLG_CN donor 数据。

### 00c7c9f9.xpr

```text
encrypted size       16,945,180
encrypted SHA256     1f7a18f28d0d67d7a6a65a5286a1e48c97d595829b4c99325fb2b5772b921e8d
decrypted SHA256     31b8eb9a7c86b1429fb7fa0d12688c65c9123e307c5f0e8c42f1df67a7cd9e6b
XPR magic            XPR2
header_size          0x29010
data_size            0x1000000
resource_count       2
texture offset       0x2901C
texture alignment    0x1C mod 0x800
TX2D                 file 0x5C, size 0x34
USER                 file 0x90, size 0x28F32
atlas                4096x4096, pitch 4096, format 2, tiled 0, endian 0
last_code            U+FF63
charmap entries      65,380
mapped codepoints    2,308
charmap end          USER+0x1FEDE
8-byte aligned point USER+0x1FEE0 (two 00 padding bytes)
count prefix         USER+0x1FEE0, raw 0905, BE u16 = 2,309
record table         USER+0x1FEE2, 2,309 x 0x10-byte GlyphRecord
suffix/trailer       0 bytes; record table ends exactly at USER end
```

重要新静态事实：clean JPN00c7 自身的实际 count prefix 是 **2-byte big-endian u16 `0905`**。这不是 patched MLG_CN0007 PoC 的 4-byte mirror，不能混用。

### 001cbbd1.xpr

```text
encrypted size       2,234,396
encrypted SHA256     5625066b835e6f26f310781fbbd3ef4f9ea93a77be2a4044289c11b74a767414
decrypted SHA256     f4fdb335a56f81bee4e4a13be71f5518827ebcf42fbfa86d30d2f1de3c6dd025
XPR magic            XPR2
header_size          0x21810
data_size            0x200000
resource_count       2
texture offset       0x2181C
texture alignment    0x1C mod 0x800
TX2D                 file 0x5C, size 0x34
USER                 file 0x90, size 0x214CA
atlas                2048x1024, pitch 2048, format 2, tiled 0, endian 0
last_code            U+FF1F
charmap entries      65,312
mapped codepoints    358
charmap end          USER+0x1FE56
8-byte aligned point USER+0x1FE58 (two 00 padding bytes)
count prefix         USER+0x1FE58, raw 0167, BE u16 = 359
record table         USER+0x1FE5A, 359 x 0x10-byte GlyphRecord
suffix/trailer       0 bytes; record table ends exactly at USER end
```

两个文件的 GlyphRecord 均按 8 个 BE u16、stride `0x10` 解析：

```text
u0, v0, u1, v1, bearing_x_raw, width, advance, reserved
```

用当前本地 `core/xpr_font.py` 做过只读手工探针：

```text
00c7 no-op decrypted rebuild == original plaintext : True
00c7 rebuilt encrypt == original encrypted bytes   : True
001c no-op decrypted rebuild == original plaintext : True
001c rebuilt encrypt == original encrypted bytes   : True
```

这是暂停前的手工控制台结果；随后已由修复后的 builder 重跑，正式 `font/build/reports/FONT_CLEAN_ROUNDTRIP_REPORT.md` 已生成并纳入提交。

## 5. 当前 WIP builder

本轮新增并已在 Phase 1 commit 中提交：

```text
tools/build_mgspw_cn_fonts.py
```

目标 CLI：

```text
python tools/build_mgspw_cn_fonts.py ^
  --analyze ^
  --roundtrip-clean ^
  --large-base font/JPN/00c7c9f9.xpr ^
  --small-base font/JPN/001cbbd1.xpr ^
  --font-file "C:\path\font.ttf" ^
  --font-face-index 0 ^
  --output-dir font/build
```

Phase 1 中 `--font-file` / `--font-face-index` 只预留接口，不打开、不复制、不嵌入字体。

脚本目前已实现的代码路径：

- 六类 production corpus census
- markup/Ruby/placeholder/control 过滤
- `font_charset.csv` / `font_charset.txt` / charset report 输出逻辑
- 两个 clean JPN XPR 的 decrypt/parse/结构报告逻辑
- clean count prefix、USER growth、resource relocation 静态 probe
- 52/56/58/60/62/64/66 px × padding 1/2 的 deterministic shelf first-fit-decreasing packing simulation
- retained clean non-Han + SC Han override/missing Han 的 planning policy
- clean decrypt → no-op rebuild → encrypt → decrypt exact round-trip report逻辑
- future glyph/build manifest contract与三候选公平比较约束

依赖：

- tracked：`core/pc_crypto.py`
- 当前工作树中原已存在、仍未跟踪：`core/xpr_font.py`
- 当前工作树中原已存在、仍未跟踪：`tests/test_xpr_font.py`

若正式采用此 WIP builder，第二笔提交需要明确把 `core/xpr_font.py` 与对应 tests 纳入，而不是只提交入口脚本。

## 6. 暂停时阻塞错误（已修复）与当前生成物

首次运行命令：

```text
python tools/build_mgspw_cn_fonts.py --analyze --roundtrip-clean
```

在写 `font_charset.txt` 时失败：

```text
TypeError: write_text() got an unexpected keyword argument 'newline'
```

位置：`tools/build_mgspw_cn_fonts.py` 的 `atomic_write_text()`。

已修复：`atomic_write_text()` 改为用 `temporary.open("w", encoding="utf-8", newline="")` 写入，再 `replace()`。

修复后从零重跑成功，当前已生成：

```text
font/build/charset/FONT_CHARSET_REPORT.md
font/build/charset/font_charset.txt
font/build/charset/font_charset.csv
font/build/research/CLEAN_JPN_FONT_BUILD_SEMANTICS.md
font/build/reports/FONT_ATLAS_CAPACITY_SIMULATION.md
font/build/reports/FONT_ATLAS_CAPACITY_SIMULATION.csv
font/build/reports/FONT_CLEAN_ROUNDTRIP_REPORT.md
```

`.gitignore` 已从泛匹配 `build/` 精确改为根目录 `/build/`，因此 `font/build/` 可以被逐项审查和提交；根 `build/translation/` 仍保持忽略。

最终 charset 输出摘要：

```text
unique codepoints     2,904
total occurrences    1,253,865
unique Han           2,721
unique ASCII         91
unique kana          16
unique punctuation   52
unique symbols       24
characters > U+FFFF  0
```

最终输出已经通过独立完整性核验：CSV 与 TXT 的字符顺序一致；capacity matrix 为 28 行、overflow 为 0；round-trip report 的 00c7/001c 均为 PASS；semantics report 的四个证据分区均存在。

容量初步结论：union worst-case 下，52–66 px、padding 1/2 的 4096×4096 fixed-cell planning simulation 全部 `overflow=NO`。这是 upper-bound/planning estimate，不是 rasterized glyph 的最终容量证明。

## 7. 后续审查与未完成事项

1. 先读本交接与六份 authoritative FONT 文档，不要重新打开已撤销的 2 MiB 调查。
2. 审查已完成的 builder，特别是：
   - visible/layout space 口径
   - human-readable angle title 与 runtime controls 的区分
   - punctuation policy 仅作统计/容量假设，不得写成最终 glyph source 决定
   - retained clean glyph 是非-Han unique glyph-index planning policy，不能误报为最终 production 方案
3. 已完成的 unit tests 为 `18 passed`（包含 `tests/test_xpr_font.py` 和 Phase 1 builder tests）。
4. 逐项核对报告必须明确分为：
   - `PROVEN_FROM_FILE_STRUCTURE`
   - `PROVEN_FROM_EXISTING_RUNTIME`
   - `NEEDS_NEW_RUNTIME_VALIDATION`
   - `UNKNOWN`
5. 特别保持 clean 00c7 的 runtime full rebuild 为 `UNKNOWN / NEEDS_NEW_RUNTIME_VALIDATION`；静态 2-byte count prefix 不等于 runtime 已通过。
6. 旧五类 compiler 已在无历史 dirty 文件的临时 clean clone 中 dry-run 通过：241 files、21,041 unique rows、91,609 compiled rows、control errors 0、hard overflow 0、`BUILD_READY=1`。当前工作树直接运行仍会被 dirty-worktree fail-closed 拦截，这是预期保护行为。
7. BRIEFING compiler 的直接检查仍被本机缺少 `@oai/artifact-tool` 依赖拦截；需要在依赖完整环境复核，不能标成 PASS。
8. 所有正式审查完成后，再做原计划第二笔提交：

```text
font: establish self-owned builder phase 1
```

## 8. 提交与 staging 注意

本节是 Phase 1 的历史快照。2026-09-17 起，当前工作区已将字体、分析结果和实验目录统一归档到 `font/`；本次整理提交按实际目录结构选择性上传，不再把下面的旧 staging 清单视为当前状态。

当前工作树本来就有大量未跟踪的历史分析、MLG/MLG_CN、PoC、fixture 和工具。它们不是本轮新增，不能使用宽泛 `git add .`。

应只逐个 stage 本轮确认的文件，例如：

```text
core/xpr_font.py
tools/build_mgspw_cn_fonts.py
tests/test_xpr_font.py
新增的 Phase 1 tests
font/build/charset/...
font/build/research/...
font/build/reports/...
必要的 .gitignore 精确修正
本交接文档（若仍需保留）
```

不要 stage：

- `font/MLG/`
- `font/MLG_CN/`
- `font/JPN_CN/`
- 历史 `font/font_poc*` / `font/small_jpn_*`
- 未经本阶段审查的旧 `tools/Build-*`、analysis CSV/report
- clean JPN XPR binaries，除非项目所有者另行明确决定 Git 策略

## 9. Phase 2A runtime status archive

本 Phase 1 handoff 是历史快照；其“仍需独立验证”描述已由后续 Phase 2A 实机验证取代。用户在真实游戏中确认 clean JPN00c7 self-owned full-rebuild fixture 可正常运行，中文正常显示，视觉效果良好，未报告乱码、纹理异常或明显显示故障。

fixture identity：`Noto Sans SC Bold`（SHA256 `d1961be1161ea1be08496c920862d06ea5c23a757628f4fd69368de1d9f51bed`），pixel size `56`，cell height `72`，baseline `56`，padding `2`，GlyphRecords `3078` / mapped `3077`；plaintext SHA256 `44788a853d8f30da08d184b4aa5c9794ca7a5f115f9d7c03e14ce4cedcf24ae5`；encrypted SHA256 `13e226b664572cef36be391c0fb78c46ae334955650f86836a2d5d3b3e1580f5`。

`CLEAN_JPN_00C7_FULL_REBUILD_RUNTIME = PROVEN` 仅覆盖 clean JPN00c7 self-owned full rebuild runtime compatibility；不覆盖 clean JPN001c self-owned 4096×4096 runtime output、最终字体选择、最终 punctuation policy 或最终 large/small raster profile。Phase 2B 尚未开始。

## 10. 暂停点安全说明

- 未修改任何游戏安装目录。
- 未 patch EXE。
- 未生成最终 release font。
- 未下载、复制或提交 Microsoft/开源字体。
- 未使用 MLG_CN FontData/charmap/GlyphRecord/bitmap 作为 production 输入。
- 本轮正式 commits 为 `23d262f`（baseline corrections）与 `97a712b`（Phase 1 builder/report bundle）。
- 与本轮无关的历史字体、PoC、analysis 和 fixture 仍保持未跟踪，最终状态必须以精确 `git status` 为准。
