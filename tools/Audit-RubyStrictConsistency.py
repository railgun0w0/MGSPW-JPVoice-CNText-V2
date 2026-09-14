"""Strict, read-only Ruby terminology consistency screening."""

from __future__ import annotations

import argparse
import csv
import re
import unicodedata
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

CSV_FIELDS = [
    "normalized_payload",
    "raw_payload",
    "jpn_display",
    "cn_display",
    "cn_variants_in_group",
    "variant_count",
    "occurrence_count",
    "resource_class",
    "file_id",
    "identity",
    "eng_reference",
    "old_cn",
    "status",
    "notes",
]

# These are intentionally conservative.  They identify terms that are
# normally fixed names, organizations, military concepts, or technical terms;
# everything else remains CONTEXTUAL_REVIEW or UNCERTAIN for human judgment.
STRONG_PAYLOADS = {
    "ambush",
    "codesa",
    "comandante",
    "fallout",
    "guardia",
    "hex",
    "hombre nuevo",
    "mad",
    "mammal",
    "opanal",
    "options",
    "peace walker",
    "reptile",
    "sniper",
    "terminal",
}
CONTEXTUAL_PAYLOADS = {
    "area",
    "bastard",
    "cigarette",
    "heaven",
    "mi viejo",
    "somoza",
    "venceremos",
    "哪裡",
}


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--root", type=Path, default=ROOT)
    parser.add_argument(
        "--input",
        type=Path,
        default=None,
        help="existing ruby_term_consistency_review.csv",
    )
    parser.add_argument("--csv-output", type=Path, default=None)
    parser.add_argument("--markdown-output", type=Path, default=None)
    return parser.parse_args()


def normalize_format(value: str) -> str:
    """Comparison-only format normalization; raw values are never changed."""
    value = unicodedata.normalize("NFKC", value).casefold()
    value = "".join(value.split())
    return "".join(character for character in value if not unicodedata.category(character).startswith("P"))


def display_value(value: str) -> str:
    return value.replace("\r", "<CR>").replace("\n", "<LF>").replace("\t", "<TAB>")


def unique(values: list[str]) -> list[str]:
    result: list[str] = []
    for value in values:
        if value not in result:
            result.append(value)
    return result


def load_contexts(root: Path) -> dict[str, dict[str, str]]:
    contexts: dict[str, dict[str, str]] = {}
    for resource_class, directory in CLASS_DIRS.items():
        for path in sorted((root / "translations" / directory).glob("*.csv")):
            with path.open("r", encoding="utf-8-sig", newline="") as handle:
                for position, row in enumerate(csv.DictReader(handle)):
                    identity = f"{row.get('file_id', path.stem) or path.stem}#{row.get('unique_index', position)}"
                    contexts[identity] = {
                        "resource_class": resource_class,
                        "scene_context": row.get("scene_context", "") or "",
                        "jpn_text": row.get("jpn_text", "") or "",
                        "cn_text": row.get("cn_text", "") or "",
                        "previous_jpn_text": row.get("previous_jpn_text", "") or "",
                        "next_jpn_text": row.get("next_jpn_text", "") or "",
                    }
    return contexts


def load_review_rows(path: Path) -> list[dict[str, str]]:
    if not path.exists():
        raise RuntimeError(f"Ruby consistency review CSV not found: {path}")
    with path.open("r", encoding="utf-8-sig", newline="") as handle:
        rows = list(csv.DictReader(handle))
    required = {"normalized_payload", "raw_payload", "jpn_display", "cn_display", "occurrences"}
    missing = sorted(required - set(rows[0]) if rows else required)
    if missing:
        raise RuntimeError(f"{path}: missing fields {missing}")
    return rows


def classify(group: dict[str, Any]) -> tuple[str, str]:
    displays = group["cn_displays"]
    format_keys = {normalize_format(value) for value in displays}
    payload = group["normalized_payload"]
    notes: list[str] = []
    if group["payload_variants"]:
        notes.append("raw payload variants retained: " + " / ".join(group["payload_variants"]))
    if len(format_keys) == 1:
        notes.append("CN differences are spacing/case/fullwidth/punctuation-only under comparison normalization")
        return "FORMAT_ONLY", "; ".join(notes)
    if payload in STRONG_PAYLOADS:
        notes.append("conservative fixed-term/name/organization/technical-term signal; human standardization still required")
        return "STRONG_UNIFY", "; ".join(notes)
    if payload in CONTEXTUAL_PAYLOADS:
        notes.append("same JPN display/payload but wording may depend on role, tone, or collocation")
        return "CONTEXTUAL_REVIEW", "; ".join(notes)
    notes.append("strict candidate confirmed, but available data is insufficient to determine whether CN variation is semantic or contextual")
    return "UNCERTAIN", "; ".join(notes)


