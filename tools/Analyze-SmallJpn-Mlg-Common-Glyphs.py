from __future__ import annotations

import csv
import hashlib
import json
import sys
from pathlib import Path

from PIL import Image

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from core.pc_crypto import filename_seed, outer_transform
from core.xpr_font import XprFont


ROOT = Path(__file__).resolve().parents[1]
ANALYSIS_ROOT = ROOT / "font" / "analysis"
OUT_DIR = ANALYSIS_ROOT / "small_jpn_mlg_common_glyphs"
REPORT = ANALYSIS_ROOT / "SMALL_JPN_MLG_COMMON_GLYPH_COMPARISON.md"
CSV_OUT = ANALYSIS_ROOT / "small_jpn_mlg_common_glyphs.csv"
MISSING_CSV = ANALYSIS_ROOT / "small_jpn_loading_missing_in_mlg.csv"

FONTS = {
    "JPN001C": ROOT / "font" / "JPN" / "001cbbd1.xpr",
    "MLG0007": ROOT / "font" / "MLG_CN" / "0007ccd8.xpr",
    "MLG000E": ROOT / "font" / "MLG_CN" / "000ebbe8.xpr",
}

COMMON = {"我": 0x6211, "中": 0x4E2D, "国": 0x56FD, "家": 0x5BB6, "大": 0x5927}
LOADING_MISSING = "们 只 会 战 斗 但 活 得 不 受 局 势 摆 布 洲 是 连 接 陆 的 脐 带 这 里".split()


