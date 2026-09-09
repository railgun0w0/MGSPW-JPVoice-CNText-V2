#!/usr/bin/env python3
"""Compile validated Sol mappings into V2 production CSVs and object manifest.

The translation Git repository is the mapping fact source.  Clean V2 JPN
templates and masters remain the structural fact source.  This compiler does
not build or install game files.
"""

from __future__ import annotations

import argparse
import csv
import hashlib
import importlib.util
import io
import json
import re
import subprocess
import sys
from collections import Counter, defaultdict
from dataclasses import dataclass
from pathlib import Path
from typing import Any, Iterable


sys.dont_write_bytecode = True


RESOURCE_CLASSES = (
    "YPK_GTT",
    "OHD",
    "LOOSE_OLANG",
    "STAGEDAT_OLANG",
    "SLOT_OLANG",
)

MASTER_PATHS = {
    "YPK_GTT": Path("build/translation/jpn_gtt/jpn_gtt_master.csv"),
    "OHD": Path("build/translation/jpn_ohd/jpn_ohd_master.csv"),
    "LOOSE_OLANG": Path("build/translation/jpn_loose_olang/jpn_loose_olang_master.csv"),
    "STAGEDAT_OLANG": Path("build/translation/jpn_stagedat/jpn_stagedat_text_master.csv"),
    "SLOT_OLANG": Path("build/translation/jpn_slot_olang/jpn_slot_olang_master.csv"),
}

PRODUCTION_DIRS = {
    "YPK_GTT": "ypk_gtt",
    "OHD": "ohd",
    "LOOSE_OLANG": "loose_olang",
    "STAGEDAT_OLANG": "stagedat_olang",
    "SLOT_OLANG": "slot_olang",
}

PRODUCTION_COLUMNS = (
    "file_id",
    "unique_index",
    "first_reference_index",
    "reference_indices",
    "reference_count",
    "scene_context",
    "entity_context",
    "previous_jpn_text",
    "jpn_text",
    "next_jpn_text",
    "jpn_control_tokens",
    "cn_text",
    "cn_control_tokens",
    "control_structure_status",
    "jpn_utf8_bytes",
    "cn_utf8_bytes",
    "translation_status",
    "build_status",
    "ingame_status",
    "translation_basis",
    "notes",
)

MANIFEST_COLUMNS = (
    "resource_class",
    "resource_id",
    "file_id",
    "container",
    "page",
    "page_entry_start",
    "page_entry_capacity",
    "tag_index",
    "payload_variant_index",
    "occurrence_count",
    "occurrence_locations",
    "archive_entry_index",
    "archive_entry_name",
    "object_type",
    "object_index",
    "record_index",
    "record_offset",
    "reference_index",
    "segment_index",
    "segment_count",
    "entity_index",
    "entity_key",
    "ordinal_in_entity",
    "language_key",
    "style",
    "header_size",
    "record_size",
    "aligned_size",
    "timing_start",
    "timing_end",
    "text_start",
    "text_end",
    "text_capacity",
    "nominal_capacity",
    "aligned_capacity",
    "record_required_bytes",
    "jpn_text",
    "cn_text",
    "control_status",
    "capacity_status",
    "translation_status",
    "build_status",
    "ingame_status",
    "source_translation_file",
    "mapping_source",
    "mapping_commit",
    "review_flag",
)

CAPACITY_COLUMNS = (
    "resource_class",
    "file_id",
    "page",
    "tag_index",
    "payload_variant_index",
    "record_index",
    "segment_count",
    "header_size",
    "record_size",
    "aligned_size",
    "nominal_capacity",
    "aligned_capacity",
    "required",
    "over_nominal_bytes",
    "over_aligned_bytes",
    "status",
    "jpn_texts",
    "cn_texts",
)

WORKLIST_COLUMNS = (
    "work_id",
    "priority",
    "resource_class",
    "resource_id",
    "file_id",
    "jpn_object_count",
    "unique_jpn_text_count",
    "page_count",
    "payload_variant_count",
    "translation_status",
    "translated_unique_texts",
    "mapped_jpn_objects",
    "control_status",
    "capacity_status",
    "build_status",
    "ingame_status",
    "translation_file",
    "reference_statuses",
    "notes",
)

ANGLE_RE = re.compile(r"<[^<>]*>")
DOLLAR_RE = re.compile(r"\$[A-Za-z0-9_]+")
PRINTF_RE = re.compile(r"%(?:\d+\$)?[sdif]")


class CompileFailure(RuntimeError):
    pass


@dataclass
class CompiledFile:
    resource_class: str
    file_id: str
    rows: list[dict[str, str]]
    mapping_source: str
    mapping_commit: str
    preserved_build_status: str
    preserved_ingame_status: str
    capacity_status: str = "NOT_APPLICABLE"
    build_status: str = "READY"
    mapped_objects: int = 0


