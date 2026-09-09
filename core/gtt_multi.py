#!/usr/bin/env python3
"""Read-only parser for MGSPW multi-segment GTT/YPK data.

The segment count and boundary table in each record header are authoritative.
NUL bytes terminate text inside an already identified segment; they are never
used to discover how many timed texts a record contains.

This module intentionally contains no builder or mutation API.
"""

from __future__ import annotations

import argparse
import json
import struct
from dataclasses import dataclass
from pathlib import Path
from typing import Sequence


GTT_MAGIC = b"GTT\0"
GTT_ALIGNMENT = 16
FIXED_HEADER_SIZE = 0x14
SEGMENT_HEADER_SIZE = 0x14


class GttParseError(ValueError):
    """Raised when GTT framing or a timed-text boundary is invalid."""


class GttRepackError(ValueError):
    """Raised when a fixed-layout record cannot be repacked safely."""


class GttHardOverflow(GttRepackError):
    """Raised when encoded timed texts exceed the aligned physical capacity."""


def align_up(value: int, alignment: int = GTT_ALIGNMENT) -> int:
    if alignment <= 0 or alignment & (alignment - 1):
        raise ValueError("alignment must be a positive power of two")
    return (value + alignment - 1) & ~(alignment - 1)


@dataclass(frozen=True)
class SegmentHeader:
    """The ten u16 values belonging to one timed-text segment."""

    flag: int
    start_a: int
    start_b: int
    boundary: int
    end_a: int
    end_b: int
    end_c: int
    end_d: int
    timing_a: int
    timing_b: int

    @property
    def start(self) -> int:
        return self.start_a

    @property
    def end(self) -> int:
        return self.end_a

    @classmethod
    def unpack_from(cls, header: bytes, offset: int) -> "SegmentHeader":
        return cls(*struct.unpack_from("<10H", header, offset))


@dataclass(frozen=True)
class TimedText:
    index: int
    start: int
    end: int
    text_bytes: bytes
    text: str
    header: SegmentHeader
    raw_region: bytes
    terminator_offset: int | None
    terminator_missing: bool
    interior_nul: bool


@dataclass(frozen=True)
class GttRecord:
    index: int
    offset: int
    segment_count: int
    header_size: int
    record_size: int
    aligned_size: int
    nominal_capacity: int
    aligned_capacity: int
    header: bytes
    nominal_payload: bytes
    aligned_payload: bytes
    alignment_slack: bytes
    timed_texts: tuple[TimedText, ...]

    @property
    def boundaries(self) -> tuple[tuple[int, int], ...]:
        return tuple((item.start, item.end) for item in self.timed_texts)

    @property
    def texts(self) -> tuple[str, ...]:
        return tuple(item.text for item in self.timed_texts)


@dataclass(frozen=True)
class GttRepackResult:
    data: bytes
    old_boundaries: tuple[tuple[int, int], ...]
    new_boundaries: tuple[tuple[int, int], ...]
    utf8_lengths_with_nul: tuple[int, ...]
    nominal_capacity: int
    aligned_capacity: int
    required: int
    record_size_before: int
    record_size_after: int
    aligned_size_before: int
    aligned_size_after: int
    boundary_byte_offsets: tuple[int, ...]
    non_boundary_header_byte_identical: bool


def _context(label: str, record_index: int, offset: int) -> str:
    prefix = f"{label}: " if label else ""
    return f"{prefix}record {record_index} at 0x{offset:X}"


