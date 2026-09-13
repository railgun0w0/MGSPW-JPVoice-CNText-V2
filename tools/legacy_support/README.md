# Vendored legacy format support

This directory contains the audited low-level parser, codec, compression, and
container helpers still used by the V2 builders for SLOT, OLANG, GTT, OHD, and
STAGEDAT resources.

The files are preserved under their historical filenames because they load one
another by sibling path. They are implementation dependencies, not approved
standalone production entry points. Use the manifest-driven and round-trip
builders in the parent `tools/` directory for production builds.

BRIEFING does not depend on this directory; its implementation is in
`core/briefing_nbe.py`, `core/pc_crypto.py`, and `tools/Build-BriefingDat.py`.
