#!/usr/bin/env python3
"""Read-only analysis of MLG original versus existing MLG CN GTT frames."""

from __future__ import annotations

import importlib.util
import json
import sys
from collections import defaultdict
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
EXPERIMENTAL_TOOLS = ROOT.parent / "JPVoice_CNText_Experimental" / "tools"
MLG_ORIG_DAT = Path(r"D:\GAME\test\JPN\MGS_PW\mgspw\MLG\disc0_rel\002aba34.DAT")
MLG_KEY = Path(r"D:\GAME\test\JPN\MGS_PW\mgspw\MLG\disc0_rel\002aba34.KEY")
MLG_CN_DAT = Path(
    r"D:\GAME\test\steam 合金装备大师合集2 合金装备和平行者汉化补丁"
    r"\mgspw\MLG\disc0_rel\002aba34.DAT"
)
OUTPUT = ROOT / "build" / "analysis" / "mlg_gtt_capacity_analysis.json"
YPK_KIND = 0x1C
SPECIAL = {
    "ALIGNMENT_SPILL",
    "FRAME_GREW",
    "FRAME_SHRANK",
    "SAME_FRAME_APPARENT_OVERFLOW",
    "TOPOLOGY_CHANGED",
}


def load_module(path: Path, name: str):
    spec = importlib.util.spec_from_file_location(name, path)
    if spec is None or spec.loader is None:
        raise RuntimeError(f"cannot load module: {path}")
    module = importlib.util.module_from_spec(spec)
    sys.modules[name] = module
    spec.loader.exec_module(module)
    return module


SLOT = load_module(EXPERIMENTAL_TOOLS / "Build-JpnSlot.py", "mlg_capacity_slot")
sys.path.insert(0, str(ROOT))
from core.gtt_multi import parse_gtt_multi  # noqa: E402


def compact(value) -> str:
    return json.dumps(value, ensure_ascii=False, separators=(",", ":"))


def collect(dat_path: Path, entries, salts, seed):
    result = defaultdict(list)
    for page in range(0, len(entries), 6):
        decoded, _ = SLOT.decode_page(dat_path, entries[page], salts, seed)
        cnf = SLOT.parse_cnf(decoded)
        for tag_index, payload in cnf.segments.items():
            tag = cnf.tags[tag_index]
            if tag.kind == YPK_KIND:
                result[tag.file_id].append((page, tag_index, payload))
    return result


def group_variants(occurrences):
    variants = []
    for page, tag_index, payload in sorted(occurrences, key=lambda item: (item[0], item[1])):
        for variant in variants:
            if payload == variant["payload"]:
                variant["occurrences"].append((page, tag_index))
                break
        else:
            variants.append({"payload": payload, "occurrences": [(page, tag_index)]})
    return variants


def classify(eng, cn, required: int) -> str:
    nominal = eng.record_size - eng.header_size
    aligned = eng.aligned_size - eng.header_size
    if eng.segment_count != cn.segment_count:
        return "TOPOLOGY_CHANGED"
    if cn.record_size < eng.record_size or cn.aligned_size < eng.aligned_size:
        return "FRAME_SHRANK"
    if required > aligned and (
        cn.record_size > eng.record_size or cn.aligned_size > eng.aligned_size
    ):
        return "FRAME_GREW"
    if required > aligned and cn.aligned_size == eng.aligned_size:
        return "SAME_FRAME_APPARENT_OVERFLOW"
    if nominal < required <= aligned and cn.aligned_size == eng.aligned_size:
        return "ALIGNMENT_SPILL"
    if (
        required <= nominal
        and cn.record_size == eng.record_size
        and cn.aligned_size == eng.aligned_size
    ):
        return "SAME_FRAME_FIT"
    return "UNCLASSIFIED"


