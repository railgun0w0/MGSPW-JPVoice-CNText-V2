#!/usr/bin/env python3
"""Dry-run BRIEFING display-line and visual-width audit.

The audit keeps BRIEFING FILES and BRIEFING MISSION as separate layout
profiles.  It reads frozen JPN rows from the BRIEFING templates and current CN
rows from the sol_translation_mappings JSON files.  It never rewrites a
translation, production CSV, DAT, or KEY.

Width estimator (fixed for this audit and intentionally not font-reverse-
engineered):

* CJK, kana, full-width, and other East Asian wide/full-width characters: 1.0
* ASCII uppercase: 0.70
* ASCII lowercase: 0.60
* ASCII digits: 0.60
* ASCII punctuation/symbols: 0.45
* ASCII spaces/tabs: 0.25
* combining marks: 0.0; other Unicode characters: 0.70

Markup/control tokens are scanned atomically using the same token families as
Compile-BriefingProductionTranslations.mjs and Build-BriefingDat.py:
angle tokens (<...>), dollar placeholders ($1/$2/$name), and printf-style
placeholders (%s/%d/%1$s/etc.). Control-only tokens have width 0. A valid
<R=visible,reading> token contributes only the visible/first field's width.
"""

from __future__ import annotations

import argparse
import csv
import json
import re
import sys
import unicodedata
from collections import Counter
from dataclasses import dataclass
from pathlib import Path
from typing import Iterable


ROOT = Path(__file__).resolve().parents[1]
FILES_PREFIX = "BRIEFING_FILES_BLOCK_"
MISSION_PREFIX = "BRIEFING_MISSION_BLOCK_"
EXPECTED = {
    "FILES": {"blocks": 363, "rows": 4810},
    "MISSION": {"blocks": 106, "rows": 835},
}

ANGLE_RE = re.compile(r"<[^<>]*>")
DOLLAR_RE = re.compile(r"\$[A-Za-z0-9_]+")
PRINTF_RE = re.compile(r"%(?:\d+\$)?[sdif]")
TOKEN_RE = re.compile(r"<[^<>]*>|\$[A-Za-z0-9_]+|%(?:\d+\$)?[sdif]")


WIDTH_CONFIG = {
    "east_asian_wide_or_fullwidth": 1.0,
    "ascii_uppercase": 0.70,
    "ascii_lowercase": 0.60,
    "ascii_digit": 0.60,
    "ascii_space_or_tab": 0.25,
    "ascii_punctuation_or_symbol": 0.45,
    "combining_mark": 0.0,
    "other_unicode": 0.70,
    "control_token": 0.0,
    "ruby_visible_field": "first field before the first comma",
}


class AuditFailure(RuntimeError):
    pass


@dataclass(frozen=True)
class Row:
    family: str
    file_id: str
    unique_index: int
    jpn_text: str
    cn_text: str


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--root", type=Path, default=ROOT)
    parser.add_argument(
        "--json-output",
        type=Path,
        default=None,
        help="default: <root>/build/translation/briefing_layout_audit.json",
    )
    parser.add_argument(
        "--markdown-output",
        type=Path,
        default=None,
        help="default: <root>/build/translation/briefing_layout_audit.md",
    )
    return parser.parse_args()


def family_for(file_id: str) -> str:
    if file_id.startswith(FILES_PREFIX):
        return "FILES"
    if file_id.startswith(MISSION_PREFIX):
        return "MISSION"
    raise AuditFailure(f"unsupported BRIEFING file_id: {file_id}")


def normalized_lines(text: str) -> list[str]:
    """Split display lines while ignoring only trailing empty line segments."""
    normalized = text.replace("\r\n", "\n").replace("\r", "\n")
    lines = normalized.split("\n")
    while lines and lines[-1] == "":
        lines.pop()
    return lines or ([""] if text == "" else [])


def plain_width(text: str) -> float:
    width = 0.0
    for char in text:
        codepoint = ord(char)
        if char in " \t":
            width += WIDTH_CONFIG["ascii_space_or_tab"]
        elif codepoint < 128 and "A" <= char <= "Z":
            width += WIDTH_CONFIG["ascii_uppercase"]
        elif codepoint < 128 and "a" <= char <= "z":
            width += WIDTH_CONFIG["ascii_lowercase"]
        elif codepoint < 128 and "0" <= char <= "9":
            width += WIDTH_CONFIG["ascii_digit"]
        elif codepoint < 128:
            width += WIDTH_CONFIG["ascii_punctuation_or_symbol"]
        elif unicodedata.combining(char) or unicodedata.category(char) in {"Mn", "Me"}:
            width += WIDTH_CONFIG["combining_mark"]
        elif unicodedata.east_asian_width(char) in {"W", "F"}:
            width += WIDTH_CONFIG["east_asian_wide_or_fullwidth"]
        else:
            width += WIDTH_CONFIG["other_unicode"]
    return round(width, 3)


