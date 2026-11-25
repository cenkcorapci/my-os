#!/usr/bin/env python3
"""Check host prerequisites for creating and testing an ArchISO image."""

from __future__ import annotations

import platform
import shutil
import sys
from pathlib import Path


def main() -> int:
    failed = False
    checks = [
        ("Linux build host", platform.system() == "Linux", "ArchISO builds require Linux."),
        ("x86_64 host", platform.machine() in {"x86_64", "amd64"}, "Use an x86_64 host."),
        ("Python 3", shutil.which("python3") is not None, "Install Python 3."),
        ("mkarchiso", shutil.which("mkarchiso") is not None, "Install the Arch `archiso` package."),
    ]
    for name, passed, remedy in checks:
        state = "OK" if passed else "MISSING"
        print(f"{state}: {name}" + ("" if passed else f" — {remedy}"))
        failed |= not passed

    qemu = shutil.which("qemu-system-x86_64")
    if qemu:
        print(f"OK: QEMU ({qemu})")
    else:
        print("OPTIONAL: QEMU missing; install qemu-full to boot an ISO locally.")
    firmware_paths = (
        "/usr/share/edk2/x64/OVMF_CODE.4m.fd",
        "/usr/share/OVMF/OVMF_CODE.fd",
    )
    firmware = next((path for path in firmware_paths if Path(path).is_file()), None)
    if firmware:
        print(f"OK: UEFI firmware ({firmware})")
    else:
        print("OPTIONAL: UEFI firmware missing; install edk2-ovmf to boot an ISO locally.")

    return 1 if failed else 0


if __name__ == "__main__":
    raise SystemExit(main())
