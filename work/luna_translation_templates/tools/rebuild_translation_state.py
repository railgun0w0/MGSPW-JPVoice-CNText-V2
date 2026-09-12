#!/usr/bin/env python3
"""Rebuild and validate the durable Sol translation checkpoint state.

The CSV templates and committed files in sol_translation_mappings are the facts.
Human-maintained progress totals are deliberately not used as input.

Usage:
    python tools/rebuild_translation_state.py --write
    python tools/rebuild_translation_state.py --check
"""

from __future__ import annotations

import argparse
import csv
import datetime as dt
import hashlib
import json
import re
import subprocess
import sys
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any, Iterable


RESOURCE_CLASSES = (
    "YPK_GTT",
    "OHD",
    "LOOSE_OLANG",
    "STAGEDAT_OLANG",
    "SLOT_OLANG",
    "BRIEFING_NBE",
)
GENERATED_LEDGER_BEGIN = "<!-- BEGIN GENERATED COMPLETED LEDGER -->"
GENERATED_LEDGER_END = "<!-- END GENERATED COMPLETED LEDGER -->"
MACHINE_STATE_BEGIN = "<!-- BEGIN TRANSLATION STATE JSON"
MACHINE_STATE_END = "END TRANSLATION STATE JSON -->"
PART_RE = re.compile(r"^(?P<base>.+)\.part\d+\.json$", re.IGNORECASE)


@dataclass
class Template:
    resource_class: str
    file_id: str
    path: Path
    rows: list[dict[str, str]]
    by_index: dict[int, dict[str, str]]
    fingerprint: str


@dataclass
class Representation:
    name: str
    root_path: Path
    paths: list[Path]
    translations: list[dict[str, Any]]
    source_kind: str = "mapping"
    errors: list[str] = field(default_factory=list)
    warnings: list[str] = field(default_factory=list)
    commit: str = ""
    notes: list[str] = field(default_factory=list)
    complete: bool = False
    valid_indices: set[int] = field(default_factory=set)


@dataclass
class FileAudit:
    template: Template
    representations: list[Representation]
    complete: bool
    partial: bool
    canonical: Representation | None
    persisted_indices: set[int]
    errors: list[str]
    warnings: list[str]


@dataclass
class GitFacts:
    repo: Path
    branch: str
    tracked_paths: set[str]
    dirty_paths: set[str]
    latest_commit_by_path: dict[str, str]
    commit_times: dict[str, int]
    known_commits: set[str]


class AuditFailure(RuntimeError):
    pass


def run_git(repo: Path, *args: str, check: bool = True) -> str:
    process = subprocess.run(
        ["git", *args],
        cwd=repo,
        text=True,
        encoding="utf-8",
        errors="replace",
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
    )
    if check and process.returncode:
        raise AuditFailure(
            f"git {' '.join(args)} failed ({process.returncode}): {process.stderr.strip()}"
        )
    return process.stdout.strip()


def find_repo(start: Path) -> Path:
    for candidate in (start, *start.parents):
        if (candidate / ".git").exists():
            return candidate
    raise AuditFailure(f"cannot find Git repository above {start}")


def load_git_facts(repo: Path, template_root: Path, mapping_root: Path) -> GitFacts:
    branch = run_git(repo, "branch", "--show-current") or "DETACHED"
    tracked_paths = {
        line.replace("\\", "/")
        for line in run_git(repo, "ls-files").splitlines()
        if line
    }
    dirty_paths: set[str] = set()
    for line in run_git(repo, "status", "--porcelain", "--untracked-files=all").splitlines():
        if len(line) >= 4:
            raw_path = line[3:]
            if " -> " in raw_path:
                raw_path = raw_path.split(" -> ", 1)[1]
            dirty_paths.add(raw_path.strip('"').replace("\\", "/"))

    history_paths = [
        mapping_root.resolve().relative_to(repo.resolve()).as_posix(),
        *[
            (template_root / resource).resolve().relative_to(repo.resolve()).as_posix()
            for resource in RESOURCE_CLASSES
        ],
    ]
    log_text = run_git(
        repo,
        "log",
        "--format=@@%H%x09%ct%x09%s",
        "--name-only",
        "--",
        *history_paths,
    )
    latest_commit_by_path: dict[str, str] = {}
    commit_times: dict[str, int] = {}
    current_commit = ""
    for line in log_text.splitlines():
        if line.startswith("@@"):
            fields = line[2:].split("\t", 2)
            current_commit = fields[0]
            commit_times[current_commit] = int(fields[1]) if fields[1].isdigit() else 0
        elif line and current_commit:
            latest_commit_by_path.setdefault(line.replace("\\", "/"), current_commit)
    known_commits = set(run_git(repo, "rev-list", "--all").splitlines())
    return GitFacts(
        repo=repo,
        branch=branch,
        tracked_paths=tracked_paths,
        dirty_paths=dirty_paths,
        latest_commit_by_path=latest_commit_by_path,
        commit_times=commit_times,
        known_commits=known_commits,
    )


def json_load(path: Path) -> dict[str, Any]:
    try:
        value = json.loads(path.read_text(encoding="utf-8-sig"))
    except Exception as exc:  # report exact artifact instead of losing the rest of the audit
        raise AuditFailure(f"cannot parse {path}: {exc}") from exc
    if not isinstance(value, dict):
        raise AuditFailure(f"mapping root is not an object: {path}")
    return value


def sha256_template_identity(rows: Iterable[tuple[int, str]]) -> str:
    encoded = json.dumps(
        list(rows), ensure_ascii=False, separators=(",", ":")
    ).encode("utf-8")
    return hashlib.sha256(encoded).hexdigest()


