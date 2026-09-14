"""Extract the exact JPN/CN Ruby base-pair set without terminology judgments."""

from __future__ import annotations

import argparse
import csv
import re
from collections import Counter, defaultdict
from pathlib import Path
from typing import Any


ROOT = Path(__file__).resolve().parents[1]
RUBY_RE = re.compile(r"<R=([^,<>\r\n]*),([^<>\r\n]*)>")
CLASS_DIRS = {
    "BRIEFING_NBE": "briefing",
    "LOOSE_OLANG": "loose_olang",
    "OHD": "ohd",
    "SLOT_OLANG": "slot_olang",
    "STAGEDAT_OLANG": "stagedat_olang",
    "YPK_GTT": "ypk_gtt",
}
OUTPUT_FIELDS = ["jpn_base", "jpn_ruby", "cn_base", "cn_ruby", "occurrence_count"]


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--root", type=Path, default=ROOT)
    parser.add_argument("--csv-output", type=Path, default=None)
    parser.add_argument("--markdown-output", type=Path, default=None)
    return parser.parse_args()


def display(value: str) -> str:
    return value.replace("\r", "<CR>").replace("\n", "<LF>").replace("\t", "<TAB>")


def load_pair_set(root: Path) -> tuple[Counter[tuple[str, str, str, str]], dict[str, Any]]:
    pair_counts: Counter[tuple[str, str, str, str]] = Counter()
    file_counts: Counter[str] = Counter()
    row_counts: Counter[str] = Counter()
    jpn_occurrences = 0
    cn_occurrences = 0
    paired_occurrences = 0
    jpn_ruby_rows = 0
    cn_ruby_rows = 0
    paired_rows = 0
    mismatches: list[dict[str, Any]] = []
    total_rows = 0
    translation_root = root / "translations"
    for resource_class, directory in CLASS_DIRS.items():
        for path in sorted((translation_root / directory).glob("*.csv")):
            file_counts[resource_class] += 1
            with path.open("r", encoding="utf-8-sig", newline="") as handle:
                for position, row in enumerate(csv.DictReader(handle)):
                    total_rows += 1
                    row_counts[resource_class] += 1
                    file_id = row.get("file_id", path.stem) or path.stem
                    unique_index = row.get("unique_index", str(position)) or str(position)
                    identity = f"{file_id}#{unique_index}"
                    jpn_tokens = [(match.group(1), match.group(2)) for match in RUBY_RE.finditer(row.get("jpn_text", "") or "")]
                    cn_tokens = [(match.group(1), match.group(2)) for match in RUBY_RE.finditer(row.get("cn_text", "") or "")]
                    jpn_occurrences += len(jpn_tokens)
                    cn_occurrences += len(cn_tokens)
                    jpn_ruby_rows += bool(jpn_tokens)
                    cn_ruby_rows += bool(cn_tokens)
                    pair_count = min(len(jpn_tokens), len(cn_tokens))
                    if pair_count:
                        paired_rows += 1
                        paired_occurrences += pair_count
                        for pair_index in range(pair_count):
                            jpn_base, jpn_ruby = jpn_tokens[pair_index]
                            cn_base, cn_ruby = cn_tokens[pair_index]
                            pair_counts[(jpn_base, jpn_ruby, cn_base, cn_ruby)] += 1
                    if len(jpn_tokens) != len(cn_tokens):
                        mismatches.append(
                            {
                                "resource_class": resource_class,
                                "file_id": file_id,
                                "identity": identity,
                                "jpn_ruby_count": len(jpn_tokens),
                                "cn_ruby_count": len(cn_tokens),
                                "paired_count": pair_count,
                                "jpn_text": row.get("jpn_text", "") or "",
                                "cn_text": row.get("cn_text", "") or "",
                            }
                        )
    return pair_counts, {
        "translation_root": str(translation_root.relative_to(root)),
        "file_ids": sum(file_counts.values()),
        "rows": total_rows,
        "files_by_resource_class": dict(sorted(file_counts.items())),
        "rows_by_resource_class": dict(sorted(row_counts.items())),
        "jpn_ruby_occurrences": jpn_occurrences,
        "cn_ruby_occurrences": cn_occurrences,
        "paired_occurrences": paired_occurrences,
        "jpn_ruby_rows": jpn_ruby_rows,
        "cn_ruby_rows": cn_ruby_rows,
        "paired_rows": paired_rows,
        "pair_count_mismatch_rows": len(mismatches),
        "pair_count_mismatches": mismatches,
    }


def csv_rows(pair_counts: Counter[tuple[str, str, str, str]]) -> list[dict[str, str]]:
    rows = [
        {
            "jpn_base": jpn_base,
            "jpn_ruby": jpn_ruby,
            "cn_base": cn_base,
            "cn_ruby": cn_ruby,
            "occurrence_count": str(count),
        }
        for (jpn_base, jpn_ruby, cn_base, cn_ruby), count in pair_counts.items()
    ]
    rows.sort(key=lambda row: (-int(row["occurrence_count"]), row["jpn_base"], row["jpn_ruby"], row["cn_base"], row["cn_ruby"]))
    return rows


