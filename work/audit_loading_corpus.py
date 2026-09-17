from __future__ import annotations

import csv
import hashlib
import re
import sys
import unicodedata
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
ANALYSIS_ROOT = ROOT / "font" / "analysis"

from core.pc_crypto import filename_seed, outer_transform
from core.xpr_font import XprFont


CSV_PATH = ROOT / "translations" / "loose_olang" / "00D0C740.csv"
FONT_PATH = ROOT / "font" / "JPN" / "001cbbd1.xpr"
CORPUS_CSV = ANALYSIS_ROOT / "loading_text_corpus.csv"
CHARS_CSV = ANALYSIS_ROOT / "loading_required_characters.csv"
REPORT = ANALYSIS_ROOT / "LOADING_TEXT_CORPUS_AUDIT.md"

# The four screenshot/runtime anchors identify this contiguous role-quote block.
# unique_index 33 is the separate LOADING... status label, not a role quote.
CORPUS_START = 20
CORPUS_END = 56
EXCLUDED_STATUS = {33}
FIXTURES = {
    29: "SNAKE",
    32: "PAZ",
    37: "KAZUHIRA_MILLER",
    39: "RAMON_GALVEZ_MENA",
}


def is_han(ch: str) -> bool:
    cp = ord(ch)
    return (
        0x3400 <= cp <= 0x4DBF
        or 0x4E00 <= cp <= 0x9FFF
        or 0xF900 <= cp <= 0xFAFF
    )


def han_chars(text: str) -> list[str]:
    return [ch for ch in text if is_han(ch)]


def display(text: str) -> str:
    return (text or "").replace("\r\n", "\\n").replace("\n", "\\n")


