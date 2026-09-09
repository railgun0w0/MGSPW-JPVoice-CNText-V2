#!/usr/bin/env python3
"""Prepare and rebuild the single JPN SLOT OLANG resource 5D3AF52D."""

from __future__ import annotations

import argparse
import csv
import hashlib
import importlib.util
import json
import re
import shutil
import sys
from pathlib import Path


FILE_ID = 0x5D3AF52D
PAGE_INDEX = 1864
TAG_INDEX = 2
EXPECTED_REFERENCES = 118
EXPECTED_UNIQUE_TEXTS = 110

V2_ROOT = Path(__file__).resolve().parents[1]
LEGACY_TOOLS = V2_ROOT.parent / "JPVoice_CNText_Experimental" / "tools"
DEFAULT_DAT = Path(r"D:\GAME\test\JPN\MGS_PW\mgspw\JPN\disc0_rel\002aba34.DAT")
DEFAULT_KEY = Path(r"D:\GAME\test\JPN\MGS_PW\mgspw\JPN\disc0_rel\002aba34.KEY")
DEFAULT_WORK_ROOT = V2_ROOT / "build" / "translation" / "5D3AF52D"
DEFAULT_TEST_ROOT = V2_ROOT / "build" / "test_5D3AF52D" / "mgspw" / "JPN" / "disc0_rel"


def load_module(path: Path, name: str):
    spec = importlib.util.spec_from_file_location(name, path)
    if spec is None or spec.loader is None:
        raise RuntimeError(f"cannot load helper module: {path}")
    module = importlib.util.module_from_spec(spec)
    sys.modules[name] = module
    spec.loader.exec_module(module)
    return module


SLOT = load_module(LEGACY_TOOLS / "Build-JpnSlot.py", "slot_5d3af52d")
RBX = load_module(LEGACY_TOOLS / "Build-JpnInitCache.py", "rbx_5d3af52d")
FULL = load_module(LEGACY_TOOLS / "Build-JpnSlotFullOlang.py", "full_5d3af52d")


