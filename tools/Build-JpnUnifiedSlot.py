#!/usr/bin/env python3
"""Merge verified SLOT resource builds into one clean-JPN temporary DAT.

The component DATs are treated as independently verified tag-payload sources.
For every changed page this tool extracts only the expected resource kind,
rebuilds the clean JPN CNF once with the union of replacements, and encodes the
page back into its original KEY allocation.
"""

from __future__ import annotations

import argparse
import hashlib
import importlib.util
import json
import shutil
import sys
from collections import defaultdict
from pathlib import Path


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


def sha256(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest().upper()


def tag_shape(cnf) -> list[tuple[int, int, int, int]]:
    return [(tag.file_id, tag.pad_a, tag.pad_b, tag.kind) for tag in cnf.tags]


def read_allocation(path: Path, entry) -> bytes:
    with path.open("rb") as stream:
        stream.seek(entry.start)
        data = stream.read(entry.capacity)
    if len(data) != entry.capacity:
        raise BuildError(f"{path}: truncated page allocation at {entry.start}")
    return data


def parse_args() -> argparse.Namespace:
    root = Path(__file__).resolve().parents[1]
    parent = root.parent
    readiness = root / "build" / "readiness"
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
        "--slot-olang-dat",
        type=Path,
        default=readiness / "slot_olang" / "mgspw" / "JPN" / "disc0_rel" / "002aba34.DAT",
    )
    parser.add_argument(
        "--ypk-gtt-dat",
        type=Path,
        default=readiness / "ypk_gtt" / "mgspw" / "JPN" / "disc0_rel" / "002aba34.DAT",
    )
    parser.add_argument(
        "--ohd-dat",
        type=Path,
        default=readiness / "ohd" / "mgspw" / "JPN" / "disc0_rel" / "002aba34.DAT",
    )
    parser.add_argument(
        "--output-dir",
        type=Path,
        default=readiness / "unified_slot" / "mgspw" / "JPN" / "disc0_rel",
    )
    parser.add_argument(
        "--report",
        type=Path,
        default=readiness / "unified_slot_structure_report.json",
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
    )
    return parser.parse_args()


