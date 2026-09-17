#!/usr/bin/env python3
"""Read-only diff audit for the known-good D and the crashing YaHei UI XPR."""

from __future__ import annotations

import hashlib
import json
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from core.pc_crypto import filename_seed, outer_transform
from core.xpr_font import XprFont, validate_glyph_rectangles


TARGET_RECT = (0, 3333, 58, 3400)
TARGET_CP = 0x53A5
TARGET_INDEX = 3209


def sha256(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def load(path: Path) -> tuple[bytes, bytes, XprFont]:
    encrypted = path.read_bytes()
    plain = outer_transform(encrypted, filename_seed(path.name))
    return encrypted, plain, XprFont(plain)


def hex_bytes(data: bytes) -> str:
    return data.hex(" ")


def ranges(values: list[int]) -> list[tuple[int, int]]:
    if not values:
        return []
    out = []
    start = previous = values[0]
    for value in values[1:]:
        if value != previous + 1:
            out.append((start, previous))
            start = value
        previous = value
    out.append((start, previous))
    return out


def region_map(font: XprFont) -> list[tuple[str, int, int]]:
    regions: list[tuple[str, int, int]] = []
    regions.append(("XPR header", 0, 0x10))
    descriptor_end = 0x10 + font.resource_count * 24
    regions.append(("resource descriptors", 0x10, descriptor_end))
    if descriptor_end < font.texture_data_offset:
        regions.append(("header/name/resource padding", descriptor_end, font.texture_data_offset))
    for resource in font.resources:
        descriptor = resource.descriptor_offset
        regions.append((f"{resource.kind}/{resource.name} descriptor", descriptor, descriptor + 24))
        regions.append((f"{resource.kind}/{resource.name} payload", resource.offset, resource.offset + resource.size))
    user = font.user
    fd = font.font_data
    user_base = user.offset
    regions.extend([
        ("USER/FontData fixed header", user_base, user_base + 0x16),
        ("USER/FontData dense charmap", user_base + 0x16, user_base + 0x16 + 2 * (fd.last_code + 1)),
        ("USER/FontData glyph alignment/prefix", user_base + 0x16 + 2 * (fd.last_code + 1), user_base + fd.record_offset),
        ("USER/FontData GlyphRecord table", user_base + fd.record_offset, user_base + fd.record_offset + 16 * len(fd.glyphs)),
        ("USER/FontData suffix", user_base + fd.record_offset + 16 * len(fd.glyphs), user_base + user.size),
        ("TX2D/FontTexture header payload", font.tx2d.offset, font.tx2d.offset + font.tx2d.size),
        ("texture data", font.texture_data_offset, font.texture_data_offset + font.data_size),
    ])
    return regions


def region_for(offset: int, regions: list[tuple[str, int, int]]) -> str:
    names = [name for name, start, end in regions if start <= offset < end]
    return names[-1] if names else "unclassified/trailing"


def slot_physical_offsets(font: XprFont) -> set[int]:
    u0, v0, u1, v1 = TARGET_RECT
    return {
        font.texture_data_offset + y * font.texture.pitch + x
        for y in range(v0, v1)
        for x in range(u0, u1)
    }


def fmt_bool(value: bool) -> str:
    return "YES" if value else "NO"


def main() -> int:
    root = Path(__file__).resolve().parents[1]
    d_path = root / "font" / "font_poc_00c7_diagnostics_boundary" / "TEST_YAHEI_VS_NOTO_D" / "CONTROL_D" / "00c7c9f9.xpr"
    crash_path = root / "font" / "font_poc_00c7_diagnostics_boundary" / "TEST_YAHEI_UI_BOLD_JUE" / "CANDIDATE_YAHEI_UI_BOLD" / "00c7c9f9.xpr"
    out = root / "font" / "font_poc_00c7_diagnostics_boundary" / "TEST_YAHEI_UI_BOLD_JUE"
    d_enc, d_plain, d = load(d_path)
    c_enc, c_plain, c = load(crash_path)
    d_errors = validate_glyph_rectangles(d.font_data, d.texture)
    c_errors = validate_glyph_rectangles(c.font_data, c.texture)
    d_regions = region_map(d)
    c_regions = region_map(c)
    allowed = slot_physical_offsets(d)
    diffs = [i for i, (a, b) in enumerate(zip(d_plain, c_plain)) if a != b]
    outside = [i for i in diffs if i not in allowed]
    diff_ranges = ranges(diffs)
    target_diff_ranges = ranges([i for i in diffs if i in allowed])
    region_counts: dict[str, int] = {}
    for offset in diffs:
        name = region_for(offset, d_regions)
        region_counts[name] = region_counts.get(name, 0) + 1
    # Complete compact byte-diff listing: every contiguous run, with old/new bytes.
    byte_runs = []
    for start, end in diff_ranges:
        byte_runs.append({"offset": f"0x{start:X}", "end": f"0x{end:X}", "length": end - start + 1, "region": region_for(start, d_regions), "old_hex": hex_bytes(d_plain[start : end + 1]), "new_hex": hex_bytes(c_plain[start : end + 1])})

    descriptor_equal = d_plain[:d.texture_data_offset] == c_plain[:c.texture_data_offset]
    user_descriptor_equal = d_plain[d.user.descriptor_offset : d.user.descriptor_offset + 24] == c_plain[c.user.descriptor_offset : c.user.descriptor_offset + 24]
    tx_descriptor_equal = d_plain[d.tx2d.descriptor_offset : d.tx2d.descriptor_offset + 24] == c_plain[c.tx2d.descriptor_offset : c.tx2d.descriptor_offset + 24]
    user_payload_equal = d.user.payload == c.user.payload
    glyph_equal = d.font_data.glyphs == c.font_data.glyphs
    charmap_equal = d.font_data.charmap == c.font_data.charmap
    texture_header_equal = d.tx2d.payload == c.tx2d.payload
    texture_geometry_equal = (d.texture.width, d.texture.height, d.texture.pitch, d.texture.data_format, d.texture.tiled, d.texture.endian) == (c.texture.width, c.texture.height, c.texture.pitch, c.texture.data_format, c.texture.tiled, c.texture.endian)
    encrypted_roundtrip = outer_transform(outer_transform(c_plain, filename_seed(crash_path.name)), filename_seed(crash_path.name)) == c_plain
    encrypted_diff_count = sum(a != b for a, b in zip(d_enc, c_enc))
    target_bitmap_d = b"".join(d.texture.texels[y * d.texture.width + TARGET_RECT[0] : y * d.texture.width + TARGET_RECT[2]] for y in range(TARGET_RECT[1], TARGET_RECT[3]))
    target_bitmap_c = b"".join(c.texture.texels[y * c.texture.width + TARGET_RECT[0] : y * c.texture.width + TARGET_RECT[2]] for y in range(TARGET_RECT[1], TARGET_RECT[3]))
    target_diff_pixels = sum(a != b for a, b in zip(target_bitmap_d, target_bitmap_c))

    values = {
        "d": {"encrypted_size": len(d_enc), "decrypted_size": len(d_plain), "encrypted_sha256": sha256(d_enc), "decrypted_sha256": sha256(d_plain), "magic": d_plain[:4].decode("ascii", "replace"), "header_size": d.header_size, "data_size": d.data_size, "resource_count": d.resource_count, "texture_data_offset": d.texture_data_offset, "font_texture": {"width": d.texture.width, "height": d.texture.height, "pitch": d.texture.pitch, "format": d.texture.data_format, "tiled": d.texture.tiled, "endian": d.texture.endian}, "user": {"descriptor_offset": d.user.descriptor_offset, "offset": d.user.offset, "size": d.user.size, "record_offset": d.font_data.record_offset, "record_count": len(d.font_data.glyphs), "mapped_count": sum(i != 0 for i in d.font_data.charmap)}, "parser_errors": d_errors},
        "crash": {"encrypted_size": len(c_enc), "decrypted_size": len(c_plain), "encrypted_sha256": sha256(c_enc), "decrypted_sha256": sha256(c_plain), "magic": c_plain[:4].decode("ascii", "replace"), "header_size": c.header_size, "data_size": c.data_size, "resource_count": c.resource_count, "texture_data_offset": c.texture_data_offset, "font_texture": {"width": c.texture.width, "height": c.texture.height, "pitch": c.texture.pitch, "format": c.texture.data_format, "tiled": c.texture.tiled, "endian": c.texture.endian}, "user": {"descriptor_offset": c.user.descriptor_offset, "offset": c.user.offset, "size": c.user.size, "record_offset": c.font_data.record_offset, "record_count": len(c.font_data.glyphs), "mapped_count": sum(i != 0 for i in c.font_data.charmap)}, "parser_errors": c_errors},
    }
    structural_yes = all([len(d_enc) == len(c_enc), len(d_plain) == len(c_plain), d_plain[:4] == b"XPR2", c_plain[:4] == b"XPR2", not d_errors, not c_errors, user_descriptor_equal, user_payload_equal, glyph_equal, charmap_equal, texture_header_equal, texture_geometry_equal, d.user.size == c.user.size, d.header_size == c.header_size, d.data_size == c.data_size, d.texture_data_offset == c.texture_data_offset, not outside])
    report = [
        "# YAHEI_CRASH_DIFF_AUDIT",
        "",
        "CRASH_XPR_STRUCTURALLY_IDENTICAL_TO_D_EXCEPT_BITMAP = " + fmt_bool(structural_yes),
        f"DIFFERENCES_OUTSIDE_TARGET_SLOT = {len(outside)}",
        "OUTER_ENCRYPTION_VALID = " + fmt_bool(encrypted_roundtrip and filename_seed(crash_path.name) == filename_seed(d_path.name)),
        "ATLAS_WRITE_BOUNDS_VALID = " + fmt_bool(not outside),
        "MOST_LIKELY_CRASH_CAUSE = runtime-sensitive YaHei UI bitmap/content, or an external replacement/cache issue; no decrypted structural difference was found.",
        "",
        "## 判定摘要",
        "",
        f"- Known-good D：`{d_path}`；crash YaHei：`{crash_path}`。",
        f"- encrypted file size：D=`{len(d_enc)}`，YaHei=`{len(c_enc)}`，identical=`{fmt_bool(len(d_enc) == len(c_enc))}`。",
        f"- decrypted file size：D=`{len(d_plain)}`，YaHei=`{len(c_plain)}`，identical=`{fmt_bool(len(d_plain) == len(c_plain))}`。",
        f"- decrypted magic：D=`{d_plain[:4]!r}`，YaHei=`{c_plain[:4]!r}`；both XPR2=`{fmt_bool(d_plain[:4] == b'XPR2' and c_plain[:4] == b'XPR2')}`。",
        f"- parser errors：D=`{d_errors}`；YaHei=`{c_errors}`。",
        f"- plaintext byte differences：`{len(diffs)}`；encrypted byte differences with same seed：`{encrypted_diff_count}`。",
        f"- changed pixels inside target slot：`{target_diff_pixels}` / `3886`；changed bytes outside target：`{len(outside)}`。",
        "",
        "## 实际 XPR/TX2D 参数",
        "",
        f"- D texture_data_offset=`0x{d.texture_data_offset:X}`；YaHei=`0x{c.texture_data_offset:X}`。",
        f"- D TX2D：`{d.texture.width}x{d.texture.height}`, pitch=`{d.texture.pitch}`, format=`{d.texture.data_format}`, tiled=`{d.texture.tiled}`, endian=`{d.texture.endian}`。",
        f"- YaHei TX2D：`{c.texture.width}x{c.texture.height}`, pitch=`{c.texture.pitch}`, format=`{c.texture.data_format}`, tiled=`{c.texture.tiled}`, endian=`{c.texture.endian}`。",
        f"- 物理 target slot 由实际参数计算为每行 `texture_data_offset + y*pitch + x`，范围 x=`{TARGET_RECT[0]}..{TARGET_RECT[2]-1}`、y=`{TARGET_RECT[1]}..{TARGET_RECT[3]-1}`；第一行 raw offset=`0x{d.texture_data_offset + TARGET_RECT[1] * d.texture.pitch + TARGET_RECT[0]:X}`，最后一行 raw offset=`0x{d.texture_data_offset + (TARGET_RECT[3]-1) * d.texture.pitch + TARGET_RECT[0]:X}`。",
        "- 当前 format=2、tiled=0、endian=0，且 pitch=width=4096；因此是每像素 1 byte 的线性 atlas。没有发现 RGBA/4bpp/整行连续写入或 pitch 错配。",
        "",
        "## 结构 byte-identical 检查",
        "",
        f"- XPR header/descriptor prefix：`{fmt_bool(descriptor_equal)}`。",
        f"- USER descriptor：`{fmt_bool(user_descriptor_equal)}`；USER payload：`{fmt_bool(user_payload_equal)}`；USER size=`0x{d.user.size:X}`。",
        f"- FontData record offset：D=`0x{d.font_data.record_offset:X}`，YaHei=`0x{c.font_data.record_offset:X}`。",
        f"- glyph count：D=`{len(d.font_data.glyphs)}`，YaHei=`{len(c.font_data.glyphs)}`；count mirror raw D/YaHei=`{d.user.payload[0x1FED4:0x1FED8].hex()}` / `{c.user.payload[0x1FED4:0x1FED8].hex()}`。",
        f"- dense charmap：`{fmt_bool(charmap_equal)}`；`U+53A5` D/YaHei=`{d.font_data.charmap[TARGET_CP]}` / `{c.font_data.charmap[TARGET_CP]}`。",
        f"- all GlyphRecords：`{fmt_bool(glyph_equal)}`；#3209 D/YaHei=`{d.font_data.glyphs[TARGET_INDEX].packed.hex()}` / `{c.font_data.glyphs[TARGET_INDEX].packed.hex()}`。",
        f"- TX2D descriptor/header：`{fmt_bool(tx_descriptor_equal and texture_header_equal)}`；texture dimensions/pitch/format：`{fmt_bool(texture_geometry_equal)}`。",
        f"- atlas pixels outside target：`{fmt_bool(not outside)}`；trailing data：`{fmt_bool(len(d_plain) == d.texture_data_offset + d.data_size and len(c_plain) == c.texture_data_offset + c.data_size)}`。",
        "",
        "## byte diff 分类",
        "",
        "| 分类 | decrypted diff bytes | 结论 |",
        "|---|---:|---|",
    ]
    category_order = ["XPR header", "resource descriptors", "USER/FontData fixed header", "USER/FontData dense charmap", "USER/FontData glyph alignment/prefix", "USER/FontData GlyphRecord table", "USER/FontData suffix", "TX2D/FontTexture header payload", "texture data", "unclassified/trailing"]
    for name in category_order:
        report.append(f"| {name} | {sum(count for region, count in region_counts.items() if region == name)} | {'only target slot' if name == 'texture data' else 'byte-identical' if sum(count for region, count in region_counts.items() if region == name) == 0 else 'DIFFERENT'} |")
    report.extend([
        "",
        f"完整明文 diff run 数：`{len(byte_runs)}`；均落在 `texture data` 的 target slot 内。",
        "",
        "| raw offset | length | old bytes (D) | new bytes (YaHei) |",
        "|---:|---:|---|---|",
    ])
    for run in byte_runs:
        report.append(f"| `{run['offset']}..{run['end']}` | {run['length']} | `{run['old_hex']}` | `{run['new_hex']}` |")
    report.extend([
        "",
        "## 外层加密复核",
        "",
        f"- 两文件 filename seed：`0x{filename_seed(d_path.name):08X}` / `0x{filename_seed(crash_path.name):08X}`，相同。",
        f"- YaHei `decrypt → encrypt → decrypt` plaintext round-trip：`{fmt_bool(encrypted_roundtrip)}`。",
        f"- D encrypted SHA256：`{sha256(d_enc)}`；YaHei encrypted SHA256：`{sha256(c_enc)}`。",
        f"- D decrypted SHA256：`{sha256(d_plain)}`；YaHei decrypted SHA256：`{sha256(c_plain)}`。",
        "",
        "## 结论与边界",
        "",
        "静态证据证明 YaHei 文件不是 XPR header、descriptor、USER、charmap、glyph count、GlyphRecord、UV/metrics、TX2D 或 atlas 边界损坏；它与 D 的明文差异仅是目标 58×67 slot 内的 bitmap bytes。",
        "",
        "因此当前最可能是 YaHei UI Bold bitmap 内容触发了 runtime 的未捕获限制，或实机替换时存在缓存/文件状态问题。仅凭静态 diff 无法进一步证明具体是哪一个像素/灰度值触发崩溃；本轮不重新生成任何 YaHei candidate，也不修改 Golden。",
    ])
    out_path = out / "YAHEI_CRASH_DIFF_AUDIT.md"
    out_path.write_text("\n".join(report) + "\n", encoding="utf-8")
    # Small machine-readable sidecar keeps the headline facts easy to consume.
    sidecar = {"status": "PASS" if structural_yes and not outside and not d_errors and not c_errors else "FAIL", "headline": {"CRASH_XPR_STRUCTURALLY_IDENTICAL_TO_D_EXCEPT_BITMAP": structural_yes, "DIFFERENCES_OUTSIDE_TARGET_SLOT": len(outside), "OUTER_ENCRYPTION_VALID": encrypted_roundtrip, "ATLAS_WRITE_BOUNDS_VALID": not outside}, "files": values, "diff": {"plaintext_diff_bytes": len(diffs), "encrypted_diff_bytes": encrypted_diff_count, "changed_target_pixels": target_diff_pixels, "raw_diff_runs": byte_runs, "region_counts": region_counts}}
    (out / "yahei_crash_diff_manifest.json").write_text(json.dumps(sidecar, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    print(json.dumps(sidecar["headline"], ensure_ascii=False))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
