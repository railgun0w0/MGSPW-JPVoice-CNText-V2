from __future__ import annotations

import importlib.util
import struct
import sys
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
SPEC = importlib.util.spec_from_file_location(
    "mgspw_font_builder_phase1",
    ROOT / "tools" / "build_mgspw_cn_fonts.py",
)
assert SPEC is not None and SPEC.loader is not None
BUILDER = importlib.util.module_from_spec(SPEC)
sys.modules[SPEC.name] = BUILDER
SPEC.loader.exec_module(BUILDER)


def test_rendered_text_removes_controls_but_keeps_ruby_payload_and_layout_space():
    text = "甲<R=乙,おつ> <I=ICON><$1>%02d%2d$NAME%s\\n<HUNTING QUEST>"
    assert BUILDER.rendered_text(text) == "甲乙おつ <HUNTING QUEST>"


def test_production_corpus_grammar_inventory_uses_observed_tokens():
    rows, _metadata = BUILDER.load_production_corpus(
        ROOT / "build/translation/compiled_translation_manifest.csv",
        ROOT / "translations/briefing",
    )
    audits = BUILDER.control_token_audit(rows)
    by_token = {(item.token, item.classification): item for item in audits}
    assert by_token[("%02d", "PLACEHOLDER")].occurrence_count == 52
    assert by_token[("%2d", "PLACEHOLDER")].occurrence_count == 4
    assert by_token[("<$1>", "CONTROL")].occurrence_count == 12
    assert by_token[("<BAD STATE>", "VISIBLE")].occurrence_count == 7
    assert all(item.classification != "AMBIGUOUS" for item in audits)
    for absent in ("<MISSION>", "<ALERT>", "<HUNTING QUEST>", "%u", "%x", "%.2f"):
        assert all(item.token != absent for item in audits)


def test_clean_00c7_phase2a_integration_is_deterministic(tmp_path):
    base = BUILDER.load_clean_font(
        "00c7c9f9.xpr", ROOT / "font/JPN/00c7c9f9.xpr"
    )
    source_font = Path(r"C:\Windows\Fonts\Noto Sans SC Bold (TrueType).otf")
    assert source_font.is_file()
    required = {0x4E00, 0x4E8C, 0x9FA5}
    first = BUILDER.build_clean_00c7_fixture(
        base,
        source_font,
        tmp_path / "first",
        face_index=0,
        required_codepoints=required,
        charset_source_hash="test-charset",
    )
    second = BUILDER.build_clean_00c7_fixture(
        base,
        source_font,
        tmp_path / "second",
        face_index=0,
        required_codepoints=required,
        charset_source_hash="test-charset",
    )
    assert first["plaintext_xpr_sha256"] == second["plaintext_xpr_sha256"]
    assert first["encrypted_xpr_sha256"] == second["encrypted_xpr_sha256"]
    encrypted = (tmp_path / "first" / "00c7c9f9.xpr").read_bytes()
    decrypted = BUILDER.outer_transform(encrypted, BUILDER.filename_seed("00c7c9f9.xpr"))
    parsed = BUILDER.XprFont(decrypted)
    assert parsed.texture.width == parsed.texture.height == parsed.texture.pitch == 4096
    assert parsed.font_data.record_prefix == struct.pack(">H", len(parsed.font_data.glyphs))
    assert all(parsed.font_data.charmap[cp] != 0 for cp in required)


def test_category_flags_distinguish_han_kana_ascii_and_non_bmp():
    entries = [
        BUILDER.CharsetEntry(ord("汉"), 2, ("YPK_GTT",)),
        BUILDER.CharsetEntry(ord("カ"), 1, ("OHD",)),
        BUILDER.CharsetEntry(ord("A"), 3, ("SLOT_OLANG",)),
        BUILDER.CharsetEntry(0x20000, 1, ("BRIEFING_NBE",)),
    ]
    flags = [BUILDER.category_flags(entry) for entry in entries]
    assert flags[0]["han"] and not flags[0]["kana"]
    assert flags[1]["kana"] and not flags[1]["han"]
    assert flags[2]["ascii"] and flags[2]["latin"]
    assert flags[3]["han"] and flags[3]["non_bmp"]


def test_shelf_packing_is_deterministic_and_not_square_division():
    rectangles = [
        BUILDER.Rectangle("wide", 3000, 100),
        BUILDER.Rectangle("narrow", 1000, 100),
        BUILDER.Rectangle("tall", 20, 200),
    ]
    first = BUILDER.pack_shelf_ffd(rectangles, width=4096, height=4096)
    second = BUILDER.pack_shelf_ffd(list(reversed(rectangles)), width=4096, height=4096)
    assert first == second
    assert first.rectangle_count == 3
    assert first.required_area == 3000 * 100 + 1000 * 100 + 20 * 200
    assert first.packed_height == 200
    assert not first.overflow


def test_shelf_packing_reports_geometry_overflow():
    result = BUILDER.pack_shelf_ffd(
        [BUILDER.Rectangle("too-wide", 4097, 1)], width=4096, height=4096
    )
    assert result.overflow
