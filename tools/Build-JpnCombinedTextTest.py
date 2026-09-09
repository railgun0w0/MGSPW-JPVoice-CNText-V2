#!/usr/bin/env python3
"""Combine reliable legacy text resources with the V2 single-YPK test DAT.

Only SLOT kinds 0x5D (OLANG) and 0x14 (localized text/texture resources) are
transplanted from the legacy text-only payload.  Legacy YPK/OHD data is never
copied; the V2 target DAT remains authoritative for all voice resources.
"""

from __future__ import annotations

import argparse
import importlib.util
import json
import shutil
import sys
from collections import Counter
from pathlib import Path


SAFE_KINDS = {0x5D, 0x14}


class CombineError(RuntimeError):
    pass


def load_module(path: Path, name: str):
    spec = importlib.util.spec_from_file_location(name, path)
    if spec is None or spec.loader is None:
        raise CombineError(f"cannot load helper module: {path}")
    module = importlib.util.module_from_spec(spec)
    sys.modules[name] = module
    spec.loader.exec_module(module)
    return module


def main() -> int:
    v2_root = Path(__file__).resolve().parents[1]
    project_parent = v2_root.parent
    legacy_root = project_parent / "JPVoice_CNText_Experimental"
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--original-dat",
        type=Path,
        default=Path(r"D:\GAME\test\JPN\MGS_PW\mgspw\JPN\disc0_rel\002aba34.DAT"),
    )
    parser.add_argument(
        "--v2-dat",
        type=Path,
        default=v2_root / "build" / "test_1C79F2AD" / "mgspw" / "JPN" / "disc0_rel" / "002aba34.DAT",
    )
    parser.add_argument(
        "--jpn-key",
        type=Path,
        default=Path(r"D:\GAME\test\JPN\MGS_PW\mgspw\JPN\disc0_rel\002aba34.KEY"),
    )
    parser.add_argument(
        "--legacy-text-dat",
        type=Path,
        default=legacy_root / "build" / "text-only" / "mgspw" / "JPN" / "disc0_rel" / "002aba34.DAT",
    )
    parser.add_argument(
        "--output-dir",
        type=Path,
        default=v2_root / "build" / "test_1C79F2AD_fulltext" / "mgspw" / "JPN" / "disc0_rel",
    )
    args = parser.parse_args()

    slot = load_module(legacy_root / "tools" / "Build-JpnSlot.py", "v2_combined_slot")
    full = load_module(
        legacy_root / "tools" / "Build-JpnSlotFullOlang.py",
        "v2_combined_encoder",
    )
    output_dat = args.output_dir / "002aba34.DAT"
    output_key = args.output_dir / "002aba34.KEY"
    report_path = args.output_dir / "combined_text_report.json"
    inputs = {args.original_dat.resolve(), args.v2_dat.resolve(), args.legacy_text_dat.resolve()}
    if output_dat.resolve() in inputs:
        raise CombineError("refusing to overwrite an input DAT")

    seed = slot.CRYPTO.filename_seed(args.jpn_key)
    _, salts, entries = slot.decode_key(args.jpn_key, seed)
    changed_legacy_pages = slot.find_changed_pages(
        args.original_dat, args.legacy_text_dat, entries
    )

    jobs: list[dict] = []
    resource_counts: Counter[str] = Counter()
    excluded_changed_counts: Counter[str] = Counter()
    for page_index in changed_legacy_pages:
        target_raw, target_header = slot.decode_page(
            args.v2_dat, entries[page_index], salts, seed
        )
        legacy_raw, _ = slot.decode_page(
            args.legacy_text_dat, entries[page_index], salts, seed
        )
        target_cnf = slot.parse_cnf(target_raw)
        legacy_cnf = slot.parse_cnf(legacy_raw)
        if target_cnf.signature != legacy_cnf.signature:
            raise CombineError(f"page {page_index}: CNF signature mismatch")

        replacements: dict[int, bytes] = {}
        for tag_index in target_cnf.segments:
            target_segment = target_cnf.segments[tag_index]
            legacy_segment = legacy_cnf.segments[tag_index]
            if target_segment == legacy_segment:
                continue
            kind = target_cnf.tags[tag_index].kind
            if kind in SAFE_KINDS:
                replacements[tag_index] = legacy_segment
                resource_counts[f"0x{kind:02X}"] += 1
            else:
                excluded_changed_counts[f"0x{kind:02X}"] += 1
        if not replacements:
            continue

        merged = slot.rebuild_cnf(target_cnf, replacements)
        verified = slot.parse_cnf(merged)
        for tag_index, replacement in replacements.items():
            if verified.segments[tag_index] != replacement:
                raise CombineError(
                    f"page {page_index} tag {tag_index}: replacement verification failed"
                )
        try:
            encoded, compressed_size, strategy = full.encode_page_best(
                merged,
                target_header,
                entries[page_index].capacity,
                salts,
                seed,
                None,
            )
        except Exception as error:
            raise CombineError(f"page {page_index}: block encode overflow: {error}") from error
        jobs.append(
            {
                "page": page_index,
                "entry": entries[page_index],
                "encoded": encoded,
                "resource_count": len(replacements),
                "compressed_size": compressed_size,
                "strategy": strategy,
            }
        )

    args.output_dir.mkdir(parents=True, exist_ok=True)
    shutil.copyfile(args.v2_dat, output_dat)
    with output_dat.open("r+b") as stream:
        for job in jobs:
            stream.seek(job["entry"].start)
            stream.write(job["encoded"])
    if output_dat.stat().st_size != args.v2_dat.stat().st_size:
        raise CombineError("combined DAT size changed")
    shutil.copyfile(args.jpn_key, output_key)

    report = {
        "base": str(args.v2_dat.resolve()),
        "legacy_text_source": str(args.legacy_text_dat.resolve()),
        "safe_kinds": ["0x14", "0x5D"],
        "legacy_voice_resources_excluded": True,
        "changed_legacy_pages_scanned": len(changed_legacy_pages),
        "patched_pages": len(jobs),
        "patched_resources": sum(resource_counts.values()),
        "patched_resource_kinds": dict(sorted(resource_counts.items())),
        "excluded_changed_resource_kinds": dict(sorted(excluded_changed_counts.items())),
        "output_dat": str(output_dat.resolve()),
        "output_key": str(output_key.resolve()),
    }
    report_path.write_text(
        json.dumps(report, ensure_ascii=False, indent=2) + "\n", encoding="utf-8"
    )
    print(f"PATCHED_PAGES={len(jobs)}")
    print(f"PATCHED_RESOURCES={sum(resource_counts.values())}")
    print(f"RESOURCE_KINDS={json.dumps(dict(sorted(resource_counts.items())))}")
    print("LEGACY_YPK_OHD_INCLUDED=0")
    print(f"DAT_PATH={output_dat.resolve()}")
    print(f"KEY_PATH={output_key.resolve()}")
    print(f"REPORT_PATH={report_path.resolve()}")
    return 0


if __name__ == "__main__":
    try:
        raise SystemExit(main())
    except CombineError as error:
        print(f"ERROR={error}", file=sys.stderr)
        raise SystemExit(1)
