# FONT glyph index boundary audit

本轮只调查 glyph index visibility；没有修改 Golden、translation、0007/000e/001c，也没有制作 TEST-3 类 atlas 包。boundary audit 生成 TEST-4；后续独立生成的 TEST-2B 见其单独报告。

## 直接结论

- current runtime 00c7 logical source：`D:\GAME\test\steam 合金装备大师合集2 合金装备和平行者汉化补丁\JPVoice_CNText_V2\font\JPN_CN\00c7c9f9.xpr`；decrypted logical SHA256：`90ba15daced7bf7cb2b2d24731d0c99c049716f2101262510b2ae554d27157ff`。
- `glyph index 3208` 映射到：`； U+FF1B`。
- TEST-4 只把 `U+53A5` 指向现有 index 3208，所以实机预期显示：`昏；`。
- 当前已知 runtime 证据：index 3208 可用，新增 index 3209 在 TEST-2 失败。

## TEST-4_MAX_EXISTING_INDEX

- 输出：`D:\GAME\test\steam 合金装备大师合集2 合金装备和平行者汉化补丁\JPVoice_CNText_V2\font\font_poc_00c7_diagnostics_boundary\TEST4_MAX_EXISTING_INDEX\00c7c9f9.xpr`
- mapping raw：`0000` → `0c88`；即 `U+53A5 → 3208`。
- record count：`3209`（未变）；mapped codepoint count：`3209`。
- USER size：`0x2C768`（未变）。
- atlas：byte-identical = `True`；parser errors = `[]`。
- encrypted SHA256：`e3383e571c61aeeb164a63b1216bd0df10733df8810fca58355ed26e1acb7caa`；decrypted SHA256：`b01ec4064acc1ee19e5a547a0c5bfe4478cd15130d2d71789f0885d2e8b4dc48`。
- 静态结果：`PASS`。

## 00c7 current logical FontData fixed header

- fixed header raw（USER +0x00..+0x15）：`0000000542860000000000000000000042860000ff5e`
- decoded fields：magic=`0x5`，cell_height=`67.0`，cell_height_2=`67.0`，last_code=`U+FF5E`。
- dense charmap：offset=`0x16`，entries=`65375`，aligned end=`0x1FED8`。
- current 00c7 glyph-table prefix：`(none)`；record offset=`0x1FED8`；record size=`16`；record end=`0x2C768`；suffix=`0` bytes。
- record 前 4 bytes（USER +`0x1FED4`, file `0x1FF64`）：`00000c89`，BE u32=`3209`，与当前 record count `3209` 相等。该字段此前被误归为 alignment/padding。
- 当前 runtime logical font 在 record table 前存在一个高度可信的 u32 glyph_record_count mirror；parser 仍未修改，等待 TEST-2B 实机确认其 runtime visibility。

## 六套 unique font raw comparison

| font | XPR header raw | USER descriptor raw | USER fixed header raw | pre-record 4 bytes | prefix | records | mapped | max index |
|---|---|---|---|---|---|---:|---:|---:|
| MLG-0007 | `58505232000228100100000000000002` | `555345520000008400022708000000000000004400000000` | `0000000542860000000000000000000042860000ff5e` | `00000283` (`643`) | `(none)` | 643 | 642 | 642 |
| MLG-000E | `58505232000220100020000000000002` | `555345520000008400021b88000000000000004400000000` | `0000000542860000000000000000000042860000ff5e` | `000001cb` (`459`) | `(none)` | 459 | 458 | 458 |
| JPN-001C | `58505232000218100020000000000002` | `5553455200000084000214ca000000000000004400000000` | `0000000542840000000000000000000042840000ff1f` | `00000167` (`359`) | `0167` | 359 | 358 | 358 |
| JPN-00C7 | `58505232000290100100000000000002` | `555345520000008400028f32000000000000004400000000` | `0000000542840000000000000000000042840000ff63` | `00000905` (`2309`) | `0905` | 2309 | 2308 | 2308 |
| MLG-0007 | `585052320002c8700100000000000002` | `55534552000000840002c768000000000000004400000000` | `0000000542860000000000000000000042860000ff5e` | `00000c89` (`3209`) | `(none)` | 3209 | 3208 | 3208 |
| MLG-000E | `585052320002c8000100000000000002` | `55534552000000840002c378000000000000004400000000` | `0000000542860000000000000000000042860000ff5e` | `00000c4a` (`3146`) | `(none)` | 3146 | 3145 | 3145 |

