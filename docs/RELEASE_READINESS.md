# RC1 Release Readiness

Audit date: 2026-09-16  
Branch: `sol-translation`  

## Decision

`RC1_READY = YES`. The tested RC1 selector set is now fixed to the two files
that are actually replaced by the working installation procedure:
`00c7c9f9.xpr` and `001cbbd1.xpr`. `0007ccd8.xpr` and `000ebbe8.xpr` are not
RC1 production files.

```
MVP_STATUS = COMPLETE
BLOCKER_COUNT = 0
MAJOR_COUNT = 0
EXE_PATCH_REQUIRED = NO
MLG_CN_PRODUCTION_DEPENDENCY = NO
CLEAN_REBUILD_VERIFIED = YES
```

## Answers to the readiness questions

**A — Can all assets be rebuilt from clean JPN?** Yes for the frozen RC1 set.
The five-class
production compiler dry-run and clean-JPN BRIEFING rebuild check pass. The font
builder reproduces the proven 00c7 and 001c fixtures exactly in an independent
output directory. The final patch manifest contains the 18 confirmed translated
resource outputs plus those two self-owned font outputs.

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
- Official Google Zopfli v1.0.3 executable for the fixed-capacity YPK/GTT
  fallback: source commit `ccf9f0588d4a4509cb1040310ec122243e670ee6`, exact
  invocation `zopfli --zlib --i15 -c <input-file>`, local executable SHA256
  `2f3287ebf748549e116cd6d45cfbfefb2b4c53aba02b40462a797c3f86386c32`.

Python Pillow/fontTools and the repository scripts are otherwise available.

**C — EXE:** no EXE modification, loader, or injector is required by the
proven 001c stock route.

**D — MLG/MLG_CN:** no production dependency. Existing MLG/MLG_CN trees and
the old full package are `REFERENCE_ONLY`/historical and must not supply
production FontData, charmap, GlyphRecords, or bitmap.

**E/F — Can RC1 be generated today and what blocks it?** Yes. The selector set
is the two-file set proven by the actual runtime installation. There are no
BLOCKERs or MAJOR issues.

**G — Current release step:** the clean rebuild and 20-file staging are complete.
In a dependency-complete environment, rerun the formal JavaScript validators
requiring `@oai/artifact-tool` as an additional release-environment check.
No selector decision remains: RC1 replaces only 00c7 and 001c, with no EXE,
0007, or 000E. Do not touch the game installation during this audit.

The fixed-capacity YPK/GTT production path is now verified with the mandatory
Zopfli fallback; it is not an optional convenience tool.

## Selector/package correction

The existing `tools/Assemble-JpnCnTestPackage.py` and its historical
`build/readiness/full_package` report describe an older 21-file test package
whose font rows point into the Experimental tree. Those `0007ccd8.xpr` and
`000ebbe8.xpr` rows are retained only as historical/reference provenance and
are excluded from the current RC1 manifest. The RC1 package replaces only
`00c7c9f9.xpr` and `001cbbd1.xpr`, matching the real tested installation; no
selector architecture change is being proposed.

## Dependency classification

| dependency | classification | evidence/handling |
|---|---|---|
| committed translation mappings and compiler | REQUIRED_AND_DOCUMENTED | production merge report |
| clean JPN 00c7/001c bases | REQUIRED_AND_DOCUMENTED | font manifests and hashes |
| external SC source font | REQUIRED_AND_DOCUMENTED | font manifests and hash |
| clean JPN 0076531d.DAT | REQUIRED_AND_DOCUMENTED | BRIEFING check |
| Pillow/fontTools/Python | REQUIRED_AND_DOCUMENTED | builder scripts |
| `@oai/artifact-tool` | REQUIRED_BUT_UNDOCUMENTED | JS checks unavailable locally; install in release environment |
| official Zopfli v1.0.3 executable | REQUIRED_AND_DOCUMENTED | YPK/GTT fixed-capacity fallback; exact source/invocation/hash above |
| old `build/readiness/full_package` fonts, including 0007/000E | REFERENCE_ONLY | Historical Experimental source provenance; excluded from RC1 |
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
