#!/usr/bin/env python3
"""Prepare JPN-authoritative BRIEFING rows with semantic ENG/MLG-CN references.

This script is deliberately read-only with respect to DAT files.  It consumes the
frozen B81 lane membership, the extracted clean-JPN BRIEFING master, and the
audited active MLG-CN patch reference.  Its JSON output is authored as CSV by
Prepare-JpnBriefingTemplates.mjs so the final templates use the same artifact-tool
workflow as the other Luna translation templates.
"""

from __future__ import annotations

import argparse
import csv
import ctypes
import json
import math
import re
from collections import defaultdict
from pathlib import Path
from typing import Any, Iterable

import numpy as np
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.metrics.pairwise import cosine_similarity


ROOT = Path(__file__).resolve().parents[1]
MASTER = ROOT / "build" / "translation" / "jpn_briefing" / "jpn_briefing_master.csv"
B81_BLOCKS = ROOT / "JPN_BRIEFING_INDEX" / "build" / "B81_lane_blocks.csv"
ACTIVE_CN = (
    ROOT
    / "build"
    / "translation"
    / "mlg_cn_briefing"
    / "mlg_cn_briefing_active_text_reference.csv"
)
DEFAULT_OUTPUT = (
    ROOT / "build" / "translation" / "jpn_briefing" / "jpn_briefing_luna_rows.json"
)

JPN_LANES = ("JPN_FILES", "JPN_MISSION")
ENG_LANES = ("ENG_FILES", "ENG_MISSION")
EXPECTED_BLOCKS = {"JPN_FILES": 363, "JPN_MISSION": 106}
EXPECTED_ROWS = {"JPN_FILES": 4810, "JPN_MISSION": 835}

HAN_OR_ASCII_RE = re.compile(
    r"[\u3400-\u4dbf\u4e00-\u9fff\uf900-\ufaff]|[A-Za-z]+|\d+(?:\.\d+)?"
)
ASCII_TOKEN_RE = re.compile(r"[A-Za-z]+|\d+(?:\.\d+)?")


def read_csv(path: Path) -> list[dict[str, str]]:
    with path.open("r", encoding="utf-8-sig", newline="") as handle:
        return list(csv.DictReader(handle))


def hex_int(value: str) -> int:
    return int(value, 16)


def distinct_nonempty(values: Iterable[str]) -> list[str]:
    seen: set[str] = set()
    result: list[str] = []
    for value in values:
        if value and value not in seen:
            seen.add(value)
            result.append(value)
    return result


def chinese_variant(value: str, flag: int) -> str:
    """Use the local Windows NLS tables to bridge simplified/traditional forms."""
    if not value or not hasattr(ctypes, "windll"):
        return value
    mapper = ctypes.windll.kernel32.LCMapStringEx
    needed = mapper("zh-CN", flag, value, len(value), None, 0, None, None, None)
    if needed <= 0:
        return value
    output = ctypes.create_unicode_buffer(needed)
    written = mapper(
        "zh-CN", flag, value, len(value), output, needed, None, None, None
    )
    return output.value if written > 0 else value


def semantic_text(value: str) -> str:
    def selected(text: str) -> str:
        return " ".join(HAN_OR_ASCII_RE.findall(text.lower()))

    simplified = chinese_variant(value, 0x02000000)
    traditional = chinese_variant(value, 0x04000000)
    return f"{selected(value)} V {selected(simplified)} V {selected(traditional)}"


def row_text(rows: list[dict[str, str]], field: str) -> str:
    return "".join(row.get(field, "") for row in rows)


def block_id(rows: list[dict[str, str]]) -> str:
    return next((row["briefing_id"] for row in rows if row.get("briefing_id")), "")


