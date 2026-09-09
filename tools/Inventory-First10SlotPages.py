#!/usr/bin/env python3
"""Read-only inventory of SLOT pages 0 through 9 for three fixed sources."""

from __future__ import annotations

import csv
import importlib.util
import json
import sys
from dataclasses import astuple
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
EXPERIMENTAL_TOOLS = ROOT.parent / "JPVoice_CNText_Experimental" / "tools"
OUTPUT = ROOT / "build" / "slot_investigation" / "first10_pages_inventory.csv"

MLG_KEY = Path(r"D:\GAME\test\JPN\MGS_PW\mgspw\MLG\disc0_rel\002aba34.KEY")
JPN_KEY = Path(r"D:\GAME\test\JPN\MGS_PW\mgspw\JPN\disc0_rel\002aba34.KEY")
SOURCES = (
    (
        "MLG_ORIG",
        Path(r"D:\GAME\test\JPN\MGS_PW\mgspw\MLG\disc0_rel\002aba34.DAT"),
        MLG_KEY,
    ),
    (
        "MLG_CN",
        Path(
            r"D:\GAME\test\steam 合金装备大师合集2 合金装备和平行者汉化补丁"
            r"\mgspw\MLG\disc0_rel\002aba34.DAT"
        ),
        MLG_KEY,
    ),
    (
        "JPN",
        Path(r"D:\GAME\test\JPN\MGS_PW\mgspw\JPN\disc0_rel\002aba34.DAT"),
        JPN_KEY,
    ),
)

FIELDS = (
    "source",
    "dat_path",
    "key_path",
    "page",
    "page_entry_start",
    "page_entry_end",
    "page_entry_capacity",
    "page_entry_first_raw",
    "page_entry_last_raw",
    "page_entry_hash_value",
    "page_entry_unknown_a",
    "page_entry_unknown_b",
    "page_header_unknown_a",
    "page_header_unknown_b",
    "page_header_padding",
    "page_compressed_size",
    "page_decoded_size",
    "page_tag_count",
    "page_signature",
    "cnf_table_pad",
    "cnf_header_size",
    "cnf_data_base",
    "tag_index",
    "kind",
    "file_id",
    "tag_is_file",
    "tag_pad_a",
    "tag_offset",
    "tag_pad_b",
    "segment_size",
    "segment_magic",
    "resource_type",
    "parser_used",
    "parse_status",
    "parse_error",
    "item_index",
    "record_index",
    "segment_index",
    "gtt_record_offset",
    "gtt_segment_count",
    "gtt_header_size",
    "gtt_record_size",
    "gtt_aligned_size",
    "gtt_nominal_capacity",
    "gtt_aligned_capacity",
    "gtt_fixed_header_hex",
    "gtt_common_metadata_hex",
    "gtt_descriptor_raw",
    "timing_start",
    "timing_end",
    "text_start",
    "text_end",
    "language_key",
    "reference_index",
    "reference_flag",
    "entity_index",
    "entity_key",
    "entity_reference_index",
    "entity_reference_count",
    "rbx_header_offset",
    "rbx_reference_offset",
    "rbx_body_offset",
    "ohd_header_hex",
    "ohd_metadata_hex",
    "text_offset",
    "text_capacity",
    "text",
    "text_encoding",
    "text_byte_length",
    "terminator_present",
    "terminator_offset",
    "interior_nul",
    "text_raw_region_hex",
)


def load_module(path: Path, name: str):
    spec = importlib.util.spec_from_file_location(name, path)
    if spec is None or spec.loader is None:
        raise RuntimeError(f"cannot load module: {path}")
    module = importlib.util.module_from_spec(spec)
    sys.modules[name] = module
    spec.loader.exec_module(module)
    return module


SLOT = load_module(EXPERIMENTAL_TOOLS / "Build-JpnSlot.py", "first10_slot")
VOICE = load_module(
    EXPERIMENTAL_TOOLS / "Build-JpnSlotNativeVoiceText.py", "first10_voice"
)
RBX = load_module(EXPERIMENTAL_TOOLS / "Build-JpnInitCache.py", "first10_rbx")
sys.path.insert(0, str(ROOT))
from core.gtt_multi import parse_gtt_multi  # noqa: E402


def compact_json(value) -> str:
    return json.dumps(value, ensure_ascii=False, separators=(",", ":"))


