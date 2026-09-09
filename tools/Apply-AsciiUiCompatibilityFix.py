#!/usr/bin/env python3
"""Preserve readable JPN ASCII for UI labels unsupported by Japanese UI fonts."""

from __future__ import annotations

import argparse
import csv
import json
import re
import subprocess
from collections import Counter, defaultdict
from pathlib import Path


KEPT_ASCII_ACTIONS = {
    "KEPT_OR_REWORDED_ASCII",
    "KEPT_ASCII_AUX_UNCHANGED",
}
NO_REFERENCE_ACTION = "NO_RELIABLE_MLG_CN_REFERENCE"
ANGLE_RE = re.compile(r"<[^<>]*>")
DOLLAR_RE = re.compile(r"\$[A-Za-z0-9_]+")
PRINTF_RE = re.compile(r"%(?:\d+\$)?[sdif]")


def parse_args() -> argparse.Namespace:
    root = Path(__file__).resolve().parents[1]
    default_repo = (
        root.parent
        / "JPVoice_CNText_Experimental"
        / ".upload_staging_mgspw_v2_20260906_push"
    )
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--audit-csv",
        type=Path,
        default=root / "build" / "ui_font_audit" / "ascii_source_translated_to_chinese.csv",
    )
    parser.add_argument("--translation-repo", type=Path, default=default_repo)
    parser.add_argument(
        "--mapping-commit",
        default="",
        help="update touched shard-manifest entries to this committed mapping revision",
    )
    return parser.parse_args()


def all_tokens(text: str) -> list[str]:
    spans: list[tuple[int, str]] = []
    for pattern in (ANGLE_RE, DOLLAR_RE, PRINTF_RE):
        spans.extend((match.start(), match.group(0)) for match in pattern.finditer(text))
    return [token for _, token in sorted(spans)]


def read_targets(path: Path) -> dict[tuple[str, str], dict[int, dict[str, str]]]:
    targets: dict[tuple[str, str], dict[int, dict[str, str]]] = defaultdict(dict)
    with path.open("r", encoding="utf-8-sig", newline="") as handle:
        for row in csv.DictReader(handle):
            retained = (
                row.get("risk_priority") == "HIGH"
                and row.get("mlg_cn_patch_action") in KEPT_ASCII_ACTIONS
            )
            no_reference = row.get("mlg_cn_patch_action") == NO_REFERENCE_ACTION
            if not retained and not no_reference:
                continue
            key = (row["resource_class"], row["file_id"])
            index = int(row["unique_index"])
            if index in targets[key]:
                raise RuntimeError(f"duplicate audit target {key}/{index}")
            targets[key][index] = row
    return targets


def mapping_paths(
    template_root: Path, mapping_root: Path, resource_class: str, file_id: str
) -> tuple[list[Path], Path | None]:
    directory = mapping_root / resource_class
    manifest_path = directory / f"{file_id}.manifest.json"
    if manifest_path.is_file():
        manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
        paths = [template_root / part["path"] for part in manifest.get("parts", [])]
        if not paths or any(not path.is_file() for path in paths):
            raise RuntimeError(f"invalid shard manifest {manifest_path}")
        return paths, manifest_path
    flat_path = directory / f"{file_id}.json"
    if not flat_path.is_file():
        raise RuntimeError(f"missing mapping for {resource_class}/{file_id}")
    flat_document = json.loads(flat_path.read_text(encoding="utf-8"))
    if flat_document.get("sharded") is True:
        paths = [directory / shard["path"] for shard in flat_document.get("shards", [])]
        if not paths or any(not path.is_file() for path in paths):
            raise RuntimeError(f"invalid legacy shard index {flat_path}")
        return paths, None
    return [flat_path], None


def serialize_like_head(repo: Path, path: Path, document: object) -> str:
    relative = path.resolve().relative_to(repo.resolve()).as_posix()
    try:
        head_text = subprocess.check_output(
            ["git", "show", f"HEAD:{relative}"],
            cwd=repo,
            text=True,
            encoding="utf-8",
        )
    except subprocess.CalledProcessError:
        head_text = ""
    if head_text.startswith("{\n") or head_text.startswith("{\r\n"):
        return json.dumps(document, ensure_ascii=False, indent=2) + "\n"
    return json.dumps(document, ensure_ascii=False, separators=(",", ":")) + "\n"


def head_text(repo: Path, path: Path) -> str:
    relative = path.resolve().relative_to(repo.resolve()).as_posix()
    return subprocess.check_output(
        ["git", "show", f"HEAD:{relative}"],
        cwd=repo,
        text=True,
        encoding="utf-8",
    )


def skip_space(text: str, position: int) -> int:
    while position < len(text) and text[position].isspace():
        position += 1
    return position