def load_templates(root: Path) -> tuple[dict[tuple[str, str], Template], list[str]]:
    templates: dict[tuple[str, str], Template] = {}
    errors: list[str] = []
    for resource_class in RESOURCE_CLASSES:
        class_dir = root / resource_class
        if not class_dir.is_dir():
            errors.append(f"missing template directory: {class_dir}")
            continue
        for path in sorted(class_dir.glob("*.csv"), key=lambda item: item.name.casefold()):
            try:
                with path.open("r", encoding="utf-8-sig", newline="") as handle:
                    rows = list(csv.DictReader(handle))
            except Exception as exc:
                errors.append(f"cannot read template {path.name}: {exc}")
                continue
            if not rows:
                errors.append(f"empty template: {resource_class}/{path.name}")
                continue
            file_ids = {row.get("file_id", "") for row in rows}
            if len(file_ids) != 1 or not next(iter(file_ids)):
                errors.append(
                    f"template does not contain exactly one nonempty file_id: "
                    f"{resource_class}/{path.name}"
                )
                continue
            file_id = next(iter(file_ids))
            if path.stem != file_id:
                errors.append(
                    f"template filename/file_id mismatch: {resource_class}/{path.name} != {file_id}"
                )
            by_index: dict[int, dict[str, str]] = {}
            for ordinal, row in enumerate(rows):
                try:
                    unique_index = int(row["unique_index"])
                except Exception:
                    errors.append(
                        f"invalid unique_index at {resource_class}/{path.name} row {ordinal + 2}"
                    )
                    continue
                if unique_index in by_index:
                    errors.append(
                        f"duplicate template unique_index {unique_index}: "
                        f"{resource_class}/{path.name}"
                    )
                by_index[unique_index] = row
            expected_indices = set(range(len(rows)))
            if set(by_index) != expected_indices:
                errors.append(
                    f"template indices are not contiguous 0..{len(rows) - 1}: "
                    f"{resource_class}/{path.name}"
                )
            key = (resource_class, file_id)
            if key in templates:
                errors.append(f"duplicate template file_id: {resource_class}/{file_id}")
                continue
            fingerprint = sha256_template_identity(
                (index, by_index[index].get("jpn_text", "")) for index in sorted(by_index)
            )
            templates[key] = Template(
                resource_class=resource_class,
                file_id=file_id,
                path=path,
                rows=rows,
                by_index=by_index,
                fingerprint=fingerprint,
            )
    return templates, errors


def resolve_member_path(
    template_root: Path, mapping_root: Path, descriptor: Path, raw_path: str
) -> Path:
    normalized = raw_path.replace("\\", "/")
    relative = Path(normalized)
    candidates: list[Path] = []
    if relative.is_absolute():
        candidates.append(relative)
    if normalized.startswith("sol_translation_mappings/"):
        candidates.append(template_root / relative)
    candidates.extend((descriptor.parent / relative, mapping_root / relative))
    if len(relative.parts) == 1:
        candidates.append(descriptor.parent / relative.name)
    for candidate in candidates:
        if candidate.is_file():
            return candidate.resolve()
    return candidates[0].resolve() if candidates else (descriptor.parent / relative).resolve()


def path_commit(git: GitFacts, path: Path) -> str:
    try:
        relative = path.resolve().relative_to(git.repo.resolve()).as_posix()
    except ValueError:
        return ""
    return git.latest_commit_by_path.get(relative, "")


def path_is_committed_clean(git: GitFacts, path: Path) -> tuple[bool, str]:
    try:
        relative = path.resolve().relative_to(git.repo.resolve()).as_posix()
    except ValueError:
        return False, "artifact is outside repository"
    if relative not in git.tracked_paths:
        return False, "artifact is not tracked by Git"
    if relative in git.dirty_paths:
        return False, "artifact has uncommitted changes"
    return True, ""


def normalize_notes(value: Any) -> list[str]:
    if isinstance(value, str) and value.strip():
        return [value.strip()]
    if isinstance(value, list):
        return [str(item).strip() for item in value if str(item).strip()]
    return []


def descriptor_members(data: dict[str, Any]) -> list[dict[str, Any]]:
    value = data.get("parts")
    if not isinstance(value, list):
        value = data.get("shards")
    return value if isinstance(value, list) else []


def normalize_translation_rows(
    data: dict[str, Any], rows: list[Any], path: Path
) -> list[dict[str, Any]]:
    if all(isinstance(row, dict) for row in rows):
        return list(rows)
    columns = data.get("columns")
    if not isinstance(columns, list) or not all(isinstance(item, str) for item in columns):
        raise AuditFailure(
            f"mapping uses positional rows without a valid columns array: {path}"
        )
    normalized: list[dict[str, Any]] = []
    for ordinal, row in enumerate(rows):
        if not isinstance(row, list) or len(row) != len(columns):
            raise AuditFailure(
                f"invalid positional translation item {ordinal} in {path}: "
                f"expected {len(columns)} values"
            )
        normalized.append(dict(zip(columns, row)))
    return normalized


def rows_from_file(path: Path) -> tuple[dict[str, Any], list[dict[str, Any]]]:
    data = json_load(path)
    rows = data.get("translations")
    if not isinstance(rows, list):
        raise AuditFailure(f"mapping has no translations array: {path}")
    return data, normalize_translation_rows(data, rows, path)


