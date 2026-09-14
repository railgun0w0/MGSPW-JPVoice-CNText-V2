"""Read-only Ruby display/payload consistency audit for the full translation corpus."""

from __future__ import annotations

import argparse
import csv
import json
import re
import unicodedata
from collections import Counter, defaultdict
from dataclasses import dataclass
from pathlib import Path
from typing import Any, Iterable


ROOT = Path(__file__).resolve().parents[1]
RUBY_RE = re.compile(r"<R=([^,<>\r\n]*),([^<>\r\n]*)>")

CLASS_DIRS = {
    "briefing": "BRIEFING_NBE",
    "loose_olang": "LOOSE_OLANG",
    "ohd": "OHD",
    "slot_olang": "SLOT_OLANG",
    "stagedat_olang": "STAGEDAT_OLANG",
    "ypk_gtt": "YPK_GTT",
}

CSV_FIELDS = [
    "normalized_payload",
    "raw_payload",
    "cn_display",
    "jpn_display",
    "eng_reference",
    "old_cn",
    "resource_class",
    "file_id",
    "identity",
    "occurrences",
    "variant_count",
    "status",
    "notes",
    "cn_raw_payload",
    "cn_display_normalized",
    "payload_variant_count",
    "payload_variants",
    "cn_display_variants",
    "jpn_display_variants",
]


@dataclass(frozen=True)
class RubyOccurrence:
    resource_class: str
    resource_type: str
    file_id: str
    unique_index: int
    cn_display: str
    cn_payload: str
    jpn_display: str
    jpn_payload: str
    eng_reference: str
    old_cn: str
    cn_text: str

    @property
    def identity(self) -> str:
        return f"{self.file_id}#{self.unique_index}"


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--root", type=Path, default=ROOT)
    parser.add_argument(
        "--json-audit",
        type=Path,
        default=None,
        help="existing full special-character audit JSON; used for scope cross-check",
    )
    parser.add_argument("--csv-output", type=Path, default=None)
    parser.add_argument("--markdown-output", type=Path, default=None)
    return parser.parse_args()


def normalize_payload(value: str) -> str:
    """Conservative candidate normalization: NFC, casefold, whitespace collapse."""
    value = unicodedata.normalize("NFC", value)
    value = " ".join(value.split())
    return value.casefold()


def normalize_display(value: str) -> str:
    """Ignore line-wrap/spacing-only display differences for consistency status."""
    value = unicodedata.normalize("NFC", value)
    return " ".join(value.split())


def display_value(value: str) -> str:
    return value.replace("\r", "<CR>").replace("\n", "<LF>").replace("\t", "<TAB>")


def json_or_raw_values(row: dict[str, str], base_field: str, variants_field: str) -> list[str]:
    values: list[str] = []
    base = row.get(base_field, "") or ""
    if base:
        values.append(base)
    variants = row.get(variants_field, "") or ""
    if variants:
        try:
            parsed = json.loads(variants)
        except json.JSONDecodeError:
            parsed = [variants]
        if isinstance(parsed, list):
            values.extend(str(value) for value in parsed if value not in (None, ""))
        elif parsed not in (None, ""):
            values.append(str(parsed))
    unique: list[str] = []
    for value in values:
        if value not in unique:
            unique.append(value)
    return unique


def load_reference_rows(root: Path, directory: str, file_name: str) -> dict[int, dict[str, str]]:
    path = root / "work" / "luna_translation_templates" / directory / file_name
    if not path.exists():
        return {}
    with path.open("r", encoding="utf-8-sig", newline="") as handle:
        result: dict[int, dict[str, str]] = {}
        for position, row in enumerate(csv.DictReader(handle)):
            try:
                unique_index = int(row.get("unique_index", position))
            except (TypeError, ValueError) as error:
                raise RuntimeError(f"{path}: invalid unique_index at row {position}") from error
            result[unique_index] = row
        return result