固定 header 本身只有已知 cell height / last code 等字段变化；但六套 JPN/MLG comparison content 的 record table 前 4 bytes 都按 `0000 + BE u16` 形式保存了与 record count 相等的值：MLG-0007=`00000283`(643)、MLG-000E=`000001CB`(459)、JPN-001C=`00000167`(359)、JPN-00C7=`00000905`(2309)、MLG_CN-0007=`00000C89`(3209)、MLG_CN-000E=`00000C4A`(3146)。官方 JPN `001c/00c7` 另外把末 2 bytes 暴露为 parser 可见的 prefix；当前 patched runtime 00c7 则把它放在 record_offset-4 的 gap 中。

## XPR / USER / TX2D descriptor raw bytes

| font | TX2D descriptor raw | TX2D/FontTexture header raw | USER descriptor raw | header_size | data_size | texture offset |
|---|---|---|---|---:|---:|---:|
| MLG-0007 | `545832440000005000000034000000000000003800000000` | `0000000300000001000000000000000000000000ffff0000ffff0000200000020000000201ffefff000002480000000000000a00` | `555345520000008400022708000000000000004400000000` | `0x22810` | `0x1000000` | `0x2281C` |
| MLG-000E | `545832440000005000000034000000000000003800000000` | `0000000300000001000000000000000000000000ffff0000ffff00001000000200000002007fe7ff000002480000000000000a00` | `555345520000008400021b88000000000000004400000000` | `0x22010` | `0x200000` | `0x2201C` |
| JPN-001C | `545832440000005000000034000000000000003800000000` | `0000000300000001000000000000000000000000ffff0000ffff00001000000200000002007fe7ff000002480000000000000a00` | `5553455200000084000214ca000000000000004400000000` | `0x21810` | `0x200000` | `0x2181C` |
| JPN-00C7 | `545832440000005000000034000000000000003800000000` | `0000000300000001000000000000000000000000ffff0000ffff0000200000020000000201ffefff000002480000000000000a00` | `555345520000008400028f32000000000000004400000000` | `0x29010` | `0x1000000` | `0x2901C` |
| MLG-0007 | `545832440000005000000034000000000000003800000000` | `0000000300000001000000000000000000000000ffff0000ffff0000200000020000000201ffefff000002480000000000000a00` | `55534552000000840002c768000000000000004400000000` | `0x2C870` | `0x1000000` | `0x2C87C` |
| MLG-000E | `545832440000005000000034000000000000003800000000` | `0000000300000001000000000000000000000000ffff0000ffff0000200000020000000201ffefff000002480000000000000a00` | `55534552000000840002c378000000000000004400000000` | `0x2C800` | `0x1000000` | `0x2C80C` |

## atlas / table topology comparison

| font | atlas | pitch | format/tiled/endian | atlas row count | max v1 | record table offset/end | suffix |
|---|---|---:|---|---:|---:|---|---:|
| MLG-0007 | `4096×4096` | 4096 | `2/0/0` | 9 | 612 | `0x1FED8..0x22708` | 0 |
| MLG-000E | `2048×1024` | 2048 | `2/0/0` | 11 | 748 | `0x1FED8..0x21B88` | 0 |
| JPN-001C | `2048×1024` | 2048 | `2/0/0` | 12 | 804 | `0x1FE5A..0x214CA` | 0 |
| JPN-00C7 | `4096×4096` | 4096 | `2/0/0` | 38 | 2546 | `0x1FEE2..0x28F32` | 0 |
| MLG-0007 | `4096×4096` | 4096 | `2/0/0` | 49 | 3332 | `0x1FED8..0x2C768` | 0 |
| MLG-000E | `4096×4096` | 4096 | `2/0/0` | 53 | 3604 | `0x1FED8..0x2C378` | 0 |

