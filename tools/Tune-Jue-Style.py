#!/usr/bin/env python3
"""Generate visual/style candidates for the already runtime-validated 厥 glyph.

Every candidate is based on TEST_REAL_GLYPH_JUE and changes only the 58x67
target atlas slot. No FONT structure, glyph record, charmap, or metrics are
changed.
"""

from __future__ import annotations

import argparse
import gc
import hashlib
import json
import math
import sys
from pathlib import Path

from PIL import Image, ImageDraw, ImageFilter, ImageFont

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from core.pc_crypto import filename_seed, outer_transform
from core.xpr_font import XprFont, validate_glyph_rectangles


TARGET_CHAR = "厥"
TARGET_CODEPOINT = 0x53A5
TARGET_INDEX = 3209
TARGET_RECT = (0, 3333, 58, 3400)
REFERENCE_CODEPOINTS = {
    "昏": 0x660F,
    "眩": 0x7729,
    "晕": 0x6655,
    "棒": 0x68D2,
    "器": 0x5668,
    "厢": 0x53A2,
    "厌": 0x538C,
    "决": 0x51B3,
    "卷": 0x5377,
}
FONT_MEDIUM = Path(r"C:\Windows\Fonts\Noto Sans SC Medium (TrueType).otf")
FONT_REGULAR = Path(r"C:\Windows\Fonts\Noto Sans SC (TrueType).otf")
FONT_BOLD = Path(r"C:\Windows\Fonts\Noto Sans SC Bold (TrueType).otf")
INK_BOTTOM = 59
CELL_W, CELL_H = 58, 67
SCALE = 4


