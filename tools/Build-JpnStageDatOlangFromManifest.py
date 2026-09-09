#!/usr/bin/env python3
"""Build translated JPN STAGEDAT OLANG entries from the compiled manifest."""

from __future__ import annotations

import argparse
import csv
import importlib.util
import json
import shutil
import struct
import sys
from collections import defaultdict
from pathlib import Path


V2_ROOT = Path(__file__).resolve().parents[1]
LEGACY_TOOLS = V2_ROOT.parent / "JPVoice_CNText_Experimental" / "tools"
DEFAULT_STAGE = Path(r"D:\GAME\test\JPN\MGS_PW\mgspw\JPN\disc0_rel\009645fa.PDT")
DEFAULT_MANIFEST = V2_ROOT / "build" / "translation" / "compiled_translation_manifest.csv"
DEFAULT_OUTPUT = (
    V2_ROOT
    / "build"
    / "readiness"
    / "stagedat"
    / "mgspw"
    / "JPN"
    / "disc0_rel"
    / "009645fa.PDT"
)


def load_module(path: Path, name: str):
    spec = importlib.util.spec_from_file_location(name, path)
    if spec is None or spec.loader is None:
        raise RuntimeError(f"cannot load helper module: {path}")
    module = importlib.util.module_from_spec(spec)
    sys.modules[name] = module
    spec.loader.exec_module(module)
    return module


STAGE = load_module(LEGACY_TOOLS / "Patch-StageDatPage.py", "v2_stage_manifest_container")
DAR = load_module(LEGACY_TOOLS / "Build-JpnInitCache.py", "v2_stage_manifest_dar")
sys.path.insert(0, str(V2_ROOT))
from core.rbx import parse_rbx, rebuild_rbx_texts, structural_signature  # noqa: E402


def parse_integer(value: str) -> int:
    text = str(value).strip()
    if text.lower().startswith("0x"):
        return int(text, 16)
    if any(character in "abcdefABCDEF" for character in text) or (
        len(text) > 1 and text.startswith("0")
    ):
        return int(text, 16)
    return int(text, 10)


def read_manifest(path: Path) -> list[dict[str, str]]:
    with path.open("r", encoding="utf-8-sig", newline="") as handle:
        rows = [
            row
            for row in csv.DictReader(handle)
            if row.get("resource_class") == "STAGEDAT_OLANG"
            and row.get("translation_status") == "APPROVED"
        ]
    if not rows:
        raise RuntimeError("manifest contains no approved STAGEDAT_OLANG rows")
    return rows


def translated_texts(rows: list[dict[str, str]], parsed, label: str) -> tuple[list[str], set[int]]:
    by_index: dict[int, dict[str, str]] = {}
    for row in rows:
        index = int(row["reference_index"])
        if row.get("object_type") != "reference" or int(row["object_index"]) != index:
            raise RuntimeError(f"{label}: invalid manifest reference identity")
        if index in by_index:
            raise RuntimeError(f"{label}: duplicate reference {index}")
        by_index[index] = row
    language_keys = {parse_integer(row["language_key"]) for row in rows}
    expected = {
        index
        for index, reference in enumerate(parsed.references)
        if reference.text and reference.language_key in language_keys
    }
    if set(by_index) != expected:
        raise RuntimeError(
            f"{label}: incomplete target reference coverage; "
            f"missing={sorted(expected - set(by_index))}, extra={sorted(set(by_index) - expected)}"
        )

    texts = [reference.text for reference in parsed.references]
    for index, row in by_index.items():
        reference = parsed.references[index]
        if row["jpn_text"] != reference.text:
            raise RuntimeError(f"{label}: JPN text mismatch at reference {index}")
        if parse_integer(row["language_key"]) != reference.language_key:
            raise RuntimeError(f"{label}: language key mismatch at reference {index}")
        if parse_integer(row["style"]) != reference.flag:
            raise RuntimeError(f"{label}: style mismatch at reference {index}")
        cn_text = row.get("cn_text", "")
        if not cn_text and reference.text.strip():
            raise RuntimeError(f"{label}: empty translation at reference {index}")
        cn_text.encode("utf-8", errors="strict")
        texts[index] = cn_text if cn_text else reference.text
    return texts, set(by_index)


