#!/usr/bin/env python3
"""Build approved SLOT OLANG translations from explicit JPN object bindings."""

from __future__ import annotations

import argparse
import csv
import hashlib
import importlib.util
import json
import shutil
import sys
from collections import defaultdict
from pathlib import Path


V2_ROOT = Path(__file__).resolve().parents[1]
LEGACY_TOOLS = V2_ROOT.parent / "JPVoice_CNText_Experimental" / "tools"
DEFAULT_DAT = Path(r"D:\GAME\test\JPN\MGS_PW\mgspw\JPN\disc0_rel\002aba34.DAT")
DEFAULT_KEY = Path(r"D:\GAME\test\JPN\MGS_PW\mgspw\JPN\disc0_rel\002aba34.KEY")
DEFAULT_MANIFEST = V2_ROOT / "build" / "translation" / "compiled_translation_manifest.csv"
DEFAULT_OUTPUT_ROOT = V2_ROOT / "build" / "test_slot_olang_manifest" / "mgspw" / "JPN" / "disc0_rel"


def load_module(path: Path, name: str):
    spec = importlib.util.spec_from_file_location(name, path)
    if spec is None or spec.loader is None:
        raise RuntimeError(f"cannot load helper module: {path}")
    module = importlib.util.module_from_spec(spec)
    sys.modules[name] = module
    spec.loader.exec_module(module)
    return module


SLOT = load_module(LEGACY_TOOLS / "Build-JpnSlot.py", "slot_manifest_olang")
FULL = load_module(LEGACY_TOOLS / "Build-JpnSlotFullOlang.py", "full_manifest_olang")
sys.path.insert(0, str(V2_ROOT))
from core.rbx import parse_rbx, rebuild_rbx_texts, structural_signature  # noqa: E402


def parse_integer(value: str) -> int:
    text = str(value).strip()
    if text.lower().startswith("0x"):
        return int(text, 16)
    if any(character in "abcdefABCDEF" for character in text) or (len(text) > 1 and text.startswith("0")):
        return int(text, 16)
    return int(text, 10)


