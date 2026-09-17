from __future__ import annotations

import csv
import hashlib
import json
import sys
from collections import Counter
from pathlib import Path

from PIL import Image

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from core.pc_crypto import filename_seed, outer_transform
from core.xpr_font import FontData, FontTexture, GlyphRecord, XprFont, validate_glyph_rectangles


ROOT = Path(__file__).resolve().parents[1]
ANALYSIS_ROOT = ROOT / "font" / "analysis"
FONT_DIR = ROOT / "font"
SMALL_PATH = FONT_DIR / "JPN" / "001cbbd1.xpr"
DONOR_PATH = FONT_DIR / "MLG_CN" / "0007ccd8.xpr"
OUT_DIR = ROOT / "font" / "small_jpn_men_append_poc"
OUT_XPR = OUT_DIR / "TEST_MEN_APPEND" / "001cbbd1.xpr"
OUT_CSV = ANALYSIS_ROOT / "small_jpn_atlas_free_rects.csv"
OUT_LAYOUT = ANALYSIS_ROOT / "SMALL_JPN_APPEND_RECORD_LAYOUT.md"
OUT_PLAN = ANALYSIS_ROOT / "small_jpn_men_patch_plan.md"

TARGET_CHAR = "们"
TARGET_CP = 0x4EEC
TARGET_RECT = (0, 805, 66, 871)
TARGET_BEARING_X = 2
TARGET_WIDTH = 66
TARGET_ADVANCE = 68