def json_value_end(text: str, position: int) -> int:
    position = skip_space(text, position)
    if text[position] == '"':
        position += 1
        while position < len(text):
            if text[position] == "\\":
                position += 2
            elif text[position] == '"':
                return position + 1
            else:
                position += 1
        raise RuntimeError("unterminated JSON string")
    if text[position] in "[{":
        opening = text[position]
        closing = "]" if opening == "[" else "}"
        depth = 1
        position += 1
        in_string = False
        while position < len(text):
            char = text[position]
            if in_string:
                if char == "\\":
                    position += 2
                    continue
                if char == '"':
                    in_string = False
            else:
                if char == '"':
                    in_string = True
                elif char == opening:
                    depth += 1
                elif char == closing:
                    depth -= 1
                    if depth == 0:
                        return position + 1
            position += 1
        raise RuntimeError("unterminated JSON container")
    end = position
    while end < len(text) and text[end] not in ",]}":
        end += 1
    return end


def array_value_spans(text: str, opening: int) -> list[tuple[int, int]]:
    if text[opening] != "[":
        raise RuntimeError("array opening not found")
    result: list[tuple[int, int]] = []
    position = opening + 1
    while True:
        position = skip_space(text, position)
        if text[position] == "]":
            return result
        start = position
        end = json_value_end(text, position)
        result.append((start, end))
        position = skip_space(text, end)
        if text[position] == ",":
            position += 1
            continue
        if text[position] == "]":
            return result
        raise RuntimeError(f"unexpected array separator at {position}")


def object_value_spans(text: str, opening: int) -> dict[str, tuple[int, int]]:
    if text[opening] != "{":
        raise RuntimeError("object opening not found")
    result: dict[str, tuple[int, int]] = {}
    position = opening + 1
    while True:
        position = skip_space(text, position)
        if text[position] == "}":
            return result
        key_start = position
        key_end = json_value_end(text, key_start)
        key = json.loads(text[key_start:key_end])
        position = skip_space(text, key_end)
        if text[position] != ":":
            raise RuntimeError(f"missing object colon at {position}")
        value_start = skip_space(text, position + 1)
        value_end = json_value_end(text, value_start)
        result[str(key)] = (value_start, value_end)
        position = skip_space(text, value_end)
        if text[position] == ",":
            position += 1
            continue
        if text[position] == "}":
            return result
        raise RuntimeError(f"unexpected object separator at {position}")


def replace_spans(text: str, replacements: list[tuple[int, int, str]]) -> str:
    for start, end, replacement in sorted(replacements, reverse=True):
        text = text[:start] + replacement + text[end:]
    return text


def update_mapping_file(
    repo: Path, path: Path, targets: dict[int, dict[str, str]]
) -> set[int]:
    original_text = head_text(repo, path)
    translations_match = re.search(r'"translations"\s*:', original_text)
    if translations_match is None:
        raise RuntimeError(f"translations array missing: {path}")
    translations_opening = skip_space(original_text, translations_match.end())
    row_spans = array_value_spans(original_text, translations_opening)
    seen: set[int] = set()
    row_replacements: list[tuple[int, int, str]] = []
    for row_start, row_end in row_spans:
        row_text = original_text[row_start:row_end]
        item = json.loads(row_text)
        compact = isinstance(item, list)
        if compact:
            if len(item) < 2:
                raise RuntimeError(f"invalid compact translation row: {path}: {item!r}")
            index = int(item[0])
            current_text = item[1]
        elif isinstance(item, dict):
            index = int(item["unique_index"])
            current_text = item.get("cn_text")
        else:
            raise RuntimeError(f"unsupported translation row: {path}: {item!r}")
        target = targets.get(index)
        if target is None:
            continue
        jpn_text = target["jpn_text"]
        audit_cn_text = target["cn_text"]
        if current_text not in {audit_cn_text, jpn_text}:
            raise RuntimeError(
                f"{path}: index {index} has unexpected cn_text {current_text!r}; "
                f"audit expected {audit_cn_text!r}"
            )
        if target["mlg_cn_patch_action"] == NO_REFERENCE_ACTION:
            marker = (
                "JPN_ASCII_UI_PRESERVED; NO_RELIABLE_MLG_CN_REFERENCE; "
                "USER_READABLE_ENGLISH_FALLBACK_2026-09-09"
            )
        else:
            marker = (
                "JPN_ASCII_UI_PRESERVED; MLG_CN_RETAINS_ASCII; "
                "UI_FONT_COMPATIBILITY_FIX_2026-09-09"
            )
        if compact and len(item) < 5:
            raise RuntimeError(f"compact mapping row has fewer than five fields: {path}/{index}")
        prior = str(item[4] if compact else item.get("review_flag", "")).strip()
        if marker not in prior:
            updated_flag = f"{prior}; {marker}" if prior else marker
        else:
            updated_flag = prior
        desired = {
            "cn_text": jpn_text,
            "cn_control_tokens": " | ".join(all_tokens(jpn_text)),
            "cn_utf8_bytes": len(jpn_text.encode("utf-8")),
            "review_flag": updated_flag,
        }
        field_replacements: list[tuple[int, int, str]] = []
        if compact:
            fields = array_value_spans(row_text, 0)
            for field_index, name in enumerate(
                ("unique_index", "cn_text", "cn_control_tokens", "cn_utf8_bytes", "review_flag")
            ):
                if name == "unique_index":
                    continue
                start, end = fields[field_index]
                field_replacements.append(
                    (start, end, json.dumps(desired[name], ensure_ascii=False, separators=(",", ":")))
                )
        else:
            fields = object_value_spans(row_text, 0)
            for name, value in desired.items():
                if name not in fields:
                    raise RuntimeError(f"{path}/{index}: missing {name}")
                start, end = fields[name]
                field_replacements.append(
                    (start, end, json.dumps(value, ensure_ascii=False, separators=(",", ":")))
                )
        updated_row = replace_spans(row_text, field_replacements)
        row_replacements.append((row_start, row_end, updated_row))
        seen.add(index)
    if seen:
        path.write_text(replace_spans(original_text, row_replacements), encoding="utf-8")
    elif path.read_text(encoding="utf-8") != original_text:
        # Recover only formatting-only changes left by an interrupted run of this tool.
        path.write_text(original_text, encoding="utf-8")
    return seen


