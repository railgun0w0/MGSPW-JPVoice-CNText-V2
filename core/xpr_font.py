"""Parser and structural rebuilder for MGSPW PC ``FONT/*.xpr`` files.

The files are filename-keyed/encrypted outside this module.  This module only
accepts and emits decrypted XPR2 bytes so parsing, resource replacement, and
outer encryption can be tested independently.
"""

from __future__ import annotations

import struct
from dataclasses import dataclass
from typing import Iterable, Mapping, Sequence


XPR_MAGIC = b"XPR2"
RESOURCE_DESCRIPTOR_SIZE = 24
FONT_CHARMAP_OFFSET = 0x16
FONT_LAST_CODE_OFFSET = 0x14
GLYPH_RECORD_SIZE = 16


class XprFormatError(ValueError):
    pass


def align_up(value: int, alignment: int, residue: int = 0) -> int:
    if alignment <= 0:
        raise ValueError("alignment must be positive")
    return ((value - residue + alignment - 1) // alignment) * alignment + residue


@dataclass(frozen=True)
class XprResource:
    index: int
    kind: str
    name: str
    descriptor_offset: int
    offset: int
    size: int
    unused0: int
    name_offset: int
    unused1: int
    payload: bytes


@dataclass(frozen=True)
class GlyphRecord:
    u0: int
    v0: int
    u1: int
    v1: int
    bearing_x_raw: int
    width: int
    advance: int
    reserved: int

    @property
    def bearing_x(self) -> int:
        return self.bearing_x_raw if self.bearing_x_raw < 0x8000 else self.bearing_x_raw - 0x10000

    @property
    def packed(self) -> bytes:
        return struct.pack(
            ">8H",
            self.u0,
            self.v0,
            self.u1,
            self.v1,
            self.bearing_x_raw,
            self.width,
            self.advance,
            self.reserved,
        )

    def with_uv(self, u0: int, v0: int, u1: int, v1: int) -> "GlyphRecord":
        return GlyphRecord(
            u0,
            v0,
            u1,
            v1,
            self.bearing_x_raw,
            self.width,
            self.advance,
            self.reserved,
        )


@dataclass(frozen=True)
class FontData:
    payload: bytes
    magic: int
    cell_height: float
    cell_height_2: float
    last_code: int
    charmap: tuple[int, ...]
    record_offset: int
    record_prefix: bytes
    glyphs: tuple[GlyphRecord, ...]
    suffix: bytes

    @classmethod
    def parse(cls, payload: bytes) -> "FontData":
        if len(payload) < FONT_CHARMAP_OFFSET:
            raise XprFormatError("USER/FontData is shorter than its fixed header")
        magic = struct.unpack_from(">I", payload, 0)[0]
        cell_height = struct.unpack_from(">f", payload, 4)[0]
        cell_height_2 = struct.unpack_from(">f", payload, 0x10)[0]
        last_code = struct.unpack_from(">H", payload, FONT_LAST_CODE_OFFSET)[0]
        map_end = FONT_CHARMAP_OFFSET + 2 * (last_code + 1)
        if map_end > len(payload):
            raise XprFormatError("USER/FontData charmap leaves the resource")
        charmap = struct.unpack_from(f">{last_code + 1}H", payload, FONT_CHARMAP_OFFSET)
        aligned_record_offset = align_up(map_end, 8)
        if aligned_record_offset > len(payload):
            raise XprFormatError("USER/FontData glyph alignment leaves the resource")

        # MGSPW has two USER variants.  0007/000e begin records directly at
        # the 8-byte boundary.  001c/00c7 store a big-endian u16 glyph count
        # first.  Both otherwise use the same 16-byte record structure.
        available = len(payload) - aligned_record_offset
        remainder = available % GLYPH_RECORD_SIZE
        record_prefix = b""
        if remainder == 2 and available >= 2:
            declared = struct.unpack_from(">H", payload, aligned_record_offset)[0]
            if declared == (available - 2) // GLYPH_RECORD_SIZE:
                record_prefix = payload[aligned_record_offset : aligned_record_offset + 2]
        record_offset = aligned_record_offset + len(record_prefix)
        remainder = (len(payload) - record_offset) % GLYPH_RECORD_SIZE
        glyph_end = len(payload) - remainder
        glyphs = tuple(
            GlyphRecord(*struct.unpack_from(">8H", payload, offset))
            for offset in range(record_offset, glyph_end, GLYPH_RECORD_SIZE)
        )
        if not glyphs:
            raise XprFormatError("USER/FontData has no glyph records")
        if any(index >= len(glyphs) for index in charmap):
            raise XprFormatError("USER/FontData charmap references a missing glyph record")
        return cls(
            payload=payload,
            magic=magic,
            cell_height=cell_height,
            cell_height_2=cell_height_2,
            last_code=last_code,
            charmap=tuple(charmap),
            record_offset=record_offset,
            record_prefix=record_prefix,
            glyphs=glyphs,
            suffix=payload[glyph_end:],
        )

    def mapped(self) -> dict[int, int]:
        return {codepoint: glyph for codepoint, glyph in enumerate(self.charmap) if glyph}

    def append(
        self,
        mappings: Mapping[int, GlyphRecord],
    ) -> tuple[bytes, dict[int, int]]:
        """Append glyph records and return ``(payload, codepoint->new index)``.

        Existing mappings and records are immutable.  Input order is retained,
        allowing a caller to define one canonical layout deterministically.
        """

        duplicate = sorted(code for code in mappings if code <= self.last_code and self.charmap[code])
        if duplicate:
            raise XprFormatError(
                "cannot append already-mapped codepoints: "
                + ", ".join(f"U+{code:04X}" for code in duplicate[:8])
            )
        if any(not 0 <= code <= 0xFFFF for code in mappings):
            raise XprFormatError("FontData charmap supports BMP codepoints only")
        if len(self.glyphs) + len(mappings) > 0xFFFF:
            raise XprFormatError("glyph index exceeds the u16 charmap limit")

        new_last = max((self.last_code, *mappings.keys())) if mappings else self.last_code
        new_charmap = list(self.charmap) + [0] * (new_last - self.last_code)
        appended_indices: dict[int, int] = {}
        new_glyphs = list(self.glyphs)
        for codepoint, glyph in mappings.items():
            glyph_index = len(new_glyphs)
            new_glyphs.append(glyph)
            new_charmap[codepoint] = glyph_index
            appended_indices[codepoint] = glyph_index

        prefix = bytearray(self.payload[:FONT_CHARMAP_OFFSET])
        struct.pack_into(">H", prefix, FONT_LAST_CODE_OFFSET, new_last)
        prefix.extend(struct.pack(f">{len(new_charmap)}H", *new_charmap))
        prefix.extend(b"\0" * (align_up(len(prefix), 8) - len(prefix)))
        if self.record_prefix:
            if len(self.record_prefix) != 2:
                raise XprFormatError("unsupported FontData glyph-table prefix")
            prefix.extend(struct.pack(">H", len(new_glyphs)))
        prefix.extend(b"".join(glyph.packed for glyph in new_glyphs))
        prefix.extend(self.suffix)
        return bytes(prefix), appended_indices


@dataclass(frozen=True)
class FontTexture:
    header: bytes
    texels: bytes
    width: int
    height: int
    pitch: int
    data_format: int
    tiled: int
    endian: int

    @classmethod
    def parse(cls, header: bytes, texels: bytes) -> "FontTexture":
        if len(header) < 0x34:
            raise XprFormatError("TX2D/FontTexture header is shorter than 0x34 bytes")
        words = struct.unpack_from(">13I", header, 0)
        fetch0, fetch1, fetch2 = words[7:10]
        pitch = ((fetch0 >> 22) & 0x1FF) * 32
        tiled = (fetch0 >> 31) & 1
        data_format = fetch1 & 0x3F
        endian = (fetch1 >> 6) & 3
        width = (fetch2 & 0x1FFF) + 1
        height = ((fetch2 >> 13) & 0x1FFF) + 1
        if data_format != 2 or tiled or endian:
            raise XprFormatError(
                f"unsupported FontTexture format={data_format}, tiled={tiled}, endian={endian}"
            )
        if len(texels) != width * height:
            raise XprFormatError(
                f"FontTexture data size {len(texels)} != {width}x{height}"
            )
        if pitch < width:
            raise XprFormatError(f"FontTexture pitch {pitch} is smaller than width {width}")
        return cls(header, texels, width, height, pitch, data_format, tiled, endian)


class XprFont:
    """A parsed decrypted XPR2 font bundle."""

    def __init__(self, data: bytes):
        if len(data) < 0x10 or data[:4] != XPR_MAGIC:
            raise XprFormatError(f"not a decrypted XPR2 bundle: {data[:4]!r}")
        self.data = data
        self.header_size, self.data_size, self.resource_count = struct.unpack_from(">3I", data, 4)
        self.texture_data_offset = 0x0C + self.header_size
        if self.texture_data_offset + self.data_size != len(data):
            raise XprFormatError(
                "XPR size fields do not cover the file exactly: "
                f"texture=0x{self.texture_data_offset:X}+0x{self.data_size:X}, file=0x{len(data):X}"
            )
        descriptor_end = 0x10 + self.resource_count * RESOURCE_DESCRIPTOR_SIZE
        if descriptor_end > self.texture_data_offset:
            raise XprFormatError("XPR resource descriptor table leaves the header")

        resources: list[XprResource] = []
        for index in range(self.resource_count):
            descriptor = 0x10 + index * RESOURCE_DESCRIPTOR_SIZE
            kind_raw, relative, size, unused0, name_relative, unused1 = struct.unpack_from(
                ">4s5I", data, descriptor
            )
            offset = 0x0C + relative
            name_offset = 0x0C + name_relative
            if offset < descriptor_end or offset + size > self.texture_data_offset:
                raise XprFormatError(f"resource {index} has an illegal range")
            if name_offset < descriptor_end or name_offset >= self.texture_data_offset:
                raise XprFormatError(f"resource {index} has an illegal name offset")
            terminator = data.find(b"\0", name_offset, self.texture_data_offset)
            if terminator < 0:
                raise XprFormatError(f"resource {index} name is not terminated")
            try:
                kind = kind_raw.decode("ascii")
                name = data[name_offset:terminator].decode("ascii")
            except UnicodeDecodeError as error:
                raise XprFormatError(f"resource {index} has a non-ASCII type/name") from error
            resources.append(
                XprResource(
                    index,
                    kind,
                    name,
                    descriptor,
                    offset,
                    size,
                    unused0,
                    name_offset,
                    unused1,
                    data[offset : offset + size],
                )
            )
        ordered = sorted(resources, key=lambda resource: resource.offset)
        if any(left.offset + left.size > right.offset for left, right in zip(ordered, ordered[1:])):
            raise XprFormatError("XPR resources overlap")
        self.resources = tuple(resources)
        self._by_identity = {(resource.kind, resource.name): resource for resource in resources}
        if len(self._by_identity) != len(resources):
            raise XprFormatError("duplicate XPR resource identity")
        self.tx2d = self.resource("TX2D", "FontTexture")
        self.user = self.resource("USER", "FontData")
        self.texture = FontTexture.parse(
            self.tx2d.payload,
            data[self.texture_data_offset : self.texture_data_offset + self.data_size],
        )
        self.font_data = FontData.parse(self.user.payload)

    def resource(self, kind: str, name: str) -> XprResource:
        try:
            return self._by_identity[(kind, name)]
        except KeyError as error:
            raise XprFormatError(f"missing {kind}/{name} resource") from error

    def rebuild(
        self,
        replacements: Mapping[tuple[str, str], bytes] | None = None,
        texture_texels: bytes | None = None,
    ) -> bytes:
        """Rebuild from this bundle's topology with selected resource changes.

        Unreplaced resource payloads are copied byte-for-byte.  The raw atlas
        belongs to TX2D/FontTexture even though XPR stores it after the header.
        """

        replacements = dict(replacements or {})
        unknown = set(replacements) - set(self._by_identity)
        if unknown:
            raise XprFormatError(f"replacement targets do not exist: {sorted(unknown)}")
        texture_texels = self.texture.texels if texture_texels is None else texture_texels
        # Validate the replacement against the retained/replaced TX2D header.
        tx_header = replacements.get(("TX2D", "FontTexture"), self.tx2d.payload)
        FontTexture.parse(tx_header, texture_texels)

        ordered = sorted(self.resources, key=lambda resource: resource.offset)
        first_offset = ordered[0].offset
        output = bytearray(self.data[:first_offset])
        prior_original_end = first_offset
        new_offsets: dict[int, tuple[int, int]] = {}
        for resource in ordered:
            gap = self.data[prior_original_end : resource.offset]
            output.extend(gap)
            payload = replacements.get((resource.kind, resource.name), resource.payload)
            new_offset = len(output)
            output.extend(payload)
            new_offsets[resource.index] = (new_offset, len(payload))
            prior_original_end = resource.offset + resource.size

        # XPR texture data starts at the template's original 0x800 alignment
        # residue (0x1C for the four MGSPW font bundles).
        alignment = 0x800
        residue = self.texture_data_offset % alignment
        new_texture_offset = align_up(len(output), alignment, residue)
        output.extend(b"\0" * (new_texture_offset - len(output)))
        output.extend(texture_texels)

        struct.pack_into(">I", output, 4, new_texture_offset - 0x0C)
        struct.pack_into(">I", output, 8, len(texture_texels))
        for resource in self.resources:
            new_offset, new_size = new_offsets[resource.index]
            struct.pack_into(">I", output, resource.descriptor_offset + 4, new_offset - 0x0C)
            struct.pack_into(">I", output, resource.descriptor_offset + 8, new_size)

        rebuilt = bytes(output)
        XprFont(rebuilt)
        return rebuilt

    def replace_user(self, payload: bytes) -> bytes:
        FontData.parse(payload)
        return self.rebuild({("USER", "FontData"): payload})

    def replace_texture(self, texels: bytes, header: bytes | None = None) -> bytes:
        replacements = None if header is None else {("TX2D", "FontTexture"): header}
        return self.rebuild(replacements, texture_texels=texels)


def validate_glyph_rectangles(font_data: FontData, texture: FontTexture) -> list[str]:
    errors: list[str] = []
    for index, glyph in enumerate(font_data.glyphs):
        if glyph.u0 > glyph.u1 or glyph.v0 > glyph.v1:
            errors.append(f"glyph {index}: inverted UV rectangle")
        elif glyph.u1 > texture.width or glyph.v1 > texture.height:
            errors.append(
                f"glyph {index}: ({glyph.u0},{glyph.v0})-({glyph.u1},{glyph.v1}) "
                f"leaves {texture.width}x{texture.height} atlas"
            )
        if glyph.width != glyph.u1 - glyph.u0:
            errors.append(
                f"glyph {index}: width {glyph.width} != UV width {glyph.u1 - glyph.u0}"
            )
    return errors


def glyph_bytes(glyphs: Iterable[GlyphRecord]) -> bytes:
    return b"".join(glyph.packed for glyph in glyphs)
