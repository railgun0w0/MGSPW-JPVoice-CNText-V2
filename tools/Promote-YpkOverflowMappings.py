#!/usr/bin/env python3
"""Promote reviewed YPK capacity edits into the authoritative Sol mappings."""

from __future__ import annotations

import argparse
import csv
import io
import json
import re
from collections import defaultdict
from pathlib import Path


CONTROL_RE = re.compile(r"<[^<>]*>|\$[A-Za-z0-9_]+|%(?:\d+\$)?[sdif]")


class PromotionError(RuntimeError):
    pass


def compact(value: object) -> str:
    return json.dumps(value, ensure_ascii=False, separators=(",", ":"))


def mapping_entry(document: dict, entry: object) -> dict:
    if isinstance(entry, dict):
        return entry
    if isinstance(entry, list):
        columns = document.get("columns")
        if not isinstance(columns, list) or len(columns) != len(entry):
            raise PromotionError("list-form mapping has invalid columns")
        return dict(zip(columns, entry))
    raise PromotionError(f"unsupported mapping entry type: {type(entry).__name__}")


def update_document(path: Path, targets: dict[int, dict[str, str]]) -> int:
    original = path.read_text(encoding="utf-8")
    document = json.loads(original)
    translations = document.get("translations")
    if not isinstance(translations, list):
        raise PromotionError(f"{path}: missing translations array")
    changed = 0
    found: set[int] = set()
    updated = original
    for entry in translations:
        normalized = mapping_entry(document, entry)
        index = normalized.get("unique_index")
        if index not in targets:
            continue
        if index in found:
            raise PromotionError(f"{path}: duplicate unique_index {index}")
        found.add(index)
        target = targets[index]
        old_text = target["old_cn_text"]
        new_text = target["new_cn_text"]
        if normalized.get("cn_text") not in (old_text, new_text):
            raise PromotionError(
                f"{path}: unique_index {index} text differs from reviewed old/new value"
            )
        before = compact(entry)
        if isinstance(entry, dict):
            revised = dict(entry)
            revised["cn_text"] = new_text
            revised["cn_control_tokens"] = " | ".join(CONTROL_RE.findall(new_text))
            revised["cn_utf8_bytes"] = len(new_text.encode("utf-8"))
        else:
            columns = document["columns"]
            revised = list(entry)
            revised[columns.index("cn_text")] = new_text
            revised[columns.index("cn_control_tokens")] = " | ".join(
                CONTROL_RE.findall(new_text)
            )
            if "cn_utf8_bytes" in columns:
                revised[columns.index("cn_utf8_bytes")] = len(new_text.encode("utf-8"))
        after = compact(revised)
        occurrences = updated.count(before)
        if occurrences != 1:
            raise PromotionError(
                f"{path}: compact entry for unique_index {index} occurs {occurrences} times"
            )
        updated = updated.replace(before, after, 1)
        if before != after:
            changed += 1
    missing = sorted(set(targets) - found)
    if missing:
        # A sharded file normally owns only a subset; its missing indices are
        # handled by sibling shards, so the caller checks global coverage.
        pass
    if updated != original:
        path.write_text(updated, encoding="utf-8")
    return changed


def raw_csv_records(text: str) -> list[str]:
    records: list[str] = []
    start = 0
    quoted = False
    index = 0
    while index < len(text):
        char = text[index]
        if char == '"':
            if quoted and index + 1 < len(text) and text[index + 1] == '"':
                index += 2
                continue
            quoted = not quoted
        if char == "\n" and not quoted:
            records.append(text[start : index + 1])
            start = index + 1
        index += 1
    if start < len(text):
        records.append(text[start:])
    if quoted:
        raise PromotionError("unterminated quoted CSV field")
    return records


def encode_csv_row(values: list[str], newline: str) -> str:
    stream = io.StringIO(newline="")
    writer = csv.writer(stream, lineterminator=newline)
    writer.writerow(values)
    return stream.getvalue()


