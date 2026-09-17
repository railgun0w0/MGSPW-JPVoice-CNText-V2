# YAHEI_CRASH_DIFF_AUDIT

CRASH_XPR_STRUCTURALLY_IDENTICAL_TO_D_EXCEPT_BITMAP = YES
DIFFERENCES_OUTSIDE_TARGET_SLOT = 0
OUTER_ENCRYPTION_VALID = YES
ATLAS_WRITE_BOUNDS_VALID = YES
MOST_LIKELY_CRASH_CAUSE = runtime-sensitive YaHei UI bitmap/content, or an external replacement/cache issue; no decrypted structural difference was found.

## 判定摘要

- Known-good D：`D:\GAME\test\steam 合金装备大师合集2 合金装备和平行者汉化补丁\JPVoice_CNText_V2\font\font_poc_00c7_diagnostics_boundary\TEST_YAHEI_VS_NOTO_D\CONTROL_D\00c7c9f9.xpr`；crash YaHei：`D:\GAME\test\steam 合金装备大师合集2 合金装备和平行者汉化补丁\JPVoice_CNText_V2\font\font_poc_00c7_diagnostics_boundary\TEST_YAHEI_UI_BOLD_JUE\CANDIDATE_YAHEI_UI_BOLD\00c7c9f9.xpr`。
- encrypted file size：D=`16959612`，YaHei=`16959612`，identical=`YES`。
- decrypted file size：D=`16959612`，YaHei=`16959612`，identical=`YES`。
- decrypted magic：D=`b'XPR2'`，YaHei=`b'XPR2'`；both XPR2=`YES`。
- parser errors：D=`[]`；YaHei=`[]`。
- plaintext byte differences：`1067`；encrypted byte differences with same seed：`1067`。
- changed pixels inside target slot：`1067` / `3886`；changed bytes outside target：`0`。

## 实际 XPR/TX2D 参数

- D texture_data_offset=`0x2C87C`；YaHei=`0x2C87C`。
- D TX2D：`4096x4096`, pitch=`4096`, format=`2`, tiled=`0`, endian=`0`。
- YaHei TX2D：`4096x4096`, pitch=`4096`, format=`2`, tiled=`0`, endian=`0`。
- 物理 target slot 由实际参数计算为每行 `texture_data_offset + y*pitch + x`，范围 x=`0..57`、y=`3333..3399`；第一行 raw offset=`0xD3187C`，最后一行 raw offset=`0xD7387C`。
- 当前 format=2、tiled=0、endian=0，且 pitch=width=4096；因此是每像素 1 byte 的线性 atlas。没有发现 RGBA/4bpp/整行连续写入或 pitch 错配。

## 结构 byte-identical 检查

- XPR header/descriptor prefix：`YES`。
- USER descriptor：`YES`；USER payload：`YES`；USER size=`0x2C778`。
- FontData record offset：D=`0x1FED8`，YaHei=`0x1FED8`。
- glyph count：D=`3210`，YaHei=`3210`；count mirror raw D/YaHei=`00000c8a` / `00000c8a`。
- dense charmap：`YES`；`U+53A5` D/YaHei=`3209` / `3209`。
- all GlyphRecords：`YES`；#3209 D/YaHei=`00000d05003a0d480004003a003e0000` / `00000d05003a0d480004003a003e0000`。
- TX2D descriptor/header：`YES`；texture dimensions/pitch/format：`YES`。
- atlas pixels outside target：`YES`；trailing data：`YES`。

## byte diff 分类

| 分类 | decrypted diff bytes | 结论 |
|---|---:|---|
| XPR header | 0 | byte-identical |
| resource descriptors | 0 | byte-identical |
| USER/FontData fixed header | 0 | byte-identical |
| USER/FontData dense charmap | 0 | byte-identical |
| USER/FontData glyph alignment/prefix | 0 | byte-identical |
| USER/FontData GlyphRecord table | 0 | byte-identical |
| USER/FontData suffix | 0 | byte-identical |
| TX2D/FontTexture header payload | 0 | byte-identical |
| texture data | 1067 | only target slot |
| unclassified/trailing | 0 | byte-identical |

完整明文 diff run 数：`336`；均落在 `texture data` 的 target slot 内。