def _parse_timed_texts(
    header: bytes,
    aligned_payload: bytes,
    segment_count: int,
    context: str,
) -> tuple[TimedText, ...]:
    table_end = FIXED_HEADER_SIZE + segment_count * SEGMENT_HEADER_SIZE
    if table_end > len(header):
        raise GttParseError(
            f"{context}: segment table ends at 0x{table_end:X}, "
            f"past header_size 0x{len(header):X}"
        )

    result: list[TimedText] = []
    previous_end = 0
    for index in range(segment_count):
        group_offset = FIXED_HEADER_SIZE + index * SEGMENT_HEADER_SIZE
        fields = SegmentHeader.unpack_from(header, group_offset)

        if fields.start_a != fields.start_b:
            raise GttParseError(
                f"{context}: segment {index} start copies differ "
                f"({fields.start_a}, {fields.start_b})"
            )
        ends = (fields.end_a, fields.end_b, fields.end_c, fields.end_d)
        if len(set(ends)) != 1:
            raise GttParseError(
                f"{context}: segment {index} end copies differ {ends}"
            )

        start = fields.start
        end = fields.end
        if fields.boundary not in (start, end):
            raise GttParseError(
                f"{context}: segment {index} boundary marker "
                f"{fields.boundary} is neither start {start} nor end {end}"
            )
        if start != previous_end:
            raise GttParseError(
                f"{context}: segment {index} starts at {start}, "
                f"expected contiguous boundary {previous_end}"
            )
        if end <= start:
            raise GttParseError(
                f"{context}: segment {index} has invalid range {start}-{end}"
            )
        if end > len(aligned_payload):
            raise GttParseError(
                f"{context}: segment {index} end {end} exceeds "
                f"aligned_capacity {len(aligned_payload)}"
            )

        slot = aligned_payload[start:end]
        terminator_in_region = slot.find(b"\0")
        terminator_missing = terminator_in_region < 0
        if terminator_missing:
            text_bytes = slot
            terminator_offset = None
            interior_nul = False
        else:
            # The header boundary is authoritative for locating the timed
            # region.  Its first NUL terminates that region's actual text; the
            # remaining bytes may contain retained source bytes or zero fill.
            # NUL is never used to infer the number of timed segments.
            text_bytes = slot[:terminator_in_region]
            terminator_offset = start + terminator_in_region
            interior_nul = terminator_in_region != len(slot) - 1
        try:
            text = text_bytes.decode("utf-8", errors="strict")
        except UnicodeDecodeError as error:
            raise GttParseError(
                f"{context}: segment {index} is not strict UTF-8: {error}"
            ) from error

        result.append(
            TimedText(
                index,
                start,
                end,
                text_bytes,
                text,
                fields,
                slot,
                terminator_offset,
                terminator_missing,
                interior_nul,
            )
        )
        previous_end = end

    return tuple(result)


def parse_gtt(data: bytes, label: str = "") -> tuple[GttRecord, ...]:
    """Parse every 16-byte-aligned GTT record in a YPK segment.

    ``record_size`` remains the nominal size from the header.  Timed-text
    boundaries are validated against ``aligned_capacity`` so a valid record may
    use alignment slack without changing ``record_size``.
    """

    records: list[GttRecord] = []
    offset = 0
    while offset < len(data):
        if data[offset : offset + 4] != GTT_MAGIC:
            if not any(data[offset:]):
                break
            raise GttParseError(
                f"{_context(label, len(records), offset)}: missing GTT magic"
            )
        if offset + 16 > len(data):
            raise GttParseError(
                f"{_context(label, len(records), offset)}: truncated fixed header"
            )

        segment_count, header_size, record_size = struct.unpack_from(
            "<III", data, offset + 4
        )
        context = _context(label, len(records), offset)
        if segment_count <= 0:
            raise GttParseError(f"{context}: segment_count must be positive")
        if header_size < FIXED_HEADER_SIZE:
            raise GttParseError(
                f"{context}: header_size {header_size} is below {FIXED_HEADER_SIZE}"
            )
        if record_size < header_size:
            raise GttParseError(
                f"{context}: record_size {record_size} is below header_size {header_size}"
            )

        aligned_size = align_up(record_size)
        aligned_end = offset + aligned_size
        if aligned_end > len(data):
            raise GttParseError(
                f"{context}: aligned physical slot ends at 0x{aligned_end:X}, "
                f"past input size 0x{len(data):X}"
            )

        header = data[offset : offset + header_size]
        nominal_payload = data[offset + header_size : offset + record_size]
        aligned_payload = data[offset + header_size : aligned_end]
        alignment_slack = data[offset + record_size : aligned_end]
        timed_texts = _parse_timed_texts(
            header, aligned_payload, segment_count, context
        )

        records.append(
            GttRecord(
                index=len(records),
                offset=offset,
                segment_count=segment_count,
                header_size=header_size,
                record_size=record_size,
                aligned_size=aligned_size,
                nominal_capacity=record_size - header_size,
                aligned_capacity=aligned_size - header_size,
                header=header,
                nominal_payload=nominal_payload,
                aligned_payload=aligned_payload,
                alignment_slack=alignment_slack,
                timed_texts=timed_texts,
            )
        )
        offset = aligned_end

    if offset != len(data) and any(data[offset:]):
        raise GttParseError(
            f"{label + ': ' if label else ''}nonzero trailing bytes at 0x{offset:X}"
        )
    return tuple(records)


