#!/usr/bin/env python3
"""Export ASCII-source translations that may regress on Latin-only UI fonts.

The report is intentionally conservative: it includes every formal translation
row whose JPN text is entirely ASCII, contains at least one Latin letter, and
whose Chinese translation contains at least one CJK ideograph.  It does not
change any translation or infer that every candidate is broken in game.
"""

from __future__ import annotations

import argparse
import csv
import re
from collections import Counter
from pathlib import Path


RESOURCE_DIRS = {
    "YPK_GTT": "ypk_gtt",
    "OHD": "ohd",
    "SLOT_OLANG": "slot_olang",
    "LOOSE_OLANG": "loose_olang",
    "STAGEDAT_OLANG": "stagedat_olang",
}

CJK_RE = re.compile(r"[\u3400-\u4dbf\u4e00-\u9fff]")
LATIN_RE = re.compile(r"[A-Za-z]")
MARKUP_RE = re.compile(r"<[^>]*>|\$\d+")

OUTPUT_FIELDS = [
    "risk_priority",
    "resource_class",
    "file_id",
    "unique_index",
    "first_reference_index",
    "reference_indices",
    "entity_context",
    "jpn_text",
    "cn_text",
    "mlg_cn_reference",
    "mlg_cn_reference_variants",
    "eng_reference",
    "eng_reference_variants",
    "reference_status",
    "reference_method",
    "reference_reason",
    "mlg_cn_patch_action",
    "previous_jpn_text",
    "next_jpn_text",
    "jpn_utf8_bytes",
    "cn_utf8_bytes",
    "has_markup",
    "has_newline",
    "source_is_uppercase_label",
    "candidate_reason",
    "recommended_action",
    "notes",
    "source_csv",
]


def is_ascii_source(text: str) -> bool:
    return bool(text and LATIN_RE.search(text)) and text.isascii()


def classify(resource_class: str, text: str) -> tuple[str, str, str]:
    visible = MARKUP_RE.sub("", text).strip()
    single_line = "\n" not in text and "\r" not in text
    letters = "".join(ch for ch in visible if ch.isalpha())
    uppercase_label = bool(letters) and letters == letters.upper()
    short_label = single_line and len(visible) <= 40

    if resource_class in {"SLOT_OLANG", "LOOSE_OLANG", "STAGEDAT_OLANG"}:
        if short_label and uppercase_label:
            return (
                "HIGH",
                "Short uppercase ASCII label was localized to CJK; it may use a Latin-only UI font.",
                "Check the exact in-game screen; preserve the JPN ASCII label if the CJK translation is blank.",
            )
        if short_label:
            return (
                "MEDIUM",
                "Short ASCII UI-like text was localized to CJK; font coverage depends on the rendering context.",
                "Check the exact in-game screen before deciding whether to preserve ASCII.",
            )
        return (
            "LOW",
            "ASCII source body/help text was translated to CJK; inclusion is exhaustive, not proof of a font problem.",
            "Keep translated unless an in-game font/rendering failure is observed.",
        )

    return (
        "LOW",
        "ASCII source dialogue/subtitle text was translated to CJK; normal text fonts may support it.",
        "Keep translated unless an in-game font/rendering failure is observed.",
    )


def classify_mlg_cn_reference(template_row: dict[str, str]) -> str:
    reference = template_row.get("mlg_cn_reference", "")
    status = template_row.get("reference_status", "")
    eng_reference = template_row.get("eng_reference", "")
    if reference:
        if CJK_RE.search(reference):
            return "TRANSLATED_TO_CJK"
        if reference.isascii() and LATIN_RE.search(reference):
            return "KEPT_OR_REWORDED_ASCII"
        return "NON_CJK_OTHER"
    if status == "AUX_UNCHANGED" and eng_reference.isascii() and LATIN_RE.search(eng_reference):
        return "KEPT_ASCII_AUX_UNCHANGED"
    return "NO_RELIABLE_MLG_CN_REFERENCE"