def load_occurrences(root: Path) -> tuple[list[RubyOccurrence], dict[str, Any]]:
    translation_root = root / "translations"
    template_dirs = {
        "BRIEFING_NBE": "BRIEFING",
        "LOOSE_OLANG": "LOOSE_OLANG",
        "OHD": "OHD",
        "SLOT_OLANG": "SLOT_OLANG",
        "STAGEDAT_OLANG": "STAGEDAT_OLANG",
        "YPK_GTT": "YPK_GTT",
    }
    occurrences: list[RubyOccurrence] = []
    file_counts: Counter[str] = Counter()
    row_counts: Counter[str] = Counter()
    cn_ruby_rows: Counter[str] = Counter()
    jpn_ruby_rows: Counter[str] = Counter()
    jpn_ruby_occurrences = 0
    missing_reference_files: list[str] = []
    for directory, resource_class in CLASS_DIRS.items():
        paths = sorted((translation_root / directory).glob("*.csv"))
        template_dir = template_dirs[resource_class]
        for path in paths:
            file_counts[resource_class] += 1
            references = load_reference_rows(root, template_dir, path.name)
            if not references:
                missing_reference_files.append(str(path.relative_to(root)))
            with path.open("r", encoding="utf-8-sig", newline="") as handle:
                for position, row in enumerate(csv.DictReader(handle)):
                    try:
                        unique_index = int(row.get("unique_index", position))
                    except (TypeError, ValueError) as error:
                        raise RuntimeError(f"{path}: invalid unique_index at row {position}") from error
                    row_counts[resource_class] += 1
                    jpn_text = row.get("jpn_text", "") or ""
                    cn_text = row.get("cn_text", "") or ""
                    jpn_tokens = list(RUBY_RE.finditer(jpn_text))
                    cn_tokens = list(RUBY_RE.finditer(cn_text))
                    jpn_ruby_occurrences += len(jpn_tokens)
                    if jpn_tokens:
                        jpn_ruby_rows[resource_class] += 1
                    if cn_tokens:
                        cn_ruby_rows[resource_class] += 1
                    if not cn_tokens:
                        continue
                    reference = references.get(unique_index, {})
                    eng_values = json_or_raw_values(reference, "eng_reference", "eng_reference_variants")
                    old_values = json_or_raw_values(reference, "mlg_cn_reference", "mlg_cn_reference_variants")
                    for occurrence_index, cn_token in enumerate(cn_tokens):
                        cn_display, cn_payload = cn_token.group(1), cn_token.group(2)
                        matching_jpn = None
                        if occurrence_index < len(jpn_tokens):
                            candidate = jpn_tokens[occurrence_index]
                            # Ruby display is a same-row/same-ordinal field even
                            # when the JPN and CN payload spelling is translated
                            # differently (for example ラボ -> LAB). Keep that
                            # difference for review instead of dropping JPN text.
                            matching_jpn = candidate
                        if matching_jpn is None or not jpn_tokens:
                            same_payload = [
                                token for token in jpn_tokens
                                if normalize_payload(token.group(2)) == normalize_payload(cn_payload)
                            ]
                            if same_payload:
                                matching_jpn = same_payload[min(occurrence_index, len(same_payload) - 1)]
                        jpn_display = matching_jpn.group(1) if matching_jpn else ""
                        jpn_payload = matching_jpn.group(2) if matching_jpn else ""
                        resource_type = resource_class
                        if resource_class == "BRIEFING_NBE":
                            resource_type = "BRIEFING_FILES" if path.stem.startswith("BRIEFING_FILES_BLOCK_") else "BRIEFING_MISSION"
                        occurrences.append(
                            RubyOccurrence(
                                resource_class=resource_class,
                                resource_type=resource_type,
                                file_id=row.get("file_id", path.stem) or path.stem,
                                unique_index=unique_index,
                                cn_display=cn_display,
                                cn_payload=cn_payload,
                                jpn_display=jpn_display,
                                jpn_payload=jpn_payload,
                                eng_reference=" | ".join(eng_values),
                                old_cn=" | ".join(old_values),
                                cn_text=cn_text,
                            )
                        )
    return occurrences, {
        "translation_root": str(translation_root.relative_to(root)),
        "mapping_files": sum(file_counts.values()),
        "rows": sum(row_counts.values()),
        "resource_classes": dict(sorted(file_counts.items())),
        "row_counts": dict(sorted(row_counts.items())),
        "cn_ruby_rows": dict(sorted(cn_ruby_rows.items())),
        "jpn_ruby_rows": dict(sorted(jpn_ruby_rows.items())),
        "jpn_ruby_occurrences": jpn_ruby_occurrences,
        "missing_reference_files": sorted(missing_reference_files),
    }


def unique_values(values: Iterable[str]) -> list[str]:
    result: list[str] = []
    for value in values:
        if value not in result:
            result.append(value)
    return result


