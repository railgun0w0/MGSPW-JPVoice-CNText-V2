#!/usr/bin/env python3
"""Rebuild the JPN OHD subtitle payload in its original SLOT allocation.

This is a temporary readiness build.  OHD records are fixed 128-byte records;
only the UTF-8/NUL text field is replaced.  All occurrences are required to
share one canonical JPN payload, and every changed page is decoded again after
writing.
"""

from __future__ import annotations

import argparse
import csv
import importlib.util
import json
import shutil
import sys
from collections import defaultdict
from pathlib import Path


OHD_KIND = 0x1E
OHD_HEADER_SIZE = 16
OHD_RECORD_SIZE = 128
OHD_TEXT_OFFSET = 60
OHD_TEXT_CAPACITY = OHD_RECORD_SIZE - OHD_TEXT_OFFSET


class BuildError(RuntimeError):
    pass


def load_module(path: Path, name: str):
    spec = importlib.util.spec_from_file_location(name, path)
    if spec is None or spec.loader is None:
        raise BuildError(f"cannot load helper module: {path}")
    module = importlib.util.module_from_spec(spec)
    sys.modules[name] = module
    spec.loader.exec_module(module)
    return module


def read_translation(path: Path) -> dict[str, str]:
    rows = list(csv.DictReader(path.open("r", encoding="utf-8-sig", newline="")))
    result: dict[str, str] = {}
    for row in rows:
        source = row.get("jpn_text", "")
        target = row.get("cn_text", "")
        if not source:
            raise BuildError(f"{path}: empty jpn_text")
        if not target:
            raise BuildError(f"{path}: empty cn_text for {source!r}")
        if source in result and result[source] != target:
            raise BuildError(f"{path}: conflicting duplicate JPN text")
        result[source] = target
    if not result:
        raise BuildError(f"{path}: no translation rows")
    return result


def parse_ohd(voice, data: bytes, label: str) -> tuple[bytes, list[bytes]]:
    return voice.parse_ohd(data, label)


def text_from_record(record: bytes, voice, label: str) -> str:
    field = record[voice.OHD_TEXT_OFFSET :]
    raw = field.split(b"\0", 1)[0]
    try:
        return raw.decode("utf-8")
    except UnicodeDecodeError as error:
        raise BuildError(f"{label}: invalid JPN OHD UTF-8: {error}") from error


def rebuild_payload(voice, source: bytes, translations: dict[str, str], file_id: str):
    header, records = parse_ohd(voice, source, f"JPN {file_id}")
    if len(header) != OHD_HEADER_SIZE:
        raise BuildError(f"{file_id}: unexpected OHD header size {len(header)}")
    rebuilt = bytearray(header)
    details: list[dict] = []
    for index, record in enumerate(records):
        source_text = text_from_record(record, voice, f"{file_id} record {index}")
        if source_text not in translations:
            raise BuildError(f"{file_id} record {index}: missing exact JPN translation")
        target_text = translations[source_text]
        encoded = target_text.encode("utf-8") + b"\0"
        if len(encoded) > OHD_TEXT_CAPACITY:
            raise BuildError(
                f"HARD_OVERFLOW {file_id} record {index}: required={len(encoded)} "
                f"capacity={OHD_TEXT_CAPACITY} over={len(encoded)-OHD_TEXT_CAPACITY}"
            )
        rebuilt_record = record[:OHD_TEXT_OFFSET] + encoded + bytes(
            OHD_TEXT_CAPACITY - len(encoded)
        )
        if rebuilt_record[:OHD_TEXT_OFFSET] != record[:OHD_TEXT_OFFSET]:
            raise BuildError(f"{file_id} record {index}: metadata changed during rebuild")
        rebuilt.extend(rebuilt_record)
        details.append(
            {
                "file_id": file_id,
                "record_index": index,
                "record_offset": OHD_HEADER_SIZE + index * OHD_RECORD_SIZE,
                "record_size": OHD_RECORD_SIZE,
                "text_offset": OHD_TEXT_OFFSET,
                "text_capacity": OHD_TEXT_CAPACITY,
                "jpn_text": source_text,
                "cn_text": target_text,
                "required": len(encoded),
                "fit": "NORMAL_FIT",
            }
        )
    rebuilt_bytes = bytes(rebuilt)
    verified_header, verified_records = parse_ohd(
        voice, rebuilt_bytes, f"rebuilt {file_id}"
    )
    if verified_header != header or len(verified_records) != len(records):
        raise BuildError(f"{file_id}: OHD header/record count round-trip mismatch")
    for detail, before, after in zip(details, records, verified_records):
        if before[:OHD_TEXT_OFFSET] != after[:OHD_TEXT_OFFSET]:
            raise BuildError(f"{file_id} record {detail['record_index']}: metadata round-trip mismatch")
        if text_from_record(after, voice, f"{file_id} verify {detail['record_index']}") != detail["cn_text"]:
            raise BuildError(f"{file_id} record {detail['record_index']}: text round-trip mismatch")
    return rebuilt_bytes, details