| raw offset | length | old bytes (D) | new bytes (YaHei) |
|---:|---:|---|---|
| `0xD38882..0xD388B2` | 49 | `78 cf cf cf cf cf cf cf cf cf cf cf cf cf cf cf cf cf cf cf cf cf cf cf cf cf cf cf cf cf cf cf cf cf cf cf cf cf cf cf cf cf cf cf cf cf cf cf 33` | `00 00 00 00 00 00 00 00 00 00 00 00 00 00 00 00 00 00 00 00 00 00 00 00 00 00 00 00 00 00 00 00 00 00 00 00 00 00 00 00 00 00 00 00 00 00 00 00 00` |
| `0xD39881..0xD39882` | 2 | `00 93` | `2c ff` |
| `0xD398B2..0xD398B2` | 1 | `3f` | `b8` |
| `0xD3A881..0xD3A882` | 2 | `00 93` | `2c ff` |
| `0xD3A8B2..0xD3A8B2` | 1 | `3f` | `b8` |
| `0xD3B881..0xD3B882` | 2 | `00 93` | `2c ff` |
| `0xD3B8B2..0xD3B8B2` | 1 | `3f` | `b8` |
| `0xD3C881..0xD3C882` | 2 | `00 93` | `2c ff` |
| `0xD3C8B2..0xD3C8B2` | 1 | `3f` | `b8` |
| `0xD3D881..0xD3D882` | 2 | `00 93` | `2c ff` |
| `0xD3D8B2..0xD3D8B2` | 1 | `3f` | `b8` |
| `0xD3E881..0xD3E882` | 2 | `00 93` | `2c ff` |
| `0xD3E888..0xD3E8B2` | 43 | `93 00 00 00 00 00 00 0b 12 00 00 00 00 00 00 52 75 35 03 00 00 00 00 00 00 06 41 14 00 00 00 00 00 00 00 00 00 00 00 00 00 00 00` | `ff ff ff ff ff ff ff ff ff ff ff ff ff ff ff ff ff ff ff ff ff ff ff ff ff ff ff ff ff ff ff ff ff ff ff ff ff ff ff ff ff ff b8` |
| `0xD3F881..0xD3F882` | 2 | `00 93` | `2c ff` |
| `0xD3F888..0xD3F8B2` | 43 | `93 00 00 00 03 46 a2 f4 97 00 00 00 00 00 00 ba ff ff f2 b5 75 1b 00 00 00 2a ff ff e5 b7 89 31 00 00 00 00 00 00 00 00 00 00 00` | `a8 20 20 20 20 20 5d 74 20 20 20 20 20 20 20 75 48 20 20 20 20 20 20 20 20 25 a1 6c 36 20 20 20 20 20 20 20 20 20 20 20 20 20 17` |
| `0xD40881..0xD40882` | 2 | `00 93` | `2c ff` |
| `0xD40888..0xD40888` | 1 | `93` | `9c` |
| `0xD4088B..0xD4088D` | 3 | `3b e7 ff` | `00 2e b4` |
| `0xD4088F..0xD40891` | 3 | `ff f6 14` | `f3 1e 00` |
| `0xD40896..0xD40897` | 2 | `09 f7` | `17 f8` |
| `0xD40899..0xD4089D` | 5 | `ff ff ff f9 1b` | `c8 68 10 00 00` |
| `0xD408A1..0xD408A1` | 1 | `4d` | `41` |
| `0xD408A5..0xD408A7` | 3 | `ff ff 5d` | `de a8 6a` |
| `0xD41881..0xD41882` | 2 | `00 93` | `2c ff` |
| `0xD41888..0xD41888` | 1 | `93` | `9c` |
| `0xD4188B..0xD4188C` | 2 | `11 f8` | `9c fd` |
| `0xD41890..0xD41891` | 2 | `ff 7d` | `b7 00` |
| `0xD41896..0xD41896` | 1 | `50` | `84` |
| `0xD4189B..0xD4189C` | 2 | `ff 9d` | `f8 59` |
| `0xD418A1..0xD418A1` | 1 | `71` | `8a` |
| `0xD418A7..0xD418A7` | 1 | `36` | `ba` |
| `0xD42881..0xD42882` | 2 | `00 93` | `2c ff` |
| `0xD42888..0xD42888` | 1 | `93` | `9c` |
| `0xD4288B..0xD4288C` | 2 | `00 a7` | `86 ff` |
| `0xD42891..0xD42892` | 2 | `e4 01` | `5e 00` |
| `0xD42895..0xD42896` | 2 | `00 a2` | `0b ec` |
| `0xD4289B..0xD4289C` | 2 | `fe 29` | `e3 0d` |
| `0xD428A1..0xD428A1` | 1 | `94` | `d4` |
| `0xD428A7..0xD428A7` | 1 | `0f` | `71` |
| `0xD43881..0xD43882` | 2 | `00 93` | `2c ff` |
| `0xD43888..0xD43888` | 1 | `93` | `9c` |
| `0xD4388B..0xD4388C` | 2 | `00 44` | `0b e3` |
| `0xD43891..0xD43892` | 2 | `ff 3a` | `ed 16` |
| `0xD43895..0xD43896` | 2 | `08 f0` | `7b ff` |
| `0xD4389B..0xD4389B` | 1 | `b2` | `4f` |
| `0xD438A0..0xD438A1` | 2 | `00 b7` | `1e ff` |
| `0xD438A6..0xD438A7` | 2 | `e7 00` | `ff 28` |
| `0xD44881..0xD44882` | 2 | `00 93` | `2c ff` |
| `0xD44888..0xD44888` | 1 | `93` | `9c` |
| `0xD4488C..0xD4488D` | 2 | `03 ee` | `5d ff` |
| `0xD44892..0xD44892` | 1 | `80` | `a9` |
| `0xD44894..0xD44895` | 2 | `00 55` | `11 f0` |
| `0xD4489A..0xD4489B` | 2 | `ff 39` | `ad 00` |
| `0xD448A0..0xD448A1` | 2 | `00 e7` | `71 ff` |
| `0xD448A6..0xD448A6` | 1 | `c0` | `e0` |
| `0xD45881..0xD45882` | 2 | `00 93` | `2c ff` |
| `0xD45888..0xD45888` | 1 | `93` | `9c` |
| `0xD4588C..0xD4588D` | 2 | `00 ac` | `01 ca` |
| `0xD45891..0xD45892` | 2 | `d7 5a` | `b2 33` |
| `0xD45894..0xD45895` | 2 | `00 b3` | `89 ff` |
| `0xD45899..0xD4589A` | 2 | `ff bd` | `f1 1b` |
| `0xD458A0..0xD458A0` | 1 | `1b` | `c7` |
| `0xD458A6..0xD458B2` | 13 | `99 00 00 00 00 00 00 00 00 00 00 00 00` | `ff ff ff ff ff ff ff ff ff ff ff ff 54` |
| `0xD46881..0xD46882` | 2 | `00 93` | `2c ff` |
| `0xD46888..0xD46888` | 1 | `93` | `9c` |
| `0xD4688A..0xD46895` | 12 | `00 00 00 76 f3 9d 3b 00 00 00 1d fc` | `f4 ff ff ff ff ff ff ff ff ff ff ff` |
| `0xD4689A..0xD4689D` | 4 | `42 00 00 00` | `ff ff ff b4` |
| `0xD4689F..0xD468A0` | 2 | `00 50` | `1d fe` |
| `0xD468A6..0xD468B2` | 13 | `77 07 07 07 07 07 07 08 2b 1a 00 00 00` | `ff ff ff ff ff ff ff ff ff ff ff ff 54` |
| `0xD47881..0xD47882` | 2 | `00 93` | `2c ff` |
| `0xD47888..0xD47894` | 13 | `93 02 23 23 23 3a 30 23 23 23 23 23 8e` | `9c 00 f4 ff ff ff ff ff ff ff ff ff ff` |
| `0xD47899..0xD478A0` | 8 | `d7 24 23 23 23 07 00 84` | `ff ff ff ff b4 00 74 ff` |
| `0xD478AF..0xD478B2` | 4 | `fe cc 80 27` | `ff ff ff 54` |
| `0xD48881..0xD48882` | 2 | `00 93` | `2c ff` |
| `0xD48888..0xD4888A` | 3 | `93 13 ff` | `9c 00 f4` |
| `0xD4889D..0xD488A0` | 4 | `ff 33 00 bc` | `b4 00 d7 ff` |
| `0xD488B2..0xD488B2` | 1 | `74` | `54` |
| `0xD49881..0xD49882` | 2 | `00 93` | `2c ff` |
| `0xD49888..0xD4988A` | 3 | `93 13 ff` | `9c 00 f4` |
| `0xD4989D..0xD498A0` | 4 | `ff 33 0f fa` | `b4 3d ff ff` |
| `0xD498B2..0xD498B2` | 1 | `47` | `54` |
| `0xD4A881..0xD4A882` | 2 | `00 94` | `2c ff` |
| `0xD4A888..0xD4A88A` | 3 | `93 13 ff` | `9c 00 f4` |
| `0xD4A89D..0xD4A89F` | 3 | `ff 33 59` | `b4 a2 ff` |
| `0xD4A8A4..0xD4A8AC` | 9 | `ff ff ff ff ff ff ff ff ff` | `f9 e8 e8 e8 e8 e8 e8 e8 fd` |
| `0xD4A8B2..0xD4A8B2` | 1 | `19` | `4c` |
| `0xD4B881..0xD4B882` | 2 | `00 96` | `2c ff` |
| `0xD4B888..0xD4B891` | 10 | `90 13 ff ff ff ff ff ff ff ff` | `9c 00 ab b4 b4 b4 b4 b4 b4 dc` |
| `0xD4B897..0xD4B89F` | 9 | `ff ff ff ff ff ff ff 33 a8` | `d4 b4 b4 b4 b4 b4 99 f9 ff` |
| `0xD4B8A4..0xD4B8AC` | 9 | `ff ff ff ff ff ff ff ff ff` | `7f 00 00 00 00 00 00 1c fd` |
| `0xD4B8B1..0xD4B8B2` | 2 | `ec 00` | `f5 0c` |
| `0xD4C881..0xD4C882` | 2 | `00 98` | `2c ff` |
| `0xD4C888..0xD4C891` | 10 | `8d 13 ff ff ff ff ff ff ff ff` | `9c 00 00 00 00 00 00 00 00 88` |
| `0xD4C897..0xD4C89F` | 9 | `ff ff ff ff ff ff ff 3d f1` | `6c 00 00 00 00 00 8d ff ff` |
| `0xD4C8A3..0xD4C8A4` | 2 | `ff d6` | `fa 18` |
| `0xD4C8AB..0xD4C8AC` | 2 | `00 52` | `76 ff` |
| `0xD4C8B1..0xD4C8B1` | 1 | `bf` | `a6` |
| `0xD4D881..0xD4D882` | 2 | `00 99` | `2c ff` |
| `0xD4D888..0xD4D888` | 1 | `8b` | `9c` |
| `0xD4D88B..0xD4D88F` | 5 | `00 00 00 00 00` | `2d 34 34 34 0a` |
| `0xD4D891..0xD4D891` | 1 | `d7` | `88` |
| `0xD4D896..0xD4D897` | 2 | `87 00` | `ff 6c` |
| `0xD4D899..0xD4D89E` | 6 | `00 00 00 00 00 6f` | `10 34 34 3a f3 ff` |
| `0xD4D8A3..0xD4D8A9` | 7 | `ff 75 00 00 00 00 00` | `c8 48 48 48 48 48 30` |
| `0xD4D8AB..0xD4D8AC` | 2 | `00 7d` | `d2 ff` |
| `0xD4D8B1..0xD4D8B1` | 1 | `92` | `4b` |
| `0xD4E881..0xD4E882` | 2 | `00 9e` | `2c ff` |
| `0xD4E888..0xD4E888` | 1 | `86` | `9c` |
| `0xD4E88B..0xD4E88F` | 5 | `00 00 00 00 00` | `e0 ff ff ff 34` |
| `0xD4E891..0xD4E891` | 1 | `d7` | `88` |
| `0xD4E896..0xD4E897` | 2 | `87 00` | `ff 6c` |
| `0xD4E899..0xD4E89E` | 6 | `00 00 00 00 07 e4` | `50 ff ff ff ff ff` |
| `0xD4E8A3..0xD4E8AC` | 10 | `fb 4f 43 43 43 43 43 01 00 a9` | `ad ff ff ff ff ff a5 2d ff ff` |
| `0xD4E8B0..0xD4E8B1` | 2 | `ff 64` | `eb 04` |
| `0xD4F881..0xD4F882` | 2 | `00 a4` | `2c ff` |
| `0xD4F888..0xD4F888` | 1 | `7e` | `9c` |
| `0xD4F88A..0xD4F88F` | 6 | `7f cb cb cb a2 00` | `00 e0 ff ff ff 34` |
| `0xD4F891..0xD4F891` | 1 | `d7` | `88` |
| `0xD4F896..0xD4F89E` | 9 | `87 00 0c cb cb cb cb b1 ff` | `ff 6c 00 50 ff ff ff f4 fc` |
| `0xD4F8A2..0xD4F8A4` | 3 | `ff b2 cf` | `bb 80 ff` |
| `0xD4F8A9..0xD4F8AC` | 4 | `ff 03 00 d6` | `97 89 ff ff` |
| `0xD4F8B0..0xD4F8B1` | 2 | `ff 25` | `95 00` |
| `0xD50881..0xD50882` | 2 | `00 a9` | `2f ff` |
| `0xD50888..0xD50888` | 1 | `76` | `9b` |
| `0xD5088A..0xD5088B` | 2 | `9f ff` | `00 e0` |
| `0xD5088E..0xD5088F` | 2 | `cb 00` | `ff 34` |
| `0xD50891..0xD50891` | 1 | `d7` | `88` |
| `0xD50896..0xD50899` | 4 | `87 00 0f ff` | `ff 6c 00 50` |
| `0xD5089D..0xD5089F` | 3 | `ff ff ff` | `c4 2a b6` |
| `0xD508A2..0xD508A4` | 3 | `ff 51 cf` | `3f 89 ff` |
| `0xD508A9..0xD508AC` | 4 | `ff 03 11 fe` | `8b e2 ff ff` |
| `0xD508B0..0xD508B0` | 1 | `e2` | `3a` |
| `0xD51881..0xD51882` | 2 | `00 b1` | `33 ff` |
| `0xD51888..0xD51888` | 1 | `6e` | `96` |
| `0xD5188A..0xD5188B` | 2 | `9f ff` | `00 e0` |
| `0xD5188E..0xD5188F` | 2 | `cb 00` | `ff 34` |
| `0xD51891..0xD51891` | 1 | `d7` | `88` |
| `0xD51896..0xD51899` | 4 | `87 00 0f ff` | `ff 6c 00 50` |
| `0xD5189D..0xD518A4` | 8 | `ff ff ff ff ff da 03 cf` | `c4 00 00 54 ab 00 92 ff` |
| `0xD518A9..0xD518AD` | 5 | `ff 03 4b ff ff` | `7e 5f 94 ca f8` |
| `0xD518AF..0xD518B0` | 2 | `ff 9f` | `de 00` |
| `0xD52881..0xD52882` | 2 | `00 c0` | `38 ff` |
| `0xD52888..0xD52888` | 1 | `62` | `91` |
| `0xD5288A..0xD5288B` | 2 | `9f ff` | `00 e0` |
| `0xD5288E..0xD5288F` | 2 | `cb 00` | `ff 34` |
| `0xD52891..0xD52891` | 1 | `d7` | `88` |
| `0xD52896..0xD52899` | 4 | `87 00 0f ff` | `ff 6c 00 50` |
| `0xD5289D..0xD528A4` | 8 | `8b e5 ff ff ff 5d 00 d1` | `c4 00 00 00 00 00 ad ff` |
| `0xD528A9..0xD528B0` | 8 | `ff 02 72 ff ff ff ff 51` | `62 00 00 00 06 34 3b 00` |
| `0xD53881..0xD53882` | 2 | `00 d0` | `3d ff` |
| `0xD53888..0xD53888` | 1 | `4f` | `8c` |
| `0xD5388A..0xD5388B` | 2 | `9f ff` | `00 e0` |
| `0xD5388E..0xD5388F` | 2 | `cb 00` | `ff 34` |
| `0xD53891..0xD53891` | 1 | `d7` | `88` |
| `0xD53896..0xD53899` | 4 | `87 00 0f ff` | `ff 6c 00 50` |
| `0xD5389D..0xD538A4` | 8 | `5b 1e d7 ff da 03 00 d4` | `c4 00 00 00 00 00 d1 ff` |
| `0xD538A9..0xD538A9` | 1 | `f7` | `4a` |
| `0xD538AC..0xD538B0` | 5 | `44 c3 ff f3 09` | `00 00 00 00 00` |
| `0xD54881..0xD54882` | 2 | `00 e1` | `4b ff` |
| `0xD54888..0xD54888` | 1 | `3d` | `87` |
| `0xD5488A..0xD5488B` | 2 | `9f ff` | `00 e0` |
| `0xD5488E..0xD5488F` | 2 | `cb 00` | `ff 34` |
| `0xD54891..0xD54891` | 1 | `d7` | `88` |
| `0xD54896..0xD54899` | 4 | `87 00 0f ff` | `ff 6c 00 50` |
| `0xD5489D..0xD5489D` | 1 | `5b` | `c4` |
| `0xD5489F..0xD548A1` | 3 | `18 da 5d` | `00 00 00` |
| `0xD548A3..0xD548A4` | 2 | `00 db` | `f4 ff` |
| `0xD548A9..0xD548A9` | 1 | `ec` | `30` |
| `0xD548AE..0xD548AF` | 2 | `41 76` | `00 00` |
| `0xD55881..0xD55882` | 2 | `00 f1` | `5a ff` |
| `0xD55888..0xD55888` | 1 | `2a` | `7e` |
| `0xD5588A..0xD5588B` | 2 | `9f ff` | `00 e0` |
| `0xD5588E..0xD5588F` | 2 | `cb 00` | `ff 34` |
| `0xD55891..0xD55891` | 1 | `d7` | `88` |
| `0xD55896..0xD55899` | 4 | `87 00 0f ff` | `ff 6c 00 50` |
| `0xD5589D..0xD5589D` | 1 | `5b` | `c4` |
| `0xD558A0..0xD558A4` | 5 | `20 03 00 00 ea` | `00 00 1b ff ff` |
| `0xD558A9..0xD558A9` | 1 | `e2` | `10` |
| `0xD56881..0xD56882` | 2 | `03 fe` | `69 ff` |
| `0xD56888..0xD56888` | 1 | `17` | `6f` |
| `0xD5688A..0xD5688B` | 2 | `9f ff` | `00 e0` |
| `0xD5688E..0xD5688F` | 2 | `cb 00` | `ff 34` |
| `0xD56891..0xD56891` | 1 | `d7` | `88` |
| `0xD56896..0xD56899` | 4 | `87 00 0f ff` | `ff 6c 00 50` |
| `0xD5689D..0xD5689D` | 1 | `5b` | `c4` |
| `0xD568A2..0xD568A4` | 3 | `00 00 fa` | `59 ff ff` |
| `0xD568A8..0xD568A9` | 2 | `ff e2` | `fa 05` |
| `0xD57881..0xD57881` | 1 | `12` | `7f` |
| `0xD57888..0xD57888` | 1 | `05` | `5f` |
| `0xD5788A..0xD5788B` | 2 | `9f ff` | `00 e0` |
| `0xD5788E..0xD57891` | 4 | `cb 00 00 d7` | `ff ff ff ff` |
| `0xD57896..0xD57898` | 3 | `87 00 0f` | `ff ff ff` |
| `0xD5789D..0xD5789D` | 1 | `5b` | `c4` |
| `0xD578A2..0xD578A3` | 2 | `00 18` | `9c ff` |
| `0xD578A9..0xD578AA` | 2 | `ff 28` | `53 00` |
| `0xD58881..0xD58881` | 1 | `22` | `9b` |
| `0xD58887..0xD58888` | 2 | `f1 00` | `ff 50` |
| `0xD5888A..0xD5888B` | 2 | `9f ff` | `00 e0` |
| `0xD5888E..0xD58891` | 4 | `cb 00 00 d7` | `ff ff ff ff` |
| `0xD58896..0xD58898` | 3 | `87 00 0f` | `ff ff ff` |
| `0xD5889D..0xD5889D` | 1 | `5b` | `c4` |
| `0xD588A2..0xD588A3` | 2 | `00 3c` | `df ff` |
| `0xD588A9..0xD588AA` | 2 | `ff 7b` | `b6 00` |
| `0xD59881..0xD59881` | 1 | `36` | `b6` |
| `0xD59887..0xD59888` | 2 | `de 00` | `ff 3e` |
| `0xD5988A..0xD5988B` | 2 | `9f ff` | `00 e0` |
| `0xD5989D..0xD5989D` | 1 | `5b` | `c4` |
| `0xD598A1..0xD598A3` | 3 | `00 00 63` | `30 ff ff` |
| `0xD598A9..0xD598AA` | 2 | `ff ce` | `fd 26` |
| `0xD5A881..0xD5A881` | 1 | `5c` | `d7` |
| `0xD5A887..0xD5A888` | 2 | `cb 00` | `ff 23` |
| `0xD5A88A..0xD5A88B` | 2 | `9f ff` | `00 e0` |
| `0xD5A89D..0xD5A89D` | 1 | `5b` | `c4` |
| `0xD5A8A1..0xD5A8A3` | 3 | `00 00 9e` | `99 ff ff` |
| `0xD5A8AA..0xD5A8AB` | 2 | `ff 22` | `9a 00` |
| `0xD5B880..0xD5B881` | 2 | `00 83` | `05 fb` |
| `0xD5B887..0xD5B888` | 2 | `ac 00` | `ff 08` |
| `0xD5B88A..0xD5B88B` | 2 | `9f ff` | `00 e0` |
| `0xD5B89D..0xD5B89D` | 1 | `5b` | `c4` |
| `0xD5B8A0..0xD5B8A3` | 4 | `00 00 00 de` | `0d f3 ff ff` |
| `0xD5B8AA..0xD5B8AB` | 2 | `ff 83` | `f8 1e` |
| `0xD5C880..0xD5C881` | 2 | `00 aa` | `29 ff` |
| `0xD5C887..0xD5C887` | 1 | `83` | `eb` |
| `0xD5C88A..0xD5C890` | 7 | `9f ff ff ff ff ff ff` | `00 49 54 54 54 54 cb` |
| `0xD5C896..0xD5C899` | 4 | `ff ff ff ff` | `dd 54 54 89` |
| `0xD5C89D..0xD5C89D` | 1 | `5b` | `c4` |
| `0xD5C8A0..0xD5C8A2` | 3 | `00 00 23` | `71 ff ff` |
| `0xD5C8AB..0xD5C8AC` | 2 | `ef 0d` | `a3 00` |
| `0xD5D880..0xD5D881` | 2 | `00 d1` | `5d ff` |
| `0xD5D887..0xD5D887` | 1 | `59` | `cc` |
| `0xD5D88A..0xD5D890` | 7 | `95 ef ef ef ef ef f7` | `00 00 00 00 00 0e f5` |
| `0xD5D896..0xD5D899` | 4 | `f2 ef f0 ff` | `92 00 00 50` |
| `0xD5D89D..0xD5D89D` | 1 | `5b` | `c4` |
| `0xD5D89F..0xD5D8A2` | 4 | `00 00 00 84` | `13 ee ff ff` |
| `0xD5D8AB..0xD5D8AC` | 2 | `ff 76` | `fe 36` |
| `0xD5E880..0xD5E881` | 2 | `01 f6` | `97 ff` |
| `0xD5E887..0xD5E887` | 1 | `30` | `a2` |
| `0xD5E88F..0xD5E890` | 2 | `00 a7` | `74 ff` |
| `0xD5E895..0xD5E896` | 2 | `f9 08` | `ff 4c` |
| `0xD5E898..0xD5E89D` | 6 | `0f ff ff ff ff 5b` | `00 30 9c 9c 9c 77` |
| `0xD5E89F..0xD5E8A2` | 4 | `00 00 03 e5` | `97 ff ff ff` |
| `0xD5E8A6..0xD5E8A6` | 1 | `ff` | `e4` |
| `0xD5E8AC..0xD5E8AD` | 2 | `e8 08` | `d3 05` |
| `0xD5F880..0xD5F880` | 1 | `1f` | `d2` |
| `0xD5F886..0xD5F887` | 2 | `fe 09` | `ff 77` |
| `0xD5F88E..0xD5F890` | 3 | `00 07 f2` | `0d e9 ff` |
| `0xD5F895..0xD5F896` | 2 | `c7 00` | `ed 06` |
| `0xD5F898..0xD5F8A1` | 10 | `0c cb cb cb cb 49 00 00 00 53` | `00 00 00 00 00 00 39 fc ff ff` |
| `0xD5F8A5..0xD5F8A7` | 3 | `ff ff ff` | `f3 31 fd` |
| `0xD5F8AD..0xD5F8AD` | 1 | `71` | `86` |
| `0xD6087F..0xD60880` | 2 | `00 46` | `1d ff` |
| `0xD60886..0xD60887` | 2 | `de 00` | `ff 4c` |
| `0xD6088E..0xD6088F` | 2 | `00 50` | `91 ff` |
| `0xD60895..0xD60895` | 1 | `8d` | `96` |
| `0xD6089D..0xD608A1` | 5 | `00 00 00 06 db` | `16 e4 ff ff ff` |
| `0xD608A5..0xD608A8` | 4 | `ff ff ac fd` | `96 00 aa ff` |
| `0xD608AD..0xD608AE` | 2 | `f5 24` | `fe 49` |
| `0xD6187F..0xD61880` | 2 | `00 72` | `6a ff` |
| `0xD61886..0xD61887` | 2 | `b4 00` | `ff 19` |
| `0xD6188D..0xD6188F` | 3 | `00 04 d3` | `45 fd ff` |
| `0xD61894..0xD61895` | 2 | `ff 52` | `fe 2a` |
| `0xD6189C..0xD618A0` | 5 | `00 00 00 00 74` | `04 bf ff ff ff` |
| `0xD618A4..0xD618A8` | 5 | `ff ff f6 15 9d` | `fb 20 00 33 ff` |
| `0xD618AE..0xD618AF` | 2 | `c4 02` | `ed 29` |
| `0xD6287F..0xD62880` | 2 | `00 b2` | `c5 ff` |
| `0xD62886..0xD62886` | 1 | `8b` | `db` |
| `0xD6288C..0xD6288E` | 3 | `00 00 70` | `25 eb ff` |
| `0xD62894..0xD62895` | 2 | `ea 09` | `af 00` |
| `0xD6289B..0xD628A0` | 6 | `00 00 00 00 20 f1` | `04 a5 ff ff ff ff` |
| `0xD628A4..0xD628A6` | 3 | `ff ff 93` | `98 00 00` |
| `0xD628A8..0xD628A9` | 2 | `1a f5` | `b7 ff` |
| `0xD628AF..0xD628B0` | 2 | `74 00` | `e1 1b` |
| `0xD6387E..0xD63880` | 3 | `00 03 f1` | `2b ff ff` |
| `0xD63886..0xD63886` | 1 | `62` | `9d` |
| `0xD6388B..0xD6388E` | 4 | `00 00 30 f1` | `20 e1 ff ff` |
| `0xD63893..0xD63894` | 2 | `ff 7e` | `fc 2d` |
| `0xD6389A..0xD6389F` | 6 | `00 00 00 00 0b d1` | `06 ad ff ff ff ff` |
| `0xD638A3..0xD638A6` | 4 | `ff ff f3 1c` | `ef 14 00 00` |
| `0xD638A8..0xD638A9` | 2 | `00 82` | `26 f8` |
| `0xD638AF..0xD638B1` | 3 | `f8 3f 00` | `ff dd 22` |
| `0xD6487E..0xD6487F` | 2 | `00 38` | `9d ff` |
| `0xD64886..0xD64886` | 1 | `26` | `5a` |
| `0xD6488A..0xD6488D` | 4 | `00 00 2d eb` | `34 e8 ff ff` |
| `0xD64893..0xD64894` | 2 | `f5 14` | `93 00` |
| `0xD64899..0xD6489E` | 6 | `00 00 00 00 00 aa` | `10 b7 ff ff ff ff` |
| `0xD648A3..0xD648A5` | 3 | `ff ff 70` | `63 00 00` |
| `0xD648A9..0xD648AA` | 2 | `0c e8` | `82 ff` |
| `0xD648B0..0xD648B2` | 3 | `f5 42 00` | `ff e5 35` |
| `0xD6587D..0xD6587F` | 3 | `00 00 84` | `25 fc ff` |
| `0xD65885..0xD65886` | 2 | `e3 00` | `f8 0e` |
| `0xD65888..0xD6588C` | 5 | `00 00 00 34 ea` | `01 71 f9 ff ff` |
| `0xD65892..0xD65893` | 2 | `ff 8e` | `de 0e` |
| `0xD65898..0xD6589D` | 6 | `00 00 00 00 01 8d` | `39 e0 ff ff ff ff` |
| `0xD658A2..0xD658A5` | 4 | `ff ff cd 03` | `b4 00 00 00` |
| `0xD658A9..0xD658AA` | 2 | `00 66` | `08 dc` |
| `0xD658B1..0xD658B3` | 3 | `f6 45 00` | `ff f8 4f` |
| `0xD6687D..0xD6687F` | 3 | `00 01 e0` | `19 db ff` |
| `0xD66885..0xD66885` | 1 | `9f` | `b3` |
| `0xD66887..0xD6688B` | 5 | `00 00 08 88 fb` | `2c c9 ff ff ff` |
| `0xD66891..0xD66893` | 3 | `ff d8 0a` | `fb 39 00` |
| `0xD66897..0xD6689C` | 6 | `00 00 00 00 06 a5` | `4f fb ff ff ff ff` |
| `0xD668A1..0xD668A4` | 4 | `ff ff f3 2c` | `e0 13 00 00` |
| `0xD668AA..0xD668AB` | 2 | `03 cb` | `38 f8` |
| `0xD668B2..0xD668B3` | 2 | `d3 02` | `f4 22` |
| `0xD6787E..0xD6787F` | 2 | `40 ff` | `1e e0` |
| `0xD67885..0xD67885` | 1 | `5c` | `56` |
| `0xD67887..0xD67889` | 3 | `00 1f da` | `13 c9 ff` |
| `0xD67891..0xD67892` | 2 | `f0 2f` | `68 00` |
| `0xD67897..0xD6789B` | 5 | `00 00 00 0e bc` | `08 ba ff ff ff` |
| `0xD678A0..0xD678A3` | 4 | `ff ff fe 52` | `f3 31 00 00` |
| `0xD678AB..0xD678AC` | 2 | `22 f0` | `63 ff` |
| `0xD678B1..0xD678B2` | 2 | `ec 22` | `ff 6b` |
| `0xD6887E..0xD68880` | 3 | `6b fc ff` | `00 23 e5` |
| `0xD68884..0xD68885` | 2 | `f8 10` | `e1 04` |
| `0xD68888..0xD6888A` | 3 | `00 65 f9` | `0b bd ff` |
| `0xD68890..0xD68891` | 2 | `f6 3e` | `8a 00` |
| `0xD68898..0xD6889B` | 4 | `00 00 0f 9d` | `09 bd ff ff` |
| `0xD6889F..0xD688A2` | 4 | `ff ff ff 80` | `fa 46 00 00` |
| `0xD688AC..0xD688AC` | 1 | `54` | `95` |
| `0xD688B0..0xD688B2` | 3 | `fe 49 00` | `ff bf 01` |
| `0xD6987F..0xD69881` | 3 | `1f 9b fb` | `00 2f f2` |
| `0xD69884..0xD69884` | 1 | `a9` | `72` |
| `0xD69889..0xD6988B` | 3 | `00 40 f1` | `08 b5 ff` |
| `0xD6988F..0xD69890` | 2 | `e7 36` | `8e 00` |
| `0xD69899..0xD698A2` | 10 | `00 00 00 5e f8 ff ff ff 95 01` | `0a c2 ff ff ff f9 50 00 00 00` |
| `0xD698AC..0xD698AD` | 2 | `00 81` | `04 a8` |
| `0xD698B0..0xD698B1` | 2 | `9f 00` | `f9 28` |
| `0xD6A881..0xD6A884` | 4 | `29 bb ff 4b` | `49 fc de 08` |
| `0xD6A88A..0xD6A88C` | 3 | `00 37 f1` | `07 b5 ff` |
| `0xD6A88E..0xD6A88F` | 2 | `c0 1d` | `80 00` |
| `0xD6A89A..0xD6A8A0` | 7 | `00 00 00 42 f3 ff 89` | `0d cb ff f5 4a 00 00` |
| `0xD6A8AD..0xD6A8B0` | 4 | `00 92 ee 15` | `02 9b ff 86` |
| `0xD6B882..0xD6B884` | 3 | `00 5c 04` | `6a 4f 00` |
| `0xD6B88B..0xD6B88E` | 4 | `00 48 68 01` | `08 b5 56 00` |
| `0xD6B89B..0xD6B89F` | 5 | `00 00 00 45 7b` | `13 bf 34 00 00` |
| `0xD6B8AE..0xD6B8B0` | 3 | `01 36 00` | `00 77 0a` |

