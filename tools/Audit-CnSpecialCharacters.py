#!/usr/bin/env python3
"""Read-only audit of unusual characters and complete CN token forms."""

from __future__ import annotations

import argparse
import csv
import importlib.util
import json
import re
import sys
import unicodedata
from collections import Counter, defaultdict
from dataclasses import dataclass
from pathlib import Path
from typing import Any


ROOT = Path(__file__).resolve().parents[1]
AUDIT_PATH = ROOT / "tools" / "Audit-BriefingLayout.py"

# Match complete forms before inspecting residual characters.  The patterns
# intentionally accept unknown angle/brace forms so this audit does not assume
# that only the currently known <R=...> tag is present.
TOKEN_RE = re.compile(
    r"<[^<>\r\n]*>"
    r"|\{[^{}\r\n]*\}"
    r"|\\(?:u[0-9A-Fa-f]{4}|x[0-9A-Fa-f]{2}|.)"
    r"|\$[A-Za-z0-9_]+"
    r"|%(?:[0-9]+\$)?[A-Za-z0-9_]+",
    re.DOTALL,
)

ASCII_PUNCTUATION = set(chr(codepoint) for codepoint in range(0x21, 0x30))
ASCII_PUNCTUATION.update(chr(codepoint) for codepoint in range(0x3A, 0x41))
ASCII_PUNCTUATION.update(chr(codepoint) for codepoint in range(0x5B, 0x60))
ASCII_PUNCTUATION.update(chr(codepoint) for codepoint in range(0x7B, 0x7F))
COMMON_CJK_PUNCTUATION = set(
    "，。！？；：、（）［］【】《》「」『』〈〉〔〕〖〗〘〙〚“”‘’‚‛„‟—–…·・～〜"
)


@dataclass(frozen=True)
class MappingRow:
    family: str
    resource_class: str
    file_id: str
    unique_index: int
    cn_text: str


def load_audit_module():
    spec = importlib.util.spec_from_file_location("audit_briefing_layout_for_specials", AUDIT_PATH)
    if spec is None or spec.loader is None:
        raise RuntimeError(f"cannot load {AUDIT_PATH}")
    module = importlib.util.module_from_spec(spec)
    sys.modules[spec.name] = module
    spec.loader.exec_module(module)
    return module


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--root", type=Path, default=ROOT)
    parser.add_argument(
        "--all-mappings",
        action="store_true",
        help="scan every authoritative translation CSV instead of BRIEFING only",
    )
    parser.add_argument(
        "--json-output",
        type=Path,
        default=None,
        help="default: <root>/build/translation/cn_special_character_audit.json",
    )
    parser.add_argument(
        "--markdown-output",
        type=Path,
        default=None,
        help="default: <root>/build/translation/cn_special_character_audit.md",
    )
    return parser.parse_args()


def is_han(character: str) -> bool:
    codepoint = ord(character)
    return (
        0x3400 <= codepoint <= 0x4DBF
        or 0x4E00 <= codepoint <= 0x9FFF
        or 0xF900 <= codepoint <= 0xFAFF
        or 0x20000 <= codepoint <= 0x2FA1F
    )


def is_normal_character(character: str) -> bool:
    if character == "\n" or character == " ":
        return True
    if character.isascii() and (character.isalnum() or character in ASCII_PUNCTUATION):
        return True
    return is_han(character) or character in COMMON_CJK_PUNCTUATION


def codepoint_text(value: str) -> str:
    return " ".join(f"U+{ord(character):04X}" for character in value)


def display_character(character: str) -> str:
    if character == "\n":
        return "<LF>"
    if character == "\r":
        return "<CR>"
    if character == "\t":
        return "<TAB>"
    if character == " ":
        return "<SPACE>"
    if character == "\ufeff":
        return "<BOM>"
    return character