def build_representation(
    git: GitFacts,
    template_root: Path,
    mapping_root: Path,
    root_path: Path,
    root_data: dict[str, Any],
) -> Representation:
    members = descriptor_members(root_data)
    translations: list[dict[str, Any]] = []
    paths = [root_path.resolve()]
    errors: list[str] = []
    warnings: list[str] = []
    notes = normalize_notes(root_data.get("notes"))
    if members:
        for member in members:
            if not isinstance(member, dict) or not member.get("path"):
                errors.append(f"invalid member entry in {root_path.name}: {member!r}")
                continue
            member_path = resolve_member_path(
                template_root, mapping_root, root_path, str(member["path"])
            )
            paths.append(member_path)
            if not member_path.is_file():
                errors.append(
                    f"descriptor member is missing: {root_path.name} -> {member['path']}"
                )
                continue
            try:
                member_data, member_rows = rows_from_file(member_path)
            except AuditFailure as exc:
                errors.append(str(exc))
                continue
            translations.extend(member_rows)
            notes.extend(normalize_notes(member_data.get("notes")))
            declared_rows = member.get("rows", member.get("row_count"))
            if declared_rows is not None and int(declared_rows) != len(member_rows):
                errors.append(
                    f"member row count mismatch: {member_path.name} "
                    f"declares {declared_rows}, has {len(member_rows)}"
                )
            first = member.get("first_unique_index")
            last = member.get("last_unique_index")
            range_text = member.get("range")
            if range_text and isinstance(range_text, str) and re.fullmatch(r"\d+-\d+", range_text):
                first, last = (int(value) for value in range_text.split("-", 1))
            actual_indices: list[int] = []
            for row in member_rows:
                try:
                    actual_indices.append(int(row.get("unique_index")))
                except Exception:
                    pass
            if first is not None and last is not None and actual_indices:
                if min(actual_indices) != int(first) or max(actual_indices) != int(last):
                    errors.append(
                        f"member range mismatch: {member_path.name} declares "
                        f"{first}-{last}, has {min(actual_indices)}-{max(actual_indices)}"
                    )
            declared_commit = member.get("commit")
            if declared_commit:
                if str(declared_commit) not in git.known_commits:
                    errors.append(
                        f"descriptor references unknown commit {declared_commit}: {member_path.name}"
                    )
    else:
        value = root_data.get("translations")
        if isinstance(value, list):
            translations.extend(normalize_translation_rows(root_data, value, root_path))
        else:
            errors.append(f"mapping has neither translations nor parts/shards: {root_path.name}")
    declared_total = root_data.get("row_count")
    if declared_total is not None and int(declared_total) != len(translations):
        errors.append(
            f"root row count mismatch: {root_path.name} declares {declared_total}, "
            f"has {len(translations)}"
        )
    for path in paths:
        clean, reason = path_is_committed_clean(git, path)
        if not clean:
            errors.append(f"{path.name}: {reason}")
    return Representation(
        name=root_path.name,
        root_path=root_path.resolve(),
        paths=paths,
        translations=translations,
        source_kind="mapping",
        errors=errors,
        warnings=warnings,
        commit=path_commit(git, root_path),
        notes=notes,
    )


def validate_representation(
    rep: Representation, template: Template, *, validate_root_metadata: bool = True
) -> None:
    expected = set(template.by_index)
    seen: dict[int, dict[str, Any]] = {}
    if validate_root_metadata:
        root_data = json_load(rep.root_path)
        if root_data.get("file_id") != template.file_id:
            rep.errors.append(
                f"root file_id mismatch: {root_data.get('file_id')!r} != {template.file_id!r}"
            )
        if root_data.get("resource_class") != template.resource_class:
            rep.errors.append(
                f"root resource_class mismatch: {root_data.get('resource_class')!r} "
                f"!= {template.resource_class!r}"
            )
    byte_mismatches: list[tuple[int, int, int]] = []
    for ordinal, row in enumerate(rep.translations):
        if not isinstance(row, dict):
            rep.errors.append(f"translation item {ordinal} is not an object")
            continue
        try:
            unique_index = int(row.get("unique_index"))
        except Exception:
            rep.errors.append(f"translation item {ordinal} has invalid unique_index")
            continue
        if unique_index in seen:
            rep.errors.append(f"duplicate mapping unique_index {unique_index}")
            continue
        seen[unique_index] = row
        if unique_index not in expected:
            rep.errors.append(f"extra mapping unique_index {unique_index}")
            continue
        if "cn_text" not in row or not isinstance(row.get("cn_text"), str):
            rep.errors.append(f"unique_index {unique_index} has no string cn_text")
            continue
        if "cn_utf8_bytes" in row and row.get("cn_utf8_bytes") not in (None, ""):
            actual_bytes = len(row["cn_text"].encode("utf-8"))
            try:
                declared_bytes = int(row["cn_utf8_bytes"])
            except Exception:
                rep.warnings.append(f"unique_index {unique_index} has invalid cn_utf8_bytes")
            else:
                if declared_bytes != actual_bytes:
                    byte_mismatches.append((unique_index, declared_bytes, actual_bytes))
    if byte_mismatches:
        samples = ", ".join(
            f"{index}:{declared}->{actual}"
            for index, declared, actual in byte_mismatches[:5]
        )
        suffix = ", ..." if len(byte_mismatches) > 5 else ""
        rep.warnings.append(
            f"cn_utf8_bytes differs from actual UTF-8 on {len(byte_mismatches)} rows "
            f"({samples}{suffix}); translation coverage remains valid"
        )
    rep.valid_indices = set(seen).intersection(expected)
    missing = sorted(expected - set(seen))
    if missing:
        display = ",".join(str(value) for value in missing[:12])
        suffix = "..." if len(missing) > 12 else ""
        rep.warnings.append(f"missing {len(missing)} indices: {display}{suffix}")
    rep.complete = not rep.errors and set(seen) == expected


def csv_translation_representation(git: GitFacts, template: Template) -> Representation | None:
    translations: list[dict[str, Any]] = []
    shifted_rows: list[int] = []
    for row in template.rows:
        try:
            unique_index = int(row.get("unique_index", ""))
        except ValueError:
            continue
        status = row.get("translation_status", "")
        if status.startswith("TRANSLATED"):
            translations.append(
                {
                    "unique_index": unique_index,
                    "cn_text": row.get("cn_text", ""),
                    "cn_control_tokens": row.get("cn_control_tokens", ""),
                    "cn_utf8_bytes": row.get("cn_utf8_bytes", ""),
                    "review_flag": row.get("translation_basis", ""),
                }
            )
            continue
        # Seven legacy YPK rows contain one surplus empty CSV cell immediately
        # before cn_text. Their values are shifted right by one column but remain
        # recoverable and committed. Recognize the exact layout without rewriting it.
        if (
            status.isdigit()
            and row.get("build_status", "").startswith("TRANSLATED")
            and row.get("cn_text", "") == ""
            and row.get("cn_control_tokens", "") != ""
        ):
            shifted_rows.append(unique_index)
            translations.append(
                {
                    "unique_index": unique_index,
                    "cn_text": row.get("cn_control_tokens", ""),
                    "cn_control_tokens": row.get("control_structure_status", ""),
                    "cn_utf8_bytes": status,
                    "review_flag": row.get("notes", ""),
                }
            )
    if not translations:
        return None
    clean, reason = path_is_committed_clean(git, template.path)
    errors = [] if clean else [reason]
    notes = [
        "Translation is persisted directly in the committed CSV template rather than a JSON mapping."
    ]
    warnings: list[str] = []
    if shifted_rows:
        indices = ",".join(str(value) for value in shifted_rows)
        warnings.append(
            f"legacy CSV column shift recovered for {len(shifted_rows)} row(s): {indices}; "
            "translation is preserved, but a future merge/build step must normalize the row"
        )
        notes.append(
            f"Legacy shifted CSV rows are mechanically recoverable at unique_index {indices}; "
            "do not retranslate them."
        )
    rep = Representation(
        name=template.path.name,
        root_path=template.path.resolve(),
        paths=[template.path.resolve()],
        translations=translations,
        source_kind="template_csv",
        errors=errors,
        warnings=warnings,
        commit=path_commit(git, template.path),
        notes=notes,
    )
    validate_representation(rep, template, validate_root_metadata=False)
    return rep