六套字体的 record table 之后 suffix 均为 0；没有发现 table trailer、sentinel、pointer table 或第二个 index table。current runtime 00c7 的 glyph table 直接结束于 USER payload 末端 `0x2C768`。XPR header/resource descriptor 的变化是资源大小/布局镜像，不存在独立 glyph-count 字段。

## count / max-index 全文件候选搜索

搜索覆盖每套 decrypted XPR 全部字节、BE/LE u16/u32 以及 BE/LE float 表示；完整 offsets 保存在 `diagnostic_manifest.json`，下表只列结构上有意义的命中。

### MLG-0007: candidates `[642, 643]`

- `642`：be_u16=0282 count=1 non-texture=[{'file_offset': 130914, 'hex': '0x1FF62', 'region': 'USER/FontData'}]；be_u32=00000282 count=1 non-texture=[{'file_offset': 130912, 'hex': '0x1FF60', 'region': 'USER/FontData'}]
- `643`：be_u16=0283 count=3 non-texture=[{'file_offset': 130918, 'hex': '0x1FF66', 'region': 'USER/FontData'}, {'file_offset': 131336, 'hex': '0x20108', 'region': 'USER/FontData'}, {'file_offset': 133464, 'hex': '0x20958', 'region': 'USER/FontData'}]；be_u32=00000283 count=3 non-texture=[{'file_offset': 130916, 'hex': '0x1FF64', 'region': 'USER/FontData'}, {'file_offset': 131334, 'hex': '0x20106', 'region': 'USER/FontData'}, {'file_offset': 133462, 'hex': '0x20956', 'region': 'USER/FontData'}]

### MLG-000E: candidates `[458, 459]`

- `458`：be_u16=01ca count=2 non-texture=[{'file_offset': 130914, 'hex': '0x1FF62', 'region': 'USER/FontData'}, {'file_offset': 132296, 'hex': '0x204C8', 'region': 'USER/FontData'}]；be_u32=000001ca count=2 non-texture=[{'file_offset': 130912, 'hex': '0x1FF60', 'region': 'USER/FontData'}, {'file_offset': 132294, 'hex': '0x204C6', 'region': 'USER/FontData'}]
- `459`：be_u16=01cb count=2 non-texture=[{'file_offset': 130918, 'hex': '0x1FF66', 'region': 'USER/FontData'}, {'file_offset': 133356, 'hex': '0x208EC', 'region': 'USER/FontData'}]；be_u32=000001cb count=1 non-texture=[{'file_offset': 130916, 'hex': '0x1FF64', 'region': 'USER/FontData'}]

### JPN-001C: candidates `[358, 359]`

- `358`：be_u16=0166 count=1 non-texture=[{'file_offset': 130788, 'hex': '0x1FEE4', 'region': 'USER/FontData'}]；be_u32=00000166 count=1 non-texture=[{'file_offset': 130786, 'hex': '0x1FEE2', 'region': 'USER/FontData'}]
- `359`：be_u16=0167 count=1 non-texture=[{'file_offset': 130792, 'hex': '0x1FEE8', 'region': 'USER/FontData'}]；be_u32=00000167 count=1 non-texture=[{'file_offset': 130790, 'hex': '0x1FEE6', 'region': 'USER/FontData'}]

### JPN-00C7: candidates `[2308, 2309]`