def token_width(token: str) -> float:
    if token.startswith("<R=") and token.endswith(">"):
        body = token[3:-1]
        if "," in body:
            visible = body.split(",", 1)[0]
            return plain_width(visible)
    return WIDTH_CONFIG["control_token"]


def visual_width(text: str) -> float:
    """Estimate visible width without counting control syntax."""
    width = 0.0
    cursor = 0
    for match in TOKEN_RE.finditer(text):
        width += plain_width(text[cursor : match.start()])
        width += token_width(match.group(0))
        cursor = match.end()
    width += plain_width(text[cursor:])
    return round(width, 3)


def token_inventory(text: str) -> list[str]:
    return [*ANGLE_RE.findall(text), *DOLLAR_RE.findall(text), *PRINTF_RE.findall(text)]


def read_csv_rows(path: Path) -> list[dict[str, str]]:
    with path.open(encoding="utf-8-sig", newline="") as handle:
        return list(csv.DictReader(handle))


def load_rows(root: Path) -> tuple[list[Row], dict[str, object]]:
    template_root = root / "work" / "luna_translation_templates" / "BRIEFING"
    mapping_root = (
        root
        / "work"
        / "luna_translation_templates"
        / "sol_translation_mappings"
        / "BRIEFING"
    )
    production_root = root / "translations" / "briefing"
    template_paths = sorted(template_root.glob("BRIEFING_*_BLOCK_*.csv"))
    mapping_paths = sorted(mapping_root.glob("BRIEFING_*_BLOCK_*.json"))
    production_paths = sorted(production_root.glob("BRIEFING_*_BLOCK_*.csv"))
    if not template_paths:
        raise AuditFailure(f"no BRIEFING templates found under {template_root}")
    if {path.stem for path in template_paths} != {path.stem for path in mapping_paths}:
        missing = sorted({path.stem for path in template_paths} - {path.stem for path in mapping_paths})
        extra = sorted({path.stem for path in mapping_paths} - {path.stem for path in template_paths})
        raise AuditFailure(f"template/mapping set mismatch: missing={missing}, extra={extra}")

    mapping_rows: dict[str, dict[int, str]] = {}
    for path in mapping_paths:
        file_id = path.stem
        payload = json.loads(path.read_text(encoding="utf-8"))
        if payload.get("file_id") != file_id:
            raise AuditFailure(f"{file_id}: mapping file_id mismatch")
        translations = payload.get("translations")
        if not isinstance(translations, list):
            raise AuditFailure(f"{file_id}: translations is not an array")
        current: dict[int, str] = {}
        for item in translations:
            if not isinstance(item, dict):
                raise AuditFailure(f"{file_id}: translation item is not an object")
            index = int(item["unique_index"])
            if index in current:
                raise AuditFailure(f"{file_id}: duplicate mapping unique_index {index}")
            current[index] = str(item.get("cn_text", ""))
        mapping_rows[file_id] = current

    rows: list[Row] = []
    template_row_counts: Counter[str] = Counter()
    for path in template_paths:
        file_id = path.stem
        family = family_for(file_id)
        template_rows = read_csv_rows(path)
        expected_mapping = mapping_rows[file_id]
        expected_indices = list(range(len(template_rows)))
        if sorted(expected_mapping) != expected_indices:
            raise AuditFailure(f"{file_id}: mapping coverage is not contiguous with template")
        for position, source in enumerate(template_rows):
            if source.get("file_id") != file_id or int(source["unique_index"]) != position:
                raise AuditFailure(f"{file_id}#{position}: template identity mismatch")
            jpn_text = source.get("jpn_text", "")
            if not jpn_text:
                raise AuditFailure(f"{file_id}#{position}: empty jpn_text")
            rows.append(Row(family, file_id, position, jpn_text, expected_mapping[position]))
            template_row_counts[family] += 1

    production_cross_check = {
        "files": len(production_paths),
        "rows": 0,
        "missing_files": sorted({path.stem for path in template_paths} - {path.stem for path in production_paths}),
        "unexpected_files": sorted({path.stem for path in production_paths} - {path.stem for path in template_paths}),
        "jpn_mismatches": [],
        "cn_mismatches": [],
        "index_mismatches": [],
    }
    for path in production_paths:
        file_id = path.stem
        prod_rows = read_csv_rows(path)
        production_cross_check["rows"] += len(prod_rows)
        template_by_index = {(row.file_id, row.unique_index): row for row in rows if row.file_id == file_id}
        for prod in prod_rows:
            try:
                index = int(prod["unique_index"])
            except (KeyError, ValueError):
                production_cross_check["index_mismatches"].append(f"{file_id}: invalid unique_index")
                continue
            key = (file_id, index)
            source = template_by_index.get(key)
            if source is None:
                production_cross_check["index_mismatches"].append(f"{file_id}#{index}: missing template row")
                continue
            if prod.get("jpn_text", "") != source.jpn_text:
                production_cross_check["jpn_mismatches"].append(f"{file_id}#{index}")
            if prod.get("cn_text", "") != source.cn_text:
                production_cross_check["cn_mismatches"].append(f"{file_id}#{index}")

    return rows, {
        "template_files": len(template_paths),
        "mapping_files": len(mapping_paths),
        "production_cross_check": production_cross_check,
        "template_row_counts": dict(template_row_counts),
    }


