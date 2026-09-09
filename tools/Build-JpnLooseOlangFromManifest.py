#!/usr/bin/env python3
"""Build translated loose JPN OLANG files from the compiled V2 manifest."""

from __future__ import annotations

import argparse
import csv
import importlib.util
import json
import shutil
import sys
from collections import defaultdict
from pathlib import Path


V2_ROOT = Path(__file__).resolve().parents[1]
LEGACY_TOOLS = V2_ROOT.parent / "JPVoice_CNText_Experimental" / "tools"
DEFAULT_GAME_ROOT = Path(r"D:\GAME\test\JPN\MGS_PW\mgspw")
DEFAULT_MANIFEST = V2_ROOT / "build" / "translation" / "compiled_translation_manifest.csv"
DEFAULT_OUTPUT_ROOT = V2_ROOT / "build" / "readiness" / "loose_olang" / "mgspw"


def load_module(path: Path, name: str):
    spec = importlib.util.spec_from_file_location(name, path)
    if spec is None or spec.loader is None:
        raise RuntimeError(f"cannot load helper module: {path}")
    module = importlib.util.module_from_spec(spec)
    sys.modules[name] = module
    spec.loader.exec_module(module)
    return module


LOOSE = load_module(LEGACY_TOOLS / "Build-JpnLooseOlang.py", "v2_loose_manifest_crypto")
sys.path.insert(0, str(V2_ROOT))
from core.rbx import parse_rbx, rebuild_rbx_texts, structural_signature  # noqa: E402


def parse_integer(value: str) -> int:
    text = str(value).strip()
    if text.lower().startswith("0x"):
        return int(text, 16)
    if any(character in "abcdefABCDEF" for character in text) or (
        len(text) > 1 and text.startswith("0")
    ):
        return int(text, 16)
    return int(text, 10)


def read_manifest(path: Path) -> list[dict[str, str]]:
    with path.open("r", encoding="utf-8-sig", newline="") as handle:
        rows = [
            row
            for row in csv.DictReader(handle)
            if row.get("resource_class") == "LOOSE_OLANG"
            and row.get("translation_status") == "APPROVED"
        ]
    if not rows:
        raise RuntimeError("manifest contains no approved LOOSE_OLANG rows")
    return rows


def translated_texts(rows: list[dict[str, str]], parsed, label: str) -> tuple[list[str], set[int]]:
    by_index: dict[int, dict[str, str]] = {}
    for row in rows:
        index = int(row["reference_index"])
        if row.get("object_type") != "reference" or int(row["object_index"]) != index:
            raise RuntimeError(f"{label}: invalid manifest reference identity")
        if index in by_index:
            raise RuntimeError(f"{label}: duplicate reference {index}")
        by_index[index] = row
    language_keys = {parse_integer(row["language_key"]) for row in rows}
    expected = {
        index
        for index, reference in enumerate(parsed.references)
        if reference.text and reference.language_key in language_keys
    }
    if set(by_index) != expected:
        raise RuntimeError(
            f"{label}: incomplete target reference coverage; "
            f"missing={sorted(expected - set(by_index))}, extra={sorted(set(by_index) - expected)}"
        )

    texts = [reference.text for reference in parsed.references]
    for index, row in by_index.items():
        reference = parsed.references[index]
        if row["jpn_text"] != reference.text:
            raise RuntimeError(f"{label}: JPN text mismatch at reference {index}")
        if parse_integer(row["language_key"]) != reference.language_key:
            raise RuntimeError(f"{label}: language key mismatch at reference {index}")
        if parse_integer(row["style"]) != reference.flag:
            raise RuntimeError(f"{label}: style mismatch at reference {index}")
        cn_text = row.get("cn_text", "")
        if not cn_text and reference.text.strip():
            raise RuntimeError(f"{label}: empty translation at reference {index}")
        cn_text.encode("utf-8", errors="strict")
        texts[index] = cn_text if cn_text else reference.text
    return texts, set(by_index)


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--game-root", type=Path, default=DEFAULT_GAME_ROOT)
    parser.add_argument("--manifest", type=Path, default=DEFAULT_MANIFEST)
    parser.add_argument("--output-root", type=Path, default=DEFAULT_OUTPUT_ROOT)
    parser.add_argument(
        "--report",
        type=Path,
        default=V2_ROOT / "build" / "readiness" / "loose_olang_structure_report.json",
    )
    args = parser.parse_args()

    rows = read_manifest(args.manifest)
    grouped: dict[str, list[dict[str, str]]] = defaultdict(list)
    for row in rows:
        grouped[row["file_id"].upper()].append(row)

    details: list[dict] = []
    for file_id, file_rows in sorted(grouped.items()):
        containers = {row["container"] for row in file_rows}
        if len(containers) != 1:
            raise RuntimeError(f"{file_id}: manifest container conflict: {sorted(containers)}")
        relative = Path(next(iter(containers)))
        source = args.game_root / relative
        if not source.is_file():
            raise FileNotFoundError(source)
        plain = LOOSE.decrypt(source)
        parsed = parse_rbx(plain, file_id)
        texts, target_indices = translated_texts(file_rows, parsed, file_id)
        rebuilt = rebuild_rbx_texts(parsed, texts, file_id)
        verified = parse_rbx(rebuilt, f"{file_id}:rebuilt")
        if structural_signature(verified) != structural_signature(parsed):
            raise RuntimeError(f"{file_id}: structural signature changed")
        for index, (before, after) in enumerate(zip(parsed.references, verified.references)):
            if index not in target_indices and before.text != after.text:
                raise RuntimeError(f"{file_id}: non-target reference {index} changed")

        output = args.output_root / relative
        if output.resolve() == source.resolve():
            raise RuntimeError(f"{file_id}: refusing to overwrite source")
        output.parent.mkdir(parents=True, exist_ok=True)
        encrypted = LOOSE.encrypt_for(output, rebuilt)
        temporary = output.with_name(output.name + ".tmp")
        temporary.write_bytes(encrypted)
        temporary.replace(output)
        roundtrip = parse_rbx(LOOSE.decrypt(output), f"{file_id}:output")
        if [reference.text for reference in roundtrip.references] != texts:
            raise RuntimeError(f"{file_id}: encrypted output text round-trip failed")
        details.append(
            {
                "file_id": file_id,
                "source": str(source),
                "output": str(output),
                "entities": len(parsed.entities),
                "references": len(parsed.references),
                "translated_references": len(target_indices),
                "size_before": source.stat().st_size,
                "size_after": output.stat().st_size,
                "structural_signature_identical": True,
                "non_target_references_identical": True,
                "text_roundtrip": True,
            }
        )

    report = {
        "status": "PASS",
        "manifest": str(args.manifest),
        "file_count": len(details),
        "translated_references": sum(item["translated_references"] for item in details),
        "structural_failures": 0,
        "files": details,
    }
    args.report.parent.mkdir(parents=True, exist_ok=True)
    args.report.write_text(json.dumps(report, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    print(f"FILES_BUILT={report['file_count']}")
    print(f"TRANSLATED_REFERENCES={report['translated_references']}")
    print("STRUCTURAL_FAILURES=0")
    print(f"OUTPUT_ROOT={args.output_root}")
    print(f"REPORT={args.report}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
