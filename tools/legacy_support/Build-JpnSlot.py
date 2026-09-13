#!/usr/bin/env python3
"""Merge the Chinese patch's changed SLOT files into the Japanese container.

The large 002aba34.DAT contains both region-specific assets and localized files,
so replacing the Japanese container with the English-region patched container is
unsafe.  This tool matches pages by their embedded CNF tag identities, replaces
only file records which the Chinese patch changed, then recompresses each target
page inside its existing Japanese allocation.  The Japanese KEY remains valid.
"""

from __future__ import annotations

import argparse
import collections
import hashlib
import importlib.util
import json
import shutil
import struct
import sys
import tempfile
import zlib
from dataclasses import dataclass
from pathlib import Path


SECTOR = 0x1000
PAGE_MASK = 0xFFFFF
# OLANG text and TXP localized textures are safe to transplant.  YPK/OHD are
# voice payloads/headers changed by the English-region patch and must remain
# Japanese for this build.
ALLOWED_CHANGED_KINDS = {0x5D, 0x14}


class SlotError(RuntimeError):
    pass


def load_crypto_module():
    path = Path(__file__).with_name("Patch-StageDatPage.py")
    spec = importlib.util.spec_from_file_location("mgspw_stage_crypto", path)
    if spec is None or spec.loader is None:
        raise SlotError(f"cannot load crypto helpers: {path}")
    module = importlib.util.module_from_spec(spec)
    sys.modules[spec.name] = module
    spec.loader.exec_module(module)
    return module


CRYPTO = load_crypto_module()


def load_olang_module():
    path = Path(__file__).with_name("Build-JpnLooseOlang.py")
    spec = importlib.util.spec_from_file_location("mgspw_olang_merge", path)
    if spec is None or spec.loader is None:
        raise SlotError(f"cannot load OLANG merger: {path}")
    module = importlib.util.module_from_spec(spec)
    sys.modules[spec.name] = module
    spec.loader.exec_module(module)
    return module


OLANG = load_olang_module()


