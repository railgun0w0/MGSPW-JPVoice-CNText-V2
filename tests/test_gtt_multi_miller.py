from __future__ import annotations

import os
import struct
import unittest
from pathlib import Path

from core.gtt_multi import align_up, parse_gtt_multi, repack_gtt_multi


EXPECTED_TEXTS = (
    "こちらミラー スネーク 聞こえるか？",
    "無事<R=上陸,ランディング>したな",
    "俺達にとって大いなる一歩だ",
)

CN_TEXTS = (
    "我是Miller。听得到吗，Snake？",
    "看来你已经着陆了。",
    "这对我们来说是一大步。",
)


def miller_ypk_path() -> Path:
    configured = os.environ.get("MGSPW_MILLER_YPK")
    if configured:
        return Path(configured)
    test_root = Path(__file__).resolve().parents[3]
    return (
        test_root
        / "MGSPW_GTT_DUMP"
        / "20260902-174047"
        / "01_JPN_ORIGINAL_1C79F2AD.ypk"
    )


class MillerRegressionTest(unittest.TestCase):
    """JPN file_id 1C79F2AD, page 88/tag 14, record 0."""

    def test_record_zero_has_three_complete_timed_texts(self) -> None:
        source = miller_ypk_path()
        self.assertTrue(source.is_file(), f"missing Miller evidence fixture: {source}")

        with source.open("rb") as stream:
            fixed_header = stream.read(16)
            source_record_size = struct.unpack_from("<I", fixed_header, 0x0C)[0]
            stream.seek(0)
            physical_record = stream.read(align_up(source_record_size))
        records = parse_gtt_multi(
            physical_record, "JPN 1C79F2AD page88/tag14"
        )
        self.assertEqual(len(records), 1)
        record = records[0]

        self.assertEqual(record.segment_count, 3)
        self.assertEqual(record.header_size, 96)
        self.assertEqual(record.record_size, 232)
        self.assertEqual(record.nominal_capacity, 136)
        self.assertEqual(record.aligned_capacity, 144)
        self.assertEqual(record.boundaries, ((0, 51), (51, 96), (96, 136)))
        self.assertEqual(record.texts, EXPECTED_TEXTS)

    def test_fixed_layout_chinese_repack(self) -> None:
        source = miller_ypk_path()
        with source.open("rb") as stream:
            fixed_header = stream.read(16)
            source_record_size = struct.unpack_from("<I", fixed_header, 0x0C)[0]
            stream.seek(0)
            physical_record = stream.read(align_up(source_record_size))

        original = parse_gtt_multi(
            physical_record, "JPN 1C79F2AD page88/tag14"
        )[0]
        rebuilt = repack_gtt_multi(original, CN_TEXTS)

        self.assertEqual(rebuilt.old_boundaries, ((0, 51), (51, 96), (96, 136)))
        self.assertEqual(rebuilt.new_boundaries, ((0, 39), (39, 67), (67, 101)))
        self.assertEqual(rebuilt.utf8_lengths_with_nul, (39, 28, 34))
        self.assertEqual(rebuilt.nominal_capacity, 136)
        self.assertEqual(rebuilt.aligned_capacity, 144)
        self.assertEqual(rebuilt.required, 101)
        self.assertEqual(rebuilt.record_size_before, 232)
        self.assertEqual(rebuilt.record_size_after, 232)
        self.assertEqual(rebuilt.aligned_size_before, 240)
        self.assertEqual(rebuilt.aligned_size_after, 240)
        self.assertTrue(rebuilt.non_boundary_header_byte_identical)
        self.assertEqual(
            rebuilt.data[original.header_size + rebuilt.required :],
            bytes(original.aligned_capacity - rebuilt.required),
        )

        round_trip_records = parse_gtt_multi(
            rebuilt.data, "Miller fixed-layout Chinese rebuilt"
        )
        self.assertEqual(len(round_trip_records), 1)
        round_trip = round_trip_records[0]
        self.assertEqual(round_trip.segment_count, original.segment_count)
        self.assertEqual(round_trip.header_size, original.header_size)
        self.assertEqual(round_trip.record_size, original.record_size)
        self.assertEqual(round_trip.aligned_size, original.aligned_size)
        self.assertEqual(round_trip.boundaries, rebuilt.new_boundaries)
        self.assertEqual(round_trip.texts, CN_TEXTS)


if __name__ == "__main__":
    unittest.main()
