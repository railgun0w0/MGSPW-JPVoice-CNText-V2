#!/usr/bin/env python3
"""Assemble verified V2 outputs into one sparse, installable test package."""

from __future__ import annotations

import argparse
import json
import shutil
from pathlib import Path


class PackageError(RuntimeError):
    pass


def copy_file(source: Path, destination: Path) -> dict:
    if not source.is_file():
        raise PackageError(f"missing source file: {source}")
    destination.parent.mkdir(parents=True, exist_ok=True)
    shutil.copy2(source, destination)
    if destination.stat().st_size != source.stat().st_size:
        raise PackageError(f"copy size mismatch: {destination}")
    return {
        "source": str(source.resolve()),
        "output": str(destination.resolve()),
        "size": source.stat().st_size,
    }


def parse_args() -> argparse.Namespace:
    root = Path(__file__).resolve().parents[1]
    readiness = root / "build" / "readiness"
    experimental = root.parent / "JPVoice_CNText_Experimental"
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--unified-slot-root",
        type=Path,
        default=readiness / "unified_slot" / "mgspw" / "JPN" / "disc0_rel",
    )
    parser.add_argument(
        "--loose-olang-root",
        type=Path,
        default=readiness / "loose_olang" / "mgspw" / "JPN" / "Text",
    )
    parser.add_argument(
        "--stagedat",
        type=Path,
        default=readiness / "stagedat" / "mgspw" / "JPN" / "disc0_rel" / "009645fa.PDT",
    )
    parser.add_argument(
        "--font-root",
        type=Path,
        default=experimental / "payload-stage2" / "mgspw" / "FONT",
    )
    parser.add_argument(
        "--output-root",
        type=Path,
        default=readiness / "full_package",
    )
    parser.add_argument(
        "--report",
        type=Path,
        default=readiness / "full_package_report.json",
    )
    return parser.parse_args()


def main() -> int:
    args = parse_args()
    root = Path(__file__).resolve().parents[1]
    allowed_root = (root / "build" / "readiness").resolve()
    output_root = args.output_root.resolve()
    if output_root == allowed_root or allowed_root not in output_root.parents:
        raise PackageError(f"output must be a child of {allowed_root}")

    loose_files = sorted(args.loose_olang_root.glob("*.olang"))
    if len(loose_files) != 14:
        raise PackageError(f"expected 14 loose OLANG files, found {len(loose_files)}")
    font_names = ["0007ccd8.xpr", "000ebbe8.xpr", "00c7c9f9.xpr"]

    plan: list[tuple[str, Path, Path]] = [
        (
            "SLOT_DAT",
            args.unified_slot_root / "002aba34.DAT",
            output_root / "mgspw" / "JPN" / "disc0_rel" / "002aba34.DAT",
        ),
        (
            "SLOT_KEY",
            args.unified_slot_root / "002aba34.KEY",
            output_root / "mgspw" / "JPN" / "disc0_rel" / "002aba34.KEY",
        ),
        (
            "STAGEDAT",
            args.stagedat,
            output_root / "mgspw" / "JPN" / "disc0_rel" / args.stagedat.name,
        ),
    ]
    plan.extend(
        (
            "LOOSE_OLANG",
            source,
            output_root / "mgspw" / "JPN" / "Text" / source.name,
        )
        for source in loose_files
    )
    plan.extend(
        (
            "FONT",
            args.font_root / name,
            output_root / "mgspw" / "FONT" / name,
        )
        for name in font_names
    )

    files: list[dict] = []
    for resource_class, source, destination in plan:
        detail = copy_file(source, destination)
        detail["resource_class"] = resource_class
        files.append(detail)

    expected_outputs = {Path(item["output"]).resolve() for item in files}
    actual_outputs = {path.resolve() for path in output_root.rglob("*") if path.is_file()}
    stale = sorted(str(path) for path in actual_outputs - expected_outputs)
    if stale:
        raise PackageError(f"unexpected stale files in package: {stale}")

    report = {
        "status": "PASS",
        "output_root": str(output_root),
        "files": files,
        "summary": {
            "files": len(files),
            "slot_files": 2,
            "loose_olang_files": len(loose_files),
            "stagedat_files": 1,
            "font_files": len(font_names),
            "total_bytes": sum(item["size"] for item in files),
        },
    }
    args.report.parent.mkdir(parents=True, exist_ok=True)
    args.report.write_text(json.dumps(report, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    print(f"PACKAGE_FILES={report['summary']['files']}")
    print(f"LOOSE_OLANG_FILES={report['summary']['loose_olang_files']}")
    print(f"FONT_FILES={report['summary']['font_files']}")
    print(f"PACKAGE_ROOT={output_root}")
    print(f"REPORT_PATH={args.report.resolve()}")
    return 0


if __name__ == "__main__":
    try:
        raise SystemExit(main())
    except PackageError as error:
        print(f"ERROR={error}")
        raise SystemExit(1)