def representation_signature(rep: Representation) -> dict[int, tuple[Any, ...]]:
    signature: dict[int, tuple[Any, ...]] = {}
    for row in rep.translations:
        if not isinstance(row, dict):
            continue
        try:
            index = int(row.get("unique_index"))
        except Exception:
            continue
        signature[index] = (
            row.get("cn_text"),
            row.get("cn_control_tokens"),
        )
    return signature


def root_candidates(mapping_dir: Path, file_id: str) -> list[Path]:
    candidates = []
    flat = mapping_dir / f"{file_id}.json"
    manifest = mapping_dir / f"{file_id}.manifest.json"
    if flat.is_file():
        candidates.append(flat)
    if manifest.is_file():
        candidates.append(manifest)
    return candidates


def audit_file(
    git: GitFacts, template_root: Path, mapping_root: Path, template: Template
) -> FileAudit:
    mapping_dir = mapping_root / template.resource_class
    representations: list[Representation] = []
    errors: list[str] = []
    warnings: list[str] = []
    referenced_paths: set[Path] = set()
    for root_path in root_candidates(mapping_dir, template.file_id):
        try:
            root_data = json_load(root_path)
            rep = build_representation(
                git, template_root, mapping_root, root_path, root_data
            )
            validate_representation(rep, template)
        except AuditFailure as exc:
            rep = Representation(
                name=root_path.name,
                root_path=root_path.resolve(),
                paths=[root_path.resolve()],
                translations=[],
                errors=[str(exc)],
                commit=path_commit(git, root_path),
            )
        representations.append(rep)
        referenced_paths.update(rep.paths)

    csv_rep = csv_translation_representation(git, template)
    if csv_rep is not None:
        representations.append(csv_rep)

    part_paths = sorted(
        (
            path
            for path in mapping_dir.glob(f"{file_id_glob(template.file_id)}.part*.json")
            if PART_RE.match(path.name)
        ),
        key=lambda item: item.name.casefold(),
    )
    orphan_parts = [path for path in part_paths if path.resolve() not in referenced_paths]
    if orphan_parts:
        warnings.append(
            "unreferenced shard artifacts: " + ", ".join(path.name for path in orphan_parts)
        )

    complete_reps = [rep for rep in representations if rep.complete]
    if len(complete_reps) > 1:
        signatures = [representation_signature(rep) for rep in complete_reps]
        if any(signature != signatures[0] for signature in signatures[1:]):
            warnings.append(
                "multiple complete representations contain conflicting text/control rows; "
                "the explicit manifest is canonical: "
                + ", ".join(rep.name for rep in complete_reps)
            )
        else:
            warnings.append(
                "duplicate complete representations are byte-equivalent at mapping-row level: "
                + ", ".join(rep.name for rep in complete_reps)
            )

    # Prefer a complete explicit manifest, then a complete descriptor, then a flat mapping.
    def priority(rep: Representation) -> tuple[int, int, str]:
        is_manifest = rep.root_path.name.endswith(".manifest.json")
        has_members = len(rep.paths) > 1
        commit_time = 0
        if rep.commit:
            commit_time = git.commit_times.get(rep.commit, 0)
        source_rank = (
            3
            if is_manifest
            else 2
            if has_members
            else 1
            if rep.source_kind == "mapping"
            else 0
        )
        return (source_rank, commit_time, rep.name)

    canonical = max(complete_reps, key=priority) if complete_reps else None
    persisted_indices: set[int] = set()
    for rep in representations:
        persisted_indices.update(rep.valid_indices)
        errors.extend(f"{rep.name}: {item}" for item in rep.errors)
        warnings.extend(f"{rep.name}: {item}" for item in rep.warnings)
    complete = canonical is not None
    partial = not complete and bool(persisted_indices)
    return FileAudit(
        template=template,
        representations=representations,
        complete=complete,
        partial=partial,
        canonical=canonical,
        persisted_indices=persisted_indices,
        errors=errors,
        warnings=warnings,
    )


def file_id_glob(file_id: str) -> str:
    # Path.glob treats [] specially; current IDs do not use them, but escaping here keeps
    # state reconstruction safe if a future resource name does.
    return file_id.replace("[", "[[]").replace("]", "[]]")


def unknown_mapping_roots(
    mapping_root: Path, templates: dict[tuple[str, str], Template]
) -> list[str]:
    known = set(templates)
    unknown: list[str] = []
    for resource_class in RESOURCE_CLASSES:
        mapping_dir = mapping_root / resource_class
        if not mapping_dir.is_dir():
            unknown.append(f"missing mapping directory: {resource_class}")
            continue
        for path in mapping_dir.glob("*.json"):
            if PART_RE.match(path.name):
                continue
            try:
                file_id = str(json_load(path).get("file_id", ""))
            except AuditFailure as exc:
                unknown.append(str(exc))
                continue
            if (resource_class, file_id) not in known:
                unknown.append(
                    f"mapping root has no template: {resource_class}/{path.name} ({file_id})"
                )
    return unknown


def compact_risk(rep: Representation) -> str:
    if rep.notes:
        summary = " ".join(rep.notes[:2])
        return shorten(summary, 220)
    flags = [
        str(row.get("review_flag", ""))
        for row in rep.translations
        if isinstance(row, dict) and str(row.get("review_flag", "")).strip()
    ]
    categories: list[str] = []
    upper = " ".join(flags).upper()
    for token, label in (
        ("AUX", "auxiliary mismatch/shift flags"),
        ("CONTROL", "control-token flags"),
        ("RUBY", "ruby flags"),
        ("SPACE", "whitespace flags"),
        ("NEWLINE", "newline flags"),
        ("PLACEHOLDER", "placeholder flags"),
    ):
        if token in upper:
            categories.append(label)
    suffix = "; ".join(categories) if categories else "see per-row review_flag"
    return f"{len(flags)}/{len(rep.translations)} rows carry review_flag; {suffix}."