# One entry per JPN reference. Duplicate JPN references deliberately carry the
# same translation and are collapsed to 110 rows in the worktable.
CN_BY_REFERENCE = (
    "放心，我没打算给你\n新的<R=任务,MISSION>。",  # 0
    "放心，我没打算给你\n新的<R=任务,MISSION>。",  # 1
    "放心，我没打算给你\n新的<R=任务,MISSION>。",  # 2
    "放心，我没打算给你\n新的<R=任务,MISSION>。",  # 3
    "放心，我没打算给你\n新的<R=任务,MISSION>。",  # 4
    "放心，我没打算给你\n新的<R=任务,MISSION>。",  # 5
    "放心，我没打算给你\n新的<R=任务,MISSION>。",  # 6
    "放心，我没打算给你\n新的<R=任务,MISSION>。",  # 7
    "……<R=胜利,VICTORY>，Boss。",  # 8
    "对不起。",  # 9
    "叫我Snake就行。",  # 10
    "非常感谢！<R=BIGBOSS,BIG BOSS>！",  # 11
    "人是我带来的，没人跟踪。",  # 12
    "不是<R=CIA,THEM>的人。",  # 13
    "放心。",  # 14
    "要撤了吗？",  # 15
    "我们……两样都不能选。",  # 16
    "“<R=否则只有死亡,VICTORIA O MUERTE>”？",  # 17
    "“要么<R=胜利,VICTORIA>，要么<->”",  # 18
    "我们没有所谓的胜利。",  # 19
    "听好了。",  # 20
    "有客人。",  # 21
    "怎么了，Kaz？",  # 22
    "谢谢。",  # 23
    "你来哥伦比亚做什么？",  # 24
    "哥斯达黎加政府的大人物……",  # 25
    "然后呢……",  # 26
    "哥斯达黎加咖啡果然不错。",  # 27
    "……活过来了！",  # 28
    "和平宪法……",  # 29
    "宪法第12条：\n“禁止常设军队。”",  # 30
    "是。",  # 31
    "哥斯达黎加没有军队……",  # 32
    "当然，不是正规军。",  # 33
    "有人开始在哥斯达黎加境内\n目击到武装团体。",  # 34
    "大约从一年前开始。",  # 35
    "其实……",  # 36
    "我是哥斯达黎加联合国和平大学的Galvez教授。",  # 37
    "他们自称“跨国企业的警卫”。",  # 38
    "政府声称他们受<R=哥斯达黎加开发公司,CODESA>雇佣。",  # 39
    "哥斯达黎加政府怎么说？",  # 40
    "不，他们不像游击队，\n组织严密得多。",  # 41
    "不是从尼加拉瓜逃来的<R=反政府组织,FSLN>吗？",  # 42
    "我们不能拿起武器。",  # 43
    "所以政府无法赶走他们？",  # 44
    "古巴导弹危机后，我们仍勉强维持着\n与美国之间微妙的<R=平衡,BALANCE>。",  # 45
    "如你所知，中南美洲是美国的后院……",  # 46
    "CIA？",  # 47
    "<R=CIA,LA CIA>参与其中。",  # 48
    "……恐怕是。",  # 49
    "他们哪来那么多资金？",  # 50
    "我们来求助于你们——\n“<R=无国界军队,MSF>”。",  # 51
    "请把他们赶出没有军队的哥斯达黎加。",  # 52
    "拜托了。",  # 53
    "听说你们不<R=依赖,RELY>国家或思想，\n无论对手是谁都敢战斗。",  # 54
    "放弃战争，不保有军队。",  # 55
    "日本也有被称为和平宪法的“第9条”。",  # 56
    "他们正在大量运入\n最先进的武器和设备。",  # 57
    "当然，那全是谎话。",  # 58
    "我们需要一个安身之处。",  # 59
    "Snake……",  # 60
    "<R=哥伦比亚,这里>也快待不下去了。",  # 61
    "不是挺好吗？",  # 62
    "我们可以把加勒比海上的海上平台\n提供给你们作为前线基地。",  # 63
    "不过……",  # 64
    "我是以“教育者”的身份来的。",  # 65
    "今晚来到这里……",  # 66
    "几十年来，我一直在大学里宣扬和平。",  # 67
    "那你为什么来？",  # 68
    "……报酬恐怕不够丰厚。",  # 69
    "我不是代表政府来的。",  # 70
    "不。",  # 71
    "我可以介绍一位认识的<R=谈判专家,NEGOTIATOR>。",  # 72
    "回去转告政府的大人物。",  # 73
    "国家无法出面。",  # 74
    "只能通过政治手段解决。",  # 75
    "如果<R=他们,CIA>牵涉其中，武力解决不了。",  # 76
    "听好了。",  # 77
    "请帮帮我们！",  # 78
    "拜托了！",  # 79
    "希望你们成为我们的“威慑力量”。",  # 80
    "我们只是抛弃了国家。",  # 81
    "我们……",  # 82
    "是不属于任何国家的军队……",  # 83
    "是的，我听说过。",  # 84
    "你似乎把我们误当成\n“<R=战争之犬,DOGS OF WAR>”之类了。",  # 85
    "等等！",  # 86
    "我去交涉。",  # 87
    "可以的话，最好<R=能有,NEED>架运输直升机。",  # 88
    "我们已经争取到政府合作。",  # 89
    "虽然只是非官方的……",  # 90
    "是。",  # 91
    "你是想雇佣我们？",  # 92
    "叫我Kaz就行。",  # 93
    "请多关照，Paz。",  # 94
    "日语里是“和平”的意思。",  # 95
    "我叫<R=和平,KAZUHIRA>。",  # 96
    "哦？和我的名字一样。",  # 97
    "<R=和平,LA PAZ>……",  # 98
    "我叫Paz……Paz Ortega。",  # 99
    "她是我的学生，在大学学习和平。",  # 100
    "她比任何人都憎恨战争。",  # 101
    "她幼年丧母，祖父母也死于内战……",  # 102
    "她是<R=私生女,BASTARD>。",  # 103
    "太残酷了。",  # 104
    "她遭到凌辱，最后设法独自逃了出来。",  # 105
    "Paz才16岁，还是个孩子。",  # 106
    "后来她被他们抓住了。",  # 107
    "Paz为寻找失踪的朋友，\n误闯进了那座设施。",  # 108
    "几天前……",  # 109
    "在<R=加勒比海沿岸,CARIBBEAN COAST>的利蒙港以北，\n有他们的物资港。",  # 110
    "知道你是“<R=BIGBOSS,BIG BOSS>”才来求你。",  # 111
    "你……",  # 112
    "抱歉……",  # 113
    "求你！把他们赶出我的祖国哥斯达黎加！",  # 114
    "我就是为此活下来的。",  # 115
    "我一定会守护和平。",  # 116
    "我的名字就是“<R=和平,LA PAZ>”。",  # 117
)


