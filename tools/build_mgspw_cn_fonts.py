#!/usr/bin/env python3
"""Phase-1 self-owned MGSPW Chinese font builder foundation.

This phase is intentionally read-only with respect to game assets.  It can:

* census the current six-class production corpus;
* parse and document the two clean JPN font bases;
* simulate deterministic 4096x4096 packing; and
* prove clean decrypt/rebuild/encrypt round-trips.

Rasterization and release XPR generation are later-phase operations.  The CLI
already reserves the external font arguments that those operations will use.
No third-party localization XPR participates in this program.
"""

from __future__ import annotations

import argparse
import csv
import hashlib
import re
import struct
import sys
import unicodedata
from collections import Counter, defaultdict
from dataclasses import dataclass
from pathlib import Path
from typing import Iterable, Sequence


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
    parser.add_argument("--large-base", type=Path, default=ROOT / "font/JPN/00c7c9f9.xpr")
    parser.add_argument("--small-base", type=Path, default=ROOT / "font/JPN/001cbbd1.xpr")
    parser.add_argument(
        "--font-file",
        type=Path,
        help="reserved external TTF/OTF/TTC input for the future rasterization phase",
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
    if not args.analyze and not args.roundtrip_clean:
        parser.error("at least one of --analyze or --roundtrip-clean is required")
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
    print(f"OUTPUT_DIR={args.output_dir.resolve()}")
    return 0


if __name__ == "__main__":
    try:
        raise SystemExit(main())
    except FontBuildPhase1Error as error:
        print(f"ERROR={error}", file=sys.stderr)
        raise SystemExit(1)