- `2308`：be_u16=0904 count=5 non-texture=[{'file_offset': 130924, 'hex': '0x1FF6C', 'region': 'USER/FontData'}, {'file_offset': 135554, 'hex': '0x21182', 'region': 'USER/FontData'}, {'file_offset': 147479, 'hex': '0x24017', 'region': 'USER/FontData'}, {'file_offset': 149799, 'hex': '0x24927', 'region': 'USER/FontData'}, {'file_offset': 159746, 'hex': '0x27002', 'region': 'USER/FontData'}]；le_u16=0409 count=2 non-texture=[{'file_offset': 51158, 'hex': '0xC7D6', 'region': 'USER/FontData'}, {'file_offset': 165715, 'hex': '0x28753', 'region': 'USER/FontData'}]；be_u32=00000904 count=2 non-texture=[{'file_offset': 135552, 'hex': '0x21180', 'region': 'USER/FontData'}, {'file_offset': 159744, 'hex': '0x27000', 'region': 'USER/FontData'}]；le_u32=04090000 count=1 non-texture=[{'file_offset': 51158, 'hex': '0xC7D6', 'region': 'USER/FontData'}]
- `2309`：be_u16=0905 count=3 non-texture=[{'file_offset': 130928, 'hex': '0x1FF70', 'region': 'USER/FontData'}, {'file_offset': 133398, 'hex': '0x20916', 'region': 'USER/FontData'}, {'file_offset': 141122, 'hex': '0x22742', 'region': 'USER/FontData'}]；le_u16=0509 count=3 non-texture=[{'file_offset': 55854, 'hex': '0xDA2E', 'region': 'USER/FontData'}, {'file_offset': 164915, 'hex': '0x28433', 'region': 'USER/FontData'}, {'file_offset': 165491, 'hex': '0x28673', 'region': 'USER/FontData'}]；be_u32=00000905 count=2 non-texture=[{'file_offset': 130926, 'hex': '0x1FF6E', 'region': 'USER/FontData'}, {'file_offset': 141120, 'hex': '0x22740', 'region': 'USER/FontData'}]；le_u32=05090000 count=1 non-texture=[{'file_offset': 55854, 'hex': '0xDA2E', 'region': 'USER/FontData'}]

### MLG-0007: candidates `[3208, 3209, 3210]`

- `3208`：be_u16=0c88 count=44 non-texture=[{'file_offset': 130780, 'hex': '0x1FEDC', 'region': 'USER/FontData'}, {'file_offset': 142012, 'hex': '0x22ABC', 'region': 'USER/FontData'}, {'file_offset': 143052, 'hex': '0x22ECC', 'region': 'USER/FontData'}, {'file_offset': 144092, 'hex': '0x232DC', 'region': 'USER/FontData'}, {'file_offset': 145132, 'hex': '0x236EC', 'region': 'USER/FontData'}, {'file_offset': 146172, 'hex': '0x23AFC', 'region': 'USER/FontData'}, {'file_offset': 147212, 'hex': '0x23F0C', 'region': 'USER/FontData'}, {'file_offset': 148252, 'hex': '0x2431C', 'region': 'USER/FontData'}, {'file_offset': 149292, 'hex': '0x2472C', 'region': 'USER/FontData'}, {'file_offset': 150332, 'hex': '0x24B3C', 'region': 'USER/FontData'}, {'file_offset': 151372, 'hex': '0x24F4C', 'region': 'USER/FontData'}, {'file_offset': 152412, 'hex': '0x2535C', 'region': 'USER/FontData'}]；le_u16=880c count=8 non-texture=[{'file_offset': 179453, 'hex': '0x2BCFD', 'region': 'USER/FontData'}, {'file_offset': 180493, 'hex': '0x2C10D', 'region': 'USER/FontData'}, {'file_offset': 181533, 'hex': '0x2C51D', 'region': 'USER/FontData'}]
- `3209`：be_u16=0c89 count=6 non-texture=[{'file_offset': 130918, 'hex': '0x1FF66', 'region': 'USER/FontData'}]；le_u16=890c count=11 non-texture=[{'file_offset': 135595, 'hex': '0x211AB', 'region': 'USER/FontData'}, {'file_offset': 135611, 'hex': '0x211BB', 'region': 'USER/FontData'}, {'file_offset': 135627, 'hex': '0x211CB', 'region': 'USER/FontData'}, {'file_offset': 135643, 'hex': '0x211DB', 'region': 'USER/FontData'}, {'file_offset': 135659, 'hex': '0x211EB', 'region': 'USER/FontData'}, {'file_offset': 180569, 'hex': '0x2C159', 'region': 'USER/FontData'}, {'file_offset': 181609, 'hex': '0x2C569', 'region': 'USER/FontData'}]；be_u32=00000c89 count=1 non-texture=[{'file_offset': 130916, 'hex': '0x1FF64', 'region': 'USER/FontData'}]
- `3210`：be_u16=0c8a count=7 non-texture=[{'file_offset': 132668, 'hex': '0x2063C', 'region': 'USER/FontData'}]

