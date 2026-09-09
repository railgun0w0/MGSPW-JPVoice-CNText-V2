#!/usr/bin/env python3
"""Build a fixed-layout JPN SLOT test patch for YPK 1C79F2AD only."""

from __future__ import annotations

import argparse
import importlib.util
import json
import re
import shutil
import sys
from collections import defaultdict
from pathlib import Path


TARGET_FILE_ID = 0x1C79F2AD
CONTROL_PATTERN = re.compile(r"<[^<>]*>|\$[A-Za-z0-9_]+")
RUBY_TRANSLATIONS = {
    "<R=上陸,ランディング>": "<R=着陆,LANDING>",
    "<R=操作,アクション>": "<R=操作,ACTION>",
    "<R=自動照準,AUTO AIM>": "<R=自动瞄准,AUTO AIM>",
    "<R=敵兵,ライブターゲット>": "<R=敌兵,LIVE TARGET>",
    "<R=地図,マップ>": "<R=地图,MAP>",
}


class BuildError(RuntimeError):
    pass


def load_module(path: Path, name: str):
    spec = importlib.util.spec_from_file_location(name, path)
    if spec is None or spec.loader is None:
        raise BuildError(f"cannot load helper module: {path}")
    module = importlib.util.module_from_spec(spec)
    sys.modules[name] = module
    spec.loader.exec_module(module)
    return module


def validate_controls(jpn_text: str, cn_text: str) -> None:
    """Keep controls exact except for the reviewed ruby translations above."""
    source = CONTROL_PATTERN.findall(jpn_text)
    target = CONTROL_PATTERN.findall(cn_text)
    if len(source) != len(target):
        raise BuildError(f"control count changed: JPN={source!r}, CN={target!r}")
    for old, new in zip(source, target):
        expected = RUBY_TRANSLATIONS.get(old, old)
        if new != expected:
            raise BuildError(
                f"control token changed unexpectedly: JPN={old!r}, "
                f"expected={expected!r}, CN={new!r}"
            )


def parse_args() -> argparse.Namespace:
    v2_root = Path(__file__).resolve().parents[1]
    project_parent = v2_root.parent
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--jpn-dat",
        type=Path,
        default=Path(r"D:\GAME\test\JPN\MGS_PW\mgspw\JPN\disc0_rel\002aba34.DAT"),
    )
    parser.add_argument(
        "--jpn-key",
        type=Path,
        default=Path(r"D:\GAME\test\JPN\MGS_PW\mgspw\JPN\disc0_rel\002aba34.KEY"),
    )
    parser.add_argument(
        "--translations",
        type=Path,
        default=v2_root / "translations" / "1C79F2AD_cn.json",
    )
    parser.add_argument(
        "--output-dir",
        type=Path,
        default=v2_root / "build" / "test_1C79F2AD" / "mgspw" / "JPN" / "disc0_rel",
    )
    parser.add_argument(
        "--legacy-tools",
        type=Path,
        default=project_parent / "JPVoice_CNText_Experimental" / "tools",
    )
    return parser.parse_args()