def update_direct_csv(path: Path, targets: dict[int, dict[str, str]]) -> int:
    original = path.read_bytes().decode("utf-8")
    bom = "\ufeff" if original.startswith("\ufeff") else ""
    body = original[len(bom) :]
    raw_records = raw_csv_records(body)
    if not raw_records:
        raise PromotionError(f"{path}: empty CSV")
    header = next(csv.reader(io.StringIO(raw_records[0], newline="")))
    required = {"unique_index", "cn_text", "cn_control_tokens", "cn_utf8_bytes"}
    if not required.issubset(header):
        raise PromotionError(f"{path}: missing required columns {sorted(required-set(header))}")
    positions = {name: header.index(name) for name in required}
    found: set[int] = set()
    changed = 0
    for record_index in range(1, len(raw_records)):
        raw_record = raw_records[record_index]
        values = next(csv.reader(io.StringIO(raw_record, newline="")))
        if len(values) <= positions["unique_index"] or not values[positions["unique_index"]]:
            continue
        try:
            index = int(values[positions["unique_index"]])
        except ValueError:
            continue
        if index not in targets:
            continue
        if index in found:
            raise PromotionError(f"{path}: duplicate unique_index {index}")
        found.add(index)
        target = targets[index]
        current = values[positions["cn_text"]].replace("\r\n", "\n")
        if current not in (target["old_cn_text"], target["new_cn_text"]):
            raise PromotionError(
                f"{path}: unique_index {index} text differs from reviewed old/new value"
            )
        new_text = target["new_cn_text"]
        values[positions["cn_text"]] = new_text
        values[positions["cn_control_tokens"]] = " | ".join(CONTROL_RE.findall(new_text))
        values[positions["cn_utf8_bytes"]] = str(len(new_text.encode("utf-8")))
        newline = "\r\n" if raw_record.endswith("\r\n") else "\n" if raw_record.endswith("\n") else ""
        revised = encode_csv_row(values, newline)
        if revised != raw_record:
            raw_records[record_index] = revised
            changed += 1
    missing = sorted(set(targets) - found)
    if missing:
        raise PromotionError(f"{path}: reviewed indices missing from direct CSV: {missing}")
    updated = bom + "".join(raw_records)
    if updated != original:
        path.write_bytes(updated.encode("utf-8"))
    return changed


def main() -> int:
    root = Path(__file__).resolve().parents[1]
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--review",
        type=Path,
        default=root / "build" / "translation" / "overflow_review_after.csv",
    )
    parser.add_argument("--translation-repo", type=Path, required=True)
    args = parser.parse_args()

    rows = list(csv.DictReader(args.review.open("r", encoding="utf-8-sig", newline="")))
    by_file: dict[str, dict[int, dict[str, str]]] = defaultdict(dict)
    for row in rows:
        file_id = row["file_id"].upper()
        index = int(row["unique_index"])
        if index in by_file[file_id]:
            raise PromotionError(f"duplicate reviewed mapping {file_id}/{index}")
        by_file[file_id][index] = row

    mapping_root = (
        args.translation_repo
        / "work"
        / "luna_translation_templates"
        / "sol_translation_mappings"
        / "YPK_GTT"
    )
    direct_root = (
        args.translation_repo / "work" / "luna_translation_templates" / "YPK_GTT"
    )
    total_changed = 0
    verified = 0
    changed_files: list[str] = []
    for file_id, targets in sorted(by_file.items()):
        manifest_path = mapping_root / f"{file_id}.manifest.json"
        if manifest_path.is_file():
            manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
            paths = [mapping_root / part["path"] for part in manifest["parts"]]
        else:
            flat_path = mapping_root / f"{file_id}.json"
            if not flat_path.is_file():
                direct_path = direct_root / f"{file_id}.csv"
                changed = update_direct_csv(direct_path, targets)
                total_changed += changed
                if changed:
                    changed_files.append(str(direct_path.resolve()))
                verified += len(targets)
                continue
            paths = [flat_path]
        found: dict[int, tuple[Path, dict]] = {}
        for path in paths:
            document = json.loads(path.read_text(encoding="utf-8"))
            for entry in document.get("translations", []):
                normalized = mapping_entry(document, entry)
                index = normalized.get("unique_index")
                if index in targets:
                    if index in found:
                        raise PromotionError(f"{file_id}/{index}: appears in multiple mapping files")
                    found[index] = (path, normalized)
        if set(found) != set(targets):
            raise PromotionError(
                f"{file_id}: reviewed indices missing from mappings: {sorted(set(targets)-set(found))}"
            )
        paths_by_target: dict[Path, dict[int, dict[str, str]]] = defaultdict(dict)
        for index, (path, _) in found.items():
            paths_by_target[path][index] = targets[index]
        for path, subset in paths_by_target.items():
            changed = update_document(path, subset)
            total_changed += changed
            if changed:
                changed_files.append(str(path.resolve()))
        for index, (path, _) in found.items():
            document = json.loads(path.read_text(encoding="utf-8"))
            entry = next(
                mapping_entry(document, item)
                for item in document["translations"]
                if mapping_entry(document, item)["unique_index"] == index
            )
            expected = targets[index]["new_cn_text"]
            if entry["cn_text"] != expected:
                raise PromotionError(f"{file_id}/{index}: post-write text mismatch")
            if "cn_utf8_bytes" in entry and entry["cn_utf8_bytes"] != len(expected.encode("utf-8")):
                raise PromotionError(f"{file_id}/{index}: post-write byte length mismatch")
            verified += 1

    print(f"REVIEW_ROWS={len(rows)}")
    print(f"FILE_IDS={len(by_file)}")
    print(f"UPDATED_MAPPINGS={total_changed}")
    print(f"VERIFIED_MAPPINGS={verified}")
    print(f"CHANGED_FILES={len(set(changed_files))}")
    return 0


if __name__ == "__main__":
    try:
        raise SystemExit(main())
    except PromotionError as error:
        print(f"ERROR={error}")
        raise SystemExit(1)