### MLG-000E: candidates `[3145, 3146]`

- `3145`：be_u16=0c49 count=45 non-texture=[{'file_offset': 130780, 'hex': '0x1FEDC', 'region': 'USER/FontData'}, {'file_offset': 139052, 'hex': '0x21F2C', 'region': 'USER/FontData'}, {'file_offset': 140092, 'hex': '0x2233C', 'region': 'USER/FontData'}, {'file_offset': 141132, 'hex': '0x2274C', 'region': 'USER/FontData'}, {'file_offset': 142172, 'hex': '0x22B5C', 'region': 'USER/FontData'}, {'file_offset': 143212, 'hex': '0x22F6C', 'region': 'USER/FontData'}, {'file_offset': 144252, 'hex': '0x2337C', 'region': 'USER/FontData'}, {'file_offset': 145292, 'hex': '0x2378C', 'region': 'USER/FontData'}, {'file_offset': 146332, 'hex': '0x23B9C', 'region': 'USER/FontData'}, {'file_offset': 147372, 'hex': '0x23FAC', 'region': 'USER/FontData'}, {'file_offset': 148412, 'hex': '0x243BC', 'region': 'USER/FontData'}, {'file_offset': 149452, 'hex': '0x247CC', 'region': 'USER/FontData'}]；le_u16=490c count=11 non-texture=[{'file_offset': 174413, 'hex': '0x2A94D', 'region': 'USER/FontData'}, {'file_offset': 175453, 'hex': '0x2AD5D', 'region': 'USER/FontData'}, {'file_offset': 176493, 'hex': '0x2B16D', 'region': 'USER/FontData'}, {'file_offset': 179595, 'hex': '0x2BD8B', 'region': 'USER/FontData'}, {'file_offset': 179611, 'hex': '0x2BD9B', 'region': 'USER/FontData'}, {'file_offset': 179627, 'hex': '0x2BDAB', 'region': 'USER/FontData'}, {'file_offset': 179643, 'hex': '0x2BDBB', 'region': 'USER/FontData'}]
- `3146`：be_u16=0c4a count=12 non-texture=[{'file_offset': 130918, 'hex': '0x1FF66', 'region': 'USER/FontData'}]；le_u16=4a0c count=14 non-texture=[{'file_offset': 175529, 'hex': '0x2ADA9', 'region': 'USER/FontData'}, {'file_offset': 176569, 'hex': '0x2B1B9', 'region': 'USER/FontData'}, {'file_offset': 177609, 'hex': '0x2B5C9', 'region': 'USER/FontData'}]；be_u32=00000c4a count=7 non-texture=[{'file_offset': 130916, 'hex': '0x1FF64', 'region': 'USER/FontData'}]

## record index semantics

对多个已知字符，直接读取 `charmap[codepoint]` 后使用 `GlyphRecord[index]` 得到稳定、合理的对应 UV/metrics；`GlyphRecord[index-1]` 是相邻但不同的 atlas rectangle。具体 index、N/N-1 raw record、bitmap stats 和可视化样本见 JSON/PNG。

