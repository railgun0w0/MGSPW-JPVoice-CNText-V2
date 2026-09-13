#!/usr/bin/env python3
"""Transplant all mapped Chinese English-slot OLANG text into Japanese SLOT records."""

from __future__ import annotations

import argparse
import collections
import hashlib
import importlib.util
import json
import re
import shutil
import struct
import subprocess
import sys
import tempfile
import zlib
from pathlib import Path


def load_module(filename: str, name: str):
    path = Path(__file__).with_name(filename)
    spec = importlib.util.spec_from_file_location(name, path)
    if spec is None or spec.loader is None:
        raise RuntimeError(f"cannot load helper module: {path}")
    module = importlib.util.module_from_spec(spec)
    sys.modules[name] = module
    spec.loader.exec_module(module)
    return module


SLOT = load_module("Build-JpnSlot.py", "mgspw_slot_full")
RBX = load_module("Build-JpnInitCache.py", "mgspw_rbx_full")


class FullMergeError(RuntimeError):
    pass


KANA_PATTERN = re.compile(r"[\u3040-\u30ff\uff66-\uff9f]")


def structural_signature(parsed) -> str:
    packed = bytearray(struct.pack("<II", len(parsed.entities), len(parsed.references)))
    for entity in parsed.entities:
        packed.extend(struct.pack("<IHH", entity.key, entity.reference_index, entity.reference_count))
    for reference in parsed.references:
        packed.extend(struct.pack("<I", reference.flag))
    return hashlib.sha256(packed).hexdigest().upper()


def rebuild_with_texts(parsed, texts: list[str], label: str) -> bytes:
    if len(texts) != len(parsed.references):
        raise FullMergeError(f"{label}: replacement text count mismatch")
    body = bytearray()
    offsets: dict[bytes, int] = {}
    relative_offsets: list[int] = []
    for text in texts:
        encoded = text.encode("utf-8")
        if encoded not in offsets:
            offsets[encoded] = len(body)
            body.extend(encoded)
            body.append(0)
            if len(body) % 2:
                body.append(0)
        relative_offsets.append(offsets[encoded])
    output = bytearray(parsed.raw[: parsed.reference_offset])
    for reference, relative in zip(parsed.references, relative_offsets):
        output.extend(struct.pack("<III", reference.language_key, relative, reference.flag))
    if len(output) != parsed.body_offset:
        raise FullMergeError(f"{label}: rebuilt reference table does not meet body offset")
    output.extend(body)
    rebuilt = bytes(output)
    verified = RBX.parse_rbx(rebuilt, f"{label}:rebuilt")
    if [reference.text for reference in verified.references] != texts:
        raise FullMergeError(f"{label}: rebuilt text round-trip failed")
    if rebuilt[: parsed.reference_offset] != parsed.raw[: parsed.reference_offset]:
        raise FullMergeError(f"{label}: target header/entity data changed")
    if [(r.language_key, r.flag) for r in verified.references] != [
        (r.language_key, r.flag) for r in parsed.references
    ]:
        raise FullMergeError(f"{label}: target reference metadata changed")
    return rebuilt