def sha256(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest().upper()


def read_manifest(path: Path, selected_file_ids: set[str]) -> list[dict[str, str]]:
    with path.open("r", encoding="utf-8-sig", newline="") as stream:
        rows = list(csv.DictReader(stream))
    rows = [
        row
        for row in rows
        if row.get("resource_class") == "SLOT_OLANG"
        and row.get("translation_status") == "APPROVED"
        and (not selected_file_ids or row.get("file_id", "").upper() in selected_file_ids)
    ]
    if not rows:
        raise RuntimeError("manifest contains no approved SLOT_OLANG rows in the selected scope")
    return rows


def validate_group(rows: list[dict[str, str]], parsed, label: str) -> list[str]:
    by_index: dict[int, dict[str, str]] = {}
    for row in rows:
        index = int(row["reference_index"])
        if row.get("object_type") != "reference" or int(row["object_index"]) != index:
            raise RuntimeError(f"{label}: manifest object identity is not a reference")
        if index in by_index:
            raise RuntimeError(f"{label}: duplicate reference {index}")
        by_index[index] = row
    target_language_keys = {
        parse_integer(row["language_key"])
        for row in rows
        if row.get("language_key", "").strip()
    }
    expected = {
        index
        for index, reference in enumerate(parsed.references)
        if reference.text
        and (not target_language_keys or reference.language_key in target_language_keys)
    }
    if set(by_index) != expected:
        missing = sorted(expected - set(by_index))
        extra = sorted(set(by_index) - expected)
        raise RuntimeError(
            f"{label}: incomplete non-empty reference coverage; missing={missing}, extra={extra}"
        )

    texts = [reference.text for reference in parsed.references]
    for index, reference in enumerate(parsed.references):
        if index not in by_index:
            continue
        row = by_index[index]
        if row["jpn_text"] != reference.text:
            raise RuntimeError(f"{label}: JPN text mismatch at reference {index}")
        if parse_integer(row["language_key"]) != reference.language_key:
            raise RuntimeError(f"{label}: language key mismatch at reference {index}")
        if parse_integer(row["style"]) != reference.flag:
            raise RuntimeError(f"{label}: reference flag mismatch at reference {index}")
        cn_text = row.get("cn_text", "")
        if not cn_text:
            raise RuntimeError(f"{label}: empty Chinese text at reference {index}")
        cn_text.encode("utf-8", errors="strict")
        texts[index] = cn_text
    return texts


def occurrence_locations(
    rows: list[dict[str, str]], canonical_page: int, canonical_tag: int, label: str
) -> list[tuple[int, int]]:
    raw_values = {row.get("occurrence_locations", "").strip() for row in rows}
    raw_values.discard("")
    if len(raw_values) > 1:
        raise RuntimeError(f"{label}: inconsistent occurrence location lists in manifest")
    if not raw_values:
        return [(canonical_page, canonical_tag)]

    locations: list[tuple[int, int]] = []
    seen: set[tuple[int, int]] = set()
    for item in next(iter(raw_values)).split(";"):
        parts = item.strip().split(":")
        if len(parts) != 2:
            raise RuntimeError(f"{label}: invalid occurrence location {item!r}")
        location = (int(parts[0]), int(parts[1]))
        if location in seen:
            raise RuntimeError(f"{label}: duplicate occurrence location {item!r}")
        seen.add(location)
        locations.append(location)
    if (canonical_page, canonical_tag) not in seen:
        raise RuntimeError(f"{label}: canonical page/tag missing from occurrence list")

    counts = {int(row["occurrence_count"]) for row in rows if row.get("occurrence_count", "").strip()}
    if len(counts) > 1 or (counts and next(iter(counts)) != len(locations)):
        raise RuntimeError(
            f"{label}: occurrence count mismatch; manifest={sorted(counts)}, locations={len(locations)}"
        )
    return locations


def expand_manifest_targets(
    manifest_rows: list[dict[str, str]], entry_count: int
) -> dict[tuple[int, int, int], tuple[list[dict[str, str]], int, int]]:
    grouped: dict[tuple[int, int, int], list[dict[str, str]]] = defaultdict(list)
    for row in manifest_rows:
        grouped[(int(row["page"]), int(row["tag_index"]), int(row["file_id"], 16))].append(row)

    targets: dict[tuple[int, int, int], tuple[list[dict[str, str]], int, int]] = {}
    for (canonical_page, canonical_tag, file_id), rows in grouped.items():
        label = f"{file_id:08X}@{canonical_page}:{canonical_tag}"
        for page, tag_index in occurrence_locations(rows, canonical_page, canonical_tag, label):
            if page >= entry_count:
                raise RuntimeError(f"page {page} is outside KEY entry table")
            target = (page, tag_index, file_id)
            if target in targets:
                raise RuntimeError(f"{label}: physical occurrence is claimed more than once: {page}:{tag_index}")
            targets[target] = (rows, canonical_page, canonical_tag)
    return targets


def build(args) -> dict:
    selected = {value.upper() for value in args.file_id}
    manifest_rows = read_manifest(args.manifest, selected)
    seed = SLOT.CRYPTO.filename_seed(args.key)
    _, salts, entries = SLOT.decode_key(args.key, seed)
    targets = expand_manifest_targets(manifest_rows, len(entries))

    groups_by_page: dict[int, list[tuple[int, int, list[dict[str, str]], int, int]]] = defaultdict(list)
    for (page, tag_index, file_id), (rows, canonical_page, canonical_tag) in targets.items():
        groups_by_page[page].append((tag_index, file_id, rows, canonical_page, canonical_tag))

    encoded_pages: dict[int, bytes] = {}
    source_pages: dict[int, tuple] = {}
    resource_reports = []
    page_reports = []
    for page in sorted(groups_by_page):
        decoded, page_header = SLOT.decode_page(args.dat, entries[page], salts, seed)
        cnf = SLOT.parse_cnf(decoded)
        replacements: dict[int, bytes] = {}
        for tag_index, file_id, rows, canonical_page, canonical_tag in sorted(groups_by_page[page]):
            if tag_index not in cnf.segments or cnf.tags[tag_index].file_id != file_id:
                actual = cnf.tags[tag_index].file_id if tag_index < len(cnf.tags) else None
                raise RuntimeError(
                    f"page {page}/tag {tag_index}: expected {file_id:08X}, found {actual!r}"
                )
            original_segment = cnf.segments[tag_index]
            parsed = parse_rbx(original_segment, f"{file_id:08X}")
            label = f"{file_id:08X}@{page}:{tag_index}"
            texts = validate_group(rows, parsed, label)
            rebuilt_raw = rebuild_rbx_texts(parsed, texts, f"{file_id:08X}")
            rebuilt_segment = rebuilt_raw + bytes((-len(rebuilt_raw)) % 16)
            replacements[tag_index] = rebuilt_segment
            verified = parse_rbx(rebuilt_segment, f"{file_id:08X}:rebuilt")
            resource_reports.append(
                {
                    "file_id": f"{file_id:08X}",
                    "page": page,
                    "tag_index": tag_index,
                    "canonical_page": canonical_page,
                    "canonical_tag_index": canonical_tag,
                    "entities_before": len(parsed.entities),
                    "entities_after": len(verified.entities),
                    "references_before": len(parsed.references),
                    "references_after": len(verified.references),
                    "translated_references": len(rows),
                    "unique_cn_texts": len(set(texts)),
                    "segment_size_before": len(original_segment),
                    "segment_size_after": len(rebuilt_segment),
                    "structural_signature_before": structural_signature(parsed),
                    "structural_signature_after": structural_signature(verified),
                    "header_entity_bytes_identical": rebuilt_raw[: parsed.reference_offset]
                    == original_segment[: parsed.reference_offset],
                    "reference_text_roundtrip": [reference.text for reference in verified.references]
                    == texts,
                    "sha256_before": sha256(original_segment),
                    "sha256_after": sha256(rebuilt_segment),
                }
            )

        rebuilt_page = SLOT.rebuild_cnf(cnf, replacements)
        zopfli = shutil.which("zopfli")
        encrypted, compressed_size, method = FULL.encode_page_best(
            rebuilt_page,
            page_header,
            entries[page].capacity,
            salts,
            seed,
            Path(zopfli) if zopfli else None,
        )
        encoded_pages[page] = encrypted
        source_pages[page] = (decoded, page_header, cnf, set(replacements))
        page_reports.append(
            {
                "page": page,
                "allocation_start": entries[page].start,
                "allocation_capacity": entries[page].capacity,
                "target_tags": sorted(replacements),
                "decoded_size_before": len(decoded),
                "decoded_size_after": len(rebuilt_page),
                "compressed_size_before": page_header.compressed_size,
                "compressed_size_after": compressed_size,
                "compression_method": method,
                "block_overflow": 0,
            }
        )

    args.output_root.mkdir(parents=True, exist_ok=True)
    output_dat = args.output_root / args.dat.name
    output_key = args.output_root / args.key.name
    shutil.copy2(args.dat, output_dat)
    with output_dat.open("r+b") as stream:
        for page in sorted(encoded_pages):
            stream.seek(entries[page].start)
            stream.write(encoded_pages[page])
    shutil.copy2(args.key, output_key)

    for page, (source_decoded, source_header, source_cnf, target_tags) in source_pages.items():
        decoded, header = SLOT.decode_page(output_dat, entries[page], salts, seed)
        cnf = SLOT.parse_cnf(decoded)
        if [(tag.file_id, tag.pad_a, tag.pad_b, tag.kind) for tag in cnf.tags] != [
            (tag.file_id, tag.pad_a, tag.pad_b, tag.kind) for tag in source_cnf.tags
        ]:
            raise RuntimeError(f"page {page}: CNF tag identity/metadata shape changed")
        for tag_index, source_segment in source_cnf.segments.items():
            if tag_index not in target_tags and cnf.segments[tag_index] != source_segment:
                raise RuntimeError(f"page {page}: non-target tag {tag_index} payload changed")
        if (
            header.unknown_a,
            header.unknown_b,
            header.padding,
        ) != (source_header.unknown_a, source_header.unknown_b, source_header.padding):
            raise RuntimeError(f"page {page}: preserved page header metadata changed")

    if output_dat.stat().st_size != args.dat.stat().st_size:
        raise RuntimeError("output DAT size changed")
    if output_key.read_bytes() != args.key.read_bytes():
        raise RuntimeError("output KEY is not byte-identical")
    if not all(
        report["structural_signature_before"] == report["structural_signature_after"]
        and report["header_entity_bytes_identical"]
        and report["reference_text_roundtrip"]
        for report in resource_reports
    ):
        raise RuntimeError("resource structural verification failed")

    report = {
        "status": "PASS",
        "input_dat": str(args.dat),
        "input_key": str(args.key),
        "manifest": str(args.manifest),
        "output_dat": str(output_dat),
        "output_key": str(output_key),
        "resources": resource_reports,
        "pages": page_reports,
        "summary": {
            "resources_built": len({report["file_id"] for report in resource_reports}),
            "physical_occurrences_built": len(resource_reports),
            "manifest_reference_bindings": len(manifest_rows),
            "references_built": sum(report["references_after"] for report in resource_reports),
            "pages_built": len(page_reports),
            "other_resource_payload_changes": 0,
            "block_overflow": 0,
            "dat_size_identical": True,
            "key_byte_identical": True,
        },
    }
    args.report.parent.mkdir(parents=True, exist_ok=True)
    args.report.write_text(json.dumps(report, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    return report


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--dat", type=Path, default=DEFAULT_DAT)
    parser.add_argument("--key", type=Path, default=DEFAULT_KEY)
    parser.add_argument("--manifest", type=Path, default=DEFAULT_MANIFEST)
    parser.add_argument("--file-id", action="append", default=[])
    parser.add_argument("--output-root", type=Path, default=DEFAULT_OUTPUT_ROOT)
    parser.add_argument(
        "--report",
        type=Path,
        default=V2_ROOT / "build" / "test_slot_olang_manifest" / "structure_report.json",
    )
    args = parser.parse_args()
    report = build(args)
    print(f"RESOURCES_BUILT={report['summary']['resources_built']}")
    print(f"PHYSICAL_OCCURRENCES_BUILT={report['summary']['physical_occurrences_built']}")
    print(f"MANIFEST_REFERENCE_BINDINGS={report['summary']['manifest_reference_bindings']}")
    print(f"REFERENCES_BUILT={report['summary']['references_built']}")
    print(f"PAGES_BUILT={report['summary']['pages_built']}")
    print(f"BLOCK_OVERFLOW={report['summary']['block_overflow']}")
    print(f"OUTPUT_DAT={report['output_dat']}")
    print(f"OUTPUT_KEY={report['output_key']}")
    print(f"REPORT={args.report}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