def round_record(value: float) -> float:
    return round(value, 3)


def line_records(text: str) -> list[dict[str, object]]:
    return [
        {"line_index": index, "display_line": line, "width": round_record(visual_width(line))}
        for index, line in enumerate(normalized_lines(text))
    ]


def jpn_top(rows: Iterable[Row], limit: int = 20) -> list[dict[str, object]]:
    candidates = []
    for row in rows:
        for item in line_records(row.jpn_text):
            candidates.append(
                {
                    "file_id": row.file_id,
                    "unique_index": row.unique_index,
                    "line_index": item["line_index"],
                    "width": item["width"],
                    "display_line": item["display_line"],
                    "jpn_text": row.jpn_text,
                }
            )
    candidates.sort(key=lambda item: (-item["width"], item["file_id"], item["unique_index"], item["line_index"]))
    for rank, item in enumerate(candidates[:limit], 1):
        item["rank"] = rank
    return candidates[:limit]


def family_audit(rows: list[Row], family: str) -> dict[str, object]:
    family_rows = [row for row in rows if row.family == family]
    jpn_lines = [(row, item) for row in family_rows for item in line_records(row.jpn_text)]
    cn_lines = [(row, item) for row in family_rows for item in line_records(row.cn_text)]
    max_jpn_width = max((item["width"] for _, item in jpn_lines), default=0.0)
    max_jpn_item = next(
        (
            {"row": row, "line": item}
            for row, item in jpn_lines
            if item["width"] == max_jpn_width
        ),
        None,
    )
    jpn_multiline_rows = sum(len(normalized_lines(row.jpn_text)) > 1 for row in family_rows)
    cn_multiline_rows = sum(len(normalized_lines(row.cn_text)) > 1 for row in family_rows)
    same_line_count = sum(
        len(normalized_lines(row.jpn_text)) == len(normalized_lines(row.cn_text)) for row in family_rows
    )
    different_line_count = len(family_rows) - same_line_count
    cn_rows_over = []
    cn_display_lines_over = 0
    for row in family_rows:
        current_lines = line_records(row.cn_text)
        widest = max(current_lines, key=lambda item: (item["width"], -item["line_index"]))
        over_lines = [item for item in current_lines if item["width"] > max_jpn_width]
        cn_display_lines_over += len(over_lines)
        if over_lines:
            overflow = round_record(widest["width"] - max_jpn_width)
            cn_rows_over.append(
                {
                    "file_id": row.file_id,
                    "unique_index": row.unique_index,
                    "cn_text": row.cn_text,
                    "cn_display_line_count": len(current_lines),
                    "cn_max_line_width": widest["width"],
                    "family_limit": max_jpn_width,
                    "overflow_amount": overflow,
                    "widest_cn_display_line": widest["display_line"],
                    "widest_cn_line_index": widest["line_index"],
                    "over_limit_line_count": len(over_lines),
                    "jpn_text": row.jpn_text,
                    "jpn_display_line_count": len(line_records(row.jpn_text)),
                }
            )
    cn_rows_over.sort(key=lambda item: (-item["overflow_amount"], -item["cn_max_line_width"], item["file_id"], item["unique_index"]))
    max_lines_per_row = max((len(normalized_lines(row.jpn_text)) for row in family_rows), default=0)
    return {
        "blocks": len({row.file_id for row in family_rows}),
        "rows": len(family_rows),
        "jpn_display_lines": len(jpn_lines),
        "jpn_multiline_rows": jpn_multiline_rows,
        "jpn_max_display_lines_per_row": max_lines_per_row,
        "jpn_max_line_width": max_jpn_width,
        "jpn_max_source": {
            "file_id": max_jpn_item["row"].file_id if max_jpn_item else "",
            "unique_index": max_jpn_item["row"].unique_index if max_jpn_item else None,
            "line_index": max_jpn_item["line"]["line_index"] if max_jpn_item else None,
            "text": max_jpn_item["line"]["display_line"] if max_jpn_item else "",
            "width": max_jpn_width,
            "jpn_text": max_jpn_item["row"].jpn_text if max_jpn_item else "",
        },
        "cn_rows_over_limit": len(cn_rows_over),
        "cn_display_lines_over_limit": cn_display_lines_over,
        "jpn_multiline_but_cn_single_line": sum(
            len(normalized_lines(row.jpn_text)) > 1 and len(normalized_lines(row.cn_text)) == 1
            for row in family_rows
        ),
        "jpn_cn_same_line_count": same_line_count,
        "jpn_cn_different_line_count": different_line_count,
        "cn_multiline_rows": cn_multiline_rows,
        "jpn_widest_top20": jpn_top(family_rows, 20),
        "cn_overflow_top50": cn_rows_over[:50],
    }


