# FONT append-only capacity audit: MLG-0007

本报告是只读结构审计。没有修改 Golden FONT/XPR，没有生成厥 bitmap，没有修改 translation/mapping，没有执行 full rebuild、selector-aware rebuild 或安装。

## 最终核心结论

静态布局上，当前 MLG-0007 可以设计为 append-only 增加一个 `厥 U+53A5`：atlas 有连续空白，USER glyph table 没有显式固定 count，charmap 是已覆盖 U+53A5 的 dense direct array，旧 glyph index 可保持不变。
但本轮没有写出或实机加载修改后的 XPR，因此运行时是否接受增长后的 USER descriptor/外层加密文件仍未实机证明。最终安全结论为结构上可行、运行时待验证。

```ini
APPEND_ONLY_FEASIBLE = UNCERTAIN
ATLAS_HAS_SPACE = YES
GLYPH_TABLE_CAN_GROW = YES
CHARMAP_CAN_GROW = YES
OLD_GLYPH_INDICES_CAN_STAY_FIXED = YES
FULL_REBUILD_REQUIRED = NO for one glyph; section reflow required for about 200 glyphs
```

## 1. Atlas capacity

- 尺寸：`4096x4096`；format=`2`；tiled=`0`；endian=`0`；pitch=`4096`。
- 现有 glyph UV rectangle：3209 个，全部唯一；重叠对：0；UV 使用范围：`x=0..4089, y=1..3331`。
- 实际非零 texel：5454755；非零像素 bbox：`[2, 1, 4087, 3328]`。
- 现有 glyph 之后的连续空白矩形：`x=0,y=3332,w=4096,h=764`，没有旧 UV rectangle，也没有非零 texel。
- 按现有 CJK 单元 `58x67`、横向步长 `63`、纵向步长 `68` 保守放置，可得到 `65` 列 × `11` 行 = **715** 个安全槽位；因此约 200 个在面积和 packing 上都能容纳。
- 这不是总面积估算：槽位位于旧 UV/像素范围下方，逐格按旧字体的 CJK cell 与间距计算。

## 2. Glyph table

- USER/FontData：file offset `0x90`，size `0x2C768`，end `0x2C7F8`。
- fixed header 后 dense charmap：USER offset `0x16`，last code `U+FF5E`，array count `65375`；map end USER offset `0x1FED4`，8-byte 对齐后 `0x1FED8`。
- glyph table offset：USER `0x1FED8` / file `0x1FF68`；record size `16`；没有 record prefix；suffix `0`。
- glyph records：`3209`；table end USER `0x2C768` / file `0x2C7F8`，正好到 USER payload 末端。
- USER end 到 texture data offset `0x2C87C` 有 `0x84` (132 bytes) 间隔，且当前间隔全为零。单个 record 仅增加 16 bytes，不需要移动 texture。
- 在保持 texture offset 完全不变的条件下，间隔最多容纳 `8` 个完整 16-byte record（余 `4` bytes）；因此 1 个可原位追加，约 200 个不行。
- 0007 没有显式 glyph-count 字段；record count 由 USER payload 尾部减去 record offset 后按 16-byte record 推导。因此单字 PoC 需要扩大 USER descriptor size，而不是寻找未知 count 字段。

## 3. Charmap

- mapped codepoints：`3208`；非零 glyph index 恰好使用 `1..3208`，只有 record 0 未被引用。
- entry 是 big-endian u16，按 Unicode codepoint 直接索引；不是按 Unicode 排序的可变长 entry 表，不需要在中间插入。
- `U+53A5` 当前 entry file offset `0xA7F0`，旧值 `0`；PoC 改为新 glyph index `3209`。所有旧 mapping entry 与旧 glyph index 均可保持不变。

## 4. XPR2 growth

- XPR2 header：header_size=`0x2C870`，data_size=`0x1000000`，resource_count=`2`，texture_data_offset=`0x2C87C`。
- TX2D/FontTexture descriptor payload：offset `0x5C`，size `0x34`；raw atlas 从 `0x2C87C` 开始，大小 `0x1000000`。
- USER/FontData descriptor payload：offset `0x90`，size `0x2C768`；单字后 size 应为 `0x2C778`。
- 单字：XPR header_size、data_size、TX2D offset/size、atlas dimensions 不变；只改 USER descriptor size、USER 内目标 charmap entry，并在 USER 尾部追加 16-byte record。
- 约 200 字：USER 增加 `0xC80`，超出当前 texture 前间隔，必须把 texture data 搬到保持 residue `0x7C` 的新对齐位置（预计新 offset `0x2D87C`）；仍无需重新 pack 整张 atlas，但需要 section reflow/relocation。

## 5. 厥 U+53A5 最小 PoC

- 新 glyph index：`3209`；新 record file offset：`0x2C7F8`。
- 推荐 atlas slot：`u0=0, v0=3333, u1=58, v1=3400`；这只是规划坐标，本轮没有写 bitmap。
- 推荐 record：`bearing_x_raw=4, width=58, advance=62, reserved=0`，与当前主流 CJK record 一致。
- 推荐 raster cell：58×67；没有独立 bearing_y 字段，应沿用现有 67px CJK cell 的 baseline。现有参考字可选：厢、决、缺、卷、厌；它们用于观察笔画密度/上下边界，不代表直接复制像素。
- 需要改变的结构只有：目标 charmap u16、追加一个 GlyphRecord、USER descriptor size。旧 records、旧 atlas 像素、旧 mappings、旧 indices 都不应移动或重编号。

## 6. 额外 glyph record（3209 vs 3208）

- record 0 未被任何非零 charmap entry 引用；其 UV=`5,1..34,68`，像素统计：{'pixel_count': 544, 'ink_bbox_exclusive': [9, 1, 30, 56]}。
- 它不是可安全复用的空槽：有实际绘制像素，形状呈现为缺字/回退框候选。静态文件不能证明 runtime 对 index 0 的全部 fallback 语义，但“未映射 + 可见回退框”足以禁止复用。

## 7. 仍未知、必须实机验证

- 修改 USER descriptor size 后，PC 版 runtime 是否允许 `USER/FontData` 在原 texture offset 前增长。
- runtime 对 charmap index 0 的确切 fallback 行为，以及新追加 index 3209 的加载/渲染行为。
- 厥 bitmap 的实际笔画边界、抗锯齿、baseline 和游戏内视觉效果。
- 修改后的 XPR 外层 filename-seeded 加密、文件长度变化和 loader 校验是否接受。
- 若扩展到约 200 字，texture relocation 后 XPR header/descriptor/对齐字段的 runtime 兼容性。

## 附件

- `font_mlg0007_layout.json`：完整结构、atlas、charmap、record 和增长测量。
- `font_mlg0007_free_regions.csv`：连续空白区域及按 58×67 单元计算的槽位。
- `font_append_poc_plan.json`：厥单字 PoC 的结构变更规划。