def main() -> int:
    for path in (MLG_ORIG_DAT, MLG_KEY, MLG_CN_DAT):
        if not path.is_file():
            raise FileNotFoundError(path)

    seed = SLOT.CRYPTO.filename_seed(MLG_KEY)
    _, salts, entries = SLOT.decode_key(MLG_KEY, seed)
    original = collect(MLG_ORIG_DAT, entries, salts, seed)
    chinese = collect(MLG_CN_DAT, entries, salts, seed)

    if set(original) != set(chinese):
        raise RuntimeError(
            f"YPK file_id sets differ: ENG-only={sorted(set(original)-set(chinese))}, "
            f"CN-only={sorted(set(chinese)-set(original))}"
        )

    record_pairs = []
    variant_rows = []
    record_count_changes = []
    category_counts = defaultdict(int)

    for file_id in sorted(original):
        eng_variants = group_variants(original[file_id])
        if len(eng_variants) != 1:
            raise RuntimeError(f"MLG original {file_id:08X} has {len(eng_variants)} payload variants")
        eng_payload = eng_variants[0]["payload"]
        eng_page, eng_tag = eng_variants[0]["occurrences"][0]
        eng_records = parse_gtt_multi(
            eng_payload, f"MLG_ORIG:{file_id:08X}:p{eng_page}:t{eng_tag}"
        )

        cn_variants = group_variants(chinese[file_id])
        for variant_index, variant in enumerate(cn_variants):
            cn_payload = variant["payload"]
            cn_records = parse_gtt_multi(
                cn_payload, f"MLG_CN:{file_id:08X}:variant{variant_index}"
            )
            variant_size_delta = len(cn_payload) - len(eng_payload)
            variant_rows.append(
                {
                    "file_id": f"{file_id:08X}",
                    "cn_variant": variant_index,
                    "cn_occurrences": compact(
                        [
                            {"page": page, "tag_index": tag_index}
                            for page, tag_index in variant["occurrences"]
                        ]
                    ),
                    "eng_record_count": len(eng_records),
                    "cn_record_count": len(cn_records),
                    "eng_ypk_size": len(eng_payload),
                    "cn_ypk_size": len(cn_payload),
                    "ypk_size_delta": variant_size_delta,
                    "ypk_size_grew": variant_size_delta > 0,
                }
            )
            if len(eng_records) != len(cn_records):
                record_count_changes.append(
                    {
                        "file_id": f"{file_id:08X}",
                        "cn_variant": variant_index,
                        "cn_occurrences": variant_rows[-1]["cn_occurrences"],
                        "eng_record_count": len(eng_records),
                        "cn_record_count": len(cn_records),
                        "record_count_delta": len(cn_records) - len(eng_records),
                        "eng_ypk_size": len(eng_payload),
                        "cn_ypk_size": len(cn_payload),
                        "ypk_size_delta": variant_size_delta,
                        "classification": "RECORD_COUNT_CHANGED",
                    }
                )

            for record_index in range(min(len(eng_records), len(cn_records))):
                eng = eng_records[record_index]
                cn = cn_records[record_index]
                required = sum(len(text.encode("utf-8")) + 1 for text in cn.texts)
                nominal = eng.record_size - eng.header_size
                aligned = eng.aligned_size - eng.header_size
                classification = classify(eng, cn, required)
                category_counts[classification] += 1
                next_eng = (
                    eng_records[record_index + 1].offset
                    if record_index + 1 < len(eng_records)
                    else None
                )
                next_cn = (
                    cn_records[record_index + 1].offset
                    if record_index + 1 < len(cn_records)
                    else None
                )
                record_pairs.append(
                    {
                        "file_id": f"{file_id:08X}",
                        "cn_variant": variant_index,
                        "cn_occurrences": variant_rows[-1]["cn_occurrences"],
                        "record_index": record_index,
                        "classification": classification,
                        "eng_offset": eng.offset,
                        "cn_offset": cn.offset,
                        "offset_delta": cn.offset - eng.offset,
                        "eng_segment_count": eng.segment_count,
                        "cn_segment_count": cn.segment_count,
                        "eng_header_size": eng.header_size,
                        "cn_header_size": cn.header_size,
                        "eng_record_size": eng.record_size,
                        "cn_record_size": cn.record_size,
                        "record_size_delta": cn.record_size - eng.record_size,
                        "eng_aligned_size": eng.aligned_size,
                        "cn_aligned_size": cn.aligned_size,
                        "aligned_size_delta": cn.aligned_size - eng.aligned_size,
                        "eng_nominal_capacity": nominal,
                        "eng_aligned_capacity": aligned,
                        "eng_alignment_slack": aligned - nominal,
                        "cn_required": required,
                        "slack_bytes_used": max(0, required - nominal),
                        "next_eng_offset": next_eng,
                        "next_cn_offset": next_cn,
                        "next_offset_delta": (
                            None if next_eng is None or next_cn is None else next_cn - next_eng
                        ),
                        "subsequent_record_shifted": (
                            False if next_eng is None or next_cn is None else next_cn > next_eng
                        ),
                        "eng_ypk_size": len(eng_payload),
                        "cn_ypk_size": len(cn_payload),
                        "ypk_size_delta": variant_size_delta,
                        "ypk_size_grew": variant_size_delta > 0,
                        "eng_texts": compact(list(eng.texts)),
                        "cn_texts": compact(list(cn.texts)),
                        "eng_boundaries": compact([list(pair) for pair in eng.boundaries]),
                        "cn_boundaries": compact([list(pair) for pair in cn.boundaries]),
                    }
                )

    ypk_grew = [row for row in variant_rows if row["ypk_size_delta"] > 0]
    frame_grew = [row for row in record_pairs if row["classification"] == "FRAME_GREW"]
    alignment_spill = [
        row for row in record_pairs if row["classification"] == "ALIGNMENT_SPILL"
    ]
    exceptions = [row for row in record_pairs if row["classification"] in SPECIAL]
    summary = {
        "UNIQUE_ENG_YPK": len(original),
        "CN_PAYLOAD_VARIANTS": len(variant_rows),
        "TOTAL_RECORD_PAIRS": len(record_pairs),
        "SAME_FRAME_FIT": category_counts["SAME_FRAME_FIT"],
        "ALIGNMENT_SPILL": category_counts["ALIGNMENT_SPILL"],
        "FRAME_GREW": category_counts["FRAME_GREW"],
        "FRAME_SHRANK": category_counts["FRAME_SHRANK"],
        "SAME_FRAME_APPARENT_OVERFLOW": category_counts[
            "SAME_FRAME_APPARENT_OVERFLOW"
        ],
        "TOPOLOGY_CHANGED": category_counts["TOPOLOGY_CHANGED"],
        "RECORD_COUNT_CHANGED": len(record_count_changes),
        "UNCLASSIFIED": category_counts["UNCLASSIFIED"],
        "YPK_SIZE_GREW": len(ypk_grew),
        "MAX_YPK_SIZE_GROWTH": max(
            (row["ypk_size_delta"] for row in ypk_grew), default=0
        ),
        "MAX_FRAME_GREW_ALIGNED_BYTES": max(
            (row["aligned_size_delta"] for row in frame_grew), default=0
        ),
        "MAX_FRAME_GREW_RECORD_SIZE_BYTES": max(
            (row["record_size_delta"] for row in frame_grew), default=0
        ),
        "MAX_ALIGNMENT_SPILL_BYTES": max(
            (row["slack_bytes_used"] for row in alignment_spill), default=0
        ),
    }
    payload = {
        "summary": summary,
        "record_pairs": record_pairs,
        "exceptions": exceptions,
        "ypk_variants": variant_rows,
        "record_count_changes": record_count_changes,
    }
    OUTPUT.parent.mkdir(parents=True, exist_ok=True)
    OUTPUT.write_text(json.dumps(payload, ensure_ascii=False), encoding="utf-8")
    print(json.dumps(summary, ensure_ascii=False))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
