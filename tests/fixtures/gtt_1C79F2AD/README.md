# GTT 1C79F2AD golden fixture

This fixture freezes the accepted JPN structure and final Chinese fixed-layout
rebuild for YPK `1C79F2AD`.  It covers 98 records, 123 timed segments, two
byte-identical physical occurrences, multi-segment record 0, and the record 52
alignment-spill case.

The binary files and `expected.json` are generated once by
`tools/Freeze-GttGolden-1C79F2AD.py`.  Normal regression runs must only read
them; they must not silently regenerate the accepted output.