def token_kind(token: str) -> str:
    if token.startswith("<"):
        if token.startswith("<R="):
            return "ANGLE_RUBY"
        if token.startswith("<I="):
            return "ANGLE_ICON_OR_INLINE"
        if token.startswith("<C="):
            return "ANGLE_COLOR_OR_CONTROL"
        if token == "<->":
            return "ANGLE_SEPARATOR_CONTROL"
        return "ANGLE_UNKNOWN_OR_OTHER"
    if token.startswith("{"):
        return "BRACE_TOKEN"
    if token.startswith("\\"):
        return "BACKSLASH_SEQUENCE"
    if token.startswith("$"):
        return "DOLLAR_PLACEHOLDER"
    if token.startswith("%"):
        return "PERCENT_TOKEN"
    return "OTHER_TOKEN"


def token_payload(token: str) -> str:
    if (token.startswith("<") and token.endswith(">")) or (token.startswith("{") and token.endswith("}")):
        return token[1:-1]
    return token


def example_record(row: Any, token: str | None = None, character: str | None = None) -> dict[str, Any]:
    record = {
        "resource_class": getattr(row, "resource_class", "BRIEFING_NBE"),
        "resource_type": row.family,
        "file_id": row.file_id,
        "unique_index": row.unique_index,
        "identity": f"{row.file_id}#{row.unique_index}",
        "cn_text": row.cn_text,
    }
    if token is not None:
        record["token"] = token
    if character is not None:
        record["character"] = character
    return record


def load_all_mapping_rows(root: Path) -> tuple[list[MappingRow], dict[str, Any]]:
    # The repository's completed translation corpus is authoritative in
    # translations/<resource_class>/*.csv.  The similarly named
    # work/.../sol_translation_mappings directory also contains historical
    # sharded/manifest JSONs, so counting every JSON there double-counts rows
    # and misses logical file_ids whose final CSV already exists.
    mapping_root = root / "translations"
    class_dirs = {
        "briefing": "BRIEFING_NBE",
        "loose_olang": "LOOSE_OLANG",
        "ohd": "OHD",
        "slot_olang": "SLOT_OLANG",
        "stagedat_olang": "STAGEDAT_OLANG",
        "ypk_gtt": "YPK_GTT",
    }
    paths = [
        (resource_class, path)
        for directory, resource_class in class_dirs.items()
        for path in sorted((mapping_root / directory).glob("*.csv"))
    ]
    if not paths:
        raise RuntimeError(f"no authoritative translation CSV files found under {mapping_root}")
    rows: list[MappingRow] = []
    file_counts: Counter[str] = Counter()
    row_counts: Counter[str] = Counter()
    nonempty_counts: Counter[str] = Counter()
    empty_counts: Counter[str] = Counter()
    schema_counts: Counter[str] = Counter()
    for resource_class, path in paths:
        file_counts[resource_class] += 1
        schema_counts[f"{resource_class}:csv"] += 1
        resource_type = resource_class
        if resource_class == "BRIEFING_NBE":
            resource_type = "BRIEFING_FILES" if path.stem.startswith("BRIEFING_FILES_BLOCK_") else "BRIEFING_MISSION"
        with path.open("r", encoding="utf-8-sig", newline="") as handle:
            normalized = list(csv.DictReader(handle))
        file_id = path.stem
        if file_id.startswith("BRIEFING_FILES_BLOCK_"):
            resource_type = "BRIEFING_FILES"
        elif file_id.startswith("BRIEFING_MISSION_BLOCK_"):
            resource_type = "BRIEFING_MISSION"
        for position, item in enumerate(normalized):
            try:
                unique_index = int(item.get("unique_index", position))
            except (TypeError, ValueError) as error:
                raise RuntimeError(f"{path}: invalid unique_index at row {position}") from error
            cn_text = "" if item.get("cn_text") is None else str(item.get("cn_text", ""))
            rows.append(MappingRow(resource_type, resource_class, file_id, unique_index, cn_text))
            row_counts[resource_class] += 1
            if cn_text:
                nonempty_counts[resource_class] += 1
            else:
                empty_counts[resource_class] += 1
    return rows, {
        "mapping_root": str(mapping_root.relative_to(root)),
        "mapping_files": len(paths),
        "resource_classes": dict(sorted(file_counts.items())),
        "row_counts": dict(sorted(row_counts.items())),
        "nonempty_cn_row_counts": dict(sorted(nonempty_counts.items())),
        "empty_cn_row_counts": dict(sorted(empty_counts.items())),
        "schema_counts": dict(sorted(schema_counts.items())),
    }