def encode_page_best(data, template, capacity, salts, seed, zopfli_path):
    candidates: list[tuple[str, bytes]] = [("zlib.compress-9", zlib.compress(data, level=9))]
    strategies = (
        ("default-mem9", zlib.Z_DEFAULT_STRATEGY),
        ("filtered-mem9", zlib.Z_FILTERED),
        ("rle-mem9", zlib.Z_RLE),
        ("huffman-mem9", zlib.Z_HUFFMAN_ONLY),
        ("fixed-mem9", zlib.Z_FIXED),
    )
    for name, strategy in strategies:
        compressor = zlib.compressobj(9, zlib.DEFLATED, 15, 9, strategy)
        compressed = compressor.compress(data) + compressor.flush()
        candidates.append((name, compressed))
    if min(len(candidate) + 16 for _, candidate in candidates) > capacity and zopfli_path is not None:
        with tempfile.TemporaryDirectory(prefix="mgspw-zopfli-") as work:
            input_path = Path(work) / "page.bin"
            input_path.write_bytes(data)
            process = subprocess.run(
                [str(zopfli_path), "--zlib", "--i15", "-c", str(input_path)],
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                check=False,
            )
            if process.returncode != 0:
                raise FullMergeError(
                    f"zopfli failed with exit {process.returncode}: "
                    f"{process.stderr.decode(errors='replace')}"
                )
            try:
                if zlib.decompress(process.stdout) != data:
                    raise FullMergeError("zopfli output round-trip mismatch")
            except zlib.error as error:
                raise FullMergeError(f"zopfli did not return a zlib stream: {error}") from error
            candidates.append(("zopfli-i15", process.stdout))
    name, compressed = min(candidates, key=lambda item: len(item[1]))
    plain = struct.pack(
        "<HHIII",
        template.unknown_a,
        template.unknown_b,
        template.padding,
        len(compressed),
        len(data),
    ) + compressed
    if len(plain) > capacity:
        sizes = ", ".join(f"{candidate_name}={len(candidate) + 16}" for candidate_name, candidate in candidates)
        raise FullMergeError(f"best rebuilt page needs {len(plain)} bytes but capacity is {capacity}; {sizes}")
    plain += bytes(capacity - len(plain))
    inner, _ = SLOT.CRYPTO.inner_transform(
        plain,
        SLOT.CRYPTO.initial_inner_key(*salts[:2]),
        SLOT.CRYPTO.inner_key_b(*salts),
    )
    return SLOT.CRYPTO.outer_transform(inner, seed, 0), len(compressed), name