def classify_group(items: list[RubyOccurrence]) -> tuple[str, str]:
    raw_payloads = unique_values(item.cn_payload for item in items)
    cn_displays = unique_values(item.cn_display for item in items)
    cn_display_normalized = unique_values(normalize_display(item.cn_display) for item in items)
    notes: list[str] = []
    if len(raw_payloads) > 1:
        notes.append("payload differs by case/spacing or spelling; preserve raw values and review possible variant")
    if len(cn_displays) > 1:
        notes.append("multiple CN display forms for the normalized payload; context may justify the difference")
    if any(not item.jpn_display for item in items):
        notes.append("JPN Ruby display could not be paired for at least one CN Ruby occurrence")
    if any(item.jpn_payload and item.jpn_payload != item.cn_payload for item in items):
        notes.append("raw JPN/CN payload differs in at least one occurrence")
    if len(cn_display_normalized) > 1:
        return "REVIEW_VARIANT", "; ".join(notes)
    if len(raw_payloads) > 1:
        return "POSSIBLE_PAYLOAD_VARIANT", "; ".join(notes)
    return "CONSISTENT", "; ".join(notes) or "single normalized CN display form observed"


def make_groups(occurrences: list[RubyOccurrence]) -> list[dict[str, Any]]:
    grouped: dict[str, list[RubyOccurrence]] = defaultdict(list)
    for occurrence in occurrences:
        grouped[normalize_payload(occurrence.cn_payload)].append(occurrence)
    result: list[dict[str, Any]] = []
    for normalized_payload, items in grouped.items():
        status, notes = classify_group(items)
        raw_payloads = unique_values(item.cn_payload for item in items)
        cn_displays = unique_values(item.cn_display for item in items)
        jpn_displays = unique_values(item.jpn_display for item in items if item.jpn_display)
        cn_display_normalized = unique_values(normalize_display(item.cn_display) for item in items)
        payload_variant_count = len(raw_payloads)
        variant_count = len(cn_display_normalized)
        result.append(
            {
                "normalized_payload": normalized_payload,
                "items": items,
                "status": status,
                "notes": notes,
                "raw_payloads": raw_payloads,
                "cn_displays": cn_displays,
                "cn_display_normalized": cn_display_normalized,
                "jpn_displays": jpn_displays,
                "payload_variant_count": payload_variant_count,
                "variant_count": variant_count,
                "occurrences": len(items),
            }
        )
    status_order = {"REVIEW_VARIANT": 0, "POSSIBLE_PAYLOAD_VARIANT": 1, "CONTEXTUAL": 2, "CONSISTENT": 3}
    result.sort(key=lambda group: (status_order.get(group["status"], 9), -group["occurrences"], -group["variant_count"], group["normalized_payload"]))
    return result


def csv_rows(groups: list[dict[str, Any]]) -> list[dict[str, str]]:
    rows: list[dict[str, str]] = []
    for group in groups:
        for key, count in Counter(
            (
                item.cn_payload,
                item.cn_display,
                item.jpn_display,
                item.eng_reference,
                item.old_cn,
                item.resource_class,
                item.file_id,
                item.identity,
            )
            for item in group["items"]
        ).items():
            raw_payload, cn_display, jpn_display, eng_reference, old_cn, resource_class, file_id, identity = key
            matching = [item for item in group["items"] if (item.cn_payload, item.cn_display, item.jpn_display, item.eng_reference, item.old_cn, item.resource_class, item.file_id, item.identity) == key]
            cn_payloads = unique_values(item.cn_payload for item in group["items"])
            cn_displays = unique_values(item.cn_display for item in group["items"])
            jpn_displays = unique_values(item.jpn_display for item in group["items"] if item.jpn_display)
            rows.append(
                {
                    "normalized_payload": group["normalized_payload"],
                    "raw_payload": raw_payload,
                    "cn_display": display_value(cn_display),
                    "jpn_display": display_value(jpn_display),
                    "eng_reference": display_value(eng_reference),
                    "old_cn": display_value(old_cn),
                    "resource_class": resource_class,
                    "file_id": file_id,
                    "identity": identity,
                    "occurrences": str(count),
                    "variant_count": str(group["variant_count"]),
                    "status": group["status"],
                    "notes": group["notes"],
                    "cn_raw_payload": raw_payload,
                    "cn_display_normalized": " | ".join(group["cn_display_normalized"]),
                    "payload_variant_count": str(group["payload_variant_count"]),
                    "payload_variants": " | ".join(cn_payloads),
                    "cn_display_variants": " | ".join(display_value(value) for value in cn_displays),
                    "jpn_display_variants": " | ".join(display_value(value) for value in jpn_displays),
                }
            )
    rows.sort(key=lambda row: (0 if row["status"] == "REVIEW_VARIANT" else 1 if row["status"] == "POSSIBLE_PAYLOAD_VARIANT" else 2, -int(row["occurrences"]), -int(row["variant_count"]), row["normalized_payload"], row["raw_payload"], row["identity"]))
    return rows


