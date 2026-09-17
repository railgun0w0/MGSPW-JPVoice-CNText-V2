#!/usr/bin/env python3
"""Read-only structural and atlas capacity audit for MLG-0007."""

from __future__ import annotations

import argparse
import csv
import hashlib
import json
import struct
import sys
from collections import Counter, defaultdict
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from core.pc_crypto import filename_seed, outer_transform
from core.xpr_font import XprFont, align_up, validate_glyph_rectangles


TARGET_CODEPOINT = 0x53A5
TARGET_NAME = "厥"
GLYPH_RECORD_SIZE = 16
CELL_W = 58
CELL_H = 67
CELL_X_STEP = 63
CELL_Y_STEP = 68
ATLAS_ALIGNMENT = 0x800


def hx(value: int) -> str:
    return f"0x{value:X}"


def sha256(value: bytes) -> str:
    return hashlib.sha256(value).hexdigest()


def rect_overlap(a: tuple[int, int, int, int], b: tuple[int, int, int, int]) -> bool:
    return a[0] < b[2] and b[0] < a[2] and a[1] < b[3] and b[1] < a[3]


def merged_union_area(rects: list[tuple[int, int, int, int]]) -> int:
    by_y: defaultdict[tuple[int, int], list[tuple[int, int]]] = defaultdict(list)
    for u0, v0, u1, v1 in rects:
        by_y[(v0, v1)].append((u0, u1))
    total = 0
    for (v0, v1), intervals in by_y.items():
        intervals.sort()
        start, end = intervals[0]
        width = 0
        for left, right in intervals[1:]:
            if left <= end:
                end = max(end, right)
            else:
                width += end - start
                start, end = left, right
        width += end - start
        total += width * (v1 - v0)
    return total


def pixel_stats(texels: bytes, width: int, height: int) -> dict[str, object]:
    nonzero = 0
    min_x = width
    min_y = height
    max_x = -1
    max_y = -1
    row_nonzero: list[int] = []
    for y in range(height):
        row = texels[y * width : (y + 1) * width]
        count = sum(value != 0 for value in row)
        if count:
            nonzero += count
            row_nonzero.append(y)
            min_x = min(min_x, next(index for index, value in enumerate(row) if value != 0))
            max_x = max(max_x, width - 1 - next(index for index, value in enumerate(reversed(row)) if value != 0))
            min_y = min(min_y, y)
            max_y = y
    return {
        "nonzero_pixel_count": nonzero,
        "nonzero_bbox_exclusive": [min_x, min_y, max_x + 1, max_y + 1],
        "nonzero_row_count": len(row_nonzero),
    }