def build_groups(rows: list[dict[str, str]]) -> list[dict[str, Any]]:
    grouped: dict[tuple[str, str], list[dict[str, str]]] = defaultdict(list)
    for row in rows:
        grouped[(row["normalized_payload"], row["jpn_display"])].append(row)
    result: list[dict[str, Any]] = []
    for (normalized_payload, jpn_display), members in grouped.items():
        cn_displays = unique([member["cn_display"] for member in members])
        if len(cn_displays) < 2:
            continue
        raw_payloads = unique([member["raw_payload"] for member in members])
        payload_variant_values = raw_payloads if len(raw_payloads) > 1 else []
        items: list[dict[str, str]] = []
        for member in members:
            item = dict(member)
            item["occurrence_count"] = int(member.get("occurrences", "0") or 0)
            items.append(item)
        group: dict[str, Any] = {
            "normalized_payload": normalized_payload,
            "jpn_display": jpn_display,
            "members": items,
            "raw_payloads": raw_payloads,
            "payload_variants": payload_variant_values,
            "cn_displays": cn_displays,
            "variant_count": len(cn_displays),
            "occurrence_count": sum(item["occurrence_count"] for item in items),
        }
        group["status"], group["notes"] = classify(group)
        result.append(group)
    status_order = {"STRONG_UNIFY": 0, "FORMAT_ONLY": 1, "CONTEXTUAL_REVIEW": 2, "UNCERTAIN": 3}
    result.sort(key=lambda group: (status_order[group["status"]], -group["occurrence_count"], -group["variant_count"], group["normalized_payload"], group["jpn_display"]))
    return result


def detailed_csv_rows(groups: list[dict[str, Any]]) -> list[dict[str, str]]:
    output: list[dict[str, str]] = []
    for group in groups:
        variants = " / ".join(display_value(value) for value in group["cn_displays"])
        for member in group["members"]:
            output.append(
                {
                    "normalized_payload": group["normalized_payload"],
                    "raw_payload": member["raw_payload"],
                    "jpn_display": display_value(group["jpn_display"]),
                    "cn_display": display_value(member["cn_display"]),
                    "cn_variants_in_group": variants,
                    "variant_count": str(group["variant_count"]),
                    "occurrence_count": str(member["occurrence_count"]),
                    "resource_class": member.get("resource_class", ""),
                    "file_id": member.get("file_id", ""),
                    "identity": member.get("identity", ""),
                    "eng_reference": member.get("eng_reference", ""),
                    "old_cn": member.get("old_cn", ""),
                    "status": group["status"],
                    "notes": group["notes"],
                }
            )
    output.sort(key=lambda row: ({"STRONG_UNIFY": 0, "FORMAT_ONLY": 1, "CONTEXTUAL_REVIEW": 2, "UNCERTAIN": 3}[row["status"]], -int(row["occurrence_count"]), -int(row["variant_count"]), row["normalized_payload"], row["jpn_display"], row["identity"]))
    return output


def context_lines(group: dict[str, Any], contexts: dict[str, dict[str, str]], limit: int = 5) -> list[str]:
    lines: list[str] = []
    seen: set[str] = set()
    for member in sorted(group["members"], key=lambda item: (-int(item.get("occurrences", "0") or 0), item.get("identity", ""))):
        identity = member.get("identity", "")
        context = contexts.get(identity, {})
        jpn_text = context.get("jpn_text", "")
        cn_text = context.get("cn_text", "")
        if not jpn_text and not cn_text:
            continue
        value = f"{identity} [{member.get('resource_class', '')}] JPN=`{display_value(jpn_text)}` CN=`{display_value(cn_text)}`"
        if value in seen:
            continue
        seen.add(value)
        lines.append(value)
        if len(lines) >= limit:
            break
    return lines


def md(value: str) -> str:
    return value.replace("|", "\\|").replace("\r", "<CR>").replace("\n", "<LF>")


def variant_count_text(group: dict[str, Any]) -> str:
    counts: Counter[str] = Counter()
    for member in group["members"]:
        counts[member["cn_display"]] += int(member.get("occurrence_count", 0))
    return " / ".join(f"{display_value(value)} ({count})" for value, count in counts.items())


