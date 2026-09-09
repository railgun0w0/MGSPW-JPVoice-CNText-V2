#!/usr/bin/env python3
from __future__ import annotations

import hashlib
import json
import struct
from pathlib import Path

from core.gtt_multi import align_up, parse_gtt_multi, repack_gtt_multi
from tests.test_gtt_multi_miller import CN_TEXTS, miller_ypk_path


def sha256(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest().upper()


def main() -> int:
    source = miller_ypk_path()
    with source.open("rb") as stream:
        fixed_header = stream.read(16)
        record_size = struct.unpack_from("<I", fixed_header, 0x0C)[0]
        stream.seek(0)
        original_bytes = stream.read(align_up(record_size))

    original = parse_gtt_multi(
        original_bytes, "JPN 1C79F2AD page88/tag14 record0"
    )[0]
    rebuilt = repack_gtt_multi(original, CN_TEXTS)
    round_trip = parse_gtt_multi(
        rebuilt.data, "Miller fixed-layout Chinese rebuilt"
    )[0]
    if round_trip.texts != CN_TEXTS:
        raise RuntimeError("Miller Chinese round-trip mismatch")

    output_dir = Path(__file__).resolve().parents[1] / "artifacts" / "miller"
    output_dir.mkdir(parents=True, exist_ok=True)
    binary_path = output_dir / "1C79F2AD_page88_tag14_record0_cn_rebuilt.bin"
    report_path = output_dir / "1C79F2AD_page88_tag14_record0_cn_rebuilt.json"
    binary_path.write_bytes(rebuilt.data)

    report = {
        "scope": {
            "file_id": "1C79F2AD",
            "page": 88,
            "tag": 14,
            "record": 0,
        },
        "source": str(source.resolve()),
        "source_physical_record_sha256": sha256(original_bytes),
        "rebuilt_record": str(binary_path.resolve()),
        "rebuilt_record_sha256": sha256(rebuilt.data),
        "old_boundaries": [list(pair) for pair in rebuilt.old_boundaries],
        "new_boundaries": [list(pair) for pair in rebuilt.new_boundaries],
        "texts": [
            {
                "index": index,
                "text": text,
                "utf8_byte_length": len(text.encode("utf-8")),
                "utf8_byte_length_with_nul": rebuilt.utf8_lengths_with_nul[index],
            }
            for index, text in enumerate(CN_TEXTS)
        ],
        "nominal_capacity": rebuilt.nominal_capacity,
        "aligned_capacity": rebuilt.aligned_capacity,
        "required": rebuilt.required,
        "record_size_before": rebuilt.record_size_before,
        "record_size_after": rebuilt.record_size_after,
        "aligned_size_before": rebuilt.aligned_size_before,
        "aligned_size_after": rebuilt.aligned_size_after,
        "non_boundary_header_byte_identical": (
            rebuilt.non_boundary_header_byte_identical
        ),
        "timing_and_non_boundary_header_byte_identical": (
            rebuilt.non_boundary_header_byte_identical
        ),
        "round_trip": {
            "segment_count": round_trip.segment_count,
            "header_size": round_trip.header_size,
            "record_size": round_trip.record_size,
            "aligned_size": round_trip.aligned_size,
            "boundaries": [list(pair) for pair in round_trip.boundaries],
            "texts": list(round_trip.texts),
            "texts_exact": round_trip.texts == CN_TEXTS,
        },
        "dat_written": False,
    }
    report_path.write_text(
        json.dumps(report, ensure_ascii=False, indent=2) + "\n", encoding="utf-8"
    )
    print(json.dumps(report, ensure_ascii=False, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
