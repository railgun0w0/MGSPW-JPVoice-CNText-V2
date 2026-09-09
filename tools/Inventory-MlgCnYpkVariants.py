#!/usr/bin/env python3
"""Read-only record/segment inventory for selected MLG CN YPK variants."""

from __future__ import annotations

import csv
import importlib.util
import json
import sys
from collections import defaultdict
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
EXPERIMENTAL_TOOLS = ROOT.parent / "JPVoice_CNText_Experimental" / "tools"
OUTPUT = ROOT / "build" / "slot_investigation" / "mlg_cn_ypk_variants.csv"

MLG_ORIG_DAT = Path(r"D:\GAME\test\JPN\MGS_PW\mgspw\MLG\disc0_rel\002aba34.DAT")
MLG_KEY = Path(r"D:\GAME\test\JPN\MGS_PW\mgspw\MLG\disc0_rel\002aba34.KEY")
MLG_CN_DAT = Path(
    r"D:\GAME\test\steam 合金装备大师合集2 合金装备和平行者汉化补丁"
    r"\mgspw\MLG\disc0_rel\002aba34.DAT"
)
TARGET_IDS = {
    0x1C767903,
    0x1C0FB1C9,
    0x1CC27647,
    0x1C79F3CB,
    0x1C79F38B,
}

FIELDS = (
    "file_id",
    "page",
    "tag_index",
    "variant_index",
    "original_page",
    "original_tag_index",
    "record_index",
    "record_offset",
    "original_record_offset",
    "segment_count",
    "original_segment_count",
    "cn_segment_count",
    "original_record_size",
    "cn_record_size",
    "original_aligned_size",
    "cn_aligned_size",
    "record_changed",
    "header_changed",
    "payload_changed",
    "original_text",
    "cn_text",
    "text_changed",
    "segment_index",
    "timing_start",
    "timing_end",
    "original_timing_start",
    "original_timing_end",
    "cn_timing_start",
    "cn_timing_end",
    "original_text_start",
    "original_text_end",
    "cn_text_start",
    "cn_text_end",
    "original_segment_text",
    "cn_segment_text",
    "segment_text_changed",
    "original_text_byte_length",
    "cn_text_byte_length",
    "original_terminator_present",
    "cn_terminator_present",
    "original_interior_nul",
    "cn_interior_nul",
)


def load_module(path: Path, name: str):
    spec = importlib.util.spec_from_file_location(name, path)
    if spec is None or spec.loader is None:
        raise RuntimeError(f"cannot load module: {path}")
    module = importlib.util.module_from_spec(spec)
    sys.modules[name] = module
    spec.loader.exec_module(module)
    return module


SLOT = load_module(EXPERIMENTAL_TOOLS / "Build-JpnSlot.py", "mlg_variant_slot")
sys.path.insert(0, str(ROOT))
from core.gtt_multi import parse_gtt_multi  # noqa: E402


def compact_json(value) -> str:
    return json.dumps(value, ensure_ascii=False, separators=(",", ":"))


def collect(dat_path: Path, entries, salts, seed):
    found = defaultdict(list)
    for page in range(0, len(entries), 6):
        decoded, _ = SLOT.decode_page(dat_path, entries[page], salts, seed)
        cnf = SLOT.parse_cnf(decoded)
        for tag_index, payload in cnf.segments.items():
            file_id = cnf.tags[tag_index].file_id
            if file_id in TARGET_IDS:
                found[file_id].append((page, tag_index, payload))
    return found


def variant_index(payload: bytes, variants: list[bytes]) -> int:
    for index, existing in enumerate(variants):
        if payload == existing:
            return index
    variants.append(payload)
    return len(variants) - 1


