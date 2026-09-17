#!/usr/bin/env python3
"""Build the minimal 00c7 TEST-2B count-field runtime diagnostic."""

from __future__ import annotations

import argparse
import hashlib
import json
import struct
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from core.pc_crypto import filename_seed, outer_transform
from core.xpr_font import XprFont, validate_glyph_rectangles


TARGET_CODEPOINT = 0x53A5
DONOR_CODEPOINT = 0x660F
TARGET_INDEX = 3209
USER_MAP_OFFSET = 0x16 + 2 * TARGET_CODEPOINT
USER_COUNT_MIRROR_OFFSET = 0x1FED4
COUNT_MIRROR_FILE_OFFSET = 0x1FF64
OUTPUT_NAME = "00c7c9f9.xpr"
RECORD_SIZE = 16


def sha256(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def hx(value: int) -> str:
    return f"0x{value:X}"


def load(path: Path) -> tuple[bytes, bytes, XprFont]:
    encrypted = path.read_bytes()
    plain = outer_transform(encrypted, filename_seed(path.name))
    return encrypted, plain, XprFont(plain)


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("v2_root", type=Path)
    args = parser.parse_args()
    root = args.v2_root.resolve()
    golden_path = root / "font" / "JPN_CN" / OUTPUT_NAME
    output_root = root / "font" / "font_poc_00c7_diagnostics_boundary"
    output_path = output_root / "TEST2B_COUNT_PATCH" / OUTPUT_NAME

    golden_encrypted, golden_plain, golden = load(golden_path)
    fd = golden.font_data
    donor_index = fd.charmap[DONOR_CODEPOINT]
    donor_record = fd.glyphs[donor_index]
    if donor_index != 1751:
        raise RuntimeError(f"unexpected Golden donor index for 昏: {donor_index}")
    if fd.charmap[TARGET_CODEPOINT] != 0:
        raise RuntimeError("Golden U+53A5 is unexpectedly mapped")
    if len(fd.glyphs) != TARGET_INDEX:
        raise RuntimeError(f"expected 3209 Golden records, got {len(fd.glyphs)}")

    user = bytearray(fd.payload)
    old_map_entry = bytes(user[USER_MAP_OFFSET : USER_MAP_OFFSET + 2])
    old_count_mirror = bytes(user[USER_COUNT_MIRROR_OFFSET : USER_COUNT_MIRROR_OFFSET + 4])
    if old_map_entry != b"\0\0":
        raise RuntimeError(f"unexpected Golden U+53A5 raw map: {old_map_entry.hex()}")
    if old_count_mirror != b"\0\0\x0c\x89":
        raise RuntimeError(f"unexpected Golden count mirror: {old_count_mirror.hex()}")

    struct.pack_into(">H", user, USER_MAP_OFFSET, TARGET_INDEX)
    user[USER_COUNT_MIRROR_OFFSET : USER_COUNT_MIRROR_OFFSET + 4] = struct.pack(">I", TARGET_INDEX + 1)
    user.extend(donor_record.packed)
    if len(user) != golden.user.size + RECORD_SIZE:
        raise RuntimeError("unexpected TEST-2B USER size")

    # No texture replacement: TEST-2B must remain atlas-identical.
    plain = golden.rebuild({("USER", "FontData"): bytes(user)})
    encrypted = outer_transform(plain, filename_seed(output_path.name))
    output_path.parent.mkdir(parents=True, exist_ok=True)
    output_path.write_bytes(encrypted)

    readback_encrypted, readback_plain, result = load(output_path)
    result_fd = result.font_data
    errors: list[str] = []
    if readback_plain != plain:
        errors.append("filename-seeded encrypt/decrypt readback mismatch")
    if struct.unpack_from(">I", result.user.payload, USER_COUNT_MIRROR_OFFSET)[0] != 3210:
        errors.append("glyph record count mirror is not 3210")
    if result.user.payload[USER_COUNT_MIRROR_OFFSET : USER_COUNT_MIRROR_OFFSET + 4] != b"\0\0\x0c\x8a":
        errors.append("count mirror raw bytes are not 00000C8A")
    if result.font_data.charmap[TARGET_CODEPOINT] != TARGET_INDEX:
        errors.append("U+53A5 does not map to 3209")
    if len(result_fd.glyphs) != 3210:
        errors.append(f"parser record count is {len(result_fd.glyphs)}, expected 3210")
    if result_fd.glyphs[TARGET_INDEX].packed != donor_record.packed:
        errors.append("record #3209 is not byte-identical to 昏 record")
    if result_fd.glyphs[:TARGET_INDEX] != fd.glyphs:
        errors.append("old GlyphRecords changed")
    if result.user.size != 0x2C778:
        errors.append(f"USER size is {hx(result.user.size)}, expected 0x2C778")
    if result.texture.texels != golden.texture.texels:
        errors.append("atlas changed")
    if result.tx2d.payload != golden.tx2d.payload:
        errors.append("TX2D changed")
    if result.texture_data_offset != golden.texture_data_offset:
        errors.append("texture offset changed")
    if result.data_size != golden.data_size:
        errors.append("XPR data_size changed")
    old_map = golden.user.payload[0x16 : 0x16 + 2 * len(fd.charmap)]
    new_map = result.user.payload[0x16 : 0x16 + 2 * len(result_fd.charmap)]
    relative = 2 * TARGET_CODEPOINT
    if old_map[:relative] != new_map[:relative] or old_map[relative + 2 :] != new_map[relative + 2 :]:
        errors.append("old charmap entries changed outside U+53A5")
    parser_errors = validate_glyph_rectangles(result_fd, result.texture)
    errors.extend(parser_errors)

    manifest = {
        "status": "PASS" if not errors else "FAIL",
        "errors": errors,
        "golden": {
            "path": str(golden_path),
            "encrypted_sha256": sha256(golden_encrypted),
            "decrypted_sha256": sha256(golden_plain),
            "user_size": golden.user.size,
            "glyph_count": len(fd.glyphs),
            "mapped_count": sum(index != 0 for index in fd.charmap),
            "atlas_sha256": sha256(golden.texture.texels),
        },
        "output": {
            "path": str(output_path),
            "encrypted_sha256": sha256(readback_encrypted),
            "decrypted_sha256": sha256(readback_plain),
            "filename_seed": hx(filename_seed(output_path.name)),
            "user_size": result.user.size,
            "glyph_count": len(result_fd.glyphs),
            "mapped_count": sum(index != 0 for index in result_fd.charmap),
            "atlas_sha256": sha256(result.texture.texels),
        },
        "donor": {
            "character": "昏",
            "codepoint": "U+660F",
            "glyph_index": donor_index,
            "record_raw_hex": donor_record.packed.hex(),
        },
        "target": {
            "character": "厥",
            "codepoint": "U+53A5",
            "glyph_index": TARGET_INDEX,
            "raw_charmap_before_hex": old_map_entry.hex(),
            "raw_charmap_after_hex": result.user.payload[USER_MAP_OFFSET : USER_MAP_OFFSET + 2].hex(),
        },
        "count_mirror": {
            "user_offset": hx(USER_COUNT_MIRROR_OFFSET),
            "file_offset": hx(COUNT_MIRROR_FILE_OFFSET),
            "before_hex": old_count_mirror.hex(),
            "after_hex": result.user.payload[USER_COUNT_MIRROR_OFFSET : USER_COUNT_MIRROR_OFFSET + 4].hex(),
            "before_be_u32": struct.unpack(">I", old_count_mirror)[0],
            "after_be_u32": struct.unpack_from(">I", result.user.payload, USER_COUNT_MIRROR_OFFSET)[0],
        },
        "assertions": {
            "readback_roundtrip": readback_plain == plain,
            "target_mapping": result_fd.charmap[TARGET_CODEPOINT],
            "target_record_equals_donor": result_fd.glyphs[TARGET_INDEX].packed == donor_record.packed,
            "old_records_unchanged": result_fd.glyphs[:TARGET_INDEX] == fd.glyphs,
            "old_charmap_unchanged_except_target": old_map[:relative] == new_map[:relative] and old_map[relative + 2 :] == new_map[relative + 2 :],
            "atlas_byte_identical": result.texture.texels == golden.texture.texels,
            "user_size": result.user.size,
            "tx2d_unchanged": result.tx2d.payload == golden.tx2d.payload,
            "texture_offset_unchanged": result.texture_data_offset == golden.texture_data_offset,
            "xpr_data_size_unchanged": result.data_size == golden.data_size,
            "parser_errors": parser_errors,
        },
    }
    manifest_path = output_root / "TEST2B_COUNT_PATCH" / "test2b_validation.json"
    manifest_path.write_text(json.dumps(manifest, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    report_lines = [
        "# TEST-2B count-field patch",
        "",
        "本测试只针对 `00c7c9f9.xpr`，沿用 TEST-2 的 charmap、append donor record 和 USER 增长，额外只改 count-like mirror。未修改 atlas、其他 FONT、translation 或 Golden。",
        "",
        "## 变更",
        "",
        f"- `U+53A5 → glyph 3209`，raw charmap：`{old_map_entry.hex()}` → `{result.user.payload[USER_MAP_OFFSET : USER_MAP_OFFSET + 2].hex()}`。",
        f"- `USER +0x1FED4` / file `0x1FF64`：`{old_count_mirror.hex()}` (`{struct.unpack('>I', old_count_mirror)[0]}`) → `00000C8A` (`3210`)。",
        f"- `glyph #3209` exact donor `昏 U+660F` record：`{donor_record.packed.hex()}`。",
        f"- USER size：`{hx(golden.user.size)}` → `{hx(result.user.size)}`；atlas 不变。",
        "",
        "## 静态回读",
        "",
        f"- status：`{'PASS' if not errors else 'FAIL'}`；parser errors：`{parser_errors}`。",
        f"- record count：`{len(result_fd.glyphs)}`；mapped count：`{sum(index != 0 for index in result_fd.charmap)}`。",
        f"- `U+53A5 → {result_fd.charmap[TARGET_CODEPOINT]}`；#3209 == donor：`{result_fd.glyphs[TARGET_INDEX].packed == donor_record.packed}`。",
        f"- old records unchanged：`{result_fd.glyphs[:TARGET_INDEX] == fd.glyphs}`；old mappings unchanged except target：`{old_map[:relative] == new_map[:relative] and old_map[relative + 2 :] == new_map[relative + 2 :]}`。",
        f"- atlas byte-identical：`{result.texture.texels == golden.texture.texels}`。",
        f"- encrypted SHA256：`{sha256(readback_encrypted)}`；decrypted SHA256：`{sha256(readback_plain)}`。",
        "",
        "## 实机预期",
        "",
        "安装后唯一预期结果：`……而昏昏`。",
        "",
        "如果 TEST-2B PASS，则 `0x1FF64` 的 u32 值可确认是 runtime-visible glyph record count；届时再修正 parser 识别该字段。当前不自动修改 parser，等待实机结果。",
        "",
        "## 手动步骤",
        "",
        "1. 恢复 Golden `00c7c9f9.xpr`。",
        "2. 安装 `TEST2B_COUNT_PATCH/00c7c9f9.xpr`。",
        "3. 查看同一句文本，预期显示 `……而昏昏`。",
        "4. 记录 `PASS / FAIL / CRASH / VISUAL_CORRUPTION`。",
        "5. 测试结束后恢复 Golden。",
    ]
    (output_root / "TEST2B_COUNT_PATCH" / "FONT_00C7_TEST2B_COUNT_PATCH.md").write_text("\n".join(report_lines) + "\n", encoding="utf-8")
    if errors:
        raise RuntimeError("TEST-2B static validation failed; see test2b_validation.json")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
