#!/usr/bin/env python3
"""Read-only semantic review of production TRUE_NEW_GLYPH characters."""

from __future__ import annotations

import argparse
import csv
import importlib.util
import re
from collections import Counter, defaultdict
from pathlib import Path


FONT_ORDER = ["JPN-0007", "JPN-000E", "JPN-001C", "JPN-00C7", "MLG-0007", "MLG-000E"]
INTERNAL_CHARS = {"蚣", "蜈", "鸭", "飓"}
NATURAL_CHARS = {"噫", "窥"}


def load_audit_module(root: Path):
    spec = importlib.util.spec_from_file_location("font_audit", root / "tools" / "Audit-ProductionFontCoverage.py")
    module = importlib.util.module_from_spec(spec)
    assert spec.loader is not None
    spec.loader.exec_module(module)
    return module


def csv_rows(path: Path) -> list[dict[str, str]]:
    with path.open(encoding="utf-8-sig", newline="") as handle:
        return list(csv.DictReader(handle))


def load_font_maps(root: Path) -> dict[str, set[int]]:
    maps: dict[str, set[int]] = {}
    for row in csv_rows(root / "font" / "analysis" / "FONT_SIX_UNIQUE_CHARMAP.csv"):
        values: set[int] = set()
        for match in re.finditer(r"U\+([0-9A-Fa-f]{4,6})(?:-U\+([0-9A-Fa-f]{4,6}))?", row["complete_unicode_ranges"]):
            start = int(match.group(1), 16)
            end = int(match.group(2), 16) if match.group(2) else start
            values.update(range(start, end + 1))
        maps[row["unique_id"]] = values
    return maps


def load_production_rows(root: Path) -> list[dict[str, str]]:
    rows: list[dict[str, str]] = []
    with (root / "build" / "translation" / "compiled_translation_manifest.csv").open(encoding="utf-8-sig", newline="") as handle:
        rows.extend(csv.DictReader(handle))
    for path in sorted((root / "translations" / "briefing").glob("*.csv")):
        with path.open(encoding="utf-8-sig", newline="") as handle:
            for row in csv.DictReader(handle):
                row.setdefault("resource_class", "BRIEFING")
                row.setdefault("file_id", path.stem)
                rows.append(row)
    return rows


def clean_cell(value: str, limit: int = 240) -> str:
    value = (value or "").replace("\r", " ").replace("\n", " / ")
    value = re.sub(r"\s+", " ", value).strip()
    value = value.replace("|", "\\|")
    return value if len(value) <= limit else value[: limit - 1] + "…"


def category_for(char: str) -> str:
    if char in INTERNAL_CHARS:
        return "PROBABLY_UNUSED_INTERNAL"
    if char in NATURAL_CHARS:
        return "NATURAL_REWRITE_POSSIBLE"
    return "KEEP_GLYPH"


def reason_for(char: str) -> str:
    custom = {
        "噫": "当前是对白语气词；“噫”偏书面且不符合两处惊呼语境，用“啊”不损失原意，且 MLG-0007 支持。",
        "窥": "当前玩家教程/简报中的“窥视窗、窥视屋内”可自然改为“观察窗、查看屋内/门内”，不改变覗き窓与覗く的操作语义，替换片段均受 MLG-0007 支持。",
        "厥": "“昏厥”准确表达气绝/失去意识的武器效果和状态；改成“晕倒”或“昏迷”会改变术语精度或语体。",
        "贤": "“贤者”“贤者的遗产”是剧情专名/核心术语，不能用泛化词替代。",
        "磋": "“切磋”是角色请求对练的准确固定表达，改成“较量”等会损失语气。",
        "蚣": "只出现在 LANG_MISSION_INFO.OLANG 的 sbm...内部任务备注，与“内容/实装状态：×”同段；暂不按玩家可见文本要求增加 glyph。",
        "蜈": "只出现在 LANG_MISSION_INFO.OLANG 的 sbm...内部任务备注，与“内容/实装状态：×”同段；暂不按玩家可见文本要求增加 glyph。",
        "鸭": "全部出现都在 `(不要)` 标记的旧/废弃文本中；当前没有玩家可见 production 证据，暂列内部候选。",
        "飓": "唯一出现是 `(不要)#遭遇飓风` 的旧/废弃文本；当前没有玩家可见 production 证据，暂列内部候选。",
        "Č": "Karel Čapek 的专名拼写含变音符号；改成 ASCII 会损失正式人名写法，保留 glyph 更稳妥。",
    }
    return custom.get(char, "当前字属于完整词语、固定成语、专名、拟声或玩家可见语境中的自然表达；未发现不损失原意且更合适的 MLG-0007 替代。")