def shorten(value: str, limit: int) -> str:
    compact = " ".join(value.replace("|", "\\|").split())
    if len(compact) <= limit:
        return compact
    return compact[: limit - 1].rstrip() + "…"


def relative(path: Path, base: Path) -> str:
    try:
        return path.resolve().relative_to(base.resolve()).as_posix()
    except ValueError:
        return path.as_posix()


def latest_checkpoint_commit(git: GitFacts, audits: list[FileAudit]) -> str:
    commits = {
        audit.canonical.commit
        for audit in audits
        if audit.complete and audit.canonical and audit.canonical.commit
    }
    if not commits:
        return "NONE"
    ranked: list[tuple[int, str]] = []
    for commit in commits:
        ranked.append((git.commit_times.get(commit, 0), commit))
    return max(ranked)[1]


def state_payload(
    git: GitFacts,
    templates: dict[tuple[str, str], Template],
    audits: list[FileAudit],
    checkpoint: str,
) -> dict[str, Any]:
    branch = git.branch
    completed: dict[str, list[str]] = {resource: [] for resource in RESOURCE_CLASSES}
    remaining: dict[str, list[str]] = {resource: [] for resource in RESOURCE_CLASSES}
    partial: dict[str, list[str]] = {resource: [] for resource in RESOURCE_CLASSES}
    completed_rows: dict[str, int] = {resource: 0 for resource in RESOURCE_CLASSES}
    persisted_rows = 0
    for audit in audits:
        resource = audit.template.resource_class
        file_id = audit.template.file_id
        persisted_rows += len(audit.persisted_indices)
        if audit.complete:
            completed[resource].append(file_id)
            completed_rows[resource] += len(audit.template.rows)
        else:
            remaining[resource].append(file_id)
            if audit.partial:
                partial[resource].append(file_id)
    next_file_id = next(
        (
            file_id
            for resource in RESOURCE_CLASSES
            for file_id in remaining[resource]
        ),
        "NONE",
    )
    errors = [item for audit in audits for item in audit.errors]
    warnings = [item for audit in audits for item in audit.warnings]
    totals_by_class = {
        resource: {
            "total_file_ids": sum(1 for key in templates if key[0] == resource),
            "completed_file_ids": len(completed[resource]),
            "remaining_file_ids": len(remaining[resource]),
            "partial_file_ids": len(partial[resource]),
            "total_rows": sum(
                len(template.rows)
                for key, template in templates.items()
                if key[0] == resource
            ),
            "completed_rows": completed_rows[resource],
        }
        for resource in RESOURCE_CLASSES
    }
    fingerprint_rows = [
        (f"{resource}/{file_id}", templates[(resource, file_id)].fingerprint)
        for resource in RESOURCE_CLASSES
        for file_id in sorted(
            (key[1] for key in templates if key[0] == resource), key=str.casefold
        )
    ]
    catalog_fingerprint = hashlib.sha256(
        json.dumps(
            fingerprint_rows, ensure_ascii=False, separators=(",", ":")
        ).encode("utf-8")
    ).hexdigest()
    return {
        "schema_version": 1,
        "branch": branch,
        "latest_validated_checkpoint_commit": checkpoint,
        "total_rows": sum(len(template.rows) for template in templates.values()),
        "persisted_rows": persisted_rows,
        "completed_rows": sum(completed_rows.values()),
        "total_file_ids": len(templates),
        "completed_file_ids": sum(len(value) for value in completed.values()),
        "remaining_file_ids": sum(len(value) for value in remaining.values()),
        "partial_file_ids": sum(len(value) for value in partial.values()),
        "by_resource_class": totals_by_class,
        "completed": completed,
        "remaining": remaining,
        "partial": partial,
        "next_file_id": next_file_id,
        "validation_errors": len(errors),
        "validation_warnings": len(warnings),
        "template_catalog_sha256": catalog_fingerprint,
    }


def list_inline(values: list[str]) -> str:
    return ", ".join(f"`{value}`" for value in values) if values else "(none)"


def parse_legacy_tracker_snapshot(progress: str) -> dict[str, Any]:
    snapshot: dict[str, Any] = {"by_resource_class": {}}
    patterns = {
        "persisted_rows": r"\| Translation work safely persisted \| \*\*(\d+) / (\d+) rows\*\* \|",
        "completed_file_ids": r"\| file_ids with complete persisted translation \| \*\*(\d+) / (\d+)\*\* \|",
    }
    for key, pattern in patterns.items():
        match = re.search(pattern, progress)
        if match:
            snapshot[key] = int(match.group(1))
            snapshot[f"claimed_total_for_{key}"] = int(match.group(2))
    for resource in RESOURCE_CLASSES:
        match = re.search(
            rf"\| {re.escape(resource)} \| \*\*(\d+) / (\d+) complete\*\* \|",
            progress,
        )
        if match:
            snapshot["by_resource_class"][resource] = {
                "completed_file_ids": int(match.group(1)),
                "total_file_ids": int(match.group(2)),
            }
    return snapshot


def reconcile_legacy_tracker(
    payload: dict[str, Any], snapshot: dict[str, Any]
) -> list[str]:
    differences: list[str] = []
    claimed_rows = snapshot.get("persisted_rows")
    if claimed_rows is not None and claimed_rows != payload["persisted_rows"]:
        delta = claimed_rows - payload["persisted_rows"]
        differences.append(
            f"legacy tracker persisted rows={claimed_rows}, facts={payload['persisted_rows']} "
            f"(legacy delta {delta:+d})"
        )
    claimed_files = snapshot.get("completed_file_ids")
    if claimed_files is not None and claimed_files != payload["completed_file_ids"]:
        delta = claimed_files - payload["completed_file_ids"]
        differences.append(
            f"legacy tracker completed file_ids={claimed_files}, facts={payload['completed_file_ids']} "
            f"(legacy delta {delta:+d})"
        )
    for resource, claim in snapshot.get("by_resource_class", {}).items():
        actual = payload["by_resource_class"][resource]["completed_file_ids"]
        claimed = claim["completed_file_ids"]
        if claimed != actual:
            differences.append(
                f"legacy tracker {resource} completed={claimed}, facts={actual} "
                f"(legacy delta {claimed - actual:+d})"
            )
    return differences


