from __future__ import annotations

import csv
import json
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
REVIEW_AFTER = ROOT / "build" / "translation" / "overflow_review_after.csv"
BACKUP = ROOT / "build" / "translation" / "overflow_review_backup"
REVIEW_BEFORE = ROOT / "build" / "translation" / "overflow_review_before.csv"
CAPACITY = ROOT / "build" / "translation" / "fixed_capacity_issues.csv"


def read_rows(path: Path) -> list[dict[str, str]]:
    with path.open("r", encoding="utf-8-sig", newline="") as handle:
        return list(csv.DictReader(handle))


def write_rows(path: Path, rows: list[dict[str, str]]) -> None:
    fields = [
        "file_id",
        "unique_index",
        "jpn_text",
        "cn_text",
        "cn_utf8_bytes",
        "record_indices",
        "segment_count",
        "record_required_before",
        "nominal_capacity",
        "aligned_capacity",
        "over_aligned_bytes",
        "source_note",
    ]
    with path.open("w", encoding="utf-8-sig", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=fields, lineterminator="\n")
        writer.writeheader()
        writer.writerows(rows)


def main() -> None:
    rows = read_rows(REVIEW_AFTER)
    capacity_by_text: dict[tuple[str, str], dict[str, set[str]]] = {}
    with CAPACITY.open("r", encoding="utf-8-sig", newline="") as handle:
        for record in csv.DictReader(handle):
            for text in json.loads(record["cn_texts"]):
                key = (record["file_id"], text)
                item = capacity_by_text.setdefault(
                    key,
                    {
                        "record_indices": set(),
                        "segment_count": set(),
                        "record_required_before": set(),
                        "nominal_capacity": set(),
                        "aligned_capacity": set(),
                        "over_aligned_bytes": set(),
                    },
                )
                item["record_indices"].add(record["record_index"])
                item["segment_count"].add(record["segment_count"])
                item["record_required_before"].add(record["required"])
                item["nominal_capacity"].add(record["nominal_capacity"])
                item["aligned_capacity"].add(record["aligned_capacity"])
                item["over_aligned_bytes"].add(record["over_aligned_bytes"])
    output: list[dict[str, str]] = []
    for row in rows:
        backup = BACKUP / f"{row['file_id']}.csv"
        source_rows = read_rows(backup)
        source = next(item for item in source_rows if item["unique_index"] == row["unique_index"])
        text = source["cn_text"]
        capacity = capacity_by_text.get((row["file_id"], text), {})

        def joined(name: str) -> str:
            values = capacity.get(name, set())
            return ";".join(sorted(values, key=lambda value: int(value)))

        output.append(
            {
                "file_id": row["file_id"],
                "unique_index": row["unique_index"],
                "jpn_text": row["jpn_text"],
                "cn_text": text,
                "cn_utf8_bytes": str(len(text.encode("utf-8"))),
                "record_indices": joined("record_indices"),
                "segment_count": joined("segment_count"),
                "record_required_before": joined("record_required_before"),
                "nominal_capacity": joined("nominal_capacity"),
                "aligned_capacity": joined("aligned_capacity"),
                "over_aligned_bytes": joined("over_aligned_bytes"),
                "source_note": "original production translation before temporary overflow compression",
            }
        )
    write_rows(REVIEW_BEFORE, output)
    print(f"ROWS={len(output)}")
    print(f"CSV={REVIEW_BEFORE}")


if __name__ == "__main__":
    main()