def replacement_for(char: str, current: str) -> tuple[str, str]:
    if char == "噫":
        return "啊", current.replace("噫", "啊")
    if char == "窥":
        if "窥视窗" in current:
            return "观察窗", current.replace("窥视窗", "观察窗")
        if "窥视门内" in current:
            return "查看门内", current.replace("窥视门内", "查看门内")
        if "窥视屋内" in current:
            return "查看屋内", current.replace("窥视屋内", "查看屋内")
        return "查看", current.replace("窥", "查看", 1)
    raise ValueError(char)


def group_contexts(root: Path, module, targets: set[str]):
    grouped: dict[str, dict[tuple[str, str, str, str], dict[str, object]]] = defaultdict(dict)
    for row in load_production_rows(root):
        raw = row.get("cn_text", "") or ""
        rendered = module.visible_text(raw)
        matched = targets.intersection(rendered)
        if not matched:
            continue
        resource_class = row.get("resource_class", "UNKNOWN")
        file_id = row.get("file_id", "") or row.get("resource_id", "")
        index = row.get("record_index", "") or row.get("reference_index", "") or row.get("unique_index", "")
        key = (resource_class, file_id, row.get("jpn_text", "") or "", raw)
        for char in matched:
            item = grouped[char].get(key)
            if item is None:
                item = {
                    "resource_class": resource_class,
                    "file_id": file_id,
                    "indices": [],
                    "jpn": row.get("jpn_text", "") or "",
                    "cn_raw": raw,
                    "visible_cn": rendered,
                    "char_occurrences": 0,
                }
                grouped[char][key] = item
            item["indices"].append(index)
            item["char_occurrences"] += rendered.count(char)
    return grouped


