# CLEAN JPN 001C stock-geometry Phase 2B validation report

## STATIC PASS

- Base: clean JPN `001cbbd1.xpr` only; no MLG/MLG_CN glyph source.
- Selector corpus: `LOOSE_OLANG/00D0C740`; 68 production rows; 441 unique visible codepoints / 398 Han.
- Source font: `Noto Sans SC Bold`; SHA256 `d1961be1161ea1be08496c920862d06ea5c23a757628f4fd69368de1d9f51bed`.
- Raster profile: pixel size `51`, cell height `67`, baseline `51`, padding `1`.
- Atlas: `2048×1024`, pitch `2048`, format `2`, tiled `0`, endian `0`, data_size `0x200000`.
- GlyphRecords / mapped: `549 / 548`; packed height `1017` / `1024`.
- Plaintext XPR SHA256: `f244d4c506fdfa41194e77238cf6a49858030c28d43ce6cfb4029cbc1842bb60`.
- Encrypted XPR SHA256: `357f12d313cf3c6b8958311afbff759b77b625a617c12800d682c7f1e1e86ce6`.

| static validation | result |
|---|---|
| clean_001c_base_only | PASS |
| count_prefix_2byte_BE | PASS |
| charmap_valid | PASS |
| GlyphRecords_valid | PASS |
| required_001c_corpus_represented | PASS |
| all_required_Han_from_Noto | PASS |
| atlas_2048x1024 | PASS |
| pitch_2048 | PASS |
| data_size_0x200000 | PASS |
| no_crop | PASS |
| no_overlap | PASS |
| no_padding_violation | PASS |
| deterministic_build | PASS |
| encrypt_decrypt_roundtrip | PASS |
| no_MLG_MLG_CN_production_source | PASS |
- Bitmap area `1,921,267`; padded area `2,054,339`; atlas usage `97.959%`; free texels `+42,813`.
- Packed width/height `2048×1017` / stock height `1024`.

## RUNTIME NOT YET TESTED

`CLEAN_JPN_001C_STOCK_SELF_OWNED_RUNTIME = NOT YET TESTED`

`EXE_PATCH_REQUIRED = NO`

Static success is not runtime proof. Replace only `001cbbd1.xpr` in a disposable test copy. Do not patch the EXE, do not replace 00c7, do not use an 001c runtime dimension patch or IFEO/debugger interception, and restore the backup after testing.
