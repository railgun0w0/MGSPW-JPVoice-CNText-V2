"""Strict parser and text-bearing stream discovery for BRIEFING oEbN data."""

from __future__ import annotations

import struct
from dataclasses import dataclass
from typing import Iterator

from core.pc_crypto import outer_transform


NBE_MAGIC = b"oEbN"
NBE_HEADER_SIZE = 0x20


class NbeParseError(ValueError):
    pass


@dataclass(frozen=True)
class NbeText:
    index: int
    relative_offset: int
    absolute_offset: int
    terminator_offset: int | None
    terminator_missing: bool
    text_bytes: bytes
    text: str


@dataclass(frozen=True)
class NbeBlock:
    offset: int
    total_size: int
    end: int
    field_04: int
    field_08: int
    version: int
    relative_value: int
    size_minus_four: int
    field_1c: int
    table_offset: int
    text_base: int
    text_capacity: int
    offsets: tuple[int, ...]
    texts: tuple[NbeText, ...]

    @property
    def text_count(self) -> int:
        return len(self.texts)


@dataclass(frozen=True)
class StreamCandidate:
    offset: int
    first_block_offset: int
    first_block_total_size: int


@dataclass(frozen=True)
class BlockFailure:
    offset: int
    error: str


def _plausible_header(data: bytes, offset: int) -> tuple[int, int] | None:
    if offset + NBE_HEADER_SIZE > len(data) or data[offset : offset + 4] != NBE_MAGIC:
        return None
    total_size, version, relative_value, size_minus_four = struct.unpack_from(
        "<4I", data, offset + 0x0C
    )
    if version != 0x14 or total_size + 8 < NBE_HEADER_SIZE:
        return None
    if size_minus_four != total_size - 4:
        return None
    text_base = offset + 0x0C + relative_value
    if text_base < offset + NBE_HEADER_SIZE or text_base > offset + total_size + 8:
        return None
    if (text_base - (offset + NBE_HEADER_SIZE)) % 4:
        return None
    return total_size, text_base


def parse_nbe_block(data: bytes, offset: int = 0, label: str = "") -> NbeBlock:
    context = f"{label + ': ' if label else ''}oEbN block at 0x{offset:X}"
    if offset < 0 or offset + NBE_HEADER_SIZE > len(data):
        raise NbeParseError(f"{context}: truncated header")
    if data[offset : offset + 4] != NBE_MAGIC:
        raise NbeParseError(f"{context}: missing magic")
    field_04, field_08, total_size, version, relative_value, size_minus_four, field_1c = (
        struct.unpack_from("<7I", data, offset + 4)
    )
    physical_size = total_size + 8
    end = offset + physical_size
    if physical_size < NBE_HEADER_SIZE or end > len(data):
        raise NbeParseError(f"{context}: invalid/truncated physical size {physical_size}")
    if version != 0x14:
        raise NbeParseError(f"{context}: unsupported version 0x{version:X}")
    if size_minus_four != total_size - 4:
        raise NbeParseError(f"{context}: inconsistent size fields")
    table_offset = offset + NBE_HEADER_SIZE
    text_base = offset + 0x0C + relative_value
    if text_base < table_offset or text_base > end:
        raise NbeParseError(f"{context}: text base outside block")
    table_size = text_base - table_offset
    if table_size % 4:
        raise NbeParseError(f"{context}: offset table is not u32-aligned")
    count = table_size // 4
    offsets = tuple(struct.unpack_from(f"<{count}I", data, table_offset)) if count else ()
    capacity = end - text_base
    if offsets and offsets[0] != 0:
        raise NbeParseError(f"{context}: first text offset is not zero")
    if any(left > right for left, right in zip(offsets, offsets[1:])):
        raise NbeParseError(f"{context}: text offsets are not monotonic")
    if any(item >= capacity for item in offsets):
        raise NbeParseError(f"{context}: text offset exceeds capacity")
    texts: list[NbeText] = []
    for index, relative_offset in enumerate(offsets):
        start = text_base + relative_offset
        next_start = text_base + offsets[index + 1] if index + 1 < count else end
        limit = next_start if next_start > start else end
        terminator = data.find(b"\0", start, limit)
        missing = terminator < 0
        text_end = limit if missing else terminator
        raw = data[start:text_end]
        try:
            text = raw.decode("utf-8", errors="strict")
        except UnicodeDecodeError as error:
            raise NbeParseError(f"{context}: text {index} is not strict UTF-8: {error}") from error
        texts.append(NbeText(index, relative_offset, start, None if missing else terminator, missing, raw, text))
    return NbeBlock(
        offset, total_size, end, field_04, field_08, version, relative_value,
        size_minus_four, field_1c, table_offset, text_base, capacity, offsets,
        tuple(texts),
    )


def iter_magic_offsets(data: bytes, start: int = 0, end: int | None = None) -> Iterator[int]:
    limit = len(data) if end is None else min(end, len(data))
    cursor = max(0, start)
    while cursor < limit:
        offset = data.find(NBE_MAGIC, cursor, limit)
        if offset < 0:
            return
        yield offset
        cursor = offset + 1


def parse_all_nbe_blocks(data: bytes, label: str = "") -> tuple[tuple[NbeBlock, ...], tuple[BlockFailure, ...]]:
    blocks: list[NbeBlock] = []
    failures: list[BlockFailure] = []
    for offset in iter_magic_offsets(data):
        if _plausible_header(data, offset) is None:
            continue
        try:
            blocks.append(parse_nbe_block(data, offset, label))
        except NbeParseError as error:
            failures.append(BlockFailure(offset, str(error)))
    return tuple(blocks), tuple(failures)


def discover_text_stream_starts(
    encrypted: bytes,
    seed: int,
    *,
    alignment: int = 0x800,
    lead_window: int = 0x1000,
) -> tuple[StreamCandidate, ...]:
    if alignment <= 0 or alignment & (alignment - 1):
        raise ValueError("alignment must be a positive power of two")
    candidates: list[StreamCandidate] = []
    prefix_size = max(lead_window, NBE_HEADER_SIZE)
    for stream_offset in range(0, len(encrypted), alignment):
        raw_prefix = encrypted[stream_offset : stream_offset + prefix_size]
        plain_prefix = outer_transform(raw_prefix, seed)
        accepted = None
        for block_offset in iter_magic_offsets(plain_prefix, 0, min(lead_window, len(plain_prefix))):
            header = _plausible_header(plain_prefix, block_offset)
            if header is None:
                continue
            total_size, _ = header
            needed = block_offset + total_size + 8
            if stream_offset + needed > len(encrypted):
                continue
            probe = outer_transform(encrypted[stream_offset : stream_offset + needed], seed)
            try:
                block = parse_nbe_block(probe, block_offset, f"stream 0x{stream_offset:X}")
            except NbeParseError:
                continue
            accepted = StreamCandidate(stream_offset, block_offset, block.total_size)
            break
        if accepted is not None:
            candidates.append(accepted)
    return tuple(candidates)
