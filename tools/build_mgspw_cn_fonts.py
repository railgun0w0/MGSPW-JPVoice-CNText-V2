#!/usr/bin/env python3
"""Self-owned MGSPW Chinese font builder.

This phase is intentionally read-only with respect to game assets.  It can:

* census the current six-class production corpus;
* parse and document the two clean JPN font bases;
* simulate deterministic 4096x4096 packing; and
* prove clean decrypt/rebuild/encrypt round-trips; and
* build a local-only clean JPN 00C7 Phase-2A runtime fixture from an
  external SC font.

No third-party localization XPR participates in this program. Phase-2A output
is a local technical fixture and is not a release asset.
"""

from __future__ import annotations

import argparse
import csv
import hashlib
import json
import re
import subprocess
import struct
import sys
import unicodedata
from collections import Counter, defaultdict
from dataclasses import dataclass
from pathlib import Path
from typing import Iterable, Sequence

from PIL import Image, ImageDraw, ImageFont
from fontTools.ttLib import TTFont


ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from core.pc_crypto import filename_seed, outer_transform
from core.xpr_font import (
    FONT_CHARMAP_OFFSET,
    GLYPH_RECORD_SIZE,
    FontData,
    GlyphRecord,
    XprFont,
    align_up,
    glyph_bytes,
    validate_glyph_rectangles,
)


OLD_RESOURCE_CLASSES = {
    "YPK_GTT",
    "OHD",
    "LOOSE_OLANG",
    "STAGEDAT_OLANG",
    "SLOT_OLANG",
}
ALL_RESOURCE_CLASSES = OLD_RESOURCE_CLASSES | {"BRIEFING_NBE"}
PIXEL_SIZES = (52, 56, 58, 60, 62, 64, 66)
PADDINGS = (1, 2)
ATLAS_WIDTH = 4096
ATLAS_HEIGHT = 4096
SELECTOR_REQUIREMENT = "UNKNOWN / UNION_REQUIRED"

ANGLE_RE = re.compile(r"<[^<>]*>")
DOLLAR_RE = re.compile(r"\$[A-Za-z0-9_]+")
# Keep this in step with the existing production font coverage parser
# (tools/Build-FontXprV2.py).  The production corpus contains width-bearing
# forms such as ``%02d`` and ``%2d``; the narrower translation-compiler
# inventory is insufficient for charset work because it would leave those
# bytes in the glyph census.
PRINTF_RE = re.compile(r"%(?:\d+\$)?[-+#0-9.*hlLzjt]*[diuoxXfFeEgGaAcspn]")
PRINTF_CANDIDATE_RE = re.compile(r"%(?:[0-9]+\$)?[A-Za-z0-9_.*+#-]+")
BRACE_RE = re.compile(r"\{[^{}\r\n]*\}")
BACKSLASH_RE = re.compile(r"\\(?:u[0-9A-Fa-f]{4}|x[0-9A-Fa-f]{2}|.)")
ESCAPED_LAYOUT_RE = re.compile(r"\\(?:r|n|t)")
CONTROL_ANGLE_RE = re.compile(r"^<[A-Za-z_-]+(?:=|>)")
ANGLE_WRAPPED_PLACEHOLDER_RE = re.compile(r"^<\$[A-Za-z0-9_]+>$")


# These punctuation sets are intentionally reporting categories, not a glyph
# source decision.  Some characters correctly appear in both CJK traditions.
CHINESE_PUNCTUATION = set("，。！？；：、（）《》〈〉“”‘’【】〔〕〖〗…—·～﹏￥")
JAPANESE_PUNCTUATION = set("。、・「」『』【】〔〕〖〗〝〟〰〜゠〒")
LAYOUT_SPACES = {" ", "\u00A0", "\u3000"}


class FontBuildPhase1Error(RuntimeError):
    pass


@dataclass(frozen=True)
class CorpusRow:
    resource_class: str
    source: str
    identity: str
    text: str


@dataclass(frozen=True)
class CharsetEntry:
    codepoint: int
    occurrence_count: int
    resource_classes: tuple[str, ...]

    @property
    def character(self) -> str:
        return chr(self.codepoint)


@dataclass(frozen=True)
class CleanFont:
    selector: str
    path: Path
    encrypted: bytes
    plaintext: bytes
    parsed: XprFont


@dataclass(frozen=True)
class Rectangle:
    key: str
    width: int
    height: int


@dataclass(frozen=True)
class PackingResult:
    overflow: bool
    packed_height: int
    required_area: int
    free_area: int
    rectangle_count: int


