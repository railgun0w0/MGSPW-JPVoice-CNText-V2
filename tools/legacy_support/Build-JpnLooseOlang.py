#!/usr/bin/env python3
"""Merge Chinese English-slot text into Japanese slots of loose PC OLANGs.

Each loose OLANG is multilingual.  The English Chinese patch changes the
0xD0E references, while Japanese mode reads 0xDB0.  This tool keeps the
authoritative Japanese file structure and copies only the corresponding
Chinese strings into its Japanese references, then re-encrypts under the
Japanese target filename.
"""

from __future__ import annotations

import argparse
import hashlib
import importlib.util
import json
import re
import struct
import sys
from collections import Counter, defaultdict
from pathlib import Path


MAP = {
    "0005ee2f.olang": "0005ee2f.olang",
    "00327f6a.olang": "00327f6a.olang",
    "0043da6e.olang": "0043da6e.olang",
    "005184e3.olang": "005184e3.olang",
    "0060e2f2.olang": "0060e2f2.olang",
    "0066e64e.olang": "0066e64e.olang",
    "0072f326.olang": "0072f326.olang",
    "007e2f18.olang": "009c9ea4.olang",
    "00c6a046.olang": "00c6a046.olang",
    "00c79b17.olang": "00cd740b.olang",
    "00cb1fb7.olang": "00cb1fb7.olang",
    "00d0c740.olang": "00d0c740.olang",
    "00d345a5.olang": "00d345a5.olang",
    "00225520.olang": "00d9bfd4.olang",
}
ENGLISH_KEY = 0x00000D0E
JAPANESE_KEY = 0x00000DB0
LANGUAGE_ORDER = (0x00000D0E, 0x00000D32, 0x00000D45, 0x00000D94, 0x00000DB0, 0x00000ED0)
MASK32 = 0xFFFFFFFF

# These strings exist only in the newer Japanese-region containers, so the
# older MLG Chinese patch has no semantic source row for them.  Keep this list
# deliberately small and reference-indexed; every other replacement is derived
# from the authoritative files.
MANUAL_OVERRIDES = {
    ("00c79b17.olang", 4): "救援",
    ("00c79b17.olang", 10): "美军导弹基地",
    ("00c79b17.olang", 16): "尼加拉瓜湖东南部",
    ("00c79b17.olang", 22): "NORAD",
    ("00c79b17.olang", 28): "夏延山空军基地",
    ("00c79b17.olang", 34): "\n任务完成",
    ("00225520.olang", 238): "要审问对方，按 <I=CQC>\n擒住对方，然后按 <I=v906_135_gam_inst_2_*0>。",
    ("007e2f18.olang", 6274): "请稍候。",
}
KANA_PATTERN = re.compile(r"[\u3040-\u30ff\uff66-\uff9f]")


def load_rbx_module():
    path = Path(__file__).with_name("Build-JpnInitCache.py")
    spec = importlib.util.spec_from_file_location("build_jpn_init_cache", path)
    if spec is None or spec.loader is None:
        raise RuntimeError(f"cannot load RBX helper: {path}")
    module = importlib.util.module_from_spec(spec)
    sys.modules[spec.name] = module
    spec.loader.exec_module(module)
    return module


RBX = load_rbx_module()


def u32(value: int) -> int:
    return value & MASK32