@dataclass(frozen=True)
class TrustedOverride:
    texts: dict[str, str]
    source: str
    build_status: str = "BUILT"
    ingame_status: str = "PASS"


def parse_args() -> argparse.Namespace:
    v2_root = Path(__file__).resolve().parents[1]
    default_repo = (
        v2_root.parent
        / "JPVoice_CNText_Experimental"
        / ".upload_staging_mgspw_v2_20260906_push"
    )
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--v2-root", type=Path, default=v2_root)
    parser.add_argument("--translation-repo", type=Path, default=default_repo)
    parser.add_argument("--write", action="store_true")
    return parser.parse_args()


def read_csv(path: Path) -> list[dict[str, str]]:
    with path.open("r", encoding="utf-8-sig", newline="") as handle:
        return list(csv.DictReader(handle))


def encode_csv(columns: Iterable[str], rows: Iterable[dict[str, Any]]) -> str:
    stream = io.StringIO(newline="")
    writer = csv.DictWriter(
        stream,
        fieldnames=list(columns),
        extrasaction="ignore",
        lineterminator="\r\n",
    )
    writer.writeheader()
    writer.writerows(rows)
    return "\ufeff" + stream.getvalue()


def atomic_write_text(path: Path, text: str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    temporary = path.with_name(path.name + ".tmp")
    with temporary.open("w", encoding="utf-8", newline="") as handle:
        handle.write(text)
    temporary.replace(path)


def load_module(path: Path, name: str):
    spec = importlib.util.spec_from_file_location(name, path)
    if spec is None or spec.loader is None:
        raise CompileFailure(f"cannot load module: {path}")
    module = importlib.util.module_from_spec(spec)
    sys.modules[name] = module
    spec.loader.exec_module(module)
    return module


def sha256_identity(rows: Iterable[tuple[int, str]]) -> str:
    payload = json.dumps(list(rows), ensure_ascii=False, separators=(",", ":"))
    return hashlib.sha256(payload.encode("utf-8")).hexdigest()


def parse_index_rows(rows: list[dict[str, str]], label: str) -> dict[int, dict[str, str]]:
    result: dict[int, dict[str, str]] = {}
    for ordinal, row in enumerate(rows):
        try:
            index = int(row.get("unique_index", ""))
        except ValueError as exc:
            raise CompileFailure(f"{label}: invalid unique_index at CSV row {ordinal + 2}") from exc
        if index in result:
            raise CompileFailure(f"{label}: duplicate unique_index {index}")
        result[index] = row
    expected = set(range(len(rows)))
    if set(result) != expected:
        raise CompileFailure(f"{label}: indices are not contiguous 0..{len(rows) - 1}")
    return result


def all_tokens(text: str) -> list[str]:
    spans: list[tuple[int, str]] = []
    for pattern in (ANGLE_RE, DOLLAR_RE, PRINTF_RE):
        spans.extend((match.start(), match.group(0)) for match in pattern.finditer(text))
    return [token for _, token in sorted(spans)]


def angle_control_signature(text: str) -> list[str]:
    signature: list[str] = []
    for token in ANGLE_RE.findall(text):
        if token.startswith("<R="):
            payload = token[3:-1]
            if "," not in payload:
                signature.append("INVALID_RUBY")
            else:
                signature.append("RUBY")
        elif token.startswith("<I=") or token.startswith("<C=") or token == "<->":
            signature.append(token)
        elif re.match(r"<[A-Za-z_-]+(?:=|>)", token):
            signature.append(token)
        # Human-readable angle-bracket titles such as <HUNTING QUEST: ...>
        # are text, not runtime control tokens, and may be localized.
    return signature


def control_error(jpn_text: str, cn_text: str) -> str:
    jpn_signature = angle_control_signature(jpn_text)
    cn_signature = angle_control_signature(cn_text)
    if jpn_signature != cn_signature:
        return f"angle control mismatch: {jpn_signature!r} != {cn_signature!r}"
    if Counter(DOLLAR_RE.findall(jpn_text)) != Counter(DOLLAR_RE.findall(cn_text)):
        return "dollar placeholder inventory mismatch"
    if Counter(PRINTF_RE.findall(jpn_text)) != Counter(PRINTF_RE.findall(cn_text)):
        return "printf placeholder inventory mismatch"
    return ""


def relative(path: Path, base: Path) -> str:
    return path.resolve().relative_to(base.resolve()).as_posix()


def load_existing_production(v2_root: Path, resource_class: str, file_id: str):
    path = v2_root / "translations" / PRODUCTION_DIRS[resource_class] / f"{file_id}.csv"
    if not path.is_file():
        return None
    rows = read_csv(path)
    try:
        by_index = parse_index_rows(rows, f"existing {resource_class}/{file_id}")
    except CompileFailure:
        return None
    return rows, by_index


def stable_status(rows: list[dict[str, str]], column: str, fallback: str) -> str:
    values = {row.get(column, "") for row in rows}
    return next(iter(values)) if len(values) == 1 and next(iter(values)) else fallback


def add_trusted_text(
    output: dict[str, str], jpn_text: str, cn_text: str, label: str
) -> None:
    if not jpn_text:
        return
    if jpn_text in output and output[jpn_text] != cn_text:
        raise CompileFailure(f"{label}: duplicate JPN text has conflicting golden translations")
    output[jpn_text] = cn_text


def load_trusted_overrides(v2_root: Path) -> dict[tuple[str, str], TrustedOverride]:
    overrides: dict[tuple[str, str], TrustedOverride] = {}

    gtt_json = v2_root / "translations" / "1C79F2AD_cn.json"
    gtt_master = v2_root / MASTER_PATHS["YPK_GTT"]
    gtt_golden = v2_root / "tests" / "fixtures" / "gtt_1C79F2AD" / "1C79F2AD_cn_golden.ypk"
    if not (gtt_json.is_file() and gtt_master.is_file() and gtt_golden.is_file()):
        raise CompileFailure("trusted 1C79F2AD translation/golden fixture is missing")
    data = json.loads(gtt_json.read_text(encoding="utf-8-sig"))
    if data.get("file_id") != "1C79F2AD" or not isinstance(data.get("records"), list):
        raise CompileFailure("trusted 1C79F2AD translation JSON has invalid identity")
    master_rows = [
        row for row in read_csv(gtt_master) if row.get("file_id", "").upper() == "1C79F2AD"
    ]
    grouped: dict[int, list[dict[str, str]]] = defaultdict(list)
    for row in master_rows:
        grouped[integer(row["record_index"])].append(row)
    if sorted(grouped) != list(range(len(data["records"]))):
        raise CompileFailure("trusted 1C79F2AD JSON/master record coverage mismatch")
    gtt_texts: dict[str, str] = {}
    for record_index, cn_segments in enumerate(data["records"]):
        jpn_segments = sorted(grouped[record_index], key=lambda row: integer(row["segment_index"]))
        if len(jpn_segments) != len(cn_segments):
            raise CompileFailure(
                f"trusted 1C79F2AD record {record_index}: segment count mismatch"
            )
        for source, cn_text in zip(jpn_segments, cn_segments):
            if not isinstance(cn_text, str) or not cn_text:
                raise CompileFailure(
                    f"trusted 1C79F2AD record {record_index}: empty/non-string segment"
                )
            add_trusted_text(gtt_texts, source["jpn_text"], cn_text, "1C79F2AD")
    overrides[("YPK_GTT", "1C79F2AD")] = TrustedOverride(
        texts=gtt_texts,
        source="translations/1C79F2AD_cn.json + tests/fixtures/gtt_1C79F2AD",
    )

    olang_fixture = v2_root / "tests" / "fixtures" / "olang_5D3AF52D"
    jpn_rbx = olang_fixture / "5D3AF52D_jpn_original.rbx"
    cn_rbx = olang_fixture / "5D3AF52D_cn_golden.rbx"
    if not (jpn_rbx.is_file() and cn_rbx.is_file()):
        raise CompileFailure("trusted 5D3AF52D golden fixture is missing")
    sys.path.insert(0, str(v2_root))
    from core.rbx import parse_rbx  # pylint: disable=import-outside-toplevel

    parsed_jpn = parse_rbx(jpn_rbx.read_bytes(), "5D3AF52D:jpn_golden")
    parsed_cn = parse_rbx(cn_rbx.read_bytes(), "5D3AF52D:cn_golden")
    if len(parsed_jpn.references) != len(parsed_cn.references):
        raise CompileFailure("trusted 5D3AF52D fixture reference count mismatch")
    olang_texts: dict[str, str] = {}
    for source, target in zip(parsed_jpn.references, parsed_cn.references):
        add_trusted_text(olang_texts, source.text, target.text, "5D3AF52D")
    overrides[("SLOT_OLANG", "5D3AF52D")] = TrustedOverride(
        texts=olang_texts,
        source="tests/fixtures/olang_5D3AF52D/5D3AF52D_cn_golden.rbx",
    )
    return overrides


def compile_files(
    v2_root: Path,
    repo: Path,
    state_module,
    audits,
    git_templates,
    trusted_overrides: dict[tuple[str, str], TrustedOverride],
) -> tuple[dict[tuple[str, str], CompiledFile], dict[str, int]]:
    local_root = v2_root / "work" / "luna_translation_templates"
    compiled: dict[tuple[str, str], CompiledFile] = {}
    counters: Counter[str] = Counter()

    for key in sorted(audits, key=lambda item: (RESOURCE_CLASSES.index(item[0]), item[1])):
        resource_class, file_id = key
        audit = audits[key]
        if not audit.complete or audit.canonical is None:
            raise CompileFailure(f"{resource_class}/{file_id}: no complete canonical mapping")
        if audit.errors:
            raise CompileFailure(f"{resource_class}/{file_id}: mapping audit errors: {audit.errors}")

        local_path = local_root / resource_class / f"{file_id}.csv"
        if not local_path.is_file():
            raise CompileFailure(f"missing clean V2 template: {local_path}")
        local_rows = read_csv(local_path)
        local_by_index = parse_index_rows(local_rows, f"local {resource_class}/{file_id}")
        local_fingerprint = sha256_identity(
            (index, local_by_index[index].get("jpn_text", ""))
            for index in sorted(local_by_index)
        )
        if local_fingerprint != git_templates[key].fingerprint:
            raise CompileFailure(f"{resource_class}/{file_id}: V2/Git template identity mismatch")

        mapped_by_index: dict[int, dict[str, Any]] = {}
        for item in audit.canonical.translations:
            index = int(item["unique_index"])
            if index in mapped_by_index:
                raise CompileFailure(f"{resource_class}/{file_id}: duplicate mapping index {index}")
            mapped_by_index[index] = item
        if set(mapped_by_index) != set(local_by_index):
            raise CompileFailure(f"{resource_class}/{file_id}: mapping coverage changed after audit")

        trusted = trusted_overrides.get(key)
        if trusted is not None:
            template_texts = {row.get("jpn_text", "") for row in local_rows}
            if set(trusted.texts) != template_texts:
                missing = sorted(template_texts - set(trusted.texts))
                extra = sorted(set(trusted.texts) - template_texts)
                raise CompileFailure(
                    f"{resource_class}/{file_id}: trusted golden/template text mismatch; "
                    f"missing={missing[:3]}, extra={extra[:3]}"
                )
            counters["trusted_ingame_files"] += 1

        existing = load_existing_production(v2_root, resource_class, file_id)
        existing_exact = False
        preserved_build = "READY"
        preserved_ingame = "NOT_TESTED"
        if existing is not None:
            existing_rows, existing_by_index = existing
            existing_exact = (
                set(existing_by_index) == set(local_by_index)
                and all(
                    existing_by_index[index].get("jpn_text", "")
                    == local_by_index[index].get("jpn_text", "")
                    and existing_by_index[index].get("cn_text", "")
                    == mapped_by_index[index].get("cn_text", "")
                    for index in local_by_index
                )
            )
            if existing_exact:
                preserved_build = stable_status(existing_rows, "build_status", "READY")
                preserved_ingame = stable_status(existing_rows, "ingame_status", "NOT_TESTED")
        if trusted is not None:
            preserved_build = trusted.build_status
            preserved_ingame = trusted.ingame_status

        output_rows: list[dict[str, str]] = []
        for index in sorted(local_by_index):
            source = local_by_index[index]
            mapping = mapped_by_index[index]
            jpn_text = source.get("jpn_text", "")
            cn_text = trusted.texts[jpn_text] if trusted is not None else mapping.get("cn_text")
            if not isinstance(cn_text, str):
                raise CompileFailure(f"{resource_class}/{file_id}:{index}: cn_text is not a string")
            if "\x00" in cn_text:
                raise CompileFailure(f"{resource_class}/{file_id}:{index}: cn_text contains NUL")
            if not cn_text:
                if jpn_text and not jpn_text.strip():
                    cn_text = jpn_text
                    counters["whitespace_only_source_preserved"] += 1
                else:
                    raise CompileFailure(f"{resource_class}/{file_id}:{index}: empty translation")
            cn_text.encode("utf-8", errors="strict")
            error = control_error(jpn_text, cn_text)
            if error:
                raise CompileFailure(f"{resource_class}/{file_id}:{index}: {error}")
            if jpn_text.count("\n") != cn_text.count("\n"):
                counters["newline_count_changed"] += 1
            if (
                len(jpn_text) - len(jpn_text.lstrip()) != len(cn_text) - len(cn_text.lstrip())
                or len(jpn_text) - len(jpn_text.rstrip()) != len(cn_text) - len(cn_text.rstrip())
            ):
                counters["edge_whitespace_changed"] += 1

            declared_bytes = mapping.get("cn_utf8_bytes")
            actual_bytes = len(cn_text.encode("utf-8"))
            if declared_bytes not in (None, ""):
                try:
                    if int(declared_bytes) != actual_bytes:
                        counters["cn_utf8_bytes_corrected"] += 1
                except (TypeError, ValueError):
                    counters["cn_utf8_bytes_corrected"] += 1

            review_flag = str(mapping.get("review_flag", "")).strip()
            if trusted is not None:
                review_flag = (
                    f"TRUSTED_INGAME_GOLDEN;{review_flag}"
                    if review_flag
                    else "TRUSTED_INGAME_GOLDEN"
                )
            notes = source.get("notes", "")
            if review_flag:
                notes = f"{notes}; review_flag={review_flag}" if notes else f"review_flag={review_flag}"
            row = {column: source.get(column, "") for column in PRODUCTION_COLUMNS}
            row.update(
                {
                    "cn_text": cn_text,
                    "cn_control_tokens": " | ".join(all_tokens(cn_text)),
                    "control_structure_status": "MATCH",
                    "cn_utf8_bytes": str(actual_bytes),
                    "translation_status": "APPROVED",
                    "build_status": preserved_build if (existing_exact or trusted is not None) else "READY",
                    "ingame_status": preserved_ingame if (existing_exact or trusted is not None) else "NOT_TESTED",
                    "notes": notes,
                }
            )
            output_rows.append(row)

        compiled[key] = CompiledFile(
            resource_class=resource_class,
            file_id=file_id,
            rows=output_rows,
            mapping_source=(trusted.source if trusted is not None else relative(audit.canonical.root_path, repo)),
            mapping_commit=audit.canonical.commit,
            preserved_build_status=(
                preserved_build if (existing_exact or trusted is not None) else "READY"
            ),
            preserved_ingame_status=(
                preserved_ingame if (existing_exact or trusted is not None) else "NOT_TESTED"
            ),
        )
        counters["files"] += 1
        counters["rows"] += len(output_rows)
        if audit.canonical.source_kind == "template_csv":
            counters["template_csv_canonical"] += 1
        if audit.canonical.root_path.name.endswith(".manifest.json"):
            counters["manifest_canonical"] += 1
        if any("legacy CSV column shift recovered" in warning for warning in audit.warnings):
            counters["legacy_shift_files_normalized"] += 1
            counters["legacy_shift_rows_normalized"] += sum(
                int(match.group(1))
                for warning in audit.warnings
                if (match := re.search(r"for (\d+) row", warning))
            )
    return compiled, dict(counters)


def translation_by_text(item: CompiledFile) -> dict[str, dict[str, str]]:
    result: dict[str, dict[str, str]] = {}
    for row in item.rows:
        text = row["jpn_text"]
        if text in result:
            raise CompileFailure(f"{item.resource_class}/{item.file_id}: duplicate JPN text in production rows")
        result[text] = row
    return result


def integer(value: str, default: int = 0) -> int:
    return int(str(value).strip()) if str(value).strip() else default


def object_type(resource_class: str) -> str:
    if resource_class == "YPK_GTT":
        return "timed_segment"
    if resource_class == "OHD":
        return "record"
    return "reference"


def object_index(resource_class: str, row: dict[str, str]) -> str:
    if resource_class == "YPK_GTT":
        return f"{row.get('record_index', '')}:{row.get('segment_index', '')}"
    if resource_class == "OHD":
        return row.get("record_index", "")
    return row.get("reference_index", "")


def capacity_key(resource_class: str, row: dict[str, str]):
    if resource_class == "YPK_GTT":
        return (row["file_id"].upper(), integer(row["record_index"]))
    if resource_class == "OHD":
        return (
            row["file_id"].upper(),
            row.get("page", ""),
            row.get("tag_index", ""),
            row.get("payload_variant_index", ""),
            integer(row["record_index"]),
        )
    return None


def build_capacity_audit(
    masters: dict[str, list[dict[str, str]]],
    compiled: dict[tuple[str, str], CompiledFile],
) -> tuple[dict[tuple[str, tuple], dict[str, Any]], list[dict[str, Any]], dict[str, int]]:
    results: dict[tuple[str, tuple], dict[str, Any]] = {}
    issues: list[dict[str, Any]] = []
    counters: Counter[str] = Counter()

    gtt_groups: dict[tuple, list[dict[str, str]]] = defaultdict(list)
    for row in masters["YPK_GTT"]:
        gtt_groups[capacity_key("YPK_GTT", row)].append(row)
    for key, rows in gtt_groups.items():
        rows.sort(key=lambda row: integer(row["segment_index"]))
        file_id, record_index = key
        expected = list(range(integer(rows[0]["segment_count"])))
        actual = [integer(row["segment_index"]) for row in rows]
        if actual != expected:
            raise CompileFailure(f"YPK_GTT/{file_id}: record {record_index} segment topology mismatch")
        layouts = {
            (
                row["segment_count"],
                row["header_size"],
                row["record_size"],
                row["aligned_size"],
            )
            for row in rows
        }
        if len(layouts) != 1:
            raise CompileFailure(f"YPK_GTT/{file_id}: record {record_index} layout fields disagree")
        translations = translation_by_text(compiled[("YPK_GTT", file_id)])
        cn_texts = [translations[row["jpn_text"]]["cn_text"] for row in rows]
        required = sum(len(text.encode("utf-8")) + 1 for text in cn_texts)
        header_size = integer(rows[0]["header_size"])
        record_size = integer(rows[0]["record_size"])
        aligned_size = integer(rows[0]["aligned_size"])
        nominal = record_size - header_size
        aligned = aligned_size - header_size
        if required > aligned:
            status = "HARD_OVERFLOW"
        elif required > nominal:
            status = "ALIGNMENT_SPILL"
        else:
            status = "NORMAL_FIT"
        result = {
            "resource_class": "YPK_GTT",
            "file_id": file_id,
            "page": "",
            "tag_index": "",
            "payload_variant_index": "",
            "record_index": record_index,
            "segment_count": integer(rows[0]["segment_count"]),
            "header_size": header_size,
            "record_size": record_size,
            "aligned_size": aligned_size,
            "nominal_capacity": nominal,
            "aligned_capacity": aligned,
            "required": required,
            "over_nominal_bytes": max(0, required - nominal),
            "over_aligned_bytes": max(0, required - aligned),
            "status": status,
            "jpn_texts": json.dumps([row["jpn_text"] for row in rows], ensure_ascii=False),
            "cn_texts": json.dumps(cn_texts, ensure_ascii=False),
        }
        results[("YPK_GTT", key)] = result
        counters[f"gtt_{status.lower()}"] += 1
        if status != "NORMAL_FIT":
            issues.append(result)

    for row in masters["OHD"]:
        file_id = row["file_id"].upper()
        key = capacity_key("OHD", row)
        translations = translation_by_text(compiled[("OHD", file_id)])
        cn_text = translations[row["jpn_text"]]["cn_text"]
        required = len(cn_text.encode("utf-8")) + 1
        capacity = integer(row["text_capacity"])
        status = "HARD_OVERFLOW" if required > capacity else "NORMAL_FIT"
        result = {
            "resource_class": "OHD",
            "file_id": file_id,
            "page": row.get("page", ""),
            "tag_index": row.get("tag_index", ""),
            "payload_variant_index": row.get("payload_variant_index", ""),
            "record_index": row.get("record_index", ""),
            "segment_count": "",
            "header_size": "",
            "record_size": row.get("record_size", ""),
            "aligned_size": row.get("record_size", ""),
            "nominal_capacity": capacity,
            "aligned_capacity": capacity,
            "required": required,
            "over_nominal_bytes": max(0, required - capacity),
            "over_aligned_bytes": max(0, required - capacity),
            "status": status,
            "jpn_texts": json.dumps([row["jpn_text"]], ensure_ascii=False),
            "cn_texts": json.dumps([cn_text], ensure_ascii=False),
        }
        results[("OHD", key)] = result
        counters[f"ohd_{status.lower()}"] += 1
        if status != "NORMAL_FIT":
            issues.append(result)
    return results, issues, dict(counters)


def file_capacity_status(
    resource_class: str,
    file_id: str,
    capacity_results: dict[tuple[str, tuple], dict[str, Any]],
) -> str:
    statuses = {
        result["status"]
        for (result_class, _), result in capacity_results.items()
        if result_class == resource_class and result["file_id"] == file_id
    }
    if not statuses:
        return "NOT_APPLICABLE"
    if "HARD_OVERFLOW" in statuses:
        return "HARD_OVERFLOW"
    if "ALIGNMENT_SPILL" in statuses:
        return "ALIGNMENT_SPILL"
    return "NORMAL_FIT"


def build_manifest(
    v2_root: Path,
    masters: dict[str, list[dict[str, str]]],
    compiled: dict[tuple[str, str], CompiledFile],
    capacity_results: dict[tuple[str, tuple], dict[str, Any]],
) -> tuple[list[dict[str, Any]], dict[str, int]]:
    rows: list[dict[str, Any]] = []
    counters: Counter[str] = Counter()
    by_text = {key: translation_by_text(item) for key, item in compiled.items()}

    for resource_class in RESOURCE_CLASSES:
        for master in masters[resource_class]:
            file_id = master.get("file_id", "").upper()
            jpn_text = master.get("jpn_text", "")
            if not jpn_text:
                counters[f"{resource_class}_empty_master_objects_skipped"] += 1
                continue
            key = (resource_class, file_id)
            if key not in compiled:
                raise CompileFailure(f"{resource_class}/{file_id}: master has no compiled file")
            translation = by_text[key].get(jpn_text)
            if translation is None:
                raise CompileFailure(f"{resource_class}/{file_id}: master JPN text has no translation")
            item = compiled[key]
            capacity = capacity_results.get((resource_class, capacity_key(resource_class, master)))
            capacity_status = capacity["status"] if capacity else "NOT_APPLICABLE"
            review_flag = ""
            marker = "review_flag="
            if marker in translation.get("notes", ""):
                review_flag = translation["notes"].split(marker, 1)[1]
            row: dict[str, Any] = {column: master.get(column, "") for column in MANIFEST_COLUMNS}
            row.update(
                {
                    "resource_class": resource_class,
                    "resource_id": file_id,
                    "file_id": file_id,
                    "object_type": object_type(resource_class),
                    "object_index": object_index(resource_class, master),
                    "nominal_capacity": capacity["nominal_capacity"] if capacity else "",
                    "aligned_capacity": capacity["aligned_capacity"] if capacity else "",
                    "record_required_bytes": capacity["required"] if capacity else "",
                    "jpn_text": jpn_text,
                    "cn_text": translation["cn_text"],
                    "control_status": "MATCH",
                    "capacity_status": capacity_status,
                    "translation_status": "APPROVED",
                    "build_status": item.build_status,
                    "ingame_status": item.preserved_ingame_status,
                    "source_translation_file": (
                        f"translations/{PRODUCTION_DIRS[resource_class]}/{file_id}.csv"
                    ),
                    "mapping_source": item.mapping_source,
                    "mapping_commit": item.mapping_commit,
                    "review_flag": review_flag,
                }
            )
            rows.append(row)
            counters[resource_class] += 1
            item.mapped_objects += 1
    return rows, dict(counters)


def update_file_statuses(
    compiled: dict[tuple[str, str], CompiledFile],
    capacity_results: dict[tuple[str, tuple], dict[str, Any]],
) -> None:
    for key, item in compiled.items():
        item.capacity_status = file_capacity_status(
            item.resource_class, item.file_id, capacity_results
        )
        if item.capacity_status == "HARD_OVERFLOW":
            item.build_status = "BLOCKED_CAPACITY"
        else:
            item.build_status = item.preserved_build_status
        for row in item.rows:
            row["build_status"] = item.build_status


def update_worklist(
    v2_root: Path,
    compiled: dict[tuple[str, str], CompiledFile],
) -> list[dict[str, Any]]:
    source_path = v2_root / "build" / "translation" / "translation_worklist.csv"
    source_rows = read_csv(source_path)
    output: list[dict[str, Any]] = []
    seen: set[tuple[str, str]] = set()
    for source in source_rows:
        key = (source["resource_class"], source["file_id"])
        if key not in compiled:
            raise CompileFailure(f"worklist has no compiled translation: {key}")
        item = compiled[key]
        row = {column: source.get(column, "") for column in WORKLIST_COLUMNS}
        row.update(
            {
                "translation_status": "APPROVED",
                "translated_unique_texts": len(item.rows),
                "mapped_jpn_objects": item.mapped_objects,
                "control_status": "MATCH",
                "capacity_status": item.capacity_status,
                "build_status": item.build_status,
                "ingame_status": item.preserved_ingame_status,
                "translation_file": (
                    f"translations/{PRODUCTION_DIRS[item.resource_class]}/{item.file_id}.csv"
                ),
            }
        )
        output.append(row)
        seen.add(key)
    if seen != set(compiled):
        missing = sorted(set(compiled) - seen)
        raise CompileFailure(f"compiled translations missing from worklist: {missing}")
    return output


def git_head(repo: Path) -> str:
    return subprocess.check_output(
        ["git", "rev-parse", "HEAD"], cwd=repo, text=True, encoding="utf-8"
    ).strip()


def main() -> int:
    args = parse_args()
    v2_root = args.v2_root.resolve()
    repo = args.translation_repo.resolve()
    template_root = repo / "work" / "luna_translation_templates"
    mapping_root = template_root / "sol_translation_mappings"
    state_path = template_root / "tools" / "rebuild_translation_state.py"
    if not state_path.is_file():
        raise CompileFailure(f"missing translation state tool: {state_path}")

    state = load_module(state_path, "production_translation_state")
    git_templates, template_errors = state.load_templates(template_root)
    if template_errors:
        raise CompileFailure("translation template errors: " + "; ".join(template_errors))
    git = state.load_git_facts(repo, template_root, mapping_root)
    if git.branch != "sol-translation":
        raise CompileFailure(f"translation repository is on {git.branch}, expected sol-translation")
    if git.dirty_paths:
        raise CompileFailure(f"translation repository is dirty: {sorted(git.dirty_paths)}")
    audits = {
        key: state.audit_file(git, template_root, mapping_root, template)
        for key, template in git_templates.items()
    }
    incomplete = [key for key, audit in audits.items() if not audit.complete]
    audit_errors = [
        f"{key}: {error}"
        for key, audit in audits.items()
        for error in audit.errors
    ]
    if incomplete or audit_errors:
        raise CompileFailure(f"translation state is not complete: incomplete={incomplete}; errors={audit_errors}")

    trusted_overrides = load_trusted_overrides(v2_root)
    compiled, compile_counts = compile_files(
        v2_root, repo, state, audits, git_templates, trusted_overrides
    )
    if len(compiled) != 241 or compile_counts.get("rows") != 21041:
        raise CompileFailure(
            f"unexpected compiled scope: files={len(compiled)}, rows={compile_counts.get('rows')}"
        )

    masters = {
        resource_class: read_csv(v2_root / relative_path)
        for resource_class, relative_path in MASTER_PATHS.items()
    }
    capacity_results, capacity_issues, capacity_counts = build_capacity_audit(
        masters, compiled
    )
    update_file_statuses(compiled, capacity_results)
    manifest_rows, manifest_counts = build_manifest(
        v2_root, masters, compiled, capacity_results
    )
    worklist_rows = update_worklist(v2_root, compiled)

    hard_overflow_records = capacity_counts.get("gtt_hard_overflow", 0) + capacity_counts.get(
        "ohd_hard_overflow", 0
    )
    report = {
        "status": "BLOCKED_CAPACITY" if hard_overflow_records else "PASS",
        "translation_repo": str(repo),
        "translation_branch": git.branch,
        "translation_checkpoint": git_head(repo),
        "production_files": len(compiled),
        "production_unique_rows": compile_counts["rows"],
        "compiled_manifest_rows": len(manifest_rows),
        "manifest_rows_by_resource_class": manifest_counts,
        "mapping_normalization": compile_counts,
        "fixed_capacity": capacity_counts,
        "hard_overflow_records": hard_overflow_records,
        "control_errors": 0,
        "build_ready": hard_overflow_records == 0,
        "container_roundtrip_pending": True,
        "notes": [
            "Newline and edge-whitespace changes are counted for review but are not treated as runtime control tokens.",
            "Whitespace-only JPN source rows are preserved byte-for-byte when an older mapping stored an empty cn_text.",
            "No DAT/KEY was built or modified by this compiler.",
        ],
    }

    outputs: dict[Path, str] = {}
    for item in compiled.values():
        path = (
            v2_root
            / "translations"
            / PRODUCTION_DIRS[item.resource_class]
            / f"{item.file_id}.csv"
        )
        outputs[path] = encode_csv(PRODUCTION_COLUMNS, item.rows)
    outputs[v2_root / "build" / "translation" / "compiled_translation_manifest.csv"] = encode_csv(
        MANIFEST_COLUMNS, manifest_rows
    )
    outputs[v2_root / "build" / "translation" / "translation_worklist.csv"] = encode_csv(
        WORKLIST_COLUMNS, worklist_rows
    )
    outputs[v2_root / "build" / "translation" / "fixed_capacity_issues.csv"] = encode_csv(
        CAPACITY_COLUMNS, capacity_issues
    )
    outputs[v2_root / "build" / "translation" / "production_merge_report.json"] = (
        json.dumps(report, ensure_ascii=False, indent=2) + "\n"
    )

    if args.write:
        for path, text in outputs.items():
            atomic_write_text(path, text)

    print(f"MODE={'WRITE' if args.write else 'DRY_RUN'}")
    print(f"PRODUCTION_FILES={len(compiled)}")
    print(f"PRODUCTION_UNIQUE_ROWS={compile_counts['rows']}")
    print(f"COMPILED_MANIFEST_ROWS={len(manifest_rows)}")
    print(f"CONTROL_ERRORS=0")
    print(f"GTT_NORMAL_FIT={capacity_counts.get('gtt_normal_fit', 0)}")
    print(f"GTT_ALIGNMENT_SPILL={capacity_counts.get('gtt_alignment_spill', 0)}")
    print(f"GTT_HARD_OVERFLOW={capacity_counts.get('gtt_hard_overflow', 0)}")
    print(f"OHD_NORMAL_FIT={capacity_counts.get('ohd_normal_fit', 0)}")
    print(f"OHD_HARD_OVERFLOW={capacity_counts.get('ohd_hard_overflow', 0)}")
    print(f"LEGACY_SHIFT_ROWS_NORMALIZED={compile_counts.get('legacy_shift_rows_normalized', 0)}")
    print(f"UTF8_LENGTH_FIELDS_CORRECTED={compile_counts.get('cn_utf8_bytes_corrected', 0)}")
    print(f"WHITESPACE_ONLY_ROWS_PRESERVED={compile_counts.get('whitespace_only_source_preserved', 0)}")
    print(f"BUILD_READY={int(report['build_ready'])}")
    print(f"REPORT={v2_root / 'build' / 'translation' / 'production_merge_report.json'}")
    return 0


if __name__ == "__main__":
    try:
        raise SystemExit(main())
    except CompileFailure as error:
        print(f"ERROR={error}", file=sys.stderr)
        raise SystemExit(1)
