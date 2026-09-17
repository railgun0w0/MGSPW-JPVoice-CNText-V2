#!/usr/bin/env python3
"""Audit the 00c7 glyph-index boundary and emit TEST-4 only."""

from __future__ import annotations

import argparse
import hashlib
import json
import struct
import sys
from pathlib import Path

from PIL import Image, ImageDraw

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from core.pc_crypto import filename_seed, outer_transform
from core.xpr_font import XprFont, validate_glyph_rectangles


TARGET_CODEPOINT = 0x53A5
TARGET_CHAR = "厥"
BOUNDARY_INDEX = 3208
DONOR_CODES = {
    "昏": 0x660F,
    "厢": 0x53A2,
    "决": 0x51B3,
    "缺": 0x7F3A,
    "卷": 0x5377,
    "厌": 0x538C,
}
UNIQUE_FONTS = [
    ("JPN-0007", Path("font/JPN/0007ccd8.xpr")),
    ("JPN-000E", Path("font/JPN/000ebbe8.xpr")),
    ("JPN-001C", Path("font/JPN/001cbbd1.xpr")),
    ("JPN-00C7", Path("font/JPN/00c7c9f9.xpr")),
    ("MLG-0007", Path("font/MLG_CN/0007ccd8.xpr")),
    ("MLG-000E", Path("font/MLG_CN/000ebbe8.xpr")),
]


