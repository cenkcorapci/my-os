#!/usr/bin/env python3
"""Boot an explicitly selected ISO in a disposable UEFI QEMU virtual machine."""

from __future__ import annotations

import argparse
import shutil
import subprocess
import sys
import tempfile
from pathlib import Path


FIRMWARE_PAIRS = (
    (
        Path("/usr/share/edk2/x64/OVMF_CODE.4m.fd"),
        Path("/usr/share/edk2/x64/OVMF_VARS.4m.fd"),
    ),
    (
        Path("/usr/share/OVMF/OVMF_CODE.fd"),
        Path("/usr/share/OVMF/OVMF_VARS.fd"),
    ),
)


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--iso", required=True, help="ISO image to boot")
    args = parser.parse_args()
    iso = Path(args.iso).expanduser().resolve()
    if not iso.is_file():
        parser.error(f"ISO does not exist: {iso}")

    qemu = shutil.which("qemu-system-x86_64")
    if not qemu:
        print("ERROR: qemu-system-x86_64 not found.", file=sys.stderr)
        return 1
    firmware = next(
        ((code, variables) for code, variables in FIRMWARE_PAIRS if code.is_file() and variables.is_file()),
        None,
    )
    if firmware is None:
        print("ERROR: UEFI OVMF firmware not found; install edk2-ovmf.", file=sys.stderr)
        return 1

    code, variables = firmware
    with tempfile.TemporaryDirectory(prefix="personal-arch-uefi-") as temp_dir:
        vars_copy = Path(temp_dir) / "OVMF_VARS.fd"
        shutil.copyfile(variables, vars_copy)
        command = [
            qemu,
            "-machine",
            "q35",
            "-m",
            "4096",
            "-smp",
            "2",
            "-drive",
            f"if=pflash,format=raw,readonly=on,file={code}",
            "-drive",
            f"if=pflash,format=raw,file={vars_copy}",
            "-drive",
            f"file={iso},media=cdrom,readonly=on",
            "-boot",
            "order=d",
            "-nic",
            "user,model=virtio-net-pci",
        ]
        if Path("/dev/kvm").exists():
            command[1:1] = ["-enable-kvm"]
        print(f"Booting {iso} with disposable UEFI variables.")
        return subprocess.run(command, check=False).returncode


if __name__ == "__main__":
    raise SystemExit(main())