def base_page_row(source, dat_path, key_path, page, entry) -> dict:
    return {
        "source": source,
        "dat_path": str(dat_path),
        "key_path": str(key_path),
        "page": page,
        "page_entry_start": entry.start,
        "page_entry_end": entry.end,
        "page_entry_capacity": entry.capacity,
        "page_entry_first_raw": f"0x{entry.first:08X}",
        "page_entry_last_raw": f"0x{entry.last:08X}",
        "page_entry_hash_value": entry.hash_value,
        "page_entry_unknown_a": entry.unknown_a,
        "page_entry_unknown_b": entry.unknown_b,
    }


def add_page_data(row: dict, header, cnf) -> None:
    row.update(
        {
            "page_header_unknown_a": header.unknown_a,
            "page_header_unknown_b": header.unknown_b,
            "page_header_padding": header.padding,
            "page_compressed_size": header.compressed_size,
            "page_decoded_size": header.decompressed_size,
            "page_tag_count": len(cnf.tags),
            "page_signature": compact_json(
                [f"0x{file_id:08X}" for file_id in cnf.signature]
            ),
            "cnf_table_pad": cnf.table_pad,
            "cnf_header_size": cnf.header_size,
            "cnf_data_base": cnf.data_base,
        }
    )


def tag_row(page_row: dict, tag_index: int, tag, segment: bytes | None) -> dict:
    row = dict(page_row)
    row.update(
        {
            "tag_index": tag_index,
            "kind": f"0x{tag.kind:02X}",
            "file_id": f"0x{tag.file_id:08X}",
            "tag_is_file": tag.is_file,
            "tag_pad_a": tag.pad_a,
            "tag_offset": tag.offset,
            "tag_pad_b": tag.pad_b,
            "segment_size": "" if segment is None else len(segment),
            "segment_magic": "" if segment is None else segment[:4].hex().upper(),
        }
    )
    return row


def emit_gtt(rows: list[dict], base: dict, segment: bytes, label: str) -> None:
    records = parse_gtt_multi(segment, label)
    if not records:
        row = dict(base)
        row.update(
            {
                "resource_type": "YPK/GTT",
                "parser_used": "core.gtt_multi.parse_gtt_multi",
                "parse_status": "SUCCESS",
            }
        )
        rows.append(row)
        return
    for record in records:
        for timed in record.timed_texts:
            row = dict(base)
            text_offset = record.offset + record.header_size + timed.start
            row.update(
                {
                    "resource_type": "YPK/GTT_TIMED_SEGMENT",
                    "parser_used": "core.gtt_multi.parse_gtt_multi",
                    "parse_status": "SUCCESS",
                    "record_index": record.index,
                    "segment_index": timed.index,
                    "gtt_record_offset": record.offset,
                    "gtt_segment_count": record.segment_count,
                    "gtt_header_size": record.header_size,
                    "gtt_record_size": record.record_size,
                    "gtt_aligned_size": record.aligned_size,
                    "gtt_nominal_capacity": record.nominal_capacity,
                    "gtt_aligned_capacity": record.aligned_capacity,
                    "gtt_fixed_header_hex": record.header[:0x14].hex(),
                    "gtt_common_metadata_hex": record.header.hex(),
                    "gtt_descriptor_raw": compact_json(list(astuple(timed.header))),
                    "timing_start": timed.header.timing_a,
                    "timing_end": timed.header.timing_b,
                    "text_start": timed.start,
                    "text_end": timed.end,
                    "text_offset": text_offset,
                    "text_capacity": timed.end - timed.start,
                    "text": timed.text,
                    "text_encoding": "UTF-8",
                    "text_byte_length": len(timed.text_bytes),
                    "terminator_present": not timed.terminator_missing,
                    "terminator_offset": (
                        ""
                        if timed.terminator_offset is None
                        else record.offset + record.header_size + timed.terminator_offset
                    ),
                    "interior_nul": timed.interior_nul,
                    "text_raw_region_hex": timed.raw_region.hex(),
                }
            )
            rows.append(row)


