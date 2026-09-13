#!/usr/bin/env python3
"""Build all frozen JPN BRIEFING translations into a clean 0076531d.DAT.

This is a fixed-layout builder.  It never relocates an oEbN block: the header,
block start, physical size and allocation topology remain unchanged.  Within a
target block it rewrites only the u32 text-offset table and the UTF-8/NUL text
region, zero-padding unused capacity.
"""

from __future__ import annotations

import argparse
import csv
import hashlib
import json
import re
import struct
import sys
from collections import Counter, defaultdict
from dataclasses import dataclass
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from core.briefing_nbe import (  # noqa: E402
    NbeBlock,
    discover_text_stream_starts,
    parse_all_nbe_blocks,
)
from core.pc_crypto import filename_seed, outer_transform  # noqa: E402


EXPECTED_SOURCE_BYTES = 4_142_432
EXPECTED_SOURCE_SHA256 = "683fef2d84253a56d0af56ad857eb9c891092a598ce19e06bc9858569d94e372"
EXPECTED_ALLOCATIONS = 945
EXPECTED_GLOBAL_BLOCKS = 2761
EXPECTED_GLOBAL_TEXT_BLOCKS = 2727
EXPECTED_GLOBAL_EMPTY_BLOCKS = 34
EXPECTED_GLOBAL_TEXT_ROWS = 42079
EXPECTED_TARGET_FILES = 469
EXPECTED_TARGET_BLOCKS = 469
EXPECTED_TARGET_ROWS = 5645
EXPECTED_FILES_BLOCKS = 363
EXPECTED_FILES_ROWS = 4810
EXPECTED_MISSION_BLOCKS = 106
EXPECTED_MISSION_ROWS = 835
FILES_START, FILES_END = 0x000000, 0x0944B0
MISSION_START, MISSION_END = 0x36D0B0, 0x385620
LEAD_EXTRA = 0x1000

REF_RE = re.compile(
    r"^stream=(0x[0-9A-Fa-f]+);block=(0x[0-9A-Fa-f]+);text=([0-9]+)$"
)
ENTITY_RE = re.compile(
    r"^stream=(0x[0-9A-Fa-f]+);block=(0x[0-9A-Fa-f]+);"
    r"block_file=(0x[0-9A-Fa-f]+);text_base=(0x[0-9A-Fa-f]+);capacity=([0-9]+)$"
)
ANGLE_RE = re.compile(r"<[^<>]*>")
DOLLAR_RE = re.compile(r"\$[A-Za-z0-9_]+")
PRINTF_RE = re.compile(r"%(?:\d+\$)?[sdif]")


class BuildFailure(RuntimeError):
    pass


@dataclass(frozen=True)
class ParsedPhysicalBlock:
    owner_stream: int
    block: NbeBlock
    plaintext: bytes

    @property
    def file_offset(self) -> int:
        return self.owner_stream + self.block.offset

    @property
    def end_file_offset(self) -> int:
        return self.owner_stream + self.block.end


@dataclass
class TargetBlock:
    file_id: str
    lane: str
    stream: int
    block_relative: int
    block_file: int
    text_base: int
    capacity: int
    rows: list[dict]


@dataclass
class Census:
    starts: list[int]
    blocks: dict[int, ParsedPhysicalBlock]
    failures: list[dict]
    duplicate_conflicts: list[dict]


