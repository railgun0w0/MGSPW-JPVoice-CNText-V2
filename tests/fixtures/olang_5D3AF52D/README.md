# OLANG 5D3AF52D golden fixture

该 fixture 固化 clean JPN page 1864/tag 2 的原始 RBX segment，以及已经通过实机测试的中文重建 segment。

测试读取 `translations/slot_olang/5D3AF52D.csv`，将 110 条批准译文展开到 118 个 JPN references，再用 `core.rbx.rebuild_rbx_texts()` 重建。预期结果必须与 golden bytes 完全一致，并保持 118 entities、118 references、entity table、language keys 和 flags。

fixture 只证明 `5D3AF52D` 的 metadata-preserving RBX body rebuild，不授予其他 file_id 任何跨区域 mapping 身份。
