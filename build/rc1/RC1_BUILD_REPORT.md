# RC1 Clean Build Report

Date: 2026-09-16  
Branch: `sol-translation`  

```
RC1_BUILD_STATUS = FAIL
FINAL_PATCH_FILE_COUNT = 20 (manifest target)
STAGING_FILE_COUNT = 0
00C7_HASH_MATCH = YES
001C_HASH_MATCH = YES
EXE_INCLUDED = NO
0007_INCLUDED = NO
000E_INCLUDED = NO
MLG_CN_PRODUCTION_DEPENDENCY = NO
CLEAN_REBUILD_VERIFIED = PARTIAL
READY_FOR_CLEAN_INSTALL_TEST = NO
```

## Verification matrix

| step | result | evidence |
|---|---|---|
| production compiler from clean temporary translation clone | PASS | 241 files, 21,041 unique rows, 91,609 manifest rows, zero control errors, `BUILD_READY=1` |
| LOOSE_OLANG clean-JPN rebuild | PASS | 14 files, 2,963 translated references, structural/text round-trips pass |
| STAGEDAT_OLANG clean-JPN rebuild | PASS | 123 entries, 16,922 translated references, zero block overflow |
| SLOT_OLANG clean-JPN rebuild | PASS | 144 resources, 68,684 manifest bindings, 110 pages, zero block overflow; DAT size and KEY identical |
| OHD clean-JPN rebuild | PASS | 226 canonical / 904 occurrence records, 4 patched pages, zero hard/block overflow |
| BRIEFING clean-JPN check | PASS | 469 blocks, 5,645 physical rows, zero binding/control/capacity/round-trip errors |
| 00c7 self-owned rebuild | PASS | plaintext `44788a853d8f30da08d184b4aa5c9794ca7a5f115f9d7c03e14ce4cedcf24ae5`; encrypted `13e226b664572cef36be391c0fb78c46ae334955650f86836a2d5d3b3e1580f5` |
| 001c self-owned stock rebuild | PASS | plaintext `f244d4c506fdfa41194e77238cf6a49858030c28d43ce6cfb4029cbc1842bb60`; encrypted `357f12d313cf3c6b8958311afbff759b77b625a617c12800d682c7f1e1e86ce6` |
| YPK/GTT clean-JPN rebuild | FAIL | page 220 requires fixed-frame compressed size 28,857 bytes but capacity is 28,672 |

## Failure and scope

The YPK/GTT builder tried every bundled zlib strategy. The page still exceeds
its fixed allocation by 185 bytes. The historical successful report records
`zopfli-i15` for page 220, but this workstation has no `zopfli` executable.
This is recorded as `NOT EXECUTED — MISSING LOCAL INPUT: zopfli executable`
for the required compression path. No old build output was substituted, no
translation data was edited, and no attempt was made to bypass the fixed-frame
capacity check.

Because YPK/GTT is a required RC1 resource class, no `build/rc1/staging/`
directory, `RC1_FILE_MANIFEST.csv`, or `RC1_SHA256SUMS.txt` was generated.
The partial clean rebuild outputs remain under `build/rc1/rebuild/` for audit
and are not an install package.

## Safety

No game installation file, Steam file, EXE, 0007/000E font, MLG/MLG_CN asset,
or production translation was modified. A temporary translation clone was
used only to satisfy the compiler's clean-worktree safety gate; the one
newline-only rewrite produced by `--write` was discarded.
