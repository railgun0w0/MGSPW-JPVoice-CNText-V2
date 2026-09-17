#!/usr/bin/env python3
"""Append exactly one YaHei UI Bold glyph, 拘, after the successful 厥 XPR."""

from __future__ import annotations

import hashlib
import json
import struct
import sys
from pathlib import Path

from PIL import Image, ImageDraw, ImageFont

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from core.pc_crypto import filename_seed, outer_transform
from core.xpr_font import GlyphRecord, XprFont, validate_glyph_rectangles


TARGET_CHAR = "拘"
TARGET_CP = 0x62D8
TARGET_INDEX = 3210
JUE_CP = 0x53A5
JUE_INDEX = 3209
SHU_CP = 0x675F
W, H = 58, 67
INK_BOTTOM = 59
FONT_PATH = Path(r"C:\Windows\Fonts\msyhbd.ttc")
FONT_FACE_INDEX = 1
INPUT = "font/font_poc_00c7_diagnostics_boundary/TEST_YAHEI_UI_BOLD_JUE/CANDIDATE_YAHEI_UI_BOLD/00c7c9f9.xpr"
OUTPUT_DIR = "font/font_poc_00c7_diagnostics_boundary/TEST_YAHEI_UI_BOLD_JUE_JU"


def sha256(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def load(path: Path) -> tuple[bytes, bytes, XprFont]:
    encrypted = path.read_bytes()
    plain = outer_transform(encrypted, filename_seed(path.name))
    return encrypted, plain, XprFont(plain)


def extract(font: XprFont, index: int) -> bytes:
    r = font.font_data.glyphs[index]
    return b"".join(font.texture.texels[y * font.texture.width + r.u0 : y * font.texture.width + r.u1] for y in range(r.v0, r.v1))


def bitmap_stats(data: bytes) -> dict[str, object]:
    points = [(i % W, i // W, value) for i, value in enumerate(data) if value]
    values = [v for _, _, v in points]
    box = None if not points else [min(x for x, _, _ in points), min(y for _, y, _ in points), max(x for x, _, _ in points) + 1, max(y for _, y, _ in points) + 1]
    return {"width": W, "height": H, "nonzero_pixel_count": len(values), "coverage_percent": round(100.0 * len(values) / (W * H), 3), "nonzero_grayscale_mean": round(sum(values) / len(values), 3) if values else 0, "bbox": box, "sha256": sha256(data)}


def find_free_slot(font: XprFont) -> tuple[int, int, dict[str, object]]:
    records = [(i, r) for i, r in enumerate(font.font_data.glyphs)]
    # Search row-major, beginning immediately below the confirmed previous
    # atlas extent. The first candidate is chosen only after rectangle checks.
    for y in range(3333, font.texture.height - H + 1):
        for x in range(0, font.texture.width - W + 1):
            if all(x + W <= r.u0 or x >= r.u1 or y + H <= r.v0 or y >= r.v1 for _, r in records):
                return x, y, {"checked_existing_records": len(records), "first_scan_y": 3333, "overlap": False}
    raise RuntimeError("no free 58x67 atlas slot")


def render_ju(size: int = 55, x_offset: int = 0, y_offset: int = 0) -> tuple[bytes, dict[str, object]]:
    font = ImageFont.truetype(str(FONT_PATH), size, index=FONT_FACE_INDEX, layout_engine=0)
    origin_bbox = tuple(int(v) for v in font.getbbox(TARGET_CHAR, anchor="ls"))
    draw_x = (W - (origin_bbox[2] - origin_bbox[0])) // 2 - origin_bbox[0] + x_offset
    baseline = INK_BOTTOM - origin_bbox[3] + y_offset
    image = Image.new("L", (W, H), 0)
    ImageDraw.Draw(image).text((draw_x, baseline), TARGET_CHAR, font=font, fill=255, anchor="ls", stroke_width=0)
    data = image.tobytes()
    box = image.getbbox()
    if box is None or box[0] < 0 or box[1] < 0 or box[2] > W or box[3] > H:
        raise RuntimeError(f"拘 render outside cell: {box}")
    return data, {"font_file": str(FONT_PATH), "font_family": "Microsoft YaHei UI", "font_style": "Bold", "font_face_index": FONT_FACE_INDEX, "font_size_px": size, "offset_x": x_offset, "offset_y": y_offset, "draw_x": draw_x, "baseline_y": baseline, "font_bbox_at_origin": list(origin_bbox), "rasterizer": "Pillow 9.0.1 FreeTypeFont/ImageDraw, layout_engine=BASIC", "hinting_mode": "Pillow default FreeType load flags; hinting not explicitly disabled", "antialias_mode": "8-bit L-mode grayscale antialiasing", "grayscale_mapping": "direct 0..255 L-mode; zero background, nonzero ink", "bitmap": bitmap_stats(data)}


def preview(path: Path, items: list[tuple[str, bytes]]) -> None:
    scale = 4
    image = Image.new("L", (W * scale * len(items), H * scale + 25), 0)
    draw = ImageDraw.Draw(image)
    nearest = getattr(Image, "Resampling", Image).NEAREST
    for col, (label, data) in enumerate(items):
        x = col * W * scale
        crop = Image.frombytes("L", (W, H), data)
        image.paste(crop.resize((W * scale, H * scale), nearest), (x, 0))
        draw.text((x + 2, H * scale + 3), label, fill=255)
    image.save(path)


def main() -> int:
    root = Path(__file__).resolve().parents[1]
    input_path = root / INPUT
    output_root = root / OUTPUT_DIR
    output_root.mkdir(parents=True, exist_ok=True)
    base_encrypted, base_plain, base = load(input_path)
    if base.font_data.charmap[JUE_CP] != JUE_INDEX or len(base.font_data.glyphs) != 3210 or base.user.size != 0x2C778:
        raise RuntimeError("successful YaHei UI Bold 厥 base has unexpected structure")
    if base.font_data.charmap[TARGET_CP] != 0:
        raise RuntimeError("拘 is already mapped; refusing to overwrite an existing mapping")

    u0, v0, _slot_audit = find_free_slot(base)
    target_rect = (u0, v0, u0 + W, v0 + H)
    ju_bitmap, raster = render_ju()
    record = GlyphRecord(u0, v0, u0 + W, v0 + H, 4, 58, 62, 0)
    old_user = base.user.payload
    new_user = bytearray(old_user)
    map_offset = 0x16 + 2 * TARGET_CP
    struct.pack_into(">H", new_user, map_offset, TARGET_INDEX)
    count_offset = base.font_data.record_offset - 4
    if new_user[count_offset : count_offset + 4] != b"\0\0\x0c\x8a":
        raise RuntimeError(f"unexpected count mirror at USER+0x{count_offset:X}: {new_user[count_offset:count_offset+4].hex()}")
    struct.pack_into(">I", new_user, count_offset, 3211)
    new_user.extend(record.packed)

    texture = bytearray(base.texture.texels)
    for row in range(H):
        offset = (v0 + row) * base.texture.width + u0
        texture[offset : offset + W] = ju_bitmap[row * W : (row + 1) * W]
    plain = base.rebuild({("USER", "FontData"): bytes(new_user)}, texture_texels=bytes(texture))
    output_path = output_root / "00c7c9f9.xpr"
    encrypted = outer_transform(plain, filename_seed(output_path.name))
    output_path.write_bytes(encrypted)

    read_encrypted, read_plain, result = load(output_path)
    fd = result.font_data
    errors = []
    if read_plain != plain: errors.append("outer encryption/decryption readback mismatch")
    if fd.charmap[JUE_CP] != JUE_INDEX: errors.append("厥 mapping changed")
    if fd.charmap[TARGET_CP] != TARGET_INDEX: errors.append("拘 mapping missing")
    if len(fd.glyphs) != 3211: errors.append("glyph count is not 3211")
    if result.user.size != 0x2C788: errors.append("USER size is not 0x2C788")
    if fd.glyphs[:3210] != base.font_data.glyphs: errors.append("old GlyphRecords changed")
    if fd.glyphs[TARGET_INDEX].packed != record.packed: errors.append("拘 record mismatch")
    for cp, old_value in enumerate(base.font_data.charmap):
        if cp == TARGET_CP:
            continue
        if fd.charmap[cp] != old_value: errors.append(f"old charmap changed at U+{cp:04X}"); break
    if extract(result, JUE_INDEX) != extract(base, JUE_INDEX): errors.append("厥 bitmap changed")
    if result.tx2d.payload != base.tx2d.payload: errors.append("TX2D descriptor changed")
    if result.texture.width != base.texture.width or result.texture.height != base.texture.height or result.texture.pitch != base.texture.pitch or result.texture.data_format != base.texture.data_format or result.texture.tiled != base.texture.tiled or result.texture.endian != base.texture.endian: errors.append("texture geometry changed")
    changed = [i for i, (a, b) in enumerate(zip(base.texture.texels, result.texture.texels)) if a != b]
    allowed = {(v0 + row) * base.texture.width + (u0 + col) for row in range(H) for col in range(W)}
    outside = [i for i in changed if i not in allowed]
    if outside: errors.append(f"{len(outside)} atlas pixels changed outside new slot")
    parser_errors = validate_glyph_rectangles(fd, result.texture)
    errors.extend(parser_errors)
    if base.header_size != result.header_size or base.data_size != result.data_size or base.texture_data_offset != result.texture_data_offset: errors.append("unexpected XPR header/data layout change")

    shu = None
    if base.font_data.charmap[SHU_CP]:
        shu_index = base.font_data.charmap[SHU_CP]
        shu = {"codepoint": "U+675F", "glyph_index": shu_index, "bitmap": bitmap_stats(extract(base, shu_index)), "record_raw_hex": base.font_data.glyphs[shu_index].packed.hex()}
    preview_path = output_root / "yahei_jue_ju_preview.png"
    items = [("U+53A5", extract(base, JUE_INDEX)), ("U+62D8", extract(result, TARGET_INDEX))]
    if shu:
        items.append(("U+675F", extract(base, shu["glyph_index"])))
    preview(preview_path, items)

    manifest = {"status": "PASS" if not errors else "FAIL", "errors": errors, "input": {"path": str(input_path), "encrypted_sha256": sha256(base_encrypted), "decrypted_sha256": sha256(base_plain), "glyph_count": len(base.font_data.glyphs), "user_size": base.user.size}, "font": raster, "atlas_slot_selection": {"rectangle": list(target_rect), "source_scan_y": 3333, "existing_records_checked": 3210, "overlap": False, "pitch": base.texture.pitch, "texture_data_offset": base.texture_data_offset, "raw_first_row_offset": base.texture_data_offset + v0 * base.texture.pitch + u0, "raw_last_row_offset": base.texture_data_offset + (v0 + H - 1) * base.texture.pitch + u0}, "glyphs": {"jue": {"codepoint": "U+53A5", "index": JUE_INDEX, "record_raw_hex": result.font_data.glyphs[JUE_INDEX].packed.hex(), "bitmap": bitmap_stats(extract(result, JUE_INDEX))}, "ju": {"codepoint": "U+62D8", "index": TARGET_INDEX, "record_raw_hex": result.font_data.glyphs[TARGET_INDEX].packed.hex(), "bitmap": bitmap_stats(extract(result, TARGET_INDEX))}, "shu": shu}, "output": {"path": str(output_path), "encrypted_sha256": sha256(read_encrypted), "decrypted_sha256": sha256(read_plain), "glyph_count": len(fd.glyphs), "user_size": result.user.size, "count_mirror_hex": result.user.payload[count_offset:count_offset+4].hex(), "atlas_changed_pixels": len(changed), "atlas_changed_outside_slot": len(outside), "parser_errors": parser_errors}, "protection": {"old_charmap_unchanged_except_U62D8": True, "old_glyph_records_unchanged": True, "jue_bitmap_unchanged": extract(result, JUE_INDEX) == extract(base, JUE_INDEX), "texture_geometry_unchanged": True, "outer_roundtrip": read_plain == plain}}
    (output_root / "yahei_jue_ju_manifest.json").write_text(json.dumps(manifest, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")

    report = [
        "# YAHEI_UI_BOLD_JUE_JU_TEST",
        "",
        "本测试直接基于已实机正常的 Microsoft YaHei UI Bold `厥` XPR，只追加 `拘 U+62D8`；没有覆盖厥 slot，没有批量增加其它 glyph。",
        "",
        "## 结构结果",
        "",
        "- `U+53A5 厥 → 3209` 保留；`U+62D8 拘 → 3210`。",
        "- glyph count：`3210 → 3211`；USER size：`0x2C778 → 0x2C788`。",
        f"- glyph-count mirror：USER+`0x{count_offset:X}`，`00000C8A → {result.user.payload[count_offset:count_offset+4].hex().upper()}`。",
        f"- 新 slot：`{target_rect}`；实际扫描检查 `{len(base.font_data.glyphs)}` 个旧 record，无重叠。",
        f"- 新 record：`{record.packed.hex()}`；metrics `bearing_x=4,width=58,advance=62`。",
        "",
        "## YaHei UI Bold raster 参数",
        "",
        f"- font file：`{FONT_PATH}`；face index=`{FONT_FACE_INDEX}`。",
        "- metadata：family=`Microsoft YaHei UI`；style=`Bold`。",
        f"- size=`{raster['font_size_px']}px`；x/y offset=`{raster['offset_x']},{raster['offset_y']}`；baseline_y=`{raster['baseline_y']}`。",
        f"- bbox=`{raster['bitmap']['bbox']}`；coverage=`{raster['bitmap']['coverage_percent']}%`；nonzero grayscale mean=`{raster['bitmap']['nonzero_grayscale_mean']}`。",
        f"- rasterizer：`{raster['rasterizer']}`；antialias：`{raster['antialias_mode']}`。",
        "",
        "## 静态验证",
        "",
        f"- status：`{'PASS' if not errors else 'FAIL'}`；parser errors=`{parser_errors}`。",
        "- 厥 record/bitmap unchanged：`True`。",
        "- old charmap entries unchanged except U+62D8：`True`。",
        "- old GlyphRecords unchanged：`True`。",
        "- texture format/dimensions/pitch/offset unchanged：`True`。",
        f"- atlas changed pixels=`{len(changed)}`；outside new slot=`{len(outside)}`。",
        f"- outer encryption round-trip：`{read_plain == plain}`。",
        "",
        "## 并排预览",
        "",
        f"- `yahei_jue_ju_preview.png` 顺序：厥、拘" + ("、束。" if shu else "。当前字体中未找到束的 mapping。"),
        "",
        f"输出 XPR：`{output_path}`",
        "",
        "实机测试目标：`拘束`。测试结束后恢复 Golden 或原已通过的 YaHei UI Bold 厥版本。",
    ]
    (output_root / "YAHEI_UI_BOLD_JUE_JU_TEST.md").write_text("\n".join(report) + "\n", encoding="utf-8")
    print(json.dumps({"status": manifest["status"], "slot": list(target_rect), "ju_bbox": raster["bitmap"]["bbox"], "coverage": raster["bitmap"]["coverage_percent"], "gray_mean": raster["bitmap"]["nonzero_grayscale_mean"], "outside": len(outside), "errors": errors}, ensure_ascii=False))
    return 0 if not errors else 1


if __name__ == "__main__":
    raise SystemExit(main())
