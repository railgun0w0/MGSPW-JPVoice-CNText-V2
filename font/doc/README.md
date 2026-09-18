# FONT documentation authority

`font/doc/` 是本仓库字体研究、production baseline 与下一阶段设计的最新权威文档目录。当前 RC1 production 采用从 clean JPN selectors 自有重建的 large/small 字体 pair；状态与 package 事实同时受 `docs/RELEASE_READINESS.md` 和 `build/rc1/RC1_FILE_MANIFEST.csv` 约束。

| document | authority scope |
|---|---|
| [`FONT_TECHNICAL_ARCHIVE.md`](FONT_TECHNICAL_ARCHIVE.md) | 已证明的字体拓扑、XPR/FontData/TX2D 结构、crash 证据链、runtime dimension 根因、撤销假设与实验资产索引。 |
| [`FONT_PRODUCTION_BASELINE.md`](FONT_PRODUCTION_BASELINE.md) | 当前可工作的 EXE/large/small Golden Baseline、runtime patch bytes 与安全策略。 |
| [`FONT_CUSTOM_BUILD_PLAN.md`](FONT_CUSTOM_BUILD_PLAN.md) | 从 clean JPN 构建完全自有中文字库的下一阶段设计；不是已完成实现。 |

权威规则：

1. 当前事实和状态冲突时，以本目录的正式文档为准。
2. `font/analysis/` 保存分析过程、census、manifest、PoC 报告和历史证据，不是 current conclusion 的默认入口。
3. 标为 `ARCHIVED / HISTORICAL REFERENCE` 的报告只用于追溯当时证据和实验路径。
4. 标为 `REFERENCE ONLY` 的报告可能仍含有效静态事实，但 production 状态必须回到本目录核对。
5. 第三方 MLG 字体只作为兼容性、逆向和容量证明，不是未来 production dependency。
6. 当前 production 路线是从 clean JPN `00c7c9f9.xpr` / `001cbbd1.xpr` selectors 进行 `SELF_OWNED_REBUILD`；RC1 已验证 `EXE_PATCH_REQUIRED = NO`。MLG/MLG_CN 只作 reverse-engineering / compatibility reference，不是 production dependency。
7. 指向未入 Git 的 Experimental、PoC、fixture 或 dump 证据必须标记 `LOCAL-ONLY`，不得形成看似可在 GitHub 打开的失效链接。
