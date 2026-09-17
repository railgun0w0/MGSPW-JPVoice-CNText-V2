#!/usr/bin/env python3
"""Finalize reports/previews from the four already-built style XPRs."""

from __future__ import annotations

import json
import runpy
from pathlib import Path


def main() -> int:
    tool = runpy.run_path(str(Path(__file__).with_name("Tune-Jue-Style.py")))
    root = Path(__file__).resolve().parents[1]
    output_root = root / "font" / "font_poc_00c7_diagnostics_boundary" / "TEST_REAL_GLYPH_JUE_STYLE_TUNING"
    base_path = root / "font" / "font_poc_00c7_diagnostics_boundary" / "TEST_REAL_GLYPH_JUE" / "00c7c9f9.xpr"
    _, base_plain, base = tool["load"](base_path)
    target_rect = tool["TARGET_RECT"]
    target_index = tool["TARGET_INDEX"]
    target_cp = tool["TARGET_CODEPOINT"]

    ref_stats = []
    refs = {}
    for char, cp in tool["REFERENCE_CODEPOINTS"].items():
        index = base.font_data.charmap[cp]
        bitmap = tool["extract_record_bitmap"](base, index)
        refs[char] = bitmap
        s = tool["bitmap_stats"](bitmap)
        ref_stats.append({
            "character": char,
            "codepoint": f"U+{cp:04X}",
            "glyph_index": index,
            "record_raw_hex": base.font_data.glyphs[index].packed.hex(),
            "rectangle": [base.font_data.glyphs[index].u0, base.font_data.glyphs[index].v0, base.font_data.glyphs[index].u1, base.font_data.glyphs[index].v1],
            "bitmap": s,
            "bbox_x0": s["ink_bbox_exclusive"][0], "bbox_y0": s["ink_bbox_exclusive"][1],
            "bbox_x1": s["ink_bbox_exclusive"][2], "bbox_y1": s["ink_bbox_exclusive"][3],
            "coverage": s["coverage_percent"], "mean_nonzero": s["mean_nonzero"],
        })

    base_texture = base.texture.texels
    u0, v0, u1, v1 = target_rect
    allowed = {y * base.texture.width + x for y in range(v0, v1) for x in range(u0, u1)}
    candidates = {}
    rows = []
    errors = []
    descriptions = {
        "A": "当前成功版本：Medium 58px，原始灰度，不 embolden。",
        "B": "Medium 58px + 1px MaxFilter 加粗；笔画更重。",
        "C": "Medium 57px；字面略收小，baseline 保持一致。",
        "D": "Bold 56px；字面收小、笔画密度最高。",
    }
    for cid in "ABCD":
        xpr_path = output_root / f"CANDIDATE_{cid}" / "00c7c9f9.xpr"
        _, plain, result = tool["load"](xpr_path)
        bitmap = tool["extract_record_bitmap"](result, target_index)
        candidates[cid] = bitmap
        s = tool["bitmap_stats"](bitmap)
        changed = [i for i, (a, b) in enumerate(zip(base_texture, result.texture.texels)) if a != b]
        outside = [i for i in changed if i not in allowed]
        local_errors = []
        if result.font_data.glyphs != base.font_data.glyphs: local_errors.append("GlyphRecord changed")
        if result.font_data.charmap != base.font_data.charmap: local_errors.append("charmap changed")
        if result.user.payload != base.user.payload: local_errors.append("USER payload changed")
        if result.tx2d.payload != base.tx2d.payload or plain[:base.texture_data_offset] != base_plain[:base.texture_data_offset]: local_errors.append("descriptor/header changed")
        if result.font_data.charmap[target_cp] != target_index: local_errors.append("target mapping changed")
        if result.font_data.glyphs[target_index].packed != base.font_data.glyphs[target_index].packed: local_errors.append("target record changed")
        if outside: local_errors.append(f"{len(outside)} bytes changed outside target slot")
        local_errors.extend(tool["validate_glyph_rectangles"](result.font_data, result.texture))
        errors.extend([f"{cid}: {e}" for e in local_errors])
        rows.append({
            "id": cid,
            "description": descriptions[cid],
            "bitmap": s,
            "xpr": {
                "path": str(xpr_path),
                "encrypted_sha256": tool["sha256"](xpr_path.read_bytes()),
                "decrypted_sha256": tool["sha256"](plain),
                "static_validation": "PASS" if not local_errors else "FAIL",
                "atlas_changed_byte_count": len(changed),
                "atlas_changed_outside_count": len(outside),
            },
        })

    recommended = min(rows, key=lambda row: float(tool["similarity_score"](row["bitmap"], ref_stats)))
    for row in rows:
        row["style_similarity_score"] = round(float(tool["similarity_score"](row["bitmap"], ref_stats)), 4)
    recommended_id = recommended["id"]

    refs_image = output_root / "existing_reference_glyphs.png"
    candidates_image = output_root / "glyph_jue_style_candidates.png"
    combined_image = output_root / "glyph_jue_style_candidates_with_references.png"
    tool["make_preview"](refs_image, refs, {})
    tool["make_preview"](candidates_image, {}, candidates)
    tool["make_preview"](combined_image, refs, candidates)

    profile = {
        "status": "PASS" if not errors else "FAIL",
        "base": {"path": str(base_path), "encrypted_sha256": tool["sha256"](base_path.read_bytes()), "decrypted_sha256": tool["sha256"](base_plain), "runtime_status": "GENERATED_GLYPH_RUNTIME_PASS_CONFIRMED_BY_USER"},
        "target": {"character": "厥", "codepoint": "U+53A5", "glyph_index": target_index, "rectangle": list(target_rect), "metrics_unchanged": True},
        "references": ref_stats,
        "candidates": rows,
        "recommended_candidate": recommended_id,
        "preview": {"references": str(refs_image), "candidates": str(candidates_image), "combined": str(combined_image)},
        "errors": errors,
    }
    (output_root / "glyph_generation_profile_v1.json").write_text(json.dumps(profile, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")

    report = [
        "# FONT_GLYPH_STYLE_TUNING",
        "",
        "本轮针对已经实机成功的 `厥 U+53A5` 做视觉风格拟合。A-D 均基于 `TEST_REAL_GLYPH_JUE`，仅替换 `[0,3333)-[58,3400)` 的 atlas bitmap；glyph count、charmap、GlyphRecord、metrics、USER 和 XPR descriptor/header 保持不变。",
        "",
        "## 结论",
        "",
        f"推荐候选：`{recommended_id}`。该推荐依据 9 个现有 MLG 参考字的 bbox、覆盖率和非零灰度均值做静态比较；最终批量模板仍应先进行一次实机视觉确认。",
        "",
        "| 候选 | 方案 | bbox | 覆盖率 | 非零灰度均值 | 风格说明 | 静态验证 |",
        "|---|---|---|---:|---:|---|---|",
    ]
    for row in rows:
        s = row["bitmap"]
        report.append(f"| {row['id']} | `{row['id']}` | `{s['ink_bbox_exclusive']}` | {s['coverage_percent']}% | {s['mean_nonzero']} | {row['description']} | `{row['xpr']['static_validation']}` |")
    report.extend([
        "",
        "## 参考字",
        "",
        "直接从当前 MLG TX2D 按 GlyphRecord UV 提取：",
        "",
        "| 字符 | index | bbox | 覆盖率 | 非零灰度均值 |",
        "|---|---:|---|---:|---:|",
    ])
    for row in ref_stats:
        s = row["bitmap"]
        report.append(f"| {row['character']} | {row['glyph_index']} | `{s['ink_bbox_exclusive']}` | {s['coverage_percent']}% | {s['mean_nonzero']} |")
    report.extend([
        "",
        "## Raster 参数",
        "",
        "- A：`C:\\Windows\\Fonts\\Noto Sans SC Medium (TrueType).otf`，58px，Pillow 9.0.1/FreeType BASIC，8-bit L 灰度抗锯齿，gamma 1.0。",
        "- B：A 的 1px MaxFilter embolden，之后重新居中并将 ink bottom 校准到 y=59。",
        "- C：同一 Medium 字体 57px，baseline bottom y=59。",
        "- D：`C:\\Windows\\Fonts\\Noto Sans SC Bold (TrueType).otf`，56px，baseline bottom y=59。",
        "- 所有候选均为 58x67 cell，zero background/nonzero ink；没有修改 metrics。",
        "",
        "## 产物",
        "",
        f"- 参考并排图：`{refs_image}`",
        f"- A-D 候选图：`{candidates_image}`",
        f"- 参考 + 候选合并图：`{combined_image}`",
        "- 每个 `CANDIDATE_A` 至 `CANDIDATE_D` 子目录还包含可独立测试的 `00c7c9f9.xpr` 和 `bitmap_preview.png`。",
        "",
        "## 建议",
        "",
        f"先实机比较候选 `{recommended_id}`；若与现有字形仍有明显粗细差，再在不改变结构的前提下微调 gamma/embolden。暂不将任何候选扩展到 145 个字符。",
    ])
    (output_root / "FONT_GLYPH_STYLE_TUNING.md").write_text("\n".join(report) + "\n", encoding="utf-8")
    print(json.dumps({"status": profile["status"], "recommended": recommended_id, "errors": errors}, ensure_ascii=False))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