def block_semantic_pairs(
    jpn_offsets: list[int],
    eng_offsets: list[int],
    master_by_offset: dict[int, list[dict[str, str]]],
    cn_by_offset: dict[int, list[dict[str, str]]],
    family: str,
) -> tuple[list[dict[str, Any]], np.ndarray]:
    if not jpn_offsets or not eng_offsets:
        return [], np.empty((len(jpn_offsets), len(eng_offsets)))

    jpn_docs = [
        semantic_text(row_text(master_by_offset[offset], "jpn_text"))
        for offset in jpn_offsets
    ]
    cn_docs = [
        semantic_text(
            "".join(
                row["patched_text"] if row.get("text_changed") == "YES" else ""
                for row in cn_by_offset.get(offset, [])
            )
        )
        for offset in eng_offsets
    ]
    vectorizer = TfidfVectorizer(
        analyzer="char", ngram_range=(1, 3), sublinear_tf=True
    )
    matrix = vectorizer.fit_transform(jpn_docs + cn_docs)
    similarities = cosine_similarity(
        matrix[: len(jpn_offsets)], matrix[len(jpn_offsets) :]
    )
    best_eng = similarities.argmax(axis=1)
    best_jpn = similarities.argmax(axis=0)

    matches: list[dict[str, Any]] = []
    for jpn_index, eng_index_value in enumerate(best_eng):
        eng_index = int(eng_index_value)
        if int(best_jpn[eng_index]) != jpn_index:
            continue
        jpn_sorted = np.sort(similarities[jpn_index])
        eng_sorted = np.sort(similarities[:, eng_index])
        jpn_margin = float(jpn_sorted[-1] - jpn_sorted[-2]) if len(jpn_sorted) > 1 else 1.0
        eng_margin = float(eng_sorted[-1] - eng_sorted[-2]) if len(eng_sorted) > 1 else 1.0
        score = float(similarities[jpn_index, eng_index])
        if score < 0.10:
            continue
        if score < 0.22 and (jpn_margin < 0.01 or eng_margin < 0.01):
            continue
        matches.append(
            {
                "jpn_offsets": [jpn_offsets[jpn_index]],
                "eng_offsets": [eng_offsets[eng_index]],
                "block_score": score,
                "reference_status": "AUX_REFERENCE_SEMANTIC_ALIGNED",
                "reference_method": f"{family}_RECIPROCAL_BLOCK_SEMANTIC_PLUS_CONTEXT_DP",
            }
        )
    return matches, similarities


def add_bracketed_context_matches(
    matches: list[dict[str, Any]],
    jpn_offsets: list[int],
    eng_offsets: list[int],
    similarities: np.ndarray,
    family: str,
) -> list[dict[str, Any]]:
    """Fill only tiny one-to-one gaps bracketed by the same semantic anchors."""
    by_jpn = {match["jpn_offsets"][0]: match for match in matches}
    by_eng = {match["eng_offsets"][0]: match for match in matches}
    jpn_pos = {offset: index for index, offset in enumerate(jpn_offsets)}
    eng_pos = {offset: index for index, offset in enumerate(eng_offsets)}

    anchor_pairs = sorted(
        (jpn_pos[j], eng_pos[match["eng_offsets"][0]]) for j, match in by_jpn.items()
    )
    additions: list[dict[str, Any]] = []
    for (left_j, left_e), (right_j, right_e) in zip(anchor_pairs, anchor_pairs[1:]):
        jpn_gap = right_j - left_j - 1
        eng_gap = right_e - left_e - 1
        if jpn_gap != eng_gap or not 1 <= jpn_gap <= 3:
            continue
        jpn_slice = jpn_offsets[left_j + 1 : right_j]
        eng_slice = eng_offsets[left_e + 1 : right_e]
        if any(offset in by_jpn for offset in jpn_slice):
            continue
        if any(offset in by_eng for offset in eng_slice):
            continue
        for jpn_offset, eng_offset in zip(jpn_slice, eng_slice):
            j = jpn_pos[jpn_offset]
            e = eng_pos[eng_offset]
            if family == "FILES" and float(similarities[j, e]) < 0.04:
                # FILES lacks Mission's scene-id structure.  A bracketing pair
                # alone is not enough when the block has virtually no lexical
                # evidence; leave it unmapped instead of manufacturing a ref.
                continue
            additions.append(
                {
                    "jpn_offsets": [jpn_offset],
                    "eng_offsets": [eng_offset],
                    "block_score": float(similarities[j, e]),
                    "reference_status": "AUX_REFERENCE_CONTEXT_ALIGNED",
                    "reference_method": f"{family}_BRACKETED_LOCAL_CONTEXT_PLUS_ROW_DP",
                }
            )
            by_jpn[jpn_offset] = additions[-1]
            by_eng[eng_offset] = additions[-1]
    return matches + additions