## 外层加密复核

- 两文件 filename seed：`0x3AF33BE1` / `0x3AF33BE1`，相同。
- YaHei `decrypt → encrypt → decrypt` plaintext round-trip：`YES`。
- D encrypted SHA256：`a9b4e5e857beb61f0ca493103ba69af33cb5061d441f98e546d18a0a74a3d4bc`；YaHei encrypted SHA256：`353b6313fd60e395e25d00d723510371e3cb11c80ce2ce1a2f2a7a45266fe9e7`。
- D decrypted SHA256：`48460635dd93b6670c548867f9ab8fd21897f8fc8643b5c58ed4488405f8434f`；YaHei decrypted SHA256：`93cc069e0be928b490a589a3d8b0412a5d61b266e68b3ee2e24a5b4897bd6ab7`。

## 结论与边界

静态证据证明 YaHei 文件不是 XPR header、descriptor、USER、charmap、glyph count、GlyphRecord、UV/metrics、TX2D 或 atlas 边界损坏；它与 D 的明文差异仅是目标 58×67 slot 内的 bitmap bytes。

因此当前最可能是 YaHei UI Bold bitmap 内容触发了 runtime 的未捕获限制，或实机替换时存在缓存/文件状态问题。仅凭静态 diff 无法进一步证明具体是哪一个像素/灰度值触发崩溃；本轮不重新生成任何 YaHei candidate，也不修改 Golden。
