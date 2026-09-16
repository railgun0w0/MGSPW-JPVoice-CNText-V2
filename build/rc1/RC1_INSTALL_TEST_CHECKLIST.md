# RC1 Install Test Checklist

Status: **READY_FOR_CLEAN_INSTALL_TEST = YES**

1. Prepare a clean JPN game installation.
2. Back up every original file named by `RC1_FILE_MANIFEST.csv` and record
   its SHA256.
3. Copy all 20 files from `build/rc1/staging/` to their manifest-relative
   destinations.
4. Replace only `00c7c9f9.xpr` and `001cbbd1.xpr` in `FONT`; do not replace
   `0007ccd8.xpr` or `000ebbe8.xpr`.
5. Do not modify the EXE or install a loader/injector.
6. Start the game and run the smoke test: startup, title/menu, Loading, mission
   start, ordinary subtitles, BRIEFING, weapon/item descriptions, Mother Base
   development UI, small-font UI, save, load, exit, and restart.
7. Restore the backups after testing if any failure is observed.
