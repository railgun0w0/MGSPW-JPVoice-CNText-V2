from __future__ import annotations

import csv
import hashlib
import re
import sys
import unicodedata
from collections import defaultdict
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
ANALYSIS_ROOT = ROOT / "font" / "analysis"

from core.pc_crypto import filename_seed, outer_transform
from core.xpr_font import XprFont


FONT_SPECS = [
    ("JPN0007", "0007ccd8.xpr"),
    ("JPN000E", "000ebbe8.xpr"),
    ("JPN001C", "001cbbd1.xpr"),
    ("JPN00C7", "00c7c9f9.xpr"),
]
RESOURCE_DIRS = {
    "briefing": "BRIEFING",
    "loose_olang": "LOOSE_OLANG",
    "ohd": "OHD",
    "slot_olang": "SLOT_OLANG",
    "stagedat_olang": "STAGEDAT_OLANG",
    "ypk_gtt": "YPK_GTT",
}
RUBY_RE = re.compile(r"<R=([^,<>]*),([^<>]*)>")
ANGLE_RE = re.compile(r"<[^<>]*>")
DOLLAR_RE = re.compile(r"\$[A-Za-z0-9_]+")
PRINTF_RE = re.compile(r"%(?:\d+\$)?[-+#0-9.*hlLzjt]*[diuoxXfFeEgGaAcspn]")
BRACE_RE = re.compile(r"\{(?:\d+|[A-Za-z_][A-Za-z0-9_]*)\}")

LOADING_FILE = "00D0C740"
LOADING_INDICES = set(range(20, 57)) - {33}