def sha256(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def hx(value: int) -> str:
    return f"0x{value:X}"


def load(path: Path) -> tuple[bytes, bytes, XprFont]:
    encrypted = path.read_bytes()
    plain = outer_transform(encrypted, filename_seed(path.name))
    return encrypted, plain, XprFont(plain)


def find_all(data: bytes, needle: bytes) -> list[int]:
    offsets: list[int] = []
    start = 0
    while True:
        offset = data.find(needle, start)
        if offset < 0:
            return offsets
        offsets.append(offset)
        start = offset + 1


def region_for(offset: int, font: XprFont) -> str:
    if offset < 0x10 + font.resource_count * 24:
        return "XPR/header-descriptors"
    for resource in font.resources:
        if resource.offset <= offset < resource.offset + resource.size:
            return f"{resource.kind}/{resource.name}"
    if font.texture_data_offset <= offset < font.texture_data_offset + font.data_size:
        return "texture-data"
    return "XPR/header-gap-or-other"


def field_search(plain: bytes, font: XprFont, values: list[int]) -> dict[str, object]:
    formats = {
        "be_u16": ">H",
        "le_u16": "<H",
        "be_u32": ">I",
        "le_u32": "<I",
        "be_float": ">f",
        "le_float": "<f",
    }
    result: dict[str, object] = {}
    for value in values:
        value_result: dict[str, object] = {}
        for label, fmt in formats.items():
            size = struct.calcsize(fmt)
            if value > 0xFFFF and fmt.endswith("H"):
                continue
            try:
                needle = struct.pack(fmt, value if fmt[-1] != "f" else float(value))
            except (OverflowError, struct.error):
                continue
            occurrences = find_all(plain, needle)
            value_result[label] = {
                "raw_hex": needle.hex(),
                "count": len(occurrences),
                "offsets": [
                    {"file_offset": offset, "hex": hx(offset), "region": region_for(offset, font)}
                    for offset in occurrences
                ],
                "size": size,
            }
        result[str(value)] = value_result
    return result


def record_info(font: XprFont, index: int) -> dict[str, object]:
    record = font.font_data.glyphs[index]
    return {
        "index": index,
        "raw_hex": record.packed.hex(),
        "u0": record.u0,
        "v0": record.v0,
        "u1": record.u1,
        "v1": record.v1,
        "bearing_x": record.bearing_x,
        "width": record.width,
        "advance": record.advance,
        "reserved": record.reserved,
    }


def slot_bytes(font: XprFont, record_index: int) -> bytes:
    record = font.font_data.glyphs[record_index]
    return b"".join(
        font.texture.texels[y * font.texture.width + record.u0 : y * font.texture.width + record.u1]
        for y in range(record.v0, record.v1)
    )


def slot_stats(data: bytes, width: int, height: int) -> dict[str, object]:
    points = [(i % width, i // width) for i, value in enumerate(data) if value]
    return {
        "width": width,
        "height": height,
        "nonzero_pixel_count": len(points),
        "ink_bbox_exclusive": (
            None
            if not points
            else [min(x for x, _ in points), min(y for _, y in points), max(x for x, _ in points) + 1, max(y for _, y in points) + 1]
        ),
        "sha256": sha256(data),
    }


def write_index_semantics_png(path: Path, font: XprFont, items: list[dict[str, object]]) -> None:
    """Create a read-only contact sheet of direct N and previous N-1 glyphs."""

    scale = 2
    tile_w, tile_h = 58 * scale, 67 * scale
    label_h = 18
    nearest = getattr(Image, "Resampling", Image).NEAREST
    image = Image.new("L", (tile_w * len(items), (tile_h + label_h) * 2), 0)
    draw = ImageDraw.Draw(image)
    for column, item in enumerate(items):
        index = int(item["charmap_value"])
        direct = font.font_data.glyphs[index]
        previous = font.font_data.glyphs[index - 1]
        for row, (label, record_index, record) in enumerate(
            [("N", index, direct), ("N-1", index - 1, previous)]
        ):
            bitmap = slot_bytes(font, record_index)
            crop = Image.frombytes("L", (record.u1 - record.u0, record.v1 - record.v0), bitmap)
            crop = crop.resize((tile_w, tile_h), nearest)
            x = column * tile_w
            y = row * (tile_h + label_h)
            image.paste(crop, (x, y))
            draw.text((x + 2, y + tile_h + 1), f"{item['codepoint']} {label} {record_index}", fill=255)
    image.save(path)


def patch_test4(golden: XprFont, output_path: Path) -> dict[str, object]:
    payload = bytearray(golden.user.payload)
    map_offset = 0x16 + 2 * TARGET_CODEPOINT
    old_entry = bytes(payload[map_offset : map_offset + 2])
    struct.pack_into(">H", payload, map_offset, BOUNDARY_INDEX)
    if len(payload) != golden.user.size:
        raise RuntimeError("TEST-4 must not change USER size")
    plain = golden.rebuild({("USER", "FontData"): bytes(payload)})
    encrypted = outer_transform(plain, filename_seed(output_path.name))
    output_path.parent.mkdir(parents=True, exist_ok=True)
    output_path.write_bytes(encrypted)
    readback_encrypted, readback_plain, result = load(output_path)
    errors: list[str] = []
    if readback_plain != plain:
        errors.append("filename-seeded encryption readback mismatch")
    if result.font_data.charmap[TARGET_CODEPOINT] != BOUNDARY_INDEX:
        errors.append("TEST-4 target mapping is not 3208")
    if len(result.font_data.glyphs) != len(golden.font_data.glyphs):
        errors.append("TEST-4 changed glyph record count")
    if result.user.size != golden.user.size:
        errors.append("TEST-4 changed USER size")
    if result.texture.texels != golden.texture.texels:
        errors.append("TEST-4 changed atlas")
    old_map = golden.user.payload[0x16 : 0x16 + 2 * len(golden.font_data.charmap)]
    new_map = result.user.payload[0x16 : 0x16 + 2 * len(result.font_data.charmap)]
    target_relative = 2 * TARGET_CODEPOINT
    if old_map[:target_relative] != new_map[:target_relative] or old_map[target_relative + 2 :] != new_map[target_relative + 2 :]:
        errors.append("TEST-4 changed charmap bytes outside U+53A5")
    if result.font_data.glyphs != golden.font_data.glyphs:
        errors.append("TEST-4 changed glyph records")
    if result.tx2d.payload != golden.tx2d.payload:
        errors.append("TEST-4 changed TX2D")
    if result.texture_data_offset != golden.texture_data_offset or result.data_size != golden.data_size:
        errors.append("TEST-4 changed texture offset or data_size")
    parser_errors = validate_glyph_rectangles(result.font_data, result.texture)
    errors.extend(parser_errors)
    return {
        "output": str(output_path),
        "passed": not errors,
        "errors": errors,
        "encrypted_sha256": sha256(readback_encrypted),
        "decrypted_sha256": sha256(readback_plain),
        "filename_seed": hx(filename_seed(output_path.name)),
        "target_raw_before_hex": old_entry.hex(),
        "target_raw_after_hex": new_map[target_relative : target_relative + 2].hex(),
        "target_mapping": result.font_data.charmap[TARGET_CODEPOINT],
        "glyph_count": len(result.font_data.glyphs),
        "mapped_codepoint_count": sum(index != 0 for index in result.font_data.charmap),
        "user_size": result.user.size,
        "atlas_sha256": sha256(result.texture.texels),
        "atlas_unchanged": result.texture.texels == golden.texture.texels,
        "parser_errors": parser_errors,
        "roundtrip": readback_plain == plain,
    }


def build_report(manifest: dict[str, object]) -> str:
    current = manifest["current_runtime_font"]
    boundary = manifest["boundary_evidence"]
    tests = manifest["test4"]
    lines = [
        "# FONT glyph index boundary audit",
        "",
        "本轮只调查 glyph index visibility；没有修改 Golden、translation、0007/000e/001c，也没有制作 TEST-3 类 atlas 包。boundary audit 生成 TEST-4；后续独立生成的 TEST-2B 见其单独报告。",
        "",
        "## 直接结论",
        "",
        f"- current runtime 00c7 logical source：`{current['path']}`；decrypted logical SHA256：`{current['decrypted_sha256']}`。",
        f"- `glyph index 3208` 映射到：`{boundary['character']} {boundary['codepoint']}`。",
        "- TEST-4 只把 `U+53A5` 指向现有 index 3208，所以实机预期显示：`昏；`。",
        "- 当前已知 runtime 证据：index 3208 可用，新增 index 3209 在 TEST-2 失败。",
        "",
        "## TEST-4_MAX_EXISTING_INDEX",
        "",
        f"- 输出：`{tests['output']}`",
        f"- mapping raw：`{tests['target_raw_before_hex']}` → `{tests['target_raw_after_hex']}`；即 `U+53A5 → {tests['target_mapping']}`。",
        f"- record count：`{tests['glyph_count']}`（未变）；mapped codepoint count：`{tests['mapped_codepoint_count']}`。",
        f"- USER size：`{hx(tests['user_size'])}`（未变）。",
        f"- atlas：byte-identical = `{tests['atlas_unchanged']}`；parser errors = `{tests['parser_errors']}`。",
        f"- encrypted SHA256：`{tests['encrypted_sha256']}`；decrypted SHA256：`{tests['decrypted_sha256']}`。",
        f"- 静态结果：`{'PASS' if tests['passed'] else 'FAIL'}`。",
        "",
        "## 00c7 current logical FontData fixed header",
        "",
        f"- fixed header raw（USER +0x00..+0x15）：`{current['fixed_header_raw_hex']}`",
        f"- decoded fields：magic=`{hx(current['magic'])}`，cell_height=`{current['cell_height']}`，cell_height_2=`{current['cell_height_2']}`，last_code=`{current['last_code_hex']}`。",
        f"- dense charmap：offset=`{hx(current['charmap_offset'])}`，entries=`{current['charmap_count']}`，aligned end=`{hx(current['aligned_map_end'])}`。",
        f"- current 00c7 glyph-table prefix：`{current['record_prefix_hex'] or '(none)'}`；record offset=`{hx(current['record_offset'])}`；record size=`16`；record end=`{hx(current['record_table_end'])}`；suffix=`{current['suffix_size']}` bytes。",
        f"- record 前 4 bytes（USER +`{hx(current['record_offset'] - 4)}`, file `0x1FF64`）：`{current['pre_record_4_hex']}`，BE u32=`{current['pre_record_4_be_u32']}`，与当前 record count `3209` 相等。该字段此前被误归为 alignment/padding。",
        "- 当前 runtime logical font 在 record table 前存在一个高度可信的 u32 glyph_record_count mirror；parser 仍未修改，等待 TEST-2B 实机确认其 runtime visibility。",
        "",
        "## 六套 unique font raw comparison",
        "",
        "| font | XPR header raw | USER descriptor raw | USER fixed header raw | pre-record 4 bytes | prefix | records | mapped | max index |",
        "|---|---|---|---|---|---|---:|---:|---:|",
    ]
    for item in manifest["fonts"]:
        lines.append(
            f"| {item['label']} | `{item['xpr_header_raw']}` | `{item['user_descriptor_raw']}` | `{item['fixed_header_raw_hex']}` | `{item['pre_record_4_hex']}` (`{item['pre_record_4_be_u32']}`) | `{item['record_prefix_hex'] or '(none)'}` | {item['record_count']} | {item['mapped_count']} | {item['max_index']} |"
        )
    lines.extend(
        [
            "",
        "固定 header 本身只有已知 cell height / last code 等字段变化；但六套字体的 record table 前 4 bytes 都按 `0000 + BE u16` 形式保存了与 record count 相等的值：JPN-0007=`00000283`(643)、JPN-000E=`000001CB`(459)、JPN-001C=`00000167`(359)、JPN-00C7=`00000905`(2309)、MLG-0007=`00000C89`(3209)、MLG-000E=`00000C4A`(3146)。clean JPN `001c/00c7` 另外把末 2 bytes 暴露为 parser 可见的 prefix；当前 runtime 00c7 则把它放在 record_offset-4 的 gap 中。",
            "",
            "## XPR / USER / TX2D descriptor raw bytes",
            "",
            "| font | TX2D descriptor raw | TX2D/FontTexture header raw | USER descriptor raw | header_size | data_size | texture offset |",
            "|---|---|---|---|---:|---:|---:|",
        ]
    )
    for item in manifest["fonts"]:
        lines.append(
            f"| {item['label']} | `{item['tx2d_descriptor_raw']}` | `{item['tx2d_header_raw']}` | `{item['user_descriptor_raw']}` | `{hx(item['xpr_header_size'])}` | `{hx(item['xpr_data_size'])}` | `{hx(item['texture_offset'])}` |"
        )
    lines.extend(
        [
            "",
            "## atlas / table topology comparison",
            "",
            "| font | atlas | pitch | format/tiled/endian | atlas row count | max v1 | record table offset/end | suffix |",
            "|---|---|---:|---|---:|---:|---|---:|",
        ]
    )
    for item in manifest["fonts"]:
        lines.append(
            f"| {item['label']} | `{item['atlas_width']}×{item['atlas_height']}` | {item['atlas_pitch']} | `{item['atlas_format']}/{item['atlas_tiled']}/{item['atlas_endian']}` | {item['atlas_row_count']} | {item['atlas_max_v1']} | `{hx(item['record_offset'])}..{hx(item['record_table_end'])}` | {item['suffix_size']} |"
        )
    lines.extend(
        [
            "",
            "六套字体的 record table 之后 suffix 均为 0；没有发现 table trailer、sentinel、pointer table 或第二个 index table。current runtime 00c7 的 glyph table 直接结束于 USER payload 末端 `0x2C768`。XPR header/resource descriptor 的变化是资源大小/布局镜像，不存在独立 glyph-count 字段。",
            "",
            "## count / max-index 全文件候选搜索",
            "",
            "搜索覆盖每套 decrypted XPR 全部字节、BE/LE u16/u32 以及 BE/LE float 表示；完整 offsets 保存在 `diagnostic_manifest.json`，下表只列结构上有意义的命中。",
            "",
        ]
    )
    for item in manifest["fonts"]:
        lines.append(f"### {item['label']}: candidates `{item['candidate_values']}`")
        lines.append("")
        for value, formats in item["candidate_search"].items():
            structured = []
            for fmt, result in formats.items():
                relevant = [hit for hit in result["offsets"] if hit["region"] != "texture-data"]
                if relevant:
                    structured.append(f"{fmt}={result['raw_hex']} count={result['count']} non-texture={relevant[:12]}")
            lines.append(f"- `{value}`：" + ("；".join(structured) if structured else "无非-texture 结构命中（texture 命中仍完整记录在 JSON）"))
        lines.append("")
    lines.extend(
        [
            "## record index semantics",
            "",
            "对多个已知字符，直接读取 `charmap[codepoint]` 后使用 `GlyphRecord[index]` 得到稳定、合理的对应 UV/metrics；`GlyphRecord[index-1]` 是相邻但不同的 atlas rectangle。具体 index、N/N-1 raw record、bitmap stats 和可视化样本见 JSON/PNG。",
            "",
            "| character | codepoint | charmap value | direct record UV | N-1 record UV | direct bitmap |",
            "|---|---|---:|---|---|---|",
        ]
    )
    for item in manifest["index_semantics"]:
        lines.append(
            f"| {item['character']} | {item['codepoint']} | {item['charmap_value']} | `{item['direct_record']['u0']},{item['direct_record']['v0']}..{item['direct_record']['u1']},{item['direct_record']['v1']}` | `{item['previous_record']['u0']},{item['previous_record']['v0']}..{item['previous_record']['u1']},{item['previous_record']['v1']}` | `{item['direct_bitmap']['nonzero_pixel_count']} px, {item['direct_bitmap']['ink_bbox_exclusive']}` |"
        )
    lines.extend(
        [
            "",
            "结论：`charmap value N → GlyphRecord[N]`，即 `RECORD_INDEX_SEMANTICS = DIRECT`。没有证据支持 one-based `N-1`。",
            f"- N 与 N-1 的原始 atlas 可视化样本：`{manifest['visual_artifact']}`。",
            "",
            "## record 0",
            "",
            f"- current runtime 00c7 record 0：`{json.dumps(manifest['record0'], ensure_ascii=False)}`。",
            "- record 0 没有任何非零 charmap entry 引用，但包含实际像素；它仍是 fallback/missing-glyph 候选，不能复用为 3209。",
            "",
            "## 前一版 TEST-2 的解释边界",
            "",
            "TEST-1 已证明当前 `U+53A5` lookup、00c7 packaging 和 filename-seeded encryption 可访问已有 record；TEST-2 在 atlas 不变、#3209 exact donor record 的条件下仍显示空白。因此 raster、atlas pixel、bitmap polarity、new-slot pitch 已不再是当前优先方向。",
            "",
            "当前已找到适用于 runtime-current 00c7 的 count mirror 候选：record_offset-4/file 0x1FF64 的 BE u32。TEST-2B 已按最小变量将其从 3209 改为 3210；只有实机 PASS 后，才能把它正式固化为 runtime-visible 字段并修正 parser。",
            "",
            "## 已发现 count-like field 的静态 patch 方案（仅记录，不执行）",
            "",
            "对当前 runtime JPN_CN-00C7/MLG-0007：保持旧 record index 不动，在 record table 前 4 bytes（USER +0x1FED4 / file 0x1FF64）把 `00000C89` 改为 `00000C8A`，同步 USER descriptor size 与尾部 record；TEST-2B 正是该最小 patch，等待实机确认。对 clean JPN-001C/00C7：同一 record 前 4-byte 区域分别反映 `00000167`/`00000905`，并且末 2 bytes 被 parser 暴露为 prefix；若未来修改，应同步该 count 与 USER size。",
            "",
            "## 最终结论",
            "",
            "```ini",
            "MAX_EXISTING_INDEX = 3208",
            "MAX_EXISTING_INDEX_CHARACTER = U+FF1B ；",
            "NEW_INDEX_3209_RUNTIME_RESULT = FAIL",
            "HIDDEN_GLYPH_COUNT_FIELD_FOUND = YES (record_offset-4/file 0x1FF64 BE u32 mirror across all six fonts)",
            "RECORD_INDEX_SEMANTICS = DIRECT",
            "NEXT_REQUIRED_PATCH = await TEST-2B runtime; if PASS, teach parser the record_offset-4 BE u32 count mirror",
            "```",
            "",
            "## TEST-4 手动测试",
            "",
            "1. 恢复 Golden `00c7c9f9.xpr`。",
            "2. 安装 `TEST4_MAX_EXISTING_INDEX/00c7c9f9.xpr`。",
            "3. 查看同一句文本；预期 `昏厥` 变为 `昏；`。",
            "4. 记录 `PASS / FAIL / CRASH / VISUAL_CORRUPTION`。",
            "5. 测试结束后恢复 Golden。",
        ]
    )
    return "\n".join(lines) + "\n"


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("v2_root", type=Path)
    parser.add_argument("--quiet", action="store_true", help="write artifacts without printing the full manifest")
    args = parser.parse_args()
    root = args.v2_root.resolve()
    loaded: list[dict[str, object]] = []
    for label, relative in UNIQUE_FONTS:
        path = root / relative
        encrypted, plain, font = load(path)
        fd = font.font_data
        mapped = fd.mapped()
        nonzero = list(mapped.values())
        candidate_values = sorted({len(fd.glyphs), len(mapped), max(nonzero), max(nonzero) + 1})
        if label == "MLG-0007":
            candidate_values = sorted(set(candidate_values) | {3208, 3209, 3210})
        map_end = 0x16 + 2 * len(fd.charmap)
        aligned_map_end = (map_end + 7) & ~7
        loaded.append(
            {
                "label": label,
                "path": str(path),
                "encrypted_sha256": sha256(encrypted),
                "decrypted_sha256": sha256(plain),
                "xpr_header_raw": plain[:16].hex(),
                "xpr_header_size": font.header_size,
                "xpr_data_size": font.data_size,
                "texture_offset": font.texture_data_offset,
                "user_descriptor_raw": plain[font.user.descriptor_offset : font.user.descriptor_offset + 24].hex(),
                "tx2d_descriptor_raw": plain[font.tx2d.descriptor_offset : font.tx2d.descriptor_offset + 24].hex(),
                "tx2d_header_raw": font.tx2d.payload.hex(),
                "atlas_width": font.texture.width,
                "atlas_height": font.texture.height,
                "atlas_pitch": font.texture.pitch,
                "atlas_format": font.texture.data_format,
                "atlas_tiled": font.texture.tiled,
                "atlas_endian": font.texture.endian,
                "atlas_row_count": len({record.v0 for record in fd.glyphs}),
                "atlas_max_v1": max(record.v1 for record in fd.glyphs),
                "fixed_header_raw_hex": fd.payload[:0x16].hex(),
                "magic": fd.magic,
                "cell_height": fd.cell_height,
                "cell_height_2": fd.cell_height_2,
                "last_code": fd.last_code,
                "last_code_hex": f"U+{fd.last_code:04X}",
                "charmap_offset": 0x16,
                "charmap_count": len(fd.charmap),
                "aligned_map_end": aligned_map_end,
                "record_prefix_hex": fd.record_prefix.hex(),
                "record_offset": fd.record_offset,
                "record_table_end": fd.record_offset + len(fd.glyphs) * 16,
                "pre_record_4_hex": fd.payload[fd.record_offset - 4 : fd.record_offset].hex(),
                "pre_record_4_be_u32": struct.unpack_from(">I", fd.payload, fd.record_offset - 4)[0],
                "suffix_size": len(fd.suffix),
                "record_count": len(fd.glyphs),
                "mapped_count": len(mapped),
                "max_index": max(nonzero),
                "candidate_values": candidate_values,
                "candidate_search": field_search(plain, font, candidate_values),
                "record0": record_info(font, 0),
            }
        )

    current_path = root / "font" / "JPN_CN" / "00c7c9f9.xpr"
    current_encrypted, current_plain, current = load(current_path)
    current_fd = current.font_data
    boundary_codepoints = [cp for cp, index in enumerate(current_fd.charmap) if index == BOUNDARY_INDEX]
    if len(boundary_codepoints) != 1:
        raise RuntimeError(f"expected exactly one codepoint for index 3208, got {boundary_codepoints}")
    boundary_codepoint = boundary_codepoints[0]
    boundary_record = record_info(current, BOUNDARY_INDEX)
    previous_record = record_info(current, BOUNDARY_INDEX - 1)
    current_donor_index = current_fd.charmap[DONOR_CODES["昏"]]
    index_semantics: list[dict[str, object]] = []
    for character, codepoint in DONOR_CODES.items():
        index = current_fd.charmap[codepoint]
        direct = record_info(current, index)
        previous = record_info(current, index - 1) if index > 0 else None
        direct_rect = current_fd.glyphs[index]
        bitmap = slot_bytes(current, index)
        points = [(i % (direct_rect.u1 - direct_rect.u0), i // (direct_rect.u1 - direct_rect.u0)) for i, value in enumerate(bitmap) if value]
        index_semantics.append(
            {
                "character": character,
                "codepoint": f"U+{codepoint:04X}",
                "charmap_value": index,
                "direct_record": direct,
                "previous_record": previous,
                "direct_bitmap": slot_stats(bitmap, direct_rect.u1 - direct_rect.u0, direct_rect.v1 - direct_rect.v0),
            }
        )

    output_root = root / "font" / "font_poc_00c7_diagnostics_boundary"
    test4_path = output_root / "TEST4_MAX_EXISTING_INDEX" / "00c7c9f9.xpr"
    test4 = patch_test4(current, test4_path)
    visual_path = output_root / "index_semantics_direct_vs_previous.png"
    write_index_semantics_png(visual_path, current, index_semantics)
    manifest = {
        "golden_current_runtime_00c7": {
            "path": str(current_path),
            "encrypted_sha256": sha256(current_encrypted),
            "decrypted_sha256": sha256(current_plain),
            "filename_seed": hx(filename_seed(current_path.name)),
        },
        "current_runtime_font": {
            "path": str(current_path),
            "encrypted_sha256": sha256(current_encrypted),
            "decrypted_sha256": sha256(current_plain),
            "fixed_header_raw_hex": current_fd.payload[:0x16].hex(),
            "magic": current_fd.magic,
            "cell_height": current_fd.cell_height,
            "cell_height_2": current_fd.cell_height_2,
            "last_code_hex": f"U+{current_fd.last_code:04X}",
            "charmap_offset": 0x16,
            "charmap_count": len(current_fd.charmap),
            "aligned_map_end": (0x16 + 2 * len(current_fd.charmap) + 7) & ~7,
            "record_prefix_hex": current_fd.record_prefix.hex(),
            "record_offset": current_fd.record_offset,
            "record_table_end": current_fd.record_offset + len(current_fd.glyphs) * 16,
            "pre_record_4_hex": current_fd.payload[current_fd.record_offset - 4 : current_fd.record_offset].hex(),
            "pre_record_4_be_u32": struct.unpack_from(">I", current_fd.payload, current_fd.record_offset - 4)[0],
            "suffix_size": len(current_fd.suffix),
            "record_count": len(current_fd.glyphs),
            "mapped_count": sum(index != 0 for index in current_fd.charmap),
            "max_index": max(current_fd.mapped().values()),
            "atlas_width": current.texture.width,
            "atlas_height": current.texture.height,
            "atlas_pitch": current.texture.pitch,
            "atlas_format": current.texture.data_format,
            "atlas_tiled": current.texture.tiled,
            "atlas_endian": current.texture.endian,
            "atlas_row_count": len({record.v0 for record in current_fd.glyphs}),
            "atlas_max_v1": max(record.v1 for record in current_fd.glyphs),
        },
        "boundary_evidence": {
            "character": chr(boundary_codepoint),
            "codepoint": f"U+{boundary_codepoint:04X}",
            "index": BOUNDARY_INDEX,
            "record": boundary_record,
            "previous_record": previous_record,
        },
        "fonts": loaded,
        "index_semantics": index_semantics,
        "visual_artifact": str(visual_path),
        "record0": record_info(current, 0),
        "test4": test4,
        "notes": [
            "TEST-4 is the only XPR generated in this audit.",
            "No atlas pixels, USER size, GlyphRecord table, or other mapping entries were changed in TEST-4.",
            "All whole-file candidate offsets are retained in candidate_search JSON; report summarizes non-texture hits.",
        ],
    }
    output_root.mkdir(parents=True, exist_ok=True)
    (output_root / "diagnostic_manifest.json").write_text(json.dumps(manifest, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    (output_root / "FONT_GLYPH_INDEX_BOUNDARY_AUDIT.md").write_text(build_report(manifest), encoding="utf-8")
    if not test4["passed"]:
        raise RuntimeError("TEST-4 static validation failed")
    if not args.quiet:
        print(json.dumps(manifest, ensure_ascii=False, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
