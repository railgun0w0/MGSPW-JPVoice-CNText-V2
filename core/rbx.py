"""Strict RBX/OLANG parsing and metadata-preserving text-body rebuild."""

from __future__ import annotations

import hashlib
import struct
from dataclasses import dataclass
from typing import Sequence


RBX_MAGIC = b"RBX\x00"


class RbxFormatError(ValueError):
    pass


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
    entity_offset: int
    reference_offset: int
    body_offset: int
    entities: tuple[Entity, ...]
    references: tuple[Reference, ...]


def parse_rbx(data: bytes, label: str = "RBX") -> Rbx:
    if len(data) < 32 or data[:4] != RBX_MAGIC:
        raise RbxFormatError(f"{label}: not a raw RBX OLANG")
    header_offset, entity_offset, reference_offset, body_offset = struct.unpack_from(
        "<IIII", data, 16
    )
    if not (32 <= header_offset <= entity_offset <= reference_offset <= body_offset <= len(data)):
        raise RbxFormatError(f"{label}: invalid section offsets")
    entity_span = reference_offset - entity_offset
    reference_span = body_offset - reference_offset
    if entity_span % 8 or reference_span % 12:
        raise RbxFormatError(f"{label}: invalid entity/reference table sizes")

    entities = tuple(
        Entity(*struct.unpack_from("<IHH", data, entity_offset + index * 8))
        for index in range(entity_span // 8)
    )
    references: list[Reference] = []
    for index in range(reference_span // 12):
        language_key, relative, flag = struct.unpack_from(
            "<III", data, reference_offset + index * 12
        )
        absolute = body_offset + relative
        if not body_offset <= absolute < len(data):
            raise RbxFormatError(f"{label}: reference {index} points outside body")
        terminator = data.find(b"\x00", absolute)
        if terminator < 0:
            raise RbxFormatError(f"{label}: reference {index} has no NUL terminator")
        try:
            text = data[absolute:terminator].decode("utf-8", errors="strict")
        except UnicodeDecodeError as error:
            raise RbxFormatError(f"{label}: reference {index} is not strict UTF-8") from error
        references.append(Reference(language_key, relative, flag, text))

    for index, entity in enumerate(entities):
        if entity.reference_index + entity.reference_count > len(references):
            raise RbxFormatError(f"{label}: entity {index} reference span is outside table")
    return Rbx(
        data,
        header_offset,
        entity_offset,
        reference_offset,
        body_offset,
        entities,
        tuple(references),
    )


def rebuild_rbx_texts(parsed: Rbx, texts: Sequence[str], label: str = "RBX") -> bytes:
    if len(texts) != len(parsed.references):
        raise RbxFormatError(
            f"{label}: replacement count {len(texts)} != reference count {len(parsed.references)}"
        )
    body = bytearray()
    offsets: dict[bytes, int] = {}
    relative_offsets: list[int] = []
    for index, text in enumerate(texts):
        if not isinstance(text, str):
            raise RbxFormatError(f"{label}: replacement {index} is not text")
        if not text and parsed.references[index].text:
            raise RbxFormatError(f"{label}: replacement {index} clears a non-empty reference")
        encoded = text.encode("utf-8", errors="strict")
        if b"\x00" in encoded:
            raise RbxFormatError(f"{label}: replacement {index} contains an interior NUL")
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
        raise RbxFormatError(f"{label}: rebuilt reference table does not meet body offset")
    output.extend(body)
    rebuilt = bytes(output)

    verified = parse_rbx(rebuilt, f"{label}:rebuilt")
    if [reference.text for reference in verified.references] != list(texts):
        raise RbxFormatError(f"{label}: rebuilt text round-trip mismatch")
    if rebuilt[: parsed.reference_offset] != parsed.raw[: parsed.reference_offset]:
        raise RbxFormatError(f"{label}: header/aux/entity bytes changed")
    if [(reference.language_key, reference.flag) for reference in verified.references] != [
        (reference.language_key, reference.flag) for reference in parsed.references
    ]:
        raise RbxFormatError(f"{label}: reference metadata changed")
    return rebuilt


def structural_signature(parsed: Rbx) -> str:
    packed = bytearray(struct.pack("<II", len(parsed.entities), len(parsed.references)))
    for entity in parsed.entities:
        packed.extend(struct.pack("<IHH", entity.key, entity.reference_index, entity.reference_count))
    for reference in parsed.references:
        packed.extend(struct.pack("<II", reference.language_key, reference.flag))
    return hashlib.sha256(packed).hexdigest().upper()
