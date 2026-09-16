from __future__ import annotations

import struct

from core.xpr_font import FontData, GlyphRecord, XprFont


def synthetic_xpr(counted: bool = False) -> bytes:
    width, height = 32, 8
    texture_header = bytearray(0x34)
    struct.pack_into(">13I", texture_header, 0, *([0] * 13))
    fetch0 = (1 << 22)  # pitch = 32
    fetch1 = 2
    fetch2 = (width - 1) | ((height - 1) << 13)
    struct.pack_into(">3I", texture_header, 0x1C, fetch0, fetch1, fetch2)

    last_code = 0x41
    user = bytearray(0x16)
    struct.pack_into(">I", user, 0, 5)
    struct.pack_into(">f", user, 4, 8.0)
    struct.pack_into(">f", user, 0x10, 8.0)
    struct.pack_into(">H", user, 0x14, last_code)
    charmap = [0] * (last_code + 1)
    charmap[0x20] = 1
    charmap[0x41] = 2
    user.extend(struct.pack(f">{len(charmap)}H", *charmap))
    user.extend(b"\0" * ((-len(user)) % 8))
    if counted:
        user.extend(struct.pack(">H", 3))
    user.extend(GlyphRecord(0, 0, 2, 8, 0, 2, 3, 0).packed)
    user.extend(GlyphRecord(2, 0, 3, 8, 0, 1, 2, 0).packed)
    user.extend(GlyphRecord(3, 0, 7, 8, 0, 4, 5, 0).packed)
    if not counted:
        user.extend(b"\0\0")

    resource_count = 2
    prefix = bytearray(0x5C)
    prefix[:4] = b"XPR2"
    struct.pack_into(">I", prefix, 0x0C, resource_count)
    prefix[0x40:0x4C] = b"FontTexture\0"
    prefix[0x4C:0x55] = b"FontData\0"
    tx_offset = len(prefix)
    prefix.extend(texture_header)
    user_offset = len(prefix)
    prefix.extend(user)
    texture_offset = ((len(prefix) - 0x1C + 0x7FF) // 0x800) * 0x800 + 0x1C
    prefix.extend(b"\0" * (texture_offset - len(prefix)))
    texels = bytearray(width * height)
    texels[3:7] = b"\x20\x40\x80\xFF"
    prefix.extend(texels)

    struct.pack_into(">II", prefix, 4, texture_offset - 0x0C, len(texels))
    struct.pack_into(">4s5I", prefix, 0x10, b"TX2D", tx_offset - 0x0C, 0x34, 0, 0x34, 0)
    struct.pack_into(">4s5I", prefix, 0x28, b"USER", user_offset - 0x0C, len(user), 0, 0x40, 0)
    return bytes(prefix)


def test_parse_and_noop_rebuild_is_exact():
    data = synthetic_xpr()
    parsed = XprFont(data)
    assert parsed.texture.width == 32
    assert parsed.texture.height == 8
    assert parsed.font_data.charmap[0x41] == 2
    assert parsed.rebuild() == data


def test_user_append_preserves_existing_indices_and_glyphs():
    parsed = XprFont(synthetic_xpr())
    base = parsed.font_data
    new_record = GlyphRecord(7, 0, 11, 8, 0, 4, 5, 0)
    user, indices = base.append({0x42: new_record})
    rebuilt = XprFont(parsed.replace_user(user))
    assert indices == {0x42: 3}
    assert rebuilt.font_data.charmap[: len(base.charmap)] == base.charmap
    assert rebuilt.font_data.charmap[0x42] == 3
    assert rebuilt.font_data.glyphs[: len(base.glyphs)] == base.glyphs
    assert rebuilt.font_data.glyphs[3] == new_record
    assert rebuilt.texture.texels == parsed.texture.texels


def test_texture_replacement_preserves_user_resource():
    parsed = XprFont(synthetic_xpr())
    texels = bytearray(parsed.texture.texels)
    texels[-1] = 0x7F
    rebuilt = XprFont(parsed.replace_texture(bytes(texels)))
    assert rebuilt.user.payload == parsed.user.payload
    assert rebuilt.tx2d.payload == parsed.tx2d.payload
    assert rebuilt.texture.texels[-1] == 0x7F


def test_counted_glyph_table_variant_updates_count_on_append():
    parsed = XprFont(synthetic_xpr(counted=True))
    assert parsed.font_data.record_prefix == b"\0\x03"
    new_record = GlyphRecord(7, 0, 11, 8, 0, 4, 5, 0)
    user, indices = parsed.font_data.append({0x42: new_record})
    rebuilt = XprFont(parsed.replace_user(user))
    assert indices == {0x42: 3}
    assert rebuilt.font_data.record_prefix == b"\0\x04"
    assert len(rebuilt.font_data.glyphs) == 4
    assert rebuilt.font_data.glyphs[:3] == parsed.font_data.glyphs