def json_text(value: object) -> str:
    return json.dumps(value, ensure_ascii=False, sort_keys=True)


def md_code(value: object) -> str:
    return str(value).replace("`", "\\`").replace("|", "\\|").replace("\r", "\\r").replace("\n", "\\n")


def render_top_jpn(title: str, items: list[dict[str, object]]) -> list[str]:
    lines = [f"## {title}", "", "| rank | file_id | unique_index | line_index | width | display_line | full jpn_text |", "|---:|---|---:|---:|---:|---|---|"]
    for item in items:
        lines.append(
            f"| {item['rank']} | `{item['file_id']}` | {item['unique_index']} | {item['line_index']} | {item['width']:.3f} | `{md_code(item['display_line'])}` | `{md_code(item['jpn_text'])}` |"
        )
    lines.append("")
    return lines


def render_top_cn(title: str, items: list[dict[str, object]]) -> list[str]:
    lines = [f"## {title}", "", "| rank | file_id | unique_index | CN lines | CN max width | limit | overflow | widest CN line | CN text | JPN lines | JPN text |", "|---:|---|---:|---:|---:|---:|---:|---|---|---:|---|"]
    for rank, item in enumerate(items, 1):
        lines.append(
            f"| {rank} | `{item['file_id']}` | {item['unique_index']} | {item['cn_display_line_count']} | {item['cn_max_line_width']:.3f} | {item['family_limit']:.3f} | {item['overflow_amount']:.3f} | `{md_code(item['widest_cn_display_line'])}` | `{md_code(item['cn_text'])}` | {item['jpn_display_line_count']} | `{md_code(item['jpn_text'])}` |"
        )
    lines.append("")
    return lines


def render_markdown(report: dict[str, object]) -> str:
    lines = [
        "# BRIEFING Layout Audit (dry-run)",
        "",
        "本报告只统计当前 `sol-translation` 分支实际文件，不修改译文、mapping、production CSV、DAT 或 KEY。FILES 与 MISSION 使用完全独立的 JPN 宽度上限。",
        "",
        "## Width estimator",
        "",
        "| class | width |",
        "|---|---:|",
    ]
    for key, value in WIDTH_CONFIG.items():
        lines.append(f"| `{key}` | `{value}` |")
    lines += [
        "",
        "Token handling: `<...>`, `$...`, and printf placeholders are consumed atomically and have width 0; `<R=visible,reading>` contributes only the first/visible field. Trailing empty line segments from terminal LF/CRLF are not counted as display lines.",
        "",
        f"Inputs: `{json_text(report['inputs'])}`",
        "",
    ]
    for family, label in (("FILES", "BRIEFING_FILES"), ("MISSION", "BRIEFING_MISSION")):
        item = report[family.lower()]
        lines += [f"## {label}", "", "| metric | value |", "|---|---:|"]
        for key in (
            "blocks",
            "rows",
            "jpn_display_lines",
            "jpn_multiline_rows",
            "jpn_max_line_width",
            "jpn_max_display_lines_per_row",
            "cn_rows_over_limit",
            "cn_display_lines_over_limit",
            "jpn_multiline_but_cn_single_line",
            "jpn_cn_same_line_count",
            "jpn_cn_different_line_count",
        ):
            lines.append(f"| `{key}` | `{item[key]}` |")
        source = item["jpn_max_source"]
        lines += [
            "",
            "Max source:",
            "",
            f"- file_id: `{source['file_id']}`",
            f"- unique_index: `{source['unique_index']}`",
            f"- line_index: `{source['line_index']}`",
            f"- width: `{source['width']}`",
            f"- display line: `{md_code(source['text'])}`",
            f"- full jpn_text: `{md_code(source['jpn_text'])}`",
            "",
        ]
    lines += render_top_jpn("FILES JPN widest Top 20", report["files"]["jpn_widest_top20"])
    lines += render_top_jpn("MISSION JPN widest Top 20", report["mission"]["jpn_widest_top20"])
    lines += render_top_cn("FILES CN overflow Top 50", report["files"]["cn_overflow_top50"])
    lines += render_top_cn("MISSION CN overflow Top 50", report["mission"]["cn_overflow_top50"])
    return "\n".join(lines).rstrip() + "\n"


