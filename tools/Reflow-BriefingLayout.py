#!/usr/bin/env python3
"""Reflow overflowing BRIEFING CN text by inserting line breaks only.

This tool uses the estimator and line parsing from Audit-BriefingLayout.py.
It keeps FILES and MISSION independent, uses the current JPN maximum display
line count as a verified hard ceiling, and never rewrites translation wording.

Without --apply the tool is a dry-run. With --apply it changes only the
``cn_text`` JSON string of rows for which a legal reflow was found. It always
writes a dry-run report first and refuses to write if any non-newline text
would change.
"""

from __future__ import annotations

import argparse
import copy
import importlib.util
import json
import re
import sys
from dataclasses import dataclass
from pathlib import Path
from typing import Any


ROOT = Path(__file__).resolve().parents[1]
AUDIT_PATH = ROOT / "tools" / "Audit-BriefingLayout.py"
AUDIT_REPORT_PATH = ROOT / "build" / "translation" / "briefing_layout_audit.json"
MAPPING_ROOT_REL = Path("work/luna_translation_templates/sol_translation_mappings/BRIEFING")
FILES_PREFIX = "BRIEFING_FILES_BLOCK_"
MISSION_PREFIX = "BRIEFING_MISSION_BLOCK_"

WORD_OR_TOKEN_RE = re.compile(
    r"<[^<>]*>|\$[A-Za-z0-9_]+|%(?:\d+\$)?[sdif]|[A-Za-z]+|[0-9]+|.",
    re.DOTALL,
)
JSON_KEY_RE = re.compile(r'"translations"\s*:\s*')

CLOSING_CHARS = "，。！？；：、）》】」』〕〉》〗〙〛…—～~.,!?:;)]}"
OPENING_CHARS = "（《【「『〔〈〖〘〚([{"

BREAK_PENALTY = {
    "sentence": 0,
    "semicolon": 1,
    "comma_or_colon": 2,
    "enumeration": 3,
    "other": 8,
}


class ReflowFailure(RuntimeError):
    pass


@dataclass(frozen=True)
class Unit:
    text: str
    width: float
    visible: str


@dataclass(frozen=True)
class SegmentSolution:
    line_count: int
    lines: tuple[str, ...]
    widths: tuple[float, ...]
    breaks: tuple[int, ...]
    break_kinds: tuple[str, ...]
    score: dict[str, float | int]


def load_audit_module():
    spec = importlib.util.spec_from_file_location("audit_briefing_layout", AUDIT_PATH)
    if spec is None or spec.loader is None:
        raise ReflowFailure(f"cannot load audit module: {AUDIT_PATH}")
    module = importlib.util.module_from_spec(spec)
    sys.modules[spec.name] = module
    spec.loader.exec_module(module)
    return module


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--root", type=Path, default=ROOT)
    parser.add_argument("--apply", action="store_true", help="write successful reflows into mapping JSON")
    parser.add_argument(
        "--json-output",
        type=Path,
        default=None,
        help="default: <root>/build/translation/briefing_reflow_dryrun.json",
    )
    parser.add_argument(
        "--markdown-output",
        type=Path,
        default=None,
        help="default: <root>/build/translation/briefing_reflow_dryrun.md",
    )
    return parser.parse_args()


def remove_newlines(text: str) -> str:
    return text.replace("\r", "").replace("\n", "")


def split_preserving_forced_breaks(text: str) -> tuple[list[str], int]:
    normalized = text.replace("\r\n", "\n").replace("\r", "\n")
    trailing = len(normalized) - len(normalized.rstrip("\n"))
    core = normalized[:-trailing] if trailing else normalized
    return core.split("\n"), trailing


def visible_for_token(token: str) -> str:
    if token.startswith("<R=") and token.endswith(">"):
        body = token[3:-1]
        return body.split(",", 1)[0] if "," in body else ""
    return ""


def tokenize(segment: str, audit: Any) -> list[Unit]:
    units: list[Unit] = []
    for match in WORD_OR_TOKEN_RE.finditer(segment):
        token = match.group(0)
        visible = visible_for_token(token) if token.startswith("<") else token
        units.append(Unit(token, audit.visual_width(token), visible))
    if "".join(unit.text for unit in units) != segment:
        raise ReflowFailure("internal tokenizer did not cover source segment exactly")
    return units


