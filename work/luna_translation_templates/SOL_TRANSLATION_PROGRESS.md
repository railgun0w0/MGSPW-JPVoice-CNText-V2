# Sol Translation Progress

Branch: `sol-translation`

## Current checkpoint

- 当前事实入口是 [`TRANSLATION_STATE.md`](TRANSLATION_STATE.md)，不要根据历史 checkpoint 推断完成度。
- 全部 **710 / 710 file_ids、26,686 / 26,686 translation rows** 已有完整 mapping，`NEXT_FILE_ID=NONE`。
- `BRIEFING/` 是物理目录名；其中模板和 mapping 的逻辑 `resource_class` 仍为 `BRIEFING_NBE`。
- BRIEFING 共 **469 blocks / 5,645 JPN rows**，其中 FILES 为 363 / 4,810，MISSION 为 106 / 835。
- 当前阶段是合并、构建和测试准备；本目录中的模板与 mapping 不等同于已写入 DAT 的正式补丁。

## Active rules

- JPN 是唯一语义和结构权威；ENG 与 MLG_CN 仅作参考。
- 保留 markup、controls、placeholders、indices/references、顺序、时序和显著空白。
- 模板保持只读；正式译文保存在 `sol_translation_mappings/`。
- 运行 `python tools/rebuild_translation_state.py --check` 校验当前事实；需要刷新状态时使用 `--write`。
- 旧人工计数、恢复窗口和阶段性 `NEXT_FILE_ID` 已移至 [`archive_docs/`](archive_docs/README.md)，不得用于继续工作。

## Complete mapping-backed checkpoint ledger

<!-- BEGIN GENERATED COMPLETED LEDGER -->

State has not been rebuilt after document archival.

<!-- END GENERATED COMPLETED LEDGER -->
