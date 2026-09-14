#!/usr/bin/env python3
"""Apply an audited Ruby canonical table with minimal source-text edits.

The default mode is read-only.  ``--write`` changes only the Ruby token text
inside existing JSON mapping ``cn_text`` fields and the five explicitly
approved legacy YPK template CSV ``cn_text`` fields.  It never creates mapping
artifacts or reserializes JSON/CSV documents.
"""

from __future__ import annotations

import argparse
import csv
import json
import re
from collections import Counter
from dataclasses import dataclass
from pathlib import Path
from typing import Iterable


RESOURCE_DIRS = {
    "YPK_GTT": "YPK_GTT",
    "OHD": "OHD",
    "LOOSE_OLANG": "LOOSE_OLANG",
    "STAGEDAT_OLANG": "STAGEDAT_OLANG",
    "SLOT_OLANG": "SLOT_OLANG",
    "BRIEFING_NBE": "BRIEFING",
}
PRODUCTION_DIRS = {
    "YPK_GTT": "ypk_gtt",
    "OHD": "ohd",
    "LOOSE_OLANG": "loose_olang",
    "STAGEDAT_OLANG": "stagedat_olang",
    "SLOT_OLANG": "slot_olang",
    "BRIEFING_NBE": "briefing",
}
LEGACY_YPK = {
    "1C79F2ED",
    "1C7B72ED",
    "1C7BF2AD",
    "1C7C72AD",
    "1C7CF2ED",
}
RUBY_RE = re.compile(r"<R=([^,<>]*),([^<>]*)>")
INDEX_RE = re.compile(r'"unique_index"\s*:\s*(\d+)(?=\s*[,}])')
CN_FIELD_RE = re.compile(r'"cn_text"\s*:\s*')


class AuditError(RuntimeError):
    pass


@dataclass
class Target:
    resource_class: str
    file_id: str
    unique_index: int
    old_cn: str
    new_cn: str
    changed_occurrences: int
    path: Path
    kind: str


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    root = Path(__file__).resolve().parents[1]
    parser.add_argument("--root", type=Path, default=root)
    parser.add_argument(
        "--canonical",
        type=Path,
        default=root / "doc" / "ruby_base_pair_canonical.csv",
    )
    parser.add_argument("--write", action="store_true")
    return parser.parse_args()


def load_canonical(path: Path) -> dict[tuple[str, str], tuple[str, str]]:
    with path.open("r", encoding="utf-8-sig", newline="") as handle:
        rows = list(csv.DictReader(handle))
    if len(rows) != 587:
        raise AuditError(f"canonical row count is {len(rows)}, expected 587")
    result: dict[tuple[str, str], tuple[str, str]] = {}
    for row in rows:
        key = (row["jpn_base"], row["jpn_ruby"])
        value = (row["cn_base"], row["cn_ruby"])
        if key in result:
            raise AuditError(f"duplicate canonical pair: {key!r}")
        if not all(value):
            raise AuditError(f"blank canonical CN value: {key!r}")
        result[key] = value
    if len(result) != 587:
        raise AuditError(f"canonical unique pair count is {len(result)}, expected 587")
    return result


def load_csv(path: Path) -> list[dict[str, str]]:
    with path.open("r", encoding="utf-8-sig", newline="") as handle:
        return list(csv.DictReader(handle))


def read_production(root: Path) -> dict[tuple[str, str, int], str]:
    result: dict[tuple[str, str, int], str] = {}
    for resource_class, directory in PRODUCTION_DIRS.items():
        for path in sorted((root / "translations" / directory).glob("*.csv")):
            for row in load_csv(path):
                key = (resource_class, row["file_id"].upper(), int(row["unique_index"]))
                result[key] = row.get("cn_text", "")
    if len(result) != 26686:
        raise AuditError(f"production corpus has {len(result)} rows, expected 26686")
    return result


def ruby_pairs(text: str) -> list[tuple[str, str]]:
    return [(match.group(1), match.group(2)) for match in RUBY_RE.finditer(text)]


def reflow_cn(
    jpn_text: str, cn_text: str, canonical: dict[tuple[str, str], tuple[str, str]]
) -> tuple[str, int, int, int]:
    return replace_rubies(jpn_text, cn_text, canonical, None)