def render_state(payload: dict[str, Any], audits: list[FileAudit]) -> str:
    now = dt.datetime.now().astimezone().replace(microsecond=0).isoformat()
    machine_json = json.dumps(payload, ensure_ascii=False, indent=2, sort_keys=True)
    lines = [
        "# Translation State",
        "",
        "This is the machine-recoverable resume point for the `sol-translation` branch.",
        "It is rebuilt from CSV templates plus committed mapping/manifest/shard files; the prose progress log is not an input.",
        "",
        f"Updated: `{now}`",
        f"Branch: `{payload['branch']}`",
        f"Latest validated checkpoint commit: `{payload['latest_validated_checkpoint_commit']}`",
        f"Total rows / persisted rows: **{payload['total_rows']} / {payload['persisted_rows']}**",
        f"Total file_ids / completed file_ids: **{payload['total_file_ids']} / {payload['completed_file_ids']}**",
        f"Current partial file_id: **{list_inline([value for values in payload['partial'].values() for value in values])}**",
        f"NEXT_FILE_ID: **`{payload['next_file_id']}`**",
        "",
        "## Resource-class status",
        "",
        "| Resource class | Completed file_ids | Completed rows | Remaining | Partial |",
        "|---|---:|---:|---:|---:|",
    ]
    for resource in RESOURCE_CLASSES:
        item = payload["by_resource_class"][resource]
        lines.append(
            f"| {resource} | {item['completed_file_ids']} / {item['total_file_ids']} | "
            f"{item['completed_rows']} / {item['total_rows']} | "
            f"{item['remaining_file_ids']} | {item['partial_file_ids']} |"
        )
    briefing_audits = [
        audit for audit in audits if audit.template.resource_class == "BRIEFING_NBE"
    ]
    briefing_files = [
        audit
        for audit in briefing_audits
        if audit.template.file_id.startswith("BRIEFING_FILES_BLOCK_")
    ]
    briefing_mission = [
        audit
        for audit in briefing_audits
        if audit.template.file_id.startswith("BRIEFING_MISSION_BLOCK_")
    ]
    briefing_rows = [
        row for audit in briefing_audits for row in audit.template.rows
    ]
    briefing_eng_refs = sum(bool(row.get("eng_reference")) for row in briefing_rows)
    briefing_old_cn_refs = sum(
        bool(row.get("mlg_cn_reference")) for row in briefing_rows
    )
    briefing_jpn_rows = sum(bool(row.get("jpn_text")) for row in briefing_rows)
    briefing_cn_rows = sum(bool(row.get("cn_text")) for row in briefing_rows)
    lines.extend(
        (
            "",
            "## 当前 BRIEFING 翻译范围（仅 JPN lane）",
            "",
            "这里的“仅 JPN lane”是 translation-unit corpus 与 topology 的范围声明，不是说 CSV 中完全不能出现英文或旧中文参考。",
            "",
            f"- `BRIEFING_NBE/`：**{len(briefing_audits)} 个 JPN block CSV / {len(briefing_rows)} 条 JPN translation rows**。",
            f"- BRIEFING FILES：**{len(briefing_files)} blocks / {sum(len(audit.template.rows) for audit in briefing_files)} JPN rows**。",
            f"- BRIEFING MISSION：**{len(briefing_mission)} blocks / {sum(len(audit.template.rows) for audit in briefing_mission)} JPN rows**。",
            f"- 源文状态：非空 `jpn_text` **{briefing_jpn_rows}/{len(briefing_rows)}**；非空 `cn_text` **{briefing_cn_rows}/{len(briefing_rows)}**，因此 BRIEFING 目前尚未开始正式翻译。",
            "- 本目录没有将 ENG/FRA/DEU/ITA/ESP lane block 建成独立翻译单元，也不是 B79 全语言 oEbN census 的模板副本。",
            "- 旧初版统计（2,461 translation units / 42,079 全语言物理文本对象 / 42,002 rows）来自错误的六语言聚合，现已废弃，不代表当前模板。",
            f"- 辅助覆盖：`eng_reference` **{briefing_eng_refs} rows**；旧 `mlg_cn_reference` **{briefing_old_cn_refs} rows**。它们只用于理解和措辞参考，不是待翻译源文或翻译权威。",
            "- 每行只把 JPN 权威源文 `jpn_text` 翻译到 `cn_text`；保留 markup/control tokens，并按正常流程更新翻译和控制结构状态。",
            "- 不得机械复制 `eng_reference` / `mlg_cn_reference`。`NO_RELIABLE_AUX_REFERENCE` 行必须依据 JPN 与本 block 上下文翻译。",
            "- 这些模板只是翻译输入：不得修改 JPN 字段或结构索引，也不得把它们视为 DAT/build 产物。",
            "",
            "相关文件：",
            "",
            "- `BRIEFING_NBE/README.md`",
            "- `reference_masters/jpn_briefing_master.csv`",
            "- `tools/Align-JpnBriefingReferences.py`",
            "- `tools/Prepare-JpnBriefingTemplates.py`",
            "- `tools/Prepare-JpnBriefingTemplates.mjs`",
            "- `sol_translation_mappings/BRIEFING_NBE/README.md` (empty mapping intake; no BRIEFING translation is claimed complete yet)",
        )
    )
    lines.extend(("", "## Complete completed file_id list", ""))
    for resource in RESOURCE_CLASSES:
        lines.append(
            f"- {resource} ({len(payload['completed'][resource])}): "
            f"{list_inline(payload['completed'][resource])}"
        )
    lines.extend(("", "## Complete remaining file_id list", ""))
    for resource in RESOURCE_CLASSES:
        lines.append(
            f"- {resource} ({len(payload['remaining'][resource])}): "
            f"{list_inline(payload['remaining'][resource])}"
        )
    lines.extend(("", "## Partial file_id list", ""))
    for resource in RESOURCE_CLASSES:
        lines.append(
            f"- {resource} ({len(payload['partial'][resource])}): "
            f"{list_inline(payload['partial'][resource])}"
        )
    lines.extend(("", "## Legacy tracker reconciliation", ""))
    tracker_differences = payload.get("tracker_reconciliation", [])
    if tracker_differences:
        lines.extend(f"- {item}" for item in tracker_differences)
    else:
        lines.append("- Legacy manual tracker totals agree with current facts.")
    errors = [
        f"{audit.template.resource_class}/{audit.template.file_id}: {item}"
        for audit in audits
        for item in audit.errors
    ]
    warnings = [
        f"{audit.template.resource_class}/{audit.template.file_id}: {item}"
        for audit in audits
        for item in audit.warnings
    ]
    warning_categories = {
        "historical cn_utf8_bytes mismatch": sum(
            "cn_utf8_bytes differs" in item for item in warnings
        ),
        "legacy shifted CSV row": sum(
            "legacy CSV column shift" in item for item in warnings
        ),
        "conflicting complete representations": sum(
            "multiple complete representations" in item for item in warnings
        ),
        "legacy tracker mismatch": len(tracker_differences),
    }
    high_risk_warnings = [
        item for item in warnings if "cn_utf8_bytes differs" not in item
    ]
    lines.extend(
        (
            "",
            "## Validation",
            "",
            f"- Errors: **{len(errors)}**",
            f"- Warnings: **{payload['validation_warnings']}**",
            "- Progress archives audited: "
            + (
                ", ".join(
                    f"`{item['path']}` ({item['sha256'][:12]}…)"
                    for item in payload.get("progress_archives", [])
                )
                or "(none)"
            ),
        )
    )
    lines.extend(
        f"- {label}: **{count}**"
        for label, count in warning_categories.items()
        if count
    )
    if errors:
        lines.extend(f"- ERROR: {item}" for item in errors)
    if high_risk_warnings:
        lines.extend(f"- WARNING: {item}" for item in high_risk_warnings)
    lines.extend(
        (
            "",
            "The JSON block below is authoritative for automated resume/check operations.",
            "The template catalog hash binds every `unique_index + jpn_text` pair without copying the Japanese text into translation mappings.",
            "",
            MACHINE_STATE_BEGIN,
            machine_json,
            MACHINE_STATE_END,
            "",
        )
    )
    return "\n".join(lines)


