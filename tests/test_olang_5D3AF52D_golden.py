from __future__ import annotations

import csv
import hashlib
import json
import unittest
from pathlib import Path

from core.rbx import parse_rbx, rebuild_rbx_texts, structural_signature


ROOT = Path(__file__).resolve().parents[1]
FIXTURE = ROOT / "tests" / "fixtures" / "olang_5D3AF52D"


class Olang5D3AF52DGoldenTest(unittest.TestCase):
    def test_full_rbx_matches_accepted_metadata_preserving_rebuild(self) -> None:
        expected = json.loads((FIXTURE / "expected.json").read_text(encoding="utf-8"))
        original_bytes = (FIXTURE / "5D3AF52D_jpn_original.rbx").read_bytes()
        rebuilt_bytes = (FIXTURE / "5D3AF52D_cn_golden.rbx").read_bytes()
        self.assertEqual(hashlib.sha256(original_bytes).hexdigest().upper(), expected["original_sha256"])
        self.assertEqual(hashlib.sha256(rebuilt_bytes).hexdigest().upper(), expected["rebuilt_sha256"])

        original = parse_rbx(original_bytes, "golden original")
        rebuilt = parse_rbx(rebuilt_bytes, "golden rebuilt")
        self.assertEqual(len(original.entities), 118)
        self.assertEqual(len(original.references), 118)
        self.assertEqual(len(rebuilt.entities), 118)
        self.assertEqual(len(rebuilt.references), 118)
        self.assertEqual(original.entities, rebuilt.entities)
        self.assertEqual(structural_signature(original), structural_signature(rebuilt))
        self.assertEqual(structural_signature(original), expected["structural_signature"])

        translation_path = ROOT / "translations" / "slot_olang" / "5D3AF52D.csv"
        with translation_path.open("r", encoding="utf-8-sig", newline="") as stream:
            rows = list(csv.DictReader(stream))
        self.assertEqual(len(rows), 110)
        by_reference = {}
        for row in rows:
            self.assertEqual(row["translation_status"], "APPROVED")
            self.assertEqual(row["ingame_status"], "PASS")
            for index in row["reference_indices"].split(";"):
                self.assertNotIn(int(index), by_reference)
                by_reference[int(index)] = row["cn_text"]
        self.assertEqual(set(by_reference), set(range(118)))
        texts = [by_reference[index] for index in range(118)]
        rebuilt_again = rebuild_rbx_texts(original, texts, "golden test")
        rebuilt_again += bytes((-len(rebuilt_again)) % 16)
        self.assertEqual(rebuilt_again, rebuilt_bytes)
        self.assertEqual([reference.text for reference in rebuilt.references], texts)
        self.assertEqual(
            [(reference.language_key, reference.flag) for reference in original.references],
            [(reference.language_key, reference.flag) for reference in rebuilt.references],
        )


if __name__ == "__main__":
    unittest.main()