def emit_ohd(rows: list[dict], base: dict, segment: bytes, label: str) -> None:
    header, records = VOICE.parse_ohd(segment, label)
    if not records:
        row = dict(base)
        row.update(
            {
                "resource_type": "OHD",
                "parser_used": "Build-JpnSlotNativeVoiceText.parse_ohd",
                "parse_status": "SUCCESS",
                "ohd_header_hex": header.hex(),
            }
        )
        rows.append(row)
        return
    for index, record in enumerate(records):
        text_region = record[VOICE.OHD_TEXT_OFFSET :]
        nul = text_region.find(b"\0")
        terminated = nul >= 0
        text_bytes = text_region if nul < 0 else text_region[:nul]
        text = text_bytes.decode("utf-8", errors="strict")
        absolute = VOICE.OHD_HEADER_SIZE + index * VOICE.OHD_RECORD_SIZE
        row = dict(base)
        row.update(
            {
                "resource_type": "OHD_RECORD",
                "parser_used": "Build-JpnSlotNativeVoiceText.parse_ohd",
                "parse_status": "SUCCESS",
                "item_index": index,
                "record_index": index,
                "ohd_header_hex": header.hex(),
                "ohd_metadata_hex": record[: VOICE.OHD_TEXT_OFFSET].hex(),
                "text_offset": absolute + VOICE.OHD_TEXT_OFFSET,
                "text_capacity": len(text_region),
                "text": text,
                "text_encoding": "UTF-8",
                "text_byte_length": len(text_bytes),
                "terminator_present": terminated,
                "terminator_offset": (
                    "" if nul < 0 else absolute + VOICE.OHD_TEXT_OFFSET + nul
                ),
                "interior_nul": terminated and nul != len(text_region) - 1,
                "text_raw_region_hex": text_region.hex(),
            }
        )
        rows.append(row)


def reference_entity(parsed, reference_index: int):
    for entity_index, entity in enumerate(parsed.entities):
        start = entity.reference_index
        if start <= reference_index < start + entity.reference_count:
            return entity_index, entity
    return None, None


def emit_olang(rows: list[dict], base: dict, segment: bytes, label: str) -> None:
    parsed = RBX.parse_rbx(segment, label)
    if not parsed.references:
        row = dict(base)
        row.update(
            {
                "resource_type": "OLANG/RBX",
                "parser_used": "Build-JpnInitCache.parse_rbx",
                "parse_status": "SUCCESS",
                "rbx_header_offset": parsed.header_offset,
                "rbx_reference_offset": parsed.reference_offset,
                "rbx_body_offset": parsed.body_offset,
            }
        )
        rows.append(row)
        return
    for index, reference in enumerate(parsed.references):
        entity_index, entity = reference_entity(parsed, index)
        text_bytes = reference.text.encode("utf-8")
        row = dict(base)
        row.update(
            {
                "resource_type": "OLANG/RBX_REFERENCE",
                "parser_used": "Build-JpnInitCache.parse_rbx",
                "parse_status": "SUCCESS",
                "item_index": "" if entity_index is None else entity_index,
                "reference_index": index,
                "language_key": f"0x{reference.language_key:08X}",
                "reference_flag": f"0x{reference.flag:08X}",
                "entity_index": "" if entity_index is None else entity_index,
                "entity_key": "" if entity is None else f"0x{entity.key:08X}",
                "entity_reference_index": "" if entity is None else entity.reference_index,
                "entity_reference_count": "" if entity is None else entity.reference_count,
                "rbx_header_offset": parsed.header_offset,
                "rbx_reference_offset": parsed.reference_offset,
                "rbx_body_offset": parsed.body_offset,
                "text_offset": parsed.body_offset + reference.body_offset,
                "text": reference.text,
                "text_encoding": "UTF-8",
                "text_byte_length": len(text_bytes),
                "terminator_present": True,
                "terminator_offset": parsed.body_offset + reference.body_offset + len(text_bytes),
            }
        )
        rows.append(row)


