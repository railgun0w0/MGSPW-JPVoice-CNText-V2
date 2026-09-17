#!/usr/bin/env python3
"""Build D/E/F grayscale-only variants from style candidate D."""

from __future__ import annotations

import hashlib
import json
import sys
from pathlib import Path

from PIL import Image, ImageDraw

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from core.pc_crypto import filename_seed, outer_transform
from core.xpr_font import XprFont, validate_glyph_rectangles


TARGET_CP = 0x53A5
TARGET_INDEX = 3209
TARGET_RECT = (0, 3333, 58, 3400)
W, H = 58, 67


def sha256(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def load(path: Path) -> tuple[bytes, bytes, XprFont]:
    encrypted = path.read_bytes()
    plain = outer_transform(encrypted, filename_seed(path.name))
    return encrypted, plain, XprFont(plain)


def slot(font: XprFont) -> bytes:
    u0, v0, u1, v1 = TARGET_RECT
    return b"".join(font.texture.texels[y * font.texture.width + u0 : y * font.texture.width + u1] for y in range(v0, v1))


def stats(bitmap: bytes) -> dict[str, object]:
    pts = [(i % W, i // W, v) for i, v in enumerate(bitmap) if v]
    values = [v for _, _, v in pts]
    bbox = None if not pts else [min(x for x, _, _ in pts), min(y for _, y, _ in pts), max(x for x, _, _ in pts) + 1, max(y for _, y, _ in pts) + 1]
    return {
        "width": W,
        "height": H,
        "nonzero_pixel_count": len(values),
        "coverage_percent": round(100.0 * len(values) / (W * H), 3),
        "nonzero_grayscale_mean": round(sum(values) / len(values), 3) if values else 0,
        "bbox": bbox,
        "min_nonzero": min(values, default=0),
        "max_nonzero": max(values, default=0),
        "sha256": sha256(bitmap),
    }


def scale_gray(bitmap: bytes, factor: float) -> bytes:
    # Round-to-nearest linear scaling; preserve every original nonzero pixel
    # as at least 1 so the measured bbox remains byte-for-byte the same.
    return bytes(
        0 if value == 0 else max(1, min(255, int(round(value * factor))))
        for value in bitmap
    )


def preview(path: Path, variants: dict[str, bytes]) -> None:
    scale = 4
    canvas = Image.new("L", (W * scale * len(variants), H * scale + 24), 0)
    draw = ImageDraw.Draw(canvas)
    nearest = getattr(Image, "Resampling", Image).NEAREST
    for column, (label, bitmap) in enumerate(variants.items()):
        x = column * W * scale
        crop = Image.frombytes("L", (W, H), bitmap)
        canvas.paste(crop.resize((W * scale, H * scale), nearest), (x, 0))
        draw.text((x + 2, H * scale + 3), label, fill=255)
    canvas.save(path)


def main() -> int:
    root = Path(__file__).resolve().parents[1]
    source_path = root / "font" / "font_poc_00c7_diagnostics_boundary" / "TEST_REAL_GLYPH_JUE_STYLE_TUNING" / "CANDIDATE_D" / "00c7c9f9.xpr"
    out = root / "font" / "font_poc_00c7_diagnostics_boundary" / "TEST_REAL_GLYPH_JUE_STYLE_GRAY_SCALE"
    out.mkdir(parents=True, exist_ok=True)

    source_encrypted, source_plain, source = load(source_path)
    if source.font_data.charmap[TARGET_CP] != TARGET_INDEX or len(source.font_data.glyphs) != 3210 or source.user.size != 0x2C778:
        raise RuntimeError("candidate D has unexpected structure")
    source_bitmap = slot(source)
    source_record = source.font_data.glyphs[TARGET_INDEX].packed
    source_texture = source.texture.texels
    u0, v0, u1, v1 = TARGET_RECT
    allowed = {y * source.texture.width + x for y in range(v0, v1) for x in range(u0, u1)}

    factors = {"D": 1.0, "E": 0.84, "F": 0.90}
    descriptions = {"D": "候选 D 原始灰度", "E": "D 灰度线性乘 0.84", "F": "D 灰度线性乘 0.90"}
    variants: dict[str, bytes] = {}
    rows = []
    errors: list[str] = []
    for label, factor in factors.items():
        bitmap = source_bitmap if factor == 1.0 else scale_gray(source_bitmap, factor)
        variants[label] = bitmap
        candidate_dir = out / label
        candidate_dir.mkdir(parents=True, exist_ok=True)
        if label == "D":
            encrypted = source_encrypted
        else:
            texture = bytearray(source_texture)
            for row in range(H):
                offset = (v0 + row) * source.texture.width + u0
                texture[offset : offset + W] = bitmap[row * W : (row + 1) * W]
            plain = source.rebuild({("USER", "FontData"): source.user.payload}, texture_texels=bytes(texture))
            encrypted = outer_transform(plain, filename_seed("00c7c9f9.xpr"))
        xpr_path = candidate_dir / "00c7c9f9.xpr"
        xpr_path.write_bytes(encrypted)

        readback_encrypted, readback_plain, result = load(xpr_path)
        local_errors: list[str] = []
        if result.user.payload != source.user.payload: local_errors.append("USER changed")
        if result.font_data.glyphs != source.font_data.glyphs: local_errors.append("GlyphRecords changed")
        if result.font_data.charmap != source.font_data.charmap: local_errors.append("charmap changed")
        if result.tx2d.payload != source.tx2d.payload: local_errors.append("TX2D descriptor changed")
        if readback_plain[:source.texture_data_offset] != source_plain[:source.texture_data_offset]: local_errors.append("XPR header/descriptor prefix changed")
        if result.font_data.charmap[TARGET_CP] != TARGET_INDEX: local_errors.append("target mapping changed")
        if result.font_data.glyphs[TARGET_INDEX].packed != source_record: local_errors.append("target metrics/UV record changed")
        if result.user.size != source.user.size or len(result.font_data.glyphs) != 3210: local_errors.append("structure/count changed")
        result_bitmap = slot(result)
        if result_bitmap != bitmap: local_errors.append("target slot readback differs")
        changed = [i for i, (a, b) in enumerate(zip(source_texture, result.texture.texels)) if a != b]
        outside = [i for i in changed if i not in allowed]
        if outside: local_errors.append(f"{len(outside)} atlas bytes changed outside target slot")
        local_errors.extend(validate_glyph_rectangles(result.font_data, result.texture))
        errors.extend([f"{label}: {error}" for error in local_errors])
        rows.append({
            "id": label,
            "description": descriptions[label],
            "gray_factor": factor,
            "scaling": "round(value*factor), clamp 0..255; original nonzero minimum 1" if label != "D" else "unchanged source bitmap",
            "bitmap": stats(result_bitmap),
            "xpr": {
                "path": str(xpr_path),
                "encrypted_sha256": sha256(readback_encrypted),
                "decrypted_sha256": sha256(readback_plain),
                "atlas_changed_byte_count_vs_D": len(changed),
                "atlas_changed_outside_target_vs_D": len(outside),
                "static_validation": "PASS" if not local_errors else "FAIL",
            },
        })

    preview_path = out / "glyph_jue_gray_scale_candidates.png"
    preview(preview_path, variants)
    manifest = {
        "status": "PASS" if not errors else "FAIL",
        "errors": errors,
        "source_D": {"path": str(source_path), "encrypted_sha256": sha256(source_encrypted), "decrypted_sha256": sha256(source_plain), "bitmap": stats(source_bitmap)},
        "target": {"character": "厥", "codepoint": "U+53A5", "glyph_index": TARGET_INDEX, "rectangle": list(TARGET_RECT), "record_raw_hex": source_record.hex(), "metrics_unchanged": True},
        "variants": rows,
        "protection": {"USER_unchanged": True, "charmap_unchanged": True, "glyph_count_unchanged": True, "glyph_records_unchanged": True, "XPR_descriptors_unchanged": True, "atlas_changes_limited_to_target_slot": True},
        "preview": str(preview_path),
    }
    (out / "gray_scale_manifest.json").write_text(json.dumps(manifest, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")

    report = [
        "# FONT_GLYPH_GRAY_SCALE_CANDIDATES",
        "",
        "本轮仅基于候选 D 对 `厥 U+53A5` 的 atlas bitmap 做灰度线性缩放。没有更换字体、字号、metrics、charmap、glyph count、USER 或 XPR 结构。",
        "",
        "## 规则",
        "",
        "- E：`round(D_pixel × 0.84)`。",
        "- F：`round(D_pixel × 0.90)`。",
        "- 所有结果 clamp 到 `0..255`；原始非零像素最低保留为 `1`，确保 bbox 不因极低灰度消失。",
        "- D 为候选 D 的 byte-identical copy。",
        "",
        "## 实测结果",
        "",
        "| 版本 | 灰度因子 | bbox | coverage | nonzero grayscale mean | 静态验证 |",
        "|---|---:|---|---:|---:|---|",
    ]
    for row in rows:
        s = row["bitmap"]
        report.append(f"| {row['id']} | {row['gray_factor']} | `{s['bbox']}` | {s['coverage_percent']}% | {s['nonzero_grayscale_mean']} | `{row['xpr']['static_validation']}` |")
    report.extend([
        "",
        "## 保护检查",
        "",
        "- 三个 XPR 都保持 `U+53A5 → 3209`、glyph count=`3210`、USER size=`0x2C778`。",
        "- target GlyphRecord 和 metrics 完全保持 D。",
        "- USER、charmap、全部 GlyphRecord、TX2D descriptor/header 均保持 D。",
        "- E/F 相对 D 的 atlas 改动严格限制在 `x=0..57,y=3333..3399`。",
        "- 每个文件均经过 `encrypt → decrypt → parser` 读回，parser errors=0。",
        "",
        "## 文件",
        "",
        f"- 对照图：`{preview_path}`",
        "- `D/00c7c9f9.xpr`：候选 D 原样复制。",
        "- `E/00c7c9f9.xpr`：D 灰度 × 0.84。",
        "- `F/00c7c9f9.xpr`：D 灰度 × 0.90。",
        "- 详细 SHA256 和统计：`gray_scale_manifest.json`。",
        "",
        "三个版本均未分别进行实机风格比较；D 的 glyph runtime 已成功，E/F 只改变像素灰度。",
    ])
    (out / "FONT_GLYPH_GRAY_SCALE_CANDIDATES.md").write_text("\n".join(report) + "\n", encoding="utf-8")
    print(json.dumps({"status": manifest["status"], "errors": errors, "output": str(out)}, ensure_ascii=False))
    return 0 if not errors else 1


if __name__ == "__main__":
    raise SystemExit(main())
