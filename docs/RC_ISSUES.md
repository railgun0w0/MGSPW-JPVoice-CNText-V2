# RC1 Issue Ledger

Audit date: 2026-09-16  
Scope: MVP freeze / release-readiness only.

## BLOCKER

None found. Existing production and clean-JPN checks provide a buildable MVP;
no evidence requires an EXE modification or MLG_CN production input.

## MAJOR

None. The RC1 selector/package decision is resolved by the actual tested
installation: replace only self-owned `00c7c9f9.xpr` and `001cbbd1.xpr`.

The older `Assemble-JpnCnTestPackage.py` / `full_package` 0007/000E rows are
historical/reference-only and are excluded from the current RC1 manifest.

## MINOR

None recorded by this audit.

## VISUAL

- `Paz` lowercase `z` may look slightly inconsistent. The current 001c manifest
  identifies it as a generated Noto Sans SC Bold glyph (U+007A, advance 26,
  baseline 51). Defer to later large/small visual-profile harmonization.

## TRANSLATION

No new translation-quality issue was assessed during freeze. Translation text
is frozen and existing validation reports remain authoritative.

## UNKNOWN_NONBLOCKING

- 709 resource groups have not been selector-proven for 001c. The current
  selector-specific runtime proof covers the required corpus, especially
  `LOOSE_OLANG/00D0C740`; no missing-glyph or startup evidence currently makes
  these a blocker.
- The JavaScript validators requiring `@oai/artifact-tool` were not executed
  in this workstation because that package is absent. The committed reports
  and the Python clean-JPN BRIEFING check remain available evidence; rerun the
  JS checks in a dependency-complete environment before release.
- Clean JPN XPR bases and the external source font are local inputs and are not
  committed binaries. Their exact hashes and paths are recorded in the font
  manifests and `RELEASE_READINESS.md`.

## RESOLVED_BUILD_ITEMS

- The former missing-Zopfli build dependency is resolved. Official Google
  Zopfli v1.0.3 was built locally from source commit
  `ccf9f0588d4a4509cb1040310ec122243e670ee6` and verified with the exact
  `--zlib --i15 -c` page-220 reproduction and full YPK/GTT rebuild.
- The former YPK/GTT fixed-capacity overflow is resolved: page 220 now packs
  at 25,828 bytes including its 16-byte header within the 28,672-byte frame.

## RELEASE_TEST_BOUNDARY

- The 20-file RC1 staging assembly, manifest, and SHA256 consistency are
  proven. Installation into a new clean JPN game, RC1 runtime smoke, and full
  gameplay QA remain `NOT YET TESTED`; no `FINAL_RELEASE_READY = YES` claim is
  made.