def main() -> int:
    for _, dat_path, key_path in SOURCES:
        if not dat_path.is_file():
            raise FileNotFoundError(dat_path)
        if not key_path.is_file():
            raise FileNotFoundError(key_path)

    key_cache = {}
    rows: list[dict] = []
    source_rows = {name: 0 for name, _, _ in SOURCES}
    pages_parsed = 0
    tags_parsed = 0
    parse_success = 0
    parse_failed = 0

    for source, dat_path, key_path in SOURCES:
        if key_path not in key_cache:
            seed = SLOT.CRYPTO.filename_seed(key_path)
            _, salts, entries = SLOT.decode_key(key_path, seed)
            key_cache[key_path] = (seed, salts, entries)
        seed, salts, entries = key_cache[key_path]

        for page in range(10):
            entry = entries[page]
            page_row = base_page_row(source, dat_path, key_path, page, entry)
            try:
                decoded, header = SLOT.decode_page(dat_path, entry, salts, seed)
                cnf = SLOT.parse_cnf(decoded)
            except Exception as error:
                row = dict(page_row)
                row.update(
                    {
                        "resource_type": "SLOT_PAGE",
                        "parser_used": "Build-JpnSlot.decode_page/parse_cnf",
                        "parse_status": "FAILED",
                        "parse_error": str(error),
                    }
                )
                rows.append(row)
                source_rows[source] += 1
                parse_failed += 1
                continue

            pages_parsed += 1
            add_page_data(page_row, header, cnf)
            tags_parsed += len(cnf.tags)

            for tag_index, tag in enumerate(cnf.tags):
                segment = cnf.segments.get(tag_index)
                base = tag_row(page_row, tag_index, tag, segment)
                before = len(rows)
                if segment is None:
                    row = dict(base)
                    row.update(
                        {
                            "resource_type": "CNF_TAG",
                            "parser_used": "Build-JpnSlot.parse_cnf",
                            "parse_status": "STRUCTURE_ONLY",
                        }
                    )
                    rows.append(row)
                elif tag.kind == VOICE.YPK_KIND:
                    try:
                        emit_gtt(rows, base, segment, f"{source}:p{page}:t{tag_index}")
                        parse_success += 1
                    except Exception as error:
                        row = dict(base)
                        row.update(
                            {
                                "resource_type": "YPK/GTT",
                                "parser_used": "core.gtt_multi.parse_gtt_multi",
                                "parse_status": "FAILED",
                                "parse_error": str(error),
                            }
                        )
                        rows.append(row)
                        parse_failed += 1
                elif tag.kind == VOICE.OHD_KIND:
                    try:
                        emit_ohd(rows, base, segment, f"{source}:p{page}:t{tag_index}")
                        parse_success += 1
                    except Exception as error:
                        row = dict(base)
                        row.update(
                            {
                                "resource_type": "OHD",
                                "parser_used": "Build-JpnSlotNativeVoiceText.parse_ohd",
                                "parse_status": "FAILED",
                                "parse_error": str(error),
                            }
                        )
                        rows.append(row)
                        parse_failed += 1
                elif tag.kind == 0x5D:
                    try:
                        emit_olang(rows, base, segment, f"{source}:p{page}:t{tag_index}")
                        parse_success += 1
                    except Exception as error:
                        row = dict(base)
                        row.update(
                            {
                                "resource_type": "OLANG/RBX",
                                "parser_used": "Build-JpnInitCache.parse_rbx",
                                "parse_status": "FAILED",
                                "parse_error": str(error),
                            }
                        )
                        rows.append(row)
                        parse_failed += 1
                else:
                    row = dict(base)
                    row.update(
                        {
                            "resource_type": "CNF_RESOURCE",
                            "parser_used": "Build-JpnSlot.parse_cnf",
                            "parse_status": "STRUCTURE_ONLY",
                        }
                    )
                    rows.append(row)
                source_rows[source] += len(rows) - before

    OUTPUT.parent.mkdir(parents=True, exist_ok=True)
    with OUTPUT.open("w", encoding="utf-8-sig", newline="") as stream:
        writer = csv.DictWriter(stream, fieldnames=FIELDS, extrasaction="ignore")
        writer.writeheader()
        writer.writerows(rows)

    print(f"CSV_PATH={OUTPUT.resolve()}")
    print(f"TOTAL_ROWS={len(rows)}")
    print(f"MLG_ORIG_ROWS={source_rows['MLG_ORIG']}")
    print(f"MLG_CN_ROWS={source_rows['MLG_CN']}")
    print(f"JPN_ROWS={source_rows['JPN']}")
    print(f"PAGES_PARSED={pages_parsed}")
    print(f"TAGS_PARSED={tags_parsed}")
    print(f"PARSE_SUCCESS={parse_success}")
    print(f"PARSE_FAILED={parse_failed}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