def parse_gtt_multi(data: bytes, label: str = "") -> tuple[GttRecord, ...]:
    """Explicit multi-segment API name used by the V2 pipeline."""

    return parse_gtt(data, label)


def _boundary_byte_offsets(segment_count: int) -> tuple[int, ...]:
    offsets: list[int] = []
    # Per 10-u16 group, flag and the last two timing/style words are retained.
    # The two starts, role-preserving boundary word, and four ends are rewritten.
    for index in range(segment_count):
        base = FIXED_HEADER_SIZE + index * SEGMENT_HEADER_SIZE
        for word_index in (1, 2, 3, 4, 5, 6, 7):
            word_offset = base + word_index * 2
            offsets.extend((word_offset, word_offset + 1))
    return tuple(offsets)


def repack_gtt_multi(
    record: GttRecord, cn_texts: Sequence[str]
) -> GttRepackResult:
    """Repack one parsed record without changing its fixed physical layout.

    Text is packed consecutively into the aligned payload slot.  ``record_size``
    is immutable even when text uses bytes in the alignment slack.
    """

    texts = tuple(cn_texts)
    if len(texts) != record.segment_count:
        raise GttRepackError(
            f"segment count mismatch: record={record.segment_count}, texts={len(texts)}"
        )

    encoded_texts: list[bytes] = []
    lengths_with_nul: list[int] = []
    for index, text in enumerate(texts):
        if not isinstance(text, str):
            raise GttRepackError(f"text {index} is not str")
        if "\0" in text:
            raise GttRepackError(f"text {index} contains an embedded NUL")
        encoded = text.encode("utf-8", errors="strict")
        encoded_texts.append(encoded)
        lengths_with_nul.append(len(encoded) + 1)

    required = sum(lengths_with_nul)
    if required > record.aligned_capacity:
        raise GttHardOverflow(
            "HARD_OVERFLOW: "
            f"required={required}, aligned_capacity={record.aligned_capacity}, "
            f"nominal_capacity={record.nominal_capacity}; record_size is immutable"
        )

    new_boundaries: list[tuple[int, int]] = []
    cursor = 0
    for length in lengths_with_nul:
        start = cursor
        cursor += length
        new_boundaries.append((start, cursor))

    header = bytearray(record.header)
    for old, (new_start, new_end) in zip(record.timed_texts, new_boundaries):
        base = FIXED_HEADER_SIZE + old.index * SEGMENT_HEADER_SIZE
        if new_end > 0xFFFF:
            raise GttHardOverflow(
                "HARD_OVERFLOW: boundary exceeds 16-bit header field; "
                "record_size is immutable"
            )

        struct.pack_into("<H", header, base + 2, new_start)
        struct.pack_into("<H", header, base + 4, new_start)
        if old.header.boundary == old.start:
            new_boundary = new_start
        elif old.header.boundary == old.end:
            new_boundary = new_end
        else:  # The read-only parser normally rejects this before repacking.
            raise GttRepackError(
                f"segment {old.index} has unknown boundary role "
                f"{old.header.boundary} for {old.start}-{old.end}"
            )
        struct.pack_into("<H", header, base + 6, new_boundary)
        for relative in (8, 10, 12, 14):
            struct.pack_into("<H", header, base + relative, new_end)

    boundary_offsets = _boundary_byte_offsets(record.segment_count)
    boundary_offset_set = set(boundary_offsets)
    non_boundary_identical = all(
        before == after
        for offset, (before, after) in enumerate(zip(record.header, header))
        if offset not in boundary_offset_set
    )
    if not non_boundary_identical:
        raise GttRepackError("internal error: non-boundary header byte changed")

    aligned_payload = bytearray(record.aligned_capacity)
    cursor = 0
    for encoded in encoded_texts:
        aligned_payload[cursor : cursor + len(encoded)] = encoded
        cursor += len(encoded)
        aligned_payload[cursor] = 0
        cursor += 1
    if cursor != required:
        raise GttRepackError("internal error: packed length does not equal required")

    rebuilt = bytes(header) + bytes(aligned_payload)
    if len(rebuilt) != record.aligned_size:
        raise GttRepackError(
            f"internal error: rebuilt aligned size {len(rebuilt)} != {record.aligned_size}"
        )
    record_size_after = struct.unpack_from("<I", header, 0x0C)[0]
    if record_size_after != record.record_size:
        raise GttRepackError("internal error: record_size changed")

    return GttRepackResult(
        data=rebuilt,
        old_boundaries=record.boundaries,
        new_boundaries=tuple(new_boundaries),
        utf8_lengths_with_nul=tuple(lengths_with_nul),
        nominal_capacity=record.nominal_capacity,
        aligned_capacity=record.aligned_capacity,
        required=required,
        record_size_before=record.record_size,
        record_size_after=record_size_after,
        aligned_size_before=record.aligned_size,
        aligned_size_after=len(rebuilt),
        boundary_byte_offsets=boundary_offsets,
        non_boundary_header_byte_identical=non_boundary_identical,
    )


