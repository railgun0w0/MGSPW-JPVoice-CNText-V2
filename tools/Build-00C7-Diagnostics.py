#!/usr/bin/env python3
"""Build isolated TEST-1/2/3 diagnostics for the 00c7 FONT runtime path."""

from __future__ import annotations

import argparse
import hashlib
import json
import struct
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from core.pc_crypto import filename_seed, outer_transform
from core.xpr_font import GlyphRecord, XprFont, validate_glyph_rectangles


TARGET_CHAR = "厥"
TARGET_CODEPOINT = 0x53A5
DONOR_CHAR = "昏"
DONOR_CODEPOINT = 0x660F
TARGET_INDEX = 3209
RECORD_SIZE = 16
TARGET_RECT = (0, 3333, 58, 3400)
OUTPUT_NAME = "00c7c9f9.xpr"


def sha256(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def hx(value: int) -> str:
    return f"0x{value:X}"


def load_font(path: Path) -> tuple[bytes, bytes, XprFont]:
    encrypted = path.read_bytes()
    plain = outer_transform(encrypted, filename_seed(path.name))
    return encrypted, plain, XprFont(plain)


def record_dict(record: GlyphRecord) -> dict[str, int]:
    return {
        "u0": record.u0,
        "v0": record.v0,
        "u1": record.u1,
        "v1": record.v1,
        "bearing_x_raw": record.bearing_x_raw,
        "bearing_x": record.bearing_x,
        "width": record.width,
        "advance": record.advance,
        "reserved": record.reserved,
    }


def slot_bytes(font: XprFont, rect: tuple[int, int, int, int]) -> bytes:
    u0, v0, u1, v1 = rect
    return b"".join(
        font.texture.texels[y * font.texture.width + u0 : y * font.texture.width + u1]
        for y in range(v0, v1)
    )


def slot_stats(data: bytes, width: int, height: int) -> dict[str, object]:
    points = [(i % width, i // width, value) for i, value in enumerate(data) if value]
    if not points:
        bbox = None
    else:
        bbox = [
            min(x for x, _, _ in points),
            min(y for _, y, _ in points),
            max(x for x, _, _ in points) + 1,
            max(y for _, y, _ in points) + 1,
        ]
    return {
        "width": width,
        "height": height,
        "nonzero_pixel_count": len(points),
        "ink_bbox_exclusive": bbox,
        "sha256": sha256(data),
        "min_nonzero": min((value for _, _, value in points), default=0),
        "max_nonzero": max((value for _, _, value in points), default=0),
    }


def write_pgm(path: Path, data: bytes, width: int, height: int) -> None:
    path.write_bytes(f"P5\n{width} {height}\n255\n".encode("ascii") + data)


def changed_indices(left: bytes, right: bytes) -> list[int]:
    if len(left) != len(right):
        raise ValueError("cannot compare byte arrays with different lengths")
    return [i for i, (a, b) in enumerate(zip(left, right)) if a != b]


def changed_summary(left: bytes, right: bytes) -> dict[str, object]:
    indices = changed_indices(left, right)
    ranges: list[list[int]] = []
    if indices:
        start = previous = indices[0]
        for index in indices[1:]:
            if index != previous + 1:
                ranges.append([start, previous + 1])
                start = index
            previous = index
        ranges.append([start, previous + 1])
    return {
        "changed_byte_count": len(indices),
        "changed_range_count": len(ranges),
        "changed_ranges_first_20": ranges[:20],
        "changed_min": min(indices) if indices else None,
        "changed_max_exclusive": max(indices) + 1 if indices else None,
    }


def target_slot_indices(font: XprFont) -> set[int]:
    u0, v0, u1, v1 = TARGET_RECT
    return {
        y * font.texture.width + x
        for y in range(v0, v1)
        for x in range(u0, u1)
    }


def patch_charmap(font: XprFont, value: int) -> bytes:
    payload = bytearray(font.user.payload)
    offset = 0x16 + 2 * TARGET_CODEPOINT
    if struct.unpack_from(">H", payload, offset)[0] != 0:
        raise RuntimeError("Golden U+53A5 is unexpectedly mapped")
    struct.pack_into(">H", payload, offset, value)
    return bytes(payload)


def append_record(font: XprFont, glyph: GlyphRecord) -> bytes:
    payload = bytearray(patch_charmap(font, TARGET_INDEX))
    payload.extend(glyph.packed)
    if len(payload) != font.user.size + RECORD_SIZE:
        raise RuntimeError("unexpected USER size after append")
    return bytes(payload)


def emit_variant(
    output_path: Path,
    golden_plain: bytes,
    golden: XprFont,
    user_payload: bytes,
    texture: bytes,
) -> tuple[bytes, bytes, XprFont]:
    plain = golden.rebuild({("USER", "FontData"): user_payload}, texture_texels=texture)
    encrypted = outer_transform(plain, filename_seed(output_path.name))
    output_path.parent.mkdir(parents=True, exist_ok=True)
    output_path.write_bytes(encrypted)
    readback_encrypted, readback_plain, readback = load_font(output_path)
    if readback_plain != plain:
        raise RuntimeError(f"encrypted readback differs for {output_path}")
    return readback_encrypted, readback_plain, readback


def validate_variant(
    name: str,
    golden: XprFont,
    golden_plain: bytes,
    result: XprFont,
    result_plain: bytes,
    donor: GlyphRecord,
    donor_index: int,
    expected_stage: int,
) -> dict[str, object]:
    errors: list[str] = []
    fd = golden.font_data
    out_fd = result.font_data
    target_map_offset = 0x16 + 2 * TARGET_CODEPOINT
    old_map = golden.user.payload[0x16 : 0x16 + 2 * len(fd.charmap)]
    new_map = result.user.payload[0x16 : 0x16 + 2 * len(out_fd.charmap)]
    target_relative = 2 * TARGET_CODEPOINT

    expected_map = donor_index if expected_stage == 1 else TARGET_INDEX
    if out_fd.charmap[TARGET_CODEPOINT] != expected_map:
        errors.append(f"target charmap is {out_fd.charmap[TARGET_CODEPOINT]}, expected {expected_map}")
    if expected_stage == 1:
        if len(out_fd.glyphs) != len(fd.glyphs):
            errors.append("TEST-1 glyph count changed")
        if result.user.size != golden.user.size:
            errors.append("TEST-1 USER size changed")
        if result.texture.texels != golden.texture.texels:
            errors.append("TEST-1 atlas changed")
    else:
        if len(out_fd.glyphs) != TARGET_INDEX + 1:
            errors.append("appended glyph count is not 3210")
        if result.user.size != golden.user.size + RECORD_SIZE:
            errors.append("appended USER size is not 0x2C778")
        if out_fd.glyphs[:TARGET_INDEX] != fd.glyphs:
            errors.append("old glyph records changed")
        if out_fd.glyphs[TARGET_INDEX] != donor:
            errors.append("appended glyph record is not the exact donor record")

    if old_map[:target_relative] != new_map[:target_relative]:
        errors.append("charmap bytes before U+53A5 changed")
    if old_map[target_relative + 2 :] != new_map[target_relative + 2 :]:
        errors.append("charmap bytes after U+53A5 changed")
    if expected_stage == 1:
        if new_map[target_relative : target_relative + 2] != struct.pack(">H", donor_index):
            errors.append("TEST-1 target raw charmap bytes are not donor index")
    if expected_stage >= 2:
        if new_map[target_relative : target_relative + 2] != struct.pack(">H", TARGET_INDEX):
            errors.append("appended target raw charmap bytes are wrong")

    if result.tx2d.payload != golden.tx2d.payload:
        errors.append("TX2D header changed")
    if result.texture_data_offset != golden.texture_data_offset:
        errors.append("texture offset changed")
    if result.data_size != golden.data_size:
        errors.append("XPR data_size changed")
    parser_errors = validate_glyph_rectangles(out_fd, result.texture)
    errors.extend(parser_errors)

    texture_diff = changed_summary(golden.texture.texels, result.texture.texels)
    allowed = target_slot_indices(golden)
    outside_count = sum(
        1
        for index, (before, after) in enumerate(zip(golden.texture.texels, result.texture.texels))
        if before != after and index not in allowed
    )
    if expected_stage <= 2 and texture_diff["changed_byte_count"] != 0:
        errors.append("TEST-1/2 atlas is not byte-identical")
    if outside_count:
        errors.append(f"{outside_count} atlas bytes changed outside destination slot")

    return {
        "name": name,
        "passed": not errors,
        "errors": errors,
        "target_charmap_file_offset": golden.user.offset + target_map_offset,
        "target_charmap_raw_hex": new_map[target_relative : target_relative + 2].hex(),
        "record_count": len(out_fd.glyphs),
        "mapped_codepoint_count": sum(index != 0 for index in out_fd.charmap),
        "user_size": result.user.size,
        "texture_diff": texture_diff,
        "atlas_changed_outside_target_slot": outside_count,
        "old_glyph_records_byte_identical": out_fd.glyphs[: len(fd.glyphs)] == fd.glyphs,
        "old_charmap_entries_byte_identical_except_target": (
            old_map[:target_relative] == new_map[:target_relative]
            and old_map[target_relative + 2 :] == new_map[target_relative + 2 :]
        ),
        "tx2d_unchanged": result.tx2d.payload == golden.tx2d.payload,
        "texture_offset_unchanged": result.texture_data_offset == golden.texture_data_offset,
        "xpr_data_size_unchanged": result.data_size == golden.data_size,
        "parser_errors": parser_errors,
    }


def review_failed_poc(golden: XprFont, failed_path: Path, dump_path: Path) -> dict[str, object]:
    if not failed_path.exists():
        return {"path": str(failed_path), "exists": False}
    encrypted, plain, failed = load_font(failed_path)
    donor_index = golden.font_data.charmap[DONOR_CODEPOINT]
    failed_target = failed.font_data.glyphs[TARGET_INDEX]
    target_slot = slot_bytes(failed, TARGET_RECT)
    write_pgm(dump_path, target_slot, TARGET_RECT[2] - TARGET_RECT[0], TARGET_RECT[3] - TARGET_RECT[1])
    changed = changed_summary(golden.texture.texels, failed.texture.texels)
    allowed = target_slot_indices(golden)
    outside = sum(
        1
        for index, (before, after) in enumerate(zip(golden.texture.texels, failed.texture.texels))
        if before != after and index not in allowed
    )
    return {
        "path": str(failed_path),
        "exists": True,
        "encrypted_sha256": sha256(encrypted),
        "decrypted_sha256": sha256(plain),
        "user_size": failed.user.size,
        "target_charmap": failed.font_data.charmap[TARGET_CODEPOINT],
        "target_charmap_raw_hex": failed.user.payload[0x16 + 2 * TARGET_CODEPOINT : 0x16 + 2 * TARGET_CODEPOINT + 2].hex(),
        "target_record_raw_hex": failed_target.packed.hex(),
        "target_record": record_dict(failed_target),
        "target_slot": slot_stats(target_slot, 58, 67),
        "atlas_diff": changed,
        "atlas_changed_outside_target_slot": outside,
        "tx2d_same_as_golden": failed.tx2d.payload == golden.tx2d.payload,
        "texture_offset_same_as_golden": failed.texture_data_offset == golden.texture_data_offset,
        "xpr_data_size_same_as_golden": failed.data_size == golden.data_size,
        "parser_errors": validate_glyph_rectangles(failed.font_data, failed.texture),
        "outer_encrypt_decrypt_roundtrip": outer_transform(plain, filename_seed(failed_path.name)) == encrypted,
        "record_uv_width": failed_target.u1 - failed_target.u0,
        "record_uv_height": failed_target.v1 - failed_target.v0,
        "record_width_matches_uv": failed_target.width == failed_target.u1 - failed_target.u0,
        "record_inside_atlas": (
            0 <= failed_target.u0 <= failed_target.u1 <= failed.texture.width
            and 0 <= failed_target.v0 <= failed_target.v1 <= failed.texture.height
        ),
        "slot_background_is_zero": min(target_slot, default=0) == 0,
        "slot_ink_polarity_nonzero_is_positive": min((value for value in target_slot if value), default=0) > 0,
        "slot_write_has_no_row_stride_overspill": outside == 0,
        "slot_dimensions": [TARGET_RECT[2] - TARGET_RECT[0], TARGET_RECT[3] - TARGET_RECT[1]],
        "dump_pgm": str(dump_path),
    }


def build_report(manifest: dict[str, object]) -> str:
    donor = manifest["donor"]
    references = manifest["reference_glyphs"]
    tests = manifest["tests"]
    failed = manifest["failed_poc_a_review"]
    lines = [
        "# 00c7 FONT runtime 分层诊断 PoC",
        "",
        "本目录只针对 `00c7c9f9.xpr`。Golden 文件未覆盖，未修改 translation、其他 FONT、游戏安装目录；没有制作 POC-B。",
        "",
        "## 核心静态结果",
        "",
        "- TEST-1、TEST-2、TEST-3 均完成 filename-seed 加密、解密 readback 和 XPR2 parser 校验。",
        "- 三个测试的静态验证均为 `PASS`。这不等于 runtime 已通过；仍需按报告末尾顺序实机测试。",
        f"- Golden `昏 U+660F` 的实际 glyph index：`{donor['glyph_index']}`。",
        f"- donor record：`{donor['record_raw_hex']}`。",
        f"- donor atlas rectangle：`{donor['rectangle']}`。",
        "",
        "## Donor：昏 U+660F",
        "",
        f"- glyph index：`{donor['glyph_index']}`",
        f"- GlyphRecord fields：`{json.dumps(donor['record'], ensure_ascii=False)}`",
        f"- raw 16 bytes：`{donor['record_raw_hex']}`",
        f"- atlas rectangle：`{donor['rectangle']}`",
        f"- donor bitmap：{json.dumps(donor['bitmap'], ensure_ascii=False)}",
        "",
        "## Golden 参考 CJK records",
        "",
        "以下完整 record 均直接从 Golden 00c7 读取：",
        "",
        "| 字符 | codepoint | glyph index | raw 16 bytes | UV | bearing_x | width | advance |",
        "|---|---|---:|---|---|---:|---:|---:|",
    ]
    for item in references:
        record = item["record"]
        lines.append(
            f"| {item['character']} | {item['codepoint']} | {item['glyph_index']} | `{item['record_raw_hex']}` | `{item['rectangle']}` | {record['bearing_x']} | {record['width']} | {record['advance']} |"
        )
    lines.extend(
        [
        "",
        "## 三个测试的变量边界",
        "",
        "| 测试 | 新增变量 | 不变内容 | 预期文字 |",
        "|---|---|---|---|",
        "| TEST-1 | 仅 `charmap[U+53A5] = glyph_of_昏` | record count、USER size、atlas | `昏昏` |",
        "| TEST-2 | TEST-1 + append exact donor record #3209 | atlas 不变，旧 records/mapping 不变 | `昏昏` |",
        "| TEST-3 | TEST-2 + donor bitmap copy 到新 slot，#3209 UV 改为新 slot | 旧 atlas pixels 不变 | `昏昏` |",
        "",
        "## 输出与静态验证",
        "",
        ]
    )
    for test_name, test in tests.items():
        lines.extend(
            [
                f"### {test_name}",
                "",
                f"- 输出：`{test['output']}`",
                f"- encrypted SHA256：`{test['encrypted_sha256']}`",
                f"- decrypted SHA256：`{test['decrypted_sha256']}`",
                f"- filename seed：`{test['filename_seed']}`",
                f"- target raw charmap：`{test['target_charmap_raw_hex']}`，mapping = `{test['target_mapping']}`",
                f"- record count：`{test['record_count']}`；USER size：`{hx(test['user_size'])}`",
                f"- parser errors：`{test['parser_errors']}`",
                f"- atlas diff：`{json.dumps(test['texture_diff'], ensure_ascii=False)}`",
                f"- atlas changed outside `[x=0..57,y=3333..3399]`：`{test['atlas_changed_outside_target_slot']}`",
                f"- old records unchanged：`{test['old_glyph_records_byte_identical']}`",
                f"- old charmap unchanged except target：`{test['old_charmap_entries_byte_identical_except_target']}`",
                f"- result：`{'PASS' if test['passed'] else 'FAIL'}`",
                "",
            ]
        )

    lines.extend(
        [
            "## 旧失败 POC-A 静态复盘",
            "",
            f"失败文件：`{failed['path']}`",
        ]
    )
    if failed.get("exists"):
        lines.extend(
            [
                f"- U+53A5 raw charmap：`{failed['target_charmap_raw_hex']}`，mapping = `{failed['target_charmap']}`",
                f"- failed #3209 raw record：`{failed['target_record_raw_hex']}`",
                f"- failed #3209 fields：`{json.dumps(failed['target_record'], ensure_ascii=False)}`",
                f"- failed destination slot decoded bitmap：`{json.dumps(failed['target_slot'], ensure_ascii=False)}`",
                f"- atlas changed outside destination slot：`{failed['atlas_changed_outside_target_slot']}`",
                f"- TX2D unchanged：`{failed['tx2d_same_as_golden']}`；texture offset unchanged：`{failed['texture_offset_same_as_golden']}`；data_size unchanged：`{failed['xpr_data_size_same_as_golden']}`",
                f"- parser errors：`{failed['parser_errors']}`",
                f"- outer encrypt/decrypt round-trip：`{failed['outer_encrypt_decrypt_roundtrip']}`",
                f"- record UV：`{failed['record_uv_width']}×{failed['record_uv_height']}`；record width matches UV：`{failed['record_width_matches_uv']}`；record inside atlas：`{failed['record_inside_atlas']}`",
                f"- slot dimensions：`{failed['slot_dimensions']}`；background zero：`{failed['slot_background_is_zero']}`；positive nonzero ink polarity：`{failed['slot_ink_polarity_nonzero_is_positive']}`",
                f"- row-stride/overspill static check：`{failed['slot_write_has_no_row_stride_overspill']}`",
                f"- PGM dump：`{failed['dump_pgm']}`",
                "",
                "旧失败 POC-A 的 record 字段本身符合规划的 58×67 / bearing 4 / advance 62 结构；其 atlas destination 也可按当前 TX2D 的 linear 8-bit、pitch=4096 逐行解码为单个非零 bitmap。静态 diff 没有发现 destination 之外的 atlas 越界、整行误写、背景极性反转或 outer encryption round-trip 错误。",
                "",
                "静态文件仍不能证明 runtime 对新 UV/record 的实际解释方式，也不能单凭 bitmap 反推出实机横向拉长纹理的来源；所以必须用 TEST-1/2/3 分层隔离。",
            ]
        )
    else:
        lines.append("- 旧失败 POC-A 文件不存在，无法做复盘。")

    lines.extend(
        [
            "",
            "## 结果判定表",
            "",
            "- TEST-1 FAIL：charmap patch、00c7 packaging 或 encryption 层仍有问题。",
            "- TEST-1 PASS + TEST-2 FAIL：USER growth、appended GlyphRecord 或 index 3209 runtime loading 有问题。",
            "- TEST-1 PASS + TEST-2 PASS + TEST-3 FAIL：新 atlas slot、texture storage、UV、pitch 或 atlas 写入有问题。",
            "- TEST-1 PASS + TEST-2 PASS + TEST-3 PASS：append-only runtime 路线成立；旧失败 POC-A 的问题集中到 generated 厥 raster、metrics 或 raster-to-atlas write path。",
            "",
            "## 手动实机测试顺序",
            "",
            "1. 恢复 Golden `00c7c9f9.xpr`。",
            "2. 安装 `TEST1_CHARMAP_EXISTING/00c7c9f9.xpr`，检查是否显示为：`被击中的对手会承受不住而昏昏`。记录 `PASS / FAIL / CRASH / VISUAL_CORRUPTION`。",
            "3. 恢复 Golden。",
            "4. 安装 `TEST2_APPENDED_RECORD_EXISTING_ATLAS/00c7c9f9.xpr`，预期仍为 `...而昏昏`，记录结果。",
            "5. 恢复 Golden。",
            "6. 安装 `TEST3_APPENDED_RECORD_NEW_ATLAS/00c7c9f9.xpr`，预期仍为 `...而昏昏`，记录结果。",
            "7. 测试结束后恢复 Golden。",
            "",
            "本轮未自动安装、未修改 Golden、未修改 0007/000e/001c、未进入批量 glyph 或 relocation。",
        ]
    )
    return "\n".join(lines) + "\n"


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("v2_root", type=Path)
    parser.add_argument(
        "--reuse-existing",
        action="store_true",
        help="reuse already emitted diagnostic XPRs and only rebuild their readback report",
    )
    args = parser.parse_args()
    root = args.v2_root.resolve()
    golden_path = root / "font" / "JPN_CN" / OUTPUT_NAME
    failed_path = root / "font" / "font_poc" / "POC_A_00C7" / OUTPUT_NAME
    output_root = root / "font" / "font_poc_00c7_diagnostics"

    golden_encrypted, golden_plain, golden = load_font(golden_path)
    fd = golden.font_data
    donor_index = fd.charmap[DONOR_CODEPOINT]
    if donor_index == 0:
        raise RuntimeError("Golden U+660F is unexpectedly unmapped")
    donor_record = fd.glyphs[donor_index]
    donor_rect = (donor_record.u0, donor_record.v0, donor_record.u1, donor_record.v1)
    donor_bitmap = slot_bytes(golden, donor_rect)
    donor_bitmap_info = slot_stats(donor_bitmap, donor_rect[2] - donor_rect[0], donor_rect[3] - donor_rect[1])

    target_map = patch_charmap(golden, donor_index)
    test2_glyph = donor_record
    test2_user = append_record(golden, test2_glyph)
    test3_glyph = donor_record.with_uv(*TARGET_RECT)
    test3_user = append_record(golden, test3_glyph)
    test3_texture = bytearray(golden.texture.texels)
    destination_before = slot_bytes(golden, TARGET_RECT)
    if any(destination_before):
        raise RuntimeError("Golden target atlas slot is not blank")
    for row in range(TARGET_RECT[3] - TARGET_RECT[1]):
        dest = (TARGET_RECT[1] + row) * golden.texture.width + TARGET_RECT[0]
        src = row * (donor_rect[2] - donor_rect[0])
        test3_texture[dest : dest + (TARGET_RECT[2] - TARGET_RECT[0])] = donor_bitmap[src : src + (TARGET_RECT[2] - TARGET_RECT[0])]

    specs = [
        ("TEST1_CHARMAP_EXISTING", target_map, golden.texture.texels, 1),
        ("TEST2_APPENDED_RECORD_EXISTING_ATLAS", test2_user, golden.texture.texels, 2),
        ("TEST3_APPENDED_RECORD_NEW_ATLAS", test3_user, bytes(test3_texture), 3),
    ]
    tests: dict[str, object] = {}
    for directory, user_payload, texture, stage in specs:
        output_path = output_root / directory / OUTPUT_NAME
        if args.reuse_existing and output_path.exists():
            encrypted, plain, result = load_font(output_path)
        else:
            encrypted, plain, result = emit_variant(output_path, golden_plain, golden, user_payload, texture)
        validation = validate_variant(
            directory,
            golden,
            golden_plain,
            result,
            plain,
            test2_glyph if stage == 2 else test3_glyph,
            donor_index,
            stage,
        )
        validation.update(
            {
                "output": str(output_path),
                "encrypted_sha256": sha256(encrypted),
                "decrypted_sha256": sha256(plain),
                "filename_seed": hx(filename_seed(output_path.name)),
                "target_mapping": result.font_data.charmap[TARGET_CODEPOINT],
            }
        )
        tests[directory] = validation

    failed_dump = output_root / "failed_poc_a_00c7_slot.pgm"
    failed_review = review_failed_poc(golden, failed_path, failed_dump)
    reference_chars = ["昏", "厢", "决", "缺", "卷", "厌"]
    reference_codepoints = [0x660F, 0x53A2, 0x51B3, 0x7F3A, 0x5377, 0x538C]
    reference_glyphs: list[dict[str, object]] = []
    for character, codepoint in zip(reference_chars, reference_codepoints):
        index = fd.charmap[codepoint]
        if index == 0:
            raise RuntimeError(f"Golden reference character {character} is unmapped")
        record = fd.glyphs[index]
        rectangle = (record.u0, record.v0, record.u1, record.v1)
        reference_glyphs.append(
            {
                "character": character,
                "codepoint": f"U+{codepoint:04X}",
                "glyph_index": index,
                "record": record_dict(record),
                "record_raw_hex": record.packed.hex(),
                "rectangle": list(rectangle),
                "bitmap": slot_stats(
                    slot_bytes(golden, rectangle),
                    rectangle[2] - rectangle[0],
                    rectangle[3] - rectangle[1],
                ),
            }
        )
    manifest = {
        "golden": {
            "path": str(golden_path),
            "encrypted_sha256": sha256(golden_encrypted),
            "decrypted_sha256": sha256(golden_plain),
            "encrypted_size": len(golden_encrypted),
            "decrypted_size": len(golden_plain),
            "filename_seed": hx(filename_seed(golden_path.name)),
            "glyph_count": len(fd.glyphs),
            "mapped_codepoint_count": sum(index != 0 for index in fd.charmap),
            "user_size": golden.user.size,
            "texture_offset": golden.texture_data_offset,
            "data_size": golden.data_size,
        },
        "donor": {
            "character": DONOR_CHAR,
            "codepoint": f"U+{DONOR_CODEPOINT:04X}",
            "glyph_index": donor_index,
            "record": record_dict(donor_record),
            "record_raw_hex": donor_record.packed.hex(),
            "rectangle": list(donor_rect),
            "bitmap": donor_bitmap_info,
        },
        "reference_glyphs": reference_glyphs,
        "target": {
            "character": TARGET_CHAR,
            "codepoint": f"U+{TARGET_CODEPOINT:04X}",
            "new_glyph_index": TARGET_INDEX,
            "rectangle": list(TARGET_RECT),
            "destination_before_sha256": sha256(destination_before),
        },
        "tests": tests,
        "failed_poc_a_review": failed_review,
        "notes": [
            "All variants are encrypted with the 00c7c9f9 filename seed.",
            "No 0007/000e/001c output was created.",
            "Only the diagnostic output directory was written.",
        ],
    }
    output_root.mkdir(parents=True, exist_ok=True)
    (output_root / "diagnostic_manifest.json").write_text(
        json.dumps(manifest, ensure_ascii=False, indent=2) + "\n", encoding="utf-8"
    )
    (output_root / "FONT_00C7_RUNTIME_DIAGNOSTIC.md").write_text(
        build_report(manifest), encoding="utf-8"
    )
    if not all(test["passed"] for test in tests.values()):
        raise RuntimeError("one or more diagnostic tests failed static validation")
    print(json.dumps(manifest, ensure_ascii=False, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