def add_example(target: dict[str, dict[str, Any]], key: str, row: Any, **kwargs: Any) -> None:
    item = target.setdefault(key, {"examples": [], "families": Counter()})
    identity = f"{row.file_id}#{row.unique_index}"
    if identity not in {example["identity"] for example in item["examples"]} and len(item["examples"]) < 5:
        item["examples"].append(example_record(row, **kwargs))
    item["families"][row.family] += 1


def collect(rows: list[Any]) -> dict[str, Any]:
    token_data: dict[str, dict[str, Any]] = {}
    char_data: dict[str, dict[str, Any]] = {}
    nested_char_data: dict[str, dict[str, Any]] = {}
    token_type_counts: Counter[str] = Counter()
    token_counts: Counter[str] = Counter()
    special_char_counts: Counter[str] = Counter()
    nested_char_counts: Counter[str] = Counter()
    token_type_rows: dict[str, set[str]] = defaultdict(set)
    special_char_rows: dict[str, set[str]] = defaultdict(set)
    nested_char_rows: dict[str, set[str]] = defaultdict(set)
    row_special_types: Counter[str] = Counter()
    all_special_by_row: dict[str, set[str]] = defaultdict(set)

    for row in rows:
        cursor = 0
        row_types: set[str] = set()
        for match in TOKEN_RE.finditer(row.cn_text):
            residual = row.cn_text[cursor : match.start()]
            for character in residual:
                if not is_normal_character(character):
                    key = character
                    add_example(char_data, key, row, character=character)
                    special_char_counts[key] += 1
                    special_char_rows[key].add(f"{row.file_id}#{row.unique_index}")
                    row_types.add("SPECIAL_CHARACTER_OUTSIDE_TOKEN")
                    all_special_by_row[f"{row.file_id}#{row.unique_index}"].add(key)
            token = match.group(0)
            kind = token_kind(token)
            token_data.setdefault(token, {"kind": kind, "examples": [], "families": Counter()})
            add_example(token_data, token, row, token=token)
            token_counts[token] += 1
            token_type_counts[kind] += 1
            identity = f"{row.file_id}#{row.unique_index}"
            token_type_rows[kind].add(identity)
            row_types.add(kind)

            payload = token_payload(token)
            if token[:1] in {"<", "{"}:
                for character in payload:
                    if not is_normal_character(character):
                        key = character
                        add_example(nested_char_data, key, row, character=character)
                        nested_char_counts[key] += 1
                        nested_char_rows[key].add(identity)
                        row_types.add("SPECIAL_CHARACTER_INSIDE_TOKEN_PAYLOAD")
                        all_special_by_row[identity].add(f"{key} (inside {kind})")
            cursor = match.end()

        residual = row.cn_text[cursor:]
        for character in residual:
            if not is_normal_character(character):
                key = character
                add_example(char_data, key, row, character=character)
                special_char_counts[key] += 1
                special_char_rows[key].add(f"{row.file_id}#{row.unique_index}")
                row_types.add("SPECIAL_CHARACTER_OUTSIDE_TOKEN")
                all_special_by_row[f"{row.file_id}#{row.unique_index}"].add(key)
        for row_type in row_types:
            row_special_types[row_type] += 1

    def finalize(
        source: dict[str, dict[str, Any]],
        counts: Counter[str],
        nested: bool = False,
    ) -> list[dict[str, Any]]:
        result = []
        row_sets = nested_char_rows if nested else special_char_rows
        for key, item in source.items():
            raw = key
            if nested:
                value = raw
                item_kind = "TOKEN_PAYLOAD_CHARACTER"
            else:
                value = raw
                item_kind = "CHARACTER"
            families = item.pop("families")
            examples = item["examples"]
            result.append(
                {
                    "kind": item_kind,
                    "character": display_character(value),
                    "raw": value,
                    "code_points": codepoint_text(value),
                    "unicode_name": unicodedata.name(value, "<unnamed>"),
                    "category": unicodedata.category(value),
                    "occurrence_count": counts[value],
                    "row_count": len(row_sets[key]),
                    "families": dict(families),
                    "examples": examples,
                }
            )
        result.sort(key=lambda item: (-item["occurrence_count"], -item["row_count"], item["code_points"]))
        return result

    token_result = []
    for raw, item in token_data.items():
        families = item.pop("families")
        occurrences = token_counts[raw]
        token_result.append(
            {
                "kind": "TOKEN",
                "token_kind": item["kind"],
                "token": raw,
                "raw": raw,
                "code_points": codepoint_text(raw),
                "occurrence_count": occurrences,
                "row_count": len({example["identity"] for example in item["examples"]}) if len(item["examples"]) < 5 else None,
                "families": dict(families),
                "likely_game_markup_or_control": item["kind"] != "OTHER_TOKEN",
                "examples": item["examples"],
            }
        )
    # The example list is capped at five, so compute exact row counts here.
    for item in token_result:
        item["row_count"] = sum(1 for row in rows if item["token"] in row.cn_text)
    token_result.sort(key=lambda item: (-item["occurrence_count"], -item["row_count"], item["token_kind"], item["token"]))

    char_result = finalize(char_data, special_char_counts)
    nested_result = finalize(nested_char_data, nested_char_counts, nested=True)
    combined = [
        {
            "kind": "TOKEN",
            "label": item["token"],
            "occurrence_count": item["occurrence_count"],
            "row_count": item["row_count"],
            "likely_game_markup_or_control": item["likely_game_markup_or_control"],
        }
        for item in token_result
    ] + [
        {
            "kind": "CHARACTER",
            "label": item["character"],
            "occurrence_count": item["occurrence_count"],
            "row_count": item["row_count"],
            "likely_game_markup_or_control": False,
        }
        for item in char_result
    ]
    combined.sort(key=lambda item: (-item["occurrence_count"], -item["row_count"], item["kind"], item["label"]))

    return {
        "special_tokens": token_result,
        "special_characters": char_result,
        "special_characters_inside_token_payloads": nested_result,
        "token_kind_summary": {
            kind: {
                "occurrence_count": count,
                "row_count": len(token_type_rows[kind]),
                "likely_game_markup_or_control": kind != "OTHER_TOKEN",
            }
            for kind, count in sorted(token_type_counts.items())
        },
        "special_row_type_summary": dict(row_special_types),
        "most_common": combined[:50],
        "special_rows": len(all_special_by_row),
    }


