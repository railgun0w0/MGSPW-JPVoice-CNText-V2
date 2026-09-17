#!/usr/bin/env python3
"""Build selector-aware MGSPW XPR fonts from the four clean JPN bundles."""

from __future__ import annotations

import argparse
import csv
import hashlib
import json
import re
import shutil
import sys
import unicodedata
from collections import Counter
from dataclasses import dataclass
from pathlib import Path
from typing import Iterable

from PIL import Image, ImageDraw, ImageFont


ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from core.pc_crypto import filename_seed, outer_transform
from core.xpr_font import FontData, FontTexture, GlyphRecord, XprFont, validate_glyph_rectangles


LANCZOS = getattr(Image, "Resampling", Image).LANCZOS


FONT_NAMES = ("0007ccd8.xpr", "00c7c9f9.xpr", "001cbbd1.xpr", "000ebbe8.xpr")
PRODUCTION_DIRS = (
    ("YPK_GTT", "ypk_gtt"),
    ("OHD", "ohd"),
    ("SLOT_OLANG", "slot_olang"),
    ("LOOSE_OLANG", "loose_olang"),
    ("STAGEDAT_OLANG", "stagedat_olang"),
    ("BRIEFING", "briefing"),
)

# Only these paths have direct in-game evidence that they use the small XPR
# selector.  Do not broaden this list based on UI appearance alone.
SMALL_SELECTOR_FIXTURES = (
    {
        "resource_class": "LOOSE_OLANG",
        "file_id": "007E2F18",
        "unique_index": 390,
        "scene": "title menu NEW GAME",
    },
    {
        "resource_class": "LOOSE_OLANG",
        "file_id": "007E2F18",
        "unique_index": 397,
        "scene": "title menu LOAD GAME",
    },
    {
        "resource_class": "LOOSE_OLANG",
        "file_id": "007E2F18",
        "unique_index": 402,
        "scene": "title menu DELETE",
    },
)

# In-game screenshots supplied after the first build directly confirm these
# STAGEDAT OLANG resources on the small XPR face.  Once a resource is confirmed,
# include all of its production rows rather than just the photographed strings.
SMALL_SELECTOR_RESOURCES = (
    {
        "resource_class": "STAGEDAT_OLANG",
        "file_id": "LANG_MYOUTER_TOP.OLANG",
        "scene": "Mother Base report/menu (runtime screenshot 2026-09-14)",
    },
    {
        "resource_class": "STAGEDAT_OLANG",
        "file_id": "LANG_MISSION_INFO.OLANG",
        "scene": "Mission Selector titles/descriptions (runtime screenshot 2026-09-14)",
    },
    {
        "resource_class": "STAGEDAT_OLANG",
        "file_id": "LANG_SYSTEM.OLANG",
        "scene": "load/save system UI (runtime screenshot 2026-09-14)",
    },
    {
        "resource_class": "STAGEDAT_OLANG",
        "file_id": "LANG_TITLEMENU.OLANG",
        "scene": "title/load UI (title small-face runtime evidence)",
    },
)

RUBY_RE = re.compile(r"<R=([^,<>]*),([^<>]*)>")
ANGLE_RE = re.compile(r"<[^<>]*>")
DOLLAR_RE = re.compile(r"\$[A-Za-z0-9_]+")
PRINTF_RE = re.compile(r"%(?:\d+\$)?[-+#0-9.*hlLzjt]*[diuoxXfFeEgGaAcspn]")
BRACE_RE = re.compile(r"\{(?:\d+|[A-Za-z_][A-Za-z0-9_]*)\}")


class FontBuildError(RuntimeError):
    pass


@dataclass
class Corpus:
    codepoints: set[int]
    files: int
    rows: int
    by_class: dict[str, int]
    ruby_tokens: int
    excluded_control_tokens: int
    supplementary: set[int]


@dataclass
class GlyphSource:
    record: GlyphRecord
    bitmap: bytes
    bitmap_width: int
    bitmap_height: int
    origin: str


@dataclass
class FaceBuild:
    name: str
    required: set[int]
    raw_data_xpr: bytes
    raw_texture_xpr: bytes
    font_data: FontData
    texture: FontTexture
    appended: dict[int, int]
    origins: dict[int, str]
    missing: set[int]
    first_append_index: int
    original_glyph_count: int
    original_mapped_count: int
    atlas_changed_bytes: int
    highest_used_y: int
    allocated_area: int
    validations: dict[str, object]


