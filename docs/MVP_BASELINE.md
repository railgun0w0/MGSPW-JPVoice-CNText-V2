# MGSPW MVP Baseline — Freeze / RC1

Date: 2026-09-16  
Branch: `sol-translation`  
Freeze commit: this documentation commit (parent `d1d4a85`)  

## Status

`MVP_STATUS = COMPLETE`

The MVP production truth is frozen. No new low-level builder work, translation
polish, font style tuning, EXE patching, or install-directory changes are part
of this freeze.

## Frozen production facts

- The five legacy production classes are compiled from the current committed
  mappings: YPK/GTT, OHD, SLOT_OLANG, LOOSE_OLANG, and STAGEDAT_OLANG.
- BRIEFING_NBE is a separate committed production pipeline: 469 blocks and
  5,645 physical rows; physical identity is not text-deduplicated.
- Clean JPN `00c7c9f9.xpr` self-owned full rebuild is runtime-proven at
  4096×4096, 56 px, padding 2.
- Clean JPN `001cbbd1.xpr` self-owned stock rebuild is runtime-proven for the
  selector-specific corpus (especially `LOOSE_OLANG/00D0C740`) at 2048×1024,
  51 px, padding 1. The other 709 resource groups remain selector-unknown.
- `EXE_PATCH_REQUIRED = NO` for the proven 001c stock route.
- Production Han glyphs come from an explicitly supplied external SC font;
  clean JPN non-Han/game glyphs are retained according to the font build plan.
  MLG and MLG_CN are reference/proof material only.

## Corpus and verification snapshot

The production compiler dry-run reports 241 files, 21,041 unique rows,
91,609 compiled rows, zero control errors, zero hard overflows, and
`BUILD_READY=1`. The clean-JPN BRIEFING check reports 469/469 files,
5,645/5,645 rows, zero binding/control/capacity errors, and complete source
allocation coverage. The font builder reports exact clean 00c7 and 001c
decrypt/parse/rebuild/encrypt/decrypt round-trips.

## Retractions and known issues

- The historical 001c “fixed 2 MiB limit” is retracted.
- Patched MLG_CN-derived 00c7 append PoCs are not clean-JPN 00c7 structure
  proofs.
- Paz lowercase `z` is a deferred visual QA item; it is not a blocker.
- The historical 21-file package and its 0007/000E font rows are
  reference-only. The frozen RC1 package replaces only the two runtime-proven
  self-owned files `00c7c9f9.xpr` and `001cbbd1.xpr`; no EXE change is needed.

## Frozen subsystems

Translation compiler, BRIEFING builder, clean-JPN XPR architecture, OuterCrypt
destination-seed handling, and the proven 00c7/001c runtime semantics are
frozen. The next phase is RC QA and release assembly, not renewed reverse
engineering.