def main() -> int:
    for path in (MLG_ORIG_DAT, MLG_KEY, MLG_CN_DAT):
        if not path.is_file():
            raise FileNotFoundError(path)

    seed = SLOT.CRYPTO.filename_seed(MLG_KEY)
    _, salts, entries = SLOT.decode_key(MLG_KEY, seed)
    original = collect(MLG_ORIG_DAT, entries, salts, seed)
    chinese = collect(MLG_CN_DAT, entries, salts, seed)

    if set(original) != TARGET_IDS or set(chinese) != TARGET_IDS:
        raise RuntimeError("not all requested file_ids were found in both MLG sources")

    rows: list[dict] = []
    total_variants = 0
    for file_id in sorted(TARGET_IDS):
        original_occurrences = sorted(original[file_id], key=lambda item: (item[0], item[1]))
        baseline_page, baseline_tag, baseline_payload = original_occurrences[0]
        if any(payload != baseline_payload for _, _, payload in original_occurrences[1:]):
            raise RuntimeError(f"original file_id {file_id:08X} has multiple payloads")
        original_records = parse_gtt_multi(
            baseline_payload, f"MLG_ORIG:{file_id:08X}:p{baseline_page}:t{baseline_tag}"
        )

        variants: list[bytes] = []
        occurrences = []
        for page, tag_index, payload in sorted(
            chinese[file_id], key=lambda item: (item[0], item[1])
        ):
            occurrences.append(
                (page, tag_index, payload, variant_index(payload, variants))
            )
        total_variants += len(variants)

        parsed_variants = [
            parse_gtt_multi(payload, f"MLG_CN:{file_id:08X}:variant{index}")
            for index, payload in enumerate(variants)
        ]
        for page, tag_index, _, index in occurrences:
            cn_records = parsed_variants[index]
            if len(cn_records) != len(original_records):
                raise RuntimeError(
                    f"{file_id:08X} variant {index}: record count differs "
                    f"({len(original_records)} != {len(cn_records)})"
                )
            for original_record, cn_record in zip(original_records, cn_records):
                if original_record.index != cn_record.index:
                    raise RuntimeError(f"{file_id:08X}: record index mismatch")
                record_changed = (
                    original_record.header + original_record.aligned_payload
                    != cn_record.header + cn_record.aligned_payload
                )
                original_texts = list(original_record.texts)
                cn_texts = list(cn_record.texts)
                segment_total = max(
                    len(original_record.timed_texts), len(cn_record.timed_texts)
                )
                for segment_index in range(segment_total):
                    original_segment = (
                        original_record.timed_texts[segment_index]
                        if segment_index < len(original_record.timed_texts)
                        else None
                    )
                    cn_segment = (
                        cn_record.timed_texts[segment_index]
                        if segment_index < len(cn_record.timed_texts)
                        else None
                    )
                    original_segment_text = (
                        "" if original_segment is None else original_segment.text
                    )
                    cn_segment_text = "" if cn_segment is None else cn_segment.text
                    row = {
                        "file_id": f"{file_id:08X}",
                        "page": page,
                        "tag_index": tag_index,
                        "variant_index": index,
                        "original_page": baseline_page,
                        "original_tag_index": baseline_tag,
                        "record_index": cn_record.index,
                        "record_offset": cn_record.offset,
                        "original_record_offset": original_record.offset,
                        "segment_count": cn_record.segment_count,
                        "original_segment_count": original_record.segment_count,
                        "cn_segment_count": cn_record.segment_count,
                        "original_record_size": original_record.record_size,
                        "cn_record_size": cn_record.record_size,
                        "original_aligned_size": original_record.aligned_size,
                        "cn_aligned_size": cn_record.aligned_size,
                        "record_changed": record_changed,
                        "header_changed": original_record.header != cn_record.header,
                        "payload_changed": (
                            original_record.aligned_payload != cn_record.aligned_payload
                        ),
                        "original_text": compact_json(original_texts),
                        "cn_text": compact_json(cn_texts),
                        "text_changed": original_texts != cn_texts,
                        "segment_index": segment_index,
                        "timing_start": (
                            "" if cn_segment is None else cn_segment.header.timing_a
                        ),
                        "timing_end": (
                            "" if cn_segment is None else cn_segment.header.timing_b
                        ),
                        "original_timing_start": (
                            "" if original_segment is None else original_segment.header.timing_a
                        ),
                        "original_timing_end": (
                            "" if original_segment is None else original_segment.header.timing_b
                        ),
                        "cn_timing_start": (
                            "" if cn_segment is None else cn_segment.header.timing_a
                        ),
                        "cn_timing_end": (
                            "" if cn_segment is None else cn_segment.header.timing_b
                        ),
                        "original_text_start": (
                            "" if original_segment is None else original_segment.start
                        ),
                        "original_text_end": (
                            "" if original_segment is None else original_segment.end
                        ),
                        "cn_text_start": "" if cn_segment is None else cn_segment.start,
                        "cn_text_end": "" if cn_segment is None else cn_segment.end,
                        "original_segment_text": original_segment_text,
                        "cn_segment_text": cn_segment_text,
                        "segment_text_changed": original_segment_text != cn_segment_text,
                        "original_text_byte_length": (
                            "" if original_segment is None else len(original_segment.text_bytes)
                        ),
                        "cn_text_byte_length": (
                            "" if cn_segment is None else len(cn_segment.text_bytes)
                        ),
                        "original_terminator_present": (
                            "" if original_segment is None else not original_segment.terminator_missing
                        ),
                        "cn_terminator_present": (
                            "" if cn_segment is None else not cn_segment.terminator_missing
                        ),
                        "original_interior_nul": (
                            "" if original_segment is None else original_segment.interior_nul
                        ),
                        "cn_interior_nul": (
                            "" if cn_segment is None else cn_segment.interior_nul
                        ),
                    }
                    rows.append(row)

    OUTPUT.parent.mkdir(parents=True, exist_ok=True)
    with OUTPUT.open("w", encoding="utf-8-sig", newline="") as stream:
        writer = csv.DictWriter(stream, fieldnames=FIELDS)
        writer.writeheader()
        writer.writerows(rows)

    print(f"CSV_PATH={OUTPUT.resolve()}")
    print(f"ROWS={len(rows)}")
    print(f"FILE_IDS={len(TARGET_IDS)}")
    print(f"VARIANTS={total_variants}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