def sha256_path(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as stream:
        while chunk := stream.read(4 * 1024 * 1024):
            digest.update(chunk)
    return digest.hexdigest().upper()


def align_up(value: int, alignment: int) -> int:
    return (value + alignment - 1) // alignment * alignment


@dataclass(frozen=True)
class KeyEntry:
    first: int
    last: int
    hash_value: int
    unknown_a: int
    unknown_b: int

    @property
    def start(self) -> int:
        return (self.first & PAGE_MASK) * SECTOR

    @property
    def end(self) -> int:
        return (self.last & PAGE_MASK) * SECTOR

    @property
    def capacity(self) -> int:
        return self.end - self.start


@dataclass(frozen=True)
class PageHeader:
    unknown_a: int
    unknown_b: int
    padding: int
    compressed_size: int
    decompressed_size: int


@dataclass(frozen=True)
class Tag:
    file_id: int
    pad_a: int
    offset: int
    pad_b: int

    @property
    def kind(self) -> int:
        return self.file_id >> 24

    @property
    def is_file(self) -> bool:
        return self.kind not in (0x00, 0x7D, 0x7E, 0x7F)


@dataclass(frozen=True)
class CnfPage:
    data: bytes
    table_pad: int
    tags: tuple[Tag, ...]
    header_size: int
    data_base: int
    segments: dict[int, bytes]

    @property
    def signature(self) -> tuple[int, ...]:
        return tuple(tag.file_id for tag in self.tags)


def decode_key(path: Path, seed: int) -> tuple[bytes, tuple[int, int, int], list[KeyEntry]]:
    encrypted = path.read_bytes()
    plain = CRYPTO.outer_transform(encrypted, seed, 0)
    if len(plain) < 12 or (len(plain) - 12) % 20:
        raise SlotError(f"invalid HD SLOT KEY size: {path}")
    salts = struct.unpack_from("<III", plain, 0)
    entries = [KeyEntry(*struct.unpack_from("<IIiII", plain, offset)) for offset in range(12, len(plain), 20)]
    previous = 0
    for index, entry in enumerate(entries):
        if entry.start < SECTOR or entry.end <= entry.start or entry.start < previous:
            raise SlotError(f"invalid KEY entry {index} in {path}")
        previous = entry.end
    return plain, salts, entries


def encode_key(plain: bytes, entries: list[KeyEntry], seed: int) -> bytes:
    output = bytearray(plain)
    if len(output) != 12 + len(entries) * 20:
        raise SlotError("KEY plaintext length does not match its entry count")
    for index, entry in enumerate(entries):
        struct.pack_into(
            "<IIiII",
            output,
            12 + index * 20,
            entry.first,
            entry.last,
            entry.hash_value,
            entry.unknown_a,
            entry.unknown_b,
        )
    return CRYPTO.outer_transform(bytes(output), seed, 0)


def read_encrypted_page(path: Path, entry: KeyEntry) -> bytes:
    with path.open("rb") as stream:
        stream.seek(entry.start)
        data = stream.read(entry.capacity)
    if len(data) != entry.capacity:
        raise SlotError(f"truncated page at 0x{entry.start:X}: {path}")
    return data


def decode_page(path: Path, entry: KeyEntry, salts: tuple[int, int, int], seed: int) -> tuple[bytes, PageHeader]:
    encrypted = read_encrypted_page(path, entry)
    outer = CRYPTO.outer_transform(encrypted, seed, 0)
    inner, _ = CRYPTO.inner_transform(
        outer,
        CRYPTO.initial_inner_key(*salts[:2]),
        CRYPTO.inner_key_b(*salts),
    )
    if len(inner) < 16:
        raise SlotError("decoded SLOT page is shorter than its header")
    header = PageHeader(*struct.unpack_from("<HHIII", inner, 0))
    if header.compressed_size > len(inner) - 16:
        raise SlotError("SLOT compressed size exceeds page allocation")
    try:
        data = zlib.decompress(inner[16 : 16 + header.compressed_size])
    except zlib.error as error:
        raise SlotError(f"SLOT zlib decode failed at 0x{entry.start:X}: {error}") from error
    if len(data) != header.decompressed_size:
        raise SlotError(
            f"SLOT decompressed size mismatch at 0x{entry.start:X}: "
            f"header={header.decompressed_size}, actual={len(data)}"
        )
    return data, header


def encode_page(
    data: bytes,
    template: PageHeader,
    capacity: int,
    salts: tuple[int, int, int],
    seed: int,
) -> tuple[bytes, int]:
    compressed = zlib.compress(data, level=9)
    plain = struct.pack(
        "<HHIII",
        template.unknown_a,
        template.unknown_b,
        template.padding,
        len(compressed),
        len(data),
    ) + compressed
    if len(plain) > capacity:
        raise SlotError(f"rebuilt page needs {len(plain)} bytes but Japanese allocation is {capacity}")
    plain += bytes(capacity - len(plain))
    inner, _ = CRYPTO.inner_transform(
        plain,
        CRYPTO.initial_inner_key(*salts[:2]),
        CRYPTO.inner_key_b(*salts),
    )
    return CRYPTO.outer_transform(inner, seed, 0), len(compressed)


def parse_cnf(data: bytes) -> CnfPage:
    if len(data) < 8:
        raise SlotError("CNF page is shorter than its header")
    count, table_pad = struct.unpack_from("<II", data, 0)
    header_size = 8 + count * 16
    if not 2 <= count <= 10000 or header_size > len(data):
        raise SlotError(f"implausible CNF tag count: {count}")
    tags = tuple(Tag(*struct.unpack_from("<IIII", data, 8 + index * 16)) for index in range(count))
    data_base = align_up(header_size, SECTOR)
    if data_base > len(data):
        raise SlotError("CNF aligned data base exceeds page size")
    segments: dict[int, bytes] = {}
    for index, tag in enumerate(tags[:-1]):
        if not tag.is_file:
            continue
        next_tag = tags[index + 1]
        size = next_tag.offset - tag.offset if next_tag.offset >= tag.offset else 0
        start = data_base + tag.offset
        end = start + size
        if start < data_base or end > len(data):
            raise SlotError(f"CNF file tag {index} points outside the page")
        segments[index] = data[start:end]
    if not segments:
        raise SlotError("CNF page contains no extractable files")
    return CnfPage(data, table_pad, tags, header_size, data_base, segments)


def rebuild_cnf(template: CnfPage, replacements: dict[int, bytes]) -> bytes:
    tags = list(template.tags)
    payload = bytearray()
    for index, tag in enumerate(tags):
        if not tag.is_file:
            continue
        segment = replacements.get(index, template.segments[index])
        tags[index] = Tag(tag.file_id, tag.pad_a, len(payload), tag.pad_b)
        payload.extend(segment)
    region_size = len(payload)
    tags = [
        Tag(tag.file_id, tag.pad_a, region_size if tag.kind == 0x7F else tag.offset, tag.pad_b)
        for tag in tags
    ]
    output = bytearray(struct.pack("<II", len(tags), template.table_pad))
    for tag in tags:
        output.extend(struct.pack("<IIII", tag.file_id, tag.pad_a, tag.offset, tag.pad_b))
    output.extend(template.data[template.header_size : template.data_base])
    output.extend(payload)
    return bytes(output)


def merge_olang_segment(
    target: bytes,
    original: bytes,
    chinese: bytes,
    file_id: int,
    work_root: Path,
) -> tuple[bytes, dict]:
    name = f"{file_id & 0xFFFFFF:06x}.olang"
    # Some embedded RBX dialects have no regional layout difference and use a
    # table variant not handled by the multilingual loose-file parser.  When
    # the authoritative Japanese and English records are byte-identical, the
    # Chinese record is already a structurally exact replacement.
    if target == original:
        return chinese, {
            "target": name,
            "same_plaintext_layout_as_mlg": True,
            "direct_identical_layout_replacement": True,
            "mapped_japanese_reference_count": 0,
            "changed_japanese_reference_count": 0,
            "unmapped_japanese_reference_count": 0,
        }
    paths = []
    for directory, data in (("target", target), ("original", original), ("chinese", chinese)):
        path = work_root / directory / name
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_bytes(data)
        paths.append(path)
    merged_encrypted, detail = OLANG.merge_file(paths[0], paths[1], paths[2])
    # Loose OLANGs are filename-stream encrypted, but SLOT CNF records contain
    # plaintext RBX.  merge_file intentionally returns the loose-file form;
    # decode it once before putting the RBX back into the compressed page.
    merged = OLANG.outer_transform(merged_encrypted, OLANG.filename_seed(paths[0]))
    if not merged.startswith(b"RBX\x00"):
        raise SlotError(f"embedded OLANG merge did not return RBX for {name}")
    # CNF file offsets are 16-byte aligned.  Padding belongs to the container,
    # not to the filename-derived OLANG stream.
    merged += bytes((-len(merged)) % 16)
    return merged, detail


def find_changed_pages(original_dat: Path, patched_dat: Path, entries: list[KeyEntry]) -> list[int]:
    changed: list[int] = []
    with original_dat.open("rb") as original, patched_dat.open("rb") as patched:
        for index, entry in enumerate(entries):
            original.seek(entry.start)
            patched.seek(entry.start)
            if original.read(entry.capacity) != patched.read(entry.capacity):
                changed.append(index)
    return changed


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--jpn-dat", type=Path, required=True)
    parser.add_argument("--jpn-key", type=Path, required=True)
    parser.add_argument("--eng-original-dat", type=Path, required=True)
    parser.add_argument("--eng-key", type=Path, required=True)
    parser.add_argument("--cn-dat", type=Path, required=True)
    parser.add_argument("--output", type=Path, required=True)
    parser.add_argument("--output-key", type=Path, required=True)
    parser.add_argument("--report", type=Path, required=True)
    args = parser.parse_args()
    if args.output.resolve() in (args.jpn_dat.resolve(), args.eng_original_dat.resolve(), args.cn_dat.resolve()):
        parser.error("refusing to overwrite an input SLOT DAT")
    if args.output_key.resolve() in (args.jpn_key.resolve(), args.eng_key.resolve()):
        parser.error("refusing to overwrite an input SLOT KEY")

    seed = CRYPTO.filename_seed(args.eng_key)
    _, eng_salts, eng_entries = decode_key(args.eng_key, seed)
    jpn_key_plain, jpn_salts, jpn_entries = decode_key(args.jpn_key, seed)
    if eng_salts != jpn_salts:
        raise SlotError("English and Japanese SLOT salts differ")
    if args.eng_original_dat.stat().st_size != args.cn_dat.stat().st_size:
        raise SlotError("English original and Chinese-patched SLOT sizes differ")

    changed_pages = find_changed_pages(args.eng_original_dat, args.cn_dat, eng_entries)
    if len(changed_pages) != 110:
        raise SlotError(f"expected 110 Chinese-patched pages, found {len(changed_pages)}")

    jpn_cache: dict[int, tuple[bytes, PageHeader, CnfPage]] = {}

    def get_jpn(index: int) -> tuple[bytes, PageHeader, CnfPage]:
        if index not in jpn_cache:
            raw, header = decode_page(args.jpn_dat, jpn_entries[index], jpn_salts, seed)
            jpn_cache[index] = (raw, header, parse_cnf(raw))
        return jpn_cache[index]

    patch_jobs: list[dict] = []
    extension_counts: collections.Counter[str] = collections.Counter()
    skipped_extension_counts: collections.Counter[str] = collections.Counter()
    changed_file_count = 0
    olang_mapped_refs = 0
    olang_changed_refs = 0
    olang_work = tempfile.TemporaryDirectory(prefix="mgspw-slot-olang-")
    olang_work_root = Path(olang_work.name)
    for eng_index in changed_pages:
        eng_raw, _ = decode_page(args.eng_original_dat, eng_entries[eng_index], eng_salts, seed)
        cn_raw, _ = decode_page(args.cn_dat, eng_entries[eng_index], eng_salts, seed)
        eng_cnf = parse_cnf(eng_raw)
        cn_cnf = parse_cnf(cn_raw)
        if eng_cnf.signature != cn_cnf.signature:
            raise SlotError(f"Chinese patch changed CNF tag identities on English page {eng_index}")
        if rebuild_cnf(eng_cnf, {}) != eng_raw or rebuild_cnf(cn_cnf, {}) != cn_raw:
            raise SlotError(f"CNF reconstruction is not byte-exact on English page {eng_index}")

        candidates: list[int] = []
        # The Japanese archive has two extra pages, both inserted rather than
        # removed, so a semantic peer is at the English index or +1/+2.
        for jpn_index in range(eng_index, min(len(jpn_entries), eng_index + 3)):
            if get_jpn(jpn_index)[2].signature == eng_cnf.signature:
                candidates.append(jpn_index)
        if len(candidates) != 1:
            raise SlotError(f"English page {eng_index} has {len(candidates)} nearby Japanese CNF matches: {candidates}")
        jpn_index = candidates[0]
        jpn_raw, jpn_header, jpn_cnf = get_jpn(jpn_index)
        if rebuild_cnf(jpn_cnf, {}) != jpn_raw:
            raise SlotError(f"CNF reconstruction is not byte-exact on Japanese page {jpn_index}")

        source_changed_indices = [
            index
            for index in eng_cnf.segments
            if eng_cnf.segments[index] != cn_cnf.segments[index]
        ]
        if not source_changed_indices:
            raise SlotError(f"changed encrypted page {eng_index} contains no changed CNF files")
        changed_indices = [index for index in source_changed_indices if eng_cnf.tags[index].kind in ALLOWED_CHANGED_KINDS]
        for index in source_changed_indices:
            if index not in changed_indices:
                skipped_extension_counts[f"0x{eng_cnf.tags[index].kind:02X}"] += 1
        if not changed_indices:
            continue
        if any(index not in jpn_cnf.segments for index in changed_indices):
            raise SlotError(f"Japanese page {jpn_index} is missing a changed CNF file")
        replacements: dict[int, bytes] = {}
        olang_details: list[dict] = []
        for index in changed_indices:
            tag = jpn_cnf.tags[index]
            if tag.kind == 0x5D:
                try:
                    replacement, detail = merge_olang_segment(
                        jpn_cnf.segments[index],
                        eng_cnf.segments[index],
                        cn_cnf.segments[index],
                        tag.file_id,
                        olang_work_root,
                    )
                except Exception as error:
                    raise SlotError(
                        f"embedded OLANG merge failed on Japanese page {jpn_index}, "
                        f"tag {index}, file 0x{tag.file_id:08X}: {error}"
                    ) from error
                if detail["unmapped_japanese_reference_count"]:
                    raise SlotError(
                        f"embedded OLANG 0x{tag.file_id:08X} on Japanese page {jpn_index} "
                        f"has {detail['unmapped_japanese_reference_count']} unmapped Japanese references"
                    )
                olang_mapped_refs += detail["mapped_japanese_reference_count"]
                olang_changed_refs += detail["changed_japanese_reference_count"]
                olang_details.append(detail)
                replacements[index] = replacement
            else:
                replacements[index] = cn_cnf.segments[index]
        merged = rebuild_cnf(jpn_cnf, replacements)
        merged_cnf = parse_cnf(merged)
        for index in jpn_cnf.segments:
            expected = replacements.get(index, jpn_cnf.segments[index])
            if merged_cnf.segments[index] != expected:
                raise SlotError(f"merged CNF verification failed at Japanese page {jpn_index}, tag {index}")

        try:
            encoded, compressed_size = encode_page(
                merged,
                jpn_header,
                jpn_entries[jpn_index].capacity,
                jpn_salts,
                seed,
            )
        except SlotError as error:
            raise SlotError(f"fixed-layout Japanese page {jpn_index} cannot hold merged text: {error}") from error
        for index in changed_indices:
            extension_counts[f"0x{jpn_cnf.tags[index].kind:02X}"] += 1
        changed_file_count += len(changed_indices)
        patch_jobs.append(
            {
                "eng_page": eng_index,
                "jpn_page": jpn_index,
                "entry": jpn_entries[jpn_index],
                "merged": merged,
                "header": jpn_header,
                "encoded": encoded,
                "olang_details": olang_details,
                "changed_tag_indices": changed_indices,
                "changed_file_ids": [f"0x{jpn_cnf.tags[index].file_id:08X}" for index in changed_indices],
                "packed_size": compressed_size,
            }
        )

    target_pages = [job["jpn_page"] for job in patch_jobs]
    if len(set(target_pages)) != len(target_pages):
        raise SlotError("multiple English pages mapped to the same Japanese page")

    input_hash = sha256_path(args.jpn_dat)
    args.output.parent.mkdir(parents=True, exist_ok=True)
    shutil.copyfile(args.jpn_dat, args.output)
    with args.output.open("r+b") as output:
        for job in patch_jobs:
            output.seek(job["entry"].start)
            output.write(job["encoded"])
    if args.output.stat().st_size != args.jpn_dat.stat().st_size:
        raise SlotError("fixed-layout SLOT DAT size changed")

    args.output_key.parent.mkdir(parents=True, exist_ok=True)
    shutil.copyfile(args.jpn_key, args.output_key)
    _, output_salts, output_entries = decode_key(args.output_key, seed)
    if output_salts != jpn_salts or output_entries != jpn_entries:
        raise SlotError("copied Japanese KEY verification failed")
    if sha256_path(args.jpn_dat) != input_hash:
        raise SlotError("Japanese input SLOT changed during the operation")

    for job in patch_jobs:
        round_trip, _ = decode_page(args.output, job["entry"], jpn_salts, seed)
        if round_trip != job["merged"]:
            raise SlotError(f"output round-trip failed on Japanese page {job['jpn_page']}")

    report = {
        "mode": "file-level Japanese SLOT merge",
        "jpn_input": str(args.jpn_dat.resolve()),
        "jpn_input_sha256": input_hash,
        "eng_original": str(args.eng_original_dat.resolve()),
        "eng_original_sha256": sha256_path(args.eng_original_dat),
        "cn_source": str(args.cn_dat.resolve()),
        "cn_source_sha256": sha256_path(args.cn_dat),
        "output": str(args.output.resolve()),
        "output_sha256": sha256_path(args.output),
        "output_key": str(args.output_key.resolve()),
        "output_key_sha256": sha256_path(args.output_key),
        "eng_page_count": len(eng_entries),
        "jpn_page_count": len(jpn_entries),
        "changed_source_pages": len(changed_pages),
        "patched_jpn_pages": len(patch_jobs),
        "changed_files": changed_file_count,
        "changed_extension_ids": dict(sorted(extension_counts.items())),
        "skipped_voice_extension_ids": dict(sorted(skipped_extension_counts.items())),
        "key_unchanged": True,
        "page_offsets_unchanged": True,
        "output_size_growth": 0,
        "embedded_olang_mapped_japanese_references": olang_mapped_refs,
        "embedded_olang_changed_japanese_references": olang_changed_refs,
        "round_trip_verified": True,
        "pages": [
            {
                "eng_page": job["eng_page"],
                "jpn_page": job["jpn_page"],
                "jpn_offset": job["entry"].start,
                "jpn_capacity": job["entry"].capacity,
                "replacement_compressed_size": job["packed_size"],
                "changed_tag_indices": job["changed_tag_indices"],
                "changed_file_ids": job["changed_file_ids"],
            }
            for job in patch_jobs
        ],
    }
    args.report.parent.mkdir(parents=True, exist_ok=True)
    args.report.write_text(json.dumps(report, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    olang_work.cleanup()
    print(json.dumps({key: report[key] for key in ("output_sha256", "output_key_sha256", "patched_jpn_pages", "changed_files", "changed_extension_ids", "skipped_voice_extension_ids", "output_size_growth")}))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
