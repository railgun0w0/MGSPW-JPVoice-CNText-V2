#!/usr/bin/env python3
"""Build all JPN-lane YPK/GTT translations into a temporary fixed-layout SLOT.

The source DAT is never modified.  Every YPK occurrence is checked against its
canonical payload, every record is repacked with the existing multi-segment
fixed-frame repacker, and the rebuilt payload is parsed again before any page
is encoded or written.
"""

from __future__ import annotations

import argparse
import csv
import importlib.util
import json
import re
import shutil
import sys
from collections import defaultdict
from pathlib import Path


class BuildError(RuntimeError):
    pass


ANGLE_PATTERN = re.compile(r"<[^<>]*>")
DOLLAR_PATTERN = re.compile(r"\$[A-Za-z0-9_]+")
PRINTF_PATTERN = re.compile(r"%(?:\d+\$)?[sdif]")


def load_module(path: Path, name: str):
    spec = importlib.util.spec_from_file_location(name, path)
    if spec is None or spec.loader is None:
        raise BuildError(f"cannot load helper module: {path}")
    module = importlib.util.module_from_spec(spec)
    sys.modules[name] = module
    spec.loader.exec_module(module)
    return module


def read_translation(path: Path, expected_file_id: str) -> dict[str, str]:
    rows = list(csv.DictReader(path.open("r", encoding="utf-8-sig", newline="")))
    result: dict[str, str] = {}
    for row in rows:
        file_id = row.get("file_id", "").upper()
        if file_id != expected_file_id:
            raise BuildError(f"{path}: row file_id {file_id!r} != {expected_file_id}")
        source = row.get("jpn_text", "")
        target = row.get("cn_text", "")
        if source in result and result[source] != target:
            raise BuildError(f"{path}: conflicting duplicate JPN text")
        if not target:
            raise BuildError(f"{path}: empty cn_text for {source!r}")
        result[source] = target
    if not result:
        raise BuildError(f"{path}: no translation rows")
    return result


def validate_controls(source: str, target: str, label: str) -> None:
    def angle_signature(text: str) -> list[str]:
        signature: list[str] = []
        for token in ANGLE_PATTERN.findall(text):
            if token.startswith("<R="):
                payload = token[3:-1]
                signature.append("RUBY" if "," in payload else "INVALID_RUBY")
            elif token.startswith("<I=") or token.startswith("<C=") or token == "<->":
                signature.append(token)
            elif re.match(r"<[A-Za-z_-]+(?:=|>)", token):
                signature.append(token)
        return signature

    source_signature = angle_signature(source)
    target_signature = angle_signature(target)
    if source_signature != target_signature:
        raise BuildError(
            f"{label}: control/markup mismatch: source={source_signature!r}, "
            f"target={target_signature!r}"
        )
    if sorted(DOLLAR_PATTERN.findall(source)) != sorted(DOLLAR_PATTERN.findall(target)):
        raise BuildError(f"{label}: dollar placeholder inventory mismatch")
    if sorted(PRINTF_PATTERN.findall(source)) != sorted(PRINTF_PATTERN.findall(target)):
        raise BuildError(f"{label}: printf placeholder inventory mismatch")


def parse_args() -> argparse.Namespace:
    root = Path(__file__).resolve().parents[1]
    parent = root.parent
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
        "--translations-dir", type=Path, default=root / "translations" / "ypk_gtt"
    )
    parser.add_argument(
        "--output-dir",
        type=Path,
        default=root / "build" / "readiness" / "ypk_gtt" / "mgspw" / "JPN" / "disc0_rel",
    )
    parser.add_argument(
        "--legacy-tools",
        type=Path,
        default=parent / "JPVoice_CNText_Experimental" / "tools",
    )
    parser.add_argument(
        "--zopfli",
        type=Path,
        default=Path(shutil.which("zopfli")) if shutil.which("zopfli") else None,
        help="optional zopfli executable used only when standard zlib does not fit",
    )
    return parser.parse_args()


