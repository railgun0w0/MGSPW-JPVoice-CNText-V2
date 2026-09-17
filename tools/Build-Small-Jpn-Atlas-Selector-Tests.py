from __future__ import annotations

import hashlib
import json
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from core.pc_crypto import filename_seed, outer_transform
from core.xpr_font import XprFont, validate_glyph_rectangles


ROOT = Path(__file__).resolve().parents[1]
FONT_DIR = ROOT / "font" / "JPN"
OUT_DIR = ROOT / "font" / "small_jpn_runtime_atlas_selector_poc"
TARGET_RECT = (1733, 470, 1799, 536)
TARGET_CP = 0x6211
TARGET_INDEX = 239
TARGET_CHAR = "我"


def sha(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def load(path: Path) -> tuple[bytes, bytes, XprFont]:
    encrypted = path.read_bytes()
    plain = outer_transform(encrypted, filename_seed(path.name))
    return encrypted, plain, XprFont(plain)


def marker(width: int, height: int) -> bytes:
    """High-contrast grayscale box/X marker, preserving the original cell size."""
    values = bytearray(width * height)
    for y in range(height):
        for x in range(width):
            block = 48 if ((x // 4 + y // 4) & 1) else 8
            is_border = x < 2 or y < 2 or x >= width - 2 or y >= height - 2
            is_x = abs(x - y) <= 1 or abs(x - ((width - 1) - y)) <= 1
            values[y * width + x] = 255 if is_border or is_x else block
    return bytes(values)


def atlas_indices(font: XprFont, rect: tuple[int, int, int, int]) -> set[int]:
    u0, v0, u1, v1 = rect
    return {
        font.texture_data_offset + y * font.texture.width + x
        for y in range(v0, v1)
        for x in range(u0, u1)
    }


def changed_ranges(left: bytes, right: bytes) -> tuple[list[int], list[list[int]]]:
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
    return indexes, ranges


def slot_bytes(font: XprFont) -> bytes:
    u0, v0, u1, v1 = TARGET_RECT
    return b"".join(
        font.texture.texels[y * font.texture.width + u0 : y * font.texture.width + u1]
        for y in range(v0, v1)
    )


def build_variant(label: str, source_path: Path, output_name: str) -> dict:
    source_encrypted, source_plain, source = load(source_path)
    # TEST A is defined by the 001c FontData record. TEST B intentionally
    # leaves 00c7 FontData untouched and edits only the same physical TX2D
    # rectangle, so 00c7's own charmap/index must not be substituted here.
    if label == "TEST_A_001C_OWN_TX2D":
        target = source.font_data.glyphs[TARGET_INDEX]
        if source.font_data.charmap[TARGET_CP] != TARGET_INDEX:
            raise RuntimeError(f"{source_path.name}: U+6211 mapping is not {TARGET_INDEX}")
        if (target.u0, target.v0, target.u1, target.v1) != TARGET_RECT:
            raise RuntimeError(f"{source_path.name}: glyph {TARGET_INDEX} rectangle is not {TARGET_RECT}")
        if target.width != TARGET_RECT[2] - TARGET_RECT[0]:
            raise RuntimeError(f"{source_path.name}: glyph width does not match target rectangle")

    width = TARGET_RECT[2] - TARGET_RECT[0]
    height = TARGET_RECT[3] - TARGET_RECT[1]
    marker_bytes = marker(width, height)
    texels = bytearray(source.texture.texels)
    u0, v0, u1, v1 = TARGET_RECT
    for row in range(height):
        start = (v0 + row) * source.texture.width + u0
        texels[start : start + width] = marker_bytes[row * width : (row + 1) * width]

    plain = source.rebuild(texture_texels=bytes(texels))
    encrypted = outer_transform(plain, filename_seed(output_name))
    destination = OUT_DIR / label / output_name
    destination.parent.mkdir(parents=True, exist_ok=True)
    destination.write_bytes(encrypted)
    read_encrypted, read_plain, readback = load(destination)

    indexes, ranges = changed_ranges(source_plain, read_plain)
    allowed = atlas_indices(source, TARGET_RECT)
    outside = sorted(set(indexes) - allowed)
    target_texel_changed = len(set(indexes) & allowed)
    errors: list[str] = []
    if len(source_encrypted) != len(read_encrypted):
        errors.append("encrypted file size changed")
    if len(source_plain) != len(read_plain):
        errors.append("decrypted file size changed")
    if readback.font_data.charmap != source.font_data.charmap:
        errors.append("charmap changed")
    if readback.font_data.glyphs != source.font_data.glyphs:
        errors.append("GlyphRecord table changed")
    if readback.user.payload != source.user.payload:
        errors.append("USER payload changed")
    if readback.tx2d.payload != source.tx2d.payload:
        errors.append("TX2D descriptor changed")
    if readback.header_size != source.header_size or readback.data_size != source.data_size or readback.resource_count != source.resource_count:
        errors.append("XPR header fields changed")
    if readback.texture.width != source.texture.width or readback.texture.height != source.texture.height or readback.texture.pitch != source.texture.pitch:
        errors.append("texture dimensions/pitch changed")
    if readback.texture.texels != bytes(texels):
        errors.append("texture readback mismatch")
    if slot_bytes(readback) != marker_bytes:
        errors.append("target marker readback mismatch")
    if outside:
        errors.append(f"{len(outside)} decrypted bytes changed outside target rectangle")
    errors.extend(validate_glyph_rectangles(readback.font_data, readback.texture))

    row_ranges = []
    for y in range(v0, v1):
        row_start = readback.texture_data_offset + y * source.texture.width + u0
        row_end = row_start + width
        row_ranges.append([row_start, row_end])

    return {
        "label": label,
        "source": str(source_path),
        "output": str(destination),
        "target": {"character": TARGET_CHAR, "codepoint": f"U+{TARGET_CP:04X}", "glyph_index": TARGET_INDEX, "rectangle": list(TARGET_RECT), "width": width, "height": height},
        "source_encrypted_sha256": sha(source_encrypted),
        "source_decrypted_sha256": sha(source_plain),
        "output_encrypted_sha256": sha(read_encrypted),
        "output_decrypted_sha256": sha(read_plain),
        "encrypted_size_source": len(source_encrypted),
        "encrypted_size_output": len(read_encrypted),
        "decrypted_size_source": len(source_plain),
        "decrypted_size_output": len(read_plain),
        "filename_seed": f"0x{filename_seed(output_name):08X}",
        "texture": {"width": source.texture.width, "height": source.texture.height, "pitch": source.texture.pitch, "format": source.texture.data_format, "tiled": source.texture.tiled, "endian": source.texture.endian, "texture_data_offset": f"0x{source.texture_data_offset:X}"},
        "decrypted_diff": {"changed_byte_count": len(indexes), "changed_range_count": len(ranges), "changed_ranges": [[f"0x{a:X}", f"0x{b:X}"] for a, b in ranges], "target_row_ranges": [[f"0x{a:X}", f"0x{b:X}"] for a, b in row_ranges], "target_allowed_byte_count": len(allowed), "changed_inside_target": target_texel_changed, "changed_outside_target": len(outside), "outside_offsets": [f"0x{i:X}" for i in outside[:50]]},
        "marker_sha256": sha(marker_bytes),
        "parser_errors": validate_glyph_rectangles(readback.font_data, readback.texture),
        "static_validation": "PASS" if not errors else "FAIL",
        "errors": errors,
    }


def main() -> None:
    # Each variant starts from the clean JPN file, not from the other experiment.
    a = build_variant("TEST_A_001C_OWN_TX2D", FONT_DIR / "001cbbd1.xpr", "001cbbd1.xpr")
    b = build_variant("TEST_B_00C7_TX2D", FONT_DIR / "00c7c9f9.xpr", "00c7c9f9.xpr")
    manifest = {"status": "PASS" if a["static_validation"] == b["static_validation"] == "PASS" else "FAIL", "tests": [a, b]}
    OUT_DIR.mkdir(parents=True, exist_ok=True)
    (OUT_DIR / "selector_test_manifest.json").write_text(json.dumps(manifest, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")

    report = [
        "# SMALL_JPN Runtime Atlas Selector Test",
        "",
        "本轮为只读构建验证之外的独立实验文件生成；没有修改 Golden、charmap、USER、GlyphRecord、glyph count 或另一份 XPR。",
        "",
        "## 测试设计",
        "",
        f"- 字符：`{TARGET_CHAR} U+{TARGET_CP:04X}`；001c charmap index=`{TARGET_INDEX}`。",
        f"- record UV：`{TARGET_RECT}`；目标像素尺寸：`{TARGET_RECT[2]-TARGET_RECT[0]}×{TARGET_RECT[3]-TARGET_RECT[1]}`。",
        "- 测试标记：同一份 66×66 高对比灰度 box/X pattern；A/B 使用完全相同的 marker bytes。",
        "- 两个文件都直接从 clean JPN 原文件独立生成。",
        "",
        "## TEST A：001c own TX2D",
        "",
        f"- 输入：`{a['source']}`",
        f"- 输出：`{a['output']}`",
        f"- 原始 encrypted SHA256：`{a['source_encrypted_sha256']}`",
        f"- 输出 encrypted SHA256：`{a['output_encrypted_sha256']}`",
        f"- 原始 decrypted SHA256：`{a['source_decrypted_sha256']}`",
        f"- 输出 decrypted SHA256：`{a['output_decrypted_sha256']}`",
        f"- filename seed：`{a['filename_seed']}`；文件大小：`{a['encrypted_size_source']}` → `{a['encrypted_size_output']}` bytes。",
        f"- 纹理物理起点：`{a['texture']['texture_data_offset']}`；pitch={a['texture']['pitch']}。",
        f"- 解密差异：`{a['decrypted_diff']['changed_byte_count']}` bytes，全部位于目标矩形行区间；目标外差异=`{a['decrypted_diff']['changed_outside_target']}`。",
        f"- 静态验证：`{a['static_validation']}`；parser errors=`{a['parser_errors']}`。",
        "",
        "## TEST B：00c7 TX2D",
        "",
        f"- 输入：`{b['source']}`",
        f"- 输出：`{b['output']}`",
        f"- 原始 encrypted SHA256：`{b['source_encrypted_sha256']}`",
        f"- 输出 encrypted SHA256：`{b['output_encrypted_sha256']}`",
        f"- 原始 decrypted SHA256：`{b['source_decrypted_sha256']}`",
        f"- 输出 decrypted SHA256：`{b['output_decrypted_sha256']}`",
        f"- filename seed：`{b['filename_seed']}`；文件大小：`{b['encrypted_size_source']}` → `{b['encrypted_size_output']}` bytes。",
        f"- 纹理物理起点：`{b['texture']['texture_data_offset']}`；pitch={b['texture']['pitch']}。",
        f"- 解密差异：`{b['decrypted_diff']['changed_byte_count']}` bytes，全部位于目标矩形行区间；目标外差异=`{b['decrypted_diff']['changed_outside_target']}`。",
        f"- 静态验证：`{b['static_validation']}`；parser errors=`{b['parser_errors']}`。",
        "",
        "## 精确修改范围",
        "",
        "线性 format=2 atlas 每行是一个连续 66-byte span；具体 66 个行区间、绝对文件偏移和完整 diff 已写入 `selector_test_manifest.json`。除这些目标行外，解密 XPR byte diff 必须为 0。",
        "",
        "## 实机判定",
        "",
        "1. 恢复 clean `001cbbd1.xpr` 和 `00c7c9f9.xpr`。",
        "2. 只安装 TEST A，打开 Loading 页面观察 `我`。",
        "3. 恢复 clean 文件，再只安装 TEST B，观察同一个 `我`。",
        "",
        "| TEST A | TEST B | 结论 |",
        "|---|---|---|",
        "| 改变 | 不改变 | Loading 使用 001c own TX2D |",
        "| 不改变 | 改变 | Loading 使用跨 XPR 的 00c7 TX2D |",
        "| 改变 | 改变 | 两份资源均被读取，停止继续 patch，重新检查 selector/binding |",
        "| 不改变 | 不改变 | 当前观察路径未读取这两个目标区域，停止继续 patch，检查缓存/其它 resource binding |",
        "",
        "本轮不加入 `们`，不 append GlyphRecord，不改 glyph count，不改 charmap。",
    ]
    (OUT_DIR / "SMALL_JPN_RUNTIME_ATLAS_SELECTOR_TEST.md").write_text("\n".join(report) + "\n", encoding="utf-8")
    print(json.dumps({"report": str(OUT_DIR / 'SMALL_JPN_RUNTIME_ATLAS_SELECTOR_TEST.md'), "tests": [a["output"], b["output"]], "status": manifest["status"]}, ensure_ascii=False))


if __name__ == "__main__":
    main()
