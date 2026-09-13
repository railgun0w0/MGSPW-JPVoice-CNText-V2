#!/usr/bin/env python3
"""Build a Japanese init/cache.dar with Chinese strings in Japanese OLANG slots.

The Japanese DAR layout, OLANG headers, entity tables, reference language keys,
and every non-target payload are preserved.  Only string bodies and their
reference offsets are rebuilt for the six known init-language OLANG files.
"""

from __future__ import annotations

import argparse
import hashlib
import json
import struct
from collections import Counter, defaultdict
from dataclasses import dataclass
from pathlib import Path


TARGETS = {
    "lang_communicationstelop.olang": "lang_communicationstelop_en.olang",
    "lang_demotelop.olang": "lang_demotelop_en.olang",
    "lang_http_error.olang": "lang_http_error_en.olang",
    "lang_online_error.olang": "lang_online_error_en.olang",
    "lang_pw_common.olang": "lang_pw_common_en.olang",
    "lang_system.olang": "lang_system_en.olang",
}
RBX_MAGIC = b"RBX\x00"


class FormatError(RuntimeError):
    pass


def sha256(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest().upper()


def align(value: int, boundary: int) -> int:
    return (value + boundary - 1) & ~(boundary - 1)


@dataclass(frozen=True)
class DarEntry:
    name: str
    data: bytes


def parse_dar(data: bytes) -> list[DarEntry]:
    if len(data) < 4:
        raise FormatError("DAR is shorter than its file-count field")
    count = struct.unpack_from("<I", data, 0)[0]
    if not 1 <= count <= 10000:
        raise FormatError(f"implausible DAR file count: {count}")
    entries: list[DarEntry] = []
    cursor = 4
    names: set[str] = set()
    for index in range(count):
        terminator = data.find(b"\x00", cursor)
        if terminator < 0:
            raise FormatError(f"DAR entry {index} has no filename terminator")
        try:
            name = data[cursor:terminator].decode("ascii", errors="strict")
        except UnicodeDecodeError as error:
            raise FormatError(f"DAR entry {index} filename is not ASCII") from error
        if not name or name in names:
            raise FormatError(f"DAR entry {index} has empty or duplicate name: {name!r}")
        names.add(name)
        cursor = align(terminator + 1, 4)
        if cursor + 4 > len(data):
            raise FormatError(f"DAR entry {name} has no size field")
        size = struct.unpack_from("<I", data, cursor)[0]
        cursor = align(cursor + 4, 16)
        end = cursor + size
        if end >= len(data):
            raise FormatError(f"DAR entry {name} payload exceeds archive")
        payload = data[cursor:end]
        if data[end] != 0:
            raise FormatError(f"DAR entry {name} lacks its trailing NUL byte")
        entries.append(DarEntry(name, payload))
        cursor = end + 1
    if any(data[cursor:]):
        raise FormatError("DAR has unexplained non-zero trailing bytes")
    return entries


def build_dar(entries: list[DarEntry]) -> bytes:
    output = bytearray(struct.pack("<I", len(entries)))
    for entry in entries:
        output.extend(entry.name.encode("ascii") + b"\x00")
        output.extend(b"\x00" * (align(len(output), 4) - len(output)))
        output.extend(struct.pack("<I", len(entry.data)))
        output.extend(b"\x00" * (align(len(output), 16) - len(output)))
        output.extend(entry.data)
        output.append(0)
    return bytes(output)


@dataclass(frozen=True)
class Entity:
    key: int
    reference_index: int
    reference_count: int


@dataclass(frozen=True)
class Reference:
    language_key: int
    body_offset: int
    flag: int
    text: str


@dataclass(frozen=True)
class Rbx:
    raw: bytes
    header_offset: int
    reference_offset: int
    body_offset: int
    entities: tuple[Entity, ...]
    references: tuple[Reference, ...]


def parse_rbx(data: bytes, label: str) -> Rbx:
    if len(data) < 32 or data[:4] != RBX_MAGIC:
        raise FormatError(f"{label}: not a raw RBX OLANG")
    header_offset, entity_offset, reference_offset, body_offset = struct.unpack_from("<IIII", data, 16)
    if not (32 <= header_offset <= entity_offset <= reference_offset <= body_offset <= len(data)):
        raise FormatError(f"{label}: invalid section offsets")
    # Most loose OLANGs place the entity table eight bytes after the section
    # header, but some SLOT-embedded RBX dialects use a larger auxiliary header.
    # The second offset field is authoritative for both forms.
    entity_span = reference_offset - entity_offset
    reference_span = body_offset - reference_offset
    if entity_span < 0 or entity_span % 8 or reference_span % 12:
        raise FormatError(f"{label}: invalid entity/reference table sizes")
    entity_count = entity_span // 8
    reference_count = reference_span // 12
    entities = tuple(
        Entity(*struct.unpack_from("<IHH", data, entity_offset + index * 8))
        for index in range(entity_count)
    )
    raw_refs = tuple(
        struct.unpack_from("<III", data, reference_offset + index * 12)
        for index in range(reference_count)
    )
    references: list[Reference] = []
    for index, (language_key, relative, flag) in enumerate(raw_refs):
        absolute = body_offset + relative
        if not body_offset <= absolute < len(data):
            raise FormatError(f"{label}: reference {index} points outside body")
        terminator = data.find(b"\x00", absolute)
        if terminator < 0:
            raise FormatError(f"{label}: reference {index} has no text terminator")
        try:
            text = data[absolute:terminator].decode("utf-8", errors="strict")
        except UnicodeDecodeError as error:
            raise FormatError(f"{label}: reference {index} is not UTF-8") from error
        references.append(Reference(language_key, relative, flag, text))
    for index, entity in enumerate(entities):
        if entity.reference_index + entity.reference_count > len(references):
            raise FormatError(f"{label}: entity {index} reference span is out of range")
    return Rbx(data, header_offset, reference_offset, body_offset, entities, tuple(references))


def entity_identities(entities: tuple[Entity, ...]) -> list[tuple[int, int]]:
    occurrences: Counter[int] = Counter()
    result: list[tuple[int, int]] = []
    for entity in entities:
        result.append((entity.key, occurrences[entity.key]))
        occurrences[entity.key] += 1
    return result


def merge_rbx(target_data: bytes, source_data: bytes, label: str) -> tuple[bytes, dict]:
    target = parse_rbx(target_data, f"{label}:target")
    source = parse_rbx(source_data, f"{label}:source")
    target_ids = entity_identities(target.entities)
    source_ids = entity_identities(source.entities)
    source_by_id = {identity: source.entities[index] for index, identity in enumerate(source_ids)}
    if len(source_by_id) != len(source.entities):
        raise FormatError(f"{label}: source entity identities are not unique")
    missing = [identity for identity in target_ids if identity not in source_by_id]
    if missing:
        raise FormatError(f"{label}: {len(missing)} target entities have no Chinese match")

    target_key_frequency = Counter(entity.key for entity in target.entities)
    source_key_frequency = Counter(entity.key for entity in source.entities)
    candidates: dict[int, list[tuple[tuple[int, int, int], str, tuple[int, int]]]] = defaultdict(list)
    for target_index, identity in enumerate(target_ids):
        target_entity = target.entities[target_index]
        source_entity = source_by_id[identity]
        if target_entity.reference_count != source_entity.reference_count:
            raise FormatError(f"{label}: entity {identity} has a reference-span mismatch")
        priority = (
            target_key_frequency[target_entity.key],
            source_key_frequency[source_entity.key],
            target_index,
        )
        for ordinal in range(target_entity.reference_count):
            target_ref = target_entity.reference_index + ordinal
            source_ref = source_entity.reference_index + ordinal
            candidates[target_ref].append((priority, source.references[source_ref].text, identity))

    uncovered = [index for index in range(len(target.references)) if index not in candidates]
    if uncovered:
        raise FormatError(f"{label}: target references are not mapped: {uncovered}")
    chosen: list[str] = []
    conflict_report: list[dict] = []
    for reference_index in range(len(target.references)):
        options = sorted(candidates[reference_index], key=lambda item: item[0])
        best_priority = options[0][0][:2]
        equally_best = {text for priority, text, _ in options if priority[:2] == best_priority}
        if len(equally_best) != 1:
            raise FormatError(f"{label}: unresolved mapping conflict at reference {reference_index}")
        text = next(iter(equally_best))
        chosen.append(text)
        distinct = {option[1] for option in options}
        if len(distinct) > 1:
            conflict_report.append(
                {
                    "reference_index": reference_index,
                    "selected_text": text,
                    "selected_identity": [f"0x{options[0][2][0]:08X}", options[0][2][1]],
                    "discarded_texts": sorted(distinct - {text}),
                }
            )

    body = bytearray()
    text_offsets: dict[bytes, int] = {}
    new_offsets: list[int] = []
    for text in chosen:
        encoded = text.encode("utf-8")
        if encoded not in text_offsets:
            text_offsets[encoded] = len(body)
            body.extend(encoded)
            body.append(0)
            if len(body) % 2:
                body.append(0)
        new_offsets.append(text_offsets[encoded])

    output = bytearray(target.raw[: target.reference_offset])
    for reference, relative in zip(target.references, new_offsets):
        output.extend(struct.pack("<III", reference.language_key, relative, reference.flag))
    if len(output) != target.body_offset:
        raise FormatError(f"{label}: rebuilt reference table does not meet body offset")
    output.extend(body)
    rebuilt = bytes(output)
    verified = parse_rbx(rebuilt, f"{label}:rebuilt")
    if [ref.text for ref in verified.references] != chosen:
        raise FormatError(f"{label}: rebuilt text round-trip failed")
    if rebuilt[: target.reference_offset] != target.raw[: target.reference_offset]:
        raise FormatError(f"{label}: target header/entity data changed")
    if [(r.language_key, r.flag) for r in verified.references] != [
        (r.language_key, r.flag) for r in target.references
    ]:
        raise FormatError(f"{label}: target reference metadata changed")
    return rebuilt, {
        "target_size": len(target_data),
        "output_size": len(rebuilt),
        "target_sha256": sha256(target_data),
        "source_sha256": sha256(source_data),
        "output_sha256": sha256(rebuilt),
        "target_entities": len(target.entities),
        "source_entities": len(source.entities),
        "references_mapped": len(chosen),
        "unique_output_strings": len(text_offsets),
        "resolved_conflicts": conflict_report,
        "target_language_keys": sorted({f"0x{r.language_key:08X}" for r in target.references}),
        "source_language_keys": sorted({f"0x{r.language_key:08X}" for r in source.references}),
    }


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--jpn-cache-dar", type=Path, required=True)
    parser.add_argument("--cn-cache-dar", type=Path, required=True)
    parser.add_argument("--output", type=Path, required=True)
    parser.add_argument("--report", type=Path, required=True)
    args = parser.parse_args()

    jpn_raw = args.jpn_cache_dar.read_bytes()
    cn_raw = args.cn_cache_dar.read_bytes()
    jpn_entries = parse_dar(jpn_raw)
    cn_entries = parse_dar(cn_raw)
    jpn_by_name = {entry.name: entry for entry in jpn_entries}
    cn_by_name = {entry.name: entry for entry in cn_entries}
    missing_jpn = sorted(set(TARGETS) - set(jpn_by_name))
    missing_cn = sorted(set(TARGETS.values()) - set(cn_by_name))
    if missing_jpn or missing_cn:
        raise FormatError(f"missing target/source entries: JPN={missing_jpn}, CN={missing_cn}")

    replacements: dict[str, bytes] = {}
    details: dict[str, dict] = {}
    for target_name, source_name in TARGETS.items():
        replacement, detail = merge_rbx(
            jpn_by_name[target_name].data,
            cn_by_name[source_name].data,
            target_name,
        )
        replacements[target_name] = replacement
        detail["source_entry"] = source_name
        details[target_name] = detail

    output_entries = [DarEntry(entry.name, replacements.get(entry.name, entry.data)) for entry in jpn_entries]
    output_raw = build_dar(output_entries)
    verified_entries = parse_dar(output_raw)
    if [entry.name for entry in verified_entries] != [entry.name for entry in jpn_entries]:
        raise FormatError("rebuilt DAR entry order changed")
    changed = []
    for before, after in zip(jpn_entries, verified_entries):
        if before.data != after.data:
            changed.append(before.name)
        if before.name not in TARGETS and before.data != after.data:
            raise FormatError(f"non-target DAR entry changed: {before.name}")
    if changed != list(TARGETS):
        raise FormatError(f"unexpected changed-entry list: {changed}")

    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.report.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_bytes(output_raw)
    report = {
        "jpn_cache_dar": str(args.jpn_cache_dar.resolve()),
        "cn_cache_dar": str(args.cn_cache_dar.resolve()),
        "output": str(args.output.resolve()),
        "jpn_dar_sha256": sha256(jpn_raw),
        "cn_dar_sha256": sha256(cn_raw),
        "output_dar_sha256": sha256(output_raw),
        "jpn_entry_count": len(jpn_entries),
        "cn_entry_count": len(cn_entries),
        "changed_entries": changed,
        "unchanged_entries_verified": len(jpn_entries) - len(changed),
        "details": details,
    }
    args.report.write_text(json.dumps(report, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    print(json.dumps(report, ensure_ascii=False))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