def md_value(value: str) -> str:
    return value.replace("|", "\\|").replace("\r", "<CR>").replace("\n", "<LF>")


def render_group_table(groups: list[dict[str, Any]], limit: int | None = None) -> list[str]:
    selected = groups if limit is None else groups[:limit]
    lines = [
        "| rank | normalized payload | raw payloads | CN displays | occurrences | variants | status |",
        "|---:|---|---|---|---:|---:|---|",
    ]
    for rank, group in enumerate(selected, 1):
        lines.append(
            f"| {rank} | `{md_value(group['normalized_payload'])}` | `{md_value(' / '.join(group['raw_payloads']))}` | "
            f"`{md_value(' / '.join(display_value(value) for value in group['cn_displays']))}` | {group['occurrences']} | "
            f"{group['variant_count']} | `{group['status']}` |"
        )
    return lines


def render_markdown(report: dict[str, Any], groups: list[dict[str, Any]]) -> str:
    summary = report["summary"]
    lines = [
        "# Ruby Term Consistency Audit",
        "",
        "本报告只读分析当前全项目 translation corpus 中的 `<R=显示文本,Ruby payload>`，不修改 mapping、CSV、DAT、KEY 或译文。Ruby payload 的原始大小写、空格和拼写均保留；normalized payload 仅用于候选聚合，不代表自动认定同义。",
        "",
        "## Scope",
        "",
        f"- logical file_ids / translation files: `{report['scope']['mapping_files']}`",
        f"- translation rows: `{report['scope']['rows']}`",
        f"- CN Ruby occurrences: `{summary['cn_ruby_occurrences']}`",
        f"- JPN Ruby occurrences: `{summary['jpn_ruby_occurrences']}`",
        f"- CN Ruby rows: `{summary['cn_ruby_rows']}`",
        f"- unique raw payloads in CN: `{summary['unique_raw_payloads']}`",
        f"- normalized payload candidates: `{summary['normalized_payloads']}`",
        "",
        "## Summary",
        "",
        "| status | payload groups |",
        "|---|---:|",
        f"| CONSISTENT | {summary['consistent_groups']} |",
        f"| REVIEW_VARIANT | {summary['review_variant_groups']} |",
        f"| POSSIBLE_PAYLOAD_VARIANT | {summary['possible_payload_variant_groups']} |",
        f"| CONTEXTUAL | {summary['contextual_groups']} |",
        "",
        "## Review priority: all REVIEW_VARIANT groups",
        "",
    ]
    review_groups = [group for group in groups if group["status"] == "REVIEW_VARIANT"]
    lines += render_group_table(review_groups)
    lines += ["", "## Top 50 by variant count", ""]
    lines += render_group_table(sorted(groups, key=lambda group: (-group["variant_count"], -group["occurrences"], group["normalized_payload"]))[:50])
    lines += ["", "## Top 50 high-occurrence groups with multiple CN displays", ""]
    multi_display = [group for group in groups if len(group["cn_display_normalized"]) > 1]
    lines += render_group_table(sorted(multi_display, key=lambda group: (-group["occurrences"], -group["variant_count"], group["normalized_payload"]))[:50])
    lines += ["", "## Known candidate payloads", ""]
    known = {"terminal", "mi viejo", "big boss", "fsln", "sandinista", "frente", "ai", "mission", "target", "area"}
    known_groups = [group for group in groups if group["normalized_payload"] in known or any(group["normalized_payload"].startswith(value + " ") for value in known)]
    lines += render_group_table(known_groups)
    lines += ["", "## Interpretation notes", "", "- `CONSISTENT` means the normalized CN display is single-valued for the normalized payload; it does not establish that the translation is correct.", "- `REVIEW_VARIANT` means multiple meaningful normalized CN displays were observed. Contextual appropriateness is intentionally not decided automatically.", "- `POSSIBLE_PAYLOAD_VARIANT` means only case/spacing normalization grouped multiple raw payload forms while the CN display remained consistent; raw forms remain separate in the CSV.", "- `CONTEXTUAL` is reserved for a future evidence-backed/manual classification and is not assigned automatically in this read-only pass.", "- ENG and MLG_CN values are reference evidence from matching template rows, not translation authority.", ""]
    return "\n".join(lines)


