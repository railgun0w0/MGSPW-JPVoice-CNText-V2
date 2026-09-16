# FONT source topology

> **REFERENCE ONLY.** 本文的 official JPN/MLG selector 对应关系仍有效，但 production/runtime 状态已由 [`../doc/FONT_TECHNICAL_ARCHIVE.md`](../doc/FONT_TECHNICAL_ARCHIVE.md) 和 [`../doc/FONT_PRODUCTION_BASELINE.md`](../doc/FONT_PRODUCTION_BASELINE.md) 接管。发生冲突时以 `font/doc/` 为准。

本文件是仓库内 FONT 来源关系的历史简表。目录中如果同时出现四个 XPR，那是为了比较 JPN 与 MLG 而汇集的分析集合，不代表 Steam 官方 JPN depot 原生同时包含四个文件。

```text
MLG large  0007ccd8.xpr  <──────────────>  JPN large  00c7c9f9.xpr
MLG small  000ebbe8.xpr  <──────────────>  JPN small  001cbbd1.xpr
```

## 官方 base

| 语言 lane | 字体规格 | XPR |
|---|---|---|
| JPN | large | `00c7c9f9.xpr` |
| JPN | small / `SMALL_JPN` | `001cbbd1.xpr` |
| MLG | large | `0007ccd8.xpr` |
| MLG | small | `000ebbe8.xpr` |

因此，`0007/000e/001c/00c7` 不能统称为“官方 JPN 四字体集合”。官方 JPN 只有 `00c7` 与 `001c`；`0007` 与 `000e` 属于 MLG lane。

## 当前汉化 patch 的生产关系

```text
MLG patched 0007ccd8.xpr
    ├─ copy ───────────────> patched 0007ccd8.xpr
    └─ decrypt with 0007 seed
       re-encrypt with 00c7 seed ─> patched JPN 00c7c9f9.xpr

MLG patched 000ebbe8.xpr
    └─ copy ───────────────> patched 000ebbe8.xpr

默认没有：patched JPN 001cbbd1.xpr
```

这条 production 路线只做 copy/rekey，不把 MLG glyph bitmap 转换成官方 JPN 原生结构；`00c7` 的 patched 内容仍然来自 MLG large `0007` 的 XPR2 明文。默认 small JPN `001c` 没有对应的中文 patched output。

`IncludeExpandedSmallJapaneseFont` 是实验性 opt-in：它把 MLG patched `000ebbe8.xpr` 的整份 XPR2 内容以 `001cbbd1.xpr` 文件名 seed 重新加密。它不是 clean JPN001C 的原生重建。其早期资源初始化崩溃发生在未同步 runtime Width/Height 的路径；后续将 `main+0x436AB`/`main+0x436B5` patch 为 `4096×4096` 后，同一 pure-rekey plaintext 已实机正常启动并显示中文。该第三方字体仍只作为兼容性/容量证明，不是未来 production dependency。

## Loading 缺字缺口

实机已确认 Loading 角色语录使用 `JPN/001cbbd1.xpr` 自带 TX2D。`LOOSE_OLANG/00D0C740.csv` 的 36 条角色语录共有 330 个唯一汉字；clean JPN001C 已覆盖 100，缺失 230。当前 production 只处理了 JPN large `00c7`，没有提供 patched JPN small `001c`，因此 Loading 继续落回 clean SMALL_JPN 并暴露这 230 个缺字。