def render_ledger(repo: Path, audits: list[FileAudit], payload: dict[str, Any]) -> str:
    lines = [
        GENERATED_LEDGER_BEGIN,
        "",
        "This complete ledger is regenerated from committed mappings. It is exhaustive, not a rolling recent-items list.",
        "",
        f"- Complete file_ids: **{payload['completed_file_ids']} / {payload['total_file_ids']}**",
        f"- Complete rows: **{payload['completed_rows']} / {payload['total_rows']}**",
        f"- Mapping-backed persisted rows: **{payload['persisted_rows']} / {payload['total_rows']}**",
        f"- Latest validated mapping checkpoint: `{payload['latest_validated_checkpoint_commit']}`",
        f"- NEXT_FILE_ID: **`{payload['next_file_id']}`**",
        *[f"- Tracker reconciliation: {item}" for item in payload.get("tracker_reconciliation", [])],
        "",
        "| Resource class | file_id | Rows | Mapping / manifest / translated CSV | Commit | Review / risk evidence |",
        "|---|---|---:|---|---|---|",
    ]
    for audit in audits:
        if not audit.complete or not audit.canonical:
            continue
        canonical = audit.canonical
        artifact = relative(canonical.root_path, repo)
        risk = compact_risk(canonical)
        lines.append(
            f"| {audit.template.resource_class} | `{audit.template.file_id}` | "
            f"{len(audit.template.rows)} | `{artifact}` | `{canonical.commit or 'UNCOMMITTED'}` | {risk} |"
        )
    lines.extend(("", GENERATED_LEDGER_END))
    return "\n".join(lines)


def replace_ledger(progress: str, ledger: str) -> str:
    if GENERATED_LEDGER_BEGIN not in progress or GENERATED_LEDGER_END not in progress:
        raise AuditFailure(
            "SOL_TRANSLATION_PROGRESS.md is missing generated ledger markers; "
            "add the durable-log scaffold before --write"
        )
    pattern = re.compile(
        re.escape(GENERATED_LEDGER_BEGIN)
        + r".*?"
        + re.escape(GENERATED_LEDGER_END),
        re.DOTALL,
    )
    return pattern.sub(ledger, progress, count=1)


def extract_machine_state(text: str) -> dict[str, Any]:
    pattern = re.compile(
        re.escape(MACHINE_STATE_BEGIN)
        + r"\s*(.*?)\s*"
        + re.escape(MACHINE_STATE_END),
        re.DOTALL,
    )
    match = pattern.search(text)
    if not match:
        raise AuditFailure("TRANSLATION_STATE.md has no machine state JSON block")
    return json.loads(match.group(1))


def compare_state(expected: dict[str, Any], actual: dict[str, Any]) -> list[str]:
    differences: list[str] = []
    for key, expected_value in expected.items():
        if actual.get(key) != expected_value:
            differences.append(f"state field differs: {key}")
    for key in actual:
        if key not in expected:
            differences.append(f"state has unexpected field: {key}")
    return differences


def inspect_archive_files(template_root: Path) -> tuple[list[dict[str, Any]], list[str]]:
    inventory: list[dict[str, Any]] = []
    warnings: list[str] = []
    archives = sorted(template_root.glob("SOL_TRANSLATION_PROGRESS_ARCHIVE*.md"))
    if not archives:
        warnings.append("no SOL_TRANSLATION_PROGRESS_ARCHIVE*.md files found")
    for path in archives:
        try:
            raw = path.read_bytes()
            text = raw.decode("utf-8-sig")
        except Exception as exc:
            warnings.append(f"cannot read archive {path.name}: {exc}")
            continue
        if not text.strip():
            warnings.append(f"empty progress archive: {path.name}")
        inventory.append(
            {
                "path": path.name,
                "bytes": len(raw),
                "sha256": hashlib.sha256(raw).hexdigest(),
            }
        )
    return inventory, warnings


