#!/usr/bin/env python3
"""Freeze the accepted 5D3AF52D original/rebuilt SLOT OLANG segments."""

from __future__ import annotations

import csv
import hashlib
import importlib.util
import json
import sys
from pathlib import Path


FILE_ID = 0x5D3AF52D
PAGE = 1864
TAG = 2


def load_module(path: Path, name: str):
    spec = importlib.util.spec_from_file_location(name, path)
    if spec is None or spec.loader is None:
        raise RuntimeError(f"cannot load helper: {path}")
    module = importlib.util.module_from_spec(spec)
    sys.modules[name] = module
    spec.loader.exec_module(module)
    return module


def read_segment(slot, dat: Path, key: Path) -> bytes:
    seed = slot.CRYPTO.filename_seed(key)
    _, salts, entries = slot.decode_key(key, seed)
    decoded, _ = slot.decode_page(dat, entries[PAGE], salts, seed)
    cnf = slot.parse_cnf(decoded)
    if cnf.tags[TAG].file_id != FILE_ID:
        raise RuntimeError(f"expected {FILE_ID:08X} at page {PAGE}/tag {TAG}")
    return cnf.segments[TAG]


def main() -> int:
    root = Path(__file__).resolve().parents[1]
    sys.path.insert(0, str(root))
    from core.rbx import parse_rbx, rebuild_rbx_texts, structural_signature

    slot = load_module(
        root.parent / "JPVoice_CNText_Experimental" / "tools" / "Build-JpnSlot.py",
        "freeze_olang_slot",
    )
    original_dat = Path(r"D:\GAME\test\JPN\MGS_PW\mgspw\JPN\disc0_rel\002aba34.DAT")
    key = Path(r"D:\GAME\test\JPN\MGS_PW\mgspw\JPN\disc0_rel\002aba34.KEY")
    rebuilt_dat = root / "build" / "test_slot_olang_manifest" / "mgspw" / "JPN" / "disc0_rel" / "002aba34.DAT"
    translations_path = root / "translations" / "slot_olang" / "5D3AF52D.csv"
    fixture = root / "tests" / "fixtures" / "olang_5D3AF52D"

    original_segment = read_segment(slot, original_dat, key)
    rebuilt_segment = read_segment(slot, rebuilt_dat, key)
    original = parse_rbx(original_segment, "golden original")
    rebuilt = parse_rbx(rebuilt_segment, "golden rebuilt")
    with translations_path.open("r", encoding="utf-8-sig", newline="") as stream:
        rows = list(csv.DictReader(stream))
    by_reference = {}
    for row in rows:
        for index in row["reference_indices"].split(";"):
            by_reference[int(index)] = row["cn_text"]
    texts = [by_reference[index] for index in range(len(original.references))]
    expected = rebuild_rbx_texts(original, texts, "golden")
    expected += bytes((-len(expected)) % 16)
    if expected != rebuilt_segment:
        raise RuntimeError("rebuilt golden segment differs from core RBX rebuild")
    if [reference.text for reference in rebuilt.references] != texts:
        raise RuntimeError("golden Chinese text round-trip mismatch")

    fixture.mkdir(parents=True, exist_ok=True)
    (fixture / "5D3AF52D_jpn_original.rbx").write_bytes(original_segment)
    (fixture / "5D3AF52D_cn_golden.rbx").write_bytes(rebuilt_segment)
    expected_data = {
        "file_id": f"{FILE_ID:08X}",
        "page": PAGE,
        "tag_index": TAG,
        "entities": len(original.entities),
        "references": len(original.references),
        "unique_jpn_texts": len({reference.text for reference in original.references}),
        "unique_cn_texts": len(set(texts)),
        "original_size": len(original_segment),
        "rebuilt_size": len(rebuilt_segment),
        "structural_signature": structural_signature(original),
        "original_sha256": hashlib.sha256(original_segment).hexdigest().upper(),
        "rebuilt_sha256": hashlib.sha256(rebuilt_segment).hexdigest().upper(),
        "translation_file": "translations/slot_olang/5D3AF52D.csv",
        "ingame_status": "PASS",
    }
    (fixture / "expected.json").write_text(
        json.dumps(expected_data, ensure_ascii=False, indent=2) + "\n", encoding="utf-8"
    )
    print(f"FIXTURE_PATH={fixture}")
    print(f"ENTITIES={len(original.entities)}")
    print(f"REFERENCES={len(original.references)}")
    print(f"UNIQUE_JPN_TEXTS={expected_data['unique_jpn_texts']}")
    print(f"ORIGINAL_SIZE={len(original_segment)}")
    print(f"REBUILT_SIZE={len(rebuilt_segment)}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