def ascii_similarity(left: str, right: str) -> float:
    left_tokens = set(ASCII_TOKEN_RE.findall(left.lower()))
    right_tokens = set(ASCII_TOKEN_RE.findall(right.lower()))
    if not left_tokens or not right_tokens:
        return 0.0
    return len(left_tokens & right_tokens) / len(left_tokens | right_tokens)


def align_rows(
    jpn_rows: list[dict[str, str]],
    eng_rows: list[dict[str, str]],
    cn_lookup: dict[tuple[int, int], dict[str, str]],
) -> list[dict[str, Any]]:
    """Ordered row alignment supporting exactly 1:1, 1:N, and N:1 groups."""
    if not jpn_rows or not eng_rows:
        return []
    jpn_values = [row["jpn_text"] for row in jpn_rows]
    cn_values = []
    for row in eng_rows:
        key = (hex_int(row["block_file_offset"]), int(row["text_index"]))
        patch = cn_lookup.get(key)
        cn_values.append(
            patch["patched_text"]
            if patch and patch.get("text_changed") == "YES"
            else ""
        )

    corpus = [semantic_text(value) for value in jpn_values + cn_values]
    if any(value.strip() for value in corpus):
        vectorizer = TfidfVectorizer(
            analyzer="char", ngram_range=(1, 3), sublinear_tf=True
        ).fit(corpus)
        vectors = vectorizer.transform(corpus)
        row_similarities = cosine_similarity(
            vectors[: len(jpn_values)], vectors[len(jpn_values) :]
        )
    else:
        vectorizer = None
        row_similarities = np.zeros((len(jpn_values), len(cn_values)))

    score_cache: dict[tuple[int, int, int, int], float] = {}

    def group_score(i: int, a: int, j: int, b: int) -> float:
        cache_key = (i, a, j, b)
        if cache_key in score_cache:
            return score_cache[cache_key]
        left = "".join(jpn_values[i : i + a])
        right = "".join(cn_values[j : j + b])
        semantic = 0.0
        if vectorizer is not None:
            local = row_similarities[i : i + a, j : j + b]
            if local.size:
                semantic = 0.65 * float(local.max()) + 0.35 * float(local.mean())
        length_similarity = math.exp(
            -abs(math.log((len(left) + 12.0) / (len(right) + 12.0)))
        )
        score = (
            6.0 * semantic
            + 0.8 * length_similarity
            + 0.8 * ascii_similarity(left, right)
            - 0.22 * (a + b - 2)
        )
        score_cache[cache_key] = score
        return score

    n = len(jpn_rows)
    m = len(eng_rows)
    negative = -1.0e100
    dp = [[negative] * (m + 1) for _ in range(n + 1)]
    previous: list[list[tuple[int, int, int, int] | None]] = [
        [None] * (m + 1) for _ in range(n + 1)
    ]
    dp[0][0] = 0.0
    operations = [(1, 1)] + [(1, size) for size in range(2, 5)] + [
        (size, 1) for size in range(2, 5)
    ]
    for i in range(n + 1):
        for j in range(m + 1):
            current = dp[i][j]
            if current <= negative / 2:
                continue
            if i < n and current - 0.12 > dp[i + 1][j]:
                dp[i + 1][j] = current - 0.12
                previous[i + 1][j] = (i, j, 1, 0)
            if j < m and current - 0.10 > dp[i][j + 1]:
                dp[i][j + 1] = current - 0.10
                previous[i][j + 1] = (i, j, 0, 1)
            for a, b in operations:
                if i + a > n or j + b > m:
                    continue
                candidate = current + group_score(i, a, j, b)
                if candidate > dp[i + a][j + b]:
                    dp[i + a][j + b] = candidate
                    previous[i + a][j + b] = (i, j, a, b)

    groups: list[dict[str, Any]] = []
    i, j = n, m
    while i or j:
        step = previous[i][j]
        if step is None:
            raise RuntimeError(f"row alignment backtrack failed at ({i}, {j})")
        old_i, old_j, a, b = step
        if a and b:
            groups.append(
                {
                    "jpn_rows": jpn_rows[old_i:i],
                    "eng_rows": eng_rows[old_j:j],
                    "shape": f"{a}:{b}",
                }
            )
        i, j = old_i, old_j
    groups.reverse()
    return groups


