# Ruby canonical 同步 checkpoint

更新时间：2026-09-14（Asia/Hong_Kong）

本 checkpoint 记录最终 Ruby canonical 表同步后的状态。同步前先建立 Git checkpoint：`d123954`。本次只处理 Ruby token，不进行其他术语润色或正文改写。

## 权威输入

- canonical 表：`doc/ruby_base_pair_canonical.csv`
- unique JPN Ruby pairs：587
- 目标 Ruby occurrences：1,251
- production source：当前 `work/luna_translation_templates/sol_translation_mappings/` JSON mapping 与明确保留的 legacy template CSV

## 本次同步

审计发现并同步 16 个剩余 mismatch：

- `SLOT_OLANG/5D3AF52D`：15 occurrences
- `YPK_GTT/1C79F2AD#1`：1 occurrence
- 修改 JSON mapping：2 个文件
- 修改 production CSV：2 个文件
- legacy YPK CSV：0 个修改
- 未创建新的 mapping，也未迁移 representation

只修改了 `<R=base,ruby>` token 内的 canonical base/ruby；Ruby token 外正文、换行、reference、entity、segment 和其他结构均保持不变。production CSV 中同步更新的 `cn_control_tokens` 与 `cn_utf8_bytes` 是 compiler 根据新 `cn_text` 生成的派生字段。

## 验证结果

- `UNMAPPED_PAIR=0`
- `RUBY_COUNT_MISMATCH=0`
- production canonical mismatch：0
- production compiler：`BUILD_READY=1`
- `CONTROL_ERRORS=0`
- `GTT_HARD_OVERFLOW=0`
- BRIEFING layout audit：PASS；FILES 仍有 2 条独立行宽超限，属于待处理 layout 项，不是 Ruby 同步引入
- pytest：10 passed
- Ruby token 外正文变化：0

提交记录：

- `55ea232` — sync remaining canonical Ruby tokens
- `3a2a132` — rebuild production with canonical Ruby tokens

后续如继续处理 BRIEFING 换行，应保持 Ruby canonical 表不变，并只在对应 `cn_text` 中调整 LF。
