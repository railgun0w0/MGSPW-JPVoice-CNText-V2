from __future__ import annotations

import argparse
import csv
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
TRANSLATIONS = ROOT / "translations" / "ypk_gtt"
REVIEW_AFTER = ROOT / "build" / "translation" / "overflow_review_after.csv"


def read_rows(path: Path) -> tuple[list[str], list[dict[str, str]]]:
    with path.open("r", encoding="utf-8-sig", newline="") as handle:
        reader = csv.DictReader(handle)
        return list(reader.fieldnames or []), list(reader)


def write_rows(path: Path, fields: list[str], rows: list[dict[str, str]]) -> None:
    temp = path.with_suffix(path.suffix + ".tmp")
    with temp.open("w", encoding="utf-8-sig", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=fields, lineterminator="\n")
        writer.writeheader()
        writer.writerows(rows)
    temp.replace(path)


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument(
        "--csv",
        type=Path,
        default=Path(r"C:\Users\RAILGU~1\Downloads\fixed_capacity_issues.csv"),
    )
    args = parser.parse_args()
    _, user_rows = read_rows(args.csv)
    if not user_rows:
        raise RuntimeError("uploaded overflow CSV has no rows")

    applied = 0
    touched_files: set[str] = set()
    for user in user_rows:
        file_id = user["file_id"].upper()
        index = user["unique_index"]
        path = TRANSLATIONS / f"{file_id}.csv"
        fields, rows = read_rows(path)
        matches = [row for row in rows if row["unique_index"] == index]
        if len(matches) != 1:
            raise RuntimeError(f"{file_id}/{index}: expected one production row, got {len(matches)}")
        # The uploaded CSV uses literal \\n+        # notation for line breaks. Store actual linefeeds in GTT text.
        text = user["cn_text"].replace("\\n", "\n")
        row = matches[0]
        row["cn_text"] = text
        row["cn_utf8_bytes"] = str(len(text.encode("utf-8")))
        write_rows(path, fields, rows)
        touched_files.add(file_id)
        applied += 1

    fields, review_rows = read_rows(REVIEW_AFTER)
    by_key = {(row["file_id"], row["unique_index"]): row for row in review_rows}
    for user in user_rows:
        key = (user["file_id"].upper(), user["unique_index"])
        if key not in by_key:
            raise RuntimeError(f"overflow review row missing: {key[0]}/{key[1]}")
        text = user["cn_text"].replace("\\n", "\n")
        by_key[key]["new_cn_text"] = text
        by_key[key]["new_utf8_bytes"] = str(len(text.encode("utf-8")))
    write_rows(REVIEW_AFTER, fields, review_rows)

    print(f"APPLIED_ROWS={applied}")
    print(f"TOUCHED_FILES={len(touched_files)}")
    print(f"REVIEW={REVIEW_AFTER}")


if __name__ == "__main__":
    main()