def sha256(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def relative(path: Path) -> str:
    try:
        return path.resolve().relative_to(ROOT.resolve()).as_posix()
    except ValueError:
        return str(path.resolve())


def atomic_write_text(path: Path, text: str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    temporary = path.with_name(path.name + ".tmp")
    with temporary.open("w", encoding="utf-8", newline="") as handle:
        handle.write(text)
    temporary.replace(path)


def write_csv(path: Path, fieldnames: Sequence[str], rows: Iterable[dict[str, object]]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    temporary = path.with_name(path.name + ".tmp")
    with temporary.open("w", encoding="utf-8", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=fieldnames, lineterminator="\n")
        writer.writeheader()
        writer.writerows(rows)
    temporary.replace(path)


def read_csv(path: Path) -> list[dict[str, str]]:
    if not path.is_file():
        raise FontBuildPhase1Error(f"missing production input: {path}")
    with path.open("r", encoding="utf-8-sig", newline="") as handle:
        return list(csv.DictReader(handle))


@dataclass(frozen=True)
class ControlTokenAudit:
    token: str
    occurrence_count: int
    resource_classes: tuple[str, ...]
    classification: str
    classification_source: str
    rendered_effect: str


def classify_control_token(token: str, family: str) -> tuple[str, str, str]:
    """Classify raw production syntax using the project control rules."""
    if family == "ANGLE":
        if ANGLE_WRAPPED_PLACEHOLDER_RE.fullmatch(token):
            return ("CONTROL", "production mapping review_flag: ANGLE_WRAPPED_$1_RUNTIME_PLACEHOLDER_PRESERVED", "syntax removed; nested placeholder is not a glyph")
        if token.startswith("<R="):
            payload = token[3:-1]
            if "," not in payload:
                return ("AMBIGUOUS", "production compiler angle_control_signature: INVALID_RUBY", "not removed until malformed Ruby semantics are resolved")
            return ("CONTROL", "production compiler angle_control_signature: RUBY; docs/TECHNICAL_FOUNDATION.md §5", "base and reading payload retained; delimiters removed")
        if token.startswith("<I=") or token.startswith("<C=") or token == "<->":
            return ("CONTROL", "production compiler angle_control_signature", "syntax removed")
        if CONTROL_ANGLE_RE.match(token):
            return ("CONTROL", "production compiler angle_control_signature: named angle control", "syntax removed")
        return ("VISIBLE", "production compiler angle_control_signature: non-control angle literal", "literal angle-bracket text retained")
    if family == "DOLLAR":
        return ("PLACEHOLDER", "production compiler DOLLAR_RE / docs/TECHNICAL_FOUNDATION.md §5", "syntax removed")
    if family == "PRINTF":
        return ("PLACEHOLDER", "tools/Build-FontXprV2.py PRINTF_RE; production format-preservation notes", "syntax removed")
    if family == "ESCAPED_LAYOUT":
        return ("CONTROL", "builder layout rule and production text encoding conventions", "layout syntax removed")
    if family == "LAYOUT":
        return ("CONTROL", "builder rendered_text physical CR/LF/TAB rule", "layout byte removed")
    if family in {"BRACE", "BACKSLASH"}:
        return ("AMBIGUOUS", "Audit-CnSpecialCharacters.py generic token scanner; no production compiler classifier", "not removed pending runtime classification")
    if family == "PERCENT_AMBIGUOUS":
        return ("AMBIGUOUS", "generic percent-token boundary not accepted by production PRINTF_RE", "not removed pending runtime classification")
    raise FontBuildPhase1Error(f"unknown control-token family: {family}")


def _add_control_audit(inventory: dict[tuple[str, str], list[object]], token: str, family: str, resource_class: str) -> None:
    classification, source, effect = classify_control_token(token, family)
    key = (family, token)
    if key not in inventory:
        inventory[key] = [0, set(), classification, source, effect]
    record = inventory[key]
    record[0] = int(record[0]) + 1
    classes = record[1]
    assert isinstance(classes, set)
    classes.add(resource_class)
    if record[2:] != [classification, source, effect]:
        raise FontBuildPhase1Error(f"inconsistent token classification: {family} {token!r}")


def control_token_audit(rows: Sequence[CorpusRow]) -> list[ControlTokenAudit]:
    """Inventory raw tokens before rendering, including ambiguous residuals."""
    inventory: dict[tuple[str, str], list[object]] = {}
    for row in rows:
        text = row.text or ""
        for match in ANGLE_RE.finditer(text):
            _add_control_audit(inventory, match.group(0), "ANGLE", row.resource_class)
        for match in DOLLAR_RE.finditer(text):
            _add_control_audit(inventory, match.group(0), "DOLLAR", row.resource_class)
        printf_matches = list(PRINTF_RE.finditer(text))
        for match in printf_matches:
            _add_control_audit(inventory, match.group(0), "PRINTF", row.resource_class)
        for match in PRINTF_CANDIDATE_RE.finditer(text):
            if not any(match.start() == printf.start() for printf in printf_matches):
                _add_control_audit(inventory, match.group(0), "PERCENT_AMBIGUOUS", row.resource_class)
        for match in BRACE_RE.finditer(text):
            _add_control_audit(inventory, match.group(0), "BRACE", row.resource_class)
        for match in BACKSLASH_RE.finditer(text):
            family = "ESCAPED_LAYOUT" if ESCAPED_LAYOUT_RE.fullmatch(match.group(0)) else "BACKSLASH"
            _add_control_audit(inventory, match.group(0), family, row.resource_class)
        for character in text:
            if character in "\r\n\t":
                _add_control_audit(inventory, {"\r": "\\r", "\n": "\\n", "\t": "\\t"}[character], "LAYOUT", row.resource_class)
    result: list[ControlTokenAudit] = []
    for (_family, token), values in inventory.items():
        result.append(ControlTokenAudit(token, int(values[0]), tuple(sorted(values[1])), str(values[2]), str(values[3]), str(values[4])))
    return sorted(result, key=lambda item: (-item.occurrence_count, item.token, item.classification))


def write_control_token_audit(rows: Sequence[CorpusRow], metadata: dict[str, object], output_path: Path) -> list[ControlTokenAudit]:
    audits = control_token_audit(rows)
    ambiguous = [item for item in audits if item.classification == "AMBIGUOUS"]
    report = [
        "# MGSPW production FONT control-token audit", "",
        "Status: **PASS** (raw-token inventory completed; ambiguous forms are listed explicitly).", "",
        "## Corpus and rule provenance", "",
        f"- Old five-class compiled production manifest: **{metadata['manifest_rows']:,}** rows.",
        f"- `BRIEFING_NBE`: **{metadata['briefing_files']:,}** files / **{metadata['briefing_rows']:,}** physical rows.",
        f"- Total production rows audited: **{metadata['production_rows']:,}**.",
        "- Scope is the current compiled object manifest plus current `translations/briefing/*.csv`; historical experiments, backups, fixtures, and reference-only text are excluded.",
        "- Angle classification reuses the production compilers' `angle_control_signature`: valid Ruby, `<I=...>`, `<C=...>`, `<->`, and named angle controls are controls; other complete angle literals remain visible text.",
        "- Width-bearing printf classification uses the repository's existing broad `tools/Build-FontXprV2.py` rule because `%02d` and `%2d` occur in production; this closes the Phase 1 narrow-regex boundary.",
        "- Nested forms such as `<$1>` appear once as an angle token and once in the overlapping dollar inventory, matching the existing compiler inventory model.", "",
        "## Required probe tokens", "", "| probe | observed occurrence count | result |", "|---|---:|---|",
    ]
    for token in ("<MISSION>", "<ALERT>", "<HUNTING QUEST>", "$NAME", "$100", "%s", "%d", "%02d", "%u", "%x", "%.2f", "\\r", "\\n", "\\t"):
        count = sum(item.occurrence_count for item in audits if item.token == token)
        report.append(f"| `{token}` | {count:,} | {'OBSERVED' if count else 'NOT OBSERVED'} |")
    report.extend(["", "## Raw token inventory", "", "| token | occurrence_count | resource_classes | classification | classification_source | rendered_effect |", "|---|---:|---|---|---|---|"])
    for item in audits:
        token = item.token.replace("|", "\\|").replace("\n", "\\n").replace("\r", "\\r").replace("\t", "\\t")
        source = item.classification_source.replace("|", "\\|")
        effect = item.rendered_effect.replace("|", "\\|")
        report.append(f"| `{token}` | {item.occurrence_count:,} | {', '.join(item.resource_classes)} | {item.classification} | {source} | {effect} |")
    report.extend(["", "## Ambiguous tokens", "", f"Ambiguous distinct tokens: **{len(ambiguous):,}**.", ""])
    if ambiguous:
        report.extend(["| token | occurrence_count | resource_classes | reason |", "|---|---:|---|---|"])
        report.extend(f"| `{item.token}` | {item.occurrence_count:,} | {', '.join(item.resource_classes)} | {item.classification_source} |" for item in ambiguous)
    else:
        report.append("None found in the current production corpus.")
    report.extend(["", "## Charset consequence", "", "Only CONTROL and PLACEHOLDER syntax is removed by the builder. VISIBLE angle literals remain glyph text. AMBIGUOUS forms, if any, remain in the rendered stream and are reported instead of being silently deleted.", ""])
    atomic_write_text(output_path, "\n".join(report))
    return audits


def rendered_text(text: str) -> str:
    """Return display-relevant characters and remove runtime syntax.

    Ruby base and reading payloads are retained because both can be rendered;
    only ``<R=``/comma/closing-delimiter syntax is removed.  Human-readable
    angle-bracket titles are retained, matching the production compilers.
    """

    def replace_angle(match: re.Match[str]) -> str:
        token = match.group(0)
        if token.startswith("<R="):
            payload = token[3:-1]
            if "," not in payload:
                raise FontBuildPhase1Error(f"malformed Ruby token: {token!r}")
            base, reading = payload.split(",", 1)
            return base + reading
        if ANGLE_WRAPPED_PLACEHOLDER_RE.fullmatch(token):
            return ""
        if token.startswith("<I=") or token.startswith("<C=") or token == "<->":
            return ""
        if CONTROL_ANGLE_RE.match(token):
            return ""
        return token

    value = ANGLE_RE.sub(replace_angle, text or "")
    value = DOLLAR_RE.sub("", value)
    value = PRINTF_RE.sub("", value)
    value = ESCAPED_LAYOUT_RE.sub("", value)
    output: list[str] = []
    for character in value:
        category = unicodedata.category(character)
        if character in "\r\n\t" or category.startswith("C"):
            continue
        if character.isspace() and character not in LAYOUT_SPACES:
            continue
        output.append(character)
    return "".join(output)


def is_han(codepoint: int) -> bool:
    return any(
        start <= codepoint <= end
        for start, end in (
            (0x3400, 0x4DBF),
            (0x4E00, 0x9FFF),
            (0xF900, 0xFAFF),
            (0x20000, 0x2EBEF),
            (0x2F800, 0x2FA1F),
            (0x30000, 0x323AF),
        )
    )


def is_kana(codepoint: int) -> bool:
    return any(
        start <= codepoint <= end
        for start, end in (
            (0x3040, 0x309F),
            (0x30A0, 0x30FF),
            (0x31F0, 0x31FF),
            (0x1B000, 0x1B16F),
            (0xFF66, 0xFF9F),
        )
    )


def unicode_name(character: str) -> str:
    return unicodedata.name(character, "<UNNAMED>")


def is_latin(character: str) -> bool:
    return "LATIN" in unicode_name(character)


def is_chinese_punctuation(character: str) -> bool:
    return character in CHINESE_PUNCTUATION


def is_japanese_or_fullwidth_punctuation(character: str) -> bool:
    name = unicode_name(character)
    return character in JAPANESE_PUNCTUATION or (
        unicodedata.category(character).startswith("P")
        and ("FULLWIDTH" in name or 0xFF00 <= ord(character) <= 0xFFEF)
    )


def load_production_corpus(
    manifest_path: Path,
    briefing_dir: Path,
) -> tuple[list[CorpusRow], dict[str, object]]:
    manifest = read_csv(manifest_path)
    rows: list[CorpusRow] = []
    manifest_classes: Counter[str] = Counter()
    for row_number, row in enumerate(manifest, start=2):
        resource_class = row.get("resource_class", "")
        if resource_class not in OLD_RESOURCE_CLASSES:
            raise FontBuildPhase1Error(
                f"{manifest_path}:{row_number}: unexpected resource_class={resource_class!r}"
            )
        text = row.get("cn_text", "")
        if not text:
            raise FontBuildPhase1Error(f"{manifest_path}:{row_number}: empty cn_text")
        file_id = row.get("file_id") or row.get("resource_id") or "UNKNOWN"
        object_index = row.get("record_index") or row.get("reference_index") or str(row_number)
        rows.append(
            CorpusRow(
                resource_class,
                relative(manifest_path),
                f"{resource_class}/{file_id}#{object_index}",
                text,
            )
        )
        manifest_classes[resource_class] += 1

    if not briefing_dir.is_dir():
        raise FontBuildPhase1Error(f"missing BRIEFING_NBE production directory: {briefing_dir}")
    briefing_paths = sorted(briefing_dir.glob("*.csv"))
    if not briefing_paths:
        raise FontBuildPhase1Error(f"no BRIEFING_NBE production CSVs: {briefing_dir}")
    briefing_rows = 0
    for path in briefing_paths:
        for row_number, row in enumerate(read_csv(path), start=2):
            text = row.get("cn_text", "")
            if not text:
                raise FontBuildPhase1Error(f"{path}:{row_number}: empty cn_text")
            unique_index = row.get("unique_index") or str(row_number - 2)
            rows.append(
                CorpusRow(
                    "BRIEFING_NBE",
                    relative(path),
                    f"BRIEFING_NBE/{path.stem}#{unique_index}",
                    text,
                )
            )
            briefing_rows += 1

    source_hasher = hashlib.sha256()
    for path in (manifest_path, *briefing_paths):
        source_hasher.update(relative(path).encode("utf-8"))
        source_hasher.update(b"\0")
        source_hasher.update(path.read_bytes())
        source_hasher.update(b"\0")

    metadata: dict[str, object] = {
        "manifest_rows": len(manifest),
        "manifest_classes": dict(sorted(manifest_classes.items())),
        "briefing_files": len(briefing_paths),
        "briefing_rows": briefing_rows,
        "production_rows": len(rows),
        "source_sha256": source_hasher.hexdigest(),
    }
    return rows, metadata


def census(rows: Sequence[CorpusRow]) -> tuple[list[CharsetEntry], dict[str, int]]:
    occurrences: Counter[int] = Counter()
    resource_classes: defaultdict[int, set[str]] = defaultdict(set)
    empty_after_controls = 0
    for row in rows:
        rendered = rendered_text(row.text)
        if not rendered:
            empty_after_controls += 1
        for character in rendered:
            codepoint = ord(character)
            occurrences[codepoint] += 1
            resource_classes[codepoint].add(row.resource_class)
    entries = [
        CharsetEntry(codepoint, occurrences[codepoint], tuple(sorted(resource_classes[codepoint])))
        for codepoint in sorted(occurrences)
    ]
    return entries, {"empty_after_controls": empty_after_controls}


def category_flags(entry: CharsetEntry) -> dict[str, bool]:
    character = entry.character
    category = unicodedata.category(character)
    return {
        "han": is_han(entry.codepoint),
        "ascii": entry.codepoint <= 0x7F,
        "digit": category == "Nd",
        "latin": is_latin(character),
        "kana": is_kana(entry.codepoint),
        "chinese_punctuation": is_chinese_punctuation(character),
        "japanese_fullwidth_punctuation": is_japanese_or_fullwidth_punctuation(character),
        "punctuation": category.startswith("P"),
        "symbol": category.startswith("S"),
        "non_bmp": entry.codepoint > 0xFFFF,
    }


def summarize_categories(entries: Sequence[CharsetEntry]) -> dict[str, tuple[int, int]]:
    names = tuple(category_flags(entries[0]).keys()) if entries else ()
    result: dict[str, tuple[int, int]] = {}
    for name in names:
        selected = [entry for entry in entries if category_flags(entry)[name]]
        result[name] = (len(selected), sum(entry.occurrence_count for entry in selected))
    return result


def write_charset_outputs(
    entries: Sequence[CharsetEntry],
    metadata: dict[str, object],
    census_metadata: dict[str, int],
    charset_dir: Path,
) -> None:
    fields = (
        "codepoint",
        "character",
        "unicode_name",
        "category",
        "occurrence_count",
        "resource_classes",
        "is_han",
        "is_ascii",
        "is_kana",
        "is_punctuation",
        "is_symbol",
        "selector_requirement",
    )
    csv_rows: list[dict[str, object]] = []
    for entry in entries:
        flags = category_flags(entry)
        csv_rows.append(
            {
                "codepoint": f"U+{entry.codepoint:04X}",
                "character": entry.character,
                "unicode_name": unicode_name(entry.character),
                "category": unicodedata.category(entry.character),
                "occurrence_count": entry.occurrence_count,
                "resource_classes": " | ".join(entry.resource_classes),
                "is_han": "YES" if flags["han"] else "NO",
                "is_ascii": "YES" if flags["ascii"] else "NO",
                "is_kana": "YES" if flags["kana"] else "NO",
                "is_punctuation": "YES" if flags["punctuation"] else "NO",
                "is_symbol": "YES" if flags["symbol"] else "NO",
                "selector_requirement": SELECTOR_REQUIREMENT,
            }
        )
    write_csv(charset_dir / "font_charset.csv", fields, csv_rows)
    atomic_write_text(
        charset_dir / "font_charset.txt",
        "".join(entry.character for entry in entries) + "\n",
    )

    total_occurrences = sum(entry.occurrence_count for entry in entries)
    summaries = summarize_categories(entries)
    labels = {
        "han": "Han",
        "ascii": "ASCII (including U+0020 layout space)",
        "digit": "Unicode decimal digits",
        "latin": "Latin",
        "kana": "Kana",
        "chinese_punctuation": "Chinese punctuation policy set",
        "japanese_fullwidth_punctuation": "Japanese/fullwidth punctuation policy set",
        "punctuation": "All Unicode punctuation",
        "symbol": "Unicode symbols",
        "non_bmp": "Characters above U+FFFF",
    }
    report = [
        "# MGSPW production FONT charset report",
        "",
        "Status: **PASS** (deterministic census; selector split remains intentionally unresolved)",
        "",
        "## Scope",
        "",
        f"- Old five-class compiled production objects: `{relative(Path('build/translation/compiled_translation_manifest.csv'))}`, **{metadata['manifest_rows']:,}** rows.",
        f"- `BRIEFING_NBE`: `translations/briefing/*.csv`, **{metadata['briefing_files']:,}** files / **{metadata['briefing_rows']:,}** physical rows.",
        f"- Total production text rows scanned: **{metadata['production_rows']:,}**.",
        f"- Aggregate source identity SHA256: `{metadata['source_sha256']}`.",
        "- Excluded: historical experiments, backups, fixtures, reference translations, JPN/ENG/MLG_CN auxiliary text, templates, worklists, documentation, and package/readiness duplicates.",
        "- Old five-class mappings are represented exactly once through their current object-level compiled manifest; `BRIEFING_NBE` is represented exactly once through its physical production CSV rows.",
        "",
        "## Counts",
        "",
        f"- Total display-relevant Unicode codepoint occurrences: **{total_occurrences:,}**.",
        f"- Unique codepoints: **{len(entries):,}**.",
        f"- Phase 1 baseline comparison: unique codepoints `2,904 -> {len(entries):,}` (**{'PASS' if len(entries) == 2904 else 'FAIL'}**); unique Han `2,721 -> {sum(is_han(entry.codepoint) for entry in entries):,}` (**{'PASS' if sum(is_han(entry.codepoint) for entry in entries) == 2721 else 'FAIL'}**).",
        "- The occurrence total may change when a previously missed control form is correctly excluded; this is not corpus drift when the source SHA256 and production row counts remain unchanged.",
        f"- Rows containing only stripped control/layout syntax: **{census_metadata['empty_after_controls']:,}**.",
        "",
        "| category | unique codepoints | occurrences |",
        "|---|---:|---:|",
    ]
    for key in labels:
        unique, occurrences = summaries[key]
        report.append(f"| {labels[key]} | {unique:,} | {occurrences:,} |")
    report.extend(
        [
            "",
            "The policy-set rows overlap by design: for example `。` is relevant to both Chinese and Japanese punctuation review. `is_punctuation` in the CSV is the Unicode general-category result.",
            "",
            "## Resource-class coverage",
            "",
            "| resource class | physical production rows |",
            "|---|---:|",
        ]
    )
    for resource_class, count in metadata["manifest_classes"].items():
        report.append(f"| {resource_class} | {count:,} |")
    report.append(f"| BRIEFING_NBE | {metadata['briefing_rows']:,} |")
    report.extend(
        [
            "",
            "## Control and visibility rules",
            "",
            "- `<R=base,reading>` contributes `base` and `reading`, because both payloads can render; Ruby delimiters and separators do not enter the charset.",
            "- `<I=...>`, `<C=...>`, `<->`, named runtime angle controls, `$NAME`, printf placeholders, escaped/physical CR-LF-tab, and Unicode control/format characters are removed.",
            "- Human-readable angle-bracket titles remain text, matching the production compiler's control classification.",
            "- U+0020/U+00A0/U+3000 are retained as render-relevant layout glyphs; other separator controls are excluded.",
            "- No resource control bytes or CSV metadata columns are decoded as text.",
            "",
            "## Selector requirement",
            "",
            f"Every row currently uses `{SELECTOR_REQUIREMENT}`. The corpus does not provide a fully proven large/small selector assignment, so Phase 1 deliberately builds and simulates the complete union instead of guessing.",
            "",
            "## Output contract",
            "",
            "- `font_charset.txt`: ascending-codepoint literal union charset.",
            "- `font_charset.csv`: per-codepoint count, resource classes, Unicode metadata, flags, and selector requirement.",
        ]
    )
    non_bmp = [entry for entry in entries if entry.codepoint > 0xFFFF]
    if non_bmp:
        report.extend(
            [
                "",
                "## Warning: non-BMP characters",
                "",
                "The current FontData charmap is BMP/u16. These characters require an explicit rewrite or format decision before a future XPR build:",
                "",
                *[f"- `{entry.character}` U+{entry.codepoint:X}: {entry.occurrence_count} occurrences" for entry in non_bmp],
            ]
        )
    atomic_write_text(charset_dir / "FONT_CHARSET_REPORT.md", "\n".join(report) + "\n")


def load_clean_font(selector: str, path: Path) -> CleanFont:
    if not path.is_file():
        raise FontBuildPhase1Error(f"missing clean JPN base: {path}")
    encrypted = path.read_bytes()
    plaintext = outer_transform(encrypted, filename_seed(path.name))
    parsed = XprFont(plaintext)
    rectangle_errors = validate_glyph_rectangles(parsed.font_data, parsed.texture)
    if rectangle_errors:
        raise FontBuildPhase1Error(
            f"{selector}: invalid clean glyph rectangles: {rectangle_errors[:5]}"
        )
    return CleanFont(selector, path, encrypted, plaintext, parsed)


@dataclass(frozen=True)
class Phase2AGlyph:
    codepoint: int
    bitmap: bytes
    width: int
    height: int
    bearing: int
    advance: int
    glyph_source: str
    font_file: str
    font_file_sha256: str
    font_face_index: int | None
    font_size: int | None
    baseline: int | None
    source_bbox: tuple[int, int, int, int] | None
    is_han_override: bool
    is_fallback: bool = False
    atlas_x: int = 0
    atlas_y: int = 0


def _percentile(values: Sequence[int], percentile: float) -> int:
    if not values:
        return 0
    ordered = sorted(values)
    index = min(len(ordered) - 1, int((percentile / 100.0) * (len(ordered) - 1)))
    return ordered[index]


def _font_cmap(path: Path, face_index: int) -> set[int]:
    try:
        font = TTFont(str(path), fontNumber=face_index, lazy=True)
        result = set()
        for table in font["cmap"].tables:
            result.update(table.cmap)
        font.close()
        return result
    except Exception as error:  # pragma: no cover - font container failures are environment-specific
        raise FontBuildPhase1Error(f"cannot inspect external font cmap: {path}: {error}") from error


def _rasterize_external_glyph(
    font: ImageFont.FreeTypeFont,
    character: str,
    codepoint: int,
    source_name: str,
    source_path: Path,
    source_hash: str,
    face_index: int,
    font_size: int,
    baseline: int,
    cell_height: int,
    is_han_override: bool,
) -> Phase2AGlyph:
    bbox = font.getbbox(character, anchor="ls")
    if bbox is None:
        raise FontBuildPhase1Error(f"external font has no bbox for U+{codepoint:04X}")
    left, top, right, bottom = bbox
    width = max(1, right - left)
    if baseline + top < 0 or baseline + bottom > cell_height:
        raise FontBuildPhase1Error(
            f"rasterized U+{codepoint:04X} is cropped at baseline={baseline}: bbox={bbox}, cell_height={cell_height}"
        )
    image = Image.new("L", (width, cell_height), 0)
    ImageDraw.Draw(image).text(
        (-left, baseline),
        character,
        font=font,
        fill=255,
        anchor="ls",
    )
    bitmap = image.tobytes()
    if not any(bitmap):
        raise FontBuildPhase1Error(f"external font produced an empty bitmap for U+{codepoint:04X}")
    advance = max(0, min(0xFFFF, int(round(font.getlength(character)))))
    return Phase2AGlyph(
        codepoint=codepoint,
        bitmap=bitmap,
        width=width,
        height=cell_height,
        bearing=max(-0x8000, min(0x7FFF, int(left))),
        advance=advance,
        glyph_source=source_name,
        font_file=str(source_path.resolve()),
        font_file_sha256=source_hash,
        font_face_index=face_index,
        font_size=font_size,
        baseline=baseline,
        source_bbox=(left, top, right, bottom),
        is_han_override=is_han_override,
    )


def _extract_clean_bitmap(texture: bytes, atlas_width: int, glyph: GlyphRecord) -> bytes:
    width = glyph.u1 - glyph.u0
    height = glyph.v1 - glyph.v0
    if width <= 0 or height <= 0:
        raise FontBuildPhase1Error("clean glyph has an empty UV rectangle")
    rows = []
    for y in range(glyph.v0, glyph.v1):
        start = y * atlas_width + glyph.u0
        rows.append(texture[start : start + width])
    bitmap = b"".join(rows)
    if len(bitmap) != width * height:
        raise FontBuildPhase1Error("clean glyph extraction exceeded atlas bounds")
    return bitmap


def _rebuild_phase2a_user(base: CleanFont, glyphs: Sequence[Phase2AGlyph], records: Sequence[GlyphRecord]) -> bytes:
    last_code = max(base.parsed.font_data.last_code, *(glyph.codepoint for glyph in glyphs if glyph.codepoint))
    charmap = [0] * (last_code + 1)
    for glyph_index, glyph in enumerate(glyphs):
        if glyph.codepoint and charmap[glyph.codepoint]:
            raise FontBuildPhase1Error(f"duplicate final charmap codepoint U+{glyph.codepoint:04X}")
        if glyph.codepoint:
            charmap[glyph.codepoint] = glyph_index
    if len(records) != len(glyphs) or len(records) > 0xFFFF:
        raise FontBuildPhase1Error("invalid final GlyphRecord count")
    payload = bytearray(base.parsed.font_data.payload[:FONT_CHARMAP_OFFSET])
    struct.pack_into(">H", payload, 0x14, last_code)
    payload.extend(struct.pack(f">{len(charmap)}H", *charmap))
    payload.extend(b"\0" * (align_up(len(payload), 8) - len(payload)))
    payload.extend(struct.pack(">H", len(records)))
    payload.extend(glyph_bytes(records))
    payload.extend(base.parsed.font_data.suffix)
    FontData.parse(bytes(payload))
    return bytes(payload)


def _phase2a_tx2d_header(template: bytes, width: int, height: int, pitch: int) -> bytes:
    if len(template) < 0x34 or pitch % 32:
        raise FontBuildPhase1Error("invalid Phase-2A TX2D geometry")
    header = bytearray(template)
    fetch0, fetch1, fetch2 = struct.unpack_from(">3I", header, 0x1C)
    fetch0 = (fetch0 & ((1 << 22) - 1)) | ((pitch // 32) << 22)
    fetch0 &= 0x7FFFFFFF
    fetch1 = (fetch1 & ~0xFF) | 2
    fetch2 = (fetch2 & ~((0x1FFF) | (0x1FFF << 13))) | ((width - 1) & 0x1FFF) | (((height - 1) & 0x1FFF) << 13)
    struct.pack_into(">3I", header, 0x1C, fetch0, fetch1, fetch2)
    return bytes(header)


def _pack_phase2a_glyphs(glyphs: Sequence[Phase2AGlyph], padding: int, width: int, height: int) -> tuple[list[Phase2AGlyph], bytes, int, bool]:
    if padding < 0:
        raise FontBuildPhase1Error("padding must be non-negative")
    atlas = bytearray(width * height)
    placed: list[Phase2AGlyph] = []
    cursor_x = padding
    cursor_y = padding
    row_height = 0
    for glyph in glyphs:
        if glyph.width + padding * 2 > width or glyph.height + padding * 2 > height:
            raise FontBuildPhase1Error(f"glyph U+{glyph.codepoint:04X} cannot fit atlas geometry")
        if cursor_x + glyph.width + padding > width:
            cursor_y += row_height + padding
            cursor_x = padding
            row_height = 0
        if cursor_y + glyph.height + padding > height:
            raise FontBuildPhase1Error(f"atlas overflow at U+{glyph.codepoint:04X}")
        placed_glyph = Phase2AGlyph(**{**glyph.__dict__, "atlas_x": cursor_x, "atlas_y": cursor_y})
        placed.append(placed_glyph)
        for row in range(glyph.height):
            source_start = row * glyph.width
            target_start = (cursor_y + row) * width + cursor_x
            atlas[target_start : target_start + glyph.width] = glyph.bitmap[source_start : source_start + glyph.width]
        cursor_x += glyph.width + padding
        row_height = max(row_height, glyph.height)
    packed_height = cursor_y + row_height + padding
    # Expanded rectangles may touch at the required padding boundary, but may
    # never overlap. This is intentionally independent from the shelf logic.
    for left_index, left in enumerate(placed):
        for right in placed[left_index + 1 :]:
            if (
                left.atlas_x - padding < right.atlas_x + right.width
                and right.atlas_x - padding < left.atlas_x + left.width
                and left.atlas_y - padding < right.atlas_y + right.height
                and right.atlas_y - padding < left.atlas_y + left.height
            ):
                raise FontBuildPhase1Error(f"packed glyph padding overlap: U+{left.codepoint:04X}/U+{right.codepoint:04X}")
    return placed, bytes(atlas), packed_height, True


def _write_phase2a_manifest(path: Path, glyphs: Sequence[Phase2AGlyph], records: Sequence[GlyphRecord]) -> None:
    fields = [
        "selector", "codepoint", "character", "glyph_index", "atlas_x", "atlas_y", "width", "height",
        "bearing", "advance", "glyph_source", "font_file", "font_file_sha256", "font_face_index",
        "font_size", "baseline", "bitmap_sha256", "is_han_override",
    ]
    rows = []
    for index, (glyph, record) in enumerate(zip(glyphs, records)):
        rows.append({
            "selector": "00c7c9f9.xpr",
            "codepoint": f"U+{glyph.codepoint:04X}",
            "character": "" if glyph.is_fallback else chr(glyph.codepoint),
            "glyph_index": index,
            "atlas_x": glyph.atlas_x,
            "atlas_y": glyph.atlas_y,
            "width": glyph.width,
            "height": glyph.height,
            "bearing": record.bearing_x,
            "advance": record.advance,
            "glyph_source": "CLEAN_JPN_PRESERVED" if glyph.is_fallback else glyph.glyph_source,
            "font_file": glyph.font_file,
            "font_file_sha256": glyph.font_file_sha256,
            "font_face_index": "" if glyph.font_face_index is None else glyph.font_face_index,
            "font_size": "" if glyph.font_size is None else glyph.font_size,
            "baseline": "" if glyph.baseline is None else glyph.baseline,
            "bitmap_sha256": sha256(glyph.bitmap),
            "is_han_override": "YES" if glyph.is_han_override else "NO",
        })
    write_csv(path, fields, rows)


def build_clean_00c7_fixture(
    base: CleanFont,
    font_path: Path,
    output_dir: Path,
    runtime_test_dir: Path | None = None,
    face_index: int = 0,
    font_size: int = 56,
    padding: int = 2,
    required_codepoints: set[int] | None = None,
    charset_source_hash: str = "",
) -> dict[str, object]:
    """Build a deterministic local-only full-rebuild 00C7 fixture."""
    if base.selector != "00c7c9f9.xpr":
        raise FontBuildPhase1Error("Phase-2A only accepts clean JPN 00c7c9f9.xpr")
    font_path = font_path.resolve()
    if not font_path.is_file():
        raise FontBuildPhase1Error(f"missing external SC font: {font_path}")
    source_hash = sha256(font_path.read_bytes())
    cmap = _font_cmap(font_path, face_index)
    try:
        external_font = ImageFont.truetype(str(font_path), font_size, index=face_index)
    except Exception as error:
        raise FontBuildPhase1Error(f"cannot load external font face {face_index}: {font_path}: {error}") from error
    source_family, source_style = external_font.getname()
    source_name = f"{source_family} {source_style}".strip()
    if required_codepoints is None:
        required_codepoints = set()
        for entry in census(load_production_corpus(ROOT / "build/translation/compiled_translation_manifest.csv", ROOT / "translations/briefing")[0])[0]:
            required_codepoints.add(entry.codepoint)
    required_codepoints = set(required_codepoints)
    if any(codepoint > 0xFFFF for codepoint in required_codepoints):
        raise FontBuildPhase1Error("Phase-2A clean FontData charmap is BMP-only")
    # The 56px source has a few generated Latin-1/fullwidth glyphs whose
    # FreeType bbox is taller than the Han bbox.  A 72px cell with baseline
    # 56 keeps every observed production glyph inside the bitmap without
    # cropping while retaining the requested 56px raster size.
    baseline = 56
    cell_height = 72
    source_bbox_heights: list[int] = []
    source_bbox_widths: list[int] = []
    rasterized: dict[int, Phase2AGlyph] = {}
    missing_cmap = sorted(codepoint for codepoint in required_codepoints if is_han(codepoint) and codepoint not in cmap)
    if missing_cmap:
        raise FontBuildPhase1Error("external SC font lacks required Han: " + ", ".join(f"U+{cp:04X}" for cp in missing_cmap[:12]))
    for codepoint in sorted(required_codepoints):
        if is_han(codepoint) or codepoint not in base.parsed.font_data.mapped():
            glyph = _rasterize_external_glyph(
                external_font,
                chr(codepoint),
                codepoint,
                source_name,
                font_path,
                source_hash,
                face_index,
                font_size,
                baseline,
                cell_height,
                is_han(codepoint),
            )
            rasterized[codepoint] = glyph
            if glyph.source_bbox is not None:
                source_bbox_widths.append(glyph.source_bbox[2] - glyph.source_bbox[0])
                source_bbox_heights.append(glyph.source_bbox[3] - glyph.source_bbox[1])

    final_glyphs: list[Phase2AGlyph] = [
        Phase2AGlyph(0, _extract_clean_bitmap(base.parsed.texture.texels, base.parsed.texture.width, base.parsed.font_data.glyphs[0]), base.parsed.font_data.glyphs[0].u1 - base.parsed.font_data.glyphs[0].u0, base.parsed.font_data.glyphs[0].v1 - base.parsed.font_data.glyphs[0].v0, base.parsed.font_data.glyphs[0].bearing_x, base.parsed.font_data.glyphs[0].advance, "CLEAN_JPN_PRESERVED", "", "", None, None, None, None, False, True)
    ]
    clean_mapped = base.parsed.font_data.mapped()
    for codepoint, old_index in sorted(clean_mapped.items()):
        if codepoint == 0 or is_han(codepoint):
            continue
        old = base.parsed.font_data.glyphs[old_index]
        final_glyphs.append(Phase2AGlyph(codepoint, _extract_clean_bitmap(base.parsed.texture.texels, base.parsed.texture.width, old), old.u1 - old.u0, old.v1 - old.v0, old.bearing_x, old.advance, "CLEAN_JPN_PRESERVED", "", "", None, None, None, None, False))
    final_glyphs.extend(rasterized[codepoint] for codepoint in sorted(rasterized))
    placed, atlas, packed_height, _ = _pack_phase2a_glyphs(final_glyphs, padding, 4096, 4096)
    records = []
    for glyph in placed:
        bearing = glyph.bearing & 0xFFFF
        records.append(GlyphRecord(glyph.atlas_x, glyph.atlas_y, glyph.atlas_x + glyph.width, glyph.atlas_y + glyph.height, bearing, glyph.width, glyph.advance, 0))
    user_payload = _rebuild_phase2a_user(base, placed, records)
    tx_header = _phase2a_tx2d_header(base.parsed.tx2d.payload, 4096, 4096, 4096)
    rebuilt_plaintext = base.parsed.rebuild({("USER", "FontData"): user_payload, ("TX2D", "FontTexture"): tx_header}, texture_texels=atlas)
    rebuilt = XprFont(rebuilt_plaintext)
    encrypted = outer_transform(rebuilt_plaintext, filename_seed("00c7c9f9.xpr"))
    decrypted_again = outer_transform(encrypted, filename_seed("00c7c9f9.xpr"))
    output_dir.mkdir(parents=True, exist_ok=True)
    xpr_path = output_dir / "00c7c9f9.xpr"
    xpr_path.write_bytes(encrypted)
    _write_phase2a_manifest(output_dir / "FONT_GLYPH_MANIFEST.csv", placed, records)
    required_mapping_ok = all(cp < len(rebuilt.font_data.charmap) and rebuilt.font_data.charmap[cp] != 0 and rebuilt.font_data.charmap[cp] < len(rebuilt.font_data.glyphs) for cp in required_codepoints)
    han_source_ok = all(g.glyph_source == source_name for g in placed if g.is_han_override)
    no_overlap = True
    for i, left in enumerate(placed):
        for right in placed[i + 1 :]:
            if left.atlas_x < right.atlas_x + right.width and right.atlas_x < left.atlas_x + left.width and left.atlas_y < right.atlas_y + right.height and right.atlas_y < left.atlas_y + left.height:
                no_overlap = False
    checks = {
        "decrypt_output_is_XPR2": decrypted_again[:4] == b"XPR2",
        "resource_descriptors_in_bounds": all(r.offset + r.size <= rebuilt.texture_data_offset for r in rebuilt.resources),
        "resources_do_not_overlap": not any(left.offset + left.size > right.offset for left, right in zip(sorted(rebuilt.resources, key=lambda item: item.offset), sorted(rebuilt.resources, key=lambda item: item.offset)[1:])),
        "USER_parse_succeeds": True,
        "charmap_indices_valid": all(index < len(rebuilt.font_data.glyphs) for index in rebuilt.font_data.charmap),
        "count_prefix_equals_record_count": rebuilt.font_data.record_prefix == struct.pack(">H", len(rebuilt.font_data.glyphs)),
        "all_UV_rectangles_in_4096x4096": not validate_glyph_rectangles(rebuilt.font_data, rebuilt.texture),
        "no_packed_glyph_overlap": no_overlap,
        "no_padding_violation": True,
        "TX2D_data_size_is_4096_squared": len(rebuilt.texture.texels) == 4096 * 4096,
        "TX2D_pitch_is_4096": rebuilt.texture.pitch == 4096,
        "TX2D_format_is_2": rebuilt.texture.data_format == 2,
        "TX2D_tiled_is_0": rebuilt.texture.tiled == 0,
        "TX2D_endian_is_0": rebuilt.texture.endian == 0,
        "required_production_codepoints_represented": required_mapping_ok,
        "all_Han_use_selected_SC_font": han_source_ok,
        "no_MLG_CN_glyph_source": all(g.glyph_source not in {"MLG", "MLG_CN", "DONOR", "UNKNOWN"} for g in placed),
        "encrypt_decrypt_roundtrip_exact": decrypted_again == rebuilt_plaintext,
    }
    git_commit = subprocess.run(["git", "rev-parse", "HEAD"], cwd=ROOT, capture_output=True, text=True, check=False).stdout.strip()
    build_manifest = {
        "builder_git_commit": git_commit,
        "clean_base_path": str(base.path.resolve()),
        "clean_base_sha256": sha256(base.encrypted),
        "clean_plaintext_sha256": sha256(base.plaintext),
        "source_font_path": str(font_path),
        "source_font_sha256": source_hash,
        "source_font_face_index": face_index,
        "source_font_family": source_family,
        "source_font_style": source_style,
        "charset_source_hash": charset_source_hash,
        "charset_unique_count": len(required_codepoints),
        "charset_han_count": sum(is_han(cp) for cp in required_codepoints),
        "raster": {"pixel_size": font_size, "cell_height": cell_height, "baseline": baseline, "backend": "Pillow 9.0.1 / FreeType 2.11.1", "grayscale_mode": "8-bit linear grayscale", "hinting_policy": "Pillow default FreeType load; no synthetic stroke", "padding": padding},
        "packing_algorithm": "deterministic stable shelf; fallback, clean non-Han by codepoint, generated codepoints by codepoint; no rotation",
        "atlas_sha256": sha256(atlas),
        "user_sha256": sha256(user_payload),
        "glyph_record_sha256": sha256(glyph_bytes(records)),
        "plaintext_xpr_sha256": sha256(rebuilt_plaintext),
        "encrypted_xpr_sha256": sha256(encrypted),
        "record_count": len(records),
        "mapped_count": len(rebuilt.font_data.mapped()),
        "preserved_clean_glyph_count": sum(1 for g in placed if g.glyph_source == "CLEAN_JPN_PRESERVED"),
        "generated_glyph_count": sum(1 for g in placed if g.glyph_source != "CLEAN_JPN_PRESERVED"),
        "generated_han_count": sum(1 for g in placed if g.is_han_override),
        "packed_height": packed_height,
        "atlas_usage_percent": round((packed_height / 4096) * 100, 4),
        "static_checks": checks,
        "runtime_status": "CLEAN_JPN_00C7_FULL_REBUILD_RUNTIME = NOT YET TESTED",
        "raster_bbox": {"max_width": max(source_bbox_widths, default=0), "max_height": max(source_bbox_heights, default=0), "p50_width": _percentile(source_bbox_widths, 50), "p95_width": _percentile(source_bbox_widths, 95), "p99_width": _percentile(source_bbox_widths, 99), "p50_height": _percentile(source_bbox_heights, 50), "p95_height": _percentile(source_bbox_heights, 95), "p99_height": _percentile(source_bbox_heights, 99), "overflow_or_crop_count": 0},
    }
    (output_dir / "FONT_BUILD_MANIFEST.json").write_text(json.dumps(build_manifest, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    report = [
        "# CLEAN JPN 00C7 Phase-2A validation report", "", "## STATIC PASS", "",
        f"- Source font: `{source_name}`; face index `{face_index}`; SHA256 `{source_hash}`.",
        f"- Raster profile: pixel size `{font_size}`, cell height `{cell_height}`, baseline `{baseline}`, padding `{padding}`, 4096×4096 8-bit grayscale.",
        f"- Raster bbox: max `{max(source_bbox_widths, default=0)}×{max(source_bbox_heights, default=0)}`, p50 `{_percentile(source_bbox_widths, 50)}×{_percentile(source_bbox_heights, 50)}`, p95 `{_percentile(source_bbox_widths, 95)}×{_percentile(source_bbox_heights, 95)}`, p99 `{_percentile(source_bbox_widths, 99)}×{_percentile(source_bbox_heights, 99)}`, crop/overflow `0`.",
        f"- Glyphs: `{sum(1 for g in placed if g.glyph_source == 'CLEAN_JPN_PRESERVED')}` preserved clean, `{sum(1 for g in placed if g.is_han_override)}` generated Han, `{len(records)}` total records / `{len(rebuilt.font_data.mapped())}` mapped.",
        f"- Atlas packed height `{packed_height}` / 4096; usage `{(packed_height / 4096) * 100:.4f}%`; no overlap and padding `{padding}` validated.",
        f"- Plaintext XPR SHA256: `{sha256(rebuilt_plaintext)}`.", f"- Encrypted XPR SHA256: `{sha256(encrypted)}`.", "",
        "| static validation | result |", "|---|---|",
    ]
    report.extend(f"| {name} | {'PASS' if value else 'FAIL'} |" for name, value in checks.items())
    report.extend(["", "## RUNTIME NOT YET TESTED", "", "`CLEAN_JPN_00C7_FULL_REBUILD_RUNTIME = NOT YET TESTED`", "", "Static parser acceptance is not runtime proof. Replace only the large 00C7 selector in a separately backed-up local test installation after reviewing `font/runtime_test/00c7_phase2a/README_TEST.md`. Do not replace 001C and do not patch the EXE.", ""])
    (output_dir / "FONT_VALIDATION_REPORT.md").write_text("\n".join(report), encoding="utf-8")
    if runtime_test_dir is not None:
        runtime_test_dir.mkdir(parents=True, exist_ok=True)
        (runtime_test_dir / "00c7c9f9.xpr").write_bytes(encrypted)
        (runtime_test_dir / "README_TEST.md").write_text("""# 00C7 Phase-2A local runtime test\n\nThis package is local-only and was built from clean JPN `font/JPN/00c7c9f9.xpr` plus the external SC font recorded in the build manifest.\n\n1. Back up the installed large-selector `00c7c9f9.xpr` before testing.\n2. Replace only that 00C7 file in a disposable test copy of the game installation.\n3. Do not replace `001cbbd1.xpr`, do not patch the EXE, and do not alter the repository's clean inputs.\n4. Test startup, main menu, large-font Chinese UI, weapon/item descriptions, long text, ASCII/digits/English, kana/game symbols, and several formerly missing Han characters.\n5. Restore the backup after testing.\n\nRuntime status remains `CLEAN_JPN_00C7_FULL_REBUILD_RUNTIME = NOT YET TESTED` until real in-game feedback is recorded.\n""", encoding="utf-8")
    if not all(checks.values()):
        failed = [name for name, value in checks.items() if not value]
        raise FontBuildPhase1Error("Phase-2A static validation failed: " + ", ".join(failed))
    return build_manifest


def descriptor_summary(font: CleanFont) -> list[str]:
    rows: list[str] = []
    for resource in font.parsed.resources:
        rows.append(
            f"| {font.selector} | {resource.index} | {resource.kind}/{resource.name} | "
            f"`0x{resource.descriptor_offset:X}` | `0x{resource.offset:X}` | "
            f"`0x{resource.size:X}` | `0x{resource.name_offset:X}` | "
            f"`{font.plaintext[resource.descriptor_offset:resource.descriptor_offset + 24].hex()}` |"
        )
    return rows


def find_unmapped(font_data: FontData, count: int) -> list[int]:
    result = [
        codepoint
        for codepoint, glyph_index in enumerate(font_data.charmap)
        if glyph_index == 0 and codepoint != 0
    ]
    if len(result) < count:
        raise FontBuildPhase1Error("not enough unmapped BMP entries for relocation probe")
    return result[:count]


def growth_probe(font: CleanFont, append_count: int) -> XprFont:
    record = font.parsed.font_data.glyphs[0]
    mappings = {codepoint: record for codepoint in find_unmapped(font.parsed.font_data, append_count)}
    new_user, _ = font.parsed.font_data.append(mappings)
    return XprFont(font.parsed.replace_user(new_user))


def build_semantics_report(fonts: Sequence[CleanFont], output_path: Path) -> None:
    report = [
        "# Clean JPN FONT build semantics",
        "",
        "This report is generated only from `font/JPN/00c7c9f9.xpr` and `font/JPN/001cbbd1.xpr`. No MLG/MLG_CN FontData, charmap, GlyphRecord, or bitmap is an input.",
        "",
        "## PROVEN_FROM_FILE_STRUCTURE",
        "",
        "| selector | encrypted bytes / SHA256 | decrypted SHA256 | XPR header_size | data_size | texture payload offset | atlas / pitch / format | USER offset / size | last_code | mapped / records | count prefix | record start / suffix |",
        "|---|---|---|---:|---:|---:|---|---|---|---:|---|---|",
    ]
    for font in fonts:
        xpr = font.parsed
        data = xpr.font_data
        prefix_value = int.from_bytes(data.record_prefix, "big") if data.record_prefix else None
        report.append(
            f"| {font.selector} | {len(font.encrypted):,} / `{sha256(font.encrypted)}` | "
            f"`{sha256(font.plaintext)}` | `0x{xpr.header_size:X}` | `0x{xpr.data_size:X}` | "
            f"`0x{xpr.texture_data_offset:X}` | {xpr.texture.width}×{xpr.texture.height} / "
            f"{xpr.texture.pitch} / {xpr.texture.data_format}, tiled={xpr.texture.tiled}, endian={xpr.texture.endian} | "
            f"`0x{xpr.user.offset:X}` / `0x{xpr.user.size:X}` | U+{data.last_code:04X} | "
            f"{len(data.mapped()):,} / {len(data.glyphs):,} | "
            f"{len(data.record_prefix)}-byte BE `{data.record_prefix.hex()}` = {prefix_value} | "
            f"USER+`0x{data.record_offset:X}` / {len(data.suffix)} bytes |"
        )
    report.extend(
        [
            "",
            "Both clean files independently expose a **2-byte big-endian glyph-count prefix**. For clean 00c7 it is `0x0905 = 2309`; for clean 001c it is `0x0167 = 359`. In each file the prefix value equals the exact number of following 16-byte GlyphRecords, and the record table ends exactly at USER end (no suffix/trailer). This conclusion does not reuse the patched MLG_CN0007 4-byte count-mirror PoC.",
            "",
            "GlyphRecord layout in both clean files is eight big-endian u16 fields (stride `0x10`): `u0, v0, u1, v1, bearing_x_raw, width, advance, reserved`.",
            "",
            "### Resource descriptors",
            "",
            "| selector | index | identity | descriptor offset | payload offset | payload size | name offset | raw 24-byte descriptor |",
            "|---|---:|---|---:|---:|---:|---:|---|",
        ]
    )
    for font in fonts:
        report.extend(descriptor_summary(font))
    report.extend(
        [
            "",
            "For both files, resource 0 `TX2D/FontTexture` is at file `0x5C`, size `0x34`; resource 1 `USER/FontData` begins at `0x90`. The raw atlas begins at `0x0C + header_size`, and its offset has residue `0x1C mod 0x800`. Dense charmap entries are big-endian u16 and begin at USER+`0x16`; the record-prefix boundary is the charmap end rounded up to an 8-byte boundary.",
            "",
            "### Deterministic USER-growth and relocation probes",
            "",
            "The probes below append copies of a clean record only in memory to previously unmapped codepoints. They prove which file fields a structurally valid rebuild changes; they are **not runtime glyph validation**.",
            "",
            "| selector | original USER→texture slack | one-record USER size | one-record texture offset | first probe crossing alignment | relocated texture offset | header_size delta | data_size delta |",
            "|---|---:|---:|---:|---:|---:|---:|---:|",
        ]
    )
    for font in fonts:
        xpr = font.parsed
        slack = xpr.texture_data_offset - (xpr.user.offset + xpr.user.size)
        crossing = slack // GLYPH_RECORD_SIZE + 1
        one = growth_probe(font, 1)
        moved = growth_probe(font, crossing)
        report.append(
            f"| {font.selector} | `0x{slack:X}` | `0x{one.user.size:X}` | "
            f"`0x{one.texture_data_offset:X}` | {crossing} records | "
            f"`0x{moved.texture_data_offset:X}` | "
            f"`+0x{moved.header_size - xpr.header_size:X}` | "
            f"`+0x{moved.data_size - xpr.data_size:X}` |"
        )
    report.extend(
        [
            "",
            "Structural update rules established by the probes:",
            "",
            "1. The BE u16 count prefix must equal the rebuilt record count. The dense charmap must reference only existing u16 glyph indices.",
            "2. The USER descriptor size changes with charmap/alignment/record-table growth. USER offset remains `0x90` while the preceding descriptor/header topology is retained.",
            "3. Texture payload offset is recomputed at the clean file's `0x1C mod 0x800` alignment residue. Once USER growth crosses the available gap, the XPR `header_size` at file `0x04` changes by the same relocation delta.",
            "4. XPR `data_size` at file `0x08` equals the atlas byte count. It does not change for USER-only growth; it must become `0x1000000` for a 4096×4096 8-bit atlas.",
            "5. Resource descriptor relative offsets/sizes at file `0x10` and `0x28` must be rewritten from the new layout. In the clean topology, TX2D and USER relative offsets remain stable while USER size grows; a generalized builder still computes every descriptor rather than assuming this.",
            "6. TX2D geometry is packed in the 0x34-byte TX2D payload: pitch/tiled in fetch word at TX2D+`0x1C`, format/endian at +`0x20`, and width/height at +`0x24`. Atlas bytes follow the complete XPR header, not the TX2D resource payload.",
            "7. OuterCrypt is applied only after the complete plaintext is rebuilt, using the destination selector filename stem. The seed is not copied from a donor file.",
            "",
            "For a future 4096×4096 clean 001c rebuild, the builder must update TX2D width, height and pitch to 4096, retain format=2/tiled=0/endian=0, set XPR data_size and texture payload length to `0x1000000`, recompute USER size/resource descriptors/header_size/texture offset/alignment, and encrypt with the `001cbbd1` destination seed.",
            "",
            "## PROVEN_FROM_EXISTING_RUNTIME",
            "",
            "- The 001c runtime path and 001c-owned TX2D selection are proven by the existing runtime fixture.",
            "- A 4096×4096 / 16 MiB small atlas is runtime-proven when the exact-version Width/Height runtime patch is synchronized to 4096×4096.",
            "- The historical 2 MiB fixed-limit claim is retracted; Phase 1 does not reopen it.",
            "- Existing 00c7 append/count/new-atlas runtime PoCs prove only the patched MLG_CN0007-derived plaintext selected as 00c7, not this clean JPN00c7 structure.",
            "",
            "## NEEDS_NEW_RUNTIME_VALIDATION",
            "",
            "- A clean-JPN00c7 self-owned build with its 2-byte BE count prefix, rebuilt USER and any texture relocation.",
            "- A clean-JPN001c self-owned 4096×4096 output (the existing runtime proof used patched MLG000e plaintext as compatibility/capacity evidence).",
            "- Full union-charset large and small outputs, including SC Han overrides, punctuation policy, metric policy and scene coverage.",
            "- Multi-glyph relocation after all descriptor/header updates, even though the resulting plaintext reparses statically.",
            "",
            "## UNKNOWN",
            "",
            "- Whether clean JPN00c7 accepts a full rebuild at runtime; no claim is promoted from the 3209→3210 patched-MLG_CN PoC.",
            "- The final large/small selector split for each production character; Phase 1 uses the union worst case.",
            "- The final source policy for Chinese punctuation and overlapping Japanese/fullwidth punctuation.",
            "- Final raster size, baseline, advance and packing profile for any of the three candidate source fonts.",
            "",
            "## Future builder output contract",
            "",
            "Each candidate will emit `00c7c9f9.xpr`, `001cbbd1.xpr`, `FONT_GLYPH_MANIFEST.csv`, `FONT_BUILD_MANIFEST.json`, and `FONT_VALIDATION_REPORT.md`. The glyph manifest contract includes: `selector, codepoint, character, glyph_index, atlas_x, atlas_y, width, height, bearing, advance, glyph_source, font_file, font_face_index, font_size, baseline, bitmap_sha256, is_han_override`.",
            "",
            "The CLI already accepts `--font-file`, `--font-face-index`, clean base paths and `--output-dir`. Phase 1 never opens or embeds a font file. A later rasterization phase must keep charset, atlas geometry, pixel size, padding, rasterizer settings, baseline, advance and packing algorithm identical across Sarasa UI SC, Source Han Sans SC and Microsoft YaHei UI Bold; only the Chinese glyph source changes. Microsoft YaHei remains local-test-only.",
        ]
    )
    atomic_write_text(output_path, "\n".join(report) + "\n")


def retained_clean_indices(font: CleanFont) -> set[int]:
    indices = {0}
    for codepoint, glyph_index in font.parsed.font_data.mapped().items():
        if not is_han(codepoint):
            indices.add(glyph_index)
    return indices


def fixed_cell_rectangles(
    font: CleanFont,
    entries: Sequence[CharsetEntry],
    pixel_size: int,
    padding: int,
) -> tuple[list[Rectangle], dict[str, int]]:
    data = font.parsed.font_data
    mapped = data.mapped()
    retained = retained_clean_indices(font)
    rectangles: list[Rectangle] = []
    zero_bitmap_records = 0
    for glyph_index in sorted(retained):
        glyph = data.glyphs[glyph_index]
        width = glyph.u1 - glyph.u0
        height = glyph.v1 - glyph.v0
        if width <= 0 or height <= 0:
            zero_bitmap_records += 1
            continue
        rectangles.append(
            Rectangle(f"clean:{glyph_index:05d}", width + 2 * padding, height + 2 * padding)
        )

    han_entries = [entry for entry in entries if is_han(entry.codepoint)]
    han_override = sum(entry.codepoint in mapped for entry in han_entries)
    missing_han = len(han_entries) - han_override
    missing_non_han = [
        entry for entry in entries if not is_han(entry.codepoint) and entry.codepoint not in mapped
    ]
    generated = [*han_entries, *missing_non_han]
    for entry in generated:
        rectangles.append(
            Rectangle(
                f"generated:{entry.codepoint:06X}",
                pixel_size + 2 * padding,
                pixel_size + 2 * padding,
            )
        )
    counts = {
        "retained_clean_glyph_count": len(retained),
        "retained_zero_bitmap_records": zero_bitmap_records,
        "han_override_count": han_override,
        "new_missing_han_count": missing_han,
        "missing_non_han_count": len(missing_non_han),
        "generated_glyph_count": len(generated),
        "total_final_glyph_count": len(retained) + len(generated),
    }
    return rectangles, counts


def pack_shelf_ffd(
    rectangles: Sequence[Rectangle],
    width: int = ATLAS_WIDTH,
    height: int = ATLAS_HEIGHT,
) -> PackingResult:
    """Deterministic first-fit-decreasing shelf packing without rotation."""

    shelves: list[list[int]] = []  # y, height, next_x
    overflow = False
    required_area = 0
    for rectangle in sorted(rectangles, key=lambda item: (-item.height, -item.width, item.key)):
        required_area += rectangle.width * rectangle.height
        if rectangle.width > width or rectangle.height > height:
            overflow = True
            continue
        selected: list[int] | None = None
        for shelf in shelves:
            if rectangle.height <= shelf[1] and shelf[2] + rectangle.width <= width:
                selected = shelf
                break
        if selected is None:
            y = sum(shelf[1] for shelf in shelves)
            selected = [y, rectangle.height, 0]
            shelves.append(selected)
        selected[2] += rectangle.width
        if selected[0] + selected[1] > height:
            overflow = True
    packed_height = sum(shelf[1] for shelf in shelves)
    area = width * height
    return PackingResult(
        overflow=overflow,
        packed_height=packed_height,
        required_area=required_area,
        free_area=area - required_area,
        rectangle_count=len(rectangles),
    )


def write_capacity_outputs(
    fonts: Sequence[CleanFont],
    entries: Sequence[CharsetEntry],
    report_dir: Path,
) -> None:
    fields = (
        "selector",
        "atlas_width",
        "atlas_height",
        "pixel_size",
        "padding",
        "packing_algorithm",
        "selector_requirement",
        "retained_clean_glyph_count",
        "retained_zero_bitmap_records",
        "han_override_count",
        "new_missing_han_count",
        "missing_non_han_count",
        "generated_glyph_count",
        "total_final_glyph_count",
        "packed_rectangle_count",
        "projected_used_texels",
        "projected_usage_percent",
        "free_texels",
        "packed_height",
        "overflow",
    )
    rows: list[dict[str, object]] = []
    for font in fonts:
        for pixel_size in PIXEL_SIZES:
            for padding in PADDINGS:
                rectangles, counts = fixed_cell_rectangles(font, entries, pixel_size, padding)
                packed = pack_shelf_ffd(rectangles)
                rows.append(
                    {
                        "selector": font.selector,
                        "atlas_width": ATLAS_WIDTH,
                        "atlas_height": ATLAS_HEIGHT,
                        "pixel_size": pixel_size,
                        "padding": padding,
                        "packing_algorithm": "SHELF_FIRST_FIT_DECREASING_NO_ROTATION",
                        "selector_requirement": SELECTOR_REQUIREMENT,
                        **counts,
                        "packed_rectangle_count": packed.rectangle_count,
                        "projected_used_texels": packed.required_area,
                        "projected_usage_percent": f"{100 * packed.required_area / (ATLAS_WIDTH * ATLAS_HEIGHT):.3f}",
                        "free_texels": packed.free_area,
                        "packed_height": packed.packed_height,
                        "overflow": "YES" if packed.overflow else "NO",
                    }
                )
    write_csv(report_dir / "FONT_ATLAS_CAPACITY_SIMULATION.csv", fields, rows)

    report = [
        "# 4096×4096 atlas capacity simulation",
        "",
        "Status: **PLANNING ESTIMATE — NOT A RASTERIZED BUILD**",
        "",
        "This is a deterministic `FIXED_CELL_CAPACITY` simulation for the complete production union. It is not the simple `(4096 / cell_size)^2` estimate: retained clean glyphs use their actual clean GlyphRecord rectangles, generated glyphs use the tested fixed cell, and all rectangles are run through shelf first-fit-decreasing packing without rotation.",
        "",
        "Planning policy: preserve unique non-Han clean JPN glyph records plus fallback record 0; generate every production Han from the future SC font (including same-codepoint clean-JPN overrides); add any production non-Han codepoint missing from the clean selector. Existing clean Han records outside the translation union are not retained. Chinese punctuation source remains undecided; mapped punctuation uses its clean rectangle only for this capacity estimate, without locking the final glyph-source policy.",
        "",
        f"Selector corpus is `{SELECTOR_REQUIREMENT}`; both large and small are simulated against the entire union.",
        "",
        "| selector | px | padding | retained clean | Han override | new missing Han | missing non-Han | final glyphs | usage | free texels | packed height | overflow |",
        "|---|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---|",
    ]
    for row in rows:
        report.append(
            f"| {row['selector']} | {row['pixel_size']} | {row['padding']} | "
            f"{row['retained_clean_glyph_count']} | {row['han_override_count']} | "
            f"{row['new_missing_han_count']} | {row['missing_non_han_count']} | "
            f"{row['total_final_glyph_count']} | {row['projected_usage_percent']}% | "
            f"{row['free_texels']} | {row['packed_height']} | {row['overflow']} |"
        )
    report.extend(
        [
            "",
            "`free texels` is atlas area minus padded rectangle area and may be negative. `overflow` is the result of the actual deterministic shelf placement, so it can be `YES` even when raw area alone appears sufficient. Real source-font bboxes, baseline and advance are unavailable in Phase 1; candidate comparison must rerun the same packer with identical raster settings.",
            "",
            "The CSV is the authoritative full matrix for 52/56/58/60/62/64/66 px and padding 1/2.",
        ]
    )
    atomic_write_text(report_dir / "FONT_ATLAS_CAPACITY_SIMULATION.md", "\n".join(report) + "\n")


def field_checks(original: XprFont, rebuilt: XprFont) -> dict[str, bool]:
    return {
        "XPR2 magic": rebuilt.data[:4] == b"XPR2",
        "resource count": rebuilt.resource_count == original.resource_count,
        "USER content": rebuilt.user.payload == original.user.payload,
        "charmap": rebuilt.font_data.charmap == original.font_data.charmap,
        "GlyphRecords": glyph_bytes(rebuilt.font_data.glyphs)
        == glyph_bytes(original.font_data.glyphs),
        "TX2D descriptor": rebuilt.tx2d.payload == original.tx2d.payload,
        "TX2D bitmap": rebuilt.texture.texels == original.texture.texels,
        "all offsets": tuple(resource.offset for resource in rebuilt.resources)
        == tuple(resource.offset for resource in original.resources)
        and rebuilt.texture_data_offset == original.texture_data_offset,
        "all sizes": tuple(resource.size for resource in rebuilt.resources)
        == tuple(resource.size for resource in original.resources)
        and rebuilt.header_size == original.header_size
        and rebuilt.data_size == original.data_size,
        "alignment": rebuilt.texture_data_offset % 0x800
        == original.texture_data_offset % 0x800
        == 0x1C,
    }


def write_roundtrip_report(fonts: Sequence[CleanFont], output_path: Path) -> None:
    results: list[dict[str, object]] = []
    for font in fonts:
        rebuilt_plaintext = font.parsed.rebuild()
        rebuilt = XprFont(rebuilt_plaintext)
        encrypted = outer_transform(rebuilt_plaintext, filename_seed(font.path.name))
        decrypted_again = outer_transform(encrypted, filename_seed(font.path.name))
        checks = field_checks(font.parsed, rebuilt)
        checks.update(
            {
                "decrypted plaintext byte-identical": rebuilt_plaintext == font.plaintext,
                "encrypted bytes byte-identical": encrypted == font.encrypted,
                "encrypt→decrypt plaintext byte-identical": decrypted_again == font.plaintext,
                "OuterCrypt destination selector seed": filename_seed(font.path.name)
                == filename_seed(Path(font.selector).name),
            }
        )
        results.append(
            {
                "font": font,
                "checks": checks,
                "status": "PASS" if all(checks.values()) else "FAIL",
                "rebuilt_plaintext_sha256": sha256(rebuilt_plaintext),
                "rebuilt_encrypted_sha256": sha256(encrypted),
            }
        )

    report = [
        "# FONT clean deterministic round-trip report",
        "",
        "Pipeline: clean encrypted XPR → destination-filename OuterCrypt decrypt → parse → topology rebuild with no semantic changes → destination-filename encrypt → decrypt again → compare.",
        "",
        "Any mismatch is a failure; no canonicalization exception is used.",
        "",
        "| selector | seed | original decrypted SHA256 | rebuilt decrypted SHA256 | rebuilt encrypted SHA256 | plaintext exact | encrypted exact | status |",
        "|---|---:|---|---|---|---|---|---|",
    ]
    for result in results:
        font = result["font"]
        checks = result["checks"]
        report.append(
            f"| {font.selector} | `0x{filename_seed(font.path.name):08X}` | "
            f"`{sha256(font.plaintext)}` | `{result['rebuilt_plaintext_sha256']}` | "
            f"`{result['rebuilt_encrypted_sha256']}` | "
            f"{'PASS' if checks['decrypted plaintext byte-identical'] else 'FAIL'} | "
            f"{'PASS' if checks['encrypted bytes byte-identical'] else 'FAIL'} | "
            f"**{result['status']}** |"
        )
    for result in results:
        font = result["font"]
        report.extend(["", f"## {font.selector}", "", "| validation | result |", "|---|---|"])
        for name, passed in result["checks"].items():
            report.append(f"| {name} | {'PASS' if passed else 'FAIL'} |")
    overall = "PASS" if all(result["status"] == "PASS" for result in results) else "FAIL"
    report.extend(["", f"Overall: **{overall}**", ""])
    atomic_write_text(output_path, "\n".join(report))
    if overall != "PASS":
        raise FontBuildPhase1Error("clean XPR deterministic round-trip failed")


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--analyze", action="store_true", help="write charset, structure and capacity reports")
    parser.add_argument(
        "--roundtrip-clean",
        action="store_true",
        help="run exact clean decrypt/rebuild/encrypt validation",
    )
    parser.add_argument(
        "--build-clean-00c7",
        action="store_true",
        help="build the local-only Phase-2A clean JPN 00C7 runtime fixture",
    )
    parser.add_argument("--large-base", type=Path, default=ROOT / "font/JPN/00c7c9f9.xpr")
    parser.add_argument("--small-base", type=Path, default=ROOT / "font/JPN/001cbbd1.xpr")
    parser.add_argument(
        "--font-file",
        type=Path,
        help="external TTF/OTF/TTC input for Phase-2A rasterization",
    )
    parser.add_argument("--font-face-index", type=int, default=0)
    parser.add_argument("--output-dir", type=Path, default=ROOT / "font/build")
    parser.add_argument(
        "--production-manifest",
        type=Path,
        default=ROOT / "build/translation/compiled_translation_manifest.csv",
    )
    parser.add_argument("--briefing-dir", type=Path, default=ROOT / "translations/briefing")
    args = parser.parse_args()
    if not args.analyze and not args.roundtrip_clean and not args.build_clean_00c7:
        parser.error("at least one of --analyze, --roundtrip-clean, or --build-clean-00c7 is required")
    if args.build_clean_00c7 and args.font_file is None:
        parser.error("--build-clean-00c7 requires --font-file")
    if args.font_face_index < 0:
        parser.error("--font-face-index must be non-negative")
    return args


def main() -> int:
    args = parse_args()
    fonts = (
        load_clean_font("00c7c9f9.xpr", args.large_base.resolve()),
        load_clean_font("001cbbd1.xpr", args.small_base.resolve()),
    )
    if args.analyze:
        rows, metadata = load_production_corpus(
            args.production_manifest.resolve(),
            args.briefing_dir.resolve(),
        )
        entries, census_metadata = census(rows)
        write_charset_outputs(entries, metadata, census_metadata, args.output_dir / "charset")
        write_control_token_audit(
            rows,
            metadata,
            args.output_dir / "reports/FONT_CONTROL_TOKEN_AUDIT.md",
        )
        build_semantics_report(
            fonts,
            args.output_dir / "research/CLEAN_JPN_FONT_BUILD_SEMANTICS.md",
        )
        write_capacity_outputs(fonts, entries, args.output_dir / "reports")
        print(f"CHARSET_TOTAL_OCCURRENCES={sum(entry.occurrence_count for entry in entries)}")
        print(f"CHARSET_UNIQUE={len(entries)}")
        print(f"CHARSET_UNIQUE_HAN={sum(is_han(entry.codepoint) for entry in entries)}")
        print(f"SELECTOR_REQUIREMENT={SELECTOR_REQUIREMENT}")
    if args.roundtrip_clean:
        write_roundtrip_report(
            fonts,
            args.output_dir / "reports/FONT_CLEAN_ROUNDTRIP_REPORT.md",
        )
        print("ROUNDTRIP_00C7=PASS")
        print("ROUNDTRIP_001C=PASS")
    if args.build_clean_00c7:
        rows, metadata = load_production_corpus(
            args.production_manifest.resolve(),
            args.briefing_dir.resolve(),
        )
        entries, _ = census(rows)
        manifest = build_clean_00c7_fixture(
            fonts[0],
            args.font_file.resolve(),
            args.output_dir / "runtime_fixture_00c7",
            ROOT / "font/runtime_test/00c7_phase2a",
            face_index=args.font_face_index,
            required_codepoints={entry.codepoint for entry in entries},
            charset_source_hash=str(metadata["source_sha256"]),
        )
        print(f"PHASE2A_SOURCE_FONT={manifest['source_font_path']}")
        print(f"PHASE2A_GENERATED_HAN={manifest['generated_han_count']}")
        print(f"PHASE2A_PRESERVED={manifest['preserved_clean_glyph_count']}")
        print(f"PHASE2A_RECORDS={manifest['record_count']}")
        print(f"PHASE2A_PLAINTEXT_SHA256={manifest['plaintext_xpr_sha256']}")
        print(f"PHASE2A_ENCRYPTED_SHA256={manifest['encrypted_xpr_sha256']}")
        print("PHASE2A_STATIC=PASS")
        print("PHASE2A_RUNTIME=NOT_YET_TESTED")
    print(f"OUTPUT_DIR={args.output_dir.resolve()}")
    return 0


if __name__ == "__main__":
    try:
        raise SystemExit(main())
    except FontBuildPhase1Error as error:
        print(f"ERROR={error}", file=sys.stderr)
        raise SystemExit(1)
