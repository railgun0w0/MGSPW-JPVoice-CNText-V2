#!/usr/bin/env python3
"""Replace only the TEST-3B target atlas slot with a real 厥 raster."""

from __future__ import annotations

import argparse
import hashlib
import json
import sys
from pathlib import Path

from PIL import Image, ImageDraw, ImageFont

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from core.pc_crypto import filename_seed, outer_transform
from core.xpr_font import XprFont, validate_glyph_rectangles


TARGET_CHAR = "厥"
TARGET_CODEPOINT = 0x53A5
TARGET_INDEX = 3209
TARGET_RECT = (0, 3333, 58, 3400)
DONOR_CODEPOINTS = {
    "厢": 0x53A2,
    "厌": 0x538C,
    "决": 0x51B3,
    "卷": 0x5377,
    "昏": 0x660F,
}
FONT_PATH = Path(r"C:\Windows\Fonts\Noto Sans SC Medium (TrueType).otf")
FONT_SIZE = 58
FONT_FACE_INDEX = 0
LAYOUT_ENGINE = 0  # Pillow/FreeType BASIC in the installed Pillow 9.x runtime.
ANCHOR = "ls"
INK_BOTTOM = 59


def sha256(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def hx(value: int) -> str:
    return f"0x{value:X}"


def load(path: Path) -> tuple[bytes, bytes, XprFont]:
    encrypted = path.read_bytes()
    plain = outer_transform(encrypted, filename_seed(path.name))
    return encrypted, plain, XprFont(plain)


def extract_record_bitmap(font: XprFont, index: int) -> bytes:
    record = font.font_data.glyphs[index]
    return b"".join(
        font.texture.texels[y * font.texture.width + record.u0 : y * font.texture.width + record.u1]
        for y in range(record.v0, record.v1)
    )


def bitmap_stats(data: bytes, width: int, height: int) -> dict[str, object]:
    points = [(i % width, i // width, value) for i, value in enumerate(data) if value]
    return {
        "width": width,
        "height": height,
        "nonzero_pixel_count": len(points),
        "ink_bbox_exclusive": (
            None
            if not points
            else [min(x for x, _, _ in points), min(y for _, y, _ in points), max(x for x, _, _ in points) + 1, max(y for _, y, _ in points) + 1]
        ),
        "sha256": sha256(data),
        "min_nonzero": min((value for _, _, value in points), default=0),
        "max_nonzero": max((value for _, _, value in points), default=0),
    }


def render_jue() -> tuple[bytes, dict[str, object]]:
    if not FONT_PATH.exists():
        raise RuntimeError(f"raster font not found: {FONT_PATH}")
    font = ImageFont.truetype(
        str(FONT_PATH), FONT_SIZE, index=FONT_FACE_INDEX, layout_engine=LAYOUT_ENGINE
    )
    font_bbox = tuple(int(value) for value in font.getbbox(TARGET_CHAR, anchor=ANCHOR))
    bbox_width = font_bbox[2] - font_bbox[0]
    draw_x = (TARGET_RECT[2] - TARGET_RECT[0] - bbox_width) // 2 - font_bbox[0]
    baseline_y = INK_BOTTOM - font_bbox[3]
    image = Image.new("L", (58, 67), 0)
    ImageDraw.Draw(image).text(
        (draw_x, baseline_y), TARGET_CHAR, font=font, fill=255, anchor=ANCHOR, stroke_width=0
    )
    bitmap = image.tobytes()
    bbox = image.getbbox()
    if bbox is None or bbox[0] < 0 or bbox[1] < 0 or bbox[2] > 58 or bbox[3] > 67:
        raise RuntimeError(f"generated 厥 leaves 58x67 cell: {bbox}")
    return bitmap, {
        "character": TARGET_CHAR,
        "codepoint": "U+53A5",
        "font_file": str(FONT_PATH),
        "font_family": "Noto Sans SC Medium",
        "font_face_index": FONT_FACE_INDEX,
        "rasterizer": "Pillow 9.0.1 FreeTypeFont/ImageDraw",
        "font_size_px": FONT_SIZE,
        "layout_engine": LAYOUT_ENGINE,
        "hinting_mode": "Pillow default FreeType load flags; hinting not explicitly disabled",
        "antialias_mode": "8-bit L-mode grayscale antialiasing",
        "grayscale_mapping": "direct 0..255; zero background, nonzero ink",
        "anchor": ANCHOR,
        "offset_x": draw_x,
        "baseline_y": baseline_y,
        "font_bbox_at_origin": list(font_bbox),
        "rendered_bbox_exclusive": list(bbox),
        "bitmap": bitmap_stats(bitmap, 58, 67),
    }


def write_preview(path: Path, bitmap: bytes, label: str, scale: int = 4) -> None:
    width, height = 58, 67
    canvas = Image.new("L", (width * scale, height * scale + 20), 0)
    crop = Image.frombytes("L", (width, height), bitmap)
    nearest = getattr(Image, "Resampling", Image).NEAREST
    canvas.paste(crop.resize((width * scale, height * scale), nearest), (0, 0))
    ImageDraw.Draw(canvas).text((2, height * scale + 2), label, fill=255)
    canvas.save(path)


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("v2_root", type=Path)
    args = parser.parse_args()
    root = args.v2_root.resolve()
    base_path = root / "font" / "font_poc_00c7_diagnostics_boundary" / "TEST3B_NEW_ATLAS_WITH_COUNT" / "00c7c9f9.xpr"
    output_root = root / "font" / "font_poc_00c7_diagnostics_boundary" / "TEST_REAL_GLYPH_JUE"
    output_path = output_root / "00c7c9f9.xpr"

    base_encrypted, base_plain, base = load(base_path)
    base_fd = base.font_data
    if base_fd.charmap[TARGET_CODEPOINT] != TARGET_INDEX:
        raise RuntimeError("TEST-3B does not map U+53A5 to 3209")
    if len(base_fd.glyphs) != 3210 or base.user.size != 0x2C778:
        raise RuntimeError("TEST-3B structure is not the expected 3210/0x2C778 state")
    if base_fd.glyphs[TARGET_INDEX].u0 != 0 or base_fd.glyphs[TARGET_INDEX].v0 != 3333:
        raise RuntimeError("TEST-3B target record is not at the planned slot")

    jue_bitmap, raster = render_jue()
    texture = bytearray(base.texture.texels)
    u0, v0, u1, v1 = TARGET_RECT
    old_target_bitmap = b"".join(
        texture[y * base.texture.width + u0 : y * base.texture.width + u1]
        for y in range(v0, v1)
    )
    for row in range(v1 - v0):
        offset = (v0 + row) * base.texture.width + u0
        texture[offset : offset + (u1 - u0)] = jue_bitmap[row * (u1 - u0) : (row + 1) * (u1 - u0)]

    plain = base.rebuild(
        {("USER", "FontData"): base.user.payload}, texture_texels=bytes(texture)
    )
    encrypted = outer_transform(plain, filename_seed(output_path.name))
    output_root.mkdir(parents=True, exist_ok=True)
    output_path.write_bytes(encrypted)

    readback_encrypted, readback_plain, result = load(output_path)
    result_fd = result.font_data
    errors: list[str] = []
    if readback_plain != plain:
        errors.append("filename-seeded encrypt/decrypt readback mismatch")
    if result.user.payload != base.user.payload:
        errors.append("USER payload changed outside the intended atlas-only operation")
    if result_fd.glyphs != base_fd.glyphs:
        errors.append("GlyphRecord table changed relative to TEST-3B")
    if result_fd.charmap != base_fd.charmap:
        errors.append("charmap changed relative to TEST-3B")
    if result.tx2d.payload != base.tx2d.payload:
        errors.append("TX2D descriptor/header changed relative to TEST-3B")
    if result.header_size != base.header_size or result.data_size != base.data_size or result.texture_data_offset != base.texture_data_offset:
        errors.append("XPR header/data/texture offset changed relative to TEST-3B")
    if result_fd.charmap[TARGET_CODEPOINT] != TARGET_INDEX:
        errors.append("U+53A5 is not mapped to 3209")
    if result_fd.glyphs[TARGET_INDEX].packed != base_fd.glyphs[TARGET_INDEX].packed:
        errors.append("#3209 record changed relative to TEST-3B")
    if result_fd.glyphs[TARGET_INDEX].packed != bytes.fromhex("00000d05003a0d480004003a003e0000"):
        errors.append("#3209 target record is not the expected UV/metrics record")
    if struct_unpack_u32(result.user.payload, 0x1FED4) != 3210:
        errors.append("count mirror changed or is not 3210")
    if result.user.size != base.user.size:
        errors.append("USER size changed relative to TEST-3B")

    base_texture = base.texture.texels
    result_texture = result.texture.texels
    allowed = {
        y * base.texture.width + x
        for y in range(v0, v1)
        for x in range(u0, u1)
    }
    changed = [i for i, (before, after) in enumerate(zip(base_texture, result_texture)) if before != after]
    outside = [i for i in changed if i not in allowed]
    result_target_bitmap = b"".join(
        result_texture[y * result.texture.width + u0 : y * result.texture.width + u1]
        for y in range(v0, v1)
    )
    if result_target_bitmap != jue_bitmap:
        errors.append("result target slot does not equal generated 厥 bitmap")
    if outside:
        errors.append(f"{len(outside)} atlas bytes changed outside target slot")
    parser_errors = validate_glyph_rectangles(result_fd, result.texture)
    errors.extend(parser_errors)

    reference_rows: list[dict[str, object]] = []
    for character, codepoint in DONOR_CODEPOINTS.items():
        index = base_fd.charmap[codepoint]
        record = base_fd.glyphs[index]
        bitmap = extract_record_bitmap(base, index)
        reference_rows.append(
            {
                "character": character,
                "codepoint": f"U+{codepoint:04X}",
                "glyph_index": index,
                "record_raw_hex": record.packed.hex(),
                "rectangle": [record.u0, record.v0, record.u1, record.v1],
                "metrics": {
                    "bearing_x": record.bearing_x,
                    "width": record.width,
                    "advance": record.advance,
                    "reserved": record.reserved,
                },
                "bitmap": bitmap_stats(bitmap, record.u1 - record.u0, record.v1 - record.v0),
            }
        )

    output_root.mkdir(parents=True, exist_ok=True)
    references_image = output_root / "existing_reference_glyphs.png"
    ref_scale = 4
    ref_canvas = Image.new("L", (58 * ref_scale * len(reference_rows), 67 * ref_scale + 20), 0)
    nearest = getattr(Image, "Resampling", Image).NEAREST
    draw = ImageDraw.Draw(ref_canvas)
    for column, row in enumerate(reference_rows):
        index = row["glyph_index"]
        record = base_fd.glyphs[index]
        bitmap = extract_record_bitmap(base, index)
        crop = Image.frombytes("L", (record.u1 - record.u0, record.v1 - record.v0), bitmap)
        x = column * 58 * ref_scale
        ref_canvas.paste(crop.resize((58 * ref_scale, 67 * ref_scale), nearest), (x, 0))
        draw.text((x + 2, 67 * ref_scale + 2), row["codepoint"], fill=255)
    ref_canvas.save(references_image)
    generated_image = output_root / "generated_jue_preview.png"
    write_preview(generated_image, jue_bitmap, "U+53A5", scale=4)

    manifest = {
        "status": "PASS" if not errors else "FAIL",
        "errors": errors,
        "base_test3b": {
            "path": str(base_path),
            "encrypted_sha256": sha256(base_encrypted),
            "decrypted_sha256": sha256(base_plain),
            "user_size": base.user.size,
            "glyph_count": len(base_fd.glyphs),
            "mapped_count": sum(index != 0 for index in base_fd.charmap),
        },
        "output": {
            "path": str(output_path),
            "encrypted_sha256": sha256(readback_encrypted),
            "decrypted_sha256": sha256(readback_plain),
            "filename_seed": hx(filename_seed(output_path.name)),
            "user_size": result.user.size,
            "glyph_count": len(result_fd.glyphs),
            "mapped_count": sum(index != 0 for index in result_fd.charmap),
        },
        "raster": raster,
        "references": reference_rows,
        "target": {
            "character": TARGET_CHAR,
            "codepoint": "U+53A5",
            "glyph_index": TARGET_INDEX,
            "rectangle": list(TARGET_RECT),
            "record_raw_hex": result_fd.glyphs[TARGET_INDEX].packed.hex(),
            "bitmap": bitmap_stats(result_target_bitmap, 58, 67),
            "old_test3b_slot_sha256": sha256(old_target_bitmap),
            "new_slot_sha256": sha256(result_target_bitmap),
        },
        "assertions": {
            "test3b_user_byte_identical": result.user.payload == base.user.payload,
            "test3b_glyph_records_byte_identical": result_fd.glyphs == base_fd.glyphs,
            "test3b_charmap_byte_identical": result_fd.charmap == base_fd.charmap,
            "test3b_xpr_descriptors_byte_identical": readback_plain[: base.texture_data_offset] == base_plain[: base.texture_data_offset],
            "target_mapping": result_fd.charmap[TARGET_CODEPOINT],
            "glyph_count": len(result_fd.glyphs),
            "target_record_unchanged_from_test3b": result_fd.glyphs[TARGET_INDEX].packed == base_fd.glyphs[TARGET_INDEX].packed,
            "target_slot_is_generated_jue": result_target_bitmap == jue_bitmap,
            "old_atlas_pixels_unchanged_outside_target": not outside,
            "atlas_changed_byte_count": len(changed),
            "atlas_changed_outside_count": len(outside),
            "parser_errors": parser_errors,
        },
        "preview_files": {
            "existing_reference_glyphs": str(references_image),
            "generated_jue_preview": str(generated_image),
        },
        "runtime_status": {
            "append_only_runtime_validated": "YES",
            "generated_glyph_runtime_validated": "PENDING_MANUAL_TEST",
        },
    }
    (output_root / "real_glyph_jue_manifest.json").write_text(
        json.dumps(manifest, ensure_ascii=False, indent=2) + "\n", encoding="utf-8"
    )
    report = [
        "# TEST_REAL_GLYPH_JUE",
        "",
        "本测试直接基于已实机通过的 TEST-3B，只替换新 atlas slot 内的 bitmap。所有 USER、GlyphRecord、charmap、XPR descriptor 和目标 UV/metrics 保持不变；没有生成其他 glyph、没有修改 translation、没有覆盖 Golden。",
        "",
        "## 文件",
        "",
        f"- 输入 TEST-3B：`{base_path}`",
        f"- 输出：`{output_path}`",
        f"- encrypted SHA256：`{sha256(readback_encrypted)}`",
        f"- decrypted SHA256：`{sha256(readback_plain)}`",
        "",
        "## 目标结构",
        "",
        "- `U+53A5 → glyph 3209`。",
        "- glyph count=`3210`；USER size=`0x2C778`。",
        "- #3209 record 保持 TEST-3B 完全不变：`00000d05003a0d480004003a003e0000`。",
        "- UV：`u0=0,v0=3333,u1=58,v1=3400`；bearing/width/advance 保持 TEST-3B。",
        "",
        "## Raster 参数",
        "",
        f"- font file：`{raster['font_file']}`",
        f"- family：`{raster['font_family']}`；face index：`{raster['font_face_index']}`",
        f"- rasterizer：`{raster['rasterizer']}`；font size：`{raster['font_size_px']} px`",
        f"- hinting：`{raster['hinting_mode']}`",
        f"- antialias：`{raster['antialias_mode']}`；grayscale：`{raster['grayscale_mapping']}`",
        f"- anchor=`{raster['anchor']}`；offset_x=`{raster['offset_x']}`；baseline_y=`{raster['baseline_y']}`",
        f"- font bbox=`{raster['font_bbox_at_origin']}`；rendered bbox=`{raster['rendered_bbox_exclusive']}`",
        f"- bitmap：`{json.dumps(raster['bitmap'], ensure_ascii=False)}`",
        "",
        "该参数不是把 TTF 默认输出直接塞入 atlas：baseline 以现有 67px CJK glyph 的底部 y=59 校准，水平位置按 font bbox 在 58px cell 内居中；实际 bbox 与参考字的 x/y 范围逐项对照如下。",
        "",
        "## 现有 glyph 对照",
        "",
        "| 字符 | codepoint | index | record raw | UV | ink bbox | nonzero pixels |",
        "|---|---|---:|---|---|---|---:|",
    ]
    for row in reference_rows:
        lines = row["bitmap"]
        report.append(
            f"| {row['character']} | {row['codepoint']} | {row['glyph_index']} | `{row['record_raw_hex']}` | `{row['rectangle']}` | `{lines['ink_bbox_exclusive']}` | {lines['nonzero_pixel_count']} |"
        )
    report.extend(
        [
            "",
            f"- 参考预览：`{references_image}`",
            f"- 厥预览：`{generated_image}`",
            "",
            "## 静态读回结果",
            "",
            f"- status：`{'PASS' if not errors else 'FAIL'}`；parser errors：`{parser_errors}`。",
            f"- TEST-3B USER byte-identical：`{result.user.payload == base.user.payload}`。",
            f"- TEST-3B GlyphRecords byte-identical：`{result_fd.glyphs == base_fd.glyphs}`。",
            f"- TEST-3B charmap byte-identical：`{result_fd.charmap == base_fd.charmap}`。",
            f"- TEST-3B XPR descriptor/header byte-identical：`{readback_plain[: base.texture_data_offset] == base_plain[: base.texture_data_offset]}`。",
            f"- `U+53A5 = {result_fd.charmap[TARGET_CODEPOINT]}`；glyph count=`{len(result_fd.glyphs)}`；USER size=`{hx(result.user.size)}`。",
            f"- #3209 record unchanged：`{result_fd.glyphs[TARGET_INDEX].packed == base_fd.glyphs[TARGET_INDEX].packed}`。",
            f"- new slot equals generated 厥：`{result_target_bitmap == jue_bitmap}`。",
            f"- atlas changed bytes：`{len(changed)}`；outside target slot：`{len(outside)}`。",
            "",
            "## 手动实机测试",
            "",
            "1. 恢复 Golden `00c7c9f9.xpr`。",
            "2. 安装 `TEST_REAL_GLYPH_JUE/00c7c9f9.xpr`。",
            "3. 进入同一句文本，唯一预期：`被击中的对手会承受不住而昏厥`。",
            "4. 记录 `PASS / FAIL / CRASH / VISUAL_CORRUPTION`。",
            "5. 测试结束后恢复 Golden。",
            "",
            "当前状态：`APPEND_ONLY_RUNTIME_VALIDATED = YES`；`GENERATED_GLYPH_RUNTIME_VALIDATED = PENDING_MANUAL_TEST`。只有本测试实机 PASS 后，才将后者改为 YES；本轮不批量生成其他字符。",
        ]
    )
    (output_root / "FONT_REAL_GLYPH_JUE.md").write_text("\n".join(report) + "\n", encoding="utf-8")
    if errors:
        raise RuntimeError("TEST_REAL_GLYPH_JUE static validation failed; see manifest")
    return 0


def struct_unpack_u32(data: bytes, offset: int) -> int:
    return int.from_bytes(data[offset : offset + 4], "big")


if __name__ == "__main__":
    raise SystemExit(main())