def sha256(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


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


def points(bitmap: bytes) -> list[tuple[int, int, int]]:
    return [(i % CELL_W, i // CELL_W, value) for i, value in enumerate(bitmap) if value]


def bitmap_stats(bitmap: bytes) -> dict[str, object]:
    ps = points(bitmap)
    values = [value for _, _, value in ps]
    if not ps:
        bbox = None
    else:
        bbox = [min(x for x, _, _ in ps), min(y for _, y, _ in ps), max(x for x, _, _ in ps) + 1, max(y for _, y, _ in ps) + 1]
    sorted_values = sorted(values)

    def percentile(p: float) -> int:
        if not sorted_values:
            return 0
        return sorted_values[min(len(sorted_values) - 1, int(round((len(sorted_values) - 1) * p)))]

    partial = sum(0 < value < 255 for value in values)
    return {
        "width": CELL_W,
        "height": CELL_H,
        "nonzero_pixel_count": len(ps),
        "coverage_percent": round(len(ps) * 100.0 / (CELL_W * CELL_H), 3),
        "ink_bbox_exclusive": bbox,
        "left_padding": None if bbox is None else bbox[0],
        "right_padding": None if bbox is None else CELL_W - bbox[2],
        "top_padding": None if bbox is None else bbox[1],
        "bottom_padding": None if bbox is None else CELL_H - bbox[3],
        "baseline_ink_bottom": None if bbox is None else bbox[3],
        "mean_nonzero": round(sum(values) / len(values), 3) if values else 0,
        "p10_nonzero": percentile(0.10),
        "p50_nonzero": percentile(0.50),
        "p90_nonzero": percentile(0.90),
        "partial_pixel_percent": round(partial * 100.0 / len(values), 3) if values else 0,
        "sha256": sha256(bitmap),
    }


def apply_gamma(bitmap: bytes, gamma: float) -> bytes:
    if abs(gamma - 1.0) < 1e-9:
        return bitmap
    table = bytes(max(0, min(255, int(round(255.0 * ((value / 255.0) ** gamma))))) for value in range(256))
    return bytes(table[value] for value in bitmap)


def render_candidate(profile: dict[str, object]) -> tuple[bytes, dict[str, object]]:
    font_path = Path(str(profile["font_file"]))
    size = int(profile["font_size_px"])
    embolden = int(profile.get("embolden_px", 0))
    gamma = float(profile.get("gamma", 1.0))
    if not font_path.exists():
        raise RuntimeError(f"font not found: {font_path}")

    font = ImageFont.truetype(str(font_path), size, index=0, layout_engine=0)
    bbox0 = tuple(int(value) for value in font.getbbox(TARGET_CHAR, anchor="ls"))
    bbox_width = bbox0[2] - bbox0[0]
    draw_x = (CELL_W - bbox_width) // 2 - bbox0[0]
    baseline = INK_BOTTOM - bbox0[3]
    image = Image.new("L", (CELL_W, CELL_H), 0)
    ImageDraw.Draw(image).text((draw_x, baseline), TARGET_CHAR, font=font, fill=255, anchor="ls", stroke_width=0)
    if embolden:
        image = image.filter(ImageFilter.MaxFilter(2 * embolden + 1))
        box = image.getbbox()
        if box:
            shift_x = (CELL_W - (box[2] - box[0])) // 2 - box[0]
            shift_y = INK_BOTTOM - box[3]
            shifted = Image.new("L", (CELL_W, CELL_H), 0)
            shifted.paste(image, (shift_x, shift_y))
            image = shifted
    bitmap = apply_gamma(image.tobytes(), gamma)
    image = Image.frombytes("L", (CELL_W, CELL_H), bitmap)
    box = image.getbbox()
    if box is None or box[0] < 0 or box[1] < 0 or box[2] > CELL_W or box[3] > CELL_H:
        raise RuntimeError(f"candidate leaves cell: {box}")
    measured = dict(profile)
    measured.update({
        "font_bbox_at_origin": list(bbox0),
        "offset_x": draw_x,
        "baseline_y": baseline,
        "rendered_bbox_exclusive": list(box),
        "rasterizer": "Pillow 9.0.1 FreeTypeFont/ImageDraw, layout_engine=BASIC",
        "hinting_mode": "Pillow default FreeType load flags; hinting not explicitly disabled",
        "antialias_mode": "8-bit L-mode grayscale antialiasing",
        "grayscale_mapping": f"direct 0..255 then gamma={gamma:g}; zero background, nonzero ink",
        "bitmap": bitmap_stats(bitmap),
    })
    return bitmap, measured


def make_preview(path: Path, refs: dict[str, bytes], candidates: dict[str, bytes]) -> None:
    labels = list(refs) + list(candidates)
    canvas = Image.new("L", (CELL_W * SCALE * len(labels), CELL_H * SCALE + 28), 0)
    draw = ImageDraw.Draw(canvas)
    nearest = getattr(Image, "Resampling", Image).NEAREST
    for col, label in enumerate(labels):
        bitmap = refs[label] if label in refs else candidates[label]
        crop = Image.frombytes("L", (CELL_W, CELL_H), bitmap)
        x = col * CELL_W * SCALE
        canvas.paste(crop.resize((CELL_W * SCALE, CELL_H * SCALE), nearest), (x, 0))
        # Pillow's default bitmap font is Latin-1 only; use codepoints for
        # Chinese reference labels so preview generation stays deterministic.
        display_label = label if label.isascii() else f"U+{ord(label):04X}"
        draw.text((x + 2, CELL_H * SCALE + 3), display_label, fill=255)
    canvas.save(path)


def similarity_score(stats: dict[str, object], reference_stats: list[dict[str, object]]) -> float:
    # A conservative style proxy: bbox/padding and coverage are compared to
    # the observed reference distribution; baseline is required to be y=59.
    def med(key: str) -> float:
        values = sorted(float(item[key]) for item in reference_stats if item[key] is not None)
        return values[len(values) // 2]

    bbox = stats["ink_bbox_exclusive"]
    if not bbox:
        return 1e9
    ref_bbox = [med("bbox_x0"), med("bbox_y0"), med("bbox_x1"), med("bbox_y1")]
    coverage_ref = med("coverage")
    mean_ref = med("mean_nonzero")
    return (
        abs(bbox[0] - ref_bbox[0]) * 1.0
        + abs(bbox[1] - ref_bbox[1]) * 1.0
        + abs(bbox[2] - ref_bbox[2]) * 1.0
        + abs(bbox[3] - ref_bbox[3]) * 1.0
        + abs(float(stats["coverage_percent"]) - coverage_ref) * 0.35
        + abs(float(stats["mean_nonzero"]) - mean_ref) * 0.015
        + (0 if stats["baseline_ink_bottom"] == INK_BOTTOM else 10)
    )


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("v2_root", type=Path)
    args = parser.parse_args()
    root = args.v2_root.resolve()
    base_path = root / "font" / "font_poc_00c7_diagnostics_boundary" / "TEST_REAL_GLYPH_JUE" / "00c7c9f9.xpr"
    output_root = root / "font" / "font_poc_00c7_diagnostics_boundary" / "TEST_REAL_GLYPH_JUE_STYLE_TUNING"
    output_root.mkdir(parents=True, exist_ok=True)

    _, base_plain, base = load(base_path)
    base_fd = base.font_data
    if base_fd.charmap[TARGET_CODEPOINT] != TARGET_INDEX or len(base_fd.glyphs) != 3210 or base.user.size != 0x2C778:
        raise RuntimeError("runtime-validated 厥 base has unexpected structure")

    refs: dict[str, bytes] = {}
    ref_stats: list[dict[str, object]] = []
    for char, cp in REFERENCE_CODEPOINTS.items():
        index = base_fd.charmap[cp]
        bitmap = extract_record_bitmap(base, index)
        refs[char] = bitmap
        s = bitmap_stats(bitmap)
        ref_stats.append({
            "character": char, "codepoint": f"U+{cp:04X}", "glyph_index": index,
            "record_raw_hex": base_fd.glyphs[index].packed.hex(),
            "rectangle": [base_fd.glyphs[index].u0, base_fd.glyphs[index].v0, base_fd.glyphs[index].u1, base_fd.glyphs[index].v1,
            ],
            "bbox_x0": s["ink_bbox_exclusive"][0], "bbox_y0": s["ink_bbox_exclusive"][1],
            "bbox_x1": s["ink_bbox_exclusive"][2], "bbox_y1": s["ink_bbox_exclusive"][3],
            "coverage": s["coverage_percent"], "mean_nonzero": s["mean_nonzero"],
            "bitmap": s,
        })

    candidates = [
        {
            "id": "A",
            "label": "A current Medium",
            "description": "当前成功版本：Medium 58px，原始灰度，不 embolden。",
            "font_file": str(FONT_MEDIUM), "font_family": "Noto Sans SC Medium", "font_size_px": 58,
            "embolden_px": 0, "gamma": 1.0,
        },
        {
            "id": "B",
            "label": "B Medium +1px",
            "description": "在当前版本基础上做 1px MaxFilter 加粗，重新居中并校准底线。",
            "font_file": str(FONT_MEDIUM), "font_family": "Noto Sans SC Medium", "font_size_px": 58,
            "embolden_px": 1, "gamma": 1.0,
        },
        {
            "id": "C",
            "label": "C Medium 57px",
            "description": "Medium 57px，保持底线 y=59，字面略收小，减少上下拥挤。",
            "font_file": str(FONT_MEDIUM), "font_family": "Noto Sans SC Medium", "font_size_px": 57,
            "embolden_px": 0, "gamma": 1.0,
        },
        {
            "id": "D",
            "label": "D Bold 56px",
            "description": "Bold 56px，较高笔画密度但缩小字面，作为重笔画备选。",
            "font_file": str(FONT_BOLD), "font_family": "Noto Sans SC Bold", "font_size_px": 56,
            "embolden_px": 0, "gamma": 1.0,
        },
    ]

    candidate_bitmaps: dict[str, bytes] = {}
    measured: list[dict[str, object]] = []
    base_texture = base.texture.texels
    u0, v0, u1, v1 = TARGET_RECT
    allowed = {y * base.texture.width + x for y in range(v0, v1) for x in range(u0, u1)}
    for profile in candidates:
        bitmap, row = render_candidate(profile)
        candidate_bitmaps[profile["id"]] = bitmap
        row["style_similarity_score"] = round(similarity_score(row["bitmap"], ref_stats), 4)
        measured.append(row)

        candidate_root = output_root / f"CANDIDATE_{profile['id']}"
        candidate_root.mkdir(parents=True, exist_ok=True)
        texture = bytearray(base_texture)
        for row_index in range(v1 - v0):
            offset = (v0 + row_index) * base.texture.width + u0
            texture[offset : offset + (u1 - u0)] = bitmap[row_index * CELL_W : (row_index + 1) * CELL_W]
        plain = base.rebuild({("USER", "FontData"): base.user.payload}, texture_texels=bytes(texture))
        encrypted = outer_transform(plain, filename_seed("00c7c9f9.xpr"))
        xpr_path = candidate_root / "00c7c9f9.xpr"
        xpr_path.write_bytes(encrypted)
        _, readback_plain, result = load(xpr_path)
        errors: list[str] = []
        if result.font_data.glyphs != base_fd.glyphs or result.font_data.charmap != base_fd.charmap:
            errors.append("USER font data changed")
        if result.tx2d.payload != base.tx2d.payload or readback_plain[: base.texture_data_offset] != base_plain[: base.texture_data_offset]:
            errors.append("descriptor/header changed")
        if result.user.size != base.user.size or len(result.font_data.glyphs) != 3210:
            errors.append("structure changed")
        changed = [i for i, (a, b) in enumerate(zip(base_texture, result.texture.texels)) if a != b]
        outside = [i for i in changed if i not in allowed]
        result_slot = b"".join(result.texture.texels[y * result.texture.width + u0 : y * result.texture.width + u1] for y in range(v0, v1))
        if result_slot != bitmap:
            errors.append("target slot readback mismatch")
        if outside:
            errors.append(f"{len(outside)} texture bytes changed outside target slot")
        errors.extend(validate_glyph_rectangles(result.font_data, result.texture))
        row["xpr"] = {
            "path": str(xpr_path),
            "encrypted_sha256": sha256(xpr_path.read_bytes()),
            "decrypted_sha256": sha256(readback_plain),
            "atlas_changed_byte_count": len(changed),
            "atlas_changed_outside_count": len(outside),
            "static_validation": "PASS" if not errors else "FAIL",
            "errors": errors,
        }
        Image.frombytes("L", (CELL_W, CELL_H), bitmap).resize((CELL_W * SCALE, CELL_H * SCALE), getattr(Image, "Resampling", Image).NEAREST).save(candidate_root / "bitmap_preview.png")
        # The texture is a 4096x4096 byte array and each crypto readback also
        # materializes a full XPR. Release per-candidate buffers before the
        # next variant so four candidates remain deterministic on Windows.
        del texture, plain, encrypted, readback_plain, result, changed, outside, result_slot
        gc.collect()

    reference_preview = output_root / "existing_mlg_references.png"
    make_preview(reference_preview, refs, {})
    candidate_preview = output_root / "glyph_jue_style_candidates.png"
    make_preview(candidate_preview, {}, {row["id"]: candidate_bitmaps[row["id"]] for row in measured})
    combined_preview = output_root / "glyph_jue_style_candidates_with_references.png"
    make_preview(combined_preview, refs, {row["id"]: candidate_bitmaps[row["id"]] for row in measured})

    recommended = min(measured, key=lambda row: float(row["style_similarity_score"]))["id"]
    profile = {
        "status": "PASS" if all(row["xpr"]["static_validation"] == "PASS" for row in measured) else "FAIL",
        "base": {
            "path": str(base_path), "encrypted_sha256": sha256(base_path.read_bytes()), "decrypted_sha256": sha256(base_plain),
            "runtime_status": "USER_CONFIRMED_GENERATED_GLYPH_RUNTIME_PASS",
        },
        "target": {"character": TARGET_CHAR, "codepoint": "U+53A5", "glyph_index": TARGET_INDEX, "rectangle": list(TARGET_RECT), "metrics_unchanged": True},
        "references": ref_stats,
        "candidates": measured,
        "recommended_candidate": recommended,
        "preview": {"references": str(reference_preview), "candidates": str(candidate_preview), "combined": str(combined_preview)},
        "structure_policy": "Only the target 58x67 atlas bitmap is changed in each candidate XPR.",
    }
    (output_root / "glyph_generation_profile_v1.json").write_text(json.dumps(profile, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")

    rec = next(row for row in measured if row["id"] == recommended)
    report = [
        "# FONT_GLYPH_STYLE_TUNING",
        "",
        "本轮只做单字 厥 U+53A5 的视觉风格候选。所有候选均从已实机通过的 TEST_REAL_GLYPH_JUE 读取，并仅替换新 atlas slot `[0,3333)-[58,3400)` 的 bitmap；glyph count、charmap、GlyphRecord、metrics、USER/XPR descriptors 均保持不变。",
        "",
        "## 结论",
        "",
        f"- 推荐：`{recommended}`（静态参考指标综合距离最低；最终仍应以游戏画面判断）。",
        "- 现阶段不批量生成 145 个字，不改变整体 XPR 结构。",
        "- `GENERATED_GLYPH_RUNTIME_VALIDATED = YES` 已由用户实机确认；以下候选是风格替换版本，尚未分别实机比较。",
        "",
        "## 候选差异",
        "",
        "| 候选 | 方案 | bbox | 像素覆盖 | 非零灰度均值 | 说明 |",
        "|---|---|---|---:|---:|---|",
    ]
    for row in measured:
        s = row["bitmap"]
        report.append(f"| {row['id']} | {row['font_family']} {row['font_size_px']}px / embolden {row['embolden_px']} / gamma {row['gamma']} | `{s['ink_bbox_exclusive']}` | {s['coverage_percent']}% | {s['mean_nonzero']} | {row['description']} |")
    report.extend([
        "",
        "## 参考字实测",
        "",
        "参考字来自当前 MLG 中文 glyph，直接按各自 GlyphRecord UV 从 TX2D 提取；不是重新栅格化。完整索引、record、UV、bbox、覆盖率和灰度统计见 `glyph_generation_profile_v1.json`。",
        "",
        "| 字符 | index | bbox | 覆盖率 | 非零灰度均值 |",
        "|---|---:|---|---:|---:|",
    ])
    for row in ref_stats:
        s = row["bitmap"]
        report.append(f"| {row['character']} | {row['glyph_index']} | `{s['ink_bbox_exclusive']}` | {s['coverage_percent']}% | {s['mean_nonzero']} |")
    report.extend([
        "",
        "## 对照图",
        "",
        f"- 参考字：`{reference_preview}`",
        f"- 候选 A-D：`{candidate_preview}`",
        f"- 参考字 + 候选 A-D：`{combined_preview}`",
        "",
        "## Raster 参数与复现",
        "",
        "- 所有候选：Pillow 9.0.1 FreeTypeFont/ImageDraw，`layout_engine=BASIC`，8-bit L-mode 灰度抗锯齿，zero background/nonzero ink，anchor=`ls`。",
        "- baseline：所有候选最终校准为 ink bottom `y=59`；水平位置按实际 bbox 在 58px cell 内居中。",
        "- A：`Noto Sans SC Medium` 58px，embolden 0，gamma 1.0；当前成功版本基线。",
        "- B：A + 1px MaxFilter 加粗，再居中和 baseline 校准；更粗、更高覆盖率。",
        "- C：`Noto Sans SC Medium` 57px；字面略小，保留 baseline，边缘留白稍多。",
        "- D：`Noto Sans SC Bold` 56px；字面收小以控制高度，笔画最重。",
        "",
        "## 静态保护结果",
        "",
        "每个候选的 XPR 都重新经过 `encrypt → decrypt → parser`，并验证：除目标 atlas rectangle 外 texture byte-identical；USER、GlyphRecords、charmap、TX2D descriptor/header、目标 record/metrics 均保持不变。详见 JSON 中每个候选的 `xpr.static_validation`。",
        "",
        "## 推荐意见",
        "",
        f"推荐先使用 `{recommended}` 作为后续批量生成模板候选。它的 bbox、覆盖率和灰度密度与 9 个 MLG 参考字的总体分布最接近；但在批量生产前仍应先对该版本做一次实机视觉确认。",
    ])
    (output_root / "FONT_GLYPH_STYLE_TUNING.md").write_text("\n".join(report) + "\n", encoding="utf-8")
    print(f"generated {len(measured)} candidates; recommended={recommended}; output={output_root}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