def write_utf8_lf(path: Path, text: str) -> None:
    with path.open("w", encoding="utf-8", newline="\n") as handle:
        handle.write(text)


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    mode = parser.add_mutually_exclusive_group(required=True)
    mode.add_argument("--write", action="store_true", help="write state and generated ledger")
    mode.add_argument("--check", action="store_true", help="verify state/ledger against facts")
    parser.add_argument(
        "--allow-regression",
        action="store_true",
        help="allow --write to remove formerly completed file_ids (normally refused)",
    )
    args = parser.parse_args()

    script_path = Path(__file__).resolve()
    template_root = script_path.parents[1]
    mapping_root = template_root / "sol_translation_mappings"
    repo = find_repo(template_root)
    git = load_git_facts(repo, template_root, mapping_root)
    progress_path = template_root / "SOL_TRANSLATION_PROGRESS.md"
    state_path = template_root / "TRANSLATION_STATE.md"

    templates, template_errors = load_templates(template_root)
    audits = [
        audit_file(git, template_root, mapping_root, templates[key])
        for resource in RESOURCE_CLASSES
        for key in sorted(
            (item for item in templates if item[0] == resource),
            key=lambda item: item[1].casefold(),
        )
    ]
    unknown_errors = unknown_mapping_roots(mapping_root, templates)
    archive_inventory, archive_warnings = inspect_archive_files(template_root)
    global_errors = template_errors + unknown_errors
    checkpoint = latest_checkpoint_commit(git, audits)
    payload = state_payload(git, templates, audits, checkpoint)
    payload["progress_archives"] = archive_inventory
    payload["validation_errors"] += len(global_errors)
    payload["validation_warnings"] += len(archive_warnings)

    progress_text = progress_path.read_text(encoding="utf-8-sig")
    legacy_snapshot = parse_legacy_tracker_snapshot(progress_text)
    tracker_differences = reconcile_legacy_tracker(payload, legacy_snapshot)
    payload["legacy_tracker_snapshot"] = legacy_snapshot
    payload["tracker_reconciliation"] = tracker_differences
    payload["validation_warnings"] += len(tracker_differences)
    ledger = render_ledger(repo, audits, payload)

    check_differences: list[str] = []
    regressions: list[str] = []
    if args.write:
        if state_path.is_file():
            try:
                previous = extract_machine_state(state_path.read_text(encoding="utf-8-sig"))
                previous_completed = {
                    (resource, file_id)
                    for resource, file_ids in previous.get("completed", {}).items()
                    for file_id in file_ids
                }
                current_completed = {
                    (resource, file_id)
                    for resource, file_ids in payload["completed"].items()
                    for file_id in file_ids
                }
                for resource, file_id in sorted(previous_completed - current_completed):
                    regressions.append(f"formerly completed mapping is no longer complete: {resource}/{file_id}")
            except Exception as exc:
                regressions.append(f"cannot validate previous state before write: {exc}")
        if global_errors or payload["validation_errors"] or (regressions and not args.allow_regression):
            print("WRITE_REFUSED=validation errors or a completed-state regression are present")
        else:
            write_utf8_lf(state_path, render_state(payload, audits))
            write_utf8_lf(progress_path, replace_ledger(progress_text, ledger))
    else:
        if not state_path.is_file():
            check_differences.append("TRANSLATION_STATE.md is missing")
        else:
            try:
                actual_payload = extract_machine_state(
                    state_path.read_text(encoding="utf-8-sig")
                )
                check_differences.extend(compare_state(payload, actual_payload))
            except Exception as exc:
                check_differences.append(str(exc))
        try:
            expected_progress = replace_ledger(progress_text, ledger)
        except AuditFailure as exc:
            check_differences.append(str(exc))
        else:
            if expected_progress != progress_text:
                check_differences.append("generated completed ledger is stale")

    print(f"MODE={'WRITE' if args.write else 'CHECK'}")
    print(f"BRANCH={payload['branch']}")
    print(f"LATEST_VALIDATED_CHECKPOINT_COMMIT={checkpoint}")
    print(f"TOTAL_ROWS={payload['total_rows']}")
    print(f"PERSISTED_ROWS={payload['persisted_rows']}")
    print(f"COMPLETED_ROWS={payload['completed_rows']}")
    print(f"TOTAL_FILE_IDS={payload['total_file_ids']}")
    print(f"COMPLETED_FILE_IDS={payload['completed_file_ids']}")
    print(f"REMAINING_FILE_IDS={payload['remaining_file_ids']}")
    print(f"PARTIAL_FILE_IDS={payload['partial_file_ids']}")
    for resource in RESOURCE_CLASSES:
        item = payload["by_resource_class"][resource]
        print(
            f"{resource}={item['completed_file_ids']}/{item['total_file_ids']} "
            f"rows={item['completed_rows']}/{item['total_rows']}"
        )
    print(f"NEXT_FILE_ID={payload['next_file_id']}")
    print(f"VALIDATION_ERRORS={payload['validation_errors']}")
    print(f"VALIDATION_WARNINGS={payload['validation_warnings']}")
    for item in global_errors:
        print(f"ERROR={item}")
    for audit in audits:
        for item in audit.errors:
            print(
                f"ERROR={audit.template.resource_class}/{audit.template.file_id}: {item}"
            )
        for item in audit.warnings:
            if "cn_utf8_bytes differs" not in item:
                print(
                    f"WARNING={audit.template.resource_class}/{audit.template.file_id}: {item}"
                )
    for item in archive_warnings:
        print(f"WARNING={item}")
    for item in regressions:
        print(f"REGRESSION={item}")
    for item in check_differences:
        print(f"CHECK_DIFFERENCE={item}")

    if args.write and (
        global_errors
        or payload["validation_errors"]
        or (regressions and not args.allow_regression)
    ):
        return 2
    if args.check and check_differences:
        return 3
    if payload["validation_errors"]:
        return 2
    return 0


if __name__ == "__main__":
    try:
        raise SystemExit(main())
    except AuditFailure as exc:
        print(f"FATAL={exc}", file=sys.stderr)
        raise SystemExit(2)
