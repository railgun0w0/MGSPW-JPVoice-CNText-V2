#!/usr/bin/env python3
"""Extract reliable JPN text objects into JSONL rows for the CSV builder.

This inventory intentionally uses only the already validated SLOT/CNF, RBX,
OHD, loose OLANG, DAR, and STAGEDAT parsers.  It does not scan unknown payloads
for strings and it does not modify any game file.
"""

from __future__ import annotations

import argparse
import hashlib
import importlib.util
import json
import re
import sys
from collections import Counter, defaultdict
from pathlib import Path


JAPANESE_KEY = 0x00000DB0
OLANG_KIND = 0x5D
OHD_KIND = 0x1E
CONTROL_RE = re.compile(r"<[^<>]*>|\$[A-Za-z0-9_]+")


def load_module(path: Path, name: str):
    spec = importlib.util.spec_from_file_location(name, path)
    if spec is None or spec.loader is None:
        raise RuntimeError(f"cannot load helper module: {path}")
    module = importlib.util.module_from_spec(spec)
    sys.modules[name] = module
    spec.loader.exec_module(module)
    return module


def hex32(value: int) -> str:
    return f"{value:08X}"


def text_group_id(text: str) -> str:
    return "TXT_" + hashlib.sha256(text.encode("utf-8")).hexdigest()[:16].upper()


def controls(text: str) -> str:
    return json.dumps(CONTROL_RE.findall(text), ensure_ascii=False, separators=(",", ":"))