def record_to_dict(record: GttRecord) -> dict:
    return {
        "index": record.index,
        "offset": record.offset,
        "segment_count": record.segment_count,
        "header_size": record.header_size,
        "record_size": record.record_size,
        "aligned_size": record.aligned_size,
        "nominal_capacity": record.nominal_capacity,
        "aligned_capacity": record.aligned_capacity,
        "boundaries": [list(pair) for pair in record.boundaries],
        "texts": list(record.texts),
        "segments": [
            {
                "index": item.index,
                "start": item.start,
                "end": item.end,
                "utf8_byte_length": len(item.text_bytes),
                "text": item.text,
                "flag": item.header.flag,
                "boundary_marker": item.header.boundary,
                "timing_a": item.header.timing_a,
                "timing_b": item.header.timing_b,
                "terminator_offset": item.terminator_offset,
                "terminator_missing": item.terminator_missing,
                "interior_nul": item.interior_nul,
                "raw_region_hex": item.raw_region.hex(),
            }
            for item in record.timed_texts
        ],
    }


def _select_records(
    records: Sequence[GttRecord], record_index: int | None
) -> Sequence[GttRecord]:
    if record_index is None:
        return records
    if not 0 <= record_index < len(records):
        raise GttParseError(
            f"record index {record_index} is outside 0..{len(records) - 1}"
        )
    return (records[record_index],)


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("input", type=Path, help="raw YPK/GTT segment")
    parser.add_argument("--record", type=int, help="emit only this record index")
    args = parser.parse_args()

    data = args.input.read_bytes()
    records = parse_gtt(data, str(args.input))
    selected = _select_records(records, args.record)
    print(
        json.dumps(
            {
                "input": str(args.input.resolve()),
                "record_count": len(records),
                "records": [record_to_dict(record) for record in selected],
            },
            ensure_ascii=False,
            indent=2,
        )
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