def main() -> int:
    args = parse_args()
    v2_root = Path(__file__).resolve().parents[1]
    sys.path.insert(0, str(v2_root))
    from core.gtt_multi import GttHardOverflow, parse_gtt_multi, repack_gtt_multi

    slot = load_module(args.legacy_tools / "Build-JpnSlot.py", "v2_target_slot")
    full = load_module(
        args.legacy_tools / "Build-JpnSlotFullOlang.py", "v2_target_slot_encoder"
    )

    output_dat = args.output_dir / "002aba34.DAT"
    output_key = args.output_dir / "002aba34.KEY"
    report_path = args.output_dir / "1C79F2AD_build_report.json"
    if output_dat.resolve() == args.jpn_dat.resolve():
        raise BuildError("refusing to overwrite the source JPN DAT")
    if output_key.resolve() == args.jpn_key.resolve():
        raise BuildError("refusing to overwrite the source JPN KEY")

    translation_doc = json.loads(args.translations.read_text(encoding="utf-8"))
    if translation_doc.get("file_id", "").upper() != f"{TARGET_FILE_ID:08X}":
        raise BuildError("translation file_id does not match 1C79F2AD")
    cn_records = translation_doc.get("records")
    if not isinstance(cn_records, list):
        raise BuildError("translation records must be a list")

    seed = slot.CRYPTO.filename_seed(args.jpn_key)
    _, salts, entries = slot.decode_key(args.jpn_key, seed)

    occurrences: list[dict] = []
    # JPN localized SLOT lane is page % 6 == 4.  Only that lane is in scope.
    for page_index in range(4, len(entries), 6):
        raw, page_header = slot.decode_page(args.jpn_dat, entries[page_index], salts, seed)
        cnf = slot.parse_cnf(raw)
        for tag_index, segment in cnf.segments.items():
            if cnf.tags[tag_index].file_id == TARGET_FILE_ID:
                occurrences.append(
                    {
                        "page": page_index,
                        "tag": tag_index,
                        "raw": raw,
                        "header": page_header,
                        "cnf": cnf,
                        "segment": segment,
                    }
                )
    if not occurrences:
        raise BuildError("JPN lane contains no physical occurrence of 1C79F2AD")

    canonical = occurrences[0]["segment"]
    differing = [
        (item["page"], item["tag"])
        for item in occurrences
        if item["segment"] != canonical
    ]
    if differing:
        raise BuildError(f"1C79F2AD has noncanonical JPN payload occurrences: {differing}")

    records = parse_gtt_multi(canonical, "JPN 1C79F2AD canonical")
    if len(cn_records) != len(records):
        raise BuildError(
            f"translation record count {len(cn_records)} != JPN record count {len(records)}"
        )

    rebuilt_ypk = bytearray(canonical)
    normal_fit = 0
    alignment_spill = 0
    overflow_details: list[dict] = []
    total_segments = 0
    record_reports: list[dict] = []
    for record, cn_texts in zip(records, cn_records):
        if not isinstance(cn_texts, list) or len(cn_texts) != record.segment_count:
            raise BuildError(
                f"record {record.index}: translation segment count does not match JPN"
            )
        for segment, cn_text in zip(record.timed_texts, cn_texts):
            try:
                validate_controls(segment.text, cn_text)
            except BuildError as error:
                raise BuildError(
                    f"record {record.index} segment {segment.index}: {error}"
                ) from error
        total_segments += record.segment_count
        required = sum(len(text.encode("utf-8")) + 1 for text in cn_texts)
        try:
            result = repack_gtt_multi(record, cn_texts)
        except GttHardOverflow:
            overflow_details.append(
                {
                    "record_index": record.index,
                    "jpn_texts": list(record.texts),
                    "cn_texts": cn_texts,
                    "required": required,
                    "hard_capacity": record.aligned_capacity,
                    "over_bytes": required - record.aligned_capacity,
                }
            )
            continue
        if required <= record.nominal_capacity:
            normal_fit += 1
            fit = "NORMAL_FIT"
        else:
            alignment_spill += 1
            fit = "ALIGNMENT_SPILL"
        rebuilt_ypk[record.offset : record.offset + record.aligned_size] = result.data
        record_reports.append(
            {
                "record_index": record.index,
                "segments": record.segment_count,
                "required": required,
                "nominal_capacity": record.nominal_capacity,
                "hard_capacity": record.aligned_capacity,
                "fit": fit,
            }
        )

    if overflow_details:
        print(json.dumps({"HARD_OVERFLOW_DETAILS": overflow_details}, ensure_ascii=False, indent=2))
        raise BuildError("HARD_OVERFLOW remains; DAT was not written")

    rebuilt_bytes = bytes(rebuilt_ypk)
    round_trip = parse_gtt_multi(rebuilt_bytes, "rebuilt 1C79F2AD")
    if [list(record.texts) for record in round_trip] != cn_records:
        raise BuildError("rebuilt GTT text round-trip mismatch")
    for before, after in zip(records, round_trip):
        if (
            before.segment_count != after.segment_count
            or before.header_size != after.header_size
            or before.record_size != after.record_size
            or before.aligned_size != after.aligned_size
            or before.offset != after.offset
        ):
            raise BuildError(f"record {before.index}: fixed GTT structure changed")

    page_occurrences: dict[int, list[dict]] = defaultdict(list)
    for occurrence in occurrences:
        page_occurrences[occurrence["page"]].append(occurrence)

    encoded_pages: list[tuple[int, object, bytes, int, str]] = []
    block_overflow: list[dict] = []
    for page_index, items in sorted(page_occurrences.items()):
        first = items[0]
        replacements = {item["tag"]: rebuilt_bytes for item in items}
        merged = slot.rebuild_cnf(first["cnf"], replacements)
        if len(merged) != len(first["raw"]):
            raise BuildError(f"page {page_index}: decoded CNF allocation changed")
        verified_cnf = slot.parse_cnf(merged)
        for tag_index in replacements:
            if verified_cnf.segments[tag_index] != rebuilt_bytes:
                raise BuildError(f"page {page_index} tag {tag_index}: YPK replacement mismatch")
        try:
            encoded, compressed_size, strategy = full.encode_page_best(
                merged,
                first["header"],
                entries[page_index].capacity,
                salts,
                seed,
                None,
            )
        except Exception as error:
            block_overflow.append({"page": page_index, "error": str(error)})
            continue
        encoded_pages.append(
            (page_index, entries[page_index], encoded, compressed_size, strategy)
        )

    if block_overflow:
        print(json.dumps({"BLOCK_OVERFLOW_DETAILS": block_overflow}, ensure_ascii=False, indent=2))
        raise BuildError("SLOT block encode overflow; DAT was not written")

    args.output_dir.mkdir(parents=True, exist_ok=True)
    shutil.copyfile(args.jpn_dat, output_dat)
    with output_dat.open("r+b") as stream:
        for _, entry, encoded, _, _ in encoded_pages:
            stream.seek(entry.start)
            stream.write(encoded)
    if output_dat.stat().st_size != args.jpn_dat.stat().st_size:
        raise BuildError("output DAT size changed")
    shutil.copyfile(args.jpn_key, output_key)

    report = {
        "file_id": f"{TARGET_FILE_ID:08X}",
        "records": len(records),
        "segments": total_segments,
        "normal_fit": normal_fit,
        "alignment_spill": alignment_spill,
        "hard_overflow": len(overflow_details),
        "patched_occurrences": len(occurrences),
        "patched_blocks": len(encoded_pages),
        "block_overflow": len(block_overflow),
        "output_dat": str(output_dat.resolve()),
        "output_key": str(output_key.resolve()),
        "blocks": [
            {
                "page": page_index,
                "compressed_size": compressed_size,
                "strategy": strategy,
            }
            for page_index, _, _, compressed_size, strategy in encoded_pages
        ],
        "record_fits": record_reports,
    }
    report_path.write_text(
        json.dumps(report, ensure_ascii=False, indent=2) + "\n", encoding="utf-8"
    )

    print(f"RECORDS={len(records)}")
    print(f"SEGMENTS={total_segments}")
    print(f"NORMAL_FIT={normal_fit}")
    print(f"ALIGNMENT_SPILL={alignment_spill}")
    print(f"HARD_OVERFLOW={len(overflow_details)}")
    print(f"PATCHED_OCCURRENCES={len(occurrences)}")
    print(f"PATCHED_BLOCKS={len(encoded_pages)}")
    print(f"BLOCK_OVERFLOW={len(block_overflow)}")
    print(f"DAT_PATH={output_dat.resolve()}")
    print(f"KEY_PATH={output_key.resolve()}")
    print(f"REPORT_PATH={report_path.resolve()}")
    return 0


if __name__ == "__main__":
    try:
        raise SystemExit(main())
    except BuildError as error:
        print(f"ERROR={error}", file=sys.stderr)
        raise SystemExit(1)