def file_id_for(lane: str, offset: int) -> str:
    family = "FILES" if lane == "JPN_FILES" else "MISSION"
    return f"BRIEFING_{family}_BLOCK_{offset:06X}"


def reference_index(row: dict[str, str]) -> str:
    return (
        f"stream={row['stream_offset']};block={row['block_offset_in_stream']};"
        f"text={row['text_index']}"
    )


def entity_context(row: dict[str, str]) -> str:
    return (
        f"stream={row['stream_offset']};block={row['block_offset_in_stream']};"
        f"block_file={row['block_file_offset']};text_base={row['text_base_file_offset']};"
        f"capacity={row['text_capacity']}"
    )


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--master", type=Path, default=MASTER)
    parser.add_argument("--b81-blocks", type=Path, default=B81_BLOCKS)
    parser.add_argument("--active-cn", type=Path, default=ACTIVE_CN)
    parser.add_argument("--output", type=Path, default=DEFAULT_OUTPUT)
    args = parser.parse_args()

    master_rows = read_csv(args.master)
    b81_rows = read_csv(args.b81_blocks)
    active_cn_rows = read_csv(args.active_cn)
    master_columns = list(master_rows[0])

    lane_by_offset = {
        hex_int(row["block_file_offset"]): row["lane"] for row in b81_rows
    }
    text_offsets_by_lane: dict[str, list[int]] = defaultdict(list)
    for row in b81_rows:
        if row["is_text_bearing"].upper() == "TRUE":
            text_offsets_by_lane[row["lane"]].append(hex_int(row["block_file_offset"]))
    for offsets in text_offsets_by_lane.values():
        offsets.sort()

    master_by_offset: dict[int, list[dict[str, str]]] = defaultdict(list)
    for row in master_rows:
        offset = hex_int(row["block_file_offset"])
        if offset in lane_by_offset:
            master_by_offset[offset].append(row)
    for rows in master_by_offset.values():
        rows.sort(key=lambda row: int(row["text_index"]))

    for lane in JPN_LANES:
        offsets = text_offsets_by_lane[lane]
        row_count = sum(len(master_by_offset[offset]) for offset in offsets)
        if len(offsets) != EXPECTED_BLOCKS[lane] or row_count != EXPECTED_ROWS[lane]:
            raise RuntimeError(
                f"{lane} frozen input mismatch: blocks={len(offsets)}, rows={row_count}"
            )

    cn_by_offset: dict[int, list[dict[str, str]]] = defaultdict(list)
    cn_lookup: dict[tuple[int, int], dict[str, str]] = {}
    for row in active_cn_rows:
        offset = hex_int(row["source_block_file_offset"])
        if lane_by_offset.get(offset) not in ENG_LANES:
            continue
        cn_by_offset[offset].append(row)
        key = (offset, int(row["text_index"]))
        if key in cn_lookup:
            raise RuntimeError(f"duplicate active CN reference key: {key}")
        cn_lookup[key] = row
    for rows in cn_by_offset.values():
        rows.sort(key=lambda row: int(row["text_index"]))

    for (offset, text_index), patch in cn_lookup.items():
        source = next(
            (
                row
                for row in master_by_offset[offset]
                if int(row["text_index"]) == text_index
            ),
            None,
        )
        if source is None or source["jpn_text"] != patch["original_text"]:
            raise RuntimeError(
                f"ENG/active-CN source mismatch at 0x{offset:X} text {text_index}"
            )

    block_matches: list[dict[str, Any]] = []

    # Mission IDs are the strongest available structure/context anchor.  Duplicate
    # IDs are intentionally aligned as combined ordered groups, not forced blockwise.
    jpn_mission_by_id: dict[str, list[int]] = defaultdict(list)
    eng_mission_by_id: dict[str, list[int]] = defaultdict(list)
    for offset in text_offsets_by_lane["JPN_MISSION"]:
        identifier = block_id(master_by_offset[offset])
        if identifier:
            jpn_mission_by_id[identifier].append(offset)
    for offset in text_offsets_by_lane["ENG_MISSION"]:
        identifier = block_id(master_by_offset[offset])
        if identifier:
            eng_mission_by_id[identifier].append(offset)
    for identifier in sorted(set(jpn_mission_by_id) & set(eng_mission_by_id)):
        block_matches.append(
            {
                "jpn_offsets": jpn_mission_by_id[identifier],
                "eng_offsets": eng_mission_by_id[identifier],
                "block_score": 1.0,
                "reference_status": "AUX_REFERENCE_CONTEXT_ALIGNED",
                "reference_method": "MISSION_EXACT_BRIEFING_ID_PLUS_CONTEXT_DP",
                "briefing_id": identifier,
            }
        )

    matched_jpn = {offset for match in block_matches for offset in match["jpn_offsets"]}
    matched_eng = {offset for match in block_matches for offset in match["eng_offsets"]}

    for family in ("FILES", "MISSION"):
        jpn_offsets = [
            offset
            for offset in text_offsets_by_lane[f"JPN_{family}"]
            if offset not in matched_jpn and not block_id(master_by_offset[offset])
        ]
        eng_offsets = [
            offset
            for offset in text_offsets_by_lane[f"ENG_{family}"]
            if offset not in matched_eng and not block_id(master_by_offset[offset])
        ]
        semantic_matches, similarities = block_semantic_pairs(
            jpn_offsets, eng_offsets, master_by_offset, cn_by_offset, family
        )
        semantic_matches = add_bracketed_context_matches(
            semantic_matches,
            jpn_offsets,
            eng_offsets,
            similarities,
            family,
        )
        block_matches.extend(semantic_matches)
        matched_jpn.update(
            offset for match in semantic_matches for offset in match["jpn_offsets"]
        )
        matched_eng.update(
            offset for match in semantic_matches for offset in match["eng_offsets"]
        )

    row_reference: dict[tuple[int, int], dict[str, Any]] = {}
    shape_counts: dict[str, int] = defaultdict(int)
    for match in block_matches:
        jpn_rows = [
            row
            for offset in match["jpn_offsets"]
            for row in master_by_offset[offset]
        ]
        eng_rows = [
            row
            for offset in match["eng_offsets"]
            for row in master_by_offset[offset]
        ]
        for group in align_rows(jpn_rows, eng_rows, cn_lookup):
            source_rows = group["eng_rows"]
            eng_reference = "".join(row["jpn_text"] for row in source_rows)
            old_cn_parts: list[str] = []
            source_keys: list[str] = []
            for row in source_rows:
                offset = hex_int(row["block_file_offset"])
                text_index = int(row["text_index"])
                source_keys.append(f"0x{offset:X}#{text_index}")
                patch = cn_lookup.get((offset, text_index))
                if patch and patch.get("text_changed") == "YES":
                    old_cn_parts.append(patch["patched_text"])
            old_cn_reference = "".join(old_cn_parts)
            jpn_block_text = ",".join(
                f"0x{hex_int(row['block_file_offset']):X}" for row in group["jpn_rows"]
            )
            eng_block_text = ",".join(
                f"0x{hex_int(row['block_file_offset']):X}" for row in source_rows
            )
            reason = (
                "JPN is authoritative; auxiliary alignment="
                f"{match['reference_method']}; shape={group['shape']}; "
                f"JPN blocks={jpn_block_text}; ENG blocks={eng_block_text}; "
                f"ENG source rows={','.join(source_keys)}; "
                f"block_semantic_score={match['block_score']:.6f}."
            )
            shape_counts[group["shape"]] += 1
            for row in group["jpn_rows"]:
                key = (hex_int(row["block_file_offset"]), int(row["text_index"]))
                if key in row_reference:
                    raise RuntimeError(f"duplicate JPN row reference assignment: {key}")
                row_reference[key] = {
                    "mlg_cn_reference": old_cn_reference,
                    "mlg_cn_reference_variants": json.dumps(
                        [old_cn_reference] if old_cn_reference else [], ensure_ascii=False
                    ),
                    "eng_reference": eng_reference,
                    "eng_reference_variants": json.dumps(
                        [eng_reference] if eng_reference else [], ensure_ascii=False
                    ),
                    "reference_status": match["reference_status"],
                    "reference_method": match["reference_method"],
                    "reference_reason": reason,
                    "eng_source_rows_json": json.dumps(source_keys, ensure_ascii=False),
                    "alignment_shape": group["shape"],
                }

    template_columns = [
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
        "mlg_cn_reference",
        "mlg_cn_reference_variants",
        "eng_reference",
        "eng_reference_variants",
        "reference_status",
        "reference_method",
        "reference_reason",
    ]
    auxiliary_columns = [
        "lane",
        "file_id",
        "mlg_cn_reference",
        "mlg_cn_reference_variants",
        "eng_reference",
        "eng_reference_variants",
        "reference_status",
        "reference_method",
        "reference_reason",
        "eng_source_rows_json",
        "alignment_shape",
    ]

    template_rows: list[dict[str, Any]] = []
    aligned_master_rows: list[dict[str, Any]] = []
    seen_jpn_keys: set[tuple[int, int]] = set()
    block_counts: dict[str, int] = defaultdict(int)
    row_counts: dict[str, int] = defaultdict(int)
    for lane in JPN_LANES:
        for offset in text_offsets_by_lane[lane]:
            rows = master_by_offset[offset]
            file_id = file_id_for(lane, offset)
            block_counts[lane] += 1
            for position, row in enumerate(rows):
                key = (offset, int(row["text_index"]))
                if key in seen_jpn_keys:
                    raise RuntimeError(f"duplicate frozen JPN row: {key}")
                seen_jpn_keys.add(key)
                row_counts[lane] += 1
                reference = row_reference.get(key)
                if reference is None:
                    reference = {
                        "mlg_cn_reference": "",
                        "mlg_cn_reference_variants": "[]",
                        "eng_reference": "",
                        "eng_reference_variants": "[]",
                        "reference_status": "NO_RELIABLE_AUX_REFERENCE",
                        "reference_method": "UNMAPPED_JPN_ONLY_OR_LOW_CONFIDENCE",
                        "reference_reason": (
                            "JPN is authoritative; no ENG/MLG-CN auxiliary reference "
                            "passed the semantic/context alignment threshold."
                        ),
                        "eng_source_rows_json": "[]",
                        "alignment_shape": "",
                    }
                reference_value = reference_index(row)
                scene = row.get("briefing_id") or (
                    "BRIEFING FILES" if lane == "JPN_FILES" else "BRIEFING MISSION"
                )
                template_row = {
                    "file_id": file_id,
                    "unique_index": int(row["text_index"]),
                    "first_reference_index": reference_value,
                    "reference_indices": json.dumps([reference_value], ensure_ascii=False),
                    "reference_count": 1,
                    "scene_context": scene,
                    "entity_context": json.dumps(
                        [entity_context(row)], ensure_ascii=False
                    ),
                    "previous_jpn_text": rows[position - 1]["jpn_text"] if position else "",
                    "jpn_text": row["jpn_text"],
                    "next_jpn_text": rows[position + 1]["jpn_text"]
                    if position + 1 < len(rows)
                    else "",
                    "jpn_control_tokens": row["jpn_control_tokens"],
                    "cn_text": "",
                    "cn_control_tokens": "",
                    "control_structure_status": "NOT_CHECKED",
                    "jpn_utf8_bytes": int(row["jpn_utf8_bytes"]),
                    "cn_utf8_bytes": "",
                    "translation_status": "NOT_STARTED",
                    "build_status": "NOT_BUILT",
                    "ingame_status": "NOT_TESTED",
                    "translation_basis": (
                        "JPN_PRIMARY; ENG_CONTEXT_AUXILIARY; MLG_CN_CONTEXT_AUXILIARY"
                    ),
                    "notes": (
                        "mechanical template; resource_class=BRIEFING_NBE; "
                        "source_objects=1; physical_jpn_row=YES"
                    ),
                    **{
                        column: reference[column]
                        for column in (
                            "mlg_cn_reference",
                            "mlg_cn_reference_variants",
                            "eng_reference",
                            "eng_reference_variants",
                            "reference_status",
                            "reference_method",
                            "reference_reason",
                        )
                    },
                }
                template_rows.append(template_row)
                aligned_master = dict(row)
                aligned_master.update(
                    {
                        "lane": lane,
                        "file_id": file_id,
                        **reference,
                    }
                )
                aligned_master_rows.append(aligned_master)

    if len(seen_jpn_keys) != 5645 or len(template_rows) != 5645:
        raise RuntimeError(
            f"frozen JPN row closure failed: unique={len(seen_jpn_keys)}, rows={len(template_rows)}"
        )
    if block_counts != EXPECTED_BLOCKS or row_counts != EXPECTED_ROWS:
        raise RuntimeError(
            f"frozen lane totals failed: blocks={dict(block_counts)}, rows={dict(row_counts)}"
        )

    file_ids = {row["file_id"] for row in template_rows}
    if len(file_ids) != 469:
        raise RuntimeError(f"template file count must be 469, got {len(file_ids)}")
    if any(row["cn_text"] for row in template_rows):
        raise RuntimeError("cn_text must remain empty in an untranslated template")

    report = {
        "status": "READY_FOR_ARTIFACT_AUTHORING",
        "source_master": str(args.master),
        "b81_lane_membership": str(args.b81_blocks),
        "active_mlg_cn_reference": str(args.active_cn),
        "template_file_count": len(file_ids),
        "template_row_count": len(template_rows),
        "lane_blocks": dict(block_counts),
        "lane_rows": dict(row_counts),
        "block_alignment_groups": len(block_matches),
        "matched_jpn_blocks": len(matched_jpn),
        "unmatched_jpn_blocks": 469 - len(matched_jpn),
        "rows_with_eng_reference": sum(
            bool(row["eng_reference"]) for row in template_rows
        ),
        "rows_with_mlg_cn_reference": sum(
            bool(row["mlg_cn_reference"]) for row in template_rows
        ),
        "rows_without_auxiliary_reference": sum(
            not row["eng_reference"] and not row["mlg_cn_reference"]
            for row in template_rows
        ),
        "alignment_shapes": dict(sorted(shape_counts.items())),
    }
    payload = {
        "template_columns": template_columns,
        "master_columns": master_columns + auxiliary_columns,
        "template_rows": template_rows,
        "aligned_master_rows": aligned_master_rows,
        "report": report,
    }
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(
        json.dumps(payload, ensure_ascii=False, indent=2) + "\n", encoding="utf-8"
    )
    print(json.dumps(report, ensure_ascii=False, indent=2))
    print(f"OUTPUT={args.output}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
