#!/usr/bin/env python3
"""Read-only audit of production display characters against the six canonical fonts."""

from __future__ import annotations

import argparse
import csv
import re
import unicodedata
from collections import Counter, defaultdict
from pathlib import Path


ANGLE_RE = re.compile(r"<[^<>]*>")
DOLLAR_RE = re.compile(r"\$[A-Za-z0-9_]+")
PRINTF_RE = re.compile(r"%(?:\d+\$)?[sdif]")
RANGE_RE = re.compile(r"U\+([0-9A-Fa-f]{4,6})(?:-U\+([0-9A-Fa-f]{4,6}))?")

FONT_PROFILES = {
    "JPN-0007": {"mapped_count": 642, "atlas": "4096x4096", "cell": "67", "type": "clean JPN / large selector"},
    "JPN-000E": {"mapped_count": 458, "atlas": "2048x1024", "cell": "67", "type": "clean JPN / small selector"},
    "JPN-001C": {"mapped_count": 358, "atlas": "2048x1024", "cell": "66", "type": "clean JPN / small selector"},
    "JPN-00C7": {"mapped_count": 2308, "atlas": "4096x4096", "cell": "66", "type": "clean JPN / large selector"},
    "MLG-0007": {"mapped_count": 3208, "atlas": "4096x4096", "cell": "67", "type": "MLG_CN / large selector"},
    "MLG-000E": {"mapped_count": 3145, "atlas": "4096x4096", "cell": "67", "type": "MLG_CN / large selector"},
}

FONT_ORDER = ["JPN-0007", "JPN-000E", "JPN-001C", "JPN-00C7", "MLG-0007", "MLG-000E"]


def read_csv(path: Path) -> list[dict[str, str]]:
    with path.open("r", encoding="utf-8-sig", newline="") as handle:
        return list(csv.DictReader(handle))


def expand_ranges(value: str) -> set[int]:
    result: set[int] = set()
    for match in RANGE_RE.finditer(value):
        start = int(match.group(1), 16)
        end = int(match.group(2), 16) if match.group(2) else start
        result.update(range(start, end + 1))
    return result


def visible_text(text: str) -> str:
    """Remove runtime syntax while retaining both visible sides of Ruby."""
    def replace_angle(match: re.Match[str]) -> str:
        token = match.group(0)
        if token.startswith("<R=") and token.endswith(">"):
            payload = token[3:-1]
            if "," in payload:
                base, reading = payload.split(",", 1)
                return base + reading
            return ""
        if token.startswith("<I=") or token.startswith("<C=") or token == "<->":
            return ""
        if re.match(r"<[A-Za-z_-]+(?:=|>)", token):
            return ""
        return token

    value = ANGLE_RE.sub(replace_angle, text or "")
    value = DOLLAR_RE.sub("", value)
    value = PRINTF_RE.sub("", value)
    value = value.replace("\\r", "").replace("\\n", "").replace("\\t", "")
    return "".join(
        char for char in value
        if not char.isspace() and not unicodedata.category(char).startswith("C")
    )


def unicode_block(codepoint: int) -> str:
    ranges = (
        (0x4E00, 0x9FFF, "CJK Unified Ideographs"),
        (0x3400, 0x4DBF, "CJK Unified Ideographs Extension A"),
        (0x3040, 0x309F, "Hiragana"),
        (0x30A0, 0x30FF, "Katakana"),
        (0xFF00, 0xFFEF, "Halfwidth and Fullwidth Forms"),
        (0x3000, 0x303F, "CJK Symbols and Punctuation"),
        (0x2000, 0x206F, "General Punctuation"),
        (0x0000, 0x007F, "Basic Latin"),
        (0x0080, 0x00FF, "Latin-1 Supplement"),
    )
    for start, end, name in ranges:
        if start <= codepoint <= end:
            return name
    return "Other"


def display_name(char: str) -> str:
    return unicodedata.name(char, "<unnamed>")


def compact_context(text: str, limit: int = 160) -> str:
    value = visible_text(text)
    return value if len(value) <= limit else value[: limit - 1] + "…"


