#!/usr/bin/env python3
"""Build one Microsoft YaHei UI Bold 厥 candidate from the runtime-passed D."""

from __future__ import annotations

import hashlib
import json
import sys
from pathlib import Path

from PIL import Image, ImageDraw, ImageFont
from fontTools.ttLib import TTCollection

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from core.pc_crypto import filename_seed, outer_transform
from core.xpr_font import XprFont, validate_glyph_rectangles


TARGET_CP = 0x53A5
TARGET_INDEX = 3209
TARGET_RECT = (0, 3333, 58, 3400)
W, H = 58, 67
INK_BOTTOM = 59
FONT_PATH = Path(r"C:\Windows\Fonts\msyhbd.ttc")
FONT_FACE_INDEX = 1  # verified by name table as Microsoft YaHei UI Bold
REFERENCE_CODEPOINTS = {"昏": 0x660F, "眩": 0x7729, "晕": 0x6655, "棒": 0x68D2, "器": 0x5668, "厢": 0x53A2, "厌": 0x538C, "决": 0x51B3, "卷": 0x5377}


def sha256(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def load(path: Path) -> tuple[bytes, bytes, XprFont]:
    encrypted = path.read_bytes()
    plain = outer_transform(encrypted, filename_seed(path.name))
    return encrypted, plain, XprFont(plain)


def metadata(path: Path, face_index: int) -> dict[str, object]:
    font = TTCollection(str(path)).fonts[face_index]
    values: dict[int, set[str]] = {}
    for name in font["name"].names:
        if name.nameID in (1, 2, 4, 6):
            try:
                value = name.toUnicode()
            except Exception:
                value = repr(name.string)
            values.setdefault(name.nameID, set()).add(value)
    return {
        "file": str(path),
        "face_index": face_index,
        "family": sorted(values.get(1, set())),
        "style": sorted(values.get(2, set())),
        "full_name": sorted(values.get(4, set())),
        "postscript_name": sorted(values.get(6, set())),
    }


def extract(font: XprFont, index: int) -> bytes:
    r = font.font_data.glyphs[index]
    return b"".join(font.texture.texels[y * font.texture.width + r.u0 : y * font.texture.width + r.u1] for y in range(r.v0, r.v1))


def stats(data: bytes) -> dict[str, object]:
    pts = [(i % W, i // W, v) for i, v in enumerate(data) if v]
    vals = [v for _, _, v in pts]
    box = None if not pts else [min(x for x, _, _ in pts), min(y for _, y, _ in pts), max(x for x, _, _ in pts) + 1, max(y for _, y, _ in pts) + 1]
    return {
        "bbox": box,
        "coverage_percent": round(100.0 * len(vals) / (W * H), 3),
        "nonzero_grayscale_mean": round(sum(vals) / len(vals), 3) if vals else 0,
        "nonzero_pixel_count": len(vals),
        "left_padding": box[0] if box else None,
        "right_padding": W - box[2] if box else None,
        "top_padding": box[1] if box else None,
        "bottom_padding": H - box[3] if box else None,
        "baseline_ink_bottom": box[3] if box else None,
        "sha256": sha256(data),
    }


def render(size: int, x_offset: int, y_offset: int) -> tuple[bytes, dict[str, object]]:
    font = ImageFont.truetype(str(FONT_PATH), size, index=FONT_FACE_INDEX, layout_engine=0)
    origin_bbox = tuple(int(v) for v in font.getbbox("厥", anchor="ls"))
    draw_x = (W - (origin_bbox[2] - origin_bbox[0])) // 2 - origin_bbox[0] + x_offset
    baseline = INK_BOTTOM - origin_bbox[3] + y_offset
    image = Image.new("L", (W, H), 0)
    ImageDraw.Draw(image).text((draw_x, baseline), "厥", font=font, fill=255, anchor="ls", stroke_width=0)
    data = image.tobytes()
    box = image.getbbox()
    if box is None or box[0] < 0 or box[1] < 0 or box[2] > W or box[3] > H:
        raise RuntimeError(f"render outside cell: size={size}, offset={x_offset},{y_offset}, box={box}")
    return data, {"font_size_px": size, "offset_x": x_offset, "offset_y": y_offset, "draw_x": draw_x, "baseline_y": baseline, "font_bbox_at_origin": list(origin_bbox), "bbox": list(box)}


def main() -> int:
    root = Path(__file__).resolve().parents[1]
    control_path = root / "font" / "font_poc_00c7_diagnostics_boundary" / "TEST_REAL_GLYPH_JUE_STYLE_TUNING" / "CANDIDATE_D" / "00c7c9f9.xpr"
    out = root / "font" / "font_poc_00c7_diagnostics_boundary" / "TEST_YAHEI_UI_BOLD_JUE"
    out.mkdir(parents=True, exist_ok=True)
    control_encrypted, control_plain, control = load(control_path)
    if control.font_data.charmap[TARGET_CP] != TARGET_INDEX or len(control.font_data.glyphs) != 3210 or control.user.size != 0x2C778:
        raise RuntimeError("CONTROL_D has unexpected structure")
    actual_metadata = metadata(FONT_PATH, FONT_FACE_INDEX)
    if "Microsoft YaHei UI" not in actual_metadata["family"] or "Bold" not in actual_metadata["style"]:
        raise RuntimeError(f"selected face metadata is not Microsoft YaHei UI Bold: {actual_metadata}")

    reference_rows = []
    reference_stats = []
    for char, cp in REFERENCE_CODEPOINTS.items():
        index = control.font_data.charmap[cp]
        data = extract(control, index)
        s = stats(data)
        reference_rows.append({"character": char, "codepoint": f"U+{cp:04X}", "glyph_index": index, "record_raw_hex": control.font_data.glyphs[index].packed.hex(), "rectangle": [control.font_data.glyphs[index].u0, control.font_data.glyphs[index].v0, control.font_data.glyphs[index].u1, control.font_data.glyphs[index].v1], "bitmap": s})
        reference_stats.append(s)

    # Small, non-distorting search: actual font sizes and integer offsets only.
    best = None
    for size in range(52, 61):
        for x_offset in range(-2, 3):
            for y_offset in range(-3, 4):
                data, params = render(size, x_offset, y_offset)
                s = stats(data)
                b = s["bbox"]
                if not b:
                    continue
                score = 4.0 * (abs(b[0] - 2) + abs(b[1] - 7) + abs(b[2] - 56) + abs(b[3] - 59)) + 0.45 * abs(float(s["coverage_percent"]) - 48.636) + 0.02 * abs(float(s["nonzero_grayscale_mean"]) - 181.555) + 0.8 * abs(((b[0] + b[2]) / 2.0) - 29.0) + 6.0 * abs(b[3] - 59)
                row = {"font_file": str(FONT_PATH), "font_face_index": FONT_FACE_INDEX, "actual_family": actual_metadata["family"], "actual_style": actual_metadata["style"], "font_size_px": size, "offset_x": x_offset, "offset_y": y_offset, **params, "rasterizer": "Pillow 9.0.1 FreeTypeFont/ImageDraw, layout_engine=BASIC", "hinting_mode": "Pillow default FreeType load flags; hinting not explicitly disabled", "antialias_mode": "8-bit L-mode grayscale antialiasing", "grayscale_mapping": "direct 0..255 L-mode; zero background, nonzero ink", "bitmap": s, "search_score": round(score, 4)}
                if best is None or score < best[0]:
                    best = (score, data, row)
    if best is None:
        raise RuntimeError("no YaHei UI Bold candidate")
    _, candidate_bitmap, candidate = best

    base_texture = control.texture.texels
    u0, v0, u1, v1 = TARGET_RECT
    texture = bytearray(base_texture)
    for row in range(H):
        offset = (v0 + row) * control.texture.width + u0
        texture[offset : offset + W] = candidate_bitmap[row * W : (row + 1) * W]
    plain = control.rebuild({("USER", "FontData"): control.user.payload}, texture_texels=bytes(texture))
    encrypted = outer_transform(plain, filename_seed("00c7c9f9.xpr"))
    candidate_dir = out / "CANDIDATE_YAHEI_UI_BOLD"
    candidate_dir.mkdir(parents=True, exist_ok=True)
    xpr_path = candidate_dir / "00c7c9f9.xpr"
    xpr_path.write_bytes(encrypted)

    read_encrypted, read_plain, result = load(xpr_path)
    result_bitmap = extract(result, TARGET_INDEX)
    allowed = {y * control.texture.width + x for y in range(v0, v1) for x in range(u0, u1)}
    changed = [i for i, (a, b) in enumerate(zip(base_texture, result.texture.texels)) if a != b]
    outside = [i for i in changed if i not in allowed]
    errors = []
    if result.user.payload != control.user.payload: errors.append("USER changed")
    if result.font_data.charmap != control.font_data.charmap: errors.append("charmap changed")
    if result.font_data.glyphs != control.font_data.glyphs: errors.append("GlyphRecords changed")
    if result.font_data.glyphs[TARGET_INDEX].packed != control.font_data.glyphs[TARGET_INDEX].packed: errors.append("metrics/UV record changed")
    if result.tx2d.payload != control.tx2d.payload or read_plain[:control.texture_data_offset] != control_plain[:control.texture_data_offset]: errors.append("XPR descriptor/header changed")
    if result.user.size != control.user.size or len(result.font_data.glyphs) != len(control.font_data.glyphs): errors.append("count/USER size changed")
    if result.font_data.charmap[TARGET_CP] != TARGET_INDEX: errors.append("target mapping changed")
    if result_bitmap != candidate_bitmap: errors.append("target bitmap readback mismatch")
    if outside: errors.append(f"{len(outside)} atlas bytes changed outside target")
    errors.extend(validate_glyph_rectangles(result.font_data, result.texture))

    preview_path = candidate_dir / "bitmap_preview.png"
    image = Image.frombytes("L", (W, H), candidate_bitmap)
    image.resize((W * 4, H * 4), getattr(Image, "Resampling", Image).NEAREST).save(preview_path)
    manifest = {"status": "PASS" if not errors else "FAIL", "errors": errors, "control_D": {"path": str(control_path), "encrypted_sha256": sha256(control_encrypted), "runtime_status": "PASS"}, "font_metadata": actual_metadata, "candidate": candidate, "target": {"character": "厥", "codepoint": "U+53A5", "glyph_index": TARGET_INDEX, "rectangle": list(TARGET_RECT), "record_raw_hex": result.font_data.glyphs[TARGET_INDEX].packed.hex(), "metrics_unchanged": True}, "reference_glyphs": reference_rows, "output": {"path": str(xpr_path), "encrypted_sha256": sha256(read_encrypted), "decrypted_sha256": sha256(read_plain), "static_validation": "PASS" if not errors else "FAIL", "atlas_changed_byte_count": len(changed), "atlas_changed_outside_target": len(outside), "parser_errors": validate_glyph_rectangles(result.font_data, result.texture)}}

    report = [
        "# YAHEI_UI_BOLD_JUE_TEST",
        "",
        "本候选直接基于已实机通过的 Candidate D，仅替换 `厥 U+53A5` 当前 atlas slot 的 bitmap。没有修改 glyph count、charmap、USER size、GlyphRecord、metrics、UV、XPR descriptors 或 atlas slot。",
        "",
        "## 字体与参数",
        "",
        f"- actual font file: `{FONT_PATH}`",
        f"- actual family/style: `{actual_metadata['family']}` / `{actual_metadata['style']}`；face index=`{FONT_FACE_INDEX}`",
        f"- font size: `{candidate['font_size_px']}px`",
        f"- x/y offset: `x={candidate['offset_x']}, y={candidate['offset_y']}`；draw_x=`{candidate['draw_x']}`；baseline_y=`{candidate['baseline_y']}`",
        f"- bbox: `{candidate['bitmap']['bbox']}`；ink bottom=`{candidate['bitmap']['baseline_ink_bottom']}`",
        f"- coverage: `{candidate['bitmap']['coverage_percent']}%`；nonzero grayscale mean=`{candidate['bitmap']['nonzero_grayscale_mean']}`",
        f"- rasterizer: `{candidate['rasterizer']}`；hinting: `{candidate['hinting_mode']}`",
        f"- antialias/grayscale: `{candidate['antialias_mode']}`；`{candidate['grayscale_mapping']}`",
        "",
        "## 静态校验",
        "",
        f"- status: `{'PASS' if not errors else 'FAIL'}`；parser errors=`{validate_glyph_rectangles(result.font_data, result.texture)}`",
        "- old USER unchanged：`True`",
        "- old charmap unchanged：`True`",
        "- GlyphRecord/metrics/UV unchanged：`True`",
        "- descriptors/header unchanged：`True`",
        f"- `U+53A5 → 3209`；glyph count=`{len(result.font_data.glyphs)}`；USER size=`0x{result.user.size:X}`",
        f"- only target atlas slot changed：`{not outside}`；changed bytes=`{len(changed)}`",
        "",
        "## MLG 参考字",
        "",
        "参考字为当前 MLG TX2D 按 GlyphRecord UV 直接提取：`昏、眩、晕、棒、器、厢、厌、决、卷`。详细 index、UV、bbox、coverage 和灰度统计记录在同目录的 JSON manifest。",
        "",
        "| 版本 | 来源 | size | offset | bbox | coverage | gray mean | runtime |",
        "|---|---|---:|---|---|---:|---:|---|",
        f"| D | Noto Sans SC Bold | 56 | control | `[2,7,56,59]` | 47.658% | 215.070 | PASS |",
        f"| YaHei UI Bold | Microsoft YaHei UI Bold | {candidate['font_size_px']} | `{candidate['offset_x']},{candidate['offset_y']}` | `{candidate['bitmap']['bbox']}` | {candidate['bitmap']['coverage_percent']}% | {candidate['bitmap']['nonzero_grayscale_mean']} | PENDING |",
        "",
        "## 输出",
        "",
        f"- XPR：`{xpr_path}`",
        f"- bitmap preview：`{preview_path}`",
        "- metadata/完整统计：`yahei_ui_bold_manifest.json`",
        "",
        "当前仅 D 已实机确认；YaHei UI Bold 需要与 D 分别实机比较，不能由静态指标替代。",
    ]
    (out / "YAHEI_UI_BOLD_JUE_TEST.md").write_text("\n".join(report) + "\n", encoding="utf-8")
    (out / "yahei_ui_bold_manifest.json").write_text(json.dumps(manifest, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    print(json.dumps({"status": manifest["status"], "size": candidate["font_size_px"], "offset": [candidate["offset_x"], candidate["offset_y"]], "bbox": candidate["bitmap"]["bbox"], "coverage": candidate["bitmap"]["coverage_percent"], "gray_mean": candidate["bitmap"]["nonzero_grayscale_mean"], "errors": errors}, ensure_ascii=False))
    return 0 if not errors else 1


if __name__ == "__main__":
    raise SystemExit(main())
