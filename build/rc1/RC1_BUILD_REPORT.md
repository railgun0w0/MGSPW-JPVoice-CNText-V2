# RC1 Clean Build Report

Date: 2026-09-16  
Branch: `sol-translation`  

```
RC1_BUILD_STATUS = PASS
FINAL_PATCH_FILE_COUNT = 20
STAGING_FILE_COUNT = 20
00C7_HASH_MATCH = YES
001C_HASH_MATCH = YES
EXE_INCLUDED = NO
0007_INCLUDED = NO
000E_INCLUDED = NO
MLG_CN_PRODUCTION_DEPENDENCY = NO
CLEAN_REBUILD_VERIFIED = YES
READY_FOR_CLEAN_INSTALL_TEST = YES
```

## Zopfli dependency

The historical production fallback is confirmed from repository history and
`tools/legacy_support/Build-JpnSlotFullOlang.py`:

```
zopfli --zlib --i15 -c <input-file>
```

It emits a zlib-wrapped stream to stdout; `i15` is the 15-iteration setting.
The official Google Zopfli source was built locally at commit
`ccf9f0588d4a4509cb1040310ec122243e670ee6` (declared version 1.0.3). The
temporary executable SHA256 is
`2f3287ebf748549e116cd6d45cfbfefb2b4c53aba02b40462a797c3f86386c32`.

For page 220, the merged payload is 76,736 bytes. Standard zlib produced a
28,841-byte stream plus the 16-byte page header (28,857, the former failure).
Zopfli-i15 produced 25,812 bytes plus the header (25,828), leaving 2,844 bytes
under the 28,672-byte fixed capacity. zlib decompression matched the payload.

## Verification matrix

| step | result | evidence |
|---|---|---|
| production compiler from clean temporary translation clone | PASS | 241 files, 21,041 unique rows, 91,609 manifest rows, zero control errors, `BUILD_READY=1` |
| LOOSE_OLANG clean-JPN rebuild | PASS | 14 files, 2,963 translated references, structural/text round-trips pass |
| STAGEDAT_OLANG clean-JPN rebuild | PASS | 123 entries, 16,922 translated references, zero block overflow |
| SLOT_OLANG clean-JPN rebuild | PASS | 144 resources, 68,684 manifest bindings, 110 pages, zero block overflow; DAT size and KEY identical |
| OHD clean-JPN rebuild | PASS | 226 canonical / 904 occurrence records, 4 patched pages, zero hard/block overflow |
| YPK/GTT clean-JPN rebuild | PASS | 36 unique YPK, 77 occurrences, 1,882 records, 2,136 segments, 49 patched pages, zero hard/block overflow |
| unified SLOT merge | PASS | 823 changed tag occurrences, 110 patched pages, written round-trip pass |
| BRIEFING clean-JPN rebuild | PASS | 469 blocks, 5,645 physical rows, zero binding/control/capacity/round-trip errors |
| 00c7 self-owned rebuild | PASS | plaintext `44788a853d8f30da08d184b4aa5c9794ca7a5f115f9d7c03e14ce4cedcf24ae5`; encrypted `13e226b664572cef36be391c0fb78c46ae334955650f86836a2d5d3b3e1580f5` |
| 001c self-owned stock rebuild | PASS | plaintext `f244d4c506fdfa41194e77238cf6a49858030c28d43ce6cfb4029cbc1842bb60`; encrypted `357f12d313cf3c6b8958311afbff759b77b625a617c12800d682c7f1e1e86ce6` |
| staging consistency | PASS | exactly 20 files, unique destinations, no zero-byte files, no EXE/0007/000E/MLG asset |
| full Python test suite | PASS | 23 passed, 2 dependency deprecation warnings |

## Staging and provenance

Staging directory: `build/rc1/staging/`
File manifest: `build/rc1/RC1_FILE_MANIFEST.csv`
SHA256 list: `build/rc1/RC1_SHA256SUMS.txt`

All 20 files are sourced from the current clean-JPN rebuild outputs or the two
self-owned generated font outputs. No `MLG_CN_DERIVED` input, old package file,
0007/000E font, EXE, or game-install path was used.

The package is ready for the user's separate clean-install smoke test. This
report does not claim that installation or gameplay was executed in this phase.
