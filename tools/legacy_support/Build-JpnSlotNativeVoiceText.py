#!/usr/bin/env python3
"""Rebuild Japanese SLOT YPK/OHD text while retaining Japanese runtime data."""

from __future__ import annotations

import argparse
import collections
import hashlib
import importlib.util
import json
import re
import shutil
import struct
import sys
from dataclasses import dataclass
from pathlib import Path


EXPECTED_CHANGED_PAGES = 110
EXPECTED_YPK_OCCURRENCES = 77
EXPECTED_OHD_OCCURRENCES = 4
EXPECTED_UNIQUE_YPK = 36
EXPECTED_ENG_RECORDS = 1860
EXPECTED_JPN_RECORDS = 1882
EXPECTED_EXTRA_RECORDS = 22
EXPECTED_CN_OVERRIDES = 24
YPK_KIND = 0x1C
OHD_KIND = 0x1E
GTT_MAGIC = b"GTT\0"
GTT_ALIGNMENT = 16
OHD_HEADER_SIZE = 16
OHD_RECORD_SIZE = 128
OHD_TEXT_OFFSET = 60
KANA_RE = re.compile(r"[\u3040-\u30ff\u31f0-\u31ff]")
HAN_RE = re.compile(r"[\u3400-\u4dbf\u4e00-\u9fff]")


class NativeVoiceTextError(RuntimeError):
    pass


def load_module(filename: str, name: str):
    path = Path(__file__).with_name(filename)
    spec = importlib.util.spec_from_file_location(name, path)
    if spec is None or spec.loader is None:
        raise NativeVoiceTextError(f"cannot load helper module: {path}")
    module = importlib.util.module_from_spec(spec)
    sys.modules[name] = module
    spec.loader.exec_module(module)
    return module


SLOT = load_module("Build-JpnSlot.py", "mgspw_slot_native_voice")
FULL = load_module("Build-JpnSlotFullOlang.py", "mgspw_slot_native_voice_full")


def align_up(value: int, alignment: int = GTT_ALIGNMENT) -> int:
    return (value + alignment - 1) // alignment * alignment


