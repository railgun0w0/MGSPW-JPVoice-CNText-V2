from __future__ import annotations

import csv
import hashlib
import json
import sys
from collections import Counter, defaultdict
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))
ANALYSIS_ROOT = ROOT / "font" / "analysis"

from core.pc_crypto import filename_seed, outer_transform
from core.xpr_font import FontData, FontTexture, XprFont


OUT_MD = ANALYSIS_ROOT / "SMALL_JPN_FONT_PAIR_ANALYSIS.md"
OUT_MAP = ANALYSIS_ROOT / "small_jpn_codepoint_glyph_map.csv"
OUT_FREE = ANALYSIS_ROOT / "small_jpn_free_slots.csv"
OUT_PLAN = ANALYSIS_ROOT / "SMALL_JPN_ONE_GLYPH_PATCH_PLAN.md"

FONT_DIR = ROOT / "font"
PATHS = {
    "SMALL_JPN_DATA_001C": FONT_DIR / "JPN" / "001cbbd1.xpr",
    "SMALL_JPN_TEXTURE_00C7": FONT_DIR / "JPN" / "00c7c9f9.xpr",
    "MLG_CN_BIG_0007": FONT_DIR / "MLG_CN" / "0007ccd8.xpr",
    "MLG_CN_SMALL_000E": FONT_DIR / "MLG_CN" / "000ebbe8.xpr",
}

TARGETS = {
    "中": 0x4E2D,
    "们": 0x4EEC,
    "陆": 0x9646,
    "拘": 0x62D8,
    "我": 0x6211,
}


