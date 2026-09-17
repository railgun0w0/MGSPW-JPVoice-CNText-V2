#!/usr/bin/env python3
"""Build TEST-3B: TEST-2B count mirror plus one new atlas slot."""

from __future__ import annotations

import argparse
import hashlib
import json
import struct
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from core.pc_crypto import filename_seed, outer_transform
from core.xpr_font import XprFont, validate_glyph_rectangles


TARGET_CODEPOINT = 0x53A5
DONOR_CODEPOINT = 0x660F
TARGET_INDEX = 3209
USER_MAP_OFFSET = 0x16 + 2 * TARGET_CODEPOINT
COUNT_OFFSET = 0x1FED4
TARGET_RECT = (0, 3333, 58, 3400)
OUTPUT_NAME = "00c7c9f9.xpr"


def sha256(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def hx(value: int) -> str:
    return f"0x{value:X}"


def load(path: Path) -> tuple[bytes, bytes, XprFont]:
    encrypted = path.read_bytes()
    plain = outer_transform(encrypted, filename_seed(path.name))
    return encrypted, plain, XprFont(plain)


def extract_slot(font: XprFont, record_index: int) -> bytes:
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


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("v2_root", type=Path)
    args = parser.parse_args()
    root = args.v2_root.resolve()
    golden_path = root / "font" / "JPN_CN" / OUTPUT_NAME
    output_root = root / "font" / "font_poc_00c7_diagnostics_boundary"
    output_path = output_root / "TEST3B_NEW_ATLAS_WITH_COUNT" / OUTPUT_NAME

    golden_encrypted, golden_plain, golden = load(golden_path)
    fd = golden.font_data
    donor_index = fd.charmap[DONOR_CODEPOINT]
    donor = fd.glyphs[donor_index]
    if donor_index != 1751:
        raise RuntimeError(f"unexpected donor index for 昏: {donor_index}")
    if len(fd.glyphs) != TARGET_INDEX:
        raise RuntimeError("Golden does not have the expected 3209 records")
    if fd.charmap[TARGET_CODEPOINT] != 0:
        raise RuntimeError("Golden U+53A5 is unexpectedly mapped")
    old_count = bytes(fd.payload[COUNT_OFFSET : COUNT_OFFSET + 4])
    if old_count != b"\0\0\x0c\x89":
        raise RuntimeError(f"unexpected Golden count mirror: {old_count.hex()}")

    user = bytearray(fd.payload)
    struct.pack_into(">H", user, USER_MAP_OFFSET, TARGET_INDEX)
    user[COUNT_OFFSET : COUNT_OFFSET + 4] = struct.pack(">I", 3210)
    target_record = donor.with_uv(*TARGET_RECT)
    user.extend(target_record.packed)

    donor_bitmap = extract_slot(golden, donor_index)
    target_width = TARGET_RECT[2] - TARGET_RECT[0]
    target_height = TARGET_RECT[3] - TARGET_RECT[1]
    if len(donor_bitmap) != target_width * target_height:
        raise RuntimeError("donor and target bitmap dimensions differ")
    texture = bytearray(golden.texture.texels)
    destination_before = b"".join(
        texture[y * golden.texture.width + TARGET_RECT[0] : y * golden.texture.width + TARGET_RECT[2]]
        for y in range(TARGET_RECT[1], TARGET_RECT[3])
    )
    if any(destination_before):
        raise RuntimeError("target atlas slot is not blank")
    for row in range(target_height):
        destination = (TARGET_RECT[1] + row) * golden.texture.width + TARGET_RECT[0]
        source = row * target_width
        texture[destination : destination + target_width] = donor_bitmap[source : source + target_width]

    plain = golden.rebuild(
        {("USER", "FontData"): bytes(user)},
        texture_texels=bytes(texture),
    )
    encrypted = outer_transform(plain, filename_seed(output_path.name))
    output_path.parent.mkdir(parents=True, exist_ok=True)
    output_path.write_bytes(encrypted)

    readback_encrypted, readback_plain, result = load(output_path)
    result_fd = result.font_data
    errors: list[str] = []
    if readback_plain != plain:
        errors.append("filename-seeded encrypt/decrypt readback mismatch")
    if result_fd.charmap[TARGET_CODEPOINT] != TARGET_INDEX:
        errors.append("U+53A5 does not map to 3209")
    if len(result_fd.glyphs) != 3210:
        errors.append("record count is not 3210")
    if struct.unpack_from(">I", result.user.payload, COUNT_OFFSET)[0] != 3210:
        errors.append("count mirror is not 3210")
    if result.user.payload[COUNT_OFFSET : COUNT_OFFSET + 4] != b"\0\0\x0c\x8a":
        errors.append("count mirror raw bytes are not 00000C8A")
    if result_fd.glyphs[TARGET_INDEX] != target_record:
        errors.append("#3209 does not use donor metrics with target UV")
    if result_fd.glyphs[TARGET_INDEX].packed != donor.with_uv(*TARGET_RECT).packed:
        errors.append("#3209 raw record is not expected target record")
    if result_fd.glyphs[:TARGET_INDEX] != fd.glyphs:
        errors.append("old glyph records changed")

    old_map = fd.payload[0x16 : 0x16 + 2 * len(fd.charmap)]
    new_map = result.user.payload[0x16 : 0x16 + 2 * len(result_fd.charmap)]
    relative = 2 * TARGET_CODEPOINT
    old_maps_unchanged = old_map[:relative] == new_map[:relative] and old_map[relative + 2 :] == new_map[relative + 2 :]
    if not old_maps_unchanged:
        errors.append("old charmap entries changed outside U+53A5")

    old_texture = golden.texture.texels
    new_texture = result.texture.texels
    allowed_indices = {
        y * golden.texture.width + x
        for y in range(TARGET_RECT[1], TARGET_RECT[3])
        for x in range(TARGET_RECT[0], TARGET_RECT[2])
    }
    changed_indices = [i for i, (before, after) in enumerate(zip(old_texture, new_texture)) if before != after]
    outside = [i for i in changed_indices if i not in allowed_indices]
    result_slot = b"".join(
        new_texture[y * result.texture.width + TARGET_RECT[0] : y * result.texture.width + TARGET_RECT[2]]
        for y in range(TARGET_RECT[1], TARGET_RECT[3])
    )
    if result_slot != donor_bitmap:
        errors.append("destination slot is not pixel-identical to donor bitmap")
    if outside:
        errors.append(f"{len(outside)} atlas bytes changed outside target slot")
    if result.tx2d.payload != golden.tx2d.payload:
        errors.append("TX2D changed")
    if result.texture_data_offset != golden.texture_data_offset:
        errors.append("texture offset changed")
    if result.data_size != golden.data_size:
        errors.append("XPR data_size changed")
    parser_errors = validate_glyph_rectangles(result_fd, result.texture)
    errors.extend(parser_errors)

    manifest = {
        "status": "PASS" if not errors else "FAIL",
        "errors": errors,
        "golden": {
            "path": str(golden_path),
            "encrypted_sha256": sha256(golden_encrypted),
            "decrypted_sha256": sha256(golden_plain),
            "atlas_sha256": sha256(old_texture),
        },
        "output": {
            "path": str(output_path),
            "encrypted_sha256": sha256(readback_encrypted),
            "decrypted_sha256": sha256(readback_plain),
            "filename_seed": hx(filename_seed(output_path.name)),
            "glyph_count": len(result_fd.glyphs),
            "mapped_count": sum(index != 0 for index in result_fd.charmap),
            "user_size": result.user.size,
            "atlas_sha256": sha256(new_texture),
        },
        "donor": {
            "character": "昏",
            "codepoint": "U+660F",
            "glyph_index": donor_index,
            "record_raw_hex": donor.packed.hex(),
            "record": {
                "u0": donor.u0,
                "v0": donor.v0,
                "u1": donor.u1,
                "v1": donor.v1,
                "bearing_x": donor.bearing_x,
                "width": donor.width,
                "advance": donor.advance,
                "reserved": donor.reserved,
            },
            "rectangle": [donor.u0, donor.v0, donor.u1, donor.v1],
            "bitmap": slot_stats(donor_bitmap, target_width, target_height),
        },
        "target": {
            "character": "厥",
            "codepoint": "U+53A5",
            "glyph_index": TARGET_INDEX,
            "record_raw_hex": target_record.packed.hex(),
            "record": {
                "u0": target_record.u0,
                "v0": target_record.v0,
                "u1": target_record.u1,
                "v1": target_record.v1,
                "bearing_x": target_record.bearing_x,
                "width": target_record.width,
                "advance": target_record.advance,
                "reserved": target_record.reserved,
            },
            "rectangle": list(TARGET_RECT),
        },
        "count_mirror": {
            "file_offset": "0x1FF64",
            "before_hex": old_count.hex(),
            "after_hex": result.user.payload[COUNT_OFFSET : COUNT_OFFSET + 4].hex(),
            "before_be_u32": struct.unpack(">I", old_count)[0],
            "after_be_u32": struct.unpack_from(">I", result.user.payload, COUNT_OFFSET)[0],
        },
        "atlas": {
            "format": result.texture.data_format,
            "tiled": result.texture.tiled,
            "endian": result.texture.endian,
            "pitch": result.texture.pitch,
            "destination_rect": list(TARGET_RECT),
            "destination_before_sha256": sha256(destination_before),
            "donor_bitmap_sha256": sha256(donor_bitmap),
            "result_destination_sha256": sha256(result_slot),
            "changed_byte_count": len(changed_indices),
            "changed_outside_destination_count": len(outside),
        },
        "assertions": {
            "readback_roundtrip": readback_plain == plain,
            "old_records_unchanged": result_fd.glyphs[:TARGET_INDEX] == fd.glyphs,
            "old_mappings_unchanged_except_target": old_maps_unchanged,
            "target_mapping": result_fd.charmap[TARGET_CODEPOINT],
            "target_record_points_to_new_slot": (result_fd.glyphs[TARGET_INDEX].u0, result_fd.glyphs[TARGET_INDEX].v0, result_fd.glyphs[TARGET_INDEX].u1, result_fd.glyphs[TARGET_INDEX].v1) == TARGET_RECT,
            "target_record_metrics_equal_donor": result_fd.glyphs[TARGET_INDEX].packed[8:] == donor.packed[8:],
            "target_bitmap_pixel_identical_to_donor": result_slot == donor_bitmap,
            "atlas_changes_only_in_destination": not outside,
            "parser_errors": parser_errors,
        },
    }
    manifest_path = output_path.parent / "test3b_validation.json"
    manifest_path.write_text(json.dumps(manifest, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    report = [
        "# TEST-3B_NEW_ATLAS_WITH_COUNT",
        "",
        "基于已通过实机的 TEST-2B，仅新增变量：将 `昏 U+660F` 的原始 bitmap 逐行复制到新 atlas slot，并把 #3209 UV 改到该 slot。未生成厥、未修改其他 glyph、未 relocation texture。",
        "",
        "## 变更",
        "",
        f"- `U+53A5 → 3209`。",
        f"- count mirror file `0x1FF64`：`{old_count.hex()}` (`{struct.unpack('>I', old_count)[0]}`) → `00000C8A` (`3210`)。",
        f"- #3209 record：`{target_record.packed.hex()}`；metrics 沿用 donor `昏`，UV=`{TARGET_RECT}`。",
        f"- donor `昏` index=`{donor_index}`，record=`{donor.packed.hex()}`，rectangle=`{[donor.u0, donor.v0, donor.u1, donor.v1]}`。",
        f"- TX2D storage：format=`{result.texture.data_format}`，tiled=`{result.texture.tiled}`，endian=`{result.texture.endian}`，pitch=`{result.texture.pitch}`；复制方式为逐行按 pitch 写入。",
        "",
        "## 静态验证",
        "",
        f"- status：`{'PASS' if not errors else 'FAIL'}`；parser errors：`{parser_errors}`。",
        f"- glyph count=`{len(result_fd.glyphs)}`；USER size=`{hx(result.user.size)}`；atlas changed bytes=`{len(changed_indices)}`。",
        f"- old records unchanged：`{result_fd.glyphs[:TARGET_INDEX] == fd.glyphs}`。",
        f"- old mappings unchanged except U+53A5：`{old_maps_unchanged}`。",
        f"- #3209 points to new slot：`{(result_fd.glyphs[TARGET_INDEX].u0, result_fd.glyphs[TARGET_INDEX].v0, result_fd.glyphs[TARGET_INDEX].u1, result_fd.glyphs[TARGET_INDEX].v1) == TARGET_RECT}`。",
        f"- destination bitmap equals donor：`{result_slot == donor_bitmap}`。",
        f"- atlas changes outside `x=0..57,y=3333..3399`：`{len(outside)}`。",
        f"- encrypted SHA256：`{sha256(readback_encrypted)}`；decrypted SHA256：`{sha256(readback_plain)}`。",
        "",
        "## 实机预期",
        "",
        "唯一预期：`……而昏昏`。若 PASS，则 append-only 新 atlas slot 路线成立；下一轮才替换 slot bitmap 为真正的厥。",
        "",
        "## 手动步骤",
        "",
        "1. 恢复 Golden `00c7c9f9.xpr`。",
        "2. 安装 `TEST3B_NEW_ATLAS_WITH_COUNT/00c7c9f9.xpr`。",
        "3. 测试同一句文本，预期显示 `……而昏昏`。",
        "4. 记录 `PASS / FAIL / CRASH / VISUAL_CORRUPTION`。",
        "5. 测试结束后恢复 Golden。",
    ]
    (output_path.parent / "FONT_00C7_TEST3B_NEW_ATLAS_WITH_COUNT.md").write_text("\n".join(report) + "\n", encoding="utf-8")
    if errors:
        raise RuntimeError("TEST-3B static validation failed; see test3b_validation.json")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