def main() -> int:
    args = parse_args()
    root = args.root.resolve()
    occurrences, input_meta = load_occurrences(root)
    if args.json_audit:
        json_audit_path = args.json_audit.resolve()
    else:
        json_audit_path = root / "build" / "translation" / "cn_special_character_audit.json"
    if not json_audit_path.exists():
        raise RuntimeError(f"special-character audit JSON not found: {json_audit_path}")
    special_audit = json.loads(json_audit_path.read_text(encoding="utf-8"))
    expected_scope = special_audit.get("scope", {})
    if expected_scope.get("mapping_files") != input_meta["mapping_files"] or expected_scope.get("rows") != input_meta["rows"]:
        raise RuntimeError(
            "special-character audit scope mismatch: "
            f"audit={expected_scope.get('mapping_files')}/{expected_scope.get('rows')} "
            f"corpus={input_meta['mapping_files']}/{input_meta['rows']}"
        )
    groups = make_groups(occurrences)
    status_counts = Counter(group["status"] for group in groups)
    report = {
        "status": "PASS",
        "scope": input_meta,
        "source_audit": {
            "path": str(json_audit_path.relative_to(root)),
            "mapping_files": expected_scope.get("mapping_files"),
            "rows": expected_scope.get("rows"),
        },
        "ruby_pattern": r"<R=([^,<>\\r\\n]*),([^<>\\r\\n]*)>",
        "normalization": "NFC + Unicode whitespace collapse + casefold; no whitespace removal, spelling rewrite, or automatic equivalence decision",
        "summary": {
            "cn_ruby_occurrences": len(occurrences),
        "jpn_ruby_occurrences": input_meta["jpn_ruby_occurrences"],
            "cn_ruby_rows": sum(input_meta["cn_ruby_rows"].values()),
            "unique_raw_payloads": len({item.cn_payload for item in occurrences}),
            "normalized_payloads": len(groups),
            "consistent_groups": status_counts["CONSISTENT"],
            "review_variant_groups": status_counts["REVIEW_VARIANT"],
            "possible_payload_variant_groups": status_counts["POSSIBLE_PAYLOAD_VARIANT"],
            "contextual_groups": status_counts["CONTEXTUAL"],
            "ruby_rows_by_resource_class": input_meta["cn_ruby_rows"],
        },
        "groups": [
            {
                "normalized_payload": group["normalized_payload"],
                "raw_payloads": group["raw_payloads"],
                "cn_displays": group["cn_displays"],
                "jpn_displays": group["jpn_displays"],
                "occurrences": group["occurrences"],
                "variant_count": group["variant_count"],
                "payload_variant_count": group["payload_variant_count"],
                "status": group["status"],
                "notes": group["notes"],
            }
            for group in groups
        ],
    }
    output_dir = root / "build" / "translation"
    csv_path = (args.csv_output or output_dir / "ruby_term_consistency_review.csv").resolve()
    md_path = (args.markdown_output or output_dir / "ruby_term_consistency_audit.md").resolve()
    csv_path.parent.mkdir(parents=True, exist_ok=True)
    md_path.parent.mkdir(parents=True, exist_ok=True)
    # This CSV is a human-review artifact and must open correctly in Windows Excel.
    with csv_path.open("w", encoding="utf-8-sig", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=CSV_FIELDS)
        writer.writeheader()
        writer.writerows(csv_rows(groups))
    md_path.write_text(render_markdown(report, groups), encoding="utf-8")
    print("STATUS=PASS")
    print(f"FILE_IDS={input_meta['mapping_files']}")
    print(f"ROWS={input_meta['rows']}")
    print(f"CN_RUBY_OCCURRENCES={report['summary']['cn_ruby_occurrences']}")
    print(f"UNIQUE_RAW_PAYLOADS={report['summary']['unique_raw_payloads']}")
    print(f"NORMALIZED_PAYLOADS={report['summary']['normalized_payloads']}")
    print(f"CONSISTENT_GROUPS={report['summary']['consistent_groups']}")
    print(f"REVIEW_VARIANT_GROUPS={report['summary']['review_variant_groups']}")
    print(f"POSSIBLE_PAYLOAD_VARIANT_GROUPS={report['summary']['possible_payload_variant_groups']}")
    print(f"CSV_OUTPUT={csv_path}")
    print(f"MARKDOWN_OUTPUT={md_path}")
    return 0


if __name__ == "__main__":
    try:
        raise SystemExit(main())
    except (OSError, ValueError, json.JSONDecodeError, RuntimeError) as error:
        print(f"ERROR: {error}")
        raise SystemExit(1)