def main() -> int:
    parser = argparse.ArgumentParser()
    project_root = Path(__file__).resolve().parents[1]
    parser.add_argument(
        "--translations-root",
        type=Path,
        default=project_root / "translations",
    )
    parser.add_argument(
        "--output",
        type=Path,
        default=project_root / "build" / "ui_font_audit" / "ascii_source_translated_to_chinese.csv",
    )
    args = parser.parse_args()

    output_rows: list[dict[str, str]] = []
    scanned_rows = 0
    template_root = project_root / "work" / "luna_translation_templates"

    for resource_class, directory in RESOURCE_DIRS.items():
        resource_root = args.translations_root / directory
        for csv_path in sorted(resource_root.glob("*.csv")):
            template_rows: dict[str, dict[str, str]] = {}
            template_path = template_root / resource_class / csv_path.name
            if template_path.exists():
                with template_path.open("r", encoding="utf-8-sig", newline="") as handle:
                    template_rows = {
                        row.get("unique_index", ""): row for row in csv.DictReader(handle)
                    }
            with csv_path.open("r", encoding="utf-8-sig", newline="") as handle:
                for row in csv.DictReader(handle):
                    scanned_rows += 1
                    jpn_text = row.get("jpn_text", "")
                    cn_text = row.get("cn_text", "")
                    if not is_ascii_source(jpn_text):
                        continue
                    if not cn_text or cn_text == jpn_text or not CJK_RE.search(cn_text):
                        continue

                    priority, reason, action = classify(resource_class, jpn_text)
                    template_row = template_rows.get(row.get("unique_index", ""), {})
                    letters = "".join(
                        ch for ch in MARKUP_RE.sub("", jpn_text) if ch.isalpha()
                    )
                    output_rows.append(
                        {
                            "risk_priority": priority,
                            "resource_class": resource_class,
                            "file_id": row.get("file_id", csv_path.stem),
                            "unique_index": row.get("unique_index", ""),
                            "first_reference_index": row.get("first_reference_index", ""),
                            "reference_indices": row.get("reference_indices", ""),
                            "entity_context": row.get("entity_context", ""),
                            "jpn_text": jpn_text,
                            "cn_text": cn_text,
                            "mlg_cn_reference": template_row.get("mlg_cn_reference", ""),
                            "mlg_cn_reference_variants": template_row.get(
                                "mlg_cn_reference_variants", "[]"
                            ),
                            "eng_reference": template_row.get("eng_reference", ""),
                            "eng_reference_variants": template_row.get(
                                "eng_reference_variants", "[]"
                            ),
                            "reference_status": template_row.get("reference_status", ""),
                            "reference_method": template_row.get("reference_method", ""),
                            "reference_reason": template_row.get("reference_reason", ""),
                            "mlg_cn_patch_action": classify_mlg_cn_reference(template_row),
                            "previous_jpn_text": row.get("previous_jpn_text", ""),
                            "next_jpn_text": row.get("next_jpn_text", ""),
                            "jpn_utf8_bytes": str(len(jpn_text.encode("utf-8"))),
                            "cn_utf8_bytes": str(len(cn_text.encode("utf-8"))),
                            "has_markup": "YES" if MARKUP_RE.search(jpn_text) else "NO",
                            "has_newline": "YES" if "\n" in jpn_text or "\r" in jpn_text else "NO",
                            "source_is_uppercase_label": (
                                "YES" if letters and letters == letters.upper() else "NO"
                            ),
                            "candidate_reason": reason,
                            "recommended_action": action,
                            "notes": row.get("notes", ""),
                            "source_csv": str(csv_path.relative_to(project_root)),
                        }
                    )

    priority_rank = {"HIGH": 0, "MEDIUM": 1, "LOW": 2}
    output_rows.sort(
        key=lambda row: (
            priority_rank[row["risk_priority"]],
            row["resource_class"],
            row["file_id"],
            int(row["unique_index"]) if row["unique_index"].isdigit() else row["unique_index"],
        )
    )

    args.output.parent.mkdir(parents=True, exist_ok=True)
    with args.output.open("w", encoding="utf-8-sig", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=OUTPUT_FIELDS, lineterminator="\n")
        writer.writeheader()
        writer.writerows(output_rows)

    by_priority = Counter(row["risk_priority"] for row in output_rows)
    by_resource = Counter(row["resource_class"] for row in output_rows)
    by_mlg_action = Counter(row["mlg_cn_patch_action"] for row in output_rows)
    print(f"CSV_PATH={args.output.resolve()}")
    print(f"SCANNED_ROWS={scanned_rows}")
    print(f"CANDIDATE_ROWS={len(output_rows)}")
    for priority in ("HIGH", "MEDIUM", "LOW"):
        print(f"{priority}={by_priority[priority]}")
    for resource_class in RESOURCE_DIRS:
        print(f"{resource_class}={by_resource[resource_class]}")
    for action in (
        "KEPT_OR_REWORDED_ASCII",
        "KEPT_ASCII_AUX_UNCHANGED",
        "TRANSLATED_TO_CJK",
        "NON_CJK_OTHER",
        "NO_RELIABLE_MLG_CN_REFERENCE",
    ):
        print(f"MLG_CN_{action}={by_mlg_action[action]}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