def main() -> int:
    args = parse_args()
    slot = load_module(args.legacy_tools / "Build-JpnSlot.py", "v2_unified_slot")
    full = load_module(args.legacy_tools / "Build-JpnSlotFullOlang.py", "v2_unified_encoder")

    components = [
        ("SLOT_OLANG", 0x5D, args.slot_olang_dat),
        ("YPK_GTT", 0x1C, args.ypk_gtt_dat),
        ("OHD", 0x1E, args.ohd_dat),
    ]
    paths = [args.jpn_dat, args.jpn_key] + [item[2] for item in components]
    missing = [str(path) for path in paths if not path.is_file()]
    if missing:
        raise BuildError(f"missing input(s): {missing}")
    output_dat = args.output_dir / args.jpn_dat.name
    if output_dat.resolve() == args.jpn_dat.resolve():
        raise BuildError("refusing to overwrite clean JPN DAT")
    clean_size = args.jpn_dat.stat().st_size
    for name, _, path in components:
        if path.stat().st_size != clean_size:
            raise BuildError(f"{name}: component DAT size differs from clean JPN")

    seed = slot.CRYPTO.filename_seed(args.jpn_key)
    _, salts, entries = slot.decode_key(args.jpn_key, seed)
    replacements_by_page: dict[int, dict[int, bytes]] = defaultdict(dict)
    component_changes: dict[str, list[dict]] = defaultdict(list)
    clean_cache: dict[int, tuple[bytes, object, object]] = {}

    for name, expected_kind, component_dat in components:
        for page_index, entry in enumerate(entries):
            if read_allocation(component_dat, entry) == read_allocation(args.jpn_dat, entry):
                continue
            clean_raw, clean_header = slot.decode_page(args.jpn_dat, entry, salts, seed)
            component_raw, component_header = slot.decode_page(component_dat, entry, salts, seed)
            clean_cnf = slot.parse_cnf(clean_raw)
            component_cnf = slot.parse_cnf(component_raw)
            if tag_shape(component_cnf) != tag_shape(clean_cnf):
                raise BuildError(f"{name} page {page_index}: CNF tag identity/metadata changed")
            if set(component_cnf.segments) != set(clean_cnf.segments):
                raise BuildError(f"{name} page {page_index}: CNF segment index set changed")
            changed_tags = [
                index
                for index in clean_cnf.segments
                if component_cnf.segments[index] != clean_cnf.segments[index]
            ]
            if not changed_tags:
                raise BuildError(f"{name} page {page_index}: encoded page differs without payload changes")
            for tag_index in changed_tags:
                tag = clean_cnf.tags[tag_index]
                if tag.kind != expected_kind:
                    raise BuildError(
                        f"{name} page {page_index} tag {tag_index}: "
                        f"unexpected changed kind 0x{tag.kind:02X}"
                    )
                replacement = component_cnf.segments[tag_index]
                existing = replacements_by_page[page_index].get(tag_index)
                if existing is not None and existing != replacement:
                    raise BuildError(
                        f"page {page_index} tag {tag_index}: conflicting component replacements"
                    )
                replacements_by_page[page_index][tag_index] = replacement
                component_changes[name].append(
                    {
                        "page": page_index,
                        "tag_index": tag_index,
                        "file_id": f"{tag.file_id:08X}",
                        "kind": f"0x{tag.kind:02X}",
                        "source_size": len(clean_cnf.segments[tag_index]),
                        "replacement_size": len(replacement),
                        "source_sha256": sha256(clean_cnf.segments[tag_index]),
                        "replacement_sha256": sha256(replacement),
                    }
                )

            reconstructed = slot.rebuild_cnf(
                clean_cnf,
                {index: component_cnf.segments[index] for index in changed_tags},
            )
            if reconstructed != component_raw:
                raise BuildError(
                    f"{name} page {page_index}: component is not reproducible from changed tag payloads"
                )
            if (
                component_header.unknown_a,
                component_header.unknown_b,
                component_header.padding,
            ) != (clean_header.unknown_a, clean_header.unknown_b, clean_header.padding):
                raise BuildError(f"{name} page {page_index}: page header metadata changed")
            clean_cache[page_index] = (clean_raw, clean_header, clean_cnf)

    expected_occurrences = {"SLOT_OLANG": 742, "YPK_GTT": 77, "OHD": 4}
    for name, expected in expected_occurrences.items():
        actual = len(component_changes[name])
        if actual != expected:
            raise BuildError(f"{name}: changed occurrences={actual}, expected={expected}")

    page_jobs: list[dict] = []
    for page_index in sorted(replacements_by_page):
        if page_index not in clean_cache:
            clean_raw, clean_header = slot.decode_page(
                args.jpn_dat, entries[page_index], salts, seed
            )
            clean_cache[page_index] = (
                clean_raw,
                clean_header,
                slot.parse_cnf(clean_raw),
            )
        clean_raw, clean_header, clean_cnf = clean_cache[page_index]
        replacements = replacements_by_page[page_index]
        merged = slot.rebuild_cnf(clean_cnf, replacements)
        verified_cnf = slot.parse_cnf(merged)
        if tag_shape(verified_cnf) != tag_shape(clean_cnf):
            raise BuildError(f"page {page_index}: merged CNF tag identity/metadata changed")
        for tag_index, original in clean_cnf.segments.items():
            expected = replacements.get(tag_index, original)
            if verified_cnf.segments[tag_index] != expected:
                raise BuildError(f"page {page_index} tag {tag_index}: merged payload mismatch")
        try:
            encoded, compressed_size, strategy = full.encode_page_best(
                merged,
                clean_header,
                entries[page_index].capacity,
                salts,
                seed,
                args.zopfli,
            )
        except Exception as error:
            raise BuildError(f"page {page_index}: SLOT block encode overflow: {error}") from error
        if len(encoded) != entries[page_index].capacity:
            raise BuildError(f"page {page_index}: encoded allocation size changed")
        page_jobs.append(
            {
                "page": page_index,
                "entry_start": entries[page_index].start,
                "allocation_capacity": entries[page_index].capacity,
                "changed_tags": sorted(replacements),
                "changed_kinds": sorted({f"0x{clean_cnf.tags[i].kind:02X}" for i in replacements}),
                "decoded_size_before": len(clean_raw),
                "decoded_size_after": len(merged),
                "compressed_size_before": clean_header.compressed_size,
                "compressed_size_after": compressed_size,
                "compression_strategy": strategy,
                "merged": merged,
                "encoded": encoded,
            }
        )

    args.output_dir.mkdir(parents=True, exist_ok=True)
    shutil.copyfile(args.jpn_dat, output_dat)
    with output_dat.open("r+b") as stream:
        for job in page_jobs:
            stream.seek(job["entry_start"])
            stream.write(job["encoded"])
    output_key = args.output_dir / args.jpn_key.name
    shutil.copyfile(args.jpn_key, output_key)

    for job in page_jobs:
        decoded, header = slot.decode_page(output_dat, entries[job["page"]], salts, seed)
        if decoded != job["merged"]:
            raise BuildError(f"page {job['page']}: written SLOT round-trip mismatch")
        clean_header = clean_cache[job["page"]][1]
        if (header.unknown_a, header.unknown_b, header.padding) != (
            clean_header.unknown_a,
            clean_header.unknown_b,
            clean_header.padding,
        ):
            raise BuildError(f"page {job['page']}: written page header metadata changed")

    if output_dat.stat().st_size != clean_size:
        raise BuildError("output DAT size changed")
    if output_key.read_bytes() != args.jpn_key.read_bytes():
        raise BuildError("output KEY is not byte-identical")

    page_report = [
        {key: value for key, value in job.items() if key not in {"merged", "encoded"}}
        for job in page_jobs
    ]
    report = {
        "status": "PASS",
        "source_dat": str(args.jpn_dat.resolve()),
        "source_key": str(args.jpn_key.resolve()),
        "output_dat": str(output_dat.resolve()),
        "output_key": str(output_key.resolve()),
        "components": {
            name: {
                "source_dat": str(path.resolve()),
                "expected_kind": f"0x{kind:02X}",
                "changed_occurrences": len(component_changes[name]),
                "unique_file_ids": len({item["file_id"] for item in component_changes[name]}),
                "changes": component_changes[name],
            }
            for name, kind, path in components
        },
        "pages": page_report,
        "summary": {
            "slot_olang_occurrences": len(component_changes["SLOT_OLANG"]),
            "ypk_gtt_occurrences": len(component_changes["YPK_GTT"]),
            "ohd_occurrences": len(component_changes["OHD"]),
            "changed_tag_occurrences": sum(len(items) for items in component_changes.values()),
            "patched_pages": len(page_jobs),
            "zopfli_pages": sum(job["compression_strategy"] == "zopfli" for job in page_jobs),
            "block_overflow": 0,
            "dat_size_identical": True,
            "key_byte_identical": True,
            "written_roundtrip": True,
        },
    }
    args.report.parent.mkdir(parents=True, exist_ok=True)
    args.report.write_text(json.dumps(report, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")

    print(f"SLOT_OLANG_OCCURRENCES={report['summary']['slot_olang_occurrences']}")
    print(f"YPK_GTT_OCCURRENCES={report['summary']['ypk_gtt_occurrences']}")
    print(f"OHD_OCCURRENCES={report['summary']['ohd_occurrences']}")
    print(f"CHANGED_TAG_OCCURRENCES={report['summary']['changed_tag_occurrences']}")
    print(f"PATCHED_PAGES={report['summary']['patched_pages']}")
    print(f"ZOPFLI_PAGES={report['summary']['zopfli_pages']}")
    print("BLOCK_OVERFLOW=0")
    print(f"DAT_PATH={output_dat.resolve()}")
    print(f"KEY_PATH={output_key.resolve()}")
    print(f"REPORT_PATH={args.report.resolve()}")
    return 0


if __name__ == "__main__":
    try:
        raise SystemExit(main())
    except BuildError as error:
        print(f"ERROR={error}", file=sys.stderr)
        raise SystemExit(1)
