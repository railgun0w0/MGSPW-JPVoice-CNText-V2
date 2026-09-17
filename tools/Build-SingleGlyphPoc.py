#!/usr/bin/env python3
"""Build and validate isolated append-only FONT runtime PoCs.

This script never writes a canonical FONT.  It decrypts the canonical
MLG_CN/0007ccd8.xpr in memory, appends only U+53A5, and emits two encrypted
copies under font/font_poc/ using the requested filename-derived seeds.
"""

from __future__ import annotations

import argparse
import hashlib
import json
import struct
import sys
from pathlib import Path

from PIL import Image, ImageDraw, ImageFont

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from core.pc_crypto import filename_seed, outer_transform
from core.xpr_font import GlyphRecord, XprFont, validate_glyph_rectangles


TARGET_CHAR = "厥"
TARGET_CODEPOINT = 0x53A5
TARGET_INDEX = 3209
CELL_W = 58
CELL_H = 67
U0, V0, U1, V1 = 0, 3333, 58, 3400
BEARING_X = 4
GLYPH_WIDTH = 58
ADVANCE = 62
RECORD_SIZE = 16


def sha256(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def hex32(value: int) -> str:
    return f"0x{value:X}"


def render_glyph(font_path: Path) -> tuple[bytes, dict[str, object]]:
    """Render one deterministic 58x67 grayscale bitmap.

    Noto Sans SC regular is used at 58 px.  The baseline is selected from the
    font's actual bbox so the visible bottom is y=59, matching the measured
    clean CJK glyph rows in MLG-0007.  Horizontal placement is centered from
    the font bbox, without stroke expansion or hinting overrides.
    """

    font_size = 58
    face_index = 0
    anchor = "ls"
    font = ImageFont.truetype(str(font_path), font_size, index=face_index)
    bbox_at_origin = tuple(int(v) for v in font.getbbox(TARGET_CHAR, anchor=anchor))
    bbox_width = bbox_at_origin[2] - bbox_at_origin[0]
    x = (CELL_W - bbox_width) // 2 - bbox_at_origin[0]
    baseline_y = 59 - bbox_at_origin[3]

    image = Image.new("L", (CELL_W, CELL_H), 0)
    draw = ImageDraw.Draw(image)
    draw.text((x, baseline_y), TARGET_CHAR, font=font, fill=255, anchor=anchor)
    pixels = image.tobytes()
    bbox = image.getbbox()
    if bbox is None:
        raise RuntimeError("rasterized 厥 has no nonzero pixels")
    if bbox[0] < 0 or bbox[1] < 0 or bbox[2] > CELL_W or bbox[3] > CELL_H:
        raise RuntimeError(f"rasterized 厥 leaves cell: bbox={bbox}")

    nonzero = sum(value != 0 for value in pixels)
    return pixels, {
        "character": TARGET_CHAR,
        "codepoint": f"U+{TARGET_CODEPOINT:04X}",
        "font_path": str(font_path),
        "font_face_index": face_index,
        "font_size_px": font_size,
        "anchor": anchor,
        "draw_x": x,
        "baseline_y": baseline_y,
        "font_bbox_at_origin": list(bbox_at_origin),
        "rendered_bbox_exclusive_in_cell": list(bbox),
        "nonzero_pixel_count": nonzero,
        "bitmap_sha256": sha256(pixels),
        "fill": 255,
        "stroke_width": 0,
        "antialias": "Pillow ImageDraw L-mode grayscale via FreeType",
    }


def write_atlas_slot(texels: bytes, width: int, bitmap: bytes) -> bytes:
    output = bytearray(texels)
    for row in range(CELL_H):
        start = (V0 + row) * width + U0
        end = start + CELL_W
        if any(output[start:end]):
            raise RuntimeError("requested atlas slot is not blank")
        output[start:end] = bitmap[row * CELL_W : (row + 1) * CELL_W]
    return bytes(output)


def append_user(font: XprFont, glyph: GlyphRecord) -> tuple[bytes, bytes]:
    fd = font.font_data
    if len(fd.glyphs) != TARGET_INDEX:
        raise RuntimeError(f"expected new glyph index {TARGET_INDEX}, got {len(fd.glyphs)}")
    if fd.charmap[TARGET_CODEPOINT] != 0:
        raise RuntimeError("U+53A5 is already mapped in the Golden source")
    map_offset = 0x16 + 2 * TARGET_CODEPOINT
    user = bytearray(fd.payload)
    original_entry = bytes(user[map_offset : map_offset + 2])
    if original_entry != b"\0\0":
        raise RuntimeError("U+53A5 map entry is not zero in the Golden source")
    struct.pack_into(">H", user, map_offset, TARGET_INDEX)
    user.extend(glyph.packed)
    if len(user) != font.user.size + RECORD_SIZE:
        raise RuntimeError("unexpected FontData size after one-record append")
    return bytes(user), original_entry


def compare_unchanged(original: XprFont, result: XprFont, target_bitmap: bytes) -> dict[str, object]:
    errors: list[str] = []
    original_fd = original.font_data
    result_fd = result.font_data
    if result_fd.charmap[TARGET_CODEPOINT] != TARGET_INDEX:
        errors.append("U+53A5 does not map to glyph 3209")
    if len(result_fd.glyphs) != TARGET_INDEX + 1:
        errors.append("result glyph count is not 3210")
    expected = GlyphRecord(U0, V0, U1, V1, BEARING_X, GLYPH_WIDTH, ADVANCE, 0)
    if result_fd.glyphs[TARGET_INDEX] != expected:
        errors.append("glyph #3209 record differs from requested record")
    if result_fd.glyphs[:TARGET_INDEX] != original_fd.glyphs:
        errors.append("old glyph records are not byte-identical")

    old_map_bytes = original.user.payload[0x16 : 0x16 + 2 * len(original_fd.charmap)]
    new_map_bytes = result.user.payload[0x16 : 0x16 + 2 * len(original_fd.charmap)]
    target_relative = 2 * TARGET_CODEPOINT
    if old_map_bytes[:target_relative] != new_map_bytes[:target_relative]:
        errors.append("charmap bytes before U+53A5 changed")
    if old_map_bytes[target_relative + 2 :] != new_map_bytes[target_relative + 2 :]:
        errors.append("charmap bytes after U+53A5 changed")

    old_tex = original.texture.texels
    new_tex = result.texture.texels
    slot_start = V0 * original.texture.width + U0
    slot_indices = {
        (V0 + row) * original.texture.width + U0 + col
        for row in range(CELL_H)
        for col in range(CELL_W)
    }
    for index, (old, new) in enumerate(zip(old_tex, new_tex)):
        if index not in slot_indices and old != new:
            errors.append(f"old atlas pixel changed at flat offset 0x{index:X}")
            break
    slot = b"".join(
        new_tex[(V0 + row) * result.texture.width + U0 : (V0 + row) * result.texture.width + U1]
        for row in range(CELL_H)
    )
    if slot != target_bitmap:
        errors.append("atlas slot pixels differ from the generated bitmap")
    if not any(slot):
        errors.append("atlas slot has no nonzero pixels")

    if original.texture.width != result.texture.width or original.texture.height != result.texture.height:
        errors.append("atlas dimensions changed")
    if original.tx2d.payload != result.tx2d.payload:
        errors.append("TX2D descriptor/header changed")
    if original.texture_data_offset != result.texture_data_offset:
        errors.append("texture data offset changed")
    if original.data_size != result.data_size:
        errors.append("XPR data_size changed")
    if result.user.offset != original.user.offset:
        errors.append("USER offset changed")
    if result.user.size != original.user.size + RECORD_SIZE:
        errors.append("USER size did not grow by 0x10")

    parser_errors = validate_glyph_rectangles(result_fd, result.texture)
    errors.extend(parser_errors)
    return {
        "errors": errors,
        "passed": not errors,
        "old_glyph_records_byte_identical": result_fd.glyphs[:TARGET_INDEX] == original_fd.glyphs,
        "old_charmap_entries_byte_identical_except_target": (
            old_map_bytes[:target_relative] == new_map_bytes[:target_relative]
            and old_map_bytes[target_relative + 2 :] == new_map_bytes[target_relative + 2 :]
        ),
        "old_atlas_pixels_byte_identical_outside_target_slot": not any(
            old != new
            for index, (old, new) in enumerate(zip(old_tex, new_tex))
            if index not in slot_indices
        ),
        "target_slot_nonzero": any(slot),
        "target_slot_sha256": sha256(slot),
        "target_record": list(result_fd.glyphs[TARGET_INDEX].__dict__.values()),
        "target_mapping": result_fd.charmap[TARGET_CODEPOINT],
        "glyph_count": len(result_fd.glyphs),
        "mapped_codepoint_count": sum(index != 0 for index in result_fd.charmap),
        "parser_errors": parser_errors,
        "slot_flat_start": slot_start,
    }


def build_variant(
    original_plain: bytes,
    original: XprFont,
    root: Path,
    output_dir: Path,
    output_filename: str,
    raster_font: Path,
) -> dict[str, object]:
    bitmap, raster = render_glyph(raster_font)
    glyph = GlyphRecord(U0, V0, U1, V1, BEARING_X, GLYPH_WIDTH, ADVANCE, 0)
    user_payload, original_target_entry = append_user(original, glyph)
    new_texels = write_atlas_slot(original.texture.texels, original.texture.width, bitmap)
    rebuilt_plain = original.rebuild(
        {("USER", "FontData"): user_payload},
        texture_texels=new_texels,
    )
    output_path = output_dir / output_filename
    output_path.parent.mkdir(parents=True, exist_ok=True)
    seed = filename_seed(output_filename)
    encrypted = outer_transform(rebuilt_plain, seed)
    output_path.write_bytes(encrypted)

    # Re-open the emitted bytes using only the destination filename seed.
    readback_encrypted = output_path.read_bytes()
    readback_plain = outer_transform(readback_encrypted, filename_seed(output_path.name))
    readback = XprFont(readback_plain)
    validation = compare_unchanged(original, readback, bitmap)
    validation.update(
        {
            "output": str(output_path),
            "output_filename": output_filename,
            "filename_seed": hex32(seed),
            "source_plain_sha256": sha256(original_plain),
            "output_encrypted_sha256": sha256(readback_encrypted),
            "output_plain_sha256": sha256(readback_plain),
            "output_encrypted_size": len(readback_encrypted),
            "output_plain_size": len(readback_plain),
            "source_user_size": original.user.size,
            "result_user_size": readback.user.size,
            "source_texture_offset": original.texture_data_offset,
            "result_texture_offset": readback.texture_data_offset,
            "original_target_map_entry_hex": original_target_entry.hex(),
            "raster": raster,
            "requested_record": list(glyph.__dict__.values()),
            "requested_atlas_slot": [U0, V0, U1, V1],
        }
    )
    (output_dir / "poc_validation.json").write_text(
        json.dumps(validation, ensure_ascii=False, indent=2) + "\n",
        encoding="utf-8",
    )
    return validation


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("v2_root", type=Path)
    parser.add_argument("--raster-font", type=Path, required=True)
    args = parser.parse_args()
    root = args.v2_root.resolve()
    raster_font = args.raster_font.resolve()
    source_path = root / "font" / "MLG_CN" / "0007ccd8.xpr"
    output_root = root / "font" / "font_poc"
    encrypted = source_path.read_bytes()
    source_seed = filename_seed(source_path.name)
    original_plain = outer_transform(encrypted, source_seed)
    original = XprFont(original_plain)
    if len(original.font_data.glyphs) != TARGET_INDEX:
        raise RuntimeError("Golden source does not have the expected 3209 records")

    variants = [
        ("POC_A_00C7", "00c7c9f9.xpr"),
        ("POC_B_0007", "0007ccd8.xpr"),
    ]
    results: dict[str, object] = {}
    for directory, filename in variants:
        results[directory] = build_variant(
            original_plain,
            original,
            root,
            output_root / directory,
            filename,
            raster_font,
        )

    report = {
        "source": str(source_path),
        "source_encrypted_sha256": sha256(encrypted),
        "source_plain_sha256": sha256(original_plain),
        "source_filename_seed": hex32(source_seed),
        "raster_font": str(raster_font),
        "target": {
            "character": TARGET_CHAR,
            "codepoint": f"U+{TARGET_CODEPOINT:04X}",
            "new_glyph_index": TARGET_INDEX,
            "atlas_slot": [U0, V0, U1, V1],
            "record": [U0, V0, U1, V1, BEARING_X, GLYPH_WIDTH, ADVANCE, 0],
        },
        "variants": results,
    }
    output_root.mkdir(parents=True, exist_ok=True)
    (output_root / "poc_results.json").write_text(
        json.dumps(report, ensure_ascii=False, indent=2) + "\n",
        encoding="utf-8",
    )
    if not all(result["passed"] for result in results.values()):
        raise RuntimeError("one or more PoC static validations failed; see poc_validation.json")
    print(json.dumps(report, ensure_ascii=False, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