def sha256_bytes(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def sha256_file(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for block in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(block)
    return digest.hexdigest()


def decrypt_xpr(path: Path) -> tuple[bytes, bytes]:
    encrypted = path.read_bytes()
    raw = outer_transform(encrypted, filename_seed(path.name))
    if raw[:4] != b"XPR2":
        raise FontBuildError(f"{path}: filename-keyed decrypt did not produce XPR2")
    return encrypted, raw


def is_visible_codepoint(codepoint: int) -> bool:
    category = unicodedata.category(chr(codepoint))
    return not category.startswith("C") and category not in {"Zl", "Zp"}


def visible_text(text: str) -> tuple[str, int, int]:
    """Return visible glyph text, Ruby occurrence count, excluded-token count.

    Both the base and annotation of ``<R=base,ruby>`` are drawn and therefore
    both contribute to the required charset.  Other known controls and
    placeholders do not.
    """

    ruby_count = 0
    excluded = 0

    def ruby(match: re.Match) -> str:
        nonlocal ruby_count
        ruby_count += 1
        return match.group(1) + match.group(2)

    text = RUBY_RE.sub(ruby, text)
    for pattern in (ANGLE_RE, DOLLAR_RE, PRINTF_RE, BRACE_RE):
        text, count = pattern.subn("", text)
        excluded += count
    return text, ruby_count, excluded


def read_csv_rows(path: Path) -> list[dict[str, str]]:
    with path.open("r", encoding="utf-8-sig", newline="") as handle:
        return list(csv.DictReader(handle))


def production_corpus(root: Path) -> Corpus:
    codepoints: set[int] = set()
    supplementary: set[int] = set()
    file_count = row_count = ruby_count = excluded = 0
    by_class: Counter[str] = Counter()
    for resource_class, directory in PRODUCTION_DIRS:
        paths = sorted((root / "translations" / directory).glob("*.csv"))
        for path in paths:
            rows = read_csv_rows(path)
            if rows and "cn_text" not in rows[0]:
                continue
            file_count += 1
            for row in rows:
                if "cn_text" not in row:
                    continue
                row_count += 1
                by_class[resource_class] += 1
                rendered, rubies, tokens = visible_text(row.get("cn_text", ""))
                ruby_count += rubies
                excluded += tokens
                for character in rendered:
                    codepoint = ord(character)
                    if not is_visible_codepoint(codepoint):
                        continue
                    if codepoint > 0xFFFF:
                        supplementary.add(codepoint)
                    else:
                        codepoints.add(codepoint)
    return Corpus(
        codepoints,
        file_count,
        row_count,
        dict(by_class),
        ruby_count,
        excluded,
        supplementary,
    )


def small_fixture_corpus(root: Path) -> tuple[set[int], list[dict[str, object]]]:
    paths: dict[tuple[str, str], Path] = {
        (resource_class, path.stem.upper()): path
        for resource_class, directory in PRODUCTION_DIRS
        for path in (root / "translations" / directory).glob("*.csv")
    }
    required: set[int] = set()
    evidence: list[dict[str, object]] = []
    cache: dict[Path, list[dict[str, str]]] = {}
    for resource in SMALL_SELECTOR_RESOURCES:
        key = (str(resource["resource_class"]), str(resource["file_id"]).upper())
        path = paths.get(key)
        if path is None:
            raise FontBuildError(f"small selector resource has no production CSV: {key}")
        rows = cache.setdefault(path, read_csv_rows(path))
        resource_codes: set[int] = set()
        for row in rows:
            rendered, _, _ = visible_text(row.get("cn_text", ""))
            resource_codes.update(
                ord(character)
                for character in rendered
                if is_visible_codepoint(ord(character))
            )
        required.update(resource_codes)
        evidence.append(
            {
                **resource,
                "scope": "whole_production_resource",
                "production_rows": len(rows),
                "codepoints": sorted(resource_codes),
            }
        )
    for fixture in SMALL_SELECTOR_FIXTURES:
        key = (str(fixture["resource_class"]), str(fixture["file_id"]).upper())
        path = paths.get(key)
        if path is None:
            raise FontBuildError(f"small selector fixture has no production CSV: {key}")
        rows = cache.setdefault(path, read_csv_rows(path))
        matches = [row for row in rows if int(row["unique_index"]) == fixture["unique_index"]]
        if len(matches) != 1:
            raise FontBuildError(f"small selector fixture {key}/{fixture['unique_index']} is not unique")
        text = matches[0]["cn_text"]
        rendered, _, _ = visible_text(text)
        codepoints = {ord(character) for character in rendered if is_visible_codepoint(ord(character))}
        required.update(codepoints)
        evidence.append(
            {
                **fixture,
                "scope": "single_production_row",
                "cn_text": text,
                "codepoints": sorted(codepoints),
            }
        )
    return required, evidence


def glyph_source(font: XprFont, codepoint: int, origin: str) -> GlyphSource | None:
    if codepoint > font.font_data.last_code:
        return None
    glyph_index = font.font_data.charmap[codepoint]
    if glyph_index == 0:
        return None
    record = font.font_data.glyphs[glyph_index]
    width = record.u1 - record.u0
    height = record.v1 - record.v0
    if width <= 0 or height <= 0 or record.u1 > font.texture.width or record.v1 > font.texture.height:
        return None
    bitmap = bytearray()
    for y in range(record.v0, record.v1):
        start = y * font.texture.width + record.u0
        bitmap.extend(font.texture.texels[start : start + width])
    return GlyphSource(record, bytes(bitmap), width, height, origin)


def raster_source(
    codepoint: int,
    font_path: Path,
    cell_height: int,
    face_name: str,
    target_width_override: int | None = None,
) -> GlyphSource | None:
    character = chr(codepoint)
    target_width = target_width_override or (58 if 0x2E80 <= codepoint <= 0x9FFF else 56)
    target_height = cell_height
    font_size = max(8, int(round(cell_height * 0.82)))
    font = ImageFont.truetype(str(font_path), font_size)
    probe = Image.new("L", (cell_height * 3, cell_height * 3), 0)
    draw = ImageDraw.Draw(probe)
    draw.text((cell_height, cell_height), character, font=font, fill=255)
    box = probe.getbbox()
    if box is None:
        return None
    glyph = probe.crop(box)
    max_width = target_width - 2
    max_height = target_height - 6
    scale = min(1.0, max_width / glyph.width, max_height / glyph.height)
    if scale < 1.0:
        glyph = glyph.resize(
            (max(1, round(glyph.width * scale)), max(1, round(glyph.height * scale))),
            LANCZOS,
        )
    canvas = Image.new("L", (target_width, target_height), 0)
    x = (target_width - glyph.width) // 2
    y = (target_height - glyph.height) // 2
    canvas.paste(glyph, (x, y))
    record = GlyphRecord(0, 0, target_width, target_height, 0, target_width, target_width + 4, 0)
    return GlyphSource(record, canvas.tobytes(), target_width, target_height, f"raster:{font_path.name}:{face_name}")


def write_bitmap(
    atlas: bytearray,
    atlas_width: int,
    atlas_height: int,
    x: int,
    y: int,
    source: GlyphSource,
) -> None:
    if x < 0 or y < 0 or x + source.bitmap_width > atlas_width or y + source.bitmap_height > atlas_height:
        raise FontBuildError("glyph bitmap leaves atlas")
    for row in range(source.bitmap_height):
        source_start = row * source.bitmap_width
        target_start = (y + row) * atlas_width + x
        atlas[target_start : target_start + source.bitmap_width] = source.bitmap[
            source_start : source_start + source.bitmap_width
        ]


def fit_source(source: GlyphSource, width: int, height: int) -> GlyphSource:
    if source.bitmap_width == width and source.bitmap_height == height:
        return source
    image = Image.frombytes("L", (source.bitmap_width, source.bitmap_height), source.bitmap)
    box = image.getbbox()
    if box is None:
        record = GlyphRecord(0, 0, width, height, 0, width, width + 4, source.record.reserved)
        return GlyphSource(record, bytes(width * height), width, height, source.origin)
    glyph = image.crop(box)
    scale = min(1.0, max(1, width - 2) / glyph.width, max(1, height - 2) / glyph.height)
    if scale < 1.0:
        glyph = glyph.resize(
            (max(1, round(glyph.width * scale)), max(1, round(glyph.height * scale))),
            LANCZOS,
        )
    canvas = Image.new("L", (width, height), 0)
    canvas.paste(glyph, ((width - glyph.width) // 2, (height - glyph.height) // 2))
    metric_scale = width / source.bitmap_width
    bearing_x = round(source.record.bearing_x * metric_scale)
    metric_width = max(1, round(source.record.width * metric_scale))
    advance = max(metric_width, round(source.record.advance * metric_scale))
    record = GlyphRecord(
        0,
        0,
        width,
        height,
        bearing_x & 0xFFFF,
        metric_width,
        advance,
        source.record.reserved,
    )
    return GlyphSource(record, canvas.tobytes(), width, height, source.origin)


def build_face(
    name: str,
    required: set[int],
    clean_data_raw: bytes,
    clean_texture_raw: bytes,
    font_path: Path,
    donors: Iterable[tuple[str, XprFont]] = (),
    texture_height: int | None = None,
    raster_width: int | None = None,
    reuse_texture_resident: bool = False,
) -> FaceBuild:
    data_template = XprFont(clean_data_raw)
    texture_template = XprFont(clean_texture_raw)
    base = data_template.font_data
    base_map = base.mapped()
    target_height = texture_height or texture_template.texture.height
    if target_height < texture_template.texture.height:
        raise FontBuildError(f"{name}: target texture height cannot shrink")
    texture_header = bytearray(texture_template.texture.header)
    if target_height != texture_template.texture.height:
        fetch2 = int.from_bytes(texture_header[0x24:0x28], "big")
        fetch2 &= ~(0x1FFF << 13)
        fetch2 |= (target_height - 1) << 13
        texture_header[0x24:0x28] = fetch2.to_bytes(4, "big")
    atlas = bytearray(texture_template.texture.texels)
    atlas.extend(b"\0" * (texture_template.texture.width * (target_height - texture_template.texture.height)))
    original_atlas = bytes(atlas)
    missing_from_base = sorted(required - set(base_map))
    supplementary = {code for code in missing_from_base if code > 0xFFFF}
    missing: set[int] = set(supplementary)
    append_records: dict[int, GlyphRecord] = {}
    origins: dict[int, str] = {code: "clean-jpn" for code in base_map}

    cell_height = round(base.cell_height)
    # A selector pair may intentionally leave an existing FontData rectangle
    # blank in the separately selected clean texture.  Required mapped glyphs
    # are painted into their immutable original UVs; index and metrics stay
    # untouched.
    for codepoint in sorted(required & set(base_map)):
        if chr(codepoint).isspace():
            continue
        record = base.glyphs[base_map[codepoint]]
        width = record.u1 - record.u0
        height = record.v1 - record.v0
        if width <= 0 or height <= 0:
            continue
        ink = any(
            any(atlas[row * texture_template.texture.width + record.u0 : row * texture_template.texture.width + record.u1])
            for row in range(record.v0, record.v1)
        )
        if ink:
            continue
        source = None
        for donor_name, donor in donors:
            source = glyph_source(donor, codepoint, donor_name)
            if source is not None:
                break
        if source is None:
            source = raster_source(codepoint, font_path, cell_height, name, raster_width)
        if source is not None:
            fitted = fit_source(source, width, height)
            write_bitmap(
                atlas,
                texture_template.texture.width,
                texture_template.texture.height,
                record.u0,
                record.v0,
                fitted,
            )
            origins[codepoint] = f"clean-jpn-slot+{source.origin}"

    x = 0
    y = max(record.v1 for record in base.glyphs)
    if y % cell_height:
        y = ((y + cell_height - 1) // cell_height) * cell_height

    for codepoint in missing_from_base:
        if codepoint > 0xFFFF:
            continue
        # The selector's texture XPR can already contain a useful glyph whose
        # mapping is absent from the separately selected data XPR.  Reusing
        # that immutable rectangle costs one appended USER record but no new
        # atlas space.  Only rectangles above the future append band are used.
        if reuse_texture_resident:
            resident = glyph_source(texture_template, codepoint, "clean-texture-resident")
            if resident is not None and resident.record.v1 <= y and any(resident.bitmap):
                append_records[codepoint] = resident.record
                origins[codepoint] = resident.origin
                continue
        source = None
        for donor_name, donor in donors:
            source = glyph_source(donor, codepoint, donor_name)
            if source is not None:
                break
        if source is None:
            source = raster_source(codepoint, font_path, cell_height, name, raster_width)
        if source is None:
            missing.add(codepoint)
            continue
        if source.bitmap_height != cell_height or (raster_width and source.bitmap_width != raster_width):
            source = fit_source(source, raster_width or source.bitmap_width, cell_height)
        if source.bitmap_height > cell_height:
            raise FontBuildError(
                f"{name} U+{codepoint:04X}: fitted source height {source.bitmap_height} > cell {cell_height}"
            )
        if x and x + source.bitmap_width > texture_template.texture.width:
            x = 0
            y += cell_height
        if y + source.bitmap_height > target_height:
            missing.add(codepoint)
            continue
        write_bitmap(
            atlas,
            texture_template.texture.width,
            target_height,
            x,
            y,
            source,
        )
        append_records[codepoint] = source.record.with_uv(
            x, y, x + source.bitmap_width, y + source.bitmap_height
        )
        origins[codepoint] = source.origin
        x += source.bitmap_width

    user_payload, appended = base.append(append_records)
    raw_data = data_template.replace_user(user_payload)
    raw_texture = texture_template.replace_texture(bytes(atlas), header=bytes(texture_header))
    output_data = XprFont(raw_data)
    output_texture = XprFont(raw_texture)
    rect_errors = validate_glyph_rectangles(output_data.font_data, output_texture.texture)

    original_map_preserved = all(
        output_data.font_data.charmap[codepoint] == glyph_index
        for codepoint, glyph_index in base_map.items()
    )
    original_glyphs_preserved = output_data.font_data.glyphs[: len(base.glyphs)] == base.glyphs
    append_only = (
        all(index >= len(base.glyphs) for index in appended.values())
        and sorted(appended.values()) == list(range(len(base.glyphs), len(base.glyphs) + len(appended)))
    )
    mapped_required = {
        code
        for code in required
        if code <= output_data.font_data.last_code and output_data.font_data.charmap[code]
    }
    missing.update(required - mapped_required)
    required_blank: list[int] = []
    for codepoint in sorted(mapped_required):
        if chr(codepoint).isspace():
            continue
        glyph = output_data.font_data.glyphs[output_data.font_data.charmap[codepoint]]
        ink = False
        for row in range(glyph.v0, glyph.v1):
            start = row * output_texture.texture.width + glyph.u0
            if any(output_texture.texture.texels[start : start + glyph.width]):
                ink = True
                break
        if not ink:
            required_blank.append(codepoint)

    allocated_area = sum(
        max(0, record.u1 - record.u0) * max(0, record.v1 - record.v0)
        for record in output_data.font_data.glyphs
    )
    header_static_preserved = (
        output_texture.tx2d.payload[:0x24] == texture_template.tx2d.payload[:0x24]
        and output_texture.tx2d.payload[0x28:] == texture_template.tx2d.payload[0x28:]
    )
    validations = {
        "original_charmap_preserved": original_map_preserved,
        "original_glyph_records_preserved": original_glyphs_preserved,
        "append_only": append_only,
        "glyph_rect_errors": rect_errors,
        "required_blank_glyphs": required_blank,
        "pair_consistent": not rect_errors and not required_blank and not missing,
        "data_unselected_tx2d_header_preserved": output_data.tx2d.payload == data_template.tx2d.payload,
        "data_unselected_texture_preserved": output_data.texture.texels == data_template.texture.texels,
        "texture_unselected_user_preserved": output_texture.user.payload == texture_template.user.payload,
        "texture_tx2d_header_static_fields_preserved": header_static_preserved,
        "texture_dimensions_expected": (
            output_texture.texture.width == texture_template.texture.width
            and output_texture.texture.height == target_height
        ),
        "data_reparse": True,
        "texture_reparse": True,
    }
    return FaceBuild(
        name=name,
        required=required,
        raw_data_xpr=raw_data,
        raw_texture_xpr=raw_texture,
        font_data=output_data.font_data,
        texture=output_texture.texture,
        appended=appended,
        origins=origins,
        missing=missing,
        first_append_index=len(base.glyphs),
        original_glyph_count=len(base.glyphs),
        original_mapped_count=len(base_map),
        atlas_changed_bytes=sum(a != b for a, b in zip(atlas, original_atlas)),
        highest_used_y=max(record.v1 for record in output_data.font_data.glyphs),
        allocated_area=allocated_area,
        validations=validations,
    )


def format_codepoint(codepoint: int) -> str:
    character = chr(codepoint)
    display = character if is_visible_codepoint(codepoint) else ""
    name = unicodedata.name(character, "UNNAMED")
    return f"U+{codepoint:04X}\t{display}\t{name}"


def write_charset(path: Path, title: str, codepoints: set[int], preface: Iterable[str] = ()) -> None:
    lines = [f"# {title}", *preface, f"# count={len(codepoints)}", "# codepoint\tchar\tunicode_name"]
    lines.extend(format_codepoint(codepoint) for codepoint in sorted(codepoints))
    path.write_text("\n".join(lines) + "\n", encoding="utf-8")


def write_layout(path: Path, face: FaceBuild) -> None:
    owners: dict[int, list[int]] = {}
    for codepoint, glyph_index in enumerate(face.font_data.charmap):
        if glyph_index:
            owners.setdefault(glyph_index, []).append(codepoint)
    with path.open("w", encoding="utf-8-sig", newline="") as handle:
        fields = (
            "codepoint",
            "char",
            "glyph_index",
            "u0",
            "v0",
            "u1",
            "v1",
            "width",
            "bearingX",
            "advance",
            "origin",
        )
        writer = csv.DictWriter(handle, fieldnames=fields, lineterminator="\n")
        writer.writeheader()
        for codepoint, glyph_index in enumerate(face.font_data.charmap):
            if not glyph_index:
                continue
            glyph = face.font_data.glyphs[glyph_index]
            writer.writerow(
                {
                    "codepoint": f"U+{codepoint:04X}",
                    "char": chr(codepoint) if is_visible_codepoint(codepoint) else "",
                    "glyph_index": glyph_index,
                    "u0": glyph.u0,
                    "v0": glyph.v0,
                    "u1": glyph.u1,
                    "v1": glyph.v1,
                    "width": glyph.width,
                    "bearingX": glyph.bearing_x,
                    "advance": glyph.advance,
                    "origin": face.origins.get(codepoint, "clean-jpn-shared"),
                }
            )


def compact_codes(codepoints: Iterable[int], width: int = 12) -> str:
    items = [f"U+{codepoint:04X}" for codepoint in sorted(codepoints)]
    if not items:
        return "(none)"
    return "\n".join(" ".join(items[index : index + width]) for index in range(0, len(items), width))


def face_json(face: FaceBuild) -> dict[str, object]:
    mapped = face.required - face.missing
    capacity = face.texture.width * face.texture.height
    return {
        "required_codepoints": len(face.required),
        "required": [f"U+{code:04X}" for code in sorted(face.required)],
        "mapped_codepoints": len(mapped),
        "missing_codepoints": len(face.missing),
        "missing": [f"U+{code:04X}" for code in sorted(face.missing)],
        "original_glyph_count": face.original_glyph_count,
        "original_mapped_count": face.original_mapped_count,
        "added_glyph_count": len(face.appended),
        "final_glyph_count": len(face.font_data.glyphs),
        "atlas": {
            "width": face.texture.width,
            "height": face.texture.height,
            "highest_used_y": face.highest_used_y,
            "allocated_rect_area": face.allocated_area,
            "allocated_rect_percent": round(100 * face.allocated_area / capacity, 4),
            "changed_texel_bytes": face.atlas_changed_bytes,
        },
        "validations": face.validations,
    }


def markdown_face(face: FaceBuild) -> str:
    data = face_json(face)
    atlas = data["atlas"]
    checks = data["validations"]
    check_lines = "\n".join(
        f"- {'PASS' if value is True or value == [] else 'FAIL'}: `{key}`"
        for key, value in checks.items()
    )
    return f"""## {face.name}

| item | result |
|---|---:|
| required codepoints | {data['required_codepoints']} |
| mapped codepoints | {data['mapped_codepoints']} |
| missing codepoints | {data['missing_codepoints']} |
| clean mapped / glyph records | {face.original_mapped_count} / {face.original_glyph_count} |
| added glyph count | {data['added_glyph_count']} |
| final glyph records | {data['final_glyph_count']} |
| atlas | {face.texture.width}×{face.texture.height} |
| highest canonical UV row | {atlas['highest_used_y']} / {face.texture.height} |
| allocated glyph-rectangle usage | {atlas['allocated_rect_percent']}% |
| changed atlas bytes | {atlas['changed_texel_bytes']} |
| FontData/FontTexture pair consistency | {'PASS' if checks['pair_consistent'] else 'FAIL'} |

### Required codepoints

```text
{compact_codes(face.required)}
```

### Missing codepoints

```text
{compact_codes(face.missing)}
```

### Validation

{check_lines}
"""


def verify_crypto(
    name: str,
    clean_encrypted: bytes,
    clean_raw: bytes,
    built_raw: bytes,
) -> tuple[bytes, dict[str, bool]]:
    seed = filename_seed(name)
    clean_reencrypted = outer_transform(clean_raw, seed)
    built_encrypted = outer_transform(built_raw, seed)
    built_decrypted = outer_transform(built_encrypted, seed)
    built_reencrypted = outer_transform(built_decrypted, seed)
    return built_encrypted, {
        "clean_decrypt_encrypt_roundtrip": clean_reencrypted == clean_encrypted,
        "built_encrypt_decrypt_roundtrip": built_decrypted == built_raw,
        "built_decrypt_encrypt_roundtrip": built_reencrypted == built_encrypted,
    }


def parse_args() -> argparse.Namespace:
    default_clean = Path(r"D:\GAME\test\JPN\MGS_PW\mgspw\FONT")
    default_donor = ROOT.parent / "JPVoice_CNText_Experimental" / "payload-stage2" / "mgspw" / "FONT"
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--clean-font-root", type=Path, default=default_clean)
    parser.add_argument("--large-donor", type=Path, default=default_donor / "0007ccd8.xpr")
    parser.add_argument("--secondary-donor", type=Path, default=default_donor / "000ebbe8.xpr")
    parser.add_argument("--fallback-font", type=Path, default=Path(r"C:\Windows\Fonts\Noto Sans SC Medium (TrueType).otf"))
    parser.add_argument("--output-root", type=Path, default=ROOT / "build" / "font_xpr_v2")
    return parser.parse_args()


def main() -> int:
    args = parse_args()
    clean_root = args.clean_font_root.resolve()
    output_root = args.output_root.resolve()
    allowed_root = (ROOT / "build").resolve()
    if output_root == allowed_root or allowed_root not in output_root.parents:
        raise FontBuildError(f"output must be a child of {allowed_root}")
    if not args.fallback_font.is_file():
        raise FontBuildError(f"fallback raster font does not exist: {args.fallback_font}")
    missing_inputs = [name for name in FONT_NAMES if not (clean_root / name).is_file()]
    if missing_inputs:
        raise FontBuildError(f"clean JPN XPR inputs missing: {missing_inputs}")
    if not args.large_donor.is_file() or not args.secondary_donor.is_file():
        raise FontBuildError("one or more read-only Chinese donor XPR files are missing")

    clean_hashes_before = {name: sha256_file(clean_root / name) for name in FONT_NAMES}
    encrypted: dict[str, bytes] = {}
    raw: dict[str, bytes] = {}
    for name in FONT_NAMES:
        encrypted[name], raw[name] = decrypt_xpr(clean_root / name)
        XprFont(raw[name])

    donor_fonts: list[tuple[str, XprFont]] = []
    for label, path in (("legacy-cn-a", args.large_donor), ("legacy-cn-b", args.secondary_donor)):
        _, donor_raw = decrypt_xpr(path)
        donor_fonts.append((label, XprFont(donor_raw)))

    corpus = production_corpus(ROOT)
    small_required, small_evidence = small_fixture_corpus(ROOT)
    large = build_face(
        "LARGE",
        corpus.codepoints,
        raw["0007ccd8.xpr"],
        raw["00c7c9f9.xpr"],
        args.fallback_font.resolve(),
        donor_fonts,
    )
    # Only screenshot-confirmed small resources and title fixtures contribute.
    # 1024 rows cannot fit that set, so grow one power-of-two step while keeping
    # the original width and avoiding the old 4096x4096 full-corpus payload.
    small = build_face(
        "SMALL",
        small_required,
        raw["001cbbd1.xpr"],
        raw["000ebbe8.xpr"],
        args.fallback_font.resolve(),
        (donor_fonts[1], donor_fonts[0]),
        texture_height=2048,
        raster_width=55,
        reuse_texture_resident=True,
    )

    output_root.mkdir(parents=True, exist_ok=True)
    font_output = output_root / "mgspw" / "FONT"
    font_output.mkdir(parents=True, exist_ok=True)
    built_raw = {
        "0007ccd8.xpr": large.raw_data_xpr,
        "00c7c9f9.xpr": large.raw_texture_xpr,
        "001cbbd1.xpr": small.raw_data_xpr,
        "000ebbe8.xpr": small.raw_texture_xpr,
    }
    crypto_checks: dict[str, dict[str, bool]] = {}
    output_files: dict[str, dict[str, object]] = {}
    for name in FONT_NAMES:
        built_encrypted, checks = verify_crypto(name, encrypted[name], raw[name], built_raw[name])
        crypto_checks[name] = checks
        path = font_output / name
        path.write_bytes(built_encrypted)
        reparsed = XprFont(outer_transform(path.read_bytes(), filename_seed(name)))
        checks["written_file_reparse"] = reparsed.data == built_raw[name]
        output_files[name] = {
            "path": str(path),
            "size": path.stat().st_size,
            "sha256": sha256_file(path),
        }

    clean_hashes_after = {name: sha256_file(clean_root / name) for name in FONT_NAMES}
    clean_inputs_unchanged = clean_hashes_before == clean_hashes_after
    for face in (large, small):
        face.validations["crypto_roundtrip_all_files"] = all(
            all(checks.values()) for checks in crypto_checks.values()
        )
        face.validations["clean_inputs_unchanged"] = clean_inputs_unchanged

    large_charset_path = output_root / "LARGE_XPR_REQUIRED_CHARSET.txt"
    small_charset_path = output_root / "SMALL_XPR_REQUIRED_CHARSET.txt"
    write_charset(
        large_charset_path,
        "LARGE XPR production visible charset",
        corpus.codepoints,
        (
            f"# production_files={corpus.files}",
            f"# production_rows={corpus.rows}",
            f"# ruby_tokens={corpus.ruby_tokens} (base and ruby annotation both included)",
            f"# excluded_control_or_placeholder_tokens={corpus.excluded_control_tokens}",
        ),
    )
    small_preface = [
        "# Scope: only UI/resources with direct small-selector runtime evidence.",
        "# Confirmed resources are included completely; no speculative global corpus is included.",
    ]
    for item in small_evidence:
        if item["scope"] == "whole_production_resource":
            small_preface.append(
                f"# {item['resource_class']}/{item['file_id']} scope=whole_resource "
                f"rows={item['production_rows']} scene={item['scene']}"
            )
        else:
            small_preface.append(
                f"# {item['resource_class']}/{item['file_id']} unique_index={item['unique_index']} "
                f"scene={item['scene']} text={json.dumps(item['cn_text'], ensure_ascii=False)}"
            )
    small_chinese = {code for code in small_required if 0x3400 <= code <= 0x9FFF}
    small_preface.append(f"# required_chinese_codepoints={len(small_chinese)}")
    write_charset(small_charset_path, "SMALL XPR required visible charset", small_required, small_preface)
    write_layout(output_root / "LARGE_XPR_CANONICAL_LAYOUT.csv", large)
    write_layout(output_root / "SMALL_XPR_CANONICAL_LAYOUT.csv", small)

    report_data = {
        "status": "PASS",
        "scope": "FONT/*.xpr only",
        "clean_font_root": str(clean_root),
        "clean_sha256": clean_hashes_before,
        "clean_inputs_unchanged": clean_inputs_unchanged,
        "production_corpus": {
            "files": corpus.files,
            "rows": corpus.rows,
            "rows_by_resource_class": corpus.by_class,
            "ruby_tokens": corpus.ruby_tokens,
            "excluded_control_or_placeholder_tokens": corpus.excluded_control_tokens,
            "supplementary_codepoints": [f"U+{code:X}" for code in sorted(corpus.supplementary)],
        },
        "large": face_json(large),
        "small": face_json(small),
        "small_selector_evidence": small_evidence,
        "crypto": crypto_checks,
        "outputs": output_files,
        "forbidden_resources_modified": [],
    }
    failures: list[str] = []
    if corpus.supplementary:
        failures.append("production visible corpus contains non-BMP codepoints")
    for face in (large, small):
        if face.missing:
            failures.append(f"{face.name} has missing codepoints")
        if not all(value is True or value == [] for value in face.validations.values()):
            failures.append(f"{face.name} validation failed")
    if not all(all(checks.values()) for checks in crypto_checks.values()):
        failures.append("crypto round-trip failed")
    if not clean_inputs_unchanged:
        failures.append("clean JPN input changed during build")
    if failures:
        report_data["status"] = "FAIL"
        report_data["failures"] = failures

    json_path = output_root / "FONT_XPR_BUILD_REPORT.json"
    json_path.write_text(json.dumps(report_data, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    markdown = f"""# MGSPW selector-aware XPR font build report

Status: **{report_data['status']}**  
Scope: `FONT/*.xpr` only. No TXP, STAGEDAT, translation, or clean JPN file was written.

## Inputs and construction

- Structural templates: the four clean JPN XPR files under `{clean_root}`.
- LARGE selector pair: `0007ccd8 USER/FontData` ↔ `00c7c9f9 TX2D/FontTexture`.
- SMALL selector pair: `001cbbd1 USER/FontData` ↔ `000ebbe8 TX2D/FontTexture`.
- Production corpus: {corpus.files} CSV files / {corpus.rows} approved rows; {corpus.ruby_tokens} Ruby tokens contributed both base and ruby display characters.
- Chinese bitmap donors are read-only legacy candidates; their XPR structure is never copied. `{args.fallback_font.name}` rasterizes donor misses.
- Canonical layouts: `LARGE_XPR_CANONICAL_LAYOUT.csv` and `SMALL_XPR_CANONICAL_LAYOUT.csv`.

{markdown_face(large)}

{markdown_face(small)}

## SMALL selector evidence and capacity decision

Runtime screenshots confirm `LANG_MYOUTER_TOP.OLANG`, `LANG_MISSION_INFO.OLANG`, `LANG_SYSTEM.OLANG`, and `LANG_TITLEMENU.OLANG` on the small face. The earlier `LOOSE_OLANG/007E2F18` title fixtures remain included at indices 390, 397, and 402. Each confirmed STAGEDAT resource contributes its complete production charset; unrelated production resources are not added speculatively.

The confirmed set cannot fit the roughly two remaining 66-pixel rows of the clean 2048×1024 canonical layout. SMALL therefore retains width 2048 and expands only to 2048×2048. It first reuses valid clean `000ebbe8` resident glyph rectangles without copying pixels, then sources remaining glyphs preferentially from the old `cn-b` reference and fits them to 55×66 append cells. USER growth is exactly the append-only record/map requirement. This remains about 4 MiB of texture data rather than the prohibited 4096×4096 / roughly 17 MiB Experimental replacement.

## Four-file resource preservation

| output | selected replacement | unselected resource |
|---|---|---|
| `0007ccd8.xpr` | USER/FontData | TX2D header and atlas byte-identical to clean |
| `00c7c9f9.xpr` | TX2D/FontTexture atlas | USER/FontData byte-identical to clean; TX2D header retained |
| `001cbbd1.xpr` | USER/FontData append-only SMALL charset | TX2D header and original atlas byte-identical to clean |
| `000ebbe8.xpr` | TX2D/FontTexture atlas, height 1024→2048 | USER/FontData byte-identical to clean; TX2D static fields retained |

All resource ranges are reparsed after rebuild, every original charmap entry and glyph record is checked, new indices are append-only, every UV is bounded, written encrypted files decrypt/reparse, and clean/built decrypt→encrypt round-trips are byte exact.

## Outputs

- Test fonts: `{font_output}`
- Exact charsets: `LARGE_XPR_REQUIRED_CHARSET.txt`, `SMALL_XPR_REQUIRED_CHARSET.txt`
- Machine report: `FONT_XPR_BUILD_REPORT.json`

No TXP/STAGEDAT work was performed.
"""
    report_path = output_root / "FONT_XPR_BUILD_REPORT.md"
    report_path.write_text(markdown, encoding="utf-8")

    print(f"STATUS={report_data['status']}")
    print(f"LARGE_REQUIRED={len(large.required)}")
    print(f"LARGE_MAPPED={len(large.required - large.missing)}")
    print(f"LARGE_MISSING={len(large.missing)}")
    print(f"LARGE_ADDED={len(large.appended)}")
    print(f"SMALL_REQUIRED={len(small.required)}")
    print(f"SMALL_MAPPED={len(small.required - small.missing)}")
    print(f"SMALL_MISSING={len(small.missing)}")
    print(f"SMALL_ADDED={len(small.appended)}")
    print(f"OUTPUT_ROOT={output_root}")
    print(f"REPORT={report_path}")
    return 0 if report_data["status"] == "PASS" else 1


if __name__ == "__main__":
    try:
        raise SystemExit(main())
    except FontBuildError as error:
        print(f"ERROR={error}", file=sys.stderr)
        raise SystemExit(1)