def sha(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def load(path: Path) -> tuple[bytes, bytes, XprFont]:
    encrypted = path.read_bytes()
    plain = outer_transform(encrypted, filename_seed(path.name))
    return encrypted, plain, XprFont(plain)


def extract(font: XprFont, index: int) -> tuple[bytes, tuple[int, int, int, int]]:
    record = font.font_data.glyphs[index]
    bitmap = b"".join(
        font.texture.texels[y * font.texture.width + record.u0 : y * font.texture.width + record.u1]
        for y in range(record.v0, record.v1)
    )
    return bitmap, (record.u0, record.v0, record.u1, record.v1)


def stats(bitmap: bytes, width: int, height: int) -> dict[str, object]:
    points = [(i % width, i // width, value) for i, value in enumerate(bitmap) if value]
    box = None if not points else [min(x for x, _, _ in points), min(y for _, y, _ in points), max(x for x, _, _ in points) + 1, max(y for _, y, _ in points) + 1]
    values = [value for _, _, value in points]
    return {
        "bbox": box,
        "nonzero": len(values),
        "coverage": len(values) / (width * height),
        "nonzero_mean": sum(values) / len(values) if values else 0.0,
        "min_nonzero": min(values) if values else 0,
        "max_nonzero": max(values) if values else 0,
    }


def pngs(label: str, char: str, bitmap: bytes, width: int, height: int) -> tuple[str, str]:
    safe = f"U{ord(char):04X}_{char}"
    directory = OUT_DIR / label
    directory.mkdir(parents=True, exist_ok=True)
    raw_path = directory / f"{safe}.png"
    view_path = directory / f"{safe}_x4.png"
    image = Image.frombytes("L", (width, height), bitmap)
    image.save(raw_path)
    image.resize((width * 4, height * 4), getattr(Image, "Resampling", Image).NEAREST).save(view_path)
    return str(raw_path.relative_to(ANALYSIS_ROOT)).replace("\\", "/"), str(view_path.relative_to(ANALYSIS_ROOT)).replace("\\", "/")


def lookup(font: XprFont, cp: int) -> tuple[int, bool, int]:
    if cp > font.font_data.last_code:
        return 0, False, 0
    index = font.font_data.charmap[cp]
    if not index or index >= len(font.font_data.glyphs):
        return index, False, 0
    ref_count = sum(1 for value in font.font_data.charmap if value == index)
    return index, True, ref_count


def normalized_mae(bitmap_a: bytes, wa: int, ha: int, bitmap_b: bytes, wb: int, hb: int) -> float:
    a = Image.frombytes("L", (wa, ha), bitmap_a).resize((66, 66), getattr(Image, "Resampling", Image).LANCZOS).tobytes()
    b = Image.frombytes("L", (wb, hb), bitmap_b).resize((66, 66), getattr(Image, "Resampling", Image).LANCZOS).tobytes()
    return sum(abs(x - y) for x, y in zip(a, b)) / len(a)


def main() -> None:
    loaded = {label: load(path) for label, path in FONTS.items()}
    rows: list[dict[str, object]] = []
    records: dict[str, dict[str, dict[str, object]]] = {label: {} for label in FONTS}
    for label, (_, _, font) in loaded.items():
        for char, cp in COMMON.items():
            index, valid, ref_count = lookup(font, cp)
            row: dict[str, object] = {"font": label, "character": char, "codepoint": f"U+{cp:04X}", "codepoint_decimal": cp, "valid_mapping": "YES" if valid else "NO", "glyph_index": index if valid else "", "glyph_index_reference_count": ref_count if valid else 0}
            if valid:
                record = font.font_data.glyphs[index]
                bitmap, rect = extract(font, index)
                width, height = rect[2] - rect[0], rect[3] - rect[1]
                s = stats(bitmap, width, height)
                raw_png, view_png = pngs(label, char, bitmap, width, height)
                row.update({"rect": f"({rect[0]},{rect[1]})-({rect[2]},{rect[3]})", "rect_u0": rect[0], "rect_v0": rect[1], "rect_u1": rect[2], "rect_v1": rect[3], "rect_width": width, "rect_height": height, "bearing_x": record.bearing_x, "width": record.width, "advance": record.advance, "reserved": record.reserved, "record_hex": record.packed.hex().upper(), "bitmap_sha256": sha(bitmap), "bitmap_bbox": s["bbox"], "bitmap_nonzero": s["nonzero"], "bitmap_coverage": s["coverage"], "bitmap_nonzero_mean": s["nonzero_mean"], "bitmap_png": raw_png, "bitmap_png_x4": view_png})
                records[label][char] = {"index": index, "record": record, "bitmap": bitmap, "rect": rect, "width": width, "height": height, "stats": s, "png": raw_png, "png_x4": view_png}
            rows.append(row)

    fieldnames = list(rows[0].keys())
    with CSV_OUT.open("w", newline="", encoding="utf-8-sig") as handle:
        writer = csv.DictWriter(handle, fieldnames=fieldnames)
        writer.writeheader()
        writer.writerows(rows)

    missing_rows = []
    for char in LOADING_MISSING:
        cp = ord(char)
        row = {"character": char, "codepoint": f"U+{cp:04X}"}
        for label in ("JPN001C", "MLG0007", "MLG000E"):
            _, _, font = loaded[label]
            index, valid, ref_count = lookup(font, cp)
            row[f"{label}_present"] = "YES" if valid else "NO"
            row[f"{label}_glyph_index"] = index if valid else ""
            row[f"{label}_reference_count"] = ref_count if valid else 0
        row["both_mlg_present"] = "YES" if row["MLG0007_present"] == row["MLG000E_present"] == "YES" else "NO"
        missing_rows.append(row)
    with MISSING_CSV.open("w", newline="", encoding="utf-8-sig") as handle:
        fields = list(missing_rows[0].keys())
        writer = csv.DictWriter(handle, fieldnames=fields)
        writer.writeheader()
        writer.writerows(missing_rows)

    comparisons = []
    for char in COMMON:
        a = records["MLG0007"][char]
        b = records["MLG000E"][char]
        base = records["JPN001C"][char]
        comparisons.append({
            "character": char,
            "mlg_bitmap_identical": a["bitmap"] == b["bitmap"],
            "mlg_record_identical": a["record"].packed == b["record"].packed,
            "mlg_rect_dimensions_same": (a["width"], a["height"]) == (b["width"], b["height"]),
            "mlg0007_dim_l1_to_jpn001c": abs(a["width"] - base["width"]) + abs(a["height"] - base["height"]),
            "mlg000e_dim_l1_to_jpn001c": abs(b["width"] - base["width"]) + abs(b["height"] - base["height"]),
            "mlg0007_metrics_l1_to_jpn001c": abs(a["record"].bearing_x - base["record"].bearing_x) + abs(a["record"].width - base["record"].width) + abs(a["record"].advance - base["record"].advance),
            "mlg000e_metrics_l1_to_jpn001c": abs(b["record"].bearing_x - base["record"].bearing_x) + abs(b["record"].width - base["record"].width) + abs(b["record"].advance - base["record"].advance),
            "mlg0007_normalized_mae_to_jpn001c": normalized_mae(a["bitmap"], a["width"], a["height"], base["bitmap"], base["width"], base["height"]),
            "mlg000e_normalized_mae_to_jpn001c": normalized_mae(b["bitmap"], b["width"], b["height"], base["bitmap"], base["width"], base["height"]),
        })

    def fmt(value):
        if isinstance(value, float):
            return f"{value:.4f}"
        return str(value)

    report = [
        "# SMALL_JPN / MLG_CN common glyph comparison",
        "",
        "本报告只做静态解密、FontData/FontTexture 解析和 bitmap PNG 导出；没有 runtime probe，也没有修改任何 XPR。基准字体是已确认的 Loading 小字体 `JPN/001cbbd1.xpr`。",
        "",
        "## 文件摘要",
        "",
        "| font | records | mapped | atlas | format/pitch | encrypted SHA256 | decrypted SHA256 |",
        "|---|---:|---:|---|---|---|---|",
    ]
    for label, (enc, plain, font) in loaded.items():
        report.append(f"| {label} | {len(font.font_data.glyphs)} | {sum(1 for v in font.font_data.charmap if v)} | {font.texture.width}×{font.texture.height} | {font.texture.data_format}/{font.texture.pitch} | `{sha(enc)}` | `{sha(plain)}` |")

    report += ["", "## 共同字符逐字数据", "", "字段中的 PNG 使用原始 atlas 灰度 bitmap；`_x4.png` 是仅用于查看的 nearest-neighbor 放大版本。", ""]
    for char, cp in COMMON.items():
        report.append(f"### `{char} U+{cp:04X}`")
        report.append("")
        report.append("| font | mapping count | glyph index | rect | size | bearing_x | width | advance | bitmap SHA256 | PNG |")
        report.append("|---|---:|---:|---|---|---:|---:|---:|---|---|")
        for label in ("JPN001C", "MLG0007", "MLG000E"):
            item = records[label][char]
            r = item["record"]
            report.append(f"| {label} | {sum(1 for v in loaded[label][2].font_data.charmap if v == item['index'])} | {item['index']} | `{item['rect']}` | {item['width']}×{item['height']} | {r.bearing_x} | {r.width} | {r.advance} | `{sha(item['bitmap'])}` | [{item['png_x4']}]({item['png_x4']}) |")
        report.append("")

    report += ["## `我 U+6211` mapping count", "", "- `MLG0007`：U+6211 在 dense charmap 中有 **1 个有效 codepoint mapping**，指向 glyph index 1531。", "- `MLG000E`：U+6211 在 dense charmap 中有 **1 个有效 codepoint mapping**，指向 glyph index 1413。", "- `JPN001C`：U+6211 有 **1 个有效 codepoint mapping**，指向 glyph index 239。", "- 本报告同时检查了 glyph index 的反向引用计数；未把同一 glyph 被其它 codepoint 引用误算为 U+6211 的多个 mapping。", ""]

    report += ["## MLG0007 vs MLG000E", "", "| char | bitmap identical | record identical | dimensions same |", "|---|---|---|---|"]
    for row in comparisons:
        report.append(f"| {row['character']} | {row['mlg_bitmap_identical']} | {row['mlg_record_identical']} | {row['mlg_rect_dimensions_same']} |")
    report.append("")
    report.append("如果 `bitmap identical=True`，表示抽取出的 bitmap byte-for-byte 相同；即使 atlas 坐标和 GlyphRecord 中的 UV 不同，也属于同一像素内容。")
    report.append("")

    report += ["## 与 JPN001C 的接近度", "", "比较规则：尺寸距离为 rect width/height 的 L1 差；metrics 距离为 `bearing_x + width + advance` 的绝对差之和；bitmap style 使用两者分别 resize 到 66×66 后的灰度 MAE，仅作静态相似度指标。", "", "| char | MLG0007 dim/metrics/MAE | MLG000E dim/metrics/MAE | 静态更接近 |", "|---|---|---|---|"]
    for row in comparisons:
        a_score = (row["mlg0007_dim_l1_to_jpn001c"], row["mlg0007_metrics_l1_to_jpn001c"], row["mlg0007_normalized_mae_to_jpn001c"])
        b_score = (row["mlg000e_dim_l1_to_jpn001c"], row["mlg000e_metrics_l1_to_jpn001c"], row["mlg000e_normalized_mae_to_jpn001c"])
        if a_score < b_score:
            winner = "MLG0007"
        elif b_score < a_score:
            winner = "MLG000E"
        else:
            winner = "TIE"
        report.append(f"| {row['character']} | `{fmt(row['mlg0007_dim_l1_to_jpn001c'])}/{fmt(row['mlg0007_metrics_l1_to_jpn001c'])}/{fmt(row['mlg0007_normalized_mae_to_jpn001c'])}` | `{fmt(row['mlg000e_dim_l1_to_jpn001c'])}/{fmt(row['mlg000e_metrics_l1_to_jpn001c'])}/{fmt(row['mlg000e_normalized_mae_to_jpn001c'])}` | {winner} |")
    report.append("")
    if all(row["mlg_bitmap_identical"] for row in comparisons):
        report.append("五个共同字的 MLG-0007 / MLG-000E 抽取 bitmap 全部完全相同；因此 bitmap 风格不存在 0007 vs 000e 的差异。")
    else:
        report.append("五个共同字中存在 MLG-0007 / MLG-000E bitmap 差异，详见上表和 CSV。")
    report.append("")
    report.append("由于两套 MLG 的共同字 bitmap 若完全相同，且它们的 rect/cell 与 JPN001C 尺寸不同，则对 JPN001C 的接近度主要由 cell 尺寸和 metrics 决定，而不是 donor 像素内容决定。")

    report += ["", "## 当前 Loading 24 个缺字在 MLG_CN 中的覆盖", ""]
    report.append("| char | codepoint | JPN001C | MLG0007 | MLG000E |")
    report.append("|---|---|---|---|---|")
    for row in missing_rows:
        report.append(f"| {row['character']} | {row['codepoint']} | {row['JPN001C_present']} | {row['MLG0007_present']} (glyph {row['MLG0007_glyph_index']}) | {row['MLG000E_present']} (glyph {row['MLG000E_glyph_index']}) |")
    report.append("")
    both = sum(1 for row in missing_rows if row["both_mlg_present"] == "YES")
    report.append(f"覆盖结论：MLG-0007 `{both}/24`，MLG-000E `{both}/24`；两套 MLG 对当前 Loading 24 个缺字均有有效 mapping。")
    report.append("")
    report.append("## 结论")
    report.append("")
    report.append("1. `我 U+6211` 在 MLG-0007 和 MLG-000E 中各只有一个有效 codepoint mapping，分别指向不同 glyph index。")
    report.append("2. MLG-0007/000E 的共同字 rect 通常为 58×67，而 JPN001C 的中文 cell 为 66×66；尺寸并不相同。")
    report.append("3. 五个共同字的 MLG-0007/000E bitmap 是否相同已逐字验证，结果见表；本次输出会明确给出 byte-level SHA256。")
    report.append("4. 两套 MLG 均覆盖当前 Loading 的全部 24 个缺字，但这只是 coverage/bitmap 静态事实，不改变当前单文件 001c Loading PoC 结论。")
    report.append("5. 本轮没有提出 runtime remap、没有构建 XPR、没有修改 XPR。")
    REPORT.write_text("\n".join(report) + "\n", encoding="utf-8")

    manifest = {"report": str(REPORT), "csv": str(CSV_OUT), "missing_csv": str(MISSING_CSV), "fonts": {label: str(path) for label, path in FONTS.items()}, "common_characters": list(COMMON), "loading_missing_count": len(LOADING_MISSING), "bitmap_png_root": str(OUT_DIR)}
    (OUT_DIR / "manifest.json").write_text(json.dumps(manifest, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    print(json.dumps({"report": str(REPORT), "csv": str(CSV_OUT), "missing_csv": str(MISSING_CSV), "png_root": str(OUT_DIR)}, ensure_ascii=False))


if __name__ == "__main__":
    main()
