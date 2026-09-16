# 001C stock-geometry Phase 2B.1 local runtime test

This fixture is built from clean JPN `font/JPN/001cbbd1.xpr` and the current proven `LOOSE_OLANG/00D0C740` corpus only.

1. Back up the installed `001cbbd1.xpr` in a disposable test copy.
2. Replace only that file; keep the already-proven `00c7c9f9.xpr` unchanged.
3. Do not modify the EXE, use an 001c runtime dimension patch, or use IFEO/debugger interception.
4. Test Loading, small UI, weapon experience/small-number areas, formerly missing Han and fallback-dot behavior.
5. Test ASCII/digits, kana/symbols, baseline, spacing, crop, and texture alignment.
6. Restore the backup after testing.

Runtime status: `CLEAN_JPN_001C_STOCK_SELF_OWNED_RUNTIME = PROVEN` for this exact selector-specific fixture and required corpus, especially `LOOSE_OLANG/00D0C740`. The other 709 UNKNOWN resource groups remain outside the proof scope.
`001C_STOCK_2048x1024_CAPACITY = SUFFICIENT`; `STOCK_PROFILE = 51px / padding 1`; `EXE_PATCH_REQUIRED = NO`.