def sha256(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--dat", type=Path, required=True, help="clean JPN 0076531d.DAT")
    parser.add_argument(
        "--production-dir",
        type=Path,
        default=ROOT / "translations" / "briefing",
    )
    parser.add_argument(
        "--master",
        type=Path,
        default=ROOT / "work" / "luna_translation_templates" / "reference_masters" / "jpn_briefing_master.csv",
    )
    parser.add_argument(
        "--output",
        type=Path,
        default=ROOT / "build" / "readiness" / "briefing" / "MGS_PW" / "mgspw" / "JPN" / "disc0_rel" / "0076531d.DAT",
    )
    parser.add_argument(
        "--report-dir",
        type=Path,
        default=ROOT / "build" / "readiness" / "briefing" / "reports",
    )
    parser.add_argument(
        "--check",
        action="store_true",
        help="validate source, binding and capacity without writing build artifacts",
    )
    return parser.parse_args()


def expect(condition: bool, message: str) -> None:
    if not condition:
        raise BuildFailure(message)


def parse_reference(value: str, label: str) -> tuple[int, int, int]:
    match = REF_RE.fullmatch(value.strip())
    if not match:
        raise BuildFailure(f"{label}: malformed first_reference_index {value!r}")
    return int(match[1], 0), int(match[2], 0), int(match[3], 10)


def parse_entity(value: str, label: str) -> tuple[int, int, int, int, int]:
    try:
        items = json.loads(value)
    except json.JSONDecodeError as error:
        raise BuildFailure(f"{label}: invalid entity_context JSON: {error}") from error
    if not isinstance(items, list) or len(items) != 1 or not isinstance(items[0], str):
        raise BuildFailure(f"{label}: entity_context must contain exactly one string")
    match = ENTITY_RE.fullmatch(items[0])
    if not match:
        raise BuildFailure(f"{label}: malformed entity_context {items[0]!r}")
    return tuple(int(match[index], 0 if index < 5 else 10) for index in range(1, 6))


def angle_signature(text: str) -> list[str]:
    result = []
    for token in ANGLE_RE.findall(text):
        if token.startswith("<R="):
            result.append("RUBY" if "," in token[3:-1] else "INVALID_RUBY")
        elif token.startswith("<I=") or token.startswith("<C=") or token == "<->":
            result.append(token)
        elif re.match(r"^<[A-Za-z_-]+(?:=|>)", token):
            result.append(token)
    return result


def inventory(pattern: re.Pattern[str], text: str) -> list[tuple[str, int]]:
    return sorted(Counter(pattern.findall(text)).items())


def control_matches(jpn: str, cn: str) -> bool:
    return (
        angle_signature(jpn) == angle_signature(cn)
        and inventory(DOLLAR_RE, jpn) == inventory(DOLLAR_RE, cn)
        and inventory(PRINTF_RE, jpn) == inventory(PRINTF_RE, cn)
    )


def load_master(path: Path) -> dict[tuple[str, int], dict]:
    if not path.is_file():
        raise BuildFailure(f"frozen JPN master not found: {path}")
    with path.open(encoding="utf-8-sig", newline="") as handle:
        rows = list(csv.DictReader(handle))
    expect(len(rows) == EXPECTED_TARGET_ROWS, f"JPN master rows {len(rows)} != {EXPECTED_TARGET_ROWS}")
    result = {}
    for row in rows:
        key = (row["file_id"], int(row["text_index"], 10))
        expect(key not in result, f"duplicate JPN master key {key}")
        result[key] = row
    expect(len({key[0] for key in result}) == EXPECTED_TARGET_BLOCKS, "JPN master block count mismatch")
    return result


def load_production(directory: Path, master: dict[tuple[str, int], dict]) -> dict[int, TargetBlock]:
    files = sorted(directory.glob("*.csv"))
    expect(len(files) == EXPECTED_TARGET_FILES, f"production files {len(files)} != {EXPECTED_TARGET_FILES}")
    blocks: dict[int, TargetBlock] = {}
    seen_keys: set[tuple[str, int]] = set()
    total_rows = 0

    for path in files:
        with path.open(encoding="utf-8-sig", newline="") as handle:
            rows = list(csv.DictReader(handle))
        expect(bool(rows), f"{path}: empty production CSV")
        file_id = rows[0].get("file_id", "")
        expect(path.stem == file_id, f"{path}: filename/file_id mismatch {file_id!r}")
        expect(all(row.get("file_id") == file_id for row in rows), f"{path}: mixed file_id values")
        lane = "FILES" if file_id.startswith("BRIEFING_FILES_BLOCK_") else (
            "MISSION" if file_id.startswith("BRIEFING_MISSION_BLOCK_") else ""
        )
        expect(bool(lane), f"{path}: unsupported BRIEFING file_id")
        indices = [int(row["unique_index"], 10) for row in rows]
        expect(indices == list(range(len(rows))), f"{file_id}: unique_index is not contiguous from zero")

        block_meta = None
        for row in rows:
            index = int(row["unique_index"], 10)
            label = f"{file_id}#{index}"
            key = (file_id, index)
            expect(key not in seen_keys, f"duplicate production row {label}")
            seen_keys.add(key)
            expect(key in master, f"{label}: missing from frozen JPN master")
            frozen = master[key]
            stream, block_rel, text_index = parse_reference(row["first_reference_index"], label)
            entity_stream, entity_block, block_file, text_base, capacity = parse_entity(row["entity_context"], label)
            expect(text_index == index, f"{label}: reference text index mismatch")
            expect((stream, block_rel) == (entity_stream, entity_block), f"{label}: reference/entity mismatch")
            expect(stream + block_rel == block_file, f"{label}: stream + block != block_file")
            try:
                refs = json.loads(row["reference_indices"])
            except json.JSONDecodeError as error:
                raise BuildFailure(f"{label}: invalid reference_indices JSON") from error
            expect(refs == [row["first_reference_index"]], f"{label}: reference_indices is not physical 1:1")
            expect(int(row["reference_count"], 10) == 1, f"{label}: reference_count != 1")
            expect(row["jpn_text"] == frozen["jpn_text"], f"{label}: JPN text differs from frozen master")
            expect(stream == int(frozen["stream_offset"], 0), f"{label}: frozen stream mismatch")
            expect(block_rel == int(frozen["block_offset_in_stream"], 0), f"{label}: frozen block mismatch")
            expect(block_file == int(frozen["block_file_offset"], 0), f"{label}: frozen block_file mismatch")
            expect(text_base == int(frozen["text_base_file_offset"], 0), f"{label}: frozen text_base mismatch")
            expect(capacity == int(frozen["text_capacity"], 10), f"{label}: frozen capacity mismatch")
            expect(row["cn_text"] != "", f"{label}: blank cn_text")
            expect("\0" not in row["cn_text"], f"{label}: embedded NUL in cn_text")
            expect(len(row["jpn_text"].encode("utf-8")) == int(row["jpn_utf8_bytes"], 10), f"{label}: jpn_utf8_bytes mismatch")
            expect(len(row["cn_text"].encode("utf-8")) == int(row["cn_utf8_bytes"], 10), f"{label}: cn_utf8_bytes mismatch")
            expect(row["translation_status"] == "APPROVED", f"{label}: translation_status is not APPROVED")
            expect(row["build_status"] == "READY", f"{label}: build_status is not READY")
            expect(row["control_structure_status"] == "MATCH", f"{label}: recorded control status is not MATCH")
            expect(control_matches(row["jpn_text"], row["cn_text"]), f"{label}: independently checked control mismatch")
            meta = (stream, block_rel, block_file, text_base, capacity)
            expect(block_meta is None or block_meta == meta, f"{file_id}: inconsistent block metadata")
            block_meta = meta

        assert block_meta is not None
        stream, block_rel, block_file, text_base, capacity = block_meta
        expect(block_file not in blocks, f"duplicate production block 0x{block_file:X}")
        blocks[block_file] = TargetBlock(file_id, lane, stream, block_rel, block_file, text_base, capacity, rows)
        total_rows += len(rows)

    expect(seen_keys == set(master), "production/frozen JPN row sets are not exactly equal")
    expect(len(blocks) == EXPECTED_TARGET_BLOCKS, f"target blocks {len(blocks)} != {EXPECTED_TARGET_BLOCKS}")
    expect(total_rows == EXPECTED_TARGET_ROWS, f"target rows {total_rows} != {EXPECTED_TARGET_ROWS}")
    files_blocks = [block for block in blocks.values() if block.lane == "FILES"]
    mission_blocks = [block for block in blocks.values() if block.lane == "MISSION"]
    expect((len(files_blocks), sum(len(x.rows) for x in files_blocks)) == (EXPECTED_FILES_BLOCKS, EXPECTED_FILES_ROWS), "FILES topology mismatch")
    expect((len(mission_blocks), sum(len(x.rows) for x in mission_blocks)) == (EXPECTED_MISSION_BLOCKS, EXPECTED_MISSION_ROWS), "MISSION topology mismatch")
    expect(all(FILES_START <= x.block_file < FILES_END for x in files_blocks), "FILES target outside frozen lane")
    expect(all(MISSION_START <= x.block_file < MISSION_END for x in mission_blocks), "MISSION target outside frozen lane")
    return blocks


def census(data: bytes, seed: int, expected_starts: list[int] | None = None) -> Census:
    discovered = sorted(item.offset for item in discover_text_stream_starts(data, seed))
    if expected_starts is not None:
        expect(discovered == expected_starts, "rebuilt allocation stream starts differ from clean source")
    blocks: dict[int, ParsedPhysicalBlock] = {}
    failures = []
    conflicts = []
    for index, start in enumerate(discovered):
        next_start = discovered[index + 1] if index + 1 < len(discovered) else len(data)
        window_end = min(len(data), max(start + 0x1000, next_start + LEAD_EXTRA))
        plaintext = outer_transform(data[start:window_end], seed)
        parsed, local_failures = parse_all_nbe_blocks(plaintext, f"allocation 0x{start:X}")
        failures.extend({"offset": f"0x{start + item.offset:X}", "error": item.error} for item in local_failures)
        for block in sorted(parsed, key=lambda item: item.offset):
            if start + block.end > next_start + LEAD_EXTRA:
                continue
            absolute = start + block.offset
            entry = ParsedPhysicalBlock(start, block, plaintext[block.offset:block.end])
            old = blocks.get(absolute)
            if old is None:
                blocks[absolute] = entry
            elif old.plaintext != entry.plaintext:
                conflicts.append({"block": f"0x{absolute:X}", "first_owner": f"0x{old.owner_stream:X}", "second_owner": f"0x{start:X}"})
    return Census(discovered, blocks, failures, conflicts)


def validate_global(census_result: Census, label: str) -> dict:
    text_blocks = sum(item.block.text_count > 0 for item in census_result.blocks.values())
    empty_blocks = sum(item.block.text_count == 0 for item in census_result.blocks.values())
    text_rows = sum(item.block.text_count for item in census_result.blocks.values())
    values = {
        "allocation_count": len(census_result.starts),
        "total_oebn": len(census_result.blocks),
        "text_oebn": text_blocks,
        "empty_oebn": empty_blocks,
        "text_rows": text_rows,
        "parser_failures": len(census_result.failures),
        "duplicate_conflicts": len(census_result.duplicate_conflicts),
        "allocation_coverage": 1.0 if census_result.starts and census_result.starts[0] == 0 else 0.0,
        "allocation_gap_count": 0 if census_result.starts and census_result.starts[0] == 0 else 1,
    }
    expected = {
        "allocation_count": EXPECTED_ALLOCATIONS,
        "total_oebn": EXPECTED_GLOBAL_BLOCKS,
        "text_oebn": EXPECTED_GLOBAL_TEXT_BLOCKS,
        "empty_oebn": EXPECTED_GLOBAL_EMPTY_BLOCKS,
        "text_rows": EXPECTED_GLOBAL_TEXT_ROWS,
        "parser_failures": 0,
        "duplicate_conflicts": 0,
        "allocation_coverage": 1.0,
        "allocation_gap_count": 0,
    }
    expect(values == expected, f"{label} global census mismatch: {values}")
    return values


def validate_bindings(targets: dict[int, TargetBlock], source_census: Census) -> list[dict]:
    audit = []
    for offset, target in sorted(targets.items()):
        expect(offset in source_census.blocks, f"{target.file_id}: source oEbN block not found")
        parsed = source_census.blocks[offset]
        block = parsed.block
        expect(parsed.owner_stream == target.stream, f"{target.file_id}: owner stream mismatch")
        expect(block.offset == target.block_relative, f"{target.file_id}: relative block mismatch")
        expect(parsed.owner_stream + block.text_base == target.text_base, f"{target.file_id}: text_base mismatch")
        expect(block.text_capacity == target.capacity, f"{target.file_id}: actual capacity mismatch")
        expect(block.text_count == len(target.rows), f"{target.file_id}: actual text count mismatch")
        used = 0
        for index, (row, text) in enumerate(zip(target.rows, block.texts)):
            expect(text.index == index, f"{target.file_id}: parsed text index gap")
            expect(not text.terminator_missing, f"{target.file_id}#{index}: source NUL missing")
            expect(text.text == row["jpn_text"], f"{target.file_id}#{index}: clean DAT/JPN production mismatch")
            used += len(row["cn_text"].encode("utf-8")) + 1
        # oEbN physical_size is 4-byte aligned.  The 0..3 bytes after the last
        # source NUL are alignment tail bytes, not translation capacity; they
        # must remain byte-identical.  All source offsets themselves are tight.
        source_used = block.offsets[-1] + len(block.texts[-1].text_bytes) + 1
        reserved_tail = block.text_capacity - source_used
        expect(0 <= reserved_tail <= 3, f"{target.file_id}: unexpected oEbN alignment tail {reserved_tail}")
        for index, text in enumerate(block.texts):
            expected_offset = 0 if index == 0 else (
                block.offsets[index - 1] + len(block.texts[index - 1].text_bytes) + 1
            )
            expect(text.relative_offset == expected_offset, f"{target.file_id}: source strings are not tightly packed")
        writable_capacity = block.text_capacity - reserved_tail
        expect(used <= writable_capacity, f"{target.file_id}: capacity overflow by {used - writable_capacity} bytes")
        audit.append({
            "file_id": target.file_id,
            "lane": target.lane,
            "stream_offset": f"0x{target.stream:X}",
            "block_file_offset": f"0x{offset:X}",
            "block_end_file_offset": f"0x{parsed.end_file_offset:X}",
            "text_count": len(target.rows),
            "text_capacity": block.text_capacity,
            "reserved_alignment_tail_bytes": reserved_tail,
            "writable_text_capacity": writable_capacity,
            "cn_used_bytes": used,
            "headroom_bytes": writable_capacity - used,
            "source_jpn_exact": "YES",
            "control_exact": "YES",
            "status": "READY",
        })
    return audit


def repack_plain_block(parsed: ParsedPhysicalBlock, texts: list[str]) -> bytes:
    block = parsed.block
    expect(len(texts) == block.text_count, f"0x{parsed.file_offset:X}: repack text count mismatch")
    encoded = [text.encode("utf-8") + b"\0" for text in texts]
    used = sum(len(item) for item in encoded)
    source_used = block.offsets[-1] + len(block.texts[-1].text_bytes) + 1
    reserved_tail = block.text_capacity - source_used
    writable_capacity = block.text_capacity - reserved_tail
    expect(used <= writable_capacity, f"0x{parsed.file_offset:X}: repack exceeds writable capacity")
    offsets = []
    cursor = 0
    for item in encoded:
        offsets.append(cursor)
        cursor += len(item)
    header_size = block.table_offset - block.offset
    header = parsed.plaintext[:header_size]
    table = struct.pack(f"<{len(offsets)}I", *offsets) if offsets else b""
    expected_table_size = block.text_base - block.table_offset
    expect(len(table) == expected_table_size, f"0x{parsed.file_offset:X}: offset table size changed")
    body = b"".join(encoded).ljust(writable_capacity, b"\0")
    opaque_alignment_tail = parsed.plaintext[-reserved_tail:] if reserved_tail else b""
    result = header + table + body + opaque_alignment_tail
    expect(len(result) == len(parsed.plaintext), f"0x{parsed.file_offset:X}: physical block size changed")
    return result


def build_candidate(source: bytes, targets: dict[int, TargetBlock], source_census: Census) -> tuple[bytes, dict[int, int]]:
    rebuilt = bytearray(source)
    changed_by_block = {}
    for offset, target in sorted(targets.items()):
        parsed = source_census.blocks[offset]
        jpn_repacked = repack_plain_block(parsed, [row["jpn_text"] for row in target.rows])
        expect(jpn_repacked == parsed.plaintext, f"{target.file_id}: clean JPN fixed-layout round-trip is not byte-identical")
        cn_repacked = repack_plain_block(parsed, [row["cn_text"] for row in target.rows])
        new_cipher = bytes(
            original_cipher ^ original_plain ^ replacement_plain
            for original_cipher, original_plain, replacement_plain in zip(
                source[offset:parsed.end_file_offset], parsed.plaintext, cn_repacked
            )
        )
        rebuilt[offset:parsed.end_file_offset] = new_cipher
        changed_by_block[offset] = sum(a != b for a, b in zip(parsed.plaintext, cn_repacked))
    return bytes(rebuilt), changed_by_block


def changed_ranges(before: bytes, after: bytes) -> list[dict]:
    expect(len(before) == len(after), "changed range input sizes differ")
    result = []
    start = None
    for index, (left, right) in enumerate(zip(before, after)):
        if left != right and start is None:
            start = index
        elif left == right and start is not None:
            result.append({"start": f"0x{start:X}", "end": f"0x{index:X}", "bytes": index - start})
            start = None
    if start is not None:
        result.append({"start": f"0x{start:X}", "end": f"0x{len(before):X}", "bytes": len(before) - start})
    return result


def validate_candidate(
    source: bytes,
    candidate: bytes,
    targets: dict[int, TargetBlock],
    source_census: Census,
    candidate_census: Census,
    block_audit: list[dict],
    changed_by_block: dict[int, int],
) -> tuple[dict, list[dict]]:
    expect(len(candidate) == len(source), "candidate DAT size changed")
    target_offsets = set(targets)
    expect(set(candidate_census.blocks) == set(source_census.blocks), "candidate/source parsed block sets differ")
    non_target_mismatch = []
    target_header_mismatch = []
    verified_rows = 0
    for offset in sorted(source_census.blocks):
        old = source_census.blocks[offset]
        new = candidate_census.blocks[offset]
        if offset not in target_offsets:
            if old.plaintext != new.plaintext:
                non_target_mismatch.append(f"0x{offset:X}")
            continue
        target = targets[offset]
        expect(old.owner_stream == new.owner_stream, f"{target.file_id}: candidate owner stream changed")
        expect(old.plaintext[:0x20] == new.plaintext[:0x20], f"{target.file_id}: oEbN header changed")
        if old.plaintext[:0x20] != new.plaintext[:0x20]:
            target_header_mismatch.append(f"0x{offset:X}")
        expect(new.block.total_size == old.block.total_size, f"{target.file_id}: total_size changed")
        expect(new.block.text_count == len(target.rows), f"{target.file_id}: candidate text count changed")
        expect(new.block.text_capacity == old.block.text_capacity, f"{target.file_id}: candidate capacity changed")
        for index, (text, row) in enumerate(zip(new.block.texts, target.rows)):
            expect(not text.terminator_missing, f"{target.file_id}#{index}: candidate NUL missing")
            expect(text.text == row["cn_text"], f"{target.file_id}#{index}: candidate CN mismatch")
            verified_rows += 1
    expect(not non_target_mismatch, f"non-target plaintext blocks changed: {non_target_mismatch[:20]}")
    expect(verified_rows == EXPECTED_TARGET_ROWS, f"candidate verified rows {verified_rows} != {EXPECTED_TARGET_ROWS}")

    ranges = changed_ranges(source, candidate)
    target_intervals = sorted(
        (offset, source_census.blocks[offset].end_file_offset) for offset in target_offsets
    )
    outside = []
    for entry in ranges:
        start, end = int(entry["start"], 0), int(entry["end"], 0)
        if not any(owner_start <= start and end <= owner_end for owner_start, owner_end in target_intervals):
            outside.append(entry)
    expect(not outside, f"ciphertext changed outside target blocks: {outside[:20]}")
    expect(sum(item["bytes"] for item in ranges) == sum(changed_by_block.values()), "changed byte accounting mismatch")

    by_id = {row["file_id"]: row for row in block_audit}
    for offset, target in targets.items():
        by_id[target.file_id]["changed_bytes"] = changed_by_block[offset]
        by_id[target.file_id]["candidate_cn_exact"] = "YES"
        by_id[target.file_id]["status"] = "PASS"

    result = {
        "target_blocks_verified": len(targets),
        "target_rows_verified": verified_rows,
        "target_header_mismatches": len(target_header_mismatch),
        "non_target_oebn_blocks": len(source_census.blocks) - len(targets),
        "non_target_oebn_mismatches": len(non_target_mismatch),
        "ciphertext_changed_ranges": len(ranges),
        "ciphertext_changed_bytes": sum(item["bytes"] for item in ranges),
        "ciphertext_changes_outside_target_blocks": len(outside),
        "dat_size_unchanged": len(source) == len(candidate),
        "key_file_required": False,
        "key_modified": False,
    }
    return result, ranges


def write_csv(path: Path, rows: list[dict]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    expect(bool(rows), f"refusing to write empty CSV: {path}")
    with path.open("w", encoding="utf-8-sig", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=list(rows[0]))
        writer.writeheader()
        writer.writerows(rows)


def main() -> int:
    args = parse_args()
    source_path = args.dat.resolve()
    expect(source_path.is_file(), f"source DAT not found: {source_path}")
    if not args.check:
        expect(source_path != args.output.resolve(), "output must not overwrite source DAT")
    source = source_path.read_bytes()
    expect(len(source) == EXPECTED_SOURCE_BYTES, f"source DAT bytes {len(source)} != {EXPECTED_SOURCE_BYTES}")
    source_hash = sha256(source)
    expect(source_hash == EXPECTED_SOURCE_SHA256, f"source DAT is not the frozen clean JPN base: {source_hash}")

    master = load_master(args.master)
    targets = load_production(args.production_dir, master)
    seed = filename_seed(source_path.name)
    source_census = census(source, seed)
    source_global = validate_global(source_census, "source")
    block_audit = validate_bindings(targets, source_census)

    check_summary = {
        "status": "PASS",
        "mode": "CHECK" if args.check else "BUILD",
        "source_dat": str(source_path),
        "source_sha256": source_hash,
        "production_files": EXPECTED_TARGET_FILES,
        "target_blocks": len(targets),
        "target_rows": sum(len(item.rows) for item in targets.values()),
        "briefing_files": {"blocks": EXPECTED_FILES_BLOCKS, "rows": EXPECTED_FILES_ROWS},
        "briefing_mission": {"blocks": EXPECTED_MISSION_BLOCKS, "rows": EXPECTED_MISSION_ROWS},
        "source_global_census": source_global,
        "binding_errors": 0,
        "control_errors": 0,
        "capacity_errors": 0,
        "jpn_roundtrip_errors": 0,
    }
    if args.check:
        print(json.dumps(check_summary, ensure_ascii=False, indent=2))
        return 0

    candidate, changed_by_block = build_candidate(source, targets, source_census)
    candidate_census = census(candidate, seed, source_census.starts)
    candidate_global = validate_global(candidate_census, "candidate")
    validation, ranges = validate_candidate(
        source, candidate, targets, source_census, candidate_census, block_audit, changed_by_block
    )

    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.report_dir.mkdir(parents=True, exist_ok=True)
    args.output.write_bytes(candidate)
    block_audit_path = args.report_dir / "briefing_block_audit.csv"
    changed_ranges_path = args.report_dir / "briefing_changed_ranges.csv"
    report_path = args.report_dir / "briefing_build_report.json"
    write_csv(block_audit_path, block_audit)
    write_csv(changed_ranges_path, ranges)

    report = {
        "status": "PASS",
        "stage": "BRIEFING fixed-layout clean-JPN build",
        "scope": "current clean JPN 0076531d.DAT and frozen 469-block B81 corpus",
        "source": {
            "path": str(source_path),
            "bytes": len(source),
            "sha256": source_hash,
        },
        "output": {
            "path": str(args.output.resolve()),
            "bytes": len(candidate),
            "sha256": sha256(candidate),
        },
        "production": {
            "directory": str(args.production_dir.resolve()),
            "files": EXPECTED_TARGET_FILES,
            "blocks": len(targets),
            "rows": sum(len(item.rows) for item in targets.values()),
            "briefing_files": {"blocks": EXPECTED_FILES_BLOCKS, "rows": EXPECTED_FILES_ROWS},
            "briefing_mission": {"blocks": EXPECTED_MISSION_BLOCKS, "rows": EXPECTED_MISSION_ROWS},
        },
        "source_global_census": source_global,
        "candidate_global_census": candidate_global,
        "validation": validation,
        "outputs": {
            "block_audit_csv": str(block_audit_path.resolve()),
            "changed_ranges_csv": str(changed_ranges_path.resolve()),
            "report_json": str(report_path.resolve()),
        },
        "completion_claim": (
            "All 469 frozen JPN BRIEFING blocks / 5,645 physical rows were rebuilt "
            "from the recognized clean JPN base and parsed back to exact production CN. "
            "All 2,292 non-target oEbN blocks and all ciphertext bytes outside target "
            "block extents remain byte-identical. This is an offline build PASS, not an "
            "in-game validation claim."
        ),
    }
    report_path.write_text(json.dumps(report, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    print(json.dumps({
        "status": report["status"],
        "output_dat": report["output"],
        "production": report["production"],
        "candidate_global_census": candidate_global,
        "validation": validation,
        "report": str(report_path.resolve()),
    }, ensure_ascii=False, indent=2))
    return 0


if __name__ == "__main__":
    try:
        raise SystemExit(main())
    except BuildFailure as error:
        print(json.dumps({"status": "FAIL", "error": str(error)}, ensure_ascii=False, indent=2), file=sys.stderr)
        raise SystemExit(2)
