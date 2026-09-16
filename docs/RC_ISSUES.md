# RC1 Issue Ledger

Audit date: 2026-09-16  
Scope: MVP freeze / release-readiness only.

## BLOCKER

None found. Existing production and clean-JPN checks provide a buildable MVP;
no evidence requires an EXE modification or MLG_CN production input.

## MAJOR

1. **RC1 selector/package assembly is not yet a single reproducible command.**
   The historical `build/readiness/full_package` report contains 21 files, but
   its three font outputs are sourced from the Experimental tree and it omits
   the proven 001c stock output. Before release, the package must be assembled
   from the current self-owned 00c7 and 001c outputs and the 0007/000e selector
   inclusion decision must be written down. This is a release-assembly gap,
   not a proven runtime failure.

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