def sha(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def load(path: Path) -> tuple[bytes, bytes, XprFont]:
    encrypted = path.read_bytes()
    plain = outer_transform(encrypted, filename_seed(path.name))
    return encrypted, plain, XprFont(plain)


def rect(glyph) -> tuple[int, int, int, int]:
    return glyph.u0, glyph.v0, glyph.u1, glyph.v1


def extract(tex: FontTexture, glyph) -> bytes:
    u0, v0, u1, v1 = rect(glyph)
    if not (0 <= u0 <= u1 <= tex.width and 0 <= v0 <= v1 <= tex.height):
        return b""
    return b"".join(
        tex.texels[y * tex.width + u0 : y * tex.width + u1]
        for y in range(v0, v1)
    )


def bitmap_stats(tex: FontTexture, glyph) -> dict:
    pixels = extract(tex, glyph)
    w = glyph.u1 - glyph.u0
    h = glyph.v1 - glyph.v0
    nz = [(i % w, i // w, p) for i, p in enumerate(pixels) if p] if w and h else []
    if nz:
        bbox = [min(p[0] for p in nz), min(p[1] for p in nz), max(p[0] for p in nz) + 1, max(p[1] for p in nz) + 1]
        mean = sum(p[2] for p in nz) / len(nz)
    else:
        bbox = None
        mean = 0.0
    return {
        "w": w,
        "h": h,
        "bytes": len(pixels),
        "sha256": sha(pixels),
        "nonzero": len(nz),
        "coverage": (len(nz) / (w * h)) if w and h else 0.0,
        "nonzero_mean": mean,
        "bbox": bbox,
        "in_bounds": len(pixels) == w * h,
    }


def fmt_bbox(value) -> str:
    return "" if value is None else "[" + ",".join(str(v) for v in value) + "]"


def fmt_hex(data: bytes) -> str:
    return data.hex().upper()


def record_dict(glyph, index: int, user_file_offset: int, mapped_codes: list[int]) -> dict:
    return {
        "index": index,
        "file_offset": f"0x{user_file_offset:X}",
        "raw": glyph.packed.hex().upper(),
        "u0": glyph.u0,
        "v0": glyph.v0,
        "u1": glyph.u1,
        "v1": glyph.v1,
        "bearing_x_raw": glyph.bearing_x_raw,
        "bearing_x": glyph.bearing_x,
        "width": glyph.width,
        "advance": glyph.advance,
        "reserved": glyph.reserved,
        "mapped_codepoints": ",".join(f"U+{c:04X}" for c in mapped_codes),
    }


def main() -> None:
    loaded = {label: load(path) for label, path in PATHS.items()}
    small_enc, small_plain, small = loaded["SMALL_JPN_DATA_001C"]
    tex_enc, tex_plain, texture_xpr = loaded["SMALL_JPN_TEXTURE_00C7"]
    mlg7_enc, mlg7_plain, mlg7 = loaded["MLG_CN_BIG_0007"]
    mlg_e_enc, mlg_e_plain, mlg_e = loaded["MLG_CN_SMALL_000E"]

    small_tex = small.texture
    texture_00c7 = texture_xpr.texture
    user_abs = small.user.offset
    aligned_rel = small.font_data.record_offset - len(small.font_data.record_prefix)
    record_prefix_rel = aligned_rel
    record_abs = user_abs + small.font_data.record_offset
    prefix_abs = user_abs + record_prefix_rel
    map_abs = user_abs + 0x16
    map_end_rel = record_prefix_rel

    inverse: dict[int, list[int]] = defaultdict(list)
    for cp, idx in enumerate(small.font_data.charmap):
        if idx:
            inverse[idx].append(cp)
    unmapped_records = [idx for idx in range(len(small.font_data.glyphs)) if idx not in inverse]

    small_record_stats = []
    used_rects = []
    for idx, glyph in enumerate(small.font_data.glyphs):
        own = bitmap_stats(small_tex, glyph)
        paired = bitmap_stats(texture_00c7, glyph)
        mapped = inverse.get(idx, [])
        if glyph.u1 > 0 and glyph.v1 > 0:
            used_rects.append((glyph.u0, glyph.v0, glyph.u1, glyph.v1))
        item = record_dict(glyph, idx, record_abs + idx * 16, mapped)
        item.update({
            "own_nonzero": own["nonzero"],
            "own_bbox": fmt_bbox(own["bbox"]),
            "own_sha256": own["sha256"],
            "paired_nonzero": paired["nonzero"],
            "paired_bbox": fmt_bbox(paired["bbox"]),
            "paired_sha256": paired["sha256"],
            "own_in_bounds": own["in_bounds"],
            "paired_in_bounds": paired["in_bounds"],
            "status": "USED" if mapped else ("UNUSED_NONEMPTY" if own["nonzero"] else "UNUSED_EMPTY"),
        })
        small_record_stats.append(item)

    def lookup(font: XprFont, cp: int):
        idx = font.font_data.charmap[cp] if cp <= font.font_data.last_code else 0
        return idx, font.font_data.glyphs[idx] if idx < len(font.font_data.glyphs) else None

    # Full codepoint map for all mapped SMALL_JPN entries, then explicit rows for requested missing samples.
    map_rows = []
    for cp, idx in enumerate(small.font_data.charmap):
        if not idx:
            continue
        glyph = small.font_data.glyphs[idx]
        own = bitmap_stats(small_tex, glyph)
        paired = bitmap_stats(texture_00c7, glyph)
        map_rows.append({
            "codepoint": f"U+{cp:04X}",
            "decimal": cp,
            "character": chr(cp),
            "present": "YES",
            "glyph_index": idx,
            "record_file_offset": f"0x{record_abs + idx * 16:X}",
            "record_hex": glyph.packed.hex().upper(),
            "bearing_x": glyph.bearing_x,
            "width": glyph.width,
            "advance": glyph.advance,
            "reserved": glyph.reserved,
            "u0": glyph.u0,
            "v0": glyph.v0,
            "u1": glyph.u1,
            "v1": glyph.v1,
            "own_nonzero": own["nonzero"],
            "own_bbox": fmt_bbox(own["bbox"]),
            "paired_00c7_nonzero": paired["nonzero"],
            "paired_00c7_bbox": fmt_bbox(paired["bbox"]),
            "paired_00c7_sha256": paired["sha256"],
        })
    mapped_codepoint_rows = {row["decimal"] for row in map_rows}
    for ch, cp in TARGETS.items():
        if cp in mapped_codepoint_rows:
            continue
        idx, glyph = lookup(small, cp)
        if idx == 0:
            map_rows.append({
                "codepoint": f"U+{cp:04X}", "decimal": cp, "character": ch,
                "present": "NO", "glyph_index": "0 (unmapped)",
                "record_file_offset": f"0x{record_abs:X}",
                "record_hex": small.font_data.glyphs[0].packed.hex().upper(),
                "bearing_x": small.font_data.glyphs[0].bearing_x,
                "width": small.font_data.glyphs[0].width,
                "advance": small.font_data.glyphs[0].advance,
                "reserved": small.font_data.glyphs[0].reserved,
                "u0": small.font_data.glyphs[0].u0, "v0": small.font_data.glyphs[0].v0,
                "u1": small.font_data.glyphs[0].u1, "v1": small.font_data.glyphs[0].v1,
                "own_nonzero": bitmap_stats(small_tex, small.font_data.glyphs[0])["nonzero"],
                "own_bbox": fmt_bbox(bitmap_stats(small_tex, small.font_data.glyphs[0])["bbox"]),
                "paired_00c7_nonzero": bitmap_stats(texture_00c7, small.font_data.glyphs[0])["nonzero"],
                "paired_00c7_bbox": fmt_bbox(bitmap_stats(texture_00c7, small.font_data.glyphs[0])["bbox"]),
                "paired_00c7_sha256": bitmap_stats(texture_00c7, small.font_data.glyphs[0])["sha256"],
            })

    fieldnames = list(map_rows[0].keys())
    with OUT_MAP.open("w", newline="", encoding="utf-8-sig") as handle:
        writer = csv.DictWriter(handle, fieldnames=fieldnames)
        writer.writeheader()
        writer.writerows(map_rows)

    free_fields = [
        "record_index", "status", "mapped_codepoints", "record_file_offset", "record_hex",
        "u0", "v0", "u1", "v1", "bearing_x", "width", "advance", "reserved",
        "own_nonzero", "own_bbox", "paired_00c7_nonzero", "paired_00c7_bbox",
        "own_sha256", "paired_00c7_sha256",
    ]
    with OUT_FREE.open("w", newline="", encoding="utf-8-sig") as handle:
        writer = csv.DictWriter(handle, fieldnames=free_fields)
        writer.writeheader()
        for item in small_record_stats:
            writer.writerow({"record_index": item["index"], **{key: item.get(key, "") for key in free_fields[1:]}})

    def xpr_summary(label, enc, plain, font):
        return {
            "label": label,
            "path": str(PATHS[label]),
            "encrypted_size": len(enc),
            "encrypted_sha256": sha(enc),
            "decrypted_size": len(plain),
            "decrypted_sha256": sha(plain),
            "header_size": font.header_size,
            "data_size": font.data_size,
            "resource_count": font.resource_count,
            "texture_data_offset": font.texture_data_offset,
            "user_offset": font.user.offset,
            "user_size": font.user.size,
            "tx2d_offset": font.tx2d.offset,
            "tx2d_size": font.tx2d.size,
            "last_code": font.font_data.last_code,
            "mapped_count": sum(1 for v in font.font_data.charmap if v),
            "record_count": len(font.font_data.glyphs),
            "record_offset_rel": font.font_data.record_offset,
            "record_prefix_hex": font.font_data.record_prefix.hex().upper(),
            "texture": {
                "width": font.texture.width, "height": font.texture.height,
                "pitch": font.texture.pitch, "format": font.texture.data_format,
                "tiled": font.texture.tiled, "endian": font.texture.endian,
            },
        }

    target_lines = []
    for ch, cp in TARGETS.items():
        s_idx, s_g = lookup(small, cp)
        c_idx, c_g = lookup(texture_xpr, cp)
        if s_g is not None:
            own = bitmap_stats(small_tex, s_g)
            paired = bitmap_stats(texture_00c7, s_g)
            s_detail = f"{s_idx}; rect={rect(s_g)}; own_nz={own['nonzero']}; 00c7_nz={paired['nonzero']}"
        else:
            s_detail = "0 (unmapped; record 0 is not a positive charmap mapping)"
        c_detail = f"{c_idx}; rect={rect(c_g)}" if c_g is not None else "0 (unmapped)"
        target_lines.append(f"- `{ch} U+{cp:04X}`: 001c `{s_detail}`; 00c7 own FontData lookup `{c_detail}`")

    donor_lines = []
    for label, font in [("MLG-0007", mlg7), ("MLG-000E", mlg_e)]:
        idx, glyph = lookup(font, TARGETS["们"])
        st = bitmap_stats(font.texture, glyph)
        donor_lines.append(
            f"- {label}: `们` -> index {idx}, record={glyph.packed.hex().upper()}, "
            f"rect={rect(glyph)}, bitmap={st['w']}x{st['h']}, bbox={fmt_bbox(st['bbox'])}, "
            f"coverage={st['coverage']:.4f}, mean={st['nonzero_mean']:.2f}"
        )

    # Compute the union of all SMALL_JPN record rectangles as an atlas occupancy summary.
    min_u = min((r[0] for r in used_rects), default=0)
    min_v = min((r[1] for r in used_rects), default=0)
    max_u = max((r[2] for r in used_rects), default=0)
    max_v = max((r[3] for r in used_rects), default=0)
    rect_area = sum(max(0, r[2] - r[0]) * max(0, r[3] - r[1]) for r in used_rects)
    overlap_area = 0
    for i, a in enumerate(used_rects):
        for b in used_rects[i + 1 :]:
            overlap_area += max(0, min(a[2], b[2]) - max(a[0], b[0])) * max(0, min(a[3], b[3]) - max(a[1], b[1]))

    paired_exact_same = 0
    paired_same_nonzero = 0
    for item, glyph in zip(small_record_stats, small.font_data.glyphs):
        own_pixels = extract(small_tex, glyph)
        paired_pixels = extract(texture_00c7, glyph)
        if own_pixels == paired_pixels:
            paired_exact_same += 1
        if sum(1 for value in own_pixels if value) == sum(1 for value in paired_pixels if value):
            paired_same_nonzero += 1
    small_rect_sizes = Counter((g.u1 - g.u0, g.v1 - g.v0) for g in small.font_data.glyphs)
    texture_rect_sizes = Counter((g.u1 - g.u0, g.v1 - g.v0) for g in texture_xpr.font_data.glyphs)

    summaries = {
        label: xpr_summary(label, *loaded[label])
        for label in loaded
    }
    report = []
    report.append("# SMALL_JPN FontData / FontTexture 配对分析\n")
    report.append("本报告为只读分析；本轮没有修改或重建任何 XPR。\n")
    report.append("## 结论摘要\n")
    report.append(f"- `001cbbd1.xpr` 的 `USER/FontData`：{len(small.font_data.glyphs)} 条 record，{sum(1 for v in small.font_data.charmap if v)} 个 mapped codepoint。")
    report.append(f"- `00c7c9f9.xpr` 的 `TX2D/FontTexture`：{texture_00c7.width}×{texture_00c7.height}，format={texture_00c7.data_format}，pitch={texture_00c7.pitch}。")
    report.append(f"- `001c` 自带的 TX2D 是 `{small_tex.width}×{small_tex.height}`；因此这里明确区分“001c 自带纹理”和用户指定的 `00c7` 纹理，不能把二者静默视为同一张 atlas。")
    report.append(f"- 001c 记录 UV 对 001c 自带纹理越界：`{sum(not x['own_in_bounds'] for x in small_record_stats)}`；对 00c7 纹理越界：`{sum(not x['paired_in_bounds'] for x in small_record_stats)}`。")
    report.append(f"- 未被 001c charmap 正向引用的 record：`{', '.join(map(str, unmapped_records)) or '无'}`。这些 record 是否可复用必须结合像素和 runtime 验证，不能仅凭未映射判定为空槽。")
    report.append("")

    report.append("## 文件与资源布局\n")
    report.append("| XPR | encrypted SHA256 | decrypted SHA256 | header/data | USER | TX2D | FontData | texture |\n|---|---|---|---|---|---|---|---|")
    for label, s in summaries.items():
        t = s["texture"]
        report.append(
            f"| {label} | `{s['encrypted_sha256']}` | `{s['decrypted_sha256']}` | `0x{s['header_size']:X}/0x{s['data_size']:X}` | "
            f"`0x{s['user_offset']:X}+0x{s['user_size']:X}` | `0x{s['tx2d_offset']:X}+0x{s['tx2d_size']:X}` | "
            f"records={s['record_count']}, mapped={s['mapped_count']}, record_rel=`0x{s['record_offset_rel']:X}`, prefix=`{s['record_prefix_hex'] or 'none'}` | "
            f"{t['width']}×{t['height']}, pitch={t['pitch']}, fmt={t['format']}, tiled={t['tiled']}, endian={t['endian']} |")
    report.append("")

    report.append("### 001c FontData 内部布局\n")
    report.append(f"- USER payload 起点：file `0x{user_abs:X}`，大小 `0x{small.user.size:X}`。")
    report.append(f"- 固定头：relative `0x0000..0x{0x16-1:X}`；`last_code` 位于 relative `0x14`，值 `U+{small.font_data.last_code:04X}`。")
    report.append(f"- dense charmap：relative `0x16..0x{map_end_rel-1:X}`，file `0x{map_abs:X}..0x{user_abs+map_end_rel-1:X}`，每项 big-endian u16。")
    report.append(f"- 记录计数字段：relative `0x{record_prefix_rel:X}` / file `0x{prefix_abs:X}`，raw `{small.font_data.record_prefix.hex().upper()}` = `{len(small.font_data.glyphs)}`。")
    report.append(f"- GlyphRecord table：relative `0x{small.font_data.record_offset:X}` / file `0x{record_abs:X}`，stride 16 bytes，结束于 relative `0x{small.font_data.record_offset + len(small.font_data.glyphs)*16:X}`；无 suffix `{len(small.font_data.suffix)}` bytes。")
    report.append("- record 字段按现有 parser 为 `u0,v0,u1,v1,bearing_x_raw,width,advance,reserved`，均 big-endian u16；没有在记录后发现额外 sentinel/trailer。")
    report.append("")

    report.append("## 001c record / 00c7 atlas 关系\n")
    report.append("001c 的 FontData 记录本身只保存 UV 和 metrics；把这些 UV 应用到 00c7 的 TX2D 后，所有记录都仍在 00c7 4096×4096 范围内。这里的“对应”是按同一条 GlyphRecord 的 UV 读取 00c7 纹理，不是把 00c7 自己的 2309 条 FontData 记录与 001c 逐条配对。\n")
    report.append(f"- 001c 记录矩形联合包围盒：`({min_u},{min_v})-({max_u},{max_v})`。矩形面积和={rect_area}，矩形间重叠面积（简单两两计数）={overlap_area}。")
    report.append(f"- 001c 自带纹理与 00c7 在这 359 个相同 UV 矩形上的像素块完全相同数：`{paired_exact_same}/359`；非零像素数量相同数：`{paired_same_nonzero}/359`。因此静态上不能把 00c7 视为 001c 自带 atlas 的 byte-identical 替代。")
    report.append("- 这不否定用户已确认的 runtime selector 事实；它说明 XPR 文件本身没有记录跨文件绑定键，且 `001c FontData + 00c7 FontTexture` 的真实配对只能由 runtime/selector 证据确认，不能从 UV 数值单独推出。")
    report.append(f"- 00c7 atlas 总像素：{texture_00c7.width*texture_00c7.height}；按 001c records 计算的剩余物理区域非常大，不能据此断言 runtime 可安全追加，仍需确认 slot/record 容量。")
    report.append(f"- 001c 自带 TX2D：{small_tex.width}×{small_tex.height}；00c7 TX2D：{texture_00c7.width}×{texture_00c7.height}。两者都是 format=2、linear、8-bit texel，但尺寸不同。")
    report.append(f"- 001c record 矩形尺寸分布（前 8 项）：`{small_rect_sizes.most_common(8)}`；其中 `{small_rect_sizes.get((66,66),0)}` 条是完整 66×66 CJK-like cell，其余是窄字/ASCII 等不同 width。")
    report.append(f"- 00c7 自己的 FontData 有 `{len(texture_xpr.font_data.glyphs)}` 条 record、`{sum(1 for v in texture_xpr.font_data.charmap if v)}` 个正向 mapped codepoint；其自身 record 矩形尺寸分布前 8 项：`{texture_rect_sizes.most_common(8)}`。这组 2309 records 不能直接替代 001c 的 359-index 表。")
    report.append("")

    report.append("## 实际字符验证\n")
    report.extend(target_lines)
    report.append("")
    report.append("对 `们/陆/拘`，001c 的 dense charmap 值均为 0，因此它们不是 SMALL_JPN 的有效正向映射；即使 00c7 自身 FontData 可能含有某个字符，也不会由 001c charmap 选中。")
    report.append("")
    report.append("### 001c 中一个正常中文 `中` 的完整 record\n")
    idx, glyph = lookup(small, TARGETS["中"])
    report.append(f"`中 U+4E2D` -> glyph index `{idx}` -> record file offset `0x{record_abs + idx*16:X}` -> raw `{glyph.packed.hex().upper()}` -> rect `{rect(glyph)}`, width={glyph.width}, bearing_x={glyph.bearing_x}, advance={glyph.advance}。")
    report.append("")

    report.append("## 未使用 record / 空槽\n")
    for item in small_record_stats:
        if item["status"] != "USED":
            report.append(
                f"- record `{item['index']}`: `{item['status']}`, mapped=`{item['mapped_codepoints'] or 'none'}`, "
                f"rect=({item['u0']},{item['v0']})-({item['u1']},{item['v1']}), "
                f"001c nonzero={item['own_nonzero']}, 00c7-at-same-UV nonzero={item['paired_nonzero']}, raw=`{item['raw']}`。"
            )
    if not unmapped_records:
        report.append("- 没有未映射 record。")
    else:
        report.append("- 结论：没有 `UNUSED_EMPTY` record。唯一未被正向 charmap 映射的 record 0 有非零像素，且其矩形是 fallback/missing-glyph 候选；不能作为 `们` 的安全空 glyph slot。")
    report.append("")

    report.append("## MLG_CN donor 兼容性\n")
    report.append("MLG 两套字体的 `们` 都已存在；以下是其 record/bitmap 事实，不代表本轮执行 donor 写入。")
    report.extend(donor_lines)
    report.append("")
    report.append("- 三套资源的 FontTexture 都是 format=2、tiled=0、endian=0 的 8-bit 线性灰度存储；因此像素编码层面可转换。")
    report.append("- MLG 的字面通常使用更大的 atlas cell/metrics，而 001c 是 SMALL_JPN；不能直接把 MLG 的 16-byte record 原样复制到 001c。至少要把 bitmap 重采样/栅格化到 SMALL_JPN 可用的槽尺寸，并重新设置 UV、width、bearing_x、advance。")
    report.append("- 若 001c 确有安全的未映射空 record，可保持 glyph count 不变，只改 charmap、该 record 和一个未占用纹理矩形；若未映射 record 是 fallback/missing glyph，则不能复用。")
    report.append("")

    report.append("## 当前 one-glyph patch 结论\n")
    report.append("- 没有可确认安全的空 glyph record：record 0 虽未被正向 charmap 使用，但有实际 fallback 像素，禁止复用。")
    report.append("- 因此最小可行方案不是覆盖现有 record，而是 append 一个新 16-byte record，并同步更新 001c 的 2-byte glyph count、USER size、charmap；本轮不自动扩容，也不修改 XPR。")
    report.append("- 不能仅修改 001c charmap 指向 00c7 自己的 `们` record：001c 与 00c7 的 GlyphRecord 表属于不同 FontData，index/UV/metrics 不共享。")
    report.append("")
    report.append("## 明确未知 / 需要 runtime 验证\n")
    report.append("- 001c FontData + 00c7 FontTexture 的跨 XPR 绑定键/selector 在静态 XPR 中没有被 parser 单独编码；本报告按用户已确认的 runtime 配对，用 001c records 的 UV读取 00c7 atlas 做一致性分析。")
    report.append("- 未映射 record 0 是否是 runtime fallback、以及未占用纹理矩形是否会被其它内部引用，静态结构不能完全证明；复用前必须做最小 one-glyph runtime PoC。")
    report.append("- MLG donor 的字形风格可以作为像素来源，但 SMALL_JPN 的最终字号、baseline 和 metrics 需要以 001c 现有中文 records 为准。")
    OUT_MD.write_text("\n".join(report) + "\n", encoding="utf-8")

    plan = [
        "# SMALL_JPN 单字 `们 U+4EEC` patch plan\n",
        "本文件只描述静态最小方案；本轮没有修改 XPR。\n",
        "## 目标\n",
        "`001cbbd1.xpr` 的 `charmap[U+4EEC]` 从 0 变为一个确认安全的 SMALL_JPN glyph index，使 Loading 文本中的 `我·只` 变为 `我们只`。FontTexture 使用用户确认的 `00c7c9f9.xpr`。\n",
        "## 结构事实\n",
        f"- dense charmap 起点：001c USER file `0x{map_abs:X}`；`U+4EEC` 当前 raw u16 为 `0x{small.font_data.charmap[TARGETS['们']]:04X}`。",
        f"- record count mirror：001c USER file `0x{prefix_abs:X}`，当前 `{len(small.font_data.glyphs)}`。",
        f"- record table：001c USER file `0x{record_abs:X}`，stride 16。",
        f"- 001c own texture：{small_tex.width}×{small_tex.height}；00c7 texture：{texture_00c7.width}×{texture_00c7.height}；二者均 format=2 linear 8-bit。",
        "## 空槽结论\n",
        "`small_jpn_free_slots.csv` 中没有 `UNUSED_EMPTY` record。唯一未被正向 charmap 映射的 record 0 有非零 fallback/missing-glyph 候选像素，不能复用。",
        "因此不能在保持 record count 不变的前提下安全修复 `们`；00c7 atlas 的空白像素区域也不能替代缺失的 FontData record。",
        "## 如果不存在安全空 record\n",
        "不能把 record 0 或任何 `UNUSED_NONEMPTY` fallback 候选直接复用。下一步只能设计 append：新增 16-byte record，001c count `0x0167 -> 0x0168`，USER size 增加 16 bytes，并增加 `U+4EEC -> new_index`；本轮不执行。",
        "## donor 处理\n",
        "MLG-0007/000e 的 `们` 可作为字形参考，但不能直接复制其 GlyphRecord。应先按 SMALL_JPN 现有 `中/我` 的 bbox、baseline、advance 将 donor bitmap 缩放或重新栅格化，再填入 SMALL_JPN atlas。",
        "## 禁止事项\n",
        "不修改 Golden XPR；不整体替换 FontData/FontTexture；不修改 00c7 自己的 FontData；不批量补字。",
    ]
    OUT_PLAN.write_text("\n".join(plan) + "\n", encoding="utf-8")

    manifest = {
        "outputs": [str(OUT_MD), str(OUT_MAP), str(OUT_FREE), str(OUT_PLAN)],
        "unmapped_records": unmapped_records,
        "summaries": summaries,
        "targets": {ch: {"codepoint": f"U+{cp:04X}", "small_jpn_index": lookup(small, cp)[0]} for ch, cp in TARGETS.items()},
    }
    (ANALYSIS_ROOT / "small_jpn_pair_analysis_manifest.json").write_text(json.dumps(manifest, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    print(json.dumps({"reports": [str(OUT_MD), str(OUT_MAP), str(OUT_FREE), str(OUT_PLAN)], "unmapped_records": unmapped_records, "small_records": len(small.font_data.glyphs), "small_mapped": sum(1 for v in small.font_data.charmap if v)}, ensure_ascii=False))


if __name__ == "__main__":
    main()