def replace_rubies(
    jpn_text: str,
    cn_text: str,
    canonical: dict[tuple[str, str], tuple[str, str]],
    selected: set[int] | None,
) -> tuple[str, int, int, int]:
    jpn = ruby_pairs(jpn_text)
    cn_matches = list(RUBY_RE.finditer(cn_text))
    if len(jpn) != len(cn_matches):
        raise AuditError(
            f"Ruby count mismatch: JPN={len(jpn)} CN={len(cn_matches)}"
        )
    new_text = cn_text
    changed = 0
    unmapped = 0
    cursor = 0
    parts: list[str] = []
    for ordinal, (jpn_pair, match) in enumerate(zip(jpn, cn_matches)):
        parts.append(cn_text[cursor : match.start()])
        is_selected = selected is None or ordinal in selected
        target = canonical.get(jpn_pair) if is_selected else None
        if not is_selected:
            parts.append(match.group(0))
        elif target is None:
            unmapped += 1
            parts.append(match.group(0))
        else:
            replacement = f"<R={target[0]},{target[1]}>"
            parts.append(replacement)
            if replacement != match.group(0):
                changed += 1
        cursor = match.end()
    parts.append(cn_text[cursor:])
    new_text = "".join(parts)
    outside_old = RUBY_RE.sub("<R>", cn_text)
    outside_new = RUBY_RE.sub("<R>", new_text)
    if outside_old != outside_new:
        raise AuditError("Ruby-outside text changed")
    return new_text, changed, unmapped, len(jpn)


def resolve_manifest_paths(mapping_dir: Path, file_id: str) -> list[Path]:
    manifest = mapping_dir / f"{file_id}.manifest.json"
    flat = mapping_dir / f"{file_id}.json"
    descriptor = manifest if manifest.is_file() else flat if flat.is_file() else None
    if descriptor is not None:
        data = json.loads(descriptor.read_text(encoding="utf-8-sig"))
        members = data.get("parts", data.get("shards", []))
        if not isinstance(members, list):
            members = []
        if descriptor == flat and not members:
            return [flat.resolve()]
        paths: list[Path] = []
        for member in members:
            raw = str(member.get("path", ""))
            normalized = raw.replace("\\", "/")
            candidates = [
                mapping_dir / normalized,
                mapping_dir.parent.parent / normalized,
            ]
            if normalized.startswith("sol_translation_mappings/"):
                candidates.insert(0, mapping_dir.parent.parent / normalized)
            chosen = next((candidate for candidate in candidates if candidate.is_file()), None)
            if chosen is None:
                raise AuditError(f"missing mapping descriptor member {raw!r} in {descriptor}")
            paths.append(chosen.resolve())
        if not paths:
            raise AuditError(f"empty mapping descriptor: {descriptor}")
        return paths
    raise AuditError(f"no existing JSON mapping for {file_id}")


def json_cn_field_span(raw: str, unique_index: int) -> tuple[int, int, str]:
    decoder = json.JSONDecoder()
    matches = [m for m in INDEX_RE.finditer(raw) if int(m.group(1)) == unique_index]
    if len(matches) != 1:
        raise AuditError(f"expected one JSON unique_index {unique_index}, found {len(matches)}")
    index_match = matches[0]
    next_index = INDEX_RE.search(raw, index_match.end())
    region_end = next_index.start() if next_index else len(raw)
    field = CN_FIELD_RE.search(raw, index_match.end(), region_end)
    if field is None:
        raise AuditError(f"unique_index {unique_index} has no cn_text field")
    value_start = field.end()
    while value_start < region_end and raw[value_start].isspace():
        value_start += 1
    value, value_end = decoder.raw_decode(raw, value_start)
    if not isinstance(value, str):
        raise AuditError(f"unique_index {unique_index} cn_text is not a JSON string")
    return value_start, value_end, value


def json_array_element_spans(raw: str, array_start: int) -> list[tuple[int, int, object]]:
    decoder = json.JSONDecoder()
    if raw[array_start] != "[":
        raise AuditError("expected JSON array")
    elements: list[tuple[int, int, object]] = []
    cursor = array_start + 1
    while True:
        while cursor < len(raw) and raw[cursor].isspace():
            cursor += 1
        if cursor >= len(raw):
            raise AuditError("unterminated JSON array")
        if raw[cursor] == "]":
            return elements
        start = cursor
        value, end = decoder.raw_decode(raw, cursor)
        elements.append((start, end, value))
        cursor = end
        while cursor < len(raw) and raw[cursor].isspace():
            cursor += 1
        if cursor >= len(raw):
            raise AuditError("unterminated JSON array")
        if raw[cursor] == ",":
            cursor += 1
            continue
        if raw[cursor] == "]":
            return elements
        raise AuditError("invalid JSON array separator")