def md_value(value: Any) -> str:
    return str(value).replace("`", "\\`").replace("|", "\\|").replace("\r", "\\r").replace("\n", "\\n")


def render_items(title: str, items: list[dict[str, Any]], token: bool) -> list[str]:
    lines = [f"## {title}", ""]
    if token:
        lines += [
            "| rank | token kind | token | occurrences | rows | likely markup/control | code points | examples |",
            "|---:|---|---|---:|---:|---|---|---|",
        ]
        for rank, item in enumerate(items, 1):
            examples = "<br>".join(
                f"`{md_value(example['identity'])}` {md_value(example['cn_text'])}" for example in item["examples"]
            )
            lines.append(
                f"| {rank} | `{item['token_kind']}` | `{md_value(item['token'])}` | {item['occurrence_count']} | {item['row_count']} | {item['likely_game_markup_or_control']} | `{item['code_points']}` | {examples} |"
            )
    else:
        lines += [
            "| rank | character | occurrences | rows | code point | Unicode name | category | examples |",
            "|---:|---|---:|---:|---|---|---|---|",
        ]
        for rank, item in enumerate(items, 1):
            examples = "<br>".join(
                f"`{md_value(example['identity'])}` {md_value(example['cn_text'])}" for example in item["examples"]
            )
            lines.append(
                f"| {rank} | `{md_value(item['character'])}` | {item['occurrence_count']} | {item['row_count']} | `{item['code_points']}` | `{md_value(item['unicode_name'])}` | `{item['category']}` | {examples} |"
            )
    lines.append("")
    return lines