def add_row(
    rows: list[tuple[str, str, str, str]],
    resource_class: str,
    source_label: str,
    row_number: int,
    row: dict[str, str],
) -> None:
    text = row.get("cn_text", "") or ""
    rendered = visible_text(text)
    if not rendered:
        return
    file_id = row.get("file_id") or row.get("resource_id") or source_label
    index = row.get("record_index") or row.get("unique_index") or str(row_number)
    label = f"{resource_class}/{file_id}#{index}"
    rows.append((rendered, resource_class, label, compact_context(text)))


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("v2_root", type=Path)
    args = parser.parse_args()
    root = args.v2_root.resolve()

    analysis_root = root / "font" / "analysis"
    charmap_rows = read_csv(analysis_root / "FONT_SIX_UNIQUE_CHARMAP.csv")
    font_maps: dict[str, set[int]] = {}
    charmap_sha: dict[str, str] = {}
    for row in charmap_rows:
        font_id = row["unique_id"]
        font_maps[font_id] = expand_ranges(row["complete_unicode_ranges"])
        charmap_sha[font_id] = row.get("charmap_sha256", "")

    production_rows: list[tuple[str, str, str, str]] = []
    source_files: list[str] = []
    manifest_path = root / "build" / "translation" / "compiled_translation_manifest.csv"
    manifest = read_csv(manifest_path)
    source_files.append(manifest_path.relative_to(root).as_posix())
    for number, row in enumerate(manifest, start=2):
        add_row(production_rows, row.get("resource_class", "UNKNOWN"), "manifest", number, row)

    briefing_dir = root / "translations" / "briefing"
    briefing_rows = 0
    for path in sorted(briefing_dir.glob("*.csv")):
        source_files.append(path.relative_to(root).as_posix())
        rows = read_csv(path)
        briefing_rows += len(rows)
        for number, row in enumerate(rows, start=2):
            row.setdefault("file_id", path.stem)
            add_row(production_rows, "BRIEFING", path.stem, number, row)

    occurrences: Counter[int] = Counter()
    resource_classes: defaultdict[int, set[str]] = defaultdict(set)
    contexts: defaultdict[int, list[str]] = defaultdict(list)
    for rendered, resource_class, label, context in production_rows:
        for char in rendered:
            codepoint = ord(char)
            occurrences[codepoint] += 1
            resource_classes[codepoint].add(resource_class)
            if len(contexts[codepoint]) < 5:
                sample = f"{label}: {context}"
                if sample not in contexts[codepoint]:
                    contexts[codepoint].append(sample)

    def coverage(codepoint: int) -> dict[str, bool]:
        return {font_id: codepoint in font_maps[font_id] for font_id in FONT_ORDER}

    def classification(codepoint: int) -> str:
        flags = coverage(codepoint)
        if flags["MLG-0007"] or flags["MLG-000E"]:
            return "CN_ALREADY_COVERED"
        if any(flags[font_id] for font_id in ("JPN-0007", "JPN-000E", "JPN-001C", "JPN-00C7")):
            return "JPN_RECOVERABLE"
        return "TRUE_NEW_GLYPH"

    codepoints = sorted(occurrences)
    records: list[dict[str, object]] = []
    for codepoint in codepoints:
        char = chr(codepoint)
        flags = coverage(codepoint)
        records.append({
            "character": char,
            "codepoint": f"U+{codepoint:04X}",
            "codepoint_int": codepoint,
            "unicode_name": display_name(char),
            "unicode_category": unicodedata.category(char),
            "unicode_block": unicode_block(codepoint),
            "production_occurrences": occurrences[codepoint],
            "resource_classes": " | ".join(sorted(resource_classes[codepoint])),
            "sample_contexts": " || ".join(contexts[codepoint]),
            "classification": classification(codepoint),
            **{font_id: "YES" if flags[font_id] else "NO" for font_id in FONT_ORDER},
        })

    common_fields = [
        "character", "codepoint", "unicode_name", "unicode_category", "unicode_block",
        "production_occurrences", "resource_classes", "sample_contexts", "classification",
    ]
    inventory_fields = common_fields + FONT_ORDER
    matrix_fields = ["character", "codepoint", "production_occurrences", "classification"] + FONT_ORDER
    recoverable_fields = common_fields + FONT_ORDER

    def write_csv(path: Path, fields: list[str], selected: list[dict[str, object]]) -> None:
        with path.open("w", encoding="utf-8", newline="") as handle:
            writer = csv.DictWriter(handle, fieldnames=fields, extrasaction="ignore")
            writer.writeheader()
            writer.writerows(selected)

    write_csv(analysis_root / "production_character_inventory.csv", inventory_fields, records)
    write_csv(analysis_root / "production_font_coverage_matrix.csv", matrix_fields, records)
    recoverable = [
        record for record in records
        if record["classification"] == "JPN_RECOVERABLE" and record["JPN-00C7"] == "YES"
    ]
    true_new = [record for record in records if record["classification"] == "TRUE_NEW_GLYPH"]
    true_new.sort(key=lambda record: (-int(record["production_occurrences"]), int(record["codepoint_int"])))
    write_csv(analysis_root / "production_recoverable_from_jpn00c7.csv", recoverable_fields, recoverable)
    write_csv(analysis_root / "production_true_new_glyphs.csv", common_fields + FONT_ORDER, true_new)

    mlg7_covered = sum(record["MLG-0007"] == "YES" for record in records)
    mlg7_missing = len(records) - mlg7_covered
    cn_covered = sum(record["classification"] == "CN_ALREADY_COVERED" for record in records)
    jpn_recoverable = sum(record["classification"] == "JPN_RECOVERABLE" for record in records)
    recoverable_00c7 = len(recoverable)
    operational_00c7 = sum(record["MLG-0007"] == "NO" and record["JPN-00C7"] == "YES" for record in records)
    other_only = sum(
        record["classification"] == "JPN_RECOVERABLE" and record["JPN-00C7"] == "NO"
        for record in records
    )
    class_rows = Counter(record["classification"] for record in records)
    source_class_rows = Counter(resource_class for _, resource_class, _, _ in production_rows)
    briefing_files = len(list(briefing_dir.glob("*.csv")))

    report: list[str] = []
    report.append("# FONT production coverage audit")
    report.append("")
    report.append("本报告是只读审计；本轮未修改 FONT/XPR、翻译源、构建产物，也未生成 glyph 或执行 build。")
    report.append("")
    report.append("## 结论摘要")
    report.append("")
    report.append(f"Production unique display chars: {len(records)}")
    report.append(f"Covered by MLG-0007: {mlg7_covered}")
    report.append(f"Missing from MLG-0007: {mlg7_missing}")
    report.append(f"Recoverable from JPN-00C7: {recoverable_00c7}")
    report.append(f"Recoverable only from other clean JPN fonts: {other_only}")
    report.append(f"Missing from all six fonts: {len(true_new)}")
    report.append("")
    report.append(f"分类计数：CN_ALREADY_COVERED={cn_covered}；JPN_RECOVERABLE={jpn_recoverable}；TRUE_NEW_GLYPH={len(true_new)}。")
    report.append(f"独立诊断子集（MLG-0007=NO 且 JPN-00C7=YES，不论 MLG-000E）：{operational_00c7}。其中严格属于 JPN_RECOVERABLE 的数量为 {recoverable_00c7}。")
    report.append("")
    report.append("### 指定字符复查")
    report.append("")
    report.append("| 字符 | 码点 | 次数 | 分类 | MLG-0007 | MLG-000E | JPN-0007 | JPN-000E | JPN-001C | JPN-00C7 |")
    report.append("|---|---:|---:|---|---|---|---|---|---|---|")
    for wanted in ("拘", "曝", "厥", "磋"):
        record = next((item for item in records if item["character"] == wanted), None)
        if record is None:
            report.append(f"| {wanted} | U+{ord(wanted):04X} | 0 | NOT_IN_PRODUCTION | - | - | - | - | - | - |")
        else:
            report.append("| " + " | ".join(str(record[field]) for field in ["character", "codepoint", "production_occurrences", "classification", "MLG-0007", "MLG-000E", "JPN-0007", "JPN-000E", "JPN-001C", "JPN-00C7"]) + " |")
    report.append("")
    report.append("## TRUE_NEW_GLYPH（按 production 出现次数降序）")
    report.append("")
    if true_new:
        for record in true_new:
            report.append(f"- {record['character']} {record['codepoint']} — {record['production_occurrences']} 次；{record['resource_classes']}")
    else:
        report.append("（无）")
    report.append("")
    report.append("## 统计口径与生产来源")
    report.append("")
    report.append(f"- 旧五类最终对象记录：`build/translation/compiled_translation_manifest.csv`，共 {len(manifest)} 行；按 `resource_class` 分布：" + ", ".join(f"{key}={value}" for key, value in sorted(source_class_rows.items()) if key != "BRIEFING") + "。")
    report.append(f"- BRIEFING 正式输入：`translations/briefing/*.csv`，{briefing_files} 个文件、{briefing_rows} 行。")
    report.append(f"- 纳入分析的非空 production 文本记录：{len(production_rows)}；`production_occurrences` 是清除控制语法后的实际显示 codepoint 出现次数，不是唯一行数。")
    report.append("- 未扫描 `ENG`、`MLG_CN` reference、`work/luna_translation_templates`、旧模板、backup/archive、README、测试输出或 readiness/package 输出；JPN_CN 也不作为独立字体集合。")
    report.append("- `<R=base,reading>` 的 base 与 reading 均计入，因为二者都是实际可显示文字；`<I=...>`、`<C=...>`、`<->`、美元/printf placeholder、换行、空白和 Unicode control/format 字符不计入。")
    report.append("")
    report.append("## 六套 unique font content")
    report.append("")
    report.append("| unique font | mapped count | atlas | cell | type | charmap SHA256 |")
    report.append("|---|---:|---|---:|---|---|")
    for font_id in FONT_ORDER:
        profile = FONT_PROFILES[font_id]
        report.append(f"| {font_id} | {profile['mapped_count']} | {profile['atlas']} | {profile['cell']} | {profile['type']} | `{charmap_sha.get(font_id, '')}` |")
    report.append("")
    report.append("## 分类定义")
    report.append("")
    report.append("- `CN_ALREADY_COVERED`：MLG-0007 或 MLG-000E 至少一个存在。")
    report.append("- `JPN_RECOVERABLE`：两套 MLG_CN 都不存在，但至少一套 clean JPN 存在。")
    report.append("- `TRUE_NEW_GLYPH`：六套 font charmap 全部不存在。")
    report.append("- `production_recoverable_from_jpn00c7.csv` 只列严格 `JPN_RECOVERABLE` 且 JPN-00C7=YES 的字符；报告另列的 operational 子集还包括 MLG-000E 已覆盖、但 MLG-0007 缺失的字符。")
    report.append("")
    report.append("## 输出文件")
    report.append("")
    report.append("- `production_character_inventory.csv`：production 唯一显示字符、次数、来源、样例和六套覆盖状态。")
    report.append("- `production_font_coverage_matrix.csv`：精简覆盖矩阵。")
    report.append("- `production_recoverable_from_jpn00c7.csv`：可从 clean JPN-00C7 回收且两套 MLG_CN 均缺失的字符。")
    report.append("- `production_true_new_glyphs.csv`：六套字体均缺失的真正新 glyph 字符。")

    (analysis_root / "FONT_PRODUCTION_COVERAGE_AUDIT.md").write_text("\n".join(report) + "\n", encoding="utf-8")
    print(f"Production unique display chars: {len(records)}")
    print(f"Covered by MLG-0007: {mlg7_covered}")
    print(f"Missing from MLG-0007: {mlg7_missing}")
    print(f"Recoverable from JPN-00C7: {recoverable_00c7}")
    print(f"Recoverable only from other clean JPN fonts: {other_only}")
    print(f"Missing from all six fonts: {len(true_new)}")
    print(f"Operational MLG-0007=NO/JPN-00C7=YES: {operational_00c7}")
    print(f"Rows: {len(production_rows)}; source files: {len(source_files)}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