def main() -> int:
    args = parse_args()
    root = args.root.resolve()
    rows, input_meta = load_rows(root)
    cross_check = input_meta["production_cross_check"]
    cross_check_keys = (
        "missing_files",
        "unexpected_files",
        "jpn_mismatches",
        "cn_mismatches",
        "index_mismatches",
    )
    cross_check_ok = not any(cross_check[key] for key in cross_check_keys)
    report = {
        "status": "PASS" if cross_check_ok else "CROSS_CHECK_MISMATCH",
        "scope": "current frozen JPN BRIEFING corpus",
        "inputs": {
            "jpn_source": "work/luna_translation_templates/BRIEFING/*.csv",
            "cn_source": "work/luna_translation_templates/sol_translation_mappings/BRIEFING/*.json",
            "production_cross_check": "translations/briefing/*.csv",
        },
        "width_estimator": WIDTH_CONFIG,
        "token_rules": {
            "angle_tokens": "<[^<>]*>",
            "dollar_placeholders": "$[A-Za-z0-9_]+",
            "printf_placeholders": "%(?:\\d+\\$)?[sdif]",
            "control_only_width": 0.0,
            "ruby_visible_field": "first field before first comma in <R=...,...>",
        },
        "inputs_meta": input_meta,
        "files": family_audit(rows, "FILES"),
        "mission": family_audit(rows, "MISSION"),
    }
    for family in ("FILES", "MISSION"):
        actual = report[family.lower()]
        expected = EXPECTED[family]
        if actual["blocks"] != expected["blocks"] or actual["rows"] != expected["rows"]:
            raise AuditFailure(f"{family}: scope mismatch: actual={actual['blocks']}/{actual['rows']} expected={expected}")

    json_path = (args.json_output or root / "build" / "translation" / "briefing_layout_audit.json").resolve()
    md_path = (args.markdown_output or root / "build" / "translation" / "briefing_layout_audit.md").resolve()
    json_path.parent.mkdir(parents=True, exist_ok=True)
    md_path.parent.mkdir(parents=True, exist_ok=True)
    json_path.write_text(json.dumps(report, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    md_path.write_text(render_markdown(report), encoding="utf-8")

    print(f"STATUS={report['status']}")
    print(f"BRIEFING_FILES={report['files']['blocks']}/{report['files']['rows']}")
    print(f"BRIEFING_MISSION={report['mission']['blocks']}/{report['mission']['rows']}")
    for family in ("files", "mission"):
        item = report[family]
        print(f"{family.upper()}_JPN_DISPLAY_LINES={item['jpn_display_lines']}")
        print(f"{family.upper()}_JPN_MULTILINE_ROWS={item['jpn_multiline_rows']}")
        print(f"{family.upper()}_MAX_LINE_WIDTH={item['jpn_max_line_width']}")
        print(f"{family.upper()}_CN_ROWS_OVER_LIMIT={item['cn_rows_over_limit']}")
        print(f"{family.upper()}_CN_DISPLAY_LINES_OVER_LIMIT={item['cn_display_lines_over_limit']}")
    print(f"JSON_OUTPUT={json_path}")
    print(f"MARKDOWN_OUTPUT={md_path}")
    return 0


if __name__ == "__main__":
    try:
        raise SystemExit(main())
    except (AuditFailure, OSError, ValueError, json.JSONDecodeError) as error:
        print(f"ERROR: {error}", file=sys.stderr)
        raise SystemExit(1)