def json_mapping_row_spans(raw: str) -> dict[int, tuple[int, int, str]]:
    """Locate cn_text raw string spans for both object and positional schemas."""
    decoder = json.JSONDecoder()
    root = json.loads(raw)
    columns = root.get("columns")
    if not isinstance(columns, list):
        columns = []
    try:
        index_column = columns.index("unique_index")
        cn_column = columns.index("cn_text")
    except ValueError:
        index_column = cn_column = -1
    match = re.search(r'"translations"\s*:\s*', raw)
    if match is None:
        raise AuditError("mapping has no translations array")
    list_start = match.end()
    while list_start < len(raw) and raw[list_start].isspace():
        list_start += 1
    rows = json_array_element_spans(raw, list_start)
    result: dict[int, tuple[int, int, str]] = {}
    for row_start, row_end, value in rows:
        if isinstance(value, dict):
            index_value = value.get("unique_index")
            if index_value is None:
                continue
            segment = raw[row_start:row_end]
            local_start, local_end, cn_value = json_cn_field_span(segment, int(index_value))
            result[int(index_value)] = (row_start + local_start, row_start + local_end, cn_value)
        elif isinstance(value, list) and index_column >= 0 and cn_column >= 0:
            if len(value) <= max(index_column, cn_column):
                raise AuditError("positional translation row is shorter than columns")
            index_value = int(value[index_column])
            elements = json_array_element_spans(raw, row_start)
            cn_start, cn_end, cn_value = elements[cn_column]
            if not isinstance(cn_value, str):
                raise AuditError(f"positional cn_text is not a string at index {index_value}")
            result[index_value] = (cn_start, cn_end, cn_value)
        else:
            raise AuditError("unsupported translation row schema")
    return result


def parse_csv_spans(raw: str) -> list[list[tuple[int, int]]]:
    """Return raw spans for every CSV field, including quoted newlines."""
    rows: list[list[tuple[int, int]]] = []
    fields: list[tuple[int, int]] = []
    i = 0
    start = 0
    length = len(raw)
    while i < length:
        if raw[i] == '"':
            i += 1
            while i < length:
                if raw[i] == '"':
                    if i + 1 < length and raw[i + 1] == '"':
                        i += 2
                        continue
                    i += 1
                    break
                i += 1
            while i < length and raw[i] not in ",\r\n":
                i += 1
        else:
            while i < length and raw[i] not in ",\r\n":
                i += 1
        fields.append((start, i))
        if i >= length:
            break
        if raw[i] == ",":
            i += 1
            start = i
            continue
        if raw[i] == "\r" and i + 1 < length and raw[i + 1] == "\n":
            i += 2
        else:
            i += 1
        rows.append(fields)
        fields = []
        start = i
    if fields:
        rows.append(fields)
    return rows


def decode_csv_field(raw_field: str) -> str:
    rows = list(csv.reader([raw_field]))
    if len(rows) != 1 or len(rows[0]) != 1:
        raise AuditError(f"cannot decode CSV field: {raw_field[:80]!r}")
    return rows[0][0]


def legacy_csv_field_spans(path: Path) -> tuple[str, dict[tuple[str, int], tuple[int, int]]]:
    raw = path.read_bytes().decode("utf-8")
    if raw.startswith("\ufeff"):
        raw = raw[1:]
    rows = parse_csv_spans(raw)
    if not rows:
        raise AuditError(f"empty CSV: {path}")
    headers = [decode_csv_field(raw[a:b]) for a, b in rows[0]]
    try:
        file_col = headers.index("file_id")
        index_col = headers.index("unique_index")
        cn_col = headers.index("cn_text")
    except ValueError as exc:
        raise AuditError(f"legacy CSV missing required column: {path}") from exc
    spans: dict[tuple[str, int], tuple[int, int]] = {}
    for fields in rows[1:]:
        if len(fields) <= max(file_col, index_col, cn_col):
            continue
        file_id = decode_csv_field(raw[slice(*fields[file_col])]).upper()
        index_text = decode_csv_field(raw[slice(*fields[index_col])])
        if not index_text.isdigit():
            continue
        spans[(file_id, int(index_text))] = fields[cn_col]
    return raw, spans


def load_templates(root: Path) -> dict[tuple[str, str, int], dict[str, str]]:
    result: dict[tuple[str, str, int], dict[str, str]] = {}
    for resource_class, directory in RESOURCE_DIRS.items():
        for path in sorted((root / "work" / "luna_translation_templates" / directory).glob("*.csv")):
            for row in load_csv(path):
                result[(resource_class, row["file_id"].upper(), int(row["unique_index"]))] = row
    if len(result) != 26686:
        raise AuditError(f"template corpus has {len(result)} rows, expected 26686")
    return result