def sha256(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest().upper()


@dataclass(frozen=True)
class GttRecord:
    index: int
    offset: int
    header: bytes
    payload: bytes
    body: bytes


def parse_gtt(data: bytes, label: str) -> list[GttRecord]:
    records: list[GttRecord] = []
    offset = 0
    while offset < len(data):
        if data[offset : offset + 4] != GTT_MAGIC:
            if not any(data[offset:]):
                break
            raise NativeVoiceTextError(f"{label}: missing GTT magic at 0x{offset:X}")
        if offset + 16 > len(data):
            raise NativeVoiceTextError(f"{label}: truncated GTT header at 0x{offset:X}")
        header_size, record_size = struct.unpack_from("<II", data, offset + 8)
        if header_size < 56 or record_size < header_size or offset + record_size > len(data):
            raise NativeVoiceTextError(
                f"{label}: invalid GTT sizes at 0x{offset:X}: header={header_size}, record={record_size}"
            )
        aligned_end = align_up(offset + record_size)
        if aligned_end > len(data):
            raise NativeVoiceTextError(f"{label}: aligned record exceeds segment at 0x{offset:X}")
        body = data[offset : offset + record_size]
        records.append(
            GttRecord(
                index=len(records),
                offset=offset,
                header=body[:header_size],
                payload=body[header_size:],
                body=body,
            )
        )
        offset = aligned_end
    if offset != len(data) and any(data[offset:]):
        raise NativeVoiceTextError(f"{label}: nonzero trailing bytes at 0x{offset:X}")
    return records


def decode_gtt_text(record: GttRecord, label: str) -> str:
    raw = record.payload.split(b"\0", 1)[0]
    try:
        return raw.decode("utf-8")
    except UnicodeDecodeError as error:
        raise NativeVoiceTextError(f"{label}: invalid UTF-8 in record {record.index}: {error}") from error


def build_gtt_record(header: bytes, text: str, label: str) -> bytes:
    if KANA_RE.search(text):
        raise NativeVoiceTextError(f"{label}: Chinese output still contains kana: {text!r}")
    if "\ufffd" in text:
        raise NativeVoiceTextError(f"{label}: Chinese output contains replacement character")
    encoded = text.encode("utf-8")
    rebuilt_header = bytearray(header)
    record_size = len(rebuilt_header) + len(encoded) + 1
    struct.pack_into("<I", rebuilt_header, 12, record_size)
    body = bytes(rebuilt_header) + encoded + b"\0"
    return body + bytes((-len(body)) % GTT_ALIGNMENT)


def parse_translation_table(path: Path) -> dict[str, dict[int, str]]:
    document = json.loads(path.read_text(encoding="utf-8"))
    output: dict[str, dict[int, str]] = {}
    for file_id, values in document.items():
        output[file_id] = {int(index): text for index, text in values.items()}
        for index, text in output[file_id].items():
            if index < 0 or not isinstance(text, str) or not text:
                raise NativeVoiceTextError(f"{path}: invalid translation {file_id}:{index}")
            if KANA_RE.search(text):
                raise NativeVoiceTextError(f"{path}: translation has kana at {file_id}:{index}")
    return output


def candidate_score(text: str, original: str) -> tuple[int, int, int, int, int]:
    return (
        bool(text.strip()),
        len(HAN_RE.findall(text)),
        text != original,
        -len(KANA_RE.findall(text)),
        -len(text),
    )


def rebuild_ypk(
    file_id: str,
    target_data: bytes,
    eng_data: bytes,
    cn_variants: list[bytes],
    extras: dict[int, str],
    cn_overrides: dict[int, str],
) -> tuple[bytes, dict]:
    target_records = parse_gtt(target_data, f"{file_id}:JPN")
    eng_records = parse_gtt(eng_data, f"{file_id}:ENG")
    cn_record_sets = [
        parse_gtt(data, f"{file_id}:CN:{variant_index}")
        for variant_index, data in enumerate(cn_variants)
    ]
    if any(len(records) != len(eng_records) for records in cn_record_sets):
        raise NativeVoiceTextError(f"{file_id}: ENG/CN record-count mismatch")
    if len(target_records) != len(eng_records) + len(extras):
        raise NativeVoiceTextError(
            f"{file_id}: JPN count {len(target_records)} != ENG {len(eng_records)} + extras {len(extras)}"
        )
    if any(index >= len(target_records) for index in extras):
        raise NativeVoiceTextError(f"{file_id}: extra-record index is out of range")
    if any(index >= len(eng_records) for index in cn_overrides):
        raise NativeVoiceTextError(f"{file_id}: CN override index is out of range")

    output = bytearray()
    eng_index = 0
    used_extras: set[int] = set()
    used_overrides: set[int] = set()
    selected_variant_counts: collections.Counter[int] = collections.Counter()
    text_hashes: list[str] = []

    for target_index, target_record in enumerate(target_records):
        if target_index in extras:
            text = extras[target_index]
            header = target_record.header
            used_extras.add(target_index)
            mode = "jpn_extra_manual"
        else:
            if eng_index >= len(eng_records):
                raise NativeVoiceTextError(f"{file_id}: exhausted ENG records at JPN index {target_index}")
            original_text = decode_gtt_text(eng_records[eng_index], f"{file_id}:ENG")
            if eng_index in cn_overrides:
                text = cn_overrides[eng_index]
                # Use the first CN header as its established Chinese layout template.
                header = cn_record_sets[0][eng_index].header
                used_overrides.add(eng_index)
                mode = "cn_manual_override"
            else:
                candidates: list[tuple[tuple[int, int, int, int, int], int, str, bytes]] = []
                errors = []
                for variant_index, records in enumerate(cn_record_sets):
                    try:
                        candidate_text = decode_gtt_text(
                            records[eng_index], f"{file_id}:CN:{variant_index}"
                        )
                    except NativeVoiceTextError as error:
                        errors.append(str(error))
                        continue
                    candidates.append(
                        (
                            candidate_score(candidate_text, original_text),
                            variant_index,
                            candidate_text,
                            records[eng_index].header,
                        )
                    )
                if not candidates:
                    raise NativeVoiceTextError(
                        f"{file_id}: no valid CN candidate for ENG record {eng_index}; {errors[:3]}"
                    )
                _, variant_index, text, header = max(candidates, key=lambda item: item[0])
                selected_variant_counts[variant_index] += 1
                mode = "cn_best_variant"
            if KANA_RE.search(text):
                raise NativeVoiceTextError(
                    f"{file_id}: mapped CN record {eng_index} still contains kana: {text!r}"
                )
            eng_index += 1
        rebuilt = build_gtt_record(header, text, f"{file_id}:{target_index}:{mode}")
        output.extend(rebuilt)
        text_hashes.append(sha256(text.encode("utf-8")))

    if eng_index != len(eng_records):
        raise NativeVoiceTextError(f"{file_id}: used {eng_index}/{len(eng_records)} ENG records")
    if used_extras != set(extras):
        raise NativeVoiceTextError(f"{file_id}: unused extra translations {sorted(set(extras) - used_extras)}")
    if used_overrides != set(cn_overrides):
        raise NativeVoiceTextError(f"{file_id}: unused CN overrides {sorted(set(cn_overrides) - used_overrides)}")

    verified = parse_gtt(bytes(output), f"{file_id}:rebuilt")
    if len(verified) != len(target_records):
        raise NativeVoiceTextError(f"{file_id}: rebuilt GTT record-count mismatch")
    final_texts = [decode_gtt_text(record, f"{file_id}:verify") for record in verified]
    remaining_kana = [index for index, text in enumerate(final_texts) if KANA_RE.search(text)]
    if remaining_kana:
        raise NativeVoiceTextError(f"{file_id}: remaining kana at {remaining_kana[:20]}")
    return bytes(output), {
        "file_id": file_id,
        "eng_record_count": len(eng_records),
        "jpn_record_count": len(target_records),
        "extra_record_indices": sorted(extras),
        "cn_override_indices": sorted(cn_overrides),
        "selected_variant_counts": dict(sorted(selected_variant_counts.items())),
        "output_size": len(output),
        "output_sha256": sha256(bytes(output)),
        "text_set_sha256": sha256("\n".join(text_hashes).encode("ascii")),
        "remaining_kana_count": 0,
        "utf8_verified": True,
    }


def parse_ohd(data: bytes, label: str) -> tuple[bytes, list[bytes]]:
    if len(data) < OHD_HEADER_SIZE:
        raise NativeVoiceTextError(f"{label}: OHD is shorter than its header")
    count = struct.unpack_from("<I", data, 8)[0]
    expected_size = OHD_HEADER_SIZE + count * OHD_RECORD_SIZE
    if len(data) != expected_size:
        raise NativeVoiceTextError(
            f"{label}: OHD size mismatch: size={len(data)}, count={count}, expected={expected_size}"
        )
    return data[:OHD_HEADER_SIZE], [
        data[OHD_HEADER_SIZE + index * OHD_RECORD_SIZE : OHD_HEADER_SIZE + (index + 1) * OHD_RECORD_SIZE]
        for index in range(count)
    ]


def merge_ohd(target: bytes, chinese: bytes, label: str) -> tuple[bytes, dict]:
    target_header, target_records = parse_ohd(target, label + ":JPN")
    _, cn_records = parse_ohd(chinese, label + ":CN")
    if len(target_records) != len(cn_records):
        raise NativeVoiceTextError(f"{label}: OHD record-count mismatch")
    output = bytearray(target_header)
    changed = 0
    for index, (target_record, cn_record) in enumerate(zip(target_records, cn_records)):
        text_field = cn_record[OHD_TEXT_OFFSET:]
        raw_text = text_field.split(b"\0", 1)[0]
        try:
            text = raw_text.decode("utf-8")
        except UnicodeDecodeError as error:
            raise NativeVoiceTextError(f"{label}: invalid CN OHD UTF-8 at {index}: {error}") from error
        if KANA_RE.search(text):
            raise NativeVoiceTextError(f"{label}: CN OHD record {index} still has kana")
        rebuilt = bytearray(target_record)
        rebuilt[OHD_TEXT_OFFSET:] = text_field
        changed += rebuilt != target_record
        output.extend(rebuilt)
    verified_header, verified_records = parse_ohd(bytes(output), label + ":rebuilt")
    if verified_header != target_header or len(verified_records) != len(target_records):
        raise NativeVoiceTextError(f"{label}: OHD round-trip verification failed")
    return bytes(output), {
        "record_count": len(target_records),
        "changed_record_count": changed,
        "jpn_metadata_preserved": True,
        "remaining_kana_count": 0,
        "utf8_verified": True,
        "output_sha256": sha256(bytes(output)),
    }


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--base-dat", type=Path, required=True)
    parser.add_argument("--jpn-key", type=Path, required=True)
    parser.add_argument("--eng-original-dat", type=Path, required=True)
    parser.add_argument("--eng-key", type=Path, required=True)
    parser.add_argument("--cn-dat", type=Path, required=True)
    parser.add_argument("--extra-translations", type=Path, required=True)
    parser.add_argument("--cn-overrides", type=Path, required=True)
    parser.add_argument("--zopfli", type=Path)
    parser.add_argument("--output", type=Path, required=True)
    parser.add_argument("--report", type=Path, required=True)
    args = parser.parse_args()
    if args.output.resolve() in (
        args.base_dat.resolve(),
        args.eng_original_dat.resolve(),
        args.cn_dat.resolve(),
    ):
        parser.error("refusing to overwrite an input SLOT DAT")
    if args.zopfli is not None and not args.zopfli.is_file():
        parser.error(f"zopfli executable not found: {args.zopfli}")

    extras_by_id = parse_translation_table(args.extra_translations)
    overrides_by_id = parse_translation_table(args.cn_overrides)
    if sum(len(values) for values in extras_by_id.values()) != EXPECTED_EXTRA_RECORDS:
        raise NativeVoiceTextError(
            f"expected {EXPECTED_EXTRA_RECORDS} JPN extra translations, found "
            f"{sum(len(values) for values in extras_by_id.values())}"
        )
    if sum(len(values) for values in overrides_by_id.values()) != EXPECTED_CN_OVERRIDES:
        raise NativeVoiceTextError(
            f"expected {EXPECTED_CN_OVERRIDES} CN overrides, found "
            f"{sum(len(values) for values in overrides_by_id.values())}"
        )

    seed = SLOT.CRYPTO.filename_seed(args.eng_key)
    _, target_salts, target_entries = SLOT.decode_key(args.jpn_key, seed)
    _, source_salts, source_entries = SLOT.decode_key(args.eng_key, seed)
    if target_salts != source_salts:
        raise NativeVoiceTextError("Japanese and English SLOT salts differ")
    changed_pages = SLOT.find_changed_pages(args.eng_original_dat, args.cn_dat, source_entries)
    if len(changed_pages) != EXPECTED_CHANGED_PAGES:
        raise NativeVoiceTextError(
            f"expected {EXPECTED_CHANGED_PAGES} patched source pages, found {len(changed_pages)}"
        )

    target_cache: dict[int, tuple[bytes, object, object]] = {}
    source_cache: dict[tuple[str, int], tuple[bytes, object, object]] = {}

    def get_target_page(index: int):
        if index not in target_cache:
            raw, header = SLOT.decode_page(args.base_dat, target_entries[index], target_salts, seed)
            target_cache[index] = (raw, header, SLOT.parse_cnf(raw))
        return target_cache[index]

    def get_source_page(region: str, dat: Path, index: int):
        key = (region, index)
        if key not in source_cache:
            raw, header = SLOT.decode_page(dat, source_entries[index], source_salts, seed)
            source_cache[key] = (raw, header, SLOT.parse_cnf(raw))
        return source_cache[key]

    page_mappings: list[tuple[int, int, object, object, object]] = []
    ypk_sources: dict[str, dict[str, list[bytes]]] = collections.defaultdict(
        lambda: {"eng": [], "cn": []}
    )
    occurrences: list[dict] = []

    for source_page_index in changed_pages:
        _, _, eng_cnf = get_source_page("eng", args.eng_original_dat, source_page_index)
        _, _, cn_cnf = get_source_page("cn", args.cn_dat, source_page_index)
        candidates = [
            index
            for index in range(source_page_index, min(len(target_entries), source_page_index + 3))
            if get_target_page(index)[2].signature == eng_cnf.signature
        ]
        if len(candidates) != 1:
            raise NativeVoiceTextError(
                f"source page {source_page_index} has Japanese target matches {candidates}"
            )
        target_page_index = candidates[0]
        _, _, target_cnf = get_target_page(target_page_index)
        page_mappings.append((source_page_index, target_page_index, eng_cnf, cn_cnf, target_cnf))
        for tag_index, eng_segment in eng_cnf.segments.items():
            cn_segment = cn_cnf.segments[tag_index]
            if eng_segment == cn_segment:
                continue
            tag = eng_cnf.tags[tag_index]
            if tag.kind not in (YPK_KIND, OHD_KIND):
                continue
            file_id = f"{tag.file_id:08X}"
            if tag.kind == YPK_KIND:
                ypk_sources[file_id]["eng"].append(eng_segment)
                ypk_sources[file_id]["cn"].append(cn_segment)
            occurrences.append(
                {
                    "source_page": source_page_index,
                    "target_page": target_page_index,
                    "tag_index": tag_index,
                    "file_id": file_id,
                    "kind": tag.kind,
                    "eng": eng_segment,
                    "cn": cn_segment,
                    "target": target_cnf.segments[tag_index],
                }
            )

    ypk_occurrences = [item for item in occurrences if item["kind"] == YPK_KIND]
    ohd_occurrences = [item for item in occurrences if item["kind"] == OHD_KIND]
    if len(ypk_occurrences) != EXPECTED_YPK_OCCURRENCES:
        raise NativeVoiceTextError(
            f"expected {EXPECTED_YPK_OCCURRENCES} YPK occurrences, found {len(ypk_occurrences)}"
        )
    if len(ohd_occurrences) != EXPECTED_OHD_OCCURRENCES:
        raise NativeVoiceTextError(
            f"expected {EXPECTED_OHD_OCCURRENCES} OHD occurrences, found {len(ohd_occurrences)}"
        )
    if len(ypk_sources) != EXPECTED_UNIQUE_YPK:
        raise NativeVoiceTextError(
            f"expected {EXPECTED_UNIQUE_YPK} unique YPK IDs, found {len(ypk_sources)}"
        )
    if set(extras_by_id) - set(ypk_sources):
        raise NativeVoiceTextError(f"extra translations refer to unknown YPK IDs")
    if set(overrides_by_id) - set(ypk_sources):
        raise NativeVoiceTextError(f"CN overrides refer to unknown YPK IDs")

    rebuilt_ypk: dict[str, bytes] = {}
    ypk_details: list[dict] = []
    total_eng_records = 0
    total_jpn_records = 0
    for file_id in sorted(ypk_sources):
        source_group = ypk_sources[file_id]
        unique_eng = {data for data in source_group["eng"]}
        if len(unique_eng) != 1:
            raise NativeVoiceTextError(f"{file_id}: expected one ENG variant, found {len(unique_eng)}")
        target_variants = {
            item["target"] for item in ypk_occurrences if item["file_id"] == file_id
        }
        if len(target_variants) != 1:
            raise NativeVoiceTextError(f"{file_id}: expected one JPN variant, found {len(target_variants)}")
        cn_variants = sorted(set(source_group["cn"]), key=sha256)
        rebuilt, detail = rebuild_ypk(
            file_id,
            next(iter(target_variants)),
            next(iter(unique_eng)),
            cn_variants,
            extras_by_id.get(file_id, {}),
            overrides_by_id.get(file_id, {}),
        )
        rebuilt_ypk[file_id] = rebuilt
        ypk_details.append(detail)
        total_eng_records += detail["eng_record_count"]
        total_jpn_records += detail["jpn_record_count"]
    if total_eng_records != EXPECTED_ENG_RECORDS or total_jpn_records != EXPECTED_JPN_RECORDS:
        raise NativeVoiceTextError(
            f"unique GTT record totals changed: ENG={total_eng_records}, JPN={total_jpn_records}"
        )

    replacements_by_page: dict[int, dict[int, bytes]] = collections.defaultdict(dict)
    occurrence_details: list[dict] = []
    for item in occurrences:
        file_id = item["file_id"]
        if item["kind"] == YPK_KIND:
            rebuilt = rebuilt_ypk[file_id]
            detail = {
                "mode": "native_jpn_gtt_rebuild",
                "jpn_metadata_source": "record order and JPN-only record headers",
            }
        else:
            rebuilt, ohd_detail = merge_ohd(item["target"], item["cn"], file_id)
            detail = {"mode": "native_jpn_ohd_text_field_merge", **ohd_detail}
        replacements_by_page[item["target_page"]][item["tag_index"]] = rebuilt
        occurrence_details.append(
            {
                "source_page": item["source_page"],
                "target_page": item["target_page"],
                "tag_index": item["tag_index"],
                "file_id": file_id,
                "kind": f"0x{item['kind']:02X}",
                "jpn_segment_sha256": sha256(item["target"]),
                "output_segment_sha256": sha256(rebuilt),
                "output_segment_size": len(rebuilt),
                **detail,
            }
        )

    page_jobs: list[dict] = []
    for page_index in sorted(replacements_by_page):
        target_raw, target_header, target_cnf = get_target_page(page_index)
        merged = SLOT.rebuild_cnf(target_cnf, replacements_by_page[page_index])
        try:
            encoded, compressed_size, compression_strategy = FULL.encode_page_best(
                merged,
                target_header,
                target_entries[page_index].capacity,
                target_salts,
                seed,
                args.zopfli,
            )
        except Exception as error:
            raise NativeVoiceTextError(
                f"native voice-text page {page_index} does not fit fixed Japanese allocation: {error}"
            ) from error
        page_jobs.append(
            {
                "page": page_index,
                "entry": target_entries[page_index],
                "merged": merged,
                "encoded": encoded,
                "compressed_size": compressed_size,
                "compression_strategy": compression_strategy,
                "replacement_count": len(replacements_by_page[page_index]),
            }
        )

    args.output.parent.mkdir(parents=True, exist_ok=True)
    shutil.copyfile(args.base_dat, args.output)
    with args.output.open("r+b") as output:
        for job in page_jobs:
            output.seek(job["entry"].start)
            output.write(job["encoded"])
    if args.output.stat().st_size != args.base_dat.stat().st_size:
        raise NativeVoiceTextError("fixed-layout native SLOT size changed")
    for job in page_jobs:
        round_trip, _ = SLOT.decode_page(args.output, job["entry"], target_salts, seed)
        if round_trip != job["merged"]:
            raise NativeVoiceTextError(f"output round-trip failed on page {job['page']}")

    report = {
        "mode": "native Japanese YPK/OHD text rebuild",
        "base_dat": str(args.base_dat.resolve()),
        "base_sha256": SLOT.sha256_path(args.base_dat),
        "eng_original_dat": str(args.eng_original_dat.resolve()),
        "cn_dat": str(args.cn_dat.resolve()),
        "extra_translations": str(args.extra_translations.resolve()),
        "extra_translations_sha256": SLOT.sha256_path(args.extra_translations),
        "cn_overrides": str(args.cn_overrides.resolve()),
        "cn_overrides_sha256": SLOT.sha256_path(args.cn_overrides),
        "output": str(args.output.resolve()),
        "output_sha256": SLOT.sha256_path(args.output),
        "changed_source_page_count": len(changed_pages),
        "patched_target_page_count": len(page_jobs),
        "ypk_occurrence_count": len(ypk_occurrences),
        "ohd_occurrence_count": len(ohd_occurrences),
        "unique_ypk_count": len(rebuilt_ypk),
        "unique_eng_gtt_record_count": total_eng_records,
        "unique_jpn_gtt_record_count": total_jpn_records,
        "jpn_extra_translation_count": sum(len(values) for values in extras_by_id.values()),
        "cn_override_count": sum(len(values) for values in overrides_by_id.values()),
        "remaining_kana_count": 0,
        "utf8_verified": True,
        "japanese_slot_base_preserved": True,
        "japanese_ohd_metadata_preserved": True,
        "page_offsets_unchanged": True,
        "output_size_growth": 0,
        "round_trip_verified": True,
        "pages": [
            {
                "page": job["page"],
                "offset": job["entry"].start,
                "capacity": job["entry"].capacity,
                "compressed_size": job["compressed_size"],
                "compression_strategy": job["compression_strategy"],
                "replacement_count": job["replacement_count"],
            }
            for job in page_jobs
        ],
        "ypk_files": ypk_details,
        "occurrences": occurrence_details,
    }
    args.report.parent.mkdir(parents=True, exist_ok=True)
    args.report.write_text(json.dumps(report, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    print(
        json.dumps(
            {
                "output": str(args.output.resolve()),
                "output_sha256": report["output_sha256"],
                "patched_pages": report["patched_target_page_count"],
                "ypk_occurrences": report["ypk_occurrence_count"],
                "ohd_occurrences": report["ohd_occurrence_count"],
                "jpn_gtt_records": report["unique_jpn_gtt_record_count"],
                "remaining_kana": 0,
            },
            ensure_ascii=False,
        )
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