def write_jsonl(path: Path, rows: list[dict]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", encoding="utf-8", newline="\n") as stream:
        for row in rows:
            stream.write(json.dumps(row, ensure_ascii=False, separators=(",", ":")) + "\n")


def entity_reference_info(parsed) -> dict[int, tuple[int, int, int]]:
    """Map reference index to entity index, duplicate-key ordinal, local ordinal."""
    result: dict[int, tuple[int, int, int]] = {}
    key_counts: Counter[int] = Counter()
    for entity_index, entity in enumerate(parsed.entities):
        key_occurrence = key_counts[entity.key]
        key_counts[entity.key] += 1
        for local_ordinal in range(entity.reference_count):
            reference_index = entity.reference_index + local_ordinal
            result.setdefault(reference_index, (entity_index, key_occurrence, local_ordinal))
    return result


def rbx_rows(
    parsed,
    *,
    resource_type: str,
    container: str,
    file_id: str,
    payload_variant_index: int,
    occurrence_count: int,
    occurrence_locations: str,
    page: int | str = "",
    page_entry_start: int | str = "",
    page_entry_capacity: int | str = "",
    tag_index: int | str = "",
    archive_entry_index: int | str = "",
    archive_entry_name: str = "",
) -> tuple[list[dict], int, int]:
    owners = entity_reference_info(parsed)
    rows: list[dict] = []
    japanese_references = 0
    empty_references = 0
    for reference_index, reference in enumerate(parsed.references):
        if reference.language_key != JAPANESE_KEY:
            continue
        japanese_references += 1
        if not reference.text:
            empty_references += 1
            continue
        owner = owners.get(reference_index)
        entity_index = owner[0] if owner else ""
        key_occurrence = owner[1] if owner else ""
        local_ordinal = owner[2] if owner else ""
        entity_key = parsed.entities[entity_index].key if owner else ""
        encoded = reference.text.encode("utf-8")
        rows.append(
            {
                "resource_type": resource_type,
                "container": container,
                "page": page,
                "page_entry_start": page_entry_start,
                "page_entry_capacity": page_entry_capacity,
                "tag_index": tag_index,
                "file_id": file_id,
                "payload_variant_index": payload_variant_index,
                "occurrence_count": occurrence_count,
                "occurrence_locations": occurrence_locations,
                "archive_entry_index": archive_entry_index,
                "archive_entry_name": archive_entry_name,
                "entity_index": entity_index,
                "entity_key": hex32(entity_key) if isinstance(entity_key, int) else "",
                "entity_key_occurrence": key_occurrence,
                "reference_index": reference_index,
                "ordinal_in_entity": local_ordinal,
                "language_key": hex32(reference.language_key),
                "style": f"0x{reference.flag:08X}",
                "body_relative_offset": reference.body_offset,
                "text_absolute_offset": parsed.body_offset + reference.body_offset,
                "text_encoding": "UTF-8",
                "text_byte_length": len(encoded),
                "terminator_present": True,
                "text_group_id": text_group_id(reference.text),
                "control_tokens": controls(reference.text),
                "jpn_text": reference.text,
                "mlg_cn_reference": "",
                "eng_reference": "",
                "cn_text": "",
            }
        )
    return rows, japanese_references, empty_references


def extract_loose(jpn_root: Path, rbx, loose) -> tuple[list[dict], dict, list[dict]]:
    rows: list[dict] = []
    errors: list[dict] = []
    total_refs = japanese_refs = empty_refs = 0
    text_dir = jpn_root / "Text"
    files = sorted(text_dir.glob("*.olang"), key=lambda path: path.name.casefold())
    for path in files:
        try:
            parsed = rbx.parse_rbx(loose.decrypt(path), f"loose:{path.name}")
            parsed_rows, ja_count, empty_count = rbx_rows(
                parsed,
                resource_type="LOOSE_OLANG",
                container=f"JPN/Text/{path.name}",
                file_id=path.stem.upper(),
                payload_variant_index=0,
                occurrence_count=1,
                occurrence_locations=path.name,
            )
            rows.extend(parsed_rows)
            total_refs += len(parsed.references)
            japanese_refs += ja_count
            empty_refs += empty_count
        except Exception as error:
            errors.append({"scope": "loose_olang", "file": path.name, "error": str(error)})
    return rows, {
        "physical_resources": len(files),
        "unique_payloads": len(files) - len(errors),
        "total_parser_objects": total_refs,
        "japanese_objects": japanese_refs,
        "empty_japanese_objects_excluded": empty_refs,
        "rows": len(rows),
        "parse_errors": len(errors),
    }, errors


def extract_slot(
    dat_path: Path, key_path: Path, slot, rbx, voice
) -> tuple[list[dict], list[dict], dict, dict, list[dict]]:
    olang_occurrences: dict[int, list[dict]] = defaultdict(list)
    ohd_occurrences: dict[int, list[dict]] = defaultdict(list)
    errors: list[dict] = []
    seed = slot.CRYPTO.filename_seed(key_path)
    _, salts, entries = slot.decode_key(key_path, seed)
    decoded_pages = 0
    for page_index, entry in enumerate(entries):
        try:
            raw, _ = slot.decode_page(dat_path, entry, salts, seed)
            cnf = slot.parse_cnf(raw)
            decoded_pages += 1
        except Exception as error:
            errors.append({"scope": "slot_page", "page": page_index, "error": str(error)})
            continue
        for tag_index, segment in cnf.segments.items():
            tag = cnf.tags[tag_index]
            item = {
                "page": page_index,
                "tag_index": tag_index,
                "file_id": tag.file_id,
                "segment": segment,
                "entry_start": entry.start,
                "entry_capacity": entry.capacity,
            }
            if tag.kind == OLANG_KIND:
                olang_occurrences[tag.file_id].append(item)
            elif tag.kind == OHD_KIND and page_index % 6 == 4:
                ohd_occurrences[tag.file_id].append(item)
        if (page_index + 1) % 200 == 0:
            print(f"SLOT_PROGRESS={page_index + 1}/{len(entries)}", flush=True)

    slot_rows: list[dict] = []
    slot_total_refs = slot_ja_refs = slot_empty_refs = 0
    slot_variants = 0
    slot_physical = sum(len(items) for items in olang_occurrences.values())
    for file_id in sorted(olang_occurrences):
        variants: dict[bytes, list[dict]] = defaultdict(list)
        for occurrence in olang_occurrences[file_id]:
            variants[occurrence["segment"]].append(occurrence)
        ordered = sorted(variants.items(), key=lambda pair: (pair[1][0]["page"], pair[1][0]["tag_index"]))
        for variant_index, (payload, occurrences) in enumerate(ordered):
            first = occurrences[0]
            label = f"slot:{first['page']}:{first['tag_index']}:{file_id:08X}"
            try:
                parsed = rbx.parse_rbx(payload, label)
            except Exception as error:
                errors.append(
                    {
                        "scope": "slot_olang",
                        "page": first["page"],
                        "tag_index": first["tag_index"],
                        "file_id": hex32(file_id),
                        "error": str(error),
                    }
                )
                continue
            locations = ";".join(f"{item['page']}:{item['tag_index']}" for item in occurrences)
            parsed_rows, ja_count, empty_count = rbx_rows(
                parsed,
                resource_type="SLOT_OLANG",
                container="JPN/disc0_rel/002aba34.DAT",
                page=first["page"],
                page_entry_start=first["entry_start"],
                page_entry_capacity=first["entry_capacity"],
                tag_index=first["tag_index"],
                file_id=hex32(file_id),
                payload_variant_index=variant_index,
                occurrence_count=len(occurrences),
                occurrence_locations=locations,
            )
            if ja_count:
                slot_variants += 1
                slot_rows.extend(parsed_rows)
                slot_total_refs += len(parsed.references)
                slot_ja_refs += ja_count
                slot_empty_refs += empty_count

    ohd_rows: list[dict] = []
    ohd_variants = 0
    ohd_physical = sum(len(items) for items in ohd_occurrences.values())
    ohd_parser_objects = 0
    for file_id in sorted(ohd_occurrences):
        variants: dict[bytes, list[dict]] = defaultdict(list)
        for occurrence in ohd_occurrences[file_id]:
            variants[occurrence["segment"]].append(occurrence)
        ordered = sorted(variants.items(), key=lambda pair: (pair[1][0]["page"], pair[1][0]["tag_index"]))
        for variant_index, (payload, occurrences) in enumerate(ordered):
            first = occurrences[0]
            label = f"ohd:{first['page']}:{first['tag_index']}:{file_id:08X}"
            try:
                header, records = voice.parse_ohd(payload, label)
            except Exception as error:
                errors.append(
                    {
                        "scope": "slot_ohd",
                        "page": first["page"],
                        "tag_index": first["tag_index"],
                        "file_id": hex32(file_id),
                        "error": str(error),
                    }
                )
                continue
            ohd_variants += 1
            ohd_parser_objects += len(records)
            locations = ";".join(f"{item['page']}:{item['tag_index']}" for item in occurrences)
            for record_index, record in enumerate(records):
                field = record[voice.OHD_TEXT_OFFSET :]
                nul = field.find(b"\0")
                text_bytes = field if nul < 0 else field[:nul]
                try:
                    text = text_bytes.decode("utf-8", errors="strict")
                except UnicodeDecodeError as error:
                    errors.append(
                        {
                            "scope": "slot_ohd_record",
                            "file_id": hex32(file_id),
                            "record_index": record_index,
                            "error": str(error),
                        }
                    )
                    continue
                ohd_rows.append(
                    {
                        "resource_type": "OHD",
                        "container": "JPN/disc0_rel/002aba34.DAT",
                        "page": first["page"],
                        "page_entry_start": first["entry_start"],
                        "page_entry_capacity": first["entry_capacity"],
                        "tag_index": first["tag_index"],
                        "file_id": hex32(file_id),
                        "payload_variant_index": variant_index,
                        "occurrence_count": len(occurrences),
                        "occurrence_locations": locations,
                        "record_index": record_index,
                        "record_offset": voice.OHD_HEADER_SIZE + record_index * voice.OHD_RECORD_SIZE,
                        "record_size": voice.OHD_RECORD_SIZE,
                        "metadata_hex": record[: voice.OHD_TEXT_OFFSET].hex().upper(),
                        "text_offset_in_record": voice.OHD_TEXT_OFFSET,
                        "text_capacity": voice.OHD_RECORD_SIZE - voice.OHD_TEXT_OFFSET,
                        "text_encoding": "UTF-8",
                        "text_byte_length": len(text_bytes),
                        "terminator_present": nul >= 0,
                        "text_group_id": text_group_id(text),
                        "control_tokens": controls(text),
                        "jpn_text": text,
                        "mlg_cn_reference": "",
                        "eng_reference": "",
                        "cn_text": "",
                    }
                )

    slot_stats = {
        "pages": len(entries),
        "pages_decoded": decoded_pages,
        "physical_resources": slot_physical,
        "unique_payloads": slot_variants,
        "total_parser_objects": slot_total_refs,
        "japanese_objects": slot_ja_refs,
        "empty_japanese_objects_excluded": slot_empty_refs,
        "rows": len(slot_rows),
        "parse_errors": sum(error["scope"].startswith("slot_") and "ohd" not in error["scope"] for error in errors),
    }
    ohd_stats = {
        "physical_resources": ohd_physical,
        "unique_payloads": ohd_variants,
        "total_parser_objects": ohd_parser_objects,
        "japanese_objects": len(ohd_rows),
        "empty_japanese_objects_excluded": sum(not row["jpn_text"] for row in ohd_rows),
        "rows": len(ohd_rows),
        "parse_errors": sum("ohd" in error["scope"] for error in errors),
    }
    return slot_rows, ohd_rows, slot_stats, ohd_stats, errors


def extract_stagedat(stage_path: Path, stage, rbx) -> tuple[list[dict], dict, list[dict]]:
    rows: list[dict] = []
    errors: list[dict] = []
    page_count = decoded_pages = dar_pages = dar_entries = rbx_resources = 0
    total_refs = japanese_refs = empty_refs = 0
    seed = stage.filename_seed(stage_path)
    with stage_path.open("rb") as stream:
        header = stage.decode_header(stream, seed)
        entries, _ = stage.decode_table(stream, seed, header)
        page_count = len(entries)
        for page_index, entry in enumerate(entries):
            try:
                data = stage.decode_page(stream, seed, header, entry)
                decoded_pages += 1
            except Exception as error:
                errors.append({"scope": "stagedat_page", "page": page_index, "error": str(error)})
                continue
            try:
                archive_entries = rbx.parse_dar(data)
            except Exception:
                archive_entries = []
            if archive_entries:
                dar_pages += 1
                dar_entries += len(archive_entries)
            for archive_entry_index, archive_entry in enumerate(archive_entries):
                if not archive_entry.data.startswith(b"RBX\0"):
                    continue
                try:
                    parsed = rbx.parse_rbx(
                        archive_entry.data,
                        f"stagedat:{page_index}:{archive_entry.name}",
                    )
                except Exception as error:
                    errors.append(
                        {
                            "scope": "stagedat_rbx",
                            "page": page_index,
                            "archive_entry_index": archive_entry_index,
                            "archive_entry_name": archive_entry.name,
                            "error": str(error),
                        }
                    )
                    continue
                parsed_rows, ja_count, empty_count = rbx_rows(
                    parsed,
                    resource_type="STAGEDAT_OLANG",
                    container="JPN/disc0_rel/009645fa.PDT",
                    page=page_index,
                    file_id=archive_entry.name,
                    payload_variant_index=0,
                    occurrence_count=1,
                    occurrence_locations=f"{page_index}:{archive_entry_index}:{archive_entry.name}",
                    archive_entry_index=archive_entry_index,
                    archive_entry_name=archive_entry.name,
                )
                if ja_count:
                    rbx_resources += 1
                    rows.extend(parsed_rows)
                    total_refs += len(parsed.references)
                    japanese_refs += ja_count
                    empty_refs += empty_count
            if (page_index + 1) % 50 == 0:
                print(f"STAGEDAT_PROGRESS={page_index + 1}/{len(entries)}", flush=True)
    return rows, {
        "pages": page_count,
        "pages_decoded": decoded_pages,
        "dar_pages": dar_pages,
        "dar_entries": dar_entries,
        "physical_resources": rbx_resources,
        "unique_payloads": rbx_resources,
        "total_parser_objects": total_refs,
        "japanese_objects": japanese_refs,
        "empty_japanese_objects_excluded": empty_refs,
        "rows": len(rows),
        "parse_errors": len(errors),
    }, errors


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    v2_root = Path(__file__).resolve().parents[1]
    project_parent = v2_root.parent
    parser.add_argument("--jpn-root", type=Path, default=Path(r"D:\GAME\test\JPN\MGS_PW\mgspw\JPN"))
    parser.add_argument("--legacy-tools", type=Path, default=project_parent / "JPVoice_CNText_Experimental" / "tools")
    parser.add_argument("--work-dir", type=Path, default=v2_root / "work" / "text_master_rows")
    parser.add_argument("--only", choices=("all", "loose"), default="all")
    args = parser.parse_args()

    jpn_root = args.jpn_root.resolve()
    dat_path = jpn_root / "disc0_rel" / "002aba34.DAT"
    key_path = jpn_root / "disc0_rel" / "002aba34.KEY"
    stage_path = jpn_root / "disc0_rel" / "009645fa.PDT"
    for path in (jpn_root, dat_path, key_path, stage_path, args.legacy_tools):
        if not path.exists():
            raise FileNotFoundError(path)

    slot = load_module(args.legacy_tools / "Build-JpnSlot.py", "v2_master_slot")
    rbx = load_module(args.legacy_tools / "Build-JpnInitCache.py", "v2_master_rbx")
    loose = load_module(args.legacy_tools / "Build-JpnLooseOlang.py", "v2_master_loose")
    voice = load_module(args.legacy_tools / "Build-JpnSlotNativeVoiceText.py", "v2_master_ohd")
    stage = load_module(args.legacy_tools / "Patch-StageDatPage.py", "v2_master_stage")

    args.work_dir.mkdir(parents=True, exist_ok=True)
    print("PHASE=LOOSE_OLANG", flush=True)
    loose_rows, loose_stats, loose_errors = extract_loose(jpn_root, rbx, loose)
    if args.only == "loose":
        loose_path = args.work_dir / "jpn_loose_olang_rows.jsonl"
        write_jsonl(loose_path, loose_rows)
        stats_path = args.work_dir / "extraction_stats.json"
        stats = json.loads(stats_path.read_text(encoding="utf-8"))
        stats["loose_olang"] = loose_stats
        existing_errors = [error for error in stats.get("errors", []) if error.get("scope") != "loose_olang"]
        stats["errors"] = existing_errors + loose_errors
        stats["error_count"] = len(stats["errors"])
        stats["row_files"]["loose_olang"] = str(loose_path.resolve())
        stats_path.write_text(json.dumps(stats, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
        print(f"LOOSE_OLANG_ROWS={len(loose_rows)}")
        print(f"PARSE_ERRORS={len(loose_errors)}")
        print(f"STATS_PATH={stats_path.resolve()}")
        return 0
    print("PHASE=SLOT", flush=True)
    slot_rows, ohd_rows, slot_stats, ohd_stats, slot_errors = extract_slot(
        dat_path, key_path, slot, rbx, voice
    )
    print("PHASE=STAGEDAT", flush=True)
    stage_rows, stage_stats, stage_errors = extract_stagedat(stage_path, stage, rbx)

    outputs = {
        "ohd": args.work_dir / "jpn_ohd_rows.jsonl",
        "loose_olang": args.work_dir / "jpn_loose_olang_rows.jsonl",
        "slot_olang": args.work_dir / "jpn_slot_olang_rows.jsonl",
        "stagedat": args.work_dir / "jpn_stagedat_rows.jsonl",
    }
    write_jsonl(outputs["ohd"], ohd_rows)
    write_jsonl(outputs["loose_olang"], loose_rows)
    write_jsonl(outputs["slot_olang"], slot_rows)
    write_jsonl(outputs["stagedat"], stage_rows)
    errors = loose_errors + slot_errors + stage_errors
    stats = {
        "scope": "reliably parsed Japanese text only; no heuristic scan",
        "japanese_language_key": hex32(JAPANESE_KEY),
        "loose_olang": loose_stats,
        "slot_olang": slot_stats,
        "ohd": ohd_stats,
        "stagedat": stage_stats,
        "error_count": len(errors),
        "errors": errors,
        "row_files": {key: str(path.resolve()) for key, path in outputs.items()},
    }
    stats_path = args.work_dir / "extraction_stats.json"
    stats_path.write_text(json.dumps(stats, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    print(f"LOOSE_OLANG_ROWS={len(loose_rows)}")
    print(f"SLOT_OLANG_ROWS={len(slot_rows)}")
    print(f"OHD_ROWS={len(ohd_rows)}")
    print(f"STAGEDAT_ROWS={len(stage_rows)}")
    print(f"PARSE_ERRORS={len(errors)}")
    print(f"STATS_PATH={stats_path.resolve()}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
