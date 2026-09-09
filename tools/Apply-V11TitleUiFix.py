#!/usr/bin/env python3
"""Apply the reviewed V1.1 title-menu ASCII preservation fix."""

from __future__ import annotations

import argparse
import json
from pathlib import Path


FIXES = {
    390: ("新游戏", "NEW GAME", 8),
    397: ("载入游戏", "LOAD GAME", 9),
    402: ("删除", "DELETE", 6),
}


def parse_args() -> argparse.Namespace:
    root = Path(__file__).resolve().parents[1]
    default_repo = (
        root.parent
        / "JPVoice_CNText_Experimental"
        / ".upload_staging_mgspw_v2_20260906_push"
    )
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--translation-repo", type=Path, default=default_repo)
    parser.add_argument(
        "--mapping-commit",
        default="",
        help="committed shard revision to record in the sharded mapping manifest",
    )
    return parser.parse_args()


def main() -> int:
    args = parse_args()
    mapping_dir = (
        args.translation_repo
        / "work"
        / "luna_translation_templates"
        / "sol_translation_mappings"
        / "LOOSE_OLANG"
    )
    files = [mapping_dir / "007E2F18.part04.json", mapping_dir / "007E2F18.part05.json"]
    seen: set[int] = set()
    for path in files:
        document = json.loads(path.read_text(encoding="utf-8"))
        rows = document.get("translations")
        if not isinstance(rows, list):
            raise RuntimeError(f"{path}: translations array missing")
        changed = False
        for row in rows:
            index = int(row["unique_index"])
            if index not in FIXES:
                continue
            old_text, new_text, expected_bytes = FIXES[index]
            if row.get("cn_text") not in {old_text, new_text}:
                raise RuntimeError(
                    f"{path}: index {index} has unexpected cn_text {row.get('cn_text')!r}"
                )
            row["cn_text"] = new_text
            row["cn_control_tokens"] = ""
            row["cn_utf8_bytes"] = expected_bytes
            row["review_flag"] = (
                "JPN_ASCII_TITLE_UI_PRESERVED; "
                "SMALL_JPN_FONT_COMPATIBILITY; INGAME_FIX_2026-09-09"
            )
            seen.add(index)
            changed = True
        if changed:
            path.write_text(
                json.dumps(document, ensure_ascii=False, separators=(",", ":")) + "\n",
                encoding="utf-8",
            )
    if seen != set(FIXES):
        raise RuntimeError(f"missing fix indices: {sorted(set(FIXES) - seen)}")
    if args.mapping_commit:
        manifest_path = mapping_dir / "007E2F18.manifest.json"
        manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
        updated_parts = 0
        for part in manifest.get("parts", []):
            name = Path(str(part.get("path", ""))).name
            if name in {"007E2F18.part04.json", "007E2F18.part05.json"}:
                part["commit"] = args.mapping_commit
                updated_parts += 1
        if updated_parts != 2:
            raise RuntimeError(f"manifest part update count is {updated_parts}, expected 2")
        note = (
            "In-game V1.1 fix preserves NEW GAME, LOAD GAME, and DELETE as JPN ASCII "
            "because the title menu uses the unexpanded Japanese small UI font."
        )
        notes = manifest.setdefault("notes", [])
        if note not in notes:
            notes.append(note)
        manifest_path.write_text(
            json.dumps(manifest, ensure_ascii=False, separators=(",", ":")) + "\n",
            encoding="utf-8",
        )
    print("FILE_ID=007E2F18")
    print("FIXED_ROWS=3")
    print("INDICES=390,397,402")
    print("VALUES=NEW GAME|LOAD GAME|DELETE")
    if args.mapping_commit:
        print(f"MANIFEST_MAPPING_COMMIT={args.mapping_commit}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