def render_markdown(report: dict[str, Any]) -> str:
    lines = [
        "# CN Special Character / Token Audit",
        "",
        "只读审计当前全部中文 translation corpus；全量模式读取 translations/ 下按逻辑 file_id 汇总的权威 CSV。本报告不修改 mapping、CSV、DAT 或 KEY。完整 token 优先聚合，token payload 中的非普通字符另行列出。",
        "",
        "## Scope",
        "",
        f"- logical file_ids / translation files: `{report['scope']['mapping_files']}`",
        f"- cn_text rows: `{report['scope']['rows']}`",
        f"- resource classes: `{', '.join(report['scope']['resource_classes'])}`",
        f"- distinct special tokens: `{report['summary']['distinct_special_tokens']}`",
        f"- distinct special characters outside tokens: `{report['summary']['distinct_special_characters']}`",
        f"- distinct special characters inside token payloads: `{report['summary']['distinct_payload_characters']}`",
        "",
        "## Normal-character definition",
        "",
        "Normal set: CJK Han ideographs, ASCII letters/digits, ASCII punctuation, ASCII SPACE, LF, and the listed common Chinese/English punctuation. Other Unicode spaces, kana, arrows, emoji, private-use, combining/format/control characters are audited as special. Complete `<...>`, `{...}`, `%...`, `$...`, and backslash sequences are reported as tokens before residual character scanning.",
        "",
        "## Token-kind summary",
        "",
        "| token kind | occurrences | rows | likely markup/control |",
        "|---|---:|---:|---|",
    ]
    for kind, item in report["token_kind_summary"].items():
        lines.append(f"| `{kind}` | {item['occurrence_count']} | {item['row_count']} | {item['likely_game_markup_or_control']} |")
    lines += ["", "## Most common", "", "| rank | kind | value | occurrences | rows | likely markup/control |", "|---:|---|---|---:|---:|---|"]
    for rank, item in enumerate(report["most_common"], 1):
        lines.append(f"| {rank} | `{item['kind']}` | `{md_value(item['label'])}` | {item['occurrence_count']} | {item['row_count']} | {item['likely_game_markup_or_control']} |")
    lines.append("")
    lines += render_items("All complete special tokens", report["special_tokens"], True)
    lines += render_items("All special characters outside complete tokens", report["special_characters"], False)
    lines += render_items("Special characters inside token payloads", report["special_characters_inside_token_payloads"], False)
    lines += [
        "## Further consistency checks",
        "",
        "- Angle tokens should be compared with the corresponding JPN control-token sequence; this includes unknown angle forms, not only `<R=...>`.",
        "- Dollar, percent, brace, and backslash forms should be checked for exact count/order preservation by the compiler/builder.",
        "- Any kana, non-ASCII space, private-use, format/control, or other Unicode character inside a token payload needs a semantic review before changing or normalizing it.",
        "- Unicode symbols outside tokens, especially arrows or invisible characters, need manual confirmation because they may be intentional UI glyphs or accidental data.",
        "",
    ]
    return "\n".join(lines)