def first_visible(units: list[Unit], start: int) -> str:
    for unit in units[start:]:
        if unit.visible:
            return unit.visible[0]
    return ""


def last_visible(units: list[Unit], end: int) -> str:
    for unit in reversed(units[:end]):
        if unit.visible:
            return unit.visible[-1]
    return ""


def break_kind(units: list[Unit], boundary: int) -> str:
    char = last_visible(units, boundary)
    if char in "。！？":
        return "sentence"
    if char == "；":
        return "semicolon"
    if char in "，：":
        return "comma_or_colon"
    if char == "、":
        return "enumeration"
    return "other"


def legal_break(units: list[Unit], boundary: int) -> bool:
    if boundary <= 0 or boundary >= len(units):
        return False
    before = last_visible(units, boundary)
    after = first_visible(units, boundary)
    if not before or not after:
        return True
    if before.isspace() or after.isspace():
        return False
    if after in CLOSING_CHARS:
        return False
    if before in OPENING_CHARS:
        return False
    return True


def line_score(widths: list[float], break_kinds: list[str], limit: float) -> dict[str, float | int]:
    line_count = len(widths)
    target = sum(widths) / line_count if line_count else 0.0
    balance = sum(abs(width - target) for width in widths) / max(limit, 1.0)
    tail_shortage = max(0.0, (0.45 * limit - widths[-1]) / max(limit, 1.0)) if widths else 0.0
    natural_penalty = sum(BREAK_PENALTY[kind] for kind in break_kinds)
    total = natural_penalty * 1000.0 + balance * 10.0 + tail_shortage * 100.0
    return {
        "total": round(total, 6),
        "natural_break_penalty": natural_penalty,
        "balance_penalty": round(balance, 6),
        "short_tail_penalty": round(tail_shortage, 6),
    }


def solve_segment(segment: str, limit: float, max_lines: int, audit: Any) -> dict[int, SegmentSolution]:
    units = tokenize(segment, audit)
    if not units:
        return {1: SegmentSolution(1, ("",), (0.0,), (), (), line_score([0.0], [], limit))}
    prefix = [0.0]
    for unit in units:
        prefix.append(round(prefix[-1] + unit.width, 6))
    if any(unit.width > limit for unit in units):
        return {}

    solutions: dict[int, SegmentSolution] = {}
    for wanted_lines in range(1, max_lines + 1):
        target = prefix[-1] / wanted_lines
        # state[(end, line_count)] = (score tuple, line ends, break kinds, widths)
        states: dict[tuple[int, int], tuple[tuple[Any, ...], tuple[int, ...], tuple[str, ...], tuple[float, ...]]] = {
            (0, 0): ((0, 0.0, 0.0, ()), (), (), ())
        }
        for line_count in range(wanted_lines):
            current = [entry for (end, count), entry in states.items() if count == line_count]
            for (start, count), entry in [
                ((end, count), value)
                for (end, count), value in states.items()
                if count == line_count
            ]:
                _, ends, kinds, widths = entry
                for boundary in range(start + 1, len(units) + 1):
                    width = round(prefix[boundary] - prefix[start], 6)
                    if width > limit + 1e-9:
                        break
                    is_final = boundary == len(units)
                    if is_final and line_count + 1 != wanted_lines:
                        continue
                    if not is_final and line_count + 1 >= wanted_lines:
                        continue
                    if not is_final and not legal_break(units, boundary):
                        continue
                    kind = "" if is_final else break_kind(units, boundary)
                    new_ends = ends + (boundary,)
                    new_kinds = kinds + (() if is_final else (kind,))
                    new_widths = widths + (width,)
                    natural = sum(BREAK_PENALTY[item] for item in new_kinds)
                    balance = sum(abs(item - target) for item in new_widths)
                    short_tail = (
                        max(0.0, 0.45 * limit - new_widths[-1])
                        if is_final
                        else 0.0
                    )
                    key = (natural, round(balance, 6), round(short_tail, 6), new_ends)
                    old = states.get((boundary, line_count + 1))
                    if old is None or key < old[0]:
                        states[(boundary, line_count + 1)] = (key, new_ends, new_kinds, new_widths)
        result = states.get((len(units), wanted_lines))
        if result is not None:
            _, ends, kinds, widths = result
            starts = (0,) + ends[:-1]
            lines = tuple("".join(unit.text for unit in units[start:end]) for start, end in zip(starts, ends))
            score = line_score(list(widths), list(kinds), limit)
            solutions[wanted_lines] = SegmentSolution(wanted_lines, lines, widths, ends[:-1], kinds, score)
    return solutions


