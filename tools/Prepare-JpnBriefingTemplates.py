#!/usr/bin/env python3
"""Compatibility entry point for the JPN-only BRIEFING Luna templates.

The historical implementation emitted all six physical language lanes. B81
froze the JPN corpus, so this entry point now runs semantic/context alignment
and then the artifact-tool CSV author. It never edits a DAT or invokes a build.
"""

from __future__ import annotations

import argparse
import shutil
import subprocess
import sys
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
ALIGNER = ROOT / "tools" / "Align-JpnBriefingReferences.py"
AUTHOR = ROOT / "tools" / "Prepare-JpnBriefingTemplates.mjs"


def default_node() -> str:
    bundled = (
        Path.home()
        / ".cache"
        / "codex-runtimes"
        / "codex-primary-runtime"
        / "dependencies"
        / "node"
        / "bin"
        / "node.exe"
    )
    if bundled.is_file():
        return str(bundled)
    resolved = shutil.which("node")
    if resolved:
        return resolved
    raise FileNotFoundError("Node.js is required to author artifact-tool CSV templates")


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument(
        "--node",
        default=None,
        help="Node.js executable compatible with the installed @oai/artifact-tool",
    )
    parser.add_argument(
        "--alignment-only",
        action="store_true",
        help="prepare the aligned JSON but do not replace template CSVs",
    )
    args = parser.parse_args()

    subprocess.run([sys.executable, str(ALIGNER)], cwd=ROOT, check=True)
    if not args.alignment_only:
        subprocess.run([args.node or default_node(), str(AUTHOR)], cwd=ROOT, check=True)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
