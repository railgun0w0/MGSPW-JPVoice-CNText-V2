#!/usr/bin/env python3
"""Apply a reviewed YPK/GTT capacity fix to the authoritative mapping."""

from __future__ import annotations

import argparse
import csv
import importlib.util
import json
import re
import sys
from pathlib import Path


SEGMENT_RE = re.compile(r"(?ms)^segment (\d+): (.*?)(?=^segment \d+: |\Z)")
ANGLE_RE = re.compile(r"<[^<>]*>")


def load_module(path: Path):
    spec = importlib.util.spec_from_file_location("ruby_canonical_helpers", path)
    if spec is None or spec.loader is None:
        raise RuntimeError(f"cannot load helper: {path}")
    module = importlib.util.module_from_spec(spec)
    sys.modules[spec.name] = module
    spec.loader.exec_module(module)
    return module


def read_csv(path: Path) -> list[dict[str, str]]:
    with path.open("r", encoding="utf-8-sig", newline="") as handle:
        return list(csv.DictReader(handle))


def segments(value: str, label: str) -> list[str]:
    matches = list(SEGMENT_RE.finditer(value))
    if not matches or [int(match.group(1)) for match in matches] != list(range(len(matches))):
        raise RuntimeError(f"{label}: invalid segment display format")
    values = []
    for match in matches:
        value = match.group(2)
        if value.endswith("\n"):
            value = value[:-1]
        if value.endswith("\r"):
            value = value[:-1]
        values.append(value)
    return values


def control_signature(value: str) -> list[str]:
    return ANGLE_RE.findall(value)


def parse_args() -> argparse.Namespace:
    root = Path(__file__).resolve().parents[1]
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--csv",
        type=Path,
        default=Path(r"C:\Users\railgun0w0\Downloads\gtt_hard_overflow_details_fixed.csv"),
    )
    parser.add_argument(
        "--mapping",
        type=Path,
        default=root / "work" / "luna_translation_templates" / "sol_translation_mappings" / "YPK_GTT" / "1C79F2AD.json",
    )
    parser.add_argument(
        "--template",
        type=Path,
        default=root / "work" / "luna_translation_templates" / "YPK_GTT" / "1C79F2AD.csv",
    )
    parser.add_argument("--write", action="store_true")
    return parser.parse_args()


def main() -> int:
    args = parse_args()
    rows = read_csv(args.csv)
    if len(rows) != 4 or {row.get("file_id", "").upper() for row in rows} != {"1C79F2AD"}:
        raise RuntimeError("expected exactly four 1C79F2AD fix rows")

    template_rows = read_csv(args.template)
    template_by_jpn: dict[str, list[dict[str, str]]] = {}
    for row in template_rows:
        template_by_jpn.setdefault(row.get("jpn_text", ""), []).append(row)

    data = json.loads(args.mapping.read_text(encoding="utf-8-sig"))
    mapping_rows = {
        int(row["unique_index"]): row
        for row in data.get("translations", [])
        if isinstance(row, dict) and "unique_index" in row
    }
    updates: dict[int, str] = {}
    for row in rows:
        jpn_values = segments(row["jpn_text"], f"record {row['record_index']} JPN")
        old_values = segments(row["original_cn"], f"record {row['record_index']} original CN")
        new_values = segments(row["current_cn"], f"record {row['record_index']} fixed CN")
        if not (len(jpn_values) == len(old_values) == len(new_values)):
            raise RuntimeError(f"record {row['record_index']}: segment count differs")
        for jpn, old, new in zip(jpn_values, old_values, new_values):
            candidates = template_by_jpn.get(jpn, [])
            indices = {int(item["unique_index"]) for item in candidates}
            if len(indices) != 1:
                raise RuntimeError(f"{jpn!r}: expected one template unique_index, found {sorted(indices)}")
            index = next(iter(indices))
            mapping = mapping_rows.get(index)
            if mapping is None or mapping.get("cn_text") != old:
                raise RuntimeError(f"unique_index {index}: supplied original CN does not match mapping")
            if control_signature(old) != control_signature(new):
                raise RuntimeError(f"unique_index {index}: control/markup signature changed")
            if index in updates and updates[index] != new:
                raise RuntimeError(f"unique_index {index}: conflicting reviewed fixes")
            updates[index] = new

    print(f"TARGET_UNIQUE_INDICES={','.join(map(str, sorted(updates)))}")
    print(f"TARGET_SEGMENT_UPDATES={len(updates)}")
    if not args.write:
        print("MODE=CHECK")
        return 0

    helper = load_module(Path(__file__).with_name("Apply-RubyCanonical.py"))
    raw = args.mapping.read_text(encoding="utf-8")
    bom = raw.startswith("\ufeff")
    body = raw[1:] if bom else raw
    spans = helper.json_mapping_row_spans(body)
    for index in updates:
        if index not in spans:
            raise RuntimeError(f"mapping span missing for unique_index {index}")
    for index, new in sorted(updates.items(), reverse=True):
        start, end, old = spans[index]
        if old != mapping_rows[index]["cn_text"]:
            raise RuntimeError(f"mapping changed before write at unique_index {index}")
        body = body[:start] + json.dumps(new, ensure_ascii=False) + body[end:]
    args.mapping.write_bytes((("\ufeff" if bom else "") + body).encode("utf-8"))
    print("MODE=WRITE")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