def main() -> int:
    args = parse_args()
    root = Path(__file__).resolve().parents[1]
    if args.output_dir.resolve() == args.jpn_dat.resolve():
        raise BuildError("refusing to overwrite clean JPN DAT")
    if args.output_dir.resolve() == args.jpn_key.resolve():
        raise BuildError("invalid output directory")

    sys.path.insert(0, str(root))
    from core.gtt_multi import GttHardOverflow, parse_gtt_multi, repack_gtt_multi

    slot = load_module(args.legacy_tools / "Build-JpnSlot.py", "v2_all_ypk_slot")
    full = load_module(
        args.legacy_tools / "Build-JpnSlotFullOlang.py", "v2_all_ypk_encoder"
    )

    translation_paths = sorted(args.translations_dir.glob("*.csv"))
    if not translation_paths:
        raise BuildError(f"no YPK translation CSVs under {args.translations_dir}")
    translations = {
        path.stem.upper(): read_translation(path, path.stem.upper())
        for path in translation_paths
    }

    seed = slot.CRYPTO.filename_seed(args.jpn_key)
    _, salts, entries = slot.decode_key(args.jpn_key, seed)
    occurrences: dict[int, list[dict]] = defaultdict(list)
    page_cache: dict[int, tuple[bytes, object, object]] = {}

    # Localized JPN SLOT lane is page % 6 == 4.  Decode only that lane.
    for page_index in range(4, len(entries), 6):
        raw, page_header = slot.decode_page(
            args.jpn_dat, entries[page_index], salts, seed
        )
        cnf = slot.parse_cnf(raw)
        page_cache[page_index] = (raw, page_header, cnf)
        for tag_index, segment in cnf.segments.items():
            tag = cnf.tags[tag_index]
            if tag.kind == 0x1C:
                occurrences[tag.file_id].append(
                    {
                        "page": page_index,
                        "tag": tag_index,
                        "raw": raw,
                        "header": page_header,
                        "cnf": cnf,
                        "segment": segment,
                    }
                )

    occurrence_ids = {f"{file_id:08X}" for file_id in occurrences}
    translation_ids = set(translations)
    missing = sorted(translation_ids - occurrence_ids)
    extra = sorted(occurrence_ids - translation_ids)
    if missing:
        raise BuildError(f"translation CSV has no JPN occurrence: {missing}")
    if extra:
        raise BuildError(f"JPN lane has YPK without translation CSV: {extra}")

    rebuilt_by_file: dict[int, bytes] = {}
    file_reports: list[dict] = []
    record_reports: list[dict] = []
    total_records = total_segments = normal_fit = alignment_spill = 0

    # Rebuild each unique canonical payload once, then apply it to all physical occurrences.
    for file_id in sorted(occurrences):
        file_hex = f"{file_id:08X}"
        items = occurrences[file_id]
        canonical = items[0]["segment"]
        differing = [
            [item["page"], item["tag"]]
            for item in items
            if item["segment"] != canonical
        ]
        if differing:
            raise BuildError(f"{file_hex}: noncanonical JPN payload occurrences {differing}")
        records = parse_gtt_multi(canonical, f"JPN {file_hex} canonical")
        rebuilt = bytearray(canonical)
        file_normal = file_spill = 0
        for record in records:
            cn_texts: list[str] = []
            for segment in record.timed_texts:
                if segment.text not in translations[file_hex]:
                    raise BuildError(
                        f"{file_hex} record {record.index} segment {segment.index}: "
                        f"missing exact jpn_text translation"
                    )
                cn_text = translations[file_hex][segment.text]
                validate_controls(
                    segment.text,
                    cn_text,
                    f"{file_hex} record {record.index} segment {segment.index}",
                )
                cn_texts.append(cn_text)
            required = sum(len(text.encode("utf-8")) + 1 for text in cn_texts)
            try:
                result = repack_gtt_multi(record, cn_texts)
            except GttHardOverflow as error:
                raise BuildError(
                    f"{file_hex} record {record.index}: {error}"
                ) from error
            if result.record_size_before != result.record_size_after:
                raise BuildError(f"{file_hex} record {record.index}: record_size changed")
            if result.aligned_size_before != result.aligned_size_after:
                raise BuildError(f"{file_hex} record {record.index}: aligned_size changed")
            rebuilt[record.offset : record.offset + record.aligned_size] = result.data
            fit = "NORMAL_FIT" if required <= record.nominal_capacity else "ALIGNMENT_SPILL"
            if fit == "NORMAL_FIT":
                normal_fit += 1
                file_normal += 1
            else:
                alignment_spill += 1
                file_spill += 1
            record_reports.append(
                {
                    "file_id": file_hex,
                    "record_index": record.index,
                    "record_offset": record.offset,
                    "segment_count": record.segment_count,
                    "header_size": record.header_size,
                    "record_size": record.record_size,
                    "aligned_size": record.aligned_size,
                    "required": required,
                    "nominal_capacity": record.nominal_capacity,
                    "aligned_capacity": record.aligned_capacity,
                    "fit": fit,
                }
            )

        rebuilt_bytes = bytes(rebuilt)
        round_trip = parse_gtt_multi(rebuilt_bytes, f"rebuilt {file_hex}")
        if len(round_trip) != len(records):
            raise BuildError(f"{file_hex}: record count changed on round-trip")
        for before, after in zip(records, round_trip):
            expected = [translations[file_hex][segment.text] for segment in before.timed_texts]
            if before.offset != after.offset:
                raise BuildError(f"{file_hex} record {before.index}: offset changed")
            if (
                before.segment_count != after.segment_count
                or before.header_size != after.header_size
                or before.record_size != after.record_size
                or before.aligned_size != after.aligned_size
            ):
                raise BuildError(f"{file_hex} record {before.index}: fixed structure changed")
            if list(after.texts) != expected:
                raise BuildError(f"{file_hex} record {before.index}: text round-trip mismatch")
            if not all(
                old.header.flag == new.header.flag
                and old.header.timing_a == new.header.timing_a
                and old.header.timing_b == new.header.timing_b
                for old, new in zip(before.timed_texts, after.timed_texts)
            ):
                raise BuildError(f"{file_hex} record {before.index}: timing/style metadata changed")
        rebuilt_by_file[file_id] = rebuilt_bytes
        total_records += len(records)
        total_segments += sum(record.segment_count for record in records)
        file_reports.append(
            {
                "file_id": file_hex,
                "occurrences": len(items),
                "pages": sorted({item["page"] for item in items}),
                "records": len(records),
                "segments": sum(record.segment_count for record in records),
                "normal_fit": file_normal,
                "alignment_spill": file_spill,
                "ypk_size": len(canonical),
            }
        )

    # Encode all affected CNF pages in memory before writing the output DAT.
    encoded_pages: list[dict] = []
    for page_index, (raw, page_header, cnf) in sorted(page_cache.items()):
        replacements: dict[int, bytes] = {}
        for tag_index, segment in cnf.segments.items():
            tag = cnf.tags[tag_index]
            if tag.kind == 0x1C:
                replacements[tag_index] = rebuilt_by_file[tag.file_id]
        if not replacements:
            continue
        merged = slot.rebuild_cnf(cnf, replacements)
        if len(merged) != len(raw):
            raise BuildError(f"page {page_index}: decoded CNF allocation changed")
        verified = slot.parse_cnf(merged)
        for tag_index, expected in replacements.items():
            if verified.segments[tag_index] != expected:
                raise BuildError(f"page {page_index} tag {tag_index}: YPK replacement mismatch")
        try:
            encoded, compressed_size, strategy = full.encode_page_best(
                merged,
                page_header,
                entries[page_index].capacity,
                salts,
                seed,
                args.zopfli,
            )
        except Exception as error:
            raise BuildError(f"page {page_index}: SLOT block encode overflow: {error}") from error
        if len(encoded) != entries[page_index].capacity:
            raise BuildError(f"page {page_index}: encoded allocation size changed")
        encoded_pages.append(
            {
                "page": page_index,
                "entry_start": entries[page_index].start,
                "tag_count": len(replacements),
                "compressed_size": compressed_size,
                "strategy": strategy,
                "encoded": encoded,
            }
        )

    # Only after all records and page blocks pass validation do we write the temporary build.
    args.output_dir.mkdir(parents=True, exist_ok=True)
    output_dat = args.output_dir / "002aba34.DAT"
    output_key = args.output_dir / "002aba34.KEY"
    shutil.copyfile(args.jpn_dat, output_dat)
    with output_dat.open("r+b") as stream:
        for job in encoded_pages:
            stream.seek(job["entry_start"])
            stream.write(job["encoded"])
    if output_dat.stat().st_size != args.jpn_dat.stat().st_size:
        raise BuildError("temporary DAT size changed")
    shutil.copyfile(args.jpn_key, output_key)

    # Decode every patched page from the written DAT and compare its CNF bytes.
    for job in encoded_pages:
        decoded, _ = slot.decode_page(output_dat, entries[job["page"]], salts, seed)
        if decoded != slot.rebuild_cnf(
            page_cache[job["page"]][2],
            {
                ti: rebuilt_by_file[page_cache[job["page"]][2].tags[ti].file_id]
                for ti in page_cache[job["page"]][2].segments
                if page_cache[job["page"]][2].tags[ti].kind == 0x1C
            },
        ):
            raise BuildError(f"page {job['page']}: written SLOT round-trip mismatch")

    report_path = root / "build" / "readiness" / "ypk_gtt_roundtrip_report.json"
    report_path.parent.mkdir(parents=True, exist_ok=True)
    report = {
        "source_dat": str(args.jpn_dat.resolve()),
        "source_key": str(args.jpn_key.resolve()),
        "output_dat": str(output_dat.resolve()),
        "output_key": str(output_key.resolve()),
        "lane": "page % 6 == 4",
        "unique_ypk": len(rebuilt_by_file),
        "ypk_occurrences": sum(len(items) for items in occurrences.values()),
        "records": total_records,
        "segments": total_segments,
        "normal_fit": normal_fit,
        "alignment_spill": alignment_spill,
        "hard_overflow": 0,
        "patched_pages": len(encoded_pages),
        "block_overflow": 0,
        "files": file_reports,
        "records_detail": record_reports,
        "pages": [
            {key: value for key, value in job.items() if key != "encoded"}
            for job in encoded_pages
        ],
    }
    report_path.write_text(json.dumps(report, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")

    print(f"UNIQUE_YPK={len(rebuilt_by_file)}")
    print(f"YPK_OCCURRENCES={sum(len(items) for items in occurrences.values())}")
    print(f"RECORDS={total_records}")
    print(f"SEGMENTS={total_segments}")
    print(f"NORMAL_FIT={normal_fit}")
    print(f"ALIGNMENT_SPILL={alignment_spill}")
    print("HARD_OVERFLOW=0")
    print(f"PATCHED_PAGES={len(encoded_pages)}")
    print("BLOCK_OVERFLOW=0")
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