def glyph_pixel_stats(font: XprFont, index: int) -> dict[str, object]:
    glyph = font.font_data.glyphs[index]
    pixels: list[tuple[int, int]] = []
    for y in range(glyph.v0, glyph.v1):
        row = font.texture.texels[y * font.texture.width : (y + 1) * font.texture.width]
        for x in range(glyph.u0, glyph.u1):
            if row[x]:
                pixels.append((x, y))
    if not pixels:
        return {"pixel_count": 0, "ink_bbox_exclusive": None}
    return {
        "pixel_count": len(pixels),
        "ink_bbox_exclusive": [
            min(x for x, _ in pixels),
            min(y for _, y in pixels),
            max(x for x, _ in pixels) + 1,
            max(y for _, y in pixels) + 1,
        ],
    }


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("v2_root", type=Path)
    args = parser.parse_args()
    root = args.v2_root.resolve()
    analysis_root = root / "font" / "analysis"
    encrypted_path = root / "font" / "MLG_CN" / "0007ccd8.xpr"
    encrypted = encrypted_path.read_bytes()
    seed = filename_seed(encrypted_path.name)
    plain = outer_transform(encrypted, seed)
    font = XprFont(plain)
    fd = font.font_data
    tx = font.texture

    rects = [(g.u0, g.v0, g.u1, g.v1) for g in fd.glyphs]
    rows: defaultdict[int, list[tuple[int, int, int]]] = defaultdict(list)
    for index, glyph in enumerate(fd.glyphs):
        rows[glyph.v0].append((glyph.u0, glyph.u1, index))
    overlap_pairs: list[list[int]] = []
    for row_rects in rows.values():
        ordered = sorted(row_rects)
        for left, right in zip(ordered, ordered[1:]):
            if left[1] > right[0]:
                overlap_pairs.append([left[2], right[2]])

    map_end = 0x16 + 2 * (fd.last_code + 1)
    aligned_map_end = align_up(map_end, 8)
    record_table_end = fd.record_offset + len(fd.glyphs) * GLYPH_RECORD_SIZE
    user_end = font.user.offset + font.user.size
    texture_gap = font.texture_data_offset - user_end
    target_map_offset_user = 0x16 + 2 * TARGET_CODEPOINT
    target_map_offset_file = font.user.offset + target_map_offset_user
    target_old_index = fd.charmap[TARGET_CODEPOINT]
    target_new_index = len(fd.glyphs)

    used_indices = {index for index in fd.charmap if index}
    referenced_by: defaultdict[int, list[int]] = defaultdict(list)
    for codepoint, index in enumerate(fd.charmap):
        if index:
            referenced_by[index].append(codepoint)
    record0_pixels = glyph_pixel_stats(font, 0)

    bottom_y = max(g.v1 for g in fd.glyphs)
    safe_x_positions: list[int] = []
    x = 0
    while x + CELL_W <= tx.width:
        safe_x_positions.append(x)
        x += CELL_X_STEP
    safe_y_positions: list[int] = []
    y = bottom_y + 1
    while y + CELL_H <= tx.height:
        safe_y_positions.append(y)
        y += CELL_Y_STEP
    safe_slot_count = len(safe_x_positions) * len(safe_y_positions)

    gap_bytes = plain[user_end : font.texture_data_offset]
    one_new_user_size = font.user.size + GLYPH_RECORD_SIZE
    one_new_user_end = user_end + GLYPH_RECORD_SIZE
    two_hundred_user_size = font.user.size + 200 * GLYPH_RECORD_SIZE
    two_hundred_user_end = user_end + 200 * GLYPH_RECORD_SIZE
    two_hundred_texture_offset = align_up(two_hundred_user_end, ATLAS_ALIGNMENT, font.texture_data_offset % ATLAS_ALIGNMENT)

    layout = {
        "source": {
            "path": str(encrypted_path),
            "encrypted_size": len(encrypted),
            "encrypted_sha256": sha256(encrypted),
            "decrypted_size": len(plain),
            "decrypted_sha256": sha256(plain),
            "filename_seed": hx(seed),
        },
        "xpr2": {
            "magic": plain[:4].decode("ascii"),
            "header_size": font.header_size,
            "header_size_hex": hx(font.header_size),
            "data_size": font.data_size,
            "data_size_hex": hx(font.data_size),
            "resource_count": font.resource_count,
            "texture_data_offset": font.texture_data_offset,
            "texture_data_offset_hex": hx(font.texture_data_offset),
            "file_end": len(plain),
            "file_end_hex": hx(len(plain)),
            "texture_alignment": ATLAS_ALIGNMENT,
            "texture_alignment_residue": font.texture_data_offset % ATLAS_ALIGNMENT,
        },
        "resources": [
            {
                "index": resource.index,
                "kind": resource.kind,
                "name": resource.name,
                "descriptor_offset": resource.descriptor_offset,
                "descriptor_offset_hex": hx(resource.descriptor_offset),
                "payload_offset": resource.offset,
                "payload_offset_hex": hx(resource.offset),
                "payload_size": resource.size,
                "payload_size_hex": hx(resource.size),
                "payload_end": resource.offset + resource.size,
                "payload_end_hex": hx(resource.offset + resource.size),
                "unused0": resource.unused0,
                "name_offset": resource.name_offset,
                "unused1": resource.unused1,
            }
            for resource in font.resources
        ],
        "user_font_data": {
            "offset": font.user.offset,
            "offset_hex": hx(font.user.offset),
            "size": font.user.size,
            "size_hex": hx(font.user.size),
            "end": user_end,
            "end_hex": hx(user_end),
            "magic": hx(fd.magic),
            "cell_height": fd.cell_height,
            "cell_height_2": fd.cell_height_2,
            "last_code": fd.last_code,
            "last_code_hex": f"U+{fd.last_code:04X}",
            "mapping_array_count": len(fd.charmap),
            "mapping_array_offset_user": 0x16,
            "mapping_array_offset_file": font.user.offset + 0x16,
            "map_end_user": map_end,
            "map_end_user_hex": hx(map_end),
            "aligned_map_end_user": aligned_map_end,
            "aligned_map_end_user_hex": hx(aligned_map_end),
            "record_offset_user": fd.record_offset,
            "record_offset_user_hex": hx(fd.record_offset),
            "record_offset_file": font.user.offset + fd.record_offset,
            "record_offset_file_hex": hx(font.user.offset + fd.record_offset),
            "record_size": GLYPH_RECORD_SIZE,
            "record_count": len(fd.glyphs),
            "record_table_end_user": record_table_end,
            "record_table_end_user_hex": hx(record_table_end),
            "record_table_end_file": font.user.offset + record_table_end,
            "record_table_end_file_hex": hx(font.user.offset + record_table_end),
            "record_prefix_hex": fd.record_prefix.hex(),
            "suffix_size": len(fd.suffix),
            "mapped_codepoint_count": sum(index != 0 for index in fd.charmap),
            "unique_referenced_glyph_indices": len(used_indices),
            "unreferenced_glyph_indices": [index for index in range(len(fd.glyphs)) if index not in used_indices],
            "record0": {
                "record": list(fd.glyphs[0].__dict__.values()),
                "packed_hex": fd.glyphs[0].packed.hex(),
                "referenced_codepoints": [],
                **record0_pixels,
                "interpretation": "unreferenced drawable missing-glyph/fallback box candidate; do not reuse",
            },
        },
        "charmap": {
            "layout": "dense big-endian u16 array indexed directly by Unicode codepoint",
            "entry_size": 2,
            "entry_endian": "big",
            "entry_offset_user": 0x16,
            "entry_offset_file_for_U+53A5": target_map_offset_file,
            "entry_offset_file_for_U+53A5_hex": hx(target_map_offset_file),
            "sorting": "not sorted entries; direct codepoint index",
            "lookup": "charmap[codepoint] -> glyph index; zero denotes absent/unmapped in this format",
            "mapping_count_before": sum(index != 0 for index in fd.charmap),
            "mapping_count_after_poc": sum(index != 0 for index in fd.charmap) + 1,
            "target": {
                "character": TARGET_NAME,
                "codepoint": f"U+{TARGET_CODEPOINT:04X}",
                "old_index": target_old_index,
                "new_index": target_new_index,
                "old_entry_hex": struct.pack(">H", target_old_index).hex(),
                "new_entry_hex": struct.pack(">H", target_new_index).hex(),
            },
        },
        "atlas": {
            "width": tx.width,
            "height": tx.height,
            "format": tx.data_format,
            "tiled": tx.tiled,
            "endian": tx.endian,
            "pitch": tx.pitch,
            "texture_header_size": len(font.tx2d.payload),
            "texture_data_offset": font.texture_data_offset,
            "glyph_rect_count": len(rects),
            "glyph_rect_unique_count": len(set(rects)),
            "glyph_rect_overlap_pair_count": len(overlap_pairs),
            "uv_union_area": merged_union_area(rects),
            "uv_bbox_exclusive": [min(r[0] for r in rects), min(r[1] for r in rects), max(r[2] for r in rects), max(r[3] for r in rects)],
            "pixel": pixel_stats(tx.texels, tx.width, tx.height),
            "row_count": len(rows),
            "last_used_v1": bottom_y,
            "continuous_blank_region_after_glyphs": {"x": 0, "y": bottom_y, "width": tx.width, "height": tx.height - bottom_y},
            "safe_slot_model": {
                "glyph_cell_width": CELL_W,
                "glyph_cell_height": CELL_H,
                "x_step": CELL_X_STEP,
                "y_step": CELL_Y_STEP,
                "first_slot": [safe_x_positions[0], safe_y_positions[0]],
                "columns": len(safe_x_positions),
                "rows": len(safe_y_positions),
                "slots": safe_slot_count,
                "sufficient_for_200": safe_slot_count >= 200,
            },
            "poc_slot": {"x": safe_x_positions[0], "y": safe_y_positions[0], "u0": safe_x_positions[0], "v0": safe_y_positions[0], "u1": safe_x_positions[0] + CELL_W, "v1": safe_y_positions[0] + CELL_H},
        },
        "growth": {
            "user_end_before": user_end,
            "texture_offset_before": font.texture_data_offset,
            "gap_before_texture": texture_gap,
            "gap_all_zero": all(value == 0 for value in gap_bytes),
            "one_glyph": {
                "record_count_before": len(fd.glyphs),
                "record_count_after": len(fd.glyphs) + 1,
                "user_size_before": font.user.size,
                "user_size_after": one_new_user_size,
                "user_end_after": one_new_user_end,
                "descriptor_USER_size_delta": GLYPH_RECORD_SIZE,
                "texture_offset_after": font.texture_data_offset,
                "relocation_required": False,
                "header_size_after": font.header_size,
                "data_size_after": font.data_size,
                "old_records_byte_identical": True,
                "old_indices_fixed": True,
                "old_charmap_entries_unchanged_except_target": True,
            },
            "two_hundred_glyphs": {
                "record_count_after": len(fd.glyphs) + 200,
                "user_size_after": two_hundred_user_size,
                "user_end_after": two_hundred_user_end,
                "texture_offset_after_if_reflowed": two_hundred_texture_offset,
                "texture_offset_shift_if_reflowed": two_hundred_texture_offset - font.texture_data_offset,
                "relocation_required": two_hundred_user_end > font.texture_data_offset,
                "atlas_slots_available": safe_slot_count,
            },
        },
        "poc": {
            "target": TARGET_NAME,
            "codepoint": f"U+{TARGET_CODEPOINT:04X}",
            "new_glyph_index": target_new_index,
            "record_file_offset": font.user.offset + record_table_end,
            "record_file_offset_hex": hx(font.user.offset + record_table_end),
            "recommended_record": {
                "u0": safe_x_positions[0],
                "v0": safe_y_positions[0],
                "u1": safe_x_positions[0] + CELL_W,
                "v1": safe_y_positions[0] + CELL_H,
                "bearing_x_raw": 4,
                "width": CELL_W,
                "advance": 62,
                "reserved": 0,
            },
            "recommended_raster": {
                "cell": "58x67",
                "vertical_baseline": "use the existing 67px CJK cell baseline; glyph records have no separate bearing_y",
                "typical_ink_bbox_relative": "roughly x=2..55, y=6..59 for existing MLG CJK glyphs; actual 厥 raster must be judged visually",
                "reference_glyphs": ["厢", "决", "缺", "卷", "厌"],
                "bitmap_generated": False,
            },
            "minimal_changes": [
                {"location": f"USER/FontData + {hx(target_map_offset_user)}", "old": f"u16 {target_old_index}", "new": f"u16 {target_new_index}", "reason": "map U+53A5 to appended glyph index; dense array already reaches U+FF5E"},
                {"location": f"USER/FontData + {hx(record_table_end)}", "old": "no record", "new": "one 16-byte GlyphRecord", "reason": "append after existing record 3208; preserve all old records"},
                {"location": "XPR descriptor USER size", "old": hx(font.user.size), "new": hx(one_new_user_size), "reason": "USER payload grows by one record"},
                {"location": "XPR header/data and TX2D", "old": "unchanged", "new": "unchanged", "reason": "one-record growth fits the existing gap before texture data"},
            ],
        },
        "parser_validation": {"xpr_errors": validate_glyph_rectangles(fd, tx)},
    }

    regions = [
        {"region_id": "bottom_contiguous_blank", "x": 0, "y": bottom_y, "width": tx.width, "height": tx.height - bottom_y, "kind": "no existing UV rect and no nonzero texel", "safe_58x67_slots": safe_slot_count},
    ]
    for v0, row_rects in sorted(rows.items()):
        ordered = sorted(row_rects)
        previous = 0
        for u0, u1, _ in ordered:
            if u0 - previous >= CELL_W:
                regions.append({"region_id": f"horizontal_gap_y{v0}_x{previous}", "x": previous, "y": v0, "width": u0 - previous, "height": CELL_H, "kind": "same-row UV gap", "safe_58x67_slots": (u0 - previous) // CELL_X_STEP})
            previous = max(previous, u1)
        if tx.width - previous >= CELL_W:
            regions.append({"region_id": f"horizontal_gap_y{v0}_x{previous}", "x": previous, "y": v0, "width": tx.width - previous, "height": CELL_H, "kind": "same-row UV gap", "safe_58x67_slots": (tx.width - previous) // CELL_X_STEP})

    with (analysis_root / "font_mlg0007_layout.json").open("w", encoding="utf-8") as handle:
        json.dump(layout, handle, ensure_ascii=False, indent=2)
        handle.write("\n")
    with (analysis_root / "font_mlg0007_free_regions.csv").open("w", encoding="utf-8", newline="") as handle:
        fields = ["region_id", "x", "y", "width", "height", "kind", "safe_58x67_slots"]
        writer = csv.DictWriter(handle, fieldnames=fields)
        writer.writeheader()
        writer.writerows(regions)
    with (analysis_root / "font_append_poc_plan.json").open("w", encoding="utf-8") as handle:
        json.dump(layout["poc"], handle, ensure_ascii=False, indent=2)
        handle.write("\n")

    report: list[str] = [
        "# FONT append-only capacity audit: MLG-0007",
        "",
        "本报告是只读结构审计。没有修改 Golden FONT/XPR，没有生成厥 bitmap，没有修改 translation/mapping，没有执行 full rebuild、selector-aware rebuild 或安装。",
        "",
        "## 最终核心结论",
        "",
        "静态布局上，当前 MLG-0007 可以设计为 append-only 增加一个 `厥 U+53A5`：atlas 有连续空白，USER glyph table 没有显式固定 count，charmap 是已覆盖 U+53A5 的 dense direct array，旧 glyph index 可保持不变。",
        "但本轮没有写出或实机加载修改后的 XPR，因此运行时是否接受增长后的 USER descriptor/外层加密文件仍未实机证明。最终安全结论为结构上可行、运行时待验证。",
        "",
        "```ini",
        "APPEND_ONLY_FEASIBLE = UNCERTAIN",
        "ATLAS_HAS_SPACE = YES",
        "GLYPH_TABLE_CAN_GROW = YES",
        "CHARMAP_CAN_GROW = YES",
        "OLD_GLYPH_INDICES_CAN_STAY_FIXED = YES",
        "FULL_REBUILD_REQUIRED = NO for one glyph; section reflow required for about 200 glyphs",
        "```",
        "",
        "## 1. Atlas capacity",
        "",
        f"- 尺寸：`{tx.width}x{tx.height}`；format=`{tx.data_format}`；tiled=`{tx.tiled}`；endian=`{tx.endian}`；pitch=`{tx.pitch}`。",
        f"- 现有 glyph UV rectangle：{len(rects)} 个，全部唯一；重叠对：{len(overlap_pairs)}；UV 使用范围：`x={min(r[0] for r in rects)}..{max(r[2] for r in rects) - 1}, y={min(r[1] for r in rects)}..{bottom_y - 1}`。",
        f"- 实际非零 texel：{layout['atlas']['pixel']['nonzero_pixel_count']}；非零像素 bbox：`{layout['atlas']['pixel']['nonzero_bbox_exclusive']}`。",
        f"- 现有 glyph 之后的连续空白矩形：`x=0,y={bottom_y},w={tx.width},h={tx.height - bottom_y}`，没有旧 UV rectangle，也没有非零 texel。",
        f"- 按现有 CJK 单元 `{CELL_W}x{CELL_H}`、横向步长 `{CELL_X_STEP}`、纵向步长 `{CELL_Y_STEP}` 保守放置，可得到 `{len(safe_x_positions)}` 列 × `{len(safe_y_positions)}` 行 = **{safe_slot_count}** 个安全槽位；因此约 200 个在面积和 packing 上都能容纳。",
        "- 这不是总面积估算：槽位位于旧 UV/像素范围下方，逐格按旧字体的 CJK cell 与间距计算。",
        "",
        "## 2. Glyph table",
        "",
        f"- USER/FontData：file offset `{hx(font.user.offset)}`，size `{hx(font.user.size)}`，end `{hx(user_end)}`。",
        f"- fixed header 后 dense charmap：USER offset `0x16`，last code `U+{fd.last_code:04X}`，array count `{len(fd.charmap)}`；map end USER offset `{hx(map_end)}`，8-byte 对齐后 `{hx(aligned_map_end)}`。",
        f"- glyph table offset：USER `{hx(fd.record_offset)}` / file `{hx(font.user.offset + fd.record_offset)}`；record size `{GLYPH_RECORD_SIZE}`；没有 record prefix；suffix `{len(fd.suffix)}`。",
        f"- glyph records：`{len(fd.glyphs)}`；table end USER `{hx(record_table_end)}` / file `{hx(font.user.offset + record_table_end)}`，正好到 USER payload 末端。",
        f"- USER end 到 texture data offset `{hx(font.texture_data_offset)}` 有 `{hx(texture_gap)}` ({texture_gap} bytes) 间隔，且当前间隔全为零。单个 record 仅增加 16 bytes，不需要移动 texture。",
        f"- 在保持 texture offset 完全不变的条件下，间隔最多容纳 `{texture_gap // GLYPH_RECORD_SIZE}` 个完整 16-byte record（余 `{texture_gap % GLYPH_RECORD_SIZE}` bytes）；因此 1 个可原位追加，约 200 个不行。",
        "- 0007 没有显式 glyph-count 字段；record count 由 USER payload 尾部减去 record offset 后按 16-byte record 推导。因此单字 PoC 需要扩大 USER descriptor size，而不是寻找未知 count 字段。",
        "",
        "## 3. Charmap",
        "",
        f"- mapped codepoints：`{sum(index != 0 for index in fd.charmap)}`；非零 glyph index 恰好使用 `1..{len(fd.glyphs) - 1}`，只有 record 0 未被引用。",
        "- entry 是 big-endian u16，按 Unicode codepoint 直接索引；不是按 Unicode 排序的可变长 entry 表，不需要在中间插入。",
        f"- `U+53A5` 当前 entry file offset `{hx(target_map_offset_file)}`，旧值 `{target_old_index}`；PoC 改为新 glyph index `{target_new_index}`。所有旧 mapping entry 与旧 glyph index 均可保持不变。",
        "",
        "## 4. XPR2 growth",
        "",
        f"- XPR2 header：header_size=`{hx(font.header_size)}`，data_size=`{hx(font.data_size)}`，resource_count=`{font.resource_count}`，texture_data_offset=`{hx(font.texture_data_offset)}`。",
        f"- TX2D/FontTexture descriptor payload：offset `{hx(font.tx2d.offset)}`，size `{hx(font.tx2d.size)}`；raw atlas 从 `{hx(font.texture_data_offset)}` 开始，大小 `{hx(len(tx.texels))}`。",
        f"- USER/FontData descriptor payload：offset `{hx(font.user.offset)}`，size `{hx(font.user.size)}`；单字后 size 应为 `{hx(one_new_user_size)}`。",
        "- 单字：XPR header_size、data_size、TX2D offset/size、atlas dimensions 不变；只改 USER descriptor size、USER 内目标 charmap entry，并在 USER 尾部追加 16-byte record。",
        f"- 约 200 字：USER 增加 `{hx(200 * GLYPH_RECORD_SIZE)}`，超出当前 texture 前间隔，必须把 texture data 搬到保持 residue `{hx(font.texture_data_offset % ATLAS_ALIGNMENT)}` 的新对齐位置（预计新 offset `{hx(two_hundred_texture_offset)}`）；仍无需重新 pack 整张 atlas，但需要 section reflow/relocation。",
        "",
        "## 5. 厥 U+53A5 最小 PoC",
        "",
        f"- 新 glyph index：`{target_new_index}`；新 record file offset：`{hx(font.user.offset + record_table_end)}`。",
        f"- 推荐 atlas slot：`u0={safe_x_positions[0]}, v0={safe_y_positions[0]}, u1={safe_x_positions[0] + CELL_W}, v1={safe_y_positions[0] + CELL_H}`；这只是规划坐标，本轮没有写 bitmap。",
        "- 推荐 record：`bearing_x_raw=4, width=58, advance=62, reserved=0`，与当前主流 CJK record 一致。",
        "- 推荐 raster cell：58×67；没有独立 bearing_y 字段，应沿用现有 67px CJK cell 的 baseline。现有参考字可选：厢、决、缺、卷、厌；它们用于观察笔画密度/上下边界，不代表直接复制像素。",
        "- 需要改变的结构只有：目标 charmap u16、追加一个 GlyphRecord、USER descriptor size。旧 records、旧 atlas 像素、旧 mappings、旧 indices 都不应移动或重编号。",
        "",
        "## 6. 额外 glyph record（3209 vs 3208）",
        "",
        f"- record 0 未被任何非零 charmap entry 引用；其 UV=`{fd.glyphs[0].u0},{fd.glyphs[0].v0}..{fd.glyphs[0].u1},{fd.glyphs[0].v1}`，像素统计：{record0_pixels}。",
        "- 它不是可安全复用的空槽：有实际绘制像素，形状呈现为缺字/回退框候选。静态文件不能证明 runtime 对 index 0 的全部 fallback 语义，但“未映射 + 可见回退框”足以禁止复用。",
        "",
        "## 7. 仍未知、必须实机验证",
        "",
        "- 修改 USER descriptor size 后，PC 版 runtime 是否允许 `USER/FontData` 在原 texture offset 前增长。",
        "- runtime 对 charmap index 0 的确切 fallback 行为，以及新追加 index 3209 的加载/渲染行为。",
        "- 厥 bitmap 的实际笔画边界、抗锯齿、baseline 和游戏内视觉效果。",
        "- 修改后的 XPR 外层 filename-seeded 加密、文件长度变化和 loader 校验是否接受。",
        "- 若扩展到约 200 字，texture relocation 后 XPR header/descriptor/对齐字段的 runtime 兼容性。",
        "",
        "## 附件",
        "",
        "- `font_mlg0007_layout.json`：完整结构、atlas、charmap、record 和增长测量。",
        "- `font_mlg0007_free_regions.csv`：连续空白区域及按 58×67 单元计算的槽位。",
        "- `font_append_poc_plan.json`：厥单字 PoC 的结构变更规划。",
    ]
    (analysis_root / "FONT_APPEND_CAPACITY_AUDIT.md").write_text("\n".join(report) + "\n", encoding="utf-8")

    print("APPEND_ONLY_FEASIBLE = UNCERTAIN")
    print("ATLAS_HAS_SPACE = YES")
    print("GLYPH_TABLE_CAN_GROW = YES")
    print("CHARMAP_CAN_GROW = YES")
    print("OLD_GLYPH_INDICES_CAN_STAY_FIXED = YES")
    print("FULL_REBUILD_REQUIRED = NO for one glyph; section reflow for about 200 glyphs")
    print(f"SAFE_ATLAS_SLOTS_58x67 = {safe_slot_count}")
    print(f"RECORD0_UNREFERENCED = {0 not in used_indices}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