| character | codepoint | charmap value | direct record UV | N-1 record UV | direct bitmap |
|---|---|---:|---|---|---|
| 昏 | U+660F | 1751 | `189,1769..247,1836` | `126,1769..184,1836` | `1890 px, [5, 7, 53, 59]` |
| 厢 | U+53A2 | 966 | `3969,885..4027,952` | `3906,885..3964,952` | `2127 px, [3, 9, 55, 59]` |
| 决 | U+51B3 | 846 | `504,817..562,884` | `441,817..499,884` | `1572 px, [2, 7, 55, 59]` |
| 缺 | U+7F3A | 2452 | `3402,2449..3460,2516` | `3339,2449..3397,2516` | `1903 px, [2, 7, 55, 59]` |
| 卷 | U+5377 | 954 | `3213,885..3271,952` | `3150,885..3208,952` | `1932 px, [2, 6, 55, 58]` |
| 厌 | U+538C | 961 | `3654,885..3712,952` | `3591,885..3649,952` | `1649 px, [2, 10, 55, 59]` |

结论：`charmap value N → GlyphRecord[N]`，即 `RECORD_INDEX_SEMANTICS = DIRECT`。没有证据支持 one-based `N-1`。
- N 与 N-1 的原始 atlas 可视化样本：`D:\GAME\test\steam 合金装备大师合集2 合金装备和平行者汉化补丁\JPVoice_CNText_V2\font\font_poc_00c7_diagnostics_boundary\index_semantics_direct_vs_previous.png`。

## record 0

- current runtime 00c7 record 0：`{"index": 0, "raw_hex": "00050001002200440004001d00210000", "u0": 5, "v0": 1, "u1": 34, "v1": 68, "bearing_x": 4, "width": 29, "advance": 33, "reserved": 0}`。
- record 0 没有任何非零 charmap entry 引用，但包含实际像素；它仍是 fallback/missing-glyph 候选，不能复用为 3209。

## 前一版 TEST-2 的解释边界

TEST-1 已证明当前 `U+53A5` lookup、00c7 packaging 和 filename-seeded encryption 可访问已有 record；TEST-2 在 atlas 不变、#3209 exact donor record 的条件下仍显示空白。因此 raster、atlas pixel、bitmap polarity、new-slot pitch 已不再是当前优先方向。

当前已找到适用于 runtime-current 00c7 的 count mirror 候选：record_offset-4/file 0x1FF64 的 BE u32。TEST-2B 已按最小变量将其从 3209 改为 3210；只有实机 PASS 后，才能把它正式固化为 runtime-visible 字段并修正 parser。

## 已发现 count-like field 的静态 patch 方案（仅记录，不执行）

对当前 runtime JPN_CN-00C7/MLG-0007：保持旧 record index 不动，在 record table 前 4 bytes（USER +0x1FED4 / file 0x1FF64）把 `00000C89` 改为 `00000C8A`，同步 USER descriptor size 与尾部 record；TEST-2B 正是该最小 patch，等待实机确认。对 clean JPN-001C/00C7：同一 record 前 4-byte 区域分别反映 `00000167`/`00000905`，并且末 2 bytes 被 parser 暴露为 prefix；若未来修改，应同步该 count 与 USER size。

## 最终结论

```ini
MAX_EXISTING_INDEX = 3208
MAX_EXISTING_INDEX_CHARACTER = U+FF1B ；
NEW_INDEX_3209_RUNTIME_RESULT = FAIL
HIDDEN_GLYPH_COUNT_FIELD_FOUND = YES (record_offset-4/file 0x1FF64 BE u32 mirror across all six fonts)
RECORD_INDEX_SEMANTICS = DIRECT
NEXT_REQUIRED_PATCH = await TEST-2B runtime; if PASS, teach parser the record_offset-4 BE u32 count mirror
```

## TEST-4 手动测试

1. 恢复 Golden `00c7c9f9.xpr`。
2. 安装 `TEST4_MAX_EXISTING_INDEX/00c7c9f9.xpr`。
3. 查看同一句文本；预期 `昏厥` 变为 `昏；`。
4. 记录 `PASS / FAIL / CRASH / VISUAL_CORRUPTION`。
5. 测试结束后恢复 Golden。