def build_plan(root: Path, canonical: dict[tuple[str, str], tuple[str, str]]) -> tuple[list[Target], Counter, Counter]:
    templates = load_templates(root)
    production = read_production(root)
    plans: list[Target] = []
    counters: Counter = Counter()
    errors: Counter = Counter()
    json_paths_by_file: dict[tuple[str, str], list[Path]] = {}
    json_rows: dict[tuple[str, str, int], tuple[Path, int, int, str]] = {}

    def ensure_json_rows(resource_class: str, file_id: str) -> None:
        key = (resource_class, file_id)
        if key in json_paths_by_file:
            return
        paths = resolve_manifest_paths(
            root / "work" / "luna_translation_templates" / "sol_translation_mappings" / RESOURCE_DIRS[resource_class],
            file_id,
        )
        json_paths_by_file[key] = paths
        for path in paths:
            raw = path.read_bytes().decode("utf-8")
            if raw.startswith("\ufeff"):
                raw = raw[1:]
            for index, (start, end, value) in json_mapping_row_spans(raw).items():
                row_key = (resource_class, file_id, index)
                if row_key in json_rows:
                    raise AuditError(f"duplicate canonical JSON row: {row_key}")
                json_rows[row_key] = (path, start, end, value)

    for key, template_row in templates.items():
        resource_class, file_id, index = key
        jpn_text = template_row.get("jpn_text", "")
        mapping_dir = (
            root
            / "work"
            / "luna_translation_templates"
            / "sol_translation_mappings"
            / RESOURCE_DIRS[resource_class]
        )
        has_json = (
            (mapping_dir / f"{file_id}.json").is_file()
            or (mapping_dir / f"{file_id}.manifest.json").is_file()
        )
        # The effective pre-compile corpus is the production CSV. This keeps
        # the rewrite target anchored to what was actually emitted before the
        # source-of-truth compiler cleanup; mappings remain the post-cleanup
        # production source.
        cn_text = production[key]
        try:
            effective_new_cn, effective_changed, unmapped, ruby_count = reflow_cn(
                jpn_text, cn_text, canonical
            )
        except AuditError as exc:
            if "Ruby count mismatch" in str(exc):
                errors["RUBY_COUNT_MISMATCH"] += 1
            else:
                errors["AUDIT_ERROR"] += 1
            raise AuditError(f"{resource_class}/{file_id}#{index}: {exc}") from exc
        counters["ruby_occurrences"] += ruby_count
        counters["unmapped_occurrences"] += unmapped
        if not effective_changed:
            continue
        if resource_class == "YPK_GTT" and file_id in LEGACY_YPK:
            new_cn = effective_new_cn
            changed = effective_changed
            path = root / "work" / "luna_translation_templates" / "YPK_GTT" / f"{file_id}.csv"
            raw, spans = legacy_csv_field_spans(path)
            if (file_id, index) not in spans:
                raise AuditError(f"missing legacy CSV row {file_id}#{index}")
            start, end = spans[(file_id, index)]
            raw_cn = decode_csv_field(raw[start:end])
            if raw_cn != template_row.get("cn_text", ""):
                # The two known shifted rows do not contain Ruby targets; this guard keeps
                # the recovery layout untouched if a future target does.
                if raw_cn != cn_text:
                    raise AuditError(f"legacy CSV/current production mismatch at {file_id}#{index}")
            if RUBY_RE.sub("<R>", raw_cn) != RUBY_RE.sub("<R>", new_cn):
                raise AuditError(f"legacy Ruby-outside mismatch at {file_id}#{index}")
            plans.append(Target(resource_class, file_id, index, raw_cn, new_cn, changed, path, "legacy_template_csv"))
            counters["legacy_occurrences"] += changed
            continue
        json_key = (resource_class, file_id, index)
        if not has_json:
            raise AuditError(f"missing JSON mapping for changed row {json_key}")
        ensure_json_rows(resource_class, file_id)
        if json_key not in json_rows:
            raise AuditError(f"missing JSON mapping row {json_key}")
        path, start, end, json_cn = json_rows[json_key]
        selected = {
            ordinal
            for ordinal, pair in enumerate(ruby_pairs(jpn_text))
            if canonical.get(pair) != ruby_pairs(cn_text)[ordinal]
        }
        new_cn, changed, json_unmapped, json_count = replace_rubies(
            jpn_text, json_cn, canonical, selected
        )
        if json_unmapped or json_count != ruby_count:
            raise AuditError(f"JSON Ruby mapping mismatch at {resource_class}/{file_id}#{index}")
        if RUBY_RE.sub("<R>", json_cn) != RUBY_RE.sub("<R>", new_cn):
            raise AuditError(f"JSON Ruby-outside text changed at {resource_class}/{file_id}#{index}")
        if not changed:
            raise AuditError(
                f"effective canonical target has no JSON token change at "
                f"{resource_class}/{file_id}#{index}"
            )
        plans.append(Target(resource_class, file_id, index, json_cn, new_cn, changed, path, "json_mapping"))
        counters["json_occurrences"] += changed
    counters["target_rows"] = len(plans)
    counters["target_files"] = len({(item.kind, item.path) for item in plans})
    return plans, counters, errors