def choose_row_reflow(text: str, limit: float, max_lines: int, audit: Any) -> dict[str, Any]:
    segments, trailing = split_preserving_forced_breaks(text)
    segment_options = [solve_segment(segment, limit, max_lines, audit) for segment in segments]
    if any(not options for options in segment_options):
        return {
            "success": False,
            "suggested_cn": text,
            "reason": "one or more forced segments contain an atomic unit wider than the limit or have no legal break path",
            "score": None,
            "breaks": [],
            "lines": audit.normalized_lines(text),
        }

    # Allocate the smallest total number of lines first; quality then chooses
    # natural, balanced solutions without deleting existing forced breaks.
    states: dict[int, tuple[tuple[Any, ...], tuple[SegmentSolution, ...]]] = {0: ((), ())}
    for options in segment_options:
        next_states: dict[int, tuple[tuple[Any, ...], tuple[SegmentSolution, ...]]] = {}
        for used, (old_key, old_solutions) in states.items():
            for count, solution in options.items():
                total = used + count
                if total > max_lines:
                    continue
                score = solution.score
                key = old_key + (
                    score["natural_break_penalty"],
                    score["balance_penalty"],
                    score["short_tail_penalty"],
                    tuple(solution.breaks),
                )
                old = next_states.get(total)
                if old is None or key < old[0]:
                    next_states[total] = (key, old_solutions + (solution,))
        states = next_states
    if not states:
        minimum_possible = sum(min(options) for options in segment_options)
        return {
            "success": False,
            "suggested_cn": text,
            "reason": f"minimum legal line count {minimum_possible} exceeds hard ceiling {max_lines}",
            "score": None,
            "breaks": [],
            "lines": audit.normalized_lines(text),
        }

    total_lines = min(states)
    _, selected = states[total_lines]
    output_lines: list[str] = []
    break_records: list[dict[str, Any]] = []
    source_cursor = 0
    for segment_index, (segment, solution) in enumerate(zip(segments, selected)):
        output_lines.extend(solution.lines)
        for break_index, offset in enumerate(solution.breaks):
            break_records.append(
                {
                    "segment_index": segment_index,
                    "original_offset": source_cursor + offset,
                    "line_after_index": len(output_lines) - len(solution.lines) + break_index,
                    "break_kind": solution.break_kinds[break_index],
                    "break_after": solution.lines[break_index][-1:] if solution.lines[break_index] else "",
                }
            )
        source_cursor += len(segment) + 1
    suggested = "\n".join(output_lines) + ("\n" * trailing)
    widths = [round(audit.visual_width(line), 3) for line in audit.normalized_lines(suggested)]
    break_kinds = [item["break_kind"] for item in break_records]
    score = line_score(widths, break_kinds, limit)
    return {
        "success": max(widths, default=0.0) <= limit + 1e-9 and len(widths) <= max_lines,
        "suggested_cn": suggested,
        "reason": "legal reflow found within family width and hard line ceiling",
        "score": score,
        "breaks": break_records,
        "lines": audit.normalized_lines(suggested),
    }