def render_markdown(groups: list[dict[str, Any]], contexts: dict[str, dict[str, str]], total_original_review: int) -> str:
    counts = Counter(group["status"] for group in groups)
    occurrences = sum(group["occurrence_count"] for group in groups)
    lines = [
        "# Strict Ruby Term Consistency Audit",
        "",
        "本报告只读筛选现有 `ruby_term_consistency_review.csv`。只有 `normalized payload` 相同、raw JPN display 完全相同、且 CN display 至少有两个不同形式的组才进入严格候选。没有修改任何 mapping、CSV、DAT、KEY 或译文。",
        "",
        "## Strict screening summary",
        "",
        f"- original `REVIEW_VARIANT` groups: `{total_original_review}`",
        f"- strict candidate groups: `{len(groups)}`",
        f"- strict candidate occurrences: `{occurrences}`",
        f"- reduced groups / likely false positives: `{total_original_review - len(groups)}`",
        "",
        "| status | groups |",
        "|---|---:|",
        f"| STRONG_UNIFY | {counts['STRONG_UNIFY']} |",
        f"| FORMAT_ONLY | {counts['FORMAT_ONLY']} |",
        f"| CONTEXTUAL_REVIEW | {counts['CONTEXTUAL_REVIEW']} |",
        f"| UNCERTAIN | {counts['UNCERTAIN']} |",
        "",
        "## Top candidates",
        "",
        "按 STRONG_UNIFY、FORMAT_ONLY、occurrence count、variant count 排序。这里不决定最终标准译法。",
        "",
        "| rank | status | normalized payload | JPN display | CN variants (occurrences) | variants | occurrences |",
        "|---:|---|---|---|---|---:|---:|",
    ]
    for rank, group in enumerate(groups[:30], 1):
        lines.append(f"| {rank} | `{group['status']}` | `{md(group['normalized_payload'])}` | `{md(group['jpn_display'])}` | `{md(variant_count_text(group))}` | {group['variant_count']} | {group['occurrence_count']} |")
    lines += ["", "## All strict candidate groups", "", "| rank | status | normalized payload | JPN display | CN variants (occurrences) | variants | occurrences | notes |", "|---:|---|---|---|---|---:|---:|---|"]
    for rank, group in enumerate(groups, 1):
        lines.append(f"| {rank} | `{group['status']}` | `{md(group['normalized_payload'])}` | `{md(group['jpn_display'])}` | `{md(variant_count_text(group))}` | {group['variant_count']} | {group['occurrence_count']} | {md(group['notes'])} |")
    lines += ["", "## Typical contexts (3–5 per candidate)", ""]
    for group in groups:
        lines += [f"### `{group['status']}` — `{md(group['normalized_payload'])}` / `{md(group['jpn_display'])}", "", f"- CN variants (occurrences): `{md(variant_count_text(group))}`", f"- ENG reference: `{md(' / '.join(unique([member.get('eng_reference', '') for member in group['members'] if member.get('eng_reference', '')])) )}`", f"- Old CN reference: `{md(' / '.join(unique([member.get('old_cn', '') for member in group['members'] if member.get('old_cn', '')])) )}`", f"- Notes: {group['notes']}", ""]
        for context in context_lines(group, contexts):
            lines.append(f"- {context}")
        lines.append("")
    lines += ["## Method notes", "", "- Strict group key: `(normalized_payload, exact raw JPN display)`.", "- Payload normalization: NFC-equivalent comparison via NFKC, Unicode whitespace collapse, casefold; spaces are not removed for payload grouping, and raw payloads remain separate.", "- `FORMAT_ONLY` additionally uses comparison-only NFKC/casefold, whitespace removal and punctuation removal; raw CN display remains unchanged in the CSV.", "- `STRONG_UNIFY` is a conservative classification for fixed names, organizations, military concepts and technical terms; it is still a human review queue, not an automatic replacement instruction.", "- `CONTEXTUAL_REVIEW` and `UNCERTAIN` are deliberately not unified automatically.", ""]
    return "\n".join(lines)


def main() -> int:
    args = parse_args()
    root = args.root.resolve()
    input_path = (args.input or root / "build" / "translation" / "ruby_term_consistency_review.csv").resolve()
    rows = load_review_rows(input_path)
    contexts = load_contexts(root)
    original_review_groups = {row["normalized_payload"] for row in rows if row.get("status") == "REVIEW_VARIANT"}
    groups = build_groups(rows)
    output_dir = root / "build" / "translation"
    csv_path = (args.csv_output or output_dir / "ruby_strict_consistency_review.csv").resolve()
    md_path = (args.markdown_output or output_dir / "ruby_strict_consistency_audit.md").resolve()
    csv_path.parent.mkdir(parents=True, exist_ok=True)
    md_path.parent.mkdir(parents=True, exist_ok=True)
    # This CSV is a human-review artifact and must open correctly in Windows Excel.
    with csv_path.open("w", encoding="utf-8-sig", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=CSV_FIELDS)
        writer.writeheader()
        writer.writerows(detailed_csv_rows(groups))
    md_path.write_text(render_markdown(groups, contexts, len(original_review_groups)), encoding="utf-8")
    counts = Counter(group["status"] for group in groups)
    print("STATUS=PASS")
    print(f"STRICT_CANDIDATE_GROUPS={len(groups)}")
    print(f"STRICT_CANDIDATE_OCCURRENCES={sum(group['occurrence_count'] for group in groups)}")
    print(f"STRONG_UNIFY={counts['STRONG_UNIFY']}")
    print(f"CONTEXTUAL_REVIEW={counts['CONTEXTUAL_REVIEW']}")
    print(f"FORMAT_ONLY={counts['FORMAT_ONLY']}")
    print(f"UNCERTAIN={counts['UNCERTAIN']}")
    print(f"FALSE_POSITIVE_REDUCTION={len(original_review_groups) - len(groups)}")
    print(f"CSV_OUTPUT={csv_path}")
    print(f"MARKDOWN_OUTPUT={md_path}")
    return 0


if __name__ == "__main__":
    try:
        raise SystemExit(main())
    except (OSError, ValueError, RuntimeError) as error:
        print(f"ERROR: {error}")
        raise SystemExit(1)
