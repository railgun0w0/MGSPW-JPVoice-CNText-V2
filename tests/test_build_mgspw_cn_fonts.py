from __future__ import annotations

import importlib.util
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
    text = "甲<R=乙,おつ> <I=ICON>$NAME%s\\n<HUNTING QUEST>"
    assert BUILDER.rendered_text(text) == "甲乙おつ <HUNTING QUEST>"


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
