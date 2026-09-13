#!/usr/bin/env python3
"""Replace one compressed page in a PC MGSPW STAGEDAT without rebuilding it.

The tool decodes the Master Collection outer stream and the original MGSPW
inner stream, verifies the selected page against an authoritative extracted
file, updates only that page and its table size, then performs a full round-trip
audit of the output container.
"""

from __future__ import annotations

import argparse
import hashlib
import json
import shutil
import struct
import zlib
from dataclasses import dataclass
from pathlib import Path


MASK32 = 0xFFFFFFFF
INNER_MULTIPLIER = 0x02E90EDD
OUTER_XOR = 0xB9D3018F


class StageError(RuntimeError):
    pass


def u32(value: int) -> int:
    return value & MASK32


def sha256_path(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as stream:
        while chunk := stream.read(4 * 1024 * 1024):
            digest.update(chunk)
    return digest.hexdigest().upper()


def filename_seed(path: Path) -> int:
    stem = path.name.split(".", 1)[0]
    value = 0
    for byte in stem.encode("ascii"):
        value = u32(value * 0x2356F + byte * 0x1D35)
    return value


class PcStream:
    def __init__(self, seed: int) -> None:
        self.state: list[int] = []
        for _ in range(624):
            high = seed & 0xFFFF0000
            seed = u32(seed * 0x10DCD + 1)
            self.state.append(high | (seed >> 16))
            seed = u32(seed * 0x10DCD + 1)
        self.output: list[int] = []
        self.index = 0
        self._twist_and_temper()

    def _twist_and_temper(self) -> None:
        for index in range(227):
            value = (self.state[index] & 0x80000000) | (self.state[index + 1] & 0x7FFFFFFF)
            self.state[index] = u32(self.state[index + 397] ^ (value >> 1) ^ (0x9908B0DF if value & 1 else 0))
        for index in range(227, 623):
            value = (self.state[index] & 0x80000000) | (self.state[index + 1] & 0x7FFFFFFF)
            self.state[index] = u32(self.state[index - 227] ^ (value >> 1) ^ (0x9908B0DF if value & 1 else 0))
        value = (self.state[623] & 0x80000000) | (self.state[0] & 0x7FFFFFFF)
        self.state[623] = u32(self.state[396] ^ (value >> 1) ^ (0x9908B0DF if value & 1 else 0))
        self.output = []
        for value in self.state:
            value ^= value >> 11
            value ^= (value << 7) & 0x9D2C5680
            value ^= (value << 15) & 0xEFC60000
            value ^= value >> 18
            self.output.append(u32(value))

    def next(self) -> int:
        if self.index >= 624:
            self._twist_and_temper()
            self.index = 0
        result = self.output[self.index]
        self.index += 1
        return result

    def discard_words(self, count: int) -> None:
        while count:
            available = 624 - self.index
            if count < available:
                self.index += count
                return
            count -= available
            self._twist_and_temper()
            self.index = 0


def outer_transform(data: bytes, seed: int, file_offset: int) -> bytes:
    stream = PcStream(seed)
    stream.discard_words((0x14 + file_offset) // 4)
    output = bytearray(data)
    for offset in range(0, len(output), 4):
        count = min(4, len(output) - offset)
        value = int.from_bytes(output[offset : offset + count], "little")
        value ^= stream.next() ^ OUTER_XOR
        output[offset : offset + count] = value.to_bytes(4, "little")[:count]
    return bytes(output)


def initial_inner_key(salt_a: int, salt_b: int) -> int:
    page_key = salt_a ^ salt_b
    return u32(((page_key ^ 0x6576) << 16) | page_key)


def inner_key_b(salt_a: int, salt_b: int, salt_c: int) -> int:
    return u32((salt_a ^ salt_b) * salt_c)


def inner_transform(data: bytes, key_a: int, key_b: int) -> tuple[bytes, int]:
    output = bytearray(data)
    for offset in range(0, len(output) - len(output) % 4, 4):
        value = struct.unpack_from("<I", output, offset)[0] ^ key_a
        struct.pack_into("<I", output, offset, value)
        key_a = u32(key_a * INNER_MULTIPLIER + key_b)
    return bytes(output), key_a


@dataclass(frozen=True)
class StageHeader:
    salts: tuple[int, int, int]
    page_count: int
    plaintext: bytes
    next_inner_key: int


@dataclass(frozen=True)
class TableEntry:
    size: int
    key: int
    offset: int


def decode_header(stream, seed: int) -> StageHeader:
    stream.seek(0)
    encrypted = stream.read(40)
    if len(encrypted) != 40:
        raise StageError("STAGEDAT is shorter than its 40-byte header")
    outer = outer_transform(encrypted, seed, 0)
    salt_a, salt_b, salt_c = struct.unpack_from("<III", outer, 0)
    key_a = initial_inner_key(salt_a, salt_b)
    key_b = inner_key_b(salt_a, salt_b, salt_c)
    tail, next_key = inner_transform(outer[12:], key_a, key_b)
    plaintext = outer[:12] + tail
    page_count = struct.unpack_from("<H", plaintext, 24)[0]
    if not 1 <= page_count <= 10000:
        raise StageError(f"implausible STAGEDAT page count: {page_count}")
    return StageHeader((salt_a, salt_b, salt_c), page_count, plaintext, next_key)


def decode_table(stream, seed: int, header: StageHeader) -> tuple[list[TableEntry], bytes]:
    size = header.page_count * 12
    stream.seek(40)
    encrypted = stream.read(size)
    if len(encrypted) != size:
        raise StageError("STAGEDAT table is truncated")
    outer = outer_transform(encrypted, seed, 40)
    key_b = inner_key_b(*header.salts)
    plaintext, _ = inner_transform(outer, header.next_inner_key, key_b)
    entries = [TableEntry(*struct.unpack_from("<III", plaintext, index * 12)) for index in range(header.page_count)]
    file_size = stream.seek(0, 2)
    for index, entry in enumerate(entries):
        if entry.size < 8 or entry.offset + entry.size > file_size:
            raise StageError(f"table entry {index} points outside STAGEDAT")
    return entries, plaintext


def encode_table(plaintext: bytes, seed: int, header: StageHeader) -> bytes:
    key_b = inner_key_b(*header.salts)
    inner, _ = inner_transform(plaintext, header.next_inner_key, key_b)
    return outer_transform(inner, seed, 40)


def decode_page(stream, seed: int, header: StageHeader, entry: TableEntry) -> bytes:
    stream.seek(entry.offset)
    encrypted = stream.read(entry.size)
    if len(encrypted) != entry.size:
        raise StageError("selected page is truncated")
    # The PC STAGEDAT page stream is independently reset for every page.
    outer = outer_transform(encrypted, seed, 0)
    inner, _ = inner_transform(outer, initial_inner_key(*header.salts[:2]), inner_key_b(*header.salts))
    expected_size = struct.unpack_from("<I", inner, 0)[0]
    try:
        decompressed = zlib.decompress(inner[4:])
    except zlib.error as error:
        raise StageError(f"selected page zlib decode failed: {error}") from error
    if len(decompressed) != expected_size:
        raise StageError(f"selected page length mismatch: header={expected_size}, actual={len(decompressed)}")
    return decompressed


def encode_page(data: bytes, seed: int, header: StageHeader) -> tuple[bytes, int]:
    compressed = zlib.compress(data, level=9)
    plaintext = struct.pack("<I", len(data)) + compressed
    inner, _ = inner_transform(plaintext, initial_inner_key(*header.salts[:2]), inner_key_b(*header.salts))
    return outer_transform(inner, seed, 0), len(plaintext)


def compare_files(original: Path, patched: Path, allowed_ranges: list[tuple[int, int]]) -> tuple[int, int, int]:
    differences = 0
    first = -1
    last = -1
    offset = 0
    with original.open("rb") as left, patched.open("rb") as right:
        while True:
            a = left.read(4 * 1024 * 1024)
            b = right.read(4 * 1024 * 1024)
            if not a and not b:
                break
            if len(a) != len(b):
                raise StageError("patched STAGEDAT size changed")
            for local, (x, y) in enumerate(zip(a, b)):
                if x != y:
                    absolute = offset + local
                    if not any(start <= absolute < end for start, end in allowed_ranges):
                        raise StageError(f"unexpected changed byte at 0x{absolute:X}")
                    differences += 1
                    if first < 0:
                        first = absolute
                    last = absolute
            offset += len(a)
    return differences, first, last


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--input", type=Path, required=True)
    parser.add_argument("--page", type=int, required=True)
    parser.add_argument("--expected-original", type=Path, required=True)
    parser.add_argument("--replacement", type=Path)
    parser.add_argument("--output", type=Path)
    parser.add_argument("--report", type=Path, required=True)
    args = parser.parse_args()
    if (args.replacement is None) != (args.output is None):
        parser.error("--replacement and --output must be provided together")
    if args.output and args.output.resolve() == args.input.resolve():
        parser.error("refusing to patch the input STAGEDAT in place")

    input_hash_before = sha256_path(args.input)
    seed = filename_seed(args.input)
    expected = args.expected_original.read_bytes()
    with args.input.open("rb") as stream:
        header = decode_header(stream, seed)
        entries, table_plain = decode_table(stream, seed, header)
        if not 0 <= args.page < len(entries):
            raise StageError(f"page index {args.page} is out of range")
        selected = entries[args.page]
        decoded = decode_page(stream, seed, header, selected)
        file_size = stream.seek(0, 2)
    if decoded != expected:
        raise StageError(
            "selected page does not match --expected-original "
            f"(page={hashlib.sha256(decoded).hexdigest().upper()}, expected={hashlib.sha256(expected).hexdigest().upper()})"
        )

    report: dict = {
        "input": str(args.input.resolve()),
        "input_sha256": input_hash_before,
        "filename_seed": f"0x{seed:08X}",
        "salts": [f"0x{value:08X}" for value in header.salts],
        "page_count": header.page_count,
        "selected_page": args.page,
        "selected_page_offset": selected.offset,
        "selected_page_packed_size": selected.size,
        "selected_page_unpacked_size": len(decoded),
        "selected_page_unpacked_sha256": hashlib.sha256(decoded).hexdigest().upper(),
        "expected_original_verified": True,
        "mode": "verify-only" if args.output is None else "patch",
    }

    if args.output is not None and args.replacement is not None:
        replacement = args.replacement.read_bytes()
        encoded_page, packed_size = encode_page(replacement, seed, header)
        next_offset = min((entry.offset for entry in entries if entry.offset > selected.offset), default=file_size)
        capacity = next_offset - selected.offset
        if packed_size > capacity:
            raise StageError(f"replacement page needs {packed_size} bytes but capacity is {capacity}")

        modified_table = bytearray(table_plain)
        struct.pack_into("<I", modified_table, args.page * 12, packed_size)
        encoded_table = encode_table(bytes(modified_table), seed, header)
        # Prove that the encoder reproduces the original table byte-for-byte before modification.
        with args.input.open("rb") as stream:
            stream.seek(40)
            original_encrypted_table = stream.read(header.page_count * 12)
        if encode_table(table_plain, seed, header) != original_encrypted_table:
            raise StageError("table cipher round-trip did not reproduce original bytes")

        args.output.parent.mkdir(parents=True, exist_ok=True)
        shutil.copyfile(args.input, args.output)
        with args.output.open("r+b") as stream:
            stream.seek(40)
            stream.write(encoded_table)
            stream.seek(selected.offset)
            stream.write(encoded_page)

        if sha256_path(args.input) != input_hash_before:
            raise StageError("input STAGEDAT changed during the operation")
        with args.output.open("rb") as stream:
            out_header = decode_header(stream, seed)
            out_entries, _ = decode_table(stream, seed, out_header)
            round_trip = decode_page(stream, seed, out_header, out_entries[args.page])
        if out_header.plaintext != header.plaintext:
            raise StageError("output STAGEDAT header changed")
        for index, (before, after) in enumerate(zip(entries, out_entries)):
            expected_entry = TableEntry(packed_size, before.key, before.offset) if index == args.page else before
            if after != expected_entry:
                raise StageError(f"unexpected table change at page {index}")
        if round_trip != replacement:
            raise StageError("output page round-trip does not match replacement")

        table_size_word = 40 + args.page * 12
        diff_count, first_diff, last_diff = compare_files(
            args.input,
            args.output,
            [(table_size_word, table_size_word + 4), (selected.offset, selected.offset + packed_size)],
        )
        report.update(
            {
                "output": str(args.output.resolve()),
                "output_sha256": sha256_path(args.output),
                "replacement": str(args.replacement.resolve()),
                "replacement_sha256": hashlib.sha256(replacement).hexdigest().upper(),
                "replacement_unpacked_size": len(replacement),
                "replacement_packed_size": packed_size,
                "page_capacity": capacity,
                "output_round_trip_verified": True,
                "changed_byte_count": diff_count,
                "first_changed_offset": first_diff,
                "last_changed_offset": last_diff,
                "allowed_change_ranges": [
                    [table_size_word, table_size_word + 4],
                    [selected.offset, selected.offset + packed_size],
                ],
            }
        )

    args.report.parent.mkdir(parents=True, exist_ok=True)
    args.report.write_text(json.dumps(report, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    print(json.dumps(report, ensure_ascii=False))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