def apply_json(plans: Iterable[Target]) -> None:
    by_path: dict[Path, list[Target]] = {}
    for item in plans:
        if item.kind == "json_mapping":
            by_path.setdefault(item.path, []).append(item)
    for path, items in by_path.items():
        raw = path.read_bytes().decode("utf-8")
        bom = raw.startswith("\ufeff")
        body = raw[1:] if bom else raw
        replacements: list[tuple[int, int, str]] = []
        for item in items:
            start, end, current = json_mapping_row_spans(body)[item.unique_index]
            if current != item.old_cn:
                raise AuditError(f"JSON changed before write: {path}#{item.unique_index}")
            replacements.append((start, end, json.dumps(item.new_cn, ensure_ascii=False)))
        for start, end, replacement in sorted(replacements, reverse=True):
            body = body[:start] + replacement + body[end:]
        path.write_bytes(("\ufeff" if bom else "") .encode("utf-8") + body.encode("utf-8"))


def apply_legacy(plans: Iterable[Target]) -> None:
    by_path: dict[Path, list[Target]] = {}
    for item in plans:
        if item.kind == "legacy_template_csv":
            by_path.setdefault(item.path, []).append(item)
    for path, items in by_path.items():
        raw_bytes = path.read_bytes()
        raw = raw_bytes.decode("utf-8")
        bom = raw.startswith("\ufeff")
        body = raw[1:] if bom else raw
        _, spans = legacy_csv_field_spans(path)
        replacements: list[tuple[int, int, str]] = []
        for item in items:
            start, end = spans[(item.file_id, item.unique_index)]
            current = decode_csv_field(body[start:end])
            if current != item.old_cn:
                raise AuditError(f"legacy CSV changed before write: {path}#{item.unique_index}")
            raw_field = body[start:end]
            old_tokens = list(RUBY_RE.finditer(current))
            new_tokens = list(RUBY_RE.finditer(item.new_cn))
            if len(old_tokens) != len(new_tokens):
                raise AuditError(f"legacy token count changed: {path}#{item.unique_index}")
            # Token text contains no CSV quotes, so replacing inside the original raw
            # field preserves quoting, line endings, and every non-token byte.
            updated = raw_field
            for old, new in zip(reversed(old_tokens), reversed(new_tokens)):
                old_token = old.group(0)
                new_token = new.group(0)
                pos = updated.find(old_token)
                if pos < 0:
                    raise AuditError(f"legacy raw token not found: {path}#{item.unique_index}")
                updated = updated[:pos] + new_token + updated[pos + len(old_token):]
            replacements.append((start, end, updated))
        for start, end, replacement in sorted(replacements, reverse=True):
            body = body[:start] + replacement + body[end:]
        path.write_bytes(("\ufeff" if bom else "").encode("utf-8") + body.encode("utf-8"))


def main() -> int:
    args = parse_args()
    root = args.root.resolve()
    canonical_path = args.canonical.resolve()
    canonical = load_canonical(canonical_path)
    plans, counters, _ = build_plan(root, canonical)
    print(f"MODE={'WRITE' if args.write else 'DRY_RUN'}")
    print(f"CANONICAL_UNIQUE_PAIRS={len(canonical)}")
    print(f"RUBY_OCCURRENCES={counters['ruby_occurrences']}")
    print(f"UNMAPPED_PAIR={counters['unmapped_occurrences']}")
    print("RUBY_COUNT_MISMATCH=0")
    print(f"JSON_MAPPING_OCCURRENCES={counters['json_occurrences']}")
    print(f"LEGACY_CSV_OCCURRENCES={counters['legacy_occurrences']}")
    print(f"MODIFIED_ROWS={counters['target_rows']}")
    print(f"MODIFIED_FILES={counters['target_files']}")
    for item in plans:
        print(
            f"CHANGE {item.kind} {item.resource_class}/{item.file_id}#{item.unique_index} "
            f"ruby_occurrences={item.changed_occurrences} path={item.path.relative_to(root)}"
        )
    if args.write:
        apply_json(plans)
        apply_legacy(plans)
        print("APPLY=PASS")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
