#!/usr/bin/env python3
"""Attach auditable MLG_CN/ENG references to the JPN text master rows.

JPN text and layout remain authoritative.  This script only reads existing
containers and existing V2 mapping evidence.  A reference is attached only
when the original JPN row can be verified at the same structural coordinate.
"""

from __future__ import annotations

import argparse
import csv
import hashlib
import importlib.util
import json
import struct
import sys
from collections import Counter, defaultdict
from pathlib import Path


JAPANESE_KEY = 0x00000DB0
ENGLISH_KEY = 0x00000D0E
OLANG_KIND = 0x5D
OHD_KIND = 0x1E
OHD_TEXT_OFFSET = 60


def load_module(path: Path, name: str):
    spec = importlib.util.spec_from_file_location(name, path)
    if spec is None or spec.loader is None:
        raise RuntimeError(f"cannot load helper module: {path}")
    module = importlib.util.module_from_spec(spec)
    sys.modules[name] = module
    spec.loader.exec_module(module)
    return module


def read_jsonl(path: Path) -> list[dict]:
    with path.open("r", encoding="utf-8") as stream:
        return [json.loads(line) for line in stream if line.strip()]


def write_jsonl(path: Path, rows: list[dict]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", encoding="utf-8", newline="\n") as stream:
        for row in rows:
            stream.write(json.dumps(row, ensure_ascii=False, separators=(",", ":")) + "\n")


def paired_english_index(parsed, reference_index: int) -> int | None:
    order = (0x00000D0E, 0x00000D32, 0x00000D45, 0x00000D94, 0x00000DB0, 0x00000ED0)
    key = parsed.references[reference_index].language_key
    if key == ENGLISH_KEY:
        return reference_index
    try:
        position = order.index(key)
    except ValueError:
        return None
    start = reference_index
    while start > 0 and parsed.references[start - 1].language_key == key:
        start -= 1
    ordinal = reference_index - start
    cursor = start
    for preceding in reversed(order[:position]):
        end = cursor
        begin = end
        while begin > 0 and parsed.references[begin - 1].language_key == preceding:
            begin -= 1
        if begin == end:
            return None
        if preceding == ENGLISH_KEY:
            candidate = begin + ordinal
            return candidate if candidate < end else None
        cursor = begin
    return None


def structural_signature(parsed) -> str:
    packed = bytearray(struct.pack("<II", len(parsed.entities), len(parsed.references)))
    for entity in parsed.entities:
        packed.extend(struct.pack("<IHH", entity.key, entity.reference_index, entity.reference_count))
    for reference in parsed.references:
        packed.extend(struct.pack("<I", reference.flag))
    return hashlib.sha256(packed).hexdigest().upper()


def semantic_source_texts(target, source) -> list[str | None]:
    """Map source texts onto target references by exact entity identity."""
    if structural_signature(target) == structural_signature(source):
        return [reference.text for reference in source.references]
    occurrences = Counter()
    source_by_identity = {}
    for entity in source.entities:
        identity = (entity.key, occurrences[entity.key])
        occurrences[entity.key] += 1
        source_by_identity[identity] = entity
    occurrences.clear()
    result: list[str | None] = [None] * len(target.references)
    for entity in target.entities:
        identity = (entity.key, occurrences[entity.key])
        occurrences[entity.key] += 1
        source_entity = source_by_identity.get(identity)
        if source_entity is None or source_entity.reference_count != entity.reference_count:
            continue
        for ordinal in range(entity.reference_count):
            target_index = entity.reference_index + ordinal
            source_index = source_entity.reference_index + ordinal
            if target_index < len(result) and source_index < len(source.references):
                result[target_index] = source.references[source_index].text
    return result


def reference_fields(jpn_text: str, original, translated, reference_index: int, method: str) -> dict:
    if reference_index >= len(original.references):
        return {"reference_status": "VERIFY_FAILED", "reference_method": method, "reference_reason": "original reference index out of range"}
    original_ref = original.references[reference_index]
    if original_ref.language_key != JAPANESE_KEY or original_ref.text != jpn_text:
        return {"reference_status": "VERIFY_FAILED", "reference_method": method, "reference_reason": "JPN coordinate/text verification failed"}
    eng = ""
    eng_index = paired_english_index(original, reference_index)
    if eng_index is not None and eng_index < len(original.references):
        eng = original.references[eng_index].text
    cn = ""
    reason = ""
    if translated is None or reference_index >= len(translated.references):
        status = "NO_AUX_RESOURCE"
        reason = "translated JPN-coordinate resource unavailable"
    else:
        translated_ref = translated.references[reference_index]
        if translated_ref.language_key != JAPANESE_KEY:
            status = "VERIFY_FAILED"
            reason = "translated reference language key changed"
        elif translated_ref.text == jpn_text:
            status = "AUX_UNCHANGED"
            reason = "auxiliary bank retains the original JPN text"
        elif not translated_ref.text:
            status = "AUX_EMPTY"
            reason = "auxiliary bank contains an empty string at this coordinate"
        else:
            status = "AUX_CN_ATTACHED"
            cn = translated_ref.text
    return {
        "mlg_cn_reference": cn,
        "eng_reference": eng,
        "reference_status": status,
        "reference_method": method,
        "reference_reason": reason,
    }


class SlotReader:
    def __init__(self, dat: Path, key: Path, slot):
        self.dat = dat
        self.slot = slot
        self.seed = slot.CRYPTO.filename_seed(key)
        _, self.salts, self.entries = slot.decode_key(key, self.seed)
        self.cache = {}

    def cnf(self, page: int):
        if page not in self.cache:
            raw, _ = self.slot.decode_page(self.dat, self.entries[page], self.salts, self.seed)
            self.cache[page] = self.slot.parse_cnf(raw)
        return self.cache[page]


def enrich_loose(rows, jpn_root, translated_root, rbx, loose):
    cache = {}
    output = []
    for row in rows:
        name = Path(row["container"]).name
        if name not in cache:
            original = rbx.parse_rbx(loose.decrypt(jpn_root / "Text" / name), f"loose:{name}:jpn")
            translated_path = translated_root / "Text" / name
            translated = rbx.parse_rbx(loose.decrypt(translated_path), f"loose:{name}:aux") if translated_path.exists() else None
            cache[name] = (original, translated)
        original, translated = cache[name]
        updated = dict(row)
        updated.update(reference_fields(row["jpn_text"], original, translated, int(row["reference_index"]), "exact_jpn_loose_file_and_reference_index"))
        output.append(updated)
    return output


def enrich_slot_olang(rows, original_reader, translated_reader, eng_reader, rbx, mapping_path):
    mapping_doc = json.loads(mapping_path.read_text(encoding="utf-8"))
    mapping_by_target = {
        (int(item["target_page"]), int(item["target_tag_index"])): item
        for item in mapping_doc["mappings"]
    }
    cache = {}
    eng_cache = {}
    output = []
    for row in rows:
        coordinate = (int(row["page"]), int(row["tag_index"]))
        if coordinate not in cache:
            page, tag = coordinate
            original_cnf = original_reader.cnf(page)
            translated_cnf = translated_reader.cnf(page)
            original_tag = original_cnf.tags[tag]
            translated_tag = translated_cnf.tags[tag]
            if original_tag.kind != OLANG_KIND or translated_tag.kind != OLANG_KIND or original_tag.file_id != translated_tag.file_id:
                raise RuntimeError(f"SLOT OLANG coordinate changed at {page}:{tag}")
            cache[coordinate] = (
                rbx.parse_rbx(original_cnf.segments[tag], f"slot:{page}:{tag}:jpn"),
                rbx.parse_rbx(translated_cnf.segments[tag], f"slot:{page}:{tag}:aux"),
            )
        original, translated = cache[coordinate]
        updated = dict(row)
        updated.update(reference_fields(row["jpn_text"], original, translated, int(row["reference_index"]), "exact_jpn_slot_page_tag_reference_index"))
        locations = [tuple(map(int, item.split(":"))) for item in row["occurrence_locations"].split(";") if item]
        mapping = next((mapping_by_target[item] for item in locations if item in mapping_by_target), None)
        if mapping is not None:
            source_coordinate = (int(mapping["source_page"]), int(mapping["source_tag_index"]))
            cache_key = (coordinate, source_coordinate)
            if cache_key not in eng_cache:
                source_cnf = eng_reader.cnf(source_coordinate[0])
                source_tag = source_cnf.tags[source_coordinate[1]]
                if f"0x{source_tag.file_id:08X}" != mapping["source_file_id"]:
                    raise RuntimeError(f"SLOT mapping source file ID changed at {source_coordinate}")
                source = rbx.parse_rbx(source_cnf.segments[source_coordinate[1]], f"slot:{source_coordinate[0]}:{source_coordinate[1]}:eng")
                eng_cache[cache_key] = semantic_source_texts(original, source)
            reference_index = int(row["reference_index"])
            eng_texts = eng_cache[cache_key]
            if reference_index < len(eng_texts) and eng_texts[reference_index] is not None:
                updated["eng_reference"] = eng_texts[reference_index]
                updated["reference_method"] += ";validated_slot_olang_map_entity_identity"
        output.append(updated)
    return output


def ohd_text(record: bytes) -> str:
    field = record[OHD_TEXT_OFFSET:]
    end = field.find(b"\0")
    return (field if end < 0 else field[:end]).decode("utf-8", errors="strict")


def enrich_ohd(rows, original_reader, translated_reader, eng_reader, voice):
    cache = {}
    output = []
    for row in rows:
        page, tag = int(row["page"]), int(row["tag_index"])
        coordinate = (page, tag)
        if coordinate not in cache:
            original_cnf = original_reader.cnf(page)
            translated_cnf = translated_reader.cnf(page)
            _, original_records = voice.parse_ohd(original_cnf.segments[tag], f"ohd:{page}:{tag}:jpn")
            _, translated_records = voice.parse_ohd(translated_cnf.segments[tag], f"ohd:{page}:{tag}:aux")
            eng_cnf = eng_reader.cnf(page - 4)
            eng_tags = [index for index, item in enumerate(eng_cnf.tags) if item.kind == OHD_KIND]
            eng_records = []
            if len(eng_tags) == 1:
                _, eng_records = voice.parse_ohd(eng_cnf.segments[eng_tags[0]], f"ohd:{page - 4}:{eng_tags[0]}:eng")
            cache[coordinate] = (original_records, translated_records, eng_records)
        original_records, translated_records, eng_records = cache[coordinate]
        index = int(row["record_index"])
        jpn = ohd_text(original_records[index])
        updated = dict(row)
        if jpn != row["jpn_text"]:
            updated.update({"reference_status": "VERIFY_FAILED", "reference_method": "exact_jpn_ohd_coordinate", "reference_reason": "JPN record text verification failed"})
        else:
            cn = ohd_text(translated_records[index]) if index < len(translated_records) else ""
            eng = ohd_text(eng_records[index]) if index < len(eng_records) else ""
            changed = cn != jpn
            status = "AUX_CN_ATTACHED" if cn and changed else ("AUX_EMPTY" if changed else "AUX_UNCHANGED")
            updated.update({
                "mlg_cn_reference": cn if cn and changed else "",
                "eng_reference": eng,
                "reference_status": status,
                "reference_method": "exact_jpn_ohd_page_record;eng_same_six_page_group_record",
                "reference_reason": "" if cn and changed else ("auxiliary bank contains an empty string at this coordinate" if changed else "auxiliary bank retains the original JPN text"),
            })
        output.append(updated)
    return output


def load_stage_pages(path, pages, stage, rbx):
    result = {}
    seed = stage.filename_seed(path)
    with path.open("rb") as stream:
        header = stage.decode_header(stream, seed)
        entries, _ = stage.decode_table(stream, seed, header)
        for page in sorted(pages):
            data = stage.decode_page(stream, seed, header, entries[page])
            result[page] = {entry.name.casefold(): entry for entry in rbx.parse_dar(data)}
    return result


def enrich_stagedat(rows, jpn_path, translated_path, eng_path, stage, rbx):
    pages = {int(row["page"]) for row in rows}
    originals = load_stage_pages(jpn_path, pages, stage, rbx)
    translated = load_stage_pages(translated_path, pages, stage, rbx)
    english = load_stage_pages(eng_path, pages, stage, rbx)
    parsed_cache = {}
    output = []
    for row in rows:
        page = int(row["page"])
        name = row["archive_entry_name"].casefold()
        key = (page, name)
        if key not in parsed_cache:
            original_entry = originals[page].get(name)
            translated_entry = translated[page].get(name)
            if original_entry is None:
                raise RuntimeError(f"missing original STAGEDAT entry {page}:{name}")
            companion = name[:-6] + "_en.olang" if name.endswith(".olang") else ""
            source_entry = english[page].get(companion)
            original_parsed = rbx.parse_rbx(original_entry.data, f"stage:{page}:{name}:jpn")
            parsed_cache[key] = (
                original_parsed,
                rbx.parse_rbx(translated_entry.data, f"stage:{page}:{name}:aux") if translated_entry else None,
                semantic_source_texts(original_parsed, rbx.parse_rbx(source_entry.data, f"stage:{page}:{companion}:eng")) if source_entry else None,
            )
        original, aux, eng_texts = parsed_cache[key]
        updated = dict(row)
        updated.update(reference_fields(row["jpn_text"], original, aux, int(row["reference_index"]), "exact_jpn_stagedat_page_entry_reference_index"))
        reference_index = int(row["reference_index"])
        if eng_texts is not None and reference_index < len(eng_texts) and eng_texts[reference_index] is not None:
            updated["eng_reference"] = eng_texts[reference_index]
            updated["reference_method"] += ";same_page_en_companion_entity_identity"
        output.append(updated)
    return output


def enrich_gtt(rows, audit_path, translation_path, eng_reader, gtt):
    with audit_path.open("r", encoding="utf-8-sig", newline="") as stream:
        audit_rows = list(csv.DictReader(stream))
    selected = {}
    for audit in audit_rows:
        if audit["status"] not in {"SUCCESS", "HARD_OVERFLOW"}:
            continue
        if not audit["jpn_file_id"] or audit["jpn_mapped_record"] == "":
            continue
        if audit["cn_segment_count"] != audit["jpn_segment_count"]:
            continue
        key = (audit["jpn_file_id"].upper(), int(audit["jpn_mapped_record"]))
        selected.setdefault(key, audit)  # first scanned MLG_CN payload variant is authoritative auxiliary

    eng_record_cache = {}
    final_translation = json.loads(translation_path.read_text(encoding="utf-8"))
    final_file_id = final_translation["file_id"].upper()
    final_records = final_translation["records"]
    output = []
    for row in rows:
        file_id = row["file_id"].upper()
        record_index = int(row["record_index"])
        segment_index = int(row["segment_index"])
        updated = dict(row)
        updated.setdefault("mlg_cn_reference", "")
        updated.setdefault("eng_reference", "")
        audit = selected.get((file_id, record_index))
        if audit is None:
            updated.update({"reference_status": "NO_RELIABLE_GTT_MAPPING", "reference_method": "v2_mapping_audit", "reference_reason": "no unique equal-topology SUCCESS/HARD_OVERFLOW mapping"})
        else:
            cn_texts = json.loads(audit["cn_texts"])
            jpn_texts = json.loads(audit["jpn_texts"])
            if segment_index >= len(cn_texts) or segment_index >= len(jpn_texts) or jpn_texts[segment_index] != row["jpn_text"]:
                updated.update({"reference_status": "VERIFY_FAILED", "reference_method": "v2_mapping_audit_first_scanned_variant", "reference_reason": "audit segment/JPN text verification failed"})
            else:
                eng_key = (int(audit["eng_page"]), int(audit["eng_tag"]), int(audit["eng_record"]))
                if eng_key not in eng_record_cache:
                    cnf = eng_reader.cnf(eng_key[0])
                    records = gtt.parse_gtt(cnf.segments[eng_key[1]], f"eng:{eng_key[0]}:{eng_key[1]}")
                    eng_record_cache[eng_key] = records[eng_key[2]]
                eng_record = eng_record_cache[eng_key]
                eng = eng_record.texts[segment_index] if segment_index < len(eng_record.texts) else ""
                updated.update({
                    "mlg_cn_reference": cn_texts[segment_index],
                    "eng_reference": eng,
                    "reference_status": "AUX_CN_ATTACHED",
                    "reference_method": "v2_mapping_audit_first_scanned_mlg_cn_variant",
                    "reference_reason": f"mapping={audit['mapping_method']}; status={audit['status']}",
                })
        if file_id == final_file_id and record_index < len(final_records) and segment_index < len(final_records[record_index]):
            updated["cn_text"] = final_records[record_index][segment_index]
        output.append(updated)
    return output


def summarize(rows):
    statuses = Counter(row.get("reference_status", "") for row in rows)
    return {
        "rows": len(rows),
        "mlg_cn_reference_rows": sum(bool(row.get("mlg_cn_reference")) for row in rows),
        "eng_reference_rows": sum(bool(row.get("eng_reference")) for row in rows),
        "cn_text_rows": sum(bool(row.get("cn_text")) for row in rows),
        "reference_statuses": dict(sorted(statuses.items())),
    }


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    v2_root = Path(__file__).resolve().parents[1]
    parent = v2_root.parent
    parser.add_argument("--jpn-root", type=Path, default=Path(r"D:\GAME\test\JPN\MGS_PW\mgspw\JPN"))
    parser.add_argument("--mlg-root", type=Path, default=Path(r"D:\GAME\test\JPN\MGS_PW\mgspw\MLG"))
    parser.add_argument("--aux-jpn-root", type=Path, default=parent / "JPVoice_CNText_Experimental" / "build" / "text-only" / "mgspw" / "JPN")
    parser.add_argument("--legacy-tools", type=Path, default=parent / "JPVoice_CNText_Experimental" / "tools")
    parser.add_argument("--work-dir", type=Path, default=v2_root / "work" / "text_master_rows")
    args = parser.parse_args()

    slot = load_module(args.legacy_tools / "Build-JpnSlot.py", "v2_aux_slot")
    rbx = load_module(args.legacy_tools / "Build-JpnInitCache.py", "v2_aux_rbx")
    loose = load_module(args.legacy_tools / "Build-JpnLooseOlang.py", "v2_aux_loose")
    voice = load_module(args.legacy_tools / "Build-JpnSlotNativeVoiceText.py", "v2_aux_voice")
    stage = load_module(args.legacy_tools / "Patch-StageDatPage.py", "v2_aux_stage")
    gtt = load_module(v2_root / "core" / "gtt_multi.py", "v2_aux_gtt")

    jpn_dat = args.jpn_root / "disc0_rel" / "002aba34.DAT"
    jpn_key = args.jpn_root / "disc0_rel" / "002aba34.KEY"
    aux_dat = args.aux_jpn_root / "disc0_rel" / "002aba34.DAT"
    mlg_dat = args.mlg_root / "disc0_rel" / "002aba34.DAT"
    mlg_key = args.mlg_root / "disc0_rel" / "002aba34.KEY"
    original_reader = SlotReader(jpn_dat, jpn_key, slot)
    translated_reader = SlotReader(aux_dat, jpn_key, slot)
    eng_reader = SlotReader(mlg_dat, mlg_key, slot)

    source_rows = {
        "ohd": read_jsonl(args.work_dir / "jpn_ohd_rows.jsonl"),
        "loose_olang": read_jsonl(args.work_dir / "jpn_loose_olang_rows.jsonl"),
        "slot_olang": read_jsonl(args.work_dir / "jpn_slot_olang_rows.jsonl"),
        "stagedat": read_jsonl(args.work_dir / "jpn_stagedat_rows.jsonl"),
    }
    with (v2_root / "build" / "translation" / "jpn_gtt" / "jpn_gtt_master.csv").open("r", encoding="utf-8-sig", newline="") as stream:
        gtt_rows = list(csv.DictReader(stream))

    print("PHASE=GTT", flush=True)
    enriched = {
        "gtt": enrich_gtt(gtt_rows, v2_root / "build" / "v2_gtt" / "records.csv", v2_root / "translations" / "1C79F2AD_cn.json", eng_reader, gtt),
    }
    print("PHASE=LOOSE_OLANG", flush=True)
    enriched["loose_olang"] = enrich_loose(source_rows["loose_olang"], args.jpn_root, args.aux_jpn_root, rbx, loose)
    print("PHASE=SLOT_OLANG", flush=True)
    enriched["slot_olang"] = enrich_slot_olang(source_rows["slot_olang"], original_reader, translated_reader, eng_reader, rbx, args.legacy_tools / "slot-olang-map.json")
    print("PHASE=OHD", flush=True)
    enriched["ohd"] = enrich_ohd(source_rows["ohd"], original_reader, translated_reader, eng_reader, voice)
    print("PHASE=STAGEDAT", flush=True)
    enriched["stagedat"] = enrich_stagedat(source_rows["stagedat"], args.jpn_root / "disc0_rel" / "009645fa.PDT", args.aux_jpn_root / "disc0_rel" / "009645fa.PDT", args.mlg_root / "disc0_rel" / "009645fa.PDT", stage, rbx)

    for key, rows in enriched.items():
        write_jsonl(args.work_dir / f"enriched_{key}_rows.jsonl", rows)
    stats = {key: summarize(rows) for key, rows in enriched.items()}
    stats["policy"] = {
        "semantic_authority": "JPN",
        "structure_authority": "JPN target resource",
        "mlg_cn": "auxiliary only; first scanned payload variant for GTT",
        "eng": "disambiguation only",
    }
    stats_path = args.work_dir / "auxiliary_reference_stats.json"
    stats_path.write_text(json.dumps(stats, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    for key in ("gtt", "ohd", "loose_olang", "slot_olang", "stagedat"):
        item = stats[key]
        print(f"{key.upper()}_AUX_CN={item['mlg_cn_reference_rows']}")
        print(f"{key.upper()}_ENG={item['eng_reference_rows']}")
    print(f"STATS_PATH={stats_path.resolve()}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