def entry_map(entries, page: int):
    result = {}
    for index, entry in enumerate(entries):
        key = entry.name.casefold()
        if key in result:
            raise RuntimeError(f"page {page}: duplicate DAR entry name {entry.name}")
        result[key] = (index, entry)
    return result


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--stage", type=Path, default=DEFAULT_STAGE)
    parser.add_argument("--manifest", type=Path, default=DEFAULT_MANIFEST)
    parser.add_argument("--output", type=Path, default=DEFAULT_OUTPUT)
    parser.add_argument(
        "--report",
        type=Path,
        default=V2_ROOT / "build" / "readiness" / "stagedat_structure_report.json",
    )
    args = parser.parse_args()
    if args.output.resolve() == args.stage.resolve():
        raise RuntimeError("refusing to overwrite source STAGEDAT")

    manifest = read_manifest(args.manifest)
    grouped: dict[tuple[int, str], list[dict[str, str]]] = defaultdict(list)
    for row in manifest:
        name = (row.get("archive_entry_name") or row["file_id"]).casefold()
        grouped[(int(row["page"]), name)].append(row)

    seed = STAGE.filename_seed(args.stage)
    encoded_pages: dict[int, bytes] = {}
    page_sizes: dict[int, int] = {}
    expected_pages: dict[int, bytes] = {}
    page_non_target: dict[int, dict[str, bytes]] = {}
    details: list[dict] = []
    overflow_pages: list[dict] = []

    by_page: dict[int, list[tuple[str, list[dict[str, str]]]]] = defaultdict(list)
    for (page, name), rows in grouped.items():
        by_page[page].append((name, rows))

    with args.stage.open("rb") as source:
        header = STAGE.decode_header(source, seed)
        entries, table_plain = STAGE.decode_table(source, seed, header)
        file_size = source.seek(0, 2)
        for page in sorted(by_page):
            if not 0 <= page < len(entries):
                raise RuntimeError(f"manifest page is outside STAGEDAT: {page}")
            decoded = STAGE.decode_page(source, seed, header, entries[page])
            dar_entries = DAR.parse_dar(decoded)
            available = entry_map(dar_entries, page)
            replacements: dict[str, bytes] = {}
            page_non_target[page] = {entry.name.casefold(): entry.data for entry in dar_entries}
            for name, rows in sorted(by_page[page]):
                if name not in available:
                    raise RuntimeError(f"page {page}: missing DAR entry {name}")
                _, entry = available[name]
                parsed = parse_rbx(entry.data, f"page{page}:{entry.name}")
                texts, target_indices = translated_texts(
                    rows, parsed, f"page{page}:{entry.name}"
                )
                rebuilt = rebuild_rbx_texts(parsed, texts, f"page{page}:{entry.name}")
                verified = parse_rbx(rebuilt, f"page{page}:{entry.name}:rebuilt")
                if structural_signature(verified) != structural_signature(parsed):
                    raise RuntimeError(f"page {page}:{entry.name}: structural signature changed")
                for index, (before, after) in enumerate(zip(parsed.references, verified.references)):
                    if index not in target_indices and before.text != after.text:
                        raise RuntimeError(
                            f"page {page}:{entry.name}: non-target reference {index} changed"
                        )
                replacements[name] = rebuilt
                details.append(
                    {
                        "page": page,
                        "entry": entry.name,
                        "file_id": rows[0]["file_id"],
                        "entities": len(parsed.entities),
                        "references": len(parsed.references),
                        "translated_references": len(target_indices),
                        "size_before": len(entry.data),
                        "size_after": len(rebuilt),
                        "structural_signature_identical": True,
                        "non_target_references_identical": True,
                        "text_roundtrip": True,
                    }
                )

            rebuilt_entries = [
                DAR.DarEntry(entry.name, replacements.get(entry.name.casefold(), entry.data))
                for entry in dar_entries
            ]
            rebuilt_page = DAR.build_dar(rebuilt_entries)
            verified_entries = entry_map(DAR.parse_dar(rebuilt_page), page)
            for name, (_, original_entry) in available.items():
                rebuilt_entry = verified_entries[name][1]
                if name not in replacements and rebuilt_entry.data != original_entry.data:
                    raise RuntimeError(f"page {page}: non-target DAR entry {original_entry.name} changed")
                if name in replacements and rebuilt_entry.data != replacements[name]:
                    raise RuntimeError(f"page {page}: target DAR entry {original_entry.name} mismatch")

            encoded, packed_size = STAGE.encode_page(rebuilt_page, seed, header)
            next_offset = entries[page + 1].offset if page + 1 < len(entries) else file_size
            capacity = next_offset - entries[page].offset
            if packed_size > capacity:
                overflow_pages.append(
                    {
                        "page": page,
                        "packed_size": packed_size,
                        "capacity": capacity,
                        "overflow": packed_size - capacity,
                    }
                )
            encoded_pages[page] = encoded
            page_sizes[page] = packed_size
            expected_pages[page] = rebuilt_page

    report = {
        "status": "BLOCK_OVERFLOW" if overflow_pages else "PASS",
        "input": str(args.stage),
        "output": None if overflow_pages else str(args.output),
        "page_count": header.page_count,
        "patched_pages": len(encoded_pages),
        "patched_entries": len(details),
        "translated_references": sum(item["translated_references"] for item in details),
        "block_overflow": len(overflow_pages),
        "overflow_pages": overflow_pages,
        "entries": details,
    }
    args.report.parent.mkdir(parents=True, exist_ok=True)
    if overflow_pages:
        args.report.write_text(json.dumps(report, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
        print(f"PATCHED_PAGES={len(encoded_pages)}")
        print(f"PATCHED_ENTRIES={len(details)}")
        print(f"TRANSLATED_REFERENCES={report['translated_references']}")
        print(f"BLOCK_OVERFLOW={len(overflow_pages)}")
        print(f"REPORT={args.report}")
        return 2

    modified_table = bytearray(table_plain)
    for page, packed_size in page_sizes.items():
        entry = entries[page]
        struct.pack_into("<III", modified_table, page * 12, packed_size, entry.key, entry.offset)
    encoded_table = STAGE.encode_table(bytes(modified_table), seed, header)
    args.output.parent.mkdir(parents=True, exist_ok=True)
    temporary = args.output.with_name(args.output.name + ".tmp")
    shutil.copyfile(args.stage, temporary)
    with temporary.open("r+b") as output:
        output.seek(40)
        output.write(encoded_table)
        for page, encoded in encoded_pages.items():
            output.seek(entries[page].offset)
            output.write(encoded)
    temporary.replace(args.output)

    if args.output.stat().st_size != args.stage.stat().st_size:
        raise RuntimeError("STAGEDAT output size changed")
    output_seed = STAGE.filename_seed(args.output)
    if output_seed != seed:
        raise RuntimeError("STAGEDAT output filename seed changed")
    with args.output.open("rb") as output:
        verified_header = STAGE.decode_header(output, output_seed)
        verified_table, _ = STAGE.decode_table(output, output_seed, verified_header)
        for index, (before, after) in enumerate(zip(entries, verified_table)):
            if (before.key, before.offset) != (after.key, after.offset):
                raise RuntimeError(f"page {index}: STAGEDAT table key/offset changed")
            expected_size = page_sizes.get(index, before.size)
            if after.size != expected_size:
                raise RuntimeError(f"page {index}: STAGEDAT table size mismatch")
        for page, expected in expected_pages.items():
            actual = STAGE.decode_page(output, output_seed, verified_header, verified_table[page])
            if actual != expected:
                raise RuntimeError(f"page {page}: STAGEDAT decode-back mismatch")
            original_entries = page_non_target[page]
            rebuilt_entries = entry_map(DAR.parse_dar(actual), page)
            target_names = {name for name, _ in by_page[page]}
            for name, original_data in original_entries.items():
                if name not in target_names and rebuilt_entries[name][1].data != original_data:
                    raise RuntimeError(f"page {page}: non-target DAR payload changed after output")

    args.report.write_text(json.dumps(report, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    print(f"PATCHED_PAGES={len(encoded_pages)}")
    print(f"PATCHED_ENTRIES={len(details)}")
    print(f"TRANSLATED_REFERENCES={report['translated_references']}")
    print("BLOCK_OVERFLOW=0")
    print(f"OUTPUT={args.output}")
    print(f"REPORT={args.report}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
