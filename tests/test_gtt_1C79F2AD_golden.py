from __future__ import annotations

import hashlib
import json
import unittest
from pathlib import Path

from core.gtt_multi import parse_gtt_multi, repack_gtt_multi


ROOT = Path(__file__).resolve().parents[1]
FIXTURE = ROOT / "tests" / "fixtures" / "gtt_1C79F2AD"


class Gtt1C79F2ADGoldenTest(unittest.TestCase):
    def test_full_ypk_matches_accepted_fixed_layout_repack(self) -> None:
        expected = json.loads((FIXTURE / "expected.json").read_text(encoding="utf-8"))
        translations = json.loads(
            (ROOT / "translations" / "1C79F2AD_cn.json").read_text(encoding="utf-8")
        )["records"]
        original_bytes = (FIXTURE / "1C79F2AD_jpn_original.ypk").read_bytes()
        rebuilt_bytes = (FIXTURE / "1C79F2AD_cn_golden.ypk").read_bytes()
        self.assertEqual(
            hashlib.sha256(original_bytes).hexdigest().upper(),
            expected["original_sha256"],
        )
        self.assertEqual(
            hashlib.sha256(rebuilt_bytes).hexdigest().upper(),
            expected["rebuilt_sha256"],
        )

        original = parse_gtt_multi(original_bytes, "golden original")
        rebuilt = parse_gtt_multi(rebuilt_bytes, "golden rebuilt")
        self.assertEqual(len(original), 98)
        self.assertEqual(len(rebuilt), 98)
        self.assertEqual(sum(r.segment_count for r in rebuilt), 123)
        self.assertEqual(len(translations), 98)

        normal = spill = 0
        for old, new, texts in zip(original, rebuilt, translations):
            packed = repack_gtt_multi(old, texts)
            self.assertEqual(
                rebuilt_bytes[new.offset : new.offset + new.aligned_size], packed.data
            )
            self.assertEqual(list(new.texts), texts)
            self.assertEqual(new.offset, old.offset)
            self.assertEqual(new.segment_count, old.segment_count)
            self.assertEqual(new.header_size, old.header_size)
            self.assertEqual(new.record_size, old.record_size)
            self.assertEqual(new.aligned_size, old.aligned_size)
            if packed.required <= old.nominal_capacity:
                normal += 1
            else:
                spill += 1

        self.assertEqual(normal, 97)
        self.assertEqual(spill, 1)
        self.assertEqual(list(rebuilt[0].texts), expected["record_0_texts"])
        self.assertEqual(rebuilt[0].boundaries, tuple(map(tuple, expected["record_0_boundaries"])))
        self.assertEqual(expected["record_52_required"], 29)
        self.assertEqual(expected["record_52_nominal_capacity"], 26)
        self.assertEqual(expected["record_52_hard_capacity"], 40)


if __name__ == "__main__":
    unittest.main()
