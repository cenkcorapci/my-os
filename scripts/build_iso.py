#!/usr/bin/env python3
"""Build an unpublished ISO candidate from the checked-in ArchISO profile."""

from __future__ import annotations

import fcntl
import os
import platform
import shutil
import subprocess
import sys
from datetime import datetime, timezone
from pathlib import Path

from validate_config import validate_repository


ROOT = Path(__file__).resolve().parents[1]
DIST = ROOT / "dist"


def main() -> int:
    errors = validate_repository()
    if errors:
        for error in errors:
            print(f"ERROR: {error}", file=sys.stderr)
        return 1
    if platform.system() != "Linux":
        print("ERROR: mkarchiso builds require a Linux host.", file=sys.stderr)
        return 1
    if os.geteuid() != 0:
        print("ERROR: ArchISO builds require root; run `sudo make build`.", file=sys.stderr)
        return 1

    mkarchiso = shutil.which("mkarchiso")
    if not mkarchiso:
        print("ERROR: mkarchiso not found; install the Arch `archiso` package.", file=sys.stderr)
        return 1

    candidate_id = datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%S.%fZ")
    try:
        DIST.mkdir(parents=True, exist_ok=True)
        with (DIST / ".build.lock").open("w", encoding="utf-8") as lock_file:
            try:
                fcntl.flock(lock_file, fcntl.LOCK_EX | fcntl.LOCK_NB)
            except BlockingIOError:
                print("ERROR: another image build is already running.", file=sys.stderr)
                return 1

            staging = DIST / ".staging" / candidate_id
            work = DIST / "work" / candidate_id
            staging.mkdir(parents=True)
            work.mkdir(parents=True)
            command = [
                mkarchiso,
                "-v",
                "-w",
                str(work),
                "-o",
                str(staging),
                str(ROOT / "iso"),
            ]
            print(f"Building unpublished candidate in {staging}")
            result = subprocess.run(command, cwd=ROOT, check=False)
            if result.returncode:
                print(
                    f"ERROR: mkarchiso failed with exit code {result.returncode}; "
                    f"staging output remains at {staging}",
                    file=sys.stderr,
                )
                return result.returncode
            if not list(staging.glob("*.iso")):
                print(
                    f"ERROR: mkarchiso completed without producing an ISO in {staging}",
                    file=sys.stderr,
                )
                return 1
            output = DIST / "candidate" / candidate_id
            output.parent.mkdir(parents=True, exist_ok=True)
            staging.rename(output)
            print(f"Candidate build complete: {output}")
    except OSError as error:
        print(f"ERROR: could not prepare ISO build: {error}", file=sys.stderr)
        return 1
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