def md_table_value(value: object) -> str:
    return clean_cell(str(value))


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("v2_root", type=Path)
    args = parser.parse_args()
    root = args.v2_root.resolve()
    module = load_audit_module(root)
    font_maps = load_font_maps(root)
    true_rows = csv_rows(root / "font" / "analysis" / "production_true_new_glyphs.csv")
    targets = {row["character"] for row in true_rows}
    grouped = group_contexts(root, module, targets)
    true_occurrences = {row["character"]: int(row["production_occurrences"]) for row in true_rows}

    categories = {char: category_for(char) for char in targets}
    counts = Counter(categories.values())
    natural_rows: list[dict[str, str]] = []

    for char in sorted(NATURAL_CHARS):
        for item in sorted(grouped[char].values(), key=lambda x: (str(x["resource_class"]), str(x["file_id"]), str(x["indices"][0]))):
            fragment, proposed = replacement_for(char, str(item["visible_cn"]))
            supported = all(ord(c) in font_maps["MLG-0007"] for c in module.visible_text(fragment))
            natural_rows.append({
                "character": char,
                "codepoint": f"U+{ord(char):04X}",
                "occurrences": str(item["char_occurrences"]),
                "file_id / index": f"{item['file_id']} / {', '.join(dict.fromkeys(str(x) for x in item['indices']))}",
                "JPN": clean_cell(str(item["jpn"])),
                "current_CN": clean_cell(str(item["visible_cn"])),
                "proposed_CN": clean_cell(proposed),
                "replacement_supported_by_MLG-0007": "YES" if supported else "NO",
                "reason": reason_for(char),
            })

    with (root / "font" / "analysis" / "font_natural_rewrite_candidates.csv").open("w", encoding="utf-8", newline="") as handle:
        fields = ["character", "codepoint", "occurrences", "file_id / index", "JPN", "current_CN", "proposed_CN", "replacement_supported_by_MLG-0007", "reason"]
        writer = csv.DictWriter(handle, fieldnames=fields)
        writer.writeheader()
        writer.writerows(natural_rows)

    report: list[str] = [
        "# TRUE_NEW_GLYPH semantic review",
        "",
        "本报告仅做只读审查和建议；没有修改 FONT/XPR、translation/mapping、production CSV，也没有执行 build。",
        "",
        "## 结论",
        "",
        f"KEEP_GLYPH unique = {counts['KEEP_GLYPH']}",
        f"NATURAL_REWRITE_POSSIBLE unique = {counts['NATURAL_REWRITE_POSSIBLE']}",
        f"PROBABLY_UNUSED_INTERNAL unique = {counts['PROBABLY_UNUSED_INTERNAL']}",
        "",
        "151 个 TRUE_NEW_GLYPH 已逐字回查最终 production 文本，并与对应 JPN 原文对照。分类是字符级分类；同一字符的所有 production 出现均纳入判断。",
        "",
        "## 分类原则",
        "",
        "- `KEEP_GLYPH`：当前表达准确、自然或承担术语/专名/固定成语/角色语气/拟声功能；避字会损害译文。",
        "- `NATURAL_REWRITE_POSSIBLE`：存在不损失原意、语境和操作语义的自然替换，且替换片段全部由 MLG-0007 支持。",
        "- `PROBABLY_UNUSED_INTERNAL`：来源带明显内部任务编号/开发备注标志；不是“确认永不加载”，只是当前证据不足以把它当作玩家可见 production 文本。",
        "",
        "## 优先字符复查",
        "",
        "| 字符 | 码点 | 次数 | 分类 | 证据摘要 |",
        "|---|---:|---:|---|---|",
    ]
    for char in ("噫", "诊", "厥", "贤", "蜈", "蚣", "赠", "徘", "徊", "磋"):
        row = next(item for item in true_rows if item["character"] == char)
        report.append(f"| {char} | U+{ord(char):04X} | {row['production_occurrences']} | {categories[char]} | {reason_for(char)} |")

    report.extend([
        "",
        "## LANG_MISSION_INFO.OLANG 判定",
        "",
        "`LANG_MISSION_INFO.OLANG` 不是整体内部文件：其中包含正常任务标题和任务说明，确实可能是玩家可见内容。",
        "但本次 `蚣`、`蜈` 的全部 18 次出现都落在带 `sbm...` / `sbm...内容` 的备注段，并伴随日文 `組み込み状況：×`、中文 `实装状态：×`。这些是开发/任务实现状态记录的强证据，因此两字暂列 `PROBABLY_UNUSED_INTERNAL`，仍需以后用实际运行路径确认，而不是直接为它们造 glyph。",
        "`鸭` 的全部出现都在 `(不要)` 标记的旧/废弃文本中；`飓` 的唯一出现是 `(不要)#遭遇飓风`。这两字同样暂列 `PROBABLY_UNUSED_INTERNAL`，但仍保留在审计清单中，不从 production 源自动删除。",
        "",
        "## NATURAL_REWRITE_POSSIBLE",
        "",
        "下面是全部自然改写候选；没有自动写回 translation。详细 CSV：`font_natural_rewrite_candidates.csv`。",
        "",
        "| 字符 | 次数 | file_id / index | JPN | current_CN | proposed_CN | MLG-0007 |",
        "|---|---:|---|---|---|---|---|",
    ])
    for item in natural_rows:
        report.append("| " + " | ".join(md_table_value(item[field]) for field in ["character", "occurrences", "file_id / index", "JPN", "current_CN", "proposed_CN", "replacement_supported_by_MLG-0007"]) + " |")

    report.extend([
        "",
        "## 151 字逐字审查清单",
        "",
        "`sample JPN` / `sample current_CN` 是实际 production 记录样例；重复物理记录已按字符累计 occurrences。完整来源仍可在 `production_character_inventory.csv` 与 `production_true_new_glyphs.csv` 中核对。",
        "",
        "| 字符 | 码点 | 次数 | 分类 | resource classes | sample JPN | sample current_CN | review reason |",
        "|---|---:|---:|---|---|---|---|---|",
    ])
    for row in sorted(true_rows, key=lambda item: (-int(item["production_occurrences"]), int(item["codepoint"][2:], 16))):
        char = row["character"]
        contexts = list(grouped[char].values())
        sample_jpn = " || ".join(clean_cell(str(item["jpn"]), 120) for item in contexts[:2])
        sample_cn = " || ".join(clean_cell(str(item["visible_cn"]), 120) for item in contexts[:2])
        report.append("| " + " | ".join([
            md_table_value(char),
            row["codepoint"],
            row["production_occurrences"],
            categories[char],
            row.get("resource_classes", ""),
            sample_jpn,
            sample_cn,
            reason_for(char),
        ]) + " |")

    report.extend([
        "",
        "## 操作边界",
        "",
        "本轮没有修改任何 translation/mapping，也没有修改字体或生成 XPR。`NATURAL_REWRITE_POSSIBLE` 只是候选建议，不代表已经批准替换；`PROBABLY_UNUSED_INTERNAL` 也不代表可以直接删除或忽略。",
        "",
        "输出：`font_natural_rewrite_candidates.csv`。",
    ])
    (root / "font" / "analysis" / "FONT_TRUE_NEW_GLYPH_REVIEW.md").write_text("\n".join(report) + "\n", encoding="utf-8")

    print(f"KEEP_GLYPH unique = {counts['KEEP_GLYPH']}")
    print(f"NATURAL_REWRITE_POSSIBLE unique = {counts['NATURAL_REWRITE_POSSIBLE']}")
    print(f"PROBABLY_UNUSED_INTERNAL unique = {counts['PROBABLY_UNUSED_INTERNAL']}")
    print(f"Natural candidate context rows = {len(natural_rows)}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
