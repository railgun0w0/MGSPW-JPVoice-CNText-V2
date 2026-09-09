#!/usr/bin/env python3
"""Export one canonical JPN GTT payload per unique voice file_id."""

from __future__ import annotations

import csv
import importlib.util
import sys
from collections import defaultdict
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
EXPERIMENTAL_TOOLS = ROOT.parent / "JPVoice_CNText_Experimental" / "tools"
JPN_DAT = Path(r"D:\GAME\test\JPN\MGS_PW\mgspw\JPN\disc0_rel\002aba34.DAT")
JPN_KEY = Path(r"D:\GAME\test\JPN\MGS_PW\mgspw\JPN\disc0_rel\002aba34.KEY")
OUTPUT = ROOT / "build" / "translation" / "jpn_gtt" / "jpn_gtt_master.csv"

YPK_KIND = 0x1C

FIELDS = (
    "file_id",
    "record_index",
    "segment_index",
    "segment_count",
    "header_size",
    "record_size",
    "aligned_size",
    "timing_start",
    "timing_end",
    "text_start",
    "text_end",
    "text_capacity",
    "jpn_text",
    "cn_text",
)


def load_module(path: Path, name: str):
    spec = importlib.util.spec_from_file_location(name, path)
    if spec is None or spec.loader is None:
        raise RuntimeError(f"cannot load module: {path}")
    module = importlib.util.module_from_spec(spec)
    sys.modules[name] = module
    spec.loader.exec_module(module)
    return module


SLOT = load_module(EXPERIMENTAL_TOOLS / "Build-JpnSlot.py", "jpn_master_slot")
sys.path.insert(0, str(ROOT))
from core.gtt_multi import parse_gtt_multi  # noqa: E402


def main() -> int:
    for path in (JPN_DAT, JPN_KEY):
        if not path.is_file():
            raise FileNotFoundError(path)

    seed = SLOT.CRYPTO.filename_seed(JPN_KEY)
    _, salts, entries = SLOT.decode_key(JPN_KEY, seed)
    canonical: dict[int, tuple[int, int, bytes]] = {}
    occurrences: defaultdict[int, int] = defaultdict(int)

    for page in range(4, len(entries), 6):
        decoded, _ = SLOT.decode_page(JPN_DAT, entries[page], salts, seed)
        cnf = SLOT.parse_cnf(decoded)
        for tag_index, segment in cnf.segments.items():
            tag = cnf.tags[tag_index]
            if tag.kind != YPK_KIND:
                continue
            occurrences[tag.file_id] += 1
            canonical.setdefault(tag.file_id, (page, tag_index, segment))

    rows: list[dict] = []
    for file_id in sorted(canonical):
        page, tag_index, payload = canonical[file_id]
        records = parse_gtt_multi(
            payload, f"JPN canonical {file_id:08X} p{page} t{tag_index}"
        )
        for record in records:
            for timed in record.timed_texts:
                rows.append(
                    {
                        "file_id": f"{file_id:08X}",
                        "record_index": record.index,
                        "segment_index": timed.index,
                        "segment_count": record.segment_count,
                        "header_size": record.header_size,
                        "record_size": record.record_size,
                        "aligned_size": record.aligned_size,
                        "timing_start": timed.header.timing_a,
                        "timing_end": timed.header.timing_b,
                        "text_start": timed.start,
                        "text_end": timed.end,
                        "text_capacity": timed.end - timed.start,
                        "jpn_text": timed.text,
                        "cn_text": "",
                    }
                )

    OUTPUT.parent.mkdir(parents=True, exist_ok=True)
    with OUTPUT.open("w", encoding="utf-8-sig", newline="") as stream:
        writer = csv.DictWriter(stream, fieldnames=FIELDS)
        writer.writeheader()
        writer.writerows(rows)

    print(f"UNIQUE_YPK={len(canonical)}")
    print(f"RECORDS={len({(row['file_id'], row['record_index']) for row in rows})}")
    print(f"SEGMENTS={len(rows)}")
    print(f"CSV_PATH={OUTPUT.resolve()}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
