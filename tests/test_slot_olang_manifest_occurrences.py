from __future__ import annotations

import importlib.util
import sys
import unittest
from pathlib import Path
from types import SimpleNamespace


ROOT = Path(__file__).resolve().parents[1]
BUILDER_PATH = ROOT / "tools" / "Build-JpnSlotOlangFromManifest.py"
SPEC = importlib.util.spec_from_file_location("slot_olang_manifest_builder_test", BUILDER_PATH)
if SPEC is None or SPEC.loader is None:
    raise RuntimeError(f"cannot load {BUILDER_PATH}")
BUILDER = importlib.util.module_from_spec(SPEC)
sys.modules[SPEC.name] = BUILDER
SPEC.loader.exec_module(BUILDER)


class SlotOlangManifestOccurrenceTest(unittest.TestCase):
    def test_canonical_bindings_expand_to_every_physical_occurrence(self) -> None:
        rows = [
            {
                "file_id": "5D0A5DB1",
                "page": "28",
                "tag_index": "6",
                "reference_index": str(index),
                "occurrence_count": "3",
                "occurrence_locations": "28:6;40:3;58:2",
            }
            for index in range(5)
        ]

        targets = BUILDER.expand_manifest_targets(rows, entry_count=100)

        self.assertEqual(
            set(targets),
            {(28, 6, 0x5D0A5DB1), (40, 3, 0x5D0A5DB1), (58, 2, 0x5D0A5DB1)},
        )
        for bound_rows, canonical_page, canonical_tag in targets.values():
            self.assertEqual(bound_rows, rows)
            self.assertEqual((canonical_page, canonical_tag), (28, 6))

    def test_occurrence_count_mismatch_is_rejected(self) -> None:
        rows = [
            {
                "file_id": "5D0A5DB1",
                "page": "28",
                "tag_index": "6",
                "occurrence_count": "2",
                "occurrence_locations": "28:6;40:3;58:2",
            }
        ]

        with self.assertRaisesRegex(RuntimeError, "occurrence count mismatch"):
            BUILDER.expand_manifest_targets(rows, entry_count=100)

    def test_empty_jpn_references_are_preserved_without_manifest_rows(self) -> None:
        parsed = SimpleNamespace(
            references=(
                SimpleNamespace(text="", language_key=3504, flag=1026),
                SimpleNamespace(text="戦闘再開", language_key=3504, flag=1026),
                SimpleNamespace(text="", language_key=3504, flag=1026),
            )
        )
        rows = [
            {
                "object_type": "reference",
                "object_index": "1",
                "reference_index": "1",
                "jpn_text": "戦闘再開",
                "language_key": "3504",
                "style": "1026",
                "cn_text": "恢复战斗",
            }
        ]

        self.assertEqual(
            BUILDER.validate_group(rows, parsed, "empty-reference fixture"),
            ["", "恢复战斗", ""],
        )

    def test_missing_non_empty_jpn_reference_is_rejected(self) -> None:
        parsed = SimpleNamespace(
            references=(SimpleNamespace(text="戦闘再開", language_key=3504, flag=1026),)
        )

        with self.assertRaisesRegex(RuntimeError, "missing=\\[0\\]"):
            BUILDER.validate_group([], parsed, "missing-reference fixture")


if __name__ == "__main__":
    unittest.main()
