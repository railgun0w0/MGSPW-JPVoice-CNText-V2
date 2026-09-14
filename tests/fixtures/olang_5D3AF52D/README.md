# OLANG 5D3AF52D golden fixture

该 fixture 固化 clean JPN page 1864/tag 2 的原始 RBX segment，以及已经通过实机测试的中文重建 segment。

回归测试以 fixture 内已经冻结的中文 segment 重放 `core.rbx.rebuild_rbx_texts()`，验证 118 entities、118 references、entity table、language keys、flags 和稳定的 RBX 结构。production 不读取该 fixture 的正文；production 中文只来自当前 mapping。由于当前译文可以合法不同于历史 golden，golden 不再作为 production 文本相等性断言。

fixture 只证明 `5D3AF52D` 的 metadata-preserving RBX body rebuild，不授予其他 file_id 任何跨区域 mapping 身份。
