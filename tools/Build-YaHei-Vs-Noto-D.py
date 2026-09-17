#!/usr/bin/env python3
"""Compare Microsoft YaHei Regular/Bold against the runtime-passed Noto D glyph."""

from __future__ import annotations

import hashlib
import json
import shutil
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
CELL_W, CELL_H = 58, 67
INK_BOTTOM = 59
MEDIAN_REFERENCE = {"x0": 2, "y0": 7, "x1": 55, "y1": 59, "coverage": 48.636, "mean": 181.555}
REGULAR_PATH = Path(r"C:\Windows\Fonts\msyh.ttc")
BOLD_PATH = Path(r"C:\Windows\Fonts\msyhbd.ttc")
REFERENCE_CODEPOINTS = {"昏": 0x660F, "眩": 0x7729, "晕": 0x6655, "棒": 0x68D2, "器": 0x5668, "厢": 0x53A2, "厌": 0x538C, "决": 0x51B3, "卷": 0x5377}


def sha256(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def load(path: Path) -> tuple[bytes, bytes, XprFont]:
    encrypted = path.read_bytes()
    plain = outer_transform(encrypted, filename_seed(path.name))
    return encrypted, plain, XprFont(plain)


def bitmap(font: XprFont, index: int) -> bytes:
    r = font.font_data.glyphs[index]
    return b"".join(font.texture.texels[y * font.texture.width + r.u0 : y * font.texture.width + r.u1] for y in range(r.v0, r.v1))


def stats(data: bytes) -> dict[str, object]:
    pts = [(i % CELL_W, i // CELL_W, value) for i, value in enumerate(data) if value]
    values = [v for _, _, v in pts]
    box = None if not pts else [min(x for x, _, _ in pts), min(y for _, y, _ in pts), max(x for x, _, _ in pts) + 1, max(y for _, y, _ in pts) + 1]
    return {
        "bbox": box,
        "coverage_percent": round(100.0 * len(values) / (CELL_W * CELL_H), 3),
        "nonzero_grayscale_mean": round(sum(values) / len(values), 3) if values else 0,
        "nonzero_pixel_count": len(values),
        "left_padding": box[0] if box else None,
        "right_padding": CELL_W - box[2] if box else None,
        "top_padding": box[1] if box else None,
        "bottom_padding": CELL_H - box[3] if box else None,
        "baseline_ink_bottom": box[3] if box else None,
        "sha256": sha256(data),
    }


def metadata(path: Path, face_index: int = 0) -> dict[str, object]:
    collection = TTCollection(str(path))
    font = collection.fonts[face_index]
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
        "family_name_id_1": sorted(values.get(1, set())),
        "subfamily_name_id_2": sorted(values.get(2, set())),
        "full_name_id_4": sorted(values.get(4, set())),
        "postscript_name_id_6": sorted(values.get(6, set())),
    }


def render(path: Path, size: int, x_offset: int, y_offset: int) -> tuple[bytes, dict[str, object]]:
    font = ImageFont.truetype(str(path), size, index=0, layout_engine=0)
    origin_bbox = tuple(int(v) for v in font.getbbox("厥", anchor="ls"))
    draw_x = (CELL_W - (origin_bbox[2] - origin_bbox[0])) // 2 - origin_bbox[0] + x_offset
    baseline = INK_BOTTOM - origin_bbox[3] + y_offset
    image = Image.new("L", (CELL_W, CELL_H), 0)
    ImageDraw.Draw(image).text((draw_x, baseline), "厥", font=font, fill=255, anchor="ls", stroke_width=0)
    data = image.tobytes()
    box = image.getbbox()
    if box is None or box[0] < 0 or box[1] < 0 or box[2] > CELL_W or box[3] > CELL_H:
        raise RuntimeError(f"render outside cell: {path} size={size} offsets={x_offset},{y_offset} box={box}")
    return data, {"font_size_px": size, "offset_x": x_offset, "offset_y": y_offset, "draw_x": draw_x, "baseline_y": baseline, "font_bbox_at_origin": list(origin_bbox), "bbox": list(box)}


def search_best(path: Path, style: str) -> tuple[bytes, dict[str, object]]:
    best = None
    for size in range(52, 61):
        for x_offset in range(-2, 3):
            for y_offset in range(-3, 4):
                data, params = render(path, size, x_offset, y_offset)
                s = stats(data)
                b = s["bbox"]
                if not b:
                    continue
                # Geometry is weighted above coverage/gray density. This is a
                # small search only; no non-uniform scaling or distortion.
                score = (
                    4.0 * (abs(b[0] - 2) + abs(b[1] - 7) + abs(b[2] - 56) + abs(b[3] - 59))
                    + 0.45 * abs(float(s["coverage_percent"]) - MEDIAN_REFERENCE["coverage"])
                    + 0.02 * abs(float(s["nonzero_grayscale_mean"]) - MEDIAN_REFERENCE["mean"])
                    + 0.8 * abs(((b[0] + b[2]) / 2.0) - 29.0)
                    + 6.0 * abs(b[3] - 59)
                )
                row = {"style": style, "font_file": str(path), "actual_metadata": metadata(path), **params, "rasterizer": "Pillow 9.0.1 FreeTypeFont/ImageDraw, layout_engine=BASIC", "hinting_mode": "Pillow default FreeType load flags; hinting not explicitly disabled", "antialias_mode": "8-bit L-mode grayscale antialiasing", "bitmap": s, "search_score": round(score, 4)}
                if best is None or score < best[0]:
                    best = (score, data, row)
    if best is None:
        raise RuntimeError(f"no render candidate for {style}")
    return best[1], best[2]


def make_preview(path: Path, items: list[tuple[str, bytes]]) -> None:
    scale = 4
    canvas = Image.new("L", (CELL_W * scale * len(items), CELL_H * scale + 25), 0)
    draw = ImageDraw.Draw(canvas)
    nearest = getattr(Image, "Resampling", Image).NEAREST
    for col, (label, data) in enumerate(items):
        x = col * CELL_W * scale
        crop = Image.frombytes("L", (CELL_W, CELL_H), data)
        canvas.paste(crop.resize((CELL_W * scale, CELL_H * scale), nearest), (x, 0))
        draw.text((x + 2, CELL_H * scale + 3), label, fill=255)
    canvas.save(path)


def main() -> int:
    root = Path(__file__).resolve().parents[1]
    control_path = root / "font" / "font_poc_00c7_diagnostics_boundary" / "TEST_REAL_GLYPH_JUE_STYLE_TUNING" / "CANDIDATE_D" / "00c7c9f9.xpr"
    out = root / "font" / "font_poc_00c7_diagnostics_boundary" / "TEST_YAHEI_VS_NOTO_D"
    out.mkdir(parents=True, exist_ok=True)
    _, control_plain, control = load(control_path)
    control_bitmap = bitmap(control, TARGET_INDEX)
    control_record = control.font_data.glyphs[TARGET_INDEX].packed
    if control.font_data.charmap[TARGET_CP] != TARGET_INDEX or len(control.font_data.glyphs) != 3210 or control.user.size != 0x2C778:
        raise RuntimeError("CONTROL_D has unexpected structure")

    refs = []
    reference_rows = []
    for char, cp in REFERENCE_CODEPOINTS.items():
        index = control.font_data.charmap[cp]
        data = bitmap(control, index)
        refs.append((f"U+{cp:04X}", data))
        reference_rows.append({"character": char, "codepoint": f"U+{cp:04X}", "glyph_index": index, "rectangle": [control.font_data.glyphs[index].u0, control.font_data.glyphs[index].v0, control.font_data.glyphs[index].u1, control.font_data.glyphs[index].v1], "bitmap": stats(data), "record_raw_hex": control.font_data.glyphs[index].packed.hex()})

    candidates = []
    for label, path, style in [("Y1", REGULAR_PATH, "Microsoft YaHei Regular"), ("Y2", BOLD_PATH, "Microsoft YaHei Bold")]:
        data, row = search_best(path, style)
        row["label"] = label
        candidates.append((label, data, row))

    source_texture = control.texture.texels
    u0, v0, u1, v1 = TARGET_RECT
    allowed = {y * control.texture.width + x for y in range(v0, v1) for x in range(u0, u1)}
    errors = []
    xpr_rows = []
    # D is copied, not regenerated. Y1/Y2 are re-encrypted using 00c7 filename seed.
    d_dir = out / "CONTROL_D"
    d_dir.mkdir(parents=True, exist_ok=True)
    d_path = d_dir / "00c7c9f9.xpr"
    shutil.copyfile(control_path, d_path)
    xpr_rows.append({"id": "D", "path": str(d_path), "encrypted_sha256": sha256(d_path.read_bytes()), "decrypted_sha256": sha256(control_plain), "static_validation": "PASS", "atlas_changed_outside_target": 0, "bitmap": stats(control_bitmap)})
    for label, data, row in candidates:
        candidate_dir = out / ("Y1_BEST_REGULAR" if label == "Y1" else "Y2_BEST_BOLD")
        candidate_dir.mkdir(parents=True, exist_ok=True)
        texture = bytearray(source_texture)
        for r in range(H := v1 - v0):
            offset = (v0 + r) * control.texture.width + u0
            texture[offset : offset + (u1 - u0)] = data[r * (u1 - u0) : (r + 1) * (u1 - u0)]
        plain = control.rebuild({("USER", "FontData"): control.user.payload}, texture_texels=bytes(texture))
        encrypted = outer_transform(plain, filename_seed("00c7c9f9.xpr"))
        path = candidate_dir / "00c7c9f9.xpr"
        path.write_bytes(encrypted)
        read_encrypted, read_plain, result = load(path)
        changed = [i for i, (a, b) in enumerate(zip(source_texture, result.texture.texels)) if a != b]
        outside = [i for i in changed if i not in allowed]
        local = []
        if result.user.payload != control.user.payload: local.append("USER changed")
        if result.font_data.glyphs != control.font_data.glyphs: local.append("GlyphRecords changed")
        if result.font_data.charmap != control.font_data.charmap: local.append("charmap changed")
        if result.tx2d.payload != control.tx2d.payload or read_plain[:control.texture_data_offset] != control_plain[:control.texture_data_offset]: local.append("descriptor/header changed")
        if result.font_data.glyphs[TARGET_INDEX].packed != control_record: local.append("target record changed")
        if result.font_data.charmap[TARGET_CP] != TARGET_INDEX: local.append("target mapping changed")
        if result.user.size != control.user.size or len(result.font_data.glyphs) != len(control.font_data.glyphs): local.append("structure changed")
        if bitmap(result, TARGET_INDEX) != data: local.append("target bitmap readback mismatch")
        if outside: local.append(f"{len(outside)} atlas bytes changed outside target")
        local.extend(validate_glyph_rectangles(result.font_data, result.texture))
        errors.extend([f"{label}: {e}" for e in local])
        row["xpr"] = {"path": str(path), "encrypted_sha256": sha256(read_encrypted), "decrypted_sha256": sha256(read_plain), "static_validation": "PASS" if not local else "FAIL", "atlas_changed_byte_count_vs_D": len(changed), "atlas_changed_outside_target_vs_D": len(outside)}
        xpr_rows.append({"id": label, **row["xpr"], "bitmap": row["bitmap"]})
        Image.frombytes("L", (CELL_W, CELL_H), data).resize((CELL_W * 4, CELL_H * 4), getattr(Image, "Resampling", Image).NEAREST).save(candidate_dir / "bitmap_preview.png")

    preview_path = out / "yahei_vs_noto_d.png"
    make_preview(preview_path, refs + [("D", control_bitmap)] + [(label, data) for label, data, _ in candidates])
    profile = {"status": "PASS" if not errors else "FAIL", "control_D": {"runtime_status": "PASS", "path": str(control_path), "encrypted_sha256": sha256(control_path.read_bytes()), "bitmap": stats(control_bitmap)}, "yahei_metadata": {"regular": metadata(REGULAR_PATH), "bold": metadata(BOLD_PATH)}, "candidates": [row for _, _, row in candidates], "xpr_variants": xpr_rows, "preview": str(preview_path), "errors": errors, "runtime_status": {"CONTROL_D": "PASS", "Y1": "PENDING_MANUAL_TEST", "Y2": "PENDING_MANUAL_TEST"}, "static_recommendation": "D", "final_runtime_winner": "PENDING"}
    (out / "yahei_vs_noto_d_manifest.json").write_text(json.dumps(profile, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")

    regular = next(row for row in candidates if row[0] == "Y1")[2]
    bold = next(row for row in candidates if row[0] == "Y2")[2]
    report = [
        "# FONT_YAHEI_VS_NOTO_D",
        "",
        "CONTROL_D = runtime PASS",
        "",
        "YAHEI_REGULAR_BEST =",
        f"font file: {regular['font_file']}",
        f"actual family/style: {regular['actual_metadata']['family_name_id_1']} / {regular['actual_metadata']['subfamily_name_id_2']}",
        f"px: {regular['font_size_px']}", f"offset: x={regular['offset_x']}, y={regular['offset_y']}", f"bbox: {regular['bitmap']['bbox']}", f"coverage: {regular['bitmap']['coverage_percent']}%", f"gray mean: {regular['bitmap']['nonzero_grayscale_mean']}",
        "",
        "YAHEI_BOLD_BEST =",
        f"font file: {bold['font_file']}",
        f"actual family/style: {bold['actual_metadata']['family_name_id_1']} / {bold['actual_metadata']['subfamily_name_id_2']}",
        f"px: {bold['font_size_px']}", f"offset: x={bold['offset_x']}, y={bold['offset_y']}", f"bbox: {bold['bitmap']['bbox']}", f"coverage: {bold['bitmap']['coverage_percent']}%", f"gray mean: {bold['bitmap']['nonzero_grayscale_mean']}",
        "",
        "STATIC_RECOMMENDATION = D",
        "FINAL_RUNTIME_WINNER = PENDING",
        "",
        "## 三者对比",
        "",
        "| 版本 | 来源 | size | offset | bbox | coverage | gray mean | runtime |",
        "|---|---|---:|---|---|---:|---:|---|",
        f"| D | Noto Sans SC Bold | 56 | control | `{stats(control_bitmap)['bbox']}` | {stats(control_bitmap)['coverage_percent']}% | {stats(control_bitmap)['nonzero_grayscale_mean']} | PASS |",
        f"| Y1 | Microsoft YaHei Regular | {regular['font_size_px']} | `{regular['offset_x']},{regular['offset_y']}` | `{regular['bitmap']['bbox']}` | {regular['bitmap']['coverage_percent']}% | {regular['bitmap']['nonzero_grayscale_mean']} | PENDING |",
        f"| Y2 | Microsoft YaHei Bold | {bold['font_size_px']} | `{bold['offset_x']},{bold['offset_y']}` | `{bold['bitmap']['bbox']}` | {bold['bitmap']['coverage_percent']}% | {bold['bitmap']['nonzero_grayscale_mean']} | PENDING |",
        "",
        "## 字体 metadata",
        "",
        f"- Regular 实际 metadata：`{json.dumps(metadata(REGULAR_PATH), ensure_ascii=False)}`",
        f"- Bold 实际 metadata：`{json.dumps(metadata(BOLD_PATH), ensure_ascii=False)}`",
        "- 两个候选都直接从已实机通过的 D 结构生成，仅改变 `厥` atlas slot；没有改变 glyph count、charmap、GlyphRecord、metrics、USER、UV 或 XPR descriptors。",
        "",
        "## 参考字与限制",
        "",
        "对照图包含当前 MLG 的 `昏、眩、晕、棒、器、厢、厌、决、卷`，以及 D/Y1/Y2。静态指标只用于筛选；D 已有实机优势，Y1/Y2 不能仅凭统计指标判定胜出。",
        "",
        f"- 对照图：`{preview_path}`",
        "- XPR：`CONTROL_D/00c7c9f9.xpr`、`Y1_BEST_REGULAR/00c7c9f9.xpr`、`Y2_BEST_BOLD/00c7c9f9.xpr`。",
        "- 详细参数、SHA256、保护检查和 metadata：`yahei_vs_noto_d_manifest.json`。",
        "",
        "当前结论：D 保持现有 fallback profile；Y1/Y2 等待用户实机比较。暂停批量生成和正式 FONT builder 修改。",
    ]
    (out / "FONT_YAHEI_VS_NOTO_D.md").write_text("\n".join(report) + "\n", encoding="utf-8")
    print(json.dumps({"status": profile["status"], "errors": errors, "regular": {"size": regular["font_size_px"], "offset": [regular["offset_x"], regular["offset_y"]], "bbox": regular["bitmap"]["bbox"]}, "bold": {"size": bold["font_size_px"], "offset": [bold["offset_x"], bold["offset_y"]], "bbox": bold["bitmap"]["bbox"]}}, ensure_ascii=False))
    return 0 if not errors else 1


if __name__ == "__main__":
    raise SystemExit(main())
