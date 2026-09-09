#!/usr/bin/env python3
"""Freeze the accepted 1C79F2AD original/rebuilt YPK golden fixture."""

from __future__ import annotations

import hashlib
import importlib.util
import json
import sys
from pathlib import Path


FILE_ID = 0x1C79F2AD


def load_module(path: Path, name: str):
    spec = importlib.util.spec_from_file_location(name, path)
    if spec is None or spec.loader is None:
        raise RuntimeError(f"cannot load helper: {path}")
    module = importlib.util.module_from_spec(spec)
    sys.modules[name] = module
    spec.loader.exec_module(module)
    return module


def find_payloads(slot, dat_path: Path, key_path: Path):
    seed = slot.CRYPTO.filename_seed(key_path)
    _, salts, entries = slot.decode_key(key_path, seed)
    found = []
    for page in range(4, len(entries), 6):
        raw, _ = slot.decode_page(dat_path, entries[page], salts, seed)
        cnf = slot.parse_cnf(raw)
        for tag, payload in cnf.segments.items():
            if cnf.tags[tag].file_id == FILE_ID:
                found.append((page, tag, payload))
    return found


def main() -> int:
    root = Path(__file__).resolve().parents[1]
    project_parent = root.parent
    sys.path.insert(0, str(root))
    from core.gtt_multi import parse_gtt_multi, repack_gtt_multi

    slot = load_module(
        project_parent / "JPVoice_CNText_Experimental" / "tools" / "Build-JpnSlot.py",
        "freeze_gtt_slot",
    )
    original_dat = Path(r"D:\GAME\test\JPN\MGS_PW\mgspw\JPN\disc0_rel\002aba34.DAT")
    key = Path(r"D:\GAME\test\JPN\MGS_PW\mgspw\JPN\disc0_rel\002aba34.KEY")
    rebuilt_dat = (
        root
        / "build"
        / "test_1C79F2AD"
        / "mgspw"
        / "JPN"
        / "disc0_rel"
        / "002aba34.DAT"
    )
    translations = json.loads(
        (root / "translations" / "1C79F2AD_cn.json").read_text(encoding="utf-8")
    )["records"]
    fixture = root / "tests" / "fixtures" / "gtt_1C79F2AD"
    fixture.mkdir(parents=True, exist_ok=True)

    originals = find_payloads(slot, original_dat, key)
    rebuilt = find_payloads(slot, rebuilt_dat, key)
    if [(p, t) for p, t, _ in originals] != [(p, t) for p, t, _ in rebuilt]:
        raise RuntimeError("original/rebuilt occurrence locations differ")
    if not originals or len({payload for _, _, payload in originals}) != 1:
        raise RuntimeError("original occurrences are not one canonical payload")
    if len({payload for _, _, payload in rebuilt}) != 1:
        raise RuntimeError("rebuilt occurrences are not byte-identical")
    original_payload = originals[0][2]
    rebuilt_payload = rebuilt[0][2]
    old_records = parse_gtt_multi(original_payload, "golden original")
    new_records = parse_gtt_multi(rebuilt_payload, "golden rebuilt")
    if len(old_records) != len(translations) or len(new_records) != len(translations):
        raise RuntimeError("golden record count mismatch")

    normal = spill = segments = 0
    for old, new, texts in zip(old_records, new_records, translations):
        expected = repack_gtt_multi(old, texts)
        actual = rebuilt_payload[new.offset : new.offset + new.aligned_size]
        if expected.data != actual:
            raise RuntimeError(f"record {old.index}: rebuilt bytes differ from repacker")
        if list(new.texts) != texts:
            raise RuntimeError(f"record {old.index}: text round-trip mismatch")
        segments += old.segment_count
        if expected.required <= old.nominal_capacity:
            normal += 1
        else:
            spill += 1

    original_path = fixture / "1C79F2AD_jpn_original.ypk"
    rebuilt_path = fixture / "1C79F2AD_cn_golden.ypk"
    expected_path = fixture / "expected.json"
    original_path.write_bytes(original_payload)
    rebuilt_path.write_bytes(rebuilt_payload)
    expected_path.write_text(
        json.dumps(
            {
                "file_id": f"{FILE_ID:08X}",
                "occurrences": [
                    {"page": page, "tag": tag} for page, tag, _ in originals
                ],
                "records": len(old_records),
                "segments": segments,
                "normal_fit": normal,
                "alignment_spill": spill,
                "hard_overflow": 0,
                "record_0_boundaries": [list(x) for x in new_records[0].boundaries],
                "record_0_texts": list(new_records[0].texts),
                "record_52_required": sum(
                    len(text.encode("utf-8")) + 1 for text in translations[52]
                ),
                "record_52_nominal_capacity": old_records[52].nominal_capacity,
                "record_52_hard_capacity": old_records[52].aligned_capacity,
                "original_sha256": hashlib.sha256(original_payload).hexdigest().upper(),
                "rebuilt_sha256": hashlib.sha256(rebuilt_payload).hexdigest().upper(),
            },
            ensure_ascii=False,
            indent=2,
        )
        + "\n",
        encoding="utf-8",
    )
    print(f"FIXTURE_PATH={fixture.resolve()}")
    print(f"RECORDS={len(old_records)}")
    print(f"SEGMENTS={segments}")
    print(f"NORMAL_FIT={normal}")
    print(f"ALIGNMENT_SPILL={spill}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