def sha256(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def csv_rows() -> list[dict[str, str]]:
    with CSV_PATH.open("r", encoding="utf-8-sig", newline="") as handle:
        return list(csv.DictReader(handle))


def load_font() -> tuple[XprFont, str, str]:
    encrypted = FONT_PATH.read_bytes()
    plaintext = outer_transform(encrypted, filename_seed(FONT_PATH.name))
    return XprFont(plaintext), sha256(encrypted), sha256(plaintext)


def record_rect(font: XprFont, index: int) -> str:
    if not 0 <= index < len(font.font_data.glyphs):
        return ""
    g = font.font_data.glyphs[index]
    return f"({g.u0},{g.v0})-({g.u1},{g.v1})"


def main() -> None:
    rows = csv_rows()
    selected: list[dict[str, str]] = []
    for row in rows:
        index = int(row["unique_index"])
        if CORPUS_START <= index <= CORPUS_END and index not in EXCLUDED_STATUS:
            selected.append(row)
    selected.sort(key=lambda row: int(row["unique_index"]))

    expected = [*range(CORPUS_START, CORPUS_END + 1)]
    actual = [int(row["unique_index"]) for row in selected]
    expected_without_status = [i for i in expected if i not in EXCLUDED_STATUS]
    if actual != expected_without_status:
        raise SystemExit(f"unexpected corpus continuity: {actual!r}")

    font, encrypted_sha, plaintext_sha = load_font()
    charmap = font.font_data.charmap

    per_char: dict[str, dict[str, object]] = {}
    for row in selected:
        text = row["cn_text"] or ""
        index = int(row["unique_index"])
        for ch in han_chars(text):
            item = per_char.setdefault(
                ch,
                {
                    "occurrences": 0,
                    "record_indices": [],
                    "samples": [],
                    "fixture_hits": [],
                },
            )
            item["occurrences"] = int(item["occurrences"]) + 1
            if index not in item["record_indices"]:
                item["record_indices"].append(index)
            if len(item["samples"]) < 3:
                item["samples"].append(text.replace("\n", "\\n"))
            if index in FIXTURES and FIXTURES[index] not in item["fixture_hits"]:
                item["fixture_hits"].append(FIXTURES[index])

    def mapping(ch: str) -> tuple[bool, int, str]:
        cp = ord(ch)
        if cp > font.font_data.last_code:
            return False, 0, ""
        index = charmap[cp]
        if index == 0:
            return False, 0, record_rect(font, 0)
        return True, index, record_rect(font, index)

    with CHARS_CSV.open("w", encoding="utf-8-sig", newline="") as handle:
        writer = csv.writer(handle)
        writer.writerow(
            [
                "character",
                "codepoint",
                "unicode_name",
                "production_occurrences",
                "loading_text_count",
                "record_unique_indices",
                "fixture_hits",
                "JPN001C_present",
                "JPN001C_glyph_index",
                "JPN001C_rect",
                "sample_contexts",
            ]
        )
        for ch in sorted(per_char, key=lambda value: ord(value)):
            item = per_char[ch]
            present, glyph_index, rect = mapping(ch)
            writer.writerow(
                [
                    ch,
                    f"U+{ord(ch):04X}",
                    unicodedata.name(ch, ""),
                    item["occurrences"],
                    len(item["record_indices"]),
                    ";".join(str(x) for x in item["record_indices"]),
                    ";".join(item["fixture_hits"]),
                    "YES" if present else "NO",
                    glyph_index,
                    rect,
                    " || ".join(item["samples"]),
                ]
            )

    with CORPUS_CSV.open("w", encoding="utf-8-sig", newline="") as handle:
        writer = csv.writer(handle)
        writer.writerow(
            [
                "corpus_order",
                "resource_class",
                "file_id",
                "unique_index",
                "first_reference_index",
                "reference_indices",
                "reference_count",
                "entity_context",
                "fixture",
                "jpn_text",
                "cn_text",
                "display_han_char_count",
            ]
        )
        for order, row in enumerate(selected, 1):
            writer.writerow(
                [
                    order,
                    "LOOSE_OLANG",
                    row["file_id"],
                    row["unique_index"],
                    row["first_reference_index"],
                    row["reference_indices"],
                    row["reference_count"],
                    row["entity_context"],
                    FIXTURES.get(int(row["unique_index"]), ""),
                    row["jpn_text"],
                    row["cn_text"],
                    len(han_chars(row["cn_text"] or "")),
                ]
            )

    covered = sorted(ch for ch in per_char if mapping(ch)[0])
    missing = sorted(ch for ch in per_char if not mapping(ch)[0])
    fixture_rows = {int(row["unique_index"]): row for row in selected}

    report: list[str] = []
    report += [
        "# LOADING_TEXT_CORPUS_AUDIT",
        "",
        "## 结论",
        "",
        f"- `LOADING_TEXT_CORPUS` 来源：`translations/loose_olang/00D0C740.csv`。",
        f"- 连续语录区：`unique_index {CORPUS_START}–{CORPUS_END}`；其中 `33` 的 `LOADING...` 是状态标签，排除后角色语录共 **{len(selected)} 条**。",
        f"- Production unique Han characters：**{len(per_char)}**。",
        f"- `JPN/001cbbd1.xpr` 已覆盖：**{len(covered)}**。",
        f"- `JPN/001cbbd1.xpr` 缺失：**{len(missing)}**。",
        "- 截图中的 `·` 没有作为源字符参与统计；统计只读取 CSV 当前 `cn_text`。",
        "",
        "### 完整缺字集合",
        "",
        ("、".join(f"{ch} U+{ord(ch):04X}" for ch in missing) if missing else "无"),
        "",
        "## 字体基准",
        "",
        f"- 文件：`font/JPN/001cbbd1.xpr`",
        f"- encrypted SHA256：`{encrypted_sha}`",
        f"- decrypted SHA256：`{plaintext_sha}`",
        f"- record count：`{len(font.font_data.glyphs)}`；mapped codepoints：`{sum(x != 0 for x in charmap)}`；record 0 保留为 fallback/missing-glyph 候选。",
        "",
        "## 四个实机 fixture 的 production 定位",
        "",
        "| fixture | resource_class | file_id | unique_index | reference_index | 原始 JPN | 当前 CN |",
        "|---|---|---|---:|---:|---|---|",
    ]
    for index in [29, 32, 37, 39]:
        row = fixture_rows[index]
        report.append(
            "| "
            + " | ".join(
                [
                    FIXTURES[index],
                    "LOOSE_OLANG",
                    row["file_id"],
                    row["unique_index"],
                    row["first_reference_index"],
                    display(row["jpn_text"]),
                    display(row["cn_text"]),
                ]
            )
            + " |"
        )

    report += [
        "",
        "SNAKE 的定位依据：该行原始日文为 `いいか、俺達に勝利はない。`，当前完整中文为 `听好了，对我们来说，没有胜利可言。`；截图中的末尾可见片段 `……利·言。` 与这条完整记录的 `胜利可言。` 相符。截图中的 `·` 只用于确认锚点，不作为源字符统计。",
    ]

    report += [
        "",
        "## 语录区边界依据",
        "",
        "四个锚点全部落在同一个 `LOOSE_OLANG/00D0C740.csv` 的连续记录链中：",
        "`29 → 32 → 37 → 39`。该链从 `20` 开始，至 `56` 结束；相邻记录的 `first_reference_index` 每次递增 6，且 `entity_context` 均为同一类 page/tag/entity/ref/ord4 结构。",
        "`unique_index 33` 的 JPN/CN 仅为 `LOADING...` / `读取中…`，是加载状态 UI，不是角色语录，因此没有混入本 corpus。`57` 起转入 `缩小/放大/滑动/返回` 等设置 UI，也没有混入。",
        "",
        "## 角色语录记录清单",
        "",
        "完整逐条记录已经落盘到 [loading_text_corpus.csv](loading_text_corpus.csv)，包含 file_id、unique_index、reference_index、JPN、CN 和 fixture 标记。",
        "",
        "## 覆盖统计",
        "",
        "| 项目 | 数量 |",
        "|---|---:|",
        f"| Loading 角色语录文本数 | {len(selected)} |",
        f"| Production unique Han chars | {len(per_char)} |",
        f"| JPN001C present | {len(covered)} |",
        f"| JPN001C missing / fallback | {len(missing)} |",
        "",
        "逐字符出现次数、所属文本、JPN001C glyph index/record rect 和样例上下文见 [loading_required_characters.csv](loading_required_characters.csv)。",
        "",
        "## 当前范围边界",
        "",
        "本报告只覆盖上述 Loading 角色语录集合，不推断菜单、HUD、无线电、briefing、OHD 或其它 SMALL_JPN 使用场景；不修改任何 XPR。",
    ]
    REPORT.write_text("\n".join(report) + "\n", encoding="utf-8")

    print(f"records={len(selected)} unique_han={len(per_char)} covered={len(covered)} missing={len(missing)}")
    print("missing=" + "".join(missing))


if __name__ == "__main__":
    main()