def sha256(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def read_rows(path: Path) -> list[dict[str, str]]:
    with path.open("r", encoding="utf-8-sig", newline="") as handle:
        return list(csv.DictReader(handle))


def visible_text(text: str) -> tuple[str, int]:
    """Keep actual JPN display text; remove control syntax only.

    Ruby base and ruby annotation are both retained because both are rendered.
    Other angle, placeholder, brace and printf structures are removed atomically.
    """

    ruby_count = 0

    def ruby(match: re.Match[str]) -> str:
        nonlocal ruby_count
        ruby_count += 1
        return match.group(1) + match.group(2)

    rendered = RUBY_RE.sub(ruby, text or "")
    excluded = 0
    for pattern in (ANGLE_RE, DOLLAR_RE, PRINTF_RE, BRACE_RE):
        rendered, count = pattern.subn("", rendered)
        excluded += count
    return rendered, ruby_count + excluded


def is_visible_character(ch: str) -> bool:
    category = unicodedata.category(ch)
    return not category.startswith("C") and not ch.isspace() and category not in {"Zl", "Zp"}


def visible_set(text: str) -> tuple[str, int]:
    rendered, token_count = visible_text(text)
    chars = sorted({ch for ch in rendered if is_visible_character(ch)}, key=ord)
    return "".join(chars), token_count


def load_fonts() -> tuple[dict[str, XprFont], dict[str, dict[int, int]], dict[str, dict[str, str]]]:
    fonts: dict[str, XprFont] = {}
    maps: dict[str, dict[int, int]] = {}
    metadata: dict[str, dict[str, str]] = {}
    for name, filename in FONT_SPECS:
        path = ROOT / "font" / "JPN" / filename
        encrypted = path.read_bytes()
        plaintext = outer_transform(encrypted, filename_seed(filename))
        font = XprFont(plaintext)
        mapped = font.font_data.mapped()
        fonts[name] = font
        maps[name] = mapped
        metadata[name] = {
            "filename": filename,
            "encrypted_sha256": sha256(encrypted),
            "decrypted_sha256": sha256(plaintext),
            "record_count": str(len(font.font_data.glyphs)),
            "mapped_count": str(len(mapped)),
            "last_code": f"U+{font.font_data.last_code:04X}",
            "texture": f"{font.texture.width}x{font.texture.height}",
        }
    return fonts, maps, metadata


def font_codepoint_sets(maps: dict[str, dict[int, int]]) -> None:
    path = ANALYSIS_ROOT / "jpn_font_codepoint_sets.csv"
    with path.open("w", encoding="utf-8-sig", newline="") as handle:
        writer = csv.writer(handle)
        writer.writerow(["font", "xpr", "character", "codepoint", "glyph_index"])
        for name, filename in FONT_SPECS:
            for cp, glyph_index in sorted(maps[name].items()):
                writer.writerow([name, filename, chr(cp), f"U+{cp:04X}", glyph_index])


def corpus_rows() -> list[dict[str, object]]:
    rows: list[dict[str, object]] = []
    for directory, resource_class in RESOURCE_DIRS.items():
        for path in sorted((ROOT / "translations" / directory).glob("*.csv")):
            for row in read_rows(path):
                if "jpn_text" not in row or not row.get("jpn_text"):
                    continue
                chars, token_count = visible_set(row["jpn_text"])
                try:
                    unique_index = int(row.get("unique_index", ""))
                except ValueError:
                    unique_index = None
                try:
                    reference_index = int(row.get("first_reference_index", ""))
                except ValueError:
                    reference_index = None
                rows.append(
                    {
                        "resource_class": resource_class,
                        "file_id": row.get("file_id", ""),
                        "unique_index": unique_index,
                        "reference_index": reference_index,
                        "reference_indices": row.get("reference_indices", ""),
                        "reference_count": row.get("reference_count", ""),
                        "entity_context": row.get("entity_context", ""),
                        "jpn_text": row["jpn_text"],
                        "visible_unique_chars": chars,
                        "token_count": token_count,
                    }
                )
    return rows


def coverage(chars: str, mapped: dict[int, int]) -> tuple[str, str, float | None]:
    present = "".join(ch for ch in chars if ord(ch) in mapped)
    missing = "".join(ch for ch in chars if ord(ch) not in mapped)
    ratio = None if not chars else 100.0 * len(present) / len(chars)
    return present, missing, ratio


def pct(value: float | None) -> str:
    return "NA" if value is None else f"{value:.2f}%"


def jaccard(left: set[str], right: set[str]) -> float:
    if not left and not right:
        return 1.0
    union = left | right
    return 0.0 if not union else len(left & right) / len(union)


def main() -> None:
    fonts, maps, metadata = load_fonts()
    font_codepoint_sets(maps)
    rows = corpus_rows()

    loading_rows = [
        row
        for row in rows
        if row["resource_class"] == "LOOSE_OLANG"
        and row["file_id"] == LOADING_FILE
        and row["unique_index"] in LOADING_INDICES
    ]
    loading_keys = {
        (row["resource_class"], row["file_id"], row["unique_index"])
        for row in loading_rows
    }
    loading_status_key = ("LOOSE_OLANG", LOADING_FILE, 33)
    loading_sets = [set(row["visible_unique_chars"]) for row in loading_rows]
    loading_union = set().union(*loading_sets) if loading_sets else set()

    annotated: list[dict[str, object]] = []
    for row in rows:
        chars = str(row["visible_unique_chars"])
        char_set = set(chars)
        p1, m1, c1 = coverage(chars, maps["JPN001C"])
        _, _, c7 = coverage(chars, maps["JPN0007"])
        _, _, ce = coverage(chars, maps["JPN000E"])
        _, _, c7c = coverage(chars, maps["JPN00C7"])
        coverages = {"JPN0007": c7, "JPN000E": ce, "JPN001C": c1, "JPN00C7": c7c}
        lower_other = [name for name in ("JPN0007", "JPN000E", "JPN00C7") if (coverages[name] or 0) < 100.0]
        max_fixture_similarity = max((jaccard(char_set, item) for item in loading_sets), default=0.0)
        annotated.append(
            {
                **row,
                "001c_covered_chars": p1,
                "001c_missing_chars": m1,
                "001c_coverage": c1,
                "0007_coverage": c7,
                "000e_coverage": ce,
                "00c7_coverage": c7c,
                "loading_fixture_similarity_max": max_fixture_similarity,
                "loading_union_similarity": jaccard(char_set, loading_union),
                "is_loading_fixture": (
                    row["resource_class"], row["file_id"], row["unique_index"]
                ) in loading_keys,
                "is_loading_status_excluded": (
                    row["resource_class"], row["file_id"], row["unique_index"]
                ) == loading_status_key,
                "candidate_status": (
                    "NO_VISIBLE_CHARS"
                    if not chars
                    else "FONT_COVERAGE_CANDIDATE"
                    if not m1
                    else "NOT_CANDIDATE"
                ),
                "candidate_value": "HIGH_VALUE_CANDIDATE" if not m1 and lower_other else "ORDINARY_CANDIDATE" if not m1 else "",
                "lower_other_fonts": ";".join(lower_other),
            }
        )

    out = ANALYSIS_ROOT / "small_jpn_text_coverage_candidates.csv"
    fields = [
        "resource_class",
        "file_id",
        "unique_index",
        "reference_index",
        "reference_indices",
        "reference_count",
        "jpn_text",
        "visible_unique_chars",
        "001c_covered_chars",
        "001c_missing_chars",
        "001c_coverage",
        "0007_coverage",
        "000e_coverage",
        "00c7_coverage",
        "loading_fixture_similarity_max",
        "loading_union_similarity",
        "is_loading_fixture",
        "candidate_status",
        "candidate_value",
        "lower_other_fonts",
    ]
    with out.open("w", encoding="utf-8-sig", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=fields)
        writer.writeheader()
        for row in annotated:
            output = {field: row.get(field, "") for field in fields}
            for field in ("001c_coverage", "0007_coverage", "000e_coverage", "00c7_coverage"):
                output[field] = pct(output[field])
            output["loading_fixture_similarity_max"] = f"{float(output['loading_fixture_similarity_max']):.6f}"
            output["loading_union_similarity"] = f"{float(output['loading_union_similarity']):.6f}"
            writer.writerow(output)

    # Maximal consecutive runs of 001c-complete records within one resource.
    region_rows: list[dict[str, object]] = []
    grouped: dict[tuple[str, str], list[dict[str, object]]] = defaultdict(list)
    for row in annotated:
        if row["candidate_status"] == "FONT_COVERAGE_CANDIDATE" and row["unique_index"] is not None:
            grouped[(str(row["resource_class"]), str(row["file_id"]))].append(row)
    for (resource_class, file_id), group in grouped.items():
        group.sort(key=lambda item: int(item["unique_index"]))
        run: list[dict[str, object]] = []
        previous: int | None = None
        for row in group + [None]:
            current = None if row is None else int(row["unique_index"])
            crosses_loading_status_gap = (
                run
                and row is not None
                and (
                    run[-1]["is_loading_status_excluded"]
                    or row["is_loading_status_excluded"]
                )
            )
            if run and (current is None or current != previous + 1 or crosses_loading_status_gap):
                region_rows.append({"resource_class": resource_class, "file_id": file_id, "rows": run[:]})
                run = []
            if row is not None:
                run.append(row)
                previous = current
    regions_path = ANALYSIS_ROOT / "small_jpn_candidate_regions.csv"
    with regions_path.open("w", encoding="utf-8-sig", newline="") as handle:
        fields = [
            "resource_class",
            "file_id",
            "scope",
            "unique_index_start",
            "unique_index_end",
            "row_count",
            "all_001c_100_percent",
            "high_value_count",
            "ordinary_count",
            "min_0007_coverage",
            "min_000e_coverage",
            "min_00c7_coverage",
            "max_loading_fixture_similarity",
            "loading_union_similarity",
            "unique_indices",
            "sample_jpn_texts",
        ]
        writer = csv.DictWriter(handle, fieldnames=fields)
        writer.writeheader()
        for region in sorted(region_rows, key=lambda item: (-len(item["rows"]), item["resource_class"], item["file_id"], int(item["rows"][0]["unique_index"]))):
            r = region["rows"]
            indices = [int(item["unique_index"]) for item in r]
            if all(item["is_loading_fixture"] for item in r):
                scope = "KNOWN_LOADING_FIXTURE"
            elif all(item["is_loading_status_excluded"] for item in r):
                scope = "KNOWN_LOADING_STATUS_EXCLUDED"
            else:
                scope = "OUTSIDE_LOADING"
            samples = [str(item["jpn_text"]).replace("\n", "\\n") for item in r[:3]]
            writer.writerow(
                {
                    "resource_class": region["resource_class"],
                    "file_id": region["file_id"],
                    "scope": scope,
                    "unique_index_start": indices[0],
                    "unique_index_end": indices[-1],
                    "row_count": len(r),
                    "all_001c_100_percent": "YES",
                    "high_value_count": sum(item["candidate_value"] == "HIGH_VALUE_CANDIDATE" for item in r),
                    "ordinary_count": sum(item["candidate_value"] == "ORDINARY_CANDIDATE" for item in r),
                    "min_0007_coverage": pct(min(item["0007_coverage"] for item in r)),
                    "min_000e_coverage": pct(min(item["000e_coverage"] for item in r)),
                    "min_00c7_coverage": pct(min(item["00c7_coverage"] for item in r)),
                    "max_loading_fixture_similarity": f"{max(item['loading_fixture_similarity_max'] for item in r):.6f}",
                    "loading_union_similarity": f"{max(item['loading_union_similarity'] for item in r):.6f}",
                    "unique_indices": ";".join(str(x) for x in indices),
                    "sample_jpn_texts": " || ".join(samples),
                }
            )

    full = [row for row in annotated if row["candidate_status"] == "FONT_COVERAGE_CANDIDATE"]
    high = [row for row in full if row["candidate_value"] == "HIGH_VALUE_CANDIDATE"]
    ordinary = [row for row in full if row["candidate_value"] == "ORDINARY_CANDIDATE"]
    external_regions = [
        region
        for region in region_rows
        if not any(
            item["is_loading_fixture"] or item["is_loading_status_excluded"]
            for item in region["rows"]
        )
    ]
    loading_candidate = [row for row in annotated if row["is_loading_fixture"]]

    report: list[str] = [
        "# SMALL_JPN_TEXT_COVERAGE_REVERSE_AUDIT",
        "",
        "## 结论",
        "",
        "本轮只做 JPN 原文字符覆盖反推；没有修改 XPR、translation、mapping，也没有进行 EXE callsite 或 runtime probe。",
        "",
        f"- 扫描 canonical production corpus：`translations/**`，共 `{len(annotated)}` 条非空 `jpn_text` 记录。",
        "- `work/luna_translation_templates/**` 的有效 production-key 记录与 `translations/**` 完全重复，因此不重复计数；其中额外的无 production index 模板行不作为实际资源记录。",
        f"- 001c 完整覆盖文本：**{len(full)}**。",
        f"- 其中 HIGH_VALUE_CANDIDATE：**{len(high)}**；其它字体也同样完整覆盖的 ORDINARY_CANDIDATE：**{len(ordinary)}**。",
        f"- 连续 001c-complete region：**{len(region_rows)}**；其中包含 Loading positive fixture 的 region：**{sum(all(item['is_loading_fixture'] for item in region['rows']) for region in region_rows)}**；其余候选 region：**{len(external_regions)}**。",
        "",
        "`FONT_COVERAGE_CANDIDATE` 只表示字符集合与 JPN001C 完整相交；不表示已经确认 runtime 使用 001c。",
        "",
        "## 四套字体的有效 charmap",
        "",
        "record 0 / fallback 不计入有效 mapped codepoint。完整逐 codepoint 导出见 [jpn_font_codepoint_sets.csv](jpn_font_codepoint_sets.csv)。",
        "",
        "| font | XPR | records | mapped codepoints | texture | encrypted SHA256 | decrypted SHA256 |",
        "|---|---|---:|---:|---|---|---|",
    ]
    for name, filename in FONT_SPECS:
        meta = metadata[name]
        report.append(
            f"| {name} | `{filename}` | {meta['record_count']} | {meta['mapped_count']} | {meta['texture']} | `{meta['encrypted_sha256']}` | `{meta['decrypted_sha256']}` |"
        )

    report += [
        "",
        "## Coverage 定义",
        "",
        "- `jpn_text` 是唯一输入；不读取 `cn_text`。",
        "- `<R=base,ruby>` 保留 `base` 和 `ruby` 两部分，因为两者均为实际显示文字。",
        "- 其它 `<...>` 控制/markup、`$placeholder`、printf placeholder、`{placeholder}`、换行、空格和 Unicode control/format 字符排除。",
        "- 每条记录以去重后的实际显示字符集合计算 coverage；coverage = mapped 字符数 / visible unique 字符数。",
        "- 001c 完整但其它任一 JPN 字体低于 100% 时标记 `HIGH_VALUE_CANDIDATE`；四套均为 100% 时仅标记 `ORDINARY_CANDIDATE`。",
        "",
        "## 已知 Loading positive fixture",
        "",
        f"Loading 锚定区域为 `LOOSE_OLANG/00D0C740.csv` 的 unique_index `20–56`，排除 `33`，共 `{len(loading_candidate)}` 条原始 JPN 记录。",
        "这 36 条只作为已知 positive fixture 分析，不把其 001c coverage 当成其它资源的 runtime 证明。",
        "",
        "| unique_index | reference_index | 001c | 0007 | 000e | 00c7 | JPN |",
        "|---:|---:|---:|---:|---:|---:|---|",
    ]
    for row in loading_candidate:
        report.append(
            f"| {row['unique_index']} | {row['reference_index']} | {pct(row['001c_coverage'])} | {pct(row['0007_coverage'])} | {pct(row['000e_coverage'])} | {pct(row['00c7_coverage'])} | {str(row['jpn_text']).replace(chr(10), '<br>')} |"
        )

    report += [
        "",
        "## 外部连续候选区域",
        "",
        "下面只列出不属于已知 Loading 区域的连续候选；完整结果见 [small_jpn_candidate_regions.csv](small_jpn_candidate_regions.csv)。",
        "",
        "| resource_class | file_id | unique_index | rows | high-value | ordinary | min 0007 | min 000e | min 00c7 | max Loading similarity | sample |",
        "|---|---|---:|---:|---:|---:|---:|---:|---:|---:|---|",
    ]
    shown = sorted(external_regions, key=lambda item: (-len(item["rows"]), -sum(x["candidate_value"] == "HIGH_VALUE_CANDIDATE" for x in item["rows"]), item["resource_class"], item["file_id"]))[:80]
    for region in shown:
        r = region["rows"]
        first = int(r[0]["unique_index"])
        last = int(r[-1]["unique_index"])
        samples = " || ".join(str(x["jpn_text"]).replace("\n", "\\n")[:100] for x in r[:2])
        report.append(
            f"| {region['resource_class']} | `{region['file_id']}` | {first}–{last} | {len(r)} | {sum(x['candidate_value'] == 'HIGH_VALUE_CANDIDATE' for x in r)} | {sum(x['candidate_value'] == 'ORDINARY_CANDIDATE' for x in r)} | {pct(min(x['0007_coverage'] for x in r))} | {pct(min(x['000e_coverage'] for x in r))} | {pct(min(x['00c7_coverage'] for x in r))} | {max(x['loading_fixture_similarity_max'] for x in r):.3f} | {samples} |"
        )
    if not shown:
        report.append("| — | — | — | 0 | 0 | 0 | — | — | — | — | 没有外部连续候选 |")

    report += [
        "",
        "## HIGH_VALUE_CANDIDATE 说明",
        "",
        "单条记录和高价值记录的完整清单在 `small_jpn_text_coverage_candidates.csv`：筛选 `candidate_status=FONT_COVERAGE_CANDIDATE` 且 `candidate_value=HIGH_VALUE_CANDIDATE`。这些记录的 001c 为 100%，而 0007、000e 或 00c7 至少一套低于 100%；它们比四套字体都能覆盖的记录更适合作为后续 SMALL_JPN 候选，但仍需 runtime 证据。",
        "",
        "## 范围与限制",
        "",
        "本审计只反推字符集合，不反推具体 selector、resource binding、EXE callsite 或实际渲染路径。候选区域的连续性来自同一 CSV 的 `file_id + unique_index`，不是 runtime 证明。",
    ]
    (ANALYSIS_ROOT / "SMALL_JPN_TEXT_COVERAGE_REVERSE_AUDIT.md").write_text("\n".join(report) + "\n", encoding="utf-8")
    print(f"rows={len(annotated)} loading={len(loading_candidate)} full_001c={len(full)} high={len(high)} ordinary={len(ordinary)} regions={len(region_rows)} external_regions={len(external_regions)}")


if __name__ == "__main__":
    main()