CONTROL_RE = re.compile(r"<[^<>]*>|\$\d+")


def sha256(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest().upper()


def control_signature(text: str) -> list[str]:
    signature: list[str] = []
    for token in CONTROL_RE.findall(text):
        if token.startswith("<R="):
            signature.append("R")
        elif token.startswith("<I="):
            signature.append("I")
        elif token == "<->":
            signature.append("-")
        elif token.startswith("<"):
            signature.append(token[1:].split("=", 1)[0].rstrip(">"))
        else:
            signature.append("$")
    return signature


def scene_name(index: int) -> str:
    if index <= 23:
        return "基地会面与称呼"
    if index <= 58:
        return "哥斯达黎加局势说明"
    if index <= 92:
        return "委托、基地与政治条件"
    return "Paz介绍与遭遇"


def load_target(dat_path: Path, key_path: Path):
    seed = SLOT.CRYPTO.filename_seed(key_path)
    key_plain, salts, entries = SLOT.decode_key(key_path, seed)
    if PAGE_INDEX >= len(entries):
        raise RuntimeError(f"page {PAGE_INDEX} is outside KEY entry table")
    decoded, page_header = SLOT.decode_page(dat_path, entries[PAGE_INDEX], salts, seed)
    cnf = SLOT.parse_cnf(decoded)
    if TAG_INDEX >= len(cnf.tags):
        raise RuntimeError(f"tag {TAG_INDEX} is outside page {PAGE_INDEX}")
    tag = cnf.tags[TAG_INDEX]
    if tag.file_id != FILE_ID:
        raise RuntimeError(f"expected {FILE_ID:08X}, found {tag.file_id:08X}")
    segment = cnf.segments[TAG_INDEX]
    parsed = RBX.parse_rbx(segment, f"{FILE_ID:08X}")
    if len(parsed.references) != EXPECTED_REFERENCES:
        raise RuntimeError(
            f"expected {EXPECTED_REFERENCES} references, found {len(parsed.references)}"
        )
    if len(CN_BY_REFERENCE) != EXPECTED_REFERENCES:
        raise RuntimeError("internal translation count mismatch")
    return seed, key_plain, salts, entries, decoded, page_header, cnf, segment, parsed


def entity_context(parsed) -> dict[int, list[tuple[int, int, int]]]:
    result: dict[int, list[tuple[int, int, int]]] = {}
    for entity_index, entity in enumerate(parsed.entities):
        for ordinal in range(entity.reference_count):
            reference_index = entity.reference_index + ordinal
            result.setdefault(reference_index, []).append((entity_index, entity.key, ordinal))
    return result


def prepare(dat_path: Path, key_path: Path, rows_jsonl: Path) -> dict:
    *_, parsed = load_target(dat_path, key_path)
    by_text: dict[str, dict] = {}
    contexts = entity_context(parsed)
    for index, (reference, cn_text) in enumerate(zip(parsed.references, CN_BY_REFERENCE)):
        current = by_text.get(reference.text)
        if current is None:
            current = {
                "first_reference_index": index,
                "reference_indices": [],
                "jpn_text": reference.text,
                "cn_text": cn_text,
            }
            by_text[reference.text] = current
        elif current["cn_text"] != cn_text:
            raise RuntimeError(f"duplicate JPN text has conflicting translations at reference {index}")
        current["reference_indices"].append(index)

    if len(by_text) != EXPECTED_UNIQUE_TEXTS:
        raise RuntimeError(f"expected {EXPECTED_UNIQUE_TEXTS} unique texts, found {len(by_text)}")

    all_jpn = [reference.text for reference in parsed.references]
    rows = []
    for unique_index, item in enumerate(by_text.values()):
        first = item["first_reference_index"]
        previous = next((all_jpn[i] for i in range(first - 1, -1, -1) if all_jpn[i] != item["jpn_text"]), "")
        last = item["reference_indices"][-1]
        following = next((all_jpn[i] for i in range(last + 1, len(all_jpn)) if all_jpn[i] != item["jpn_text"]), "")
        entity_parts = []
        for reference_index in item["reference_indices"]:
            for entity_index, key, ordinal in contexts.get(reference_index, []):
                entity_parts.append(f"ref{reference_index}:entity{entity_index}:key{key}:ord{ordinal}")
        jpn_tokens = CONTROL_RE.findall(item["jpn_text"])
        cn_tokens = CONTROL_RE.findall(item["cn_text"])
        control_ok = control_signature(item["jpn_text"]) == control_signature(item["cn_text"])
        if not control_ok:
            raise RuntimeError(f"control structure mismatch at reference {first}")
        rows.append(
            {
                "file_id": f"{FILE_ID:08X}",
                "unique_index": unique_index,
                "first_reference_index": first,
                "reference_indices": ";".join(str(i) for i in item["reference_indices"]),
                "reference_count": len(item["reference_indices"]),
                "scene_context": scene_name(first),
                "entity_context": ";".join(entity_parts),
                "previous_jpn_text": previous,
                "jpn_text": item["jpn_text"],
                "next_jpn_text": following,
                "jpn_control_tokens": " | ".join(jpn_tokens),
                "cn_text": item["cn_text"],
                "cn_control_tokens": " | ".join(cn_tokens),
                "control_structure_status": "MATCH",
                "jpn_utf8_bytes": len(item["jpn_text"].encode("utf-8")),
                "cn_utf8_bytes": len(item["cn_text"].encode("utf-8")),
                "translation_status": "COMPLETE",
                "translation_basis": "JPN_PRIMARY; MLG_CN_CONTEXT_AUXILIARY",
                "notes": "Ruby display/reading content localized; markup shape retained.",
            }
        )

    rows_jsonl.parent.mkdir(parents=True, exist_ok=True)
    with rows_jsonl.open("w", encoding="utf-8", newline="\n") as stream:
        for row in rows:
            stream.write(json.dumps(row, ensure_ascii=False) + "\n")
    return {"references": len(parsed.references), "unique_texts": len(rows), "rows_jsonl": str(rows_jsonl)}


def read_worktable(csv_path: Path) -> dict[str, str]:
    with csv_path.open("r", encoding="utf-8-sig", newline="") as stream:
        rows = list(csv.DictReader(stream))
    if len(rows) != EXPECTED_UNIQUE_TEXTS:
        raise RuntimeError(f"worktable must contain {EXPECTED_UNIQUE_TEXTS} rows, found {len(rows)}")
    mapping: dict[str, str] = {}
    for row in rows:
        jpn = row.get("jpn_text", "")
        cn = row.get("cn_text", "")
        if not jpn or not cn:
            raise RuntimeError("worktable contains an empty JPN or CN text")
        if jpn in mapping:
            raise RuntimeError("worktable contains duplicate JPN rows")
        if control_signature(jpn) != control_signature(cn):
            raise RuntimeError(f"worktable control structure mismatch: {jpn!r}")
        mapping[jpn] = cn
    return mapping


def build(dat_path: Path, key_path: Path, csv_path: Path, output_root: Path, report_path: Path) -> dict:
    mapping = read_worktable(csv_path)
    seed, key_plain, salts, entries, decoded, page_header, cnf, segment, parsed = load_target(dat_path, key_path)
    missing = sorted({reference.text for reference in parsed.references} - set(mapping))
    extra = sorted(set(mapping) - {reference.text for reference in parsed.references})
    if missing or extra:
        raise RuntimeError(f"worktable/source mismatch: missing={len(missing)}, extra={len(extra)}")
    translated = [mapping[reference.text] for reference in parsed.references]

    rebuilt_raw = FULL.rebuild_with_texts(parsed, translated, f"{FILE_ID:08X}")
    rebuilt_segment = rebuilt_raw + bytes((-len(rebuilt_raw)) % 16)
    rebuilt_page = SLOT.rebuild_cnf(cnf, {TAG_INDEX: rebuilt_segment})
    zopfli = shutil.which("zopfli")
    encrypted_page, compressed_size, compression_method = FULL.encode_page_best(
        rebuilt_page,
        page_header,
        entries[PAGE_INDEX].capacity,
        salts,
        seed,
        Path(zopfli) if zopfli else None,
    )
    if len(encrypted_page) != entries[PAGE_INDEX].capacity:
        raise RuntimeError("encoded page did not preserve allocation")

    output_root.mkdir(parents=True, exist_ok=True)
    output_dat = output_root / dat_path.name
    output_key = output_root / key_path.name
    shutil.copy2(dat_path, output_dat)
    with output_dat.open("r+b") as stream:
        stream.seek(entries[PAGE_INDEX].start)
        stream.write(encrypted_page)
    shutil.copy2(key_path, output_key)

    verify_decoded, verify_header = SLOT.decode_page(output_dat, entries[PAGE_INDEX], salts, seed)
    verify_cnf = SLOT.parse_cnf(verify_decoded)
    verify_segment = verify_cnf.segments[TAG_INDEX]
    verify_rbx = RBX.parse_rbx(verify_segment, f"{FILE_ID:08X}:verify")

    source_tag_shape = [(tag.file_id, tag.pad_a, tag.pad_b, tag.kind) for tag in cnf.tags]
    verify_tag_shape = [(tag.file_id, tag.pad_a, tag.pad_b, tag.kind) for tag in verify_cnf.tags]
    non_target_equal = all(
        verify_cnf.segments[index] == original
        for index, original in cnf.segments.items()
        if index != TAG_INDEX
    )
    entity_equal = verify_rbx.entities == parsed.entities
    reference_metadata_equal = [
        (reference.language_key, reference.flag) for reference in verify_rbx.references
    ] == [(reference.language_key, reference.flag) for reference in parsed.references]
    roundtrip_equal = [reference.text for reference in verify_rbx.references] == translated
    header_entity_equal = rebuilt_raw[: parsed.reference_offset] == segment[: parsed.reference_offset]
    source_size = dat_path.stat().st_size
    output_size = output_dat.stat().st_size
    key_equal = output_key.read_bytes() == key_path.read_bytes()

    structural_ok = all(
        (
            source_tag_shape == verify_tag_shape,
            len(cnf.tags) == len(verify_cnf.tags),
            entity_equal,
            reference_metadata_equal,
            roundtrip_equal,
            header_entity_equal,
            non_target_equal,
            verify_header.unknown_a == page_header.unknown_a,
            verify_header.unknown_b == page_header.unknown_b,
            verify_header.padding == page_header.padding,
            entries[PAGE_INDEX].capacity == len(encrypted_page),
            source_size == output_size,
            key_equal,
        )
    )
    if not structural_ok:
        raise RuntimeError("post-build structural consistency check failed")

    report = {
        "status": "PASS",
        "scope": {
            "file_id": f"{FILE_ID:08X}",
            "page": PAGE_INDEX,
            "tag_index": TAG_INDEX,
            "patched_occurrences": 1,
            "patched_pages": 1,
            "other_resources_rebuilt": 0,
        },
        "inputs": {"clean_jpn_dat": str(dat_path), "clean_jpn_key": str(key_path), "worktable": str(csv_path)},
        "outputs": {"dat": str(output_dat), "key": str(output_key), "report": str(report_path)},
        "translation": {
            "jpn_references": len(parsed.references),
            "unique_jpn_texts": len({reference.text for reference in parsed.references}),
            "mapped_references": len(translated),
            "translated_unique_texts": len(mapping),
            "empty_cn_texts": sum(not text for text in translated),
            "control_structure_mismatches": 0,
        },
        "olang_structure": {
            "entity_count_before": len(parsed.entities),
            "entity_count_after": len(verify_rbx.entities),
            "reference_count_before": len(parsed.references),
            "reference_count_after": len(verify_rbx.references),
            "header_entity_bytes_identical": header_entity_equal,
            "entity_table_identical": entity_equal,
            "reference_language_key_and_flag_identical": reference_metadata_equal,
            "text_roundtrip_identical": roundtrip_equal,
            "segment_size_before": len(segment),
            "segment_size_after": len(verify_segment),
            "segment_sha256_before": sha256(segment),
            "segment_sha256_after": sha256(verify_segment),
        },
        "cnf_page_structure": {
            "tag_count_before": len(cnf.tags),
            "tag_count_after": len(verify_cnf.tags),
            "tag_identity_and_metadata_shape_identical": source_tag_shape == verify_tag_shape,
            "non_target_segment_payloads_byte_identical": non_target_equal,
            "decoded_page_size_before": len(decoded),
            "decoded_page_size_after": len(verify_decoded),
            "allocation_start": entries[PAGE_INDEX].start,
            "allocation_capacity_before": entries[PAGE_INDEX].capacity,
            "allocation_capacity_after": len(encrypted_page),
            "compressed_size_before": page_header.compressed_size,
            "compressed_size_after": compressed_size,
            "compression_method": compression_method,
            "block_overflow": 0,
        },
        "container": {
            "dat_size_before": source_size,
            "dat_size_after": output_size,
            "dat_size_identical": source_size == output_size,
            "key_byte_identical": key_equal,
        },
    }
    report_path.parent.mkdir(parents=True, exist_ok=True)
    report_path.write_text(json.dumps(report, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    return report


def main() -> int:
    parser = argparse.ArgumentParser()
    subparsers = parser.add_subparsers(dest="command", required=True)
    prepare_parser = subparsers.add_parser("prepare")
    prepare_parser.add_argument("--dat", type=Path, default=DEFAULT_DAT)
    prepare_parser.add_argument("--key", type=Path, default=DEFAULT_KEY)
    prepare_parser.add_argument("--rows-jsonl", type=Path, default=DEFAULT_WORK_ROOT / "context_rows.jsonl")
    build_parser = subparsers.add_parser("build")
    build_parser.add_argument("--dat", type=Path, default=DEFAULT_DAT)
    build_parser.add_argument("--key", type=Path, default=DEFAULT_KEY)
    build_parser.add_argument(
        "--worktable",
        type=Path,
        default=V2_ROOT / "translations" / "slot_olang" / "5D3AF52D.csv",
    )
    build_parser.add_argument("--output-root", type=Path, default=DEFAULT_TEST_ROOT)
    build_parser.add_argument("--report", type=Path, default=DEFAULT_WORK_ROOT / "5D3AF52D_structure_report.json")
    args = parser.parse_args()
    if args.command == "prepare":
        result = prepare(args.dat, args.key, args.rows_jsonl)
    else:
        result = build(args.dat, args.key, args.worktable, args.output_root, args.report)
    print(json.dumps(result, ensure_ascii=False))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