def main() -> int:
    args = parse_args()
    root = args.root.resolve()
    audit = load_audit_module()
    if args.all_mappings:
        rows, input_meta = load_all_mapping_rows(root)
        resource_classes = sorted({row.resource_class for row in rows})
        scope = {
            "mapping_directory": input_meta["mapping_root"],
            "mapping_files": input_meta["mapping_files"],
            "rows": len(rows),
            "nonempty_cn_rows": sum(bool(row.cn_text) for row in rows),
            "empty_cn_rows": sum(not bool(row.cn_text) for row in rows),
            "resource_classes": resource_classes,
            "resource_types": dict(sorted(Counter(row.family for row in rows).items())),
        }
    else:
        rows, input_meta = audit.load_rows(root)
        scope = {
            "mapping_directory": "work/luna_translation_templates/sol_translation_mappings/BRIEFING",
            "mapping_files": len({row.file_id for row in rows}),
            "rows": len(rows),
            "nonempty_cn_rows": sum(bool(row.cn_text) for row in rows),
            "empty_cn_rows": sum(not bool(row.cn_text) for row in rows),
            "resource_classes": ["BRIEFING_NBE"],
            "resource_types": dict(sorted(Counter(row.family for row in rows).items())),
        }
    data = collect(rows)
    report = {
        "status": "PASS",
        "scope": scope,
        "normal_character_definition": {
            "han": "CJK Unified Ideographs and extensions/common compatibility ideographs",
            "ascii_letters_digits": True,
            "ascii_punctuation": True,
            "space": "U+0020 SPACE only",
            "line_feed": "U+000A LF",
            "common_cjk_punctuation": sorted(f"U+{ord(value):04X}" for value in COMMON_CJK_PUNCTUATION),
        },
        "token_patterns": {
            "angle": r"<[^<>\\r\\n]*>",
            "brace": r"\\{[^{}\\r\\n]*\\}",
            "backslash": r"\\\\(?:u[0-9A-Fa-f]{4}|x[0-9A-Fa-f]{2}|.)",
            "dollar": r"\\$[A-Za-z0-9_]+",
            "percent": r"%(?:[0-9]+\\$)?[A-Za-z0-9_]+",
        },
        "inputs_meta": input_meta,
        "summary": {
            "distinct_special_tokens": len(data["special_tokens"]),
            "distinct_special_characters": len(data["special_characters"]),
            "distinct_payload_characters": len(data["special_characters_inside_token_payloads"]),
            "special_rows": data["special_rows"],
            "non_newline_input_changes": False,
        },
        **data,
    }
    json_path = (args.json_output or root / "build" / "translation" / "cn_special_character_audit.json").resolve()
    md_path = (args.markdown_output or root / "build" / "translation" / "cn_special_character_audit.md").resolve()
    json_path.parent.mkdir(parents=True, exist_ok=True)
    md_path.parent.mkdir(parents=True, exist_ok=True)
    json_path.write_text(json.dumps(report, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    md_path.write_text(render_markdown(report), encoding="utf-8")
    print(f"STATUS={report['status']}")
    print(f"ROWS={report['scope']['rows']}")
    print(f"DISTINCT_SPECIAL_TOKENS={report['summary']['distinct_special_tokens']}")
    print(f"DISTINCT_SPECIAL_CHARACTERS={report['summary']['distinct_special_characters']}")
    print(f"DISTINCT_PAYLOAD_CHARACTERS={report['summary']['distinct_payload_characters']}")
    print(f"JSON_OUTPUT={json_path}")
    print(f"MARKDOWN_OUTPUT={md_path}")
    return 0


if __name__ == "__main__":
    try:
        raise SystemExit(main())
    except (OSError, ValueError, json.JSONDecodeError, RuntimeError) as error:
        print(f"ERROR: {error}", file=sys.stderr)
        raise SystemExit(1)
