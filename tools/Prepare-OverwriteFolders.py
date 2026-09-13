#!/usr/bin/env python3
"""Create directly overlayable patch and pre-patch backup folders."""

from __future__ import annotations

import argparse
import hashlib
import json
import shutil
from pathlib import Path


EXPECTED_FILES = 21


class PrepareError(RuntimeError):
    pass


def sha256_file(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def parse_args() -> argparse.Namespace:
    root = Path(__file__).resolve().parents[1]
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--package-root",
        type=Path,
        default=root / "build" / "readiness" / "full_package",
    )
    parser.add_argument(
        "--game-root",
        type=Path,
        default=Path(r"D:\GAME\steamapps\common\MGS_PW"),
    )
    parser.add_argument(
        "--output-root",
        type=Path,
        default=root / "build" / "distribution",
    )
    return parser.parse_args()


def copy_verified(source: Path, destination: Path) -> dict:
    destination.parent.mkdir(parents=True, exist_ok=True)
    shutil.copy2(source, destination)
    source_hash = sha256_file(source)
    output_hash = sha256_file(destination)
    if source_hash != output_hash:
        raise PrepareError(f"copy hash mismatch: {destination}")
    return {
        "bytes": source.stat().st_size,
        "sha256": source_hash,
    }


def main() -> int:
    args = parse_args()
    root = Path(__file__).resolve().parents[1]
    allowed_root = (root / "build" / "distribution").resolve()
    output_root = args.output_root.resolve()
    if output_root != allowed_root:
        raise PrepareError(f"output root must be exactly {allowed_root}")

    package_root = args.package_root.resolve()
    game_root = args.game_root.resolve()
    if not package_root.is_dir():
        raise PrepareError(f"package root not found: {package_root}")
    if not game_root.is_dir():
        raise PrepareError(f"game root not found: {game_root}")

    patch_root = output_root / "JPVoice_CNText_V2_BRIEFING_MVP_PATCH"
    backup_root = output_root / "JPVoice_CNText_V2_BRIEFING_MVP_BACKUP"
    for destination in (patch_root, backup_root):
        if destination.exists():
            raise PrepareError(
                f"refusing to replace existing output: {destination}; rename or remove it explicitly first"
            )

    package_files = sorted(path for path in package_root.rglob("*") if path.is_file())
    if len(package_files) != EXPECTED_FILES:
        raise PrepareError(
            f"expected {EXPECTED_FILES} package files, found {len(package_files)}"
        )

    plan = []
    for source in package_files:
        relative = source.relative_to(package_root)
        if not relative.parts or relative.parts[0].lower() != "mgspw":
            raise PrepareError(f"package path is not relative to MGS_PW root: {relative}")
        installed = game_root / relative
        if not installed.is_file():
            raise PrepareError(f"installed backup source not found: {installed}")
        plan.append((relative, source, installed))

    patch_rows = []
    backup_rows = []
    changed_from_installed = 0
    for relative, package_source, installed_source in plan:
        patch_detail = copy_verified(package_source, patch_root / relative)
        backup_detail = copy_verified(installed_source, backup_root / relative)
        relative_text = relative.as_posix()
        patch_rows.append({"relative_path": relative_text, **patch_detail})
        backup_rows.append({"relative_path": relative_text, **backup_detail})
        if patch_detail["sha256"] != backup_detail["sha256"]:
            changed_from_installed += 1

    actual_patch = sorted(path for path in patch_root.rglob("*") if path.is_file())
    actual_backup = sorted(path for path in backup_root.rglob("*") if path.is_file())
    if len(actual_patch) != EXPECTED_FILES or len(actual_backup) != EXPECTED_FILES:
        raise PrepareError("generated overlay file count mismatch")

    output_root.mkdir(parents=True, exist_ok=True)
    patch_manifest = {
        "status": "PASS",
        "kind": "PATCH_OVERLAY",
        "copy_destination": str(game_root),
        "overlay_root": str(patch_root),
        "files": patch_rows,
        "summary": {
            "files": len(patch_rows),
            "bytes": sum(row["bytes"] for row in patch_rows),
            "files_different_from_current_install": changed_from_installed,
        },
    }
    backup_manifest = {
        "status": "PASS",
        "kind": "PRE_PATCH_BACKUP_OVERLAY",
        "restore_destination": str(game_root),
        "overlay_root": str(backup_root),
        "files": backup_rows,
        "summary": {
            "files": len(backup_rows),
            "bytes": sum(row["bytes"] for row in backup_rows),
        },
    }
    patch_manifest_path = output_root / "JPVoice_CNText_V2_BRIEFING_MVP_PATCH_MANIFEST.json"
    backup_manifest_path = output_root / "JPVoice_CNText_V2_BRIEFING_MVP_BACKUP_MANIFEST.json"
    patch_manifest_path.write_text(
        json.dumps(patch_manifest, ensure_ascii=False, indent=2) + "\n",
        encoding="utf-8",
    )
    backup_manifest_path.write_text(
        json.dumps(backup_manifest, ensure_ascii=False, indent=2) + "\n",
        encoding="utf-8",
    )
    instructions = output_root / "OVERWRITE_INSTRUCTIONS.txt"
    instructions.write_text(
        "PATCH: copy the contents of JPVoice_CNText_V2_BRIEFING_MVP_PATCH "
        "over the MGS_PW directory.\n"
        "RESTORE: copy the contents of JPVoice_CNText_V2_BRIEFING_MVP_BACKUP "
        "over the same MGS_PW directory.\n"
        "Both overlay folders start with mgspw\\ and contain exactly 21 files.\n",
        encoding="utf-8",
    )

    print(f"PATCH_ROOT={patch_root}")
    print(f"BACKUP_ROOT={backup_root}")
    print(f"PATCH_FILES={len(patch_rows)}")
    print(f"BACKUP_FILES={len(backup_rows)}")
    print(f"PATCH_BYTES={patch_manifest['summary']['bytes']}")
    print(f"BACKUP_BYTES={backup_manifest['summary']['bytes']}")
    print(f"FILES_DIFFERENT_FROM_CURRENT_INSTALL={changed_from_installed}")
    print(f"HASH_MISMATCHES=0")
    return 0


if __name__ == "__main__":
    try:
        raise SystemExit(main())
    except PrepareError as error:
        print(f"ERROR={error}")
        raise SystemExit(1)