def merge_semantic_partial(target_data: bytes, source_data: bytes, label: str) -> tuple[bytes, dict]:
    target = RBX.parse_rbx(target_data, f"{label}:target")
    source = RBX.parse_rbx(source_data, f"{label}:source")
    target_ids = RBX.entity_identities(target.entities)
    source_ids = RBX.entity_identities(source.entities)
    source_by_id = {identity: source.entities[index] for index, identity in enumerate(source_ids)}
    candidates: dict[int, set[str]] = collections.defaultdict(set)
    mapped_entities = 0
    skipped_entities = 0
    for target_index, identity in enumerate(target_ids):
        target_entity = target.entities[target_index]
        source_entity = source_by_id.get(identity)
        if source_entity is None or target_entity.reference_count != source_entity.reference_count:
            skipped_entities += 1
            continue
        mapped_entities += 1
        for ordinal in range(target_entity.reference_count):
            candidates[target_entity.reference_index + ordinal].add(
                source.references[source_entity.reference_index + ordinal].text
            )
    conflicts = {index: sorted(texts) for index, texts in candidates.items() if len(texts) != 1}
    if conflicts:
        raise FullMergeError(f"{label}: partial semantic merge has {len(conflicts)} conflicting references")
    texts = [reference.text for reference in target.references]
    for index, choices in candidates.items():
        texts[index] = next(iter(choices))
    mapped_refs = sorted(candidates)
    uncovered = [index for index in range(len(texts)) if index not in candidates]
    rebuilt = rebuild_with_texts(target, texts, label)
    return rebuilt, {
        "mode": "semantic_partial",
        "target_entities": len(target.entities),
        "source_entities": len(source.entities),
        "mapped_entities": mapped_entities,
        "skipped_entities": skipped_entities,
        "target_references": len(target.references),
        "source_references": len(source.references),
        "mapped_reference_indices": mapped_refs,
        "uncovered_reference_indices": uncovered,
    }


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--base-dat", type=Path, required=True)
    parser.add_argument("--jpn-key", type=Path, required=True)
    parser.add_argument("--cn-dat", type=Path, required=True)
    parser.add_argument("--eng-key", type=Path, required=True)
    parser.add_argument("--mapping", type=Path, required=True)
    parser.add_argument("--manual-translations", type=Path, required=True)
    parser.add_argument("--auto-uncovered", type=Path, required=True)
    parser.add_argument("--manual-uncovered", type=Path, required=True)
    parser.add_argument("--final-kana-overrides", type=Path, required=True)
    parser.add_argument("--zopfli", type=Path)
    parser.add_argument("--output", type=Path, required=True)
    parser.add_argument("--report", type=Path, required=True)
    args = parser.parse_args()
    if args.output.resolve() in (args.base_dat.resolve(), args.cn_dat.resolve()):
        parser.error("refusing to overwrite an input SLOT DAT")
    if args.zopfli is not None and not args.zopfli.is_file():
        parser.error(f"zopfli executable not found: {args.zopfli}")

    mapping_doc = json.loads(args.mapping.read_text(encoding="utf-8"))
    manual_doc = json.loads(args.manual_translations.read_text(encoding="utf-8"))
    auto_uncovered_doc = json.loads(args.auto_uncovered.read_text(encoding="utf-8"))
    manual_uncovered_doc = json.loads(args.manual_uncovered.read_text(encoding="utf-8"))
    final_kana_doc = json.loads(args.final_kana_overrides.read_text(encoding="utf-8"))
    mappings = mapping_doc["mappings"]
    if len(mappings) != 742:
        raise FullMergeError(f"expected 742 OLANG mappings, found {len(mappings)}")
    manual_target = manual_doc["target_file_id"]
    manual_overrides = {int(index): text for index, text in manual_doc["reference_overrides"].items()}
    if len(manual_overrides) != 30:
        raise FullMergeError(f"expected 30 manual translations, found {len(manual_overrides)}")
    auto_uncovered = {
        (item["target_page"], item["target_tag_index"], item["reference_index"]): item["text"]
        for item in auto_uncovered_doc["overrides"]
    }
    if len(auto_uncovered) != 9:
        raise FullMergeError(f"expected 9 automatic uncovered overrides, found {len(auto_uncovered)}")
    manual_uncovered: dict[tuple[str, int], str] = {}
    for file_id, references in manual_uncovered_doc["translations"].items():
        for reference_index, text in references.items():
            manual_uncovered[(file_id, int(reference_index))] = text
    if len(manual_uncovered) != 145:
        raise FullMergeError(f"expected 145 manual uncovered translations, found {len(manual_uncovered)}")
    final_kana_overrides: dict[str, str] = {}
    final_kana_expected: collections.Counter[str] = collections.Counter()
    for item in final_kana_doc["overrides"]:
        source = item["source"]
        translation = item["translation"]
        if source in final_kana_overrides:
            raise FullMergeError(f"duplicate final kana override source: {source!r}")
        if not KANA_PATTERN.search(source):
            raise FullMergeError(f"final kana override source has no kana: {source!r}")
        if KANA_PATTERN.search(translation):
            raise FullMergeError(f"final kana override translation still has kana: {translation!r}")
        expected_occurrences = item["expected_occurrences"]
        if not isinstance(expected_occurrences, int) or expected_occurrences <= 0:
            raise FullMergeError(f"invalid expected occurrence count for {source!r}")
        final_kana_overrides[source] = translation
        final_kana_expected[source] = expected_occurrences
    if len(final_kana_overrides) != final_kana_doc["expected_unique_count"]:
        raise FullMergeError(
            "final kana override unique-count mismatch: "
            f"expected {final_kana_doc['expected_unique_count']}, found {len(final_kana_overrides)}"
        )
    if sum(final_kana_expected.values()) != final_kana_doc["expected_occurrence_count"]:
        raise FullMergeError(
            "final kana override occurrence-count mismatch: "
            f"expected {final_kana_doc['expected_occurrence_count']}, "
            f"configured {sum(final_kana_expected.values())}"
        )

    seed = SLOT.CRYPTO.filename_seed(args.eng_key)
    _, target_salts, target_entries = SLOT.decode_key(args.jpn_key, seed)
    _, source_salts, source_entries = SLOT.decode_key(args.eng_key, seed)
    if target_salts != source_salts:
        raise FullMergeError("Japanese and English SLOT salts differ")

    target_pages: dict[int, tuple[bytes, object, object]] = {}
    source_pages: dict[int, tuple[bytes, object, object]] = {}

    def get_page(cache, dat, entries, salts, index):
        if index not in cache:
            raw, header = SLOT.decode_page(dat, entries[index], salts, seed)
            cache[index] = (raw, header, SLOT.parse_cnf(raw))
        return cache[index]

    replacements_by_page: dict[int, dict[int, bytes]] = collections.defaultdict(dict)
    mapping_details: list[dict] = []
    total_target_refs = 0
    total_source_refs = 0
    total_mapped_refs = 0
    total_changed_refs = 0
    total_manual_refs = 0
    total_auto_uncovered_refs = 0
    total_manual_uncovered_refs = 0
    total_final_kana_override_refs = 0
    used_auto_uncovered: set[tuple[int, int, int]] = set()
    used_manual_uncovered: set[tuple[str, int]] = set()
    used_final_kana_overrides: collections.Counter[str] = collections.Counter()
    remaining_uncovered: list[dict] = []
    merge_mode_counts: collections.Counter[str] = collections.Counter()

    for mapping in mappings:
        target_page_index = mapping["target_page"]
        source_page_index = mapping["source_page"]
        _, _, target_cnf = get_page(target_pages, args.base_dat, target_entries, target_salts, target_page_index)
        _, _, source_cnf = get_page(source_pages, args.cn_dat, source_entries, source_salts, source_page_index)
        target_tag_index = mapping["target_tag_index"]
        source_tag_index = mapping["source_tag_index"]
        target_tag = target_cnf.tags[target_tag_index]
        source_tag = source_cnf.tags[source_tag_index]
        if f"0x{target_tag.file_id:08X}" != mapping["target_file_id"]:
            raise FullMergeError(f"target file-ID mismatch at {target_page_index}:{target_tag_index}")
        if f"0x{source_tag.file_id:08X}" != mapping["source_file_id"]:
            raise FullMergeError(f"source file-ID mismatch at {source_page_index}:{source_tag_index}")
        target_segment = target_cnf.segments[target_tag_index]
        source_segment = source_cnf.segments[source_tag_index]
        target_parsed = RBX.parse_rbx(target_segment, f"target {mapping['target_file_id']}")
        source_parsed = RBX.parse_rbx(source_segment, f"source {mapping['source_file_id']}")
        if structural_signature(target_parsed) != mapping["target_structural_signature"]:
            raise FullMergeError(f"target structural signature mismatch for {mapping['target_file_id']}")
        if structural_signature(source_parsed) != mapping["source_structural_signature"]:
            raise FullMergeError(f"source structural signature mismatch for {mapping['source_file_id']}")
        label = f"{mapping['target_file_id']}<-{mapping['source_file_id']}"
        try:
            rebuilt, strict_detail = RBX.merge_rbx(target_segment, source_segment, label)
            detail = {
                "mode": "semantic_strict",
                "target_references": len(target_parsed.references),
                "source_references": len(source_parsed.references),
                "mapped_reference_indices": list(range(len(target_parsed.references))),
                "uncovered_reference_indices": [],
                "strict_detail": strict_detail,
            }
        except Exception:
            rebuilt, detail = merge_semantic_partial(target_segment, source_segment, label)
        texts = [reference.text for reference in RBX.parse_rbx(rebuilt, f"{label}:merged").references]
        if mapping["target_file_id"] == manual_target:
            if mapping["mode"] != "partial_manual":
                raise FullMergeError("manual target is not marked partial_manual in mapping")
            for index, text in manual_overrides.items():
                if not 0 <= index < len(texts):
                    raise FullMergeError(f"manual reference index is out of range: {index}")
                texts[index] = text
            rebuilt = rebuild_with_texts(target_parsed, texts, label + ":manual")
            detail["manual_reference_indices"] = sorted(manual_overrides)
            detail["uncovered_reference_indices"] = [
                index for index in detail["uncovered_reference_indices"] if index not in manual_overrides
            ]
            total_manual_refs += len(manual_overrides)
        supplemental_auto: list[int] = []
        supplemental_manual: list[int] = []
        uncovered_before_supplement = set(detail["uncovered_reference_indices"])
        for index in sorted(uncovered_before_supplement):
            auto_key = (target_page_index, target_tag_index, index)
            manual_key = (mapping["target_file_id"], index)
            if auto_key in auto_uncovered:
                texts[index] = auto_uncovered[auto_key]
                supplemental_auto.append(index)
                used_auto_uncovered.add(auto_key)
            elif manual_key in manual_uncovered:
                texts[index] = manual_uncovered[manual_key]
                supplemental_manual.append(index)
                used_manual_uncovered.add(manual_key)
        if supplemental_auto or supplemental_manual:
            rebuilt = rebuild_with_texts(target_parsed, texts, label + ":supplemental")
            resolved = set(supplemental_auto) | set(supplemental_manual)
            detail["uncovered_reference_indices"] = [
                index for index in detail["uncovered_reference_indices"] if index not in resolved
            ]
            total_auto_uncovered_refs += len(supplemental_auto)
            total_manual_uncovered_refs += len(supplemental_manual)
        final_kana_override_indices: list[int] = []
        for index, text in enumerate(texts):
            if text not in final_kana_overrides:
                continue
            texts[index] = final_kana_overrides[text]
            final_kana_override_indices.append(index)
            used_final_kana_overrides[text] += 1
        if final_kana_override_indices:
            rebuilt = rebuild_with_texts(target_parsed, texts, label + ":final-kana")
            total_final_kana_override_refs += len(final_kana_override_indices)
        original_texts = [reference.text for reference in target_parsed.references]
        verified = RBX.parse_rbx(rebuilt, f"{label}:final")
        final_texts = [reference.text for reference in verified.references]
        remaining_kana_indices = [
            index for index, text in enumerate(final_texts) if KANA_PATTERN.search(text)
        ]
        if remaining_kana_indices:
            raise FullMergeError(
                f"{label}: {len(remaining_kana_indices)} Japanese-slot references still contain kana: "
                f"{remaining_kana_indices[:20]}"
            )
        changed_indices = [index for index, (before, after) in enumerate(zip(original_texts, final_texts)) if before != after]
        rebuilt += bytes((-len(rebuilt)) % 16)
        replacements_by_page[target_page_index][target_tag_index] = rebuilt
        mapped_count = len(detail["mapped_reference_indices"])
        uncovered = detail["uncovered_reference_indices"]
        total_target_refs += len(target_parsed.references)
        total_source_refs += len(source_parsed.references)
        total_mapped_refs += mapped_count
        total_changed_refs += len(changed_indices)
        merge_mode_counts[detail["mode"]] += 1
        if uncovered:
            remaining_uncovered.append(
                {
                    "target_file_id": mapping["target_file_id"],
                    "target_page": target_page_index,
                    "target_tag_index": target_tag_index,
                    "reference_indices": uncovered,
                }
            )
        mapping_details.append(
            {
                **mapping,
                "merge_mode": detail["mode"],
                "mapped_references": mapped_count,
                "changed_references": len(changed_indices),
                "manual_references": len(detail.get("manual_reference_indices", [])),
                "auto_uncovered_references": supplemental_auto,
                "manual_uncovered_references": supplemental_manual,
                "final_kana_override_references": final_kana_override_indices,
                "uncovered_references": uncovered,
                "output_segment_size": len(rebuilt),
            }
        )

    page_jobs: list[dict] = []
    if used_auto_uncovered != set(auto_uncovered):
        unused = sorted(set(auto_uncovered) - used_auto_uncovered)
        raise FullMergeError(f"unused automatic uncovered overrides: {unused}")
    if used_manual_uncovered != set(manual_uncovered):
        unused = sorted(set(manual_uncovered) - used_manual_uncovered)
        raise FullMergeError(f"unused manual uncovered translations: {unused[:20]}")
    if used_final_kana_overrides != final_kana_expected:
        mismatches = {
            source: {
                "expected": final_kana_expected[source],
                "actual": used_final_kana_overrides[source],
            }
            for source in sorted(set(final_kana_expected) | set(used_final_kana_overrides))
            if final_kana_expected[source] != used_final_kana_overrides[source]
        }
        raise FullMergeError(
            "final kana override occurrence mismatch: "
            + json.dumps(mismatches, ensure_ascii=False)
        )
    for page_index in sorted(replacements_by_page):
        target_raw, target_header, target_cnf = target_pages[page_index]
        merged = SLOT.rebuild_cnf(target_cnf, replacements_by_page[page_index])
        try:
            encoded, compressed_size, compression_strategy = encode_page_best(
                merged,
                target_header,
                target_entries[page_index].capacity,
                target_salts,
                seed,
                args.zopfli,
            )
        except Exception as error:
            full_size = len(zlib.compress(merged, level=9)) + 16
            leave_one_out = []
            for tag_index in replacements_by_page[page_index]:
                reduced_replacements = dict(replacements_by_page[page_index])
                reduced_replacements.pop(tag_index)
                reduced = SLOT.rebuild_cnf(target_cnf, reduced_replacements)
                reduced_size = len(zlib.compress(reduced, level=9)) + 16
                leave_one_out.append(
                    {
                        "tag_index": tag_index,
                        "file_id": f"0x{target_cnf.tags[tag_index].file_id:08X}",
                        "reduced_size": reduced_size,
                        "savings": full_size - reduced_size,
                    }
                )
            diagnostic = json.dumps(
                sorted(leave_one_out, key=lambda item: item["savings"], reverse=True)[:6],
                ensure_ascii=False,
            )
            raise FullMergeError(
                f"fixed-layout full OLANG page {page_index} cannot fit "
                f"{len(replacements_by_page[page_index])} replacements: {error}; "
                f"leave-one-out={diagnostic}"
            ) from error
        page_jobs.append(
            {
                "page": page_index,
                "entry": target_entries[page_index],
                "merged": merged,
                "encoded": encoded,
                "compressed_size": compressed_size,
                "compression_strategy": compression_strategy,
                "capacity": target_entries[page_index].capacity,
                "replacement_count": len(replacements_by_page[page_index]),
            }
        )

    args.output.parent.mkdir(parents=True, exist_ok=True)
    shutil.copyfile(args.base_dat, args.output)
    with args.output.open("r+b") as output:
        for job in page_jobs:
            output.seek(job["entry"].start)
            output.write(job["encoded"])
    if args.output.stat().st_size != args.base_dat.stat().st_size:
        raise FullMergeError("fixed-layout full OLANG SLOT size changed")
    for job in page_jobs:
        round_trip, _ = SLOT.decode_page(args.output, job["entry"], target_salts, seed)
        if round_trip != job["merged"]:
            raise FullMergeError(f"output round-trip failed on page {job['page']}")

    report = {
        "mode": "full Japanese-slot OLANG semantic migration",
        "base_dat": str(args.base_dat.resolve()),
        "base_sha256": SLOT.sha256_path(args.base_dat),
        "cn_dat": str(args.cn_dat.resolve()),
        "cn_sha256": SLOT.sha256_path(args.cn_dat),
        "mapping": str(args.mapping.resolve()),
        "mapping_sha256": SLOT.sha256_path(args.mapping),
        "manual_translations": str(args.manual_translations.resolve()),
        "manual_translations_sha256": SLOT.sha256_path(args.manual_translations),
        "output": str(args.output.resolve()),
        "output_sha256": SLOT.sha256_path(args.output),
        "mapping_count": len(mappings),
        "patched_page_count": len(page_jobs),
        "target_reference_count": total_target_refs,
        "source_reference_count": total_source_refs,
        "mapped_reference_count": total_mapped_refs,
        "changed_reference_count": total_changed_refs,
        "manual_reference_count": total_manual_refs,
        "auto_uncovered_reference_count": total_auto_uncovered_refs,
        "manual_uncovered_reference_count": total_manual_uncovered_refs,
        "final_kana_override_unique_count": len(final_kana_overrides),
        "final_kana_override_reference_count": total_final_kana_override_refs,
        "remaining_kana_reference_count": 0,
        "remaining_uncovered_count": sum(len(item["reference_indices"]) for item in remaining_uncovered),
        "remaining_uncovered": remaining_uncovered,
        "merge_mode_counts": dict(sorted(merge_mode_counts.items())),
        "page_offsets_unchanged": True,
        "output_size_growth": 0,
        "round_trip_verified": True,
        "pages": [
            {
                "page": job["page"],
                "offset": job["entry"].start,
                "capacity": job["capacity"],
                "compressed_size": job["compressed_size"],
                "compression_strategy": job["compression_strategy"],
                "replacement_count": job["replacement_count"],
            }
            for job in page_jobs
        ],
        "mappings": mapping_details,
    }
    args.report.parent.mkdir(parents=True, exist_ok=True)
    args.report.write_text(json.dumps(report, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    print(
        json.dumps(
            {key: report[key] for key in (
                "output_sha256",
                "mapping_count",
                "patched_page_count",
                "target_reference_count",
                "mapped_reference_count",
                "changed_reference_count",
                "manual_reference_count",
                "auto_uncovered_reference_count",
                "manual_uncovered_reference_count",
                "final_kana_override_unique_count",
                "final_kana_override_reference_count",
                "remaining_kana_reference_count",
                "remaining_uncovered_count",
                "merge_mode_counts",
                "output_size_growth",
            )},
            ensure_ascii=False,
        )
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