def parse_args() -> argparse.Namespace:
    root = Path(__file__).resolve().parents[1]
    parent = root.parent
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--jpn-dat",
        type=Path,
        default=Path(r"D:\GAME\test\JPN\MGS_PW\mgspw\JPN\disc0_rel\002aba34.DAT"),
    )
    parser.add_argument(
        "--jpn-key",
        type=Path,
        default=Path(r"D:\GAME\test\JPN\MGS_PW\mgspw\JPN\disc0_rel\002aba34.KEY"),
    )
    parser.add_argument(
        "--translation",
        type=Path,
        default=root / "translations" / "ohd" / "1E4C1146.csv",
    )
    parser.add_argument(
        "--output-dir",
        type=Path,
        default=root / "build" / "readiness" / "ohd" / "mgspw" / "JPN" / "disc0_rel",
    )
    parser.add_argument(
        "--legacy-tools",
        type=Path,
        default=parent / "JPVoice_CNText_Experimental" / "tools",
    )
    parser.add_argument(
        "--zopfli",
        type=Path,
        default=Path(shutil.which("zopfli")) if shutil.which("zopfli") else None,
    )
    return parser.parse_args()


def main() -> int:
    args = parse_args()
    root = Path(__file__).resolve().parents[1]
    if args.output_dir.resolve() == args.jpn_dat.resolve():
        raise BuildError("refusing to overwrite clean JPN DAT")
    sys.path.insert(0, str(root))
    slot = load_module(args.legacy_tools / "Build-JpnSlot.py", "v2_ohd_slot")
    full = load_module(args.legacy_tools / "Build-JpnSlotFullOlang.py", "v2_ohd_encoder")
    voice = load_module(args.legacy_tools / "Build-JpnSlotNativeVoiceText.py", "v2_ohd_parser")
    translations = read_translation(args.translation)

    seed = slot.CRYPTO.filename_seed(args.jpn_key)
    _, salts, entries = slot.decode_key(args.jpn_key, seed)
    occurrences: list[dict] = []
    page_cache: dict[int, tuple[bytes, object, object]] = {}
    for page_index in range(4, len(entries), 6):
        raw, page_header = slot.decode_page(args.jpn_dat, entries[page_index], salts, seed)
        cnf = slot.parse_cnf(raw)
        page_cache[page_index] = (raw, page_header, cnf)
        for tag_index, segment in cnf.segments.items():
            tag = cnf.tags[tag_index]
            if tag.kind == OHD_KIND:
                occurrences.append(
                    {
                        "page": page_index,
                        "tag": tag_index,
                        "file_id": f"{tag.file_id:08X}",
                        "segment": segment,
                    }
                )
    if not occurrences:
        raise BuildError("JPN localized SLOT lane contains no OHD occurrence")
    file_ids = sorted({item["file_id"] for item in occurrences})
    expected_file_id = args.translation.stem.upper()
    if file_ids != [expected_file_id]:
        raise BuildError(f"OHD identity mismatch: lane={file_ids}, translation={expected_file_id}")
    canonical_header, canonical_records = parse_ohd(
        voice, occurrences[0]["segment"], f"JPN {expected_file_id} canonical"
    )
    canonical_texts = [
        text_from_record(record, voice, f"{expected_file_id} canonical record {index}")
        for index, record in enumerate(canonical_records)
    ]
    rebuilt_occurrences: dict[tuple[int, int], bytes] = {}
    occurrence_details: list[dict] = []
    record_details: list[dict] = []
    for item in occurrences:
        item_header, item_records = parse_ohd(
            voice,
            item["segment"],
            f"JPN {expected_file_id} page {item['page']} tag {item['tag']}",
        )
        item_texts = [
            text_from_record(record, voice, f"{expected_file_id} page {item['page']} record {index}")
            for index, record in enumerate(item_records)
        ]
        if item_texts != canonical_texts:
            raise BuildError(
                f"{expected_file_id} page {item['page']} tag {item['tag']}: "
                "record count/text sequence differs from canonical OHD"
            )
        rebuilt_payload, details = rebuild_payload(
            voice, item["segment"], translations, expected_file_id
        )
        rebuilt_occurrences[(item["page"], item["tag"])] = rebuilt_payload
        if not record_details:
            record_details = details
        occurrence_details.append(
            {
                "page": item["page"],
                "tag_index": item["tag"],
                "source_size": len(item["segment"]),
                "rebuilt_size": len(rebuilt_payload),
                "metadata_before_60_bytes_preserved": all(
                    before[ : OHD_TEXT_OFFSET] == after[ : OHD_TEXT_OFFSET]
                    for before, after in zip(item_records, parse_ohd(voice, rebuilt_payload, "occurrence verify")[1])
                ),
            }
        )
    encoded_pages: list[dict] = []
    for page_index, (raw, page_header, cnf) in sorted(page_cache.items()):
        replacements = {
            tag_index: rebuilt_occurrences[(page_index, tag_index)]
            for tag_index, segment in cnf.segments.items()
            if cnf.tags[tag_index].kind == OHD_KIND
        }
        if not replacements:
            continue
        merged = slot.rebuild_cnf(cnf, replacements)
        if len(merged) != len(raw):
            raise BuildError(f"page {page_index}: decoded CNF allocation changed")
        verified = slot.parse_cnf(merged)
        for tag_index, expected in replacements.items():
            if verified.segments[tag_index] != expected:
                raise BuildError(f"page {page_index} tag {tag_index}: OHD replacement mismatch")
        try:
            encoded, compressed_size, strategy = full.encode_page_best(
                merged, page_header, entries[page_index].capacity, salts, seed, args.zopfli
            )
        except Exception as error:
            raise BuildError(f"page {page_index}: SLOT block encode overflow: {error}") from error
        if len(encoded) != entries[page_index].capacity:
            raise BuildError(f"page {page_index}: encoded allocation size changed")
        encoded_pages.append(
            {
                "page": page_index,
                "tag_indices": sorted(replacements),
                "entry_start": entries[page_index].start,
                "allocation_capacity": entries[page_index].capacity,
                "decoded_size_before": len(raw),
                "decoded_size_after": len(merged),
                "compressed_size_before": page_header.compressed_size,
                "compressed_size_after": compressed_size,
                "compression_strategy": strategy,
                "merged": merged,
                "encoded": encoded,
            }
        )

    args.output_dir.mkdir(parents=True, exist_ok=True)
    output_dat = args.output_dir / "002aba34.DAT"
    output_key = args.output_dir / "002aba34.KEY"
    shutil.copyfile(args.jpn_dat, output_dat)
    with output_dat.open("r+b") as stream:
        for job in encoded_pages:
            stream.seek(job["entry_start"])
            stream.write(job["encoded"])
    if output_dat.stat().st_size != args.jpn_dat.stat().st_size:
        raise BuildError("temporary DAT size changed")
    shutil.copyfile(args.jpn_key, output_key)
    for job in encoded_pages:
        decoded, _ = slot.decode_page(output_dat, entries[job["page"]], salts, seed)
        if decoded != job["merged"]:
            raise BuildError(f"page {job['page']}: written SLOT round-trip mismatch")

    report_path = root / "build" / "readiness" / "ohd_structure_report.json"
    report_path.parent.mkdir(parents=True, exist_ok=True)
    report = {
        "status": "PASS",
        "resource_class": "OHD",
        "file_id": expected_file_id,
        "source_dat": str(args.jpn_dat.resolve()),
        "source_key": str(args.jpn_key.resolve()),
        "output_dat": str(output_dat.resolve()),
        "output_key": str(output_key.resolve()),
        "record_count_canonical": len(record_details),
        "record_count_all_occurrences": len(record_details) * len(occurrences),
        "occurrence_count": len(occurrences),
        "patched_pages": len(encoded_pages),
        "hard_overflow": 0,
        "block_overflow": 0,
        "source_payloads_byte_identical": all(
            item["segment"] == occurrences[0]["segment"] for item in occurrences
        ),
        "dat_size_identical": output_dat.stat().st_size == args.jpn_dat.stat().st_size,
        "key_byte_identical": output_key.read_bytes() == args.jpn_key.read_bytes(),
        "metadata_preserved": True,
        "occurrences": occurrence_details,
        "record_details": record_details,
        "pages": [
            {key: value for key, value in job.items() if key not in {"merged", "encoded"}}
            for job in encoded_pages
        ],
    }
    report_path.write_text(json.dumps(report, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    print(f"FILE_ID={expected_file_id}")
    print(f"RECORDS_CANONICAL={len(record_details)}")
    print(f"RECORDS_ALL_OCCURRENCES={len(record_details) * len(occurrences)}")
    print(f"OCCURRENCES={len(occurrences)}")
    print(f"PATCHED_PAGES={len(encoded_pages)}")
    print("HARD_OVERFLOW=0")
    print("BLOCK_OVERFLOW=0")
    print(f"DAT_PATH={output_dat.resolve()}")
    print(f"KEY_PATH={output_key.resolve()}")
    print(f"REPORT_PATH={report_path.resolve()}")
    return 0


if __name__ == "__main__":
    try:
        raise SystemExit(main())
    except BuildError as error:
        print(f"ERROR={error}", file=sys.stderr)
        raise SystemExit(1)
