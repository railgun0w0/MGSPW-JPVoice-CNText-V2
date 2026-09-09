from __future__ import annotations

import struct
import unittest

from core.rbx import RbxFormatError, parse_rbx, rebuild_rbx_texts, structural_signature


def make_rbx_with_empty_reference() -> bytes:
    raw = bytearray(32)
    raw[:4] = b"RBX\x00"
    struct.pack_into("<IIII", raw, 16, 32, 32, 40, 64)
    raw.extend(struct.pack("<IHH", 7, 0, 2))
    raw.extend(struct.pack("<III", 3504, 0, 1026))
    raw.extend(struct.pack("<III", 3504, 2, 1026))
    raw.extend(b"\x00\x00JP\x00")
    return bytes(raw)


class RbxEmptyReferenceTest(unittest.TestCase):
    def test_original_empty_reference_round_trips_while_text_is_translated(self) -> None:
        original = parse_rbx(make_rbx_with_empty_reference(), "empty fixture")
        rebuilt_raw = rebuild_rbx_texts(original, ["", "中文"], "empty fixture")
        rebuilt = parse_rbx(rebuilt_raw, "empty fixture rebuilt")

        self.assertEqual([reference.text for reference in rebuilt.references], ["", "中文"])
        self.assertEqual(original.entities, rebuilt.entities)
        self.assertEqual(structural_signature(original), structural_signature(rebuilt))

    def test_non_empty_reference_cannot_be_cleared(self) -> None:
        original = parse_rbx(make_rbx_with_empty_reference(), "empty fixture")

        with self.assertRaisesRegex(RbxFormatError, "clears a non-empty reference"):
            rebuild_rbx_texts(original, ["", ""], "empty fixture")


if __name__ == "__main__":
    unittest.main()
