# CLEAN JPN 00C7 Phase-2A validation report

## STATIC PASS

- Source font: `Noto Sans SC Bold`; face index `0`; SHA256 `d1961be1161ea1be08496c920862d06ea5c23a757628f4fd69368de1d9f51bed`.
- Raster profile: pixel size `56`, cell height `72`, baseline `56`, padding `2`, 4096×4096 8-bit grayscale.
- Raster bbox: max `56×57`, p50 `56×54`, p95 `56×55`, p99 `56×55`, crop/overflow `0`.
- Glyphs: `343` preserved clean, `2721` generated Han, `3078` total records / `3077` mapped.
- Atlas packed height `3235` / 4096; vertical usage `78.9795%`; bitmap area usage `71.8198%`, padded rectangle area usage `81.3691%`; no overlap and padding `2` validated.
- Plaintext XPR SHA256: `44788a853d8f30da08d184b4aa5c9794ca7a5f115f9d7c03e14ce4cedcf24ae5`.
- Encrypted XPR SHA256: `13e226b664572cef36be391c0fb78c46ae334955650f86836a2d5d3b3e1580f5`.

| static validation | result |
|---|---|
| decrypt_output_is_XPR2 | PASS |
| resource_descriptors_in_bounds | PASS |
| resources_do_not_overlap | PASS |
| USER_parse_succeeds | PASS |
| charmap_indices_valid | PASS |
| count_prefix_equals_record_count | PASS |
| all_UV_rectangles_in_4096x4096 | PASS |
| no_packed_glyph_overlap | PASS |
| no_padding_violation | PASS |
| TX2D_data_size_is_4096_squared | PASS |
| TX2D_pitch_is_4096 | PASS |
| TX2D_format_is_2 | PASS |
| TX2D_tiled_is_0 | PASS |
| TX2D_endian_is_0 | PASS |
| required_production_codepoints_represented | PASS |
| all_Han_use_selected_SC_font | PASS |
| no_MLG_CN_glyph_source | PASS |
| encrypt_decrypt_roundtrip_exact | PASS |

## RUNTIME NOT YET TESTED

`CLEAN_JPN_00C7_FULL_REBUILD_RUNTIME = NOT YET TESTED`

Static parser acceptance is not runtime proof. Replace only the large 00C7 selector in a separately backed-up local test installation after reviewing `font/runtime_test/00c7_phase2a/README_TEST.md`. Do not replace 001C and do not patch the EXE.