def current_mapping_value_position(raw: str, unique_index: int, expected_cn: str) -> tuple[int, int, str]:
    match = JSON_KEY_RE.search(raw)
    if match is None:
        raise ReflowFailure("mapping has no translations array")
    decoder = json.JSONDecoder()
    position = match.end()
    while position < len(raw) and raw[position].isspace():
        position += 1
    if position >= len(raw) or raw[position] != "[":
        raise ReflowFailure("mapping translations value is not an array")
    position += 1
    while position < len(raw):
        while position < len(raw) and raw[position].isspace():
            position += 1
        if position < len(raw) and raw[position] == "]":
            break
        item_start = position
        item, item_end = decoder.raw_decode(raw, position)
        if not isinstance(item, dict):
            raise ReflowFailure("mapping translation item is not an object")
        if int(item.get("unique_index", -1)) == unique_index:
            item_raw = raw[item_start:item_end]
            cn_match = re.search(r'"cn_text"\s*:\s*', item_raw)
            if cn_match is None:
                raise ReflowFailure(f"mapping row {unique_index} has no cn_text")
            value_start = item_start + cn_match.end()
            while raw[value_start].isspace():
                value_start += 1
            old_value, value_end = decoder.raw_decode(raw, value_start)
            if old_value != expected_cn:
                raise ReflowFailure(f"mapping row {unique_index} cn_text changed during audit")
            return value_start, value_end, old_value
        position = item_end
        while position < len(raw) and raw[position].isspace():
            position += 1
        if position < len(raw) and raw[position] == ",":
            position += 1
    raise ReflowFailure(f"mapping row {unique_index} not found")


def patch_mapping_file(path: Path, updates: dict[int, str], expected: dict[int, str]) -> None:
    with path.open("r", encoding="utf-8", newline="") as handle:
        raw = handle.read()
    replacements: list[tuple[int, int, str]] = []
    for index, new_value in updates.items():
        start, end, old_value = current_mapping_value_position(raw, index, expected[index])
        if remove_newlines(old_value) != remove_newlines(new_value):
            raise ReflowFailure(f"{path.name}#{index}: reflow would change non-newline text")
        encoded = json.dumps(new_value, ensure_ascii=False, separators=(",", ":"))
        replacements.append((start, end, encoded))
    patched = raw
    for start, end, replacement in sorted(replacements, reverse=True):
        patched = patched[:start] + replacement + patched[end:]
    before = json.loads(raw)
    after = json.loads(patched)
    before_compare = copy.deepcopy(before)
    after_compare = copy.deepcopy(after)
    for item in before_compare.get("translations", []):
        item["cn_text"] = remove_newlines(item.get("cn_text", ""))
    for item in after_compare.get("translations", []):
        item["cn_text"] = remove_newlines(item.get("cn_text", ""))
    if before_compare != after_compare:
        raise ReflowFailure(f"{path.name}: patch changed a non-cn or non-newline field")
    with path.open("w", encoding="utf-8", newline="") as handle:
        handle.write(patched)


def md_text(value: str) -> str:
    return value.replace("`", "\\`").replace("|", "\\|").replace("\r", "\\r").replace("\n", "\\n")


