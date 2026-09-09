from __future__ import annotations

import csv
import json
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
BEFORE = ROOT / "build" / "translation" / "overflow_review_before.csv"
MASTER = ROOT / "build" / "translation" / "jpn_gtt" / "jpn_gtt_master.csv"
OUTPUT = ROOT / "build" / "translation" / "overflow_29_recheck_after.csv"


def read_rows(path: Path) -> list[dict[str, str]]:
    with path.open("r", encoding="utf-8-sig", newline="") as handle:
        return list(csv.DictReader(handle))


def write_rows(path: Path, rows: list[dict[str, str]]) -> None:
    fields = [
        "file_id",
        "record_index",
        "segment_count",
        "header_size",
        "record_size",
        "aligned_size",
        "required_before",
        "required_after",
        "nominal_capacity",
        "aligned_capacity",
        "over_before",
        "over_after",
        "status_after",
        "jpn_texts",
        "cn_texts_before",
        "cn_texts_after",
    ]
    with path.open("w", encoding="utf-8-sig", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=fields, lineterminator="\n")
        writer.writeheader()
        writer.writerows(rows)


def main() -> None:
    before_rows = read_rows(BEFORE)
    before_by_text: dict[tuple[str, str], str] = {}
    current_by_text: dict[tuple[str, str], str] = {}
    affected: set[tuple[str, int]] = set()
    for row in before_rows:
        before_by_text[(row["file_id"], row["jpn_text"])] = row["cn_text"]
        for record_index in row["record_indices"].split(";"):
            affected.add((row["file_id"], int(record_index)))
    for file_id in sorted({file_id for file_id, _ in affected}):
        for row in read_rows(ROOT / "translations" / "ypk_gtt" / f"{file_id}.csv"):
            current_by_text[(file_id, row["jpn_text"])] = row["cn_text"]

    master_groups: dict[tuple[str, int], list[dict[str, str]]] = {}
    for row in read_rows(MASTER):
        key = (row["file_id"], int(row["record_index"]))
        if key in affected:
            master_groups.setdefault(key, []).append(row)

    output: list[dict[str, str]] = []
    if set(master_groups) != affected:
        raise RuntimeError(f"missing affected master records: {sorted(affected-set(master_groups))}")
    for (file_id, record_index), rows in sorted(master_groups.items()):
        rows.sort(key=lambda row: int(row["segment_index"]))
        before = [
            before_by_text.get((file_id, row["jpn_text"]), current_by_text[(file_id, row["jpn_text"])])
            for row in rows
        ]
        after = [current_by_text[(file_id, row["jpn_text"])] for row in rows]
        required_before = sum(len(text.encode("utf-8")) + 1 for text in before)
        required_after = sum(len(text.encode("utf-8")) + 1 for text in after)
        first = rows[0]
        header_size = int(first["header_size"])
        record_size = int(first["record_size"])
        aligned_size = int(first["aligned_size"])
        nominal_capacity = record_size - header_size
        hard_capacity = aligned_size - header_size
        if required_after > hard_capacity:
            status_after = "HARD_OVERFLOW"
        elif required_after > nominal_capacity:
            status_after = "ALIGNMENT_SPILL"
        else:
            status_after = "NORMAL_FIT"
        output.append(
            {
                "file_id": file_id,
                "record_index": record_index,
                "segment_count": first["segment_count"],
                "header_size": header_size,
                "record_size": record_size,
                "aligned_size": aligned_size,
                "required_before": required_before,
                "required_after": str(required_after),
                "nominal_capacity": nominal_capacity,
                "aligned_capacity": hard_capacity,
                "over_before": max(0, required_before - hard_capacity),
                "over_after": str(max(0, required_after - hard_capacity)),
                "status_after": status_after,
                "jpn_texts": json.dumps([row["jpn_text"] for row in rows], ensure_ascii=False),
                "cn_texts_before": json.dumps(before, ensure_ascii=False),
                "cn_texts_after": json.dumps(after, ensure_ascii=False),
            }
        )
    write_rows(OUTPUT, output)
    hard = sum(row["status_after"] == "HARD_OVERFLOW" for row in output)
    spill = sum(row["status_after"] == "ALIGNMENT_SPILL" for row in output)
    fit = sum(row["status_after"] == "NORMAL_FIT" for row in output)
    print(f"RECORDS={len(output)}")
    print(f"NORMAL_FIT={fit}")
    print(f"ALIGNMENT_SPILL={spill}")
    print(f"HARD_OVERFLOW={hard}")
    print(f"CSV={OUTPUT}")


if __name__ == "__main__":
    main()
