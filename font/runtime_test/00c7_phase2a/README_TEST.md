# 00C7 Phase-2A local runtime test

This package is local-only and was built from clean JPN `font/JPN/00c7c9f9.xpr` plus the external SC font recorded in the build manifest.

1. Back up the installed large-selector `00c7c9f9.xpr` before testing.
2. Replace only that 00C7 file in a disposable test copy of the game installation.
3. Do not replace `001cbbd1.xpr`, do not patch the EXE, and do not alter the repository's clean inputs.
4. Test startup, main menu, large-font Chinese UI, weapon/item descriptions, long text, ASCII/digits/English, kana/game symbols, and several formerly missing Han characters.
5. Restore the backup after testing.

Runtime status remains `CLEAN_JPN_00C7_FULL_REBUILD_RUNTIME = NOT YET TESTED` until real in-game feedback is recorded.