def render_markdown(pair_counts: Counter[tuple[str, str, str, str]], meta: dict[str, Any]) -> str:
    rows = csv_rows(pair_counts)
    lines = [
        "# Exact JPN/CN Ruby Base Pair Set",
        "",
        "本报告只提取当前全项目 translation corpus 中同一 identity、同一 Ruby 出现顺序的 JPN/CN 四元组。所有字段保留原始值；仅按 `(jpn_base, jpn_ruby, cn_base, cn_ruby)` 精确去重，不做术语判断、规范化或文本修改。",
        "",
        "## Scope and pairing",
        "",
        f"- logical file_ids / translation files: `{meta['file_ids']}`",
        f"- translation rows: `{meta['rows']}`",
        f"- JPN Ruby occurrences: `{meta['jpn_ruby_occurrences']}`",
        f"- CN Ruby occurrences: `{meta['cn_ruby_occurrences']}`",
        f"- paired occurrences: `{meta['paired_occurrences']}`",
        f"- rows with JPN Ruby: `{meta['jpn_ruby_rows']}`",
        f"- rows with CN Ruby: `{meta['cn_ruby_rows']}`",
        f"- rows with paired Ruby: `{meta['paired_rows']}`",
        f"- identity rows with different JPN/CN Ruby counts: `{meta['pair_count_mismatch_rows']}`",
        f"- distinct exact four-tuples: `{len(pair_counts)}`",
        "",
        "配对方式：对每个 `file_id#unique_index`，分别提取 `jpn_text` 和 `cn_text` 的 Ruby token，按从左到右的出现序号配对。若某行两侧 Ruby 数量不同，仅保留可配对的前 `min(count)` 项，并在 mismatch 区域列出该行；没有进行自动补配或推断。",
        "",
        "## Deduplicated exact four-tuple set",
        "",
        "| rank | jpn_base | jpn_ruby | cn_base | cn_ruby | occurrence_count |",
        "|---:|---|---|---|---|---:|",
    ]
    for rank, row in enumerate(rows, 1):
        lines.append(f"| {rank} | `{display(row['jpn_base'])}` | `{display(row['jpn_ruby'])}` | `{display(row['cn_base'])}` | `{display(row['cn_ruby'])}` | {row['occurrence_count']} |")
    lines += ["", "## Pair-count mismatches", ""]
    if not meta["pair_count_mismatches"]:
        lines.append("没有发现 JPN/CN Ruby occurrence count 不一致的 identity row。")
    else:
        lines += ["| resource_class | identity | JPN count | CN count | paired count | JPN text | CN text |", "|---|---|---:|---:|---:|---|---|"]
        for item in meta["pair_count_mismatches"]:
            lines.append(f"| {item['resource_class']} | `{item['identity']}` | {item['jpn_ruby_count']} | {item['cn_ruby_count']} | {item['paired_count']} | `{display(item['jpn_text'])}` | `{display(item['cn_text'])}` |")
    lines += ["", "## Resource summary", "", "| resource_class | file_ids | rows |", "|---|---:|---:|"]
    for resource_class in sorted(meta["files_by_resource_class"]):
        lines.append(f"| {resource_class} | {meta['files_by_resource_class'][resource_class]} | {meta['rows_by_resource_class'][resource_class]} |")
    lines.append("")
    return "\n".join(lines)


def main() -> int:
    args = parse_args()
    root = args.root.resolve()
    pair_counts, meta = load_pair_set(root)
    output_dir = root / "build" / "translation"
    csv_path = (args.csv_output or output_dir / "ruby_base_pair_set.csv").resolve()
    md_path = (args.markdown_output or output_dir / "ruby_base_pair_audit.md").resolve()
    csv_path.parent.mkdir(parents=True, exist_ok=True)
    md_path.parent.mkdir(parents=True, exist_ok=True)
    with csv_path.open("w", encoding="utf-8-sig", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=OUTPUT_FIELDS)
        writer.writeheader()
        writer.writerows(csv_rows(pair_counts))
    md_path.write_text(render_markdown(pair_counts, meta), encoding="utf-8")
    print("STATUS=PASS")
    print(f"FILE_IDS={meta['file_ids']}")
    print(f"ROWS={meta['rows']}")
    print(f"JPN_RUBY_OCCURRENCES={meta['jpn_ruby_occurrences']}")
    print(f"CN_RUBY_OCCURRENCES={meta['cn_ruby_occurrences']}")
    print(f"PAIRED_OCCURRENCES={meta['paired_occurrences']}")
    print(f"DISTINCT_EXACT_QUADRUPLES={len(pair_counts)}")
    print(f"PAIR_COUNT_MISMATCH_ROWS={meta['pair_count_mismatch_rows']}")
    print(f"CSV_OUTPUT={csv_path}")
    print(f"MARKDOWN_OUTPUT={md_path}")
    return 0


if __name__ == "__main__":
    try:
        raise SystemExit(main())
    except (OSError, RuntimeError, ValueError) as error:
        print(f"ERROR: {error}")
        raise SystemExit(1)