def sha256(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest().upper()


def filename_seed(path: Path) -> int:
    value = 0
    for byte in path.name.split(".", 1)[0].encode("ascii"):
        value = u32(value * 0x2356F + byte * 0x1D35)
    return value


class PcStream:
    def __init__(self, seed: int) -> None:
        self.state: list[int] = []
        for _ in range(624):
            high = seed & 0xFFFF0000
            seed = u32(seed * 0x10DCD + 1)
            self.state.append(high | (seed >> 16))
            seed = u32(seed * 0x10DCD + 1)
        self.output: list[int] = []
        self.index = 0
        self._twist()

    def _twist(self) -> None:
        for index in range(227):
            value = (self.state[index] & 0x80000000) | (self.state[index + 1] & 0x7FFFFFFF)
            self.state[index] = u32(self.state[index + 397] ^ (value >> 1) ^ (0x9908B0DF if value & 1 else 0))
        for index in range(227, 623):
            value = (self.state[index] & 0x80000000) | (self.state[index + 1] & 0x7FFFFFFF)
            self.state[index] = u32(self.state[index - 227] ^ (value >> 1) ^ (0x9908B0DF if value & 1 else 0))
        value = (self.state[623] & 0x80000000) | (self.state[0] & 0x7FFFFFFF)
        self.state[623] = u32(self.state[396] ^ (value >> 1) ^ (0x9908B0DF if value & 1 else 0))
        self.output = []
        for value in self.state:
            value ^= value >> 11
            value ^= (value << 7) & 0x9D2C5680
            value ^= (value << 15) & 0xEFC60000
            value ^= value >> 18
            self.output.append(u32(value))

    def next(self) -> int:
        if self.index >= 624:
            self._twist()
            self.index = 0
        result = self.output[self.index]
        self.index += 1
        return result


def outer_transform(data: bytes, seed: int) -> bytes:
    stream = PcStream(seed)
    for _ in range(5):
        stream.next()
    output = bytearray(data)
    for offset in range(0, len(output), 4):
        count = min(4, len(output) - offset)
        value = int.from_bytes(output[offset : offset + count], "little")
        value ^= stream.next() ^ 0xB9D3018F
        output[offset : offset + count] = value.to_bytes(4, "little")[:count]
    return bytes(output)


def decrypt(path: Path) -> bytes:
    raw = path.read_bytes()
    plain = raw if raw.startswith(b"RBX\x00") else outer_transform(raw, filename_seed(path))
    if not plain.startswith(b"RBX\x00"):
        raise RBX.FormatError(f"{path}: outer decryption did not produce RBX")
    return plain


def encrypt_for(path: Path, plain: bytes) -> bytes:
    encrypted = outer_transform(plain, filename_seed(path))
    if outer_transform(encrypted, filename_seed(path)) != plain:
        raise RBX.FormatError(f"{path}: outer cipher round-trip failed")
    return encrypted


def refs_for_language(rbx, entity, language_key: int) -> tuple[int, ...]:
    return tuple(
        index
        for index in range(entity.reference_index, entity.reference_index + entity.reference_count)
        if rbx.references[index].language_key == language_key
    )


def paired_english_index(rbx, reference_index: int) -> int | None:
    """Return the EN row paired with a row in a multilingual reference run.

    Most groups are EN/FR/DE/IT/JA/ES.  Some files duplicate every language
    row, producing EN/EN/FR/FR/.../JA/JA; matching the ordinal within each run
    handles both layouts without relying on entity spans.
    """
    key = rbx.references[reference_index].language_key
    if key == ENGLISH_KEY:
        return reference_index
    try:
        language_position = LANGUAGE_ORDER.index(key)
    except ValueError:
        return None
    if language_position == 0:
        return reference_index

    run_start = reference_index
    while run_start > 0 and rbx.references[run_start - 1].language_key == key:
        run_start -= 1
    ordinal = reference_index - run_start
    cursor = run_start
    for preceding_key in reversed(LANGUAGE_ORDER[:language_position]):
        run_end = cursor
        preceding_start = run_end
        while preceding_start > 0 and rbx.references[preceding_start - 1].language_key == preceding_key:
            preceding_start -= 1
        if preceding_start == run_end:
            return None
        if preceding_key == ENGLISH_KEY:
            paired = preceding_start + ordinal
            return paired if paired < run_end else None
        cursor = preceding_start
    return None


def normalize_anchor(text: str) -> str:
    text = re.sub(r"<[^>]*>", " ", text.casefold())
    return " ".join(re.findall(r"[a-z0-9]+", text))


def source_english_for_japanese(rbx, japanese_index: int) -> int | None:
    if rbx.references[japanese_index].language_key != JAPANESE_KEY:
        return None
    paired = paired_english_index(rbx, japanese_index)
    if paired is None or rbx.references[paired].language_key != ENGLISH_KEY:
        return None
    return paired


def rebuild_target(target, final_texts: list[str], label: str) -> bytes:
    if len(final_texts) != len(target.references):
        raise RBX.FormatError(f"{label}: final text count mismatch")
    body = bytearray()
    group_offsets: dict[tuple[int, bytes], int] = {}
    new_offsets: list[int] = []
    for reference, text in zip(target.references, final_texts):
        encoded = text.encode("utf-8")
        group = (reference.body_offset, encoded)
        if group not in group_offsets:
            group_offsets[group] = len(body)
            body.extend(encoded)
            body.append(0)
            if len(body) % 2:
                body.append(0)
        new_offsets.append(group_offsets[group])

    output = bytearray(target.raw[: target.reference_offset])
    for reference, relative in zip(target.references, new_offsets):
        output.extend(struct.pack("<III", reference.language_key, relative, reference.flag))
    if len(output) != target.body_offset:
        raise RBX.FormatError(f"{label}: rebuilt reference table missed body offset")
    output.extend(body)
    rebuilt = bytes(output)
    verified = RBX.parse_rbx(rebuilt, f"{label}:rebuilt")
    if [reference.text for reference in verified.references] != final_texts:
        raise RBX.FormatError(f"{label}: text round-trip failed")
    if rebuilt[: target.reference_offset] != target.raw[: target.reference_offset]:
        raise RBX.FormatError(f"{label}: header/entity table changed")
    if [(r.language_key, r.flag) for r in verified.references] != [
        (r.language_key, r.flag) for r in target.references
    ]:
        raise RBX.FormatError(f"{label}: reference metadata changed")
    return rebuilt


def merge_file(target_path: Path, original_path: Path, chinese_path: Path) -> tuple[bytes, dict]:
    target_plain = decrypt(target_path)
    original_plain = decrypt(original_path)
    chinese_plain = decrypt(chinese_path)
    target = RBX.parse_rbx(target_plain, f"{target_path.name}:target")
    original = RBX.parse_rbx(original_plain, f"{chinese_path.name}:original")
    chinese = RBX.parse_rbx(chinese_plain, f"{chinese_path.name}:chinese")

    original_ids = RBX.entity_identities(original.entities)
    chinese_ids = RBX.entity_identities(chinese.entities)
    if original_ids != chinese_ids:
        raise RBX.FormatError(f"{chinese_path.name}: original/Chinese entity identities differ")
    if len(original.references) != len(chinese.references):
        raise RBX.FormatError(f"{chinese_path.name}: original/Chinese reference counts differ")
    for index, (before, after) in enumerate(zip(original.references, chinese.references)):
        if (before.language_key, before.flag) != (after.language_key, after.flag):
            raise RBX.FormatError(f"{chinese_path.name}: reference metadata differs at {index}")

    same_layout = target_plain == original_plain
    original_en_by_text: dict[str, list[int]] = defaultdict(list)
    original_ja_by_text: dict[str, list[int]] = defaultdict(list)
    for index, reference in enumerate(original.references):
        if reference.language_key == ENGLISH_KEY:
            original_en_by_text[reference.text].append(index)
        elif reference.language_key == JAPANESE_KEY and reference.text:
            original_ja_by_text[reference.text].append(index)

    final_texts = [reference.text for reference in target.references]
    conflicts: list[dict] = []
    changed_refs: list[int] = []
    mapping_methods = Counter()
    unmapped_refs: list[int] = []
    mapping_evidence: dict[str, dict] = {}

    for target_ref, target_reference in enumerate(target.references):
        if target_reference.language_key != JAPANESE_KEY:
            continue
        target_en = paired_english_index(target, target_ref)
        if target_en is None:
            unmapped_refs.append(target_ref)
            continue

        selected: str | None = None
        method = ""
        source_refs: list[int] = []
        override = MANUAL_OVERRIDES.get((target_path.name, target_ref))
        if override is not None:
            selected = override
            method = "manual_jpn_only_override"
        elif same_layout:
            source_en = paired_english_index(original, target_ref)
            if source_en is None:
                raise RBX.FormatError(f"{target_path.name}: no paired source EN row for JA reference {target_ref}")
            selected = chinese.references[source_en].text
            source_refs = [source_en]
            method = "identical_layout_reference"
        else:
            # Regional files often retain a long aligned prefix.  Require the
            # local EN or JA anchor to agree before trusting the same index.
            if target_en < len(original.references) and original.references[target_en].language_key == ENGLISH_KEY:
                same_en = original.references[target_en].text == target.references[target_en].text
                same_ja = (
                    target_ref < len(original.references)
                    and original.references[target_ref].language_key == JAPANESE_KEY
                    and bool(target_reference.text)
                    and original.references[target_ref].text == target_reference.text
                )
                if same_en or same_ja:
                    selected = chinese.references[target_en].text
                    source_refs = [target_en]
                    method = "aligned_regional_reference"

            # Exact target-English anchors cover normal regional reorderings.
            if selected is None:
                matches = original_en_by_text.get(target.references[target_en].text, [])
                translations = {chinese.references[index].text for index in matches}
                if matches and len(translations) == 1:
                    selected = next(iter(translations))
                    source_refs = matches
                    method = "exact_english_anchor"

            # A newer target row can consolidate several older source rows.
            # Shared Japanese text identifies the group; English substrings put
            # its Chinese fragments back into target sentence order.
            if selected is None and target_reference.text:
                target_anchor = normalize_anchor(target.references[target_en].text)
                fragments: list[tuple[int, int, str]] = []
                for source_ja in original_ja_by_text.get(target_reference.text, []):
                    source_en = source_english_for_japanese(original, source_ja)
                    if source_en is None:
                        continue
                    source_anchor = normalize_anchor(original.references[source_en].text)
                    position = target_anchor.find(source_anchor) if source_anchor else -1
                    if position >= 0:
                        fragments.append((position, source_en, chinese.references[source_en].text))
                if fragments:
                    fragments.sort(key=lambda item: (item[0], item[1]))
                    unique_fragments: list[tuple[int, int, str]] = []
                    seen_source_refs: set[int] = set()
                    for fragment in fragments:
                        if fragment[1] not in seen_source_refs:
                            unique_fragments.append(fragment)
                            seen_source_refs.add(fragment[1])
                    selected = "".join(fragment[2] for fragment in unique_fragments)
                    source_refs = [fragment[1] for fragment in unique_fragments]
                    method = "composite_japanese_anchor"

            # Finally accept a Japanese semantic anchor only when every source
            # occurrence resolves to the same Chinese text.
            if selected is None and target_reference.text:
                matches = []
                for source_ja in original_ja_by_text.get(target_reference.text, []):
                    source_en = source_english_for_japanese(original, source_ja)
                    if source_en is not None:
                        matches.append(source_en)
                translations = {chinese.references[index].text for index in matches}
                if matches and len(translations) == 1:
                    selected = next(iter(translations))
                    source_refs = matches
                    method = "exact_japanese_anchor"

        if selected is None:
            unmapped_refs.append(target_ref)
            continue
        mapping_methods[method] += 1
        final_texts[target_ref] = selected
        if selected != target.references[target_ref].text:
            changed_refs.append(target_ref)
        mapping_evidence[str(target_ref)] = {"method": method, "source_english_references": source_refs}

    remaining_kana_refs = [
        index
        for index, (reference, text) in enumerate(zip(target.references, final_texts))
        if reference.language_key == JAPANESE_KEY and KANA_PATTERN.search(text)
    ]
    if remaining_kana_refs:
        raise RBX.FormatError(
            f"{target_path.name}: {len(remaining_kana_refs)} Japanese-slot references still contain kana: "
            f"{remaining_kana_refs[:20]}"
        )
    rebuilt_plain = rebuild_target(target, final_texts, target_path.name)
    verified = RBX.parse_rbx(rebuilt_plain, f"{target_path.name}:verified")
    for index, (before, after) in enumerate(zip(target.references, verified.references)):
        if before.language_key != JAPANESE_KEY and before.text != after.text:
            raise RBX.FormatError(f"{target_path.name}: non-Japanese reference {index} changed")
    encrypted = encrypt_for(target_path, rebuilt_plain)
    ja_refs = {index for index, ref in enumerate(target.references) if ref.language_key == JAPANESE_KEY}
    mapped_refs = set(int(index) for index in mapping_evidence)
    return encrypted, {
        "target": target_path.name,
        "source": chinese_path.name,
        "same_plaintext_layout_as_mlg": same_layout,
        "target_sha256": sha256(target_path.read_bytes()),
        "original_mlg_sha256": sha256(original_path.read_bytes()),
        "chinese_source_sha256": sha256(chinese_path.read_bytes()),
        "output_sha256": sha256(encrypted),
        "target_japanese_reference_count": len(ja_refs),
        "mapped_japanese_reference_count": len(mapped_refs & ja_refs),
        "changed_japanese_reference_count": len(changed_refs),
        "unmapped_japanese_reference_count": len(ja_refs - mapped_refs),
        "remaining_kana_japanese_reference_count": len(remaining_kana_refs),
        "reference_mapping_methods": dict(sorted(mapping_methods.items())),
        "unmapped_references": unmapped_refs,
        "mapping_evidence": mapping_evidence,
        "conflicts": conflicts,
    }


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--jpn-dir", type=Path, required=True)
    parser.add_argument("--mlg-original-dir", type=Path, required=True)
    parser.add_argument("--cn-dir", type=Path, required=True)
    parser.add_argument("--output-dir", type=Path, required=True)
    parser.add_argument("--report", type=Path, required=True)
    args = parser.parse_args()
    args.output_dir.mkdir(parents=True, exist_ok=True)
    details: dict[str, dict] = {}
    for target_name, source_name in MAP.items():
        target_path = args.jpn_dir / target_name
        original_path = args.mlg_original_dir / source_name
        chinese_path = args.cn_dir / source_name
        for path in (target_path, original_path, chinese_path):
            if not path.is_file():
                raise FileNotFoundError(path)
        output, detail = merge_file(target_path, original_path, chinese_path)
        output_path = args.output_dir / target_name
        # Older payloads used hardlinks for same-name loose files.  Unlink the
        # destination first so rebuilding can never overwrite the source patch
        # through a pre-existing hardlink.
        if output_path.exists():
            output_path.unlink()
        output_path.write_bytes(output)
        if decrypt(output_path)[:4] != b"RBX\x00":
            raise RBX.FormatError(f"{target_name}: written output did not decrypt")
        details[target_name] = detail

    report = {
        "jpn_dir": str(args.jpn_dir.resolve()),
        "mlg_original_dir": str(args.mlg_original_dir.resolve()),
        "cn_dir": str(args.cn_dir.resolve()),
        "output_dir": str(args.output_dir.resolve()),
        "file_count": len(details),
        "target_japanese_reference_count": sum(item["target_japanese_reference_count"] for item in details.values()),
        "mapped_japanese_reference_count": sum(item["mapped_japanese_reference_count"] for item in details.values()),
        "changed_japanese_reference_count": sum(item["changed_japanese_reference_count"] for item in details.values()),
        "unmapped_japanese_reference_count": sum(item["unmapped_japanese_reference_count"] for item in details.values()),
        "remaining_kana_japanese_reference_count": sum(
            item["remaining_kana_japanese_reference_count"] for item in details.values()
        ),
        "conflict_count": sum(len(item["conflicts"]) for item in details.values()),
        "files": details,
    }
    args.report.parent.mkdir(parents=True, exist_ok=True)
    args.report.write_text(json.dumps(report, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    print(json.dumps({
        "file_count": report["file_count"],
        "target_japanese_reference_count": report["target_japanese_reference_count"],
        "mapped_japanese_reference_count": report["mapped_japanese_reference_count"],
        "changed_japanese_reference_count": report["changed_japanese_reference_count"],
        "unmapped_japanese_reference_count": report["unmapped_japanese_reference_count"],
        "remaining_kana_japanese_reference_count": report["remaining_kana_japanese_reference_count"],
        "conflict_count": report["conflict_count"],
        "report": str(args.report.resolve()),
    }, ensure_ascii=False))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