def update_manifest(
    repo: Path, manifest_path: Path, touched_parts: set[Path], mapping_commit: str
) -> int:
    manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
    updated = 0
    touched_names = {path.name for path in touched_parts}
    for part in manifest.get("parts", []):
        if Path(str(part.get("path", ""))).name in touched_names:
            part["commit"] = mapping_commit
            updated += 1
    if updated != len(touched_names):
        raise RuntimeError(
            f"{manifest_path}: updated {updated} parts, expected {len(touched_names)}"
        )
    note = (
        "ASCII UI compatibility policy preserves JPN ASCII for short uppercase labels "
        "when the working MLG_CN patch retains ASCII, and for no-reference rows where "
        "the user selected readable English as the safe fallback."
    )
    notes = manifest.setdefault("notes", [])
    if note not in notes:
        notes.append(note)
    manifest_path.write_text(serialize_like_head(repo, manifest_path, manifest), encoding="utf-8")
    return updated


def main() -> int:
    args = parse_args()
    repo = args.translation_repo.resolve()
    template_root = repo / "work" / "luna_translation_templates"
    mapping_root = template_root / "sol_translation_mappings"
    targets = read_targets(args.audit_csv.resolve())
    expected_rows = sum(len(rows) for rows in targets.values())
    if expected_rows != 351:
        raise RuntimeError(f"expected 351 policy targets, found {expected_rows}")

    seen_total: set[tuple[str, str, int]] = set()
    touched_files: set[Path] = set()
    touched_manifests: dict[Path, set[Path]] = defaultdict(set)
    resource_counts: Counter[str] = Counter()

    for (resource_class, file_id), rows in sorted(targets.items()):
        paths, manifest_path = mapping_paths(
            template_root, mapping_root, resource_class, file_id
        )
        group_seen: set[int] = set()
        for path in paths:
            seen = update_mapping_file(repo, path, rows)
            if seen:
                touched_files.add(path)
                group_seen.update(seen)
                if manifest_path is not None:
                    touched_manifests[manifest_path].add(path)
        missing = set(rows) - group_seen
        extra = group_seen - set(rows)
        if missing or extra:
            raise RuntimeError(
                f"{resource_class}/{file_id}: missing={sorted(missing)}, extra={sorted(extra)}"
            )
        for index in group_seen:
            seen_total.add((resource_class, file_id, index))
            resource_counts[resource_class] += 1

    if len(seen_total) != expected_rows:
        raise RuntimeError(f"updated {len(seen_total)} rows, expected {expected_rows}")

    manifest_parts = 0
    if args.mapping_commit:
        for manifest_path, parts in sorted(touched_manifests.items()):
            manifest_parts += update_manifest(
                repo, manifest_path, parts, args.mapping_commit
            )

    print(f"FIXED_ROWS={len(seen_total)}")
    print(f"FILE_IDS={len(targets)}")
    print(f"MAPPING_FILES={len(touched_files)}")
    print(f"SHARD_MANIFESTS={len(touched_manifests)}")
    print(f"MANIFEST_PARTS_UPDATED={manifest_parts}")
    for resource_class in ("LOOSE_OLANG", "SLOT_OLANG", "STAGEDAT_OLANG"):
        print(f"{resource_class}={resource_counts[resource_class]}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
