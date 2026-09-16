# RC1 Release Readiness

Audit date: 2026-09-16  
Branch: `sol-translation`  

## Decision

`RC1_READY = NO` pending one release-assembly decision (the historical package
must be replaced by an explicitly self-owned selector package). This is not a
runtime blocker for the frozen MVP:

```
MVP_STATUS = COMPLETE
BLOCKER_COUNT = 0
MAJOR_COUNT = 1
EXE_PATCH_REQUIRED = NO
MLG_CN_PRODUCTION_DEPENDENCY = NO
CLEAN_REBUILD_VERIFIED = PARTIAL
```

## Answers to the readiness questions

**A — Can all assets be rebuilt from clean JPN?** Partially. The five-class
production compiler dry-run and clean-JPN BRIEFING rebuild check pass. The font
builder reproduces the proven 00c7 and 001c fixtures exactly in an independent
output directory. A final combined RC1 package containing the self-owned 00c7,
001c, and the required selector set has not yet been assembled.

**B — Mandatory local-only inputs:**

- `font/JPN/00c7c9f9.xpr` (encrypted SHA256
  `1f7a18f28d0d67d7a6a65a5286a1e48c97d595829b4c99325fb2b5772b921e8d`).
- `font/JPN/001cbbd1.xpr` (encrypted SHA256
  `5625066b835e6f26f310781fbbd3ef4f9ea93a77be2a4044289c11b74a767414`).
- External source font `C:\Windows\Fonts\Noto Sans SC Bold (TrueType).otf`,
  SHA256 `d1961be1161ea1be08496c920862d06ea5c23a757628f4fd69368de1d9f51bed`.
- Clean JPN BRIEFING source `0076531d.DAT`, SHA256
  `683fef2d84253a56d0af56ad857eb9c891092a598ce19e06bc9858569d94e372`.
- Node package `@oai/artifact-tool` for the JavaScript validators (missing in
  this workstation: `NOT EXECUTED — MISSING LOCAL INPUT`).

Python Pillow/fontTools and the repository scripts are otherwise available.

**C — EXE:** no EXE modification, loader, or injector is required by the
proven 001c stock route.

**D — MLG/MLG_CN:** no production dependency. Existing MLG/MLG_CN trees and
the old full package are `REFERENCE_ONLY`/historical and must not supply
production FontData, charmap, GlyphRecords, or bitmap.

**E/F — Can RC1 be generated today and what blocks it?** The frozen MVP can be
rebuilt, but RC1 packaging is not ready until the selector set is explicitly
assembled from self-owned outputs. This is the sole MAJOR issue; there are no
BLOCKERs.

**G — Shortest next step:** in a dependency-complete environment, rerun the
formal JS checks, regenerate the committed resource outputs from clean JPN,
build the self-owned 00c7/001c outputs using the recorded font input, decide
and document 0007/000e selector inclusion, then assemble and hash the RC1
package according to `FINAL_PATCH_FILE_MANIFEST.csv`. Do not touch the game
installation during this audit.

## Dependency classification

| dependency | classification | evidence/handling |
|---|---|---|
| committed translation mappings and compiler | REQUIRED_AND_DOCUMENTED | production merge report |
| clean JPN 00c7/001c bases | REQUIRED_AND_DOCUMENTED | font manifests and hashes |
| external SC source font | REQUIRED_AND_DOCUMENTED | font manifests and hash |
| clean JPN 0076531d.DAT | REQUIRED_AND_DOCUMENTED | BRIEFING check |
| Pillow/fontTools/Python | REQUIRED_AND_DOCUMENTED | builder scripts |
| `@oai/artifact-tool` | REQUIRED_BUT_UNDOCUMENTED | JS checks unavailable locally; install in release environment |
| old `build/readiness/full_package` fonts | REFERENCE_ONLY | Experimental source provenance; do not ship |
| MLG / MLG_CN XPR and glyph assets | REFERENCE_ONLY | proof/history only |
| historical PoC/backup/fixture trees | OBSOLETE_NOT_USED | excluded from production graph |

## Install/uninstall model (design only)

Manual or small scripted install copies the manifest's generated files into the
game's `mgspw/JPN/disc0_rel` and `mgspw/FONT` destinations after backing up each
original by exact filename and SHA256. It needs write permission to the game
directory (normally administrator approval), but no Steam mode change, loader,
injector, or EXE edit. Uninstall restores the backups; Steam “verify integrity”
is an independent recovery path. Save data is outside the patch file set.
Neither install nor uninstall is executed in this phase.