def render_markdown(report: dict[str, Any]) -> str:
    lines = [
        "# BRIEFING Reflow Dry-Run / Apply Report",
        "",
        f"mode: `{report['mode']}`",
        "",
        "本工具只允许在 `cn_text` 中插入或调整 LF；没有缩写、改写、删除或增加任何译文文字。控制 token、placeholder、连续英文和连续数字均作为不可拆分单元。",
        "",
        "## Audit definition check",
        "",
        f"- existing audit max-line statistics match freshly loaded JPN rows: `{report['audit_definition_check']['pass']}`",
        f"- FILES hard ceiling: `{report['profiles']['FILES']['hard_line_ceiling']}` lines",
        f"- MISSION hard ceiling: `{report['profiles']['MISSION']['hard_line_ceiling']}` lines",
        "",
        "## Score strategy",
        "",
        "先最小化总行数；同样行数下，断点惩罚依次为句末 0、分号 1、逗号/冒号 2、顿号 3、普通字符 8。随后最小化各行相对平均宽度的偏差，并惩罚低于安全宽度 45% 的尾行。所有候选行必须不超过 profile limit。",
        "",
    ]
    for family in ("FILES", "MISSION"):
        profile = report["profiles"][family]
        lines += [
            f"## {family}",
            "",
            "| metric | value |",
            "|---|---:|",
        ]
        for key in (
            "blocks",
            "rows",
            "width_limit",
            "hard_line_ceiling",
            "original_overflow_rows",
            "successful_reflows",
            "remaining_overflow_rows",
            "needs_rewrite",
            "changed_mapping_rows",
        ):
            lines.append(f"| `{key}` | `{profile[key]}` |")
        lines += ["", "### Remaining NEEDS_REWRITE", ""]
        remaining = profile["needs_rewrite_items"]
        if not remaining:
            lines.append("None.")
        else:
            lines += ["| file_id | unique_index | width before | line count before | reason | CN |", "|---|---:|---:|---:|---|---|"]
            for item in remaining:
                lines.append(
                    f"| `{item['file_id']}` | {item['unique_index']} | {item['width_before']:.3f} | {item['line_count_before']} | `{item['reason']}` | `{md_text(item['current_cn'])}` |"
                )
        lines += ["", f"### {family} reflow results", ""]
        results = profile["items"]
        if results:
            lines += [
                "| file_id | unique_index | status | before | after max | after lines | overflow solved | chosen breaks | suggested CN |",
                "|---|---:|---|---:|---:|---:|---|---|---|",
            ]
            for item in results:
                lines.append(
                    f"| `{item['file_id']}` | {item['unique_index']} | `{item['status']}` | {item['width_before']:.3f} | {item['width_after_max']:.3f} | {item['line_count_after']} | {item['overflow_solved']} | `{md_text(json.dumps(item['breaks'], ensure_ascii=False, separators=(',', ':')))}` | `{md_text(item['suggested_cn'])}` |"
                )
        else:
            lines.append("No original overflow rows.")
        lines += ["", f"### {family} post-reflow widest Top 50", ""]
        lines += ["| rank | file_id | unique_index | line_index | width | line | suggested CN |", "|---:|---|---:|---:|---:|---|---|"]
        for item in profile["post_reflow_widest_top50"]:
            lines.append(
                f"| {item['rank']} | `{item['file_id']}` | {item['unique_index']} | {item['line_index']} | {item['width']:.3f} | `{md_text(item['display_line'])}` | `{md_text(item['suggested_cn'])}` |"
            )
        lines.append("")
    return "\n".join(lines).rstrip() + "\n"


