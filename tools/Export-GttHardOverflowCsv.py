#!/usr/bin/env python3
"""Export human-readable details for current YPK/GTT HARD_OVERFLOW records."""

from __future__ import annotations

import argparse
import csv
import json
from pathlib import Path


OUTPUT_COLUMNS = [
    "resource_class",
    "file_id",
    "record_index",
    "segment_count",
    "jpn_text",
    "current_cn",
    "eng_reference",
    "mlg_cn_reference",
    "previous_record_context",
    "next_record_context",
    "header_size",
    "record_size",
    "nominal_capacity",
    "aligned_capacity",
    "current_required_bytes",
    "over_nominal_bytes",
    "over_aligned_bytes",
    "status",
    "notes",
]


def parse_args() -> argparse.Namespace:
    root = Path(__file__).resolve().parents[1]
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--issues",
        type=Path,
        default=root / "build" / "translation" / "fixed_capacity_issues.csv",
    )
    parser.add_argument(
        "--manifest",
        type=Path,
        default=root / "build" / "translation" / "compiled_translation_manifest.csv",
    )
    parser.add_argument(
        "--template",
        type=Path,
        default=root / "work" / "luna_translation_templates" / "YPK_GTT" / "1C79F2AD.csv",
    )
    parser.add_argument(
        "--output",
        type=Path,
        default=root / "build" / "translation" / "gtt_hard_overflow_details.csv",
    )
    return parser.parse_args()


def read_rows(path: Path) -> list[dict[str, str]]:
    with path.open("r", encoding="utf-8-sig", newline="") as handle:
        return list(csv.DictReader(handle))


def display_segments(values: list[str]) -> str:
    return "\n".join(f"segment {index}: {value}" for index, value in enumerate(values))


def context_for(
    records: dict[int, list[dict[str, str]]], record_index: int, direction: int
) -> str:
    neighbor = record_index + direction
    if neighbor not in records:
        return ""
    return "\n".join(
        f"record {neighbor} / segment {row['segment_index']}: "
        f"JPN={row.get('jpn_text', '')} | CN={row.get('cn_text', '')}"
        for row in records[neighbor]
    )


def references_for(template_rows: list[dict[str, str]], jpn_values: list[str]) -> tuple[str, str]:
    jpn_set = set(jpn_values)
    eng: set[str] = set()
    mlg: set[str] = set()
    for row in template_rows:
        if row.get("jpn_text", "") not in jpn_set:
            continue
        if row.get("eng_reference", ""):
            eng.add(row["eng_reference"])
        if row.get("mlg_cn_reference", ""):
            mlg.add(row["mlg_cn_reference"])
    return "\n---\n".join(sorted(eng)), "\n---\n".join(sorted(mlg))


def main() -> int:
    args = parse_args()
    issue_rows = [row for row in read_rows(args.issues) if row.get("status") == "HARD_OVERFLOW"]
    manifest_rows = [
        row
        for row in read_rows(args.manifest)
        if row.get("resource_class") == "YPK_GTT" and row.get("file_id") == "1C79F2AD"
    ]
    template_rows = read_rows(args.template)

    records: dict[int, list[dict[str, str]]] = {}
    for row in manifest_rows:
        records.setdefault(int(row["record_index"]), []).append(row)
    for rows in records.values():
        rows.sort(key=lambda row: int(row["segment_index"]))

    output: list[dict[str, str]] = []
    for issue in issue_rows:
        record_index = int(issue["record_index"])
        jpn_values = json.loads(issue["jpn_texts"])
        cn_values = json.loads(issue["cn_texts"])
        eng, mlg = references_for(template_rows, jpn_values)
        output.append(
            {
                "resource_class": issue["resource_class"],
                "file_id": issue["file_id"],
                "record_index": issue["record_index"],
                "segment_count": issue["segment_count"],
                "jpn_text": display_segments(jpn_values),
                "current_cn": display_segments(cn_values),
                "eng_reference": eng,
                "mlg_cn_reference": mlg,
                "previous_record_context": context_for(records, record_index, -1),
                "next_record_context": context_for(records, record_index, 1),
                "header_size": issue["header_size"],
                "record_size": issue["record_size"],
                "nominal_capacity": issue["nominal_capacity"],
                "aligned_capacity": issue["aligned_capacity"],
                "current_required_bytes": issue["required"],
                "over_nominal_bytes": issue["over_nominal_bytes"],
                "over_aligned_bytes": issue["over_aligned_bytes"],
                "status": issue["status"],
                "notes": "NO_REFERENCE_IN_CORPUS" if not eng and not mlg else "",
            }
        )

    args.output.parent.mkdir(parents=True, exist_ok=True)
    with args.output.open("w", encoding="utf-8-sig", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=OUTPUT_COLUMNS, lineterminator="\n")
        writer.writeheader()
        writer.writerows(output)
    print(f"ROWS={len(output)}")
    print(f"OUTPUT={args.output.resolve()}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