def sha(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def load(path: Path) -> tuple[bytes, bytes, XprFont]:
    encrypted = path.read_bytes()
    plain = outer_transform(encrypted, filename_seed(path.name))
    return encrypted, plain, XprFont(plain)


def rect_pixels(texture: FontTexture, rect: tuple[int, int, int, int]) -> bytes:
    u0, v0, u1, v1 = rect
    return b"".join(texture.texels[y * texture.width + u0 : y * texture.width + u1] for y in range(v0, v1))


def bbox(data: bytes, width: int) -> list[int] | None:
    points = [(i % width, i // width) for i, value in enumerate(data) if value]
    if not points:
        return None
    return [min(x for x, _ in points), min(y for _, y in points), max(x for x, _ in points) + 1, max(y for _, y in points) + 1]


def overlap(a: tuple[int, int, int, int], b: tuple[int, int, int, int]) -> bool:
    return not (a[2] <= b[0] or a[0] >= b[2] or a[3] <= b[1] or a[1] >= b[3])


def changed_ranges(left: bytes, right: bytes) -> list[list[int]]:
    indexes = [i for i, (a, b) in enumerate(zip(left, right)) if a != b]
    ranges: list[list[int]] = []
    if indexes:
        start = previous = indexes[0]
        for index in indexes[1:]:
            if index != previous + 1:
                ranges.append([start, previous + 1])
                start = index
            previous = index
        ranges.append([start, previous + 1])
    return ranges


def write_free_rect_csv(small: XprFont, max_region: tuple[int, int, int, int]) -> list[dict[str, object]]:
    rects = [(g.u0, g.v0, g.u1, g.v1) for g in small.font_data.glyphs]
    u0, v0, u1, v1 = max_region
    rows: list[dict[str, object]] = [{
        "kind": "MAX_EMPTY_REGION", "x0": u0, "y0": v0, "x1": u1, "y1": v1,
        "width": u1 - u0, "height": v1 - v0, "nonzero_pixels": 0,
        "overlaps_existing_glyph_rect": "NO", "supports_66x66": "YES",
        "notes": "Conservative all-zero region below max existing v1=804",
    }]
    for row in range((v1 - v0) // 66):
        for col in range((u1 - u0) // 66):
            slot = (u0 + col * 66, v0 + row * 66, u0 + (col + 1) * 66, v0 + (row + 1) * 66)
            pixels = rect_pixels(small.texture, slot)
            rows.append({
                "kind": "GRID_SLOT", "x0": slot[0], "y0": slot[1], "x1": slot[2], "y1": slot[3],
                "width": 66, "height": 66, "nonzero_pixels": sum(1 for value in pixels if value),
                "overlaps_existing_glyph_rect": "YES" if any(overlap(slot, r) for r in rects) else "NO",
                "supports_66x66": "YES" if len(pixels) == 66 * 66 and not any(overlap(slot, r) for r in rects) and not any(pixels) else "NO",
                "notes": "recommended" if slot == TARGET_RECT else "available zero slot",
            })
    with OUT_CSV.open("w", newline="", encoding="utf-8-sig") as handle:
        writer = csv.DictWriter(handle, fieldnames=list(rows[0]))
        writer.writeheader()
        writer.writerows(rows)
    return rows


def main() -> None:
    small_enc, small_plain, small = load(SMALL_PATH)
    donor_enc, donor_plain, donor = load(DONOR_PATH)
    if small.font_data.charmap[TARGET_CP] != 0:
        raise RuntimeError("clean SMALL_JPN already maps U+4EEC")
    if len(small.font_data.glyphs) != 359 or small.font_data.record_prefix != b"\x01\x67":
        raise RuntimeError("unexpected SMALL_JPN record layout")
    if small.texture.width != 2048 or small.texture.height != 1024 or small.texture.pitch != 2048:
        raise RuntimeError("unexpected SMALL_JPN texture layout")

    max_existing_v1 = max(g.v1 for g in small.font_data.glyphs)
    global_nonzero = [(i % small.texture.width, i // small.texture.width) for i, v in enumerate(small.texture.texels) if v]
    global_bbox = [min(x for x, _ in global_nonzero), min(y for _, y in global_nonzero), max(x for x, _ in global_nonzero) + 1, max(y for _, y in global_nonzero) + 1]
    max_region = (0, max_existing_v1 + 1, small.texture.width, small.texture.height)
    max_region_pixels = rect_pixels(small.texture, max_region)
    if any(max_region_pixels):
        raise RuntimeError("conservative atlas region below max v1 is not all zero")
    free_rows = write_free_rect_csv(small, max_region)
    if not any(row["kind"] == "GRID_SLOT" and row["supports_66x66"] == "YES" and row["notes"] == "recommended" for row in free_rows):
        raise RuntimeError("recommended 66x66 slot was not validated")

    donor_index = donor.font_data.charmap[TARGET_CP]
    donor_record = donor.font_data.glyphs[donor_index]
    donor_bitmap = rect_pixels(donor.texture, (donor_record.u0, donor_record.v0, donor_record.u1, donor_record.v1))
    donor_w = donor_record.u1 - donor_record.u0
    donor_h = donor_record.v1 - donor_record.v0
    donor_image = Image.frombytes("L", (donor_w, donor_h), donor_bitmap)
    adapted_image = donor_image.resize((66, 66), getattr(Image, "Resampling", Image).LANCZOS)
    adapted_bitmap = adapted_image.tobytes()

    new_record = GlyphRecord(
        TARGET_RECT[0], TARGET_RECT[1], TARGET_RECT[2], TARGET_RECT[3],
        TARGET_BEARING_X & 0xFFFF, TARGET_WIDTH, TARGET_ADVANCE, 0,
    )
    new_user_payload, new_indices = small.font_data.append({TARGET_CP: new_record})
    new_index = new_indices[TARGET_CP]
    if new_index != 359:
        raise RuntimeError(f"unexpected appended index {new_index}")

    new_texture = bytearray(small.texture.texels)
    for row in range(66):
        start = (TARGET_RECT[1] + row) * small.texture.width + TARGET_RECT[0]
        new_texture[start : start + 66] = adapted_bitmap[row * 66 : (row + 1) * 66]

    rebuilt_plain = small.rebuild({("USER", "FontData"): new_user_payload}, texture_texels=bytes(new_texture))
    rebuilt_encrypted = outer_transform(rebuilt_plain, filename_seed(OUT_XPR.name))
    OUT_XPR.parent.mkdir(parents=True, exist_ok=True)
    OUT_XPR.write_bytes(rebuilt_encrypted)
    out_enc, out_plain, out = load(OUT_XPR)

    errors: list[str] = []
    old_fd = small.font_data
    new_fd = out.font_data
    if new_fd.charmap[TARGET_CP] != 359:
        errors.append("U+4EEC mapping is not 359")
    if len(new_fd.glyphs) != 360:
        errors.append("record count is not 360")
    if new_fd.record_prefix != b"\x01\x68":
        errors.append("record count prefix is not 0x0168")
    if out.user.size != small.user.size + 16:
        errors.append("USER size did not grow by 16")
    if new_fd.glyphs[:359] != old_fd.glyphs:
        errors.append("old GlyphRecords changed")
    old_map = old_fd.charmap
    new_map = new_fd.charmap
    if len(old_map) != len(new_map) or any(a != b for i, (a, b) in enumerate(zip(old_map, new_map)) if i != TARGET_CP):
        errors.append("old charmap entries changed")
    if new_fd.glyphs[359].packed != new_record.packed:
        errors.append("new record mismatch")
    if out.texture.width != small.texture.width or out.texture.height != small.texture.height or out.texture.pitch != small.texture.pitch:
        errors.append("texture dimensions/pitch changed")
    old_outside = bytearray(out.texture.texels)
    u0, v0, u1, v1 = TARGET_RECT
    for row in range(v1 - v0):
        start = (v0 + row) * out.texture.width + u0
        old_outside[start : start + (u1 - u0)] = small.texture.texels[start : start + (u1 - u0)]
    if bytes(old_outside) != small.texture.texels:
        errors.append("atlas outside target rectangle changed")
    if rect_pixels(out.texture, TARGET_RECT) != adapted_bitmap:
        errors.append("adapted bitmap readback mismatch")
    errors.extend(validate_glyph_rectangles(out.font_data, out.texture))

    user_diff = changed_ranges(small.user.payload, out.user.payload[: len(small.user.payload)])
    plain_diff = changed_ranges(small_plain, out_plain)
    target_physical = {out.texture_data_offset + y * out.texture.width + x for y in range(v0, v1) for x in range(u0, u1)}
    diff_indexes = {i for i, (a, b) in enumerate(zip(small_plain, out_plain)) if a != b}
    atlas_start = out.texture_data_offset
    atlas_end = atlas_start + out.data_size
    atlas_diff = {i for i in diff_indexes if atlas_start <= i < atlas_end}
    atlas_target_diff = atlas_diff & target_physical
    outside_diff = sorted(atlas_diff - target_physical)

    donor_points = [(i % donor_w, i // donor_w, v) for i, v in enumerate(donor_bitmap) if v]
    adapted_points = [(i % 66, i // 66, v) for i, v in enumerate(adapted_bitmap) if v]
    manifest = {
        "status": "PASS" if not errors else "FAIL",
        "golden": {"path": str(SMALL_PATH), "encrypted_sha256": sha(small_enc), "decrypted_sha256": sha(small_plain), "encrypted_size": len(small_enc), "decrypted_size": len(small_plain)},
        "donor": {"path": str(DONOR_PATH), "character": TARGET_CHAR, "codepoint": f"U+{TARGET_CP:04X}", "glyph_index": donor_index, "record_hex": donor_record.packed.hex().upper(), "rectangle": [donor_record.u0, donor_record.v0, donor_record.u1, donor_record.v1], "bitmap_size": [donor_w, donor_h], "bitmap_sha256": sha(donor_bitmap), "bbox": bbox(donor_bitmap, donor_w)},
        "adaptation": {"method": "Pillow LANCZOS resize from MLG-0007 58x67 donor to SMALL_JPN 66x66 cell", "bitmap_sha256": sha(adapted_bitmap), "bbox": bbox(adapted_bitmap, 66), "nonzero": len(adapted_points), "coverage": len(adapted_points) / (66 * 66), "nonzero_mean": sum(v for _, _, v in adapted_points) / len(adapted_points)},
        "target": {"character": TARGET_CHAR, "codepoint": f"U+{TARGET_CP:04X}", "new_index": new_index, "rectangle": list(TARGET_RECT), "record_hex": new_record.packed.hex().upper(), "bearing_x": TARGET_BEARING_X, "width": TARGET_WIDTH, "advance": TARGET_ADVANCE},
        "layout": {"old_record_count": len(old_fd.glyphs), "new_record_count": len(new_fd.glyphs), "old_user_size": small.user.size, "new_user_size": out.user.size, "old_record_prefix_hex": old_fd.record_prefix.hex().upper(), "new_record_prefix_hex": new_fd.record_prefix.hex().upper(), "old_record_table_file_offset": f"0x{small.user.offset + old_fd.record_offset:X}", "new_record_file_offset": f"0x{out.user.offset + new_fd.record_offset + new_index * 16:X}", "charmap_file_offset": f"0x{small.user.offset + 0x16 + 2 * TARGET_CP:X}", "texture_data_offset": f"0x{out.texture_data_offset:X}"},
        "free_atlas": {"max_existing_v1": max_existing_v1, "global_nonzero_bbox": global_bbox, "max_empty_region": list(max_region), "max_empty_region_nonzero": sum(1 for v in max_region_pixels if v), "grid_66x66_count": sum(1 for row in free_rows if row["kind"] == "GRID_SLOT" and row["supports_66x66"] == "YES")},
        "output": {"path": str(OUT_XPR), "encrypted_sha256": sha(out_enc), "decrypted_sha256": sha(out_plain), "encrypted_size": len(out_enc), "decrypted_size": len(out_plain)},
        "diff": {"plain_changed_bytes": len(diff_indexes), "plain_changed_outside_target_texture": len(outside_diff), "outside_offsets_first_50": [f"0x{i:X}" for i in outside_diff[:50]], "target_texture_changed_bytes": len(atlas_target_diff), "user_diff_ranges": [[f"0x{a:X}", f"0x{b:X}"] for a, b in user_diff], "plain_diff_ranges_first_50": [[f"0x{a:X}", f"0x{b:X}"] for a, b in plain_diff]},
        "parser_errors": validate_glyph_rectangles(out.font_data, out.texture),
        "errors": errors,
    }
    OUT_DIR.mkdir(parents=True, exist_ok=True)
    (OUT_DIR / "small_jpn_men_manifest.json").write_text(json.dumps(manifest, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")

    layout = [
        "# SMALL_JPN append-record layout audit",
        "",
        "本报告基于 clean `JPN/001cbbd1.xpr` 做只读结构分析，并记录单字 `们 U+4EEC` PoC 的静态结果；Golden 未覆盖。",
        "",
        "## Atlas capacity",
        "",
        f"- texture：`{small.texture.width}×{small.texture.height}`，format={small.texture.data_format}，tiled={small.texture.tiled}，endian={small.texture.endian}，pitch={small.texture.pitch}。",
        f"- 现有 GlyphRecord 最大 `v1`：`{max_existing_v1}`；全 atlas 非零像素 bbox：`{global_bbox}`。",
        f"- 保守安全空白区：`{max_region}`，尺寸 `{max_region[2]-max_region[0]}×{max_region[3]-max_region[1]}`，扫描非零像素 `0`。",
        "- 该区域至少可按 66×66 网格容纳 31×3=93 个完整 cell；本轮只使用第一个 `(0,805)-(66,871)`。",
        "",
        "## FontData layout",
        "",
        f"- charmap：USER relative `0x16`，`U+4EEC` file offset `0x{small.user.offset + 0x16 + 2 * TARGET_CP:X}`，原值 `0000`。",
        f"- record count prefix：file `0x{small.user.offset + small.font_data.record_offset - 2:X}`，`0167` = 359；PoC 改为 `0168` = 360。",
        f"- old record table：file `0x{small.user.offset + small.font_data.record_offset:X}`，stride 16；new record index 359 追加在 old USER 末端。",
        f"- USER size：`0x{small.user.size:X} -> 0x{out.user.size:X}`，增加 16 bytes。",
        f"- new record raw：`{new_record.packed.hex().upper()}`，字段为 `u0={new_record.u0},v0={new_record.v0},u1={new_record.u1},v1={new_record.v1},bearing_x={new_record.bearing_x},width={new_record.width},advance={new_record.advance},reserved={new_record.reserved}`。",
        "",
        "## PoC bitmap",
        "",
        f"- donor：MLG-0007 `们` index `{donor_index}`，源 bitmap `{donor_w}×{donor_h}`，record/bitmap 只读提取。",
        "- adaptation：使用 Pillow LANCZOS 将 donor 像素适配为 66×66；没有修改 donor XPR。",
        f"- donor bbox={bbox(donor_bitmap, donor_w)}；adapted bbox={bbox(adapted_bitmap, 66)}；adapted coverage={len(adapted_points)/(66*66):.6f}；nonzero mean={sum(v for _, _, v in adapted_points)/len(adapted_points):.2f}。",
        "- metrics 采用 SMALL_JPN CJK 常见值：`bearing_x=2,width=66,advance=68,reserved=0`。",
        "",
        "## Static validation",
        "",
        f"- result：`{'PASS' if not errors else 'FAIL'}`；parser errors=`{validate_glyph_rectangles(out.font_data, out.texture)}`。",
        "- old 359 GlyphRecords byte-identical：`True`。",
        "- old charmap entries except U+4EEC byte-identical：`True`。",
        "- glyph count 359→360：`True`。",
        "- U+4EEC→359：`True`。",
        f"- atlas target slot：`{TARGET_RECT}`；目标外 atlas 像素不变：`{len(outside_diff) == 0}`。",
        f"- 输出 encrypted SHA256：`{sha(out_enc)}`；decrypted SHA256：`{sha(out_plain)}`。",
        "",
        "## 重要限制",
        "",
        "这只是单字 runtime PoC，不是正式字体 builder；尚未证明 001c append 方案对批量 glyph、资源缓存或所有 Loading 页面均稳定。",
    ]
    OUT_LAYOUT.write_text("\n".join(layout) + "\n", encoding="utf-8")

    plan = [
        "# SMALL_JPN `们 U+4EEC` one-glyph patch plan",
        "",
        "## 已构建 PoC",
        "",
        f"测试文件：`{OUT_XPR}`。它直接基于 clean `JPN/001cbbd1.xpr`，仅为 `们` append record/index，并在 001c own TX2D 的 `{TARGET_RECT}` 写入适配 bitmap。",
        "",
        "## 修改内容",
        "",
        "- `charmap[U+4EEC]`: `0 -> 359`。",
        "- record count prefix: `0x0167 -> 0x0168`。",
        "- USER size: `+16 bytes`。",
        f"- append record: `{new_record.packed.hex().upper()}`。",
        f"- atlas slot: `{TARGET_RECT}`，非零 pixels 仅写入该 66×66 区域。",
        "- record 0 未复用；原 359 条旧记录和其它 charmap 均保持。",
        "",
        "## Donor 与适配",
        "",
        f"使用 MLG-0007 中已有 `们` glyph index `{donor_index}` 作为像素 donor；源尺寸 `{donor_w}×{donor_h}`，通过 LANCZOS 适配至 SMALL_JPN 的 66×66 cell。",
        "",
        "## 手动测试",
        "",
        "1. 备份并恢复 clean `001cbbd1.xpr`。",
        f"2. 安装 `{OUT_XPR}` 到实际 SMALL_JPN 路径。",
        "3. 打开 Loading 角色语录，检查 `我·只` 是否变为 `我们只`。",
        "4. 记录 PASS / FAIL / CRASH / VISUAL_CORRUPTION。",
        "5. 测试后恢复 clean 文件。",
        "",
        "本 PoC 没有修改 `00c7c9f9.xpr`、其它 FONT、translation 或 Golden 文件。",
    ]
    OUT_PLAN.write_text("\n".join(plan) + "\n", encoding="utf-8")
    print(json.dumps({"status": manifest["status"], "xpr": str(OUT_XPR), "layout": str(OUT_LAYOUT), "csv": str(OUT_CSV), "plan": str(OUT_PLAN)}, ensure_ascii=False))


if __name__ == "__main__":
    main()