def main() -> int:
    args = parse_args()
    root = args.root.resolve()
    audit = load_audit_module()
    rows, input_meta = audit.load_rows(root)
    fresh_files = audit.family_audit(rows, "FILES")
    fresh_mission = audit.family_audit(rows, "MISSION")
    if not AUDIT_REPORT_PATH.is_file():
        raise ReflowFailure(f"existing audit report not found: {AUDIT_REPORT_PATH}")
    existing = json.loads(AUDIT_REPORT_PATH.read_text(encoding="utf-8"))
    definition_checks = {
        "FILES": {
            "blocks": existing["files"]["blocks"] == fresh_files["blocks"],
            "rows": existing["files"]["rows"] == fresh_files["rows"],
            "jpn_max_display_lines_per_row": existing["files"]["jpn_max_display_lines_per_row"] == fresh_files["jpn_max_display_lines_per_row"],
        },
        "MISSION": {
            "blocks": existing["mission"]["blocks"] == fresh_mission["blocks"],
            "rows": existing["mission"]["rows"] == fresh_mission["rows"],
            "jpn_max_display_lines_per_row": existing["mission"]["jpn_max_display_lines_per_row"] == fresh_mission["jpn_max_display_lines_per_row"],
        },
    }
    if not all(value for family in definition_checks.values() for value in family.values()):
        raise ReflowFailure(f"existing audit/JPN ceiling definition mismatch: {definition_checks}")

    row_results: dict[str, list[dict[str, Any]]] = {"FILES": [], "MISSION": []}
    limits = {"FILES": fresh_files["jpn_max_line_width"], "MISSION": fresh_mission["jpn_max_line_width"]}
    ceilings = {"FILES": fresh_files["jpn_max_display_lines_per_row"], "MISSION": fresh_mission["jpn_max_display_lines_per_row"]}
    mapping_expected: dict[str, dict[int, str]] = {}
    for row in rows:
        mapping_expected.setdefault(row.file_id, {})[row.unique_index] = row.cn_text
        current_lines = audit.line_records(row.cn_text)
        width_before = max((line["width"] for line in current_lines), default=0.0)
        if width_before <= limits[row.family] + 1e-9:
            continue
        result = choose_row_reflow(row.cn_text, limits[row.family], ceilings[row.family], audit)
        after_lines = audit.line_records(result["suggested_cn"])
        width_after_max = max((line["width"] for line in after_lines), default=0.0)
        line_count_after = len(after_lines)
        success = bool(result["success"] and width_after_max <= limits[row.family] + 1e-9 and line_count_after <= ceilings[row.family])
        if not success:
            status = "NEEDS_REWRITE"
            suggested = row.cn_text
            reason = result["reason"]
            overflow_solved = False
        else:
            status = "REFLOW_SUCCESS"
            suggested = result["suggested_cn"]
            reason = result["reason"]
            overflow_solved = True
        if remove_newlines(row.cn_text) != remove_newlines(suggested):
            raise ReflowFailure(f"{row.file_id}#{row.unique_index}: non-newline text changed")
        row_results[row.family].append(
            {
                "resource_type": row.family,
                "file_id": row.file_id,
                "unique_index": row.unique_index,
                "jpn_text": row.jpn_text,
                "jpn_display_lines": audit.normalized_lines(row.jpn_text),
                "current_cn": row.cn_text,
                "suggested_cn": suggested,
                "width_before": width_before,
                "width_after": [line["width"] for line in after_lines],
                "width_after_max": width_after_max,
                "line_count_before": len(current_lines),
                "line_count_after": line_count_after if success else len(current_lines),
                "chosen_breaks": result["breaks"] if success else [],
                "breaks": result["breaks"] if success else [],
                "overflow_solved": overflow_solved,
                "status": status,
                "reason": reason,
                "score": result["score"],
                "needs_manual": not success,
            }
        )

    profiles: dict[str, dict[str, Any]] = {}
    for family, fresh in (("FILES", fresh_files), ("MISSION", fresh_mission)):
        items = row_results[family]
        successes = [item for item in items if item["status"] == "REFLOW_SUCCESS"]
        needs = [item for item in items if item["status"] == "NEEDS_REWRITE"]
        post_lines: list[dict[str, Any]] = []
        for row in rows:
            if row.family != family:
                continue
            item = next((candidate for candidate in items if candidate["file_id"] == row.file_id and candidate["unique_index"] == row.unique_index), None)
            text = item["suggested_cn"] if item else row.cn_text
            for line in audit.line_records(text):
                post_lines.append({
                    "file_id": row.file_id,
                    "unique_index": row.unique_index,
                    "line_index": line["line_index"],
                    "width": line["width"],
                    "display_line": line["display_line"],
                    "suggested_cn": text,
                })
        post_lines.sort(key=lambda value: (-value["width"], value["file_id"], value["unique_index"], value["line_index"]))
        for rank, item in enumerate(post_lines[:50], 1):
            item["rank"] = rank
        profiles[family] = {
            "blocks": fresh["blocks"],
            "rows": fresh["rows"],
            "width_limit": fresh["jpn_max_line_width"],
            "hard_line_ceiling": fresh["jpn_max_display_lines_per_row"],
            "original_overflow_rows": len(items),
            "successful_reflows": len(successes),
            "remaining_overflow_rows": len(needs),
            "needs_rewrite": len(needs),
            "changed_mapping_rows": sum(item["suggested_cn"] != item["current_cn"] for item in successes),
            "needs_rewrite_items": needs,
            "items": items,
            "post_reflow_widest_top50": post_lines[:50],
        }

    report = {
        "status": "PASS" if not any(profile["needs_rewrite"] for profile in profiles.values()) else "NEEDS_REWRITE_PRESENT",
        "mode": "APPLY" if args.apply else "DRY_RUN",
        "scope": "current BRIEFING mapping CN overflow rows only",
        "newline_representation": "parsed cn_text uses LF; JSON stores it as escaped \\n",
        "audit_definition_check": {
            "pass": all(value for family in definition_checks.values() for value in family.values()),
            "details": definition_checks,
        },
        "inputs_meta": input_meta,
        "profiles": profiles,
        "summary": {
            "original_overflow_total": sum(profile["original_overflow_rows"] for profile in profiles.values()),
            "successful_reflows_total": sum(profile["successful_reflows"] for profile in profiles.values()),
            "remaining_overflow_total": sum(profile["remaining_overflow_rows"] for profile in profiles.values()),
            "needs_rewrite_total": sum(profile["needs_rewrite"] for profile in profiles.values()),
            "changed_mapping_rows_total": sum(profile["changed_mapping_rows"] for profile in profiles.values()),
            "non_newline_text_changes": False,
        },
        "score_strategy": {
            "line_count": "minimize total display lines first",
            "break_preference_penalty": BREAK_PENALTY,
            "balance": "sum absolute deviation from per-solution average width, normalized by family limit",
            "short_tail": "penalty for final line below 45% of family limit",
            "hard_constraints": ["each line <= family JPN max width", "total lines <= family JPN max lines", "legal token/word/digit boundaries"],
        },
        "apply": {
            "requested": args.apply,
            "mapping_files_to_change": sorted({item["file_id"] for profile in profiles.values() for item in profile["items"] if item["status"] == "REFLOW_SUCCESS"}),
            "production_csv_written": False,
            "layout_audit_rerun": False,
        },
    }

    json_path = (args.json_output or root / "build" / "translation" / "briefing_reflow_dryrun.json").resolve()
    md_path = (args.markdown_output or root / "build" / "translation" / "briefing_reflow_dryrun.md").resolve()
    json_path.parent.mkdir(parents=True, exist_ok=True)
    md_path.parent.mkdir(parents=True, exist_ok=True)
    json_path.write_text(json.dumps(report, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    md_path.write_text(render_markdown(report), encoding="utf-8")

    if args.apply:
        if report["summary"]["needs_rewrite_total"]:
            print("WARNING: NEEDS_REWRITE rows remain; successful rows only will be applied.")
        by_file: dict[str, dict[int, str]] = {}
        for family in profiles.values():
            for item in family["items"]:
                if item["status"] == "REFLOW_SUCCESS" and item["suggested_cn"] != item["current_cn"]:
                    by_file.setdefault(item["file_id"], {})[item["unique_index"]] = item["suggested_cn"]
        for file_id, updates in by_file.items():
            path = root / MAPPING_ROOT_REL / f"{file_id}.json"
            patch_mapping_file(path, updates, mapping_expected[file_id])
        report["apply"]["mapping_files_written"] = len(by_file)
        report["apply"]["mapping_rows_written"] = sum(len(value) for value in by_file.values())
        report["apply"]["mapping_write_non_newline_changes"] = False
        json_path.write_text(json.dumps(report, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
        md_path.write_text(render_markdown(report), encoding="utf-8")

    print(f"MODE={report['mode']}")
    for family in ("FILES", "MISSION"):
        profile = profiles[family]
        print(f"{family}_ORIGINAL_OVERFLOW={profile['original_overflow_rows']}")
        print(f"{family}_SUCCESSFUL_REFLOWS={profile['successful_reflows']}")
        print(f"{family}_NEEDS_REWRITE={profile['needs_rewrite']}")
        print(f"{family}_CHANGED_MAPPING_ROWS={profile['changed_mapping_rows']}")
    print(f"TOTAL_NON_NEWLINE_TEXT_CHANGES={report['summary']['non_newline_text_changes']}")
    print(f"JSON_OUTPUT={json_path}")
    print(f"MARKDOWN_OUTPUT={md_path}")
    return 0


if __name__ == "__main__":
    try:
        raise SystemExit(main())
    except (ReflowFailure, OSError, ValueError, json.JSONDecodeError) as error:
        print(f"ERROR: {error}", file=sys.stderr)
        raise SystemExit(1)
